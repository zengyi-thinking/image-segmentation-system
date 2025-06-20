"""
图像诊断工具
用于检测和诊断图像加载问题
"""

import numpy as np
import cv2
from PIL import Image, ExifTags
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import os
import logging
import hashlib
import json


class ImageDiagnostics:
    """图像诊断工具"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 支持的格式和对应的加载器
        self.format_loaders = {
            '.jpg': ['opencv', 'pil'],
            '.jpeg': ['opencv', 'pil'],
            '.png': ['opencv', 'pil'],
            '.bmp': ['opencv', 'pil'],
            '.tiff': ['pil', 'opencv'],
            '.tif': ['pil', 'opencv'],
            '.webp': ['pil', 'opencv'],
            '.gif': ['pil'],
            '.ico': ['pil']
        }
    
    def diagnose_image(self, image_path: Union[str, Path]) -> Dict:
        """
        全面诊断图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            诊断结果字典
        """
        image_path = Path(image_path)
        
        diagnosis = {
            'path': str(image_path),
            'timestamp': 'N/A',
            'file_info': {},
            'format_info': {},
            'load_tests': {},
            'recommendations': [],
            'issues': [],
            'overall_status': 'unknown'
        }
        
        try:
            # 1. 基本文件信息
            diagnosis['file_info'] = self._get_file_info(image_path)
            
            # 2. 格式信息
            diagnosis['format_info'] = self._get_format_info(image_path)
            
            # 3. 加载测试
            diagnosis['load_tests'] = self._test_loading_methods(image_path)
            
            # 4. 生成建议和问题报告
            diagnosis['recommendations'] = self._generate_recommendations(diagnosis)
            diagnosis['issues'] = self._identify_issues(diagnosis)
            
            # 5. 总体状态
            diagnosis['overall_status'] = self._determine_overall_status(diagnosis)
            
        except Exception as e:
            diagnosis['error'] = str(e)
            diagnosis['overall_status'] = 'error'
        
        return diagnosis
    
    def _get_file_info(self, image_path: Path) -> Dict:
        """获取基本文件信息"""
        info = {
            'exists': image_path.exists(),
            'is_file': image_path.is_file() if image_path.exists() else False,
            'size_bytes': 0,
            'readable': False,
            'extension': image_path.suffix.lower(),
            'filename': image_path.name,
            'has_non_ascii': not str(image_path).isascii()
        }
        
        if image_path.exists():
            try:
                stat = image_path.stat()
                info.update({
                    'size_bytes': stat.st_size,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'readable': os.access(image_path, os.R_OK),
                    'modified_time': str(stat.st_mtime)
                })
                
                # 计算文件哈希
                if stat.st_size < 50 * 1024 * 1024:  # 小于50MB才计算哈希
                    with open(image_path, 'rb') as f:
                        content = f.read()
                        info['md5_hash'] = hashlib.md5(content).hexdigest()
                        info['file_signature'] = content[:16].hex() if content else ''
                
            except Exception as e:
                info['file_error'] = str(e)
        
        return info
    
    def _get_format_info(self, image_path: Path) -> Dict:
        """获取图像格式信息"""
        info = {
            'pil_info': {},
            'opencv_info': {},
            'format_supported': False
        }
        
        # PIL信息
        try:
            with Image.open(image_path) as img:
                info['pil_info'] = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    'animated': getattr(img, 'is_animated', False),
                    'n_frames': getattr(img, 'n_frames', 1)
                }
                
                # EXIF信息
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    info['pil_info']['has_exif'] = True
                    info['pil_info']['exif_orientation'] = exif.get(274, 1)  # Orientation tag
                else:
                    info['pil_info']['has_exif'] = False
                
                info['format_supported'] = True
                
        except Exception as e:
            info['pil_error'] = str(e)
        
        # OpenCV信息
        try:
            if str(image_path).isascii():
                img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
                if img is not None:
                    info['opencv_info'] = {
                        'shape': img.shape,
                        'dtype': str(img.dtype),
                        'channels': len(img.shape) if len(img.shape) == 2 else img.shape[2],
                        'size_mb': img.nbytes / (1024 * 1024)
                    }
                else:
                    info['opencv_error'] = "OpenCV返回None"
            else:
                info['opencv_error'] = "路径包含非ASCII字符"
                
        except Exception as e:
            info['opencv_error'] = str(e)
        
        return info
    
    def _test_loading_methods(self, image_path: Path) -> Dict:
        """测试不同的加载方法"""
        tests = {}
        
        # 测试PIL加载
        tests['pil'] = self._test_pil_loading(image_path)
        
        # 测试OpenCV加载
        tests['opencv'] = self._test_opencv_loading(image_path)
        
        # 测试字节流加载
        tests['bytes'] = self._test_bytes_loading(image_path)
        
        return tests
    
    def _test_pil_loading(self, image_path: Path) -> Dict:
        """测试PIL加载"""
        result = {
            'success': False,
            'error': None,
            'load_time': 0,
            'image_info': {}
        }
        
        try:
            import time
            start_time = time.time()
            
            with Image.open(image_path) as img:
                img_rgb = img.convert('RGB')
                img_array = np.array(img_rgb)
                
                result.update({
                    'success': True,
                    'load_time': time.time() - start_time,
                    'image_info': {
                        'shape': img_array.shape,
                        'dtype': str(img_array.dtype),
                        'min_val': int(img_array.min()),
                        'max_val': int(img_array.max()),
                        'mean_val': float(img_array.mean())
                    }
                })
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_opencv_loading(self, image_path: Path) -> Dict:
        """测试OpenCV加载"""
        result = {
            'success': False,
            'error': None,
            'load_time': 0,
            'image_info': {}
        }
        
        try:
            import time
            start_time = time.time()
            
            if str(image_path).isascii():
                img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            else:
                # 使用字节流方式
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                result.update({
                    'success': True,
                    'load_time': time.time() - start_time,
                    'image_info': {
                        'shape': img_rgb.shape,
                        'dtype': str(img_rgb.dtype),
                        'min_val': int(img_rgb.min()),
                        'max_val': int(img_rgb.max()),
                        'mean_val': float(img_rgb.mean())
                    }
                })
            else:
                result['error'] = "OpenCV返回None"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_bytes_loading(self, image_path: Path) -> Dict:
        """测试字节流加载"""
        result = {
            'success': False,
            'error': None,
            'load_time': 0,
            'image_info': {}
        }
        
        try:
            import time
            import io
            start_time = time.time()
            
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = img.convert('RGB')
            img_array = np.array(img_rgb)
            
            result.update({
                'success': True,
                'load_time': time.time() - start_time,
                'image_info': {
                    'shape': img_array.shape,
                    'dtype': str(img_array.dtype),
                    'min_val': int(img_array.min()),
                    'max_val': int(img_array.max()),
                    'mean_val': float(img_array.mean())
                }
            })
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _generate_recommendations(self, diagnosis: Dict) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        file_info = diagnosis.get('file_info', {})
        format_info = diagnosis.get('format_info', {})
        load_tests = diagnosis.get('load_tests', {})
        
        # 文件相关建议
        if not file_info.get('exists'):
            recommendations.append("文件不存在，请检查路径是否正确")
        elif not file_info.get('readable'):
            recommendations.append("文件无读取权限，请检查文件权限设置")
        elif file_info.get('size_bytes', 0) == 0:
            recommendations.append("文件为空，请使用有效的图像文件")
        elif file_info.get('size_mb', 0) > 50:
            recommendations.append("文件过大，建议压缩或调整图像尺寸")
        
        # 路径相关建议
        if file_info.get('has_non_ascii'):
            recommendations.append("文件路径包含非ASCII字符，可能导致OpenCV加载失败")
        
        # 格式相关建议
        if format_info.get('pil_error') and format_info.get('opencv_error'):
            recommendations.append("图像格式可能损坏，尝试使用图像编辑软件重新保存")
        
        # 加载方法建议
        successful_methods = [method for method, result in load_tests.items() 
                            if result.get('success')]
        
        if not successful_methods:
            recommendations.append("所有加载方法都失败，图像文件可能已损坏")
        elif len(successful_methods) == 1:
            recommendations.append(f"建议使用 {successful_methods[0]} 方法加载此图像")
        
        return recommendations
    
    def _identify_issues(self, diagnosis: Dict) -> List[str]:
        """识别问题"""
        issues = []
        
        file_info = diagnosis.get('file_info', {})
        format_info = diagnosis.get('format_info', {})
        load_tests = diagnosis.get('load_tests', {})
        
        # 严重问题
        if not file_info.get('exists'):
            issues.append("CRITICAL: 文件不存在")
        elif file_info.get('size_bytes', 0) == 0:
            issues.append("CRITICAL: 文件为空")
        elif not any(result.get('success') for result in load_tests.values()):
            issues.append("CRITICAL: 所有加载方法都失败")
        
        # 警告问题
        if file_info.get('has_non_ascii'):
            issues.append("WARNING: 路径包含非ASCII字符")
        if file_info.get('size_mb', 0) > 20:
            issues.append("WARNING: 文件较大，可能影响性能")
        if format_info.get('pil_error') or format_info.get('opencv_error'):
            issues.append("WARNING: 部分加载方法失败")
        
        return issues
    
    def _determine_overall_status(self, diagnosis: Dict) -> str:
        """确定总体状态"""
        issues = diagnosis.get('issues', [])
        load_tests = diagnosis.get('load_tests', {})
        
        # 检查是否有严重问题
        if any('CRITICAL' in issue for issue in issues):
            return 'critical'
        
        # 检查是否有成功的加载方法
        if any(result.get('success') for result in load_tests.values()):
            if any('WARNING' in issue for issue in issues):
                return 'warning'
            else:
                return 'good'
        
        return 'error'
    
    def generate_report(self, diagnosis: Dict) -> str:
        """生成诊断报告"""
        report = []
        
        report.append("=" * 60)
        report.append("图像诊断报告")
        report.append("=" * 60)
        
        # 基本信息
        file_info = diagnosis.get('file_info', {})
        report.append(f"文件路径: {diagnosis['path']}")
        report.append(f"文件大小: {file_info.get('size_mb', 0):.2f} MB")
        report.append(f"总体状态: {diagnosis['overall_status'].upper()}")
        
        # 问题列表
        issues = diagnosis.get('issues', [])
        if issues:
            report.append("\n发现的问题:")
            for issue in issues:
                report.append(f"  • {issue}")
        
        # 建议
        recommendations = diagnosis.get('recommendations', [])
        if recommendations:
            report.append("\n修复建议:")
            for rec in recommendations:
                report.append(f"  • {rec}")
        
        # 加载测试结果
        load_tests = diagnosis.get('load_tests', {})
        report.append("\n加载测试结果:")
        for method, result in load_tests.items():
            status = "✅ 成功" if result.get('success') else "❌ 失败"
            time_info = f" ({result.get('load_time', 0):.3f}s)" if result.get('success') else ""
            error_info = f" - {result.get('error')}" if result.get('error') else ""
            report.append(f"  {method}: {status}{time_info}{error_info}")
        
        report.append("=" * 60)
        
        return "\n".join(report)
