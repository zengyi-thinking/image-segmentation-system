"""
性能监控和内存管理系统
提供实时性能监控、内存使用跟踪和优化建议
"""

import psutil
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from collections import deque
import gc
import numpy as np

from utils.logger import LoggerMixin
from utils.config_manager import get_config


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    gpu_memory_mb: float = 0.0
    gpu_utilization: float = 0.0


@dataclass
class AlgorithmPerformance:
    """算法性能数据"""
    algorithm_name: str
    execution_time: float
    memory_peak_mb: float
    memory_start_mb: float
    memory_end_mb: float
    cpu_usage_avg: float
    image_size: tuple
    parameters: Dict[str, Any]
    success: bool
    error_message: str = ""


class MemoryManager(LoggerMixin):
    """内存管理器"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.max_memory_mb = self.config.performance.max_memory_usage_mb
        self.cache_size_mb = self.config.performance.cache_size_mb
        
        # 内存缓存
        self._image_cache = {}
        self._cache_usage_mb = 0
        self._cache_access_times = {}
        
        self.logger.info(f"内存管理器初始化 - 最大内存: {self.max_memory_mb}MB, 缓存大小: {self.cache_size_mb}MB")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'used_mb': memory_info.rss / 1024 / 1024,
            'virtual_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'cache_mb': self._cache_usage_mb
        }
    
    def check_memory_limit(self) -> bool:
        """检查是否超过内存限制"""
        current_usage = self.get_memory_usage()
        
        if current_usage['used_mb'] > self.max_memory_mb:
            self.logger.warning(f"内存使用超限: {current_usage['used_mb']:.1f}MB > {self.max_memory_mb}MB")
            return False
        
        return True
    
    def cleanup_memory(self):
        """清理内存"""
        # 清理图像缓存
        self.clear_cache()
        
        # 强制垃圾回收
        collected = gc.collect()
        
        self.logger.info(f"内存清理完成 - 回收对象: {collected}")
    
    def cache_image(self, key: str, image: np.ndarray) -> bool:
        """缓存图像"""
        if not isinstance(image, np.ndarray):
            return False
        
        # 计算图像大小
        image_size_mb = image.nbytes / 1024 / 1024
        
        # 检查缓存空间
        if self._cache_usage_mb + image_size_mb > self.cache_size_mb:
            self._evict_cache(image_size_mb)
        
        # 添加到缓存
        self._image_cache[key] = image.copy()
        self._cache_usage_mb += image_size_mb
        self._cache_access_times[key] = time.time()
        
        self.logger.debug(f"图像已缓存: {key} ({image_size_mb:.1f}MB)")
        return True
    
    def get_cached_image(self, key: str) -> Optional[np.ndarray]:
        """获取缓存的图像"""
        if key in self._image_cache:
            self._cache_access_times[key] = time.time()
            self.logger.debug(f"缓存命中: {key}")
            return self._image_cache[key].copy()
        
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self._image_cache.clear()
        self._cache_usage_mb = 0
        self._cache_access_times.clear()
        self.logger.info("图像缓存已清空")
    
    def _evict_cache(self, needed_mb: float):
        """缓存淘汰策略 (LRU)"""
        # 按访问时间排序
        sorted_items = sorted(self._cache_access_times.items(), key=lambda x: x[1])
        
        freed_mb = 0
        for key, _ in sorted_items:
            if freed_mb >= needed_mb:
                break
            
            if key in self._image_cache:
                image = self._image_cache[key]
                image_size_mb = image.nbytes / 1024 / 1024
                
                del self._image_cache[key]
                del self._cache_access_times[key]
                
                freed_mb += image_size_mb
                self._cache_usage_mb -= image_size_mb
                
                self.logger.debug(f"缓存淘汰: {key} ({image_size_mb:.1f}MB)")


class PerformanceMonitor(LoggerMixin):
    """性能监控器"""
    
    def __init__(self, history_size: int = 1000):
        super().__init__()
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.algorithm_history = deque(maxlen=100)
        
        self._monitoring = False
        self._monitor_thread = None
        self._monitor_interval = 1.0  # 秒
        
        # 性能阈值
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        
        # 回调函数
        self.alert_callbacks = []
        
        self.logger.info("性能监控器初始化完成")
    
    def start_monitoring(self, interval: float = 1.0):
        """开始性能监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_interval = interval
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info(f"性能监控已启动 - 间隔: {interval}s")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        self.logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        
        while self._monitoring:
            try:
                # 收集性能指标
                metrics = self._collect_metrics(last_disk_io, last_network_io)
                self.metrics_history.append(metrics)
                
                # 检查阈值
                self._check_thresholds(metrics)
                
                # 更新IO计数器
                last_disk_io = psutil.disk_io_counters()
                last_network_io = psutil.net_io_counters()
                
                time.sleep(self._monitor_interval)
                
            except Exception as e:
                self.logger.error("性能监控循环错误", exception=e)
                time.sleep(self._monitor_interval)
    
    def _collect_metrics(self, last_disk_io, last_network_io) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU和内存
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # 磁盘IO
        current_disk_io = psutil.disk_io_counters()
        disk_read_mb = 0
        disk_write_mb = 0
        
        if last_disk_io and current_disk_io:
            disk_read_mb = (current_disk_io.read_bytes - last_disk_io.read_bytes) / 1024 / 1024
            disk_write_mb = (current_disk_io.write_bytes - last_disk_io.write_bytes) / 1024 / 1024
        
        # 网络IO
        current_network_io = psutil.net_io_counters()
        network_sent_mb = 0
        network_recv_mb = 0
        
        if last_network_io and current_network_io:
            network_sent_mb = (current_network_io.bytes_sent - last_network_io.bytes_sent) / 1024 / 1024
            network_recv_mb = (current_network_io.bytes_recv - last_network_io.bytes_recv) / 1024 / 1024
        
        # GPU信息（如果可用）
        gpu_memory_mb = 0
        gpu_utilization = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_memory_mb = gpu.memoryUsed
                gpu_utilization = gpu.load * 100
        except ImportError:
            pass
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization=gpu_utilization
        )
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        alerts = []
        
        if metrics.cpu_percent > self.cpu_threshold:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.memory_threshold:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")
        
        if metrics.memory_available_mb < 500:
            alerts.append(f"可用内存不足: {metrics.memory_available_mb:.1f}MB")
        
        # 触发警报回调
        for alert in alerts:
            self.logger.warning(f"性能警报: {alert}")
            for callback in self.alert_callbacks:
                try:
                    callback(alert, metrics)
                except Exception as e:
                    self.logger.error("警报回调执行失败", exception=e)
    
    def record_algorithm_performance(self, performance: AlgorithmPerformance):
        """记录算法性能"""
        self.algorithm_history.append(performance)
        
        self.logger.log_algorithm_result(
            performance.algorithm_name,
            0,  # segments count not available here
            performance.execution_time,
            performance.success
        )
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, duration_minutes: int = 10) -> List[PerformanceMetrics]:
        """获取指定时间段的性能历史"""
        if not self.metrics_history:
            return []
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_algorithm_statistics(self) -> Dict[str, Any]:
        """获取算法性能统计"""
        if not self.algorithm_history:
            return {}
        
        stats = {}
        algorithms = set(p.algorithm_name for p in self.algorithm_history)
        
        for algorithm in algorithms:
            performances = [p for p in self.algorithm_history if p.algorithm_name == algorithm]
            
            execution_times = [p.execution_time for p in performances if p.success]
            memory_peaks = [p.memory_peak_mb for p in performances if p.success]
            
            if execution_times:
                stats[algorithm] = {
                    'count': len(performances),
                    'success_rate': sum(1 for p in performances if p.success) / len(performances),
                    'avg_execution_time': np.mean(execution_times),
                    'min_execution_time': np.min(execution_times),
                    'max_execution_time': np.max(execution_times),
                    'avg_memory_peak': np.mean(memory_peaks) if memory_peaks else 0,
                    'max_memory_peak': np.max(memory_peaks) if memory_peaks else 0
                }
        
        return stats
    
    def add_alert_callback(self, callback: Callable[[str, PerformanceMetrics], None]):
        """添加警报回调函数"""
        self.alert_callbacks.append(callback)
    
    def export_metrics(self, file_path: str):
        """导出性能指标到文件"""
        try:
            import json
            
            data = {
                'metrics_history': [asdict(m) for m in self.metrics_history],
                'algorithm_history': [asdict(p) for p in self.algorithm_history],
                'export_time': time.time()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"性能指标已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出性能指标失败: {file_path}", exception=e)


# 全局实例
_global_memory_manager = None
_global_performance_monitor = None

def get_memory_manager() -> MemoryManager:
    """获取全局内存管理器"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor
