"""
控制面板组件
包含图像加载、参数设置、执行控制和结果显示
"""

import tkinter as tk
from tkinter import ttk
from .style_manager import get_style_manager


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
        
        # 创建主框架
        self.main_frame = self.style_manager.create_labelframe(
            parent, 
            text="🎛️ 控制面板", 
            padding=15,
            style_name='Heading.TLabelFrame'
        )
        self.main_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.main_frame.configure(width=350)
        
        # 初始化变量
        self.init_variables()
        
        # 创建子组件
        self.create_image_loader()
        self.create_parameter_panel()
        self.create_execution_panel()
        self.create_result_panel()
    
    def init_variables(self):
        """初始化控制变量"""
        self.alpha_var = tk.DoubleVar(value=1.0)
        self.beta_var = tk.DoubleVar(value=0.1)
        self.connectivity_var = tk.IntVar(value=4)
        self.threshold_var = tk.DoubleVar(value=0.0)
        self.auto_threshold_var = tk.BooleanVar(value=True)
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
    
    def create_parameter_panel(self):
        """创建参数设置区域"""
        param_frame = self.style_manager.create_labelframe(
            self.main_frame,
            text="⚙️ 算法参数",
            padding=10,
            style_name='Heading.TLabelFrame'
        )
        param_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 颜色权重
        self.create_alpha_control(param_frame)
        
        # 空间权重
        self.create_beta_control(param_frame)
        
        # 连接性
        self.create_connectivity_control(param_frame)
        
        # 分割阈值
        self.create_threshold_control(param_frame)
    
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
        self.progress_text.configure(text=text)
        if progress is not None:
            self.progress_var.set(progress)
    
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
        return {
            'alpha': self.alpha_var.get(),
            'beta': self.beta_var.get(),
            'connectivity': self.connectivity_var.get(),
            'threshold': None if self.auto_threshold_var.get() else self.threshold_var.get(),
            'auto_threshold': self.auto_threshold_var.get()
        }
