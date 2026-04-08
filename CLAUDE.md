# CLAUDE.md
本文档为 Claude Code（claude.ai/code）提供完整指导，用于理解、修改、调试本代码仓库的所有代码，包含项目全量架构、核心逻辑、参数规范、开发规则与细节说明。

---

## 一、项目概述
GestureBot 是**本科毕业设计《基于手势识别的人车运动交互控制系统研究》** 配套工程实现，是一套基于YOLO11深度学习模型的ROSMASTER X3机器人小车手势运动交互控制系统。
- **硬件平台**：Jetson Orin 系列主控板 + ROSMASTER X3 麦克纳姆轮全向移动机器人（STM32下位机扩展板）
- **核心功能**：通过USB摄像头实时采集图像，基于YOLO11模型端侧推理实现7类小车控制手势的实时检测与分类，将手势映射为标准运动指令，通过串口与下位机通讯实现小车实时运动控制；同时基于Flask提供Web可视化界面，支持远程监控、手动控制与参数在线调节。
- **核心创新**：在YOLO11n轻量化模型基础上，引入ELA（Efficient Local Attention）高效局部注意力模块，在极小的参数量增量下，显著提升模型的手势定位精度与相似动作区分能力，实现端侧实时推理与零误分类控制。
- **通讯架构**：上位机Jetson Orin通过USB串口与ROSMASTER X3下位机STM32扩展板通讯，基于Rosmaster_Lib实现标准运动指令的封装与解析，完成手势指令到小车运动的闭环控制。

---

## 二、架构设计
### 2.1 核心组件
#### 1. 多线程架构（线程安全设计）
- **视频处理线程**：核心工作线程，负责USB摄像头帧捕获、YOLO模型推理、手势→运动指令映射、ROSMASTER X3小车运动控制、帧渲染与缓存
- **Web服务器线程**：基于Flask框架 + gevent协程，处理异步HTTP请求，提供视频流、状态查询、远程控制、参数调节接口
- **主线程**：守护线程，负责系统初始化、信号监听、异常捕获、线程安全关闭与资源释放

#### 2. 核心类定义
- `X3WheelController`：ROSMASTER X3 机器人运动控制器，封装下位机通讯协议，支持7种标准运动状态的控制、速度调节、急停与状态查询
- `SystemState`：线程安全的全局状态管理类，基于`threading.Lock`实现锁机制，统一管理手势识别结果、置信度、系统帧率、运动状态、参数配置等共享数据
- `GestureControlSystem`：手势识别与运动控制主系统，封装全流程初始化、线程启动、推理循环、指令映射、异常处理与安全关闭逻辑
- `SimpleLogger`：线程安全的内存环形日志记录器，支持日志分级、历史回溯、Web接口实时查询

#### 3. 手势→运动指令映射规则
系统通过全局常量 `GESTURE_TO_MOTION` 字典，将YOLO模型检测到的手势类别，一对一映射为ROSMASTER X3小车标准运动指令，映射关系不可动态修改：
| 手势类别       | 映射运动指令 | 指令含义       | 协议状态码 |
|----------------|--------------|----------------|------------|
| forward        | FORWARD      | 前进           | 1          |
| backward       | BACKWARD     | 后退           | 2          |
| left           | LEFT         | 横向左移       | 3          |
| right          | RIGHT        | 横向右移       | 4          |
| rotate_left    | ROTATE_LEFT  | 原地左旋转     | 5          |
| rotate_right   | ROTATE_RIGHT | 原地右旋转     | 6          |
| stop           | STOP         | 紧急停止       | 0          |
| background     | 无           | 背景类（自动过滤） | -        |

#### 4. ROSMASTER X3 运动状态协议（下位机标准）
- 0：停止（STOP）- 最高优先级，任何状态下接收到停止指令立即执行
- 1：前进（FORWARD）- 麦克纳姆轮Y轴正方向全向移动
- 2：后退（BACKWARD）- 麦克纳姆轮Y轴负方向全向移动
- 3：左移（LEFT）- 麦克纳姆轮X轴负方向全向移动
- 4：右移（RIGHT）- 麦克纳姆轮X轴正方向全向移动
- 5：左旋转（ROTATE_LEFT）- 原地Z轴逆时针旋转
- 6：右旋转（ROTATE_RIGHT）- 原地Z轴顺时针旋转

