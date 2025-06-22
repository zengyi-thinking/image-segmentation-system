"""
K-Means聚类图像分割算法
基于颜色聚类的图像分割方法
"""

import numpy as np
import cv2
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
from typing import Dict, Any, Optional, Tuple

from utils.logger import LoggerMixin, log_performance
from utils.exceptions import AlgorithmError, ParameterError, validate_algorithm_parameters
from data_structures.segmentation_result import SegmentationResult


class KMeansSegmentation(LoggerMixin):
    """K-Means聚类分割算法"""
    
    def __init__(self):
        super().__init__()
        self.algorithm_name = "K-Means"
        self.logger.info("K-Means分割算法初始化")
    
    @log_performance("K-Means分割")
    def segment(self, image: np.ndarray, 
                k: int = 5,
                max_iter: int = 100,
                color_space: str = 'RGB',
                spatial_weight: float = 0.0,
                random_state: int = 42,
                **kwargs) -> Dict[str, Any]:
        """
        执行K-Means分割
        
        Args:
            image: 输入图像 (H, W, 3)
            k: 聚类数量 (2-20)
            max_iter: 最大迭代次数 (10-1000)
            color_space: 颜色空间 ('RGB', 'LAB', 'HSV')
            spatial_weight: 空间信息权重 (0.0-1.0)
            random_state: 随机种子
            
        Returns:
            分割结果字典
        """
        try:
            # 参数验证
            self._validate_parameters(k, max_iter, color_space, spatial_weight)
            
            start_time = time.time()
            
            # 预处理图像
            processed_image = self._preprocess_image(image, color_space)
            
            # 准备特征向量
            features = self._prepare_features(processed_image, spatial_weight)
            
            # 执行K-Means聚类
            labels, centers = self._perform_clustering(features, k, max_iter, random_state)
            
            # 生成分割结果
            segmented_image = self._generate_segmented_image(labels, centers, image.shape)
            
            # 后处理
            segmented_image = self._post_process(segmented_image)
            
            execution_time = time.time() - start_time
            
            # 创建结果对象
            result = SegmentationResult(
                segmented_image=segmented_image,
                num_segments=k,
                algorithm="K-Means",
                parameters={
                    'k': k,
                    'max_iter': max_iter,
                    'color_space': color_space,
                    'spatial_weight': spatial_weight,
                    'random_state': random_state
                },
                execution_time=execution_time,
                image_shape=image.shape
            )
            
            self.logger.log_algorithm_result("K-Means", k, execution_time, True)
            
            return {
                'segmented_image': segmented_image,
                'num_segments': k,
                'labels': labels.reshape(image.shape[:2]),
                'centers': centers,
                'execution_time': execution_time,
                'algorithm': 'K-Means',
                'parameters': result.parameters,
                'result_object': result
            }
            
        except Exception as e:
            self.logger.error("K-Means分割失败", exception=e)
            raise AlgorithmError("K-Means", str(e), {
                'k': k, 'max_iter': max_iter, 'color_space': color_space
            })
    
    def _validate_parameters(self, k: int, max_iter: int, color_space: str, spatial_weight: float):
        """验证参数"""
        if not (2 <= k <= 20):
            raise ParameterError("k", k, "2到20之间")
        
        if not (10 <= max_iter <= 1000):
            raise ParameterError("max_iter", max_iter, "10到1000之间")
        
        if color_space not in ['RGB', 'LAB', 'HSV']:
            raise ParameterError("color_space", color_space, "RGB, LAB, 或 HSV")
        
        if not (0.0 <= spatial_weight <= 1.0):
            raise ParameterError("spatial_weight", spatial_weight, "0.0到1.0之间")
    
    def _preprocess_image(self, image: np.ndarray, color_space: str) -> np.ndarray:
        """预处理图像"""
        if color_space == 'LAB':
            # 转换到LAB颜色空间
            processed = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        elif color_space == 'HSV':
            # 转换到HSV颜色空间
            processed = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        else:
            # 保持RGB
            processed = image.copy()
        
        # 归一化到0-1范围
        processed = processed.astype(np.float32) / 255.0
        
        return processed
    
    def _prepare_features(self, image: np.ndarray, spatial_weight: float) -> np.ndarray:
        """准备特征向量"""
        h, w, c = image.shape
        
        # 颜色特征
        color_features = image.reshape(-1, c)
        
        if spatial_weight > 0:
            # 添加空间特征
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            
            # 归一化空间坐标
            x_coords = x_coords.astype(np.float32) / w
            y_coords = y_coords.astype(np.float32) / h
            
            spatial_features = np.column_stack([
                x_coords.ravel(),
                y_coords.ravel()
            ])
            
            # 组合颜色和空间特征
            features = np.column_stack([
                color_features,
                spatial_features * spatial_weight
            ])
        else:
            features = color_features
        
        return features
    
    def _perform_clustering(self, features: np.ndarray, k: int, 
                          max_iter: int, random_state: int) -> Tuple[np.ndarray, np.ndarray]:
        """执行K-Means聚类"""
        kmeans = KMeans(
            n_clusters=k,
            max_iter=max_iter,
            random_state=random_state,
            n_init=10
        )
        
        labels = kmeans.fit_predict(features)
        centers = kmeans.cluster_centers_
        
        return labels, centers
    
    def _generate_segmented_image(self, labels: np.ndarray, centers: np.ndarray, 
                                image_shape: Tuple[int, int, int]) -> np.ndarray:
        """生成分割图像"""
        h, w, c = image_shape
        
        # 只使用颜色部分的聚类中心
        color_centers = centers[:, :3]
        
        # 将标签映射到颜色
        segmented = color_centers[labels]
        segmented = segmented.reshape(h, w, c)
        
        # 转换回0-255范围
        segmented = (segmented * 255).astype(np.uint8)
        
        return segmented
    
    def _post_process(self, image: np.ndarray) -> np.ndarray:
        """后处理"""
        # 可选的形态学操作
        kernel = np.ones((3, 3), np.uint8)
        
        # 开运算去除噪声
        processed = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        
        # 闭运算填充空洞
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        return processed


