# -*- coding: utf-8 -*-
"""Day1 知识点 MD -> 打印版 PDF（reportlab，中文字体嵌入，适合打印）"""
import re, html, pathlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)

# ---------- 字体 ----------
pdfmetrics.registerFont(TTFont("MSYH", "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("MSYHBD", "C:/Windows/Fonts/msyhbd.ttc", subfontIndex=0))
registerFontFamily("MSYH", normal="MSYH", bold="MSYHBD", italic="MSYH", boldItalic="MSYHBD")

NAVY = colors.HexColor("#1a3a6b")
BASE = pathlib.Path(r"F:\自己创建的skill\学习\中级经济师 - 金融学习\exams\错题本")

def esc(s):
    s = html.unescape(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

def st(name, **kw):
    d = dict(fontName="MSYH", fontSize=10.2, leading=15.5, textColor=colors.HexColor("#111111"),
             wordWrap="CJK", spaceBefore=2, spaceAfter=2)
    d.update(kw)
    return ParagraphStyle(name, **d)

S_TITLE = st("t", fontName="MSYHBD", fontSize=16, leading=22, alignment=TA_CENTER,
             textColor=NAVY, spaceBefore=0, spaceAfter=6)
S_SUB    = st("sub", fontSize=9, leading=13, textColor=colors.HexColor("#555555"), alignment=TA_CENTER)
S_H2     = st("h2", fontName="MSYHBD", fontSize=12.5, leading=18, textColor=colors.white,
              backColor=NAVY, borderPadding=(3, 6, 4, 6), spaceBefore=10, spaceAfter=6)
S_H3     = st("h3", fontName="MSYHBD", fontSize=11, leading=16, textColor=NAVY,
              spaceBefore=8, spaceAfter=3)
S_BODY   = st("body")
S_LI1    = st("li1", leftIndent=12, bulletIndent=2, spaceBefore=1.5, spaceAfter=1.5)
S_LI2    = st("li2", leftIndent=26, bulletIndent=16, fontSize=9.8, leading=14.5)
S_QUOTE  = st("quote", fontSize=9.3, leading=14, textColor=colors.HexColor("#333333"),
              backColor=colors.HexColor("#f2f5fa"), borderPadding=(3, 5, 4, 5),
              leftIndent=4, spaceBefore=4, spaceAfter=6)
S_CELL   = st("cell", fontSize=9.2, leading=13.2, spaceBefore=0, spaceAfter=0)
S_CELLH  = st("cellh", fontName="MSYHBD", fontSize=9.2, leading=13.2,
              textColor=colors.white, spaceBefore=0, spaceAfter=0)

def parse(md_text):
    flow = []
    lines = md_text.splitlines()
    i, first_h1 = 0, True
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1; continue
        if s.startswith("|"):                                   # 表格
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^:?-{2,}:?$", cells[0].replace(" ", "")):
                    rows.append(cells)
                i += 1
            if rows:
                ncol = max(len(r) for r in rows)
                rows = [r + [""] * (ncol - len(r)) for r in rows]
                data = [[Paragraph(esc(c), S_CELLH if r == 0 else S_CELL) for c in r]
                        for r in rows]
                avail = A4[0] - 28 * mm
                widths = [avail / ncol] * ncol
                # 首列略窄
                if ncol >= 3:
                    widths[0] = avail * 0.16
                    rest = (avail - widths[0]) / (ncol - 1)
                    widths = [widths[0]] + [rest] * (ncol - 1)
                t = Table(data, colWidths=widths, repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7d92b5")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#f2f5fa")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ]))
                flow += [Spacer(1, 2), t, Spacer(1, 3)]
            continue
        if s.startswith("> "):                                   # 引用块
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            flow.append(Paragraph("<br/>".join(esc(b) for b in buf if b), S_QUOTE))
            continue
        if re.match(r"^---+$", s):
            flow.append(HRFlowable(width="100%", thickness=0.6,
                                   color=colors.HexColor("#b9c6da"),
                                   spaceBefore=6, spaceAfter=6))
            i += 1; continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            lvl, txt = len(m.group(1)), esc(m.group(2))
            if lvl == 1 and first_h1:
                flow.append(Paragraph(txt, S_TITLE)); first_h1 = False
            elif lvl == 1:
                flow.append(Paragraph(txt, S_H2))
            elif lvl == 2:
                flow.append(Paragraph(txt, S_H2))
            else:
                flow.append(Paragraph(txt, S_H3))
            i += 1; continue
        m = re.match(r"^(\s*)-\s+(.*)$", ln)                     # 列表
        if m:
            nest = len(m.group(1)) >= 2
            style, bullet = (S_LI2, "◦") if nest else (S_LI1, "•")
            flow.append(Paragraph(esc(m.group(2)), style, bulletText=bullet))
            i += 1; continue
        m = re.match(r"^(\d+)[.、]\s+(.*)$", s)                  # 有序列表
        if m:
            flow.append(Paragraph(esc(m.group(2)), S_LI1, bulletText=m.group(1) + "."))
            i += 1; continue
        flow.append(Paragraph(esc(s), S_BODY))
        i += 1
    return flow

def footer(canv, doc):
    canv.saveState()
    canv.setFont("MSYH", 8)
    canv.setFillColor(colors.HexColor("#888888"))
    canv.drawCentredString(A4[0] / 2, 10 * mm, f"— {canv.getPageNumber()} —")
    canv.restoreState()

def build(md_name, pdf_name, subtitle):
    text = (BASE / md_name).read_text(encoding="utf-8")
    doc = SimpleDocTemplate(str(BASE / pdf_name), pagesize=A4,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=subtitle)
    story = [Paragraph(subtitle, S_SUB), Spacer(1, 4)]
    story += parse(text)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"OK {pdf_name}")

build("Day1_知识点_记忆版.md", "Day1_知识点_记忆版.pdf",
      "中级经济师备考 · Day 1 错题知识点 · 背诵卡（早读 10 遍）")
build("Day1_知识点_详细版.md", "Day1_知识点_详细版.pdf",
      "中级经济师备考 · Day 1 错题知识点 · 免翻教材版")
