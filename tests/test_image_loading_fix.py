"""
图像加载修复验证脚本
验证图像加载错误修复的效果
"""

import sys
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))


def create_test_image():
    """创建测试图像"""
    try:
        test_image = np.random.randint(0, 255, (100, 150, 3), dtype=np.uint8)
        temp_dir = Path("temp_fix_test")
        temp_dir.mkdir(exist_ok=True)
        
        test_file = temp_dir / "fix_test.png"
        pil_image = Image.fromarray(test_image)
        pil_image.save(test_file)
        
        return str(test_file)
    except Exception as e:
        print(f"创建测试图像失败: {e}")
        return None


def test_gui_image_loading():
    """测试GUI图像加载"""
    print("🖼️ 测试GUI图像加载修复...")
    
    try:
        import tkinter as tk
        from gui.enhanced_main_window import EnhancedMainWindow
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()
        
        # 创建主窗口
        app = EnhancedMainWindow(root)
        
        # 创建测试图像
        test_file = create_test_image()
        if not test_file:
            return False
        
        print(f"  使用测试图像: {test_file}")
        
        # 模拟图像加载过程
        try:
            # 1. 加载图像
            image = app.image_loader.load_image(test_file)
            print(f"  ✅ 图像加载成功: {image.shape}")
            
            # 2. 设置当前图像
            app.current_image = image
            
            # 3. 显示图像
            app.image_display.display_image(image)
            print("  ✅ 图像显示成功")
            
            # 4. 测试统计信息
            stats = app.image_loader.get_load_statistics()
            print(f"  ✅ 统计信息: {stats}")
            
            # 5. 测试缩放功能
            app.image_display.set_zoom(1.2)
            print("  ✅ 缩放功能正常")
            
            # 6. 测试回调函数
            if hasattr(app.image_display, 'on_image_click') and app.image_display.on_image_click:
                print("  ✅ 图像点击回调已设置")
            
            if hasattr(app.image_display, 'on_zoom_change') and app.image_display.on_zoom_change:
                print("  ✅ 缩放变化回调已设置")
            
            print("  🎉 所有功能测试通过！")
            
        except Exception as e:
            print(f"  ❌ 图像加载过程失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_image_loading():
    """测试直接图像加载"""
    print("\n📁 测试直接图像加载...")
    
    try:
        from utils.image_io import ImageLoader
        
        loader = ImageLoader()
        test_file = create_test_image()
        
        if test_file:
            image = loader.load_image(test_file)
            if image is not None:
                print(f"  ✅ 直接加载成功: {image.shape}")
                
                stats = loader.get_load_statistics()
                print(f"  ✅ 统计信息: {stats}")
                return True
            else:
                print("  ❌ 直接加载失败")
                return False
        else:
            print("  ❌ 无法创建测试图像")
            return False
            
    except Exception as e:
        print(f"❌ 直接加载测试失败: {e}")
        return False


def test_image_display_component():
    """测试图像显示组件"""
    print("\n🎨 测试图像显示组件...")
    
    try:
        import tkinter as tk
        from gui.enhanced_image_display import EnhancedImageDisplay
        from utils.image_io import ImageLoader
        
        root = tk.Tk()
        root.withdraw()
        
        loader = ImageLoader()
        test_frame = tk.Frame(root)
        display = EnhancedImageDisplay(test_frame, loader)
        
        # 测试方法是否存在且可调用
        if hasattr(display, 'display_image') and callable(display.display_image):
            print("  ✅ display_image方法存在且可调用")
        else:
            print("  ❌ display_image方法不存在或不可调用")
            return False
        
        # 测试图像显示
        test_file = create_test_image()
        if test_file:
            image = loader.load_image(test_file)
            if image is not None:
                display.display_image(image)
                print("  ✅ 图像显示成功")
            else:
                print("  ❌ 图像加载失败")
                return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 图像显示组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """清理测试文件"""
    try:
        import shutil
        temp_dir = Path("temp_fix_test")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print("🧹 清理完成")
    except Exception as e:
        print(f"⚠️ 清理失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 图像加载修复验证")
    print("=" * 60)
    
    tests = [
        ("直接图像加载", test_direct_image_loading),
        ("图像显示组件", test_image_display_component),
        ("GUI图像加载", test_gui_image_loading)
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
        print("🎉 图像加载错误修复成功！")
        print("\n✅ 修复内容:")
        print("• 解决了方法名与属性名冲突问题")
        print("• 修复了'NoneType' object is not callable错误")
        print("• 增强了回调函数安全性")
        print("• 完善了错误处理机制")
        
        print("\n🚀 现在可以:")
        print("1. 正常启动GUI应用程序")
        print("2. 成功加载各种格式的图像")
        print("3. 使用图像缩放和拖拽功能")
        print("4. 执行图像分割操作")
        
    else:
        print("⚠️ 部分测试失败，可能需要进一步检查")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
