# -*- coding: utf-8 -*-
"""重切分章卷：剔除残缺题（选项缺失/答案缺失/答案与选项不符），按章重新切成 10 题一卷"""
import os, re, shutil, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "exams", "真题分章卷")
BAK = os.path.join(ROOT, "exams", "真题分章卷_备份")

Q = re.compile(r"^\*\*(\d+)\.\*\*\s*[（(](单选|多选)[）)]\s*(.*)$")
OPT = re.compile(r"^([A-E])\.\s*(.+)$")
ROW_KEY = re.compile(r"^\|\s*题\s*\|(.+)\|\s*$")
ROW_VAL = re.compile(r"^\|\s*答案\s*\|(.+)\|\s*$")
SRC = re.compile(r"^>\s*来源[:：]\s*(.+)$")

# 已知 PDF 换行截断的手工修复：(题干片段, 选项字母, 正确全文)
FIXES = []

# 已知"选项被 PDF 截断导致答案与文本矛盾"的题，整题剔除（题干片段）
DROP = [
    "关于劳动供给曲线的说法",   # D 项原文截断，按官方答案 ABC 与解析文本矛盾，无法还原
    "需求价格弹性较小的商品有",  # 官方答案 BE 与教材"奢侈品弹性大、必需品弹性小"矛盾，存疑弃用
]


def should_drop(stem):
    return any(f in stem for f in DROP)


# 归类纠偏：明显串章的题移回正确章（题干片段 → 目标章文件名前缀）
RECHAP = [
    # 第 7 章 国民收入核算与宏观模型
    ("不属于影响总需求的因素", "经基第07章_国民收入核算和简单的宏观经济模型"),
    ("影响一国总需求的主要因素", "经基第07章_国民收入核算和简单的宏观经济模型"),
    # 第 8 章 经济增长与发展
    ("推动高质量发展的内在需求", "经基第08章_经济增长和经济发展理论"),
    # 第 9 章 价格总水平
    ("价格总水平通过影响汇率", "经基第09章_价格总水平和就业、失业"),
    # 第 11 章 公共物品与财政职能
    ("公共物品供给制度", "经基第11章_公共物品与财政职能"),
    # 第 17 章 财政政策
    ("汲水政策", "经基第17章_财政政策"),
    ("政府通过减少财政支出", "经基第17章_财政政策"),
    ("紧缩性财政政策", "经基第17章_财政政策"),
    # 第 18 章 货币供求
    ("货币失衡类型", "经基第18章_货币供求与货币均衡"),
    ("货币需求是由", "经基第18章_货币供求与货币均衡"),
    ("费雪方程式", "经基第18章_货币供求与货币均衡"),
    ("属于货币需求理论", "经基第18章_货币供求与货币均衡"),
    # 第 5 章 生产要素市场
    ("劳动的供给曲线向后弯曲的说法", "经基第05章_生产要素市场理论"),
    # 第 4 章 市场结构
    ("完全垄断市场上生产者的需求曲线", "经基第04章_市场结构理论"),
]


def apply_fix(stem, letter, text):
    for frag, lt, full in FIXES:
        if lt == letter and frag in stem:
            return full
    return text


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    qs, cur = [], None
    keys, ans, srcs = [], {}, []
    for ln in lines:
        s = ln.strip()
        m = SRC.match(s)
        if m:
            head = re.split(r"[｜|]", m.group(1))[0]
            srcs.append(head)
        mk, mv = ROW_KEY.match(s), ROW_VAL.match(s)
        if mk:
            keys = [c.strip() for c in mk.group(1).split("|")]
        elif mv:
            ans = dict(zip(keys, [c.strip() for c in mv.group(1).split("|")]))
        mq = Q.match(s)
        if mq:
            cur = {"no": int(mq.group(1)), "type": mq.group(2), "stem": mq.group(3).strip(), "opts": []}
            qs.append(cur)
            continue
        mo = OPT.match(s)
        if mo and cur is not None:
            if mo.group(1) not in [o[0] for o in cur["opts"]]:
                cur["opts"].append((mo.group(1), mo.group(2).strip()))
            continue
        if cur is not None and not cur["opts"] and s and not s.startswith((">", "#", "|", "<", "---")):
            cur["stem"] += s
    for q in qs:
        q["ans"] = ans.get(str(q["no"]), "").strip()
    return qs, srcs


