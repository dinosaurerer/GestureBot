from ultralytics import YOLO

# Load a YOLO11n PyTorch model
model = YOLO("/home/jetson/ultralytics/ultralytics/yolo11n.pt")
# model = YOLO("/home/jetson/ultralytics/ultralytics/yolo11n-seg.pt")
# model = YOLO("/home/jetson/ultralytics/ultralytics/yolo11n-pose.pt")
# model = YOLO("/home/jetson/ultralytics/ultralytics/yolo11n-cls.pt")
# model = YOLO("/home/jetson/ultralytics/ultralytics/yolo11n-obb.pt")

# Export the model to TensorRT
model.export(format="engine")