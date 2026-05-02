import cv2
from ultralytics import YOLO
from collections import defaultdict, deque
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

model = YOLO(r"../runs/detect/mbot2_detector3/weights/best.pt")
print("Model classes:", model.names)

# Edit these to match your model's actual class names
MATERIAL_MAP = {
    "bottle": "plastic", "plastic_bottle": "plastic", "cup": "plastic", "container": "plastic",
    "can": "metal", "tin_can": "metal", "aluminum_can": "metal",
    "glass_bottle": "glass", "jar": "glass", "glass": "glass",
    "paper": "paper", "newspaper": "paper", "cardboard": "paper", "box": "paper",
}

# Material -> robot colour input
MATERIAL_TO_COLOR = {
    "plastic": "red",
    "metal":   "blue",
    "glass":   "green",
    "paper":   "purple",
}

MATERIAL_COLORS = {
    "plastic": (0, 200, 255), "metal": (200, 200, 200),
    "glass":   (255, 200, 0), "paper": (0, 255, 0),
    "unknown": (128, 128, 128),
}

# Stability filter: need N out of last M frames to agree
HISTORY_LEN = 10
STABILITY_THRESHOLD = 6
detection_history = deque(maxlen=HISTORY_LEN)

# Shared state served over HTTP
latest = {"material": "none", "color": "none"}
state_lock = threading.Lock()

def classify_material(class_name):
    return MATERIAL_MAP.get(class_name.lower().replace(" ", "_"), "unknown")

# ---- HTTP server (runs in background) ----
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with state_lock:
            payload = latest["color"]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(payload.encode())
    def log_message(self, *args, **kwargs):
        pass

def start_server(port=8080):
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=start_server, daemon=True).start()
print("Detection server running on http://0.0.0.0:8080")

# ---- Detection helpers ----
def update_stable(counts):
    if counts:
        dominant = max(counts.items(), key=lambda x: x[1])[0]
        detection_history.append(dominant if dominant != "unknown" else None)
    else:
        detection_history.append(None)

    tally = defaultdict(int)
    for m in detection_history:
        if m: tally[m] += 1

    with state_lock:
        if tally:
            top, n = max(tally.items(), key=lambda x: x[1])
            if n >= STABILITY_THRESHOLD:
                latest["material"] = top
                latest["color"] = MATERIAL_TO_COLOR.get(top, "none")
                return
        latest["material"] = "none"
        latest["color"] = "none"

def draw_detections(frame, results):
    counts = defaultdict(int)
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        conf = float(box.conf[0])
        cls_name = model.names[int(box.cls[0])]
        material = classify_material(cls_name)
        color = MATERIAL_COLORS[material]
        counts[material] += 1
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{material} ({cls_name}) {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return frame, counts

def draw_summary(frame, counts):
    cv2.rectangle(frame, (10, 10), (260, 200), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (260, 200), (255, 255, 255), 1)
    cv2.putText(frame, "Material Counts", (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    y = 55
    for material in ["plastic", "metal", "glass", "paper"]:
        cv2.putText(frame, f"{material}: {counts.get(material, 0)}", (20, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, MATERIAL_COLORS[material], 2)
        y += 22
    with state_lock:
        m, c = latest["material"], latest["color"]
    cv2.putText(frame, f"Locked: {m}", (20, y + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(frame, f"-> {c}", (20, y + 34),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    return frame


cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    results = model(frame, conf=0.5, verbose=False)
    frame, counts = draw_detections(frame, results)
    update_stable(counts)
    frame = draw_summary(frame, counts)
    cv2.imshow("Waste Material Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()