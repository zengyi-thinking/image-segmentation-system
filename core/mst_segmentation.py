"""
基于最小生成树的图像分割算法实现
使用Kruskal算法构建MST，然后通过阈值分割形成区域
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import heapq
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_structures.union_find import SegmentationUnionFind, UnionFind
from .graph_builder import PixelGraphBuilder
from .edge_weights import EdgeWeightCalculator


class MSTSegmentation:
    """基于最小生成树的图像分割器"""
    
    def __init__(self, 
                 connectivity: int = 4,
                 weight_calculator: Optional[EdgeWeightCalculator] = None,
                 min_segment_size: int = 50):
        """
        初始化MST分割器
        
        Args:
            connectivity: 像素连接性 (4 或 8)
            weight_calculator: 边权重计算器
            min_segment_size: 最小分割区域大小
        """
        self.connectivity = connectivity
        self.weight_calculator = weight_calculator or EdgeWeightCalculator()
        self.min_segment_size = min_segment_size
        self.graph_builder = PixelGraphBuilder(connectivity, weight_calculator)
        
    def segment(self,
                image: np.ndarray,
                threshold: float = None,
                adaptive_threshold: bool = True,
                progress_callback=None) -> Dict:
        """
        执行MST图像分割

        Args:
            image: 输入图像 (H, W, C)
            threshold: 分割阈值，None表示自动计算
            adaptive_threshold: 是否使用自适应阈值
            progress_callback: 进度回调函数

        Returns:
            分割结果字典

        Raises:
            ValueError: 输入图像无效
            RuntimeError: 分割过程中发生错误
        """
        # 输入验证
        if image is None or image.size == 0:
            raise ValueError("输入图像为空或无效")

        if len(image.shape) < 2:
            raise ValueError("输入图像维度不足")

        if len(image.shape) == 2:
            # 灰度图像转为RGB
            image = np.stack([image] * 3, axis=-1)

        height, width = image.shape[:2]

        try:
            # 1. 构建像素图
            if progress_callback:
                progress_callback("构建像素图...", 0.1)
            graph = self.graph_builder.build_graph(image)

            # 2. 构建最小生成树
            if progress_callback:
                progress_callback("构建最小生成树...", 0.3)
            mst_edges, mst_weights = self._build_mst(graph)

            # 3. 计算分割阈值
            if threshold is None:
                threshold = self._calculate_threshold(mst_weights, adaptive_threshold)

            # 验证阈值
            if threshold <= 0:
                threshold = np.median(mst_weights) if mst_weights else 1.0

            # 4. 基于阈值进行分割
            if progress_callback:
                progress_callback(f"使用阈值 {threshold:.2f} 进行分割...", 0.6)
            segmentation_result = self._threshold_segmentation(
                graph, mst_edges, mst_weights, threshold, height, width
            )

            # 5. 后处理：合并小区域
            if progress_callback:
                progress_callback("后处理：合并小区域...", 0.8)
            self._post_process_segments(segmentation_result, graph)

            if progress_callback:
                progress_callback("分割完成", 1.0)

            return segmentation_result

        except Exception as e:
            error_msg = f"分割过程中发生错误: {str(e)}"
            if progress_callback:
                progress_callback(error_msg, -1)
            raise RuntimeError(error_msg) from e
    
    def _build_mst(self, graph: Dict) -> Tuple[List, List]:
        """
        使用Kruskal算法构建最小生成树
        
        Args:
            graph: 像素图结构
            
        Returns:
            MST的边和权重列表
        """
        # 创建边列表并按权重排序
        edges_with_weights = list(zip(graph['edges'], graph['weights']))
        edges_with_weights.sort(key=lambda x: x[1])  # 按权重排序
        
        # 初始化并查集
        num_nodes = len(graph['nodes'])
        uf = UnionFind(num_nodes)  # 使用基础并查集
        
        mst_edges = []
        mst_weights = []
        
        # Kruskal算法
        for edge, weight in edges_with_weights:
            node1, node2 = edge
            
            # 如果两个节点不在同一连通分量中，添加这条边
            if not uf.connected(node1, node2):
                uf.union(node1, node2)
                mst_edges.append(edge)
                mst_weights.append(weight)
                
                # MST有n-1条边
                if len(mst_edges) == num_nodes - 1:
                    break
        
        return mst_edges, mst_weights
    
    def _calculate_threshold(self, 
                           mst_weights: List[float], 
                           adaptive: bool = True) -> float:
        """
        计算分割阈值
        
        Args:
            mst_weights: MST边权重列表
            adaptive: 是否使用自适应方法
            
        Returns:
            分割阈值
        """
        weights = np.array(mst_weights)
        
        if adaptive:
            # 自适应阈值：使用权重分布的统计特性
            mean_weight = np.mean(weights)
            std_weight = np.std(weights)
            
            # 使用均值加一个标准差作为阈值
            threshold = mean_weight + 0.5 * std_weight
        else:
            # 简单阈值：使用中位数
            threshold = np.median(weights)
        
        return threshold
    
    def _threshold_segmentation(self, 
                              graph: Dict,
                              mst_edges: List,
                              mst_weights: List,
                              threshold: float,
                              height: int,
                              width: int) -> Dict:
        """
        基于阈值的分割
        
        Args:
            graph: 原始图结构
            mst_edges: MST边列表
            mst_weights: MST权重列表
            threshold: 分割阈值
            height: 图像高度
            width: 图像宽度
            
        Returns:
            分割结果
        """
        # 初始化分割并查集
        seg_uf = SegmentationUnionFind(height, width)
        
        # 只保留权重小于阈值的边
        valid_edges = []
        for edge, weight in zip(mst_edges, mst_weights):
            if weight <= threshold:
                node1, node2 = edge
                pixel1 = graph['nodes'][node1]
                pixel2 = graph['nodes'][node2]
                
                seg_uf.union_pixels(pixel1, pixel2, weight)
                valid_edges.append((edge, weight))
        
        # 获取分割结果
        label_map = seg_uf.get_segmentation_map()
        segment_stats = seg_uf.get_segment_statistics()
        
        result = {
            'label_map': label_map,
            'union_find': seg_uf,
            'threshold': threshold,
            'valid_edges': valid_edges,
            'statistics': segment_stats,
            'mst_edges': mst_edges,
            'mst_weights': mst_weights
        }
        
        return result
    
    def _post_process_segments(self, 
                             segmentation_result: Dict, 
                             graph: Dict) -> None:
        """
        后处理：合并小分割区域
        
        Args:
            segmentation_result: 分割结果
            graph: 原始图结构
        """
        seg_uf = segmentation_result['union_find']
        
        # 合并小区域
        seg_uf.merge_small_segments(self.min_segment_size, graph['adjacency'])
        
        # 更新分割结果
        segmentation_result['label_map'] = seg_uf.get_segmentation_map()
        segmentation_result['statistics'] = seg_uf.get_segment_statistics()
    
    def segment_with_multiple_thresholds(self, 
                                       image: np.ndarray,
                                       thresholds: List[float]) -> Dict:
        """
        使用多个阈值进行分割，用于比较分析
        
        Args:
            image: 输入图像
            thresholds: 阈值列表
            
        Returns:
            多阈值分割结果
        """
        height, width = image.shape[:2]
        
        # 构建图和MST（只需要一次）
        graph = self.graph_builder.build_graph(image)
        mst_edges, mst_weights = self._build_mst(graph)
        
        results = {}
        
        for threshold in thresholds:
            result = self._threshold_segmentation(
                graph, mst_edges, mst_weights, threshold, height, width
            )
            self._post_process_segments(result, graph)
            results[threshold] = result
        
        return {
            'results': results,
            'graph': graph,
            'mst_edges': mst_edges,
            'mst_weights': mst_weights
        }
    
    def get_segmentation_hierarchy(self, 
                                 image: np.ndarray,
                                 num_levels: int = 5) -> Dict:
        """
        获取分割层次结构（不同粒度的分割）
        
        Args:
            image: 输入图像
            num_levels: 层次数量
            
        Returns:
            层次分割结果
        """
        height, width = image.shape[:2]
        
        # 构建图和MST
        graph = self.graph_builder.build_graph(image)
        mst_edges, mst_weights = self._build_mst(graph)
        
        # 计算不同层次的阈值
        weights = np.array(mst_weights)
        min_weight = np.min(weights)
        max_weight = np.max(weights)
        
        thresholds = np.linspace(min_weight, max_weight, num_levels)
        
        # 执行多阈值分割
        hierarchy_results = self.segment_with_multiple_thresholds(image, thresholds)
        
        return hierarchy_results
    
    def visualize_mst(self, 
                     image: np.ndarray, 
                     mst_edges: List,
                     mst_weights: List,
                     threshold: float = None) -> np.ndarray:
        """
        可视化最小生成树
        
        Args:
            image: 原始图像
            mst_edges: MST边列表
            mst_weights: MST权重列表
            threshold: 显示阈值，只显示权重小于此值的边
            
        Returns:
            可视化图像
        """
        import cv2
        
        vis_image = image.copy()
        graph = self.graph_builder.build_graph(image)
        
        for edge, weight in zip(mst_edges, mst_weights):
            if threshold is None or weight <= threshold:
                node1, node2 = edge
                pixel1 = graph['nodes'][node1]
                pixel2 = graph['nodes'][node2]
                
                # 根据权重设置颜色（权重越大颜色越红）
                if threshold is not None:
                    color_intensity = int(255 * (weight / threshold))
                    color = (0, 255 - color_intensity, color_intensity)
                else:
                    color = (0, 255, 0)
                
                cv2.line(vis_image,
                        (pixel1[1], pixel1[0]),  # (col, row)
                        (pixel2[1], pixel2[0]),  # (col, row)
                        color, 1)
        
        return vis_image
