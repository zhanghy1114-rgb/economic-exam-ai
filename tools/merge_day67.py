# -*- coding: utf-8 -*-
"""
把 Day6 / Day7 两份《知识点·详细版》合并成《金融·考前终极一本通》的错题层。

规则：
1. 按「知识点归属」里的章号排序（章号 == 所属章节号，零例外）
2. 同考点组按 MERGE_MAP 合并（保留双方全解，错因分别标注来源）
3. 统一重编号 F-01…F-nn
4. 输出带骨架占位 <!--SKEL:NN--> 的中间文件，供手工补每章必考骨架
"""
import re, os, json, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, 'exams', '错题本')
SRC = [('D6', os.path.join(BANK, 'Day6_知识点_详细版.md')),
       ('D7', os.path.join(BANK, 'Day7_知识点_详细版.md'))]

CHAP_NAME = {
    1: '金融学基础', 2: '金融体系', 3: '商业银行', 4: '保险公司',
    5: '证券公司与基金管理公司', 6: '金融市场与金融工具', 7: '金融资产定价',
    8: '公司治理与风险管理', 9: '货币供求与货币均衡', 10: '开放经济均衡',
    11: '中央银行与金融调控', 12: '金融监管',
}

# 同考点合并组（list of tuple），第一个为主条（保留其标题做主标题）
MERGE_MAP = [
    ('D6-06', 'D7-38'),   # 利率期限结构三理论 + 预期理论三推论
    ('D6-08', 'D7-49'),   # 国际金本位制 + 金本位 vs 布雷顿森林
    ('D6-16', 'D7-27'),   # 私募合格投资者门槛 1000万 + 私募资管三数字钉
    ('D6-28', 'D7-19'),   # 信托财产
    ('D6-29', 'D7-20'),   # 保险合同主体
    ('D6-64', 'D7-54'),   # SDR
    ('D6-65', 'D7-57'),   # 央行资产负债表
    ('D6-69', 'D7-56', 'D7-60'),  # 央行职能
]

# 归属章纠正（原文件归类与 2026 章目不符的，按教材实际归属改）
CHAP_FIX = {
    'D7-22': 6,   # 在岸/离岸/国际金融市场 → 第6章金融市场
    'D6-53': 9,   # 货币乘数 → 第9章
    'D6-56': 9,   # 现金漏损率 → 第9章
    'D6-54': 9,   # 凯恩斯货币需求三动机 → 第9章
    'D6-18': 9,   # 流动性陷阱 → 第9章
    'D6-59': 10,  # 国际储备 → 第10章
    'D6-61': 10,  # 外债 → 第10章
    'D6-62': 10,  # 外债种类 → 第10章
    'D6-60': 10,  # BP 曲线 → 第10章
    'D6-09': 10,  # 国际货币体系核心内容 → 第10章
    'D7-38': 1,   # 利率期限结构 → 第1章（大纲归金融学基础）
    'D7-45': 9,   # 弗里德曼货币需求函数 → 第9章
    'D7-42': 9,   # 货币层次 → 第9章
    'D7-44': 9,   # M3 → 第9章
    'D7-43': 9,   # 通胀成因 → 第9章
    'D7-46': 9,   # 基础货币渠道 → 第9章
    'D6-55': 9,   # 通胀分级 → 第9章
    'D6-57': 9,   # 供给学派治理通胀 → 第9章
    'D6-58': 11,  # 央行抗通胀三招 → 第11章
    'D7-01': 9,   # IS-LM → 第9章（大纲：IS-LM 只在金融第9章）
    'D6-09': 1,   # 国际货币体系演变 → 第1章
    'D7-47': 1,   # 汇率制度分类 → 第1章（大纲：理解汇率制度的基本内容与类别）
    'D7-22': 6,
    'D6-04': 10,  # 国际收支影响因素 → 第10章
    'D6-05': 1,   # 汇率分类 → 第1章
    'D7-47': 10,  # 汇率制度弹性 → 第10章
    'D7-48': 1,   # 购买力平价 → 第1章（汇率决定理论）
    'D6-63': 6,   # 股票按投资主体分类 → 第6章
    'D7-31': 6,   # 融资租赁功能 → 第6章
    'D7-32': 6,   # 兼并与收购 → 第6章
    'D6-21': 5,   # 投资银行 → 第5章
}


def split_blocks(path, tag):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    # 从头部的 "# 第X部分" 之前截断无关头部
    lines = text.split('\n')
    blocks = {}
    cur = None
    buf = []
    for ln in lines:
        m = re.match(r'^## (%s-\d{2})\s+(.*)$' % tag, ln)
        if m:
            if cur:
                blocks[cur] = '\n'.join(buf).rstrip()
            cur = m.group(1)
            title = m.group(2).strip()
            buf = ['## %s　%s' % (cur, title)]
        elif cur:
            # 遇到文件级分隔（--- 后接 # 第X部分）或收账块，结束
            if re.match(r'^# 第.+部分 · 第', ln) or re.match(r'^## 本卷收账', ln):
                blocks[cur] = '\n'.join(buf).rstrip()
                cur = None
                buf = []
                continue
            buf.append(ln)
    if cur:
        blocks[cur] = '\n'.join(buf).rstrip()
    return blocks


def parse_block(b):
    """返回 dict: title, chap, belong, body(dict of 五段)"""
    lines = b.split('\n')
    title = lines[0].lstrip('# ').strip()
    title = re.sub(r'^(D[67]-\d{2})[　\s]*', '', title)
    chap = None
    m = re.search(r'第\s*(\d{1,2})\s*章', b)
    if m:
        chap = int(m.group(1))
    belong = ''
    m2 = re.search(r'\*\*知识点归属\*\*[：:]\s*(.+)', b)
    if m2:
        belong = m2.group(1).strip()
    return {'title': title, 'chap': chap, 'belong': belong, 'raw': b}


def main():
    items = {}
    for tag, path in SRC:
        for k, v in split_blocks(path, tag).items():
            d = parse_block(v)
            d['id'] = k
            items[k] = d

    # 应用章纠正
    for k, c in CHAP_FIX.items():
        if k in items:
            items[k]['chap'] = c
            items[k]['belong'] = re.sub(r'第\s*\d{1,2}\s*章', '第 %02d 章' % c, items[k]['belong'])
            items[k]['raw'] = re.sub(r'(\*\*知识点归属\*\*[：:]\s*第\s*)\d{1,2}(\s*章)',
                                     lambda m: m.group(1) + '%02d' % c + m.group(2), items[k]['raw'])

    missing = [k for k, v in items.items() if v['chap'] is None]
    if missing:
        print('!! 无章号:', missing)

    # 合并
    merged_groups = []
    used = set()
    for grp in MERGE_MAP:
        g = [x for x in grp if x in items]
        if len(g) < 2:
            continue
        used.update(g)
        merged_groups.append(g)
    singles = [[k] for k in items if k not in used]

    groups = merged_groups + singles
    # 排序：章号 → 组内首个原编号
    def gsort(g):
        ch = min(items[x]['chap'] for x in g)
        return (ch, min(items[x]['id'] for x in g))
    # 合并组章号统一取主条（第一个）的章号
    groups.sort(key=gsort)

    # 章号冲突检查：合并组内章号不同时，采用主条章号
    out = []
    idx = 0
    for g in groups:
        idx += 1
        fid = 'F-%02d' % idx
        main_id = g[0]
        chap = items[main_id]['chap']
        if len(g) > 1:
            sub = ' / '.join(items[x]['title'] for x in g)
            title = sub
        else:
            title = items[main_id]['title']
        out.append({'fid': fid, 'chap': chap, 'title': title, 'src': g})

    # 重排编号（须先按章排序后再编号，否则章内编号不连续）
    # groups 已按章排序，直接顺序编号即可
    return items, out


if __name__ == '__main__':
    items, out = main()
    print('总条数(合并后):', len(out))
    from collections import Counter
    c = Counter(x['chap'] for x in out)
    for i in range(1, 13):
        ids = [x['fid'] for x in out if x['chap'] == i]
        print('第%02d章 %-14s %2d条  %s' % (i, CHAP_NAME[i], len(ids), (ids[0] + '～' + ids[-1]) if ids else '-'))
    print('--- 合并组 ---')
    for x in out:
        if len(x['src']) > 1:
            print(x['fid'], x['src'], '|', x['title'][:60])
    json.dump({'items': {k: {'chap': v['chap'], 'title': v['title'], 'raw': v['raw']} for k, v in items.items()},
               'out': out},
              open(os.path.join(BASE, 'tools', '_merge67.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
