"""
进度指示器和用户反馈系统
提供美观的进度对话框、状态指示器和用户友好的反馈信息
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass

from gui.theme_manager import get_theme_manager
from utils.logger import LoggerMixin


@dataclass
class ProgressInfo:
    """进度信息"""
    current: int
    total: int
    message: str
    detail: str = ""
    percentage: float = 0.0
    elapsed_time: float = 0.0
    estimated_time: float = 0.0


class ProgressDialog(LoggerMixin):
    """进度对话框"""
    
    def __init__(self, parent, title: str = "处理中...", 
                 message: str = "请稍候...", 
                 cancelable: bool = True,
                 show_details: bool = True):
        """
        初始化进度对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 初始消息
            cancelable: 是否可取消
            show_details: 是否显示详细信息
        """
        super().__init__()
        self.parent = parent
        self.title = title
        self.cancelable = cancelable
        self.show_details = show_details
        
        # 状态变量
        self.cancelled = False
        self.completed = False
        self.progress_info = ProgressInfo(0, 100, message)
        self.start_time = time.time()
        
        # 回调函数
        self.cancel_callback = None
        self.complete_callback = None
        
        # 主题管理器
        self.theme_manager = get_theme_manager()
        
        # 创建对话框
        self._create_dialog()
        
        self.logger.info(f"进度对话框创建: {title}")
    
    def _create_dialog(self):
        """创建对话框界面"""
        # 创建顶级窗口
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        
        # 设置为模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 应用主题
        self.theme_manager.apply_theme_to_widget(self.dialog)
        
        # 创建主框架
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题标签
        self.title_label = ttk.Label(
            main_frame,
            text=self.progress_info.message,
            font=('Microsoft YaHei UI', 12, 'bold')
        )
        self.title_label.pack(pady=(0, 15))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # 百分比标签
        self.percentage_label = ttk.Label(
            main_frame,
            text="0%",
            font=('Microsoft YaHei UI', 10)
        )
        self.percentage_label.pack()
        
        # 详细信息框架
        if self.show_details:
            details_frame = ttk.LabelFrame(main_frame, text="详细信息", padding=10)
            details_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
            
            # 当前操作
            self.current_label = ttk.Label(
                details_frame,
                text="准备中...",
                font=('Microsoft YaHei UI', 9)
            )
            self.current_label.pack(anchor=tk.W, pady=(0, 5))
            
            # 时间信息
            time_frame = ttk.Frame(details_frame)
            time_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(time_frame, text="已用时间:", font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
            self.elapsed_label = ttk.Label(time_frame, text="00:00", font=('Microsoft YaHei UI', 9))
            self.elapsed_label.pack(side=tk.LEFT, padx=(5, 20))
            
            ttk.Label(time_frame, text="预计剩余:", font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
            self.remaining_label = ttk.Label(time_frame, text="--:--", font=('Microsoft YaHei UI', 9))
            self.remaining_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0))
        
        if self.cancelable:
            self.cancel_button = ttk.Button(
                button_frame,
                text="取消",
                command=self._on_cancel,
                width=12
            )
            self.cancel_button.pack(side=tk.RIGHT)
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # 开始更新循环
        self._update_display()
    
    def _center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        
        # 获取父窗口位置和大小
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算对话框位置
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _update_display(self):
        """更新显示内容"""
        if self.dialog.winfo_exists():
            try:
                # 更新进度条
                self.progress_var.set(self.progress_info.percentage)
                
                # 更新百分比
                self.percentage_label.config(text=f"{self.progress_info.percentage:.1f}%")
                
                # 更新标题
                self.title_label.config(text=self.progress_info.message)
                
                # 更新详细信息
                if self.show_details:
                    self.current_label.config(text=self.progress_info.detail or "处理中...")
                    
                    # 更新时间信息
                    elapsed = time.time() - self.start_time
                    self.elapsed_label.config(text=self._format_time(elapsed))
                    
                    if self.progress_info.percentage > 0:
                        estimated_total = elapsed / (self.progress_info.percentage / 100)
                        remaining = max(0, estimated_total - elapsed)
                        self.remaining_label.config(text=self._format_time(remaining))
                
                # 如果未完成且未取消，继续更新
                if not self.completed and not self.cancelled:
                    self.dialog.after(100, self._update_display)
                
            except tk.TclError:
                # 对话框已关闭
                pass
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 0:
            return "--:--"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_cancel(self):
        """取消按钮回调"""
        if not self.cancelable:
            return
        
        self.cancelled = True
        
        if self.cancel_callback:
            try:
                self.cancel_callback()
            except Exception as e:
                self.logger.error("取消回调执行失败", exception=e)
        
        self.close()
    
    def update_progress(self, current: int, total: int, message: str = None, detail: str = None):
        """更新进度"""
        self.progress_info.current = current
        self.progress_info.total = total
        self.progress_info.percentage = (current / total * 100) if total > 0 else 0
        
        if message:
            self.progress_info.message = message
        
        if detail:
            self.progress_info.detail = detail
        
        self.logger.debug(f"进度更新: {current}/{total} ({self.progress_info.percentage:.1f}%)")
    
    def set_indeterminate(self, active: bool = True):
        """设置不确定进度模式"""
        if active:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.percentage_label.config(text="处理中...")
        else:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
    
    def complete(self, message: str = "完成"):
        """标记为完成"""
        self.completed = True
        self.progress_info.message = message
        self.progress_info.percentage = 100
        
        if self.complete_callback:
            try:
                self.complete_callback()
            except Exception as e:
                self.logger.error("完成回调执行失败", exception=e)
        
        self.logger.info(f"进度对话框完成: {message}")
        
        # 延迟关闭
        self.dialog.after(1000, self.close)
    
    def close(self):
        """关闭对话框"""
        try:
            if self.dialog.winfo_exists():
                self.dialog.grab_release()
                self.dialog.destroy()
        except tk.TclError:
            pass
    
    def set_cancel_callback(self, callback: Callable[[], None]):
        """设置取消回调"""
        self.cancel_callback = callback
    
    def set_complete_callback(self, callback: Callable[[], None]):
        """设置完成回调"""
        self.complete_callback = callback


class StatusBar(LoggerMixin):
    """状态栏组件"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        
        # 创建状态栏
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态标签
        self.status_label = ttk.Label(
            self.status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 进度条（小型）
        self.mini_progress = ttk.Progressbar(
            self.status_frame,
            length=100,
            height=15,
            mode='determinate'
        )
        
        # 内存使用标签
        self.memory_label = ttk.Label(
            self.status_frame,
            text="内存: 0MB",
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            padding=(5, 2),
            width=12
        )
        self.memory_label.pack(side=tk.RIGHT, padx=(2, 0))
        
        # 开始状态更新
        self._update_status()
    
    def set_status(self, message: str, show_progress: bool = False):
        """设置状态消息"""
        self.status_label.config(text=message)
        
        if show_progress:
            self.mini_progress.pack(side=tk.RIGHT, padx=(5, 2))
            self.mini_progress.config(mode='indeterminate')
            self.mini_progress.start(10)
        else:
            self.mini_progress.stop()
            self.mini_progress.pack_forget()
    
    def set_progress(self, percentage: float):
        """设置进度"""
        if not self.mini_progress.winfo_viewable():
            self.mini_progress.pack(side=tk.RIGHT, padx=(5, 2))
        
        self.mini_progress.config(mode='determinate')
        self.mini_progress['value'] = percentage
    
    def _update_status(self):
        """更新状态信息"""
        try:
            # 更新内存使用
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.config(text=f"内存: {memory_mb:.0f}MB")
            
        except Exception:
            pass
        
        # 每5秒更新一次
        self.parent.after(5000, self._update_status)


def show_progress_dialog(parent, title: str, message: str, 
                        task_func: Callable, 
                        cancelable: bool = True,
                        show_details: bool = True) -> Any:
    """
    显示进度对话框并执行任务
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 初始消息
        task_func: 要执行的任务函数
        cancelable: 是否可取消
        show_details: 是否显示详细信息
        
    Returns:
        任务执行结果
    """
    result = None
    exception = None
    
    # 创建进度对话框
    progress = ProgressDialog(parent, title, message, cancelable, show_details)
    
    def task_wrapper():
        nonlocal result, exception
        try:
            result = task_func(progress)
            progress.complete("任务完成")
        except Exception as e:
            exception = e
            progress.complete("任务失败")
    
    # 在后台线程执行任务
    task_thread = threading.Thread(target=task_wrapper, daemon=True)
    task_thread.start()
    
    # 等待任务完成或取消
    while task_thread.is_alive() and not progress.cancelled:
        parent.update()
        time.sleep(0.1)
    
    # 如果任务被取消
    if progress.cancelled:
        return None
    
    # 如果有异常，抛出
    if exception:
        raise exception
    
    return result
