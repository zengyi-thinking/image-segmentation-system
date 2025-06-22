"""
自定义异常类和异常处理系统
提供专门的异常类型和统一的异常处理机制
"""

from typing import Optional, Any, Dict
import traceback
from utils.logger import get_logger


class ImageSegmentationError(Exception):
    """图像分割系统基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详细信息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        
        # 记录异常
        logger = get_logger("Exception")
        logger.error(f"[{self.error_code}] {message}", exception=self)


class ImageLoadError(ImageSegmentationError):
    """图像加载异常"""
    
    def __init__(self, file_path: str, reason: str = None):
        self.file_path = file_path
        self.reason = reason or "未知原因"
        
        message = f"图像加载失败: {file_path} - {self.reason}"
        details = {"file_path": file_path, "reason": reason}
        
        super().__init__(message, "IMAGE_LOAD_ERROR", details)


class ImageSaveError(ImageSegmentationError):
    """图像保存异常"""
    
    def __init__(self, file_path: str, reason: str = None):
        self.file_path = file_path
        self.reason = reason or "未知原因"
        
        message = f"图像保存失败: {file_path} - {self.reason}"
        details = {"file_path": file_path, "reason": reason}
        
        super().__init__(message, "IMAGE_SAVE_ERROR", details)


class AlgorithmError(ImageSegmentationError):
    """算法执行异常"""
    
    def __init__(self, algorithm_name: str, reason: str = None, parameters: Dict[str, Any] = None):
        self.algorithm_name = algorithm_name
        self.reason = reason or "算法执行失败"
        self.parameters = parameters or {}
        
        message = f"算法 {algorithm_name} 执行失败: {self.reason}"
        details = {"algorithm": algorithm_name, "reason": reason, "parameters": parameters}
        
        super().__init__(message, "ALGORITHM_ERROR", details)


class ParameterError(ImageSegmentationError):
    """参数错误异常"""
    
    def __init__(self, parameter_name: str, value: Any, expected: str = None):
        self.parameter_name = parameter_name
        self.value = value
        self.expected = expected
        
        message = f"参数错误: {parameter_name} = {value}"
        if expected:
            message += f", 期望: {expected}"
        
        details = {"parameter": parameter_name, "value": value, "expected": expected}
        
        super().__init__(message, "PARAMETER_ERROR", details)


class MemoryError(ImageSegmentationError):
    """内存不足异常"""
    
    def __init__(self, operation: str, required_mb: float = None, available_mb: float = None):
        self.operation = operation
        self.required_mb = required_mb
        self.available_mb = available_mb
        
        message = f"内存不足: {operation}"
        if required_mb and available_mb:
            message += f" (需要: {required_mb:.1f}MB, 可用: {available_mb:.1f}MB)"
        
        details = {"operation": operation, "required_mb": required_mb, "available_mb": available_mb}
        
        super().__init__(message, "MEMORY_ERROR", details)


class ConfigurationError(ImageSegmentationError):
    """配置错误异常"""
    
    def __init__(self, config_key: str, reason: str = None):
        self.config_key = config_key
        self.reason = reason or "配置无效"
        
        message = f"配置错误: {config_key} - {self.reason}"
        details = {"config_key": config_key, "reason": reason}
        
        super().__init__(message, "CONFIG_ERROR", details)


class GUIError(ImageSegmentationError):
    """GUI异常"""
    
    def __init__(self, component: str, operation: str, reason: str = None):
        self.component = component
        self.operation = operation
        self.reason = reason or "GUI操作失败"
        
        message = f"GUI错误: {component}.{operation} - {self.reason}"
        details = {"component": component, "operation": operation, "reason": reason}
        
        super().__init__(message, "GUI_ERROR", details)


class ValidationError(ImageSegmentationError):
    """数据验证异常"""
    
    def __init__(self, data_type: str, validation_rule: str, value: Any = None):
        self.data_type = data_type
        self.validation_rule = validation_rule
        self.value = value
        
        message = f"数据验证失败: {data_type} - {validation_rule}"
        if value is not None:
            message += f" (值: {value})"
        
        details = {"data_type": data_type, "validation_rule": validation_rule, "value": value}
        
        super().__init__(message, "VALIDATION_ERROR", details)


class ExceptionHandler:
    """统一异常处理器"""
    
    def __init__(self):
        self.logger = get_logger("ExceptionHandler")
        self.error_callbacks = {}
    
    def register_error_callback(self, error_type: type, callback):
        """注册错误回调函数"""
        self.error_callbacks[error_type] = callback
    
    def handle_exception(self, exception: Exception, context: str = None) -> bool:
        """
        处理异常
        
        Args:
            exception: 异常对象
            context: 异常上下文
            
        Returns:
            bool: 是否应该继续执行
        """
        # 记录异常
        context_msg = f" (上下文: {context})" if context else ""
        self.logger.error(f"异常处理{context_msg}", exception=exception)
        
        # 调用特定的错误回调
        exception_type = type(exception)
        if exception_type in self.error_callbacks:
            try:
                return self.error_callbacks[exception_type](exception)
            except Exception as callback_error:
                self.logger.error("错误回调函数执行失败", exception=callback_error)
        
        # 根据异常类型决定处理方式
        if isinstance(exception, ImageLoadError):
            return self._handle_image_load_error(exception)
        elif isinstance(exception, AlgorithmError):
            return self._handle_algorithm_error(exception)
        elif isinstance(exception, MemoryError):
            return self._handle_memory_error(exception)
        elif isinstance(exception, GUIError):
            return self._handle_gui_error(exception)
        elif isinstance(exception, ParameterError):
            return self._handle_parameter_error(exception)
        else:
            return self._handle_generic_error(exception)
    
    def _handle_image_load_error(self, error: ImageLoadError) -> bool:
        """处理图像加载错误"""
        self.logger.info(f"图像加载失败建议: 检查文件路径和格式 - {error.file_path}")
        return False  # 不继续执行
    
    def _handle_algorithm_error(self, error: AlgorithmError) -> bool:
        """处理算法错误"""
        self.logger.info(f"算法错误建议: 检查参数设置或尝试其他算法 - {error.algorithm_name}")
        return False  # 不继续执行
    
    def _handle_memory_error(self, error: MemoryError) -> bool:
        """处理内存错误"""
        self.logger.info("内存不足建议: 尝试减小图像尺寸或关闭其他程序")
        return False  # 不继续执行
    
    def _handle_gui_error(self, error: GUIError) -> bool:
        """处理GUI错误"""
        self.logger.info(f"GUI错误建议: 尝试重新启动应用程序 - {error.component}")
        return True  # GUI错误通常可以继续执行
    
    def _handle_parameter_error(self, error: ParameterError) -> bool:
        """处理参数错误"""
        self.logger.info(f"参数错误建议: 检查参数设置 - {error.parameter_name}")
        return False  # 不继续执行
    
    def _handle_generic_error(self, error: Exception) -> bool:
        """处理通用错误"""
        self.logger.info("通用错误建议: 检查系统状态或联系技术支持")
        return False  # 不继续执行


def safe_execute(func, *args, error_handler: ExceptionHandler = None, context: str = None, **kwargs):
    """
    安全执行函数，自动处理异常
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        error_handler: 异常处理器
        context: 执行上下文
        **kwargs: 函数关键字参数
        
    Returns:
        tuple: (是否成功, 结果或异常)
    """
    if error_handler is None:
        error_handler = ExceptionHandler()
    
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        should_continue = error_handler.handle_exception(e, context)
        return should_continue, e


def exception_handler(error_type: type = Exception, return_value: Any = None, log_error: bool = True):
    """
    异常处理装饰器
    
    Args:
        error_type: 要捕获的异常类型
        return_value: 异常时的返回值
        log_error: 是否记录错误
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log_error:
                    logger = get_logger()
                    logger.error(f"函数 {func.__name__} 执行异常", exception=e)
                return return_value
        return wrapper
    return decorator


