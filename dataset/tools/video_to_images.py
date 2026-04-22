import cv2
import os
from pathlib import Path
from tqdm import tqdm


def main():
    # 配置参数
    VIDEO_DIR = Path("ges_data_opt")
    OUTPUT_DIR = Path("dataset/images")
    FRAME_INTERVAL = 5  # 每隔几帧抽取一张图片

    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 为每个类别创建图片文件夹
    gesture_classes = ['forward', 'backward', 'left', 'right', 'rotate_left', 'rotate_right', 'stop']
    for class_name in gesture_classes:
        (OUTPUT_DIR / class_name).mkdir(exist_ok=True)

    print("=" * 60)
    print("视频转图片工具")
    print("=" * 60)
    print(f"视频目录: {VIDEO_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"抽帧间隔: 每 {FRAME_INTERVAL} 帧抽取一张")
    print("=" * 60)

    total_videos = 0
    total_images = 0

    # 遍历每个类别文件夹
    for class_name in gesture_classes:
        class_video_dir = VIDEO_DIR / class_name
        class_image_dir = OUTPUT_DIR / class_name

        if not class_video_dir.exists():
            print(f"\n跳过 {class_name} (文件夹不存在)")
            continue

        # 获取该类别的所有视频文件
        video_files = sorted(list(class_video_dir.glob("*.mp4")))

        if not video_files:
            print(f"\n跳过 {class_name} (没有视频文件)")
            continue

        print(f"\n处理类别: {class_name}")
        print(f"找到 {len(video_files)} 个视频文件")

        # 遍历该类别的每个视频
        for video_file in video_files:
            print(f"  处理: {video_file.name}")
            total_videos += 1

            # 打开视频
            cap = cv2.VideoCapture(str(video_file))
            if not cap.isOpened():
                print(f"    警告: 无法打开视频 {video_file.name}")
                continue

            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            frame_number = 0
            saved_image_number = len(list(class_image_dir.glob("*.png"))) + 1

            with tqdm(total=total_frames, desc="    进度", unit="帧") as pbar:
                while True:
                    ret, frame = cap.read()

                    if not ret:
                        break

                    # 按间隔保存帧
                    if frame_number % FRAME_INTERVAL == 0:
                        image_name = f"{saved_image_number:05d}.png"
                        image_path = class_image_dir / image_name
                        cv2.imwrite(str(image_path), frame)
                        saved_image_number += 1
                        total_images += 1

                    frame_number += 1
                    pbar.update(1)

            cap.release()

    # 生成数据集统计信息
    print("\n" + "=" * 60)
    print("转换完成！")
    print("=" * 60)
    print(f"处理视频数: {total_videos}")
    print(f"生成图片数: {total_images}")

    # 显示每个类别的图片数量
    print("\n各类别图片统计:")
    print("-" * 60)
    for class_name in gesture_classes:
        class_image_dir = OUTPUT_DIR / class_name
        if class_image_dir.exists():
            count = len(list(class_image_dir.glob("*.png")))
            print(f"  {class_name:15s}: {count:5d} 张")
    print("=" * 60)


if __name__ == "__main__":
    main()
