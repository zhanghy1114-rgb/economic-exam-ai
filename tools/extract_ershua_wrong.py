# -*- coding: utf-8 -*-
"""从二刷卷判卷结果 PDF 的 OCR 文本提取错题清单。

输入：C:/Users/86151/AppData/Local/Temp/wbpdf_ocr/pgNNN.txt（Windows OCR）
输出：tmp2/ershua_wrong.json  [{"label","type","ans","you","score","page"}]
      tmp2/ershua_report.txt  对账报告
"""
import io, os, re, json, glob

OCR_DIR = r'C:\Users\86151\AppData\Local\Temp\wbpdf_ocr'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp2')
HTML = os.path.join(OUT, '..')  # unused placeholder

def parse_pages():
    recs = []
    chap = None
    headers = []
    for f in sorted(glob.glob(os.path.join(OCR_DIR, 'pg*.txt'))):
        pg = int(re.search(r'pg(\d+)', f).group(1))
        t = io.open(f, encoding='utf-8-sig').read()
        tc = re.sub(r'\s+', '', t)  # 去掉 OCR 空格便于匹配
        # 章头页：第 0 1 章 ... （ 二 刷 N 道 ）
        mh = re.search(r'第(\d{1,2})章[^\n]*?（二刷(\d+)道）', tc)
        if mh:
            chap = mh.group(1).zfill(2)
            headers.append({'page': pg, 'chap': chap, 'n': int(mh.group(2))})
        # 结果行：正解BCE（多选，共3项）你答ACE本题0分
        for m in re.finditer(r'正解([A-E]{1,5})(?:（(单选|多选)[^）]*）)?你答([A-E]{0,5}|未答|未作答)本题(\d+)分', tc):
            recs.append({'page': pg, 'chap': chap, 'ans': m.group(1),
                         'you': m.group(3) if m.group(3) else '',
                         'score': int(m.group(4))})
        # label 行：0 3 一 R 1 0 多 选 → 去空格后 03-R10
        lab = None
        ml = re.search(r'(\d{2})[-一—]R(\d{1,2})', tc)
        if ml:
            lab = '%s-R%s' % (ml.group(1), ml.group(2))
        if recs and recs[-1]['page'] == pg and 'label' not in recs[-1]:
            recs[-1]['label'] = lab
        # 题型兜底
        if recs and recs[-1]['page'] == pg and 'type' not in recs[-1]:
            mt = re.search(r'(单选|多选)', tc)
            recs[-1]['type'] = mt.group(1) if mt else None
    return recs, headers


def main():
    recs, headers = parse_pages()
    # 加载二刷卷 HTML DATA
    hp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exams', '模考卷', '金融全科·错题二刷卷.html')
    htxt = io.open(hp, encoding='utf-8').read()
    m = re.search(r'const DATA = (\{.*?\});\s*\n', htxt, re.S)
    data = json.loads(m.group(1))
    qmap = {q['label']: q for q in data['qs']}

    rep = []
    rep.append('OCR 记录 %d 条；章头 %d 个；HTML 题库 %d 题' % (len(recs), len(headers), len(qmap)))
    # 对账
    ok, bad, missing = [], [], []
    for r in recs:
        lab = r.get('label')
        if not lab or lab not in qmap:
            missing.append(r)
            continue
        q = qmap[lab]
        r['type'] = r.get('type') or q['type']
        if r['ans'] == q['ans']:
            ok.append(r)
        else:
            bad.append((lab, r['ans'], q['ans']))
    rep.append('label 命中 %d，未命中 %d，正解不一致 %d' % (len(ok), len(missing), len(bad)))
    for b in bad:
        rep.append('  不一致: %s OCR=%s HTML=%s' % b)
    for r in missing:
        rep.append('  未命中: page=%s chap=%s ans=%s you=%s label=%s' % (r['page'], r['chap'], r['ans'], r['you'], r.get('label')))

    # 章头数 vs 实际记录数
    rep.append('')
    rep.append('章头 vs 记录：')
    from collections import Counter
    cnt = Counter(r['chap'] for r in recs if r.get('chap'))
    for h in headers:
        rep.append('  第%s章 头=%d 实测=%d' % (h['chap'], h['n'], cnt.get(h['chap'], 0)))

    # 错题：you 集合 != ans 集合
    wrong = []
    for r in recs:
        lab = r.get('label')
        if not lab or lab not in qmap:
            rep.append('  ⚠ 无法判错(缺label): page=%s ans=%s you=%s' % (r['page'], r['ans'], r['you']))
            continue
        you_set = set(r['you']) if r['you'] else set()
        ans_set = set(r['ans'])
        if you_set != ans_set:
            wrong.append({'label': lab, 'type': qmap[lab]['type'], 'ans': r['ans'],
                          'you': r['you'], 'score': r['score'], 'page': r['page']})
    rep.append('')
    rep.append('二刷仍错 %d 道：' % len(wrong))
    from collections import defaultdict
    bych = defaultdict(list)
    for w in wrong:
        bych[w['label'][:2]].append(w)
    for ch in sorted(bych):
        ws = sorted(bych[ch], key=lambda x: int(x['label'].split('R')[1]))
        rep.append('  第%s章 %d 道: %s' % (ch, len(ws), ' '.join('%s(你%s/正%s)' % (w['label'], w['you'] or '无', w['ans']) for w in ws)))

    json.dump(wrong, io.open(os.path.join(OUT, 'ershua_wrong.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    io.open(os.path.join(OUT, 'ershua_report.txt'), 'w', encoding='utf-8').write('\n'.join(rep))
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
