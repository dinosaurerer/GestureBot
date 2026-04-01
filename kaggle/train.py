import warnings

warnings.filterwarnings('ignore')
from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('yolo11n.yaml')  # 地址改成自己的
    model.train(data=r'GES.yaml',
                cache='ram',
                imgsz=640,
                epochs=500,
                single_cls=False,  # 是否是单类别检测
                batch=64,
                close_mosaic=10,
                workers=0,
                device='cuda',  # 自动选择可用GPU
                # device='cpu',  # 改为cpu，系统无可用GPU
                amp=True,
                project='runs/train',
                name='exp',
                cfg='config.yaml'
                )