class GMMSegmentation(LoggerMixin):
    """高斯混合模型分割算法"""
    
    def __init__(self):
        super().__init__()
        self.algorithm_name = "GMM"
        self.logger.info("GMM分割算法初始化")
    
    @log_performance("GMM分割")
    def segment(self, image: np.ndarray,
                n_components: int = 5,
                covariance_type: str = 'full',
                max_iter: int = 100,
                color_space: str = 'RGB',
                random_state: int = 42,
                **kwargs) -> Dict[str, Any]:
        """
        执行高斯混合模型分割
        
        Args:
            image: 输入图像
            n_components: 高斯分量数量
            covariance_type: 协方差类型 ('full', 'tied', 'diag', 'spherical')
            max_iter: 最大迭代次数
            color_space: 颜色空间
            random_state: 随机种子
            
        Returns:
            分割结果字典
        """
        try:
            # 参数验证
            self._validate_parameters(n_components, covariance_type, max_iter, color_space)
            
            start_time = time.time()
            
            # 预处理图像
            processed_image = self._preprocess_image(image, color_space)
            
            # 准备特征
            features = processed_image.reshape(-1, processed_image.shape[2])
            
            # 执行GMM聚类
            labels, means = self._perform_gmm_clustering(
                features, n_components, covariance_type, max_iter, random_state
            )
            
            # 生成分割结果
            segmented_image = self._generate_segmented_image(labels, means, image.shape)
            
            execution_time = time.time() - start_time
            
            # 创建结果对象
            result = SegmentationResult(
                segmented_image=segmented_image,
                num_segments=n_components,
                algorithm="GMM",
                parameters={
                    'n_components': n_components,
                    'covariance_type': covariance_type,
                    'max_iter': max_iter,
                    'color_space': color_space,
                    'random_state': random_state
                },
                execution_time=execution_time,
                image_shape=image.shape
            )
            
            self.logger.log_algorithm_result("GMM", n_components, execution_time, True)
            
            return {
                'segmented_image': segmented_image,
                'num_segments': n_components,
                'labels': labels.reshape(image.shape[:2]),
                'means': means,
                'execution_time': execution_time,
                'algorithm': 'GMM',
                'parameters': result.parameters,
                'result_object': result
            }
            
        except Exception as e:
            self.logger.error("GMM分割失败", exception=e)
            raise AlgorithmError("GMM", str(e), {
                'n_components': n_components, 'covariance_type': covariance_type
            })
    
    def _validate_parameters(self, n_components: int, covariance_type: str, 
                           max_iter: int, color_space: str):
        """验证参数"""
        if not (2 <= n_components <= 20):
            raise ParameterError("n_components", n_components, "2到20之间")
        
        if covariance_type not in ['full', 'tied', 'diag', 'spherical']:
            raise ParameterError("covariance_type", covariance_type, 
                               "full, tied, diag, 或 spherical")
        
        if not (10 <= max_iter <= 1000):
            raise ParameterError("max_iter", max_iter, "10到1000之间")
        
        if color_space not in ['RGB', 'LAB', 'HSV']:
            raise ParameterError("color_space", color_space, "RGB, LAB, 或 HSV")
    
    def _preprocess_image(self, image: np.ndarray, color_space: str) -> np.ndarray:
        """预处理图像"""
        if color_space == 'LAB':
            processed = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        elif color_space == 'HSV':
            processed = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        else:
            processed = image.copy()
        
        processed = processed.astype(np.float32) / 255.0
        return processed
    
    def _perform_gmm_clustering(self, features: np.ndarray, n_components: int,
                              covariance_type: str, max_iter: int, 
                              random_state: int) -> Tuple[np.ndarray, np.ndarray]:
        """执行GMM聚类"""
        gmm = GaussianMixture(
            n_components=n_components,
            covariance_type=covariance_type,
            max_iter=max_iter,
            random_state=random_state
        )
        
        labels = gmm.fit_predict(features)
        means = gmm.means_
        
        return labels, means
    
    def _generate_segmented_image(self, labels: np.ndarray, means: np.ndarray,
                                image_shape: Tuple[int, int, int]) -> np.ndarray:
        """生成分割图像"""
        h, w, c = image_shape
        
        # 将标签映射到均值颜色
        segmented = means[labels]
        segmented = segmented.reshape(h, w, c)
        
        # 转换回0-255范围
        segmented = (segmented * 255).astype(np.uint8)
        
        return segmented


def get_available_algorithms():
    """获取可用的聚类分割算法"""
    return {
        'K-Means': KMeansSegmentation,
        'GMM': GMMSegmentation
    }
