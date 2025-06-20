"""
图像输入输出工具模块
处理图像的加载、保存和格式转换
"""

import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from typing import Optional, Union, Tuple


class ImageLoader:
    """图像加载器"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def load_image(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        加载图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            RGB格式的图像数组，加载失败返回None
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                print(f"错误: 文件不存在 {image_path}")
                return None
            
            if image_path.suffix.lower() not in self.supported_formats:
                print(f"错误: 不支持的图像格式 {image_path.suffix}")
                return None
            
            # 使用OpenCV加载图像
            image = cv2.imread(str(image_path))
            
            if image is None:
                print(f"错误: 无法读取图像文件 {image_path}")
                return None
            
            # 转换为RGB格式
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            return image_rgb
            
        except Exception as e:
            print(f"加载图像时发生错误: {e}")
            return None
    
    def load_image_pil(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        使用PIL加载图像（备用方法）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            RGB格式的图像数组
        """
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 转换为numpy数组
                image_array = np.array(img)
                
                return image_array
                
        except Exception as e:
            print(f"使用PIL加载图像时发生错误: {e}")
            return None
    
    def get_image_info(self, image_path: Union[str, Path]) -> Optional[dict]:
        """
        获取图像信息
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像信息字典
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'size': img.size,  # (width, height)
                    'mode': img.mode,
                    'format': img.format,
                    'filename': Path(image_path).name
                }
                
                return info
                
        except Exception as e:
            print(f"获取图像信息时发生错误: {e}")
            return None
    
    def resize_image(self, 
                    image: np.ndarray, 
                    target_size: Tuple[int, int],
                    keep_aspect_ratio: bool = True) -> np.ndarray:
        """
        调整图像大小
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            keep_aspect_ratio: 是否保持宽高比
            
        Returns:
            调整后的图像
        """
        if keep_aspect_ratio:
            # 计算缩放比例
            h, w = image.shape[:2]
            target_w, target_h = target_size
            
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # 创建目标尺寸的画布并居中放置
            canvas = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            
            return canvas
        else:
            return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)


class ImageSaver:
    """图像保存器"""
    
    def __init__(self):
        self.quality_settings = {
            '.jpg': 95,
            '.jpeg': 95,
            '.png': 9,  # PNG压缩级别
        }
    
    def save_image(self, 
                  image: np.ndarray, 
                  output_path: Union[str, Path],
                  quality: Optional[int] = None) -> bool:
        """
        保存图像文件
        
        Args:
            image: 要保存的图像（RGB格式）
            output_path: 输出文件路径
            quality: 图像质量（JPEG: 0-100, PNG: 0-9）
            
        Returns:
            是否保存成功
        """
        try:
            output_path = Path(output_path)
            
            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为BGR格式（OpenCV使用）
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # 设置保存参数
            save_params = []
            ext = output_path.suffix.lower()
            
            if quality is None:
                quality = self.quality_settings.get(ext, 95)
            
            if ext in ['.jpg', '.jpeg']:
                save_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            elif ext == '.png':
                save_params = [cv2.IMWRITE_PNG_COMPRESSION, quality]
            
            # 保存图像
            success = cv2.imwrite(str(output_path), image_bgr, save_params)
            
            if success:
                print(f"图像已保存到: {output_path}")
                return True
            else:
                print(f"保存图像失败: {output_path}")
                return False
                
        except Exception as e:
            print(f"保存图像时发生错误: {e}")
            return False
    
    def save_image_pil(self, 
                      image: np.ndarray, 
                      output_path: Union[str, Path],
                      quality: int = 95) -> bool:
        """
        使用PIL保存图像（备用方法）
        
        Args:
            image: 要保存的图像（RGB格式）
            output_path: 输出文件路径
            quality: 图像质量
            
        Returns:
            是否保存成功
        """
        try:
            # 转换为PIL图像
            pil_image = Image.fromarray(image)
            
            # 保存参数
            save_kwargs = {}
            if Path(output_path).suffix.lower() in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            pil_image.save(output_path, **save_kwargs)
            print(f"图像已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"使用PIL保存图像时发生错误: {e}")
            return False


class ImagePreprocessor:
    """图像预处理器"""
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """
        归一化图像到0-255范围
        
        Args:
            image: 输入图像
            
        Returns:
            归一化后的图像
        """
        if image.dtype != np.uint8:
            # 归一化到0-255
            image = image.astype(np.float32)
            image = (image - image.min()) / (image.max() - image.min()) * 255
            image = image.astype(np.uint8)
        
        return image
    
    @staticmethod
    def apply_gaussian_blur(image: np.ndarray, 
                          kernel_size: int = 5,
                          sigma: float = 1.0) -> np.ndarray:
        """
        应用高斯模糊
        
        Args:
            image: 输入图像
            kernel_size: 核大小
            sigma: 标准差
            
        Returns:
            模糊后的图像
        """
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, 
                        alpha: float = 1.2,
                        beta: int = 10) -> np.ndarray:
        """
        增强对比度
        
        Args:
            image: 输入图像
            alpha: 对比度系数
            beta: 亮度偏移
            
        Returns:
            增强后的图像
        """
        enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return enhanced
