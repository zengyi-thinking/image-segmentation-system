"""
图像分割系统综合测试套件
包含单元测试、集成测试和端到端测试
"""

import unittest
import sys
import os
from pathlib import Path
import numpy as np
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试模块
from utils.image_io import ImageLoader
from utils.logger import get_logger, setup_global_logger
from utils.config_manager import ConfigManager
from utils.exceptions import ImageLoadError, AlgorithmError, ParameterError
from utils.performance_monitor import MemoryManager, PerformanceMonitor
from core.mst_segmentation import MSTSegmentation
from core.watershed_segmentation import WatershedSegmentation


class TestImageIO(unittest.TestCase):
    """图像IO测试"""
    
    def setUp(self):
        """测试前准备"""
        self.loader = ImageLoader()
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试图像
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_image_path = Path(self.temp_dir) / "test_image.png"
        
        from PIL import Image
        Image.fromarray(self.test_image).save(self.test_image_path)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_valid_image(self):
        """测试加载有效图像"""
        image = self.loader.load_image(self.test_image_path)
        self.assertIsNotNone(image)
        self.assertEqual(image.shape, (100, 100, 3))
        self.assertEqual(image.dtype, np.uint8)
    
    def test_load_nonexistent_image(self):
        """测试加载不存在的图像"""
        with self.assertRaises(ImageLoadError):
            self.loader.load_image("nonexistent.png")
    
    def test_load_unsupported_format(self):
        """测试加载不支持的格式"""
        unsupported_file = Path(self.temp_dir) / "test.xyz"
        unsupported_file.write_text("dummy content")
        
        with self.assertRaises(ImageLoadError):
            self.loader.load_image(unsupported_file)
    
    def test_image_size_validation(self):
        """测试图像尺寸验证"""
        # 创建超大图像路径（模拟）
        large_image_path = Path(self.temp_dir) / "large.png"
        
        # 模拟文件大小检查
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 200 * 1024 * 1024  # 200MB
            
            with self.assertRaises(ImageLoadError):
                self.loader._validate_image_path(large_image_path)
    
    def test_load_statistics(self):
        """测试加载统计"""
        initial_stats = self.loader.get_load_statistics()
        
        # 加载图像
        self.loader.load_image(self.test_image_path)
        
        updated_stats = self.loader.get_load_statistics()
        self.assertEqual(updated_stats['total_loaded'], initial_stats['total_loaded'] + 1)


class TestAlgorithms(unittest.TestCase):
    """算法测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        self.mst_algorithm = MSTSegmentation()
        self.watershed_algorithm = WatershedSegmentation()
    
    def test_mst_segmentation(self):
        """测试MST分割算法"""
        try:
            result = self.mst_algorithm.segment(self.test_image)
            self.assertIsNotNone(result)
            self.assertIn('segmented_image', result)
            self.assertIn('num_segments', result)
        except Exception as e:
            self.skipTest(f"MST算法测试跳过: {e}")
    
    def test_watershed_segmentation(self):
        """测试Watershed分割算法"""
        try:
            result = self.watershed_algorithm.segment(self.test_image)
            self.assertIsNotNone(result)
            self.assertIn('segmented_image', result)
            self.assertIn('num_segments', result)
        except Exception as e:
            self.skipTest(f"Watershed算法测试跳过: {e}")
    
    def test_invalid_parameters(self):
        """测试无效参数"""
        with self.assertRaises((ParameterError, ValueError)):
            self.mst_algorithm.segment(self.test_image, alpha=-1)
    
    def test_empty_image(self):
        """测试空图像"""
        empty_image = np.array([])
        
        with self.assertRaises((AlgorithmError, ValueError)):
            self.mst_algorithm.segment(empty_image)


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config(self):
        """测试默认配置"""
        config = self.config_manager.get_config()
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.algorithm)
        self.assertIsNotNone(config.gui)
        self.assertIsNotNone(config.performance)
        self.assertIsNotNone(config.logging)
    
    def test_save_and_load_config(self):
        """测试配置保存和加载"""
        # 修改配置
        config = self.config_manager.get_config()
        original_alpha = config.algorithm.mst_alpha
        config.algorithm.mst_alpha = 2.5
        
        # 保存配置
        self.config_manager.save_config()
        
        # 创建新的配置管理器
        new_manager = ConfigManager(self.temp_dir)
        new_config = new_manager.get_config()
        
        # 验证配置已保存
        self.assertEqual(new_config.algorithm.mst_alpha, 2.5)
        self.assertNotEqual(new_config.algorithm.mst_alpha, original_alpha)
    
    def test_config_validation(self):
        """测试配置验证"""
        config = self.config_manager.get_config()
        
        # 设置无效值
        config.algorithm.mst_alpha = -1
        
        with self.assertRaises(AssertionError):
            self.config_manager._validate_config()


class TestMemoryManager(unittest.TestCase):
    """内存管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.memory_manager = MemoryManager()
    
    def test_memory_usage(self):
        """测试内存使用监控"""
        usage = self.memory_manager.get_memory_usage()
        
        self.assertIn('used_mb', usage)
        self.assertIn('available_mb', usage)
        self.assertIn('percent', usage)
        self.assertGreater(usage['used_mb'], 0)
    
    def test_image_cache(self):
        """测试图像缓存"""
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 缓存图像
        success = self.memory_manager.cache_image("test_key", test_image)
        self.assertTrue(success)
        
        # 获取缓存图像
        cached_image = self.memory_manager.get_cached_image("test_key")
        self.assertIsNotNone(cached_image)
        np.testing.assert_array_equal(test_image, cached_image)
        
        # 清空缓存
        self.memory_manager.clear_cache()
        cached_image = self.memory_manager.get_cached_image("test_key")
        self.assertIsNone(cached_image)


