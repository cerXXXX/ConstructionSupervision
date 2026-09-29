"""Скрипт генерации сопроводительной документации в формате PDF (по разделу 5 ТЗ)."""

import subprocess
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

md_path = DOCS / "documentation.md"
html_path = DOCS / "documentation.html"
pdf_path = DOCS / "documentation.pdf"

text = md_path.read_text(encoding="utf-8")
body = markdown.markdown(text, extensions=["tables", "fenced_code"])

html_template = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Сопроводительная документация проекта</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    color: #24292e;
    margin: 40px auto;
    max-width: 900px;
    padding: 0 20px;
    font-size: 14px;
  }
  h1, h2, h3, h4 {
    border-bottom: 1px solid #eaecef;
    padding-bottom: .3em;
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
  }
  h1 { font-size: 24px; }
  h2 { font-size: 19px; }
  h3 { font-size: 16px; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
  }
  table, th, td {
    border: 1px solid #dfe2e5;
  }
  th, td {
    padding: 6px 12px;
    text-align: left;
  }
  th {
    background-color: #f6f8fa;
    font-weight: 600;
  }
  code {
    background-color: #f6f8fa;
    padding: .2em .4em;
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 85%;
  }
  pre code {
    display: block;
    padding: 12px;
    overflow-x: auto;
    line-height: 1.45;
  }
  blockquote {
    padding: 0 1em;
    color: #6a737d;
    border-left: .25em solid #dfe2e5;
    margin: 0 0 16px 0;
  }
  @media print {
    body { max-width: 100%; margin: 15mm; font-size: 12px; }
    h1, h2, h3 { page-break-after: avoid; }
    table, pre { page-break-inside: avoid; }
  }
</style>
</head>
<body>
""" + body + """
</body>
</html>"""

html_path.write_text(html_template, encoding="utf-8")

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_exe,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path.resolve()}",
    str(html_path.resolve())
]
subprocess.run(cmd, check=True)
print(f"Generated PDF: {pdf_path} (size: {pdf_path.stat().st_size} bytes)")
