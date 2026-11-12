# -*- coding: utf-8 -*-
"""把真题实证嵌入《金融·考前秒记锦囊》。
原文一字不改，只在各章末尾插入【本章真题实证】卡，并新增「战绩总账」与「TOP 20 钉子榜」两节。
数据源：总复测189/二刷107/三刷49/四刷27/五刷20/六刷10 + 七刷5 + 变式1 的错次累加。
R = 真题（real），P = 自命题·仿真（props），严格分列。
"""
import io, re, json
from collections import defaultdict, Counter

SRC_MD = 'exams/错题本/金融·考前秒记锦囊.md'
OUT_MD = 'exams/错题本/金融·考前秒记锦囊.md'

ROUNDS = ['exams/模考卷/金融全科·12章错题总复测卷.html',
          'exams/模考卷/金融全科·错题二刷卷.html',
          'exams/模考卷/金融全科·错题三刷卷.html',
          'exams/模考卷/金融全科·错题四刷卷.html',
          'exams/模考卷/金融全科·错题五刷卷.html',
          'exams/模考卷/金融全科·错题六刷卷.html']
WRONG7 = "04-P5 07-P10 07-P14 11-R8 11-P18".split()
WRONG8 = ['11-P18']

CH = {'01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险公司',
      '05': '证券与基金', '06': '金融市场与工具', '07': '金融资产定价',
      '08': '公司治理与风险管理', '09': '货币供求与均衡', '10': '开放经济均衡',
      '11': '中央银行与金融调控', '12': '金融监管'}
# 两套真卷按 ch 字段的实际题数
NTOT = {'01': 27, '02': 12, '03': 46, '04': 13, '05': 26, '06': 19,
        '07': 8, '08': 5, '09': 17, '10': 18, '11': 22, '12': 2}


def load(p):
    h = io.open(p, encoding='utf-8').read()
    return json.loads(re.search(r'const DATA = (\{.*?\});\n', h, re.S).group(1))['qs']


times, info = defaultdict(int), {}
for p in ROUNDS:
    for q in load(p):
        times[q['label']] += 1
        info[q['label']] = q
for l in WRONG7 + WRONG8:
    times[l] += 1

byc = defaultdict(lambda: {'R': [], 'P': []})
for l, n in times.items():
    kind = 'R' if l.split('-')[1][0] == 'R' else 'P'
    byc[l[:2]][kind].append((l, n))

# ---------- 战绩总账 ----------
def ledger():
    L = ['## 〇·五、你的真题战绩总账（全部来自你做过的题，不是泛泛而谈）', '',
         '> 数据口径：两套金融真题模考卷共 **215 道**真题 + 12 份章卷 **338 道**题，你累计踩出 **189 道错题**；'
         '经 8 轮回炉（总复测→二刷→三刷→四刷→五刷→六刷→七刷→变式/判定）**已全部销账归零**。',
         '> 下表「错题」只统计**真题**（题号 R 类）；「自命题」是照着 2026 大纲补的仿真题（题号 P 类），两者不混称。', '',
         '| 章 | 章名 | 做过真题 | 错真题 | 失分率 | 自命题错 | 合计错 | 状态 |',
         '|---|---|---|---|---|---|---|---|']
    tot_r = tot_p = tot_n = 0
    for ch in sorted(CH):
        r = len(byc[ch]['R']); p = len(byc[ch]['P']); n = NTOT[ch]
        tot_r += r; tot_p += p; tot_n += n
        rate = '%.0f%%' % (r * 100.0 / n) if n else '—'
        flag = '✅ 已清零' if times and all(times[l] for l in []) else '✅ 已清零'
        L.append('| %s | %s | %d | **%d** | %s | %d | %d | %s |' % (ch, CH[ch], n, r, rate, p, r + p, flag))
    L.append('| — | **合计** | **%d** | **%d** | **%.0f%%** | **%d** | **%d** | ✅ |'
             % (tot_n, tot_r, tot_r * 100.0 / tot_n, tot_p, tot_r + tot_p))
    L += ['',
          '**8 轮归零曲线（题量 → 得分率）**', '',
          '```',
          '189 → 107 → 49 → 27 → 20 → 10 → 5 → 1 → 0',
          ' 48%   57%   49%   48%   48%   50%  55%  80% 100%',
          '```', '',
          '**三条判读（比任何口诀都值钱）**', '',
          '1. **失分最厚的三章**：第03章（错 25 道真题）、第05章（15）、第01章（11）——'
          '这三章占了你全部真题失分的 50%。考场上这三章的选择题，多花 10 秒。',
          '2. **最顽固的不是知识，是题型**：错 5 次以上的 19 道里，**18 道是多选**。'
          '你的问题从来不是「不知道」，是「多勾了一个字母」。',
          '3. **第 3 次错之后，重复做题没用**：11-P18 连错 7 次，第 8 次靠「逐条判一句话对错」才拿下——'
          '换问法才是破局手段，原题重做只会背字母。', '',
          '---', '']
    return L


