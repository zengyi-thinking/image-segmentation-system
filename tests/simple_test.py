"""
简化的系统测试脚本
验证核心功能是否正常工作
"""

import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        # 测试核心模块
        from core.edge_weights import EdgeWeightCalculator
        from core.graph_builder import PixelGraphBuilder
        from data_structures.union_find import SegmentationUnionFind
        print("✓ 核心模块导入成功")
        
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    
    try:
        from core.edge_weights import EdgeWeightCalculator
        from core.graph_builder import PixelGraphBuilder
        from data_structures.union_find import SegmentationUnionFind
        
        # 创建简单的测试图像
        test_image = np.zeros((10, 10, 3), dtype=np.uint8)
        test_image[0:5, 0:5] = [255, 0, 0]  # 红色区域
        test_image[5:10, 5:10] = [0, 255, 0]  # 绿色区域
        
        print("✓ 测试图像创建成功")
        
        # 测试边权重计算
        weight_calc = EdgeWeightCalculator(alpha=1.0, beta=0.1)
        weight = weight_calc.calculate_weight((0, 0), (0, 1), test_image)
        print(f"✓ 边权重计算成功: {weight:.2f}")
        
        # 测试图构建
        graph_builder = PixelGraphBuilder(connectivity=4, weight_calculator=weight_calc)
        graph = graph_builder.build_graph(test_image)
        print(f"✓ 图构建成功: {len(graph['nodes'])} 节点, {len(graph['edges'])} 边")
        
        # 测试并查集
        uf = SegmentationUnionFind(10, 10)
        uf.union_pixels((0, 0), (0, 1), 1.0)
        uf.union_pixels((1, 1), (1, 2), 1.5)
        
        label_map = uf.get_segmentation_map()
        print(f"✓ 并查集测试成功: 分割图尺寸 {label_map.shape}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mst_segmentation():
    """测试MST分割算法"""
    print("\n测试MST分割算法...")
    
    try:
        # 检查是否有scipy依赖
        try:
            import scipy
            print("✓ SciPy可用")
        except ImportError:
            print("⚠ SciPy不可用，跳过部分测试")
        
        from core.edge_weights import EdgeWeightCalculator
        from core.graph_builder import PixelGraphBuilder
        
        # 创建更复杂的测试图像
        test_image = np.zeros((20, 20, 3), dtype=np.uint8)
        
        # 创建几个不同的区域
        test_image[0:10, 0:10] = [255, 0, 0]    # 红色
        test_image[0:10, 10:20] = [0, 255, 0]   # 绿色
        test_image[10:20, 0:10] = [0, 0, 255]   # 蓝色
        test_image[10:20, 10:20] = [255, 255, 0] # 黄色
        
        # 添加噪声
        noise = np.random.randint(-10, 10, test_image.shape, dtype=np.int16)
        test_image = np.clip(test_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        print("✓ 复杂测试图像创建成功")
        
        # 构建图
        weight_calc = EdgeWeightCalculator(alpha=1.0, beta=0.1)
        graph_builder = PixelGraphBuilder(connectivity=4, weight_calculator=weight_calc)
        graph = graph_builder.build_graph(test_image)
        
        print(f"✓ 图构建成功: {len(graph['edges'])} 条边")
        
        # 简化的MST算法测试（不使用完整的MST分割类）
        edges_with_weights = list(zip(graph['edges'], graph['weights']))
        edges_with_weights.sort(key=lambda x: x[1])
        
        print(f"✓ 边排序成功，权重范围: {min(graph['weights']):.2f} - {max(graph['weights']):.2f}")
        
        # 使用并查集进行简单的阈值分割
        from data_structures.union_find import SegmentationUnionFind
        
        uf = SegmentationUnionFind(20, 20)
        threshold = np.median(graph['weights'])
        
        merged_count = 0
        for edge, weight in edges_with_weights:
            if weight <= threshold:
                node1, node2 = edge
                pixel1 = graph['nodes'][node1]
                pixel2 = graph['nodes'][node2]
                
                if uf.union_pixels(pixel1, pixel2, weight):
                    merged_count += 1
        
        label_map = uf.get_segmentation_map()
        stats = uf.get_segment_statistics()
        
        print(f"✓ 分割完成:")
        print(f"  使用阈值: {threshold:.2f}")
        print(f"  合并边数: {merged_count}")
        print(f"  分割区域数: {stats['num_segments']}")
        print(f"  平均区域大小: {stats['avg_segment_size']:.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ MST分割测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structures():
    """测试数据结构"""
    print("\n测试数据结构...")
    
    try:
        from data_structures.pixel_graph import PixelGraph
        from data_structures.segmentation_result import SegmentationResult
        
        # 测试像素图
        pixel_graph = PixelGraph(5, 5, connectivity=4)
        pixel_graph.add_edge((0, 0), (0, 1), 1.0)
        pixel_graph.add_edge((0, 1), (1, 1), 1.5)
        
        neighbors = pixel_graph.get_neighbors((0, 1))
        print(f"✓ 像素图测试成功: (0,1)的邻居数量 {len(neighbors)}")
        
        # 测试分割结果
        test_labels = np.random.randint(0, 5, (10, 10))
        test_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        
        seg_result = SegmentationResult(test_labels, test_image, "测试算法")
        features = seg_result.compute_segment_features(0)
        
        print(f"✓ 分割结果测试成功: 区域0的面积 {features.get('area', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_demo_output():
    """创建演示输出"""
    print("\n创建演示输出...")
    
    try:
        # 创建示例目录
        examples_dir = Path("examples")
        examples_dir.mkdir(exist_ok=True)
        
        # 创建简单的测试图像并保存
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 创建几个区域
        test_image[10:40, 10:40] = [255, 0, 0]    # 红色
        test_image[10:40, 60:90] = [0, 255, 0]    # 绿色
        test_image[60:90, 10:40] = [0, 0, 255]    # 蓝色
        test_image[60:90, 60:90] = [255, 255, 0]  # 黄色
        
        # 添加噪声
        noise = np.random.randint(-20, 20, test_image.shape, dtype=np.int16)
        test_image = np.clip(test_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # 尝试保存图像
        try:
            import cv2
            cv2.imwrite(str(examples_dir / "test_image.png"), 
                       cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))
            print("✓ 测试图像已保存到 examples/test_image.png")
        except ImportError:
            print("⚠ OpenCV不可用，无法保存图像")
        
        # 创建README文件
        readme_content = """# 示例文件

这个目录包含测试图像和演示结果。

## 文件说明

- `test_image.png`: 测试用的合成图像
- `segmentation_demo.png`: 分割结果演示（运行完整测试后生成）

## 使用方法

1. GUI模式：
   ```
   python main.py --gui
   ```

2. 命令行模式：
   ```
   python main.py --cli --input examples/test_image.png --output examples/result.png
   ```
"""
        
        with open(examples_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print("✓ 示例README已创建")
        
        return True
        
    except Exception as e:
        print(f"✗ 演示输出创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("图像分割系统 - 简化测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("基本功能", test_basic_functionality),
        ("MST分割算法", test_mst_segmentation),
        ("数据结构", test_data_structures),
        ("演示输出", create_demo_output)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 通过")
        else:
            print(f"✗ {test_name} 失败")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统基本功能正常。")
        print("\n下一步:")
        print("1. 安装完整依赖: pip install -r requirements.txt")
        print("2. 运行完整测试: python test_system.py")
        print("3. 启动GUI: python main.py --gui")
        print("4. 或使用命令行: python main.py --cli --input examples/test_image.png")
    else:
        print("⚠ 部分测试失败，请检查错误信息。")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
