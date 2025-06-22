#!/usr/bin/env python3
"""
构建和打包脚本
支持多平台构建、测试和分发
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path
import zipfile
import tarfile
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from version import __version__


class Builder:
    """构建管理器"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.version = __version__
        
        # 创建构建目录
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def clean(self):
        """清理构建文件"""
        print("🧹 清理构建文件...")
        
        # 清理目录
        dirs_to_clean = [
            self.build_dir,
            self.dist_dir,
            self.project_root / "*.egg-info",
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache",
        ]
        
        for dir_pattern in dirs_to_clean:
            if "*" in str(dir_pattern):
                # 处理通配符
                parent = dir_pattern.parent
                pattern = dir_pattern.name
                for path in parent.glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                        print(f"  删除目录: {path}")
            elif dir_pattern.exists():
                shutil.rmtree(dir_pattern, ignore_errors=True)
                print(f"  删除目录: {dir_pattern}")
        
        # 清理Python缓存文件
        for root, dirs, files in os.walk(self.project_root):
            # 删除__pycache__目录
            if "__pycache__" in dirs:
                pycache_path = Path(root) / "__pycache__"
                shutil.rmtree(pycache_path, ignore_errors=True)
                dirs.remove("__pycache__")
            
            # 删除.pyc文件
            for file in files:
                if file.endswith(('.pyc', '.pyo')):
                    file_path = Path(root) / file
                    file_path.unlink(missing_ok=True)
        
        print("✅ 清理完成")
    
    def test(self):
        """运行测试"""
        print("🧪 运行测试套件...")
        
        # 运行测试
        test_cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        
        try:
            result = subprocess.run(test_cmd, cwd=self.project_root, check=True)
            print("✅ 所有测试通过")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def lint(self):
        """代码质量检查"""
        print("🔍 代码质量检查...")
        
        # 检查工具列表
        checks = [
            (["python", "-m", "flake8", ".", "--max-line-length=100"], "Flake8"),
            (["python", "-m", "black", "--check", "."], "Black"),
        ]
        
        all_passed = True
        
        for cmd, name in checks:
            try:
                subprocess.run(cmd, cwd=self.project_root, check=True, 
                             capture_output=True, text=True)
                print(f"  ✅ {name} 检查通过")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {name} 检查失败")
                if e.stdout:
                    print(f"     输出: {e.stdout}")
                if e.stderr:
                    print(f"     错误: {e.stderr}")
                all_passed = False
            except FileNotFoundError:
                print(f"  ⚠️ {name} 未安装，跳过检查")
        
        return all_passed
    
    def build_wheel(self):
        """构建wheel包"""
        print("📦 构建wheel包...")
        
        try:
            cmd = [sys.executable, "setup.py", "bdist_wheel"]
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("✅ Wheel包构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Wheel包构建失败: {e}")
            return False
    
    def build_source(self):
        """构建源码包"""
        print("📦 构建源码包...")
        
        try:
            cmd = [sys.executable, "setup.py", "sdist"]
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("✅ 源码包构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 源码包构建失败: {e}")
            return False
    
    def build_executable(self):
        """构建可执行文件"""
        print("🔨 构建可执行文件...")
        
        try:
            # 检查PyInstaller是否安装
            subprocess.run([sys.executable, "-c", "import PyInstaller"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ PyInstaller未安装，无法构建可执行文件")
            print("   请运行: pip install PyInstaller")
            return False
        
        # PyInstaller命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", f"ImageSegmentation-{self.version}",
            "--add-data", "config;config",
            "--add-data", "examples;examples",
            "--hidden-import", "PIL._tkinter_finder",
            "main.py"
        ]
        
        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("✅ 可执行文件构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 可执行文件构建失败: {e}")
            return False
    
    def create_release_package(self):
        """创建发布包"""
        print("📦 创建发布包...")
        
        release_name = f"image-segmentation-system-{self.version}"
        release_dir = self.build_dir / release_name
        
        # 创建发布目录
        if release_dir.exists():
            shutil.rmtree(release_dir)
        release_dir.mkdir(parents=True)
        
        # 复制文件
        files_to_copy = [
            "main.py",
            "quick_start.py",
            "requirements.txt",
            "README.md",
            "LICENSE",
            "version.py",
            "setup.py",
        ]
        
        dirs_to_copy = [
            "core",
            "data_structures", 
            "evaluation",
            "gui",
            "utils",
            "config",
            "examples",
            "docs",
        ]
        
        # 复制文件
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, release_dir / file_name)
        
        # 复制目录
        for dir_name in dirs_to_copy:
            src = self.project_root / dir_name
            if src.exists():
                dst = release_dir / dir_name
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", ".git*"
                ))
        
        # 创建安装脚本
        self._create_install_scripts(release_dir)
        
        # 创建压缩包
        self._create_archives(release_dir, release_name)
        
        print("✅ 发布包创建完成")
    
    def _create_install_scripts(self, release_dir):
        """创建安装脚本"""
        # Windows批处理文件
        install_bat = release_dir / "install.bat"
        install_bat.write_text("""@echo off
echo 图像分割系统安装脚本
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo 安装依赖包...
pip install -r requirements.txt

echo.
echo 安装完成！
echo 运行 python main.py 启动程序
pause
""", encoding='utf-8')
        
        # Linux/macOS shell脚本
        install_sh = release_dir / "install.sh"
        install_sh.write_text("""#!/bin/bash

echo "图像分割系统安装脚本"
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

echo "检查Python版本..."
python3 --version

echo "安装依赖包..."
pip3 install -r requirements.txt

echo
echo "安装完成！"
echo "运行 python3 main.py 启动程序"
""")
        install_sh.chmod(0o755)
    
    def _create_archives(self, release_dir, release_name):
        """创建压缩包"""
        # ZIP格式 (Windows)
        zip_path = self.dist_dir / f"{release_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(release_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(release_dir.parent)
                    zipf.write(file_path, arc_path)
        
        print(f"  创建ZIP包: {zip_path}")
        
        # TAR.GZ格式 (Linux/macOS)
        tar_path = self.dist_dir / f"{release_name}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tarf:
            tarf.add(release_dir, arcname=release_name)
        
        print(f"  创建TAR.GZ包: {tar_path}")
    
    def install_dev_dependencies(self):
        """安装开发依赖"""
        print("📦 安装开发依赖...")
        
        dev_packages = [
            "pytest>=6.0",
            "pytest-cov>=2.0", 
            "black>=21.0",
            "flake8>=3.8",
            "PyInstaller>=4.0",
        ]
        
        for package in dev_packages:
            try:
                cmd = [sys.executable, "-m", "pip", "install", package]
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✅ 安装 {package}")
            except subprocess.CalledProcessError:
                print(f"  ❌ 安装失败 {package}")
    
    def full_build(self):
        """完整构建流程"""
        print(f"🚀 开始完整构建流程 (版本 {self.version})")
        print("=" * 50)
        
        steps = [
            ("清理", self.clean),
            ("代码检查", self.lint),
            ("运行测试", self.test),
            ("构建源码包", self.build_source),
            ("构建Wheel包", self.build_wheel),
            ("创建发布包", self.create_release_package),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 步骤: {step_name}")
            if not step_func():
                print(f"❌ 构建失败于步骤: {step_name}")
                return False
        
        print("\n🎉 完整构建成功完成！")
        print(f"📦 发布文件位于: {self.dist_dir}")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="图像分割系统构建脚本")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--lint", action="store_true", help="代码质量检查")
    parser.add_argument("--build", action="store_true", help="构建包")
    parser.add_argument("--exe", action="store_true", help="构建可执行文件")
    parser.add_argument("--release", action="store_true", help="创建发布包")
    parser.add_argument("--full", action="store_true", help="完整构建流程")
    parser.add_argument("--install-dev", action="store_true", help="安装开发依赖")
    
    args = parser.parse_args()
    
    builder = Builder()
    
    if args.install_dev:
        builder.install_dev_dependencies()
    elif args.clean:
        builder.clean()
    elif args.test:
        builder.test()
    elif args.lint:
        builder.lint()
    elif args.build:
        builder.build_source()
        builder.build_wheel()
    elif args.exe:
        builder.build_executable()
    elif args.release:
        builder.create_release_package()
    elif args.full:
        builder.full_build()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
