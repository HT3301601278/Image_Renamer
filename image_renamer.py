import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pytesseract
from PIL import Image, ImageTk


class ImageRenamer:
    def __init__(self, root):
        self.root = root
        # 添加 DPI 感知
        self.root.tk.call('tk', 'scaling', 2.0)  # 可以根据实际情况调整缩放比例
        self.root.title("图片重命名工具")
        
        # 设置最小窗口大小
        self.root.minsize(1200, 800)
        
        # 初始化变量
        self.images = []
        self.current_image = None
        self.selection_coords = None
        self.start_x = None
        self.start_y = None
        
        # 添加新的状态变量
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.last_x = 0
        self.last_y = 0
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建顶部工具栏
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill="x", pady=(0, 10))
        
        # 创建自定义样式
        style = ttk.Style()
        style.configure('Accent.TButton', 
                       font=('微软雅黑', 11),
                       padding=(15, 8))
        
        # 创建按钮
        self.select_button = ttk.Button(
            self.toolbar, 
            text="选择图片", 
            command=self.select_images,
            style='Accent.TButton'
        )
        self.select_button.pack(side="left", padx=5)
        
        self.rename_button = ttk.Button(
            self.toolbar, 
            text="重命名图片", 
            command=self.rename_images,
            style='Accent.TButton'
        )
        self.rename_button.pack(side="left", padx=5)
        
        # 创建图片显示区域框架
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.pack(fill="both", expand=True)
        
        # 创建画布
        self.canvas = tk.Canvas(
            self.image_frame,
            bg='#f0f0f0',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 修改画布绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        
        # 创建底部状态栏
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill="x", pady=(10, 0))
        
        # 设置状态标签样式
        style.configure('Status.TLabel',
                       font=('微软雅黑', 10),
                       padding=(5, 5))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="",
            wraplength=1000,
            style='Status.TLabel'
        )
        self.status_label.pack(fill="x")
        
        # 设置提示标签样式
        style.configure('Tip.TLabel',
                       font=('微软雅黑', 9),
                       foreground='#666666',
                       padding=(5, 5))
        
        # 添加提示信息
        self.tip_label = ttk.Label(
            self.status_frame,
            text="提示：在图片上拖动鼠标选择要识别的文字区域",
            style='Tip.TLabel'
        )
        self.tip_label.pack(fill="x")
        
    def update_status(self, message):
        """更新状态信息"""
        self.status_label.config(text=message)
        self.root.update()
        
    def select_images(self):
        # 选择多个图片文件
        file_paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_paths:
            self.images = list(file_paths)
            self.show_image(self.images[0])
            self.update_status(f"已选择 {len(self.images)} 个文件")
    
    def show_image(self, image_path):
        # 显示图片在画布上
        image = Image.open(image_path)
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算合适的显示尺寸，使用屏幕尺寸的一定比例
        display_width = int(screen_width * 0.7)
        display_height = int(screen_height * 0.7)
        display_size = (display_width, display_height)
        
        # 保持纵横比进行缩放
        image.thumbnail(display_size, Image.Resampling.LANCZOS)
        self.current_image = ImageTk.PhotoImage(image)
        
        # 调整画布大小
        self.canvas.config(width=image.width, height=image.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.current_image)
        
    def on_press(self, event):
        """处理鼠标按下事件"""
        self.last_x = event.x
        self.last_y = event.y
        
        if hasattr(self, 'selection_rect'):
            # 检查是否点击了调整大小的边缘
            edge = self.get_resize_edge(event.x, event.y)
            if edge:
                self.resizing = True
                self.resize_edge = edge
                return
                
            # 检查是否在选择框内
            coords = self.canvas.coords(self.selection_rect)
            if (coords[0] <= event.x <= coords[2] and 
                coords[1] <= event.y <= coords[3]):
                self.dragging = True
                return
        
        # 如果既不是调整大小也不是拖动，就开始新的选择
        self.start_selection(event)
    
    def on_drag(self, event):
        """处理鼠标拖动事件"""
        if self.dragging:
            # 计算移动距离
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # 更新选择框位置
            coords = self.canvas.coords(self.selection_rect)
            new_coords = [
                coords[0] + dx, coords[1] + dy,
                coords[2] + dx, coords[3] + dy
            ]
            self.canvas.coords(self.selection_rect, *new_coords)
            self.selection_coords = tuple(map(int, new_coords))
            
        elif self.resizing:
            # 处理调整大小
            coords = list(self.canvas.coords(self.selection_rect))
            if 'e' in self.resize_edge:  # 东边
                coords[2] = event.x
            if 'w' in self.resize_edge:  # 西边
                coords[0] = event.x
            if 's' in self.resize_edge:  # 南边
                coords[3] = event.y
            if 'n' in self.resize_edge:  # 北边
                coords[1] = event.y
                
            # 确保选择框不会反转
            if coords[2] < coords[0]:
                coords[0], coords[2] = coords[2], coords[0]
            if coords[3] < coords[1]:
                coords[1], coords[3] = coords[3], coords[1]
                
            self.canvas.coords(self.selection_rect, *coords)
            self.selection_coords = tuple(map(int, coords))
            
        else:
            # 正常的框选更新
            self.update_selection(event)
            
        self.last_x = event.x
        self.last_y = event.y
        self.update_status(f"已选择区域: {self.selection_coords}")
    
    def on_release(self, event):
        """处理鼠标释放事件"""
        if self.dragging or self.resizing:
            # 更新最终坐标
            coords = self.canvas.coords(self.selection_rect)
            self.selection_coords = tuple(map(int, coords))
        else:
            # 正常的框选结束
            self.end_selection(event)
            
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
    
    def get_resize_edge(self, x, y, threshold=8):
        """检测鼠标是否在选择框边缘"""
        if not hasattr(self, 'selection_rect'):
            return None
            
        coords = self.canvas.coords(self.selection_rect)
        edges = []
        
        # 检查是否在水平边缘
        if abs(y - coords[1]) < threshold:  # 北边
            edges.append('n')
        elif abs(y - coords[3]) < threshold:  # 南边
            edges.append('s')
            
        # 检查是否在垂直边缘
        if abs(x - coords[0]) < threshold:  # 西边
            edges.append('w')
        elif abs(x - coords[2]) < threshold:  # 东边
            edges.append('e')
            
        return ''.join(edges) if edges else None
    
    def on_motion(self, event):
        """处理鼠标移动事件，更新鼠标样式"""
        if not hasattr(self, 'selection_rect'):
            return
            
        edge = self.get_resize_edge(event.x, event.y)
        if edge:
            if edge in ('n', 's'):
                self.canvas.config(cursor='sb_v_double_arrow')
            elif edge in ('e', 'w'):
                self.canvas.config(cursor='sb_h_double_arrow')
            elif edge in ('nw', 'se'):
                self.canvas.config(cursor='size_nw_se')
            elif edge in ('ne', 'sw'):
                self.canvas.config(cursor='size_ne_sw')
        else:
            coords = self.canvas.coords(self.selection_rect)
            if (coords[0] <= event.x <= coords[2] and 
                coords[1] <= event.y <= coords[3]):
                self.canvas.config(cursor='fleur')  # 移动光标
            else:
                self.canvas.config(cursor='')  # 默认光标
    
    def start_selection(self, event):
        # 开始框选
        self.start_x = event.x
        self.start_y = event.y
        if hasattr(self, 'selection_rect'):
            self.canvas.delete(self.selection_rect)
            
    def update_selection(self, event):
        # 更新选择框
        if hasattr(self, 'selection_rect'):
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="red"
        )
        
    def end_selection(self, event):
        # 结束框选，保存坐标
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        self.selection_coords = (x1, y1, x2, y2)
        self.update_status(f"已选择区域: {self.selection_coords}")
        
    def rename_images(self):
        if not self.selection_coords or not self.images:
            messagebox.showwarning("警告", "请先选择图片并框选区域")
            return
            
        for image_path in self.images:
            try:
                self.update_status(f"正在处理图片: {image_path}")
                
                # 打开图片
                image = Image.open(image_path)
                
                # 获取原始图片大小与显示图片的比例
                display_ratio = image.size[0] / self.canvas.winfo_width()
                
                # 调整选择框坐标以匹配原始图片尺寸
                real_coords = [int(c * display_ratio) for c in self.selection_coords]
                
                # 裁剪选中区域
                cropped = image.crop(real_coords)
                
                # OCR识别
                text = pytesseract.image_to_string(cropped, lang='chi_sim').strip()
                self.update_status(f"识别文本: {text}")
                
                if text:
                    # 获取原始文件扩展名
                    _, ext = os.path.splitext(image_path)
                    # 构建新文件名（移除非法字符）
                    new_name = ''.join(c for c in text if c.isalnum() or c in '._- ') + ext
                    new_path = os.path.join(os.path.dirname(image_path), new_name)
                    
                    self.update_status(f"重命名文件为: {new_name}")
                    
                    # 重命名文件
                    os.rename(image_path, new_path)
                else:
                    self.update_status("OCR未能识别出文字")
                    
            except Exception as e:
                self.update_status(f"处理图片出错: {str(e)}")
                
        messagebox.showinfo("完成", "图片重命名完成！")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRenamer(root)
    root.mainloop() 