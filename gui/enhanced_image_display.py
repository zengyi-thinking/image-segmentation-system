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

        # 增强的滚动条 - 始终可见
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                        command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL,
                                        command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set,
                             xscrollcommand=self.h_scrollbar.set)

        # 布局 - 滚动条始终显示
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # 滚动增强功能
        self.scroll_sensitivity = 1.0
        self.smooth_scroll_enabled = True
        self.auto_scroll_enabled = True

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

        # 增强的滚轮事件 - 支持缩放和滚动
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux

        # 水平滚轮支持 (Shift + 滚轮)
        self.canvas.bind("<Shift-MouseWheel>", self.on_horizontal_scroll)
        self.canvas.bind("<Shift-Button-4>", self.on_horizontal_scroll)  # Linux
        self.canvas.bind("<Shift-Button-5>", self.on_horizontal_scroll)  # Linux

        # 增强的键盘事件
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.bind("<KeyPress>", self.on_key_press)

        # 方向键滚动
        self.canvas.bind("<Up>", self.on_arrow_key)
        self.canvas.bind("<Down>", self.on_arrow_key)
        self.canvas.bind("<Left>", self.on_arrow_key)
        self.canvas.bind("<Right>", self.on_arrow_key)

        # Page Up/Down 滚动
        self.canvas.bind("<Prior>", self.on_page_key)  # Page Up
        self.canvas.bind("<Next>", self.on_page_key)   # Page Down

        # Home/End 键
        self.canvas.bind("<Home>", self.on_home_end_key)
        self.canvas.bind("<End>", self.on_home_end_key)

        self.canvas.focus_set()

        # 窗口大小变化
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # 滚动条事件绑定
        self.v_scrollbar.bind("<Button-1>", self.on_scrollbar_click)
        self.h_scrollbar.bind("<Button-1>", self.on_scrollbar_click)

        # 触控板/触摸屏手势支持
        self.setup_gesture_support()

    def setup_gesture_support(self):
        """设置手势支持"""
        # 双击缩放
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        # 右键菜单
        self.canvas.bind("<Button-3>", self.on_right_click)

        # 中键拖拽
        self.canvas.bind("<Button-2>", self.on_middle_click)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_release)

        # 触控板手势模拟 (通过组合键)
        self.canvas.bind("<Control-Button-1>", self.on_gesture_start)
        self.canvas.bind("<Control-B1-Motion>", self.on_gesture_move)
        self.canvas.bind("<Control-ButtonRelease-1>", self.on_gesture_end)

        # 手势状态
        self.gesture_active = False
        self.gesture_start_pos = None
        self.gesture_start_zoom = None

    def on_double_click(self, event):
        """双击事件 - 智能缩放"""
        if self.original_image is None:
            return

        # 如果当前是适应窗口大小，则切换到实际大小
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w <= 1 or canvas_h <= 1:
            return

        img_h, img_w = self.original_image.shape[:2]
        scale_w = (canvas_w - 20) / img_w
        scale_h = (canvas_h - 20) / img_h
        fit_scale = min(scale_w, scale_h)

        if abs(self.zoom_factor - fit_scale) < 0.1:
            # 当前是适应窗口，切换到实际大小
            self.actual_size()
        else:
            # 否则适应窗口
            self.fit_to_window()

    def on_right_click(self, event):
        """右键菜单"""
        if self.original_image is None:
            return

        # 创建右键菜单
        context_menu = tk.Menu(self.canvas, tearoff=0)

        context_menu.add_command(label="🔍 放大", command=self.zoom_in)
        context_menu.add_command(label="🔍 缩小", command=self.zoom_out)
        context_menu.add_separator()
        context_menu.add_command(label="📐 适应窗口", command=self.fit_to_window)
        context_menu.add_command(label="1:1 实际大小", command=self.actual_size)
        context_menu.add_separator()
        context_menu.add_command(label="🔄 重置视图", command=self.reset_view)
        context_menu.add_command(label="📍 居中显示", command=self.center_image)
        context_menu.add_separator()
        context_menu.add_command(label="ℹ️ 图像信息", command=self.show_image_info)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def on_middle_click(self, event):
        """中键点击 - 开始平移"""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.canvas.configure(cursor="fleur")

    def on_middle_drag(self, event):
        """中键拖拽 - 平移"""
        if hasattr(self, 'last_mouse_x'):
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y

            self.pan_x += dx
            self.pan_y += dy
            self.update_display()

            self.last_mouse_x = event.x
            self.last_mouse_y = event.y

    def on_middle_release(self, event):
        """中键释放"""
        self.canvas.configure(cursor="hand2")

    def on_gesture_start(self, event):
        """手势开始"""
        self.gesture_active = True
        self.gesture_start_pos = (event.x, event.y)
        self.gesture_start_zoom = self.zoom_factor

    def on_gesture_move(self, event):
        """手势移动 - 模拟缩放手势"""
        if not self.gesture_active or self.gesture_start_pos is None:
            return

        # 计算距离变化来模拟缩放手势
        start_x, start_y = self.gesture_start_pos
        current_distance = ((event.x - start_x) ** 2 + (event.y - start_y) ** 2) ** 0.5

        # 根据距离变化调整缩放
        if current_distance > 50:  # 向外手势 - 放大
            zoom_factor = self.gesture_start_zoom * (1 + current_distance / 500)
        elif current_distance < -50:  # 向内手势 - 缩小
            zoom_factor = self.gesture_start_zoom * (1 - abs(current_distance) / 500)
        else:
            zoom_factor = self.gesture_start_zoom

        self.set_zoom(zoom_factor)

    def on_gesture_end(self, event):
        """手势结束"""
        self.gesture_active = False
        self.gesture_start_pos = None
        self.gesture_start_zoom = None
    
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

            # 增强的滚动区域更新
            self.update_scroll_region()

            # 更新缩放显示
            self.zoom_var.set(f"{self.zoom_factor*100:.0f}%")

            # 更新按钮状态
            self.update_button_states()

            # 更新滚动条可见性
            self.update_scrollbar_visibility()

        except Exception as e:
            print(f"更新图像显示失败: {e}")

    def update_scroll_region(self):
        """更新滚动区域"""
        if self.original_image is None:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return

        h, w = self.original_image.shape[:2]
        display_w = int(w * self.zoom_factor)
        display_h = int(h * self.zoom_factor)

        # 设置滚动区域为图像的实际大小
        self.canvas.configure(scrollregion=(0, 0, display_w, display_h))

    def update_scrollbar_visibility(self):
        """更新滚动条可见性"""
        if self.original_image is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        h, w = self.original_image.shape[:2]
        display_w = int(w * self.zoom_factor)
        display_h = int(h * self.zoom_factor)

        # 根据内容大小决定滚动条的显示状态
        # 这里我们保持滚动条始终可见，但可以根据需要调整
        pass
    
    def zoom_in(self):
        """放大"""
        new_zoom = min(self.zoom_factor * 1.2, self.max_zoom)
        if self.smooth_scroll_enabled:
            self.smooth_zoom_to(new_zoom)
        else:
            self.set_zoom(new_zoom)

    def zoom_out(self):
        """缩小"""
        new_zoom = max(self.zoom_factor / 1.2, self.min_zoom)
        if self.smooth_scroll_enabled:
            self.smooth_zoom_to(new_zoom)
        else:
            self.set_zoom(new_zoom)

    def set_zoom(self, zoom_factor: float):
        """设置缩放比例"""
        if self.original_image is None:
            return

        old_zoom = self.zoom_factor
        self.zoom_factor = max(self.min_zoom, min(zoom_factor, self.max_zoom))

        # 如果缩放发生了变化，更新显示
        if abs(old_zoom - self.zoom_factor) > 0.001:
            self.update_display()

            if self.on_zoom_change and callable(self.on_zoom_change):
                try:
                    self.on_zoom_change(self.zoom_factor)
                except Exception as e:
                    print(f"缩放回调函数错误: {e}")

    def smooth_zoom_to(self, target_zoom: float):
        """平滑缩放到目标比例"""
        if hasattr(self, 'zoom_animation_id') and self.zoom_animation_id:
            self.canvas.after_cancel(self.zoom_animation_id)

        self.zoom_start = self.zoom_factor
        self.zoom_target = max(self.min_zoom, min(target_zoom, self.max_zoom))
        self.zoom_steps = 0
        self.zoom_max_steps = 15

        self.animate_smooth_zoom()

    def animate_smooth_zoom(self):
        """执行平滑缩放动画"""
        if self.zoom_steps >= self.zoom_max_steps:
            self.set_zoom(self.zoom_target)
            return

        # 使用缓动函数计算当前缩放值
        progress = self.zoom_steps / self.zoom_max_steps
        # 使用ease-out缓动
        eased_progress = 1 - (1 - progress) ** 3

        current_zoom = self.zoom_start + (self.zoom_target - self.zoom_start) * eased_progress
        self.set_zoom(current_zoom)

        self.zoom_steps += 1
        self.zoom_animation_id = self.canvas.after(30, self.animate_smooth_zoom)

    def zoom_to_point(self, x: float, y: float, zoom_factor: float):
        """缩放到指定点"""
        if self.original_image is None:
            return

        # 计算缩放前的图像坐标
        old_img_x = (x - self.pan_x) / self.zoom_factor
        old_img_y = (y - self.pan_y) / self.zoom_factor

        # 设置新的缩放比例
        self.set_zoom(zoom_factor)

        # 计算新的平移位置，使指定点保持在相同位置
        new_pan_x = x - old_img_x * self.zoom_factor
        new_pan_y = y - old_img_y * self.zoom_factor

        self.pan_x = new_pan_x
        self.pan_y = new_pan_y

        self.update_display()

    def zoom_to_selection(self, x1: float, y1: float, x2: float, y2: float):
        """缩放到选定区域"""
        if self.original_image is None:
            return

        # 计算选择区域的中心和大小
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width == 0 or height == 0:
            return

        # 计算适合的缩放比例
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        scale_x = (canvas_w - 40) / width
        scale_y = (canvas_h - 40) / height
        target_zoom = min(scale_x, scale_y)

        # 缩放到选定区域
        self.zoom_to_point(center_x, center_y, target_zoom)
    
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
        """增强的鼠标滚轮事件 - 支持缩放和滚动"""
        if self.original_image is None:
            return

        # 检查是否按住Ctrl键进行缩放
        if event.state & 0x4:  # Ctrl键被按下
            # 获取滚轮方向进行缩放
            if event.delta > 0 or event.num == 4:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # 普通滚动 - 垂直滚动
            self.scroll_vertical(event)

    def on_horizontal_scroll(self, event):
        """水平滚动事件"""
        if self.original_image is None:
            return
        self.scroll_horizontal(event)

    def scroll_vertical(self, event):
        """增强的垂直滚动"""
        if self.smooth_scroll_enabled:
            self.smooth_scroll_vertical(event)
        else:
            scroll_amount = int(self.scroll_sensitivity * 3)
            if event.delta > 0 or event.num == 4:
                self.canvas.yview_scroll(-scroll_amount, "units")
            else:
                self.canvas.yview_scroll(scroll_amount, "units")

    def scroll_horizontal(self, event):
        """增强的水平滚动"""
        if self.smooth_scroll_enabled:
            self.smooth_scroll_horizontal(event)
        else:
            scroll_amount = int(self.scroll_sensitivity * 3)
            if event.delta > 0 or event.num == 4:
                self.canvas.xview_scroll(-scroll_amount, "units")
            else:
                self.canvas.xview_scroll(scroll_amount, "units")

    def smooth_scroll_vertical(self, event):
        """平滑垂直滚动"""
        direction = -1 if (event.delta > 0 or event.num == 4) else 1
        self.start_smooth_scroll('vertical', direction)

    def smooth_scroll_horizontal(self, event):
        """平滑水平滚动"""
        direction = -1 if (event.delta > 0 or event.num == 4) else 1
        self.start_smooth_scroll('horizontal', direction)

    def start_smooth_scroll(self, orientation, direction):
        """开始平滑滚动动画"""
        if hasattr(self, 'scroll_animation_id') and self.scroll_animation_id:
            self.canvas.after_cancel(self.scroll_animation_id)

        self.scroll_steps = 0
        self.scroll_max_steps = 10
        self.scroll_orientation = orientation
        self.scroll_direction = direction
        self.scroll_amount = self.scroll_sensitivity * 2

        self.animate_smooth_scroll()

    def animate_smooth_scroll(self):
        """执行平滑滚动动画"""
        if self.scroll_steps >= self.scroll_max_steps:
            return

        # 计算当前步骤的滚动量（渐减效果）
        progress = self.scroll_steps / self.scroll_max_steps
        current_amount = self.scroll_amount * (1 - progress) * self.scroll_direction

        if self.scroll_orientation == 'vertical':
            self.canvas.yview_scroll(int(current_amount), "units")
        else:
            self.canvas.xview_scroll(int(current_amount), "units")

        self.scroll_steps += 1
        self.scroll_animation_id = self.canvas.after(20, self.animate_smooth_scroll)

    def on_arrow_key(self, event):
        """方向键滚动"""
        scroll_amount = 10  # 像素

        if event.keysym == "Up":
            self.canvas.yview_scroll(-scroll_amount, "units")
        elif event.keysym == "Down":
            self.canvas.yview_scroll(scroll_amount, "units")
        elif event.keysym == "Left":
            self.canvas.xview_scroll(-scroll_amount, "units")
        elif event.keysym == "Right":
            self.canvas.xview_scroll(scroll_amount, "units")

    def on_page_key(self, event):
        """Page Up/Down 键滚动"""
        if event.keysym == "Prior":  # Page Up
            self.canvas.yview_scroll(-1, "pages")
        elif event.keysym == "Next":  # Page Down
            self.canvas.yview_scroll(1, "pages")

    def on_home_end_key(self, event):
        """Home/End 键滚动"""
        if event.keysym == "Home":
            self.canvas.yview_moveto(0)  # 滚动到顶部
        elif event.keysym == "End":
            self.canvas.yview_moveto(1)  # 滚动到底部

    def on_scrollbar_click(self, event):
        """滚动条点击事件"""
        # 可以在这里添加滚动条点击的特殊处理
        pass
    
    def on_key_press(self, event):
        """增强的键盘按键事件"""
        # 缩放控制
        if event.keysym == "plus" or event.keysym == "equal":
            self.zoom_in()
        elif event.keysym == "minus":
            self.zoom_out()
        elif event.keysym == "0":
            self.actual_size()
        elif event.keysym == "f" or event.keysym == "F":
            self.fit_to_window()
        elif event.keysym == "r" or event.keysym == "R":
            self.reset_view()

        # 快速缩放
        elif event.keysym == "1":
            self.set_zoom(0.25)  # 25%
        elif event.keysym == "2":
            self.set_zoom(0.5)   # 50%
        elif event.keysym == "3":
            self.set_zoom(0.75)  # 75%
        elif event.keysym == "4":
            self.set_zoom(1.0)   # 100%
        elif event.keysym == "5":
            self.set_zoom(1.5)   # 150%
        elif event.keysym == "6":
            self.set_zoom(2.0)   # 200%

        # 视图控制
        elif event.keysym == "c" or event.keysym == "C":
            self.center_image()
        elif event.keysym == "space":
            self.toggle_fullscreen()

        # 滚动敏感度调整
        elif event.keysym == "bracketleft":  # [
            self.set_scroll_sensitivity(self.scroll_sensitivity - 0.1)
        elif event.keysym == "bracketright":  # ]
            self.set_scroll_sensitivity(self.scroll_sensitivity + 0.1)

        # 平滑滚动切换
        elif event.keysym == "s" or event.keysym == "S":
            if event.state & 0x4:  # Ctrl+S
                return  # 让保存功能处理
            self.toggle_smooth_scroll()

        # 信息显示
        elif event.keysym == "i" or event.keysym == "I":
            self.show_image_info()

        # 帮助
        elif event.keysym == "h" or event.keysym == "H":
            self.show_keyboard_help()

    def show_image_info(self):
        """显示图像信息"""
        if self.original_image is None:
            return

        h, w = self.original_image.shape[:2]
        channels = self.original_image.shape[2] if len(self.original_image.shape) == 3 else 1

        info = f"""📊 图像信息:
尺寸: {w} × {h} 像素
通道数: {channels}
总像素: {w * h:,}
当前缩放: {self.zoom_factor*100:.1f}%
滚动敏感度: {self.scroll_sensitivity:.1f}
平滑滚动: {'开启' if self.smooth_scroll_enabled else '关闭'}"""

        # 这里可以显示在状态栏或弹窗中
        print(info)  # 临时输出到控制台

    def show_keyboard_help(self):
        """显示键盘快捷键帮助"""
        help_text = """🔧 键盘快捷键:

缩放控制:
  +/= : 放大
  - : 缩小
  0 : 实际大小 (100%)
  1-6 : 快速缩放 (25%, 50%, 75%, 100%, 150%, 200%)
  F : 适应窗口
  R : 重置视图
  C : 居中显示

滚动控制:
  方向键 : 精确滚动
  Page Up/Down : 页面滚动
  Home/End : 滚动到顶部/底部
  [ / ] : 调整滚动敏感度

其他功能:
  S : 切换平滑滚动
  I : 显示图像信息
  H : 显示此帮助
  Space : 全屏切换

鼠标操作:
  Ctrl+滚轮 : 缩放
  滚轮 : 垂直滚动
  Shift+滚轮 : 水平滚动
  拖拽 : 平移图像"""

        print(help_text)  # 临时输出到控制台
    
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
            "has_image": self.original_image is not None,
            "scroll_sensitivity": self.scroll_sensitivity,
            "smooth_scroll_enabled": self.smooth_scroll_enabled
        }

    def set_scroll_sensitivity(self, sensitivity: float):
        """设置滚动敏感度"""
        self.scroll_sensitivity = max(0.1, min(sensitivity, 3.0))

    def toggle_smooth_scroll(self):
        """切换平滑滚动"""
        self.smooth_scroll_enabled = not self.smooth_scroll_enabled

    def scroll_to_position(self, x_fraction: float, y_fraction: float):
        """滚动到指定位置 (0.0-1.0)"""
        self.canvas.xview_moveto(x_fraction)
        self.canvas.yview_moveto(y_fraction)

    def get_scroll_position(self) -> tuple:
        """获取当前滚动位置"""
        x_pos = self.canvas.canvasx(0) / max(1, self.canvas.winfo_width())
        y_pos = self.canvas.canvasy(0) / max(1, self.canvas.winfo_height())
        return (x_pos, y_pos)

    def enable_auto_scroll(self, enabled: bool = True):
        """启用/禁用自动滚动"""
        self.auto_scroll_enabled = enabled
