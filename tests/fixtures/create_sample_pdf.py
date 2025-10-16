"""
创建测试用的 PDF 样本文件

需要安装 reportlab: pip install reportlab
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 注册中文字体（使用系统自带的字体）
# Windows 系统字体路径
font_path = r"C:\Windows\Fonts\simsun.ttc"
if os.path.exists(font_path):
    try:
        pdfmetrics.registerFont(TTFont('SimSun', font_path))
        font_name = 'SimSun'
    except:
        font_name = 'Helvetica'
else:
    font_name = 'Helvetica'


def create_text_pdf(filename):
    """创建包含文本的 PDF（非扫描版）"""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # 设置元数据
    c.setAuthor("测试作者")
    c.setTitle("PDF 测试文档")
    c.setSubject("用于测试 PDF 解析器")

    # 第一页
    c.setFont(font_name, 16)
    c.drawString(100, height - 100, "PDF Test Document")

    if font_name == 'SimSun':
        c.setFont('SimSun', 14)
        c.drawString(100, height - 150, "这是一个测试 PDF 文档")
        c.drawString(100, height - 180, "包含中文内容")
    else:
        c.setFont('Helvetica', 14)
        c.drawString(100, height - 150, "This is a test PDF document")
        c.drawString(100, height - 180, "Contains text content")

    c.setFont('Helvetica', 12)
    c.drawString(100, height - 220, "Page 1")
    c.drawString(100, height - 240, "Content: Lorem ipsum dolor sit amet")

    # 第二页
    c.showPage()
    c.setFont('Helvetica', 12)
    c.drawString(100, height - 100, "Page 2")
    c.drawString(100, height - 120, "More content on second page")

    c.save()
    print(f"Created: {filename}")


def create_empty_pdf(filename):
    """创建空白 PDF（模拟扫描版，几乎没有文本）"""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # 只画一些图形，不包含文本
    c.rect(100, height - 200, 400, 100)
    c.circle(300, height - 400, 50)

    c.save()
    print(f"Created: {filename}")


if __name__ == "__main__":
    # 创建样本文件目录
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_files")
    os.makedirs(sample_dir, exist_ok=True)

    # 创建文本型 PDF
    text_pdf = os.path.join(sample_dir, "sample_text.pdf")
    create_text_pdf(text_pdf)

    # 创建空白 PDF（模拟扫描版）
    empty_pdf = os.path.join(sample_dir, "sample_scanned.pdf")
    create_empty_pdf(empty_pdf)

    print("\nPDF 样本文件创建完成！")
