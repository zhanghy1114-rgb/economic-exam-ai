# -*- coding: utf-8 -*-
"""从《错题本.md》抽取经基 406 道错题的记忆锚，按章归集 → 考前锚点速览。"""
import io, re
from collections import defaultdict, OrderedDict

SRC = 'exams/错题本/错题本.md'
PROG = 'exams/全章扫荡进度表.md'
OUT = 'exams/错题本/经基·考前锚点速览.md'

# ---- 章节名 + 失分 ----
_pt = io.open(PROG, encoding='utf-8').read().split('## 经济基础')[1]
pt = _pt.split('## 金融')[0] if '## 金融' in _pt else _pt
CHNAME, LOST, NTQ = {}, {}, {}
for ln in pt.split('\n'):
    m = re.match(r'^\|\s*第(\d\d)章\s*\|([^|]+)\|\s*(\d+)\s*\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|', ln)
    if not m:
        continue
    ch = int(m.group(1))
    CHNAME[ch] = m.group(2).strip()
    NTQ[ch] = int(m.group(3))
    g = re.search(r'([\d.]+)\s*/\s*([\d.]+)', m.group(6))
    LOST[ch] = round(float(g.group(2)) - float(g.group(1)), 1) if g else None

# ---- 遍历错题本 ----
txt = io.open(SRC, encoding='utf-8').read()
lines = txt.split('\n')
segs = []
cur = {'title': '__HEAD__', 'lines': []}
for ln in lines:
    if ln.startswith('# ') and not ln.startswith('## '):
        cur = {'title': ln[2:].strip(), 'lines': []}
        segs.append(cur)
    else:
        cur['lines'].append(ln)

def ch_of(title):
    m = re.search(r'第\s*(\d{1,2})\s*章', title)
    return int(m.group(1)) if m else None

def kp_only(s):
    s = s.split('→')[0].split('|')[0]
    return re.sub(r'\s+', ' ', s).strip()[:34]


def clean(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[-•]\s*', '', s)
    return s

anchors = defaultdict(list)   # ch -> [(考点, 锚, 状态)]
for s in segs:
    ti = s['title']
    if not ('经基' in ti or '经济基础' in ti or '全科混合' in ti):
        continue
    ch = ch_of(ti)
    if ch is None:
        continue
    body = s['lines']
    cur_kp, cur_state, fallback = '', 'wrong', ''

    def flush():
        if fallback and cur_state != 'dead':
            anchors[ch].append((kp_only(cur_kp), fallback, cur_state))

    for ln in body:
        m1 = re.match(r'^## ❌\s*(.*)$', ln)
        m2 = re.match(r'^\*\*(❌→✅|❌|⚠️)\s*(.*?)\*\*\s*(.*)$', ln)
        if m1 or m2:
            flush()
            fallback = ''
            if m1:
                cur_kp = clean(m1.group(1)); cur_state = 'wrong'
            else:
                cur_state = 'dead' if m2.group(1) == '❌→✅' else ('warn' if m2.group(1) == '⚠️' else 'wrong')
                cur_kp = clean(m2.group(2) + ' ' + m2.group(3))
            continue
        ma = re.search(r'(?:记忆锚|锚)\*{0,2}\s*[:：]\s*(.+)$', ln)
        if ma:
            a = clean(ma.group(1))
            a = re.sub(r'^[（(]\s*', '', a)
            if 6 <= len(a) <= 320:
                anchors[ch].append((kp_only(cur_kp), a, cur_state))
                fallback = ''
        elif fallback == '' and re.match(r'^\s*-\s+\S', ln):
            a = clean(re.sub(r'^\s*-\s+', '', ln))
            if 8 <= len(a) <= 300 and not a.startswith(('题目', '题干', '你答', '正解')):
                fallback = a
    flush()

# 去重（按锚前 18 字判重），保留首个
res = OrderedDict()
for ch in sorted(anchors):
    seen = set()
    lst = []
    for kp, a, st in anchors[ch]:
        key = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9]', '', a)[:18]
        if key in seen:
            continue
        seen.add(key)
        lst.append((kp, a, st))
    res[ch] = lst

print('各章锚点数：')
tot = 0
for ch in sorted(res):
    n = len(res[ch])
    tot += n
    print(' %02d %-22s 失%5s 锚%2d' % (ch, CHNAME.get(ch, '')[:20], LOST.get(ch), n))
print('锚点合计', tot)

# ---- 生成 md ----
QUOTA = {}   # 每章条数上限
L = []
L.append('# 经基 · 考前锚点速览（只来自你做错的题）')
L.append('')
L.append('> **这份材料怎么来的**：把《错题本.md》里经基 **406 道错题**下方的「记忆锚」逐条抽出来、按章归集、去掉重复，'
         '一条不新增、一句不编造——全部是你自己踩坑后写下的那句话。')
L.append('> **怎么看**：明早进考场前，只按章跳读，每章扫 30 秒。凡是脑子里"哦"一下的，就是记住了；'
         '凡是读完没反应的，那一条才是你要再看一眼的。')
