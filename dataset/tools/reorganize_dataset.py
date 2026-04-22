#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集重组脚本
将按类别分类的图片整合到一个文件夹，并按类别_序号格式重命名
"""

import os
import shutil
import sys
from pathlib import Path

# 设置输出编码为UTF-8，防止Windows下的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def reorganize_dataset():
    """重组数据集"""

    # 定义路径
    base_dir = Path("dataset")
    source_dir = base_dir / "images"
    target_dir = base_dir / "images_all"

    # 确保源目录存在
    if not source_dir.exists():
        print(f"错误：源目录 {source_dir} 不存在")
        return

    # 创建目标目录
    target_dir.mkdir(exist_ok=True)

    # 定义类别映射
    categories = [
        "forward",
        "backward",
        "left",
        "right",
        "rotate_left",
        "rotate_right",
        "stop"
    ]

    print(f"开始重组数据集...")
    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}\n")

    total_files = 0
    category_stats = {}

    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    # 遍历每个类别文件夹
    for category in categories:
        category_path = source_dir / category

        if not category_path.exists():
            print(f"警告：类别目录 {category} 不存在，跳过")
            continue

        # 获取该类别下的所有图片文件
        image_files = []
        for ext in image_extensions:
            # 只使用小写扩展名查找，避免重复
            image_files.extend(category_path.glob(f"*{ext.lower()}"))

        # 去重（防止重复文件）
        image_files = list(set(image_files))

        if not image_files:
            print(f"警告：类别 {category} 下没有图片，跳过")
            continue

        # 统计并处理该类别的图片
        category_count = 0
        print(f"处理类别: {category} ({len(image_files)} 张图片)")

        for idx, src_file in enumerate(image_files, start=1):
            # 获取文件扩展名
            file_ext = src_file.suffix.lower()

            # 生成新文件名：类别_序号.扩展名
            # 使用三位数编号，如 forward_001.jpg
            new_filename = f"{category}_{idx:03d}{file_ext}"
            dst_file = target_dir / new_filename

            # 如果目标文件已存在，跳过
            if dst_file.exists():
                print(f"  跳过已存在: {new_filename}")
                continue

            # 复制文件到目标目录
            shutil.copy2(src_file, dst_file)
            category_count += 1
            total_files += 1

            # 显示进度
            if idx % 50 == 0:
                print(f"  已处理 {idx}/{len(image_files)} 张图片")

        category_stats[category] = category_count
        print(f"  ✓ 完成：{category_count} 张图片\n")

    # 打印统计信息
    print("=" * 60)
    print("重组完成！")
    print("=" * 60)
    print(f"总计处理: {total_files} 张图片")
    print("\n各类别统计:")
    for category, count in category_stats.items():
        print(f"  {category:15} : {count:4} 张图片")
    print("=" * 60)
    print(f"\n所有图片已保存到: {target_dir}")
    print(f"\n接下来可以使用以下命令查看结果:")
    print(f"  ls {target_dir}")


if __name__ == "__main__":
    reorganize_dataset()
