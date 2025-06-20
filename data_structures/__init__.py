"""
数据结构模块
包含图像分割系统使用的高效数据结构
"""

from .union_find import UnionFind, WeightedUnionFind, SegmentationUnionFind

__all__ = [
    'UnionFind',
    'WeightedUnionFind',
    'SegmentationUnionFind'
]
