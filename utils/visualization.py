"""
可视化工具模块
提供分割结果的可视化功能
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Optional, Tuple, List
import random


class SegmentationVisualizer:
    """分割结果可视化器"""
    
    def __init__(self):
        self.color_map = None
        self._generate_color_map()
    
    def _generate_color_map(self, num_colors: int = 1000):
        """
        生成随机颜色映射
        
        Args:
            num_colors: 颜色数量
        """
        # 生成随机颜色
        colors = []
        for i in range(num_colors):
            # 使用HSV颜色空间生成更均匀分布的颜色
            hue = (i * 137.508) % 360  # 黄金角度分布
            saturation = 0.7 + 0.3 * random.random()
            value = 0.8 + 0.2 * random.random()
            
            # 转换为RGB
            rgb = mcolors.hsv_to_rgb([hue/360, saturation, value])
            colors.append([int(c * 255) for c in rgb])
        
        self.color_map = np.array(colors)
    
    def visualize_segments(self, 
                          original_image: np.ndarray,
                          label_map: np.ndarray,
                          alpha: float = 0.6) -> np.ndarray:
        """
        可视化分割区域
        
        Args:
            original_image: 原始图像
            label_map: 分割标签图
            alpha: 透明度混合系数
            
        Returns:
            可视化结果图像
        """
        height, width = label_map.shape
        colored_segments = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 为每个分割区域分配颜色
        unique_labels = np.unique(label_map)
        
        for label in unique_labels:
            if label < len(self.color_map):
                color = self.color_map[label]
            else:
                # 如果标签超出颜色映射范围，生成随机颜色
                color = [random.randint(0, 255) for _ in range(3)]
            
            mask = label_map == label
            colored_segments[mask] = color
        
        # 与原图混合
        result = cv2.addWeighted(original_image, 1-alpha, colored_segments, alpha, 0)
        
        return result
    
    def visualize_boundaries(self, 
                           original_image: np.ndarray,
                           label_map: np.ndarray,
                           boundary_color: Tuple[int, int, int] = (255, 0, 0),
                           thickness: int = 1) -> np.ndarray:
        """
        可视化分割边界
        
        Args:
            original_image: 原始图像
            label_map: 分割标签图
            boundary_color: 边界颜色 (R, G, B)
            thickness: 边界线粗细
            
        Returns:
            带边界的图像
        """
        result = original_image.copy()
        
        # 计算边界
        boundaries = self._find_boundaries(label_map)
        
        # 绘制边界
        result[boundaries] = boundary_color
        
        # 如果需要更粗的边界线
        if thickness > 1:
            kernel = np.ones((thickness, thickness), np.uint8)
            boundaries_thick = cv2.dilate(boundaries.astype(np.uint8), kernel, iterations=1)
            result[boundaries_thick.astype(bool)] = boundary_color
        
        return result
    
    def _find_boundaries(self, label_map: np.ndarray) -> np.ndarray:
        """
        查找分割边界
        
        Args:
            label_map: 分割标签图
            
        Returns:
            边界掩码
        """
        # 使用Sobel算子检测边界
        grad_x = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(label_map.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        
        # 计算梯度幅值
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 边界是梯度幅值大于0的位置
        boundaries = gradient_magnitude > 0
        
        return boundaries
    
    def create_comparison_view(self, 
                             original_image: np.ndarray,
                             segmentation_results: List[Tuple[str, np.ndarray]],
                             figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
        """
        创建多种分割结果的对比视图
        
        Args:
            original_image: 原始图像
            segmentation_results: 分割结果列表 [(名称, 标签图), ...]
            figsize: 图像大小
            
        Returns:
            matplotlib图形对象
        """
        num_results = len(segmentation_results)
        cols = min(3, num_results + 1)  # 最多3列
        rows = (num_results + 1 + cols - 1) // cols  # 向上取整
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        if rows == 1:
            axes = axes.reshape(1, -1)
        
        # 显示原始图像
        axes[0, 0].imshow(original_image)
        axes[0, 0].set_title('Original Image')
        axes[0, 0].axis('off')
        
        # 显示分割结果
        for i, (name, label_map) in enumerate(segmentation_results):
            row = (i + 1) // cols
            col = (i + 1) % cols
            
            # 可视化分割结果
            vis_result = self.visualize_segments(original_image, label_map)
            
            axes[row, col].imshow(vis_result)
            axes[row, col].set_title(f'{name}\n({len(np.unique(label_map))} segments)')
            axes[row, col].axis('off')
        
        # 隐藏多余的子图
        total_plots = num_results + 1
        for i in range(total_plots, rows * cols):
            row = i // cols
            col = i % cols
            axes[row, col].axis('off')
        
        plt.tight_layout()
        return fig
    
    def plot_segment_statistics(self, 
                              label_map: np.ndarray,
                              title: str = "Segment Statistics") -> plt.Figure:
        """
        绘制分割统计信息
        
        Args:
            label_map: 分割标签图
            title: 图表标题
            
        Returns:
            matplotlib图形对象
        """
        # 计算每个分割区域的大小
        unique_labels, counts = np.unique(label_map, return_counts=True)
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(title)
        
        # 分割区域大小分布
        axes[0, 0].hist(counts, bins=30, alpha=0.7, color='skyblue')
        axes[0, 0].set_xlabel('Segment Size (pixels)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Segment Size Distribution')
        
        # 分割区域大小排序
        sorted_counts = np.sort(counts)[::-1]
        axes[0, 1].plot(sorted_counts, marker='o', markersize=3)
        axes[0, 1].set_xlabel('Segment Rank')
        axes[0, 1].set_ylabel('Segment Size')
        axes[0, 1].set_title('Segment Sizes (Sorted)')
        axes[0, 1].set_yscale('log')
        
        # 累积分布
        cumulative = np.cumsum(sorted_counts) / np.sum(counts) * 100
        axes[1, 0].plot(cumulative)
        axes[1, 0].set_xlabel('Segment Rank')
        axes[1, 0].set_ylabel('Cumulative Percentage (%)')
        axes[1, 0].set_title('Cumulative Size Distribution')
        
        # 统计信息文本
        stats_text = f"""
        Total Segments: {len(unique_labels)}
        Mean Size: {np.mean(counts):.1f}
        Median Size: {np.median(counts):.1f}
        Std Size: {np.std(counts):.1f}
        Max Size: {np.max(counts)}
        Min Size: {np.min(counts)}
        """
        
        axes[1, 1].text(0.1, 0.5, stats_text, transform=axes[1, 1].transAxes,
                        fontsize=12, verticalalignment='center',
                        bbox=dict(boxstyle='round', facecolor='lightgray'))
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        return fig
    
    def create_overlay_visualization(self, 
                                   original_image: np.ndarray,
                                   label_map: np.ndarray,
                                   show_boundaries: bool = True,
                                   show_labels: bool = False) -> np.ndarray:
        """
        创建叠加可视化
        
        Args:
            original_image: 原始图像
            label_map: 分割标签图
            show_boundaries: 是否显示边界
            show_labels: 是否显示标签数字
            
        Returns:
            叠加可视化结果
        """
        result = original_image.copy()
        
        if show_boundaries:
            result = self.visualize_boundaries(result, label_map)
        
        if show_labels:
            # 在每个分割区域的中心显示标签
            unique_labels = np.unique(label_map)
            
            for label in unique_labels:
                mask = label_map == label
                if np.sum(mask) > 100:  # 只为足够大的区域显示标签
                    # 计算区域中心
                    coords = np.where(mask)
                    center_y = int(np.mean(coords[0]))
                    center_x = int(np.mean(coords[1]))
                    
                    # 绘制标签文本
                    cv2.putText(result, str(label), 
                              (center_x, center_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result
    
    def save_visualization(self, 
                         image: np.ndarray,
                         output_path: str,
                         dpi: int = 300) -> bool:
        """
        保存可视化结果
        
        Args:
            image: 要保存的图像
            output_path: 输出路径
            dpi: 分辨率
            
        Returns:
            是否保存成功
        """
        try:
            plt.figure(figsize=(10, 8))
            plt.imshow(image)
            plt.axis('off')
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
            plt.close()
            return True
        except Exception as e:
            print(f"保存可视化结果时发生错误: {e}")
            return False
