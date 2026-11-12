# -*- coding: utf-8 -*-
"""把 03 章训练卷①的 33 道错题批量写入 错题本.md 顶部（2026-11-02）"""
import re, io, json

DATA = io.open('tools/_ch3_drill_data.json', encoding='utf-8').read()
D = json.loads(DATA)

MY = {  # 本次作答（来自打印版错题清单）
    'R1':'C','R2':'A','R3':'C','R4':'B','R5':'D','R6':'BC','R7':'BDE','R8':'ACE','R9':'CE',
    'R10':'AE','R11':'ABC','R12':'AB','R13':'ACD','R14':'A','R15':'B','R17':'A','R18':'C',
    'R19':'A','R20':'A','R21':'D','R22':'D','R23':'AB','R24':'BCDE','R26':'CD','R27':'DE',
    'P3':'B','P4':'C','P5':'A','P6':'A','P7':'C','P8':'A','P9':'AD','P11':'ABC',
}
ERR_LABELS = list(MY.keys())
RES = {k: ('少选' if set(MY[k]) < set(D[k]['ans']) else '错误') for k in ERR_LABELS}

# 病因码
E1 = {'R4', 'P5'}                       # 方向/图形反转
E3 = {'R22', 'P8'}                      # 单选选非方向
def cause(lb):
    q = D[lb]
    if lb in E1: return ('E1', '方向反转')
    if lb in E3: return ('E3', '选非方向')
    if q['type'] == '多选':
        return ('E5', '多选漏选') if RES[lb] == '少选' else ('E4', '多选错选')
    return ('E2', '概念混淆/张冠李戴')

def short(stem, n=42):
    t = re.sub(r'\s', '', stem)
    return t[:n] + ('…' if len(t) > n else '')

def fmt_my(s):
    return '、'.join(s)

lines = []
n_multi = sum(1 for lb in ERR_LABELS if D[lb]['type'] == '多选')
n_single = len(ERR_LABELS) - n_multi
wrong_multi = sum(1 for lb in ERR_LABELS if D[lb]['type'] == '多选' and RES[lb] == '错误')
skip_multi = sum(1 for lb in ERR_LABELS if D[lb]['type'] == '多选' and RES[lb] == '少选')

lines.append('# 金融03章 商业银行 · 即时判题训练卷①（错题回炉27 + 自命题11，2026-11-02）')
lines.append('')
lines.append('> 首测 **13/54（24%）**，合格线 32 —— **未过线，差 19 分**｜状态：🔴 崩盘警报')
lines.append('> 分节：错题回炉 **7.5/40（19%）** 🔴🔴（这些题 10-28/29 模考刚错过）｜自命题 **5.5/14（39%）** 🔴')
lines.append('> 结构：全对 5｜**少选 5**｜**错误 28**｜未答 0（19 单选错 + 9 多选错选 + 5 少选 = 33）')
lines.append('> ⚠️ **诊断（卷内自带）**：主要问题不是不知道，而是**提取不稳**：28 题错选 + 5 题少选。02 章错题回炉 80% → 03 章 19%，同一路径得分坍塌——03 章错题从没按章复盘过（只在 Day6/Day7 知识点里躺了 5 天），数字钉子密集（7 题数字题全错），见下分节复盘')
lines.append('')
lines.append('### 单选（错 %d）' % n_single)
lines.append('')

for lb in ERR_LABELS:
    q = D[lb]
    code, cname = cause(lb)
    kp = q.get('kp', '').replace('第3章:', '').replace('第6章:', '（跨6章）') or '商业银行'
    tag_extra = ''
    if RES[lb] == '少选':
        tag_extra = ' · 少选得 %.1f' % (0.5 * len([c for c in MY[lb] if c in q['ans']]))
    lines.append('**❌ %s（%s·%s %s%s）** %s → 用户 **%s**，正解 **%s**'
                 % (lb, kp, cname, code, tag_extra, short(q['stem']), fmt_my(MY[lb]), q['ans']))
    opts_line = '｜'.join('%s %s' % (o['k'], o['t'][:34]) for o in q['opts'])
    lines.append('- 原题选项：%s' % opts_line)
    if q.get('traps'):
        lines.append('- 错因点：%s' % q['traps'][0])
    anchor = q.get('fast', '')
    anchor = re.sub(r'^⚡', '', anchor)
    lines.append('- 锚：**%s**' % anchor[:120])
    lines.append('')

# 分组统计行
lines.append('### 多选（错 %d：错选 %d + 少选 %d）' % (n_multi, wrong_multi, skip_multi))
lines.append('')
lines.append('> 多选明细已并入上方逐条；**错选 9 题全部是"多勾一项归零"**（R6-C/R7-D/R8-E/R10-A/R12-A/R13-D/R24-D/R26-C/P9-D 各多勾一个字母），'
             '再次违反"宁少选不错选"；少选 5 题（R9/R11/R23/R27/P11）合计只拿 6 分、丢了 20 分')
lines.append('')
lines.append('**📌 本章红色警报**：')
lines.append('')
lines.append('1. **数字题 7 题全灭**：R2（理财门槛 1000 万/300 万/40 万）、R3（充足率 5/6/8）、R10（集中度 15/10/50）、R12（租赁 50/30/100）、R14（成本收入比 45%）、P6（LCR 100% vs 流动性比例 25%）、P11（杠杆率 4%）——数字钉一个没钉住')
lines.append('2. **资本三层全线失守**：R17/R22/P7/P8 四题错的全是"哪层装什么"——核心一级=股+留存收益、其他一级=优先股/永续债、二级=二级资本债/超额拨备、扣减项=商誉+无形+递延税')
lines.append('3. **归类题靠感觉**：R1（法定→央行/超额→商行）、R20/P9（存款=负债、贷款=资产）、P3（保函/信用证/承诺→表外）——"三桶归类"没建立')
lines.append('')
lines.append('---')
lines.append('')

# 插入到错题本.md 头部（最近更新行之后第一个 --- 之后）
P = 'exams/错题本/错题本.md'
s = io.open(P, encoding='utf-8').read()
s = s.replace('> 最近更新：2026-11-01（金融02章·即时判题训练卷①判卷）',
              '> 最近更新：2026-11-02（金融03章·即时判题训练卷①判卷）')
anchor = '---\n\n# 金融02章'
assert anchor in s
new_sec = '---\n\n' + '\n'.join(lines) + '\n# 金融02章'
s = s.replace(anchor, new_sec, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('已写入 %d 条错题（单选 %d + 多选 %d）' % (len(ERR_LABELS), n_single, n_multi))
print('病因码分布:', {c: sum(1 for lb in ERR_LABELS if cause(lb)[0] == c) for c in ['E1','E2','E3','E4','E5']})
