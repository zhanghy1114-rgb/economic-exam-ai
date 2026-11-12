# -*- coding: utf-8 -*-
"""把 05 章训练卷①的 20 道错题批量写入 错题本.md 顶部（2026-11-02 晚）"""
import re, io, json

D = json.loads(io.open('tools/_ch5_drill_data.json', encoding='utf-8').read())

MY = {  # 本次作答（来自打印版错题清单，20/20 与卷内正解核对一致）
    'R1': 'B', 'R2': 'D', 'R3': 'A', 'R4': 'C',
    'R6': 'ABC', 'R7': 'ACE', 'R8': 'ACDE',
    'R9': 'B', 'R10': 'C', 'R11': 'D', 'R12': 'C', 'R13': 'D', 'R14': 'C', 'R17': 'A',
    'R21': 'ABC',
    'P2': 'D', 'P3': 'A', 'P6': 'B', 'P7': 'D', 'P10': 'ABCE',
}
RES = {}
for k, v in MY.items():
    a = D[k]['ans']
    if v == a:
        RES[k] = '错误'
    elif set(v) <= set(a) and len(v) < len(a):
        RES[k] = '少选'
    else:
        RES[k] = '错误'

# 病因码：单选概念/数值混淆 E2×13；选非方向 E3×2（P3、P7）；多选错选 E4×4；多选少选 E5×1
E2 = {'R1', 'R2', 'R3', 'R4', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R17', 'P2', 'P6'}
E3 = {'P3', 'P7'}
E5 = {'R7'}
def cause(lb):
    if lb in E2: return ('E2', '概念/数值混淆')
    if lb in E3: return ('E3', '选非方向丢失')
    if lb in E5: return ('E5', '多选漏选')
    return ('E4', '多选错选')

def short(stem, n=40):
    t = re.sub(r'\s', '', stem)
    return t[:n] + ('…' if len(t) > n else '')

L = []
L.append('# 金融05章 证券公司与基金管理公司 · 即时判题训练卷①（错题回炉21 + 自命题12，2026-11-02）')
L.append('')
L.append('> 首测 **17.5/41（43%）**，合格线 25 —— **未过线，差 7.5 分**｜状态：🔴 连续第二卷未过线')
L.append('> 分节：错题回炉 **7.5/25（30%）** 🔴（比 04 章 54% 大幅回落——05 章错题从没复盘过就裸做）｜自命题 **10/16（63%）** 🟡（新骨架部分及格）')
L.append('> 结构：全对 13｜少选 1｜**错误 19**｜未答 0')
L.append('> ⚠️ 病灶：**多选 5 题错 4**（R6/R8/R21/P10 全是"多勾一项归零"）——E4 已四卷连犯（02章2→03章9→04章4→05章4=19题×2分=38分白丢）；单选错 15 题里 **13 题是"教材写了但没记住"的数字钉与条文**（5% 股东/5% 货币基金/3000万/5人/推介渠道/退出监管）')
L.append('> 📌 两个选非题双杀（P3 托管人准入、P7 职责边界）——都是把**正确表述**当答案选了，选非方向连续丢分')
L.append('> 📌 P2 管理费计算题答 D（30万）正解 A（8.22万）——公式忘了除 365，量级判断也没用上（20亿×1.5%÷365 只能是"几万"级）')
L.append('')
L.append('### 逐条（20 题）')
L.append('')
for lb in MY:
    q = D[lb]
    code, cname = cause(lb)
    kp = q.get('kp', '').replace('第5章·', '') or '证券与基金'
    extra = ''
    if RES[lb] == '少选':
        extra = ' · 少选得 %.1f' % (0.5 * len([c for c in MY[lb] if c in q['ans']]))
    cross = ' · 跨章题（原卷归类05章）' if lb in ('R12', 'R19') else ''
    L.append('**❌ %s（%s·%s %s%s%s）** %s → 用户 **%s**，正解 **%s**'
             % (lb, kp, cname, code, extra, cross, short(q['stem']), MY[lb], q['ans']))
    L.append('- 原题选项：%s' % '｜'.join('%s %s' % (o['k'], o['t'][:30]) for o in q['opts']))
    if q.get('traps'):
        L.append('- 错因点：%s' % q['traps'][0])
    L.append('- 锚：**%s**' % re.sub(r'^⚡', '', q.get('fast', ''))[:110])
    L.append('')
L.append('### 多选病灶速览')
L.append('')
L.append('> 错选 4 题（各多勾一项归零）：R6 多勾 **A 代销**（承销只有代销/包销，A 是利率债销的干扰）｜R8 多勾 **D 独立性当内控原则**（内控四原则=健全合理制衡独立，D 表述变了样）｜R21 多勾 **B 期货公司不在列**（销售机构=银证期保咨独，B 实际在列但混了别的）｜P10 多勾 **E 申购赎回费按日计提**（一次性费用，不按天算）')
L.append('> 少选 1 题：R7 漏 **B 安全保管基金财产 + E 办理信息披露**（托管人职责只记了复核监督两件）')
L.append('')
L.append('---')
L.append('')

P = 'exams/错题本/错题本.md'
s = io.open(P, encoding='utf-8').read()
s = s.replace('> 最近更新：2026-11-02（金融04章·即时判题训练卷①判卷）',
              '> 最近更新：2026-11-02（金融05章·即时判题训练卷①判卷）')
anchor = '---\n\n# 金融04章'
assert anchor in s, '锚点缺失'
s = s.replace(anchor, '---\n\n' + '\n'.join(L) + '\n# 金融04章', 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('已写入 20 条；病因:', {'E2': len(E2), 'E3': len(E3), 'E4': 4, 'E5': len(E5)})
