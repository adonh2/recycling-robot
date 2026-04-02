import cv2
import numpy as np
from PIL import Image


def get_color_ranges():
    return {
        "red": [
            (np.array([0, 120, 70]), np.array([10, 255, 255])),
            (np.array([170, 120, 70]), np.array([180, 255, 255])),
        ],
        "blue": [
            (np.array([100, 120, 70]), np.array([140, 255, 255])),
        ],
        "purple": [
            (np.array([125, 80, 70]), np.array([165, 255, 255])),
        ],
    }


def find_bbox(hsv_image, ranges):
    combined_mask = None

    for lower, upper in ranges:
        mask = cv2.inRange(hsv_image, lower, upper)
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask = cv2.bitwise_or(combined_mask, mask)

    mask_img = Image.fromarray(combined_mask)
    return mask_img.getbbox()


cap = cv2.VideoCapture(0)

color_ranges = get_color_ranges()

# Outline colors in BGR
outline_colors = {
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "purple": (255, 0, 255),
}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    for color_name, ranges in color_ranges.items():
        bbox = find_bbox(hsv_image, ranges)

        if bbox is not None:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), outline_colors[color_name], 3)
            cv2.putText(
                frame,
                color_name,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                outline_colors[color_name],
                2
            )

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
cv2.destroyAllWindows()
