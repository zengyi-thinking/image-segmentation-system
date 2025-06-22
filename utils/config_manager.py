"""
配置管理系统
提供统一的配置管理功能，支持配置文件读取、验证和动态更新
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from dataclasses import dataclass, asdict
from utils.logger import get_logger


@dataclass
class AlgorithmConfig:
    """算法配置"""
    # MST算法配置
    mst_alpha: float = 1.0
    mst_beta: float = 0.1
    mst_connectivity: int = 4
    mst_min_segment_size: int = 10
    
    # Watershed算法配置
    watershed_min_distance: int = 20
    watershed_compactness: float = 0.001
    watershed_line: bool = True
    
    # 通用配置
    auto_threshold: bool = True
    default_threshold: float = 0.0


@dataclass
class GUIConfig:
    """GUI配置"""
    # 窗口配置
    window_width: int = 1600
    window_height: int = 1000
    min_width: int = 1200
    min_height: int = 800
    
    # 主题配置
    default_theme: str = "blue"
    theme_auto_save: bool = True
    
    # 图像显示配置
    max_image_size: tuple = (4096, 4096)
    zoom_min: float = 0.1
    zoom_max: float = 5.0
    zoom_step: float = 1.2
    
    # 滚动配置
    scroll_sensitivity: float = 1.0
    smooth_scroll: bool = True
    scroll_animation_steps: int = 10


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 内存管理
    max_memory_usage_mb: int = 2048
    cache_size_mb: int = 512
    gc_threshold: int = 100
    
    # 并发配置
    max_threads: int = 4
    use_multiprocessing: bool = False
    
    # 图像处理
    image_chunk_size: int = 1024
    lazy_loading: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True


@dataclass
class SystemConfig:
    """系统总配置"""
    algorithm: AlgorithmConfig
    gui: GUIConfig
    performance: PerformanceConfig
    logging: LoggingConfig
    
    # 系统信息
    version: str = "2.0.0"
    debug_mode: bool = False
    auto_save_settings: bool = True


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "system_config.json"
        self.user_config_file = self.config_dir / "user_config.json"
        
        self.logger = get_logger("ConfigManager")
        self._config = None
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> SystemConfig:
        """加载配置"""
        try:
            # 首先尝试加载用户配置
            if self.user_config_file.exists():
                config_data = self._load_json_file(self.user_config_file)
                self.logger.info("已加载用户配置文件")
            elif self.config_file.exists():
                config_data = self._load_json_file(self.config_file)
                self.logger.info("已加载系统配置文件")
            else:
                # 使用默认配置
                config_data = {}
                self.logger.info("使用默认配置")
            
            # 创建配置对象
            self._config = self._create_config_from_dict(config_data)
            
            # 验证配置
            self._validate_config()
            
            # 保存配置（确保文件存在）
            self.save_config()
            
            return self._config
            
        except Exception as e:
            self.logger.error("配置加载失败，使用默认配置", exception=e)
            self._config = self._create_default_config()
            return self._config
    
    def save_config(self, user_config: bool = True):
        """保存配置"""
        try:
            config_dict = asdict(self._config)
            
            if user_config:
                self._save_json_file(self.user_config_file, config_dict)
                self.logger.info("用户配置已保存")
            else:
                self._save_json_file(self.config_file, config_dict)
                self.logger.info("系统配置已保存")
                
        except Exception as e:
            self.logger.error("配置保存失败", exception=e)
    
    def get_config(self) -> SystemConfig:
        """获取当前配置"""
        if self._config is None:
            self.load_config()
        return self._config
    
    def update_config(self, **kwargs):
        """更新配置"""
        if self._config is None:
            self.load_config()
        
        # 更新配置字段
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                self.logger.debug(f"配置更新: {key} = {value}")
        
        # 自动保存
        if self._config.auto_save_settings:
            self.save_config()
    
    def reset_to_default(self):
        """重置为默认配置"""
        self._config = self._create_default_config()
        self.save_config()
        self.logger.info("配置已重置为默认值")
    
    def export_config(self, file_path: str):
        """导出配置到文件"""
        try:
            config_dict = asdict(self._config)
            
            file_path = Path(file_path)
            if file_path.suffix.lower() == '.yaml':
                self._save_yaml_file(file_path, config_dict)
            else:
                self._save_json_file(file_path, config_dict)
            
            self.logger.info(f"配置已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"配置导出失败: {file_path}", exception=e)
    
    def import_config(self, file_path: str):
        """从文件导入配置"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.yaml':
                config_data = self._load_yaml_file(file_path)
            else:
                config_data = self._load_json_file(file_path)
            
            self._config = self._create_config_from_dict(config_data)
            self._validate_config()
            self.save_config()
            
            self.logger.info(f"配置已从文件导入: {file_path}")
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {file_path}", exception=e)
    
    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
        return SystemConfig(
            algorithm=AlgorithmConfig(),
            gui=GUIConfig(),
            performance=PerformanceConfig(),
            logging=LoggingConfig()
        )
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> SystemConfig:
        """从字典创建配置对象"""
        # 创建默认配置
        config = self._create_default_config()
        
        # 更新算法配置
        if 'algorithm' in config_data:
            alg_data = config_data['algorithm']
            for key, value in alg_data.items():
                if hasattr(config.algorithm, key):
                    setattr(config.algorithm, key, value)
        
        # 更新GUI配置
        if 'gui' in config_data:
            gui_data = config_data['gui']
            for key, value in gui_data.items():
                if hasattr(config.gui, key):
                    setattr(config.gui, key, value)
        
        # 更新性能配置
        if 'performance' in config_data:
            perf_data = config_data['performance']
            for key, value in perf_data.items():
                if hasattr(config.performance, key):
                    setattr(config.performance, key, value)
        
        # 更新日志配置
        if 'logging' in config_data:
            log_data = config_data['logging']
            for key, value in log_data.items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)
        
        # 更新系统配置
        for key in ['version', 'debug_mode', 'auto_save_settings']:
            if key in config_data:
                setattr(config, key, config_data[key])
        
        return config
    
    def _validate_config(self):
        """验证配置有效性"""
        config = self._config
        
        # 验证算法配置
        assert 0.1 <= config.algorithm.mst_alpha <= 10.0, "MST alpha 参数超出范围"
        assert 0.001 <= config.algorithm.mst_beta <= 1.0, "MST beta 参数超出范围"
        assert config.algorithm.mst_connectivity in [4, 8], "连接性必须是4或8"
        
        # 验证GUI配置
        assert config.gui.window_width >= config.gui.min_width, "窗口宽度不能小于最小宽度"
        assert config.gui.window_height >= config.gui.min_height, "窗口高度不能小于最小高度"
        assert 0.1 <= config.gui.zoom_min <= config.gui.zoom_max <= 10.0, "缩放范围无效"
        
        # 验证性能配置
        assert config.performance.max_memory_usage_mb > 0, "最大内存使用量必须大于0"
        assert config.performance.max_threads > 0, "线程数必须大于0"
        
        self.logger.debug("配置验证通过")
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_json_file(self, file_path: Path, data: Dict[str, Any]):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except ImportError:
            raise ImportError("需要安装PyYAML库来支持YAML配置文件")
    
    def _save_yaml_file(self, file_path: Path, data: Dict[str, Any]):
        """保存YAML文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except ImportError:
            raise ImportError("需要安装PyYAML库来支持YAML配置文件")


# 全局配置管理器实例
_global_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def get_config() -> SystemConfig:
    """获取当前系统配置"""
    return get_config_manager().get_config()

def update_config(**kwargs):
    """更新系统配置"""
    get_config_manager().update_config(**kwargs)
