"""
图形用户界面模块
包含GUI相关的组件和窗口
"""

# 导入兼容版本的组件
try:
    from .main_window_refactored import MainWindowRefactored
    from .style_manager import get_style_manager, StyleManager
    from .control_panel import ControlPanel
    from .image_display import ImageDisplay

    # 主要导出兼容版本
    MainWindow = MainWindowRefactored

    __all__ = [
        'MainWindow',
        'MainWindowRefactored',
        'StyleManager',
        'get_style_manager',
        'ControlPanel',
        'ImageDisplay'
    ]

except ImportError as e:
    print(f"⚠️ 兼容版GUI组件导入失败: {e}")

    # 备用方案：导入原版
    try:
        from .main_window import MainWindow

        __all__ = [
            'MainWindow'
        ]

    except ImportError as e2:
        print(f"❌ 原版GUI组件也导入失败: {e2}")

        # 最后的备用方案
        MainWindow = None
        __all__ = []
