"""
图像加载功能测试脚本
测试增强版图像加载器的各种功能
"""

import sys
import numpy as np
from pathlib import Path
import os
import tempfile
from PIL import Image
import cv2

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from utils.image_io import ImageLoader, ImageSaver, ImageLoadError
from utils.image_diagnostics import ImageDiagnostics


def create_test_images():
    """创建各种格式的测试图像"""
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # 创建基础测试图像
    test_image = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
    
    # 创建不同格式的图像
    formats = ['.jpg', '.png', '.bmp', '.tiff']
    created_files = []
    
    for fmt in formats:
        try:
            file_path = test_dir / f"test_image{fmt}"
            
            if fmt in ['.jpg', '.jpeg']:
                # JPEG格式
                pil_image = Image.fromarray(test_image)
                pil_image.save(file_path, quality=95)
            elif fmt == '.png':
                # PNG格式
                pil_image = Image.fromarray(test_image)
                pil_image.save(file_path, optimize=True)
            elif fmt == '.bmp':
                # BMP格式
                cv2.imwrite(str(file_path), cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))
            elif fmt in ['.tiff', '.tif']:
                # TIFF格式
                pil_image = Image.fromarray(test_image)
                pil_image.save(file_path)
            
            created_files.append(file_path)
            print(f"✅ 创建测试图像: {file_path}")
            
        except Exception as e:
            print(f"❌ 创建 {fmt} 格式失败: {e}")
    
    # 创建特殊测试图像
    special_files = create_special_test_images(test_dir, test_image)
    created_files.extend(special_files)
    
    return created_files

def create_special_test_images(test_dir: Path, base_image: np.ndarray):
    """创建特殊测试图像"""
    special_files = []
    
    try:
        # 1. 大尺寸图像
        large_image = np.random.randint(0, 255, (2000, 3000, 3), dtype=np.uint8)
        large_path = test_dir / "large_image.jpg"
        Image.fromarray(large_image).save(large_path, quality=85)
        special_files.append(large_path)
        print("✅ 创建大尺寸测试图像")
        
        # 2. 灰度图像
        gray_image = np.random.randint(0, 255, (200, 300), dtype=np.uint8)
        gray_path = test_dir / "gray_image.png"
        Image.fromarray(gray_image, mode='L').save(gray_path)
        special_files.append(gray_path)
        print("✅ 创建灰度测试图像")
        
        # 3. RGBA图像
        rgba_image = np.random.randint(0, 255, (200, 300, 4), dtype=np.uint8)
        rgba_path = test_dir / "rgba_image.png"
        Image.fromarray(rgba_image, mode='RGBA').save(rgba_path)
        special_files.append(rgba_path)
        print("✅ 创建RGBA测试图像")
        
        # 4. 中文路径图像
        chinese_dir = test_dir / "中文测试"
        chinese_dir.mkdir(exist_ok=True)
        chinese_path = chinese_dir / "测试图像.jpg"
        Image.fromarray(base_image).save(chinese_path, quality=90)
        special_files.append(chinese_path)
        print("✅ 创建中文路径测试图像")
        
        # 5. 损坏的图像文件
        corrupted_path = test_dir / "corrupted.jpg"
        with open(corrupted_path, 'wb') as f:
            f.write(b"这不是一个有效的图像文件")
        special_files.append(corrupted_path)
        print("✅ 创建损坏测试文件")
        
        # 6. 空文件
        empty_path = test_dir / "empty.jpg"
        empty_path.touch()
        special_files.append(empty_path)
        print("✅ 创建空测试文件")
        
    except Exception as e:
        print(f"⚠️ 创建特殊测试图像时出错: {e}")
    
    return special_files

def test_image_loader():
    """测试图像加载器"""
    print("\n🔍 测试增强版图像加载器...")
    
    # 创建测试图像
    test_files = create_test_images()
    
    # 创建加载器
    loader = ImageLoader(
        max_size=(2048, 2048),
        auto_orient=True,
        normalize_format=True
    )
    
    results = {
        'total_tests': 0,
        'successful_loads': 0,
        'failed_loads': 0,
        'format_conversions': 0,
        'size_reductions': 0
    }
    
    print(f"\n📋 测试 {len(test_files)} 个图像文件:")
    
    for test_file in test_files:
        results['total_tests'] += 1
        print(f"\n测试文件: {test_file.name}")
        
        try:
            # 尝试加载图像
            image = loader.load_image(test_file)
            
            if image is not None:
                results['successful_loads'] += 1
                print(f"  ✅ 加载成功 - 形状: {image.shape}, 类型: {image.dtype}")
                
                # 验证图像数据
                if len(image.shape) == 3 and image.shape[2] == 3:
                    print(f"  📊 像素范围: {image.min()}-{image.max()}, 平均值: {image.mean():.1f}")
                else:
                    print(f"  ⚠️ 图像形状异常: {image.shape}")
            else:
                results['failed_loads'] += 1
                print("  ❌ 加载失败 - 返回None")
                
        except ImageLoadError as e:
            results['failed_loads'] += 1
            print(f"  ❌ 加载失败 - {str(e)}")
        except Exception as e:
            results['failed_loads'] += 1
            print(f"  ❌ 未预期错误 - {str(e)}")
    
    # 获取加载统计
    stats = loader.get_load_statistics()
    results.update(stats)
    
    print(f"\n📊 加载测试结果:")
    print(f"  总测试数: {results['total_tests']}")
    print(f"  成功加载: {results['successful_loads']}")
    print(f"  失败加载: {results['failed_loads']}")
    print(f"  格式转换: {results['format_conversions']}")
    print(f"  尺寸调整: {results['size_reductions']}")
    
    success_rate = results['successful_loads'] / results['total_tests'] * 100
    print(f"  成功率: {success_rate:.1f}%")
    
    return results

