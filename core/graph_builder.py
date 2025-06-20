"""
图构建模块
将图像转换为像素图，建立像素间的邻接关系和边权重
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
import cv2
from .edge_weights import EdgeWeightCalculator


class PixelGraphBuilder:
    """像素图构建器"""
    
    def __init__(self, 
                 connectivity: int = 4,
                 weight_calculator: Optional[EdgeWeightCalculator] = None):
        """
        初始化图构建器
        
        Args:
            connectivity: 连接性 (4-连通或8-连通)
            weight_calculator: 边权重计算器
        """
        self.connectivity = connectivity
        self.weight_calculator = weight_calculator or EdgeWeightCalculator()
        
        # 邻接偏移量
        if connectivity == 4:
            self.offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上下左右
        elif connectivity == 8:
            self.offsets = [(-1, -1), (-1, 0), (-1, 1),        # 8-连通
                           (0, -1),           (0, 1),
                           (1, -1),  (1, 0),  (1, 1)]
        else:
            raise ValueError("连接性必须是4或8")
    
    def build_graph(self, image: np.ndarray) -> Dict:
        """
        构建像素图
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            图结构字典，包含节点、边和权重信息
        """
        height, width = image.shape[:2]
        
        # 初始化图结构
        graph = {
            'nodes': [],           # 节点列表 [(row, col), ...]
            'edges': [],           # 边列表 [(node1_idx, node2_idx), ...]
            'weights': [],         # 权重列表 [weight, ...]
            'adjacency': {},       # 邻接表 {node_idx: [neighbor_idx, ...]}
            'node_to_idx': {},     # 节点到索引的映射
            'image_shape': (height, width)
        }
        
        # 创建节点
        node_idx = 0
        for row in range(height):
            for col in range(width):
                node = (row, col)
                graph['nodes'].append(node)
                graph['node_to_idx'][node] = node_idx
                graph['adjacency'][node_idx] = []
                node_idx += 1
        
        # 创建边
        edge_idx = 0
        for row in range(height):
            for col in range(width):
                current_node = (row, col)
                current_idx = graph['node_to_idx'][current_node]
                
                # 检查所有邻居
                for dr, dc in self.offsets:
                    neighbor_row, neighbor_col = row + dr, col + dc
                    
                    # 检查边界
                    if (0 <= neighbor_row < height and 
                        0 <= neighbor_col < width):
                        
                        neighbor_node = (neighbor_row, neighbor_col)
                        neighbor_idx = graph['node_to_idx'][neighbor_node]
                        
                        # 避免重复边（只添加一个方向）
                        if current_idx < neighbor_idx:
                            # 计算边权重
                            weight = self.weight_calculator.calculate_weight(
                                current_node, neighbor_node, image
                            )
                            
                            # 添加边
                            graph['edges'].append((current_idx, neighbor_idx))
                            graph['weights'].append(weight)
                            
                            # 更新邻接表
                            graph['adjacency'][current_idx].append(neighbor_idx)
                            graph['adjacency'][neighbor_idx].append(current_idx)
                            
                            edge_idx += 1
        
        return graph
    
    def build_sparse_graph(self, image: np.ndarray, 
                          threshold: float = None) -> Dict:
        """
        构建稀疏图（只保留权重小于阈值的边）
        
        Args:
            image: 输入图像
            threshold: 权重阈值，None表示自动计算
            
        Returns:
            稀疏图结构
        """
        # 首先构建完整图
        graph = self.build_graph(image)
        
        if threshold is None:
            # 自动计算阈值（使用权重的中位数）
            threshold = np.median(graph['weights'])
        
        # 过滤边
        filtered_edges = []
        filtered_weights = []
        new_adjacency = {idx: [] for idx in range(len(graph['nodes']))}
        
        for i, (edge, weight) in enumerate(zip(graph['edges'], graph['weights'])):
            if weight <= threshold:
                filtered_edges.append(edge)
                filtered_weights.append(weight)
                
                # 更新邻接表
                node1_idx, node2_idx = edge
                new_adjacency[node1_idx].append(node2_idx)
                new_adjacency[node2_idx].append(node1_idx)
        
        # 更新图结构
        graph['edges'] = filtered_edges
        graph['weights'] = filtered_weights
        graph['adjacency'] = new_adjacency
        graph['threshold'] = threshold
        
        return graph
    
    def add_long_range_connections(self, graph: Dict, 
                                  image: np.ndarray,
                                  max_distance: int = 5,
                                  similarity_threshold: float = 10.0) -> Dict:
        """
        添加长距离连接（连接相似但不相邻的像素）
        
        Args:
            graph: 现有图结构
            image: 输入图像
            max_distance: 最大连接距离
            similarity_threshold: 相似性阈值
            
        Returns:
            增强的图结构
        """
        height, width = graph['image_shape']
        
        # 随机采样一些像素进行长距离连接
        sample_ratio = 0.1  # 采样10%的像素
        total_pixels = height * width
        sample_size = int(total_pixels * sample_ratio)
        
        # 随机选择像素
        sampled_pixels = np.random.choice(total_pixels, sample_size, replace=False)
        
        for pixel_idx in sampled_pixels:
            row = pixel_idx // width
            col = pixel_idx % width
            current_node = (row, col)
            current_idx = graph['node_to_idx'][current_node]
            
            # 在一定范围内寻找相似像素
            for dr in range(-max_distance, max_distance + 1):
                for dc in range(-max_distance, max_distance + 1):
                    if dr == 0 and dc == 0:
                        continue
                        
                    neighbor_row, neighbor_col = row + dr, col + dc
                    
                    if (0 <= neighbor_row < height and 
                        0 <= neighbor_col < width):
                        
                        neighbor_node = (neighbor_row, neighbor_col)
                        neighbor_idx = graph['node_to_idx'][neighbor_node]
                        
                        # 检查是否已经连接
                        if neighbor_idx not in graph['adjacency'][current_idx]:
                            # 计算相似性
                            weight = self.weight_calculator.calculate_weight(
                                current_node, neighbor_node, image
                            )
                            
                            # 如果足够相似，添加连接
                            if weight <= similarity_threshold:
                                graph['edges'].append((current_idx, neighbor_idx))
                                graph['weights'].append(weight)
                                graph['adjacency'][current_idx].append(neighbor_idx)
                                graph['adjacency'][neighbor_idx].append(current_idx)
        
        return graph
    
    def get_graph_statistics(self, graph: Dict) -> Dict:
        """
        获取图的统计信息
        
        Args:
            graph: 图结构
            
        Returns:
            统计信息字典
        """
        num_nodes = len(graph['nodes'])
        num_edges = len(graph['edges'])
        weights = np.array(graph['weights'])
        
        # 计算度分布
        degrees = [len(neighbors) for neighbors in graph['adjacency'].values()]
        
        stats = {
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'avg_degree': np.mean(degrees),
            'max_degree': np.max(degrees),
            'min_degree': np.min(degrees),
            'weight_mean': np.mean(weights),
            'weight_std': np.std(weights),
            'weight_min': np.min(weights),
            'weight_max': np.max(weights),
            'density': 2 * num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
        }
        
        return stats
    
    def visualize_graph_structure(self, graph: Dict, 
                                 image: np.ndarray,
                                 show_edges: bool = True,
                                 edge_threshold: float = None) -> np.ndarray:
        """
        可视化图结构
        
        Args:
            graph: 图结构
            image: 原始图像
            show_edges: 是否显示边
            edge_threshold: 边权重阈值，只显示权重小于此值的边
            
        Returns:
            可视化图像
        """
        vis_image = image.copy()
        height, width = graph['image_shape']
        
        if show_edges:
            for i, (edge, weight) in enumerate(zip(graph['edges'], graph['weights'])):
                if edge_threshold is None or weight <= edge_threshold:
                    node1_idx, node2_idx = edge
                    node1 = graph['nodes'][node1_idx]
                    node2 = graph['nodes'][node2_idx]
                    
                    # 绘制边
                    cv2.line(vis_image, 
                            (node1[1], node1[0]),  # (col, row)
                            (node2[1], node2[0]),  # (col, row)
                            (0, 255, 0), 1)
        
        return vis_image
