"""
主题管理器
支持多种界面主题和动态切换
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
import json
from pathlib import Path


class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        self.current_theme = "light"
        self.themes = self._load_themes()
        self.style = ttk.Style()
        self.callbacks = []  # 主题变更回调
        
    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """加载主题配置"""
        return {
            "light": {
                "name": "浅色主题",
                "colors": {
                    "bg_primary": "#ffffff",
                    "bg_secondary": "#f8f9fa",
                    "bg_tertiary": "#e9ecef",
                    "fg_primary": "#212529",
                    "fg_secondary": "#6c757d",
                    "accent_primary": "#007bff",
                    "accent_secondary": "#28a745",
                    "accent_warning": "#ffc107",
                    "accent_danger": "#dc3545",
                    "border": "#dee2e6",
                    "shadow": "#00000020"
                },
                "fonts": {
                    "default": ("Microsoft YaHei UI", 9),
                    "heading": ("Microsoft YaHei UI", 12, "bold"),
                    "title": ("Microsoft YaHei UI", 16, "bold"),
                    "code": ("Consolas", 9),
                    "small": ("Microsoft YaHei UI", 8)
                },
                "spacing": {
                    "small": 5,
                    "medium": 10,
                    "large": 15,
                    "xlarge": 20
                }
            },
            
            "dark": {
                "name": "深色主题",
                "colors": {
                    "bg_primary": "#2b2b2b",
                    "bg_secondary": "#3c3c3c",
                    "bg_tertiary": "#4a4a4a",
                    "fg_primary": "#ffffff",
                    "fg_secondary": "#cccccc",
                    "accent_primary": "#0d7377",
                    "accent_secondary": "#14a085",
                    "accent_warning": "#f39c12",
                    "accent_danger": "#e74c3c",
                    "border": "#555555",
                    "shadow": "#00000040"
                },
                "fonts": {
                    "default": ("Microsoft YaHei UI", 9),
                    "heading": ("Microsoft YaHei UI", 12, "bold"),
                    "title": ("Microsoft YaHei UI", 16, "bold"),
                    "code": ("Consolas", 9),
                    "small": ("Microsoft YaHei UI", 8)
                },
                "spacing": {
                    "small": 5,
                    "medium": 10,
                    "large": 15,
                    "xlarge": 20
                }
            },
            
            "blue": {
                "name": "蓝色主题",
                "colors": {
                    "bg_primary": "#f0f8ff",
                    "bg_secondary": "#e6f3ff",
                    "bg_tertiary": "#cce7ff",
                    "fg_primary": "#1a365d",
                    "fg_secondary": "#2d5a87",
                    "accent_primary": "#3182ce",
                    "accent_secondary": "#2b6cb0",
                    "accent_warning": "#ed8936",
                    "accent_danger": "#e53e3e",
                    "border": "#bee3f8",
                    "shadow": "#0000001a"
                },
                "fonts": {
                    "default": ("Microsoft YaHei UI", 9),
                    "heading": ("Microsoft YaHei UI", 12, "bold"),
                    "title": ("Microsoft YaHei UI", 16, "bold"),
                    "code": ("Consolas", 9),
                    "small": ("Microsoft YaHei UI", 8)
                },
                "spacing": {
                    "small": 5,
                    "medium": 10,
                    "large": 15,
                    "xlarge": 20
                }
            },
            
            "green": {
                "name": "绿色主题",
                "colors": {
                    "bg_primary": "#f0fff4",
                    "bg_secondary": "#e6fffa",
                    "bg_tertiary": "#c6f6d5",
                    "fg_primary": "#1a202c",
                    "fg_secondary": "#2d3748",
                    "accent_primary": "#38a169",
                    "accent_secondary": "#2f855a",
                    "accent_warning": "#d69e2e",
                    "accent_danger": "#e53e3e",
                    "border": "#9ae6b4",
                    "shadow": "#0000001a"
                },
                "fonts": {
                    "default": ("Microsoft YaHei UI", 9),
                    "heading": ("Microsoft YaHei UI", 12, "bold"),
                    "title": ("Microsoft YaHei UI", 16, "bold"),
                    "code": ("Consolas", 9),
                    "small": ("Microsoft YaHei UI", 8)
                },
                "spacing": {
                    "small": 5,
                    "medium": 10,
                    "large": 15,
                    "xlarge": 20
                }
            }
        }
    
    def get_available_themes(self) -> Dict[str, str]:
        """获取可用主题列表"""
        return {key: theme["name"] for key, theme in self.themes.items()}
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self.current_theme
    
    def get_theme_config(self, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """获取主题配置"""
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, self.themes["light"])
    
    def get_color(self, color_name: str, theme_name: Optional[str] = None) -> str:
        """获取主题颜色"""
        theme = self.get_theme_config(theme_name)
        return theme["colors"].get(color_name, "#000000")
    
    def get_font(self, font_name: str, theme_name: Optional[str] = None) -> tuple:
        """获取主题字体"""
        theme = self.get_theme_config(theme_name)
        return theme["fonts"].get(font_name, ("Arial", 9))
    
    def get_spacing(self, spacing_name: str, theme_name: Optional[str] = None) -> int:
        """获取主题间距"""
        theme = self.get_theme_config(theme_name)
        return theme["spacing"].get(spacing_name, 10)
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        if theme_name not in self.themes:
            raise ValueError(f"未知主题: {theme_name}")
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # 应用TTK样式
        self._apply_ttk_styles(theme)
        
        # 通知回调
        for callback in self.callbacks:
            try:
                callback(theme_name, theme)
            except Exception as e:
                print(f"主题回调错误: {e}")
    
    def _apply_ttk_styles(self, theme: Dict[str, Any]):
        """应用TTK样式"""
        colors = theme["colors"]
        fonts = theme["fonts"]
        
        try:
            # 设置基础主题
            if self.current_theme == "dark":
                if "equilux" in self.style.theme_names():
                    self.style.theme_use("equilux")
                elif "clam" in self.style.theme_names():
                    self.style.theme_use("clam")
            else:
                if "clam" in self.style.theme_names():
                    self.style.theme_use("clam")
                elif "default" in self.style.theme_names():
                    self.style.theme_use("default")
            
            # 配置样式
            self._configure_label_styles(colors, fonts)
            self._configure_button_styles(colors, fonts)
            self._configure_frame_styles(colors, fonts)
            self._configure_entry_styles(colors, fonts)
            self._configure_progressbar_styles(colors)
            self._configure_notebook_styles(colors, fonts)
            
        except Exception as e:
            print(f"应用TTK样式失败: {e}")
    
    def _configure_label_styles(self, colors: Dict, fonts: Dict):
        """配置标签样式"""
        self.style.configure("Title.TLabel",
                           font=fonts["title"],
                           foreground=colors["fg_primary"],
                           background=colors["bg_primary"])
        
        self.style.configure("Heading.TLabel",
                           font=fonts["heading"],
                           foreground=colors["fg_primary"],
                           background=colors["bg_primary"])
        
        self.style.configure("Info.TLabel",
                           font=fonts["default"],
                           foreground=colors["fg_secondary"],
                           background=colors["bg_primary"])
        
        self.style.configure("Code.TLabel",
                           font=fonts["code"],
                           foreground=colors["fg_primary"],
                           background=colors["bg_secondary"])
    
    def _configure_button_styles(self, colors: Dict, fonts: Dict):
        """配置按钮样式"""
        self.style.configure("Modern.TButton",
                           font=fonts["default"],
                           foreground=colors["fg_primary"],
                           background=colors["bg_secondary"],
                           borderwidth=1,
                           focuscolor="none")
        
        self.style.map("Modern.TButton",
                      background=[("active", colors["bg_tertiary"]),
                                ("pressed", colors["accent_primary"])])
        
        self.style.configure("Primary.TButton",
                           font=fonts["heading"],
                           foreground="#ffffff",
                           background=colors["accent_primary"],
                           borderwidth=0,
                           focuscolor="none")
        
        self.style.map("Primary.TButton",
                      background=[("active", colors["accent_secondary"]),
                                ("pressed", colors["accent_primary"])])
        
        self.style.configure("Success.TButton",
                           font=fonts["default"],
                           foreground="#ffffff",
                           background=colors["accent_secondary"],
                           borderwidth=0)
        
        self.style.configure("Warning.TButton",
                           font=fonts["default"],
                           foreground="#000000",
                           background=colors["accent_warning"],
                           borderwidth=0)
        
        self.style.configure("Danger.TButton",
                           font=fonts["default"],
                           foreground="#ffffff",
                           background=colors["accent_danger"],
                           borderwidth=0)
    
    def _configure_frame_styles(self, colors: Dict, fonts: Dict):
        """配置框架样式"""
        self.style.configure("Card.TFrame",
                           background=colors["bg_primary"],
                           borderwidth=1,
                           relief="solid")
        
        # LabelFrame样式
        try:
            self.style.configure("Modern.TLabelFrame",
                               background=colors["bg_primary"],
                               borderwidth=2,
                               relief="groove")
            
            self.style.configure("Modern.TLabelFrame.Label",
                               font=fonts["heading"],
                               foreground=colors["fg_primary"],
                               background=colors["bg_primary"])
        except:
            pass  # 如果不支持就跳过
    
    def _configure_entry_styles(self, colors: Dict, fonts: Dict):
        """配置输入框样式"""
        self.style.configure("Modern.TEntry",
                           font=fonts["default"],
                           foreground=colors["fg_primary"],
                           fieldbackground=colors["bg_primary"],
                           borderwidth=1,
                           insertcolor=colors["fg_primary"])
    
    def _configure_progressbar_styles(self, colors: Dict):
        """配置进度条样式"""
        self.style.configure("Modern.Horizontal.TProgressbar",
                           background=colors["accent_primary"],
                           troughcolor=colors["bg_tertiary"],
                           borderwidth=0,
                           lightcolor=colors["accent_primary"],
                           darkcolor=colors["accent_primary"])
    
    def _configure_notebook_styles(self, colors: Dict, fonts: Dict):
        """配置标签页样式"""
        self.style.configure("Modern.TNotebook",
                           background=colors["bg_primary"],
                           borderwidth=0)
        
        self.style.configure("Modern.TNotebook.Tab",
                           font=fonts["default"],
                           foreground=colors["fg_secondary"],
                           background=colors["bg_secondary"],
                           padding=[12, 8])
        
        self.style.map("Modern.TNotebook.Tab",
                      background=[("selected", colors["bg_primary"]),
                                ("active", colors["bg_tertiary"])],
                      foreground=[("selected", colors["fg_primary"]),
                                ("active", colors["fg_primary"])])
    
    def add_theme_callback(self, callback):
        """添加主题变更回调"""
        self.callbacks.append(callback)
    
    def remove_theme_callback(self, callback):
        """移除主题变更回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def save_theme_preference(self, theme_name: str):
        """保存主题偏好"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / "theme_config.json"
            config = {"current_theme": theme_name}
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存主题偏好失败: {e}")
    
    def load_theme_preference(self) -> str:
        """加载主题偏好"""
        try:
            config_file = Path("config") / "theme_config.json"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("current_theme", "light")
                    
        except Exception as e:
            print(f"加载主题偏好失败: {e}")
        
        return "light"


# 全局主题管理器实例
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """获取全局主题管理器实例"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
