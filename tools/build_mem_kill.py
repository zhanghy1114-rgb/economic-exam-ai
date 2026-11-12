# -*- coding: utf-8 -*-
"""从《金融·考前终极一本通》生成配套记忆版 + 秒杀版（编号 F-xx 严格一一对应）"""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, 'exams', '错题本')
SRC = os.path.join(BANK, '金融·考前终极一本通.md')

s = open(SRC, encoding='utf-8').read()
parts = re.split(r'\n# 第 (\d{2}) 章 ', s)

CHAP = {}
items = []
for i in range(1, len(parts), 2):
    ch = int(parts[i])
    name = parts[i + 1].split('（')[0].strip()
    body = parts[i + 1] + '\n## __END__'
    CHAP[ch] = name
    for m in re.finditer(r'\n## (F-\d{2,3})　([^\n]*)\n(.*?)(?=\n## F-|\n# 第|\n## 收账|\n## __END__)', body, re.S):
        fid, title, blk = m.group(1), m.group(2), m.group(3)
        g = re.search(r'\*\*知识点归属\*\*：(.+)', blk)
        belong = g.group(1).strip() if g else ''
        j = re.search(r'\*\*知识点全解\*\*[：:]?\s*(.*?)(?=\n- \*\*考法\*\*)', blk, re.S)
        jie = j.group(1).strip() if j else ''
        k = re.search(r'\*\*考法\*\*[：:]?\s*(.*?)(?=\n- \*\*错因\*\*)', blk, re.S)
        kao = k.group(1).strip() if k else ''
        e = re.search(r'\*\*错因\*\*[：:]?\s*(.*?)(?=\n- \*\*记忆锚\*\*)', blk, re.S)
        err = e.group(1).strip() if e else ''
        a = re.search(r'\*\*记忆锚\*\*[：:]?\s*(.*?)$', blk, re.S)
        anchor = a.group(1).strip() if a else ''
        items.append(dict(fid=fid, ch=ch, title=title, belong=belong, jie=jie,
                          kao=kao, err=err, anchor=anchor))

print('解析条目:', len(items))


