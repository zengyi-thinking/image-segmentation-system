"""
图像输入输出工具模块
处理图像的加载、保存和格式转换
增强版本，支持更多格式和错误处理
"""

import numpy as np
import cv2
from PIL import Image, ImageOps, ExifTags
from pathlib import Path
from typing import Optional, Union, Tuple, Dict, List
import os
import logging
import warnings
import io


class ImageLoadError(Exception):
    """图像加载错误的自定义异常"""
    pass


class ImageLoader:
    """增强版图像加载器"""

    def __init__(self, max_size: Tuple[int, int] = (4096, 4096),
                 auto_orient: bool = True,
                 normalize_format: bool = True):
        """
        初始化图像加载器

        Args:
            max_size: 最大图像尺寸限制 (width, height)
            auto_orient: 是否自动根据EXIF信息旋转图像
            normalize_format: 是否自动标准化图像格式
        """
        self.max_size = max_size
        self.auto_orient = auto_orient
        self.normalize_format = normalize_format

        # 支持的图像格式（更全面）
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
            '.webp', '.gif', '.ico', '.ppm', '.pgm', '.pbm'
        }

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 图像统计信息
        self.load_stats = {
            'total_loaded': 0,
            'failed_loads': 0,
            'format_conversions': 0,
            'size_reductions': 0
        }
    
    def load_image(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        增强版图像加载方法

        Args:
            image_path: 图像文件路径

        Returns:
            RGB格式的图像数组，加载失败返回None

        Raises:
            ImageLoadError: 包含详细错误信息的异常
        """
        try:
            image_path = Path(image_path)
            self.load_stats['total_loaded'] += 1

            # 1. 路径和文件验证
            self._validate_image_path(image_path)

            # 2. 尝试多种加载方法
            image = self._load_with_fallback(image_path)

            if image is None:
                raise ImageLoadError(f"所有加载方法都失败: {image_path}")

            # 3. 图像后处理
            image = self._post_process_image(image, image_path)

            self.logger.info(f"成功加载图像: {image_path} ({image.shape})")
            return image

        except ImageLoadError:
            self.load_stats['failed_loads'] += 1
            raise
        except Exception as e:
            self.load_stats['failed_loads'] += 1
            error_msg = f"加载图像时发生未预期错误: {str(e)}"
            self.logger.error(error_msg)
            raise ImageLoadError(error_msg) from e

    def _validate_image_path(self, image_path: Path):
        """验证图像路径和文件"""
        # 检查文件是否存在
        if not image_path.exists():
            raise ImageLoadError(f"文件不存在: {image_path}")

        # 检查是否为文件
        if not image_path.is_file():
            raise ImageLoadError(f"路径不是文件: {image_path}")

        # 检查文件大小
        file_size = image_path.stat().st_size
        if file_size == 0:
            raise ImageLoadError(f"文件为空: {image_path}")

        if file_size > 100 * 1024 * 1024:  # 100MB限制
            raise ImageLoadError(f"文件过大 ({file_size/1024/1024:.1f}MB): {image_path}")

        # 检查文件扩展名
        if image_path.suffix.lower() not in self.supported_formats:
            supported_list = ', '.join(sorted(self.supported_formats))
            raise ImageLoadError(
                f"不支持的图像格式: {image_path.suffix}\n"
                f"支持的格式: {supported_list}"
            )

        # 检查文件权限
        if not os.access(image_path, os.R_OK):
            raise ImageLoadError(f"文件无读取权限: {image_path}")

    def _load_with_fallback(self, image_path: Path) -> Optional[np.ndarray]:
        """使用多种方法尝试加载图像"""
        load_methods = [
            ("PIL", self._load_with_pil),
            ("OpenCV", self._load_with_opencv),
            ("PIL(强制RGB)", self._load_with_pil_force_rgb),
            ("原始字节", self._load_with_raw_bytes)
        ]

        last_error = None

        for method_name, method in load_methods:
            try:
                self.logger.debug(f"尝试使用 {method_name} 加载: {image_path}")
                image = method(image_path)

                if image is not None:
                    self.logger.info(f"成功使用 {method_name} 加载图像")
                    return image

            except Exception as e:
                last_error = e
                self.logger.warning(f"{method_name} 加载失败: {str(e)}")
                continue

        # 所有方法都失败
        if last_error:
            raise ImageLoadError(f"所有加载方法都失败，最后错误: {str(last_error)}")

        return None

    def _load_with_pil(self, image_path: Path) -> Optional[np.ndarray]:
        """使用PIL加载图像"""
        try:
            with Image.open(image_path) as img:
                # 处理EXIF旋转信息
                if self.auto_orient:
                    img = ImageOps.exif_transpose(img)

                # 转换为RGB模式
                if img.mode != 'RGB':
                    if img.mode == 'RGBA':
                        # 处理透明通道
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')

                # 转换为numpy数组
                image_array = np.array(img)

                return image_array

        except Exception as e:
            raise ImageLoadError(f"PIL加载失败: {str(e)}")

    def _load_with_opencv(self, image_path: Path) -> Optional[np.ndarray]:
        """使用OpenCV加载图像"""
        try:
            # 处理中文路径问题
            image_str = str(image_path)

            # 如果路径包含非ASCII字符，使用字节流方式
            if not image_str.isascii():
                return self._load_opencv_with_bytes(image_path)

            # 正常加载
            image = cv2.imread(image_str, cv2.IMREAD_COLOR)

            if image is None:
                raise ImageLoadError("OpenCV返回None")

            # 转换为RGB格式
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image_rgb

        except Exception as e:
            raise ImageLoadError(f"OpenCV加载失败: {str(e)}")

    def _load_opencv_with_bytes(self, image_path: Path) -> Optional[np.ndarray]:
        """使用OpenCV字节流方式加载（解决中文路径问题）"""
        try:
            # 读取文件字节
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)

            # 解码图像
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ImageLoadError("OpenCV字节流解码失败")

            # 转换为RGB格式
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image_rgb

        except Exception as e:
            raise ImageLoadError(f"OpenCV字节流加载失败: {str(e)}")

    def _load_with_pil_force_rgb(self, image_path: Path) -> Optional[np.ndarray]:
        """强制使用PIL转换为RGB"""
        try:
            with Image.open(image_path) as img:
                # 强制转换为RGB，忽略原始模式
                img_rgb = img.convert('RGB')

                # 处理EXIF旋转
                if self.auto_orient:
                    img_rgb = ImageOps.exif_transpose(img_rgb)

                return np.array(img_rgb)

        except Exception as e:
            raise ImageLoadError(f"PIL强制RGB转换失败: {str(e)}")

    def _load_with_raw_bytes(self, image_path: Path) -> Optional[np.ndarray]:
        """使用原始字节流加载（最后的备用方案）"""
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # 尝试用PIL从字节流加载
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = img.convert('RGB')

            return np.array(img_rgb)

        except Exception as e:
            raise ImageLoadError(f"原始字节流加载失败: {str(e)}")

    def _post_process_image(self, image: np.ndarray, image_path: Path) -> np.ndarray:
        """图像后处理"""
        try:
            # 1. 尺寸检查和调整
            if self.max_size:
                image = self._resize_if_needed(image)

            # 2. 格式标准化
            if self.normalize_format:
                image = self._normalize_image_format(image)

            # 3. 数据类型检查
            if image.dtype != np.uint8:
                image = self._convert_to_uint8(image)

            # 4. 形状验证
            if len(image.shape) != 3 or image.shape[2] != 3:
                raise ImageLoadError(f"图像形状异常: {image.shape}，期望 (H, W, 3)")

            return image

        except Exception as e:
            raise ImageLoadError(f"图像后处理失败: {str(e)}")

    def _resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """如果图像过大则调整尺寸"""
        height, width = image.shape[:2]
        max_width, max_height = self.max_size

        if width <= max_width and height <= max_height:
            return image

        # 计算缩放比例
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h)

        new_width = int(width * scale)
        new_height = int(height * scale)

        self.logger.info(f"调整图像尺寸: {width}x{height} -> {new_width}x{new_height}")
        self.load_stats['size_reductions'] += 1

        # 使用高质量插值
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        return resized

    def _normalize_image_format(self, image: np.ndarray) -> np.ndarray:
        """标准化图像格式"""
        # 确保是3通道RGB图像
        if len(image.shape) == 2:
            # 灰度图转RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            self.load_stats['format_conversions'] += 1
        elif len(image.shape) == 3:
            if image.shape[2] == 4:
                # RGBA转RGB
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                self.load_stats['format_conversions'] += 1
            elif image.shape[2] == 1:
                # 单通道转RGB
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                self.load_stats['format_conversions'] += 1

        return image

    def _convert_to_uint8(self, image: np.ndarray) -> np.ndarray:
        """转换图像数据类型为uint8"""
        if image.dtype == np.float32 or image.dtype == np.float64:
            # 浮点数图像，假设范围是0-1
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = np.clip(image, 0, 255).astype(np.uint8)
        elif image.dtype == np.uint16:
            # 16位图像转8位
            image = (image / 256).astype(np.uint8)
        else:
            # 其他类型直接转换
            image = image.astype(np.uint8)

        return image

    def validate_image_format(self, image_path: Union[str, Path]) -> Dict[str, any]:
        """验证图像格式并返回详细信息"""
        try:
            image_path = Path(image_path)

            # 基本文件信息
            file_info = {
                'path': str(image_path),
                'exists': image_path.exists(),
                'size_bytes': image_path.stat().st_size if image_path.exists() else 0,
                'extension': image_path.suffix.lower(),
                'supported': image_path.suffix.lower() in self.supported_formats
            }

            if not image_path.exists():
                return file_info

            # 尝试获取图像信息
            try:
                with Image.open(image_path) as img:
                    file_info.update({
                        'format': img.format,
                        'mode': img.mode,
                        'size': img.size,
                        'has_exif': hasattr(img, '_getexif') and img._getexif() is not None
                    })
            except Exception as e:
                file_info['pil_error'] = str(e)

            # 尝试OpenCV信息
            try:
                if str(image_path).isascii():
                    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        file_info.update({
                            'opencv_shape': img.shape,
                            'opencv_dtype': str(img.dtype)
                        })
                else:
                    file_info['opencv_error'] = "路径包含非ASCII字符"
            except Exception as e:
                file_info['opencv_error'] = str(e)

            return file_info

        except Exception as e:
            return {'error': str(e)}

    def get_load_statistics(self) -> Dict[str, int]:
        """获取加载统计信息"""
        try:
            if hasattr(self, 'load_stats') and self.load_stats:
                return self.load_stats.copy()
            else:
                # 返回默认统计信息
                return {
                    'total_loaded': 0,
                    'failed_loads': 0,
                    'format_conversions': 0,
                    'size_reductions': 0
                }
        except Exception as e:
            print(f"获取加载统计信息时发生错误: {e}")
            return {
                'total_loaded': 0,
                'failed_loads': 0,
                'format_conversions': 0,
                'size_reductions': 0
            }

    def reset_statistics(self):
        """重置统计信息"""
        self.load_stats = {
            'total_loaded': 0,
            'failed_loads': 0,
            'format_conversions': 0,
            'size_reductions': 0
        }

    def get_supported_formats(self) -> List[str]:
        """获取支持的图像格式列表"""
        return sorted(list(self.supported_formats))
    
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
    """增强版图像保存器"""

    def __init__(self):
        self.quality_settings = {
            '.jpg': 95,
            '.jpeg': 95,
            '.png': 9,  # PNG压缩级别
            '.webp': 90,
            '.bmp': None,
            '.tiff': None,
            '.tif': None
        }

        # 保存统计
        self.save_stats = {
            'total_saved': 0,
            'failed_saves': 0,
            'format_conversions': 0
        }

        self.logger = logging.getLogger(__name__)
    
    def save_image(self,
                  image: np.ndarray,
                  output_path: Union[str, Path],
                  quality: Optional[int] = None,
                  metadata: Optional[Dict] = None) -> bool:
        """
        增强版图像保存方法

        Args:
            image: 要保存的图像（RGB格式）
            output_path: 输出文件路径
            quality: 图像质量
            metadata: 图像元数据

        Returns:
            是否保存成功
        """
        try:
            output_path = Path(output_path)
            self.save_stats['total_saved'] += 1

            # 验证输入
            self._validate_save_input(image, output_path)

            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 尝试多种保存方法
            success = self._save_with_fallback(image, output_path, quality, metadata)

            if success:
                self.logger.info(f"图像已保存到: {output_path}")
                return True
            else:
                self.save_stats['failed_saves'] += 1
                self.logger.error(f"保存图像失败: {output_path}")
                return False

        except Exception as e:
            self.save_stats['failed_saves'] += 1
            self.logger.error(f"保存图像时发生错误: {e}")
            return False

    def _validate_save_input(self, image: np.ndarray, output_path: Path):
        """验证保存输入"""
        if image is None:
            raise ValueError("图像不能为None")

        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"图像形状异常: {image.shape}，期望 (H, W, 3)")

        if image.dtype != np.uint8:
            raise ValueError(f"图像数据类型异常: {image.dtype}，期望 uint8")

        # 检查输出目录权限
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(f"无法创建输出目录: {output_path.parent}")

    def _save_with_fallback(self, image: np.ndarray, output_path: Path,
                           quality: Optional[int], metadata: Optional[Dict]) -> bool:
        """使用多种方法尝试保存图像"""
        save_methods = [
            ("OpenCV", self._save_with_opencv),
            ("PIL", self._save_with_pil),
            ("PIL(强制转换)", self._save_with_pil_force)
        ]

        for method_name, method in save_methods:
            try:
                self.logger.debug(f"尝试使用 {method_name} 保存: {output_path}")
                success = method(image, output_path, quality, metadata)

                if success:
                    self.logger.info(f"成功使用 {method_name} 保存图像")
                    return True

            except Exception as e:
                self.logger.warning(f"{method_name} 保存失败: {str(e)}")
                continue

        return False

    def _save_with_opencv(self, image: np.ndarray, output_path: Path,
                         quality: Optional[int], metadata: Optional[Dict]) -> bool:
        """使用OpenCV保存图像"""
        try:
            # 转换为BGR格式
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 设置保存参数
            save_params = []
            ext = output_path.suffix.lower()

            if quality is None:
                quality = self.quality_settings.get(ext, 95)

            if ext in ['.jpg', '.jpeg']:
                save_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            elif ext == '.png':
                save_params = [cv2.IMWRITE_PNG_COMPRESSION, min(quality, 9)]
            elif ext == '.webp':
                save_params = [cv2.IMWRITE_WEBP_QUALITY, quality]

            # 处理中文路径
            if not str(output_path).isascii():
                return self._save_opencv_with_bytes(image_bgr, output_path, save_params)

            # 正常保存
            success = cv2.imwrite(str(output_path), image_bgr, save_params)
            return success

        except Exception as e:
            raise Exception(f"OpenCV保存失败: {str(e)}")

    def _save_opencv_with_bytes(self, image_bgr: np.ndarray, output_path: Path,
                               save_params: List) -> bool:
        """使用OpenCV字节流保存（解决中文路径问题）"""
        try:
            # 编码图像
            ext = output_path.suffix.lower()
            success, encoded_img = cv2.imencode(ext, image_bgr, save_params)

            if not success:
                return False

            # 写入文件
            with open(output_path, 'wb') as f:
                f.write(encoded_img.tobytes())

            return True

        except Exception as e:
            raise Exception(f"OpenCV字节流保存失败: {str(e)}")

    def _save_with_pil(self, image: np.ndarray, output_path: Path,
                      quality: Optional[int], metadata: Optional[Dict]) -> bool:
        """使用PIL保存图像"""
        try:
            # 转换为PIL图像
            pil_image = Image.fromarray(image)

            # 设置保存参数
            save_kwargs = {}
            ext = output_path.suffix.lower()

            if quality is None:
                quality = self.quality_settings.get(ext, 95)

            if ext in ['.jpg', '.jpeg']:
                save_kwargs.update({
                    'quality': quality,
                    'optimize': True,
                    'progressive': True
                })
            elif ext == '.png':
                save_kwargs.update({
                    'optimize': True,
                    'compress_level': min(quality, 9)
                })
            elif ext == '.webp':
                save_kwargs.update({
                    'quality': quality,
                    'method': 6
                })

            # 添加元数据
            if metadata:
                if ext in ['.jpg', '.jpeg'] and 'exif' in metadata:
                    save_kwargs['exif'] = metadata['exif']

            # 保存图像
            pil_image.save(output_path, **save_kwargs)
            return True

        except Exception as e:
            raise Exception(f"PIL保存失败: {str(e)}")

    def _save_with_pil_force(self, image: np.ndarray, output_path: Path,
                            quality: Optional[int], metadata: Optional[Dict]) -> bool:
        """强制使用PIL保存（最后的备用方案）"""
        try:
            # 确保图像格式正确
            if image.dtype != np.uint8:
                image = np.clip(image, 0, 255).astype(np.uint8)

            # 转换为PIL图像
            pil_image = Image.fromarray(image, 'RGB')

            # 简单保存，不使用高级参数
            pil_image.save(output_path)
            return True

        except Exception as e:
            raise Exception(f"PIL强制保存失败: {str(e)}")

    def get_save_statistics(self) -> Dict[str, int]:
        """获取保存统计信息"""
        return self.save_stats.copy()

    def reset_statistics(self):
        """重置统计信息"""
        self.save_stats = {
            'total_saved': 0,
            'failed_saves': 0,
            'format_conversions': 0
        }
    
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
