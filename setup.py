"""
图像分割系统安装配置文件
支持pip安装和打包分发
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取requirements.txt
def read_requirements():
    requirements_file = this_directory / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# 读取版本信息
def get_version():
    version_file = this_directory / "version.py"
    if version_file.exists():
        exec(open(version_file).read())
        return locals()['__version__']
    return "2.0.0"

setup(
    name="image-segmentation-system",
    version=get_version(),
    author="Image Segmentation Team",
    author_email="team@example.com",
    description="一个功能强大的图像分割系统，提供多种先进的分割算法",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/image-segmentation-system",
    project_urls={
        "Bug Tracker": "https://github.com/your-repo/image-segmentation-system/issues",
        "Documentation": "https://your-docs-site.com",
        "Source Code": "https://github.com/your-repo/image-segmentation-system",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "gpu": [
            "cupy-cuda11x>=9.0",
            "GPUtil>=1.4",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "image-segmentation=main:main",
            "img-seg=main:main",
        ],
        "gui_scripts": [
            "image-segmentation-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
        "config": ["*.json", "*.yaml"],
        "examples": ["*.png", "*.jpg", "*.jpeg"],
        "docs": ["*.md", "*.rst"],
    },
    zip_safe=False,
    keywords=[
        "image processing",
        "image segmentation", 
        "computer vision",
        "MST algorithm",
        "watershed algorithm",
        "GUI application",
        "scientific computing"
    ],
)
