"""
分割结果数据结构
存储和管理图像分割的结果数据
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
from pathlib import Path


class SegmentationResult:
    """分割结果数据结构"""
    
    def __init__(self, 
                 label_map: np.ndarray,
                 original_image: Optional[np.ndarray] = None,
                 algorithm_name: str = "Unknown",
                 parameters: Optional[Dict] = None):
        """
        初始化分割结果
        
        Args:
            label_map: 分割标签图
            original_image: 原始图像
            algorithm_name: 算法名称
            parameters: 算法参数
        """
        self.label_map = label_map
        self.original_image = original_image
        self.algorithm_name = algorithm_name
        self.parameters = parameters or {}
        
        # 计算基本统计信息
        self._compute_basic_statistics()
        
        # 存储额外信息
        self.metadata = {}
        self.performance_metrics = {}
        self.quality_metrics = {}
        
    def _compute_basic_statistics(self):
        """计算基本统计信息"""
        unique_labels, counts = np.unique(self.label_map, return_counts=True)
        
        self.num_segments = len(unique_labels)
        self.segment_sizes = dict(zip(unique_labels, counts))
        self.total_pixels = self.label_map.size
        
        # 统计信息
        self.statistics = {
            'num_segments': self.num_segments,
            'total_pixels': self.total_pixels,
            'avg_segment_size': np.mean(counts),
            'max_segment_size': np.max(counts),
            'min_segment_size': np.min(counts),
            'std_segment_size': np.std(counts),
            'median_segment_size': np.median(counts)
        }
    
    def get_segment_mask(self, label: int) -> np.ndarray:
        """
        获取指定标签的分割掩码
        
        Args:
            label: 分割标签
            
        Returns:
            布尔掩码数组
        """
        return self.label_map == label
    
    def get_segment_pixels(self, label: int) -> List[Tuple[int, int]]:
        """
        获取指定分割区域的像素坐标
        
        Args:
            label: 分割标签
            
        Returns:
            像素坐标列表
        """
        mask = self.get_segment_mask(label)
        coords = np.where(mask)
        return list(zip(coords[0], coords[1]))
    
    def get_segment_bounding_box(self, label: int) -> Tuple[int, int, int, int]:
        """
        获取分割区域的边界框
        
        Args:
            label: 分割标签
            
        Returns:
            边界框 (min_row, min_col, max_row, max_col)
        """
        mask = self.get_segment_mask(label)
        coords = np.where(mask)
        
        if len(coords[0]) == 0:
            return (0, 0, 0, 0)
        
        min_row, max_row = np.min(coords[0]), np.max(coords[0])
        min_col, max_col = np.min(coords[1]), np.max(coords[1])
        
        return (min_row, min_col, max_row, max_col)
    
    def get_segment_centroid(self, label: int) -> Tuple[float, float]:
        """
        获取分割区域的质心
        
        Args:
            label: 分割标签
            
        Returns:
            质心坐标 (row, col)
        """
        mask = self.get_segment_mask(label)
        coords = np.where(mask)
        
        if len(coords[0]) == 0:
            return (0.0, 0.0)
        
        centroid_row = np.mean(coords[0])
        centroid_col = np.mean(coords[1])
        
        return (centroid_row, centroid_col)
    
    def compute_segment_features(self, label: int) -> Dict[str, Any]:
        """
        计算分割区域的特征
        
        Args:
            label: 分割标签
            
        Returns:
            特征字典
        """
        mask = self.get_segment_mask(label)
        
        # 基本几何特征
        area = np.sum(mask)
        bbox = self.get_segment_bounding_box(label)
        centroid = self.get_segment_centroid(label)
        
        # 形状特征
        perimeter = self._compute_perimeter(mask)
        compactness = (perimeter ** 2) / (4 * np.pi * area) if area > 0 else 0
        
        features = {
            'area': area,
            'perimeter': perimeter,
            'compactness': compactness,
            'bounding_box': bbox,
            'centroid': centroid,
            'aspect_ratio': (bbox[2] - bbox[0]) / (bbox[3] - bbox[1]) if bbox[3] > bbox[1] else 1.0
        }
        
        # 如果有原始图像，计算颜色特征
        if self.original_image is not None:
            color_features = self._compute_color_features(mask)
            features.update(color_features)
        
        return features
    
    def _compute_perimeter(self, mask: np.ndarray) -> float:
        """计算区域周长"""
        import cv2
        
        # 使用形态学操作计算边界
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
        boundary = mask.astype(np.uint8) - eroded
        
        return np.sum(boundary)
    
    def _compute_color_features(self, mask: np.ndarray) -> Dict[str, Any]:
        """计算颜色特征"""
        if self.original_image is None:
            return {}
        
        # 提取区域内的像素值
        region_pixels = self.original_image[mask]
        
        if len(region_pixels) == 0:
            return {}
        
        # 计算颜色统计
        color_features = {
            'mean_color': np.mean(region_pixels, axis=0),
            'std_color': np.std(region_pixels, axis=0),
            'min_color': np.min(region_pixels, axis=0),
            'max_color': np.max(region_pixels, axis=0)
        }
        
        return color_features
    
    def filter_small_segments(self, min_size: int) -> 'SegmentationResult':
        """
        过滤小分割区域
        
        Args:
            min_size: 最小区域大小
            
        Returns:
            过滤后的分割结果
        """
        filtered_label_map = self.label_map.copy()
        
        # 找到小区域
        for label, size in self.segment_sizes.items():
            if size < min_size:
                # 将小区域标记为背景（标签0）
                filtered_label_map[self.label_map == label] = 0
        
        # 重新标记连续的标签
        unique_labels = np.unique(filtered_label_map)
        new_label_map = np.zeros_like(filtered_label_map)
        
        for new_label, old_label in enumerate(unique_labels):
            new_label_map[filtered_label_map == old_label] = new_label
        
        # 创建新的分割结果
        filtered_result = SegmentationResult(
            new_label_map,
            self.original_image,
            self.algorithm_name + "_filtered",
            self.parameters.copy()
        )
        
        return filtered_result
    
    def merge_segments(self, labels_to_merge: List[int], new_label: int) -> 'SegmentationResult':
        """
        合并指定的分割区域
        
        Args:
            labels_to_merge: 要合并的标签列表
            new_label: 新标签
            
        Returns:
            合并后的分割结果
        """
        merged_label_map = self.label_map.copy()
        
        for label in labels_to_merge:
            merged_label_map[self.label_map == label] = new_label
        
        merged_result = SegmentationResult(
            merged_label_map,
            self.original_image,
            self.algorithm_name + "_merged",
            self.parameters.copy()
        )
        
        return merged_result
    
    def compute_quality_metrics(self) -> Dict[str, float]:
        """
        计算分割质量指标
        
        Returns:
            质量指标字典
        """
        if self.original_image is None:
            return {}
        
        metrics = {}
        
        # 区域内方差（越小越好）
        intra_variance = self._compute_intra_region_variance()
        metrics['intra_region_variance'] = intra_variance
        
        # 区域间对比度（越大越好）
        inter_contrast = self._compute_inter_region_contrast()
        metrics['inter_region_contrast'] = inter_contrast
        
        # 分割一致性
        consistency = self._compute_segmentation_consistency()
        metrics['segmentation_consistency'] = consistency
        
        self.quality_metrics = metrics
        return metrics
    
    def _compute_intra_region_variance(self) -> float:
        """计算区域内方差"""
        total_variance = 0.0
        total_pixels = 0
        
        for label in np.unique(self.label_map):
            mask = self.get_segment_mask(label)
            region_pixels = self.original_image[mask]
            
            if len(region_pixels) > 1:
                variance = np.var(region_pixels)
                total_variance += variance * len(region_pixels)
                total_pixels += len(region_pixels)
        
        return total_variance / total_pixels if total_pixels > 0 else 0.0
    
    def _compute_inter_region_contrast(self) -> float:
        """计算区域间对比度"""
        # 简化实现：计算相邻区域间的平均颜色差异
        import cv2
        
        # 计算边界
        grad_x = cv2.Sobel(self.label_map.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(self.label_map.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        boundaries = (np.abs(grad_x) + np.abs(grad_y)) > 0
        
        if np.sum(boundaries) == 0:
            return 0.0
        
        # 计算边界处的颜色差异
        boundary_coords = np.where(boundaries)
        total_contrast = 0.0
        count = 0
        
        for i in range(len(boundary_coords[0])):
            row, col = boundary_coords[0][i], boundary_coords[1][i]
            
            # 检查相邻像素
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.label_map.shape[0] and 
                    0 <= nc < self.label_map.shape[1]):
                    
                    if self.label_map[row, col] != self.label_map[nr, nc]:
                        # 计算颜色差异
                        color_diff = np.linalg.norm(
                            self.original_image[row, col].astype(float) - 
                            self.original_image[nr, nc].astype(float)
                        )
                        total_contrast += color_diff
                        count += 1
        
        return total_contrast / count if count > 0 else 0.0
    
    def _compute_segmentation_consistency(self) -> float:
        """计算分割一致性"""
        # 简化实现：计算每个区域内颜色的一致性
        total_consistency = 0.0
        
        for label in np.unique(self.label_map):
            mask = self.get_segment_mask(label)
            region_pixels = self.original_image[mask]
            
            if len(region_pixels) > 1:
                # 计算颜色标准差的倒数作为一致性度量
                std_dev = np.mean(np.std(region_pixels, axis=0))
                consistency = 1.0 / (1.0 + std_dev)
                total_consistency += consistency * len(region_pixels)
        
        return total_consistency / self.total_pixels
    
    def save_to_file(self, filepath: str):
        """
        保存分割结果到文件
        
        Args:
            filepath: 文件路径
        """
        filepath = Path(filepath)
        
        # 保存标签图
        np.save(filepath.with_suffix('.npy'), self.label_map)
        
        # 保存元数据
        metadata = {
            'algorithm_name': self.algorithm_name,
            'parameters': self.parameters,
            'statistics': self.statistics,
            'quality_metrics': self.quality_metrics,
            'performance_metrics': self.performance_metrics,
            'metadata': self.metadata
        }
        
        with open(filepath.with_suffix('.json'), 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SegmentationResult':
        """
        从文件加载分割结果
        
        Args:
            filepath: 文件路径
            
        Returns:
            分割结果对象
        """
        filepath = Path(filepath)
        
        # 加载标签图
        label_map = np.load(filepath.with_suffix('.npy'))
        
        # 加载元数据
        with open(filepath.with_suffix('.json'), 'r') as f:
            metadata = json.load(f)
        
        # 创建结果对象
        result = cls(
            label_map,
            algorithm_name=metadata.get('algorithm_name', 'Unknown'),
            parameters=metadata.get('parameters', {})
        )
        
        # 恢复其他信息
        result.quality_metrics = metadata.get('quality_metrics', {})
        result.performance_metrics = metadata.get('performance_metrics', {})
        result.metadata = metadata.get('metadata', {})
        
        return result
