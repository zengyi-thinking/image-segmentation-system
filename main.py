"""
图像分割系统主程序
提供命令行和GUI两种使用方式
"""

import sys
import argparse
import numpy as np
import cv2
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from core import MSTSegmentation, EdgeWeightCalculator
from utils.image_io import ImageLoader, ImageSaver
from utils.visualization import SegmentationVisualizer
from gui.main_window import MainWindow


def run_cli_segmentation(image_path: str, 
                        output_path: str = None,
                        threshold: float = None,
                        connectivity: int = 4,
                        alpha: float = 1.0,
                        beta: float = 0.1):
    """
    命令行模式运行图像分割
    
    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径
        threshold: 分割阈值
        connectivity: 连接性
        alpha: 颜色权重
        beta: 空间权重
    """
    print(f"加载图像: {image_path}")
    
    # 加载图像
    loader = ImageLoader()
    image = loader.load_image(image_path)
    
    if image is None:
        print(f"错误: 无法加载图像 {image_path}")
        return
    
    print(f"图像尺寸: {image.shape}")
    
    # 创建分割器
    weight_calculator = EdgeWeightCalculator(alpha=alpha, beta=beta)
    segmenter = MSTSegmentation(
        connectivity=connectivity,
        weight_calculator=weight_calculator
    )
    
    # 执行分割
    print("开始图像分割...")
    result = segmenter.segment(image, threshold=threshold)
    
    # 显示统计信息
    stats = result['statistics']
    print(f"分割完成!")
    print(f"分割区域数: {stats['num_segments']}")
    print(f"平均区域大小: {stats['avg_segment_size']:.1f}")
    print(f"使用阈值: {result['threshold']:.2f}")
    
    # 可视化结果
    visualizer = SegmentationVisualizer()
    
    # 生成分割结果图像
    segmented_image = visualizer.visualize_segments(
        image, result['label_map']
    )
    
    # 生成边界图像
    boundary_image = visualizer.visualize_boundaries(
        image, result['label_map']
    )
    
    # 保存结果
    if output_path:
        saver = ImageSaver()
        
        # 保存分割结果
        seg_path = output_path.replace('.', '_segmented.')
        saver.save_image(segmented_image, seg_path)
        print(f"分割结果保存到: {seg_path}")
        
        # 保存边界图像
        boundary_path = output_path.replace('.', '_boundaries.')
        saver.save_image(boundary_image, boundary_path)
        print(f"边界图像保存到: {boundary_path}")
    
    # 显示结果（如果有显示器）
    try:
        cv2.imshow('Original', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imshow('Segmented', cv2.cvtColor(segmented_image, cv2.COLOR_RGB2BGR))
        cv2.imshow('Boundaries', cv2.cvtColor(boundary_image, cv2.COLOR_RGB2BGR))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("无法显示图像（可能没有显示器）")


def run_gui():
    """运行GUI模式"""
    try:
        import tkinter as tk
        from gui.main_window import MainWindow
        
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
        
    except ImportError:
        print("错误: 无法导入tkinter，请安装GUI依赖")
        print("或者使用命令行模式: python main.py --cli --input <image_path>")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='图像分割系统')
    
    # 模式选择
    parser.add_argument('--cli', action='store_true', 
                       help='使用命令行模式')
    parser.add_argument('--gui', action='store_true', 
                       help='使用GUI模式（默认）')
    
    # 命令行参数
    parser.add_argument('--input', '-i', type=str,
                       help='输入图像路径')
    parser.add_argument('--output', '-o', type=str,
                       help='输出图像路径')
    parser.add_argument('--threshold', '-t', type=float,
                       help='分割阈值（自动计算如果未指定）')
    parser.add_argument('--connectivity', '-c', type=int, default=4,
                       choices=[4, 8], help='像素连接性 (4 或 8)')
    parser.add_argument('--alpha', type=float, default=1.0,
                       help='颜色权重系数')
    parser.add_argument('--beta', type=float, default=0.1,
                       help='空间权重系数')
    
    args = parser.parse_args()
    
    # 如果没有指定模式，默认使用GUI
    if not args.cli and not args.gui:
        args.gui = True
    
    if args.cli:
        if not args.input:
            print("错误: 命令行模式需要指定输入图像路径")
            parser.print_help()
            return
        
        run_cli_segmentation(
            image_path=args.input,
            output_path=args.output,
            threshold=args.threshold,
            connectivity=args.connectivity,
            alpha=args.alpha,
            beta=args.beta
        )
    
    elif args.gui:
        run_gui()


if __name__ == "__main__":
    main()
