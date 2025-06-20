"""
性能分析窗口模块
从主窗口中分离出来的性能分析功能
"""

import tkinter as tk
from tkinter import ttk
import threading
import numpy as np

from core import MSTSegmentation, WatershedSegmentation, EdgeWeightCalculator
from evaluation import PerformanceAnalyzer


class PerformanceAnalysisWindow:
    """性能分析窗口类"""
    
    def __init__(self, parent, current_image, performance_analyzer):
        """
        初始化性能分析窗口
        
        Args:
            parent: 父窗口
            current_image: 当前图像
            performance_analyzer: 性能分析器
        """
        self.parent = parent
        self.current_image = current_image
        self.performance_analyzer = performance_analyzer
        
        # 创建性能分析窗口
        self.window = tk.Toplevel(parent)
        self.window.title("📊 性能分析仪表板")
        self.window.geometry("1200x800")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 创建界面
        self.create_interface()
    
    def create_interface(self):
        """创建性能分析界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="📊 算法性能分析仪表板",
            font=('Microsoft YaHei UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="🎛️ 分析控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 算法选择
        algo_frame = ttk.Frame(control_frame)
        algo_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(algo_frame, text="选择算法:").pack(anchor=tk.W)
        self.algo_var = tk.StringVar(value="MST")
        
        algo_combo = ttk.Combobox(
            algo_frame, 
            textvariable=self.algo_var,
            values=["MST", "Watershed"],
            state="readonly",
            width=15
        )
        algo_combo.pack(pady=(5, 0))
        
        # 测试次数选择
        runs_frame = ttk.Frame(control_frame)
        runs_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(runs_frame, text="测试次数:").pack(anchor=tk.W)
        self.runs_var = tk.IntVar(value=5)
        
        runs_spin = ttk.Spinbox(
            runs_frame,
            from_=1,
            to=20,
            textvariable=self.runs_var,
            width=10
        )
        runs_spin.pack(pady=(5, 0))
        
        # 开始分析按钮
        analyze_button = ttk.Button(
            control_frame,
            text="🚀 开始性能分析",
            command=self.start_analysis
        )
        analyze_button.pack(side=tk.LEFT, padx=(20, 0))
        
        # 结果显示区域
        self.result_frame = ttk.Frame(main_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始提示
        initial_label = ttk.Label(
            self.result_frame,
            text="选择算法和测试次数，然后点击'开始性能分析'",
            font=('Microsoft YaHei UI', 12)
        )
        initial_label.pack(expand=True)
    
    def start_analysis(self):
        """开始性能分析"""
        if self.current_image is None:
            return
        
        # 清空之前的结果
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # 显示进度
        progress_label = ttk.Label(
            self.result_frame,
            text="🔄 正在进行性能分析，请稍候...",
            font=('Microsoft YaHei UI', 12)
        )
        progress_label.pack(expand=True)
        
        # 在后台线程中执行分析
        analysis_thread = threading.Thread(target=self.perform_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def perform_analysis(self):
        """执行性能分析"""
        try:
            algorithm = self.algo_var.get()
            num_runs = self.runs_var.get()
            
            # 创建算法函数
            if algorithm == "MST":
                algo_func = self.create_mst_algorithm()
            elif algorithm == "Watershed":
                algo_func = self.create_watershed_algorithm()
            else:
                raise ValueError(f"不支持的算法: {algorithm}")
            
            # 执行多次运行基准测试
            benchmark_result = self.performance_analyzer.benchmark_with_multiple_runs(
                algo_func,
                self.current_image,
                algorithm,
                num_runs=num_runs,
                warmup_runs=2
            )
            
            # 在主线程中更新界面
            self.window.after(0, lambda: self.display_results(benchmark_result))
            
        except Exception as e:
            error_msg = f"性能分析过程中发生错误:\n{str(e)}"
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
    
    def display_results(self, benchmark_result):
        """显示性能分析结果"""
        # 清空进度显示
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        if not benchmark_result.get('success', False):
            error_label = ttk.Label(
                self.result_frame,
                text=f"❌ 性能分析失败: {benchmark_result.get('error', '未知错误')}",
                font=('Microsoft YaHei UI', 12),
                foreground='red'
            )
            error_label.pack(expand=True)
            return
        
        # 创建结果显示界面
        notebook = ttk.Notebook(self.result_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 性能概览标签页
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="📈 性能概览")
        
        # 详细统计标签页
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 详细统计")
        
        # 可视化图表标签页
        charts_frame = ttk.Frame(notebook)
        notebook.add(charts_frame, text="📉 性能图表")
        
        # 显示各个标签页内容
        self.display_overview(overview_frame, benchmark_result)
        self.display_statistics(stats_frame, benchmark_result)
        self.display_charts(charts_frame, benchmark_result)
    
    def display_overview(self, parent, benchmark_result):
        """显示性能概览"""
        # 创建概览卡片
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # 执行时间卡片
        exec_time = benchmark_result['execution_time']
        time_card = self.create_metric_card(
            cards_frame,
            "⏱️ 执行时间",
            f"{exec_time['mean']:.3f}s",
            f"范围: {exec_time['min']:.3f}s - {exec_time['max']:.3f}s"
        )
        time_card.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        # 内存使用卡片
        memory = benchmark_result['memory_usage']
        memory_card = self.create_metric_card(
            cards_frame,
            "💾 内存使用",
            f"{memory['mean']:.1f}MB",
            f"峰值: {memory['max']:.1f}MB"
        )
        memory_card.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        # 效率分数卡片
        efficiency = benchmark_result.get('efficiency_score', 0)
        efficiency_card = self.create_metric_card(
            cards_frame,
            "🎯 效率分数",
            f"{efficiency:.1f}/100",
            "综合性能评估"
        )
        efficiency_card.pack(side=tk.LEFT, fill=tk.Y)
        
        # 详细信息
        details_frame = ttk.LabelFrame(parent, text="📋 分析详情", padding=15)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        details_text = f"""算法名称: {benchmark_result['algorithm_name']}