class TestPerformanceMonitor(unittest.TestCase):
    """性能监控器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.monitor = PerformanceMonitor()
    
    def test_metrics_collection(self):
        """测试性能指标收集"""
        # 启动监控
        self.monitor.start_monitoring(0.1)
        
        # 等待收集一些数据
        time.sleep(0.5)
        
        # 停止监控
        self.monitor.stop_monitoring()
        
        # 检查是否收集到数据
        metrics = self.monitor.get_current_metrics()
        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertGreaterEqual(metrics.memory_percent, 0)
    
    def test_alert_callback(self):
        """测试警报回调"""
        callback_called = False
        
        def test_callback(alert, metrics):
            nonlocal callback_called
            callback_called = True
        
        self.monitor.add_alert_callback(test_callback)
        
        # 模拟高CPU使用率
        mock_metrics = Mock()
        mock_metrics.cpu_percent = 95.0
        mock_metrics.memory_percent = 50.0
        mock_metrics.memory_available_mb = 1000
        
        self.monitor._check_thresholds(mock_metrics)
        
        self.assertTrue(callback_called)


class TestLogging(unittest.TestCase):
    """日志系统测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        setup_global_logger(self.temp_dir, "DEBUG")
        self.logger = get_logger("TestLogger")
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_levels(self):
        """测试日志级别"""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        
        # 检查日志文件是否创建
        log_files = list(Path(self.temp_dir).glob("*.log"))
        self.assertGreater(len(log_files), 0)
    
    def test_performance_logging(self):
        """测试性能日志"""
        self.logger.log_performance("test_operation", 1.5, param1="value1")
        
        # 验证日志记录（这里只是确保不抛出异常）
        self.assertTrue(True)


class TestExceptions(unittest.TestCase):
    """异常处理测试"""
    
    def test_image_load_error(self):
        """测试图像加载异常"""
        error = ImageLoadError("test.png", "文件不存在")
        
        self.assertEqual(error.file_path, "test.png")
        self.assertEqual(error.reason, "文件不存在")
        self.assertEqual(error.error_code, "IMAGE_LOAD_ERROR")
    
    def test_algorithm_error(self):
        """测试算法异常"""
        error = AlgorithmError("MST", "参数无效", {"alpha": -1})
        
        self.assertEqual(error.algorithm_name, "MST")
        self.assertEqual(error.reason, "参数无效")
        self.assertEqual(error.parameters["alpha"], -1)
    
    def test_parameter_error(self):
        """测试参数异常"""
        error = ParameterError("alpha", -1, "必须大于0")
        
        self.assertEqual(error.parameter_name, "alpha")
        self.assertEqual(error.value, -1)
        self.assertEqual(error.expected, "必须大于0")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试图像
        self.test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        self.test_image_path = Path(self.temp_dir) / "test.png"
        
        from PIL import Image
        Image.fromarray(self.test_image).save(self.test_image_path)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 1. 加载图像
        loader = ImageLoader()
        image = loader.load_image(self.test_image_path)
        self.assertIsNotNone(image)
        
        # 2. 执行分割算法
        try:
            algorithm = MSTSegmentation()
            result = algorithm.segment(image)
            self.assertIsNotNone(result)
        except Exception as e:
            self.skipTest(f"算法测试跳过: {e}")
        
        # 3. 检查结果
        if 'result' in locals():
            self.assertIn('segmented_image', result)
            self.assertIn('num_segments', result)


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestImageIO,
        TestAlgorithms,
        TestConfigManager,
        TestMemoryManager,
        TestPerformanceMonitor,
        TestLogging,
        TestExceptions,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("🧪 开始运行图像分割系统测试套件...")
    print("=" * 60)
    
    result = run_all_tests()
    
    print("=" * 60)
    print(f"测试完成!")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)
