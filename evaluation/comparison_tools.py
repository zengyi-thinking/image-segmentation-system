"""
算法对比工具
提供并排算法对比、结果可视化和性能分析展示功能
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional, Callable
import pandas as pd
from pathlib import Path
import time

from .metrics import SegmentationMetrics
from .performance_analyzer import PerformanceAnalyzer


class AlgorithmComparator:
    """
    算法对比器
    
    提供全面的算法对比功能：
    - 并排结果可视化
    - 量化指标对比
    - 性能分析对比
    - 详细报告生成
    """
    
    def __init__(self):
        self.metrics_calculator = SegmentationMetrics()
        self.performance_analyzer = PerformanceAnalyzer()
        self.comparison_results = []
    
    def compare_algorithms(self,
                         algorithms: List[Dict],
                         test_image: np.ndarray,
                         ground_truth: Optional[np.ndarray] = None,
                         save_results: bool = True,
                         output_dir: str = "comparison_results") -> Dict[str, Any]:
        """
        比较多个算法的性能和结果
        
        Args:
            algorithms: 算法列表，格式：[{'name': str, 'func': callable, 'params': dict}]
            test_image: 测试图像
            ground_truth: 真实标签（可选）
            save_results: 是否保存结果
            output_dir: 输出目录
            
        Returns:
            比较结果字典
        """
        print(f"开始比较 {len(algorithms)} 个算法...")
        
        # 存储所有结果
        algorithm_results = {}
        performance_results = {}
        
        # 对每个算法进行测试
        for i, algorithm in enumerate(algorithms):
            print(f"\n测试算法 {i+1}/{len(algorithms)}: {algorithm['name']}")
            
            try:
                # 执行算法并测量性能
                start_time = time.time()
                
                # 性能分析
                perf_result = self.performance_analyzer.profile_segmentation_algorithm(
                    algorithm['func'],
                    test_image,
                    algorithm['name'],
                    algorithm.get('params', {})
                )
                
                if perf_result['success']:
                    segmentation_result = perf_result['result']
                    
                    # 提取标签图
                    if isinstance(segmentation_result, dict):
                        if 'label_map' in segmentation_result:
                            label_map = segmentation_result['label_map']
                        elif 'segmentation_result' in segmentation_result:
                            label_map = segmentation_result['segmentation_result'].label_map
                        else:
                            label_map = segmentation_result
                    else:
                        label_map = segmentation_result
                    
                    # 计算评估指标
                    metrics = self.metrics_calculator.compute_all_metrics(
                        test_image, label_map, ground_truth
                    )
                    
                    algorithm_results[algorithm['name']] = {
                        'label_map': label_map,
                        'metrics': metrics,
                        'segmentation_result': segmentation_result,
                        'success': True
                    }
                    
                    performance_results[algorithm['name']] = perf_result
                    
                    print(f"  ✅ 成功 - 执行时间: {perf_result['execution_time']:.3f}s")
                    
                else:
                    print(f"  ❌ 失败: {perf_result.get('error_message', '未知错误')}")
                    algorithm_results[algorithm['name']] = {
                        'success': False,
                        'error': perf_result.get('error_message', '未知错误')
                    }
                    
            except Exception as e:
                print(f"  ❌ 异常: {str(e)}")
                algorithm_results[algorithm['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        # 生成比较结果
        comparison_result = {
            'test_image': test_image,
            'ground_truth': ground_truth,
            'algorithm_results': algorithm_results,
            'performance_results': performance_results,
            'comparison_summary': self._generate_comparison_summary(
                algorithm_results, performance_results
            ),
            'timestamp': time.time()
        }
        
        # 保存结果
        if save_results:
            self._save_comparison_results(comparison_result, output_dir)
        
        self.comparison_results.append(comparison_result)
        
        return comparison_result
    
    def visualize_comparison(self,
                           comparison_result: Dict[str, Any],
                           show_metrics: bool = True,
                           show_performance: bool = True,
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        可视化算法比较结果
        
        Args:
            comparison_result: 比较结果
            show_metrics: 是否显示评估指标
            show_performance: 是否显示性能指标
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        algorithm_results = comparison_result['algorithm_results']
        performance_results = comparison_result['performance_results']
        test_image = comparison_result['test_image']
        
        # 过滤成功的结果
        successful_algorithms = [
            name for name, result in algorithm_results.items() 
            if result.get('success', False)
        ]
        
        if not successful_algorithms:
            print("没有成功的算法结果可以可视化")
            return None
        
        # 计算布局
        num_algorithms = len(successful_algorithms)
        num_rows = 2 + (1 if show_metrics else 0) + (1 if show_performance else 0)
        
        # 创建图形
        fig = plt.figure(figsize=(4 * num_algorithms, 4 * num_rows))
        gs = GridSpec(num_rows, num_algorithms, figure=fig)
        
        # 第一行：原始图像
        for i in range(num_algorithms):
            ax = fig.add_subplot(gs[0, i])
            if i == 0:
                ax.imshow(test_image)
                ax.set_title("原始图像")
            else:
                ax.axis('off')
            ax.set_xticks([])
            ax.set_yticks([])
        
        # 第二行：分割结果
        for i, alg_name in enumerate(successful_algorithms):
            ax = fig.add_subplot(gs[1, i])
            label_map = algorithm_results[alg_name]['label_map']
            
            # 创建彩色分割图
            colored_segmentation = self._create_colored_segmentation(label_map)
            ax.imshow(colored_segmentation)
            ax.set_title(f"{alg_name}\n分割结果")
            ax.set_xticks([])
            ax.set_yticks([])
        
        current_row = 2
        
        # 评估指标对比
        if show_metrics:
            ax = fig.add_subplot(gs[current_row, :])
            self._plot_metrics_comparison(ax, algorithm_results, successful_algorithms)
            current_row += 1
        
        # 性能指标对比
        if show_performance:
            ax = fig.add_subplot(gs[current_row, :])
            self._plot_performance_comparison(ax, performance_results, successful_algorithms)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _create_colored_segmentation(self, label_map: np.ndarray) -> np.ndarray:
        """创建彩色分割图"""
        # 获取唯一标签
        unique_labels = np.unique(label_map)
        num_labels = len(unique_labels)
        
        # 创建颜色映射
        colors = plt.cm.tab20(np.linspace(0, 1, num_labels))
        
        # 创建彩色图像
        colored = np.zeros((*label_map.shape, 3))
        for i, label in enumerate(unique_labels):
            mask = label_map == label
            colored[mask] = colors[i][:3]
        
        return colored
    
    def _plot_metrics_comparison(self, 
                               ax: plt.Axes, 
                               algorithm_results: Dict, 
                               algorithm_names: List[str]):
        """绘制评估指标对比"""
        # 收集指标数据
        metrics_data = []
        for alg_name in algorithm_names:
            metrics = algorithm_results[alg_name]['metrics']
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    metrics_data.append({
                        'Algorithm': alg_name,
                        'Metric': metric_name,
                        'Value': value
                    })
        
        if not metrics_data:
            ax.text(0.5, 0.5, '没有可用的评估指标', 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # 创建DataFrame
        df = pd.DataFrame(metrics_data)
        
        # 选择主要指标进行显示
        main_metrics = [
            'intra_region_variance', 'inter_region_contrast', 
            'boundary_recall', 'region_compactness'
        ]
        
        available_metrics = [m for m in main_metrics if m in df['Metric'].values]
        if available_metrics:
            df_filtered = df[df['Metric'].isin(available_metrics)]
            
            # 创建分组柱状图
            metric_names = df_filtered['Metric'].unique()
            x = np.arange(len(metric_names))
            width = 0.8 / len(algorithm_names)
            
            for i, alg_name in enumerate(algorithm_names):
                alg_data = df_filtered[df_filtered['Algorithm'] == alg_name]
                values = [alg_data[alg_data['Metric'] == m]['Value'].iloc[0] 
                         if len(alg_data[alg_data['Metric'] == m]) > 0 else 0 
                         for m in metric_names]
                
                ax.bar(x + i * width, values, width, label=alg_name)
            
            ax.set_xlabel('评估指标')
            ax.set_ylabel('指标值')
            ax.set_title('算法评估指标对比')
            ax.set_xticks(x + width * (len(algorithm_names) - 1) / 2)
            ax.set_xticklabels(metric_names, rotation=45)
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    def _plot_performance_comparison(self, 
                                   ax: plt.Axes, 
                                   performance_results: Dict, 
                                   algorithm_names: List[str]):
        """绘制性能指标对比"""
        # 收集性能数据
        exec_times = []
        memory_usage = []
        
        for alg_name in algorithm_names:
            perf = performance_results[alg_name]
            exec_times.append(perf['execution_time'])
            memory_usage.append(perf['memory_used_mb'])
        
        # 创建双轴图
        ax2 = ax.twinx()
        
        x = np.arange(len(algorithm_names))
        width = 0.35
        
        # 执行时间
        bars1 = ax.bar(x - width/2, exec_times, width, label='执行时间 (秒)', 
                      color='skyblue', alpha=0.7)
        
        # 内存使用
        bars2 = ax2.bar(x + width/2, memory_usage, width, label='内存使用 (MB)', 
                       color='lightcoral', alpha=0.7)
        
        # 设置标签和标题
        ax.set_xlabel('算法')
        ax.set_ylabel('执行时间 (秒)', color='blue')
        ax2.set_ylabel('内存使用 (MB)', color='red')
        ax.set_title('算法性能对比')
        ax.set_xticks(x)
        ax.set_xticklabels(algorithm_names, rotation=45)
        
        # 添加数值标签
        for bar, value in zip(bars1, exec_times):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.3f}s', ha='center', va='bottom')
        
        for bar, value in zip(bars2, memory_usage):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.1f}MB', ha='center', va='bottom')
        
        ax.grid(True, alpha=0.3)
        
        # 图例
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    def _generate_comparison_summary(self,
                                   algorithm_results: Dict,
                                   performance_results: Dict) -> Dict[str, Any]:
        """生成比较摘要"""
        successful_algorithms = [
            name for name, result in algorithm_results.items()
            if result.get('success', False)
        ]

        if not successful_algorithms:
            return {
                'total_algorithms': len(algorithm_results),
                'successful_algorithms': 0,
                'failed_algorithms': len(algorithm_results)
            }

        # 性能统计
        exec_times = [performance_results[name]['execution_time']
                     for name in successful_algorithms]
        memory_usage = [performance_results[name]['memory_used_mb']
                       for name in successful_algorithms]

        # 找出最佳算法
        fastest_idx = np.argmin(exec_times)
        most_memory_efficient_idx = np.argmin(memory_usage)

        summary = {
            'total_algorithms': len(algorithm_results),
            'successful_algorithms': len(successful_algorithms),
            'failed_algorithms': len(algorithm_results) - len(successful_algorithms),
            'fastest_algorithm': {
                'name': successful_algorithms[fastest_idx],
                'execution_time': exec_times[fastest_idx]
            },
            'most_memory_efficient': {
                'name': successful_algorithms[most_memory_efficient_idx],
                'memory_usage': memory_usage[most_memory_efficient_idx]
            },
            'average_execution_time': np.mean(exec_times),
            'average_memory_usage': np.mean(memory_usage)
        }

        # 如果有评估指标，找出质量最佳的算法
        quality_scores = []
        for name in successful_algorithms:
            metrics = algorithm_results[name]['metrics']
            # 简单的质量分数计算（可以根据需要调整）
            score = 0
            if 'inter_region_contrast' in metrics:
                score += metrics['inter_region_contrast'] * 0.3
            if 'boundary_recall' in metrics:
                score += metrics['boundary_recall'] * 0.3
            if 'region_compactness' in metrics:
                score += metrics['region_compactness'] * 0.2
            if 'segmentation_consistency' in metrics:
                score += metrics['segmentation_consistency'] * 0.2

            quality_scores.append(score)

        if quality_scores:
            best_quality_idx = np.argmax(quality_scores)
            summary['best_quality_algorithm'] = {
                'name': successful_algorithms[best_quality_idx],
                'quality_score': quality_scores[best_quality_idx]
            }

        return summary

    def _save_comparison_results(self,
                               comparison_result: Dict[str, Any],
                               output_dir: str):
        """保存比较结果"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # 保存可视化结果
        fig = self.visualize_comparison(comparison_result, save_path=None)
        if fig:
            fig.savefig(output_path / f"comparison_{timestamp}.png",
                       dpi=300, bbox_inches='tight')
            plt.close(fig)

        # 保存详细报告
        self._generate_detailed_report(comparison_result, output_path, timestamp)

        print(f"比较结果已保存到: {output_path}")

    def _generate_detailed_report(self,
                                comparison_result: Dict[str, Any],
                                output_path: Path,
                                timestamp: str):
        """生成详细报告"""
        report_path = output_path / f"detailed_report_{timestamp}.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("算法比较详细报告\n")
            f.write("=" * 60 + "\n\n")

            # 基本信息
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试图像尺寸: {comparison_result['test_image'].shape}\n\n")

            # 比较摘要
            summary = comparison_result['comparison_summary']
            f.write("比较摘要:\n")
            f.write("-" * 30 + "\n")
            f.write(f"总算法数: {summary['total_algorithms']}\n")
            f.write(f"成功算法数: {summary['successful_algorithms']}\n")
            f.write(f"失败算法数: {summary['failed_algorithms']}\n\n")

            if summary['successful_algorithms'] > 0:
                f.write(f"最快算法: {summary['fastest_algorithm']['name']} ")
                f.write(f"({summary['fastest_algorithm']['execution_time']:.3f}s)\n")

                f.write(f"最省内存算法: {summary['most_memory_efficient']['name']} ")
                f.write(f"({summary['most_memory_efficient']['memory_usage']:.1f}MB)\n")

                if 'best_quality_algorithm' in summary:
                    f.write(f"最佳质量算法: {summary['best_quality_algorithm']['name']} ")
                    f.write(f"(质量分数: {summary['best_quality_algorithm']['quality_score']:.3f})\n")

                f.write(f"\n平均执行时间: {summary['average_execution_time']:.3f}s\n")
                f.write(f"平均内存使用: {summary['average_memory_usage']:.1f}MB\n\n")

            # 详细结果
            f.write("详细结果:\n")
            f.write("-" * 30 + "\n")

            for alg_name, result in comparison_result['algorithm_results'].items():
                f.write(f"\n算法: {alg_name}\n")

                if result.get('success', False):
                    f.write("状态: 成功\n")

                    # 性能指标
                    if alg_name in comparison_result['performance_results']:
                        perf = comparison_result['performance_results'][alg_name]
                        f.write(f"执行时间: {perf['execution_time']:.3f}s\n")
                        f.write(f"内存使用: {perf['memory_used_mb']:.1f}MB\n")
                        f.write(f"处理速度: {perf.get('pixels_per_second', 0):.0f} 像素/秒\n")

                    # 评估指标
                    metrics = result['metrics']
                    f.write("评估指标:\n")
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            f.write(f"  {metric_name}: {value:.4f}\n")

                else:
                    f.write("状态: 失败\n")
                    f.write(f"错误: {result.get('error', '未知错误')}\n")

        print(f"详细报告已保存到: {report_path}")

    def create_side_by_side_comparison(self,
                                     algorithm_results: Dict[str, Any],
                                     test_image: np.ndarray,
                                     algorithm_names: List[str],
                                     save_path: Optional[str] = None) -> plt.Figure:
        """
        创建并排对比图

        Args:
            algorithm_results: 算法结果字典
            test_image: 测试图像
            algorithm_names: 要比较的算法名称列表
            save_path: 保存路径

        Returns:
            matplotlib图形对象
        """
        num_algorithms = len(algorithm_names)
        fig, axes = plt.subplots(2, num_algorithms + 1,
                                figsize=(4 * (num_algorithms + 1), 8))

        # 第一行第一列：原始图像
        axes[0, 0].imshow(test_image)
        axes[0, 0].set_title("原始图像")
        axes[0, 0].set_xticks([])
        axes[0, 0].set_yticks([])

        # 第二行第一列：空白或图例
        axes[1, 0].axis('off')

        # 显示各算法结果
        for i, alg_name in enumerate(algorithm_names):
            col_idx = i + 1

            if (alg_name in algorithm_results and
                algorithm_results[alg_name].get('success', False)):

                label_map = algorithm_results[alg_name]['label_map']

                # 第一行：分割结果
                colored_seg = self._create_colored_segmentation(label_map)
                axes[0, col_idx].imshow(colored_seg)
                axes[0, col_idx].set_title(f"{alg_name}")
                axes[0, col_idx].set_xticks([])
                axes[0, col_idx].set_yticks([])

                # 第二行：边界叠加
                boundary_overlay = self._create_boundary_overlay(test_image, label_map)
                axes[1, col_idx].imshow(boundary_overlay)
                axes[1, col_idx].set_title(f"{alg_name} - 边界")
                axes[1, col_idx].set_xticks([])
                axes[1, col_idx].set_yticks([])

            else:
                # 显示错误信息
                axes[0, col_idx].text(0.5, 0.5, f"{alg_name}\n失败",
                                     ha='center', va='center',
                                     transform=axes[0, col_idx].transAxes)
                axes[0, col_idx].set_xticks([])
                axes[0, col_idx].set_yticks([])

                axes[1, col_idx].axis('off')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def _create_boundary_overlay(self,
                               original_image: np.ndarray,
                               label_map: np.ndarray) -> np.ndarray:
        """创建边界叠加图像"""
        # 计算边界
        grad_x = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        boundaries = np.sqrt(grad_x**2 + grad_y**2) > 0

        # 创建叠加图像
        overlay = original_image.copy()
        if len(overlay.shape) == 2:
            overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2RGB)

        # 在边界处添加红色
        overlay[boundaries] = [255, 0, 0]

        return overlay
