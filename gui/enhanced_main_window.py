"""
美化版主窗口
集成主题管理、增强图像显示和现代化界面设计
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
from utils.image_io import ImageLoader, ImageSaver, ImageLoadError
from utils.visualization import SegmentationVisualizer
from utils.image_diagnostics import ImageDiagnostics
from data_structures.segmentation_result import SegmentationResult

# 导入GUI组件
from .style_manager import get_style_manager
from .theme_manager import get_theme_manager
from .control_panel import ControlPanel
from .enhanced_image_display import EnhancedImageDisplay


class EnhancedMainWindow:
    """美化版主窗口类"""

    def __init__(self, root):
        self.root = root
        self.setup_window()

        # 获取管理器
        self.style_manager = get_style_manager()
        self.theme_manager = get_theme_manager()

        # 数据存储
        self.current_image = None
        self.segmentation_result = None
        self.image_loader = ImageLoader(
            max_size=(4096, 4096),
            auto_orient=True,
            normalize_format=True
        )
        self.image_saver = ImageSaver()
        self.visualizer = SegmentationVisualizer()
        self.diagnostics = ImageDiagnostics()

        # 状态变量
        self.is_processing = False
        self.processing_thread = None

        # 加载保存的主题
        saved_theme = self.theme_manager.load_theme_preference()
        self.theme_manager.apply_theme(saved_theme)

        # 创建界面
        self.create_menu()
        self.create_widgets()

        # 设置窗口属性
        self.root.minsize(1200, 800)
        self.center_window()

        # 显示启动信息
        self.show_startup_info()

    def setup_window(self):
        """设置窗口基本属性"""
        self.root.title("🖼️ 图像分割系统 - 美化增强版")
        self.root.geometry("1600x1000")

        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass

    def show_startup_info(self):
        """显示启动信息"""
        theme_name = self.theme_manager.get_current_theme()
        theme_display_name = self.theme_manager.themes[theme_name]["name"]

        print("🎨 美化版图像分割系统启动")
        print(f"  当前主题: {theme_display_name}")
        print(f"  图像加载器: 增强版 (支持多格式、中文路径)")
        print(f"  图像显示: 增强版 (支持缩放、拖拽、动画)")
        print("  界面特性: 主题切换、响应式布局、现代化设计")

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
        menubar.add_cascade(label="📁 文件", menu=file_menu)
        file_menu.add_command(label="🖼️ 打开图像", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 保存结果", command=self.save_result, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="🔍 图像诊断", command=self.show_image_diagnostics)
        file_menu.add_separator()
        file_menu.add_command(label="❌ 退出", command=self.root.quit, accelerator="Ctrl+Q")

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ 视图", menu=view_menu)

        # 主题子菜单
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="🎨 主题", menu=theme_menu)

        self.theme_var = tk.StringVar(value=self.theme_manager.get_current_theme())
        for theme_key, theme_name in self.theme_manager.get_available_themes().items():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_key,
                command=lambda t=theme_key: self.change_theme(t)
            )

        view_menu.add_separator()
        view_menu.add_command(label="🔄 重置视图", command=self.reset_view)
        view_menu.add_command(label="📐 适应窗口", command=self.fit_to_window)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 工具", menu=tools_menu)
        tools_menu.add_command(label="📊 性能分析", command=self.show_performance_analysis)
        tools_menu.add_command(label="⚖️ 算法对比", command=self.show_algorithm_comparison)
        tools_menu.add_command(label="🎨 样式状态", command=self.show_style_info)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ 帮助", menu=help_menu)
        help_menu.add_command(label="📖 使用说明", command=self.show_help)
        help_menu.add_command(label="🔧 快捷键", command=self.show_shortcuts)
        help_menu.add_command(label="ℹ️ 关于", command=self.show_about)

        # 绑定快捷键
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_result())
        self.root.bind("<Control-q>", lambda e: self.root.quit())

    def create_widgets(self):
        """创建界面组件"""
        # 创建标题栏
        self.create_title_bar()

        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建回调函数字典
        callbacks = {
            'load_image': self.load_image,
            'start_segmentation': self.start_segmentation
        }

        # 创建控制面板
        self.control_panel = ControlPanel(main_frame, callbacks)

        # 创建增强版图像显示区域
        self.image_display = EnhancedImageDisplay(main_frame, self.image_loader)
        self.image_display.on_image_click = self.on_image_click
        self.image_display.on_zoom_change = self.on_zoom_change

        # 创建状态栏
        self.create_status_bar()

        # 应用主题
        self.apply_theme()
        self.theme_manager.add_theme_callback(self._on_theme_change)

    def create_title_bar(self):
        """创建美化的标题栏"""
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 主标题
        title_label = ttk.Label(
            title_frame,
            text="🖼️ 图像分割系统",
            font=self.theme_manager.get_font("title")
        )
        title_label.pack(side=tk.LEFT)

        # 副标题
        subtitle_label = ttk.Label(
            title_frame,
            text="基于最小生成树(MST)算法的智能图像分割 - 美化增强版",
            font=self.theme_manager.get_font("default"),
            foreground=self.theme_manager.get_color("fg_secondary")
        )
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))

        # 版本信息
        version_label = ttk.Label(
            title_frame,
            text="v2.0",
            font=self.theme_manager.get_font("small"),
            foreground=self.theme_manager.get_color("accent_primary")
        )
        version_label.pack(side=tk.RIGHT)

    def create_status_bar(self):
        """创建美化的状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))

        # 状态栏背景
        status_bg = ttk.Frame(status_frame, style="Card.TFrame")
        status_bg.pack(fill=tk.X)

        # 主状态文本
        self.status_var = tk.StringVar(value="✅ 系统就绪 - 请选择图像文件开始分割")
        status_label = ttk.Label(
            status_bg,
            textvariable=self.status_var,
            font=self.theme_manager.get_font("default"),
            foreground=self.theme_manager.get_color("accent_secondary")
        )
        status_label.pack(side=tk.LEFT, padx=10, pady=8)

        # 分隔符
        separator = ttk.Separator(status_bg, orient=tk.VERTICAL)
        separator.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # 主题显示
        theme_name = self.theme_manager.themes[self.theme_manager.get_current_theme()]["name"]
        self.theme_status_var = tk.StringVar(value=f"🎨 {theme_name}")
        theme_label = ttk.Label(
            status_bg,
            textvariable=self.theme_status_var,
            font=self.theme_manager.get_font("small"),
            foreground=self.theme_manager.get_color("fg_secondary")
        )
        theme_label.pack(side=tk.RIGHT, padx=10, pady=8)

    def change_theme(self, theme_name: str):
        """切换主题"""
        try:
            self.theme_manager.apply_theme(theme_name)
            self.theme_manager.save_theme_preference(theme_name)

            # 更新主题状态显示
            theme_display_name = self.theme_manager.themes[theme_name]["name"]
            self.theme_status_var.set(f"🎨 {theme_display_name}")

            self.status_var.set(f"🎨 已切换到{theme_display_name}")

        except Exception as e:
            messagebox.showerror("主题错误", f"切换主题失败: {str(e)}")

    def apply_theme(self):
        """应用主题到窗口"""
        theme = self.theme_manager.get_theme_config()
        colors = theme["colors"]

        # 更新根窗口背景
        self.root.configure(bg=colors["bg_primary"])

    def _on_theme_change(self, theme_name: str, theme_config: dict):
        """主题变更回调"""
        self.apply_theme()

    def load_image(self):
        """加载图像"""
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=[
                ("所有支持的图像", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("PNG文件", "*.png"),
                ("BMP文件", "*.bmp"),
                ("TIFF文件", "*.tiff *.tif"),
                ("WebP文件", "*.webp"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.status_var.set("📂 正在加载图像...")
            self.root.update()

            try:
                # 使用增强版加载器
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
                    info_text += f"💾 大小: {file_size:.1f} KB\n"
                    info_text += f"🔧 加载器: 增强版"

                    self.control_panel.update_image_info(info_text)

                    # 显示图像
                    self.image_display.display_image(image)

                    # 启用分割按钮
                    self.control_panel.enable_segment_button(True)

                    # 获取加载统计（安全访问）
                    try:
                        stats = self.image_loader.get_load_statistics()
                        if stats and isinstance(stats, dict):
                            self.status_var.set(
                                f"✅ 图像加载完成 - {width}×{height} 像素 "
                                f"(成功: {stats.get('total_loaded', 0)}, 转换: {stats.get('format_conversions', 0)})"
                            )
                        else:
                            self.status_var.set(f"✅ 图像加载完成 - {width}×{height} 像素")
                    except Exception as e:
                        print(f"获取加载统计时发生错误: {e}")
                        self.status_var.set(f"✅ 图像加载完成 - {width}×{height} 像素")
                else:
                    messagebox.showerror("❌ 加载失败", "无法加载图像文件\n请检查文件格式是否支持")
                    self.status_var.set("❌ 图像加载失败")

            except ImageLoadError as e:
                messagebox.showerror("❌ 图像加载错误", str(e))
                self.status_var.set("❌ 图像加载失败")
            except Exception as e:
                messagebox.showerror("❌ 未知错误", f"加载图像时发生错误:\n{str(e)}")
                self.status_var.set("❌ 图像加载失败")

    def show_image_diagnostics(self):
        """显示图像诊断"""
        if self.current_image is None:
            messagebox.showwarning("⚠️ 警告", "请先加载图像文件")
            return

        # 这里可以显示详细的诊断信息
        messagebox.showinfo("🔍 图像诊断", "图像诊断功能正在开发中...")

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
        self.processing_thread = threading.Thread(target=self.perform_segmentation, args=(params,))
        self.processing_thread.daemon = True
        self.processing_thread.start()

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
            try:
                # 确保控制面板存在且有update_progress方法
                if hasattr(self, 'control_panel') and hasattr(self.control_panel, 'update_progress'):
                    self.control_panel.update_progress(message, progress)

                # 更新状态栏
                if hasattr(self, 'status_var'):
                    if progress >= 0:
                        self.status_var.set(f"🔄 {message}")
                    else:
                        self.status_var.set(f"❌ {message}")
            except Exception as e:
                print(f"更新进度显示时发生错误: {e}")

        # 确保在主线程中执行
        if hasattr(self, 'root') and self.root:
            self.root.after(0, update)
        else:
            update()

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

            # 显示结果（这里需要扩展图像显示组件来支持多个图像）
            # 暂时显示分割结果
            self.image_display.display_image(segmented_image, reset_view=False)

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

        info_text += f"\n🎨 当前主题: {self.theme_manager.themes[self.theme_manager.get_current_theme()]['name']}"

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
                ("WebP文件", "*.webp"),
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

    def on_image_click(self, x, y):
        """图像点击回调"""
        if self.current_image is not None:
            h, w = self.current_image.shape[:2]
            if 0 <= x < w and 0 <= y < h:
                pixel = self.current_image[int(y), int(x)]
                self.status_var.set(f"🖱️ 点击位置: ({x:.0f}, {y:.0f}), RGB({pixel[0]}, {pixel[1]}, {pixel[2]})")

    def on_zoom_change(self, zoom_factor):
        """缩放变化回调"""
        self.status_var.set(f"🔍 缩放: {zoom_factor*100:.0f}%")

    def reset_view(self):
        """重置视图"""
        self.image_display.reset_view()
        self.status_var.set("🔄 视图已重置")

    def fit_to_window(self):
        """适应窗口"""
        self.image_display.fit_to_window()
        self.status_var.set("📐 已适应窗口大小")

    def show_performance_analysis(self):
        """显示性能分析"""
        if self.segmentation_result is None:
            messagebox.showwarning("⚠️ 警告", "请先执行图像分割")
            return

        # 获取统计信息
        loader_stats = self.image_loader.get_load_statistics()
        saver_stats = self.image_saver.get_save_statistics()

        analysis_text = f"""📊 性能分析报告

🖼️ 图像加载统计:
• 总加载次数: {loader_stats['total_loaded']}
• 失败次数: {loader_stats['failed_loads']}
• 格式转换: {loader_stats['format_conversions']}
• 尺寸调整: {loader_stats['size_reductions']}

💾 图像保存统计:
• 总保存次数: {saver_stats['total_saved']}
• 失败次数: {saver_stats['failed_saves']}

🎯 分割结果:
• 区域数量: {self.segmentation_result.statistics['num_segments']}
• 平均区域大小: {self.segmentation_result.statistics['avg_segment_size']:.1f}
• 处理图像尺寸: {self.current_image.shape}

🎨 当前配置:
• 主题: {self.theme_manager.themes[self.theme_manager.get_current_theme()]['name']}
• 图像显示: 增强版 (支持缩放拖拽)
• 图像加载: 增强版 (多格式支持)
"""

        messagebox.showinfo("📊 性能分析", analysis_text)

    def show_algorithm_comparison(self):
        """显示算法对比"""
        messagebox.showinfo("⚖️ 算法对比", "算法对比功能正在开发中...")

    def show_style_info(self):
        """显示样式信息"""
        status = self.style_manager.get_status()
        theme_info = self.theme_manager.get_theme_config()

        info_text = f"""🎨 样式和主题状态

📋 样式管理器:
• Python版本: {status['python_version']}
• 主题可用: {'✅' if status['theme_available'] else '❌'}
• 自定义样式: {'✅' if status['custom_styles_available'] else '❌'}
• 可用主题: {', '.join(status['available_themes'])}

🎨 当前主题: {theme_info['name']}
• 主色调: {theme_info['colors']['bg_primary']}
• 强调色: {theme_info['colors']['accent_primary']}
• 字体: {theme_info['fonts']['default'][0]}

💡 如果样式显示异常，这是正常的兼容性处理。
系统会自动使用备用样式确保功能正常。
"""

        messagebox.showinfo("🎨 样式状态", info_text)

    def show_help(self):
        """显示帮助信息"""
        help_text = """📖 使用说明

🖼️ 图像操作:
• 打开图像: 文件 → 打开图像 (Ctrl+O)
• 保存结果: 文件 → 保存结果 (Ctrl+S)
• 图像诊断: 文件 → 图像诊断

👁️ 视图操作:
• 缩放: 鼠标滚轮 或 +/- 键
• 拖拽: 鼠标左键拖拽
• 适应窗口: F 键 或 视图菜单
• 实际大小: 0 键
• 重置视图: R 键

🎨 主题切换:
• 浅色主题: 适合白天使用
• 深色主题: 适合夜间使用
• 蓝色主题: 专业商务风格
• 绿色主题: 清新自然风格

⚙️ 分割参数:
• 颜色权重(α): 控制颜色相似性重要程度
• 空间权重(β): 控制空间距离重要程度
• 连接性: 4-连通或8-连通
• 分割阈值: 控制分割细粒度
"""

        messagebox.showinfo("📖 使用说明", help_text)

    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts_text = """🔧 快捷键列表

📁 文件操作:
• Ctrl+O: 打开图像
• Ctrl+S: 保存结果
• Ctrl+Q: 退出程序

👁️ 视图操作:
• 鼠标滚轮: 缩放图像
• +/=: 放大图像
• -: 缩小图像
• 0: 实际大小
• F: 适应窗口
• R: 重置视图

🖱️ 鼠标操作:
• 左键拖拽: 平移图像
• 左键点击: 查看像素信息
• 滚轮: 缩放图像

⌨️ 其他:
• Tab: 切换焦点
• Enter: 确认操作
• Esc: 取消操作
"""

        messagebox.showinfo("🔧 快捷键", shortcuts_text)

    def show_about(self):
        """显示关于信息"""
        about_text = f"""🖼️ 图像分割系统 v2.0 (美化增强版)

🔬 基于图论的智能图像分割系统
🌟 使用最小生成树(MST)算法

✨ 新增特性:
• 🎨 多主题支持 (浅色/深色/蓝色/绿色)
• 🖼️ 增强图像显示 (缩放/拖拽/动画)
• 📁 强化图像加载 (多格式/中文路径/错误恢复)
• 🎯 智能参数建议和质量评估
• 📊 详细性能分析和统计信息
• 🔧 完善的快捷键支持

🛠️ 技术栈:
• Python 3.8+ (当前: {sys.version.split()[0]})
• OpenCV 图像处理
• NumPy 数值计算
• Tkinter GUI框架 (增强版)
• PIL/Pillow 图像处理

🎨 界面特性:
• 响应式布局设计
• 主题动态切换
• 现代化视觉元素
• 流畅的动画效果

👥 开发团队: 图像处理研究组
📅 版本日期: 2025年6月
🏷️ 许可证: MIT License

💡 当前主题: {self.theme_manager.themes[self.theme_manager.get_current_theme()]['name']}
"""

        messagebox.showinfo("ℹ️ 关于系统", about_text)