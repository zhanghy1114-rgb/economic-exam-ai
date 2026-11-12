# -*- coding: utf-8 -*-
"""从原文回填分章卷里缺失的答案（只写唯一命中，杜绝配错）"""
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "exams", "真题分章卷")
SRC = os.path.join(ROOT, "notes", "真题库", "txt")

Q_SRC = re.compile(r"^\s*(\d{1,3})\s*[、.．](.+)$")
Q_ANY = re.compile(r"^\*\*(\d+)\.\*\*\s*[（(](单选|多选)[）)](.+)$")
OPT = re.compile(r"^([A-E])\.\s*(.+)$")
ANS = re.compile(
    r"(?:【参考答案】|参考答案|【答案】|答案)\s*[:：]?\s*([A-E]{1,5})(?![A-E])"
)
ROW_KEY = re.compile(r"^\|\s*题\s*\|(.+)\|\s*$")
ROW_VAL = re.compile(r"^\|\s*答案\s*\|(.+)\|\s*$")


def norm(t):
    return re.sub(r"[\s（(）)　,，。．、:：?？]", "", t)


def load_src():
    """只索引题号行，避免匹配到【解析】里的重复文本"""
    docs = {}
    index = defaultdict(list)
    for fn in sorted(os.listdir(SRC)):
        if not (fn.startswith("真题_") and fn.endswith(".txt")):
            continue
        lines = open(os.path.join(SRC, fn), encoding="utf-8").read().split("\n")
        docs[fn] = lines
        for i, ln in enumerate(lines):
            if not Q_SRC.match(ln):
                continue
            n = norm(Q_SRC.match(ln).group(2))
            if len(n) >= 8:
                index[n].append((fn, i))
    return docs, index


def find_answer(stem, docs, index):
    key = norm(stem)[:24]
    if len(key) < 8:
        return None, "题干太短"
    hits = []
    for hk, hs in index.items():
        if key in hk:
            hits.extend(hs)
    if not hits:
        return None, "原文未命中"
    found = set()
    for fn, i in hits:
        lines = docs[fn]
        # 向后找答案，但碰到下一题号行就停（防跨题取答案）
        for j in range(i + 1, min(i + 60, len(lines))):
            if Q_SRC.match(lines[j]):
                break
            m = ANS.search(lines[j])
            if m:
                raw = next((g for g in m.groups() if g), "")
                letters = "".join(sorted(set(re.findall(r"[A-E]", raw))))
                if letters:
                    found.add(letters)
                break
    if len(found) == 1:
        return found.pop(), "ok"
    if not found:
        return None, "命中但无答案行"
    return None, f"多处冲突{found}"


def main():
    docs, index = load_src()
    filled, skipped, files = 0, defaultdict(int), 0
    for fn in sorted(os.listdir(VOL)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        path = os.path.join(VOL, fn)
        lines = open(path, encoding="utf-8").read().split("\n")
        # 读取题目 + 答案表位置
        items, cur, key_ln, val_ln, keys = [], None, -1, -1, []
        for i, s in enumerate(lines):
            s = s.strip()
            mk = ROW_KEY.match(s)
            mv = ROW_VAL.match(s)
            if mk:
                key_ln = i; keys = [c.strip() for c in mk.group(1).split("|")]
            elif mv:
                val_ln = i
            m = Q_ANY.match(s)
            if m:
                if cur:
                    items.append(cur)
                cur = {"no": int(m.group(1)), "stem": m.group(3), "opt0": i}
            elif OPT.match(s) and cur is not None:
                pass
        if cur:
            items.append(cur)
        if val_ln < 0 or not keys:
            continue
        vals = [c.strip() for c in ROW_VAL.match(lines[val_ln].strip()).group(1).split("|")]
        ans = dict(zip(keys, vals))
        changed = False
        for it in items:
            no = str(it["no"])
            if ans.get(no, "").strip():
                continue
            letters, why = find_answer(it["stem"], docs, index)
            if letters:
                ans[no] = letters
                filled += 1
                changed = True
            else:
                skipped[why] += 1
        if changed:
            files += 1
            newvals = [ans.get(k, "") for k in keys]
            lines[val_ln] = "| 答案 | " + " | ".join(newvals) + " |"
            open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"回填 {filled} 题（涉及 {files} 份卷）")
    for k, v in sorted(skipped.items(), key=lambda x: -x[1]):
        print(f"  未回填[{k}]: {v}")


if __name__ == "__main__":
    main()