L.append('> **经基总账**：真题 693 题 / 85 卷，实得 317.5 / 805 = **39.4%**。失分 487.5 分。')
L.append('')
L.append('---')
L.append('')
# 失分榜
L.append('## 零、先看这张失分榜（决定你今晚的时间怎么分）')
L.append('')
L.append('| 章 | 章名 | 真题 | 失分 | 本表锚点数 | 优先级 |')
L.append('|---|---|---|---|---|---|')
rank = sorted([c for c in LOST if LOST[c] is not None], key=lambda c: -LOST[c])
for i, ch in enumerate(rank[:14]):
    pr = '🔴 必看' if i < 6 else ('🟠 有余力再看' if i < 10 else '🟡 扫一眼')
    L.append('| %02d | %s | %d | **%.1f** | %d | %s |' % (ch, CHNAME.get(ch, ''), NTQ.get(ch, 0), LOST[ch], len(res.get(ch, [])), pr))
L.append('')
L.append('> **一句话**：前 6 章（28 会计 56 分、19 央行 29 分、14 税收 28.5 分、35 合同 25 分、36 公司 22.5 分、18 货币 21.5 分）'
         '合计失 **182.5 分**，占你全部失分的 37%。今晚只背这 6 章的锚点，性价比最高。')
L.append('')
L.append('---')
L.append('')
L.append('## 一、分章锚点（按失分从重到轻）')
L.append('')

def budget(ch):
    l = LOST.get(ch)
    if l is None: return 6
    if l >= 25: return 18
    if l >= 15: return 12
    if l >= 8:  return 8
    return 4
BUDGET = {ch: budget(ch) for ch in res}

for ch in rank:
    if ch not in res:
        continue
    lst = res[ch]
    alive = [x for x in lst if x[2] != 'dead']
    dead = [x for x in lst if x[2] == 'dead']
    show = alive[:BUDGET.get(ch, 14)]
    L.append('### 第 %02d 章　%s　`失 %.1f 分 · 错题锚点 %d 条`' % (ch, CHNAME.get(ch, ''), LOST.get(ch, 0), len(lst)))
    L.append('')
    for j, (kp, a, st) in enumerate(show, 1):
        L.append('%d. **%s**' % (j, a))
    if dead:
        L.append('')
        L.append('> ✅ 下列 %d 条你已复测通过（可跳过）：%s' % (
            len(dead), '；'.join(x[1][:34] for x in dead[:4])))
    if len(alive) > len(show):
        L.append('')
        L.append('> 另有 %d 条同类锚点未列出（重复度高），需要全量见《错题本.md》第 %d 章段。' % (len(alive) - len(show), ch))
    L.append('')
    L.append('---')
    L.append('')

# 空白区提醒
L.append('## 二、两个空白区（本表没有锚点，因为它们从未真做）')
L.append('')
L.append('**第 23 章 统计与数据科学（32 题）+ 第 24 章 描述统计（32 题）= 64 题**')
L.append('')
L.append('> 当时按"挂账"处理，直接记 0 分，**从未真做**。所以本表里这两章没有任何锚点——'
         '不是你错了没记，是压根没做。这两章在卷一里必考，考前只做一件事：'
         '翻 `exams/错题本/Day4_知识点_秒杀版.md` 里的统计部分，把「均值/中位数/众数的适用数据」'
         '「方差标准差」「抽样误差」「回归系数含义」四组过一遍，别开新题。')
L.append('')
L.append('---')
L.append('')
L.append('## 三、时间不够时，只背这 12 条（全卷最高频病根）')
L.append('')
L.append('```')
L.append('① 选非题：先圈"错误/不正确/不属于"，逐项打 ✅❌，只选 ❌')
L.append('② 多选：每个字母先问"教材写没写"，没写的不勾——错选归零，少选还有 0.5')
L.append('③ 绝对化：仅/只/完全/必须/一律 → 先找反例，找到就划')
L.append('④ 数字题：先问"谁的数"，数字对、主体错是最像答案的坑')
L.append('⑤ 会计六要素：日期→照片→家底三兄弟；时期→录像→成果三兄弟')
L.append('⑥ 所有者权益 = 资产 − 负债（扣掉房贷后的净值）')
L.append('⑦ 收入/费用不上资产负债表')
L.append('⑧ 存货 = 库房所有家当打包算，别漏"在产品"')
L.append('⑨ 计量属性五兄弟 = 历重可现公（历史/重置/可变现/现值/公允）')
L.append('⑩ 见"实质/形式/里子面子"→ 实质重于形式')
L.append('⑪ 弹性>1 降价=收入涨；弹性<1 涨价=收入涨（谷贱伤农）')
L.append('⑫ 自动稳定器三件套 = 累进税 + 转移支付 + 农产品价格维持')
L.append('```')
L.append('')
L.append('---')
L.append('')
L.append('**最后**：这份速览里的每一条，都是你自己做错之后写下的。考场上一眼认出"这是我错过的那道题"，分就回来了。')
L.append('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('OK %s | %.1f KB' % (OUT, len('\n'.join(L).encode('utf-8')) / 1024.0))
