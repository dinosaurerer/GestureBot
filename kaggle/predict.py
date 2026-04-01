from ultralytics import YOLO
import cv2

# Load a pretrained YOLO11n model
model = YOLO(r"C:\Users\Administrator\Desktop\kaggle\results\yolo11-hand-gesture-recognition\runs\train\exp\weights\best.pt")

# video
source = r"D:\workspace\GestureBot\dataset\original_ges_videos\forward\forward_01.mp4"

cap = cv2.VideoCapture(source)
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, fps, (w, h))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    annotated = results[0].plot()

    out.write(annotated)
    # cv2.imshow('gesture', annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()