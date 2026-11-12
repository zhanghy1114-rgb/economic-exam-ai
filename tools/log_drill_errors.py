# -*- coding: utf-8 -*-
"""通用「训练卷错题 → 错题本」入档器（03~05 章用的是各章专用脚本，本脚本 06 章起通用）

用法：
  python log_drill_errors.py 06                      # 自动在 tmp2/ 找最新的 *_答题记录.txt
  python log_drill_errors.py 06 path/to/记录.txt

输入格式（卷子交卷页点「导出答题记录」得到的 TSV）：
  本卷：金融第06章 ...
  得分：xx

  题号  题型  你答  正解  得分  判定
  R1    单选  B     A     0     ✗ 错误
  ...

做的事：
  1) 从 HTML 内 DATA 取题干/选项/秒杀/易错点（唯一数据源，不读 selected.json）
  2) 按病因码自动归类：E1 方向反转（贴现/大小方向）｜E2 概念数值混淆｜E3 选非方向｜E4 多选错选｜E5 多选漏选
  3) 生成「逐条」块，插入 exams/错题本/错题本.md 顶部（幂等：同章重复执行会先删旧块）
"""
import io, os, re, sys, json, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
BANK = os.path.join(ROOT, 'exams', '错题本', '错题本.md')
TMP = os.path.join(ROOT, 'tmp2')

CH = sys.argv[1] if len(sys.argv) > 1 else '06'
DRIVE = os.path.join(ROOT, 'exams', '模考卷', '金融第%s章·即时判题训练卷.html' % CH)

E1_HINT = ('贴现', '发行价', '价格', '金额', '收益', '现值', '汇率')


