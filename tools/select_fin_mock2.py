# -*- coding: utf-8 -*-
"""第二套选题：真题池中第一套未用的全部题目 -> _fin_selected2.json
排序：单选在前（按章 01→12），多选在后；题号 1..103 单选，104..118 多选。
"""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, '..', 'exams', '模考卷')

pool = json.load(io.open(os.path.join(OUT_DIR, '_fin_pool.json'), encoding='utf-8'))
sel1 = json.load(io.open(os.path.join(OUT_DIR, '_fin_selected.json'), encoding='utf-8'))
used = {(q['file'], q['src_no']) for q in sel1}

rest = [q for q in pool if (q['file'], q['src_no']) not in used]
# 剔除材料缺失的残题（原卷即已截断，无法作答）
DROP = {
    ('金融第01章_金融学基础_02.md', 7),   # 复利计算题：本金/利率/期限材料丢失
    ('金融第03章_商业银行_02.md', 7),   # 案例题：净资产/净资本材料丢失
    ('金融第03章_商业银行_03.md', 2),   # 题干（兼并vs收购）与选项（风险加权资产）错位
    ('金融第03章_商业银行_04.md', 4),   # "上述原始存款"材料丢失
    ('金融第06章_金融市场与金融工具_01.md', 6),  # 央行操作材料丢失
    ('金融第07章_金融资产定价_01.md', 9),  # 各股票β数据材料丢失
    ('金融第09章_货币供求与货币均衡_02.md', 4),  # 存款创造参数材料丢失
    ('金融第09章_货币供求与货币均衡_02.md', 9),  # 银行案例材料丢失
}
n_drop = sum(1 for q in rest if (q['file'], q['src_no']) in DROP)
rest = [q for q in rest if (q['file'], q['src_no']) not in DROP]
if n_drop: print('剔除残题 %d 道：%s' % (n_drop, DROP))
singles = sorted([q for q in rest if q['type'] == '单选'], key=lambda q: (q['ch'], q['file'], q['src_no']))
multis  = sorted([q for q in rest if q['type'] == '多选'], key=lambda q: (q['ch'], q['file'], q['src_no']))

out = []
for i, q in enumerate(singles + multis, 1):
    q = dict(q)
    q['no'] = i
    out.append(q)

io.open(os.path.join(OUT_DIR, '_fin_selected2.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))

from collections import Counter
cc = Counter(q['ch'] for q in out)
print('第二套共 %d 题（单 %d / 多 %d）' % (len(out), len(singles), len(multis)))
for ch in sorted(cc):
    name = next(q['chname'] for q in out if q['ch'] == ch)
    print('  %s %s: %d' % (ch, name, cc[ch]))
# 校验：与第一套零重叠
assert not (used & {(q['file'], q['src_no']) for q in out}), '与第一套重叠！'
print('✅ 与第一套零重叠')
