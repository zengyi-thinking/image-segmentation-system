"""
Watershed算法专项测试
详细测试Watershed分割算法的各种参数配置和边界情况
"""

import sys
import numpy as np
import time
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from core import WatershedSegmentation
from data_structures.segmentation_result import SegmentationResult


def create_test_scenarios():
    """创建各种测试场景"""
    scenarios = []
    
    # 1. 简单二值图像
    binary_image = np.zeros((50, 50, 3), dtype=np.uint8)
    binary_image[10:20, 10:20] = 255  # 白色方块
    binary_image[30:40, 30:40] = 255  # 另一个白色方块
    scenarios.append(("二值图像", binary_image))
    
    # 2. 多区域图像
    multi_region = np.zeros((60, 60, 3), dtype=np.uint8)
    multi_region[10:20, 10:20] = [255, 0, 0]    # 红色
    multi_region[10:20, 40:50] = [0, 255, 0]    # 绿色
    multi_region[40:50, 10:20] = [0, 0, 255]    # 蓝色
    multi_region[40:50, 40:50] = [255, 255, 0]  # 黄色
    scenarios.append(("多区域图像", multi_region))
    
    # 3. 渐变图像
    gradient = np.zeros((40, 40, 3), dtype=np.uint8)
    for i in range(40):
        for j in range(40):
            gradient[i, j] = [i * 6, j * 6, (i + j) * 3]
    scenarios.append(("渐变图像", gradient))
    
    # 4. 噪声图像
    noise = np.random.randint(0, 255, (30, 30, 3), dtype=np.uint8)
    scenarios.append(("噪声图像", noise))
    
    # 5. 边界测试图像
    edge_test = np.zeros((20, 20, 3), dtype=np.uint8)
    edge_test[0:10, :] = 100   # 上半部分
    edge_test[10:20, :] = 200  # 下半部分
    scenarios.append(("边界测试", edge_test))
    
    return scenarios


def test_parameter_variations():
    """测试不同参数配置"""
    print("🔧 测试参数变化...")
    
    # 创建测试图像
    test_image = np.zeros((40, 40, 3), dtype=np.uint8)
    test_image[10:20, 10:20] = [255, 0, 0]
    test_image[25:35, 25:35] = [0, 255, 0]
    
    # 参数配置列表
    parameter_configs = [
        {"min_distance": 5, "compactness": 0.0001, "watershed_line": True},
        {"min_distance": 10, "compactness": 0.001, "watershed_line": True},
        {"min_distance": 20, "compactness": 0.01, "watershed_line": True},
        {"min_distance": 15, "compactness": 0.005, "watershed_line": False},
        {"min_distance": 8, "compactness": 0.002, "watershed_line": True},
    ]
    
    results = []
    
    for i, params in enumerate(parameter_configs):
        print(f"\n  配置 {i+1}: {params}")
        
        try:
            # 创建分割器
            segmenter = WatershedSegmentation(**params)
            
            # 执行分割
            start_time = time.time()
            result = segmenter.segment(test_image)
            end_time = time.time()
            
            if result and 'label_map' in result:
                execution_time = end_time - start_time
                num_segments = result['statistics']['num_segments']
                
                print(f"    ✅ 成功 - 区域数: {num_segments}, 时间: {execution_time:.3f}s")
                
                results.append({
                    'params': params,
                    'success': True,
                    'num_segments': num_segments,
                    'execution_time': execution_time,
                    'processing_stats': result.get('processing_stats', {})
                })
            else:
                print(f"    ❌ 分割失败")
                results.append({
                    'params': params,
                    'success': False
                })
                
        except Exception as e:
            print(f"    ❌ 异常: {str(e)}")
            results.append({
                'params': params,
                'success': False,
                'error': str(e)
            })
    
    # 分析结果
    successful_results = [r for r in results if r.get('success', False)]
    
    if successful_results:
        print(f"\n  📊 成功配置: {len(successful_results)}/{len(parameter_configs)}")
        
        # 找出最快的配置
        fastest = min(successful_results, key=lambda x: x['execution_time'])
        print(f"  🏃 最快配置: {fastest['params']} ({fastest['execution_time']:.3f}s)")
        
        # 找出分割区域最多的配置
        most_segments = max(successful_results, key=lambda x: x['num_segments'])
        print(f"  🔢 最多区域: {most_segments['params']} ({most_segments['num_segments']} 区域)")
    
    return len(successful_results) > 0


