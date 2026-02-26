#!/usr/bin/env python3
import os
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Chinese font
try:
    pdfmetrics.registerFont(TTFont('NotoSans', '/tmp/NotoSans-Regular.ttf'))
    chinese_font = 'NotoSans'
    print("Chinese font registered successfully")
except Exception as e:
    print(f"Failed to register Chinese font: {e}")
    chinese_font = 'Helvetica'

# Read markdown content
md_file = '/root/opencode/k8s-resource-analyzer/docs/开发文档.md'
with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Create PDF
pdf_file = '/root/opencode/k8s-resource-analyzer/docs/K8s资源使用率分析工具_开发文档.pdf'
doc = SimpleDocTemplate(pdf_file, pagesize=A4, 
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2.5*cm, rightMargin=2.5*cm)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontName=chinese_font,
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=30,
    alignment=1
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontName=chinese_font,
    fontSize=14,
    textColor=colors.HexColor('#2c3e50'),
    spaceBefore=20,
    spaceAfter=12,
)

subheading_style = ParagraphStyle(
    'CustomSubHeading',
    parent=styles['Heading3'],
    fontName=chinese_font,
    fontSize=12,
    textColor=colors.HexColor('#34495e'),
    spaceBefore=12,
    spaceAfter=8,
)

code_style = ParagraphStyle(
    'Code',
    fontName='Courier',
    fontSize=9,
    textColor=colors.HexColor('#2c3e50'),
    backgroundColor=colors.HexColor('#f5f5f5'),
    spaceBefore=5,
    spaceAfter=5,
)

body_style = ParagraphStyle(
    'Body',
    fontName=chinese_font,
    fontSize=10,
    textColor=colors.HexColor('#2c3e50'),
    spaceBefore=6,
    spaceAfter=6,
    leading=16,
)

elements = []

lines = content.split('\n')
i = 0
in_code_block = False
code_content = []

def clean_markdown(text):
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^\s*[-*]\s+', '• ', text)
    text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text)
    return text

def is_heading(line):
    return line.startswith('#')

def get_heading_level(line):
    count = 0
    for c in line:
        if c == '#':
            count += 1
        else:
            break
    return count

while i < len(lines):
    line = lines[i]
    
    if line.strip().startswith('```'):
        if in_code_block:
            code_text = '\n'.join(code_content)
            elements.append(Paragraph(f'<pre>{code_text}</pre>', code_style))
            code_content = []
            in_code_block = False
        else:
            in_code_block = True
        i += 1
        continue
    
    if in_code_block:
        code_content.append(line)
        i += 1
        continue
    
    line = line.strip()
    
    if not line:
        elements.append(Spacer(1, 0.3*cm))
        i += 1
        continue
    
    if is_heading(line):
        level = get_heading_level(line)
        text = clean_markdown(line)
        
        if level == 1:
            if elements:
                elements.append(PageBreak())
            elements.append(Paragraph(text, title_style))
        elif level == 2:
            elements.append(Paragraph(text, heading_style))
        elif level == 3:
            elements.append(Paragraph(text, subheading_style))
        else:
            elements.append(Paragraph(text, subheading_style))
    else:
        line = clean_markdown(line)
        
        if '|' in line and '-' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                table_data = [parts]
                i += 1
                while i < len(lines):
                    row_line = lines[i].strip()
                    if not row_line or '|' not in row_line:
                        break
                    row_parts = [p.strip() for p in row_line.split('|') if p.strip()]
                    if len(row_parts) == len(parts):
                        table_data.append(row_parts)
                    i += 1
                
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.3*cm))
                continue
        else:
            line = line.replace('• ', '<br/>• ')
            elements.append(Paragraph(line, body_style))
    
    i += 1

doc.build(elements)
print(f"PDF已生成: {pdf_file}")