def validate_parameter(value: Any, param_name: str, validator_func, error_message: str = None):
    """
    参数验证函数
    
    Args:
        value: 要验证的值
        param_name: 参数名称
        validator_func: 验证函数
        error_message: 自定义错误消息
    """
    if not validator_func(value):
        message = error_message or f"参数 {param_name} 验证失败"
        raise ParameterError(param_name, value, message)


def validate_image_size(width: int, height: int, max_size: tuple = (4096, 4096)):
    """验证图像尺寸"""
    max_width, max_height = max_size
    
    if width <= 0 or height <= 0:
        raise ValidationError("图像尺寸", "宽度和高度必须大于0", f"{width}x{height}")
    
    if width > max_width or height > max_height:
        raise ValidationError("图像尺寸", f"尺寸不能超过 {max_width}x{max_height}", f"{width}x{height}")


def validate_algorithm_parameters(algorithm: str, parameters: Dict[str, Any]):
    """验证算法参数"""
    if algorithm == "MST":
        alpha = parameters.get("alpha", 1.0)
        beta = parameters.get("beta", 0.1)
        connectivity = parameters.get("connectivity", 4)
        
        if not (0.1 <= alpha <= 10.0):
            raise ParameterError("alpha", alpha, "0.1 到 10.0 之间")
        
        if not (0.001 <= beta <= 1.0):
            raise ParameterError("beta", beta, "0.001 到 1.0 之间")
        
        if connectivity not in [4, 8]:
            raise ParameterError("connectivity", connectivity, "4 或 8")
    
    elif algorithm == "Watershed":
        min_distance = parameters.get("min_distance", 20)
        compactness = parameters.get("compactness", 0.001)
        
        if not (1 <= min_distance <= 100):
            raise ParameterError("min_distance", min_distance, "1 到 100 之间")
        
        if not (0.0001 <= compactness <= 0.01):
            raise ParameterError("compactness", compactness, "0.0001 到 0.01 之间")


# 全局异常处理器
_global_exception_handler = None

def get_exception_handler() -> ExceptionHandler:
    """获取全局异常处理器"""
    global _global_exception_handler
    if _global_exception_handler is None:
        _global_exception_handler = ExceptionHandler()
    return _global_exception_handler
