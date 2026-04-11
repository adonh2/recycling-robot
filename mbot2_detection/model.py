from ultralytics import YOLO

# Start from a pre-trained base (transfer learning)
model = YOLO("yolov8n.pt")  # 'n' = nano, fastest; try 'm' for more accuracy

model.train(
    data="C:\\Users\\lonan\\Desktop\\Projects\\recycling-robot\\mbot2_detection\\mbot-detection.v2i.yolov8\\data.yaml",  # From Roboflow export
    epochs=50,
    imgsz=640,
    batch=16,
    name="mbot2_detector"
)