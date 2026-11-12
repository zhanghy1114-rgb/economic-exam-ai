# -*- coding: utf-8 -*-
"""把两套 HTML 里【校正后】的答案键同步回真题分章卷 md 的答案速查表。

原卷答案键有 11 道题与教材口径不符，已在 HTML 中校正（解析里标了 ⚠ 依据），
但 exams/真题分章卷/*.md 的答案速查表仍是原卷键，按章刷题时会被误导。
本脚本：改答案单元格为校正值（加 * 号），并在该卷末尾附校正脚注（保留原值）。
"""
import io, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'exams', '模考卷')
BANK = os.path.join(ROOT, 'exams', '真题分章卷')

PAIRS = [
    ('金融专业真题模考卷（第一套）.html', '_fin_selected.json'),
    ('金融专业真题模考卷（第二套）.html', '_fin_selected2.json'),
]


def html_qs(p):
    s = io.open(os.path.join(OUT, p), encoding='utf-8').read()
    return json.loads(re.search(r'const DATA = (.*?);\nconst TOTAL_TIME', s, re.S).group(1))['qs']


def collect():
    """返回 {md文件名: [(卷内题号, 原键, 新键, 章, 题干)]}"""
    d = {}
    for hf, sf in PAIRS:
        hq = {q['no']: q for q in html_qs(hf)}
        for q in json.load(io.open(os.path.join(OUT, sf), encoding='utf-8')):
            h = hq.get(q['no'])
            if not h or h['ans'] == q['ans']:
                continue
            src_no = q.get('src_no') or q['no']
            d.setdefault(q['file'], []).append((src_no, q['ans'], h['ans'], q['ch'], h['stem']))
    return d


def main():
    todo = collect()
    total = 0
    for fn, items in sorted(todo.items()):
        path = os.path.join(BANK, fn)
        if not os.path.exists(path):
            print('⚠ 找不到', fn)
            continue
        txt = io.open(path, encoding='utf-8').read()
        lines = txt.split('\n')
        hit = 0
        for i, ln in enumerate(lines):
            if not ln.startswith('| 答案'):
                continue
            cells = ln.split('|')
            for src_no, old, new, ch, stem in items:
                idx = src_no + 1          # cells[1] 是"答案"标签，第 1 题在 cells[2]
                if idx >= len(cells):
                    print('   ⚠ 越界', fn, src_no)
                    continue
                if cells[idx].strip().rstrip('*').strip() == new:
                    continue              # 已校正过
                cells[idx] = ' ' + new + '* '
                hit += 1
            lines[i] = '|'.join(cells)
            break
        if not hit:
            print('   （无改动）', fn)
            continue
        # 追加校正脚注
        note = ['', '> ⚠ **答案键校正**（依据教材口径，原卷键与教材不符）：']
        for src_no, old, new, ch, stem in items:
            note.append('> - 第 %d 题：**%s → %s**（原卷键 %s）　%s' % (src_no, old, new, old, stem[:36]))
        if '答案键校正' in txt:
            lines = [l for l in lines]    # 已有脚注则只更新表
        else:
            lines = lines[:] + note
        io.open(path, 'w', encoding='utf-8').write('\n'.join(lines))
        print('✅ %s　校正 %d 处' % (fn, hit))
        total += hit
    print('\n合计校正 %d 处' % total)


if __name__ == '__main__':
    main()
