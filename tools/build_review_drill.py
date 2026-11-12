# -*- coding: utf-8 -*-
"""金融全科 12 章错题总复测卷生成器

数据源（唯一）：
  1) 错题 label 清单：exams/错题本/错题本.md 里 12 个「# 金融XX章 即时判题训练卷」区块的全部 ❌ 条目
  2) 题目完整数据：exams/模考卷/金融第XX章·即时判题训练卷.html 内 DATA（含校正答案键）

做法：12 章错题按章顺序合并 → 重编号（no 全局唯一、label=XX-R1 跨章唯一）→
      隐藏「上次答 X」标签（防泄底，测真实提取）→ 分节=12 章 → 套 template_drill.html
"""
import io, os, re, sys, json, copy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
BANK = os.path.join(ROOT, 'exams', '错题本', '错题本.md')
DRILL_DIR = os.path.join(ROOT, 'exams', '模考卷')
TPL = os.path.join(HERE, 'template_drill.html')
OUT = os.path.join(ROOT, 'exams', '模考卷', '金融全科·12章错题总复测卷.html')

CH_NAMES = {
    '01': '金融学基础', '02': '金融体系', '03': '商业银行', '04': '保险公司',
    '05': '证券与基金', '06': '金融市场与工具', '07': '金融资产定价',
    '08': '公司治理与风险管理', '09': '货币供求与均衡', '10': '开放经济均衡',
    '11': '中央银行与金融调控', '12': '金融监管',
}
CN_NUM = {'01': '一', '02': '二', '03': '三', '04': '四', '05': '五', '06': '六',
          '07': '七', '08': '八', '09': '九', '10': '十', '11': '十一', '12': '十二'}


def load_wrong_labels():
    """从错题本.md 逐区块提取 12 章的错题 label（按出现顺序）。"""
    chs = {}
    cur = None
    for ln in io.open(BANK, encoding='utf-8'):
        m = re.match(r'^# 金融(\d{2})章 ', ln)
        if m:
            cur = m.group(1) if m.group(1) in CH_NAMES else None
            if cur:
                chs.setdefault(cur, [])
            continue
        if ln.startswith('# '):          # 其他区块 → 离开金融训练卷区块
            cur = None
            continue
        m = re.match(r'^\*\*❌[→]?\s*([RP]\d+)\b', ln)
        if m and cur:
            chs[cur].append(m.group(1))
    return chs


def load_chapter_data(ch):
    p = os.path.join(DRILL_DIR, '金融第%s章·即时判题训练卷.html' % ch)
    txt = io.open(p, encoding='utf-8').read()
    m = re.search(r'const DATA = (.*?);\n', txt, re.S)
    qs = json.loads(m.group(1))['qs']
    return {q['label']: q for q in qs}


def main():
    chs = load_wrong_labels()
    total_labels = sum(len(v) for v in chs.values())
    print('错题本提取：', {k: len(v) for k, v in sorted(chs.items())}, '｜合计', total_labels)

    out_qs, sections, missing = [], [], []
    no = 0
    for ch in sorted(chs):
        if not chs[ch]:
            continue
        qmap = load_chapter_data(ch)
        got = 0
        for lab in chs[ch]:
            q = qmap.get(lab)
            if not q:
                missing.append((ch, lab))
                continue
            no += 1
            got += 1
            nq = copy.deepcopy(q)
            nq['no'] = no
            nq['label'] = '%s-%s' % (ch, lab)     # 如 09-R6，跨章唯一
            nq['sec'] = 'ch%s' % ch
            nq.pop('wasWrong', None)              # 隐藏上次答案，防泄底
            nq.pop('myOld', None)
            if not nq.get('sec2'):
                nq['sec2'] = 75 if q['type'] == '多选' else 50
            out_qs.append(nq)
        sections.append({'key': 'ch%s' % ch,
                         'name': '第%s部分 · 第 %s 章 %s（错题 %d 道）' % (CN_NUM[ch], ch, CH_NAMES[ch], got),
                         'short': '%s %s' % (ch, CH_NAMES[ch][:5]),
                         'desc': '第 %s 章训练卷中你答错/少选的 %d 道题。<b>先不翻卡重做，即时判题见真章</b>。' % (ch, got)})

    if missing:
        print('⚠️ 找不到对应题目的 label：', missing)

    # 校验
    nos = set(q['no'] for q in out_qs)
    labs = set(q['label'] for q in out_qs)
    assert len(nos) == len(out_qs) and len(labs) == len(out_qs), '主键冲突'
    for q in out_qs:
        keys = set(o['k'] for o in q['opts'])
        assert set(q['ans']) <= keys, ('答案越界', q['label'], q['ans'])
        need = 4 if q['type'] == '单选' else 5
        assert len(q['opts']) == need, ('选项数异常', q['label'])
        assert q.get('analysis'), ('缺解析', q['label'])

    n_s = sum(1 for q in out_qs if q['type'] == '单选')
    n_m = len(out_qs) - n_s
    full = n_s + 2 * n_m
    total_min = max(10, round((n_s * 50 + n_m * 75) / 60.0))

    CFG = {
        'title': '金融全科 12 章错题总复测卷',
        'totalMin': total_min,
        'pass': int(round(full * 0.6)),
        'full': full,
        'nSingle': n_s,
        'nMulti': n_m,
        'sections': sections,
    }
    TXT = io.open(TPL, encoding='utf-8').read()
    html = TXT.replace('/*__DATA__*/', json.dumps({'qs': out_qs}, ensure_ascii=False))
    html = html.replace('/*__CFG__*/', json.dumps(CFG, ensure_ascii=False))
    html = html.replace('__TITLE__', '金融全科 · 12 章错题总复测卷')
    html = html.replace('__SUB__', '12 章错题 %d 道 ｜ 满分 %d ｜ 合格 %d ｜ 限时 %d 分钟（可分次做，进度自动存）'
                        % (len(out_qs), full, CFG['pass'], total_min))
    html = html.replace('__KEY__', 'fin_review_all_v1')
    html = html.replace('__FOOT__',
        '<b>使用说明</b>：① 这是你金融 01-12 章训练卷中<b>全部答错/少选的题</b>（含模考原错题回炉与自命题），'
        '按章分 12 节，题号「09-R6」= 第 09 章卷第 R6 题。'
        '② 单选点一下立即判定；多选勾完点「确认本题」。③ 即时判题 ON/OFF 可切换。'
        '④ 进度自动存本机浏览器，<b>可以分几天做</b>；勿用无痕模式。<br>'
        '<b>开卷前 60 秒</b>：四张手卡——<b>松紧方向（降降买/卖提提）｜FDI 不是债｜两支柱分家（审慎防风险·货币稳物价）｜数字先圈主语</b>，'
        '外加选非两步走「草稿写 ❌ → 只勾 ❌ 项」。<br>'
        '<b>来源声明</b>：含真题（R 系列，两套模考错题）与自命题仿真题（P 系列，依 2026 大纲编写，不得视为真题）。')

    io.open(OUT, 'w', encoding='utf-8').write(html)
    print('✅ 输出：%s（%.1f KB）' % (OUT, os.path.getsize(OUT) / 1024.0))
    print('   %d 题（单选 %d / 多选 %d）｜满分 %d｜合格 %d｜限时 %d 分钟'
          % (len(out_qs), n_s, n_m, full, CFG['pass'], total_min))
    print('   各章：', ' '.join('%s:%d' % (ch, sum(1 for q in out_qs if q['sec'] == 'ch' + ch))
                               for ch in sorted(chs)))


if __name__ == '__main__':
    main()