### 2.2 检测系统规范
- **检测目标**：7种控制手势 + 1类背景（background），共8个检测类别
- **基线模型**：YOLO11n（从零训练，mAP50=0.995，mAP50-95=0.741，Precision=0.994，Recall=1.000）
- **改进模型**：YOLO11n-ELA（最终部署模型，在Neck特征融合层引入3个ELA注意力模块，mAP50=0.995，mAP50-95=0.760，Precision=0.998，Recall=1.000，全类别零误分类）
- **默认模型路径**：`/home/jetson/ultralytics/ultralytics/best.pt`（TensorRT加速模型默认路径：`/home/jetson/ultralytics/ultralytics/best.engine`）
- **核心控制逻辑**：单帧检测到置信度≥阈值的有效手势 → 映射为对应运动指令并下发至小车；连续15帧未检测到有效手势 → 自动下发停止指令，确保系统安全
- **置信度阈值**：默认0.5，支持Web界面在线调节，调节范围0.1~0.9
- **过滤规则**：background类别自动过滤，不参与指令映射；单帧多检测结果仅取置信度最高的有效手势

---

## 三、常用命令
### 3.1 核心运行命令
```bash
# 基础运行命令（使用默认参数）
python main.py

# 带自定义参数运行（参数优先级：命令行 > 默认配置）
python main.py debug model=/path/to/custom_model.pt speed=80 port=7000 host=0.0.0.0 conf=0.6

# 调试模式运行（开启详细日志打印，不实际控制小车）
python main.py debug dry_run
```

### 3.2 数据集与模型相关命令
```bash
# 手势数据集采集（录制视频）
# 操作说明：按空格键开始/停止录制，按q键退出，视频保存至dataset/raw_videos/
python dataset/tools/collect_gesture_video.py

# 视频转训练图像数据集（自动抽帧、去重、划分训练集/验证集）
python dataset/tools/video_to_images.py

# 模型离线推理测试（本地视频/图片，支持结果可视化与保存）
python predict.py --source /path/to/test_video.mp4 --model /path/to/model.pt --save_result

# 模型导出（Jetson端侧专用：PT → ONNX → TensorRT Engine，最大化推理速度）
python kaggle/model_pt_onnx_engine.py
```

### 3.3 训练与分析命令
```bash
# 模型训练（Kaggle平台/本地GPU均可运行，支持YOLO11n与YOLO11n-ELA）
python kaggle/train.py --model yolo11-ELA.yaml --data kaggle/config.yaml --epochs 300 --batch 64

# 训练结果可视化与分析报告生成（自动生成混淆矩阵、PR曲线、损失曲线）
python training_analysis/generate_report.py --train_dir runs/detect/train/
```

### 3.4 系统与环境命令
```bash
# 检查ROSMASTER X3小车通讯状态（验证串口连接与下位机响应）
python tools/check_robot_connection.py

# 查看系统实时日志
tail -f gesture_bot.log

# 环境依赖一键安装
pip install -r requirements.txt
```

### 3.5 关键默认参数
| 参数名 | 默认值 | 可调范围 | 说明 |
|--------|--------|----------|------|
| Web服务端口 | 6500 | 1024~65535 | Web界面与API服务端口 |
| Web服务主机 | 0.0.0.0 | 合法IP地址 | 服务绑定地址，0.0.0.0允许局域网访问 |
| 小车默认速度 | 70 | 0~100 | 麦克纳姆轮运动速度百分比 |
| 摄像头分辨率 | 640x480 | 摄像头支持范围 | 视频采集分辨率 |
| YOLO推理尺寸 | 640x640 | 320~1280 | 模型输入图像尺寸，必须为32的倍数 |
| 置信度阈值 | 0.5 | 0.1~0.9 | 手势检测有效置信度下限 |
| 自动停止帧阈值 | 15 | 5~100 | 连续无有效手势自动停止的帧数 |

---

