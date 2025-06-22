"""
批处理系统
支持批量图像处理和结果导出
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from PIL import Image

from utils.logger import LoggerMixin
from utils.image_io import ImageLoader
from utils.exceptions import ImageLoadError, AlgorithmError
from utils.config_manager import get_config
from core.mst_segmentation import MSTSegmentation
from core.watershed_segmentation import WatershedSegmentation
from core.kmeans_segmentation import KMeansSegmentation, GMMSegmentation


class BatchProcessor(LoggerMixin):
    """批处理器"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.image_loader = ImageLoader()
        
        # 可用算法
        self.algorithms = {
            'MST': MSTSegmentation(),
            'Watershed': WatershedSegmentation(),
            'K-Means': KMeansSegmentation(),
            'GMM': GMMSegmentation()
        }
        
        # 处理状态
        self.is_processing = False
        self.current_progress = 0
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        
        # 回调函数
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        
        self.logger.info("批处理器初始化完成")
    
    def process_directory(self, 
                         input_dir: Union[str, Path],
                         output_dir: Union[str, Path],
                         algorithm: str,
                         parameters: Dict[str, Any],
                         file_patterns: List[str] = None,
                         recursive: bool = False,
                         max_workers: int = None,
                         save_format: str = 'png',
                         save_original: bool = False,
                         save_report: bool = True) -> Dict[str, Any]:
        """
        批量处理目录中的图像
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            algorithm: 算法名称
            parameters: 算法参数
            file_patterns: 文件模式列表
            recursive: 是否递归处理子目录
            max_workers: 最大工作线程数
            save_format: 保存格式
            save_original: 是否保存原图
            save_report: 是否生成报告
            
        Returns:
            处理结果统计
        """
        try:
            self.is_processing = True
            start_time = time.time()
            
            # 参数验证
            input_dir = Path(input_dir)
            output_dir = Path(output_dir)
            
            if not input_dir.exists():
                raise ValueError(f"输入目录不存在: {input_dir}")
            
            if algorithm not in self.algorithms:
                raise ValueError(f"不支持的算法: {algorithm}")
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 查找图像文件
            image_files = self._find_image_files(input_dir, file_patterns, recursive)
            self.total_files = len(image_files)
            
            if self.total_files == 0:
                self.logger.warning("未找到图像文件")
                return self._create_result_summary(start_time, [])
            
            self.logger.info(f"找到 {self.total_files} 个图像文件")
            
            # 设置线程数
            if max_workers is None:
                max_workers = min(self.config.performance.max_threads, self.total_files)
            
            # 批量处理
            results = self._process_files_parallel(
                image_files, output_dir, algorithm, parameters,
                max_workers, save_format, save_original
            )
            
            # 生成报告
            if save_report:
                self._generate_report(results, output_dir, algorithm, parameters)
            
            # 处理完成
            total_time = time.time() - start_time
            summary = self._create_result_summary(start_time, results)
            
            self.logger.info(f"批处理完成 - 总时间: {total_time:.2f}s, "
                           f"成功: {self.processed_files}, 失败: {self.failed_files}")
            
            if self.completion_callback:
                self.completion_callback(summary)
            
            return summary
            
        except Exception as e:
            self.logger.error("批处理失败", exception=e)
            if self.error_callback:
                self.error_callback(str(e))
            raise
        finally:
            self.is_processing = False
    
    def _find_image_files(self, input_dir: Path, patterns: List[str], 
                         recursive: bool) -> List[Path]:
        """查找图像文件"""
        if patterns is None:
            patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
        
        image_files = []
        
        if recursive:
            for pattern in patterns:
                image_files.extend(input_dir.rglob(pattern))
        else:
            for pattern in patterns:
                image_files.extend(input_dir.glob(pattern))
        
        # 去重并排序
        image_files = sorted(list(set(image_files)))
        
        return image_files
    
    def _process_files_parallel(self, image_files: List[Path], output_dir: Path,
                              algorithm: str, parameters: Dict[str, Any],
                              max_workers: int, save_format: str,
                              save_original: bool) -> List[Dict[str, Any]]:
        """并行处理文件"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_file = {
                executor.submit(
                    self._process_single_file,
                    file_path, output_dir, algorithm, parameters,
                    save_format, save_original
                ): file_path
                for file_path in image_files
            }
            
            # 收集结果
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        self.processed_files += 1
                    else:
                        self.failed_files += 1
                    
                except Exception as e:
                    self.logger.error(f"处理文件失败: {file_path}", exception=e)
                    results.append({
                        'file_path': str(file_path),
                        'success': False,
                        'error': str(e),
                        'execution_time': 0
                    })
                    self.failed_files += 1
                
                # 更新进度
                self.current_progress = len(results)
                if self.progress_callback:
                    self.progress_callback(self.current_progress, self.total_files)
        
        return results
    
    def _process_single_file(self, file_path: Path, output_dir: Path,
                           algorithm: str, parameters: Dict[str, Any],
                           save_format: str, save_original: bool) -> Dict[str, Any]:
        """处理单个文件"""
        start_time = time.time()
        
        try:
            # 加载图像
            image = self.image_loader.load_image(file_path)
            
            # 执行分割
            algorithm_instance = self.algorithms[algorithm]
            result = algorithm_instance.segment(image, **parameters)
            
            # 保存结果
            output_paths = self._save_results(
                file_path, output_dir, image, result['segmented_image'],
                save_format, save_original
            )
            
            execution_time = time.time() - start_time
            
            return {
                'file_path': str(file_path),
                'success': True,
                'algorithm': algorithm,
                'parameters': parameters,
                'num_segments': result['num_segments'],
                'execution_time': execution_time,
                'output_paths': output_paths
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'file_path': str(file_path),
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
    
    def _save_results(self, input_path: Path, output_dir: Path,
                     original_image: np.ndarray, segmented_image: np.ndarray,
                     save_format: str, save_original: bool) -> Dict[str, str]:
        """保存处理结果"""
        output_paths = {}
        
        # 生成输出文件名
        base_name = input_path.stem
        
        # 保存分割结果
        segmented_path = output_dir / f"{base_name}_segmented.{save_format}"
        Image.fromarray(segmented_image).save(segmented_path)
        output_paths['segmented'] = str(segmented_path)
        
        # 保存原图（可选）
        if save_original:
            original_path = output_dir / f"{base_name}_original.{save_format}"
            Image.fromarray(original_image).save(original_path)
            output_paths['original'] = str(original_path)
        
        # 保存对比图
        comparison_image = self._create_comparison_image(original_image, segmented_image)
        comparison_path = output_dir / f"{base_name}_comparison.{save_format}"
        Image.fromarray(comparison_image).save(comparison_path)
        output_paths['comparison'] = str(comparison_path)
        
        return output_paths
    
    def _create_comparison_image(self, original: np.ndarray, 
                               segmented: np.ndarray) -> np.ndarray:
        """创建对比图像"""
        h, w = original.shape[:2]
        
        # 创建并排对比图
        comparison = np.zeros((h, w * 2, 3), dtype=np.uint8)
        comparison[:, :w] = original
        comparison[:, w:] = segmented
        
        return comparison
    
    def _generate_report(self, results: List[Dict[str, Any]], output_dir: Path,
                        algorithm: str, parameters: Dict[str, Any]):
        """生成处理报告"""
        # JSON报告
        report_data = {
            'summary': {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'failed_files': self.failed_files,
                'success_rate': self.processed_files / self.total_files if self.total_files > 0 else 0,
                'algorithm': algorithm,
                'parameters': parameters
            },
            'results': results
        }
        
        json_path = output_dir / "batch_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # CSV报告
        csv_path = output_dir / "batch_report.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题
            writer.writerow([
                'File Path', 'Success', 'Algorithm', 'Segments', 
                'Execution Time', 'Error'
            ])
            
            # 写入数据
            for result in results:
                writer.writerow([
                    result['file_path'],
                    result['success'],
                    result.get('algorithm', ''),
                    result.get('num_segments', ''),
                    f"{result['execution_time']:.3f}",
                    result.get('error', '')
                ])
        
        self.logger.info(f"报告已生成: {json_path}, {csv_path}")
    
    def _create_result_summary(self, start_time: float, 
                             results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建结果摘要"""
        total_time = time.time() - start_time
        
        # 计算统计信息
        successful_results = [r for r in results if r['success']]
        
        avg_execution_time = 0
        if successful_results:
            avg_execution_time = np.mean([r['execution_time'] for r in successful_results])
        
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'success_rate': self.processed_files / self.total_files if self.total_files > 0 else 0,
            'total_time': total_time,
            'average_execution_time': avg_execution_time,
            'throughput': self.processed_files / total_time if total_time > 0 else 0
        }
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度回调"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置完成回调"""
        self.completion_callback = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """设置错误回调"""
        self.error_callback = callback
    
    def cancel_processing(self):
        """取消处理"""
        self.is_processing = False
        self.logger.info("批处理已取消")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return {
            'is_processing': self.is_processing,
            'current_progress': self.current_progress,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'progress_percentage': (self.current_progress / self.total_files * 100) 
                                 if self.total_files > 0 else 0
        }


def create_batch_config(algorithm: str, parameters: Dict[str, Any],
                       input_dir: str, output_dir: str,
                       **options) -> Dict[str, Any]:
    """创建批处理配置"""
    config = {
        'algorithm': algorithm,
        'parameters': parameters,
        'input_dir': input_dir,
        'output_dir': output_dir,
        'file_patterns': options.get('file_patterns', ['*.jpg', '*.png']),
        'recursive': options.get('recursive', False),
        'max_workers': options.get('max_workers', 4),
        'save_format': options.get('save_format', 'png'),
        'save_original': options.get('save_original', False),
        'save_report': options.get('save_report', True)
    }
    
    return config


def save_batch_config(config: Dict[str, Any], file_path: Union[str, Path]):
    """保存批处理配置"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_batch_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载批处理配置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
