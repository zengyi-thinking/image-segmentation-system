"""
项目清理后的功能验证测试
确保所有核心功能在清理后仍然正常工作
"""

import sys
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))


def create_test_image():
    """创建测试图像"""
    try:
        test_image = np.random.randint(0, 255, (100, 150, 3), dtype=np.uint8)
        temp_dir = Path("temp_cleanup_test")
        temp_dir.mkdir(exist_ok=True)
        
        test_file = temp_dir / "cleanup_test.png"
        pil_image = Image.fromarray(test_image)
        pil_image.save(test_file)
        
        return str(test_file)
    except Exception as e:
        print(f"创建测试图像失败: {e}")
        return None


def test_core_functionality():
    """测试核心分割功能"""
    print("🔬 测试核心分割功能...")
    
    try:
        from core import MSTSegmentation, EdgeWeightCalculator
        from utils.image_io import ImageLoader
        
        # 创建测试图像
        test_file = create_test_image()
        if not test_file:
            return False
        
        # 加载图像
        loader = ImageLoader()
        image = loader.load_image(test_file)
        
        if image is None:
            print("  ❌ 图像加载失败")
            return False
        
        print(f"  ✅ 图像加载成功: {image.shape}")
        
        # 创建分割器
        weight_calc = EdgeWeightCalculator(alpha=1.0, beta=0.1)
        segmenter = MSTSegmentation(connectivity=4, weight_calculator=weight_calc)
        
        # 执行分割
        result = segmenter.segment(image)
        
        if result and 'label_map' in result:
            print(f"  ✅ 分割成功: {result['statistics']['num_segments']} 个区域")
            return True
        else:
            print("  ❌ 分割失败")
            return False
            
    except Exception as e:
        print(f"❌ 核心功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_imports():
    """测试GUI模块导入"""
    print("\n🖼️ 测试GUI模块导入...")
    
    try:
        # 测试增强版主窗口
        from gui.enhanced_main_window import EnhancedMainWindow
        print("  ✅ 增强版主窗口导入成功")
        
        # 测试原版主窗口
        from gui.main_window import MainWindow
        print("  ✅ 原版主窗口导入成功")
        
        # 测试控制面板
        from gui.control_panel import ControlPanel
        print("  ✅ 控制面板导入成功")
        
        # 测试图像显示组件
        from gui.enhanced_image_display import EnhancedImageDisplay
        print("  ✅ 增强版图像显示组件导入成功")
        
        # 测试主题管理器
        from gui.theme_manager import get_theme_manager
        print("  ✅ 主题管理器导入成功")
        
        # 测试样式管理器
        from gui.style_manager import get_style_manager
        print("  ✅ 样式管理器导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utils_functionality():
    """测试工具模块功能"""
    print("\n🛠️ 测试工具模块功能...")
    
    try:
        from utils.image_io import ImageLoader, ImageSaver
        from utils.visualization import SegmentationVisualizer
        from utils.image_diagnostics import ImageDiagnostics
        
        # 测试图像加载器
        loader = ImageLoader()
        stats = loader.get_load_statistics()
        print(f"  ✅ 图像加载器: {stats}")
        
        # 测试图像保存器
        saver = ImageSaver()
        save_stats = saver.get_save_statistics()
        print(f"  ✅ 图像保存器: {save_stats}")
        
        # 测试可视化器
        visualizer = SegmentationVisualizer()
        print("  ✅ 分割可视化器创建成功")
        
        # 测试诊断工具
        diagnostics = ImageDiagnostics()
        print("  ✅ 图像诊断工具创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_structures():
    """测试数据结构模块"""
    print("\n📊 测试数据结构模块...")
    
    try:
        from data_structures.union_find import UnionFind, SegmentationUnionFind
        from data_structures.segmentation_result import SegmentationResult
        from data_structures.pixel_graph import PixelGraph
        
        # 测试并查集
        uf = UnionFind(10)
        uf.union(0, 1)
        print(f"  ✅ 基础并查集: connected(0,1) = {uf.connected(0, 1)}")
        
        # 测试分割并查集
        seg_uf = SegmentationUnionFind(10, 10)
        print("  ✅ 分割并查集创建成功")
        
        # 测试分割结果
        label_map = np.zeros((10, 10), dtype=int)
        test_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        result = SegmentationResult(label_map, test_image, "测试", {})
        print(f"  ✅ 分割结果: {result.statistics['num_segments']} 个区域")
        
        # 测试像素图
        graph = PixelGraph(10, 10, connectivity=4)
        print("  ✅ 像素图创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_entry_points():
    """测试主入口点"""
    print("\n🚀 测试主入口点...")
    
    try:
        # 测试main.py导入
        import main
        print("  ✅ main.py 导入成功")
        
        # 测试quick_start.py导入
        import quick_start
        print("  ✅ quick_start.py 导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 主入口点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """清理测试文件"""
    try:
        import shutil
        temp_dir = Path("temp_cleanup_test")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print("🧹 清理完成")
    except Exception as e:
        print(f"⚠️ 清理失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🧹 项目清理后功能验证")
    print("=" * 60)
    
    tests = [
        ("核心分割功能", test_core_functionality),
        ("GUI模块导入", test_gui_imports),
        ("工具模块功能", test_utils_functionality),
        ("数据结构模块", test_data_structures),
        ("主入口点", test_main_entry_points)
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
    
    cleanup()
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 项目清理成功！所有核心功能正常工作。")
        print("\n✅ 清理完成的内容:")
        print("• 移动所有测试文件到 tests/ 目录")
        print("• 删除冗余的GUI文件")
        print("• 清理所有 __pycache__ 目录")
        print("• 更新导入引用")
        print("• 保持所有核心功能完整")
        
    else:
        print("⚠️ 部分测试失败，可能需要进一步检查")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
