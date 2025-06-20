"""
边权重计算模块
实现像素间边权重的计算方法，支持多种相似性度量
"""

import numpy as np
from typing import Tuple, Union
import cv2


class EdgeWeightCalculator:
    """边权重计算器"""
    
    def __init__(self, alpha: float = 1.0, beta: float = 0.1, color_space: str = 'RGB'):
        """
        初始化边权重计算器
        
        Args:
            alpha: 颜色差异权重系数
            beta: 空间距离权重系数  
            color_space: 颜色空间 ('RGB', 'HSV', 'LAB')
        """
        self.alpha = alpha
        self.beta = beta
        self.color_space = color_space
        
    def calculate_weight(self, 
                        pixel1: Tuple[int, int], 
                        pixel2: Tuple[int, int], 
                        image: np.ndarray) -> float:
        """
        计算两个像素间的边权重
        
        Args:
            pixel1: 第一个像素坐标 (row, col)
            pixel2: 第二个像素坐标 (row, col)
            image: 输入图像
            
        Returns:
            边权重值
        """
        # 获取像素颜色值
        color1 = image[pixel1[0], pixel1[1]]
        color2 = image[pixel2[0], pixel2[1]]
        
        # 计算颜色差异
        color_diff = self._color_difference(color1, color2)
        
        # 计算空间距离
        spatial_dist = self._spatial_distance(pixel1, pixel2)
        
        # 组合权重
        weight = self.alpha * color_diff + self.beta * spatial_dist
        
        return weight
    
    def _color_difference(self, color1: np.ndarray, color2: np.ndarray) -> float:
        """
        计算颜色差异
        
        Args:
            color1: 第一个像素的颜色值
            color2: 第二个像素的颜色值
            
        Returns:
            颜色差异值
        """
        if self.color_space == 'RGB':
            return self._rgb_difference(color1, color2)
        elif self.color_space == 'HSV':
            return self._hsv_difference(color1, color2)
        elif self.color_space == 'LAB':
            return self._lab_difference(color1, color2)
        else:
            raise ValueError(f"不支持的颜色空间: {self.color_space}")
    
    def _rgb_difference(self, color1: np.ndarray, color2: np.ndarray) -> float:
        """RGB颜色空间差异"""
        return np.linalg.norm(color1.astype(float) - color2.astype(float))
    
    def _hsv_difference(self, color1: np.ndarray, color2: np.ndarray) -> float:
        """HSV颜色空间差异"""
        # 转换为HSV
        hsv1 = cv2.cvtColor(color1.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]
        hsv2 = cv2.cvtColor(color2.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]
        
        # HSV差异计算（考虑色调的周期性）
        h_diff = min(abs(hsv1[0] - hsv2[0]), 180 - abs(hsv1[0] - hsv2[0]))
        s_diff = abs(hsv1[1] - hsv2[1])
        v_diff = abs(hsv1[2] - hsv2[2])
        
        return np.sqrt(h_diff**2 + s_diff**2 + v_diff**2)
    
    def _lab_difference(self, color1: np.ndarray, color2: np.ndarray) -> float:
        """LAB颜色空间差异（Delta E）"""
        # 转换为LAB
        lab1 = cv2.cvtColor(color1.reshape(1, 1, 3), cv2.COLOR_RGB2LAB)[0, 0]
        lab2 = cv2.cvtColor(color2.reshape(1, 1, 3), cv2.COLOR_RGB2LAB)[0, 0]
        
        # Delta E计算
        return np.linalg.norm(lab1.astype(float) - lab2.astype(float))
    
    def _spatial_distance(self, pixel1: Tuple[int, int], pixel2: Tuple[int, int]) -> float:
        """
        计算空间距离
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            
        Returns:
            欧几里得距离
        """
        return np.sqrt((pixel1[0] - pixel2[0])**2 + (pixel1[1] - pixel2[1])**2)
    
    def calculate_gradient_weight(self, 
                                 pixel1: Tuple[int, int], 
                                 pixel2: Tuple[int, int], 
                                 gradient: np.ndarray) -> float:
        """
        基于梯度的权重计算
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            gradient: 梯度图像
            
        Returns:
            基于梯度的权重
        """
        grad1 = gradient[pixel1[0], pixel1[1]]
        grad2 = gradient[pixel2[0], pixel2[1]]
        
        # 使用梯度幅值的平均值作为权重
        return (grad1 + grad2) / 2.0
    
    def calculate_texture_weight(self, 
                               pixel1: Tuple[int, int], 
                               pixel2: Tuple[int, int], 
                               image: np.ndarray, 
                               window_size: int = 3) -> float:
        """
        基于纹理的权重计算
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            image: 输入图像
            window_size: 纹理窗口大小
            
        Returns:
            基于纹理的权重
        """
        # 提取局部纹理特征
        texture1 = self._extract_texture_feature(pixel1, image, window_size)
        texture2 = self._extract_texture_feature(pixel2, image, window_size)
        
        # 计算纹理差异
        return np.linalg.norm(texture1 - texture2)
    
    def _extract_texture_feature(self, 
                               pixel: Tuple[int, int], 
                               image: np.ndarray, 
                               window_size: int) -> np.ndarray:
        """
        提取局部纹理特征
        
        Args:
            pixel: 像素坐标
            image: 输入图像
            window_size: 窗口大小
            
        Returns:
            纹理特征向量
        """
        row, col = pixel
        half_size = window_size // 2
        
        # 确保窗口在图像范围内
        row_start = max(0, row - half_size)
        row_end = min(image.shape[0], row + half_size + 1)
        col_start = max(0, col - half_size)
        col_end = min(image.shape[1], col + half_size + 1)
        
        # 提取局部窗口
        window = image[row_start:row_end, col_start:col_end]
        
        # 计算简单的纹理特征（方差、均值等）
        if len(window.shape) == 3:
            window_gray = cv2.cvtColor(window, cv2.COLOR_RGB2GRAY)
        else:
            window_gray = window
            
        features = np.array([
            np.mean(window_gray),      # 均值
            np.std(window_gray),       # 标准差
            np.max(window_gray) - np.min(window_gray)  # 动态范围
        ])
        
        return features


class AdaptiveWeightCalculator(EdgeWeightCalculator):
    """自适应权重计算器"""
    
    def __init__(self, alpha: float = 1.0, beta: float = 0.1, 
                 color_space: str = 'RGB', adaptive: bool = True):
        super().__init__(alpha, beta, color_space)
        self.adaptive = adaptive
        
    def calculate_adaptive_weight(self, 
                                pixel1: Tuple[int, int], 
                                pixel2: Tuple[int, int], 
                                image: np.ndarray,
                                local_variance: np.ndarray) -> float:
        """
        自适应权重计算，根据局部方差调整权重
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            image: 输入图像
            local_variance: 局部方差图
            
        Returns:
            自适应权重值
        """
        base_weight = self.calculate_weight(pixel1, pixel2, image)
        
        if not self.adaptive:
            return base_weight
            
        # 获取局部方差
        var1 = local_variance[pixel1[0], pixel1[1]]
        var2 = local_variance[pixel2[0], pixel2[1]]
        avg_variance = (var1 + var2) / 2.0
        
        # 根据方差调整权重（高方差区域权重增加）
        variance_factor = 1.0 + avg_variance / 255.0
        
        return base_weight * variance_factor
