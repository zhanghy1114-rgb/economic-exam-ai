# -*- coding: utf-8 -*-
"""
把真题文本拆成「题目卷」与「答案与解析」两份，避免做题时看到答案。
用法: python split_zhenti.py
输入: notes/真题库/txt/真题_*.txt
输出: exams/真题卷/<名称>_题目卷.txt 与 <名称>_答案与解析.txt
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "notes", "真题库", "txt")
OUT = os.path.join(ROOT, "exams", "真题卷")
os.makedirs(OUT, exist_ok=True)

# 新题号：行首 数字 + . ． 、
Q_START = re.compile(r"^\s*(\d{1,3})\s*[.．、]")
# 答案/解析标记
ANS_MARK = re.compile(r"(【参考答案】|【参考答案|【答案】|【答案|【参考解析】|【解析】|参考答案[:：]|答案[:：]\s*[A-E])")


def split_text(text: str):
    ques, ans = [], []
    in_answer = False
    for line in text.split("\n"):
        s = line.rstrip()
        if not s:
            continue
        if Q_START.match(s):
            in_answer = False
        if ANS_MARK.search(s):
            in_answer = True
        (ans if in_answer else ques).append(s)
    return "\n".join(ques), "\n".join(ans)


def main():
    files = sorted(f for f in os.listdir(SRC) if f.startswith("真题_") and f.endswith(".txt"))
    if not files:
        print("未找到真题文本，请先运行 extract_zhenti.py")
        return

    print(f"{'真题卷':<24} {'题目行':>6} {'答案行':>6} {'题数':>5}")
    print("-" * 46)
    total_q = 0
    for fn in files:
        base = fn[:-4]
        with open(os.path.join(SRC, fn), encoding="utf-8") as f:
            text = f.read()
        q, a = split_text(text)
        nq = len(Q_START.findall("\n".join(q.split("\n"))))
        total_q += nq
        with open(os.path.join(OUT, base + "_题目卷.txt"), "w", encoding="utf-8") as f:
            f.write(q + "\n")
        with open(os.path.join(OUT, base + "_答案与解析.txt"), "w", encoding="utf-8") as f:
            f.write(a + "\n")
        print(f"{base:<24} {len(q.splitlines()):>6} {len(a.splitlines()):>6} {nq:>5}")
    print("-" * 46)
    print(f"{'合计':<24} {'':>6} {'':>6} {total_q:>5}")
    print(f"\n输出目录: {OUT}")


if __name__ == "__main__":
    main()