def test_edge_cases():
    """测试边界情况"""
    print("\n🚨 测试边界情况...")
    
    edge_cases = [
        ("空图像", np.zeros((10, 10, 3), dtype=np.uint8)),
        ("单色图像", np.full((15, 15, 3), 128, dtype=np.uint8)),
        ("极小图像", np.random.randint(0, 255, (5, 5, 3), dtype=np.uint8)),
        ("单像素差异", np.full((10, 10, 3), 100, dtype=np.uint8)),
    ]
    
    # 为单像素差异图像添加一个不同的像素
    edge_cases[3][1][5, 5] = [200, 200, 200]
    
    passed_cases = 0
    
    for case_name, test_image in edge_cases:
        print(f"\n  测试: {case_name}")
        
        try:
            segmenter = WatershedSegmentation(
                min_distance=5,
                compactness=0.001,
                watershed_line=True
            )
            
            result = segmenter.segment(test_image)
            
            if result and 'label_map' in result:
                print(f"    ✅ 处理成功 - 区域数: {result['statistics']['num_segments']}")
                passed_cases += 1
            else:
                print(f"    ⚠️ 处理完成但无有效结果")
                
        except Exception as e:
            print(f"    ❌ 异常: {str(e)}")
    
    print(f"\n  📊 边界情况通过: {passed_cases}/{len(edge_cases)}")
    return passed_cases >= len(edge_cases) // 2  # 至少一半通过


def test_processing_stats():
    """测试处理统计信息"""
    print("\n📊 测试处理统计...")
    
    # 创建测试图像
    test_image = np.zeros((30, 30, 3), dtype=np.uint8)
    test_image[5:15, 5:15] = [255, 100, 50]
    test_image[20:25, 20:25] = [50, 255, 100]
    
    try:
        segmenter = WatershedSegmentation(
            min_distance=8,
            compactness=0.002,
            watershed_line=True
        )
        
        result = segmenter.segment(test_image)
        
        if result and 'processing_stats' in result:
            stats = result['processing_stats']
            
            print("  ✅ 处理统计可用")
            print(f"    ⏱️ 总时间: {stats.get('total_time', 0):.3f}s")
            print(f"    🔧 预处理时间: {stats.get('preprocessing_time', 0):.3f}s")
            print(f"    📐 梯度计算时间: {stats.get('gradient_time', 0):.3f}s")
            print(f"    🎯 标记检测时间: {stats.get('markers_time', 0):.3f}s")
            print(f"    🌊 分水岭时间: {stats.get('watershed_time', 0):.3f}s")
            print(f"    🔄 后处理时间: {stats.get('postprocessing_time', 0):.3f}s")
            
            # 验证时间统计的合理性
            total_components = (
                stats.get('preprocessing_time', 0) +
                stats.get('gradient_time', 0) +
                stats.get('markers_time', 0) +
                stats.get('watershed_time', 0) +
                stats.get('postprocessing_time', 0)
            )
            
            total_time = stats.get('total_time', 0)
            
            if abs(total_time - total_components) < 0.1:  # 允许小误差
                print("  ✅ 时间统计一致性检查通过")
                return True
            else:
                print(f"  ⚠️ 时间统计不一致: 总时间={total_time:.3f}s, 组件总和={total_components:.3f}s")
                return False
        else:
            print("  ❌ 处理统计不可用")
            return False
            
    except Exception as e:
        print(f"  ❌ 处理统计测试异常: {str(e)}")
        return False


def test_result_consistency():
    """测试结果一致性"""
    print("\n🔄 测试结果一致性...")
    
    # 创建测试图像
    test_image = np.zeros((25, 25, 3), dtype=np.uint8)
    test_image[5:12, 5:12] = [200, 100, 50]
    test_image[15:22, 15:22] = [50, 200, 100]
    
    # 使用相同参数多次运行
    params = {
        "min_distance": 10,
        "compactness": 0.001,
        "watershed_line": True
    }
    
    results = []
    
    for run in range(3):
        try:
            segmenter = WatershedSegmentation(**params)
            result = segmenter.segment(test_image)
            
            if result and 'label_map' in result:
                results.append({
                    'run': run + 1,
                    'num_segments': result['statistics']['num_segments'],
                    'label_map_shape': result['label_map'].shape,
                    'unique_labels': len(np.unique(result['label_map']))
                })
            
        except Exception as e:
            print(f"  ❌ 运行 {run + 1} 异常: {str(e)}")
    
    if len(results) >= 2:
        # 检查一致性
        first_result = results[0]
        consistent = True
        
        for result in results[1:]:
            if (result['num_segments'] != first_result['num_segments'] or
                result['label_map_shape'] != first_result['label_map_shape']):
                consistent = False
                break
        
        if consistent:
            print(f"  ✅ 结果一致性检查通过 ({len(results)} 次运行)")
            print(f"    🔢 分割区域数: {first_result['num_segments']}")
            print(f"    📐 标签图尺寸: {first_result['label_map_shape']}")
            return True
        else:
            print(f"  ⚠️ 结果不一致")
            for result in results:
                print(f"    运行 {result['run']}: {result['num_segments']} 区域")
            return False
    else:
        print(f"  ❌ 有效运行次数不足: {len(results)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🌊 Watershed算法专项测试")
    print("=" * 60)
    
    tests = [
        ("参数变化测试", test_parameter_variations),
        ("边界情况测试", test_edge_cases),
        ("处理统计测试", test_processing_stats),
        ("结果一致性测试", test_result_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 Watershed算法所有测试通过！")
        print("\n✅ 测试覆盖:")
        print("• 多种参数配置验证")
        print("• 边界情况处理")
        print("• 处理统计信息准确性")
        print("• 结果一致性验证")
        
    else:
        print("⚠️ 部分测试失败，请检查算法实现")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
