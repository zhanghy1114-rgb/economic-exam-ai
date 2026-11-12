# -*- coding: utf-8 -*-
"""
渲染《金融专业 · 考前终极一本通》
输入：tools/_merge67.json（由 merge_day67.py 产出）
输出：exams/错题本/金融·考前终极一本通.md
      每章 A 段留 <!--SKEL:NN--> 占位，由手工补写本章必考骨架
"""
import re, os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, 'exams', '错题本')
J = json.load(open(os.path.join(BASE, 'tools', '_merge67.json'), encoding='utf-8'))
items = J['items']
out = J['out']

CHAP_NAME = {
    1: '金融学基础', 2: '金融体系', 3: '商业银行', 4: '保险公司',
    5: '证券公司与基金管理公司', 6: '金融市场与金融工具', 7: '金融资产定价',
    8: '公司治理与风险管理', 9: '货币供求与货币均衡', 10: '开放经济均衡',
    11: '中央银行与金融调控', 12: '金融监管',
}
# 真题池题量（按 exams/真题分章卷 统计）
ZT = {1: 29, 2: 12, 3: 50, 4: 15, 5: 29, 6: 20, 7: 9, 8: 6, 9: 24, 10: 19, 11: 24, 12: 3}

SEG = ['知识点归属', '知识点全解', '考法', '错因', '记忆锚']


def segs(raw):
    """把条目正文切成五段 dict"""
    lines = raw.split('\n')[1:]  # 去掉标题行
    d = {k: [] for k in SEG}
    cur = None
    for ln in lines:
        m = re.match(r'^- \*\*(%s)\*\*[：:]?(.*)$' % '|'.join(SEG), ln)
        if m:
            cur = m.group(1)
            rest = m.group(2).strip()
            if rest:
                d[cur].append(rest)
            continue
        if cur:
            d[cur].append(ln)
    return {k: '\n'.join(v).strip() for k, v in d.items()}


def render(item):
    src = item['src']
    parts = [segs(items[s]['raw']) for s in src]
    if len(src) == 1:
        p = parts[0]
        body = []
        body.append('- **知识点归属**：%s' % p['知识点归属'])
        body.append('- **知识点全解**：%s' % p['知识点全解'])
        body.append('- **考法**：%s' % p['考法'])
        body.append('- **错因**：%s' % p['错因'])
        body.append('- **记忆锚**：%s' % p['记忆锚'])
        head = '## %s　%s' % (item['fid'], items[src[0]]['title'])
        srcnote = '> 题源：%s' % src[0]
    else:
        body = []
        belong = parts[0]['知识点归属']
        body.append('- **知识点归属**：%s' % belong)
        jie = []
        for s, p in zip(src, parts):
            jie.append('**〔%s〕** %s' % (s, p['知识点全解']))
        body.append('- **知识点全解**：' + '\n\n  '.join(jie))
        body.append('- **考法**：' + ' ｜ '.join('〔%s〕%s' % (s, p['考法']) for s, p in zip(src, parts)))
        body.append('- **错因**：' + ' ｜ '.join('〔%s〕%s' % (s, p['错因']) for s, p in zip(src, parts)))
        body.append('- **记忆锚**：' + ' ｜ '.join('〔%s〕%s' % (s, p['记忆锚']) for s, p in zip(src, parts)))
        head = '## %s　%s' % (item['fid'], ' ｜ '.join(items[s]['title'] for s in src))
        srcnote = '> 题源：%s（同考点合并）' % ' + '.join(src)
    return '\n'.join([head, '', srcnote, ''] + body)


