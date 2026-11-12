# -*- coding: utf-8 -*-
"""Day7 三件套按「知识点归属章」重排（对齐 Day5/Day6：分节章号 == 归属章号），编号同步重排"""
import io, re, os

NL = chr(10)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exams', '错题本')
CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
CHNAME = {'01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险与信托',
          '05': '证券公司与基金管理公司', '06': '金融市场与金融工具', '07': '金融资产定价',
          '08': '公司治理与风险管理', '09': '货币供求与货币均衡', '10': '开放经济均衡',
          '11': '中央银行与金融调控'}


def collapse(txt):
    """把 2 行以上连续空行压成 1 行（只压缩成块交界的堆积，不动行内格式）"""
    import re as _re
    return _re.sub(r'\n{3,}', '\n\n', txt)


def load(p):
    return io.open(os.path.join(D, p), encoding='utf-8').read()


def save(p, txt):
    io.open(os.path.join(D, p), 'w', encoding='utf-8', newline='').write(txt)


def split_blocks(lines, pat, stoppat=None, droppat=None):
    """返回 (prefix, [(no, block_lines)], suffix)；droppat 命中的旧分节标题直接丢弃（会重建）。
    一旦命中 stoppat，其后所有行一律归入 suffix（尾部块正文不得丢进 prefix）。"""
    pre, blocks, suf, cur = [], [], [], None
    stopped = False
    for l in lines:
        if droppat and re.match(droppat, l):
            continue
        if stopped:
            suf.append(l); continue
        m = re.match(pat, l)
        if m:
            if cur: blocks.append(cur)
            cur = [int(m.group(1)), [l]]
            continue
        if stoppat and re.match(stoppat, l):
            if cur: blocks.append(cur); cur = None
            stopped = True
            suf.append(l); continue
        if cur is None:
            pre.append(l); continue
        cur[1].append(l)
    if cur: blocks.append(cur)
    return pre, blocks, suf


# ---------- 1. 详细版：先解析出每条的归属章号 ----------
det = load('Day7_知识点_详细版.md').split(NL)
pre, blocks, suf = split_blocks(det, r'^## D7-(\d\d)　', r'^## 本卷收账', r'^# 第.+部分 · 第')
assert len(blocks) == 60, len(blocks)
info = {}
for no, blk in blocks:
    m = next((re.match(r'^- \*\*知识点归属\*\*：第 (\d\d) 章', l) for l in blk if l.startswith('- **知识点归属')), None)
    assert m, no
    info[no] = m.group(1)

order = sorted(range(1, 61), key=lambda n: (info[n], n))   # 按章升序，同章保持原序
MAP = {old: i + 1 for i, old in enumerate(order)}          # 旧编号 → 新编号
def rm(t):
    return re.sub(r'D7-(\d\d)', lambda m: 'D7-%02d' % MAP.get(int(m.group(1)), int(m.group(1))), t)

# 章 → 新编号区间
parts = []
cur = None
for i, old in enumerate(order):
    ch = info[old]
    if cur is None or cur[0] != ch:
        if cur: parts.append(cur)
        cur = [ch, i + 1, i + 1]
    else:
        cur[2] = i + 1
parts.append(cur)


def rng(a, b):
    return 'D7-%02d～%02d' % (a, b) if b > a else 'D7-%02d' % a


cover = ' / '.join('%s 章%s' % (ch, CHNAME[ch]) for ch, _, _ in parts)
HEAD = """# Day 7 知识点 · 详细版

> 覆盖：金融__COVER__（按知识点归属章排序，第 12 章本卷无错题）
> 来源：Day 7 金融专业真题模考**第二套（整卷 110 题）**，错题 **65 道**（全错 61 + 半对 4），归并为 **60 条**知识点（Q11+Q96、Q98+Q100、Q53+Q54+Q56、Q90+Q95 合并同考点）
> 编号：**D7-01～60**，与 Day7 记忆版、秒杀版严格一一对应
> 2026-10-29

## 口径说明（别再混）

| 词 | 含义 | 本文件 |
|---|---|---|
| **条** | 知识点（同类错题合并后的条目） | **60 条** |
| **题** | 原始错题（错题本里的 ❌ 条数） | **65 道** |

两个数字不同是正常的：一道题可能同时触发两三个知识点，多道题也可能归到同一条。

## 本批四项铁律（读书前先看这里）

- **T1 选非只勾 ❌**：圈出「错误的是／不属于／不包括／不可能」，逐项打 ✅❌，**只勾 ❌**。本卷选非题 11 道（Q11、Q16、Q26、Q28、Q33、Q40、Q51、Q62、Q70、Q75、Q94），**一道没对**（E3 累计 50 次）
- **T2 多选五字母逐个 √×**：A→E 都要落笔，勾完回头再扫一遍 D 和 E。本卷 15 道多选只拿 11 分，**漏选 12 处、错选 9 处**（E4 累计 165、E5 累计 179）
- **T3 绝对化 / 半截句必划**：出现「主要来源于同业／有偿分配／自发固定／直接用于支付」先找反例；只写了前半句、没有结论的选项是不完整项，不勾
- **T4 数字与主体单独记**：成本收入比 45%、私募资管 1000 万/90 天/30-40-100 万、β=2.25、贴现价 97.5、证券咨询 5 人 …… 金融考的是原文数字，推理救不了

---""".replace('__COVER__', cover)

