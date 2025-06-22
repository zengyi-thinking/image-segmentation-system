"""
Watershed图像分割算法实现
基于分水岭变换的图像分割，用于与MST算法进行对比
"""

import numpy as np
import cv2
from scipy import ndimage
from skimage import segmentation, feature, filters, morphology
from skimage.segmentation import watershed
from typing import Dict, Optional, Tuple, Any, Callable
import time

# Try different import paths for peak_local_maxima
try:
    from skimage.feature.peak import peak_local_maxima
except ImportError:
    try:
        from skimage.feature import peak_local_maxima
    except ImportError:
        # Fallback implementation if peak_local_maxima is not available
        def peak_local_maxima(image, min_distance=1, threshold_abs=None, **kwargs):
            """
            Fallback implementation for peak_local_maxima
            """
            from scipy.ndimage import maximum_filter

            # Apply maximum filter
            local_maxima = maximum_filter(image, size=min_distance) == image

            # Apply threshold if provided
            if threshold_abs is not None:
                local_maxima = local_maxima & (image >= threshold_abs)

            # Return coordinates as tuple of arrays (similar to original function)
            coords = np.where(local_maxima)
            return coords

from data_structures.segmentation_result import SegmentationResult


class WatershedSegmentation:
    """
    Watershed分割算法实现
    
    基于分水岭变换的图像分割算法，通过模拟水流填充过程来分割图像。
    算法步骤：
    1. 预处理：去噪、增强对比度
    2. 梯度计算：计算图像梯度作为地形图
    3. 标记点检测：找到局部最小值作为种子点
    4. 分水岭变换：模拟水流填充过程
    5. 后处理：合并小区域、优化边界
    """
    
    def __init__(self, 
                 min_distance: int = 20,
                 compactness: float = 0.001,
                 watershed_line: bool = True):
        """
        初始化Watershed分割器
        
        Args:
            min_distance: 局部最大值之间的最小距离
            compactness: 分水岭的紧凑性参数
            watershed_line: 是否在分割边界添加分水岭线
        """
        self.min_distance = min_distance
        self.compactness = compactness
        self.watershed_line = watershed_line
        
        # 统计信息
        self.processing_stats = {
            'preprocessing_time': 0.0,
            'gradient_time': 0.0,
            'markers_time': 0.0,
            'watershed_time': 0.0,
            'postprocessing_time': 0.0,
            'total_time': 0.0
        }
    
    def segment(self, 
                image: np.ndarray, 
                markers: Optional[np.ndarray] = None,
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行Watershed分割
        
        Args:
            image: 输入图像 (H, W, 3) 或 (H, W)
            markers: 可选的标记图像，如果为None则自动生成
            progress_callback: 进度回调函数
            
        Returns:
            包含分割结果的字典
        """
        start_time = time.time()
        
        try:
            # 确保图像格式正确
            if len(image.shape) == 3:
                # 转换为灰度图像
                if image.shape[2] == 3:
                    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                else:
                    gray_image = image[:, :, 0]
            else:
                gray_image = image.copy()
            
            height, width = gray_image.shape
            self._safe_progress_callback(progress_callback, "开始Watershed分割...", 0.0)
            
            # 1. 预处理
            self._safe_progress_callback(progress_callback, "图像预处理...", 0.1)
            preprocessed = self._preprocess_image(gray_image)
            
            # 2. 计算梯度
            self._safe_progress_callback(progress_callback, "计算图像梯度...", 0.3)
            gradient = self._compute_gradient(preprocessed)
            
            # 3. 生成或处理标记点
            self._safe_progress_callback(progress_callback, "检测标记点...", 0.5)
            if markers is None:
                markers = self._generate_markers(preprocessed, gradient)
            else:
                markers = self._process_markers(markers)
            
            # 4. 执行分水岭变换
            self._safe_progress_callback(progress_callback, "执行分水岭变换...", 0.7)
            labels = self._apply_watershed(gradient, markers)
            
            # 5. 后处理
            self._safe_progress_callback(progress_callback, "后处理优化...", 0.9)
            final_labels = self._postprocess_labels(labels, preprocessed)
            
            # 计算统计信息
            self.processing_stats['total_time'] = time.time() - start_time
            
            # 创建分割结果
            result = SegmentationResult(
                label_map=final_labels,
                original_image=image,
                algorithm_name="Watershed",
                parameters={
                    'min_distance': self.min_distance,
                    'compactness': self.compactness,
                    'watershed_line': self.watershed_line
                }
            )
            
            self._safe_progress_callback(progress_callback, "Watershed分割完成", 1.0)
            
            return {
                'label_map': final_labels,
                'segmentation_result': result,
                'statistics': result.statistics,
                'processing_stats': self.processing_stats.copy(),
                'algorithm': 'Watershed'
            }
            
        except Exception as e:
            error_msg = f"Watershed分割过程中发生错误: {str(e)}"
            self._safe_progress_callback(progress_callback, error_msg, -1)
            raise RuntimeError(error_msg) from e
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像"""
        start_time = time.time()
        
        # 去噪
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        # 增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        self.processing_stats['preprocessing_time'] = time.time() - start_time
        return enhanced
    
    def _compute_gradient(self, image: np.ndarray) -> np.ndarray:
        """计算图像梯度"""
        start_time = time.time()
        
        # 使用Sobel算子计算梯度
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(grad_x**2 + grad_y**2)
        
        # 归一化到0-255范围
        gradient = ((gradient - gradient.min()) / 
                   (gradient.max() - gradient.min()) * 255).astype(np.uint8)
        
        self.processing_stats['gradient_time'] = time.time() - start_time
        return gradient
    
    def _generate_markers(self, image: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """自动生成标记点"""
        start_time = time.time()
        
        # 使用形态学操作找到局部最小值
        # 1. 计算距离变换
        binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        distance = ndimage.distance_transform_edt(binary)
        
        # 2. 找到局部最大值作为种子点
        local_maxima = peak_local_maxima(
            distance, 
            min_distance=self.min_distance,
            threshold_abs=0.3 * distance.max()
        )
        
        # 3. 创建标记图像
        markers = np.zeros_like(image, dtype=np.int32)
        for i, (y, x) in enumerate(zip(local_maxima[0], local_maxima[1])):
            markers[y, x] = i + 1
        
        # 4. 扩展标记点
        markers = morphology.dilation(markers, morphology.disk(2))
        
        self.processing_stats['markers_time'] = time.time() - start_time
        return markers
    
    def _process_markers(self, markers: np.ndarray) -> np.ndarray:
        """处理用户提供的标记点"""
        start_time = time.time()
        
        # 确保标记点是连续的整数
        unique_labels = np.unique(markers)
        processed_markers = np.zeros_like(markers, dtype=np.int32)
        
        for i, label in enumerate(unique_labels):
            if label > 0:  # 跳过背景
                processed_markers[markers == label] = i + 1
        
        self.processing_stats['markers_time'] = time.time() - start_time
        return processed_markers
    
    def _apply_watershed(self, gradient: np.ndarray, markers: np.ndarray) -> np.ndarray:
        """应用分水岭变换"""
        start_time = time.time()
        
        # 执行分水岭变换
        labels = watershed(
            gradient, 
            markers, 
            compactness=self.compactness,
            watershed_line=self.watershed_line
        )
        
        self.processing_stats['watershed_time'] = time.time() - start_time
        return labels
    
    def _postprocess_labels(self, labels: np.ndarray, original: np.ndarray) -> np.ndarray:
        """后处理标签图像"""
        start_time = time.time()
        
        # 移除小区域
        min_size = max(50, (labels.shape[0] * labels.shape[1]) // 1000)
        cleaned_labels = morphology.remove_small_objects(
            labels.astype(bool), 
            min_size=min_size
        ).astype(np.int32)
        
        # 重新标记连续区域
        final_labels = segmentation.relabel_sequential(cleaned_labels)[0]
        
        self.processing_stats['postprocessing_time'] = time.time() - start_time
        return final_labels
    
    def _safe_progress_callback(self, callback, message: str, progress: float):
        """安全的进度回调调用"""
        if callback is not None and callable(callback):
            try:
                callback(message, progress)
            except Exception as e:
                print(f"进度回调函数错误: {e}")
    
    def get_processing_stats(self) -> Dict[str, float]:
        """获取处理统计信息"""
        return self.processing_stats.copy()
    
    def set_parameters(self, **kwargs):
        """设置算法参数"""
        if 'min_distance' in kwargs:
            self.min_distance = max(1, int(kwargs['min_distance']))
        if 'compactness' in kwargs:
            self.compactness = max(0.0, float(kwargs['compactness']))
        if 'watershed_line' in kwargs:
            self.watershed_line = bool(kwargs['watershed_line'])
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取当前算法参数"""
        return {
            'min_distance': self.min_distance,
            'compactness': self.compactness,
            'watershed_line': self.watershed_line
        }
