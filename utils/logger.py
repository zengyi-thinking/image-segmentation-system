"""
日志系统模块
提供统一的日志记录功能，支持不同级别的日志输出和文件记录
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback


class ImageSegmentationLogger:
    """图像分割系统日志管理器"""
    
    def __init__(self, name: str = "ImageSegmentation", log_dir: str = "logs"):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
            log_dir: 日志文件目录
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 所有日志
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误文件处理器 - 只记录错误
        error_file = self.log_dir / f"{self.name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录一般信息"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告信息"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录错误信息"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.error(message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录严重错误"""
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.critical(message, **kwargs)
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """记录函数调用"""
        kwargs = kwargs or {}
        self.debug(f"调用函数 {func_name}, args={args}, kwargs={kwargs}")
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """记录性能指标"""
        message = f"性能统计 - {operation}: 耗时 {duration:.3f}s"
        if metrics:
            metric_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
            message += f", {metric_str}"
        self.info(message)
    
    def log_image_info(self, image_path: str, width: int, height: int, channels: int):
        """记录图像信息"""
        self.info(f"图像加载 - 路径: {image_path}, 尺寸: {width}x{height}, 通道: {channels}")
    
    def log_algorithm_result(self, algorithm: str, segments: int, duration: float, success: bool):
        """记录算法执行结果"""
        status = "成功" if success else "失败"
        self.info(f"算法执行 - {algorithm}: {status}, 分割区域: {segments}, 耗时: {duration:.3f}s")


class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> ImageSegmentationLogger:
        """获取日志器"""
        if self._logger is None:
            class_name = self.__class__.__name__
            self._logger = ImageSegmentationLogger(f"ImageSegmentation.{class_name}")
        return self._logger


def get_logger(name: str = "ImageSegmentation") -> ImageSegmentationLogger:
    """获取日志器实例"""
    return ImageSegmentationLogger(name)


def log_exception(func):
    """装饰器：自动记录函数异常"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            logger.log_function_call(func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败", exception=e)
            raise
    return wrapper


def log_performance(operation_name: str = None):
    """装饰器：自动记录函数性能"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger()
            
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"操作 {op_name} 失败，耗时 {duration:.3f}s", exception=e)
                raise
        return wrapper
    return decorator


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, logger: Optional[ImageSegmentationLogger] = None):
        self.logger = logger or get_logger("ErrorHandler")
    
    def handle_image_load_error(self, file_path: str, error: Exception) -> bool:
        """处理图像加载错误"""
        self.logger.error(f"图像加载失败: {file_path}", exception=error)
        
        # 根据错误类型提供不同的处理建议
        if "No such file" in str(error):
            self.logger.info("建议: 检查文件路径是否正确")
        elif "cannot identify image file" in str(error):
            self.logger.info("建议: 检查文件格式是否支持")
        elif "Permission denied" in str(error):
            self.logger.info("建议: 检查文件访问权限")
        
        return False
    
    def handle_algorithm_error(self, algorithm: str, error: Exception) -> bool:
        """处理算法执行错误"""
        self.logger.error(f"算法 {algorithm} 执行失败", exception=error)
        
        # 根据错误类型提供处理建议
        if "memory" in str(error).lower():
            self.logger.info("建议: 尝试减小图像尺寸或调整算法参数")
        elif "parameter" in str(error).lower():
            self.logger.info("建议: 检查算法参数设置")
        
        return False
    
    def handle_gui_error(self, component: str, error: Exception) -> bool:
        """处理GUI错误"""
        self.logger.error(f"GUI组件 {component} 错误", exception=error)
        
        # GUI错误通常不应该中断程序
        return True
    
    def handle_file_save_error(self, file_path: str, error: Exception) -> bool:
        """处理文件保存错误"""
        self.logger.error(f"文件保存失败: {file_path}", exception=error)
        
        if "Permission denied" in str(error):
            self.logger.info("建议: 检查目录写入权限")
        elif "No space left" in str(error):
            self.logger.info("建议: 检查磁盘空间")
        
        return False


# 全局日志器实例
_global_logger = None

def setup_global_logger(log_dir: str = "logs", level: str = "INFO"):
    """设置全局日志器"""
    global _global_logger
    _global_logger = ImageSegmentationLogger("ImageSegmentation", log_dir)
    
    # 设置日志级别
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    _global_logger.logger.setLevel(level_map.get(level.upper(), logging.INFO))

def get_global_logger() -> ImageSegmentationLogger:
    """获取全局日志器"""
    global _global_logger
    if _global_logger is None:
        setup_global_logger()
    return _global_logger


# 便捷函数
def debug(message: str, **kwargs):
    """记录调试信息"""
    get_global_logger().debug(message, **kwargs)

def info(message: str, **kwargs):
    """记录一般信息"""
    get_global_logger().info(message, **kwargs)

def warning(message: str, **kwargs):
    """记录警告信息"""
    get_global_logger().warning(message, **kwargs)

def error(message: str, exception: Optional[Exception] = None, **kwargs):
    """记录错误信息"""
    get_global_logger().error(message, exception, **kwargs)

def critical(message: str, exception: Optional[Exception] = None, **kwargs):
    """记录严重错误"""
    get_global_logger().critical(message, exception, **kwargs)
