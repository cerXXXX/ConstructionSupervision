"""Скрипт генерации сопроводительной документации в формате PDF (по разделу 5 ТЗ)."""

import os
import shutil
import subprocess
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

md_path = DOCS / "documentation.md"
html_path = DOCS / "documentation.html"
pdf_path = DOCS / "documentation.pdf"
pdf_tmp = DOCS / "documentation.tmp.pdf"
pdf_alt = DOCS / "documentation_updated.pdf"

text = md_path.read_text(encoding="utf-8")
body = markdown.markdown(text, extensions=["tables", "fenced_code"])

html_template = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Сопроводительная документация проекта «СтройКонтроль»</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55;
    color: #1f2328;
    margin: 40px auto;
    max-width: 960px;
    padding: 0 24px;
    font-size: 13.5px;
  }
  h1, h2, h3, h4 {
    border-bottom: 1px solid #d8dee4;
    padding-bottom: .3em;
    margin-top: 28px;
    margin-bottom: 14px;
    font-weight: 600;
    color: #1f2328;
  }
  h1 { font-size: 24px; }
  h2 { font-size: 18px; margin-top: 32px; border-bottom: 2px solid #0969da; }
  h3 { font-size: 15px; }
  h4 { font-size: 14px; border-bottom: none; }
  p {
    margin-top: 6px;
    margin-bottom: 10px;
  }
  ul, ol {
    margin-top: 4px;
    margin-bottom: 12px;
    padding-left: 26px;
  }
  li {
    margin-bottom: 4px;
  }
  li > p {
    margin: 2px 0;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 10px;
    margin-bottom: 18px;
    font-size: 12.5px;
    line-height: 1.4;
  }
  table, th, td {
    border: 1px solid #d0d7de;
  }
  th, td {
    padding: 7px 10px;
    text-align: left;
    vertical-align: top;
  }
  th {
    background-color: #f6f8fa;
    font-weight: 600;
  }
  code {
    background-color: #eff1f3;
    padding: .2em .4em;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 88%;
    color: #1f2328;
  }
  pre {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 12px 14px;
    overflow-x: auto;
    line-height: 1.45;
    margin: 10px 0 16px 0;
  }
  pre code {
    background-color: transparent;
    padding: 0;
    font-size: 85%;
    display: block;
  }
  blockquote {
    padding: 6px 14px;
    color: #59636e;
    border-left: 4px solid #0969da;
    background-color: #f6f8fa;
    margin: 0 0 16px 0;
    border-radius: 0 4px 4px 0;
  }
  blockquote p {
    margin: 4px 0;
  }
  hr {
    border: 0;
    height: 1px;
    background: #d8dee4;
    margin: 24px 0;
  }
  @media print {
    body { max-width: 100%; margin: 12mm 15mm; font-size: 11.5px; line-height: 1.45; }
    h1, h2, h3 { page-break-after: avoid; }
    table, pre { page-break-inside: avoid; }
    tr { page-break-inside: avoid; }
    table { font-size: 10.5px; }
    pre code { font-size: 10px; }
  }
</style>
</head>
<body>
""" + body + """
</body>
</html>"""

html_path.write_text(html_template, encoding="utf-8")

if pdf_tmp.exists():
    pdf_tmp.unlink()

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_exe,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_tmp.resolve()}",
    str(html_path.resolve())
]
subprocess.run(cmd, check=True)

if not pdf_tmp.exists() or pdf_tmp.stat().st_size == 0:
    raise RuntimeError(f"Edge did not produce PDF output at {pdf_tmp}")

# Попытка обновить целевой documentation.pdf
try:
    if pdf_path.exists():
        pdf_path.unlink()
    shutil.move(str(pdf_tmp), str(pdf_path))
    print(f"Generated PDF: {pdf_path} (size: {pdf_path.stat().st_size} bytes)")
except OSError as err:
    shutil.copy2(str(pdf_tmp), str(pdf_alt))
    pdf_tmp.unlink()
    print(f"[ВНИМАНИЕ] Целевой файл {pdf_path.name} заблокирован внешним приложением (просмотрщиком): {err}")
    print(f"Свежий PDF успешно сохранен как: {pdf_alt} (size: {pdf_alt.stat().st_size} bytes)")
    print(f"Чтобы обновить {pdf_path.name}, закройте просмотрщик и перезапустите скрипт.")