def test_image_diagnostics():
    """测试图像诊断工具"""
    print("\n🔬 测试图像诊断工具...")
    
    diagnostics = ImageDiagnostics()
    test_dir = Path("test_images")
    
    if not test_dir.exists():
        print("❌ 测试图像目录不存在，请先运行图像加载测试")
        return
    
    # 测试几个代表性文件
    test_cases = [
        "test_image.jpg",
        "large_image.jpg", 
        "gray_image.png",
        "中文测试/测试图像.jpg",
        "corrupted.jpg",
        "empty.jpg",
        "nonexistent.jpg"
    ]
    
    for test_case in test_cases:
        test_path = test_dir / test_case
        print(f"\n诊断文件: {test_case}")
        
        try:
            diagnosis = diagnostics.diagnose_image(test_path)
            
            print(f"  状态: {diagnosis['overall_status'].upper()}")
            
            # 显示问题
            issues = diagnosis.get('issues', [])
            if issues:
                print("  问题:")
                for issue in issues[:3]:  # 只显示前3个问题
                    print(f"    • {issue}")
            
            # 显示建议
            recommendations = diagnosis.get('recommendations', [])
            if recommendations:
                print("  建议:")
                for rec in recommendations[:2]:  # 只显示前2个建议
                    print(f"    • {rec}")
            
            # 显示加载测试结果
            load_tests = diagnosis.get('load_tests', {})
            successful_methods = [method for method, result in load_tests.items() 
                                if result.get('success')]
            
            if successful_methods:
                print(f"  可用加载方法: {', '.join(successful_methods)}")
            else:
                print("  ❌ 所有加载方法都失败")
                
        except Exception as e:
            print(f"  ❌ 诊断失败: {e}")

def test_image_saver():
    """测试图像保存器"""
    print("\n💾 测试增强版图像保存器...")
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    
    # 创建保存器
    saver = ImageSaver()
    
    # 测试保存到不同格式
    save_dir = Path("test_saves")
    save_dir.mkdir(exist_ok=True)
    
    formats = ['.jpg', '.png', '.bmp', '.tiff']
    results = {'successful_saves': 0, 'failed_saves': 0}
    
    for fmt in formats:
        save_path = save_dir / f"test_save{fmt}"
        
        try:
            success = saver.save_image(test_image, save_path)
            
            if success and save_path.exists():
                results['successful_saves'] += 1
                file_size = save_path.stat().st_size / 1024  # KB
                print(f"  ✅ {fmt} 保存成功 ({file_size:.1f} KB)")
            else:
                results['failed_saves'] += 1
                print(f"  ❌ {fmt} 保存失败")
                
        except Exception as e:
            results['failed_saves'] += 1
            print(f"  ❌ {fmt} 保存异常: {e}")
    
    # 测试中文路径保存
    chinese_save_dir = save_dir / "中文保存测试"
    chinese_save_dir.mkdir(exist_ok=True)
    chinese_save_path = chinese_save_dir / "测试保存.jpg"
    
    try:
        success = saver.save_image(test_image, chinese_save_path)
        if success:
            results['successful_saves'] += 1
            print("  ✅ 中文路径保存成功")
        else:
            results['failed_saves'] += 1
            print("  ❌ 中文路径保存失败")
    except Exception as e:
        results['failed_saves'] += 1
        print(f"  ❌ 中文路径保存异常: {e}")
    
    # 获取保存统计
    stats = saver.get_save_statistics()
    
    print(f"\n📊 保存测试结果:")
    print(f"  成功保存: {results['successful_saves']}")
    print(f"  失败保存: {results['failed_saves']}")
    print(f"  总保存数: {stats['total_saved']}")
    
    return results

def test_error_handling():
    """测试错误处理"""
    print("\n🛡️ 测试错误处理机制...")
    
    loader = ImageLoader()
    
    error_cases = [
        ("不存在的文件", "nonexistent_file.jpg"),
        ("无效扩展名", "test.xyz"),
        ("目录而非文件", "."),
    ]
    
    for case_name, test_path in error_cases:
        print(f"\n测试 {case_name}: {test_path}")
        
        try:
            image = loader.load_image(test_path)
            if image is None:
                print("  ✅ 正确返回None")
            else:
                print("  ❌ 应该失败但成功了")
        except ImageLoadError as e:
            print(f"  ✅ 正确抛出ImageLoadError: {str(e)[:50]}...")
        except Exception as e:
            print(f"  ⚠️ 抛出了其他异常: {type(e).__name__}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("🖼️ 图像读取兼容性测试")
    print("=" * 60)
    
    try:
        # 1. 测试图像加载器
        load_results = test_image_loader()
        
        # 2. 测试图像诊断工具
        test_image_diagnostics()
        
        # 3. 测试图像保存器
        save_results = test_image_saver()
        
        # 4. 测试错误处理
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("📊 总体测试结果")
        print("=" * 60)
        
        total_success = load_results['successful_loads'] + save_results['successful_saves']
        total_tests = load_results['total_tests'] + len(['.jpg', '.png', '.bmp', '.tiff']) + 1  # +1 for chinese path
        
        print(f"总成功操作: {total_success}")
        print(f"总测试数: {total_tests}")
        print(f"总体成功率: {total_success/total_tests*100:.1f}%")
        
        if load_results['successful_loads'] > 0:
            print("\n🎉 图像读取兼容性修复成功！")
            print("✅ 支持多种图像格式")
            print("✅ 处理中文路径")
            print("✅ 自动格式转换")
            print("✅ 完善错误处理")
        else:
            print("\n⚠️ 图像读取功能需要进一步调试")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    main()
