import cv2
import os
import sys
import tty
import termios
import select
import time

def getKey():
    settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    save_path = "images"

    for file in os.listdir(save_path):
        if file.endswith(".jpg"):
            os.remove(os.path.join(save_path, file))

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    num = 1
    is_capturing = False
    capture_count = 0
    max_capture = 25

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        cv2.imshow("Camera Feed", frame)

        key = getKey()

        if key in ('c', 'C'):
            if not is_capturing and capture_count >= max_capture:
                capture_count = 0
                print("Ready for the next images. Press 'c' to start capturing.")
            elif not is_capturing:
                is_capturing = True
                print("Start capturing images...")
            else:
                is_capturing = False
                print("Stop capturing images.")

        if is_capturing:
            if capture_count < max_capture:
                filename = f"{save_path}/{num:03d}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Image saved as {filename}")
                num += 1
                capture_count += 1
                time.sleep(0.2)
            else:
                is_capturing = False
                print(f"Captured {max_capture} images. Press 'c' to start the next batch.")

        if key in ('q', 'Q'):
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    settings = termios.tcgetattr(sys.stdin)
    main()