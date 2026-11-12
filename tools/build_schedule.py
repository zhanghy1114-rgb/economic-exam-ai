# -*- coding: utf-8 -*-
"""生成冲刺期每日任务卡：std=标准一遍制 / max=加强两遍制"""
import os
import re
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "exams", "真题分章卷")

EXAM = date(2026, 11, 7)
TODAY = date(2026, 10, 23)
MODE = os.environ.get("MODE", "std")

if MODE == "max":
    JJ_DAYS, JR_DAYS = 5, 2
    OUT = os.path.join(ROOT, "exams", "每日任务卡（加强版）.md")
else:
    JJ_DAYS, JR_DAYS = 7, 3
    OUT = os.path.join(ROOT, "exams", "每日任务卡.md")

PHRASE = "做完,自对答案,A类看解析自学,只把 B 类题号抛给我"


def vols(subj):
    out = {}
    for fn in sorted(os.listdir(VOL)):
        m = re.match(rf"{subj}第(\d{{2}})章_(.+)_(\d{{2}})\.md", fn)
        if m:
            out.setdefault(int(m.group(1)), []).append((int(m.group(3)), fn))
    return {k: [f for _, f in sorted(v)] for k, v in sorted(out.items())}


def spread(files, days):
    base, extra = divmod(len(files), days)
    buckets, i = [], 0
    for d in range(days):
        take = base + (1 if d < extra else 0)
        buckets.append(files[i:i + take])
        i += take
    return buckets


def emit(L, day, buckets, heading, note, maj_ramp=True):
    L.append(f"## {heading}\n")
    L.append(f"_{note}_\n")
    for b in buckets:
        day += 1
        d = TODAY + timedelta(days=day - 1)
        L.append(f"### Day {day}｜{d.month}/{d.day}（周{'一二三四五六日'[d.weekday()]}）｜{len(b)} 卷\n")
        grp = {}
        for f in b:
            ch = re.match(r"(.+第\d{2}章)_(.+)_(\d{2})", f.replace(".md", ""))
            grp.setdefault(ch.group(1) + " " + ch.group(2), []).append(ch.group(3))
        for k, v in grp.items():
            L.append(f"- **{k}**：卷 {'／'.join(v)}")
        L.append("")
    return day


def main():
    jj = vols("经基")
    jr = vols("金融")
    jj_all = [f for ch in jj.values() for f in ch]
    jr_all = [f for ch in jr.values() for f in ch]

    L = []
    title = "加强版（两遍制）" if MODE == "max" else "标准版（一遍制）"
    L.append(f"# 每日任务卡·{title}（2026-10-23 → 11-06）\n")
    L.append(f"> 考试 {EXAM.isoformat()}｜经基 {len(jj_all)} 卷 + 金融 {len(jr_all)} 卷")
    L.append("> **单选 ≤50 秒／多选 ≤75 秒，10 题卷掐表 10 分钟**。做完登记 `全章扫荡进度表.md`\n")

    day = emit(L, 0, spread(jj_all, JJ_DAYS),
               "阶段一 · 经基全章真题", f"{PHRASE}｜薄章由我自命题补足")
    day = emit(L, day, spread(jr_all, JR_DAYS),
               "阶段二 · 金融全章真题",
               f"{PHRASE}｜金融 7/8/12 章真题极少,我自命题各补 18 题")

    if MODE == "max":
        day += 1
        d = TODAY + timedelta(days=day - 1)
        L.append("## 阶段三 · 第二遍精准回炉（关键：考前 5 天内刷新一遍）\n")
        L.append("_ ⊂  第一遍后 15 天会忘 70%,第二遍必须在考前 3-5 天做过,才能把短期记忆带进考场_\n")
        for i, txt in enumerate((
            "**B 类错题全部**（前 7 天累积，预计 400-500 题）→ 同章变式重做",
            "**补空的自命题 134 题**重做一遍（这些是 2026 新增，最生）",
            "**高权重章回炉**：经基 28 会计概论／02 市场供求／06 市场失灵；金融 03 商业银行／01 金融学基础",
            "**A/B 编号清单 256 条**通扫一遍，默写卡壳的当场补",
        )):
            dd = TODAY + timedelta(days=day - 1 + i)
            L.append(f"- **Day {day + i}｜{dd.month}/{dd.day}**：{txt}")
        L.append("")
        day += 3
        plan2 = [("真题_经基2025-1101上午", 105), ("真题_金融2024卷二", 100)]
    else:
        L.append("## 阶段三 · 整卷实战（练配速＋体力，必掐 90 分钟）\n")
        plan2 = [("真题_经基2025-1101上午", 105),
                 ("真题_经基2025-1102下午", 105),
                 ("真题_金融2024卷二", 100)]

    for nm, q in plan2:
        day += 1
        d = TODAY + timedelta(days=day - 1)
        L.append(f"- **Day {day}｜{d.month}/{d.day}**：`exams/真题卷/{nm}_题目卷.txt`（{q} 题，90 分钟不停表）")
    L.append("")

    L.append("## 阶段末 · 清账收口\n")
    for txt in ("错题本未销账项最后一次过 + 默写",
                "最后 1 套保持手感 + 看 `考场配速卡.md`，**22:00 前必须睡**"):
        day += 1
        d = TODAY + timedelta(days=day - 1)
        L.append(f"- **Day {day}｜{d.month}/{d.day}**：{txt}")

    L.append("\n> 每日动作：当章 A/B 清单速扫 5min → 按卡做题 → 自对答案 → A 类自学 → **B 类题号抛我** → 登记进度表")
    L.append(f"\n> 共 {day} 天，11/07 上考场")

    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"written {os.path.basename(OUT)}｜经基 {len(jj_all)}卷/{JJ_DAYS}天，金融 {len(jr_all)}卷/{JR_DAYS}天")


if __name__ == "__main__":
    main()
