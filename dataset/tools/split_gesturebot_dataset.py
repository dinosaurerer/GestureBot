#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GestureBot手势数据集划分脚本
将D:\workspace\GestureBot\dataset\GestureBot_Hand_Dataset文件夹下的images和对应的labels
按照0.7 0.2 0.1比率划分出train val test数据集

运行方式：
python dataset/tools/split_gesturebot_dataset.py
"""

import os
import sys
import random
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 设置输出编码为UTF-8，防止Windows下的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def gesturebot_dataset_split():
    """将GestureBot_Hand_Dataset数据集划分为train/val/test"""

    # 定义路径
    source_dataset = Path("D:/workspace/GestureBot/dataset/GestureBot_Hand_Dataset")
    target_dataset = Path("D:/workspace/GestureBot/datasets/ges_dataset")

    # 数据集划分比例
    train_ratio = 0.7
    val_ratio = 0.2
    test_ratio = 0.1

    # 类别列表
    classes = ['forward', 'backward', 'left', 'right', 'rotate_left', 'rotate_right', 'stop']
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}

    print("=" * 80)
    print("GestureBot手势数据集划分")
    print("=" * 80)
    print(f"源数据集路径: {source_dataset}")
    print(f"目标数据集路径: {target_dataset}")
    print(f"数据集划分比例: 训练集 {train_ratio*100:.0f}% | 验证集 {val_ratio*100:.0f}% | 测试集 {test_ratio*100:.0f}%")
    print("=" * 80)

    # 检查源数据集是否存在
    if not source_dataset.exists():
        print(f"错误：源数据集路径不存在: {source_dataset}")
        return

    # 检查源数据集结构
    source_images = source_dataset / "images"
    source_labels = source_dataset / "labels"

    if not source_images.exists() or not source_labels.exists():
        print("错误：源数据集缺少images或labels文件夹")
        return

    # 创建目标数据集目录结构
    print("\n创建目标数据集目录结构...")
    for split in ['train', 'val', 'test']:
        split_dir = target_dataset / split
        (split_dir / "images").mkdir(parents=True, exist_ok=True)
        (split_dir / "labels").mkdir(parents=True, exist_ok=True)

    # 收集所有图片和标签文件
    print("\n收集图片和标签文件...")

    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

    # 按类别收集图片
    class_images = defaultdict(list)

    # 遍历源数据集的images文件夹
    for img_file in source_images.glob("*"):
        if img_file.suffix.lower() in image_extensions:
            # 从文件名解析类别和序号
            # 格式：class_001.png 或 class_001.jpg
            # 使用startswith匹配类别名（处理rotate_left和rotate_right等带下划线的类别）
            class_name = None
            for cls in classes:
                if img_file.stem.startswith(cls + '_'):
                    class_name = cls
                    break

            if class_name is not None:
                class_images[class_name].append(img_file)

    # 统计总数
    total_images = sum(len(images) for images in class_images.values())
    print(f"总共找到 {total_images} 张图片")

    # 显示每个类别的图片数量
    print("\n各类别图片数量:")
    for cls in classes:
        count = len(class_images[cls])
        print(f"  {cls}: {count} 张")

    if total_images == 0:
        print("错误：没有找到任何有效的图片文件")
        return

    # 初始化分类计数器
    split_counts = {cls: {'train': 0, 'val': 0, 'test': 0} for cls in classes}

    # 划分数据集
    print("\n划分数据集...")
    for cls, images in class_images.items():
        # 随机打乱图片顺序
        random.shuffle(images)

        # 计算每个集的数量
        n_total = len(images)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        n_test = n_total - n_train - n_val  # 确保所有图片都被分配

        # 分配图片到各个集
        train_images = images[:n_train]
        val_images = images[n_train:n_train + n_val]
        test_images = images[n_train + n_val:]

        # 复制文件
        for img_path in train_images:
            # 复制图片
            dst_img = target_dataset / "train" / "images" / img_path.name
            shutil.copy2(img_path, dst_img)

            # 复制标签
            label_name = img_path.stem + ".txt"
            src_label = source_labels / label_name
            if src_label.exists():
                dst_label = target_dataset / "train" / "labels" / label_name
                shutil.copy2(src_label, dst_label)

            split_counts[cls]['train'] += 1

        for img_path in val_images:
            # 复制图片
            dst_img = target_dataset / "val" / "images" / img_path.name
            shutil.copy2(img_path, dst_img)

            # 复制标签
            label_name = img_path.stem + ".txt"
            src_label = source_labels / label_name
            if src_label.exists():
                dst_label = target_dataset / "val" / "labels" / label_name
                shutil.copy2(src_label, dst_label)

            split_counts[cls]['val'] += 1

        for img_path in test_images:
            # 复制图片
            dst_img = target_dataset / "test" / "images" / img_path.name
            shutil.copy2(img_path, dst_img)

            # 复制标签
            label_name = img_path.stem + ".txt"
            src_label = source_labels / label_name
            if src_label.exists():
                dst_label = target_dataset / "test" / "labels" / label_name
                shutil.copy2(src_label, dst_label)

            split_counts[cls]['test'] += 1

    # 统计结果
    print("\n" + "=" * 80)
    print("数据集划分结果")
    print("=" * 80)

    # 统计总数
    total_split = {split: 0 for split in ['train', 'val', 'test']}

    print(f"{'类别':<12} {'训练集':<8} {'验证集':<8} {'测试集':<8} {'总计':<8}")
    print("-" * 50)

    for cls in classes:
        train_count = split_counts[cls]['train']
        val_count = split_counts[cls]['val']
        test_count = split_counts[cls]['test']
        total_count = train_count + val_count + test_count

        total_split['train'] += train_count
        total_split['val'] += val_count
        total_split['test'] += test_count

        print(f"{cls:<12} {train_count:<8} {val_count:<8} {test_count:<8} {total_count:<8}")

    print("-" * 50)
    print(f"总计     {total_split['train']:<8} {total_split['val']:<8} {total_split['test']:<8} {total_images:<8}")

    # 验证比例
    actual_train_ratio = total_split['train'] / total_images
    actual_val_ratio = total_split['val'] / total_images
    actual_test_ratio = total_split['test'] / total_images

    print(f"\n实际比例: 训练集 {actual_train_ratio*100:.1f}% | 验证集 {actual_val_ratio*100:.1f}% | 测试集 {actual_test_ratio*100:.1f}%")

    # 生成数据集报告
    report_file = target_dataset / "dataset_split_report.txt"
    print(f"\n数据集报告已保存到: {report_file}")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# GestureBot数据集划分报告\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 格式: 数据集划分统计信息\n")
        f.write("=" * 80 + "\n\n")

        f.write("## 数据集总体信息\n")
        f.write(f"源数据集: {source_dataset}\n")
        f.write(f"目标数据集: {target_dataset}\n")
        f.write(f"总图片数: {total_images}\n")
        f.write(f"类别数量: {len(classes)}\n")
        f.write(f"类别: {', '.join(classes)}\n\n")

        f.write("## 数据集划分\n")
        f.write(f"训练集: {total_split['train']} 张 ({actual_train_ratio*100:.1f}%)\n")
        f.write(f"验证集: {total_split['val']} 张 ({actual_val_ratio*100:.1f}%)\n")
        f.write(f"测试集: {total_split['test']} 张 ({actual_test_ratio*100:.1f}%)\n\n")

        f.write("## 各类别分布\n")
        f.write(f"{'类别':<12} {'训练集':<8} {'验证集':<8} {'测试集':<8} {'总计':<8} {'百分比':<8}\n")
        f.write("-" * 70 + "\n")

        for cls in classes:
            train_count = split_counts[cls]['train']
            val_count = split_counts[cls]['val']
            test_count = split_counts[cls]['test']
            total_count = train_count + val_count + test_count
            percent = total_count / total_images * 100

            f.write(f"{cls:<12} {train_count:<8} {val_count:<8} {test_count:<8} {total_count:<8} {percent:.1f}%\n")

        f.write("-" * 70 + "\n")

        # 计算实际总数
        total_actual = total_split['train'] + total_split['val'] + total_split['test']
        f.write(f"总计     {total_split['train']:<8} {total_split['val']:<8} {total_split['test']:<8} {total_actual:<8}\n\n")

        f.write("## 使用说明\n")
        f.write("1. YAML配置文件路径: ultralytics/cfg/datasets/gesturebot.yaml\n")
        f.write("2. 训练命令: yolo train data=gesturebot.yaml model=yolo11n.pt\n")
        f.write("3. 验证命令: yolo val data=gesturebot.yaml model=best.pt\n")
        f.write("4. 预测命令: yolo predict data=gesturebot.yaml model=best.pt source=test/images/\n\n")

        f.write("## 目录结构\n")
        f.write("datasets/ges_dataset/\n")
        f.write("├── train/\n")
        f.write("│   ├── images/\n")
        f.write("│   └── labels/\n")
        f.write("├── val/\n")
        f.write("│   ├── images/\n")
        f.write("│   └── labels/\n")
        f.write("├── test/\n")
        f.write("│   ├── images/\n")
        f.write("│   └── labels/\n")

    print("\n" + "=" * 80)
    print("数据集划分完成！")
    print("=" * 80)
    print("请手动创建YAML配置文件，参考以下路径：")
    print(f"数据集路径: {target_dataset}")
    print("YAML配置应指向 datasets/ges_dataset 目录")
    print("=" * 80)


if __name__ == "__main__":
    gesturebot_dataset_split()