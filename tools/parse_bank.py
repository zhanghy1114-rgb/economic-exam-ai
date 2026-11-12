# -*- coding: utf-8 -*-
"""把 OCR 出来的官方习题集解析成结构化题库（章/节/题型/题干/选项/答案/解析）"""
import re, sys, json

sys.stdout.reconfigure(encoding='utf-8')

CN = '一二三四五六七八九十'
Q_TYPE = r'〖\s*(单项选择题|多项选择题)\s*〗'


def norm(s):
    s = s.replace('℃', 'C').replace('〇', '0')
    s = re.sub(r'[ \t]+', '', s)
    return s


def reorder_options(opts):
    """处理双栏错位：A,C,E / B,D → A,B,C,D,E"""
    if not opts:
        return opts
    letters = [k for k, _ in opts]
    out = dict(opts)
    if letters == sorted(letters):
        return [(k, out[k]) for k in letters]
    # 按字母排序（同一字母多次出现时取最长文本）
    merged = {}
    for k, v in opts:
        if k not in merged or len(v) > len(merged[k]):
            merged[k] = v
    return [(k, merged[k]) for k in sorted(merged)]


def parse_chapter(seg, chap):
    """返回题目列表"""
    # 切节
    parts = re.split(r'第[' + CN + r']{1,3}节\s*([^\n]{0,30})', seg)
    sections = []
    if len(parts) == 1:
        sections.append(('', seg))
    else:
        for i in range(1, len(parts), 2):
            title = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ''
            sections.append((title, body))

    qs = []
    for sec_title, body in sections:
        # 切「同步习题」与「参考答案」
        split = re.split(r'二[、，]\s*参考答案', body)
        stem_part = split[0]
        ans_part = split[1] if len(split) > 1 else ''
        # 题目块
        pat = re.compile(r'(?<![\d])(\d{1,2})\s*[·．.、]?\s*' + Q_TYPE + r'(.+?)(?=(?<![\d])\d{1,2}\s*[·．.、]?\s*' + Q_TYPE + r'|考点[' + CN + r']|第[' + CN + r']{1,3}节|$)', re.S)
        blocks = []
        for m in pat.finditer(stem_part):
            num = int(m.group(1))
            typ = m.group(2)
            content = m.group(3)
            blocks.append((num, typ, content))
        # 答案
        answers = {}
        for m in re.finditer(r'(?<![\d])(\d{1,2})\s*[·．.、]?\s*([A-E]{1,5})(?=[^A-Za-z]|$)', ans_part):
            n = int(m.group(1))
            if n not in answers:
                answers[n] = m.group(2)
        for num, typ, content in blocks:
            # 选项：找 A./B./C./D./E.
            opt_marks = list(re.finditer(r'([A-E])\s*[\.．、,，]\s*', content))
            if not opt_marks:
                continue
            stem = content[:opt_marks[0].start()].strip()
            opts = []
            for i, om in enumerate(opt_marks):
                end = opt_marks[i + 1].start() if i + 1 < len(opt_marks) else len(content)
                txt = content[om.end():end].strip()
                txt = re.sub(r'第[' + CN + r']{1,3}节.*$', '', txt)
                txt = re.sub(r'考点[' + CN + r']{1,3}.*$', '', txt)
                txt = re.sub(r'[丿丨]\s*\d{1,3}\s*$', '', txt).strip()
                if txt:
                    opts.append((om.group(1), txt[:120]))
            opts = reorder_options(opts)
            if len(opts) < 3:
                continue
            stem = re.sub(r'[【〖\[].*?[】〗\]]', '', stem).strip()
            qs.append({
                'chap': chap, 'sec': sec_title.strip(), 'num': num, 'type': typ,
                'stem': stem[:200], 'options': opts,
                'answer': answers.get(num, ''),
            })
    return qs


def main(path, out_json):
    t = open(path, encoding='utf-8').read()
    t = norm(t)
    # 章边界：该「第X章」之后 500 字内必须出现「第一节」，否则是页眉重复
    cand = []
    for m in re.finditer(r'第([' + CN + r']{1,3})章', t):
        seg = t[m.start():m.start() + 500]
        if '第一节' in seg:
            cand.append((m.start(), m.group(1)))
    # 去连续重复
    m2 = []
    for pos, c in cand:
        if m2 and m2[-1][1] == c:
            continue
        m2.append((pos, c))
    # 只保留正文（跳过目录：目录里也有"第一节"）→ 取章序列最长递增的一段
    body_start = m2[0][0] if m2 else 0
    for i in range(len(m2) - 1):
        if m2[i + 1][1] == '二' and m2[i][1] == '一':
            body_start = m2[i][0]
            break
    m2 = [(p, c) for p, c in m2 if p >= body_start]
    body = t[body_start:]
    allq = []
    chapters = []
    for i, (pos, c) in enumerate(m2):
        end = m2[i + 1][0] if i + 1 < len(m2) else len(t)
        chapters.append((c, t[pos:end]))
    for c, seg in chapters:
        qs = parse_chapter(seg, c)
        allq.extend(qs)
        print(f'  第{c}章: {len(qs)} 题', flush=True)
    json.dump(allq, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('总计', len(allq), '题 ->', out_json)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
