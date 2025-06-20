"""
重构后的主窗口
使用模块化组件和兼容的样式管理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
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

# 导入GUI组件
from .style_manager import get_style_manager
from .control_panel import ControlPanel
from .image_display import ImageDisplay


class MainWindowRefactored:
    """重构后的主窗口类"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # 获取样式管理器
        self.style_manager = get_style_manager()
        
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
        
        # 设置窗口属性
        self.root.minsize(1000, 700)
        self.center_window()
        
        # 显示样式管理器状态
        self.show_style_status()
    
    def setup_window(self):
        """设置窗口基本属性"""
        self.root.title("🖼️ 图像分割系统 - MST算法 (兼容版)")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
    
    def show_style_status(self):
        """显示样式管理器状态"""
        status = self.style_manager.get_status()
        print("🎨 样式管理器状态:")
        print(f"  Python版本: {status['python_version']}")
        print(f"  主题可用: {status['theme_available']}")
        print(f"  自定义样式可用: {status['custom_styles_available']}")
        print(f"  可用主题: {status['available_themes']}")
    
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
        tools_menu.add_command(label="样式状态", command=self.show_style_info)
        
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
        
        # 创建回调函数字典
        callbacks = {
            'load_image': self.load_image,
            'start_segmentation': self.start_segmentation
        }
        
        # 创建控制面板
        self.control_panel = ControlPanel(main_frame, callbacks)
        
        # 创建图像显示区域
        self.image_display = ImageDisplay(main_frame, self.image_loader)
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        # 主标题
        title_label = self.style_manager.create_label(
            title_frame,
            text="🖼️ 图像分割系统",
            style_name='Title.TLabel'
        )
        title_label.configure(font=('Microsoft YaHei UI', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 副标题
        subtitle_label = self.style_manager.create_label(
            title_frame,
            text="基于最小生成树(MST)算法的智能图像分割 (兼容版)",
            style_name='Info.TLabel'
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
    
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
        version_label = ttk.Label(status_bg, text="v1.1 (兼容版)",
                                 font=('Microsoft YaHei UI', 8),
                                 foreground='#95a5a6')
        version_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
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
                    
                    self.control_panel.update_image_info(info_text)
                    
                    # 显示图像
                    self.image_display.display_original_image(image)
                    
                    # 启用分割按钮
                    self.control_panel.enable_segment_button(True)
                    
                    self.status_var.set(f"✅ 图像加载完成 - {width}×{height} 像素")
                else:
                    messagebox.showerror("错误", "无法加载图像文件\n请检查文件格式是否支持")
                    self.status_var.set("❌ 图像加载失败")
                    
            except Exception as e:
                messagebox.showerror("错误", f"加载图像时发生错误:\n{str(e)}")
                self.status_var.set("❌ 图像加载失败")
    
    def start_segmentation(self):
        """开始分割处理"""
        if self.current_image is None:
            messagebox.showwarning("⚠️ 警告", "请先加载图像文件")
            return
        
        if self.is_processing:
            return
        
        # 获取参数
        params = self.control_panel.get_parameters()
        
        # 验证参数
        if params['alpha'] <= 0 or params['beta'] <= 0:
            messagebox.showerror("❌ 参数错误", "颜色权重和空间权重必须大于0")
            return
        
        # 开始处理
        self.is_processing = True
        self.control_panel.enable_segment_button(False)
        self.control_panel.start_progress()
        self.control_panel.update_progress("初始化...")
        self.status_var.set("🔄 正在执行图像分割...")
        
        # 清空结果显示
        self.control_panel.update_result_text("🔄 正在处理，请稍候...\n")
        
        # 创建后台线程
        thread = threading.Thread(target=self.perform_segmentation, args=(params,))
        thread.daemon = True
        thread.start()
    
    def perform_segmentation(self, params):
        """执行分割算法"""
        try:
            # 创建分割器
            self.update_progress("创建分割器...", 0.1)
            weight_calculator = EdgeWeightCalculator(alpha=params['alpha'], beta=params['beta'])
            segmenter = MSTSegmentation(
                connectivity=params['connectivity'],
                weight_calculator=weight_calculator,
                min_segment_size=max(10, self.current_image.size // 10000)
            )
            
            # 执行分割
            self.update_progress("开始图像分割...", 0.2)
            result = segmenter.segment(
                self.current_image,
                threshold=params['threshold'],
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
                    'alpha': params['alpha'],
                    'beta': params['beta'],
                    'connectivity': params['connectivity'],
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
    
    def update_progress(self, message, progress):
        """更新进度显示"""
        def update():
            self.control_panel.update_progress(message, progress)
            if progress >= 0:
                self.status_var.set(f"🔄 {message}")
            else:
                self.status_var.set(f"❌ {message}")
        
        self.root.after(0, update)
    
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
            self.image_display.display_segmentation_result(segmented_image)
            self.image_display.display_boundary_result(boundary_image)
            
            # 更新结果信息
            self.update_result_info()
            
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
            self.control_panel.enable_segment_button(True)
            self.control_panel.stop_progress()
            self.control_panel.update_progress("处理完成")
    
    def update_result_info(self):
        """更新结果信息显示"""
        if self.segmentation_result is None:
            return
        
        stats = self.segmentation_result.statistics
        params = self.segmentation_result.parameters
        
        # 计算额外统计信息
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
        
        self.control_panel.update_result_text(info_text)
    
    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("❌ 错误", message)
        self.is_processing = False
        self.control_panel.enable_segment_button(True)
        self.control_panel.stop_progress()
        self.control_panel.update_progress("发生错误")
        self.status_var.set("❌ 处理失败")
        
        # 更新结果文本显示错误信息
        self.control_panel.update_result_text(f"❌ 处理失败\n\n错误信息:\n{message}")
    
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
    
    def show_style_info(self):
        """显示样式信息"""
        status = self.style_manager.get_status()
        info_text = f"""🎨 样式管理器状态

Python版本: {status['python_version']}
主题可用: {'✅' if status['theme_available'] else '❌'}
自定义样式可用: {'✅' if status['custom_styles_available'] else '❌'}

可用主题: {', '.join(status['available_themes'])}

💡 如果样式显示异常，这是正常的兼容性处理。
系统会自动使用备用样式确保功能正常。"""
        
        messagebox.showinfo("🎨 样式状态", info_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """🖼️ 图像分割系统 v1.1 (兼容版)

🔬 基于图论的智能图像分割系统
🌟 使用最小生成树(MST)算法

✨ 主要特性:
• 高质量图像分割
• 实时参数调整
• 多种可视化模式
• 现代化用户界面
• 跨版本兼容性

🛠️ 技术栈:
• Python 3.8+
• OpenCV 图像处理
• NumPy 数值计算
• Tkinter GUI框架
• Matplotlib 可视化

🔧 兼容性:
• 支持Python 3.8-3.13+
• 自动样式降级
• 错误恢复机制

👥 开发团队: 图像处理研究组
📅 版本日期: 2025年6月
🏷️ 许可证: MIT License
"""
        messagebox.showinfo("ℹ️ 关于系统", about_text)
