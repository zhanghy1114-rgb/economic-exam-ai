# -*- coding: utf-8 -*-
"""生成"分章即时判题训练卷"（单文件离线 HTML）。

用法: python build_drill.py 01
  数据源：
    A. 该章在两套模考中<b>答错过的真题</b>（从 _fin_selected*.json + _paper*_judged.json 反查）
       —— 这就是"把错题放进卷子"
    B. tools/props/金融第XX章.json 里的<b>自命题·仿真题</b>（真题做完后只用这类题测水平）
  输出: exams/模考卷/金融第XX章·即时判题训练卷.html
"""
import io, os, json, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT_DIR = os.path.join(ROOT, 'exams', '模考卷')
TPL = os.path.join(HERE, 'template_drill.html')

CH = sys.argv[1] if len(sys.argv) > 1 else '01'
CH_KEY = '金融第%02d章' % int(CH)

def norm_opts(opts):
    """兼容两种选项结构：HTML 用 [{'k','t'}]，selected.json 用 [['A','文本']]"""
    out = []
    for o in opts:
        if isinstance(o, dict):
            out.append({'k': o['k'], 't': o['t']})
        else:
            out.append({'k': o[0], 't': o[1]})
    return out


def li(v):
    """统一把 chain / traps 规范成 list（ana2 里部分题被存成了整段字符串）"""
    if not v:
        return []
    if isinstance(v, list):
        return [x for x in v if x]
    return [x.strip() for x in re.split(r'\n+', str(v)) if x.strip()]


CH_NAME = {
    '01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险公司',
    '05': '证券与基金', '06': '金融市场与工具', '07': '金融资产定价', '08': '公司治理与风险',
    '09': '货币供求', '10': '开放经济均衡', '11': '中央银行与调控', '12': '金融监管',
}

# ⚠ 数据源必须是【两套 HTML 内校正后的 DATA】，绝不能直接用 _fin_selected*.json：
#   后者存的是原卷答案键，第一套有 4 题（Q2/Q3/Q71/Q72）与教材口径不符，已在 HTML 里校正
#   （并在解析中标了 ⚠ 依据）。HTML 的 stem 也修过残缺（如 Q71 "..利率决定理论"）。
SETS = [
    ('1', '金融专业真题模考卷（第一套）.html', '_paper1_judged.json'),
    ('2', '金融专业真题模考卷（第二套）.html', '_paper2_judged.json'),
]


def html_qs(path):
    """从单文件 HTML 里取出校正后的题目数据"""
    txt = io.open(path, encoding='utf-8').read()
    m = re.search(r'const DATA = (.*?);\nconst TOTAL_TIME', txt, re.S)
    if not m:
        raise SystemExit('❌ 解析失败：%s 里找不到 DATA（模板结构变了？）' % path)
    return json.loads(m.group(1))['qs']


def load_wrong():
    """抽出该章做错过的真题（题干/选项/答案/解析一律取 HTML 校正后的版本）"""
    out, seen = [], set()
    for tag, hf, jf in SETS:
        sp = os.path.join(OUT_DIR, hf)
        jp = os.path.join(OUT_DIR, jf)
        if not os.path.exists(sp) or not os.path.exists(jp):
            continue
        qs = html_qs(sp)
        jg = json.load(io.open(jp, encoding='utf-8'))
        for q in qs:
            if q['ch'] != CH_KEY:
                continue
            r = jg.get(str(q['no']), {})
            if not r:
                continue                       # 该套没判过的题跳过
            if r.get('mark') == '✓':          # 只收做错的（含漏选△、错选✗、空）
                continue
            if r.get('ans') != q['ans']:
                print('⚠ 答案键不一致 Q%s：HTML=%s judged=%s（以 HTML 为准）'
                      % (q['no'], q['ans'], r.get('ans')))
            key = re.sub(r'\s', '', q['stem'])[:24]
            if key in seen:
                continue
            seen.add(key)
            out.append({
                'no': q['no'],
                'type': q['type'],
                'stem': q['stem'],
                'opts': norm_opts(q['opts']),
                'ans': q['ans'],
                'myOld': r.get('my', ''),
                'oldRes': r.get('mark', ''),
                'ana': q.get('ana', {}),
            })
    return out


def load_props():
    p = os.path.join(HERE, 'props', '%s.json' % CH_KEY)
    if not os.path.exists(p):
        return []
    return json.load(io.open(p, encoding='utf-8'))


