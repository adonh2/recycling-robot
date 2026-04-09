import cv2
import os

os.makedirs("frames", exist_ok=True)

video_folder = r"C:\Users\lonan\Desktop\Projects\recycling-robot\mbot2 videos"

# Get all video files in the folder
videos = [f for f in os.listdir(video_folder) if f.endswith((".mp4", ".mov", ".avi", ".MOV"))]

print(f"Found {len(videos)} videos: {videos}")

total_saved = 0
frame_counter = 0  # Global counter so frames from different videos don't overwrite each other

for video in videos:
    video_path = os.path.join(video_folder, video)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open {video}, skipping...")
        continue

    print(f"\nProcessing {video}...")
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_counter % 10 == 0:
            cv2.imwrite(f"frames/frame_{frame_counter}.jpg", frame)
            saved += 1

        frame_counter += 1

    cap.release()
    print(f"  Saved {saved} frames from {video}")
    total_saved += saved

print(f"\nDone! {total_saved} total frames saved to /frames folder")