## 四、网页界面与API接口
### 4.1 标准API接口
| 接口路径 | 请求方法 | 功能说明 | 返回格式 |
|----------|----------|----------|----------|
| `/` | GET | 主控制网页界面（templates/gesture_control.html） | HTML |
| `/video_feed` | GET | MJPEG格式实时视频流（渲染后的检测结果帧） | 视频流 |
| `/api/status` | GET | 获取系统实时状态（手势结果、帧率、运动状态、参数等） | JSON |
| `/api/control` | POST | 手动提交运动控制指令 | JSON |
| `/api/settings` | POST | 在线更新运动速度、置信度阈值参数 | JSON |
| `/api/logs` | GET | 获取最近100条系统日志 | JSON |
| `/api/stop` | POST | 紧急停止指令（最高优先级，立即停止小车） | JSON |

#### 关键接口参数规范
- **POST /api/control** 请求体格式：
```json
{
  "command": "forward", // 可选值：forward/backward/left/right/rotate_left/rotate_right/stop
  "speed": 70 // 可选，速度百分比，不传则使用当前默认值
}
```
- **POST /api/settings** 请求体格式：
```json
{
  "speed": 80, // 可选，0~100
  "conf_threshold": 0.6 // 可选，0.1~0.9
}
```

### 4.2 Web控制界面核心功能
- 实时视频流显示（叠加手势检测框、类别、置信度、运动指令）
- 手势识别结果实时展示（手势类别 → 运动指令 → 置信度映射）
- 7种运动状态的手动控制按钮（支持鼠标点击/触屏操作）
- 系统状态实时监控（推理帧率、当前置信度、检测次数、运动状态）
- 速度与置信度阈值在线调节滑块（实时生效，无需重启系统）
- 手势-指令对照表
- 系统滚动日志实时显示
- 紧急停止按钮（页面置顶，最高优先级）

---

## 五、开发说明
### 5.1 线程安全规范
- 所有全局共享状态的读写，必须通过`SystemState`类封装的方法执行，禁止直接修改共享变量
- 所有共享状态的更新操作，必须使用`threading.Lock`互斥锁保护，避免多线程竞争导致的数据异常
- 视频帧的读取必须通过线程安全的`get_latest_frame()`方法执行，禁止直接访问帧缓存变量
- 日志写入必须通过`SimpleLogger`类的线程安全方法执行，禁止直接操作日志文件
- 小车控制指令的下发必须加锁，避免多线程同时下发指令导致的下位机通讯异常

### 5.2 ROSMASTER X3 机器人初始化与通讯流程
#### 标准初始化流程（不可调整顺序）
1. 创建Rosmaster库实例，绑定串口设备（默认`/dev/ttyUSB0`，波特率115200）
2. 启动下位机串口接收线程，建立上下位机全双工通讯
3. 设置小车类型为ROSMASTER X3，加载对应运动学模型
4. 初始化`X3WheelController`车轮控制器，绑定运动状态与速度参数
5. 连续3次下发停止指令，确保小车初始状态为安全停止
6. 读取下位机电池电量、固件版本等状态，验证通讯正常

#### 上下位机通讯核心逻辑
- 物理链路：Jetson Orin USB口 ↔ ROSMASTER X3扩展板microUSB串口 ↔ STM32下位机
- 协议层：基于Rosmaster_Lib封装的标准串口协议，自动处理指令封装、校验、重发
- 指令下发：上位机将运动指令封装为串口数据帧，通过USB串口下发至STM32，STM32解析后执行电机控制
- 状态回传：STM32实时采集编码器、IMU、电池电量等数据，回传至上位机，用于状态监控与异常处理

### 5.3 视频处理与推理主流程（单帧循环）
1. 从USB摄像头捕获一帧RGB图像，做基础预处理（畸变校正、尺寸归一化）
2. 将图像输入YOLO模型执行端侧推理，输出检测框、类别、置信度结果
3. 过滤background类别与低于置信度阈值的结果，取置信度最高的有效手势
4. 通过`GESTURE_TO_MOTION`字典映射为对应运动指令，通过`X3WheelController`下发至小车
5. 在原始帧上绘制检测框、手势名称、运动指令、置信度、帧率等视觉反馈信息
6. 将渲染后的帧存入线程安全的帧缓存，用于Web界面视频流传输
7. 统计连续无有效手势的帧数，达到阈值则自动下发停止指令
8. 异常捕获：推理失败、摄像头读取失败、小车通讯失败时，立即下发停止指令，记录错误日志

