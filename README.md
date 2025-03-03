# 图片批量重命名工具

这是一个基于OCR技术的图片批量重命名工具，可以通过识别图片中的文字来自动重命名图片文件。

## 功能特点

- 🖼️ 支持批量处理多个图片文件
- 📝 基于Tesseract OCR引擎进行文字识别
- 🔍 可视化选择识别区域
- 🖱️ 支持拖拽和调整选择框大小
- 🌈 现代化的用户界面
- 🔄 支持浏览和预览图片
- 🎯 高分辨率屏幕适配

## 系统要求

- Python 3.6+
- Tesseract-OCR 引擎
- 以下Python包依赖：
  - tkinter
  - Pillow (PIL)
  - pytesseract

## 安装步骤

1. 安装 Tesseract-OCR
   - Windows用户可以从[GitHub](https://github.com/UB-Mannheim/tesseract/wiki)下载安装包
   - 安装完成后，请确保在程序中正确设置Tesseract路径

2. 安装Python依赖
   ```bash
   pip install Pillow pytesseract
   ```

## 使用说明

1. 运行程序：
   ```bash
   python image_renamer.py
   ```

2. 使用步骤：
   - 点击"选择图片"按钮选择要处理的图片文件
   - 在显示的图片上用鼠标框选包含文字的区域
   - 可以拖动或调整选择框的大小
   - 点击"重命名图片"按钮开始处理
   - 程序会自动识别选中区域的文字，并将其作为新的文件名

## 注意事项

- 确保选择的区域文字清晰可见
- 文件名中的特殊字符会被自动过滤
- 建议在重命名之前备份原始文件
- 默认支持中文识别，如需其他语言请修改代码中的`lang`参数
