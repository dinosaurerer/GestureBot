#!/usr/bin/env python3
# coding=utf-8
# 测试文件 - 使用 YOLO11n.pt 检测 orange 控制小车前进
# 基于 YOLO 的人车运动交互控制系统 - 毕业设计测试版
# 适配 Rosmaster X3 车型

import cv2 as cv
import time
import os
import threading
from datetime import datetime

from flask import Flask, render_template, Response, jsonify
from gevent import pywsgi

from Rosmaster_Lib import Rosmaster

# 导入 YOLO 模型
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("Warning: YOLO not available. Install with: pip install ultralytics")
    YOLO_AVAILABLE = False


# ========== X3 轮子控制器 ==========
class X3WheelController:
    """Rosmaster X3 运动控制器 - 使用 set_car_run 方法"""

    def __init__(self, bot, speed_percent=70):
        self.__bot = bot
        self.__speed_percent = speed_percent
        self.__car_stabilize_state = 0  # 自稳状态，0=关闭，1=开启

        # 运动模式定义 - 参考 rosmaster_main.py 中的 ctrl_car_x3
        # state: 0=停止, 1=前进, 2=后退, 3=左移, 4=右移, 5=左旋转, 6=右旋转
        self.__motion_states = {
            "STOP":        0,
            "FORWARD":     1,
            "BACKWARD":    2,
            "LEFT":        3,
            "RIGHT":       4,
            "ROTATE_LEFT": 5,
            "ROTATE_RIGHT": 6,
        }

        # 速度定义 - 参考官方代码 g_speed_ctrl_xy 和 g_speed_ctrl_z
        self.__motion_speeds = {
            "FORWARD":     70,     # 前进速度
            "BACKWARD":    70,     # 后退速度
            "LEFT":        50,     # 左移速度
            "RIGHT":       50,     # 右移速度
            "ROTATE_LEFT": 60,     # 左旋转速度
            "ROTATE_RIGHT": 60,     # 右旋转速度
        }

    def set_speed_percent(self, speed):
        self.__speed_percent = max(0, min(100, speed))
        print(f"Speed set to: {self.__speed_percent}%")
        # 更新运动速度
        for key in self.__motion_speeds:
            if key != "FORWARD" and key != "BACKWARD":
                self.__motion_speeds[key] = int(self.__speed_percent * 0.5)
            else:
                self.__motion_speeds[key] = int(self.__speed_percent * 0.7)

    def get_speed_by_percent(self, motion_name, custom_speed=None):
        if custom_speed is not None:
            return int(custom_speed)
        return int(self.__motion_speeds[motion_name] * custom_speed / 100) if custom_speed else self.__motion_speeds[motion_name]

    def execute(self, motion_name, custom_speed=None):
        if motion_name not in self.__motion_states:
            print(f"Unknown motion mode: {motion_name}")
            return None

        state = self.__motion_states[motion_name]

        if motion_name == "STOP":
            # 停止
            self.__bot.set_car_run(0, self.__car_stabilize_state)
            print(f"Execute: {motion_name}")
            return {"state": state, "speed": 0}
        else:
            # 运动
            if custom_speed is not None:
                speed = max(0, min(100, custom_speed))
            else:
                speed = self.__motion_speeds[motion_name]

            self.__bot.set_car_run(state, speed, self.__car_stabilize_state)
            print(f"Execute: {motion_name} | state={state}, speed={speed}")
            return {"state": state, "speed": speed}

    def stop(self):
        self.execute("STOP")

    def set_stabilize(self, enable):
        """设置自稳开关"""
        self.__car_stabilize_state = 1 if enable else 0
        print(f"Stabilize: {'ON' if enable else 'OFF'}")


