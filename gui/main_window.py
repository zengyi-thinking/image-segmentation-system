"""
主GUI窗口
图像分割系统的主界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import threading
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import MSTSegmentation, EdgeWeightCalculator
from utils.image_io import ImageLoader, ImageSaver
from utils.visualization import SegmentationVisualizer
from data_structures.segmentation_result import SegmentationResult


class MainWindow:
    """主窗口类"""

    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()

        # 数据存储
        self.current_image = None
        self.segmentation_result = None
        self.image_loader = ImageLoader()
        self.image_saver = ImageSaver()
        self.visualizer = SegmentationVisualizer()

        # 状态变量
        self.is_processing = False

        # 创建界面
        self.create_menu()
        self.create_widgets()

        # 设置窗口图标和最小尺寸
        self.root.minsize(1000, 700)

        # 居中显示窗口
        self.center_window()

    def setup_window(self):
        """设置窗口基本属性"""
        self.root.title("🖼️ 图像分割系统 - MST算法")
        self.root.geometry("1400x900")

        # 设置窗口背景色
        self.root.configure(bg='#f0f0f0')

    def setup_styles(self):
        """设置现代化样式"""
        style = ttk.Style()

        # 设置主题
        try:
            style.theme_use('clam')  # 使用现代主题
        except:
            pass

        # 自定义样式
        style.configure('Title.TLabel',
                       font=('Microsoft YaHei UI', 12, 'bold'),
                       foreground='#2c3e50')

        style.configure('Heading.TLabelFrame.Label',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       foreground='#34495e')

        style.configure('Modern.TButton',
                       font=('Microsoft YaHei UI', 9),
                       padding=(10, 5))

        style.configure('Primary.TButton',
                       font=('Microsoft YaHei UI', 10, 'bold'))

        style.configure('Info.TLabel',
                       font=('Microsoft YaHei UI', 9),
                       foreground='#7f8c8d')

        # 配置进度条样式
        style.configure('Modern.Horizontal.TProgressbar',
                       background='#3498db',
                       troughcolor='#ecf0f1',
                       borderwidth=0,
                       lightcolor='#3498db',
                       darkcolor='#3498db')

    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图像", command=self.load_image)
        file_menu.add_command(label="保存结果", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="性能分析", command=self.show_performance_analysis)
        tools_menu.add_command(label="算法对比", command=self.show_algorithm_comparison)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建标题栏
        self.create_title_bar()

        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # 左侧控制面板
        self.create_control_panel(main_frame)

        # 右侧图像显示区域
        self.create_image_display(main_frame)

        # 底部状态栏
        self.create_status_bar()

    def create_title_bar(self):
        """创建标题栏"""
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        # 主标题
        title_label = ttk.Label(title_frame,
                               text="🖼️ 图像分割系统",
                               style='Title.TLabel',
                               font=('Microsoft YaHei UI', 16, 'bold'))
        title_label.pack(side=tk.LEFT)

        # 副标题
        subtitle_label = ttk.Label(title_frame,
                                  text="基于最小生成树(MST)算法的智能图像分割",
                                  style='Info.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="🎛️ 控制面板",
                                      padding=15, style='Heading.TLabelFrame')
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        control_frame.configure(width=350)  # 固定宽度

        # 图像加载区域
        load_frame = ttk.LabelFrame(control_frame, text="📁 图像加载",
                                   padding=10, style='Heading.TLabelFrame')
        load_frame.pack(fill=tk.X, pady=(0, 15))

        # 美化的加载按钮
        load_button = ttk.Button(load_frame, text="📂 选择图像文件",
                                command=self.load_image, style='Modern.TButton')
        load_button.pack(fill=tk.X, pady=(0, 8))

        # 图像信息显示
        self.image_info_label = ttk.Label(load_frame, text="📋 未加载图像",
                                         style='Info.TLabel', wraplength=300)
        self.image_info_label.pack(fill=tk.X)
        
        # 参数设置区域
        param_frame = ttk.LabelFrame(control_frame, text="⚙️ 算法参数",
                                    padding=10, style='Heading.TLabelFrame')
        param_frame.pack(fill=tk.X, pady=(0, 15))

        # 颜色权重
        alpha_frame = ttk.Frame(param_frame)
        alpha_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(alpha_frame, text="🎨 颜色权重 (α):",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        self.alpha_var = tk.DoubleVar(value=1.0)
        alpha_scale = ttk.Scale(alpha_frame, from_=0.1, to=5.0,
                               variable=self.alpha_var, orient=tk.HORIZONTAL,
                               length=280)
        alpha_scale.pack(fill=tk.X, pady=(5, 0))

        self.alpha_label = ttk.Label(alpha_frame, text="1.00",
                                    style='Info.TLabel', font=('Consolas', 9))
        self.alpha_label.pack(anchor=tk.W)
        alpha_scale.configure(command=lambda v: self.alpha_label.configure(text=f"{float(v):.2f}"))

        # 空间权重
        beta_frame = ttk.Frame(param_frame)
        beta_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(beta_frame, text="📐 空间权重 (β):",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        self.beta_var = tk.DoubleVar(value=0.1)
        beta_scale = ttk.Scale(beta_frame, from_=0.01, to=1.0,
                              variable=self.beta_var, orient=tk.HORIZONTAL,
                              length=280)
        beta_scale.pack(fill=tk.X, pady=(5, 0))

        self.beta_label = ttk.Label(beta_frame, text="0.100",
                                   style='Info.TLabel', font=('Consolas', 9))
        self.beta_label.pack(anchor=tk.W)
        beta_scale.configure(command=lambda v: self.beta_label.configure(text=f"{float(v):.3f}"))
        
        # 连接性
        connectivity_frame = ttk.Frame(param_frame)
        connectivity_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(connectivity_frame, text="🔗 像素连接性:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        self.connectivity_var = tk.IntVar(value=4)
        radio_frame = ttk.Frame(connectivity_frame)
        radio_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Radiobutton(radio_frame, text="4-连通 (上下左右)",
                       variable=self.connectivity_var, value=4).pack(anchor=tk.W)
        ttk.Radiobutton(radio_frame, text="8-连通 (八个方向)",
                       variable=self.connectivity_var, value=8).pack(anchor=tk.W)

        # 分割阈值
        threshold_frame = ttk.Frame(param_frame)
        threshold_frame.pack(fill=tk.X)

        ttk.Label(threshold_frame, text="🎯 分割阈值:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        self.threshold_var = tk.DoubleVar(value=0.0)
        self.auto_threshold_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(threshold_frame, text="🤖 自动计算最优阈值",
                       variable=self.auto_threshold_var,
                       command=self.toggle_threshold_mode).pack(anchor=tk.W, pady=(5, 5))

        self.threshold_scale = ttk.Scale(threshold_frame, from_=0.0, to=100.0,
                                        variable=self.threshold_var, orient=tk.HORIZONTAL,
                                        state=tk.DISABLED, length=280)
        self.threshold_scale.pack(fill=tk.X)

        self.threshold_label = ttk.Label(threshold_frame, text="🤖 自动模式",
                                        style='Info.TLabel', font=('Consolas', 9))
        self.threshold_label.pack(anchor=tk.W)
        
        # 执行按钮
        execute_frame = ttk.LabelFrame(control_frame, text="🚀 执行分割",
                                      padding=10, style='Heading.TLabelFrame')
        execute_frame.pack(fill=tk.X, pady=(0, 15))

        self.segment_button = ttk.Button(execute_frame, text="🎯 开始图像分割",
                                        command=self.start_segmentation,
                                        state=tk.DISABLED,
                                        style='Primary.TButton')
        self.segment_button.pack(fill=tk.X, pady=(0, 10))

        # 进度显示
        progress_label = ttk.Label(execute_frame, text="处理进度:",
                                  font=('Microsoft YaHei UI', 9))
        progress_label.pack(anchor=tk.W)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(execute_frame, variable=self.progress_var,
                                           mode='indeterminate',
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X, pady=(5, 5))

        self.progress_text = ttk.Label(execute_frame, text="等待开始...",
                                      style='Info.TLabel', font=('Microsoft YaHei UI', 8))
        self.progress_text.pack(anchor=tk.W)
        
        # 结果信息
        result_frame = ttk.LabelFrame(control_frame, text="📊 分割结果",
                                     padding=10, style='Heading.TLabelFrame')
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 创建文本框和滚动条的容器
        text_container = ttk.Frame(result_frame)
        text_container.pack(fill=tk.BOTH, expand=True)

        self.result_text = tk.Text(text_container, height=10, width=35,
                                  font=('Consolas', 9),
                                  bg='#f8f9fa', fg='#2c3e50',
                                  relief=tk.FLAT, borderwidth=1,
                                  wrap=tk.WORD)

        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL,
                                 command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加默认提示文本
        self.result_text.insert(tk.END, "📋 分割结果将在这里显示\n\n")
        self.result_text.insert(tk.END, "💡 提示：\n")
        self.result_text.insert(tk.END, "• 选择图像文件\n")
        self.result_text.insert(tk.END, "• 调整算法参数\n")
        self.result_text.insert(tk.END, "• 点击开始分割\n")
        self.result_text.configure(state=tk.DISABLED)
    
    def create_image_display(self, parent):
        """创建图像显示区域"""
        display_frame = ttk.LabelFrame(parent, text="🖼️ 图像显示",
                                      padding=15, style='Heading.TLabelFrame')
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建标签页
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 原始图像标签页
        self.original_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.original_frame, text="📷 原始图像")

        self.original_canvas = tk.Canvas(self.original_frame, bg='#f8f9fa',
                                        relief=tk.FLAT, borderwidth=0,
                                        highlightthickness=1,
                                        highlightcolor='#bdc3c7')
        self.original_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 分割结果标签页
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="🎨 分割结果")

        self.result_canvas = tk.Canvas(self.result_frame, bg='#f8f9fa',
                                      relief=tk.FLAT, borderwidth=0,
                                      highlightthickness=1,
                                      highlightcolor='#bdc3c7')
        self.result_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 边界显示标签页
        self.boundary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.boundary_frame, text="🔍 边界显示")

        self.boundary_canvas = tk.Canvas(self.boundary_frame, bg='#f8f9fa',
                                        relief=tk.FLAT, borderwidth=0,
                                        highlightthickness=1,
                                        highlightcolor='#bdc3c7')
        self.boundary_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 添加空白提示
        self.add_canvas_placeholder(self.original_canvas, "📷 请选择图像文件")
        self.add_canvas_placeholder(self.result_canvas, "🎨 分割结果将在这里显示")
        self.add_canvas_placeholder(self.boundary_canvas, "🔍 边界检测结果将在这里显示")

    def add_canvas_placeholder(self, canvas, text):
        """为画布添加占位符文本"""
        def draw_placeholder():
            canvas.delete("placeholder")
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width > 1 and height > 1:
                canvas.create_text(width//2, height//2,
                                  text=text,
                                  font=('Microsoft YaHei UI', 12),
                                  fill='#95a5a6',
                                  tags="placeholder")

        canvas.bind('<Configure>', lambda e: draw_placeholder())
        canvas.after(100, draw_placeholder)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(5, 15))

        # 状态栏背景
        status_bg = ttk.Frame(status_frame, relief=tk.SUNKEN, borderwidth=1)
        status_bg.pack(fill=tk.X)

        # 状态文本
        self.status_var = tk.StringVar(value="✅ 系统就绪 - 请选择图像文件开始分割")
        status_label = ttk.Label(status_bg, textvariable=self.status_var,
                                font=('Microsoft YaHei UI', 9),
                                foreground='#27ae60')
        status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 版本信息
        version_label = ttk.Label(status_bg, text="v1.0",
                                 font=('Microsoft YaHei UI', 8),
                                 foreground='#95a5a6')
        version_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def toggle_threshold_mode(self):
        """切换阈值模式"""
        if self.auto_threshold_var.get():
            self.threshold_scale.configure(state=tk.DISABLED)
            self.threshold_label.configure(text="🤖 自动模式")
        else:
            self.threshold_scale.configure(state=tk.NORMAL)
            self.threshold_label.configure(text=f"📊 {self.threshold_var.get():.2f}")
            self.threshold_scale.configure(
                command=lambda v: self.threshold_label.configure(text=f"📊 {float(v):.2f}")
            )
    
    def load_image(self):
        """加载图像"""
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=[
                ("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("PNG文件", "*.png"),
                ("BMP文件", "*.bmp"),
                ("TIFF文件", "*.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.status_var.set("📂 正在加载图像...")
            self.root.update()

            try:
                # 加载图像
                image = self.image_loader.load_image(file_path)

                if image is not None:
                    self.current_image = image

                    # 更新图像信息
                    height, width = image.shape[:2]
                    channels = image.shape[2] if len(image.shape) == 3 else 1
                    file_size = os.path.getsize(file_path) / 1024  # KB

                    info_text = f"📋 图像信息:\n"
                    info_text += f"📐 尺寸: {width} × {height}\n"
                    info_text += f"🎨 通道: {channels}\n"
                    info_text += f"📁 文件: {os.path.basename(file_path)}\n"
                    info_text += f"💾 大小: {file_size:.1f} KB"

                    self.image_info_label.configure(text=info_text)

                    # 显示图像
                    self.display_image(self.original_canvas, image)

                    # 清除其他画布的占位符
                    self.result_canvas.delete("placeholder")
                    self.boundary_canvas.delete("placeholder")

                    # 启用分割按钮
                    self.segment_button.configure(state=tk.NORMAL)

                    self.status_var.set(f"✅ 图像加载完成 - {width}×{height} 像素")
                else:
                    messagebox.showerror("错误", "无法加载图像文件\n请检查文件格式是否支持")
                    self.status_var.set("❌ 图像加载失败")

            except Exception as e:
                messagebox.showerror("错误", f"加载图像时发生错误:\n{str(e)}")
                self.status_var.set("❌ 图像加载失败")
    
    def display_image(self, canvas, image):
        """在画布上显示图像"""
        try:
            # 获取画布尺寸
            canvas.update()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # 画布还没有正确初始化，延迟显示
                self.root.after(100, lambda: self.display_image(canvas, image))
                return

            # 调整图像大小以适应画布（留出边距）
            display_width = canvas_width - 20
            display_height = canvas_height - 20

            image_resized = self.image_loader.resize_image(
                image, (display_width, display_height), keep_aspect_ratio=True
            )

            # 转换为PIL图像并显示
            pil_image = Image.fromarray(image_resized)
            photo = ImageTk.PhotoImage(pil_image)

            # 清除画布并显示新图像
            canvas.delete("all")

            # 添加阴影效果
            shadow_offset = 3
            canvas.create_rectangle(
                canvas_width//2 - image_resized.shape[1]//2 + shadow_offset,
                canvas_height//2 - image_resized.shape[0]//2 + shadow_offset,
                canvas_width//2 + image_resized.shape[1]//2 + shadow_offset,
                canvas_height//2 + image_resized.shape[0]//2 + shadow_offset,
                fill='#bdc3c7', outline='', tags="shadow"
            )

            # 显示图像
            canvas.create_image(canvas_width//2, canvas_height//2,
                               image=photo, anchor=tk.CENTER, tags="image")

            # 保存引用以防止垃圾回收
            canvas.image = photo

        except Exception as e:
            print(f"显示图像时发生错误: {e}")
            # 显示错误信息
            canvas.delete("all")
            canvas.create_text(canvas_width//2, canvas_height//2,
                              text=f"❌ 显示错误\n{str(e)}",
                              font=('Microsoft YaHei UI', 10),
                              fill='#e74c3c')
    
    def start_segmentation(self):
        """开始分割处理"""
        if self.current_image is None:
            messagebox.showwarning("⚠️ 警告", "请先加载图像文件")
            return

        if self.is_processing:
            return

        # 验证参数
        alpha = self.alpha_var.get()
        beta = self.beta_var.get()

        if alpha <= 0 or beta <= 0:
            messagebox.showerror("❌ 参数错误", "颜色权重和空间权重必须大于0")
            return

        # 在后台线程中执行分割
        self.is_processing = True
        self.segment_button.configure(state=tk.DISABLED, text="🔄 正在处理...")
        self.progress_bar.start()
        self.progress_text.configure(text="初始化...")
        self.status_var.set("🔄 正在执行图像分割...")

        # 清空结果显示
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "🔄 正在处理，请稍候...\n")
        self.result_text.configure(state=tk.DISABLED)

        # 创建后台线程
        thread = threading.Thread(target=self.perform_segmentation)
        thread.daemon = True
        thread.start()

    def update_progress(self, message, progress):
        """更新进度显示"""
        def update():
            self.progress_text.configure(text=message)
            if progress >= 0:
                self.status_var.set(f"🔄 {message}")
            else:
                self.status_var.set(f"❌ {message}")

        self.root.after(0, update)
    
    def perform_segmentation(self):
        """执行分割算法"""
        try:
            # 获取参数
            alpha = self.alpha_var.get()
            beta = self.beta_var.get()
            connectivity = self.connectivity_var.get()

            threshold = None if self.auto_threshold_var.get() else self.threshold_var.get()

            # 创建分割器
            self.update_progress("创建分割器...", 0.1)
            weight_calculator = EdgeWeightCalculator(alpha=alpha, beta=beta)
            segmenter = MSTSegmentation(
                connectivity=connectivity,
                weight_calculator=weight_calculator,
                min_segment_size=max(10, self.current_image.size // 10000)  # 自适应最小区域大小
            )

            # 执行分割（带进度回调）
            self.update_progress("开始图像分割...", 0.2)
            result = segmenter.segment(
                self.current_image,
                threshold=threshold,
                progress_callback=self.update_progress
            )

            # 验证结果
            if result is None or 'label_map' not in result:
                raise RuntimeError("分割算法返回无效结果")

            # 创建分割结果对象
            self.update_progress("生成分割结果...", 0.9)
            self.segmentation_result = SegmentationResult(
                result['label_map'],
                self.current_image,
                "MST分割",
                {
                    'alpha': alpha,
                    'beta': beta,
                    'connectivity': connectivity,
                    'threshold': result['threshold'],
                    'num_segments': result['statistics']['num_segments']
                }
            )

            # 在主线程中更新界面
            self.root.after(0, self.update_results)

        except Exception as e:
            import traceback
            error_msg = f"分割过程中发生错误:\n{str(e)}"
            print(f"分割错误详情: {traceback.format_exc()}")
            self.root.after(0, lambda: self.show_error(error_msg))
    
    def update_results(self):
        """更新分割结果显示"""
        try:
            self.update_progress("生成可视化图像...", 0.95)

            # 生成可视化图像
            segmented_image = self.visualizer.visualize_segments(
                self.current_image, self.segmentation_result.label_map
            )

            boundary_image = self.visualizer.visualize_boundaries(
                self.current_image, self.segmentation_result.label_map
            )

            # 显示结果
            self.display_image(self.result_canvas, segmented_image)
            self.display_image(self.boundary_canvas, boundary_image)

            # 更新结果信息
            self.update_result_info()

            # 切换到结果标签页
            self.notebook.select(1)

            # 显示完成消息
            stats = self.segmentation_result.statistics
            completion_msg = f"✅ 分割完成 - 生成 {stats['num_segments']} 个区域"
            self.status_var.set(completion_msg)

        except Exception as e:
            import traceback
            print(f"更新结果错误详情: {traceback.format_exc()}")
            self.show_error(f"显示结果时发生错误:\n{str(e)}")
        finally:
            # 恢复界面状态
            self.is_processing = False
            self.segment_button.configure(state=tk.NORMAL, text="🎯 开始图像分割")
            self.progress_bar.stop()
            self.progress_text.configure(text="处理完成")
    
    def update_result_info(self):
        """更新结果信息显示"""
        if self.segmentation_result is None:
            return

        stats = self.segmentation_result.statistics
        params = self.segmentation_result.parameters

        # 计算一些额外的统计信息
        total_pixels = stats['total_pixels']
        coverage = (stats['num_segments'] * stats['avg_segment_size']) / total_pixels * 100

        info_text = f"""🎯 分割参数:
🎨 颜色权重 (α): {params.get('alpha', 'N/A'):.2f}
📐 空间权重 (β): {params.get('beta', 'N/A'):.3f}
🔗 连接性: {params.get('connectivity', 'N/A')}-连通
🎯 分割阈值: {params.get('threshold', 'N/A'):.2f}

📊 分割结果:
🔢 区域数量: {stats['num_segments']:,}
📏 平均区域大小: {stats['avg_segment_size']:.1f} 像素
📈 最大区域大小: {stats['max_segment_size']:,} 像素
📉 最小区域大小: {stats['min_segment_size']:,} 像素
📊 大小标准差: {stats['std_segment_size']:.1f}
📋 总像素数: {total_pixels:,}
✅ 覆盖率: {coverage:.1f}%

💡 质量评估:
"""

        # 添加质量评估
        if stats['num_segments'] < 10:
            info_text += "🔴 分割过粗 - 建议降低阈值\n"
        elif stats['num_segments'] > 1000:
            info_text += "🟡 分割过细 - 建议提高阈值\n"
        else:
            info_text += "🟢 分割质量良好\n"

        if stats['avg_segment_size'] < 50:
            info_text += "⚠️ 平均区域较小\n"

        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, info_text)
        self.result_text.configure(state=tk.DISABLED)
    
    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("❌ 错误", message)
        self.is_processing = False
        self.segment_button.configure(state=tk.NORMAL, text="🎯 开始图像分割")
        self.progress_bar.stop()
        self.progress_text.configure(text="发生错误")
        self.status_var.set("❌ 处理失败")

        # 更新结果文本显示错误信息
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"❌ 处理失败\n\n错误信息:\n{message}")
        self.result_text.configure(state=tk.DISABLED)
    
    def save_result(self):
        """保存分割结果"""
        if self.segmentation_result is None:
            messagebox.showwarning("⚠️ 警告", "没有可保存的分割结果\n请先执行图像分割")
            return

        # 让用户选择保存类型
        save_options = messagebox.askyesnocancel(
            "💾 保存选项",
            "选择保存内容:\n\n是(Yes) - 保存分割结果图像\n否(No) - 保存边界检测图像\n取消 - 不保存"
        )

        if save_options is None:  # 用户取消
            return

        file_path = filedialog.asksaveasfilename(
            title="保存分割结果",
            defaultextension=".png",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("BMP文件", "*.bmp"),
                ("TIFF文件", "*.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            try:
                self.status_var.set("💾 正在保存...")

                if save_options:  # 保存分割结果
                    image_to_save = self.visualizer.visualize_segments(
                        self.current_image, self.segmentation_result.label_map
                    )
                    save_type = "分割结果"
                else:  # 保存边界图像
                    image_to_save = self.visualizer.visualize_boundaries(
                        self.current_image, self.segmentation_result.label_map
                    )
                    save_type = "边界检测结果"

                # 保存图像
                success = self.image_saver.save_image(image_to_save, file_path)

                if success:
                    messagebox.showinfo("✅ 保存成功",
                                      f"{save_type}已保存到:\n{file_path}")
                    self.status_var.set(f"✅ {save_type}保存成功")
                else:
                    messagebox.showerror("❌ 保存失败", "无法保存文件，请检查路径和权限")
                    self.status_var.set("❌ 保存失败")

            except Exception as e:
                error_msg = f"保存过程中发生错误:\n{str(e)}"
                messagebox.showerror("❌ 保存错误", error_msg)
                self.status_var.set("❌ 保存失败")
    
    def show_performance_analysis(self):
        """显示性能分析"""
        messagebox.showinfo("性能分析", "性能分析功能正在开发中...")
    
    def show_algorithm_comparison(self):
        """显示算法对比"""
        messagebox.showinfo("算法对比", "算法对比功能正在开发中...")
    
    def show_about(self):
        """显示关于信息"""
        about_text = """🖼️ 图像分割系统 v1.0

🔬 基于图论的智能图像分割系统
🌟 使用最小生成树(MST)算法

✨ 主要特性:
• 高质量图像分割
• 实时参数调整
• 多种可视化模式
• 现代化用户界面

🛠️ 技术栈:
• Python 3.8+
• OpenCV 图像处理
• NumPy 数值计算
• Tkinter GUI框架
• Matplotlib 可视化

👥 开发团队: 图像处理研究组
📅 版本日期: 2025年6月
🏷️ 许可证: MIT License
"""
        messagebox.showinfo("ℹ️ 关于系统", about_text)
