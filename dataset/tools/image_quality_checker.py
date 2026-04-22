#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片质量检测工具
使用拉普拉斯算子计算图片模糊度分数
"""

import cv2 as cv
import numpy as np
import os
from pathlib import Path
import argparse
from datetime import datetime


class ImageQualityChecker:
    """图片质量检测器"""

    def __init__(self):
        # 模糊度阈值（可调整）
        self.blur_thresholds = {
            'sharp': 100,      # 清晰
            'good': 50,        # 良好
            'acceptable': 20,   # 可接受
            'blurry': 10,      # 模糊
            'very_blurry': 0    # 非常模糊
        }

    def calculate_blur_score(self, image_path):
        """
        使用拉普拉斯算子计算图片模糊度分数

        Args:
            image_path: 图片路径

        Returns:
            score: 模糊度分数（越高越清晰）
            status: 质量状态描述
        """
        try:
            # 读取图片
            img = cv.imread(str(image_path))
            if img is None:
                return 0, "无法读取图片"

            # 转换为灰度图
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

            # 使用拉普拉斯算子
            laplacian_var = cv.Laplacian(gray, cv.CV_64F).var()

            score = float(laplacian_var)

            # 判断质量等级
            status = self._get_quality_status(score)

            return score, status

        except Exception as e:
            return 0, f"错误: {str(e)}"

    def _get_quality_status(self, score):
        """根据分数返回质量状态"""
        if score >= self.blur_thresholds['sharp']:
            return "清晰"
        elif score >= self.blur_thresholds['good']:
            return "良好"
        elif score >= self.blur_thresholds['acceptable']:
            return "可接受"
        elif score >= self.blur_thresholds['blurry']:
            return "模糊"
        else:
            return "非常模糊"

    def check_single_image(self, image_path):
        """检查单张图片"""
        score, status = self.calculate_blur_score(image_path)

        print(f"图片: {os.path.basename(image_path)}")
        print(f"  模糊度分数: {score:.2f}")
        print(f"  质量状态: {status}")
        print("-" * 60)

        return score, status

    def check_directory(self, directory, output_file=None, sort_by_score=True,
                     show_threshold=None, copy_low_quality=False):
        """
        检查目录中的所有图片

        Args:
            directory: 目录路径
            output_file: 输出文件路径（可选）
            sort_by_score: 是否按分数排序
            show_threshold: 只显示低于此分数的图片
            copy_low_quality: 将低质量图片复制到单独文件夹
        """
        directory = Path(directory)
        if not directory.exists():
            print(f"错误：目录 {directory} 不存在")
            return

        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

        # 获取所有图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(directory.glob(f"*{ext.lower()}"))

        if not image_files:
            print(f"警告：目录 {directory} 中没有找到图片文件")
            return

        print(f"开始检测 {len(image_files)} 张图片...")
        print("=" * 80)

        # 检测每张图片
        results = []
        for idx, img_path in enumerate(image_files, 1):
            score, status = self.calculate_blur_score(img_path)
            results.append({
                'path': img_path,
                'name': img_path.name,
                'score': score,
                'status': status
            })

            # 显示进度
            if idx % 50 == 0:
                print(f"已处理 {idx}/{len(image_files)} 张图片...")

        # 按分数排序
        if sort_by_score:
            results.sort(key=lambda x: x['score'])

        # 显示结果
        print("\n" + "=" * 80)
        print("检测结果统计")
        print("=" * 80)

        # 统计各质量级别的数量
        quality_counts = {}
        for result in results:
            status = result['status']
            quality_counts[status] = quality_counts.get(status, 0) + 1

        print("\n质量分布:")
        for status, count in sorted(quality_counts.items()):
            percentage = (count / len(results)) * 100
            print(f"  {status:8} : {count:4} 张 ({percentage:5.1f}%)")

        # 显示详细结果
        print("\n" + "=" * 80)
        print("详细结果（按模糊度从低到高排序）")
        print("=" * 80)

        if show_threshold:
            print(f"只显示模糊度分数低于 {show_threshold} 的图片\n")

        for idx, result in enumerate(results, 1):
            if show_threshold and result['score'] >= show_threshold:
                continue

            print(f"{idx:4}. {result['name']:40} 分数: {result['score']:6.2f}  {result['status']}")

        # 显示最模糊和最清晰的图片
        print("\n" + "=" * 80)
        print("最模糊的10张图片（建议删除）:")
        print("=" * 80)
        for idx, result in enumerate(results[:10], 1):
            print(f"  {idx:2}. {result['name']:40} 分数: {result['score']:6.2f}")

        print("\n" + "=" * 80)
        print("最清晰的10张图片:")
        print("=" * 80)
        for idx, result in enumerate(results[-10:], 1):
            print(f"  {idx:2}. {result['name']:40} 分数: {result['score']:6.2f}")

        # 计算统计数据
        scores = [r['score'] for r in results]
        print("\n" + "=" * 80)
        print("统计数据")
        print("=" * 80)
        print(f"  总图片数: {len(results)}")
        print(f"  平均分数: {np.mean(scores):.2f}")
        print(f"  中位数:   {np.median(scores):.2f}")
        print(f"  标准差:   {np.std(scores):.2f}")
        print(f"  最低分数: {min(scores):.2f}")
        print(f"  最高分数: {max(scores):.2f}")

        # 输出到文件
        if output_file:
            self._save_results(results, output_file)

        # 复制低质量图片
        if copy_low_quality:
            self._copy_low_quality_images(results, directory)

    def _save_results(self, results, output_file):
        """保存结果到文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 图片质量检测报告\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 格式: 文件名 | 模糊度分数 | 质量状态\n")
            f.write("=" * 80 + "\n\n")

            for result in results:
                f.write(f"{result['name']:40} | {result['score']:8.2f} | {result['status']}\n")

        print(f"\n结果已保存到: {output_file}")

    def _copy_low_quality_images(self, results, source_dir):
        """将低质量图片复制到单独文件夹"""
        # 定义低质量文件夹
        low_quality_dir = source_dir.parent / "images_low_quality"
        low_quality_dir.mkdir(exist_ok=True)

        # 复制模糊和非常模糊的图片
        low_quality_count = 0
        for result in results:
            if result['status'] in ['模糊', '非常模糊']:
                import shutil
                shutil.copy2(result['path'], low_quality_dir / result['name'])
                low_quality_count += 1

        print(f"\n已将 {low_quality_count} 张低质量图片复制到: {low_quality_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='图片质量检测工具')
    parser.add_argument('path', type=str, help='图片路径或目录路径')
    parser.add_argument('-o', '--output', type=str, help='输出结果文件路径')
    parser.add_argument('-t', '--threshold', type=float, help='只显示低于此分数的图片')
    parser.add_argument('--no-sort', action='store_true', help='不按分数排序')
    parser.add_argument('--copy-low', action='store_true', help='将低质量图片复制到单独文件夹')

    args = parser.parse_args()

    checker = ImageQualityChecker()

    path = Path(args.path)

    if path.is_file():
        # 单张图片
        print("检测单张图片...")
        print("=" * 60)
        checker.check_single_image(path)

    elif path.is_dir():
        # 目录
        print("检测目录中的所有图片...")
        print("=" * 80)

        checker.check_directory(
            directory=path,
            output_file=args.output,
            sort_by_score=not args.no_sort,
            show_threshold=args.threshold,
            copy_low_quality=args.copy_low
        )

    else:
        print(f"错误：路径 {path} 不存在")


if __name__ == "__main__":
    main()