# ========== 系统状态管理 ==========
class SystemState:
    """系统状态管理"""

    def __init__(self):
        self.__lock = threading.Lock()
        self.__current_gesture = "STOP"
        self.__confidence = 0.0
        self.__fps = 0
        self.__motion_state = 0
        self.__motion_speed = 0
        self.__speed_percent = 70
        self.__model_loaded = False
        self.__total_detections = 0
        self.__detection_target = "orange"
        self.__orange_detected = False

    def update_orange_detected(self, detected, confidence=0.0):
        """更新 orange 检测状态"""
        with self.__lock:
            self.__orange_detected = detected
            # 只在检测到时更新置信度，否则保持上次的值
            if detected:
                self.__confidence = confidence
                # 只有置信度超过阈值才增加检测次数
                if confidence > 0.5:
                    self.__current_gesture = "FORWARD"
                    self.__total_detections += 1
                else:
                    self.__current_gesture = "STOP"
            else:
                self.__current_gesture = "STOP"
                # 未检测到时，不重置置信度，保持上次的检测置信度

    def update_fps(self, fps):
        with self.__lock:
            self.__fps = fps

    def update_motion_status(self, motion_info):
        """更新运动状态"""
        with self.__lock:
            if motion_info:
                self.__motion_state = motion_info.get("state", 0)
                self.__motion_speed = motion_info.get("speed", 0)

    def set_speed_percent(self, speed):
        with self.__lock:
            self.__speed_percent = speed

    def set_model_info(self, loaded):
        with self.__lock:
            self.__model_loaded = loaded

    def get(self):
        with self.__lock:
            return {
                "current_gesture": self.__current_gesture,
                "detection_target": self.__detection_target,
                "orange_detected": self.__orange_detected,
                "confidence": round(self.__confidence, 2),
                "fps": round(self.__fps, 1),
                "motion_state": self.__motion_state,
                "motion_speed": self.__motion_speed,
                "speed_percent": self.__speed_percent,
                "model_loaded": self.__model_loaded,
                "total_detections": self.__total_detections,
            }


# 全局状态
system_state = SystemState()


