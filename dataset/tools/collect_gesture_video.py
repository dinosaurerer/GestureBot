import cv2
import os
import sys
import time
from pathlib import Path
import threading
from queue import Queue

# 手势类别定义
GESTURE_CLASSES = {
    'FORWARD': '前进',
    'BACKWARD': '后退',
    'LEFT': '左移',
    'RIGHT': '右移',
    'ROTATE_LEFT': '左旋转',
    'ROTATE_RIGHT': '右旋转',
    'STOP': '停止'
}


class KeyboardListener(threading.Thread):
    """独立线程监听键盘输入，避免阻塞主线程"""

    def __init__(self):
        super().__init__(daemon=True)
        self.key_queue = Queue()
        self.running = True

    def run(self):
        """在独立线程中监听键盘输入"""
        import termios
        import tty
        import select

        try:
            settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())

            while self.running:
                # 使用较长的超时时间，减少CPU占用
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    key = sys.stdin.read(1)
                    self.key_queue.put(key)
                time.sleep(0.01)  # 额外休眠，减少CPU占用

        except Exception as e:
            pass
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

    def get_key(self):
        """获取按键（非阻塞）"""
        try:
            return self.key_queue.get_nowait()
        except:
            return None

    def stop(self):
        """停止监听"""
        self.running = False


def wait_for_user_choice(prompt, options):
    """等待用户选择"""
    while True:
        print(f"\n{prompt} (选项: {'/'.join(options)}): ", end='', flush=True)
        time.sleep(0.1)


def main():
    # 输出目录
    output_dir = Path("ges_data_opt")
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("手势数据集视频采集工具")
    print("=" * 60)
    print("\n操作说明:")
    print("  [空格键] 开始/停止录制")
    print("  [q 键]    退出程序")
    print("=" * 60)

    # 启动键盘监听线程
    keyboard = KeyboardListener()
    keyboard.start()

    # 打开摄像头
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("错误: 无法打开摄像头！")
        keyboard.stop()
        return

    # 设置摄像头分辨率（关键优化！）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"\n摄像头信息: {width}x{height} @ {fps}fps")

    # 为每个类别创建文件夹
    for class_name in GESTURE_CLASSES.keys():
        (output_dir / class_name.lower()).mkdir(exist_ok=True)

    current_class_idx = 0
    class_names = list(GESTURE_CLASSES.keys())

    # 设置窗口位置和大小
    cv2.namedWindow("手势数据采集", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("手势数据采集", 640, 480)

    try:
        while True:
            class_name = class_names[current_class_idx]
            class_cn = GESTURE_CLASSES[class_name]

            # 显示当前采集提示
            print(f"\n{'=' * 60}")
            print(f"当前类别: [{class_name}] - {class_cn}")
            print(f"进度: {current_class_idx + 1}/{len(class_names)}")
            print("=" * 60)
            print("\n请做出对应的手势，然后按下 [空格键] 开始录制...")
            print("选择(Y/N): ", end='', flush=True)

            recording = False
            video_writer = None
            video_count = 0
            waiting_for_choice = False

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("错误: 无法读取摄像头画面！")
                    break

                # 显示提示信息
                if recording:
                    # 录制中：显示红色 REC 标志
                    cv2.rectangle(frame, (10, 10), (160, 50), (0, 0, 255), -1)
                    cv2.putText(frame, "REC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                               1.5, (255, 255, 255), 2)

                    status_text = f"录制中... [{class_cn}] - 按[空格]停止"
                    color = (0, 0, 255)
                else:
                    # 等待中
                    status_text = f"准备录制 [{class_cn}] - 按[空格]开始 | 按[q]退出"
                    color = (0, 255, 0)

                cv2.putText(frame, status_text, (10, height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                cv2.imshow("手势数据采集", frame)

                # 检测按键（从队列获取）
                key = keyboard.get_key()

                if key == 'q' or key == 'Q':
                    print("\n用户退出程序。")
                    keyboard.stop()
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                if key == ' ':
                    if recording:
                        # 停止录制
                        recording = False
                        if video_writer is not None:
                            video_writer.release()
                            video_writer = None

                        video_count += 1
                        print(f"\n视频已保存: {class_name.lower()}_{video_count:02d}.mp4")
                        waiting_for_choice = True

                        # 继续显示画面，等待用户输入
                        while waiting_for_choice:
                            ret, frame = cap.read()
                            if ret:
                                cv2.putText(frame, f"继续采集当前类别? (Y/N)", (10, height - 20),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                                cv2.imshow("手势数据采集", frame)

                            key = keyboard.get_key()

                            if key == 'q' or key == 'Q':
                                print("\n用户退出程序。")
                                keyboard.stop()
                                cap.release()
                                cv2.destroyAllWindows()
                                return

                            if key == 'y' or key == 'Y':
                                print("Y - 继续采集当前类别...")
                                waiting_for_choice = False
                            elif key == 'n' or key == 'N':
                                print("N - 跳到下一个类别")
                                waiting_for_choice = False
                                current_class_idx += 1
                                if current_class_idx >= len(class_names):
                                    print("\n" + "=" * 60)
                                    print("所有类别采集完成！")
                                    print("=" * 60)
                                    keyboard.stop()
                                    cap.release()
                                    cv2.destroyAllWindows()
                                    return
                                break  # 退出内层循环，切换到下一个类别

                            # ESC 退出
                            if cv2.waitKey(1) & 0xFF == 27:
                                print("\n用户退出程序。")
                                keyboard.stop()
                                cap.release()
                                cv2.destroyAllWindows()
                                return

                    else:
                        # 开始录制
                        video_count += 1
                        video_path = output_dir / class_name.lower() / f"{class_name.lower()}_{video_count:02d}.mp4"

                        # 创建视频写入器
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_writer = cv2.VideoWriter(
                            str(video_path), fourcc, fps, (width, height)
                        )

                        recording = True
                        print(f"\n开始录制: {video_path.name}")
                        print("录制中... 按[空格]停止录制")

                if recording and video_writer is not None:
                    video_writer.write(frame)

                # ESC 退出
                if cv2.waitKey(1) & 0xFF == 27:
                    print("\n用户退出程序。")
                    keyboard.stop()
                    cap.release()
                    cv2.destroyAllWindows()
                    return

    except KeyboardInterrupt:
        print("\n程序被中断。")
    finally:
        if video_writer is not None:
            video_writer.release()
        keyboard.stop()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    import termios
    settings = termios.tcgetattr(sys.stdin)
    try:
        main()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
