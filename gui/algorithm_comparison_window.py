"""
算法对比窗口模块
从主窗口中分离出来的算法对比功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import numpy as np

from core import MSTSegmentation, WatershedSegmentation, EdgeWeightCalculator
from evaluation import AlgorithmComparator


class AlgorithmComparisonWindow:
    """算法对比窗口类"""
    
    def __init__(self, parent, current_image, algorithm_comparator):
        """
        初始化算法对比窗口
        
        Args:
            parent: 父窗口
            current_image: 当前图像
            algorithm_comparator: 算法对比器
        """
        self.parent = parent
        self.current_image = current_image
        self.algorithm_comparator = algorithm_comparator
        
        # 创建对比窗口
        self.window = tk.Toplevel(parent)
        self.window.title("⚖️ 算法对比分析")
        self.window.geometry("1400x900")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 创建界面
        self.create_interface()
    
    def create_interface(self):
        """创建对比界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="🔬 算法性能对比分析",
            font=('Microsoft YaHei UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="🎛️ 对比控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 开始对比按钮
        compare_button = ttk.Button(
            control_frame,
            text="🚀 开始算法对比",
            command=self.start_comparison
        )
        compare_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存结果按钮
        self.save_button = ttk.Button(
            control_frame,
            text="💾 保存对比结果",
            command=self.save_results,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT)
        
        # 结果显示区域
        self.result_frame = ttk.Frame(main_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始提示
        initial_label = ttk.Label(
            self.result_frame,
            text="点击'开始算法对比'来比较MST和Watershed算法的性能",
            font=('Microsoft YaHei UI', 12)
        )
        initial_label.pack(expand=True)
    
    def start_comparison(self):
        """开始算法对比"""
        if self.current_image is None:
            return
        
        # 清空之前的结果
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # 显示进度
        progress_label = ttk.Label(
            self.result_frame,
            text="🔄 正在进行算法对比分析，请稍候...",
            font=('Microsoft YaHei UI', 12)
        )
        progress_label.pack(expand=True)
        
        # 在后台线程中执行对比
        comparison_thread = threading.Thread(target=self.perform_comparison)
        comparison_thread.daemon = True
        comparison_thread.start()
    
    def perform_comparison(self):
        """执行算法对比"""
        try:
            # 定义要对比的算法
            algorithms = [
                {
                    'name': 'MST',
                    'func': self.create_mst_algorithm(),
                    'params': {}
                },
                {
                    'name': 'Watershed',
                    'func': self.create_watershed_algorithm(),
                    'params': {}
                }
            ]
            
            # 执行对比
            comparison_result = self.algorithm_comparator.compare_algorithms(
                algorithms,
                self.current_image,
                save_results=False
            )
            
            # 在主线程中更新界面
            self.window.after(0, lambda: self.display_results(comparison_result))
            
        except Exception as e:
            error_msg = f"算法对比过程中发生错误:\n{str(e)}"
            self.window.after(0, lambda: self.show_error(error_msg))
    
    def create_mst_algorithm(self):
        """创建MST算法函数"""
        def mst_segment(image):
            weight_calculator = EdgeWeightCalculator(alpha=1.0, beta=0.1)
            segmenter = MSTSegmentation(
                connectivity=4,
                weight_calculator=weight_calculator,
                min_segment_size=max(10, image.size // 10000)
            )
            return segmenter.segment(image)
        return mst_segment
    
    def create_watershed_algorithm(self):
        """创建Watershed算法函数"""
        def watershed_segment(image):
            segmenter = WatershedSegmentation(
                min_distance=20,
                compactness=0.001,
                watershed_line=True
            )
            return segmenter.segment(image)
        return watershed_segment
    
    def display_results(self, comparison_result):
        """显示对比结果"""
        # 清空进度显示
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # 创建结果显示界面
        notebook = ttk.Notebook(self.result_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 可视化对比标签页
        visual_frame = ttk.Frame(notebook)
        notebook.add(visual_frame, text="📊 可视化对比")
        
        # 性能指标标签页
        metrics_frame = ttk.Frame(notebook)
        notebook.add(metrics_frame, text="📈 性能指标")
        
        # 详细报告标签页
        report_frame = ttk.Frame(notebook)
        notebook.add(report_frame, text="📋 详细报告")
        
        # 显示各个标签页内容
        self.display_visual_comparison(visual_frame, comparison_result)
        self.display_performance_metrics(metrics_frame, comparison_result)
        self.display_detailed_report(report_frame, comparison_result)
        
        # 启用保存按钮
        self.save_button.configure(state=tk.NORMAL)
        self.current_comparison_result = comparison_result
    
    def display_visual_comparison(self, parent, comparison_result):
        """显示可视化对比"""
        try:
            # 使用matplotlib显示对比图
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            fig = self.algorithm_comparator.visualize_comparison(comparison_result)
            if fig:
                canvas = FigureCanvasTkAgg(fig, parent)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                error_label = ttk.Label(parent, text="无法生成可视化对比图")
                error_label.pack(expand=True)
                
        except Exception as e:
            error_label = ttk.Label(parent, text=f"显示可视化对比时发生错误: {str(e)}")
            error_label.pack(expand=True)
    
    def display_performance_metrics(self, parent, comparison_result):
        """显示性能指标"""
        # 创建表格显示性能指标
        columns = ('算法', '执行时间(s)', '内存使用(MB)', '分割区域数', '成功状态')
        
        tree = ttk.Treeview(parent, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # 添加数据
        performance_results = comparison_result.get('performance_results', {})
        algorithm_results = comparison_result.get('algorithm_results', {})
        
        for alg_name in performance_results:
            perf = performance_results[alg_name]
            alg_result = algorithm_results.get(alg_name, {})
            
            success = "✅ 成功" if alg_result.get('success', False) else "❌ 失败"
            segments = alg_result.get('metrics', {}).get('num_segments', 'N/A')
            
            tree.insert('', 'end', values=(
                alg_name,
                f"{perf.get('execution_time', 0):.3f}",
                f"{perf.get('memory_used_mb', 0):.1f}",
                segments,
                success
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def display_detailed_report(self, parent, comparison_result):
        """显示详细报告"""
        # 创建文本框显示详细报告
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # 生成报告内容
        report_content = self.generate_report(comparison_result)
        text_widget.insert(tk.END, report_content)
        text_widget.configure(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def generate_report(self, comparison_result):
        """生成对比报告内容"""
        report = "=" * 60 + "\n"
        report += "🔬 算法对比分析报告\n"
        report += "=" * 60 + "\n\n"
        
        # 基本信息
        report += f"📅 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"🖼️ 测试图像: {self.current_image.shape}\n\n"
        
        # 对比摘要
        summary = comparison_result.get('comparison_summary', {})
        report += "📊 对比摘要:\n"
        report += "-" * 30 + "\n"
        report += f"总算法数: {summary.get('total_algorithms', 0)}\n"
        report += f"成功算法数: {summary.get('successful_algorithms', 0)}\n"
        report += f"失败算法数: {summary.get('failed_algorithms', 0)}\n\n"
        
        if summary.get('successful_algorithms', 0) > 0:
            fastest = summary.get('fastest_algorithm', {})
            memory_efficient = summary.get('most_memory_efficient', {})
            
            report += f"🏃 最快算法: {fastest.get('name', 'N/A')} "
            report += f"({fastest.get('execution_time', 0):.3f}s)\n"
            
            report += f"💾 最省内存: {memory_efficient.get('name', 'N/A')} "
            report += f"({memory_efficient.get('memory_usage', 0):.1f}MB)\n\n"
        
        return report
    
    def show_error(self, error_msg):
        """显示对比错误"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        error_label = ttk.Label(
            self.result_frame,
            text=f"❌ {error_msg}",
            font=('Microsoft YaHei UI', 12),
            foreground='red'
        )
        error_label.pack(expand=True)
    
    def save_results(self):
        """保存对比结果"""
        if not hasattr(self, 'current_comparison_result'):
            messagebox.showwarning("⚠️ 警告", "没有可保存的对比结果")
            return
        
        try:
            # 选择保存目录
            save_dir = filedialog.askdirectory(title="选择保存目录")
            if save_dir:
                self.algorithm_comparator._save_comparison_results(
                    self.current_comparison_result, 
                    save_dir
                )
                messagebox.showinfo("✅ 保存成功", f"对比结果已保存到:\n{save_dir}")
        except Exception as e:
            messagebox.showerror("❌ 保存失败", f"保存对比结果时发生错误:\n{str(e)}")
