# -*- coding: utf-8 -*-
"""《金融·考前秒记锦囊》markdown → 手机版 HTML（复用原设计语言，新增真题实证样式）。"""
import io, re, html, sys

MD = sys.argv[1] if len(sys.argv) > 1 else 'exams/错题本/金融·考前秒记锦囊.md'
OUT = sys.argv[2] if len(sys.argv) > 2 else MD.replace('.md', '_手机版.html')
TITLE = sys.argv[3] if len(sys.argv) > 3 else '金融 · 考前秒记锦囊（真题实证版）'
SUB = sys.argv[4] if len(sys.argv) > 4 else ('真题实证版｜每章挂你做过的真题战绩：题号 / 考点 / 正解 / 错次<br>'
      '215 道真题 + 338 道章卷题 → 189 道错题 → 8 轮回炉归零')

CSS = """
:root{
  --bg:#f6f7f9; --card:#ffffff; --ink:#1a1d21; --ink2:#5b6470; --line:#e3e6ea;
  --red:#c0392b; --redbg:#fdf0ee; --blue:#1d6fb8; --bluebg:#eef5fc;
  --gold:#a6761d; --goldbg:#fdf7e8; --green:#1e7d5a; --greenbg:#eaf6f1;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#14171a; --card:#1c2024; --ink:#eef1f4; --ink2:#9aa4b0; --line:#2c3238;
    --red:#ff8a7a; --redbg:#2a1c1a; --blue:#7bb8ee; --bluebg:#16232e;
    --gold:#e0b25c; --goldbg:#2a2317; --green:#6cd3a8; --greenbg:#152420;
  }
}
*{box-sizing:border-box;-webkit-text-size-adjust:100%}
body{margin:0;padding:0 0 60px;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  line-height:1.72;font-size:16px}
.wrap{max-width:760px;margin:0 auto;padding:0 14px}
header{padding:26px 0 14px;border-bottom:2px solid var(--ink);margin-bottom:18px}
h1{font-size:23px;margin:0 0 6px;letter-spacing:-.3px}
.sub{font-size:13.5px;color:var(--ink2);line-height:1.6}
h2{font-size:17px;margin:26px 0 12px;padding-left:10px;border-left:4px solid var(--ink);line-height:1.35}
h3{font-size:15.5px;margin:22px 0 10px;line-height:1.5;font-weight:700}
h3 .badge{display:inline-block;font-size:12px;font-weight:700;border-radius:20px;padding:2px 9px;
  background:var(--goldbg);color:var(--gold);margin-left:6px;vertical-align:middle;letter-spacing:0;
  font-variant-numeric:tabular-nums}
p{margin:10px 0;font-size:15px}
b{font-weight:700}
.hit{color:var(--red);font-weight:700;font-variant-numeric:tabular-nums}
.chip{display:inline-block;background:var(--bluebg);color:var(--blue);border-radius:6px;
  padding:1px 7px;font-size:12.5px;font-weight:700;margin:1px 2px;font-variant-numeric:tabular-nums}
.lead{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 15px;margin:0 0 14px}
blockquote{margin:10px 0;background:var(--bluebg);border-left:4px solid var(--blue);
  border-radius:0 10px 10px 0;padding:11px 13px;font-size:14.5px;color:var(--ink)}
blockquote.warn{background:var(--redbg);border-left-color:var(--red)}
blockquote.tip{background:var(--greenbg);border-left-color:var(--green)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:8px 0;
  border:1px solid var(--line);border-radius:12px;background:var(--card)}
table{width:100%;border-collapse:collapse;font-size:13.5px;min-width:100%}
th{text-align:left;font-weight:700;color:var(--ink2);font-size:12px;padding:8px 7px;
  border-bottom:2px solid var(--line);letter-spacing:.4px;white-space:nowrap;background:var(--card)}
td{padding:8px 7px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.55}
tr:last-child td{border-bottom:none}
td:first-child{font-weight:700;color:var(--blue);white-space:nowrap}
td .hit{color:var(--red)}
pre{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;
  font-size:12.5px;line-height:1.9;overflow-x:auto;margin:10px 0;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
ul,ol{margin:8px 0;padding-left:22px;font-size:15px}
li{margin:5px 0}
hr{border:none;border-top:1px solid var(--line);margin:22px 0}
.foot{text-align:center;font-size:12.5px;color:var(--ink2);padding:22px 0 0}
"""