out = [HEAD]
pi = 0
for i, old in enumerate(order):
    ch = info[old]
    if pi < len(parts) and parts[pi][0] == ch and i + 1 == parts[pi][1]:
        out.append('')
        out.append('# 第%s部分 · 第 %s 章 %s（%s）' % (CN[pi], ch, CHNAME[ch], rng(parts[pi][1], parts[pi][2])))
        pi += 1
    out.append('')
    no, blk = next(b for b in blocks if b[0] == old)
    out.extend(rm(l) for l in blk)
out.append('')
out.extend(rm(l) for l in suf)
save('Day7_知识点_详细版.md', collapse(NL.join(out) + NL))
print('详细版重排 OK：%d 条 / %d 部分' % (len(order), len(parts)))

# ---------- 2. 记忆版 ----------
mem = load('Day7_知识点_记忆版.md').split(NL)
pre2, blocks2, suf2 = split_blocks(mem, r'^\*\*D7-(\d\d) ', r'^## 收尾三问', r'^## 第.+部分　第')
# pre2 含 HEAD + 首个 part 行之前的原 part/内容，需重建 HEAD
head2 = [l for l in pre2 if l.startswith('# ') or l.startswith('> ') or l.startswith('- **T') or
         l.startswith('## 早读四项铁律') or l.strip() == '---']
head2_txt = '''# Day 7 知识点　记忆版（早读 10 遍）

> 编号 **D7-01～60**，与详细版、秒杀版严格一一对应
> **读法两步**：先念「知识行」把知识点读完整；遮住「秒杀行」，自问自答再看答案
> 2026-10-29｜来源：Day 7 金融模考第二套 **65 道错题 → 60 条知识点**

## 早读四项铁律（朗读前先看一遍）

- **T1 选非只勾 ❌**：圈出「错误的是／不属于／不包括／不可能」，逐项打 ✅❌，**只勾 ❌**（本卷选非 11 道，一道没对）
- **T2 多选五字母逐个 √×**，勾完回头扫一遍 D 和 E（本卷漏选 12 处、错选 9 处，宁少选不错选）
- **T3 绝对化词 + 半截句必划**：「主要来源于同业／有偿分配／自发固定／直接用于支付」先找反例；只写前半句没有结论的选项不勾
- **T4 数字单独钉**：成本收入比 45%、β=2.25、贴现价 97.5、私募 1000 万/90 天/30-40-100 万、咨询 5 人

---'''
out2 = head2_txt.split(NL)
pi = 0
for i, old in enumerate(order):
    ch = info[old]
    if pi < len(parts) and parts[pi][0] == ch and i + 1 == parts[pi][1]:
        out2.append('')
        out2.append('## 第%s部分　第 %s 章 %s（%s）' % (CN[pi], ch, CHNAME[ch], rng(parts[pi][1], parts[pi][2])))
        pi += 1
        out2.append('')
    blk = next(b[1] for b in blocks2 if b[0] == old)
    out2.extend(rm(l) for l in blk)
    out2.append('')
out2.append(rm('## 收尾三问（读完自问，答不上来回详细版查编号）'))
out2.extend(rm(l) for l in suf2 if not l.startswith('## 收尾三问'))
save('Day7_知识点_记忆版.md', collapse(NL.join(out2) + NL))
blocks2_len = len(blocks2)
print('记忆版重排 OK：%d 条 / %d 部分' % (blocks2_len, pi))

# ---------- 3. 秒杀版 ----------
sec = load('Day7_知识点_秒杀版.md').split(NL)
pre3, blocks3, suf3 = split_blocks(sec, r'^\| D7-(\d\d) \|', r'^## 本卷六组钉子',
                                   r'^(## 第.+部分　第|\| 编号 \| 题眼 \| 秒杀 \||\|---\|---\|---\|)$')
head3 = [l for l in pre3 if l.startswith('# ') or l.startswith('> ')]
head3_txt = '''# Day 7 知识点　秒杀版（碎片时间刷反射）

> 编号 **D7-01～60**，与详细版、记忆版严格一一对应
> 用法：**只看左栏题眼，脱口说出右栏动作**，说不出来就回详细版查编号
> 2026-10-29｜**关注 🔴 标记**：那是本卷全灭或多次失手的地方'''
out3 = head3_txt.split(NL)
pi = 0
for i, old in enumerate(order):
    ch = info[old]
    if pi < len(parts) and parts[pi][0] == ch and i + 1 == parts[pi][1]:
        out3.append('')
        out3.append('## 第%s部分　第 %s 章 %s（%s）' % (CN[pi], ch, CHNAME[ch], rng(parts[pi][1], parts[pi][2])))
        pi += 1
        out3.append('')
        out3.append('| 编号 | 题眼 | 秒杀 |')
        out3.append('|---|---|---|')
    blk = next(b[1] for b in blocks3 if b[0] == old)
    out3.extend(rm(l) for l in blk)
out3.append('')
out3.append(rm('## 本卷六组钉子（考前扫一眼）'))
out3.extend(rm(l) for l in suf3 if not l.startswith('## 本卷六组钉子'))
save('Day7_知识点_秒杀版.md', collapse(NL.join(out3) + NL))
print('秒杀版重排 OK：%d 条 / %d 部分' % (len(blocks3), pi))

print('编号映射（旧→新）前 12：', {k: v for k, v in list(MAP.items())[:12]})
print('各部分：', [(p[0], rng(p[1], p[2])) for p in parts])