def strip_tags(s):
    s = re.sub(r'<br\s*/?>', ' ', str(s or ''))
    s = re.sub(r'</?b>', '**', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def load_data():
    txt = io.open(DRIVE, encoding='utf-8').read()
    m = re.search(r'const DATA = (.*?);\nconst KEY', txt, re.S)
    if not m:
        raise SystemExit('❌ 找不到 DATA：%s' % DRIVE)
    qs = json.loads(m.group(1))['qs']
    return {q['label']: q for q in qs}, qs


def norm(s):
    return ''.join(sorted(set(re.sub(r'[^A-E]', '', s or ''))))


def find_record():
    if len(sys.argv) > 2:
        return sys.argv[2]
    cs = [os.path.join(TMP, f) for f in os.listdir(TMP) if f.endswith('.txt')]
    cs = [c for c in cs if '答题记录' in io.open(c, encoding='utf-8', errors='ignore').read(400)]
    if not cs:
        raise SystemExit('❌ tmp2/ 里没有 *_答题记录.txt，请先把导出文件放进来或直接给路径')
    return max(cs, key=os.path.getmtime)


def parse_record(path):
    raw = io.open(path, encoding='utf-8-sig', errors='ignore').read().splitlines()
    got = ''
    rows = []
    for ln in raw:
        if ln.startswith('得分'):
            got = ln.split('：')[-1].strip()
        parts = ln.split('\t')
        if len(parts) >= 6 and re.match(r'^[RP]\d+$', parts[0].strip()):
            rows.append({'label': parts[0].strip(), 'type': parts[1].strip(),
                         'my': parts[2].strip(), 'ans': parts[3].strip(),
                         'sc': parts[4].strip(), 'verdict': parts[5].strip()})
    return got, rows


def cause(q, r):
    my, ans = norm(r['my']), norm(r['ans'])
    if not my:
        return 'E2', '未作答'
    if q['type'] == '单选':
        if re.search(r'错误|不属于|不包括|不是|不正确|不能', strip_tags(q['stem'])):
            return 'E3', '选非方向丢失'
        if any(h in strip_tags(q['stem']) for h in E1_HINT):
            return 'E1', '方向/数值反转'
        return 'E2', '概念/数值混淆'
    extra = set(my) - set(ans)
    if extra:
        return 'E4', '多选错选'
    return 'E5', '多选漏选'


def build_block(rows, qmap, score_line):
    bads = [r for r in rows if not (r['verdict'].startswith('✅'))]
    full = sum(2 if qmap[r['label']]['type'] == '多选' else 1 for r in rows if r['label'] in qmap)
    got = 0.0
    for r in rows:
        try:
            got += float(r['sc'])
        except ValueError:
            pass
    ns = sum(1 for r in rows if qmap.get(r['label'], {}).get('type') == '单选')
    nm = len(rows) - ns
    # 分节
    sec = {}
    for r in rows:
        q = qmap.get(r['label'])
        if not q:
            continue
        s = sec.setdefault(q['sec'], [0, 0.0])
        s[0] += 2 if q['type'] == '多选' else 1
        try:
            s[1] += float(r['sc'])
        except ValueError:
            pass
    codes = {}
    for r in bads:
        q = qmap.get(r['label'])
        if not q:
            continue
        c, _ = cause(q, r)
        codes[c] = codes.get(c, 0) + 1

    sc = got
    pct = sc / full * 100 if full else 0
    passline = int(round(full * 0.6))
    n_right = sum(1 for r in rows if r['verdict'].startswith('✅'))
    n_part = sum(1 for r in rows if r['verdict'].startswith('△'))
    n_wrong = sum(1 for r in rows if r['verdict'].startswith('✗'))
    n_empty = sum(1 for r in rows if '未作答' in r['verdict'])

    L = []
    L.append('# 金融%s章 即时判题训练卷（%s 判卷）' % (CH, datetime.date.today().strftime('%Y-%m-%d')))
    L.append('')
    L.append('> 成绩 **%g/%d（%.0f%%）**，合格线 %d —— %s'
             % (sc, full, pct, passline, '✅ **过线**' if sc >= passline else '🔴 **未过线，差 %g 分**' % (passline - sc)))
    for k, (t, s) in sec.items():
        nm_ = '错题回炉' if k == 'wrong' else '自命题'
        L.append('> 分节：%s **%g/%d（%.0f%%）**' % (nm_, s, t, s / t * 100 if t else 0))
    L.append('> 结构：全对 %d｜少选 %d｜**错误 %d**｜未答 %d' % (n_right, n_part, n_wrong, n_empty))
    L.append('> 病因：' + '、'.join('%s×%d' % (k, v) for k, v in sorted(codes.items())))
    L.append('')
    L.append('### 逐条（%d 题）' % len(bads))
    L.append('')
    for r in bads:
        q = qmap.get(r['label'])
        if not q:
            continue
        c, cname = cause(q, r)
        kp = strip_tags(q.get('kp', '')).replace('第6章·', '').replace('第5章·', '').replace('第7章·', '').replace('第9章·', '')
        body = strip_tags(q['stem'])[:46]
        extra = ''
        if r['verdict'].startswith('△'):
            extra = ' · 少选得 %s' % r['sc']
        L.append('**❌ %s（%s·%s %s%s）** %s… → 用户 **%s**，正解 **%s**'
                 % (r['label'], kp, cname, c, extra, body, r['my'] or '未答', r['ans']))
        L.append('- 原题选项：%s' % '｜'.join('%s %s' % (o['k'], strip_tags(o['t'])[:34]) for o in q['opts']))
        traps = q.get('traps') or []
        if traps:
            L.append('- 错因点：%s' % strip_tags(traps[0]))
        anchor = strip_tags(q.get('fast', ''))
        if anchor and '**' not in anchor:
            anchor = '**%s**' % anchor
        L.append('- 锚：%s' % anchor)
        L.append('')
    L.append('---')
    L.append('')
    return '\n'.join(L), dict(got=got, full=full, pct=pct, passline=passline,
                              n_right=n_right, n_part=n_part, n_wrong=n_wrong,
                              bads=len(bads), codes=codes, sec=sec)


def main():
    qmap, qs = load_data()
    path = find_record()
    got_line, rows = parse_record(path)
    if not rows:
        raise SystemExit('❌ 没解析到题目行（%s）——确认是「导出答题记录」的 TSV，不是页面 HTML' % path)
    block, st = build_block(rows, qmap, got_line)

    s = io.open(BANK, encoding='utf-8').read()
    # 幂等：删掉同章旧块
    s = re.sub(r'# 金融%s章 即时判题训练卷（[^\n]*\n\n(?:>[^\n]*\n)+### 逐条.*?\n---\n\n' % CH,
               '', s, flags=re.S)
    m = re.search(r'^---\n\n', s, re.M)
    if not m:
        raise SystemExit('❌ 错题本.md 结构变了，找不到第一个 --- 分隔')
    shutil.copy(BANK, BANK + '.bak_%s' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    s = s[:m.end()] + block + s[m.end():]
    s = re.sub(r'> 最近更新：[^\n]*', '> 最近更新：%s（金融%s章·即时判题训练卷判卷）'
               % (datetime.date.today().strftime('%Y-%m-%d'), CH), s, count=1)
    io.open(BANK, 'w', encoding='utf-8').write(s)

    print('记录文件：%s' % path)
    print('成绩 %g/%d（%.0f%%）｜合格 %d｜全对 %d 少选 %d 错误 %d 未答 %d'
          % (st['got'], st['full'], st['pct'], st['passline'],
             st['n_right'], st['n_part'], st['n_wrong'],
             len(rows) - st['n_right'] - st['n_part'] - st['n_wrong']))
    for k, (t, v) in st['sec'].items():
        print('  %s: %g/%d（%.0f%%）' % (k, v, t, v / t * 100 if t else 0))
    print('错题 %d 条已入档｜病因 %s' % (st['bads'], st['codes']))


if __name__ == '__main__':
    main()
