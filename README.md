# GestureBot - 自适应手势识别的人车运动交互控制系统

**Gesture-Based Human-Vehicle Interaction Control System**

基于 YOLO11 的实时手势识别控制系统，通过摄像头捕获手势指令，驱动 Rosmaster X3 机器人完成前进、后退、转向等运动控制。

## 系统概览

```
摄像头 → YOLO11 手势检测 → 指令映射 → Rosmaster X3 运动
              ↓
         Web 实时监控界面 (Flask + MJPEG)
```

**核心流程**：USB 摄像头实时捕获画面 → YOLO11 推理识别 7 种手势 → 映射为运动指令 → 驱动机器人执行动作，同时通过 Web 界面提供实时视频流和手动控制。

## 手势控制映射

系统支持 7 种手势，每种手势直接对应一种机器人运动状态：

| 手势 | 运动指令 | 说明 |
|------|---------|------|
| ✊ forward | 前进 (FORWARD) | 向前直行 |
| ✋ backward | 后退 (BACKWARD) | 向后直行 |
| 👈 left | 左移 (LEFT) | 麦克纳姆轮横向移动 |
| 👉 right | 右移 (RIGHT) | 麦克纳姆轮横向移动 |
| 🔄 rotate_left | 左旋转 (ROTATE_LEFT) | 原地逆时针旋转 |
| 🔁 rotate_right | 右旋转 (ROTATE_RIGHT) | 原地顺时针旋转 |
| ✋ stop | 停止 (STOP) | 停止运动 |

连续 15 帧未检测到有效手势时，自动执行停止指令，确保安全性。

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   GestureBot                     │
├──────────────┬──────────────┬────────────────────┤
│  视频处理线程  │  Web服务器线程 │      主线程        │
│              │              │                    │
│ 摄像头捕获    │  Flask +     │  优雅关闭处理      │
│ YOLO推理     │  Gevent      │  系统协调管理      │
│ 指令映射      │  MJPEG流     │                    │
│ 视觉反馈      │  REST API    │                    │
└──────────────┴──────────────┴────────────────────┘
```

**核心类**：
- `GestureControlSystem` — 手势检测与运动控制系统
- `X3WheelController` — Rosmaster X3 运动控制器（7 种运动模式）
- `SystemState` — 线程安全的状态管理（锁机制保护共享数据）
- `SimpleLogger` — 内存日志记录器

## 模型训练

### 数据集

| 项目 | 数值 |
|------|------|
| 总图片数 | 1,549 张 |
| 手势类别 | 7 类 |
| 训练/验证/测试 | 70% / 20% / 10% |
| 标注格式 | YOLO (txt) |
| 图片尺寸 | 640×640 |

### 基线模型（YOLO11n）

| 指标 | 值 |
|------|------|
| 模型 | YOLO11n（从零训练） |
| 训练平台 | Kaggle (2× Tesla T4) |
| 训练轮次 | 175 (early stopping) |
| Precision | 0.993 |
| Recall | 1.000 |
| mAP50 | **0.995** |
| mAP50-95 | 0.733 |
| 参数量 | 2.62M |

### 模型改进：YOLO11n-ELA

在 YOLO11n 的 Neck 特征融合层中引入 **ELA（Efficient Local Attention）** 注意力机制（CVPR 2024），通过 1D 空间卷积 + GroupNorm 捕获局部空间依赖，提升边界框定位精度。

> 实验数据对比表（训练进行中，完成后补充）

## Web 控制界面

基于 Flask + Gevent 构建的实时监控与控制界面：

- 实时 MJPEG 视频流显示
- 手势识别结果实时展示（手势类别 → 运动指令 → 置信度）
- 7 种运动模式手动控制按钮
- 速度和置信度阈值滑块调节
- 系统状态监控（FPS、置信度、检测次数、模型状态）
- 手势对照表
- 运行日志

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主控制界面 |
| `/video_feed` | GET | MJPEG 实时视频流 |
| `/api/status` | GET | 系统状态（JSON） |
| `/api/control` | POST | 手动运动控制 |
| `/api/settings` | POST/GET | 速度/阈值参数设置 |
| `/api/logs` | GET | 运行日志 |

## 快速开始

### 环境要求

- Python >= 3.8
- CUDA 支持（推理加速）
- Rosmaster X3 硬件（部署时）

### 安装依赖

```bash
pip install ultralytics flask gevent opencv-python Rosmaster_Lib
```

### 运行系统

```bash
# 基础运行
python main.py

# 带参数运行
python main.py model=/path/to/best.pt speed=80 port=7000 host=192.168.1.100

# 访问 Web 界面
# http://<host>:6500
```

### 数据集采集

```bash
# 采集手势视频
python dataset/tools/collect_gesture_video.py
# 空格键：开始/停止录制 | q键：退出

# 视频转训练图片
python dataset/tools/video_to_images.py
```

## 项目结构

```
GestureBot/
├── main.py                    # 主程序（手势识别控制系统）
├── predict.py                 # 模型推理测试脚本
├── templates/
│   └── gesture_control.html   # Web 控制界面
├── kaggle/
│   ├── train.py               # Kaggle 训练脚本（YOLO11n-ELA）
│   ├── config.yaml            # 训练超参数配置
│   ├── model_pt_onnx_engine.py # 模型导出（PT→ONNX→TensorRT）
│   └── 训练测试结果             # ELA 模型 3 轮验证输出
├── training_analysis/         # 基线模型训练结果与分析报告
├── ultralytics/               # YOLO11 框架（含 ELA 模块）
│   └── nn/modules/ela.py      # ELA 注意力模块实现
├── dataset/                   # 数据集工具
│   └── tools/                 # 视频采集、帧提取工具
└── CLAUDE.md                  # 项目技术文档
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 目标检测 | Ultralytics YOLO11 |
| 注意力机制 | ELA (CVPR 2024) |
| Web 框架 | Flask + Gevent |
| 图像处理 | OpenCV |
| 机器人控制 | Rosmaster_Lib |
| 模型部署 | TensorRT (Jetson) |
| 训练平台 | Kaggle (2× Tesla T4) |

## 许可证

MIT License
