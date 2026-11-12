# -*- coding: utf-8 -*-
"""错题三刷卷生成器：二刷卷（107题）判卷结果中仍错的 49 题 → 三刷即时判题卷。

数据源：
  1) 附录错题清单 49 label（OCR 自 Desktop/WorkBuddy.pdf，2026-11-07 凌晨）
  2) exams/模考卷/金融全科·错题二刷卷.html 内 DATA —— 完整题目数据
输出：exams/模考卷/金融全科·错题三刷卷.html
"""
import io, os, re, json, copy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SRC = os.path.join(ROOT, 'exams', '模考卷', '金融全科·错题二刷卷.html')
TPL = os.path.join(HERE, 'template_drill.html')
OUT = os.path.join(ROOT, 'exams', '模考卷', '金融全科·错题三刷卷.html')

# 二刷仍错 49 题（OCR 附录错题清单，已与 DATA 49/49 对齐 + 交叉验证）
WRONG49 = """01-R6 03-R9 03-R10
03-R13 03-R22 03-R23 03-R26 03-R27 03-P9
04-R10 04-P1 04-P5 04-P11
05-R4 05-R6 05-R21 05-P10
06-R5
07-R4 07-P2 07-P10 07-P14 07-P19
08-R3
09-R3 09-R6 09-P12 09-P13 09-P19
10-R2 10-R11 10-P3 10-P16
11-R3 11-R6 11-R8 11-R9 11-R11 11-R12 11-R13 11-P5 11-P16 11-P17 11-P18 11-P20
12-R1 12-R2 12-P14 12-P19""".split()

CH_NAMES = {'01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险公司',
            '05': '证券与基金', '06': '金融市场与工具', '07': '金融资产定价',
            '08': '公司治理与风险管理', '09': '货币供求与均衡', '10': '开放经济均衡',
            '11': '中央银行与金融调控', '12': '金融监管'}
CN_NUM = {'01': '一', '02': '二', '03': '三', '04': '四', '05': '五', '06': '六',
          '07': '七', '08': '八', '09': '九', '10': '十', '11': '十一', '12': '十二'}


def main():
    labs = sorted(WRONG49, key=lambda l: (l[:2], 0 if l.split('-')[1][0] == 'R' else 1,
                                          int(l.split('-')[1][1:])))
    src = json.loads(re.search(r'const DATA = (.*?);\n', io.open(SRC, encoding='utf-8').read(), re.S).group(1))['qs']
    qmap = {q['label']: q for q in src}
    assert len(qmap) == 107, len(qmap)

    out, sections = [], {}
    no = 0
    for lab in labs:
        q = qmap[lab]
        no += 1
        nq = copy.deepcopy(q)
        nq['no'] = no
        nq['sec'] = 'ch' + lab[:2]
        if not nq.get('sec2'):
            nq['sec2'] = 75 if q['type'] == '多选' else 50
        out.append(nq)
        sections.setdefault(lab[:2], []).append(lab)

    for q in out:
        keys = set(o['k'] for o in q['opts'])
        assert set(q['ans']) <= keys, ('答案越界', q['label'])
        assert q.get('analysis'), ('缺解析', q['label'])

    n_s = sum(1 for q in out if q['type'] == '单选')
    n_m = len(out) - n_s
    full = n_s + 2 * n_m
    total_min = max(10, round((n_s * 50 + n_m * 75) / 60.0))
    sec_cfg = []
    for ch in sorted(sections):
        sec_cfg.append({'key': 'ch%s' % ch,
                        'name': '第%s部分 · 第 %s 章 %s（三刷 %d 道）' % (CN_NUM[ch], ch, CH_NAMES[ch], len(sections[ch])),
                        'short': '%s %s' % (ch, CH_NAMES[ch][:5]),
                        'desc': '二刷卷中本章仍答错/少选的 %d 道题（第 %s 次回炉）。' % (len(sections[ch]), '三')})
    CFG = {'title': '金融全科 · 错题三刷卷（二刷 49 顽固错题）', 'totalMin': total_min,
           'pass': int(round(full * 0.6)), 'full': full, 'nSingle': n_s, 'nMulti': n_m,
           'sections': sec_cfg}

    TXT = io.open(TPL, encoding='utf-8').read()
    html = TXT.replace('/*__DATA__*/', json.dumps({'qs': out}, ensure_ascii=False))
    html = html.replace('/*__CFG__*/', json.dumps(CFG, ensure_ascii=False))
    html = html.replace('__TITLE__', '金融全科 · 错题三刷卷')
    html = html.replace('__SUB__', '二刷仍错 %d 道（单 %d / 多 %d）｜ 满分 %d ｜ 合格 %d ｜ 限时 %d 分钟'
                        % (len(out), n_s, n_m, full, CFG['pass'], total_min))
    html = html.replace('__KEY__', 'fin_sanshua_v1')
    html = html.replace('__FOOT__',
        '<b>使用说明</b>：① 二刷卷 107 题你销账 58 道（全对），剩<b>这 49 道</b>——错误 40 + 少选 9，'
        '二刷得分 91.5/161（57%）。② 重灾区：第11章 12 道、第3章 8 道。'
        '③ 单选点选即判；多选勾完点「确认本题」。④ 每题秒杀行先看一眼再作答，答完看推理链。<br>'
        '<b>来源声明</b>：含真题（R 系列）与自命题仿真题（P 系列，不得视为真题）。')

    io.open(OUT, 'w', encoding='utf-8').write(html)
    print('OK 输出：%s（%.1f KB）' % (OUT, os.path.getsize(OUT) / 1024.0))
    print('   %d 题（单 %d / 多 %d）|满分 %d|合格 %d|限时 %d 分钟' % (len(out), n_s, n_m, full, CFG['pass'], total_min))
    print('   各章：', ' '.join('%s:%d' % (ch, len(sections[ch])) for ch in sorted(sections)))


if __name__ == '__main__':
    main()
