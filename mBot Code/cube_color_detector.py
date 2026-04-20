"""
Detect the color of a cube placed inside a yellow A4 box viewed by webcam.

Pipeline:
1. Capture webcam frames.
2. Find yellow regions via HSV thresholding.
3. Locate the largest yellow contour and approximate it as a 4-corner quad.
4. Draw a crosshair box on the detected A4 sheet.
5. Warp that quad to a flat top-down A4 view (210 x 297 ratio).
6. Inside the warped view, mask OUT the yellow border to isolate the cube.
7. Find the largest non-yellow blob -> assume it's the cube.
8. Classify the cube's mean HSV color and display the result.

Controls:
    q - quit
"""

import cv2
import numpy as np


# ---- HSV ranges (OpenCV: H 0-179, S 0-255, V 0-255) ----
YELLOW_LOWER = np.array([18, 90, 90])
YELLOW_UPPER = np.array([38, 255, 255])

# Named color classification ranges. Red wraps around hue, so it has two.
COLOR_RANGES = {
    "Red":    [(np.array([0,   120, 70]),  np.array([10,  255, 255])),
               (np.array([170, 120, 70]),  np.array([179, 255, 255]))],
    "Orange": [(np.array([11,  120, 70]),  np.array([17,  255, 255]))],
    "Yellow": [(np.array([18,  90,  90]),  np.array([38,  255, 255]))],
    "Green":  [(np.array([39,  60,  60]),  np.array([85,  255, 255]))],
    "Cyan":   [(np.array([86,  60,  60]),  np.array([100, 255, 255]))],
    "Blue":   [(np.array([101, 80,  50]),  np.array([130, 255, 255]))],
    "Purple": [(np.array([131, 60,  50]),  np.array([160, 255, 255]))],
    "Pink":   [(np.array([161, 60,  70]),  np.array([169, 255, 255]))],
}

# Output warped-A4 dimensions. Ratio matches real A4 (210 x 297 mm).
A4_W, A4_H = 420, 594


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as [top-left, top-right, bottom-right, bottom-left]."""
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([
        pts[np.argmin(s)],   # TL has smallest x+y
        pts[np.argmin(d)],   # TR has smallest y-x
        pts[np.argmax(s)],   # BR has largest x+y
        pts[np.argmax(d)],   # BL has largest y-x
    ], dtype=np.float32)


def find_yellow_quad(frame_bgr: np.ndarray):
    """Return the 4 ordered corners of the largest yellow quadrilateral, or None."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, YELLOW_LOWER, YELLOW_UPPER)

    # Close gaps in the yellow border and remove specks
    k = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, mask

    # Must be reasonably large to be an A4 sheet on camera
    frame_area = frame_bgr.shape[0] * frame_bgr.shape[1]
    candidates = [c for c in contours if cv2.contourArea(c) > 0.03 * frame_area]
    if not candidates:
        return None, mask

    largest = max(candidates, key=cv2.contourArea)
    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    if len(approx) != 4:
        return None, mask

    return order_corners(approx), mask


def classify_color(hsv_pixels: np.ndarray):
    """Classify an Nx3 array of HSV pixels into (name, mean_BGR)."""
    if hsv_pixels.size == 0:
        return "Unknown", (128, 128, 128)

    h, s, v = hsv_pixels[:, 0], hsv_pixels[:, 1], hsv_pixels[:, 2]
    mean_h, mean_s, mean_v = int(np.mean(h)), int(np.mean(s)), int(np.mean(v))

    mean_bgr = cv2.cvtColor(
        np.uint8([[[mean_h, mean_s, mean_v]]]), cv2.COLOR_HSV2BGR
    )[0][0]
    mean_bgr = tuple(int(c) for c in mean_bgr)

    # Handle grayscale cases first
    if mean_v < 50:
        return "Black", mean_bgr
    if mean_s < 40 and mean_v > 200:
        return "White", mean_bgr
    if mean_s < 40:
        return "Gray", mean_bgr

    # Score each named hue range by pixel count
    best_name, best_score = "Unknown", 0
    for name, ranges in COLOR_RANGES.items():
        score = 0
        for lo, hi in ranges:
            m = ((h >= lo[0]) & (h <= hi[0]) &
                 (s >= lo[1]) & (s <= hi[1]) &
                 (v >= lo[2]) & (v <= hi[2]))
            score += int(np.count_nonzero(m))
        if score > best_score:
            best_name, best_score = name, score

    return best_name, mean_bgr


