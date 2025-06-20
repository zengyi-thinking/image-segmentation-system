"""
图像显示组件
处理图像的显示、缩放和可视化
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from .style_manager import get_style_manager


class ImageDisplay:
    """图像显示组件"""
    
    def __init__(self, parent, image_loader=None):
        """
        初始化图像显示组件
        
        Args:
            parent: 父容器
            image_loader: 图像加载器实例
        """
        self.parent = parent
        self.image_loader = image_loader
        self.style_manager = get_style_manager()
        
        # 创建主框架
        self.main_frame = self.style_manager.create_labelframe(
            parent,
            text="🖼️ 图像显示",
            padding=15,
            style_name='Heading.TLabelFrame'
        )
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.create_notebook()
        
        # 创建画布
        self.create_canvases()
        
        # 添加占位符
        self.add_placeholders()
    
    def create_notebook(self):
        """创建标签页容器"""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
    
    def create_canvases(self):
        """创建各个画布"""
        # 原始图像标签页
        self.original_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.original_frame, text="📷 原始图像")
        
        self.original_canvas = self.create_canvas(self.original_frame)
        
        # 分割结果标签页
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="🎨 分割结果")
        
        self.result_canvas = self.create_canvas(self.result_frame)
        
        # 边界显示标签页
        self.boundary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.boundary_frame, text="🔍 边界显示")
        
        self.boundary_canvas = self.create_canvas(self.boundary_frame)
    
    def create_canvas(self, parent):
        """创建单个画布"""
        canvas = tk.Canvas(parent, bg='#f8f9fa',
                          relief=tk.FLAT, borderwidth=0,
                          highlightthickness=1,
                          highlightcolor='#bdc3c7')
        canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return canvas
    
    def add_placeholders(self):
        """添加占位符文本"""
        self.add_canvas_placeholder(self.original_canvas, "📷 请选择图像文件")
        self.add_canvas_placeholder(self.result_canvas, "🎨 分割结果将在这里显示")
        self.add_canvas_placeholder(self.boundary_canvas, "🔍 边界检测结果将在这里显示")
    
    def add_canvas_placeholder(self, canvas, text):
        """为画布添加占位符文本"""
        def draw_placeholder():
            canvas.delete("placeholder")
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width > 1 and height > 1:
                canvas.create_text(width//2, height//2,
                                  text=text,
                                  font=('Microsoft YaHei UI', 12),
                                  fill='#95a5a6',
                                  tags="placeholder")
        
        canvas.bind('<Configure>', lambda e: draw_placeholder())
        canvas.after(100, draw_placeholder)
    
    def display_image(self, canvas, image):
        """在指定画布上显示图像"""
        try:
            # 获取画布尺寸
            canvas.update()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布还没有正确初始化，延迟显示
                canvas.after(100, lambda: self.display_image(canvas, image))
                return
            
            # 调整图像大小以适应画布（留出边距）
            display_width = canvas_width - 20
            display_height = canvas_height - 20
            
            if self.image_loader:
                image_resized = self.image_loader.resize_image(
                    image, (display_width, display_height), keep_aspect_ratio=True
                )
            else:
                # 简单的缩放方法
                image_resized = self._simple_resize(image, display_width, display_height)
            
            # 转换为PIL图像并显示
            pil_image = Image.fromarray(image_resized)
            photo = ImageTk.PhotoImage(pil_image)
            
            # 清除画布并显示新图像
            canvas.delete("all")
            
            # 添加阴影效果
            self._add_shadow_effect(canvas, image_resized, canvas_width, canvas_height)
            
            # 显示图像
            canvas.create_image(canvas_width//2, canvas_height//2,
                               image=photo, anchor=tk.CENTER, tags="image")
            
            # 保存引用以防止垃圾回收
            canvas.image = photo
            
        except Exception as e:
            print(f"显示图像时发生错误: {e}")
            self._show_error_on_canvas(canvas, str(e))
    
    def _simple_resize(self, image, target_width, target_height):
        """简单的图像缩放方法"""
        try:
            from PIL import Image as PILImage
            
            # 转换为PIL图像
            if isinstance(image, np.ndarray):
                pil_image = PILImage.fromarray(image)
            else:
                pil_image = image
            
            # 计算缩放比例
            width_ratio = target_width / pil_image.width
            height_ratio = target_height / pil_image.height
            scale = min(width_ratio, height_ratio)
            
            new_width = int(pil_image.width * scale)
            new_height = int(pil_image.height * scale)
            
            # 缩放图像
            resized = pil_image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            
            # 转换回numpy数组
            return np.array(resized)
            
        except Exception as e:
            print(f"图像缩放失败: {e}")
            return image
    
    def _add_shadow_effect(self, canvas, image_resized, canvas_width, canvas_height):
        """添加阴影效果"""
        try:
            shadow_offset = 3
            canvas.create_rectangle(
                canvas_width//2 - image_resized.shape[1]//2 + shadow_offset,
                canvas_height//2 - image_resized.shape[0]//2 + shadow_offset,
                canvas_width//2 + image_resized.shape[1]//2 + shadow_offset,
                canvas_height//2 + image_resized.shape[0]//2 + shadow_offset,
                fill='#bdc3c7', outline='', tags="shadow"
            )
        except Exception as e:
            print(f"添加阴影效果失败: {e}")
    
    def _show_error_on_canvas(self, canvas, error_message):
        """在画布上显示错误信息"""
        canvas.delete("all")
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        canvas.create_text(canvas_width//2, canvas_height//2,
                          text=f"❌ 显示错误\n{error_message}",
                          font=('Microsoft YaHei UI', 10),
                          fill='#e74c3c',
                          justify=tk.CENTER)
    
    def display_original_image(self, image):
        """显示原始图像"""
        self.display_image(self.original_canvas, image)
        
        # 清除其他画布的占位符
        self.result_canvas.delete("placeholder")
        self.boundary_canvas.delete("placeholder")
    
    def display_segmentation_result(self, segmented_image):
        """显示分割结果"""
        self.display_image(self.result_canvas, segmented_image)
        
        # 切换到分割结果标签页
        self.notebook.select(1)
    
    def display_boundary_result(self, boundary_image):
        """显示边界检测结果"""
        self.display_image(self.boundary_canvas, boundary_image)
    
    def clear_results(self):
        """清除分割结果显示"""
        self.result_canvas.delete("all")
        self.boundary_canvas.delete("all")
        
        # 重新添加占位符
        self.add_canvas_placeholder(self.result_canvas, "🎨 分割结果将在这里显示")
        self.add_canvas_placeholder(self.boundary_canvas, "🔍 边界检测结果将在这里显示")
    
    def switch_to_tab(self, tab_index):
        """切换到指定标签页"""
        try:
            self.notebook.select(tab_index)
        except Exception as e:
            print(f"切换标签页失败: {e}")
    
    def get_current_tab(self):
        """获取当前标签页索引"""
        try:
            return self.notebook.index(self.notebook.select())
        except:
            return 0
    
    def export_current_image(self):
        """导出当前显示的图像"""
        try:
            current_tab = self.get_current_tab()
            
            if current_tab == 0:
                canvas = self.original_canvas
                image_type = "原始图像"
            elif current_tab == 1:
                canvas = self.result_canvas
                image_type = "分割结果"
            else:
                canvas = self.boundary_canvas
                image_type = "边界检测"
            
            # 检查是否有图像
            if hasattr(canvas, 'image') and canvas.image:
                return canvas.image, image_type
            else:
                return None, None
                
        except Exception as e:
            print(f"导出图像失败: {e}")
            return None, None
    
    def zoom_image(self, canvas, scale_factor):
        """缩放图像显示"""
        # 这个功能可以在未来实现
        pass
    
    def reset_view(self):
        """重置视图"""
        # 重新显示所有图像以适应当前画布大小
        for canvas in [self.original_canvas, self.result_canvas, self.boundary_canvas]:
            if hasattr(canvas, 'image') and canvas.image:
                # 触发重新显示
                canvas.event_generate('<Configure>')
    
    def get_canvas_info(self):
        """获取画布信息"""
        return {
            'original_size': (self.original_canvas.winfo_width(), self.original_canvas.winfo_height()),
            'result_size': (self.result_canvas.winfo_width(), self.result_canvas.winfo_height()),
            'boundary_size': (self.boundary_canvas.winfo_width(), self.boundary_canvas.winfo_height()),
            'current_tab': self.get_current_tab()
        }
