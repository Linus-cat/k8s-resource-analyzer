#!/usr/bin/env python3
import re

# Read markdown content
md_file = '/root/opencode/k8s-resource-analyzer/docs/开发文档.md'
with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

html_template = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {
    size: A4;
    margin: 2cm 2cm 2cm 2cm;
    @bottom-center {
        content: counter(page);
    }
}

body {
    font-family: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #333;
    text-align: justify;
}

h1 {
    font-size: 24pt;
    font-weight: bold;
    color: #1a1a1a;
    text-align: center;
    margin-top: 0;
    margin-bottom: 30pt;
    padding-bottom: 15pt;
    border-bottom: 2px solid #2c3e50;
}

h2 {
    font-size: 16pt;
    font-weight: bold;
    color: #2c3e50;
    margin-top: 25pt;
    margin-bottom: 15pt;
    padding-bottom: 8pt;
    border-bottom: 1px solid #ecf0f1;
    page-break-before: auto;
}

h3 {
    font-size: 13pt;
    font-weight: bold;
    color: #34495e;
    margin-top: 18pt;
    margin-bottom: 10pt;
}

p {
    font-size: 11pt;
    line-height: 1.5;
    margin: 0;
    padding: 0;
    text-indent: 2em;
}

.author-info {
    font-size: 11pt;
    line-height: 1.8;
    margin-bottom: 30pt;
    text-align: left;
}

.author-info p {
    margin: 5pt 0;
    text-indent: 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 15pt 0;
    font-size: 10pt;
}

th {
    background-color: #34495e;
    color: white;
    font-weight: bold;
    text-align: center;
    padding: 10pt 8pt;
    border: 1px solid #2c3e50;
}

td {
    padding: 8pt;
    border: 1px solid #bdc3c7;
    text-align: center;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

code {
    font-family: "Courier New", monospace;
    font-size: 10pt;
    background-color: #f5f5f5;
    padding: 2pt 5pt;
    border-radius: 3pt;
    color: #c0392b;
}

pre {
    font-family: "Courier New", monospace;
    font-size: 9pt;
    background-color: #f8f9fa;
    padding: 12pt;
    border-radius: 5pt;
    border-left: 3px solid #3498db;
    overflow-x: auto;
    margin: 12pt 0;
    text-indent: 0;
}

ul, ol {
    margin: 10pt 0 10pt 25pt;
}

li {
    font-size: 11pt;
    line-height: 1.5;
    margin: 6pt 0;
}

strong {
    font-weight: bold;
}
</style>
</head>
<body>
'''

def convert_md_to_html(md_text):
    lines = md_text.split('\n')
    result = []
    in_code_block = False
    code_content = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        
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
            
        if not line:
            if in_table:
                result.append('</table>')
                in_table = False
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
            result.append(f'<li>{line[2:]}</li>')
        # Table
        elif '|' in line and line.startswith('|'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                if not in_table:
                    result.append('<table>')
                    in_table = True
                is_separator = all(set(p).issubset(set('-:')) for p in parts)
                if is_separator:
                    continue
                row = '<tr>' + ''.join(f'<td>{p}</td>' for p in parts) + '</tr>'
                result.append(row)
        else:
            if in_table:
                result.append('</table>')
                in_table = False
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            
            # Check if this is author info section
            if '作者' in line or '邮箱' in line or 'AI工具' in line or '作者:' in line or '邮箱:' in line:
                result.append(f'<p class="author-info">{line}</p>')
            else:
                result.append(f'<p>{line}</p>')
    
    if in_table:
        result.append('</table>')
    
    return '\n'.join(result)

html_content = html_template + convert_md_to_html(content)
html_content += '</body></html>'

# Save HTML
html_file = '/root/opencode/k8s-resource-analyzer/docs/开发文档.html'
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

# Generate PDF using WeasyPrint
from weasyprint import HTML, CSS

pdf_file = '/root/opencode/k8s-resource-analyzer/docs/K8s资源使用率分析工具_开发文档.pdf'

HTML(html_file).write_pdf(pdf_file)

print(f"PDF已生成: {pdf_file}")
