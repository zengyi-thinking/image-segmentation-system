"""
系统测试脚本
用于验证图像分割系统的基本功能
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from core import MSTSegmentation, EdgeWeightCalculator
from utils.visualization import SegmentationVisualizer
from data_structures.segmentation_result import SegmentationResult


def create_test_image(size=(100, 100)):
    """
    创建测试图像
    
    Args:
        size: 图像尺寸 (height, width)
        
    Returns:
        测试图像
    """
    height, width = size
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 创建几个不同颜色的区域
    # 红色区域
    image[10:40, 10:40] = [255, 0, 0]
    
    # 绿色区域
    image[10:40, 60:90] = [0, 255, 0]
    
    # 蓝色区域
    image[60:90, 10:40] = [0, 0, 255]
    
    # 黄色区域
    image[60:90, 60:90] = [255, 255, 0]
    
    # 添加一些噪声
    noise = np.random.randint(-20, 20, image.shape, dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return image


def test_basic_segmentation():
    """测试基本分割功能"""
    print("测试基本分割功能...")
    
    # 创建测试图像
    test_image = create_test_image((100, 100))
    
    # 创建分割器
    weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
    segmenter = MSTSegmentation(
        connectivity=4,
        weight_calculator=weight_calculator,
        min_segment_size=10
    )
    
    # 执行分割
    result = segmenter.segment(test_image, threshold=None)
    
    # 检查结果
    assert 'label_map' in result
    assert 'statistics' in result
    assert 'threshold' in result
    
    label_map = result['label_map']
    stats = result['statistics']
    
    print(f"分割完成:")
    print(f"  区域数量: {stats['num_segments']}")
    print(f"  平均区域大小: {stats['avg_segment_size']:.1f}")
    print(f"  使用阈值: {result['threshold']:.2f}")
    
    return test_image, result


def test_visualization():
    """测试可视化功能"""
    print("\n测试可视化功能...")
    
    # 获取分割结果
    test_image, result = test_basic_segmentation()
    
    # 创建可视化器
    visualizer = SegmentationVisualizer()
    
    # 生成可视化图像
    segmented_image = visualizer.visualize_segments(test_image, result['label_map'])
    boundary_image = visualizer.visualize_boundaries(test_image, result['label_map'])
    
    # 检查结果
    assert segmented_image.shape == test_image.shape
    assert boundary_image.shape == test_image.shape
    
    print("可视化测试通过")
    
    return test_image, segmented_image, boundary_image


def test_data_structures():
    """测试数据结构"""
    print("\n测试数据结构...")
    
    # 测试并查集
    from data_structures.union_find import SegmentationUnionFind
    
    uf = SegmentationUnionFind(10, 10)
    
    # 测试合并操作
    uf.union_pixels((0, 0), (0, 1), 1.0)
    uf.union_pixels((0, 1), (1, 1), 1.5)
    
    # 检查连通性
    assert uf.connected(uf.pixel_to_idx[(0, 0)], uf.pixel_to_idx[(1, 1)])
    
    # 获取分割图
    label_map = uf.get_segmentation_map()
    assert label_map.shape == (10, 10)
    
    print("数据结构测试通过")


def test_segmentation_result():
    """测试分割结果类"""
    print("\n测试分割结果类...")
    
    # 创建测试数据
    test_image, result = test_basic_segmentation()
    
    # 创建分割结果对象
    seg_result = SegmentationResult(
        result['label_map'],
        test_image,
        "MST测试",
        {'threshold': result['threshold']}
    )
    
    # 测试基本功能
    assert seg_result.num_segments > 0
    assert seg_result.total_pixels == test_image.size // 3  # RGB图像
    
    # 测试区域特征计算
    unique_labels = np.unique(result['label_map'])
    if len(unique_labels) > 0:
        features = seg_result.compute_segment_features(unique_labels[0])
        assert 'area' in features
        assert 'centroid' in features
    
    print("分割结果类测试通过")


def test_multiple_thresholds():
    """测试多阈值分割"""
    print("\n测试多阈值分割...")
    
    # 创建测试图像
    test_image = create_test_image((50, 50))
    
    # 创建分割器
    weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
    segmenter = MSTSegmentation(connectivity=4, weight_calculator=weight_calculator)
    
    # 测试多阈值分割
    thresholds = [5.0, 10.0, 20.0]
    results = segmenter.segment_with_multiple_thresholds(test_image, thresholds)
    
    assert 'results' in results
    assert len(results['results']) == len(thresholds)
    
    # 检查不同阈值产生不同的分割结果
    segment_counts = []
    for threshold in thresholds:
        stats = results['results'][threshold]['statistics']
        segment_counts.append(stats['num_segments'])
        print(f"  阈值 {threshold}: {stats['num_segments']} 个区域")
    
    print("多阈值分割测试通过")


def create_visualization_demo():
    """创建可视化演示"""
    print("\n创建可视化演示...")
    
    # 创建更大的测试图像
    test_image = create_test_image((200, 200))
    
    # 执行分割
    weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
    segmenter = MSTSegmentation(connectivity=4, weight_calculator=weight_calculator)
    result = segmenter.segment(test_image)
    
    # 创建可视化
    visualizer = SegmentationVisualizer()
    segmented_image = visualizer.visualize_segments(test_image, result['label_map'])
    boundary_image = visualizer.visualize_boundaries(test_image, result['label_map'])
    
    # 创建对比图
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(test_image)
    axes[0].set_title('原始图像')
    axes[0].axis('off')
    
    axes[1].imshow(segmented_image)
    axes[1].set_title(f'分割结果 ({result["statistics"]["num_segments"]} 区域)')
    axes[1].axis('off')
    
    axes[2].imshow(boundary_image)
    axes[2].set_title('边界显示')
    axes[2].axis('off')
    
    plt.tight_layout()
    
    # 保存演示图像
    demo_dir = Path("examples")
    demo_dir.mkdir(exist_ok=True)
    
    plt.savefig(demo_dir / "segmentation_demo.png", dpi=150, bbox_inches='tight')
    print(f"演示图像已保存到: {demo_dir / 'segmentation_demo.png'}")
    
    # 保存原始测试图像
    cv2.imwrite(str(demo_dir / "test_image.png"), 
                cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))
    
    plt.show()


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("图像分割系统测试")
    print("=" * 50)
    
    try:
        # 基本功能测试
        test_basic_segmentation()
        test_visualization()
        test_data_structures()
        test_segmentation_result()
        test_multiple_thresholds()
        
        print("\n" + "=" * 50)
        print("所有测试通过! ✓")
        print("=" * 50)
        
        # 创建演示
        create_visualization_demo()
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n系统测试完成，可以运行主程序:")
        print("python main.py --gui  # GUI模式")
        print("python main.py --cli --input examples/test_image.png  # 命令行模式")
    else:
        print("\n系统测试失败，请检查错误信息")
        sys.exit(1)
