"""
图像分割系统主程序 v2.0.0
提供命令行和GUI两种使用方式，集成所有增强功能
"""

import sys
import argparse
import numpy as np
import cv2
from pathlib import Path
import time

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 导入核心模块
from core.mst_segmentation import MSTSegmentation
from core.watershed_segmentation import WatershedSegmentation
from core.kmeans_segmentation import KMeansSegmentation, GMMSegmentation
from utils.image_io import ImageLoader
from utils.visualization import SegmentationVisualizer
from utils.logger import setup_global_logger, get_global_logger
from utils.config_manager import get_config_manager
from utils.performance_monitor import get_performance_monitor
from utils.exceptions import ImageLoadError, AlgorithmError
from version import __version__, print_version_info


def run_cli_segmentation(image_path: str,
                        output_path: str = None,
                        algorithm: str = 'MST',
                        threshold: float = None,
                        connectivity: int = 4,
                        alpha: float = 1.0,
                        beta: float = 0.1,
                        k: int = 5,
                        **kwargs):
    """
    命令行模式运行图像分割

    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径
        algorithm: 分割算法 ('MST', 'Watershed', 'K-Means', 'GMM')
        threshold: 分割阈值
        connectivity: 连接性
        alpha: 颜色权重
        beta: 空间权重
        k: 聚类数量（K-Means/GMM）
    """
    logger = get_global_logger()

    try:
        logger.info(f"开始命令行分割 - 算法: {algorithm}, 图像: {image_path}")

        # 加载图像
        loader = ImageLoader()
        image = loader.load_image(image_path)

        print(f"✅ 图像加载成功: {image.shape}")

        # 选择算法
        algorithms = {
            'MST': MSTSegmentation(),
            'Watershed': WatershedSegmentation(),
            'K-Means': KMeansSegmentation(),
            'GMM': GMMSegmentation()
        }

        if algorithm not in algorithms:
            raise ValueError(f"不支持的算法: {algorithm}")

        segmenter = algorithms[algorithm]

        # 准备参数
        params = {}
        if algorithm == 'MST':
            params = {
                'alpha': alpha,
                'beta': beta,
                'connectivity': connectivity,
                'threshold': threshold
            }
        elif algorithm == 'Watershed':
            params = {
                'min_distance': kwargs.get('min_distance', 20),
                'compactness': kwargs.get('compactness', 0.001)
            }
        elif algorithm in ['K-Means', 'GMM']:
            params = {
                'k' if algorithm == 'K-Means' else 'n_components': k,
                'color_space': kwargs.get('color_space', 'RGB')
            }

        # 执行分割
        print(f"🔄 开始{algorithm}分割...")
        start_time = time.time()

        result = segmenter.segment(image, **params)

        execution_time = time.time() - start_time

        # 显示统计信息
        print(f"✅ 分割完成!")
        print(f"📊 分割区域数: {result['num_segments']}")
        print(f"⏱️ 执行时间: {execution_time:.2f}s")
        print(f"🔧 算法: {algorithm}")

        # 可视化结果
        visualizer = SegmentationVisualizer()
        segmented_image = result['segmented_image']

        # 保存结果
        if output_path:
            from PIL import Image

            # 保存分割结果
            output_path = Path(output_path)
            seg_path = output_path.parent / f"{output_path.stem}_{algorithm}_segmented{output_path.suffix}"
            Image.fromarray(segmented_image).save(seg_path)
            print(f"💾 分割结果保存到: {seg_path}")

            # 保存对比图
            comparison = np.hstack([image, segmented_image])
            comp_path = output_path.parent / f"{output_path.stem}_{algorithm}_comparison{output_path.suffix}"
            Image.fromarray(comparison).save(comp_path)
            print(f"💾 对比图保存到: {comp_path}")

        # 显示结果（如果有显示器）
        try:
            cv2.imshow('Original', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            cv2.imshow('Segmented', cv2.cvtColor(segmented_image, cv2.COLOR_RGB2BGR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except:
            print("ℹ️ 无法显示图像（可能没有显示器）")

        logger.info(f"命令行分割完成 - 耗时: {execution_time:.2f}s")

    except Exception as e:
        logger.error(f"命令行分割失败: {str(e)}", exception=e)
        print(f"❌ 错误: {str(e)}")
        raise


def run_gui():
    """运行GUI模式"""
    logger = get_global_logger()

    try:
        import tkinter as tk

        logger.info("启动GUI模式")

        # 初始化性能监控
        performance_monitor = get_performance_monitor()
        performance_monitor.start_monitoring()

        # 尝试使用增强版GUI
        try:
            from gui.enhanced_main_window import EnhancedMainWindow

            root = tk.Tk()
            app = EnhancedMainWindow(root)

            print("🎨 图像分割系统 v2.0.0")
            print("✅ 使用增强版GUI界面")
            print("📚 按F1查看帮助，按H查看快捷键")

            logger.info("增强版GUI启动成功")

            # 设置退出处理
            def on_closing():
                logger.info("GUI正在关闭")
                performance_monitor.stop_monitoring()
                root.destroy()

            root.protocol("WM_DELETE_WINDOW", on_closing)
            root.mainloop()

        except Exception as e:
            logger.warning(f"增强版GUI启动失败: {e}")
            print(f"⚠️ 增强版GUI启动失败: {e}")
            print("🔄 尝试使用基础版GUI...")

            # 备用方案：使用基础版GUI
            from gui.main_window import MainWindow

            root = tk.Tk()
            app = MainWindow(root)
            print("✅ 使用基础版GUI界面")

            logger.info("基础版GUI启动成功")
            root.mainloop()

    except ImportError as ie:
        error_msg = f"无法导入tkinter: {ie}"
        logger.error(error_msg)
        print(f"❌ 错误: {error_msg}")
        print("💡 请安装GUI依赖或使用命令行模式:")
        print("   python main.py --cli --input <image_path>")

    except Exception as e:
        error_msg = f"GUI启动失败: {e}"
        logger.error(error_msg, exception=e)
        print(f"❌ {error_msg}")
        print("💡 请尝试命令行模式:")
        print("   python main.py --cli --input <image_path>")


def main():
    """主函数"""
    # 设置全局日志
    setup_global_logger(level="INFO")
    logger = get_global_logger()

    parser = argparse.ArgumentParser(
        description='图像分割系统 v2.0.0 - 专业级图像分割工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  GUI模式:
    python main.py
    python main.py --gui

  命令行模式:
    python main.py --cli -i image.jpg -o result.jpg
    python main.py --cli -i image.jpg --algorithm MST --alpha 1.5
    python main.py --cli -i image.jpg --algorithm K-Means --k 8

  其他:
    python main.py --version
    python main.py --help
        """
    )

    # 模式选择
    parser.add_argument('--cli', action='store_true',
                       help='使用命令行模式')
    parser.add_argument('--gui', action='store_true',
                       help='使用GUI模式（默认）')
    parser.add_argument('--version', action='store_true',
                       help='显示版本信息')

    # 命令行参数
    parser.add_argument('--input', '-i', type=str,
                       help='输入图像路径')
    parser.add_argument('--output', '-o', type=str,
                       help='输出图像路径')
    parser.add_argument('--algorithm', '-a', type=str, default='MST',
                       choices=['MST', 'Watershed', 'K-Means', 'GMM'],
                       help='分割算法')

    # MST算法参数
    parser.add_argument('--threshold', '-t', type=float,
                       help='分割阈值（自动计算如果未指定）')
    parser.add_argument('--connectivity', '-c', type=int, default=4,
                       choices=[4, 8], help='像素连接性 (4 或 8)')
    parser.add_argument('--alpha', type=float, default=1.0,
                       help='颜色权重系数')
    parser.add_argument('--beta', type=float, default=0.1,
                       help='空间权重系数')

    # K-Means/GMM参数
    parser.add_argument('--k', type=int, default=5,
                       help='聚类数量（K-Means/GMM）')
    parser.add_argument('--color-space', type=str, default='RGB',
                       choices=['RGB', 'LAB', 'HSV'],
                       help='颜色空间')

    # Watershed参数
    parser.add_argument('--min-distance', type=int, default=20,
                       help='Watershed最小距离')
    parser.add_argument('--compactness', type=float, default=0.001,
                       help='Watershed紧密度')

    # 系统参数
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        setup_global_logger(level="DEBUG")
    else:
        setup_global_logger(level=args.log_level)

    # 显示版本信息
    if args.version:
        print_version_info()
        return

    # 记录启动信息
    logger.info(f"图像分割系统启动 - 版本: {__version__}")

    # 如果没有指定模式，默认使用GUI
    if not args.cli and not args.gui:
        args.gui = True

    try:
        if args.cli:
            if not args.input:
                print("❌ 错误: 命令行模式需要指定输入图像路径")
                parser.print_help()
                return

            run_cli_segmentation(
                image_path=args.input,
                output_path=args.output,
                algorithm=args.algorithm,
                threshold=args.threshold,
                connectivity=args.connectivity,
                alpha=args.alpha,
                beta=args.beta,
                k=args.k,
                color_space=args.color_space,
                min_distance=args.min_distance,
                compactness=args.compactness
            )

        elif args.gui:
            run_gui()

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}", exception=e)
        print(f"❌ 程序执行失败: {str(e)}")
        if args.debug:
            raise


if __name__ == "__main__":
    main()