# ========== Orange 检测控制系统 ==========
class OrangeDetectControlSystem:
    """Orange 检测控制系统 - Rosmaster X3 适配版"""

    # YOLO11 模型的类别
    # YOLO11n.pt 包含 80 个 COCO 类别
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]

    # orange 在 COCO 类别中的索引
    ORANGE_CLASS_ID = 49  # 'orange' 在列表中的索引

    MOTION_DESCRIPTIONS = {
        "STOP":        {"zh": "停止",       "desc": "Stop"},
        "FORWARD":     {"zh": "前进",       "desc": "Move Forward"},
        "BACKWARD":    {"zh": "后退",       "desc": "Move Backward"},
        "LEFT":        {"zh": "左移",       "desc": "Move Left"},
        "RIGHT":       {"zh": "右移",       "desc": "Move Right"},
        "ROTATE_LEFT": {"zh": "左旋转",     "desc": "Rotate Left"},
        "ROTATE_RIGHT": {"zh": "右旋转",     "desc": "Rotate Right"},
    }

    def __init__(self, model_path="yolo11n.pt", speed_percent=70, debug=False):
        self.__debug = debug
        self.__speed_percent = speed_percent
        self.__conf_threshold = 0.5

        self.__current_action = "STOP"
        self.__last_action = "STOP"
        self.__no_detect_count = 0
        self.__max_no_detect = 15  # 连续多少帧无检测则停止
        self.__last_execute_time = 0
        self.__min_execute_interval = 0.1

        # 加载 YOLO11n 模型
        self.__model = None
        if YOLO_AVAILABLE:
            self.__load_yolo_model(model_path)

        # 初始化小车
        self.__bot = None
        self.__wheel_controller = None
        self.__init_bot()

        # 初始化摄像头
        self.__camera = None
        self.__init_camera()

        # 控制状态
        self.__running = True
        self.__latest_frame = None

    def __load_yolo_model(self, model_path):
        """加载 YOLO 模型"""
        try:
            # 加载 YOLO11n 模型
            self.__model = YOLO(model_path)
            logger.info(f"YOLO model loaded: {model_path}")
            system_state.set_model_info(True)
        except Exception as e:
            logger.error(f"YOLO model load failed: {e}")
            system_state.set_model_info(False)

    def __init_bot(self):
        """初始化小车 - 适配 Rosmaster X3"""
        try:
            self.__bot = Rosmaster(debug=self.__debug)
            # 先创建接收线程（参考官方代码顺序）
            self.__bot.create_receive_threading()
            time.sleep(0.1)

            # 设置为 X3 车型
            self.__bot.set_car_type(self.__bot.CARTYPE_X3)
            time.sleep(0.1)

            # 创建 X3 控制器
            self.__wheel_controller = X3WheelController(
                self.__bot,
                speed_percent=self.__speed_percent
            )
            system_state.set_speed_percent(self.__speed_percent)

            # 发送停止指令确保初始状态正确
            self.__wheel_controller.stop()
            time.sleep(0.1)

            logger.info("Bot initialized (Rosmaster X3)")
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")

    def __init_camera(self):
        """初始化摄像头 - 使用 cv2.VideoCapture"""
        try:
            self.__camera = cv.VideoCapture(0)
            self.__camera.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            self.__camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
            logger.info("USB camera initialized")
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")

    def set_speed(self, speed):
        """设置速度"""
        self.__speed_percent = max(0, min(100, speed))
        if self.__wheel_controller:
            self.__wheel_controller.set_speed_percent(speed)
        system_state.set_speed_percent(speed)

    def set_conf_threshold(self, threshold):
        """设置置信度阈值"""
        self.__conf_threshold = max(0.1, min(1.0, threshold))
        logger.info(f"Confidence threshold set: {self.__conf_threshold}")

    def execute_motion(self, motion_name):
        """执行运动指令"""
        if self.__wheel_controller is None:
            logger.info(f"[Simulate] Execute: {motion_name}")
            return None

        motion_info = self.__wheel_controller.execute(motion_name)
        system_state.update_motion_status(motion_info)
        self.__last_execute_time = time.time()
        return motion_info

    def detect_orange(self, frame):
        """
        检测 orange

        Args:
            frame: 摄像头画面

        Returns:
            detected: 是否检测到 orange
            confidence: 置信度
            annotated_frame: 标注后的画面
        """
        if self.__model is None:
            return False, 0.0, frame

        try:
            # YOLO 推理
            results = self.__model(frame, verbose=False)

            # 可视化检测结果
            annotated_frame = results[0].plot()

            # 检查是否检测到 orange
            detected = False
            max_confidence = 0.0

            if len(results) > 0 and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])

                    # 检查是否是 orange 类别 (ID=49)
                    if cls_id == self.ORANGE_CLASS_ID:
                        detected = True
                        if conf > max_confidence:
                            max_confidence = conf

            return detected, max_confidence, annotated_frame

        except Exception as e:
            logger.error(f"Orange detection error: {e}")
            return False, 0.0, frame

    def process_frame(self, frame):
        """
        处理单帧画面，检测 orange 并执行控制

        Args:
            frame: 输入画面

        Returns:
            annotated_frame: 标注后的画面
        """
        # 检测 orange
        detected, confidence, annotated_frame = self.detect_orange(frame)

        # 绘制系统标题 (使用英文避免中文乱码)
        cv.putText(annotated_frame, "Orange Detection - Rosmaster X3",
                  (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        current_time = time.time()
        time_since_last = current_time - self.__last_execute_time

        if detected and confidence > self.__conf_threshold:
            # 检测到 orange
            self.__current_action = "FORWARD"
            system_state.update_orange_detected(True, confidence)
            self.__no_detect_count = 0

            if (self.__current_action != self.__last_action or
                time_since_last >= self.__min_execute_interval):
                self.execute_motion("FORWARD")
                self.__last_action = self.__current_action
        else:
            # 未检测到 orange
            self.__no_detect_count += 1
            if self.__no_detect_count >= self.__max_no_detect:
                # 连续多帧无检测，停止小车
                if self.__current_action != "STOP":
                    self.execute_motion("STOP")
                    self.__current_action = "STOP"
                    self.__last_action = "STOP"
                    system_state.update_orange_detected(False, 0)

        # 绘制检测状态 (使用英文)
        if self.__current_action != "STOP":
            status_text = f"Orange Detected! (Conf: {confidence:.2f}) | Moving Forward"
            status_color = (0, 255, 0)
            # 绘制绿色边框表示检测
            cv.rectangle(annotated_frame, (5, 40),
                       (annotated_frame.shape[1] - 5, 75),
                       (0, 255, 0), 2)
        else:
            status_text = "Waiting for Orange Detection..."
            status_color = (0, 100, 255)

        cv.putText(annotated_frame, status_text,
                  (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        # 绘制速度信息
        cv.putText(annotated_frame, f"Speed: {self.__speed_percent}%",
                  (annotated_frame.shape[1] - 150, 30),
                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

        # 绘制阈值信息
        cv.putText(annotated_frame, f"Thresh: {self.__conf_threshold}",
                  (annotated_frame.shape[1] - 150, 60),
                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (200, 150, 0), 2)

        # 保存最新帧
        self.__latest_frame = annotated_frame

        return annotated_frame

    def stop(self):
        """停止系统"""
        self.__running = False
        if self.__wheel_controller:
            self.__wheel_controller.stop()
        if self.__bot:
            self.__bot.set_beep(100)
        if self.__camera:
            self.__camera.release()


# ========== 简单日志系统 ==========
class SimpleLogger:
    def __init__(self, max_logs=50):
        self.__logs = []
        self.__lock = threading.Lock()
        self.__max_logs = max_logs

    def add(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "time": timestamp,
            "level": level,
            "message": message
        }
        with self.__lock:
            self.__logs.append(log_entry)
            if len(self.__logs) > self.__max_logs:
                self.__logs.pop(0)
        print(f"[{timestamp}] [{level}] {message}")

    def info(self, message):
        self.add("INFO", message)

    def warning(self, message):
        self.add("WARNING", message)

    def error(self, message):
        self.add("ERROR", message)

    def get_all(self):
        with self.__lock:
            return list(self.__logs)


logger = SimpleLogger()


# ========== Flask Web 应用 ==========
app = Flask(__name__)

# 全局控制实例
control_system = None


@app.route('/')
def index():
    """主页面"""
    return render_template('test_orange.html')


@app.route('/video_feed')
def video_feed():
    """视频流"""
    def generate():
        m_fps = 0
        t_start = time.time()

        while control_system and control_system._OrangeDetectControlSystem__running:
            success, frame = control_system._OrangeDetectControlSystem__camera.read()
            if success:
                annotated_frame = control_system.process_frame(frame)

                # 计算FPS
                m_fps += 1
                fps = m_fps / (time.time() - t_start)
                system_state.update_fps(fps)

                # 编码为JPEG
                ret, img_encode = cv.imencode('.jpg', annotated_frame)
                if ret:
                    img_bytes = img_encode.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
            else:
                time.sleep(0.1)

    return Response(generate(),
                mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        "success": True,
        "data": system_state.get()
    })


@app.route('/api/control', methods=['POST'])
def control_robot():
    """手动控制机器人"""
    from flask import request
    data = request.json
    action = data.get('action')

    if action == 'stop':
        control_system.execute_motion("STOP")
        logger.info("Web manual control: Stop")
    elif action in OrangeDetectControlSystem.MOTION_DESCRIPTIONS:
        control_system.execute_motion(action)
        logger.info(f"Web manual control: {action}")
    else:
        return jsonify({"success": False, "message": "Unknown command"})

    return jsonify({"success": True, "action": action})


@app.route('/api/settings', methods=['POST', 'GET'])
def settings():
    """参数设置"""
    from flask import request
    if request.method == 'POST':
        data = request.json
        speed = data.get('speed')
        threshold = data.get('threshold')

        if speed is not None:
            control_system.set_speed(int(speed))
        if threshold is not None:
            control_system.set_conf_threshold(float(threshold))

        return jsonify({"success": True, "message": "Settings updated"})

    return jsonify({"success": True})


@app.route('/api/logs')
def get_logs():
    """获取日志"""
    return jsonify({
        "success": True,
        "data": logger.get_all()
    })


def start_web_server(host='0.0.0.0', port=6500):
    """启动 Web 服务器"""
    logger.info(f"Web server starting: http://{host}:{port}")
    try:
        server = pywsgi.WSGIServer((host, port), app)
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Web server stopped")


# ========== 主程序 ==========
def main():
    import sys

    # 默认使用 YOLO11n.pt
    model_path = "/home/jetson/ultralytics/ultralytics/yolo11n.pt"
    speed_percent = 70
    debug = False
    web_host = '0.0.0.0'
    web_port = 6500

    for arg in sys.argv[1:]:
        if arg == "debug":
            debug = True
        elif arg.startswith("model="):
            model_path = arg.split("=")[1]
        elif arg.startswith("speed="):
            speed_percent = int(arg.split("=")[1])
        elif arg.startswith("port="):
            web_port = int(arg.split("=")[1])
        elif arg.startswith("host="):
            web_host = arg.split("=")[1]

    print("\n" + "="*60)
    print("    Orange Detection - Rosmaster X3 Web Control")
    print("="*60)
    print(f"Web URL: http://{web_host}:{web_port}")
    print(f"Model: YOLO11n.pt")
    print(f"Detection Target: Orange (Class ID: {OrangeDetectControlSystem.ORANGE_CLASS_ID})")
    print(f"Speed: {speed_percent}%")
    print("="*60 + "\n")

    global control_system
    control_system = OrangeDetectControlSystem(
        model_path=model_path,
        speed_percent=speed_percent,
        debug=debug
    )

    # 启动提示音
    if control_system._OrangeDetectControlSystem__bot:
        for i in range(2):
            control_system._OrangeDetectControlSystem__bot.set_beep(50)
            time.sleep(0.2)

    # 启动 Web 服务器线程
    web_thread = threading.Thread(target=start_web_server,
                              args=(web_host, web_port),
                              daemon=True)
    web_thread.start()

    # 主循环
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        control_system.stop()
        print("\nSystem stopped")


if __name__ == '__main__':
    main()
