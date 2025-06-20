"""
像素图数据结构
高效存储和操作像素间的关系图
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional
import scipy.sparse as sp
from collections import defaultdict


class PixelGraph:
    """像素关系图数据结构"""
    
    def __init__(self, height: int, width: int, connectivity: int = 4):
        """
        初始化像素图
        
        Args:
            height: 图像高度
            width: 图像宽度
            connectivity: 连接性 (4 或 8)
        """
        self.height = height
        self.width = width
        self.connectivity = connectivity
        self.num_pixels = height * width
        
        # 像素坐标到索引的映射
        self.coord_to_idx = {}
        self.idx_to_coord = {}
        self._build_coordinate_mapping()
        
        # 图结构存储
        self.adjacency_list = defaultdict(list)  # 邻接表
        self.edge_weights = {}  # 边权重
        self.node_features = {}  # 节点特征
        
        # 稀疏矩阵表示（用于高效计算）
        self.adjacency_matrix = None
        self.weight_matrix = None
        
    def _build_coordinate_mapping(self):
        """构建坐标到索引的映射"""
        idx = 0
        for row in range(self.height):
            for col in range(self.width):
                coord = (row, col)
                self.coord_to_idx[coord] = idx
                self.idx_to_coord[idx] = coord
                idx += 1
    
    def add_edge(self, 
                pixel1: Tuple[int, int], 
                pixel2: Tuple[int, int], 
                weight: float):
        """
        添加边
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            weight: 边权重
        """
        idx1 = self.coord_to_idx[pixel1]
        idx2 = self.coord_to_idx[pixel2]
        
        # 添加到邻接表
        self.adjacency_list[idx1].append(idx2)
        self.adjacency_list[idx2].append(idx1)
        
        # 存储边权重
        edge_key = (min(idx1, idx2), max(idx1, idx2))
        self.edge_weights[edge_key] = weight
    
    def get_edge_weight(self, 
                       pixel1: Tuple[int, int], 
                       pixel2: Tuple[int, int]) -> Optional[float]:
        """
        获取边权重
        
        Args:
            pixel1: 第一个像素坐标
            pixel2: 第二个像素坐标
            
        Returns:
            边权重，如果边不存在返回None
        """
        idx1 = self.coord_to_idx[pixel1]
        idx2 = self.coord_to_idx[pixel2]
        edge_key = (min(idx1, idx2), max(idx1, idx2))
        
        return self.edge_weights.get(edge_key)
    
    def get_neighbors(self, pixel: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        获取像素的邻居
        
        Args:
            pixel: 像素坐标
            
        Returns:
            邻居像素坐标列表
        """
        idx = self.coord_to_idx[pixel]
        neighbor_indices = self.adjacency_list[idx]
        
        return [self.idx_to_coord[neighbor_idx] for neighbor_idx in neighbor_indices]
    
    def set_node_feature(self, pixel: Tuple[int, int], feature: np.ndarray):
        """
        设置节点特征
        
        Args:
            pixel: 像素坐标
            feature: 特征向量
        """
        idx = self.coord_to_idx[pixel]
        self.node_features[idx] = feature
    
    def get_node_feature(self, pixel: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        获取节点特征
        
        Args:
            pixel: 像素坐标
            
        Returns:
            特征向量
        """
        idx = self.coord_to_idx[pixel]
        return self.node_features.get(idx)
    
    def build_sparse_matrices(self):
        """构建稀疏矩阵表示"""
        # 构建邻接矩阵
        row_indices = []
        col_indices = []
        
        for node_idx, neighbors in self.adjacency_list.items():
            for neighbor_idx in neighbors:
                row_indices.append(node_idx)
                col_indices.append(neighbor_idx)
        
        # 创建邻接矩阵
        data = np.ones(len(row_indices))
        self.adjacency_matrix = sp.csr_matrix(
            (data, (row_indices, col_indices)), 
            shape=(self.num_pixels, self.num_pixels)
        )
        
        # 构建权重矩阵
        weight_data = []
        weight_rows = []
        weight_cols = []
        
        for (idx1, idx2), weight in self.edge_weights.items():
            weight_data.extend([weight, weight])  # 对称矩阵
            weight_rows.extend([idx1, idx2])
            weight_cols.extend([idx2, idx1])
        
        self.weight_matrix = sp.csr_matrix(
            (weight_data, (weight_rows, weight_cols)),
            shape=(self.num_pixels, self.num_pixels)
        )
    
    def get_degree(self, pixel: Tuple[int, int]) -> int:
        """
        获取节点度数
        
        Args:
            pixel: 像素坐标
            
        Returns:
            节点度数
        """
        idx = self.coord_to_idx[pixel]
        return len(self.adjacency_list[idx])
    
    def get_graph_statistics(self) -> Dict:
        """
        获取图统计信息
        
        Returns:
            统计信息字典
        """
        degrees = [len(neighbors) for neighbors in self.adjacency_list.values()]
        weights = list(self.edge_weights.values())
        
        stats = {
            'num_nodes': self.num_pixels,
            'num_edges': len(self.edge_weights),
            'avg_degree': np.mean(degrees) if degrees else 0,
            'max_degree': np.max(degrees) if degrees else 0,
            'min_degree': np.min(degrees) if degrees else 0,
            'avg_weight': np.mean(weights) if weights else 0,
            'max_weight': np.max(weights) if weights else 0,
            'min_weight': np.min(weights) if weights else 0,
            'density': len(self.edge_weights) / (self.num_pixels * (self.num_pixels - 1) / 2)
        }
        
        return stats
    
    def filter_edges_by_weight(self, threshold: float) -> 'PixelGraph':
        """
        根据权重阈值过滤边
        
        Args:
            threshold: 权重阈值
            
        Returns:
            过滤后的新图
        """
        filtered_graph = PixelGraph(self.height, self.width, self.connectivity)
        
        # 复制节点特征
        filtered_graph.node_features = self.node_features.copy()
        
        # 只添加权重小于等于阈值的边
        for (idx1, idx2), weight in self.edge_weights.items():
            if weight <= threshold:
                pixel1 = self.idx_to_coord[idx1]
                pixel2 = self.idx_to_coord[idx2]
                filtered_graph.add_edge(pixel1, pixel2, weight)
        
        return filtered_graph
    
    def get_connected_components(self) -> List[Set[Tuple[int, int]]]:
        """
        获取连通分量
        
        Returns:
            连通分量列表，每个分量是像素坐标的集合
        """
        visited = set()
        components = []
        
        def dfs(pixel: Tuple[int, int], component: Set[Tuple[int, int]]):
            if pixel in visited:
                return
            
            visited.add(pixel)
            component.add(pixel)
            
            # 访问所有邻居
            for neighbor in self.get_neighbors(pixel):
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        # 遍历所有像素
        for row in range(self.height):
            for col in range(self.width):
                pixel = (row, col)
                if pixel not in visited:
                    component = set()
                    dfs(pixel, component)
                    if component:
                        components.append(component)
        
        return components
    
    def compute_laplacian_matrix(self) -> sp.csr_matrix:
        """
        计算拉普拉斯矩阵
        
        Returns:
            拉普拉斯矩阵
        """
        if self.adjacency_matrix is None:
            self.build_sparse_matrices()
        
        # 计算度矩阵
        degrees = np.array(self.adjacency_matrix.sum(axis=1)).flatten()
        degree_matrix = sp.diags(degrees, format='csr')
        
        # 拉普拉斯矩阵 = 度矩阵 - 邻接矩阵
        laplacian = degree_matrix - self.adjacency_matrix
        
        return laplacian
    
    def save_to_file(self, filename: str):
        """
        保存图到文件
        
        Args:
            filename: 文件名
        """
        import pickle
        
        graph_data = {
            'height': self.height,
            'width': self.width,
            'connectivity': self.connectivity,
            'adjacency_list': dict(self.adjacency_list),
            'edge_weights': self.edge_weights,
            'node_features': self.node_features
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(graph_data, f)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'PixelGraph':
        """
        从文件加载图
        
        Args:
            filename: 文件名
            
        Returns:
            加载的图对象
        """
        import pickle
        
        with open(filename, 'rb') as f:
            graph_data = pickle.load(f)
        
        # 创建新图对象
        graph = cls(
            graph_data['height'], 
            graph_data['width'], 
            graph_data['connectivity']
        )
        
        # 恢复数据
        graph.adjacency_list = defaultdict(list, graph_data['adjacency_list'])
        graph.edge_weights = graph_data['edge_weights']
        graph.node_features = graph_data['node_features']
        
        return graph
