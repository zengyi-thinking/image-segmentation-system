"""
控制面板组件
包含图像加载、参数设置、执行控制和结果显示
"""

import tkinter as tk
from tkinter import ttk
from .style_manager import get_style_manager
from .theme_manager import get_theme_manager


class ControlPanel:
    """控制面板组件"""
    
    def __init__(self, parent, callbacks=None):
        """
        初始化控制面板

        Args:
            parent: 父容器
            callbacks: 回调函数字典
        """
        self.parent = parent
        self.callbacks = callbacks or {}
        self.style_manager = get_style_manager()
        self.theme_manager = get_theme_manager()

        # 创建主框架 - 带滚动功能
        self.create_scrollable_frame(parent)

        # 初始化变量
        self.init_variables()

        # 创建子组件
        self.create_image_loader()
        self.create_algorithm_selection()
        self.create_parameter_panel()
        self.create_execution_panel()
        self.create_result_panel()

    def create_scrollable_frame(self, parent):
        """创建可滚动的控制面板框架"""
        # 外层容器
        self.outer_frame = ttk.Frame(parent)
        self.outer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.outer_frame.configure(width=350)

        # 创建画布和滚动条
        self.canvas = tk.Canvas(self.outer_frame, highlightthickness=0, width=350)
        self.scrollbar = ttk.Scrollbar(self.outer_frame, orient="vertical", command=self.canvas.yview)

        # 可滚动的内容框架
        self.scrollable_frame = ttk.Frame(self.canvas)

        # 配置滚动
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 创建窗口
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # 配置画布滚动
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 布局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.bind_mousewheel()

        # 创建主标题框架
        self.main_frame = self.style_manager.create_labelframe(
            self.scrollable_frame,
            text="🎛️ 控制面板",
            padding=15,
            style_name='Heading.TLabelFrame'
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def bind_mousewheel(self):
        """绑定鼠标滚轮事件到控制面板"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        # 绑定进入和离开事件
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

        # 支持键盘滚动
        self.canvas.bind('<Up>', lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind('<Down>', lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind('<Prior>', lambda e: self.canvas.yview_scroll(-1, "pages"))  # Page Up
        self.canvas.bind('<Next>', lambda e: self.canvas.yview_scroll(1, "pages"))   # Page Down

        self.canvas.focus_set()
    
    def init_variables(self):
        """初始化控制变量"""
        # 算法选择
        self.algorithm_var = tk.StringVar(value="MST")

        # MST算法参数
        self.alpha_var = tk.DoubleVar(value=1.0)
        self.beta_var = tk.DoubleVar(value=0.1)
        self.connectivity_var = tk.IntVar(value=4)
        self.threshold_var = tk.DoubleVar(value=0.0)
        self.auto_threshold_var = tk.BooleanVar(value=True)

        # Watershed算法参数
        self.min_distance_var = tk.IntVar(value=20)
        self.compactness_var = tk.DoubleVar(value=0.001)
        self.watershed_line_var = tk.BooleanVar(value=True)

        # 通用变量
        self.progress_var = tk.DoubleVar()
    
    def create_image_loader(self):
        """创建图像加载区域"""
        load_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="📁 图像加载",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
        load_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 加载按钮
        self.load_button = self.style_manager.create_button(
            load_frame,
            text="📂 选择图像文件",
            command=self.callbacks.get('load_image'),
            style_name='Modern.TButton'
        )
        self.load_button.pack(fill=tk.X, pady=(0, 8))
        
        # 图像信息显示
        self.image_info_label = self.style_manager.create_label(
            load_frame,
            text="📋 未加载图像",
            style_name='Info.TLabel',
            wraplength=300
        )
        self.image_info_label.pack(fill=tk.X)

    def create_algorithm_selection(self):
        """创建算法选择区域"""
        algo_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="🧠 算法选择",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
        algo_frame.pack(fill=tk.X, pady=(0, 15))

        # 算法选择
        ttk.Label(algo_frame, text="选择分割算法:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        algo_radio_frame = ttk.Frame(algo_frame)
        algo_radio_frame.pack(fill=tk.X, pady=(5, 0))

        # MST算法选项
        mst_radio = ttk.Radiobutton(
            algo_radio_frame,
            text="🌳 MST (最小生成树) - 基于图论的分割",
            variable=self.algorithm_var,
            value="MST",
            command=self.on_algorithm_changed
        )
        mst_radio.pack(anchor=tk.W, pady=(0, 5))

        # Watershed算法选项
        watershed_radio = ttk.Radiobutton(
            algo_radio_frame,
            text="🌊 Watershed (分水岭) - 基于形态学的分割",
            variable=self.algorithm_var,
            value="Watershed",
            command=self.on_algorithm_changed
        )
        watershed_radio.pack(anchor=tk.W)

        # 算法描述
        self.algo_description = self.style_manager.create_label(
            algo_frame,
            text="MST算法通过构建最小生成树来分割图像，适合处理复杂纹理和边界。",
            style_name='Info.TLabel',
            wraplength=300
        )
        self.algo_description.pack(fill=tk.X, pady=(10, 0))

    def on_algorithm_changed(self):
        """算法选择改变时的回调"""
        selected_algo = self.algorithm_var.get()

        if selected_algo == "MST":
            description = "MST算法通过构建最小生成树来分割图像，适合处理复杂纹理和边界。"
        elif selected_algo == "Watershed":
            description = "Watershed算法模拟水流填充过程，适合分割具有明显边界的对象。"
        else:
            description = "请选择一个分割算法。"

        self.algo_description.configure(text=description)

        # 更新参数面板
        self.update_parameter_panel()

        # 通知主窗口算法已改变
        if 'algorithm_changed' in self.callbacks:
            self.callbacks['algorithm_changed'](selected_algo)

    def create_parameter_panel(self):
        """创建参数设置区域"""
        self.param_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="⚙️ 算法参数",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
        self.param_frame.pack(fill=tk.X, pady=(0, 15))

        # 创建参数容器
        self.param_container = ttk.Frame(self.param_frame)
        self.param_container.pack(fill=tk.X)

        # 初始显示MST参数
        self.create_mst_parameters()
        self.create_watershed_parameters()

        # 初始只显示MST参数
        self.update_parameter_panel()

    def create_mst_parameters(self):
        """创建MST算法参数"""
        self.mst_frame = ttk.Frame(self.param_container)

        # 颜色权重
        self.create_alpha_control(self.mst_frame)

        # 空间权重
        self.create_beta_control(self.mst_frame)

        # 连接性
        self.create_connectivity_control(self.mst_frame)

        # 分割阈值
        self.create_threshold_control(self.mst_frame)

    def create_watershed_parameters(self):
        """创建Watershed算法参数"""
        self.watershed_frame = ttk.Frame(self.param_container)

        # 最小距离参数
        self.create_min_distance_control(self.watershed_frame)

        # 紧凑性参数
        self.create_compactness_control(self.watershed_frame)

        # 分水岭线参数
        self.create_watershed_line_control(self.watershed_frame)

    def update_parameter_panel(self):
        """根据选择的算法更新参数面板"""
        # 隐藏所有参数框架
        self.mst_frame.pack_forget()
        self.watershed_frame.pack_forget()

        # 显示对应的参数框架
        if self.algorithm_var.get() == "MST":
            self.mst_frame.pack(fill=tk.X)
        elif self.algorithm_var.get() == "Watershed":
            self.watershed_frame.pack(fill=tk.X)
    
    def create_alpha_control(self, parent):
        """创建颜色权重控制"""
        alpha_frame = ttk.Frame(parent)
        alpha_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(alpha_frame, text="🎨 颜色权重 (α):",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)
        
        alpha_scale = ttk.Scale(alpha_frame, from_=0.1, to=5.0,
                               variable=self.alpha_var, orient=tk.HORIZONTAL,
                               length=280)
        alpha_scale.pack(fill=tk.X, pady=(5, 0))
        
        self.alpha_label = self.style_manager.create_label(
            alpha_frame,
            text="1.00",
            style_name='Info.TLabel'
        )
        self.alpha_label.configure(font=('Consolas', 9))
        self.alpha_label.pack(anchor=tk.W)
        
        alpha_scale.configure(
            command=lambda v: self.alpha_label.configure(text=f"{float(v):.2f}")
        )
    
    def create_beta_control(self, parent):
        """创建空间权重控制"""
        beta_frame = ttk.Frame(parent)
        beta_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(beta_frame, text="📐 空间权重 (β):",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)
        
        beta_scale = ttk.Scale(beta_frame, from_=0.01, to=1.0,
                              variable=self.beta_var, orient=tk.HORIZONTAL,
                              length=280)
        beta_scale.pack(fill=tk.X, pady=(5, 0))
        
        self.beta_label = self.style_manager.create_label(
            beta_frame,
            text="0.100",
            style_name='Info.TLabel'
        )
        self.beta_label.configure(font=('Consolas', 9))
        self.beta_label.pack(anchor=tk.W)
        
        beta_scale.configure(
            command=lambda v: self.beta_label.configure(text=f"{float(v):.3f}")
        )
    
    def create_connectivity_control(self, parent):
        """创建连接性控制"""
        connectivity_frame = ttk.Frame(parent)
        connectivity_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(connectivity_frame, text="🔗 像素连接性:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)
        
        radio_frame = ttk.Frame(connectivity_frame)
        radio_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Radiobutton(radio_frame, text="4-连通 (上下左右)",
                       variable=self.connectivity_var, value=4).pack(anchor=tk.W)
        ttk.Radiobutton(radio_frame, text="8-连通 (八个方向)",
                       variable=self.connectivity_var, value=8).pack(anchor=tk.W)
    
    def create_threshold_control(self, parent):
        """创建阈值控制"""
        threshold_frame = ttk.Frame(parent)
        threshold_frame.pack(fill=tk.X)
        
        ttk.Label(threshold_frame, text="🎯 分割阈值:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)
        
        ttk.Checkbutton(threshold_frame, text="🤖 自动计算最优阈值",
                       variable=self.auto_threshold_var,
                       command=self.toggle_threshold_mode).pack(anchor=tk.W, pady=(5, 5))
        
        self.threshold_scale = ttk.Scale(threshold_frame, from_=0.0, to=100.0,
                                        variable=self.threshold_var, orient=tk.HORIZONTAL,
                                        state=tk.DISABLED, length=280)
        self.threshold_scale.pack(fill=tk.X)
        
        self.threshold_label = self.style_manager.create_label(
            threshold_frame,
            text="🤖 自动模式",
            style_name='Info.TLabel'
        )
        self.threshold_label.configure(font=('Consolas', 9))
        self.threshold_label.pack(anchor=tk.W)

    def create_min_distance_control(self, parent):
        """创建最小距离控制"""
        min_dist_frame = ttk.Frame(parent)
        min_dist_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(min_dist_frame, text="📏 最小距离:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        min_dist_scale = ttk.Scale(min_dist_frame, from_=5, to=50,
                                  variable=self.min_distance_var, orient=tk.HORIZONTAL,
                                  length=280)
        min_dist_scale.pack(fill=tk.X, pady=(5, 0))

        self.min_dist_label = self.style_manager.create_label(
            min_dist_frame,
            text="20",
            style_name='Info.TLabel'
        )
        self.min_dist_label.configure(font=('Consolas', 9))
        self.min_dist_label.pack(anchor=tk.W)

        min_dist_scale.configure(
            command=lambda v: self.min_dist_label.configure(text=f"{int(float(v))}")
        )

    def create_compactness_control(self, parent):
        """创建紧凑性控制"""
        compact_frame = ttk.Frame(parent)
        compact_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(compact_frame, text="🎯 紧凑性:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        compact_scale = ttk.Scale(compact_frame, from_=0.0001, to=0.01,
                                 variable=self.compactness_var, orient=tk.HORIZONTAL,
                                 length=280)
        compact_scale.pack(fill=tk.X, pady=(5, 0))

        self.compact_label = self.style_manager.create_label(
            compact_frame,
            text="0.0010",
            style_name='Info.TLabel'
        )
        self.compact_label.configure(font=('Consolas', 9))
        self.compact_label.pack(anchor=tk.W)

        compact_scale.configure(
            command=lambda v: self.compact_label.configure(text=f"{float(v):.4f}")
        )

    def create_watershed_line_control(self, parent):
        """创建分水岭线控制"""
        line_frame = ttk.Frame(parent)
        line_frame.pack(fill=tk.X)

        ttk.Label(line_frame, text="🌊 分水岭线:",
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W)

        ttk.Checkbutton(line_frame, text="在分割边界添加分水岭线",
                       variable=self.watershed_line_var).pack(anchor=tk.W, pady=(5, 0))

    def create_execution_panel(self):
        """创建执行控制区域"""
        execute_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="🚀 执行分割",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
        execute_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 执行按钮
        self.segment_button = self.style_manager.create_button(
            execute_frame,
            text="🎯 开始图像分割",
            command=self.callbacks.get('start_segmentation'),
            style_name='Primary.TButton',
            state=tk.DISABLED
        )
        self.segment_button.pack(fill=tk.X, pady=(0, 10))
        
        # 进度显示
        progress_label = ttk.Label(execute_frame, text="处理进度:",
                                  font=('Microsoft YaHei UI', 9))
        progress_label.pack(anchor=tk.W)
        
        self.progress_bar = self.style_manager.create_progressbar(
            execute_frame,
            variable=self.progress_var,
            mode='indeterminate',
            style_name='Modern.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 5))
        
        self.progress_text = self.style_manager.create_label(
            execute_frame,
            text="等待开始...",
            style_name='Info.TLabel'
        )
        self.progress_text.configure(font=('Microsoft YaHei UI', 8))
        self.progress_text.pack(anchor=tk.W)
    
    def create_result_panel(self):
        """创建结果显示区域"""
        result_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="📊 分割结果",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
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
    
    def update_image_info(self, info_text):
        """更新图像信息显示"""
        self.image_info_label.configure(text=info_text)
    
    def update_progress(self, text, progress=None):
        """更新进度显示"""
        try:
            if hasattr(self, 'progress_text') and self.progress_text:
                self.progress_text.configure(text=text)

            if progress is not None and hasattr(self, 'progress_var') and self.progress_var:
                # 确保progress是有效的数值
                if isinstance(progress, (int, float)) and -1 <= progress <= 1:
                    self.progress_var.set(progress)
        except Exception as e:
            print(f"更新进度时发生错误: {e}")
    
    def update_result_text(self, text):
        """更新结果文本"""
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, text)
        self.result_text.configure(state=tk.DISABLED)
    
    def enable_segment_button(self, enabled=True):
        """启用/禁用分割按钮"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.segment_button.configure(state=state)
        
        if enabled:
            self.segment_button.configure(text="🎯 开始图像分割")
        else:
            self.segment_button.configure(text="🔄 正在处理...")
    
    def start_progress(self):
        """开始进度条动画"""
        self.progress_bar.start()
    
    def stop_progress(self):
        """停止进度条动画"""
        self.progress_bar.stop()
    
    def get_parameters(self):
        """获取当前参数设置"""
        algorithm = self.algorithm_var.get()

        if algorithm == "MST":
            return {
                'algorithm': 'MST',
                'alpha': self.alpha_var.get(),
                'beta': self.beta_var.get(),
                'connectivity': self.connectivity_var.get(),
                'threshold': None if self.auto_threshold_var.get() else self.threshold_var.get(),
                'auto_threshold': self.auto_threshold_var.get()
            }
        elif algorithm == "Watershed":
            return {
                'algorithm': 'Watershed',
                'min_distance': self.min_distance_var.get(),
                'compactness': self.compactness_var.get(),
                'watershed_line': self.watershed_line_var.get()
            }
        else:
            return {'algorithm': 'MST'}  # 默认返回MST参数

    def get_selected_algorithm(self):
        """获取选择的算法"""
        return self.algorithm_var.get()
