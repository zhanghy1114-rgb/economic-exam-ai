# -*- coding: utf-8 -*-
"""解析金融真题分章卷 -> 题目池 JSON（供模考卷 HTML 使用）"""
import io, re, glob, os, json, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exams', '真题分章卷')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exams', '模考卷', '_fin_pool.json')

def parse_file(path):
    s = io.open(path, encoding='utf-8').read()
    title = s.split('\n')[0].lstrip('# ').strip()
    m = re.match(r'(金融第\d+章)\s*(.+?)\s*·', title)
    ch = m.group(1) if m else ''
    chname = m.group(2).strip() if m else ''
    src = re.search(r'来源：([^｜|]+)', s)
    src = src.group(1).strip() if src else ''
    # 题块
    blocks = re.split(r'\n(?=\*\*\d+\.\*\*)', s)
    qs = []
    for b in blocks:
        mm = re.match(r'\*\*(\d+)\.\*\*（(单选|多选)）(.*?)(?=\n[A-E]\.|\Z)', b, re.S)
        if not mm: continue
        no, qtype, stem = int(mm.group(1)), mm.group(2), mm.group(3).strip()
        stem = re.sub(r'修改答案\s*$', '', stem).strip()   # 清洗 PDF 污染词
        stem = re.sub(r'X{2,}', '', stem).strip()   # 清洗 XXX 占位污染
        stem = re.sub(r'^单选题\((\d+)分\)\s*', '', stem).strip()   # 清洗分值前缀
        opts = re.findall(r'\n([A-E])\.\s*(.*?)(?=\n[A-E]\.\s|\n---|\Z)', b, re.S)
        opts = [(k, v.strip().replace('\n', ' ')) for k, v in opts]
        qs.append({'src_no': no, 'type': qtype, 'stem': stem, 'opts': opts})
    # 答案表
    ans = {}
    m2 = re.search(r'\|\s*答案\s*\|(.+?)\n', s)
    if m2:
        cells = [c.strip() for c in m2.group(1).split('|')]
        cells = [c for c in cells if c != '']
        m3 = re.search(r'\|\s*题\s*\|(.+?)\n', s)
        keys = [c.strip() for c in m3.group(1).split('|') if c.strip() != ''] if m3 else []
        for i, k in enumerate(keys):
            if i < len(cells):
                ans[int(k)] = cells[i]
    for q in qs:
        q['ans'] = ans.get(q['src_no'], '')
        q['ch'] = ch; q['chname'] = chname; q['src'] = src
        q['file'] = os.path.basename(path)
    return qs

def main():
    files = sorted(glob.glob(os.path.join(BASE, '金融*.md')))
    pool = []
    for f in files:
        pool.extend(parse_file(f))
    # 体检
    bad = []
    for q in pool:
        n_opt = len(q['opts'])
        need = 4 if q['type'] == '单选' else 5
        reasons = []
        if n_opt < need: reasons.append('选项%d/%d' % (n_opt, need))
        if not q['ans']: reasons.append('无答案')
        else:
            keys = set(k for k, _ in q['opts'])
            if not set(q['ans']) <= keys: reasons.append('答案越界%s∉%s' % (q['ans'], ''.join(sorted(keys))))
        if re.search(r'。{3,}|…{2,}|\.{4,}', q['stem']): reasons.append('题干残缺')
        if any(x in q['stem'] for x in ('老张', '案例中所提到的', '根据案例中的材料', '最不可以成为信托受益人', '银行以证券自营商和做市商')):
            reasons.append('案例材料缺失')
        if any(re.search(r'。{3,}', t) for _, t in q['opts']): reasons.append('选项残缺')
        if any(re.match(r'^\s*[X]{1,3}\s*$', t) for _, t in q['opts']): reasons.append('选项缺失(占位X)')
        if any(x in q['stem'] for x in ('刘先生', '该银行法定存款准备金率', '控制信托业务风险的核心', '货币流通速度是多少')):
            reasons.append('题干残缺/存疑')
        if len(q['stem']) < 12: reasons.append('题干过短')
        if reasons:
            q['bad'] = reasons
            bad.append(q)
    good = [q for q in pool if 'bad' not in q]
    print('池总 %d｜合格 %d｜问题 %d' % (len(pool), len(good), len(bad)))
    for q in bad:
        print('  ✗ %s Q%d %s | %s' % (q['file'], q['src_no'], '/'.join(q['bad']), q['stem'][:40]))
    from collections import Counter
    c = Counter((q['ch'], q['type']) for q in good)
    print('\n各章合格题量：')
    for ch in sorted(set(q['ch'] for q in good)):
        print('  %s %s  单%d 多%d' % (ch, good[[x['ch'] for x in good].index(ch)]['chname'],
              c[(ch, '单选')], c[(ch, '多选')]))
    print('\n合格合计：单选 %d｜多选 %d' % (c_total := sum(1 for q in good if q['type'] == '单选'),
                                          sum(1 for q in good if q['type'] == '多选')))
    if not os.path.exists(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(good, ensure_ascii=False, indent=1))
    print('\n已写 %s' % OUT)

if __name__ == '__main__':
    main()