def inline(s):
    """行内标记：**粗体** / `代码` / 🎯错×N 高亮"""
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`([^`]+)`', r'<span class="chip">\1</span>', s)
    s = re.sub(r'🎯<b>错(×\d+)</b>', r'<span class="hit">🎯错\1</span>', s)
    s = re.sub(r'🎯<b>([^<]+)</b>', r'<span class="hit">🎯\1</span>', s)
    return s


def cell(s):
    return inline(s.strip())


def build_table(rows):
    out = ['<div class="scroll"><table>']
    head = rows[0]
    ths = [c for c in head.strip().strip('|').split('|')]
    out.append('<tr>' + ''.join('<th>%s</th>' % cell(c) for c in ths) + '</tr>')
    for r in rows[1:]:
        tds = [c for c in r.strip().strip('|').split('|')]
        if len(tds) > len(ths):
            tds = tds[:len(ths)]
        while len(tds) < len(ths):
            tds.append('')
        out.append('<tr>' + ''.join('<td>%s</td>' % cell(c) for c in tds) + '</tr>')
    out.append('</table></div>')
    return '\n'.join(out)


def main():
    md = io.open(MD, encoding='utf-8').read()
    lines = md.split('\n')
    body, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith('```'):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith('```'):
                buf.append(lines[j]); j += 1
            body.append('<pre>%s</pre>' % html.escape('\n'.join(buf)))
            i = j + 1
            continue
        if s == '---' or s == '':
            i += 1; continue
        if s.startswith('#### '):
            body.append('<h4>%s</h4>' % inline(s[5:]))
            i += 1; continue
        if s.startswith('### '):
            txt = s[4:]
            m = re.match(r'^(.*?)　`([^`]+)`$', txt)
            if m:
                body.append('<h3>%s<span class="badge">%s</span></h3>' % (inline(m.group(1)), html.escape(m.group(2))))
            else:
                body.append('<h3>%s</h3>' % inline(txt))
            i += 1; continue
        if s.startswith('## '):
            body.append('<h2>%s</h2>' % inline(s[3:]))
            i += 1; continue
        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                r = lines[i].strip()
                if not re.match(r'^\|[\s\-:|]+\|$', r):
                    rows.append(r)
                i += 1
            if rows:
                body.append(build_table(rows))
            continue
        if s.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            txt = ' '.join(x.strip() for x in buf if x.strip())
            cls = 'warn' if ('最痛' in txt or '铁钉' in txt) else ('tip' if ('自命题补漏' in txt or '怎么用' in txt) else '')
            body.append('<blockquote%s>%s</blockquote>' % (' class="%s"' % cls if cls else '', inline(txt)))
            continue
        m = re.match(r'^(\d+)\.\s+(.*)$', s)
        if m:
            buf = []
            while i < len(lines):
                mm = re.match(r'^(\d+)\.\s+(.*)$', lines[i].strip())
                if not mm: break
                buf.append('<li>%s</li>' % inline(mm.group(2)))
                i += 1
            body.append('<ol>%s</ol>' % ''.join(buf))
            continue
        if s.startswith('- '):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                buf.append('<li>%s</li>' % inline(lines[i].strip()[2:]))
                i += 1
            body.append('<ul>%s</ul>' % ''.join(buf))
            continue
        # 标题行（首行 # ）
        if s.startswith('# '):
            i += 1; continue
        body.append('<p>%s</p>' % inline(s))
        i += 1

    h = ['<!DOCTYPE html>', '<html lang="zh-CN">', '<head>',
         '<meta charset="UTF-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">',
         '<title>%s</title>' % TITLE,
         '<style>%s</style>' % CSS, '</head>', '<body>', '<div class="wrap">',
         '<header><h1>%s</h1>' % TITLE,
         '<div class="sub">%s</div></header>' % SUB]
    h += body
    h += ['<div class="foot">%s<br>稳住，BOSS。</div>' % (sys.argv[5] if len(sys.argv) > 5 else '货币管水位，审慎管谁在裸泳。'),
          '</div></body></html>']
    out = '\n'.join(h)
    io.open(OUT, 'w', encoding='utf-8').write(out)
    print('OK %s | %.1f KB' % (OUT, len(out.encode('utf-8')) / 1024.0))
    # 结构自检
    for tag in ['div', 'table', 'tr', 'td', 'th', 'pre', 'blockquote', 'h2', 'h3']:
        o = len(re.findall(r'<%s[\s>]' % tag, out)); c = len(re.findall(r'</%s>' % tag, out))
        print('  <%s> %d / </%s> %d %s' % (tag, o, tag, c, 'OK' if o == c else '✗ 不匹配'))


if __name__ == '__main__':
    main()
