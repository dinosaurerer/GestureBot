CLAUDE.md

本文档为 Claude Code（claude.ai/code）提供指导，用于处理本代码仓库中的代码。

一、项目概述

GestureBot 是一套基于手势识别的 Rosmaster X3 机器人小车运动交互控制系统。系统通过 YOLO11 模型实时检测 7 种手势，将手势映射为机器人运动指令，并通过 Web 界面提供实时监控与远程控制。

二、架构设计

2.1 核心组件

1. 多线程架构

  - 视频处理线程：捕获帧、执行 YOLO 推理、映射手势指令、控制机器人

  - Web 服务器线程：基于 Flask 应用，使用 gevent 处理异步 HTTP 请求

  - 主线程：简单循环，用于安全关闭处理

2. 核心类

  - `X3WheelController`：Rosmaster X3 机器人运动控制器（支持 7 种运动状态）

  - `SystemState`：线程安全的状态管理类（管理手势、置信度、帧率等信息）

  - `GestureControlSystem`：手势检测与运动控制的主系统（含手势→指令映射）

  - `SimpleLogger`：支持线程安全的内存日志记录器

3. 手势→运动指令映射

  系统通过 `GESTURE_TO_MOTION` 字典将检测到的手势类别直接映射为运动指令：

  - forward → FORWARD（前进，状态 1）
  - backward → BACKWARD（后退，状态 2）
  - left → LEFT（左移，状态 3）
  - right → RIGHT（右移，状态 4）
  - rotate_left → ROTATE_LEFT（左旋转，状态 5）
  - rotate_right → ROTATE_RIGHT（右旋转，状态 6）
  - stop → STOP（停止，状态 0）

4. 运动状态（X3 机器人协议）

  - 0：停止（STOP）
  - 1：前进（FORWARD）
  - 2：后退（BACKWARD）
  - 3：左转（LEFT）
  - 4：右转（RIGHT）
  - 5：左旋转（ROTATE_LEFT）
  - 6：右旋转（ROTATE_RIGHT）

2.2 检测系统

- 检测目标：7 种手势（forward, backward, left, right, rotate_left, rotate_right, stop）

- 基线模型：YOLO11n（从零训练，mAP50=0.995, mAP50-95=0.733）

- 改进模型：YOLO11n-ELA（在 Neck 特征融合层引入 ELA 注意力机制，CVPR 2024）

- 模型默认路径：/home/jetson/ultralytics/ultralytics/best.pt

- 逻辑：检测到有效手势 → 映射为运动指令并执行；连续 15 帧未检测到 → 停止

- 置信度阈值：0.5（可调整）

- background 类自动过滤

三、常用命令

3.1 运行系统

# 基础运行命令
python main.py

# 带参数运行
python main.py debug model=/path/to/best.pt speed=80 port=7000 host=192.168.1.100

# 数据集采集
python dataset/tools/collect_gesture_video.py
# 按空格键开始/停止录制，按 q 键退出

# 将视频转换为训练图像
python dataset/tools/video_to_images.py

# 模型推理测试（本地视频）
python predict.py

# 模型导出（PT → ONNX → TensorRT Engine，在 Jetson 上运行）
python kaggle/model_pt_onnx_engine.py

3.2 关键参数

- Web 端口：6500（默认）

- 速度：70%（默认）

- 摄像头：640x480 分辨率

- YOLO 置信度：0.5（默认）

- 默认模型路径：/home/jetson/ultralytics/ultralytics/best.pt

四、网页界面

4.1 API 接口

- `/`：主网页界面（gesture_control.html）

- `/video_feed`：MJPEG 视频流（仅包含处理后的帧）

- `/api/status`：JSON 格式的系统状态

- `/api/control`：POST 方法提交运动指令

- `/api/settings`：更新速度/置信度阈值

- `/api/logs`：获取最近的日志记录

4.2 控制界面功能

- 实时视频显示

- 手势识别结果展示（手势类别 → 运动指令 → 置信度）

- 所有运动状态的手动控制按钮

- 实时状态监控（帧率、置信度、检测结果、检测次数）

- 速度和置信度阈值调节滑块