def clean(t, n=200):
    """压成一行陈述"""
    t = re.sub(r'\n+', ' ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    t = t.replace('**', '').strip(' 　-|')
    if len(t) > n:
        cut = t[:n]
        p = max(cut.rfind('。'), cut.rfind('；'), cut.rfind('，'))
        t = cut[:p + 1] if p > 40 else cut + '…'
    return t.strip()


def knowledge(it):
    """知识行 = 结论式标题 + 全解里最关键的一句判据（控制在 90 字内，早读能念）"""
    head = re.sub(r'\s*[（(].*?[)）]\s*', '', it['title']).strip(' 　｜|')
    head = re.sub(r'🔴|🟠', '', head).strip()
    jie = it['jie']
    jie = re.sub(r'〔D[67]-\d{2}〕', '', jie)
    core = ''
    # 1) 优先抓 ⚠️ 判据句
    for m in re.finditer(r'⚠️\s*([^\n]+)', jie):
        t = m.group(1).strip()
        if len(t) >= 8:
            core = t
            break
    # 2) 否则抓全解第一个完整句
    if not core:
        flat = re.sub(r'\n+', ' ', jie)
        flat = re.sub(r'\s{2,}', ' ', flat).replace('**', '')
        m = re.search(r'([^。；]{12,90}[。；])', flat)
        core = m.group(1).strip() if m else flat[:70]
    if '|' in core or core.startswith('---'):
        rows = [r for r in jie.split('\n') if '|' in r and not re.match(r'^\s*\|?[\s\-:|]+\|?\s*$', r)]
        if len(rows) >= 2:
            cells = [c.strip() for c in rows[1].strip('|').split('|')]
            cells = [c for c in cells if c]
            core = '：'.join(cells[:2])
    core = re.sub(r'\s{2,}', ' ', core).replace('**', '').strip(' 　-|')
    core = re.sub(r'^[-•·\d\.\s]+', '', core)
    if len(core) > 88:
        cut = core[:88]
        pp = max(cut.rfind('，'), cut.rfind('；'), cut.rfind(' '))
        core = cut[:pp] if pp > 40 else cut
    txt = head + ('——' + core if core else '')
    return re.sub(r'\s{2,}', ' ', txt).strip(' —')


def kill(it):
    """秒杀行：题眼 → 答案，取自记忆锚；无锚则用考法"""
    a = clean(it['anchor'], 120)
    if not a:
        a = '见' + clean(it['kao'], 60)
    return a


# ---------- 记忆版 ----------
L = []
A = L.append
A('# 金融 · 终极记忆版（F-01～F-%s）' % items[-1]['fid'].split('-')[1])
A('')
A('> **配套**：与《金融·考前终极一本通》详细版、秒杀版编号严格一一对应（F-xx）')
A('> **用法（早读 15-20 分钟）**：每条两步——①**先念「知识行」**（朗读打底，能换皮做题）；②**遮住 ⚡ 行自问自答**（题眼→答案）。答不上来的条打 ★，次日只回炉打 ★ 的')
A('> **生成**：2026-10-30 ｜ 来源：Day6 第一套模考 + Day7 第二套模考，143 道错题归并 125 条')
A('')
A('## 开读前四铁律')
A('')
A('- **T1 选非只勾 ❌**：圈「错误的是／不属于／不包括」，逐项 ✅❌，只勾 ❌')
A('- **T2 多选五字母逐个 √×**：A→E 都落笔，宁少选不错选')
A('- **T3 绝对化先找反例**：只能／必须／任何／全部 → 先找反例')
A('- **T4 数字与主体单独记**：见数字先问"谁的数"')
A('')
cur = None
for it in items:
    if it['ch'] != cur:
        cur = it['ch']
        A('---')
        A('')
        A('# 第 %02d 章 %s' % (cur, CHAP[cur]))
        A('')
    A('**%s　%s**' % (it['fid'], it['belong'].split('·')[-1].strip()))
    A('')
    A('- 知识行：%s' % knowledge(it))
    A('- ⚡秒杀：%s' % kill(it))
    A('')
A('---')
A('')
A('## 三问自查（读完合上本子自问）')
A('')
A('1. 第 03 章（商业银行）的数字串，你能一口气报出几个？（资本充足率 5/6/8 · 集中度 10/15 · 不良率 5/4 · 成本收入比 45 · 存保 50 万 · 村镇 100 万）')
A('2. 第 07 章三个绩效指数，分母分别是啥？（夏普 σ · 特雷诺 β · 詹森是差）')
A('3. 第 11 章双支柱：货币政策管什么、宏观审慎管什么？（总量与物价 / 杠杆与系统性风险）')
A('')
p1 = os.path.join(BANK, '金融·终极记忆版.md')
open(p1, 'w', encoding='utf-8').write('\n'.join(L))

# ---------- 秒杀版 ----------
L2 = []
B = L2.append
B('# 金融 · 终极秒杀版（题眼 → 答案）')
B('')
B('> **用法（碎片时间）**：只看「题眼」列，脑子里先出答案，再看「秒杀」列对。对不上就翻详细版对应 F-xx')
B('> **编号**：F-xx 与详细版、记忆版一一对应')
B('')
cur = None
for it in items:
    if it['ch'] != cur:
        cur = it['ch']
        B('')
        B('## 第 %02d 章 %s' % (cur, CHAP[cur]))
        B('')
        B('| 编号 | 题眼（看到什么） | 秒杀（选什么/划什么） |')
        B('|---|---|---|')
    eye = re.sub(r'[（(].*?[)）]', '', it['title']).strip(' 　｜|')
    eye = re.sub(r'🔴|🟠', '', eye).strip()
    eye = eye.split('：')[0].split('（')[0].strip()
    if len(eye) > 26:
        eye = eye[:26]
    kil = kill(it).replace('|', '／').replace('\n', ' ')
    B('| %s | %s | %s |' % (it['fid'], eye, kil))
B('')
B('---')
B('')
B('**秒杀三句总纲**：①选非题只勾 ❌；②多选宁少选不错选；③绝对化词先找反例。')
B('')
p2 = os.path.join(BANK, '金融·终极秒杀版.md')
open(p2, 'w', encoding='utf-8').write('\n'.join(L2))
print('written:', p1, os.path.getsize(p1), '|', p2, os.path.getsize(p2))
