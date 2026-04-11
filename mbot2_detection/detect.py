import cv2
from ultralytics import YOLO

model = YOLO(r"../runs/detect/mbot2_detector3/weights/best.pt")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.5)
    annotated = results[0].plot()

    cv2.imshow("mBot2 Detector", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()