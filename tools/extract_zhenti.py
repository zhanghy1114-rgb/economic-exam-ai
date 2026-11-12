# -*- coding: utf-8 -*-
"""
提取经基/金融真题 PDF 文本，自动修复 GBK mojibake 乱码。
用法: python extract_zhenti.py
输出: notes/真题库/txt/ 下 真题_<年份场次>.txt
"""
import os
import re
import warnings

import PyPDF2

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "notes", "真题库", "txt")
os.makedirs(OUT_DIR, exist_ok=True)

# (输出名, PDF 相对路径)
TARGETS = [
    ("真题_经基2025-1101上午", os.path.join("经济基础09-25", "基础(2009-2025)", "2025年中级经济师11.1上午《经济基础》真题解析.pdf")),
    ("真题_经基2025-1101下午", os.path.join("经济基础09-25", "基础(2009-2025)", "2025年中级经济师11.1下午《经济基础》真题解析.pdf")),
    ("真题_经基2025-1102上午", os.path.join("经济基础09-25", "基础(2009-2025)", "2025年中级经济师11.2上午《经济基础》真题解析.pdf")),
    ("真题_经基2025-1102下午", os.path.join("经济基础09-25", "基础(2009-2025)", "2025年中级经济师11.2下午《经济基础》真题解析.pdf")),
    ("真题_经基2024-1", os.path.join("经济基础09-25", "基础(2009-2025)", "2024年真题及答案解析1.pdf")),
    ("真题_经基2024-2", os.path.join("经济基础09-25", "基础(2009-2025)", "2024年真题及答案解析2.pdf")),
    ("真题_经基2024-3", os.path.join("经济基础09-25", "基础(2009-2025)", "2024年真题及答案解析3.pdf")),
    ("真题_经基2024-4", os.path.join("经济基础09-25", "基础(2009-2025)", "2024年真题及答案解析4.pdf")),
    ("真题_经基2023补考上午", os.path.join("经济基础09-25", "基础(2009-2025)", "2023年4月补考", "2023.4.8经济基础上午答案及解析（104题）.pdf")),
    ("真题_经基2023补考下午", os.path.join("经济基础09-25", "基础(2009-2025)", "2023年4月补考", "2023.4.8经济基础下答案及解析（101题）.pdf")),
    # ---- 金融实务 ----
    ("真题_金融2024卷二", os.path.join("金融10-24", "2024中经真题-金融-卷二（完整版）.pdf")),
    ("真题_金融2024卷一", os.path.join("金融10-24", "2024中经真题-金融-卷一.pdf")),
    ("真题_金融2023补考", os.path.join("金融10-24", "2023年4月经济师补考《中级金融》真题及答案（61题）..pdf")),
    ("真题_金融2021", os.path.join("金融10-24", "2021中级经济师《金融专业》真题及答案解析（10.31下午）【完整版】.pdf..pdf")),
    ("真题_金融2020", os.path.join("金融10-24", "2020年中级经济师《金融》真题答案（11.22上午）【全】.pdf")),
]

# GBK mojibake 特征：连续的 Latin-1 补充区字符（U+0080-U+00FF）
# 正常中文在 U+4E00-U+9FFF，不受影响，因此只修复乱码片段、保留正常中文
LATIN_SEQ = re.compile(r"[\u0080-\u00ff]{2,}")


def looks_mojibake(text: str) -> bool:
    return len(LATIN_SEQ.findall(text[:5000])) > 10


def fix_text(text: str) -> str:
    """GBK 被误当 Latin-1 解码 -> 逐段反向修复（只修乱码段，正常中文原样保留）"""

    def _fix(m):
        seg = m.group(0)
        for enc in ("gbk", "gb18030"):
            try:
                out = seg.encode("latin-1", errors="ignore").decode(enc, errors="ignore")
                if out and not re.search(r"[\u0080-\u00ff]", out):
                    return out
            except Exception:
                pass
        return seg

    return LATIN_SEQ.sub(_fix, text)


def extract(pdf_path: str) -> str:
    reader = PyPDF2.PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    raw = "\n".join(parts)
    return fix_text(raw) if looks_mojibake(raw) else raw


def clean(text: str) -> str:
    """压缩空行，去掉纯页码行"""
    lines = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if re.fullmatch(r"[\d\s\-/]+", s):  # 纯页码
            continue
        lines.append(s)
    return "\n".join(lines)


def main():
    print(f"{'文件':<26} {'页':>4} {'字符':>7} {'单选':>5} {'多选':>5} {'答案':>5}")
    print("-" * 60)
    for name, rel in TARGETS:
        pdf = os.path.join(ROOT, rel)
        if not os.path.exists(pdf):
            print(f"{name:<26} MISSING")
            continue
        try:
            reader = PyPDF2.PdfReader(pdf)
            npages = len(reader.pages)
            text = clean(extract(pdf))
        except Exception as e:
            print(f"{name:<26} ERR {e}")
            continue

        # 粗略统计
        dan = len(re.findall(r"(?m)^\s*(\d{1,3})\s*[.．、]", text))
        ans = len(re.findall(r"参考答案|【答案】|答案[:：]", text))
        out = os.path.join(OUT_DIR, name + ".txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{name:<26} {npages:>4} {len(text):>7} {dan:>5} {'':>5} {ans:>5}")


if __name__ == "__main__":
    main()
