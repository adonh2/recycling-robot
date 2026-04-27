from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # Start fresh from base model

model.train(
    data=r"C:\Users\adonh\OneDrive\Desktop\green cube detection.v1i.yolov8\data.yaml",  # Update this path to your new export
    epochs=50,
    imgsz=640,
    batch=16,
    name="green_cube"  # New name so it doesn't overwrite your mBot2 model
)
