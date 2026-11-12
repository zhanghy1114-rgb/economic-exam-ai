# -*- coding: utf-8 -*-
"""扫描真题分章卷，找出 PDF 跨页断裂造成的残缺题"""
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "exams", "真题分章卷")
OUT = os.path.join(ROOT, "exams", "残缺题清单.md")

Q = re.compile(r"^\*\*(\d+)\.\*\*(.+)$")
OPT = re.compile(r"^([A-E])\.\s*(.*)$")
BRACKET = re.compile(r"[（(]\s*[）)]")


def check(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    bad, cur = [], None
    for ln in lines:
        s = ln.strip()
        if s.startswith("<details") or s.startswith("|") or s.startswith("#"):
            if cur:
                flush(cur, bad)
                cur = None
            continue
        m = Q.match(s)
        if m:
            if cur:
                flush(cur, bad)
            cur = {"no": m.group(1), "stem": m.group(2), "opts": []}
            continue
        om = OPT.match(s)
        if om and cur is not None:
            cur["opts"].append((om.group(1), om.group(2).strip()))
    if cur:
        flush(cur, bad)
    return bad


def flush(cur, bad):
    stem, opts = cur["stem"], cur["opts"]
    issues = []
    # 题干：以（ 结尾但没闭包 / 空括号 / 过短
    if stem.rstrip().endswith(("（", "(", "、", "，")) and not BRACKET.search(stem):
        issues.append("题干结尾疑似截断")
    if len(stem) < 12:
        issues.append(f"题干过短({len(stem)}字)")
    if BRACKET.search(stem) and not stem.rstrip().endswith(("。", "）", ")", "．")):
        pass
    # 选项：少于 4 个 / 空内容 / 只有标点 / 极短
    if len(opts) < 4:
        issues.append(f"选项仅{len(opts)}个")
    for k, v in opts:
        if len(v) < 2:
            issues.append(f"选项{k}内容缺失")
        elif re.match(r"^[^一-龥A-Za-z0-9]+$", v):
            issues.append(f"选项{k}只剩标点:'{v}'")
    # 题号连续性
    if issues:
        bad.append((cur["no"], "; ".join(issues), stem[:40]))


def main():
    total, files = 0, 0
    rows = defaultdict(list)
    for fn in sorted(os.listdir(VOL)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        bad = check(os.path.join(VOL, fn))
        if bad:
            files += 1
            total += len(bad)
            rows[fn] = bad
    L = ["# 残缺题清单（PDF 跨页断裂，需修）\n",
         f"> 扫描 {len(os.listdir(VOL))} 份卷，发现 **{files} 份有问题、共 {total} 题**。\n"]
    for fn in sorted(rows):
        L.append(f"## {fn}\n")
        L.append("| 题号 | 问题 | 题干 |")
        L.append("|---|---|---|")
        for no, iss, st in rows[fn]:
            L.append(f"| {no} | {iss} | {st} |")
        L.append("")
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"{files} 份文件 / {total} 题有问题 → {OUT}")


if __name__ == "__main__":
    main()
