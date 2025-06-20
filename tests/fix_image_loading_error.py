"""
图像加载错误修复脚本
专门解决GUI图像加载过程中的"NoneType object is not callable"错误
"""

import sys
import traceback
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))


def create_test_image():
    """创建测试图像文件"""
    try:
        # 创建一个简单的测试图像
        test_image = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        
        # 保存为临时文件
        temp_dir = Path("temp_test")
        temp_dir.mkdir(exist_ok=True)
        
        test_file = temp_dir / "test_image.png"
        pil_image = Image.fromarray(test_image)
        pil_image.save(test_file)
        
        print(f"✅ 创建测试图像: {test_file}")
        return str(test_file)
        
    except Exception as e:
        print(f"❌ 创建测试图像失败: {e}")
        return None


def test_image_loader():
    """测试图像加载器"""
    print("\n🔍 测试图像加载器...")
    
    try:
        from utils.image_io import ImageLoader, ImageLoadError
        
        # 创建加载器
        loader = ImageLoader(
            max_size=(2048, 2048),
            auto_orient=True,
            normalize_format=True
        )
        
        # 测试统计信息方法
        print("  测试统计信息方法...")
        try:
            stats = loader.get_load_statistics()
            print(f"    ✅ 统计信息: {stats}")
        except Exception as e:
            print(f"    ❌ 统计信息获取失败: {e}")
            return False
        
        # 创建测试图像
        test_file = create_test_image()
        if not test_file:
            return False
        
        # 测试图像加载
        print("  测试图像加载...")
        try:
            image = loader.load_image(test_file)
            if image is not None:
                print(f"    ✅ 图像加载成功: {image.shape}")
                
                # 再次测试统计信息
                stats = loader.get_load_statistics()
                print(f"    ✅ 加载后统计信息: {stats}")
                
            else:
                print("    ❌ 图像加载返回None")
                return False
                
        except Exception as e:
            print(f"    ❌ 图像加载失败: {e}")
            traceback.print_exc()
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 图像加载器测试失败: {e}")
        traceback.print_exc()
        return False


def test_enhanced_image_display():
    """测试增强版图像显示组件"""
    print("\n🖼️ 测试增强版图像显示组件...")
    
    try:
        import tkinter as tk
        from gui.enhanced_image_display import EnhancedImageDisplay
        from utils.image_io import ImageLoader
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 创建图像加载器
        loader = ImageLoader()
        
        # 创建图像显示组件
        test_frame = tk.Frame(root)
        display = EnhancedImageDisplay(test_frame, loader)
        
        # 测试回调函数设置
        print("  测试回调函数设置...")
        
        def test_image_click(x, y):
            print(f"    图像点击: ({x}, {y})")
        
        def test_zoom_change(zoom):
            print(f"    缩放变化: {zoom}")
        
        # 设置回调函数
        display.on_image_click = test_image_click
        display.on_zoom_change = test_zoom_change
        
        print("    ✅ 回调函数设置成功")
        
        # 测试图像显示
        print("  测试图像显示...")
        test_file = create_test_image()
        if test_file:
            image = loader.load_image(test_file)
            if image is not None:
                try:
                    display.display_image(image)
                    print("    ✅ 图像显示成功")
                except Exception as e:
                    print(f"    ❌ 图像显示失败: {e}")
                    traceback.print_exc()
                    return False
        
        # 测试缩放功能
        print("  测试缩放功能...")
        try:
            display.set_zoom(1.5)
            print("    ✅ 缩放功能正常")
        except Exception as e:
            print(f"    ❌ 缩放功能失败: {e}")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 图像显示组件测试失败: {e}")
        traceback.print_exc()
        return False


