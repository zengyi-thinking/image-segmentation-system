"""
分割质量评估指标
实现各种图像分割质量评估方法
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import time
import psutil
import os


class SegmentationMetrics:
    """分割质量评估指标计算器"""
    
    def __init__(self):
        self.metrics_cache = {}
    
    def compute_all_metrics(self, 
                           original_image: np.ndarray,
                           label_map: np.ndarray,
                           ground_truth: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        计算所有评估指标
        
        Args:
            original_image: 原始图像
            label_map: 分割标签图
            ground_truth: 真实标签图（可选）
            
        Returns:
            评估指标字典
        """
        metrics = {}
        
        # 无监督评估指标
        metrics.update(self.compute_unsupervised_metrics(original_image, label_map))
        
        # 如果有真实标签，计算监督评估指标
        if ground_truth is not None:
            metrics.update(self.compute_supervised_metrics(label_map, ground_truth))
        
        return metrics
    
    def compute_unsupervised_metrics(self, 
                                   original_image: np.ndarray,
                                   label_map: np.ndarray) -> Dict[str, float]:
        """
        计算无监督评估指标
        
        Args:
            original_image: 原始图像
            label_map: 分割标签图
            
        Returns:
            无监督评估指标
        """
        metrics = {}
        
        # 区域内方差（越小越好）
        metrics['intra_region_variance'] = self.compute_intra_region_variance(
            original_image, label_map
        )
        
        # 区域间对比度（越大越好）
        metrics['inter_region_contrast'] = self.compute_inter_region_contrast(
            original_image, label_map
        )
        
        # 边界准确性
        metrics['boundary_recall'] = self.compute_boundary_recall(
            original_image, label_map
        )
        
        # 分割一致性
        metrics['segmentation_consistency'] = self.compute_segmentation_consistency(
            original_image, label_map
        )
        
        # 区域紧凑性
        metrics['region_compactness'] = self.compute_region_compactness(label_map)
        
        # 分割均匀性
        metrics['segmentation_uniformity'] = self.compute_segmentation_uniformity(label_map)
        
        return metrics
    
    def compute_supervised_metrics(self, 
                                 predicted_labels: np.ndarray,
                                 ground_truth: np.ndarray) -> Dict[str, float]:
        """
        计算监督评估指标
        
        Args:
            predicted_labels: 预测标签图
            ground_truth: 真实标签图
            
        Returns:
            监督评估指标
        """
        metrics = {}
        
        # 展平标签图
        pred_flat = predicted_labels.flatten()
        gt_flat = ground_truth.flatten()
        
        # 调整兰德指数（ARI）
        metrics['adjusted_rand_index'] = adjusted_rand_score(gt_flat, pred_flat)
        
        # 标准化互信息（NMI）
        metrics['normalized_mutual_info'] = normalized_mutual_info_score(gt_flat, pred_flat)
        
        # 像素准确率
        metrics['pixel_accuracy'] = self.compute_pixel_accuracy(predicted_labels, ground_truth)
        
        # IoU（交并比）
        metrics['mean_iou'] = self.compute_mean_iou(predicted_labels, ground_truth)
        
        # F1分数
        metrics['f1_score'] = self.compute_f1_score(predicted_labels, ground_truth)

        # Dice系数
        metrics['dice_coefficient'] = self.compute_dice_coefficient(predicted_labels, ground_truth)

        # Jaccard指数（与IoU相同，但单独计算以确保一致性）
        metrics['jaccard_index'] = self.compute_jaccard_index(predicted_labels, ground_truth)

        return metrics
    
    def compute_intra_region_variance(self, 
                                    image: np.ndarray, 
                                    label_map: np.ndarray) -> float:
        """计算区域内方差"""
        total_variance = 0.0
        total_pixels = 0
        
        unique_labels = np.unique(label_map)
        
        for label in unique_labels:
            mask = label_map == label
            region_pixels = image[mask]
            
            if len(region_pixels) > 1:
                # 计算每个颜色通道的方差
                if len(region_pixels.shape) == 2:  # 彩色图像
                    variance = np.mean([np.var(region_pixels[:, i]) for i in range(region_pixels.shape[1])])
                else:  # 灰度图像
                    variance = np.var(region_pixels)
                
                total_variance += variance * len(region_pixels)
                total_pixels += len(region_pixels)
        
        return total_variance / total_pixels if total_pixels > 0 else 0.0
    
    def compute_inter_region_contrast(self, 
                                    image: np.ndarray, 
                                    label_map: np.ndarray) -> float:
        """计算区域间对比度"""
        # 计算边界
        boundaries = self._find_boundaries(label_map)
        
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
                if (0 <= nr < label_map.shape[0] and 
                    0 <= nc < label_map.shape[1]):
                    
                    if label_map[row, col] != label_map[nr, nc]:
                        # 计算颜色差异
                        if len(image.shape) == 3:
                            color_diff = np.linalg.norm(
                                image[row, col].astype(float) - 
                                image[nr, nc].astype(float)
                            )
                        else:
                            color_diff = abs(float(image[row, col]) - float(image[nr, nc]))
                        
                        total_contrast += color_diff
                        count += 1
        
        return total_contrast / count if count > 0 else 0.0
    
    def compute_boundary_recall(self, 
                              image: np.ndarray, 
                              label_map: np.ndarray,
                              threshold: float = 10.0) -> float:
        """计算边界召回率"""
        # 计算图像梯度（真实边界）
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 使用Canny边缘检测
        true_edges = cv2.Canny(gray, 50, 150)
        
        # 计算分割边界
        seg_boundaries = self._find_boundaries(label_map)
        
        # 计算召回率
        true_edge_pixels = np.sum(true_edges > 0)
        if true_edge_pixels == 0:
            return 0.0
        
        # 在真实边界附近查找分割边界
        kernel = np.ones((3, 3), np.uint8)
        dilated_seg_boundaries = cv2.dilate(seg_boundaries.astype(np.uint8), kernel, iterations=1)
        
        recalled_edges = np.sum((true_edges > 0) & (dilated_seg_boundaries > 0))
        
        return recalled_edges / true_edge_pixels
    
    def compute_segmentation_consistency(self, 
                                       image: np.ndarray, 
                                       label_map: np.ndarray) -> float:
        """计算分割一致性"""
        total_consistency = 0.0
        total_pixels = 0
        
        unique_labels = np.unique(label_map)
        
        for label in unique_labels:
            mask = label_map == label
            region_pixels = image[mask]
            
            if len(region_pixels) > 1:
                # 计算颜色标准差的倒数作为一致性度量
                if len(region_pixels.shape) == 2:  # 彩色图像
                    std_dev = np.mean([np.std(region_pixels[:, i]) for i in range(region_pixels.shape[1])])
                else:  # 灰度图像
                    std_dev = np.std(region_pixels)
                
                consistency = 1.0 / (1.0 + std_dev)
                total_consistency += consistency * len(region_pixels)
                total_pixels += len(region_pixels)
        
        return total_consistency / total_pixels if total_pixels > 0 else 0.0
    
    def compute_region_compactness(self, label_map: np.ndarray) -> float:
        """计算区域紧凑性"""
        total_compactness = 0.0
        total_area = 0
        
        unique_labels = np.unique(label_map)
        
        for label in unique_labels:
            mask = label_map == label
            area = np.sum(mask)
            
            if area > 0:
                # 计算周长
                perimeter = self._compute_perimeter(mask)
                
                # 紧凑性 = 4π * 面积 / 周长²
                if perimeter > 0:
                    compactness = (4 * np.pi * area) / (perimeter ** 2)
                else:
                    compactness = 1.0
                
                total_compactness += compactness * area
                total_area += area
        
        return total_compactness / total_area if total_area > 0 else 0.0
    
    def compute_segmentation_uniformity(self, label_map: np.ndarray) -> float:
        """计算分割均匀性"""
        unique_labels, counts = np.unique(label_map, return_counts=True)
        
        if len(counts) <= 1:
            return 1.0
        
        # 计算区域大小的变异系数
        mean_size = np.mean(counts)
        std_size = np.std(counts)
        
        # 均匀性 = 1 - 变异系数
        coefficient_of_variation = std_size / mean_size if mean_size > 0 else 0
        uniformity = 1.0 / (1.0 + coefficient_of_variation)
        
        return uniformity
    
    def compute_pixel_accuracy(self, 
                             predicted: np.ndarray, 
                             ground_truth: np.ndarray) -> float:
        """计算像素准确率"""
        # 简化实现：计算标签匹配的像素比例
        # 注意：这里假设标签已经对齐
        correct_pixels = np.sum(predicted == ground_truth)
        total_pixels = predicted.size
        
        return correct_pixels / total_pixels
    
    def compute_mean_iou(self, 
                        predicted: np.ndarray, 
                        ground_truth: np.ndarray) -> float:
        """计算平均IoU"""
        unique_labels = np.unique(np.concatenate([predicted.flatten(), ground_truth.flatten()]))
        
        ious = []
        for label in unique_labels:
            pred_mask = predicted == label
            gt_mask = ground_truth == label
            
            intersection = np.sum(pred_mask & gt_mask)
            union = np.sum(pred_mask | gt_mask)
            
            if union > 0:
                iou = intersection / union
                ious.append(iou)
        
        return np.mean(ious) if ious else 0.0
    
    def compute_f1_score(self, 
                        predicted: np.ndarray, 
                        ground_truth: np.ndarray) -> float:
        """计算F1分数"""
        # 简化实现：基于像素级别的F1分数
        unique_labels = np.unique(ground_truth)
        
        f1_scores = []
        for label in unique_labels:
            pred_mask = predicted == label
            gt_mask = ground_truth == label
            
            tp = np.sum(pred_mask & gt_mask)
            fp = np.sum(pred_mask & ~gt_mask)
            fn = np.sum(~pred_mask & gt_mask)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
                f1_scores.append(f1)
        
        return np.mean(f1_scores) if f1_scores else 0.0

    def compute_dice_coefficient(self,
                               predicted: np.ndarray,
                               ground_truth: np.ndarray) -> float:
        """计算Dice系数"""
        unique_labels = np.unique(ground_truth)

        dice_scores = []
        for label in unique_labels:
            pred_mask = predicted == label
            gt_mask = ground_truth == label

            intersection = np.sum(pred_mask & gt_mask)
            total = np.sum(pred_mask) + np.sum(gt_mask)

            if total > 0:
                dice = (2.0 * intersection) / total
                dice_scores.append(dice)

        return np.mean(dice_scores) if dice_scores else 0.0

    def compute_jaccard_index(self,
                            predicted: np.ndarray,
                            ground_truth: np.ndarray) -> float:
        """计算Jaccard指数（与IoU相同）"""
        return self.compute_mean_iou(predicted, ground_truth)

    def _find_boundaries(self, label_map: np.ndarray) -> np.ndarray:
        """查找分割边界"""
        grad_x = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        boundaries = gradient_magnitude > 0
        
        return boundaries
    
    def _compute_perimeter(self, mask: np.ndarray) -> float:
        """计算区域周长"""
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
        boundary = mask.astype(np.uint8) - eroded
        
        return np.sum(boundary)


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.peak_memory = None
        
    def start_profiling(self):
        """开始性能分析"""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory
        
    def stop_profiling(self) -> Dict[str, float]:
        """停止性能分析并返回结果"""
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        execution_time = end_time - self.start_time if self.start_time else 0
        memory_used = end_memory - self.start_memory if self.start_memory else 0
        peak_memory_used = self.peak_memory - self.start_memory if self.start_memory else 0
        
        return {
            'execution_time': execution_time,
            'memory_used_mb': memory_used,
            'peak_memory_mb': peak_memory_used,
            'final_memory_mb': end_memory
        }
    
    def update_peak_memory(self):
        """更新峰值内存使用"""
        current_memory = self._get_memory_usage()
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # 转换为MB
