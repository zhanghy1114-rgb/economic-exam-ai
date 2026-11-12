# -*- coding: utf-8 -*-
"""真题分章卷质量巡检：答案正确性 / 题型一致性 / 残缺题"""
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "exams", "真题分章卷")
OUT = os.path.join(ROOT, "exams", "题库质量报告.md")

Q = re.compile(r"^\*\*(\d+)\.\*\*\s*[（(](单选|多选)[）)](.+)$")
Q_ANY = re.compile(r"^\*\*(\d+)\.\*\*(.+)$")
OPT = re.compile(r"^([A-E])\.\s*(.+)$")
SKIP = re.compile(r"本题选项缺失")
ROW_KEY = re.compile(r"^\|\s*题\s*\|(.+)\|\s*$")
ROW_VAL = re.compile(r"^\|\s*答案\s*\|(.+)\|\s*$")


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    items, cur, inans, ans = [], None, False, {}
    keys = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("<details"):
            inans = True
        if inans:
            mk = ROW_KEY.match(s)
            mv = ROW_VAL.match(s)
            if mk:
                keys = [c.strip() for c in mk.group(1).split("|")]
            elif mv and keys:
                vals = [c.strip() for c in mv.group(1).split("|")]
                ans = {int(k): v for k, v in zip(keys, vals) if k.isdigit() and v}
            continue
        m = Q_ANY.match(s)
        if m:
            if cur:
                items.append(cur)
            tm = re.match(r"[（(](单选|多选)[）)]", m.group(2))
            cur = {"no": int(m.group(1)), "type": tm.group(1) if tm else "?",
                   "stem": m.group(2), "opts": [], "skip": SKIP.search(m.group(2)) is not None}
            continue
        om = OPT.match(s)
        if om and cur is not None:
            cur["opts"].append(om.group(1))
    if cur:
        items.append(cur)
    for it in items:
        it["ans"] = ans.get(it["no"], "")
    return items


def main():
    issues = Counter()
    detail = []
    files = [f for f in sorted(os.listdir(VOL)) if f.endswith(".md") and not f.startswith("_")]
    tot = 0
    for fn in files:
        items = parse(os.path.join(VOL, fn))
        tot += len(items)
        for it in items:
            a, t = it["ans"], it["type"]
            # 1 无答案
            if not a:
                issues["缺答案"] += 1
                detail.append((fn, it["no"], "缺答案", it["stem"][:30]))
                continue
            # 2 字母合法性（去重/升序/范围）
            if re.search(r"([A-E]).*\1", a) or a != "".join(sorted(a)):
                issues["答案字母异常"] += 1
                detail.append((fn, it["no"], f"答案'{a}'字母重复或乱序", it["stem"][:30]))
            # 3 题型 vs 答案个数（错位的最强信号）
            if t == "单选" and len(a) > 1:
                issues["**单选却给多选答案**"] += 1
                detail.append((fn, it["no"], f"单选但答案={a}", it["stem"][:30]))
            if t == "多选" and len(a) == 1:
                issues["多选答案仅1项"] += 1
                detail.append((fn, it["no"], f"多选但答案={a}", it["stem"][:30]))
            if len(a) > 4:
                issues["答案超过4项"] += 1
                detail.append((fn, it["no"], f"答案={a}超出多选上限", it["stem"][:30]))
            # 4 选项数
            if not it["skip"]:
                want = 4 if t == "单选" else 5
                if len(it["opts"]) < want:
                    issues[f"选项不足({len(it['opts'])}个)"] += 1
                    detail.append((fn, it["no"], f"{t}只有{len(it['opts'])}个选项", it["stem"][:30]))
            else:
                issues["已标记跳过"] += 1
    L = ["# 题库质量报告\n", f"> 扫描 {len(files)} 份卷，共 **{tot} 题**\n",
         "| 问题类型 | 题数 | 严重度 |", "|---|---:|---|"]

    def write():
        order = sorted(issues.items(), key=lambda x: -x[1])
        sev = {"**单选却给多选答案**": "🔴 致命", "缺答案": "🔴 致命", "答案字母异常": "🟠 高",
               "答案超过4项": "🟠 高", "多选答案仅1项": "🟡 中", "已标记跳过": "✅ 已处理"}
        for k, v in order:
            s = sev.get(k, "🟡 中" if k.startswith("选项不足") else "⚪ 低")
            L.append(f"| {k} | {v} | {s} |")
        L.append("")
        if detail:
            L.append("| 文件 | 题号 | 问题 | 题干 |")
            L.append("|---|---|---|---|")
            for fn, no, iss, st in detail:
                L.append(f"| {fn.replace('.md','')} | {no} | {iss} | {st} |")
    write()
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"总题数 {tot}")
    for k, v in sorted(issues.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
