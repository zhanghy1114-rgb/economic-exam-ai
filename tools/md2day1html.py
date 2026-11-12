# -*- coding: utf-8 -*-
"""Day1 知识点 MD -> 打印版 HTML（供 Edge 无头打印成 PDF）"""
import sys, pathlib
import markdown

BASE = pathlib.Path(r"F:\自己创建的skill\学习\中级经济师 - 金融学习\exams\错题本")
OUT  = pathlib.Path(r"C:\Users\86151\AppData\Local\Temp\day1_pdf")
OUT.mkdir(parents=True, exist_ok=True)

CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Microsoft YaHei", "SimHei", sans-serif; font-size: 10.5pt;
       line-height: 1.55; color: #111; margin: 0; }
h1 { font-size: 17pt; text-align: center; border-bottom: 2.5pt solid #1a3a6b;
     padding-bottom: 6pt; color: #1a3a6b; margin: 0 0 8pt 0; }
h2 { font-size: 13pt; color: #1a3a6b; background: #eef2f8; border-left: 4pt solid #1a3a6b;
     padding: 4pt 8pt; margin: 14pt 0 6pt 0; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #24457e; margin: 10pt 0 4pt 0;
     border-bottom: 1pt dashed #9db3d4; padding-bottom: 2pt; page-break-after: avoid; }
p { margin: 4pt 0; }
blockquote { background: #f5f7fa; border-left: 3pt solid #8aa4c8; margin: 6pt 0;
             padding: 5pt 9pt; color: #333; }
blockquote p { margin: 2pt 0; }
ul, ol { margin: 4pt 0 6pt 0; padding-left: 18pt; }
li { margin: 2.5pt 0; page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; page-break-inside: auto; }
th { background: #1a3a6b; color: #fff; font-weight: bold; }
th, td { border: 0.7pt solid #7d92b5; padding: 3.5pt 6pt; text-align: left;
         vertical-align: top; page-break-inside: avoid; }
tr:nth-child(even) td { background: #f2f5fa; }
strong { color: #b02a2a; }
h1 strong, th strong { color: inherit; }
hr { border: none; border-top: 1pt solid #b9c6da; margin: 10pt 0; }
"""

def convert(md_path, html_name, subtitle):
    text = pathlib.Path(md_path).read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "sane_lists", "smarty"])
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>{CSS}</style></head>
<body><div style="text-align:center;color:#666;font-size:9pt;margin-bottom:2pt">{subtitle}</div>
{body}</body></html>"""
    out = OUT / html_name
    out.write_text(html, encoding="utf-8")
    print(f"OK  {out}")

convert(BASE / "Day1_知识点_记忆版.md", "mem.html", "中级经济师备考 · Day 1 错题知识点（背诵卡）")
convert(BASE / "Day1_知识点_详细版.md", "detail.html", "中级经济师备考 · Day 1 错题知识点（免翻教材版）")
