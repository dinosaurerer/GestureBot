CLAUDE.md

本文档为 Claude Code（claude.ai/code）提供指导，用于处理本代码仓库中的代码。

一、项目概述

GestureBot 是一套用于 Rosmaster X3 机器人小车的手势识别控制系统。该系统采用 YOLO（You Only Look Once）计算机视觉模型检测手势，并通过网页界面控制机器人运动。

二、架构设计

2.1 核心组件

1. 多线程架构

  - 视频处理线程：捕获帧、执行 YOLO 推理、控制机器人

  - Web 服务器线程：基于 Flask 应用，使用 gevent 处理异步 HTTP 请求

  - 主线程：简单循环，用于优雅关闭处理

2. 核心类

  - `X3WheelController`：Rosmaster X3 机器人运动控制器（支持 7 种运动状态）

  - `SystemState`：线程安全的状态管理类（管理手势、置信度、帧率等信息）

  - `OrangeDetectControlSystem`：集成视觉检测与机器人控制的主控制系统（后续改为GestureControlSystem）

  - `SimpleLogger`：支持线程安全的内存日志记录器

3. 运动状态（X3 机器人协议）
        

  - 0：停止（STOP）

  - 1：前进（FORWARD）

  - 2：后退（BACKWARD）

  - 3：左转（LEFT）

  - 4：右转（RIGHT）

  - 5：左旋转（ROTATE_LEFT）

  - 6：右旋转（ROTATE_RIGHT）

2.2 检测系统

- 检测目标：“橙子”（COCO 类别 ID：49）【当前阶段使用“橙子”作为目标进行功能验证，后续将替换为手势数据集进行训练与识别。】

- 模型：YOLO11n.pt（默认路径：/home/jetson/ultralytics/ultralytics/yolo11n.pt）

- 逻辑：检测到橙子 → 机器人前进；连续 15 帧未检测到 → 停止

- 置信度阈值：0.5（可调整）

三、常用命令

3.1 运行系统

# 基础运行命令
python main.py

# 带参数运行
python main.py debug model=/path/to/model.pt speed=80 port=7000 host=192.168.1.100

# 数据集采集
python dataset/tools/collect_gesture_video.py
# 按空格键开始/停止录制，按 q 键退出

# 将视频转换为训练图像
python dataset/tools/video_to_images.py

3.2 关键参数

- Web 端口：6500（默认）

- 速度：70%（默认）

- 摄像头：640x480 分辨率

- YOLO 置信度：0.5（默认）

四、网页界面

4.1 API 接口

- `/`：主网页界面（test_orange.html）

- `/video_feed`：MJPEG 视频流（仅包含处理后的帧）

- `/api/status`：JSON 格式的系统状态

- `/api/control`：POST 方法提交运动指令

- `/api/settings`：更新速度/置信度阈值

- `/api/logs`：获取最近的日志记录

4.2 控制界面功能

- 实时视频显示

- 所有运动状态的手动控制按钮

- 实时状态监控（帧率、置信度、检测结果）

- 速度和置信度阈值调节滑块

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

2. 运行 YOLO 推理，检测橙子

3. 根据检测结果更新机器人运动状态

4. 在帧上绘制视觉反馈（检测框等）

5. 保存帧用于网页流媒体传输

5.4 重要文件

- `main.py`：包含所有核心逻辑的主应用程序

- `templates/test_orange.html`：网页界面文件

- `dataset/tools/`：数据集采集工具目录

- `original_images_ges/`：训练数据存储结构目录

六、依赖包

- ultralytics（YOLO 相关库）

- Flask（Web 框架）

- gevent（异步处理库）

- OpenCV（cv2，图像处理库）

- Rosmaster_Lib（机器人控制库）

- threading（Python 内置线程库）

- datetime（Python 内置日期时间库）

七、环境配置

项目使用 Conda 进行环境管理（配置信息在 .vscode/settings.json 中）。运行前请确保所有依赖包已安装完成。

八、手势类别

系统支持识别 7 种手势类型：

- FORWARD：前进

- BACKWARD：后退

- LEFT：左转

- RIGHT：右转

- ROTATE_LEFT：左旋转

- ROTATE_RIGHT：右旋转

- STOP：停止运动
