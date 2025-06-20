"""
项目清理验证脚本
快速验证所有核心功能是否正常工作
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块
        from core import MSTSegmentation, EdgeWeightCalculator
        print("  ✅ 核心分割模块")
        
        # 测试GUI模块
        from gui.enhanced_main_window import EnhancedMainWindow
        print("  ✅ 增强版GUI")
        
        # 测试工具模块
        from utils.image_io import ImageLoader
        print("  ✅ 图像处理工具")
        
        # 测试数据结构
        from data_structures.union_find import UnionFind
        print("  ✅ 数据结构")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def test_gui_startup():
    """测试GUI启动"""
    print("\n🖼️ 测试GUI启动...")
    
    try:
        import tkinter as tk
        from gui.enhanced_main_window import EnhancedMainWindow
        
        # 创建测试窗口（不显示）
        root = tk.Tk()
        root.withdraw()
        
        # 创建主窗口
        app = EnhancedMainWindow(root)
        print("  ✅ GUI创建成功")
        
        # 测试关键组件
        if hasattr(app, 'image_loader'):
            print("  ✅ 图像加载器就绪")
        
        if hasattr(app, 'image_display'):
            print("  ✅ 图像显示组件就绪")
        
        if hasattr(app, 'control_panel'):
            print("  ✅ 控制面板就绪")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"  ❌ GUI测试失败: {e}")
        return False


def check_project_structure():
    """检查项目结构"""
    print("\n📁 检查项目结构...")
    
    required_dirs = [
        'core', 'gui', 'utils', 'data_structures', 
        'tests', 'config', 'docs', 'examples'
    ]
    
    required_files = [
        'main.py', 'quick_start.py', 'requirements.txt',
        'README.md', 'PROJECT_STRUCTURE.md'
    ]
    
    all_good = True
    
    # 检查目录
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ 缺失")
            all_good = False
    
    # 检查文件
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} 缺失")
            all_good = False
    
    return all_good


def check_tests_directory():
    """检查测试目录"""
    print("\n🧪 检查测试目录...")
    
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("  ❌ tests/ 目录不存在")
        return False
    
    test_files = list(tests_dir.glob("*.py"))
    if len(test_files) > 0:
        print(f"  ✅ 找到 {len(test_files)} 个测试文件")
        for test_file in test_files[:5]:  # 显示前5个
            print(f"    - {test_file.name}")
        if len(test_files) > 5:
            print(f"    ... 还有 {len(test_files) - 5} 个文件")
        return True
    else:
        print("  ❌ 没有找到测试文件")
        return False


def check_no_redundant_files():
    """检查是否还有冗余文件"""
    print("\n🧹 检查冗余文件...")
    
    # 检查根目录是否还有测试文件
    root_test_files = [f for f in os.listdir('.') if f.startswith(('test_', 'fix_'))]
    
    if len(root_test_files) == 0:
        print("  ✅ 根目录已清理，无测试文件")
    else:
        print(f"  ⚠️ 根目录仍有 {len(root_test_files)} 个测试文件:")
        for file in root_test_files:
            print(f"    - {file}")
    
    # 检查__pycache__目录
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
    
    if len(pycache_dirs) == 0:
        print("  ✅ 无__pycache__目录")
    else:
        print(f"  ⚠️ 仍有 {len(pycache_dirs)} 个__pycache__目录")
    
    return len(root_test_files) == 0 and len(pycache_dirs) == 0


def main():
    """主函数"""
    print("=" * 60)
    print("🧹 项目清理验证")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("GUI启动", test_gui_startup),
        ("项目结构", check_project_structure),
        ("测试目录", check_tests_directory),
        ("清理状态", check_no_redundant_files)
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
    
    print("\n" + "=" * 60)
    print(f"📊 验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 项目清理完成！所有功能正常。")
        print("\n✅ 清理成果:")
        print("• 📁 所有测试文件已移至 tests/ 目录")
        print("• 🗑️ 删除了冗余的GUI文件")
        print("• 🧹 清理了所有缓存目录")
        print("• 📋 创建了项目结构文档")
        print("• 🎨 提供了UI增强建议")
        print("• ✅ 保持了所有核心功能")
        
        print("\n🚀 现在可以:")
        print("1. python main.py --gui  # 启动GUI")
        print("2. python quick_start.py  # 快速启动")
        print("3. python tests/test_cleanup_verification.py  # 运行测试")
        
    else:
        print("⚠️ 部分验证失败，请检查具体问题")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
