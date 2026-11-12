# -*- coding: utf-8 -*-
"""组装单文件 HTML 模考卷。
用法: python build_html.py [套号]   默认 1
  套1: _fin_selected.json  -> 金融专业真题模考卷（第一套）.html   ana/ 解析
  套2: _fin_selected2.json -> 金融专业真题模考卷（第二套）.html   ana2/ 解析
"""
import io, os, json, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT_DIR = os.path.join(ROOT, 'exams', '模考卷')

sys.path.insert(0, HERE)
from parse_ana import load_all as load_ana

SET_NO = int(sys.argv[1]) if len(sys.argv) > 1 else 1

if SET_NO == 1:
    SEL   = os.path.join(OUT_DIR, '_fin_selected.json')
    OUT   = os.path.join(OUT_DIR, '金融专业真题模考卷（第一套）.html')
    ANA   = os.path.join(HERE, 'ana')
    PAPER = '第一套'
    KEY   = 'fin_mock_paper_1_v1'
    CFG = {
        'totalMin': 90, 'pass': 84, 'nSingle': 70, 'nMulti': 35, 'full': 140,
        'note': '《金融专业知识和实务》105 题 / 90 分钟 / 140 分，合格线 84 分。本卷结构与实考完全一致 —— 若超时未完成，说明"识别考点"还没形成条件反射，优先补秒杀口诀而非刷新题。',
    }
    INTRO_EXTRA = ('<li><b>答案键校正</b>：第 2、3、9、71、72、87 题原卷答案键与教材/法规口径不符，'
                   '已校正并在该题解析中标注 ⚠ 依据；第 79、93 题存在争议项，已标注提示。</li>')
else:
    SEL   = os.path.join(OUT_DIR, '_fin_selected2.json')
    OUT   = os.path.join(OUT_DIR, '金融专业真题模考卷（第二套）.html')
    ANA   = os.path.join(HERE, 'ana2')
    PAPER = '第二套'
    KEY   = 'fin_mock_paper_2_v1'
    CFG = {
        'totalMin': 95, 'pass': 75, 'nSingle': 95, 'nMulti': 15, 'full': 125,
        'note': '实考为 105 题 / 90 分钟 / 140 分。本卷是真题池<b>剩余题</b>的全量组卷（110 题 / 125 分），'
                '题量与实考相当、多选占比低于实考（真题池多选已用尽），用于<b>榨干剩余真题</b>；'
                '按 95 分钟配速，合格线 75 分（60% 口径）。',
    }
    INTRO_EXTRA = ('<li><b>与第一套的关系</b>：本卷全部题目均为第一套<b>未使用</b>的真题（95 单选 + 15 多选），'
                   '两套合计覆盖金融真题池 100%。多选仅 15 题（真题池多选已用尽），属正常现象。</li>')

TPL = os.path.join(HERE, 'template.html')

def load_patches():
    p = os.path.join(ANA, 'patches.md' if SET_NO == 1 else 'patches2.md')
    if not os.path.exists(p): return {}
    txt = io.open(p, encoding='utf-8').read()
    cur, d = None, {}
    for line in txt.split('\n'):
        m = re.match(r'^###\s+(\d+)\s*$', line)
        if m:
            cur = int(m.group(1)); d[cur] = {}; continue
        if cur is None: continue
        m = re.match(r'^([a-zA-Z]+):\s*(.*)$', line)
        if m and not line.startswith('#'):
            d[cur][m.group(1)] = m.group(2).strip()
    return d

def main():
    qs = json.load(io.open(SEL, encoding='utf-8'))
    ana = load_ana(ANA)
    PATCH = load_patches()

    out = []
    for q in qs:
        no = q['no']
        p = PATCH.get(no, {})
        stem = p.get('stem', q['stem'])
        opts = [{'k': k, 't': p.get('opt' + k, t)} for k, t in q['opts']]
        ans = p.get('ans', q['ans'])
        item = {
            'no': no,
            'sec': 'single' if q['type'] == '单选' else 'multi',
            'type': q['type'],
            'ch': q['ch'],
            'chname': q['chname'],
            'src': q.get('src', ''),
            'stem': stem,
            'opts': opts,
            'ans': ans,
            'ana': ana.get(no, {}),
        }
        out.append(item)

    miss = [q['no'] for q in out if not q['ana'].get('analysis')]
    if miss:
        print('⚠ 缺解析题号：', miss)
    for q in out:
        keys = set(o['k'] for o in q['opts'])
        if not set(q['ans']) <= keys:
            print('❌ 答案越界：', q['no'], q['ans'], sorted(keys))
        need = 4 if q['type'] == '单选' else 5
        if len(q['opts']) != need:
            print('❌ 选项数异常：', q['no'], len(q['opts']), '/', need)

    data = {'qs': out}
    tpl = io.open(TPL, encoding='utf-8').read()
    js = json.dumps(data, ensure_ascii=False)
    assert '/*__DATA__*/' in tpl and '/*__CFG__*/' in tpl
    html = tpl.replace('/*__DATA__*/', js)
    html = html.replace('/*__CFG__*/', json.dumps(CFG, ensure_ascii=False))
    html = html.replace('__PAPER_NO__', PAPER)
    html = html.replace('__KEY__', KEY)
    html = html.replace('__INTRO_EXTRA__', INTRO_EXTRA)
    assert '__' + 'PAPER_NO' + '__' not in html and '__INTRO_EXTRA__' not in html
    io.open(OUT, 'w', encoding='utf-8').write(html)
    n_s = sum(1 for q in out if q['type'] == '单选')
    n_m = sum(1 for q in out if q['type'] == '多选')
    print('第%d套 题数：单选 %d + 多选 %d = %d' % (SET_NO, n_s, n_m, len(out)))
    print('解析覆盖：%d / %d' % (len(out) - len(miss), len(out)))
    print('输出：%s（%.1f KB）' % (OUT, os.path.getsize(OUT) / 1024.0))

if __name__ == '__main__':
    main()