def main():
    if not os.path.exists(BAK):
        shutil.copytree(VOL, BAK)
        print("已备份 ->", BAK)

    chapters = collections.OrderedDict()
    dropped = collections.Counter()
    for fn in sorted(os.listdir(VOL)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        m = re.match(r"^(.+?)_(\d+)\.md$", fn)
        if not m:
            continue
        ch, idx = m.group(1), int(m.group(2))
        qs, srcs = parse(os.path.join(VOL, fn))
        ent = chapters.setdefault(ch, {"qs": [], "srcs": [], "files": []})
        ent["files"].append(fn)
        ent["srcs"].extend(srcs)
        for q in qs:
            if should_drop(q["stem"]):
                dropped["人为剔除"] += 1
                continue
            # 归类纠偏：明显不属于本章的题移到正确章
            tgt = ch
            blob = q["stem"] + " " + " ".join(o[1] for o in q["opts"])
            for frag, tch in RECHAP:
                if frag in blob:
                    tgt = tch
                    break
            letters = [o[0] for o in q["opts"]]
            texts = [o[1] for o in q["opts"]]
            why = None
            need = 5 if q["type"] == "多选" else 4
            if len(q["opts"]) < need:
                why = "选项缺失"
            elif len(set(texts)) != len(texts):
                why = "选项重复"
            elif not q["ans"]:
                why = "答案缺失"
            elif any(c not in letters for c in q["ans"]):
                why = "答案与选项不符"
            elif len(q["stem"]) < 8:
                why = "题干过短"
            if why:
                dropped[why] += 1
                continue
            # 同章去重（题干归一化后相同即视为重复题）
            key = re.sub(r"[\s（(）)　,，。．、:：?？\"“”]", "", q["stem"])[:30]
            bucket = chapters.setdefault(tgt, {"qs": [], "srcs": [], "files": []})
            if key in bucket.setdefault("seen", set()):
                dropped["重复题"] += 1
                continue
            bucket["seen"].add(key)
            if tgt != ch:
                bucket["srcs"].extend(ent["srcs"])
                dropped["改归章"] += 1
            bucket["qs"].append(q)

    total_keep = total_drop = 0
    for ch, ent in chapters.items():
        qs = ent["qs"]
        total_keep += len(qs)
        group, per = len(qs) // 10 + (1 if len(qs) % 10 else 0), 10
        if group == 0:
            continue
        # 来源去重
        seen, src = set(), []
        for s in ent["srcs"]:
            for part in re.split(r"[、,，]", s):
                part = part.strip()
                if part and part not in seen:
                    seen.add(part)
                    src.append(part)
        src_txt = "、".join(src[:6])
        for g in range(group):
            chunk = qs[g * per:(g + 1) * per]
            if not chunk:
                continue
            L = [f"# {ch.replace('_', ' ')} · 真题卷 {g+1}/{group}", ""]
            L.append(f"> 来源：{src_txt}｜共 {len(chunk)} 题｜建议 {len(chunk)} 分钟")
            L.append("> ⏱ 单选 ≤50 秒｜多选 ≤75 秒（多选少选每项 0.5 分，错选 0 分）")
            L.append("")
            L.append("---")
            L.append("")
            amap = []
            for i, q in enumerate(chunk, 1):
                amap.append(q["ans"])
                L.append(f"**{i}.**（{q['type']}）{q['stem']}")
                for k, v in q["opts"]:
                    L.append(f"{k}. {apply_fix(q['stem'], k, v)}")
                L.append("")
            L.append("---")
            L.append("")
            L.append("<details><summary>答案速查（做完再看）</summary>")
            L.append("")
            L.append("| 题 | " + " | ".join(str(i) for i in range(1, len(chunk) + 1)) + " |")
            L.append("|---" * (len(chunk) + 1) + "|")
            L.append("| 答案 | " + " | ".join(amap) + " |")
            L.append("")
            L.append("</details>")
            L.append("")
            out = os.path.join(VOL, f"{ch}_{g+1:02d}.md")
            open(out, "w", encoding="utf-8").write("\n".join(L))
        # 删多余的旧卷
        for fn in ent["files"]:
            m = re.match(r"^(.+)_(\d+)\.md$", fn)
            if m and int(m.group(2)) > group:
                try:
                    os.remove(os.path.join(VOL, fn))
                except Exception as e:
                    print("delete fail", fn, e)

    print(f"保留可用题 {total_keep} 题｜剔除 {sum(dropped.values())} 题 {dict(dropped)}")
    md = sorted(f for f in os.listdir(VOL) if f.endswith(".md") and not f.startswith("_"))
    print(f"重切后卷数 {len(md)}")


if __name__ == "__main__":
    main()