def main():
    wrong = load_wrong()
    props = load_props()
    name = CH_NAME.get(CH, CH_KEY)

    qs = []
    # Part A 错题回炉
    for i, w in enumerate(wrong, 1):
        a = w['ana']
        qs.append({
            'no': 2000 + i,
            'label': 'R%d' % i,
            'sec': 'wrong',
            'type': w['type'],
            'lv': '真',
            'sec2': 75 if w['type'] == '多选' else 50,
            'wasWrong': True,
            'myOld': w['myOld'] or '空',
            'src': '真题错题',
            'stem': w['stem'],
            'opts': w['opts'],
            'ans': w['ans'],
            'kp': a.get('kp', ''),
            'model': a.get('model', ''),
            'chain': li(a.get('chain')),
            'fast': a.get('fast', ''),
            'traps': li(a.get('traps')),
            'mother': a.get('mother', ''),
            'analysis': a.get('analysis', ''),
        })
    # Part B 自命题检验
    for j, p in enumerate(props, 1):
        qs.append({
            'no': 3000 + j,
            'label': 'P%d' % j,
            'sec': 'prop',
            'type': p['type'],
            'lv': p.get('lv', '真'),
            'sec2': p.get('sec', 50),
            'wasWrong': False,
            'src': '自命题·仿真',
            'stem': p['stem'],
            'opts': [{'k': k, 't': t} for k, t in p['opts']],
            'ans': p['ans'],
            'kp': p.get('kp', ''),
            'model': p.get('model', ''),
            'chain': li(p.get('chain')),
            'fast': p.get('fast', ''),
            'traps': li(p.get('traps')),
            'mother': p.get('mother', ''),
            'analysis': p.get('analysis', ''),
        })

    # 校验
    for q in qs:
        keys = set(o['k'] for o in q['opts'])
        if not set(q['ans']) <= keys:
            print('❌ 答案越界', q['label'], q['ans'])
        need = 4 if q['type'] == '单选' else 5
        if len(q['opts']) != need:
            print('❌ 选项数异常', q['label'], len(q['opts']))
        if q['type'] == '多选' and not (2 <= len(q['ans']) <= 4):
            print('❌ 多选正确项数异常', q['label'], q['ans'])
        if not q['analysis']:
            print('⚠ 缺解析', q['label'])

    n_s = sum(1 for q in qs if q['type'] == '单选')
    n_m = len(qs) - n_s
    full = n_s + 2 * n_m
    minute = n_s * 50 + n_m * 75
    total_min = max(10, round(minute / 60.0))

    CFG = {
        'title': '金融第%s章 %s · 即时判题训练卷' % (CH, name),
        'totalMin': total_min,
        'pass': int(round(full * 0.6)),
        'full': full,
        'nSingle': n_s,
        'nMulti': n_m,
        'sections': [
            {'key': 'wrong', 'name': '第一部分 · 错题回炉（真题）',
             'short': 'R 错题回炉',
             'desc': '这 %d 题是你在两套真题模考中<b>答错过的本题真题</b>（含错选与少选）。'
                     '右上角红色标签 = 上次你的答案。先不看解析重做一遍——<b>能全对才叫真的销账</b>。' % len(wrong)},
            {'key': 'prop', 'name': '第二部分 · 自命题检验',
             'short': 'P 自命题',
             'desc': '⚠️ 本节的 %d 题是<b>自命题仿真题，不是真题</b>（依 2026 大纲 + 一本通本章 A 段骨架编写，'
                     '手法照真题但无年份题号），用来补<b>错题覆盖不到的大纲考点</b>，避免背答案式刷分。' % len(props)},
        ],
    }

    TXT = io.open(TPL, encoding='utf-8').read()
    TITLE = '金融第%s章 · %s' % (CH, name)
    SUB = '错题 %d 题 + 自命题 %d 题 ｜ %d 分钟 ｜ 满分 %d' % (len(wrong), len(props), total_min, full)
    KEY = 'fin_drill_ch%s_v1' % CH
    FOOT = ('<b>使用说明</b>：① 单选点一下立即判定；多选勾完点「确认本题」判定。'
            '② 判定后自动展开正解 + ⚡秒杀判据，点「展开完整解析」看推理链与易错点。'
            '③ 「即时判题 ON/OFF」——想测真实水平时先关掉（变成传统交卷后才判）。'
            '④ 进度自动存本机浏览器，换设备不同步；勿用无痕模式。<br>'
            '<b>来源声明</b>：第一部分为你在金融第一套 / 第二套真题模考中答错的本局真题；'
            '第二部分为按 2026 官方考试大纲与本人错题本编写的自命题仿真题，<b>不得视为真题</b>。')

    html = TXT.replace('/*__DATA__*/', json.dumps({'qs': qs}, ensure_ascii=False))
    html = html.replace('/*__CFG__*/', json.dumps(CFG, ensure_ascii=False))
    html = html.replace('__TITLE__', TITLE)
    html = html.replace('__SUB__', SUB)
    html = html.replace('__KEY__', KEY)
    html = html.replace('__FOOT__', FOOT)

    os.makedirs(OUT_DIR, exist_ok=True)
    OUT = os.path.join(OUT_DIR, '金融第%s章·即时判题训练卷.html' % CH)
    io.open(OUT, 'w', encoding='utf-8').write(html)

    print('第%s章 %s' % (CH, name))
    print('  错题回炉 %d + 自命题 %d = %d 题（单选 %d / 多选 %d）' % (len(wrong), len(props), len(qs), n_s, n_m))
    print('  满分 %d 分，合格线 %d，限时 %d 分钟' % (full, CFG['pass'], total_min))
    print('  输出：%s（%.1f KB）' % (OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == '__main__':
    main()
