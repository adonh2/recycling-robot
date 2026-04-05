import cv2
import numpy as np

cap = cv2.VideoCapture(0)

def detect_colour(frame):
    # Crop to centre region (where the block will sit)
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    region = frame[cy-40:cy+40, cx-40:cx+40]
    
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    avg = cv2.mean(hsv)[:3]
    h_val, s_val, v_val = avg

    if s_val < 50:
        return "GREY"
    elif h_val < 10 or h_val > 160:
        return "RED"
    elif 35 < h_val < 85:
        return "GREEN"
    elif 85 < h_val < 130:
        return "BLUE"
    else:
        return "UNKNOWN"

while True:
    ret, frame = cap.read()
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    # Draw the detection box so you can see what it's reading
    cv2.rectangle(frame, (cx-40, cy-40), (cx+40, cy+40), (255, 255, 255), 2)
    
    colour = detect_colour(frame)
    cv2.putText(frame, colour, (cx-40, cy-50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    
    cv2.imshow("Colour Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()