### 5.4 仓库核心文件说明
| 文件路径 | 功能说明 |
|----------|----------|
| `main.py` | 项目主入口，包含`GestureControlSystem`主系统类、线程初始化、主循环逻辑 |
| `controller/wheel_controller.py` | `X3WheelController`运动控制器实现，封装小车通讯与运动控制逻辑 |
| `system/state.py` | `SystemState`线程安全状态管理类实现 |
| `system/logger.py` | `SimpleLogger`线程安全日志类实现 |
| `templates/gesture_control.html` | Web控制界面前端模板 |
| `app/web_app.py` | Flask Web应用与API接口实现 |
| `predict.py` | 模型离线推理测试脚本 |
| `kaggle/train.py` | YOLO11n/YOLO11n-ELA模型训练脚本 |
| `kaggle/config.yaml` | 数据集路径、训练超参数配置文件 |
| `kaggle/model_pt_onnx_engine.py` | Jetson端模型导出脚本（PT→ONNX→TensorRT Engine） |
| `dataset/tools/` | 数据集采集、预处理、格式转换工具目录 |
| `training_analysis/` | 模型训练结果分析脚本、报告模板、可视化代码 |
| `ultralytics/nn/modules/ela.py` | ELA高效局部注意力模块PyTorch实现 |
| `ultralytics/cfg/models/11/yolo11-ELA.yaml` | YOLO11n-ELA改进模型架构配置文件 |
| `requirements.txt` | 项目全量依赖包与版本要求 |
| `.vscode/settings.json` | VS Code开发环境配置、Conda环境路径配置 |

---

## 六、模型改进：YOLO11n-ELA
### 6.1 改进方案
在原生YOLO11n轻量化模型的**Neck特征融合层**中，引入3个ELA（Efficient Local Attention）高效局部注意力模块，在不修改Backbone主干网络的前提下，最小化参数量增量，最大化模型检测性能提升。
- ELA模块代码路径：`ultralytics/nn/modules/ela.py`
- 改进模型架构配置：`ultralytics/cfg/models/11/yolo11-ELA.yaml`
- 模块插入位置：Neck层3个特征融合点（Concat拼接操作之后、C3k2模块之前），每个融合点插入1个ELA层
- 核心设计：仅修改Neck层，Backbone主干网络完全保持原生YOLO11n不变，最大化兼容原生模型的预训练权重与推理优化

### 6.2 ELA模块核心原理
ELA（Efficient Local Attention）是针对现有注意力机制的缺陷提出的轻量化高效局部注意力方案，出自论文《ELA: Efficient Local Attention for Deep Convolutional Neural Networks》（arXiv:2403.01123），核心原理如下：
1. **针对的核心问题**：针对Coordinate Attention等现有空间注意力机制的三大缺陷：Batch Normalization的泛化能力不足、通道降维对通道注意力带来的负面效果、注意力生成过程复杂度高
2. **核心实现**：通过两组1D卷积分别沿空间X、Y维度编码特征图，结合Group Normalization（组归一化）做特征增强，无需通道降维即可高效编码双向位置特征，精准定位感兴趣区域
3. **轻量化优势**：无通道降维，保留完整的特征信息；结构简单，参数增量极小，推理开销几乎可忽略；支持无缝嵌入ResNet、MobileNet、YOLO等主流CNN网络
4. **版本适配**：本项目使用ELA-S版本，平衡参数量与性能，适配Jetson端侧实时推理场景

### 6.3 ELA模块Ultralytics注册规范
ELA模块已完整注册到Ultralytics框架的模块系统中，支持直接在yaml配置文件中调用，无需额外修改推理逻辑：
1. `ultralytics/nn/modules/__init__.py`：导出ELA类，加入模块导出列表
2. `ultralytics/nn/tasks.py`：导入ELA类，在parse_model函数中添加ELA模块的解析处理逻辑
3. 调用方式：在yaml配置文件中，直接通过`[-1, 1, ELA, [in_channels]]`格式调用

