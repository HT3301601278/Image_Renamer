import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import os


pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'

class ImageRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("图片重命名工具")
        
        # 初始化变量
        self.images = []
        self.current_image = None
        self.selection_coords = None
        self.start_x = None
        self.start_y = None
        
        # 创建画布
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill="both", expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # 创建按钮
        self.select_button = tk.Button(root, text="选择图片", command=self.select_images)
        self.select_button.pack(side="left", padx=5, pady=5)
        
        self.rename_button = tk.Button(root, text="重命名图片", command=self.rename_images)
        self.rename_button.pack(side="left", padx=5, pady=5)
        
        # 添加状态标签
        self.status_label = tk.Label(root, text="", wraplength=400)
        self.status_label.pack(side="bottom", pady=5)
        
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
        # 调整图片大小以适应窗口
        display_size = (800, 600)  # 可以根据需要调整
        image.thumbnail(display_size, Image.Resampling.LANCZOS)
        self.current_image = ImageTk.PhotoImage(image)
        self.canvas.config(width=image.width, height=image.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.current_image)
        
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