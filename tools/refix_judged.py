# -*- coding: utf-8 -*-
"""用 HTML 内【校正后】的答案键重算两套模考的判卷结果。

背景：_fin_selected*.json 里存的是原卷答案键，其中部分题与教材口径不符，
第一套 HTML 已做过校正（并在解析里标注 ⚠ 依据）。但 _paper*_judged.json
当时是用原始键判的，导致历史得分与错题集有偏差。本脚本就地修正，先备份。
"""
import io, os, json, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'exams', '模考卷')

SETS = [
    ('1', '金融专业真题模考卷（第一套）.html', '_paper1_judged.json'),
    ('2', '金融专业真题模考卷（第二套）.html', '_paper2_judged.json'),
]


def score_of(q, my):
    if not my:
        return 0, '空'
    if q['type'] == '单选':
        return (1, '✓') if my == q['ans'] else (0, '✗')
    A = set(q['ans'])
    S = set(my)
    if S - A:
        return 0, '✗'
    if S == A:
        return 2, '✓'
    return 0.5 * len(S & A), '△'


def main():
    for tag, hf, jf in SETS:
        hp, jp = os.path.join(OUT, hf), os.path.join(OUT, jf)
        txt = io.open(hp, encoding='utf-8').read()
        data = json.loads(re.search(r'const DATA = (.*?);\nconst TOTAL_TIME', txt, re.S).group(1))
        jg = json.load(io.open(jp, encoding='utf-8'))

        bak = jp.replace('.json', '_原始键备份.json')
        if not os.path.exists(bak):
            shutil.copy2(jp, bak)

        chg, tot_old, tot_new = [], 0, 0
        for q in data['qs']:
            no = str(q['no'])
            old = jg.get(no)
            if not old:
                continue
            sc, mk = score_of(q, old.get('my', ''))
            tot_old += old.get('sc', 0)
            tot_new += sc
            if old.get('sc') != sc or old.get('mark') != mk:
                chg.append((no, q['ch'], old.get('my'), old.get('ans'), q['ans'],
                            old.get('sc'), sc, old.get('mark'), mk))
            jg[no] = {'my': old.get('my', ''), 'ans': q['ans'], 'sc': sc, 'mark': mk,
                      'type': q['type'], 'ch': q['ch']}
        json.dump(jg, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

        print('=' * 74)
        print('第%s套  %s' % (tag, hf))
        print('  总分：%.1f → %.1f' % (tot_old, tot_new))
        print('  变动题：%d 道' % len(chg))
        for c in chg:
            print('    Q%-4s %-10s 你答%-6s 旧键%-6s→新键%-6s 分 %s→%s  %s→%s'
                  % (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8]))


if __name__ == '__main__':
    main()
