import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes

import pytesseract
from PIL import Image, ImageTk


class ImageRenamer:
    def __init__(self, root):
        self.root = root

        # 高分辨率屏幕适配
        try:
            # 告诉Windows使用Per-Monitor DPI感知
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            # 获取主显示器的DPI
            dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id()) / 96.0
            # 根据DPI设置缩放
            self.root.tk.call('tk', 'scaling', dpi)
        except Exception:
            # 如果上述方法失败，使用传统方法
            self.root.tk.call('tk', 'scaling', 1.5)

        self.root.title("图片重命名工具")
        self.root.configure(bg="#f5f5f7")

        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)

        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.ico")  # 如果有图标文件，可以设置
        except:
            pass

        # 设置最小窗口大小
        self.root.minsize(1200, 800)

        # 初始化变量
        self.images = []
        self.current_image = None
        self.current_image_index = 0
        self.selection_coords = None
        self.start_x = None
        self.start_y = None

        # 添加状态变量
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.last_x = 0
        self.last_y = 0

        # 创建自定义样式
        self.create_styles()

        # 创建主框架
        self.main_frame = ttk.Frame(root, style='Main.TFrame')
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 创建顶部工具栏
        self.create_toolbar()

        # 创建图片显示区域
        self.create_image_area()

        # 创建底部状态栏
        self.create_status_bar()

    def create_styles(self):
        """创建自定义样式"""
        style = ttk.Style()

        # 设置主题
        try:
            style.theme_use('clam')  # 使用更现代的主题
        except:
            pass

        # 主框架样式
        style.configure('Main.TFrame', background='#f5f5f7')

        # 工具栏样式
        style.configure('Toolbar.TFrame', background='#f5f5f7')

        # 按钮样式
        style.configure('Accent.TButton',
                        font=('微软雅黑', 11),
                        padding=(15, 8))

        # 悬停按钮样式
        style.map('Accent.TButton',
                  background=[('active', '#4a86e8')],
                  foreground=[('active', 'white')])

        # 图片区域样式
        style.configure('ImageArea.TFrame', background='#ffffff')

        # 状态栏样式
        style.configure('Status.TFrame', background='#f5f5f7')

        # 状态标签样式
        style.configure('Status.TLabel',
                        font=('微软雅黑', 10),
                        background='#f5f5f7',
                        padding=(5, 5))

        # 提示标签样式
        style.configure('Tip.TLabel',
                        font=('微软雅黑', 9),
                        foreground='#666666',
                        background='#f5f5f7',
                        padding=(5, 5))

        # 导航按钮样式
        style.configure('Nav.TButton',
                        font=('微软雅黑', 12),
                        padding=(10, 5))

    def create_toolbar(self):
        """创建顶部工具栏"""
        self.toolbar = ttk.Frame(self.main_frame, style='Toolbar.TFrame')
        self.toolbar.pack(fill="x", pady=(0, 15))

        # 创建标题标签
        title_label = ttk.Label(
            self.toolbar,
            text="图片重命名工具",
            font=('微软雅黑', 16, 'bold'),
            background='#f5f5f7'
        )
        title_label.pack(side="left", padx=10)

        # 创建按钮
        self.select_button = ttk.Button(
            self.toolbar,
            text="选择图片",
            command=self.select_images,
            style='Accent.TButton'
        )
        self.select_button.pack(side="left", padx=10)

        self.rename_button = ttk.Button(
            self.toolbar,
            text="重命名图片",
            command=self.rename_images,
            style='Accent.TButton'
        )
        self.rename_button.pack(side="left", padx=10)

        # 添加帮助按钮
        self.help_button = ttk.Button(
            self.toolbar,
            text="帮助",
            command=self.show_help,
            style='Accent.TButton'
        )
        self.help_button.pack(side="right", padx=10)

    def create_image_area(self):
        """创建图片显示区域"""
        # 创建图片显示区域框架
        self.image_container = ttk.Frame(self.main_frame, style='ImageArea.TFrame')
        self.image_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建画布
        self.canvas_frame = ttk.Frame(self.image_container)
        self.canvas_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas = tk.Canvas(
            self.canvas_frame,
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

        # 创建导航按钮框架
        self.nav_frame = ttk.Frame(self.image_container, style='Toolbar.TFrame')
        self.nav_frame.pack(fill="x", pady=10)

        # 添加上一张/下一张按钮
        self.prev_button = ttk.Button(
            self.nav_frame,
            text="上一张",
            command=self.show_prev_image,
            style='Nav.TButton'
        )
        self.prev_button.pack(side="left", padx=10)

        # 添加图片计数标签
        self.count_label = ttk.Label(
            self.nav_frame,
            text="0/0",
            font=('微软雅黑', 11),
            background='#f5f5f7'
        )
        self.count_label.pack(side="left", padx=20)

        self.next_button = ttk.Button(
            self.nav_frame,
            text="下一张",
            command=self.show_next_image,
            style='Nav.TButton'
        )
        self.next_button.pack(side="left", padx=10)

        # 添加清除选择按钮
        self.clear_button = ttk.Button(
            self.nav_frame,
            text="清除选择",
            command=self.clear_selection,
            style='Nav.TButton'
        )
        self.clear_button.pack(side="right", padx=10)

    def create_status_bar(self):
        """创建底部状态栏"""
        self.status_frame = ttk.Frame(self.main_frame, style='Status.TFrame')
        self.status_frame.pack(fill="x", pady=(15, 0))

        # 状态信息
        self.status_label = ttk.Label(
            self.status_frame,
            text="准备就绪",
            wraplength=1000,
            style='Status.TLabel'
        )
        self.status_label.pack(fill="x")

        # 提示信息
        self.tip_label = ttk.Label(
            self.status_frame,
            text="提示：在图片上拖动鼠标选择要识别的文字区域，可以拖动或调整选择框大小",
            style='Tip.TLabel'
        )
        self.tip_label.pack(fill="x")

    def update_status(self, message):
        """更新状态信息"""
        self.status_label.config(text=message)
        self.root.update()

    def update_image_counter(self):
        """更新图片计数器"""
        if self.images:
            self.count_label.config(text=f"{self.current_image_index + 1}/{len(self.images)}")
        else:
            self.count_label.config(text="0/0")

    def select_images(self):
        """选择多个图片文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_paths:
            self.images = list(file_paths)
            self.current_image_index = 0
            self.show_image(self.images[0])
            self.update_status(f"已选择 {len(self.images)} 个文件")
            self.update_image_counter()

            # 更新导航按钮状态
            self.update_nav_buttons()

    def show_image(self, image_path):
        """显示图片在画布上"""
        try:
            # 清除现有选择框
            if hasattr(self, 'selection_rect'):
                self.canvas.delete(self.selection_rect)
                self.selection_coords = None

            # 打开图片
            image = Image.open(image_path)

            # 获取画布尺寸
            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # 如果画布尚未正确初始化，使用默认尺寸
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600

            # 计算缩放比例，保持纵横比
            img_width, img_height = image.size
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            scale_ratio = min(width_ratio, height_ratio) * 0.9  # 留出一些边距

            # 计算新尺寸
            new_width = int(img_width * scale_ratio)
            new_height = int(img_height * scale_ratio)

            # 缩放图片
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.current_image = ImageTk.PhotoImage(resized_image)

            # 清除画布并显示新图片
            self.canvas.delete("all")

            # 计算居中位置
            x_pos = (canvas_width - new_width) // 2
            y_pos = (canvas_height - new_height) // 2

            # 在画布上显示图片
            self.canvas.create_image(x_pos, y_pos, anchor="nw", image=self.current_image)

            # 保存图片显示位置和尺寸，用于坐标转换
            self.image_display_info = {
                'x': x_pos,
                'y': y_pos,
                'width': new_width,
                'height': new_height,
                'original_width': img_width,
                'original_height': img_height
            }

            # 更新状态
            self.update_status(f"当前图片: {os.path.basename(image_path)}")

        except Exception as e:
            self.update_status(f"加载图片出错: {str(e)}")

    def show_prev_image(self):
        """显示上一张图片"""
        if not self.images or self.current_image_index <= 0:
            return

        self.current_image_index -= 1
        self.show_image(self.images[self.current_image_index])
        self.update_image_counter()
        self.update_nav_buttons()

    def show_next_image(self):
        """显示下一张图片"""
        if not self.images or self.current_image_index >= len(self.images) - 1:
            return

        self.current_image_index += 1
        self.show_image(self.images[self.current_image_index])
        self.update_image_counter()
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """更新导航按钮状态"""
        if not self.images:
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.clear_button.config(state="disabled")
            return

        # 更新上一张按钮状态
        if self.current_image_index <= 0:
            self.prev_button.config(state="disabled")
        else:
            self.prev_button.config(state="normal")

        # 更新下一张按钮状态
        if self.current_image_index >= len(self.images) - 1:
            self.next_button.config(state="disabled")
        else:
            self.next_button.config(state="normal")

            # 更新清除选择按钮状态
            if hasattr(self, 'selection_rect'):
                self.clear_button.config(state="normal")
            else:
                self.clear_button.config(state="disabled")

    def clear_selection(self):
        """清除当前选择框"""
        if hasattr(self, 'selection_rect'):
            self.canvas.delete(self.selection_rect)
            delattr(self, 'selection_rect')
            self.selection_coords = None
            self.update_status("已清除选择区域")
            self.canvas.config(cursor='')

    def show_help(self):
        """显示帮助信息"""
        help_text = """使用说明：

1. 点击"选择图片"按钮选择要处理的图片文件
2. 在图片上按住鼠标左键拖动来选择要识别的文字区域
3. 可以拖动选择框或通过边缘调整其大小
4. 使用"上一张"/"下一张"按钮浏览多张图片
5. 点击"重命名图片"按钮，程序将自动识别选中区域的文字并重命名图片
6. 使用"清除选择"按钮可以清除当前的选择框

注意：
- 支持的图片格式：PNG、JPG、JPEG、BMP、GIF
- 文字识别支持中文和英文
- 重命名时会自动过滤掉不支持的文件名字符"""

        messagebox.showinfo("使用帮助", help_text)

    def get_display_to_original_ratio(self):
        """获取显示图片与原始图片的比例"""
        if not hasattr(self, 'image_display_info'):
            return 1.0
        return (self.image_display_info['original_width'] /
                self.image_display_info['width'])

    def rename_images(self):
        if not self.selection_coords or not self.images:
            messagebox.showwarning("警告", "请先选择图片并框选区域")
            return

        total = len(self.images)
        success = 0
        failed = 0

        for i, image_path in enumerate(self.images, 1):
            try:
                self.update_status(f"正在处理第 {i}/{total} 张图片: {image_path}")

                # 打开图片
                image = Image.open(image_path)

                # 获取比例并调整坐标
                ratio = self.get_display_to_original_ratio()
                real_coords = [int(c * ratio) for c in self.selection_coords]

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

                    # 检查文件名是否已存在
                    base, ext = os.path.splitext(new_path)
                    counter = 1
                    while os.path.exists(new_path):
                        new_path = f"{base}_{counter}{ext}"
                        counter += 1

                    self.update_status(f"重命名文件为: {os.path.basename(new_path)}")
                    os.rename(image_path, new_path)
                    success += 1
                else:
                    self.update_status("OCR未能识别出文字")
                    failed += 1

            except Exception as e:
                self.update_status(f"处理图片出错: {str(e)}")
                failed += 1

        # 显示处理结果统计
        result_message = f"处理完成！\n成功: {success} 张\n失败: {failed} 张"
        messagebox.showinfo("完成", result_message)

    def on_press(self, event):
        """处理鼠标按下事件"""
        if not hasattr(self, 'image_display_info'):
            return

        # 获取相对于图片显示区域的坐标
        x = event.x - self.image_display_info['x']
        y = event.y - self.image_display_info['y']

        # 检查是否在图片区域内
        if (0 <= x <= self.image_display_info['width'] and
                0 <= y <= self.image_display_info['height']):

            # 如果已有选择框，检查是否在调整手柄上
            if hasattr(self, 'selection_rect'):
                coords = self.canvas.coords(self.selection_rect)
                edge = self.get_resize_edge(event.x, event.y)
                if edge:
                    self.resizing = True
                    self.resize_edge = edge
                    return

                # 检查是否在选择框内部
                if (coords[0] <= event.x <= coords[2] and
                        coords[1] <= event.y <= coords[3]):
                    self.dragging = True
                    self.last_x = event.x
                    self.last_y = event.y
                    return

            # 开始新的选择
            self.start_x = event.x
            self.start_y = event.y
            if hasattr(self, 'selection_rect'):
                self.canvas.delete(self.selection_rect)
            self.selection_rect = self.canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline='#1a73e8',
                width=2
            )

    def on_drag(self, event):
        """处理鼠标拖动事件"""
        if not hasattr(self, 'selection_rect'):
            return

        if self.resizing:
            # 处理调整大小
            self.resize_selection(event.x, event.y)
        elif self.dragging:
            # 处理拖动
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            self.canvas.move(self.selection_rect, dx, dy)
            self.last_x = event.x
            self.last_y = event.y
        else:
            # 处理新选择
            self.canvas.coords(
                self.selection_rect,
                self.start_x, self.start_y,
                event.x, event.y
            )

        # 更新选择框坐标
        coords = self.canvas.coords(self.selection_rect)
        self.selection_coords = [
            coords[0] - self.image_display_info['x'],
            coords[1] - self.image_display_info['y'],
            coords[2] - self.image_display_info['x'],
            coords[3] - self.image_display_info['y']
        ]

    def on_release(self, event):
        """处理鼠标释放事件"""
        self.dragging = False
        self.resizing = False
        self.resize_edge = None

        if hasattr(self, 'selection_rect'):
            # 确保选择框不会出现负宽度或负高度
            coords = list(self.canvas.coords(self.selection_rect))
            if coords[2] < coords[0]:
                coords[0], coords[2] = coords[2], coords[0]
            if coords[3] < coords[1]:
                coords[1], coords[3] = coords[3], coords[1]
            self.canvas.coords(self.selection_rect, *coords)

            # 更新选择框坐标
            self.selection_coords = [
                coords[0] - self.image_display_info['x'],
                coords[1] - self.image_display_info['y'],
                coords[2] - self.image_display_info['x'],
                coords[3] - self.image_display_info['y']
            ]

    def on_motion(self, event):
        """处理鼠标移动事件"""
        if not hasattr(self, 'selection_rect'):
            return

        edge = self.get_resize_edge(event.x, event.y)
        if edge:
            # 设置适当的光标
            if edge in ['n', 's']:
                self.canvas.config(cursor='sb_v_double_arrow')
            elif edge in ['e', 'w']:
                self.canvas.config(cursor='sb_h_double_arrow')
            elif edge in ['nw', 'se']:
                self.canvas.config(cursor='size_nw_se')
            elif edge in ['ne', 'sw']:
                self.canvas.config(cursor='size_ne_sw')
        else:
            coords = self.canvas.coords(self.selection_rect)
            if (coords[0] <= event.x <= coords[2] and
                    coords[1] <= event.y <= coords[3]):
                self.canvas.config(cursor='fleur')  # 移动光标
            else:
                self.canvas.config(cursor='')  # 默认光标

    def get_resize_edge(self, x, y, threshold=8):
        """确定鼠标是否在选择框边缘"""
        if not hasattr(self, 'selection_rect'):
            return None

        coords = self.canvas.coords(self.selection_rect)
        left, top, right, bottom = coords

        # 检查是否在边缘附近
        in_left = abs(x - left) <= threshold
        in_right = abs(x - right) <= threshold
        in_top = abs(y - top) <= threshold
        in_bottom = abs(y - bottom) <= threshold

        # 返回对应的边缘标识
        if in_top and in_left: return 'nw'
        if in_top and in_right: return 'ne'
        if in_bottom and in_left: return 'sw'
        if in_bottom and in_right: return 'se'
        if in_top: return 'n'
        if in_bottom: return 's'
        if in_left: return 'w'
        if in_right: return 'e'
        return None

    def resize_selection(self, x, y):
        """调整选择框大小"""
        if not self.resize_edge:
            return

        coords = list(self.canvas.coords(self.selection_rect))

        # 根据拖动的边缘更新坐标
        if 'n' in self.resize_edge: coords[1] = y
        if 's' in self.resize_edge: coords[3] = y
        if 'w' in self.resize_edge: coords[0] = x
        if 'e' in self.resize_edge: coords[2] = x

        # 更新选择框
        self.canvas.coords(self.selection_rect, *coords)

    def on_window_resize(self, event):
        """处理窗口大小变化事件"""
        # 确保事件来自主窗口而不是子组件
        if event.widget == self.root:
            # 添加一个小延迟来防止过于频繁的刷新
            self.root.after_cancel(self.resize_timer) if hasattr(self, 'resize_timer') else None
            self.resize_timer = self.root.after(100, self.refresh_current_image)

    def refresh_current_image(self):
        """刷新当前显示的图片"""
        if hasattr(self, 'current_image_index') and self.images:
            self.show_image(self.images[self.current_image_index])


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRenamer(root)
    root.mainloop()