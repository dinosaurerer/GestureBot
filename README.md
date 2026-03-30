# Gesture-Based Human-Vehicle Interaction Control System
自适应手势识别的人车运动交互控制系统设计与实现

## 项目简介

这是一个基于YOLO手势识别的Rosmaster X3机器人控制系统，通过计算机视觉技术实现自然的人车交互。当前版本使用橙子检测进行功能验证，后续将替换为手势识别模块。

## 核心功能

| 模块 | 功能描述 | 开发状态 |
|------|----------|----------|
| **视觉检测** | 使用YOLO进行实时目标检测 | ✅ 已实现 |
| **机器人控制** | Rosmaster X3七种运动模式控制 | ✅ 已实现 |
| **Web界面** | 实时视频流和远程控制 | ✅ 已实现 |
| **多线程架构** | 视频处理与Web服务并行 | ✅ 已实现 |
| **手势识别** | 计划替换橙子检测 | 🔄 未来规划 |

## 当前功能特点

### 橙子检测模式（当前测试阶段）
- **检测目标**: 橙子（COCO类别ID: 49）
- **控制逻辑**: 检测到橙子→前进；连续15帧未检测→停止
- **YOLO模型**: YOLO11n.pt（默认路径）
- **置信度阈值**: 0.5（可调节）

### 运动控制模式
- **7种运动状态**:
  - 0: 停止 (STOP)
  - 1: 前进 (FORWARD)
  - 2: 后退 (BACKWARD)
  - 3: 左移 (LEFT)
  - 4: 右移 (RIGHT)
  - 5: 左旋转 (ROTATE_LEFT)
  - 6: 右旋转 (ROTATE_RIGHT)

## 系统架构

```
GestureBot - Rosmaster X3 控制系统
├── 视频处理线程
│   ├── USB摄像头捕获 (640x480)
│   ├── YOLO推理检测
│   ├── 机器人控制指令
│   └── 视觉反馈绘制
├── Web服务器线程
│   ├── Flask Web应用
│   ├── Gevent异步处理
│   └── MJPEG视频流
└── 主线程
    ├── 优雅关闭处理
    └── 系统协调管理

核心类结构:
├── X3WheelController     # X3轮子控制器
├── SystemState          # 线程安全状态管理
├── OrangeDetectControlSystem # 检测控制系统
└── SimpleLogger         # 内存日志记录器
```

## 技术栈

- **Python 3.7+** - 主要编程语言
- **Flask** - Web框架
- **Gevent** - 异步处理
- **OpenCV** - 图像处理
- **Ultralytics YOLO** - 目标检测
- **Rosmaster_Lib** - 机器人控制
- **Threading** - 多线程支持

## 支持的硬件平台

- ✅ **Rosmaster X3** - 当前测试平台
- 🔄 Rosmaster X3PLUS - 计划支持
- 🔄 R2/R2L系列 - 计划支持

## 快速开始

### 环境要求

```bash
Python >= 3.7
```

### 安装依赖

```bash
pip install ultralytics flask gevent opencv-python Rosmaster_Lib
```

### 运行系统

```bash
# 基础运行
python main.py

# 带参数运行
python main.py debug model=/path/to/model.pt speed=80 port=7000 host=192.168.1.100

# Web界面访问
# http://localhost:6500
```

### 数据集采集（未来手势识别）

```bash
# 采集手势视频
python dataset/tools/collect_gesture_video.py
# 按空格键开始/停止录制，按q键退出

# 转换视频为训练图像
python dataset/tools/video_to_images.py
```

## Web界面功能

- **实时视频显示** - MJPEG视频流
- **手动控制按钮** - 7种运动状态控制
- **实时状态监控** - 帧率、置信度、检测结果
- **参数调节** - 速度(0-100%)、置信度阈值(0.1-1.0)
- **系统日志** - 实时日志显示

### API接口

- `GET /` - 主网页界面
- `GET /video_feed` - MJPEG视频流
- `GET /api/status` - JSON格式系统状态
- `POST /api/control` - 手动控制指令
- `POST/GET /api/settings` - 更新参数设置
- `GET /api/logs` - 获取日志记录

## 开发进度

- [x] 项目架构重构
- [x] 多线程视频处理
- [x] YOLO检测集成
- [x] Web界面开发
- [x] 线程安全状态管理
- [x] 参数配置系统
- [x] 日志记录系统
- [x] 橙子检测测试
- [ ] 手势数据集采集
- [ ] 手势模型训练
- [ ] 手势识别集成
- [ ] 系统优化测试

## 项目结构

```
.
├── main.py              # 主程序（重构完成）
├── CLAUDE.md            # 项目文档
├── README.md            # 项目说明
├── .gitignore           # Git忽略文件
├── requirements.txt     # 依赖列表
├── templates/           # Web模板
│   ├── test_orange.html      # 橙子检测界面
│   └── gesture_control.html # 手势控制界面（预留）
├── dataset/             # 数据集目录（已忽略）
│   └── tools/               # 数据集工具
├── original_images_ges/ # 手势数据集（已忽略）
└── logs/               # 日志目录
```

## 代码亮点

1. **多线程架构** - 视频处理与Web服务完全分离，避免阻塞
2. **线程安全** - 使用threading.Lock保护共享状态
3. **模块化设计** - 清晰的类分离和职责划分
4. **实时视频流** - 高效的MJPEG视频传输
5. **优雅关闭** - 完善的资源清理机制
6. **配置灵活** - 支持命令行参数和Web界面调节

## 注意事项

1. 默认使用YOLO11n.pt模型，需确保模型文件存在
2. 数据集目录已添加到.gitignore，不会被上传
3. 首次运行需要初始化Rosmaster硬件连接
4. 建议在独立网络环境中运行，避免延迟

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License