def main():
    L = []
    A = L.append
    A('# 金融专业 · 考前终极一本通（Day6 + Day7 合并强化版）')
    A('')
    A('> **覆盖**：2026 金融专业 12 章全章（按知识点归属章排序，章号零例外）')
    A('> **错题层来源**：Day6 第一套模考（105 题 / 错 78）+ Day7 第二套模考（110 题 / 错 65），共 143 道错题，归并为 **125 条**知识点')
    A('> **骨架层来源**：2026 官方考试大纲 + 240 题金融真题池高频 + 教材 2026 新增考点补空')
    A('> **编号**：**F-01～125**，与配套记忆版、秒杀版严格一一对应')
    A('> **生成**：2026-10-30')
    A('')
    A('---')
    A('')
    A('## 0. 这份文件怎么用（先读这 30 秒）')
    A('')
    A('| 场景 | 怎么用 | 时间 |')
    A('|---|---|---|')
    A('| 早读 | 只念**记忆版**（知识行 + ⚡秒杀行），遮住秒杀行自问自答 | 15-20 min |')
    A('| 白天 | 按章读**详细版**的 A 段（必考骨架），F 段只扫错题条 | 30 min/章 |')
    A('| 碎片 | 刷**秒杀版**表格，见题眼出答案 | 随时 |')
    A('| 考前 1 天 | 只读**数字钉总表** + 每章 C 段 | 40 min |')
    A('')
    A('**三遍过法**：第 1 遍按章顺序通读（01→12）；第 2 遍只做 🔴🟠 章；第 3 遍只做 F 段里还答不上来的条。')
    A('')
    A('## 1. 四项铁律（每次开卷前默念一遍）')
    A('')
    A('- **T1 选非只勾 ❌**：圈出「错误的是／不属于／不包括／不可能」，A→E 逐项打 ✅❌，**只勾 ❌**')
    A('- **T2 多选五字母逐个 √×**：A→E 都要落笔，勾完回头再扫一遍 D 和 E；宁少选不错选')
    A('- **T3 绝对化先找反例**：出现「只能／必须／任何／全部／完全／直接」先找反例；只写前半句、没结论的选项是不完整项，不勾')
    A('- **T4 数字与主体单独记**：金融考的是原文数字和数字的主人，推理救不了——见数字先问"谁的数"')
    A('')
    A('## 2. 章节优先级地图（先看这张表再决定读哪一章）')
    A('')
    A('| 章 | 名称 | 真题池 | 你的错题条 | 大纲变动 | 优先级 |')
    A('|---|---|---|---|---|---|')
    PRI = {1: '🟠 中', 2: '🔴 高（教材重写）', 3: '🔴 高（最厚+最弱）', 4: '🟠 中', 5: '🔴 高（最弱）',
           6: '🟠 中', 7: '🔴 高（★★★大改+真题稀）', 8: '🔴 高（真题仅6）', 9: '🔴 高（IS-LM 新增）',
           10: '🔴 高（三元悖论新增）', 11: '🔴 高（双支柱新增）', 12: '🔴 高（真题仅3）'}
    CHG = {1: '无变化', 2: '整章重写·六大体系', 3: '新增经营四原则', 4: '新增承保/理赔/再保险', 5: '内容有增加',
           6: '内容有增加', 7: '★★★ 核心大改', 8: '内容有增加', 9: '★ 新增 IS-LM',
           10: '★ 新增 IS-LM-BP/米德冲突/三元悖论', 11: '★ 新增结构性工具/双支柱', 12: '新增危机演化/巴塞尔'}
    for i in range(1, 13):
        n = len([x for x in out if x['chap'] == i])
        A('| %02d | %s | %d 题 | %d 条 | %s | %s |' % (i, CHAP_NAME[i], ZT[i], n, CHG[i], PRI[i]))
    A('')
    A('**读法**：🔴 章每天至少 1 章，🟠 章隔天 1 章。第 07/08/12 章真题稀薄 = **你没刷过 ≠ 不考**，这三章必须靠 A 段骨架补。')
    A('')
    A('---')
    A('')

    for i in range(1, 13):
        ids = [x for x in out if x['chap'] == i]
        rng = ('%s～%s' % (ids[0]['fid'], ids[-1]['fid'])) if ids else '—'
        A('# 第 %02d 章 %s（%s）' % (i, CHAP_NAME[i], rng))
        A('')
        A('> 真题池 %d 题 ｜ 你的错题 %d 条 ｜ 大纲：%s ｜ 优先级 %s' % (ZT[i], len(ids), CHG[i], PRI[i]))
        A('')
        A('## A. 本章必考骨架（背完这些，本章基础分不丢）')
        A('')
        A('<!--SKEL:%02d-->' % i)
        A('')
        A('## B. 错题知识点（%s）' % rng)
        A('')
        for it in ids:
            A(render(it))
            A('')
            A('---')
            A('')
    A('## 收账：本卷过法')
    A('')
    A('- 读完打钩：A 段骨架 / B 段错题条 / C 段秒杀')
    A('- 次日只回炉：F 段里仍答不上来的条 + 本章 🔴 章')
    A('')
    txt = '\n'.join(L)
    p = os.path.join(BANK, '金融·考前终极一本通.md')
    open(p, 'w', encoding='utf-8').write(txt)
    print('written:', p, len(txt))


if __name__ == '__main__':
    main()