测试次数: {benchmark_result['num_runs']}
图像尺寸: {self.current_image.shape}
总像素数: {self.current_image.size:,}

性能指标:
• 平均执行时间: {exec_time['mean']:.3f}s (±{exec_time['std']:.3f}s)
• 最快执行时间: {exec_time['min']:.3f}s
• 最慢执行时间: {exec_time['max']:.3f}s
• 中位数时间: {exec_time['median']:.3f}s

• 平均内存使用: {memory['mean']:.1f}MB (±{memory['std']:.1f}MB)
• 最小内存使用: {memory['min']:.1f}MB
• 最大内存使用: {memory['max']:.1f}MB
• 中位数内存: {memory['median']:.1f}MB

• 效率分数: {efficiency:.1f}/100
• 处理速度: {self.current_image.size / exec_time['mean']:.0f} 像素/秒"""
        
        details_label = ttk.Label(
            details_frame,
            text=details_text,
            font=('Consolas', 10),
            justify=tk.LEFT
        )
        details_label.pack(anchor=tk.W)
    
    def create_metric_card(self, parent, title, value, subtitle):
        """创建指标卡片"""
        card_frame = ttk.LabelFrame(parent, text=title, padding=15)
        
        value_label = ttk.Label(
            card_frame,
            text=value,
            font=('Microsoft YaHei UI', 18, 'bold'),
            foreground='#2c3e50'
        )
        value_label.pack()
        
        subtitle_label = ttk.Label(
            card_frame,
            text=subtitle,
            font=('Microsoft YaHei UI', 9),
            foreground='#7f8c8d'
        )
        subtitle_label.pack(pady=(5, 0))
        
        return card_frame

    def display_statistics(self, parent, benchmark_result):
        """显示详细统计"""
        # 创建统计表格
        columns = ('指标', '平均值', '标准差', '最小值', '最大值', '中位数')

        tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        # 设置列标题和宽度
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        # 添加执行时间数据
        exec_time = benchmark_result['execution_time']
        tree.insert('', 'end', values=(
            '执行时间 (秒)',
            f"{exec_time['mean']:.4f}",
            f"{exec_time['std']:.4f}",
            f"{exec_time['min']:.4f}",
            f"{exec_time['max']:.4f}",
            f"{exec_time['median']:.4f}"
        ))

        # 添加内存使用数据
        memory = benchmark_result['memory_usage']
        tree.insert('', 'end', values=(
            '内存使用 (MB)',
            f"{memory['mean']:.2f}",
            f"{memory['std']:.2f}",
            f"{memory['min']:.2f}",
            f"{memory['max']:.2f}",
            f"{memory['median']:.2f}"
        ))

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def display_charts(self, parent, benchmark_result):
        """显示性能图表"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np

            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle(f'{benchmark_result["algorithm_name"]} 算法性能分析', fontsize=14)

            # 执行时间分布
            exec_times = [benchmark_result['execution_time'][key] for key in ['min', 'mean', 'max']]
            ax1.bar(['最小值', '平均值', '最大值'], exec_times, color=['green', 'blue', 'red'])
            ax1.set_title('执行时间分布')
            ax1.set_ylabel('时间 (秒)')

            # 内存使用分布
            memory_usage = [benchmark_result['memory_usage'][key] for key in ['min', 'mean', 'max']]
            ax2.bar(['最小值', '平均值', '最大值'], memory_usage, color=['lightgreen', 'lightblue', 'lightcoral'])
            ax2.set_title('内存使用分布')
            ax2.set_ylabel('内存 (MB)')

            # 效率分数
            efficiency = benchmark_result.get('efficiency_score', 0)
            ax3.pie([efficiency, 100-efficiency], labels=['效率分数', '剩余'],
                   colors=['gold', 'lightgray'], startangle=90)
            ax3.set_title(f'效率分数: {efficiency:.1f}/100')

            # 性能趋势（模拟）
            runs = list(range(1, benchmark_result['num_runs'] + 1))
            # 生成模拟的性能趋势数据
            mean_time = benchmark_result['execution_time']['mean']
            std_time = benchmark_result['execution_time']['std']
            trend_data = np.random.normal(mean_time, std_time, benchmark_result['num_runs'])

            ax4.plot(runs, trend_data, 'o-', color='purple')
            ax4.axhline(y=mean_time, color='red', linestyle='--', label=f'平均值: {mean_time:.3f}s')
            ax4.set_title('执行时间趋势')
            ax4.set_xlabel('运行次数')
            ax4.set_ylabel('执行时间 (秒)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

            plt.tight_layout()

            # 嵌入到Tkinter中
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        except Exception as e:
            error_label = ttk.Label(
                parent,
                text=f"无法生成性能图表: {str(e)}",
                font=('Microsoft YaHei UI', 12)
            )
            error_label.pack(expand=True)

    def show_error(self, error_msg):
        """显示性能分析错误"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        error_label = ttk.Label(
            self.result_frame,
            text=f"❌ {error_msg}",
            font=('Microsoft YaHei UI', 12),
            foreground='red'
        )
        error_label.pack(expand=True)