### 6.4 最终模型性能对比
| 指标 | YOLO11n（基线模型） | YOLO11n-ELA（改进模型） | 变化幅度 |
|------|----------------------|-------------------------|----------|
| 网络层数 | 319 | 334 | +15层 |
| 参数量 | 2.62M | 6.13M | +3.51M |
| GFLOPs | 6.6 | 13.7 | +7.1 |
| Precision（精确率） | 0.994 | 0.998 | +0.4% |
| Recall（召回率） | 1.000 | 1.000 | 持平 |
| mAP50 | 0.995 | 0.995 | 持平 |
| mAP50-95 | 0.741 | 0.760 | +1.9% |
| 训练集box_loss | 0.792 | 0.733 | 下降7.45% |
| 训练集cls_loss | 0.443 | 0.407 | 下降8.13% |
| 验证集box_loss | 0.968 | 0.933 | 下降3.62% |
| 验证集cls_loss | 0.468 | 0.457 | 下降2.35% |
| 混淆矩阵误分类数 | 5例 | 0例 | 完全消除误分类 |

### 6.5 训练配置规范
- 训练平台：Kaggle（2× Tesla T4 16G GPU）
- 训练框架：Ultralytics 8.x
- Batch Size：64
- 输入图像尺寸：640×640
- 预设训练轮次：300
- 实际训练轮次：基线模型160轮（早停），改进模型164轮（早停）
- Early Stopping Patience：50轮（验证集mAP50-95连续50轮无提升则停止训练）
- 优化器：AdamW
- 学习率策略：余弦退火学习率
- 数据增强：Mosaic、MixUp、随机翻转、随机缩放、亮度/对比度扰动
- 训练脚本：`kaggle/train.py`，通过`--model`参数切换基线模型与改进模型

---

## 七、依赖包与版本要求
| 依赖包 | 版本要求 | 功能说明 |
|--------|----------|----------|
| ultralytics | ≥8.2.0 | YOLO模型训练、推理、导出核心库 |
| torch | ≥2.0.0 | PyTorch深度学习框架，匹配Jetson JetPack版本 |
| torchvision | ≥0.15.0 | 图像处理与预训练模型库 |
| Flask | ≥2.3.0 | Web框架，提供界面与API服务 |
| gevent | ≥23.9.0 | 异步协程库，提升Web服务并发能力 |
| opencv-python | ≥4.8.0 | OpenCV图像处理、摄像头采集库 |
| numpy | ≥1.24.0 | 数值计算与数组处理 |
| Rosmaster_Lib | ≥1.0.0 | 亚博智能ROSMASTER X3机器人官方控制库 |
| pyserial | ≥3.5 | 串口通讯库，用于小车上下位机通讯 |
| tensorrt | ≥8.5.0 | Jetson端TensorRT推理加速库 |
| onnx | ≥1.14.0 | 模型格式转换中间件 |
| onnxruntime | ≥1.15.0 | ONNX模型推理引擎 |
| matplotlib | ≥3.7.0 | 训练结果可视化、混淆矩阵绘制 |
| pandas | ≥2.0.0 | 训练日志处理与数据分析 |
| scikit-learn | ≥1.2.0 | 混淆矩阵、PR曲线计算 |

> 完整依赖清单与版本锁定见仓库根目录`requirements.txt`，执行`pip install -r requirements.txt`可一键安装。

---

## 八、环境配置
### 8.1 核心环境说明
- 上位机硬件：Jetson Orin NX/Nano 系列开发板
- 操作系统：Ubuntu 20.04/22.04（匹配JetPack版本）
- 深度学习环境：JetPack 5.1.2+（自带CUDA、cuDNN、TensorRT）
- Python版本：3.10+
- 环境管理：Miniconda3（Conda环境配置见`.vscode/settings.json`）
- 小车硬件：ROSMASTER X3 全向移动机器人（带USB扩展板、USB摄像头）

### 8.2 环境部署步骤
1. 安装JetPack系统，配置CUDA、cuDNN、TensorRT环境，验证GPU可用
2. 安装Miniconda3，创建项目专属Conda环境，激活环境
3. 克隆本仓库至`/home/jetson/`目录，进入仓库根目录
4. 执行`pip install -r requirements.txt`安装所有Python依赖
5. 安装ROSMASTER X3官方Rosmaster_Lib库，配置串口权限（`sudo usermod -aG dialout $USER`）
6. 连接小车USB串口与USB摄像头，执行`python tools/check_robot_connection.py`验证小车通讯正常
7. 执行`python main.py`启动系统，访问`http://<Jetson_IP>:6500`验证Web界面与功能正常

