import warnings

warnings.filterwarnings('ignore')
from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('yolo11-ELA.yaml')  # YOLO11n + ELA注意力机制
    model.train(data=r'GES.yaml',
                cache='ram',
                imgsz=640,
                epochs=500,
                single_cls=False,
                batch=128,
                close_mosaic=10,
                workers=4,
                device=[0, 1],  # Kaggle 双 GPU
                amp=True,
                project='runs/train',
                name='exp_ela',
                )