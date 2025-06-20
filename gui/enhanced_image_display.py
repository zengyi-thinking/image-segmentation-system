"""
增强版图像显示组件
支持缩放、拖拽、动画等高级功能
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance
import numpy as np
from typing import Optional, Tuple, Callable
import math

from .theme_manager import get_theme_manager


class EnhancedImageDisplay:
    """增强版图像显示组件"""
    
    def __init__(self, parent, image_loader=None):
        """
        初始化增强版图像显示组件
        
        Args:
            parent: 父容器
            image_loader: 图像加载器实例
        """
        self.parent = parent
        self.image_loader = image_loader
        self.theme_manager = get_theme_manager()
        
        # 图像数据
        self.original_image = None
        self.current_image = None
        self.photo_image = None  # 重命名以避免与方法名冲突
        
        # 显示状态
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.pan_x = 0
        self.pan_y = 0
        
        # 交互状态
        self.is_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # 动画状态
        self.animation_id = None
        self.fade_alpha = 1.0
        
        # 回调函数
        self.on_image_click = None
        self.on_zoom_change = None
        
        # 创建界面
        self.create_widgets()
        self.setup_bindings()
        
        # 应用主题
        self.apply_theme()
        self.theme_manager.add_theme_callback(self._on_theme_change)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        self.create_toolbar()
        
        # 图像显示区域
        self.create_image_area()
        
        # 状态栏
        self.create_status_bar()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 缩放控制
        zoom_frame = ttk.LabelFrame(toolbar_frame, text="🔍 缩放控制", padding=5)
        zoom_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # 缩小按钮
        self.zoom_out_btn = ttk.Button(zoom_frame, text="➖", width=3,
                                      command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        # 缩放显示
        self.zoom_var = tk.StringVar(value="100%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var, width=8)
        zoom_label.pack(side=tk.LEFT, padx=5)
        
        # 放大按钮
        self.zoom_in_btn = ttk.Button(zoom_frame, text="➕", width=3,
                                     command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        # 适应窗口按钮
        self.fit_btn = ttk.Button(zoom_frame, text="📐", width=3,
                                 command=self.fit_to_window)
        self.fit_btn.pack(side=tk.LEFT, padx=2)
        
        # 实际大小按钮
        self.actual_size_btn = ttk.Button(zoom_frame, text="1:1", width=3,
                                         command=self.actual_size)
        self.actual_size_btn.pack(side=tk.LEFT, padx=2)
        
        # 视图控制
        view_frame = ttk.LabelFrame(toolbar_frame, text="👁️ 视图控制", padding=5)
        view_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # 重置视图按钮
        self.reset_btn = ttk.Button(view_frame, text="🔄", width=3,
                                   command=self.reset_view)
        self.reset_btn.pack(side=tk.LEFT, padx=2)
        
        # 全屏按钮
        self.fullscreen_btn = ttk.Button(view_frame, text="⛶", width=3,
                                        command=self.toggle_fullscreen)
        self.fullscreen_btn.pack(side=tk.LEFT, padx=2)
        
        # 图像信息
        info_frame = ttk.LabelFrame(toolbar_frame, text="ℹ️ 图像信息", padding=5)
        info_frame.pack(side=tk.RIGHT)
        
        self.info_var = tk.StringVar(value="无图像")
        info_label = ttk.Label(info_frame, textvariable=self.info_var)
        info_label.pack()
    
    def create_image_area(self):
        """创建图像显示区域"""
        # 创建带滚动条的画布
        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 画布
        self.canvas = tk.Canvas(canvas_frame, 
                               highlightthickness=0,
                               cursor="hand2")
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, 
                                   command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL,
                                   command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set,
                             xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 添加占位符
        self.add_placeholder()
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 鼠标位置
        self.mouse_pos_var = tk.StringVar(value="鼠标位置: -")
        mouse_label = ttk.Label(status_frame, textvariable=self.mouse_pos_var)
        mouse_label.pack(side=tk.LEFT)
        
        # 像素值
        self.pixel_value_var = tk.StringVar(value="像素值: -")
        pixel_label = ttk.Label(status_frame, textvariable=self.pixel_value_var)
        pixel_label.pack(side=tk.RIGHT)
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # 滚轮缩放
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
        # 键盘事件
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.focus_set()
        
        # 窗口大小变化
        self.canvas.bind("<Configure>", self.on_canvas_configure)
    
    def add_placeholder(self):
        """添加占位符"""
        self.canvas.delete("placeholder")
        
        # 获取主题颜色
        bg_color = self.theme_manager.get_color("bg_secondary")
        fg_color = self.theme_manager.get_color("fg_secondary")
        font = self.theme_manager.get_font("heading")
        
        self.canvas.configure(bg=bg_color)
        
        # 添加占位符文本
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text="🖼️ 请加载图像文件\n\n💡 支持拖拽、缩放、平移操作",
            font=font,
            fill=fg_color,
            justify=tk.CENTER,
            tags="placeholder"
        )
    
    def display_image(self, image: np.ndarray, reset_view: bool = True):
        """
        显示图像
        
        Args:
            image: 要显示的图像
            reset_view: 是否重置视图
        """
        if image is None:
            return
        
        self.original_image = image.copy()
        self.current_image = image.copy()
        
        if reset_view:
            self.reset_view()
        else:
            self.update_display()
        
        # 更新图像信息
        h, w = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        self.info_var.set(f"{w}×{h}×{channels}")
        
        # 淡入动画
        self.fade_in_animation()
    
    def update_display(self):
        """更新图像显示"""
        if self.original_image is None:
            return
        
        try:
            # 计算显示尺寸
            h, w = self.original_image.shape[:2]
            display_w = int(w * self.zoom_factor)
            display_h = int(h * self.zoom_factor)
            
            # 调整图像大小
            if self.zoom_factor != 1.0:
                pil_image = Image.fromarray(self.original_image)
                pil_image = pil_image.resize((display_w, display_h), Image.Resampling.LANCZOS)
                self.current_image = np.array(pil_image)
            else:
                self.current_image = self.original_image.copy()
            
            # 转换为PhotoImage
            pil_image = Image.fromarray(self.current_image)
            
            # 应用淡入效果
            if self.fade_alpha < 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(self.fade_alpha)
            
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # 清除画布
            self.canvas.delete("image")
            self.canvas.delete("placeholder")

            # 显示图像
            self.canvas.create_image(
                self.pan_x, self.pan_y,
                anchor=tk.NW,
                image=self.photo_image,
                tags="image"
            )
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # 更新缩放显示
            self.zoom_var.set(f"{self.zoom_factor*100:.0f}%")
            
            # 更新按钮状态
            self.update_button_states()
            
        except Exception as e:
            print(f"更新图像显示失败: {e}")
    
    def zoom_in(self):
        """放大"""
        new_zoom = min(self.zoom_factor * 1.2, self.max_zoom)
        self.set_zoom(new_zoom)
    
    def zoom_out(self):
        """缩小"""
        new_zoom = max(self.zoom_factor / 1.2, self.min_zoom)
        self.set_zoom(new_zoom)
    
    def set_zoom(self, zoom_factor: float):
        """设置缩放比例"""
        if self.original_image is None:
            return
        
        self.zoom_factor = max(self.min_zoom, min(zoom_factor, self.max_zoom))
        self.update_display()
        
        if self.on_zoom_change and callable(self.on_zoom_change):
            try:
                self.on_zoom_change(self.zoom_factor)
            except Exception as e:
                print(f"缩放回调函数错误: {e}")
    
    def fit_to_window(self):
        """适应窗口大小"""
        if self.original_image is None:
            return
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:
            return
        
        img_h, img_w = self.original_image.shape[:2]
        
        # 计算适应比例
        scale_w = (canvas_w - 20) / img_w
        scale_h = (canvas_h - 20) / img_h
        scale = min(scale_w, scale_h)
        
        self.set_zoom(scale)
        self.center_image()
    
    def actual_size(self):
        """实际大小"""
        self.set_zoom(1.0)
        self.center_image()
    
    def center_image(self):
        """居中显示图像"""
        if self.original_image is None:
            return
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        img_h, img_w = self.original_image.shape[:2]
        display_w = int(img_w * self.zoom_factor)
        display_h = int(img_h * self.zoom_factor)
        
        self.pan_x = (canvas_w - display_w) // 2
        self.pan_y = (canvas_h - display_h) // 2
        
        self.update_display()
    
    def reset_view(self):
        """重置视图"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        if self.original_image is not None:
            self.fit_to_window()
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        # 这里可以实现全屏功能
        pass
    
    def on_mouse_click(self, event):
        """鼠标点击事件"""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.is_dragging = True
        
        try:
            self.canvas.configure(cursor="move")
        except tk.TclError:
            # 如果光标设置失败，使用默认光标
            pass
        
        if self.on_image_click and callable(self.on_image_click):
            try:
                # 转换为图像坐标
                img_x = (event.x - self.pan_x) / self.zoom_factor
                img_y = (event.y - self.pan_y) / self.zoom_factor
                self.on_image_click(img_x, img_y)
            except Exception as e:
                print(f"图像点击回调函数错误: {e}")
    
    def on_mouse_drag(self, event):
        """鼠标拖拽事件"""
        if not self.is_dragging:
            return
        
        # 计算移动距离
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        
        # 更新平移位置
        self.pan_x += dx
        self.pan_y += dy
        
        # 更新显示
        self.update_display()
        
        # 更新鼠标位置
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        self.is_dragging = False
        try:
            self.canvas.configure(cursor="hand2")
        except tk.TclError:
            # 如果光标设置失败，使用默认光标
            pass
    
    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if self.original_image is None:
            return
        
        # 更新鼠标位置显示
        img_x = (event.x - self.pan_x) / self.zoom_factor
        img_y = (event.y - self.pan_y) / self.zoom_factor
        
        self.mouse_pos_var.set(f"鼠标位置: ({img_x:.0f}, {img_y:.0f})")
        
        # 更新像素值显示
        if (0 <= img_x < self.original_image.shape[1] and 
            0 <= img_y < self.original_image.shape[0]):
            
            pixel = self.original_image[int(img_y), int(img_x)]
            if len(pixel) == 3:
                self.pixel_value_var.set(f"像素值: RGB({pixel[0]}, {pixel[1]}, {pixel[2]})")
            else:
                self.pixel_value_var.set(f"像素值: {pixel}")
        else:
            self.pixel_value_var.set("像素值: -")
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮事件"""
        if self.original_image is None:
            return
        
        # 获取滚轮方向
        if event.delta > 0 or event.num == 4:
            # 向上滚动，放大
            self.zoom_in()
        else:
            # 向下滚动，缩小
            self.zoom_out()
    
    def on_key_press(self, event):
        """键盘按键事件"""
        if event.keysym == "plus" or event.keysym == "equal":
            self.zoom_in()
        elif event.keysym == "minus":
            self.zoom_out()
        elif event.keysym == "0":
            self.actual_size()
        elif event.keysym == "f":
            self.fit_to_window()
        elif event.keysym == "r":
            self.reset_view()
    
    def on_canvas_configure(self, event):
        """画布大小变化事件"""
        # 更新占位符位置
        if self.original_image is None:
            self.add_placeholder()
    
    def fade_in_animation(self):
        """淡入动画"""
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
        
        self.fade_alpha = 0.0
        self._animate_fade_in()
    
    def _animate_fade_in(self):
        """执行淡入动画"""
        self.fade_alpha += 0.1
        
        if self.fade_alpha >= 1.0:
            self.fade_alpha = 1.0
            self.update_display()
            return
        
        self.update_display()
        self.animation_id = self.canvas.after(50, self._animate_fade_in)
    
    def update_button_states(self):
        """更新按钮状态"""
        # 缩放按钮状态
        if self.zoom_factor >= self.max_zoom:
            self.zoom_in_btn.configure(state=tk.DISABLED)
        else:
            self.zoom_in_btn.configure(state=tk.NORMAL)
        
        if self.zoom_factor <= self.min_zoom:
            self.zoom_out_btn.configure(state=tk.DISABLED)
        else:
            self.zoom_out_btn.configure(state=tk.NORMAL)
    
    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_theme_config()
        colors = theme["colors"]
        
        # 更新画布颜色
        self.canvas.configure(bg=colors["bg_secondary"])
        
        # 更新占位符
        if self.original_image is None:
            self.add_placeholder()
    
    def _on_theme_change(self, theme_name: str, theme_config: dict):
        """主题变更回调"""
        self.apply_theme()
    
    def clear_image(self):
        """清除图像"""
        self.original_image = None
        self.current_image = None
        self.photo_image = None

        self.canvas.delete("image")
        self.add_placeholder()

        self.info_var.set("无图像")
        self.mouse_pos_var.set("鼠标位置: -")
        self.pixel_value_var.set("像素值: -")
    
    def get_current_view_info(self) -> dict:
        """获取当前视图信息"""
        return {
            "zoom_factor": self.zoom_factor,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y,
            "has_image": self.original_image is not None
        }
