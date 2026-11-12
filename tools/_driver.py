# -*- coding: utf-8 -*-
"""诊断 + 驱动：先单独测删除耗时，再跑主流程，全程计时输出到 stderr"""
import os
import sys
import time

T0 = time.time()
ROOT = r"F:\自己创建的skill\学习\中级经济师 - 金融学习"
D = os.path.join(ROOT, "exams", "真题分章卷")


def log(m):
    sys.stderr.write(f"[{time.time() - T0:6.2f}s] {m}\n")
    sys.stderr.flush()


log("driver start")
os.makedirs(D, exist_ok=True)

# 1) 删除旧文件（用 Python，绕开 rm）
log("skip cleaning (slow on win)")

# 2) 加载主脚本模块（不执行 main）
src_path = os.path.join(ROOT, "tools", "parse_zhenti.py")
src = open(src_path, encoding="utf-8").read().replace(
    'if __name__ == "__main__":\n    main()', "")
g = {"__file__": src_path, "__name__": "pz"}
exec(compile(src, "pz", "exec"), g)
log("module loaded")

# 3) 解析
SRCD = os.path.join(ROOT, "notes", "真题库", "txt")
all_items = []
for fn in sorted(os.listdir(SRCD)):
    if not (fn.startswith("真题_") and fn.endswith(".txt")):
        continue
    subj = "金融" if "金融" in fn else "经基"
    its = g["parse_full"](os.path.join(SRCD, fn), subj)
    for it in its:
        it["vol"] = fn[:-4]
    all_items.extend(its)
log(f"parsed {len(all_items)}")

# 4) 归类
for it in all_items:
    keys = g["JR_KEYS"] if it["subject"] == "金融" else g["JJ_KEYS"]
    c, nm, s = g["classify"](it, keys)
    it["chap"], it["chap_name"], it["score"] = c, nm, s
log("classified")

# 5) 输出分章卷
nfiles = 0
for subj, keys, prefix in (("经基", g["JJ_KEYS"], "经基"), ("金融", g["JR_KEYS"], "金融")):
    for code, name, _ in keys:
        items = [i for i in all_items if i["subject"] == subj and i["chap"] == code]
        if not items:
            continue
        for pi in range(0, len(items), 10):
            chunk = items[pi:pi + 10]
            seq = pi // 10 + 1
            total = (len(items) + 9) // 10
            fn = f"{prefix}第{int(code):02d}章_{name}_{seq:02d}.md"
            srcs = sorted({i["vol"].replace("真题_", "") for i in chunk})
            L = [f"# {prefix}第 {code} 章 {name} · 真题卷 {seq}/{total}", "",
                 f"> 来源：{'、'.join(srcs)}｜共 {len(chunk)} 题｜建议 {len(chunk)} 分钟",
                 "> ⏱ 单选 ≤50 秒｜多选 ≤75 秒（多选少选每项 0.5 分，错选 0 分）",
                 "", "---", ""]
            for k, it in enumerate(chunk, 1):
                tag = "多选" if it.get("is_multi") else "单选"
                L.append(f"**{k}.**（{tag}）{it['stem']}")
                for letter, body in it["opts"]:
                    L.append(f"{letter}. {body}")
                L.append("")
            L += ["---", "", "<details><summary>答案速查（做完再看）</summary>", "",
                  "| 题 | " + " | ".join(str(x) for x in range(1, len(chunk) + 1)) + " |",
                  "|" + "---|" * (len(chunk) + 1),
                  "| 答案 | " + " | ".join(i.get("answer", "?") for i in chunk) + " |",
                  "", "</details>"]
            with open(os.path.join(D, fn), "w", encoding="utf-8") as f:
                f.write("\n".join(L) + "\n")
            nfiles += 1
log(f"dumped {nfiles} files")

# 6) 未归类
un = [i for i in all_items if i["chap"] == "0"]
if un:
    with open(os.path.join(D, "_未归类待判.md"), "w", encoding="utf-8") as f:
        f.write(f"# 未归类真题 {len(un)} 道（需人工判章）\n\n")
        for k, it in enumerate(un, 1):
            f.write(f"**{k}.** [{it['subject']}/{it['vol']}] {it['stem']}\n")
            for letter, body in it["opts"]:
                f.write(f"{letter}. {body}\n")
            f.write(f"答案：{it.get('answer', '?')}\n\n")
log(f"unclassified {len(un)}")
log("ALL DONE")
