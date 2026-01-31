# Gesture-Based Human-Vehicle Interaction Control System
自适应手势识别的人车运动交互控制系统设计与实现

## 项目简介

这是一个基于手势识别的人车运动交互控制系统，旨在通过计算机视觉技术实现自然的人车交互。用户可以通过手势控制机器人的运动，实现直观、便捷的操控体验。

## 核心功能

| 模块 | 功能描述 | 开发状态 |
|------|----------|----------|
| 手势识别 | 通过摄像头实时捕获并识别人体手势 | 🔄 待实现 |
| 交互控制 | 将识别的手势转换为机器人运动指令 | 🔄 待实现 |
| 硬件接口 | Rosmaster机器人平台底层控制 | ✅ 基础完成 |
| 传感器集成 | IMU数据采集与处理 | ✅ 已支持 |

## 系统架构

```
Gesture-Based Human-Vehicle Interaction Control System
├── 手势识别模块 (Gesture Recognition)
│   ├── 摄像头捕获 (Camera Capture)
│   ├── 手部检测 (Hand Detection)
│   └── 手势分类 (Gesture Classification)
├── 交互控制模块 (Interaction Control)
│   ├── 手势-指令映射 (Gesture-Command Mapping)
│   ├── 运动控制算法 (Motion Control Algorithm)
│   └── PID控制器 (PID Controller)
├── 硬件接口模块 (Hardware Interface)
│   ├── Rosmaster驱动 (Rosmaster Driver)
│   ├── 传感器数据获取 (Sensor Data Acquisition)
│   └── 执行器控制 (Actuator Control)
└── 用户界面模块 (User Interface)
    ├── 实时显示 (Real-time Display)
    └── 参数调节 (Parameter Adjustment)
```

## 技术栈

- **Python 3** - 主要编程语言
- **Jupyter Notebook** - 开发和测试环境
- **Rosmaster_Lib** - 机器人硬件控制库
- **OpenCV** - 图像处理（预期）
- **MediaPipe** - 手势检测（预期）

## 支持的硬件平台

- X3 系列机器人
- X3PLUS 系列机器人
- R2/R2L 系列机器人

## 集成传感器

- **IMU** - 惯性测量单元
  - 加速度计 (Accelerometer)
  - 陀螺仪 (Gyroscope)
  - 磁力计 (Magnetometer)

## 执行器支持

- PWM舵机控制
- 总线舵机控制
- RGB LED灯带控制

## 开发进度

- [x] 项目初始化
- [x] Rosmaster硬件控制基础测试
- [ ] 手势识别模块实现
- [ ] 手势-指令映射逻辑
- [ ] 运动控制算法优化
- [ ] 用户界面开发
- [ ] 系统集成测试

## 快速开始

### 环境要求

```bash
Python >= 3.7
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
jupyter notebook test/test_rosmaster.ipynb
```

## 项目结构

```
.
├── README.md                      # 项目说明文档
├── test/                          # 测试代码目录
│   └── test_rosmaster.ipynb       # Rosmaster基础控制测试
└── .claude/                       # Claude CLI配置
    └── settings.local.json
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
