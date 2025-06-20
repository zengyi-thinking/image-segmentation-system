"""
性能分析器
分析算法的运行时间、内存使用等性能指标
"""

import time
import psutil
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Callable, Any, Optional
import pandas as pd
from pathlib import Path
import json


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.results = []
        self.current_session = None
        
    def profile_function(self, 
                        func: Callable,
                        *args,
                        **kwargs) -> Dict[str, Any]:
        """
        分析函数性能
        
        Args:
            func: 要分析的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            性能分析结果
        """
        # 记录开始状态
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        
        # 执行函数
        try:
            result = func(*args, **kwargs)
            success = True
            error_msg = None
        except Exception as e:
            result = None
            success = False
            error_msg = str(e)
        
        # 记录结束状态
        end_time = time.time()
        end_memory = self._get_memory_usage()
        end_cpu = psutil.cpu_percent()
        
        # 计算性能指标
        performance_data = {
            'execution_time': end_time - start_time,
            'memory_used_mb': end_memory - start_memory,
            'peak_memory_mb': end_memory,
            'cpu_usage_start': start_cpu,
            'cpu_usage_end': end_cpu,
            'success': success,
            'error_message': error_msg,
            'result': result,
            'timestamp': time.time()
        }
        
        return performance_data
    
    def profile_segmentation_algorithm(self,
                                     algorithm_func: Callable,
                                     image: np.ndarray,
                                     algorithm_name: str,
                                     parameters: Dict = None) -> Dict[str, Any]:
        """
        分析分割算法性能
        
        Args:
            algorithm_func: 分割算法函数
            image: 输入图像
            algorithm_name: 算法名称
            parameters: 算法参数
            
        Returns:
            详细的性能分析结果
        """
        parameters = parameters or {}
        
        # 记录图像信息
        image_info = {
            'height': image.shape[0],
            'width': image.shape[1],
            'channels': image.shape[2] if len(image.shape) == 3 else 1,
            'total_pixels': image.size,
            'dtype': str(image.dtype)
        }
        
        # 执行性能分析
        performance_data = self.profile_function(algorithm_func, image, **parameters)
        
        # 添加算法特定信息
        performance_data.update({
            'algorithm_name': algorithm_name,
            'parameters': parameters,
            'image_info': image_info
        })
        
        # 计算额外的性能指标
        if performance_data['success'] and performance_data['result'] is not None:
            result = performance_data['result']
            if isinstance(result, dict) and 'statistics' in result:
                stats = result['statistics']
                performance_data['segments_count'] = stats.get('num_segments', 0)
                performance_data['avg_segment_size'] = stats.get('avg_segment_size', 0)
                
                # 计算处理速度
                pixels_per_second = image.size / performance_data['execution_time']
                performance_data['pixels_per_second'] = pixels_per_second
        
        # 保存结果
        self.results.append(performance_data)
        
        return performance_data
    
    def compare_algorithms(self,
                          algorithms: List[Dict],
                          test_images: List[np.ndarray],
                          image_names: List[str] = None) -> pd.DataFrame:
        """
        比较多个算法的性能
        
        Args:
            algorithms: 算法列表，每个元素包含 {'name': str, 'func': callable, 'params': dict}
            test_images: 测试图像列表
            image_names: 图像名称列表
            
        Returns:
            比较结果DataFrame
        """
        if image_names is None:
            image_names = [f"Image_{i+1}" for i in range(len(test_images))]
        
        comparison_results = []
        
        for img_idx, (image, img_name) in enumerate(zip(test_images, image_names)):
            print(f"测试图像 {img_name} ({image.shape})...")
            
            for alg_idx, algorithm in enumerate(algorithms):
                print(f"  运行算法: {algorithm['name']}")
                
                # 执行性能分析
                result = self.profile_segmentation_algorithm(
                    algorithm['func'],
                    image,
                    algorithm['name'],
                    algorithm.get('params', {})
                )
                
                # 整理结果
                row = {
                    'image_name': img_name,
                    'algorithm': algorithm['name'],
                    'execution_time': result['execution_time'],
                    'memory_used_mb': result['memory_used_mb'],
                    'pixels_per_second': result.get('pixels_per_second', 0),
                    'segments_count': result.get('segments_count', 0),
                    'success': result['success'],
                    'image_pixels': result['image_info']['total_pixels']
                }
                
                comparison_results.append(row)
        
        return pd.DataFrame(comparison_results)
    
    def analyze_scalability(self,
                           algorithm_func: Callable,
                           base_image: np.ndarray,
                           scale_factors: List[float],
                           algorithm_name: str,
                           parameters: Dict = None) -> pd.DataFrame:
        """
        分析算法的可扩展性
        
        Args:
            algorithm_func: 算法函数
            base_image: 基础图像
            scale_factors: 缩放因子列表
            algorithm_name: 算法名称
            parameters: 算法参数
            
        Returns:
            可扩展性分析结果
        """
        scalability_results = []
        
        for scale in scale_factors:
            # 缩放图像
            new_height = int(base_image.shape[0] * scale)
            new_width = int(base_image.shape[1] * scale)
            
            import cv2
            scaled_image = cv2.resize(base_image, (new_width, new_height))
            
            print(f"测试缩放因子 {scale:.2f} (尺寸: {scaled_image.shape})")
            
            # 执行性能分析
            result = self.profile_segmentation_algorithm(
                algorithm_func,
                scaled_image,
                algorithm_name,
                parameters
            )
            
            # 记录结果
            row = {
                'scale_factor': scale,
                'image_size': scaled_image.size,
                'height': scaled_image.shape[0],
                'width': scaled_image.shape[1],
                'execution_time': result['execution_time'],
                'memory_used_mb': result['memory_used_mb'],
                'pixels_per_second': result.get('pixels_per_second', 0),
                'segments_count': result.get('segments_count', 0),
                'success': result['success']
            }
            
            scalability_results.append(row)
        
        return pd.DataFrame(scalability_results)
    
    def generate_performance_report(self, 
                                  output_dir: str = "performance_reports") -> str:
        """
        生成性能分析报告
        
        Args:
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 创建报告
        report = {
            'summary': self._generate_summary(),
            'detailed_results': self.results,
            'timestamp': time.time()
        }
        
        # 保存JSON报告
        json_path = output_path / "performance_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # 生成可视化图表
        self._generate_performance_charts(output_path)
        
        return str(json_path)
    
    def _generate_summary(self) -> Dict:
        """生成性能摘要"""
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r['success']]
        
        if not successful_results:
            return {'total_tests': len(self.results), 'successful_tests': 0}
        
        execution_times = [r['execution_time'] for r in successful_results]
        memory_usage = [r['memory_used_mb'] for r in successful_results]
        
        summary = {
            'total_tests': len(self.results),
            'successful_tests': len(successful_results),
            'avg_execution_time': np.mean(execution_times),
            'min_execution_time': np.min(execution_times),
            'max_execution_time': np.max(execution_times),
            'avg_memory_usage': np.mean(memory_usage),
            'max_memory_usage': np.max(memory_usage),
            'algorithms_tested': list(set(r.get('algorithm_name', 'Unknown') for r in self.results))
        }
        
        return summary
    
    def _generate_performance_charts(self, output_dir: Path):
        """生成性能图表"""
        if not self.results:
            return
        
        successful_results = [r for r in self.results if r['success']]
        
        if not successful_results:
            return
        
        # 执行时间图表
        plt.figure(figsize=(12, 8))
        
        # 子图1: 执行时间对比
        plt.subplot(2, 2, 1)
        algorithms = [r.get('algorithm_name', 'Unknown') for r in successful_results]
        exec_times = [r['execution_time'] for r in successful_results]
        
        plt.bar(range(len(algorithms)), exec_times)
        plt.xlabel('算法')
        plt.ylabel('执行时间 (秒)')
        plt.title('算法执行时间对比')
        plt.xticks(range(len(algorithms)), algorithms, rotation=45)
        
        # 子图2: 内存使用对比
        plt.subplot(2, 2, 2)
        memory_usage = [r['memory_used_mb'] for r in successful_results]
        
        plt.bar(range(len(algorithms)), memory_usage)
        plt.xlabel('算法')
        plt.ylabel('内存使用 (MB)')
        plt.title('算法内存使用对比')
        plt.xticks(range(len(algorithms)), algorithms, rotation=45)
        
        # 子图3: 处理速度对比
        plt.subplot(2, 2, 3)
        speeds = [r.get('pixels_per_second', 0) for r in successful_results]
        
        plt.bar(range(len(algorithms)), speeds)
        plt.xlabel('算法')
        plt.ylabel('像素/秒')
        plt.title('算法处理速度对比')
        plt.xticks(range(len(algorithms)), algorithms, rotation=45)
        
        # 子图4: 分割区域数量
        plt.subplot(2, 2, 4)
        segment_counts = [r.get('segments_count', 0) for r in successful_results]
        
        plt.bar(range(len(algorithms)), segment_counts)
        plt.xlabel('算法')
        plt.ylabel('分割区域数量')
        plt.title('分割区域数量对比')
        plt.xticks(range(len(algorithms)), algorithms, rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_dir / "performance_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_scalability_analysis(self, 
                                 scalability_df: pd.DataFrame,
                                 output_path: str = None) -> plt.Figure:
        """
        绘制可扩展性分析图表
        
        Args:
            scalability_df: 可扩展性分析结果
            output_path: 输出路径
            
        Returns:
            matplotlib图形对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 执行时间 vs 图像大小
        axes[0, 0].plot(scalability_df['image_size'], scalability_df['execution_time'], 'o-')
        axes[0, 0].set_xlabel('图像大小 (像素)')
        axes[0, 0].set_ylabel('执行时间 (秒)')
        axes[0, 0].set_title('执行时间 vs 图像大小')
        axes[0, 0].grid(True)
        
        # 内存使用 vs 图像大小
        axes[0, 1].plot(scalability_df['image_size'], scalability_df['memory_used_mb'], 'o-')
        axes[0, 1].set_xlabel('图像大小 (像素)')
        axes[0, 1].set_ylabel('内存使用 (MB)')
        axes[0, 1].set_title('内存使用 vs 图像大小')
        axes[0, 1].grid(True)
        
        # 处理速度 vs 图像大小
        axes[1, 0].plot(scalability_df['image_size'], scalability_df['pixels_per_second'], 'o-')
        axes[1, 0].set_xlabel('图像大小 (像素)')
        axes[1, 0].set_ylabel('处理速度 (像素/秒)')
        axes[1, 0].set_title('处理速度 vs 图像大小')
        axes[1, 0].grid(True)
        
        # 分割区域数量 vs 图像大小
        axes[1, 1].plot(scalability_df['image_size'], scalability_df['segments_count'], 'o-')
        axes[1, 1].set_xlabel('图像大小 (像素)')
        axes[1, 1].set_ylabel('分割区域数量')
        axes[1, 1].set_title('分割区域数量 vs 图像大小')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def clear_results(self):
        """清除分析结果"""
        self.results = []
    
    def export_results_csv(self, filename: str):
        """导出结果到CSV文件"""
        if not self.results:
            print("没有结果可导出")
            return
        
        # 展平结果数据
        flattened_results = []
        for result in self.results:
            row = {
                'algorithm_name': result.get('algorithm_name', ''),
                'execution_time': result['execution_time'],
                'memory_used_mb': result['memory_used_mb'],
                'success': result['success'],
                'timestamp': result['timestamp']
            }
            
            # 添加图像信息
            if 'image_info' in result:
                row.update({f"image_{k}": v for k, v in result['image_info'].items()})
            
            # 添加其他性能指标
            for key in ['pixels_per_second', 'segments_count']:
                if key in result:
                    row[key] = result[key]
            
            flattened_results.append(row)
        
        df = pd.DataFrame(flattened_results)
        df.to_csv(filename, index=False)
        print(f"结果已导出到: {filename}")
