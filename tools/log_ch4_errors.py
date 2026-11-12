# -*- coding: utf-8 -*-
"""把 04 章训练卷①的 11 道错题批量写入 错题本.md 顶部（2026-11-02 下午）"""
import re, io, json

D = json.loads(io.open('tools/_ch4_drill_data.json', encoding='utf-8').read())

MY = {  # 本次作答（来自打印版错题清单）
    'R6': 'BD', 'R7': 'CDE', 'R9': 'A', 'R10': 'ABCE',
    'P1': 'D', 'P5': 'BC', 'P6': 'D', 'P7': 'ACDE',
    'P8': 'C', 'P9': 'CD', 'P11': 'ACE',
}
RES = {k: ('少选' if set(MY[k]) < set(D[k]['ans']) else '错误') for k in MY}

# 病因码：R9/P1/P6/P8 单选概念混淆 E2；R7/R10/P7/P9 多选错选 E4；R6/P5/P11 多选少选 E5
E2 = {'R9', 'P1', 'P6', 'P8'}
E5 = {'R6', 'P5', 'P11'}
def cause(lb):
    if lb in E2: return ('E2', '概念混淆/张冠李戴')
    if lb in E5: return ('E5', '多选漏选')
    return ('E4', '多选错选')

def short(stem, n=40):
    t = re.sub(r'\s', '', stem)
    return t[:n] + ('…' if len(t) > n else '')

L = []
L.append('# 金融04章 保险公司 · 即时判题训练卷①（错题回炉10 + 自命题11，2026-11-02）')
L.append('')
L.append('> 首测 **13.5/28（48%）**，合格线 17 —— **未过线，差 3.5 分**｜状态：🟠 回升未达标（03 章 24% → 04 章 48%）')
L.append('> 分节：错题回炉 **7/13（54%）** 🟡（比 03 章 19% 明显回升）｜自命题 **6.5/15（43%）** 🔴（新考点仍无长记忆）')
L.append('> 结构：全对 10｜**少选 3**｜**错误 8**｜未答 0')
L.append('> ⚠️ 病灶延续 E4：4 道多选错选**全部是多勾一项归零**（R7-D/R10-C/P7-D/P9-D）；E5 少选 3 题（漏 A 委托人/漏 A 成数/漏 B 被保险人定义）——**"宁少选不错选"与"逐项落笔√×"两条纪律仍没执行**')
L.append('> 📌 三个二次坑（都是错题回炉部分）：R7 保险资金运用**同题二错**（上次 D 房地产开发、这次 D 发放信用贷款——两次都栽在"什么不能投"）；R9 保险人识别**同题二错**（上次 A、这次仍 A——甲是投保人！）；R10 财富管理信托**两次错不同项**（上次 ABCDE、这次 ABCE——慈善信托 C 混进来）')
L.append('')
L.append('### 逐条（11 题）')
L.append('')
for lb in MY:
    q = D[lb]
    code, cname = cause(lb)
    kp = q.get('kp', '').replace('第4章:', '') or '保险公司'
    extra = ''
    if RES[lb] == '少选':
        extra = ' · 少选得 %.1f' % (0.5 * len([c for c in MY[lb] if c in q['ans']]))
    tag = ' · 同题二错' if lb in ('R7', 'R9', 'R10') else ''
    L.append('**❌ %s（%s·%s %s%s%s）** %s → 用户 **%s**，正解 **%s**'
             % (lb, kp, cname, code, tag, extra, short(q['stem']), MY[lb], q['ans']))
    L.append('- 原题选项：%s' % '｜'.join('%s %s' % (o['k'], o['t'][:30]) for o in q['opts']))
    if q.get('traps'):
        L.append('- 错因点：%s' % q['traps'][0])
    L.append('- 锚：**%s**' % re.sub(r'^⚡', '', q.get('fast', ''))[:110])
    L.append('')
L.append('### 多选病灶速览')
L.append('')
L.append('> 错选 4 题（各多勾一项归零）：R7 多勾 **D 发放信用贷款**（放贷是银行专营）｜R10 多勾 **C 慈善信托**（公益不属财富管理服务信托）｜P7 多勾 **D 投资股票**（允许项被当成禁止）｜P9 多勾 **D 可清偿受托人债务**（独立性恰恰相反——这句是**反着说的正确表述**，最典型的方向陷阱）')
L.append('> 少选 3 题：R6 漏 **A 委托人**｜P5 漏 **A 成数按固定比例**｜P11 漏 **B 被保险人定义**')
L.append('')
L.append('---')
L.append('')

P = 'exams/错题本/错题本.md'
s = io.open(P, encoding='utf-8').read()
s = s.replace('> 最近更新：2026-11-02（金融03章·即时判题训练卷①判卷）',
              '> 最近更新：2026-11-02（金融04章·即时判题训练卷①判卷）')
anchor = '---\n\n# 金融03章'
assert anchor in s
s = s.replace(anchor, '---\n\n' + '\n'.join(L) + '\n# 金融03章', 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('已写入 11 条；病因:', {'E2': len(E2), 'E4': 4, 'E5': len(E5)})
