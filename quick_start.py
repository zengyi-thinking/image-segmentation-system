"""
图像分割系统快速启动脚本
提供简单的启动选项和系统检查
"""

import sys
import os
from pathlib import Path
import subprocess

def check_dependencies():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")
    
    required_packages = [
        'numpy', 'opencv-python', 'pillow', 'matplotlib', 'scipy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'pillow':
                import PIL
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def run_system_test():
    """运行系统测试"""
    print("\n🧪 运行系统测试...")
    
    try:
        # 添加项目路径
        sys.path.insert(0, str(Path(__file__).parent))
        
        # 简单的导入测试
        from core.edge_weights import EdgeWeightCalculator
        from core.mst_segmentation import MSTSegmentation
        from utils.visualization import SegmentationVisualizer
        
        print("✅ 核心模块导入成功")
        
        # 简单的功能测试
        import numpy as np
        test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        weight_calc = EdgeWeightCalculator()
        segmenter = MSTSegmentation(weight_calculator=weight_calc)
        
        print("✅ 算法组件创建成功")
        print("✅ 系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        return False

def launch_gui():
    """启动GUI界面"""
    print("\n🚀 启动GUI界面...")
    
    try:
        import tkinter as tk
        from gui.main_window import MainWindow
        
        root = tk.Tk()
        app = MainWindow(root)
        
        print("✅ GUI界面已启动")
        print("💡 提示: 关闭窗口即可退出程序")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("请检查tkinter是否正确安装")

def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🖼️  图像分割系统 - 快速启动")
    print("="*60)
    print("请选择操作:")
    print("1. 🔍 检查系统依赖")
    print("2. 🧪 运行系统测试")
    print("3. 🚀 启动GUI界面")
    print("4. 📖 查看使用说明")
    print("5. 🔧 安装依赖包")
    print("0. ❌ 退出程序")
    print("="*60)

def show_usage():
    """显示使用说明"""
    print("\n📖 使用说明:")
    print("-"*40)
    print("🎯 GUI模式 (推荐):")
    print("   python main.py --gui")
    print("   或直接运行: python quick_start.py")
    print()
    print("💻 命令行模式:")
    print("   python main.py --cli --input image.jpg --output result.png")
    print()
    print("📁 项目结构:")
    print("   core/          - 核心算法模块")
    print("   gui/           - 图形界面模块")
    print("   utils/         - 工具模块")
    print("   examples/      - 示例图像")
    print("   docs/          - 文档")
    print()
    print("🔧 参数说明:")
    print("   --alpha        - 颜色权重 (0.1-5.0)")
    print("   --beta         - 空间权重 (0.01-1.0)")
    print("   --connectivity - 连接性 (4或8)")
    print("   --threshold    - 分割阈值")
    print()
    print("💡 更多信息请查看 docs/user_manual.md")

def install_dependencies():
    """安装依赖包"""
    print("\n🔧 安装依赖包...")
    
    try:
        # 检查pip是否可用
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        
        print("📦 正在安装依赖包...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖包安装成功")
        else:
            print(f"❌ 安装失败: {result.stderr}")
            
    except subprocess.CalledProcessError:
        print("❌ pip不可用，请手动安装依赖包")
    except FileNotFoundError:
        print("❌ requirements.txt文件不存在")

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("\n请输入选项 (0-5): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                check_dependencies()
            elif choice == "2":
                if run_system_test():
                    print("\n🎉 系统运行正常，可以开始使用！")
            elif choice == "3":
                if check_dependencies() and run_system_test():
                    launch_gui()
                else:
                    print("❌ 系统检查失败，请先解决依赖问题")
            elif choice == "4":
                show_usage()
            elif choice == "5":
                install_dependencies()
            else:
                print("❌ 无效选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    # 设置工作目录
    os.chdir(Path(__file__).parent)
    
    # 如果没有参数，显示菜单
    if len(sys.argv) == 1:
        main()
    else:
        # 直接启动GUI
        if check_dependencies() and run_system_test():
            launch_gui()
        else:
            print("❌ 系统检查失败")
            sys.exit(1)
