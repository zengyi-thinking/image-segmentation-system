"""
GUI样式管理器
处理不同Python版本的Tkinter样式兼容性问题
"""

import tkinter as tk
from tkinter import ttk
import sys


class StyleManager:
    """样式管理器，处理跨版本兼容性"""
    
    def __init__(self):
        self.style = ttk.Style()
        self.theme_available = True
        self.custom_styles_available = True
        
        # 检测Python版本和Tkinter兼容性
        self.python_version = sys.version_info
        self.setup_theme()
        self.setup_styles()
    
    def setup_theme(self):
        """设置主题，处理兼容性问题"""
        try:
            # 尝试使用现代主题
            available_themes = self.style.theme_names()
            
            if 'clam' in available_themes:
                self.style.theme_use('clam')
            elif 'alt' in available_themes:
                self.style.theme_use('alt')
            elif 'default' in available_themes:
                self.style.theme_use('default')
            else:
                print("⚠️ 警告: 使用系统默认主题")
                self.theme_available = False
                
        except Exception as e:
            print(f"⚠️ 主题设置失败: {e}")
            self.theme_available = False
    
    def setup_styles(self):
        """设置自定义样式，带兼容性检查"""
        try:
            # 基础标签样式
            self._configure_safe('Title.TLabel', {
                'font': ('Microsoft YaHei UI', 12, 'bold'),
                'foreground': '#2c3e50'
            })
            
            self._configure_safe('Info.TLabel', {
                'font': ('Microsoft YaHei UI', 9),
                'foreground': '#7f8c8d'
            })
            
            # 按钮样式
            self._configure_safe('Modern.TButton', {
                'font': ('Microsoft YaHei UI', 9),
                'padding': (10, 5)
            })
            
            self._configure_safe('Primary.TButton', {
                'font': ('Microsoft YaHei UI', 10, 'bold')
            })
            
            # 进度条样式
            self._configure_safe('Modern.Horizontal.TProgressbar', {
                'background': '#3498db',
                'troughcolor': '#ecf0f1',
                'borderwidth': 0,
                'lightcolor': '#3498db',
                'darkcolor': '#3498db'
            })
            
            # LabelFrame样式 - 这是问题的关键
            self._setup_labelframe_styles()
            
        except Exception as e:
            print(f"⚠️ 样式设置失败: {e}")
            self.custom_styles_available = False
    
    def _setup_labelframe_styles(self):
        """设置LabelFrame样式，处理兼容性问题"""
        try:
            # 尝试设置LabelFrame.Label样式（这是正确的方式）
            self._configure_safe('Heading.TLabelFrame.Label', {
                'font': ('Microsoft YaHei UI', 10, 'bold'),
                'foreground': '#34495e'
            })
            
            # 对于Python 3.13+，可能需要不同的方式
            if self.python_version >= (3, 13):
                # 尝试直接设置LabelFrame样式
                self._configure_safe('Heading.TLabelFrame', {
                    'borderwidth': 2,
                    'relief': 'groove'
                })
            
        except Exception as e:
            print(f"⚠️ LabelFrame样式设置失败: {e}")
            # 如果自定义样式失败，我们将使用默认样式
            self.custom_styles_available = False
    
    def _configure_safe(self, style_name, options):
        """安全地配置样式，捕获异常"""
        try:
            self.style.configure(style_name, **options)
        except Exception as e:
            print(f"⚠️ 样式 {style_name} 配置失败: {e}")
    
    def get_safe_style(self, preferred_style, fallback_style=None):
        """获取安全的样式名称"""
        if not self.custom_styles_available:
            return fallback_style
        
        try:
            # 检查样式是否存在
            self.style.lookup(preferred_style, 'font')
            return preferred_style
        except:
            return fallback_style
    
    def create_labelframe(self, parent, text="", padding=10, style_name=None):
        """创建兼容的LabelFrame"""
        try:
            if style_name and self.custom_styles_available:
                # 尝试使用自定义样式
                return ttk.LabelFrame(parent, text=text, padding=padding, style=style_name)
            else:
                # 使用默认样式
                frame = ttk.LabelFrame(parent, text=text, padding=padding)
                
                # 如果需要，手动设置字体
                if hasattr(frame, 'configure'):
                    try:
                        frame.configure(font=('Microsoft YaHei UI', 10, 'bold'))
                    except:
                        pass
                
                return frame
                
        except Exception as e:
            print(f"⚠️ LabelFrame创建失败: {e}")
            # 最后的备用方案：使用普通Frame
            return ttk.Frame(parent)
    
    def create_button(self, parent, text="", command=None, style_name=None, **kwargs):
        """创建兼容的按钮"""
        safe_style = self.get_safe_style(style_name)
        
        if safe_style:
            return ttk.Button(parent, text=text, command=command, style=safe_style, **kwargs)
        else:
            # 使用默认样式并手动设置字体
            button = ttk.Button(parent, text=text, command=command, **kwargs)
            try:
                button.configure(font=('Microsoft YaHei UI', 9))
            except:
                pass
            return button
    
    def create_label(self, parent, text="", style_name=None, **kwargs):
        """创建兼容的标签"""
        safe_style = self.get_safe_style(style_name)
        
        if safe_style:
            return ttk.Label(parent, text=text, style=safe_style, **kwargs)
        else:
            # 使用默认样式并手动设置字体
            label = ttk.Label(parent, text=text, **kwargs)
            
            # 根据样式名称设置字体
            if style_name == 'Title.TLabel':
                try:
                    label.configure(font=('Microsoft YaHei UI', 12, 'bold'), foreground='#2c3e50')
                except:
                    pass
            elif style_name == 'Info.TLabel':
                try:
                    label.configure(font=('Microsoft YaHei UI', 9), foreground='#7f8c8d')
                except:
                    pass
            
            return label
    
    def create_progressbar(self, parent, style_name=None, **kwargs):
        """创建兼容的进度条"""
        safe_style = self.get_safe_style(style_name)
        
        if safe_style:
            return ttk.Progressbar(parent, style=safe_style, **kwargs)
        else:
            return ttk.Progressbar(parent, **kwargs)
    
    def get_status(self):
        """获取样式管理器状态"""
        return {
            'theme_available': self.theme_available,
            'custom_styles_available': self.custom_styles_available,
            'python_version': f"{self.python_version.major}.{self.python_version.minor}",
            'available_themes': list(self.style.theme_names()) if self.theme_available else []
        }


# 全局样式管理器实例
_style_manager = None

def get_style_manager():
    """获取全局样式管理器实例"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager
