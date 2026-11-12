# -*- coding: utf-8 -*-
"""从金融真题池按章配额选题，组成 105 题全真模考卷（单选70 + 多选35 = 140分）"""
import io, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, '..', 'exams', '模考卷', '_fin_pool.json')
OUT = os.path.join(HERE, '..', 'exams', '模考卷', '_fin_selected.json')

# 章 -> (单选配额, 多选配额)
QUOTA = {
    '金融第01章': (8, 5),
    '金融第02章': (5, 1),
    '金融第03章': (10, 8),
    '金融第04章': (5, 2),
    '金融第05章': (8, 3),
    '金融第06章': (6, 3),
    '金融第07章': (5, 2),
    '金融第08章': (3, 0),
    '金融第09章': (7, 3),
    '金融第10章': (5, 4),
    '金融第11章': (7, 3),
    '金融第12章': (1, 1),
}

# 案例材料缺失题（真题抽取时材料段丢失，无法作答）—— 剔除出候选池
EXCLUDE = ['老张的朋友', '最不可以成为信托受益人']

def norm(s):
    return re.sub(r'[\s（），()、。．,．]+', '', s)[:46]

def pick(items, n):
    """均匀采样 n 个，保持原顺序"""
    if n >= len(items): return list(items)
    step = len(items) / float(n)
    idx = sorted(set(min(len(items)-1, int(i*step)) for i in range(n)))
    # 不足则补齐
    i = 0
    while len(idx) < n and i < len(items):
        if i not in idx: idx.append(i)
        i += 1
    idx = sorted(idx)[:n]
    return [items[i] for i in idx]

def main():
    pool = json.load(io.open(POOL, encoding='utf-8'))
    # 去重
    seen, uniq, drop = set(), [], 0
    for q in pool:
        k = norm(q['stem'])
        if k in seen: continue
        seen.add(k)
        if any(x in q['stem'] for x in EXCLUDE):
            drop += 1; continue
        uniq.append(q)
    print('去重后 %d（原 %d）｜剔除材料缺失题 %d' % (len(uniq), len(pool), drop))

    single, multi = [], []
    for ch, (ns, nm) in QUOTA.items():
        for t, quota, bucket in (('单选', ns, single), ('多选', nm, multi)):
            cands = [q for q in uniq if q['ch'] == ch and q['type'] == t]
            got = pick(cands, quota)
            if len(got) < quota:
                print('  ⚠ %s %s 需%d 实得%d' % (ch, t, quota, len(got)))
            bucket.extend(got)

    print('单选 %d（目标70）｜多选 %d（目标35）' % (len(single), len(multi)))
    # 编号：单选 1-70，多选 71-105
    for i, q in enumerate(single): q['no'] = i + 1
    for i, q in enumerate(multi): q['no'] = len(single) + i + 1
    allq = single + multi
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(allq, ensure_ascii=False, indent=1))
    print('已写 %s（%d 题）' % (OUT, len(allq)))

if __name__ == '__main__':
    main()
