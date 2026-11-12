# -*- coding: utf-8 -*-
"""错题二刷卷生成器：从「金融全科·12章错题总复测卷」DATA 中取指定错题（TSV）重新组卷。

用法：python build_retest_drill.py
数据源：
  1) tmp2/金融全科·12章错题总复测卷_答题记录.txt —— 107 道错题 label 清单
  2) exams/模考卷/金融全科·12章错题总复测卷.html 内 DATA —— 完整题目数据（含解析/秒杀/易错点）
"""
import io, os, re, json, copy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
REC = os.path.join(ROOT, 'tmp2', '金融全科·12章错题总复测卷_答题记录.txt')
SRC = os.path.join(ROOT, 'exams', '模考卷', '金融全科·12章错题总复测卷.html')
TPL = os.path.join(HERE, 'template_drill.html')
OUT = os.path.join(ROOT, 'exams', '模考卷', '金融全科·错题二刷卷.html')

CH_NAMES = {'01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险公司',
            '05': '证券与基金', '06': '金融市场与工具', '07': '金融资产定价',
            '08': '公司治理与风险管理', '09': '货币供求与均衡', '10': '开放经济均衡',
            '11': '中央银行与金融调控', '12': '金融监管'}
CN_NUM = {'01': '一', '02': '二', '03': '三', '04': '四', '05': '五', '06': '六',
          '07': '七', '08': '八', '09': '九', '10': '十', '11': '十一', '12': '十二'}


def load_labels():
    """返回 [(label, my)]：按章 → 题型（R 回炉在前、P 自命题在后）→ 题号数值 排序。"""
    labs = []
    for ln in io.open(REC, encoding='utf-8').read().splitlines():
        p = ln.split('\t')
        if len(p) >= 6 and re.match(r'^\d{2}-[RP]\d+$', p[0].strip()):
            labs.append((p[0].strip(), p[2].strip()))

    def key(t):
        lab = t[0]
        ch, rest = lab.split('-')[0], lab.split('-')[1]
        return (ch, 0 if rest[0] == 'R' else 1, int(rest[1:]))

    labs.sort(key=key)
    return labs


def main():
    labs = load_labels()
    src = json.loads(re.search(r'const DATA = (.*?);\n', io.open(SRC, encoding='utf-8').read(), re.S).group(1))['qs']
    qmap = {q['label']: q for q in src}

    out, missing, sections = [], [], {}
    no = 0
    for lab, my in labs:
        q = qmap.get(lab)
        if not q:
            missing.append(lab)
            continue
        no += 1
        nq = copy.deepcopy(q)
        nq['no'] = no
        nq['sec'] = 'ch' + lab[:2]
        nq.pop('wasWrong', None)
        nq.pop('myOld', None)
        if not nq.get('sec2'):
            nq['sec2'] = 75 if q['type'] == '多选' else 50
        out.append(nq)
        ch = lab[:2]
        sections.setdefault(ch, []).append(lab)

    if missing:
        print('⚠️ 缺失：', missing)

    order = sorted(sections)
    sec_cfg = []
    for ch in order:
        labs_ch = sections[ch]
        sec_cfg.append({'key': 'ch%s' % ch,
                        'name': '第%s部分 · 第 %s 章 %s（二刷 %d 道）' % (CN_NUM[ch], ch, CH_NAMES[ch], len(labs_ch)),
                        'short': '%s %s' % (ch, CH_NAMES[ch][:5]),
                        'desc': '总复测卷中本章答错/少选的 %d 道题。' % len(labs_ch)})

    for q in out:
        keys = set(o['k'] for o in q['opts'])
        assert set(q['ans']) <= keys, ('答案越界', q['label'])
        assert q.get('analysis'), ('缺解析', q['label'])

    n_s = sum(1 for q in out if q['type'] == '单选')
    n_m = len(out) - n_s
    full = n_s + 2 * n_m
    total_min = max(10, round((n_s * 50 + n_m * 75) / 60.0))
    CFG = {'title': '金融全科 · 错题二刷卷（总复测 107 错题）', 'totalMin': total_min,
           'pass': int(round(full * 0.6)), 'full': full, 'nSingle': n_s, 'nMulti': n_m,
           'sections': sec_cfg}

    TXT = io.open(TPL, encoding='utf-8').read()
    html = TXT.replace('/*__DATA__*/', json.dumps({'qs': out}, ensure_ascii=False))
    html = html.replace('/*__CFG__*/', json.dumps(CFG, ensure_ascii=False))
    html = html.replace('__TITLE__', '金融全科 · 错题二刷卷')
    html = html.replace('__SUB__', '总复测错题 %d 道（单 %d / 多 %d）｜ 满分 %d ｜ 合格 %d ｜ 限时 %d 分钟'
                        % (len(out), n_s, n_m, full, CFG['pass'], total_min))
    html = html.replace('__KEY__', 'fin_retest_v1')
    html = html.replace('__FOOT__',
        '<b>使用说明</b>：① 这是你 11-05 总复测卷 189 题中<b>答错 87 + 少选 20 = 107 道</b>，按章分 12 节，'
        '题号「09-R6」与总复测卷一致。② 单选点选即判；多选勾完点「确认本题」。'
        '③ 全对 82 道未收录——<b>这 107 道就是考前的全部提分空间</b>（差 32.5 分，对应错题约 60 分分值）。'
        '④ 开卷前 60 秒：四张手卡（松紧方向｜FDI 不是债｜两支柱分家｜数字先圈主语）+ 选非两步走。<br>'
        '<b>来源声明</b>：含真题（R 系列）与自命题仿真题（P 系列，不得视为真题）。')

    io.open(OUT, 'w', encoding='utf-8').write(html)
    print('✅ 输出：%s（%.1f KB）' % (OUT, os.path.getsize(OUT) / 1024.0))
    print('   %d 题（单 %d / 多 %d）｜满分 %d｜合格 %d｜限时 %d 分钟' % (len(out), n_s, n_m, full, CFG['pass'], total_min))
    print('   各章：', ' '.join('%s:%d' % (ch, len(sections[ch])) for ch in order))


if __name__ == '__main__':
    main()
