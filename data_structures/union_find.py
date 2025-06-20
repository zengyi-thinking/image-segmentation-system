"""
并查集数据结构实现
用于高效管理连通分量和区域合并操作
"""

from typing import Dict, List, Set, Optional
import numpy as np


class UnionFind:
    """并查集数据结构"""
    
    def __init__(self, n: int):
        """
        初始化并查集
        
        Args:
            n: 元素数量
        """
        self.parent = list(range(n))  # 父节点数组
        self.rank = [0] * n          # 秩数组（用于按秩合并）
        self.size = [1] * n          # 每个连通分量的大小
        self.num_components = n       # 连通分量数量
    
    def find(self, x: int) -> int:
        """
        查找元素x的根节点（带路径压缩）
        
        Args:
            x: 要查找的元素
            
        Returns:
            根节点
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        合并两个元素所在的集合
        
        Args:
            x: 第一个元素
            y: 第二个元素
            
        Returns:
            是否成功合并（如果已经在同一集合中返回False）
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False  # 已经在同一集合中
        
        # 按秩合并
        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        
        self.parent[root_y] = root_x
        self.size[root_x] += self.size[root_y]
        
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1
        
        self.num_components -= 1
        return True
    
    def connected(self, x: int, y: int) -> bool:
        """
        检查两个元素是否在同一集合中
        
        Args:
            x: 第一个元素
            y: 第二个元素
            
        Returns:
            是否连通
        """
        return self.find(x) == self.find(y)
    
    def get_component_size(self, x: int) -> int:
        """
        获取元素x所在连通分量的大小
        
        Args:
            x: 元素
            
        Returns:
            连通分量大小
        """
        root = self.find(x)
        return self.size[root]
    
    def get_components(self) -> Dict[int, List[int]]:
        """
        获取所有连通分量
        
        Returns:
            字典，键为根节点，值为该分量中的所有元素
        """
        components = {}
        for i in range(len(self.parent)):
            root = self.find(i)
            if root not in components:
                components[root] = []
            components[root].append(i)
        return components
    
    def get_component_roots(self) -> Set[int]:
        """
        获取所有连通分量的根节点
        
        Returns:
            根节点集合
        """
        return {self.find(i) for i in range(len(self.parent))}


class WeightedUnionFind(UnionFind):
    """带权重的并查集"""
    
    def __init__(self, n: int):
        super().__init__(n)
        self.edge_weights = {}  # 存储合并时的边权重
        self.merge_history = []  # 合并历史
    
    def union_with_weight(self, x: int, y: int, weight: float) -> bool:
        """
        带权重的合并操作
        
        Args:
            x: 第一个元素
            y: 第二个元素
            weight: 合并边的权重
            
        Returns:
            是否成功合并
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # 记录合并历史
        merge_info = {
            'components': (root_x, root_y),
            'weight': weight,
            'sizes': (self.size[root_x], self.size[root_y])
        }
        self.merge_history.append(merge_info)
        
        # 执行合并
        success = self.union(x, y)
        
        if success:
            # 记录边权重
            new_root = self.find(x)
            self.edge_weights[new_root] = weight
        
        return success
    
    def get_merge_threshold(self, percentile: float = 50.0) -> float:
        """
        根据合并历史计算权重阈值
        
        Args:
            percentile: 百分位数
            
        Returns:
            权重阈值
        """
        if not self.merge_history:
            return 0.0
        
        weights = [info['weight'] for info in self.merge_history]
        return np.percentile(weights, percentile)


class SegmentationUnionFind(WeightedUnionFind):
    """专用于图像分割的并查集"""
    
    def __init__(self, height: int, width: int):
        """
        初始化图像分割并查集
        
        Args:
            height: 图像高度
            width: 图像宽度
        """
        super().__init__(height * width)
        self.height = height
        self.width = width
        self.pixel_to_idx = {}
        self.idx_to_pixel = {}
        
        # 建立像素坐标到索引的映射
        idx = 0
        for row in range(height):
            for col in range(width):
                self.pixel_to_idx[(row, col)] = idx
                self.idx_to_pixel[idx] = (row, col)
                idx += 1
    
    def union_pixels(self, pixel1: tuple, pixel2: tuple, weight: float) -> bool:
        """
        合并两个像素
        
        Args:
            pixel1: 第一个像素坐标 (row, col)
            pixel2: 第二个像素坐标 (row, col)
            weight: 边权重
            
        Returns:
            是否成功合并
        """
        idx1 = self.pixel_to_idx[pixel1]
        idx2 = self.pixel_to_idx[pixel2]
        return self.union_with_weight(idx1, idx2, weight)
    
    def get_segmentation_map(self) -> np.ndarray:
        """
        获取分割结果图
        
        Returns:
            分割标签图 (height, width)
        """
        label_map = np.zeros((self.height, self.width), dtype=np.int32)
        
        # 获取所有连通分量
        components = self.get_components()
        
        # 为每个分量分配标签
        for label, (root, pixels) in enumerate(components.items()):
            for pixel_idx in pixels:
                row, col = self.idx_to_pixel[pixel_idx]
                label_map[row, col] = label
        
        return label_map
    
    def get_segment_statistics(self) -> Dict:
        """
        获取分割统计信息
        
        Returns:
            统计信息字典
        """
        components = self.get_components()
        
        sizes = [len(pixels) for pixels in components.values()]
        
        stats = {
            'num_segments': len(components),
            'avg_segment_size': np.mean(sizes),
            'max_segment_size': np.max(sizes),
            'min_segment_size': np.min(sizes),
            'std_segment_size': np.std(sizes),
            'total_pixels': self.height * self.width
        }
        
        return stats
    
    def filter_small_segments(self, min_size: int) -> Dict:
        """
        过滤小分割区域
        
        Args:
            min_size: 最小区域大小
            
        Returns:
            过滤后的分割信息
        """
        components = self.get_components()
        filtered_components = {}
        small_segments = []
        
        for root, pixels in components.items():
            if len(pixels) >= min_size:
                filtered_components[root] = pixels
            else:
                small_segments.extend(pixels)
        
        return {
            'filtered_components': filtered_components,
            'small_segments': small_segments,
            'num_filtered': len(filtered_components),
            'num_small': len(small_segments)
        }
    
    def merge_small_segments(self, min_size: int, 
                           adjacency_info: Dict) -> None:
        """
        将小分割区域合并到相邻的大区域
        
        Args:
            min_size: 最小区域大小
            adjacency_info: 邻接信息
        """
        filter_result = self.filter_small_segments(min_size)
        small_segments = filter_result['small_segments']
        
        for pixel_idx in small_segments:
            pixel = self.idx_to_pixel[pixel_idx]
            
            # 找到相邻的大区域
            neighbors = adjacency_info.get(pixel_idx, [])
            for neighbor_idx in neighbors:
                neighbor_root = self.find(neighbor_idx)
                if self.size[neighbor_root] >= min_size:
                    # 合并到这个大区域
                    self.union(pixel_idx, neighbor_idx)
                    break