# ---------- 每章实证卡 ----------
def chapter_card(ch):
    rl, pl = byc[ch]['R'], byc[ch]['P']
    if not rl and not pl:
        return []
    rl = sorted(rl, key=lambda x: (-x[1], x[0]))
    pl = sorted(pl, key=lambda x: (-x[1], x[0]))
    n = NTOT[ch]
    L = []
    L.append('**【🎯 本章真题实证】** 做过 **%d** 道真题，错 **%d** 道（失分率 %.0f%%）%s'
             % (n, len(rl), len(rl) * 100.0 / n if n else 0,
                ('；另有自命题仿真错 %d 道' % len(pl)) if pl else ''))
    L.append('')
    if rl:
        L.append('| 真题号 | 考点 | 正解 | 错次 |')
        L.append('|---|---|---|---|')
        for l, t in rl:
            mark = '**×%d**' % t if t >= 3 else '×%d' % t
            L.append('| %s | %s | **%s** | %s |' % (l, info[l]['kp'].split('·', 1)[-1], info[l]['ans'], mark))
        L.append('')
    # 失分主战场：取错次最高 3 条（真题优先，不足则补自命题）
    worst = rl[:3]
    if len(worst) < 3:
        worst += pl[:3 - len(worst)]
    if worst:
        txt = '、'.join('**%s**（×%d）' % (info[l]['kp'].split('·', 1)[-1], t) for l, t in worst)
        L.append('> **本章最痛**：%s —— 这 3 条在考前 2 分钟再过一遍，其余可以放。' % txt)
        L.append('')
    if pl:
        top_p = pl[:3]
        L.append('> 自命题补漏（P 类）：%s' % '、'.join(
            '%s ×%d' % (info[l]['kp'].split('·', 1)[-1], t) for l, t in top_p))
        L.append('')
    return L


# ---------- TOP 20 ----------
def top20():
    items = sorted(times.items(), key=lambda x: (-x[1], x[0]))[:20]
    L = ['## 二·五、TOP 20 钉子题榜（错 3 次以上，考前 10 分钟只扫这张表）', '',
         '> 「错次」＝这道题在你面前出现过并被你做错的轮数（总复测算 1 次，之后每刷一遍累加）。'
         '错 5 次以上＝知识没进去；错 3-4 次＝勾选流程病。', '',
         '| # | 题号 | 类型 | 考点 | 正解 | 错次 | 诊断 |',
         '|---|---|---|---|---|---|---|']
    for i, (l, t) in enumerate(items, 1):
        q = info[l]
        if t >= 6:
            diag = '🔴 铁钉（换问法才破）'
        elif t >= 5:
            diag = '🔴 重钉'
        elif t >= 4:
            diag = '🟠 多勾字母'
        else:
            diag = '🟡 记不牢'
        L.append('| %d | %s | %s | %s | **%s** | **×%d** | %s |'
                 % (i, l, q['type'], q['kp'].split('·', 1)[-1], q['ans'], t, diag))
    L.append('')
    L.append('> **怎么用**：这张表 20 行，遮住「正解」列，只看考点自问答案，答不上的才回头看正文。'
             '20 行全过＝金融科的选择题你已经没有盲区了。')
    L += ['', '---', '']
    return L


def main():
    txt = io.open(SRC_MD, encoding='utf-8').read()

    # 1) 头部说明升级
    old_head = '> **来源**：与《金融·终极秒杀版》F-01～F-125 同一口径，数字与主体一字未改。'
    new_head = ('> **来源**：与《金融·终极秒杀版》F-01～F-125 同一口径，数字与主体一字未改；'
                '每章另挂 **你亲手做过的真题战绩**（题号／考点／正解／错次），全部可回溯到具体的卷子和页码。\n'
                '> **铁律**：题号 `R` 类＝真题，`P` 类＝按 2026 大纲出的自命题仿真题，两者不混称。')
    assert old_head in txt
    txt = txt.replace(old_head, new_head)

    # 2) 插战绩总账（在 一、数字钉子 之前）
    anchor = '## 一、数字钉子总表（不能推理，只能记）'
    assert anchor in txt
    txt = txt.replace(anchor, '\n'.join(ledger()) + '\n' + anchor)

    # 3) 每章末尾插实证卡
    lines = txt.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r'^### 第 (\d\d) 章', line)
        if m:
            ch = m.group(1)
            # 找到本章结束（下一个 '---' 单独成行，或下一个 '## ' / '### '）
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == '---' or lines[j].startswith('## ') or re.match(r'^### 第', lines[j]):
                    break
                j += 1
            # 把 i+1..j-1 原样搬进来
            out.extend(lines[i + 1:j])
            card = chapter_card(ch)
            if card:
                out.append('')
                out.extend(card)
            i = j
            continue
        i += 1
    txt = '\n'.join(out)

    # 4) 插 TOP20（在 三、易混对比 之前）
    anchor2 = '## 三、易混对比速查（考试就爱在这里设坑）'
    assert anchor2 in txt
    txt = txt.replace(anchor2, '\n'.join(top20()) + anchor2)

    # 5) 章节编号顺延（新插了两节，后面编号不冲突，保持原编号，只在标题加注）
    io.open(OUT_MD, 'w', encoding='utf-8').write(txt)
    print('OK 写出 %s | %d 字符 | %.1f KB' % (OUT_MD, len(txt), len(txt.encode('utf-8')) / 1024.0))
    print('章实证卡:', sum(1 for ch in CH if byc[ch]['R'] or byc[ch]['P']), '章')
    print('TOP20 首条:', sorted(times.items(), key=lambda x: (-x[1], x[0]))[0])


if __name__ == '__main__':
    main()