### 8.3 关键配置说明
- 串口设备：ROSMASTER X3默认串口设备为`/dev/ttyUSB0`，波特率115200，可在`controller/wheel_controller.py`中修改
- 摄像头设备：默认使用`/dev/video0`，可在`main.py`中通过`camera_id`参数修改
- 模型路径：默认加载`/home/jetson/ultralytics/ultralytics/best.pt`，可通过命令行`model`参数自定义
- 局域网访问：Web服务默认绑定`0.0.0.0`，同一局域网内设备可通过Jetson的IP地址访问控制界面

---

## 九、手势类别规范
系统支持识别7种标准控制手势，与运动指令一一对应，无歧义，具体规范如下：
| 手势类别       | 对应运动指令 | 手势动作说明 |
|----------------|--------------|--------------|
| forward        | 前进         | 单手手掌向前伸直，正对摄像头 |
| backward       | 后退         | 单手手掌向后摆动，手背正对摄像头 |
| left           | 左移         | 单手手掌向左侧平伸，掌心朝向左侧 |
| right          | 右移         | 单手手掌向右侧平伸，掌心朝向右侧 |
| rotate_left    | 原地左旋转   | 单手竖起食指，向逆时针方向画圈 |
| rotate_right   | 原地右旋转   | 单手竖起食指，向顺时针方向画圈 |
| stop           | 停止         | 单手手掌向上竖起，掌心正对摄像头（停止手势） |
| background     | 无           | 无手势的背景画面，自动过滤 |

---

## 十、核心安全机制
1. **最高优先级停止机制**：stop指令为最高优先级，任何状态下接收到stop手势/手动停止指令/紧急停止API调用，立即停止小车，清空运动状态
2. **超时自动停止机制**：连续15帧未检测到有效手势，自动下发停止指令，避免手势丢失导致的小车失控
3. **异常安全机制**：摄像头读取失败、模型推理异常、小车串口通讯中断时，立即触发停止指令，记录错误日志，禁止下发任何运动指令
4. **速度限制机制**：最大速度限制为100%，默认速度70%，避免速度过快导致的失控风险
5. **指令防抖机制**：连续2帧检测到同一手势才下发对应运动指令，避免单帧误检导致的小车误动作
6. **串口通讯校验机制**：所有下发至下位机的指令均带校验位，校验失败的指令不执行，自动重发3次，仍失败则触发停止

---

## 十一、常见问题排查
| 问题现象 | 排查方向 | 解决方案 |
|----------|----------|----------|
| 小车无响应，无法控制 | 1. 串口设备是否正确；2. 扩展板开关是否打开；3. 串口权限是否配置；4. 小车是否上电 | 1. 检查`/dev/ttyUSB0`设备是否存在；2. 打开扩展板电源开关；3. 执行`sudo usermod -aG dialout $USER`并重启；4. 检查小车电池电量 |
| 模型加载失败，推理报错 | 1. 模型路径是否正确；2. PyTorch版本是否匹配；3. 模型文件是否损坏；4. TensorRT引擎是否与JetPack版本匹配 | 1. 确认模型路径正确；2. 重新安装匹配的PyTorch版本；3. 重新导出模型文件；4. 在Jetson本地重新生成TensorRT引擎 |
| Web界面无法访问 | 1. 服务是否正常启动；2. 端口是否被占用；3. 防火墙是否放行端口；4. 主机IP是否正确 | 1. 检查服务启动日志，确认无报错；2. 修改端口号，避免端口占用；3. 关闭防火墙或放行对应端口；4. 确认Jetson的局域网IP地址 |
| 摄像头无法读取，无视频流 | 1. 摄像头是否正确连接；2. 摄像头设备号是否正确；3. 摄像头权限是否配置；4. OpenCV是否正确安装 | 1. 重新拔插USB摄像头；2. 修改`camera_id`参数匹配正确设备号；3. 执行`sudo chmod 777 /dev/video0`；4. 重新安装OpenCV |
| 手势误检/漏检严重 | 1. 置信度阈值是否过低/过高；2. 光线是否充足；3. 手势是否在摄像头画面中心；4. 模型是否为最终改进版 | 1. 调整置信度阈值至0.5~0.7；2. 保证光线充足，避免逆光；3. 手势保持在画面中心，动作标准；4. 切换至YOLO11n-ELA改进模型 |

---

