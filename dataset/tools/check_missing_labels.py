#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缺少标签的图片
"""

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

# 设置输出编码为UTF-8，防止Windows下的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_missing_labels():
    """检查缺少标签的图片"""

    # 定义路径
    images_dir = Path("dataset/images_all")
    labels_dir = Path("dataset/labels_all")

    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    print("=" * 80)
    print("检查图片标签文件匹配情况")
    print("=" * 80)

    # 获取所有图片文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(images_dir.glob(f"*{ext.lower()}"))

    if not image_files:
        print(f"错误：在 {images_dir} 中没有找到图片文件")
        return

    print(f"找到 {len(image_files)} 张图片")

    # 统计
    missing_count = 0
    present_count = 0
    unmatched_files = []

    # 检查每张图片
    for img_path in image_files:
        # 获取图片文件名（不带扩展名）
        img_name = img_path.stem
        img_ext = img_path.suffix.lower()

        # 检查对应的标签文件
        label_path = labels_dir / f"{img_name}.txt"

        if not label_path.exists():
            # 没有标签文件
            missing_count += 1
            unmatched_files.append(str(img_path))

            if missing_count <= 10:  # 只显示前10个
                print("[缺少标签]:", img_path.name)
        else:
            # 有标签文件
            present_count += 1

    # 检查多余的标签文件
    print("\n" + "=" * 80)
    print("检查多余的标签文件")
    print("=" * 80)

    extra_labels = []
    for label_file in labels_dir.glob("*.txt"):
        # 从标签文件名推断图片文件名
        label_name = label_file.stem
        img_found = False

        for ext in image_extensions:
            img_path = images_dir / f"{label_name}{ext.lower()}"
            if img_path.exists():
                img_found = True
                break

        if not img_found:
            extra_labels.append(str(label_file))
            print("[没有图片]:", label_file.name)

    # 统计结果
    print("\n" + "=" * 80)
    print("统计结果")
    print("=" * 80)
    print(f"总图片数: {len(image_files)}")
    print(f"有标签的图片: {present_count} ({present_count/len(image_files)*100:.1f}%)")
    print(f"缺少标签的图片: {missing_count} ({missing_count/len(image_files)*100:.1f}%)")
    print(f"多余的标签文件: {len(extra_labels)}")

    if missing_count > 0:
        print("\n" + "=" * 80)
        print("缺少标签的图片列表")
        print("=" * 80)
        print(f"共 {missing_count} 张图片缺少标签")

        if missing_count <= 20:
            # 少量缺失时显示全部
            for unmatched in unmatched_files:
                print(f"  {unmatched}")
        else:
            # 大量缺失时显示部分
            print("前20个:")
            for i, unmatched in enumerate(unmatched_files[:20], 1):
                print(f"  {i:2}. {Path(unmatched).name}")
            print(f"... 还有 {missing_count-20} 个文件未显示")

        # 生成缺失列表文件
        missing_list = "dataset/missing_labels.txt"
        print(f"\n缺失标签列表已保存到: {missing_list}")
        with open(missing_list, 'w', encoding='utf-8') as f:
            f.write("# 缺少标签的图片列表\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 格式: 图片路径\n")
            f.write("=" * 80 + "\n\n")
            for unmatched in unmatched_files:
                f.write(f"{unmatched}\n")

    if extra_labels:
        print(f"\n" + "=" * 80)
        print("多余的标签文件列表")
        print("=" * 80)
        for label in extra_labels:
            print(f"  {label}")

    # 建议
    print("\n" + "=" * 80)
    print("操作建议")
    print("=" * 80)

    if missing_count > 0:
        print("✅ 建议:")
        if missing_count < len(image_files) * 0.1:
            print("  • 缺失较少，可以继续补充标注")
        elif missing_count < len(image_files) * 0.3:
            print("  • 缺失较多，建议集中标注")
        else:
            print("  • 缺失很多，建议重新审核标注进度")

        print(f"\n可以运行以下命令快速定位缺失的图片:")
        print(f"  type dataset/missing_labels.txt")

    if extra_labels:
        print(f"\n⚠️  发现 {len(extra_labels)} 个多余的标签文件:")
        print("  • 检查是否是误删的图片对应的标签")
        print("  • 如果确认不需要，可以删除这些标签文件")


if __name__ == "__main__":
    check_missing_labels()