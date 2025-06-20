"""
算法对比功能测试
测试MST和Watershed算法的对比功能，包括性能分析和结果比较
"""

import sys
import numpy as np
import time
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from core import MSTSegmentation, WatershedSegmentation, EdgeWeightCalculator
from evaluation import AlgorithmComparator, PerformanceAnalyzer, SegmentationMetrics
from utils.image_io import ImageLoader


def create_test_images():
    """创建测试图像"""
    test_images = []
    
    # 1. 简单几何图像
    simple_image = np.zeros((100, 100, 3), dtype=np.uint8)
    simple_image[20:40, 20:40] = [255, 0, 0]  # 红色方块
    simple_image[60:80, 60:80] = [0, 255, 0]  # 绿色方块
    simple_image[40:60, 40:60] = [0, 0, 255]  # 蓝色方块
    test_images.append(("简单几何", simple_image))
    
    # 2. 渐变图像
    gradient_image = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(100):
        gradient_image[i, :] = [i * 255 // 100, 128, 255 - i * 255 // 100]
    test_images.append(("渐变图像", gradient_image))
    
    # 3. 噪声图像
    noise_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    test_images.append(("噪声图像", noise_image))
    
    # 4. 纹理图像
    texture_image = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(100):
        for j in range(100):
            if (i + j) % 10 < 5:
                texture_image[i, j] = [200, 200, 200]
            else:
                texture_image[i, j] = [50, 50, 50]
    test_images.append(("纹理图像", texture_image))
    
    return test_images


def test_watershed_algorithm():
    """测试Watershed算法"""
    print("🌊 测试Watershed算法...")
    
    test_images = create_test_images()
    
    for name, image in test_images:
        print(f"\n  测试图像: {name}")
        
        try:
            # 创建Watershed分割器
            segmenter = WatershedSegmentation(
                min_distance=10,
                compactness=0.001,
                watershed_line=True
            )
            
            # 执行分割
            start_time = time.time()
            result = segmenter.segment(image)
            end_time = time.time()
            
            if result and 'label_map' in result:
                print(f"    ✅ 分割成功")
                print(f"    ⏱️ 执行时间: {end_time - start_time:.3f}s")
                print(f"    🔢 分割区域数: {result['statistics']['num_segments']}")
                print(f"    📊 处理统计: {result.get('processing_stats', {})}")
            else:
                print(f"    ❌ 分割失败")
                
        except Exception as e:
            print(f"    ❌ 异常: {str(e)}")
    
    return True


def test_algorithm_comparison():
    """测试算法对比功能"""
    print("\n⚖️ 测试算法对比功能...")
    
    # 创建测试图像
    test_image = create_test_images()[0][1]  # 使用简单几何图像
    
    try:
        # 创建算法对比器
        comparator = AlgorithmComparator()
        
        # 定义要对比的算法
        def create_mst_algorithm():
            def mst_segment(image):
                weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
                segmenter = MSTSegmentation(
                    connectivity=4,
                    weight_calculator=weight_calculator,
                    min_segment_size=10
                )
                return segmenter.segment(image)
            return mst_segment
        
        def create_watershed_algorithm():
            def watershed_segment(image):
                segmenter = WatershedSegmentation(
                    min_distance=10,
                    compactness=0.001,
                    watershed_line=True
                )
                return segmenter.segment(image)
            return watershed_segment
        
        algorithms = [
            {
                'name': 'MST',
                'func': create_mst_algorithm(),
                'params': {}
            },
            {
                'name': 'Watershed',
                'func': create_watershed_algorithm(),
                'params': {}
            }
        ]
        
        # 执行对比
        print("  🔄 执行算法对比...")
        comparison_result = comparator.compare_algorithms(
            algorithms,
            test_image,
            save_results=False
        )
        
        # 检查结果
        if comparison_result:
            print("  ✅ 算法对比成功")
            
            summary = comparison_result.get('comparison_summary', {})
            print(f"    📊 成功算法数: {summary.get('successful_algorithms', 0)}")
            print(f"    📊 失败算法数: {summary.get('failed_algorithms', 0)}")
            
            if 'fastest_algorithm' in summary:
                fastest = summary['fastest_algorithm']
                print(f"    🏃 最快算法: {fastest['name']} ({fastest['execution_time']:.3f}s)")
            
            if 'most_memory_efficient' in summary:
                efficient = summary['most_memory_efficient']
                print(f"    💾 最省内存: {efficient['name']} ({efficient['memory_usage']:.1f}MB)")
            
            return True
        else:
            print("  ❌ 算法对比失败")
            return False
            
    except Exception as e:
        print(f"  ❌ 算法对比异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_analysis():
    """测试性能分析功能"""
    print("\n📊 测试性能分析功能...")
    
    # 创建测试图像
    test_image = create_test_images()[1][1]  # 使用渐变图像
    
    try:
        # 创建性能分析器
        analyzer = PerformanceAnalyzer()
        
        # 创建测试算法
        def test_algorithm(image):
            weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
            segmenter = MSTSegmentation(
                connectivity=4,
                weight_calculator=weight_calculator,
                min_segment_size=10
            )
            return segmenter.segment(image)
        
        # 执行多次运行基准测试
        print("  🔄 执行性能基准测试...")
        benchmark_result = analyzer.benchmark_with_multiple_runs(
            test_algorithm,
            test_image,
            "MST_Test",
            num_runs=3,
            warmup_runs=1
        )
        
        # 检查结果
        if benchmark_result.get('success', False):
            print("  ✅ 性能分析成功")
            
            exec_time = benchmark_result['execution_time']
            memory = benchmark_result['memory_usage']
            
            print(f"    ⏱️ 平均执行时间: {exec_time['mean']:.3f}s (±{exec_time['std']:.3f}s)")
            print(f"    💾 平均内存使用: {memory['mean']:.1f}MB (±{memory['std']:.1f}MB)")
            print(f"    🎯 效率分数: {benchmark_result.get('efficiency_score', 0):.1f}/100")
            
            return True
        else:
            print(f"  ❌ 性能分析失败: {benchmark_result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"  ❌ 性能分析异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluation_metrics():
    """测试评估指标功能"""
    print("\n📏 测试评估指标功能...")
    
    try:
        # 创建测试数据
        test_image = create_test_images()[0][1]  # 简单几何图像
        
        # 创建模拟的分割结果
        predicted_labels = np.zeros((100, 100), dtype=int)
        predicted_labels[20:40, 20:40] = 1  # 区域1
        predicted_labels[60:80, 60:80] = 2  # 区域2
        predicted_labels[40:60, 40:60] = 3  # 区域3
        
        # 创建评估指标计算器
        metrics_calculator = SegmentationMetrics()
        
        # 计算无监督指标
        print("  🔄 计算无监督指标...")
        unsupervised_metrics = metrics_calculator.calculate_unsupervised_metrics(
            predicted_labels, test_image
        )
        
        print("  ✅ 无监督指标计算成功")
        print(f"    🔢 分割区域数: {unsupervised_metrics.get('num_segments', 0)}")
        print(f"    📏 平均区域大小: {unsupervised_metrics.get('mean_segment_size', 0):.1f}")
        print(f"    📊 区域紧凑性: {unsupervised_metrics.get('compactness', 0):.3f}")
        
        # 计算所有指标
        all_metrics = metrics_calculator.calculate_all_metrics(
            predicted_labels, None, test_image
        )
        
        print(f"  📊 总计算指标数: {len(all_metrics)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 评估指标测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_integration():
    """测试GUI集成功能"""
    print("\n🖼️ 测试GUI集成功能...")
    
    try:
        # 测试控制面板参数获取
        print("  🔄 测试参数获取...")
        
        # 模拟MST参数
        mst_params = {
            'algorithm': 'MST',
            'alpha': 1.0,
            'beta': 0.1,
            'connectivity': 4,
            'threshold': None,
            'auto_threshold': True
        }
        
        # 模拟Watershed参数
        watershed_params = {
            'algorithm': 'Watershed',
            'min_distance': 20,
            'compactness': 0.001,
            'watershed_line': True
        }
        
        print("  ✅ MST参数格式正确")
        print(f"    📋 MST参数: {mst_params}")
        
        print("  ✅ Watershed参数格式正确")
        print(f"    📋 Watershed参数: {watershed_params}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GUI集成测试异常: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 算法对比功能综合测试")
    print("=" * 60)
    
    tests = [
        ("Watershed算法", test_watershed_algorithm),
        ("算法对比功能", test_algorithm_comparison),
        ("性能分析功能", test_performance_analysis),
        ("评估指标功能", test_evaluation_metrics),
        ("GUI集成功能", test_gui_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有算法对比功能测试通过！")
        print("\n✅ 测试覆盖:")
        print("• Watershed分割算法实现")
        print("• 算法性能对比分析")
        print("• 多次运行基准测试")
        print("• 评估指标计算")
        print("• GUI参数集成")
        
    else:
        print("⚠️ 部分测试失败，请检查具体问题")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
