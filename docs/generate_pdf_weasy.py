#!/usr/bin/env python3
import re

# Read markdown content
md_file = '/root/opencode/k8s-resource-analyzer/docs/开发文档.md'
with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Convert markdown to HTML
html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'SimSun', sans-serif; margin: 40px; }
h1 { color: #1a1a1a; text-align: center; font-size: 24px; }
h2 { color: #2c3e50; font-size: 18px; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
h3 { color: #34495e; font-size: 14px; margin-top: 20px; }
p { font-size: 12px; line-height: 1.8; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 11px; }
th { background-color: #ecf0f1; }
code { background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
ul, ol { margin-left: 20px; }
li { margin: 5px 0; font-size: 12px; }
</style>
</head>
<body>
"""

def convert_md_to_html(md_text):
    lines = md_text.split('\n')
    in_code_block = False
    in_list = False
    result = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if in_list:
                result.append('</ul>' if result[-1].startswith('<li>') else '')
                in_list = False
            continue
            
        if line.startswith('```'):
            if in_code_block:
                result.append('</code></pre>')
                in_code_block = False
            else:
                result.append('<pre><code>')
                in_code_block = True
            continue
            
        if in_code_block:
            result.append(line)
            continue
            
        # Headers
        if line.startswith('# '):
            result.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            result.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            result.append(f'<h3>{line[4:]}</h3>')
        # List items
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{line[2:]}</li>')
        # Table
        elif '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2 and not line.startswith('|'):
                if '<table>' not in ''.join(result[-5:]):
                    result.append('<table>')
                is_header = all(p.replace('-', '') for p in parts)
                tag = 'th' if is_header else 'td'
                row = '<tr>' + ''.join(f'<{tag}>{p}</{tag}>' for p in parts) + '</tr>'
                result.append(row)
                if '</table>' not in ''.join(result[-5:]):
                    pass
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            result.append(f'<p>{line}</p>')
    
    if in_list:
        result.append('</ul>')
    
    return '\n'.join(result)

html_content += convert_md_to_html(content)
html_content += '</body></html>'

# Save HTML
html_file = '/root/opencode/k8s-resource-analyzer/docs/开发文档.html'
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

# Generate PDF using WeasyPrint
from weasyprint import HTML

pdf_file = '/root/opencode/k8s-resource-analyzer/docs/K8s资源使用率分析工具_开发文档.pdf'
HTML(html_file).write_pdf(pdf_file)

print(f"PDF已生成: {pdf_file}")