def test_enhanced_main_window():
    """测试增强版主窗口"""
    print("\n🏠 测试增强版主窗口...")
    
    try:
        import tkinter as tk
        from gui.enhanced_main_window import EnhancedMainWindow
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()
        
        # 创建主窗口
        app = EnhancedMainWindow(root)
        
        # 测试图像加载器
        print("  测试图像加载器初始化...")
        if hasattr(app, 'image_loader') and app.image_loader:
            print("    ✅ 图像加载器初始化成功")
            
            # 测试统计信息
            try:
                stats = app.image_loader.get_load_statistics()
                print(f"    ✅ 统计信息获取成功: {stats}")
            except Exception as e:
                print(f"    ❌ 统计信息获取失败: {e}")
                return False
        else:
            print("    ❌ 图像加载器未正确初始化")
            return False
        
        # 测试图像显示组件
        print("  测试图像显示组件初始化...")
        if hasattr(app, 'image_display') and app.image_display:
            print("    ✅ 图像显示组件初始化成功")
            
            # 检查回调函数
            if hasattr(app.image_display, 'on_image_click') and app.image_display.on_image_click:
                print("    ✅ 图像点击回调已设置")
            else:
                print("    ⚠️ 图像点击回调未设置")
            
            if hasattr(app.image_display, 'on_zoom_change') and app.image_display.on_zoom_change:
                print("    ✅ 缩放变化回调已设置")
            else:
                print("    ⚠️ 缩放变化回调未设置")
        else:
            print("    ❌ 图像显示组件未正确初始化")
            return False
        
        # 测试模拟图像加载
        print("  测试模拟图像加载...")
        test_file = create_test_image()
        if test_file:
            try:
                # 模拟加载过程
                image = app.image_loader.load_image(test_file)
                if image is not None:
                    app.current_image = image
                    app.image_display.display_image(image)
                    print("    ✅ 模拟图像加载成功")
                else:
                    print("    ❌ 模拟图像加载返回None")
                    return False
            except Exception as e:
                print(f"    ❌ 模拟图像加载失败: {e}")
                traceback.print_exc()
                return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 主窗口测试失败: {e}")
        traceback.print_exc()
        return False


def test_callback_safety():
    """测试回调函数安全性"""
    print("\n🛡️ 测试回调函数安全性...")
    
    try:
        import tkinter as tk
        from gui.enhanced_image_display import EnhancedImageDisplay
        
        # 创建测试环境
        root = tk.Tk()
        root.withdraw()
        
        test_frame = tk.Frame(root)
        display = EnhancedImageDisplay(test_frame)
        
        # 测试None回调
        print("  测试None回调...")
        display.on_image_click = None
        display.on_zoom_change = None
        
        # 模拟事件
        class MockEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        try:
            display.on_mouse_click(MockEvent(100, 100))
            print("    ✅ None回调处理正常")
        except Exception as e:
            print(f"    ❌ None回调处理失败: {e}")
            return False
        
        # 测试错误回调
        print("  测试错误回调...")
        def error_callback(*args):
            raise Exception("测试错误")
        
        display.on_image_click = error_callback
        display.on_zoom_change = error_callback
        
        try:
            display.on_mouse_click(MockEvent(100, 100))
            display.set_zoom(1.5)
            print("    ✅ 错误回调处理正常")
        except Exception as e:
            print(f"    ❌ 错误回调处理失败: {e}")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 回调安全性测试失败: {e}")
        traceback.print_exc()
        return False


def cleanup_test_files():
    """清理测试文件"""
    try:
        import shutil
        temp_dir = Path("temp_test")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("🧹 清理测试文件完成")
    except Exception as e:
        print(f"⚠️ 清理测试文件失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 图像加载错误修复工具")
    print("=" * 60)
    
    tests = [
        ("图像加载器", test_image_loader),
        ("图像显示组件", test_enhanced_image_display),
        ("主窗口", test_enhanced_main_window),
        ("回调安全性", test_callback_safety)
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
    
    # 清理测试文件
    cleanup_test_files()
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！图像加载错误已修复。")
        print("\n🔧 修复内容:")
        print("• ✅ 修复了图像加载统计信息的安全访问")
        print("• ✅ 增强了回调函数的安全性检查")
        print("• ✅ 添加了图像显示组件的错误处理")
        print("• ✅ 完善了主窗口的异常捕获")
        
        print("\n💡 使用建议:")
        print("1. 重新启动GUI应用程序")
        print("2. 尝试加载不同格式的图像文件")
        print("3. 测试图像的缩放和拖拽功能")
        print("4. 如果仍有问题，请查看控制台错误信息")
        
    else:
        print("⚠️ 部分测试失败，可能需要进一步调试。")
        print("请检查错误信息并重新运行修复脚本。")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