- 手势对照表

- 系统日志显示

五、开发说明

5.1 线程安全

- 所有共享状态更新均使用 `threading.Lock` 锁机制

- 视频帧通过线程安全的 `get_latest_frame()` 方法访问

- 状态管理集中在 `SystemState` 类中

5.2 机器人初始化流程

1. 创建 Rosmaster 实例

2. 创建接收线程（通信关键步骤）

3. 将小车类型设置为 X3

4. 初始化车轮控制器

5. 发送停止指令，确保初始状态安全

5.3 视频处理流程

1. 从 USB 摄像头捕获帧

2. 运行 YOLO 推理，检测手势

3. 取置信度最高的有效手势（过滤 background 类）

4. 通过 GESTURE_TO_MOTION 映射为运动指令并执行

5. 在帧上绘制视觉反馈（手势名称、运动指令、置信度）

6. 保存帧用于网页流媒体传输

5.4 重要文件

- `main.py`：主应用程序（GestureControlSystem 手势识别控制系统）

- `templates/gesture_control.html`：手势控制 Web 界面

- `predict.py`：模型推理测试脚本（支持实时视频检测和结果保存）

- `kaggle/train.py`：Kaggle 训练脚本（支持 YOLO11n 和 YOLO11n-ELA）

- `kaggle/config.yaml`：训练超参数配置

- `kaggle/model_pt_onnx_engine.py`：模型导出脚本（PT → TensorRT Engine）

- `dataset/tools/`：数据集采集工具目录

- `training_analysis/`：基线模型训练结果与分析报告

- `ultralytics/nn/modules/ela.py`：ELA 注意力模块实现

- `ultralytics/cfg/models/11/yolo11-ELA.yaml`：YOLO11n-ELA 模型架构

六、模型改进：YOLO11n-ELA

6.1 改进内容

在 YOLO11n 的 Neck 特征融合层中引入 ELA（Efficient Local Attention，CVPR 2024）注意力模块：

- ELA 模块位置：`ultralytics/nn/modules/ela.py`

- 模型架构文件：`ultralytics/cfg/models/11/yolo11-ELA.yaml`

- 在 3 个特征融合点（Concat 之后、C3k2 之前）各插入一个 ELA 层

- Backbone 不变，仅修改 Neck

6.2 ELA 原理

- 沿空间 X/Y 维度分别做 1D 卷积 + GroupNorm，捕获局部空间依赖

- 无通道降维，保留完整特征信息

- 参数增量极小，推理开销几乎为零

- 论文：https://arxiv.org/abs/2403.01123

6.3 模块注册

ELA 已注册到 ultralytics 模块系统：

- `ultralytics/nn/modules/__init__.py`：导出 ELA 类

- `ultralytics/nn/tasks.py`：import ELA + parse_model 处理逻辑

6.4 模型对比

| 指标 | YOLO11n（基线） | YOLO11n-ELA（改进） |
|------|----------------|-------------------|
| 层数 | 319 | 334 |
| 参数量 | 2.62M | 6.13M |
| GFLOPs | 6.6 | 13.7 |
| mAP50 | 0.995 | 训练中 |
| mAP50-95 | 0.733 | 训练中 |

6.5 训练配置

- 训练平台：Kaggle（2× Tesla T4）

- Batch Size：128

- 图片尺寸：640

- Epochs：500（early stopping patience=50）

- 训练脚本：`kaggle/train.py`（model='yolo11-ELA.yaml'）

七、依赖包

- ultralytics（YOLO 相关库）

- Flask（Web 框架）

- gevent（异步处理库）

- OpenCV（cv2，图像处理库）

- Rosmaster_Lib（机器人控制库）

- threading（Python 内置线程库）

- datetime（Python 内置日期时间库）

八、环境配置

项目使用 Conda 进行环境管理（配置信息在 .vscode/settings.json 中）。运行前请确保所有依赖包已安装完成。

九、手势类别

系统支持识别 7 种手势类型：

- forward：前进
- backward：后退
- left：左转
- right：右转
- rotate_left：左旋转
- rotate_right：右旋转
- stop：停止运动
