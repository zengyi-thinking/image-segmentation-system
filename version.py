"""
版本信息文件
"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# 版本历史
VERSION_HISTORY = {
    "2.0.0": {
        "date": "2025-06-22",
        "features": [
            "全面的滚动功能增强",
            "新增日志系统和异常处理",
            "性能监控和内存管理",
            "进度指示器和用户体验改进",
            "完善的测试套件",
            "详细的文档和帮助系统",
            "配置管理和部署优化"
        ],
        "improvements": [
            "优化代码结构和质量",
            "增强错误处理机制",
            "改进GUI交互体验",
            "提升算法性能",
            "完善主题兼容性"
        ],
        "bugfixes": [
            "修复图像加载问题",
            "解决内存泄漏",
            "修正界面显示异常",
            "优化滚动性能"
        ]
    },
    "1.0.0": {
        "date": "2024-12-01",
        "features": [
            "基础MST分割算法",
            "Watershed分割算法",
            "GUI界面",
            "算法对比功能",
            "性能分析"
        ]
    }
}

def get_version():
    """获取当前版本"""
    return __version__

def get_version_info():
    """获取版本信息元组"""
    return __version_info__

def get_version_history():
    """获取版本历史"""
    return VERSION_HISTORY

def print_version_info():
    """打印版本信息"""
    current = VERSION_HISTORY.get(__version__, {})
    
    print(f"图像分割系统 v{__version__}")
    print(f"发布日期: {current.get('date', '未知')}")
    
    if 'features' in current:
        print("\n新功能:")
        for feature in current['features']:
            print(f"  • {feature}")
    
    if 'improvements' in current:
        print("\n改进:")
        for improvement in current['improvements']:
            print(f"  • {improvement}")
    
    if 'bugfixes' in current:
        print("\n修复:")
        for bugfix in current['bugfixes']:
            print(f"  • {bugfix}")

if __name__ == "__main__":
    print_version_info()