def detect_cube_color(warped_bgr: np.ndarray):
    """Find the cube in the warped A4 view and return (name, mean_BGR, bbox)."""
    hsv = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2HSV)

    # Crop out the yellow border region so we only look at the inside
    margin = 40
    inner = hsv[margin:-margin, margin:-margin]
    if inner.size == 0:
        return None

    # Mask out yellow (the box itself) and paper-white background
    yellow_mask = cv2.inRange(inner, YELLOW_LOWER, YELLOW_UPPER)
    white_mask = cv2.inRange(inner, np.array([0, 0, 200]), np.array([179, 40, 255]))
    non_bg = cv2.bitwise_not(cv2.bitwise_or(yellow_mask, white_mask))

    # Clean the mask
    k = np.ones((5, 5), np.uint8)
    non_bg = cv2.morphologyEx(non_bg, cv2.MORPH_OPEN, k)
    non_bg = cv2.morphologyEx(non_bg, cv2.MORPH_CLOSE, k, iterations=2)

    contours, _ = cv2.findContours(non_bg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    cube = max(contours, key=cv2.contourArea)
    if cv2.contourArea(cube) < 500:  # too small to be a cube
        return None

    # Sample only the pixels inside the cube contour (avoids edge bleed)
    cube_mask = np.zeros(inner.shape[:2], dtype=np.uint8)
    cv2.drawContours(cube_mask, [cube], -1, 255, thickness=cv2.FILLED)
    cube_mask = cv2.erode(cube_mask, k, iterations=2)  # shrink away edges

    pixels = inner[cube_mask > 0]
    if pixels.size == 0:
        return None

    name, mean_bgr = classify_color(pixels)
    x, y, w, h = cv2.boundingRect(cube)
    bbox = (x + margin, y + margin, w, h)  # back into warped coords
    return name, mean_bgr, bbox


def draw_crosshair_box(frame: np.ndarray, corners: np.ndarray):
    """Draw a yellow bounding polygon plus crosshair lines across it."""
    pts = corners.astype(int)
    cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=3)

    # Corner ticks for a "crosshair" feel
    for (x, y) in pts:
        cv2.line(frame, (x - 15, y), (x + 15, y), (0, 255, 255), 2)
        cv2.line(frame, (x, y - 15), (x, y + 15), (0, 255, 255), 2)

    # Center crosshair
    cx, cy = int(np.mean(pts[:, 0])), int(np.mean(pts[:, 1]))
    cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 255), 1)
    cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 255), 1)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam.")

    dst_corners = np.array([[0, 0], [A4_W, 0], [A4_W, A4_H], [0, A4_H]], dtype=np.float32)

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        display = frame.copy()
        result = find_yellow_quad(frame)
        corners, _ = result if result[0] is not None else (None, None)

        if corners is not None:
            draw_crosshair_box(display, corners)

            # Perspective-correct to a flat A4 view
            M = cv2.getPerspectiveTransform(corners, dst_corners)
            warped = cv2.warpPerspective(frame, M, (A4_W, A4_H))

            cube = detect_cube_color(warped)
            if cube is not None:
                name, mean_bgr, (x, y, w, h) = cube
                cv2.rectangle(warped, (x, y), (x + w, y + h), (0, 0, 0), 2)
                label = f"Cube: {name}"
                cv2.putText(warped, label, (x, max(25, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                cv2.rectangle(warped, (10, 10), (60, 60), mean_bgr, -1)
                cv2.rectangle(warped, (10, 10), (60, 60), (0, 0, 0), 2)

                # Also label on the main feed
                cv2.putText(display, label, (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            else:
                cv2.putText(warped, "No cube detected", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow("A4 top-down view", warped)
        else:
            cv2.putText(display, "Show the yellow A4 box to the camera",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("Webcam", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()