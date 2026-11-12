# -*- coding: utf-8 -*-
"""
生成「逐题详解页」HTML：题目 + 全部选项 + 你的选择 + 正确答案 + 解析
用法：
  python build_review.py 1   # 第一套（读 _paper1_judged.json）
  python build_review.py 2   # 第二套（读 _paper2_judged.json）
"""
import io, os, re, sys, json, html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK = os.path.join(BASE, 'exams', '模考卷')

PAPERS = {
    '1': dict(file='金融专业真题模考卷（第一套）.html',
              judged='_paper1_judged.json',
              out='第一套_逐题详解.html',
              title='金融专业真题模考卷（第一套）· 逐题详解',
              full=140, passline=84, tmin=90),
    '2': dict(file='金融专业真题模考卷（第二套）.html',
              judged='_paper2_judged.json',
              out='第二套_逐题详解.html',
              title='金融专业真题模考卷（第二套）· 逐题详解',
              full=125, passline=75, tmin=95),
}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#16181d; --ink2:#4a5159; --ink3:#79828c; --line:#e3e7ec; --bg:#f5f6f8; --card:#fff;
  --ok:#1a7f4b; --okbg:#e8f7ee; --okline:#9fd8b6;
  --bad:#c0392b; --badbg:#fdeceb; --badline:#f2b8b2;
  --warn:#a86a00; --warnbg:#fff6e5; --warnline:#f0d19a;
  --pri:#1f5fa8; --pribg:#eef4fc;
}
body{font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);
     line-height:1.68;font-size:15px;-webkit-font-smoothing:antialiased}
.wrap{max-width:940px;margin:0 auto;padding:0 18px 90px}

/* 顶栏 */
.top{position:sticky;top:0;z-index:20;background:rgba(245,246,248,.94);backdrop-filter:blur(10px);
     border-bottom:1px solid var(--line);padding:12px 0 10px;margin-bottom:22px}
.topin{max-width:940px;margin:0 auto;padding:0 18px}
.h1{font-size:17px;font-weight:700;letter-spacing:.2px}
.h1 small{font-weight:400;color:var(--ink3);font-size:12.5px;margin-left:8px}
.scorebar{display:flex;gap:18px;align-items:baseline;margin-top:8px;flex-wrap:wrap}
.sb{font-size:13px;color:var(--ink2)}
.sb b{font-size:21px;color:var(--ink);font-variant-numeric:tabular-nums}
.sb .red{color:var(--bad)}
.filters{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}
.fb{border:1px solid var(--line);background:#fff;color:var(--ink2);font-size:12.5px;padding:5px 12px;
    border-radius:20px;cursor:pointer;font-family:inherit;transition:.15s}
.fb:hover{border-color:#c3cbd4}
.fb.on{background:var(--ink);color:#fff;border-color:var(--ink)}

/* 章标题 */
.chap{font-size:13px;font-weight:700;color:var(--ink2);letter-spacing:.6px;margin:34px 0 12px;
      padding-left:10px;border-left:3px solid var(--ink);display:flex;justify-content:space-between;
      align-items:baseline;scroll-margin-top:130px}
.chap span{font-weight:400;color:var(--ink3);font-size:12px;letter-spacing:0}

/* 题卡 */
.q{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:12px;
   scroll-margin-top:130px}
.q.bad{border-left:3px solid var(--bad)}
.q.half{border-left:3px solid var(--warn)}
.q.good{border-left:3px solid var(--ok)}
.qh{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:9px}
.no{font-weight:700;font-size:15px;font-variant-numeric:tabular-nums}
.tag{font-size:11.5px;padding:1px 8px;border-radius:4px;background:#eef1f4;color:var(--ink2)}
.tag.s{background:var(--pribg);color:var(--pri)}
.tag.m{background:#f3eefc;color:#6d43a8}
.res{font-size:11.5px;padding:1px 9px;border-radius:4px;font-weight:600}
.res.r{background:var(--badbg);color:var(--bad);border:1px solid var(--badline)}
.res.w{background:var(--warnbg);color:var(--warn);border:1px solid var(--warnline)}
.res.g{background:var(--okbg);color:var(--ok);border:1px solid var(--okline)}
.sc{margin-left:auto;font-size:12px;color:var(--ink3);font-variant-numeric:tabular-nums}
.stem{font-size:15px;margin-bottom:11px;color:var(--ink)}
/* 选项 */
.opts{list-style:none;display:flex;flex-direction:column;gap:5px;margin-bottom:12px}
.opt{display:flex;gap:9px;padding:7px 11px;border:1px solid var(--line);border-radius:8px;font-size:14px;
     color:var(--ink2);background:#fcfcfd}
.opt .k{font-weight:700;color:var(--ink3);min-width:15px}
.opt .mk{margin-left:auto;font-size:11px;padding:0 7px;border-radius:4px;white-space:nowrap;align-self:center}
.opt.correct{background:var(--okbg);border-color:var(--okline);color:#145c37;font-weight:500}
.opt.correct .k{color:var(--ok)}
.opt.correct .mk{background:var(--ok);color:#fff}
.opt.mine-wrong{background:var(--badbg);border-color:var(--badline);color:#8e2b21}
.opt.mine-wrong .k{color:var(--bad)}
.opt.mine-wrong .mk{background:var(--bad);color:#fff}
/* 判定条 */
.verdict{display:flex;gap:20px;flex-wrap:wrap;font-size:13.5px;padding:9px 12px;border-radius:8px;
         background:var(--bg);border:1px dashed var(--line)}
.verdict div{color:var(--ink2)}
.verdict b{font-family:ui-monospace,Consolas,monospace;font-size:15px;letter-spacing:1px}
.verdict .my b{color:var(--bad)}
.verdict .my.ok b{color:var(--ok)}
.verdict .an b{color:var(--ok)}
/* 解析 */
details{margin-top:11px;border-top:1px dashed var(--line);padding-top:9px}
summary{font-size:13px;color:var(--pri);cursor:pointer;font-weight:600;list-style:none;user-select:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";display:inline-block;transition:.15s}
details[open] summary::before{content:"▾ "}
.ana{padding:11px 0 2px;font-size:13.8px;color:var(--ink2)}
.ana .row{display:flex;gap:10px;margin-bottom:9px;align-items:flex-start}
.ana .lb{flex:0 0 78px;font-size:11.5px;font-weight:700;color:var(--ink3);letter-spacing:.4px;padding-top:2px}
.ana .tx{flex:1;min-width:0}
.ana .tx b{color:var(--ink);background:#fff8dc;padding:0 2px;border-radius:2px}
.chain{counter-reset:c;list-style:none}
.chain li{counter-increment:c;padding-left:20px;position:relative;margin-bottom:5px}
.chain li::before{content:counter(c);position:absolute;left:0;top:1px;width:15px;height:15px;border-radius:50%;
  background:#eef1f4;color:var(--ink2);font-size:10.5px;text-align:center;line-height:15px;font-weight:700}
.chain li b{background:#fff8dc}
.fast{background:var(--warnbg);border-left:3px solid #e8b64c;padding:8px 11px;border-radius:0 6px 6px 0}
.fast b{background:none}
.traps{list-style:none}
.traps li{padding-left:14px;position:relative;margin-bottom:4px}
.traps li::before{content:"!";position:absolute;left:0;top:0;color:var(--bad);font-weight:800;font-size:12px}
.mother{color:var(--ink);background:var(--pribg);padding:8px 11px;border-radius:6px;font-size:13.2px}
.mother b{background:none}
.official p{margin-bottom:7px}
.official p:last-child{margin-bottom:0}
.flagw{font-size:12px;color:var(--warn);background:var(--warnbg);border:1px solid var(--warnline);
       padding:5px 9px;border-radius:6px;margin-bottom:9px}

.foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--ink3);text-align:center}
@media print{
  body{background:#fff;font-size:10.5pt}
  .top{position:static;background:#fff}
  .filters,.hint{display:none!important}
  .wrap{padding:0;max-width:none}
  .q{break-inside:avoid;box-shadow:none;border:1px solid #ddd}
  details{display:block!important}
  details>.ana{display:block!important}
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  @page{margin:12mm}
}
"""

JS = """
const qs = document.querySelectorAll('.q');
document.querySelectorAll('.fb[data-f]').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.fb[data-f]').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    const f=b.dataset.f;
    qs.forEach(q=>{ q.style.display = (f==='all'||q.dataset.r===f) ? '' : 'none'; });
    document.querySelectorAll('.chap').forEach(c=>{
      let n=c.nextElementSibling, any=false;
      while(n && !n.classList.contains('chap')){ if(n.classList.contains('q')&&n.style.display!=='none') any=true; n=n.nextElementSibling; }
      c.style.display = any?'':'none';
    });
  });
});
document.querySelectorAll('.fb[data-exp]').forEach(b=>{
  b.addEventListener('click',()=>{
    const on=b.dataset.exp==='1';
    document.querySelectorAll('details').forEach(d=>d.open=on);
    b.dataset.exp = on?'0':'1';
    b.textContent = on?'收起全部解析':'展开全部解析';
  });
});
document.addEventListener('keydown',e=>{
  if(e.key==='e'||e.key==='E'){ document.querySelector('.fb[data-exp]').click(); }
});
"""


def esc(s):
    return html.escape(s or '', quote=False)


def build(paper):
    cfg = PAPERS[paper]
    src = io.open(os.path.join(MOCK, cfg['file']), encoding='utf-8').read()
    data = json.loads(re.search(r'const DATA = (.*?);\nconst TOTAL_TIME', src, re.S).group(1))
    by = {q['no']: q for q in data['qs']}
    jp = os.path.join(MOCK, cfg['judged'])
    judged = json.load(io.open(jp, encoding='utf-8'))

    nos = sorted(by)
    total = sum(judged[str(n)]['sc'] for n in nos)
    right = sum(1 for n in nos if judged[str(n)]['mark'] == '✓')
    half = sum(1 for n in nos if judged[str(n)]['mark'] == '△')
    wrong = sum(1 for n in nos if judged[str(n)]['mark'] == '✗')
    sgl = sum(judged[str(n)]['sc'] for n in nos if by[n]['type'] == '单选')
    mul = sum(judged[str(n)]['sc'] for n in nos if by[n]['type'] == '多选')
    n_s = sum(1 for n in nos if by[n]['type'] == '单选')
    n_m = sum(1 for n in nos if by[n]['type'] == '多选')

    h = []
    A = h.append
    A('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A(f'<title>{esc(cfg["title"])}</title><style>{CSS}</style></head><body>')
    A('<div class="top"><div class="topin">')
    A(f'<div class="h1">{esc(cfg["title"].replace("· 逐题详解", ""))}<small>逐题详解 · {len(nos)} 题 · 正确答案 + 全部选项 + 你的选择 + 解析</small></div>')
    A('<div class="scorebar">')
    A(f'<div class="sb">总分 <b>{total:g}</b> / {cfg["full"]}　<span class="red">({total/cfg["full"]*100:.1f}%)</span></div>')
    A(f'<div class="sb">单选 <b>{sgl:g}</b>/{n_s}</div>')
    A(f'<div class="sb">多选 <b>{mul:g}</b>/{2*n_m}</div>')
    A(f'<div class="sb">全对 <b>{right}</b>｜半对 <b>{half}</b>｜全错 <b>{wrong}</b></div>')
    A(f'<div class="sb" style="color:var(--ink3)">合格线 {cfg["passline"]}｜限时 {cfg["tmin"]} 分钟</div>')
    A('</div>')
    A('<div class="filters">')
    A(f'<button class="fb on" data-f="all">全部 {len(nos)}</button>')
    A(f'<button class="fb" data-f="bad">❌ 全错 {wrong}</button>')
    A(f'<button class="fb" data-f="half">⚠️ 半对 {half}</button>')
    A(f'<button class="fb" data-f="good">✅ 全对 {right}</button>')
    A('<button class="fb" data-exp="0">展开全部解析</button>')
    A('</div></div></div>')
    A('<div class="wrap">')

    cur = None
    for n in nos:
        q = by[n]
        d = judged[str(n)]
        ch = q['ch'].replace('金融第', '').replace('章', '')
        mark = d['mark']
        cls = {'✓': 'good', '△': 'half', '✗': 'bad'}[mark]
        rk = {'✓': 'good', '△': 'half', '✗': 'bad'}[mark]
        rtxt = {'✓': '✅ 全对', '△': f'⚠️ 半对 {d["sc"]:g}分', '✗': '❌ 全错'}[mark]
        if ch != cur:
            cur = ch
            seg = [m for m in nos if by[m]['ch'].replace('金融第', '').replace('章', '') == ch
                   and (by[m]['type'] == q['type'])]
            nseg = len(seg)
            nerr = sum(1 for m in seg if judged[str(m)]['mark'] != '✓')
            part = '单选段' if q['type'] == '单选' else '多选段'
            cid = f'ch{ch}{"s" if q["type"]=="单选" else "m"}'
            A(f'<div class="chap" id="{cid}">第{ch}章 {esc(q.get("chname",""))}'
              f'<span>{part} · {nseg} 题 · 错/半对 {nerr}</span></div>')
        A(f'<article class="q {cls}" data-r="{rk}" id="q{n}">')
        A('<div class="qh">')
        A(f'<span class="no">Q{n}</span>')
        A(f'<span class="tag {"s" if q["type"]=="单选" else "m"}">{"单选 1分" if q["type"]=="单选" else "多选 2分"}</span>')
        A(f'<span class="tag">{esc(q["ana"].get("kp",""))[:26]}</span>')
        A(f'<span class="res {"r" if mark=="✗" else ("w" if mark=="△" else "g")}">{rtxt}</span>')
        A(f'<span class="sc">得 {d["sc"]:g} 分</span>')
        A('</div>')
        stem_txt = re.sub(r'\s+', ' ', q['stem']).strip()
        A(f'<div class="stem">{esc(stem_txt)}</div>')

        my = d.get('my') or ''
        ans = q['ans']
        A('<ul class="opts">')
        for o in q['opts']:
            k, t = o['k'], o['t'].strip()
            isc = k in ans
            ismine = k in my
            if isc and ismine:
                c = 'opt correct'; mk = '正解 · 你选 ✓'
            elif isc:
                c = 'opt correct'; mk = '正解'
            elif ismine:
                c = 'opt mine-wrong'; mk = '你选 ✗'
            else:
                c = 'opt'; mk = ''
            mkh = f'<span class="mk">{mk}</span>' if mk else ''
            A(f'<li class="{c}"><span class="k">{k}</span><span class="tx">{esc(t)}</span>{mkh}</li>')
        A('</ul>')

        okc = ' ok' if mark == '✓' else ''
        A('<div class="verdict">')
        A(f'<div class="my{okc}">你的答案　<b>{esc(my) if my else "（未作答）"}</b></div>')
        A(f'<div class="an">正确答案　<b>{esc(ans)}</b></div>')
        A(f'<div>得分 <b>{d["sc"]:g}</b> / {1 if q["type"]=="单选" else 2}</div>')
        if mark == '△':
            miss = [k for k in ans if k not in my]
            extra = [k for k in my if k not in ans]
            note = []
            if miss: note.append('漏选 ' + ''.join(miss))
            if extra: note.append('错选 ' + ''.join(extra))
            A(f'<div style="color:var(--warn)">{" · ".join(note)}</div>')
        A('</div>')

        a = q['ana']
        A('<details><summary>看解析（考点 / 推理链 / ⚡最快解法 / 易错点 / 母题）</summary><div class="ana">')
        if a.get('model'):
            A(f'<div class="row"><div class="lb">问法模型</div><div class="tx">{a["model"]}</div></div>')
        ch_ = a.get('chain')
        if ch_:
            if isinstance(ch_, str):
                ch_ = [ch_]
            A('<div class="row"><div class="lb">推理链</div><div class="tx"><ol class="chain">' +
              ''.join(f'<li>{x}</li>' for x in ch_) + '</ol></div></div>')
        if a.get('fast'):
            A(f'<div class="row"><div class="lb">最快解法</div><div class="tx"><div class="fast">{a["fast"]}</div></div></div>')
        tr = a.get('traps') or []
        if isinstance(tr, str):
            tr = [tr]
        if tr:
            A('<div class="row"><div class="lb">易错点</div><div class="tx"><ul class="traps">' +
              ''.join(f'<li>{x}</li>' for x in tr) + '</ul></div></div>')
        if a.get('mother'):
            A(f'<div class="row"><div class="lb">母题抽象</div><div class="tx"><div class="mother">{a["mother"]}</div></div></div>')
        if a.get('analysis'):
            A(f'<div class="row"><div class="lb">详解</div><div class="tx official">{a["analysis"]}</div></div>')
        if a.get('flag'):
            A(f'<div class="flagw">⚠ {esc(a["flag"])}</div>')
        A('</div></details>')
        A('</article>')

    A(f'<div class="foot">共 {len(nos)} 题 · 由真题池组卷 · 逐题详解自动生成 · 快捷键 E 展开/收起全部解析</div>')
    A('</div>')
    A(f'<script>{JS}</script></body></html>')

    out = os.path.join(MOCK, cfg['out'])
    io.open(out, 'w', encoding='utf-8').write('\n'.join(h))
    print(f'{cfg["out"]}  {os.path.getsize(out)/1024:.0f} KB  题数 {len(nos)}  总分 {total:g}/{cfg["full"]}  全对{right}/半对{half}/全错{wrong}')
    build_md(paper, by, judged, nos, total, cfg, right, half, wrong)


def build_md(paper, by, judged, nos, total, cfg, right, half, wrong):
    """同步产出一份纯文本版（题目 + 全部选项 + 答案），便于打印/检索"""
    NL = chr(10)
    o = []
    A = o.append
    A(f'# {cfg["title"].replace("· 逐题详解", "")} · 逐题核对表（题目+全部选项+答案）')
    A('')
    A(f'> 得分 **{total:g} / {cfg["full"]} = {total/cfg["full"]*100:.1f}%**｜合格线 {cfg["passline"]}｜限时 {cfg["tmin"]} 分钟')
    A(f'> 全对 {right} 题｜半对 {half} 题｜全错 {wrong} 题｜错+半对共 {half+wrong} 题')
    A('> 选项标记：**粗体 = 正确答案**｜`←你` = 你勾的项｜无标记 = 未勾')
    A('> 结果：✅ 全对｜⚠️ 半对（少选）｜❌ 全错')
    A('')
    A('---')
    A('')
    A(f'## 一、全卷速查（{len(nos)} 题）')
    A('')
    A('| 题 | 章 | 题型 | 题目（摘要） | 你答 | 正解 | 得分 | 结果 |')
    A('|---|---|---|---|---|---|---|---|')
    for n in nos:
        q = by[n]; d = judged[str(n)]
        ch = q['ch'].replace('金融第', '').replace('章', '')
        st = re.sub(r'\s+', '', q['stem'])
        st = st if len(st) <= 44 else st[:44] + '…'
        mk = {'✓': '✅', '△': '⚠️', '✗': '❌'}[d['mark']]
        A(f'| {n} | {ch} | {"单" if q["type"]=="单选" else "多"} | {st} | {d["my"]} | **{q["ans"]}** | {d["sc"]:g} | {mk} |')
    A('')
    A('---')
    A('')

    def block(title, items):
        A(title)
        A('')
        cur = None
        for n in items:
            q = by[n]; d = judged[str(n)]
            ch = q['ch'].replace('金融第', '').replace('章', '')
            if ch != cur:
                cur = ch
                A('')
                A(f'### 第{ch}章 {q.get("chname","")}')
                A('')
            tag = {'✓': '✅ 全对', '△': '⚠️ 半对', '✗': '❌ 全错'}[d['mark']]
            A(f'**Q{n}（{q["type"]}）{tag}**　你答 {d["my"]} → 正解 {q["ans"]}，得 {d["sc"]:g} 分　｜　考点：{q["ana"].get("kp","")}')
            A('')
            A('题干：' + re.sub(r'\s+', ' ', q['stem']).strip())
            A('')
            for op in q['opts']:
                k, t = op['k'], op['t'].strip()
                lab = f'**{k}. {t}**' if k in q['ans'] else f'{k}. {t}'
                tail = '　`←你`' if k in (d['my'] or '') else ''
                A(f'- {lab}{tail}')
            A('')

    bad = [n for n in nos if judged[str(n)]['mark'] != '✓']
    good = [n for n in nos if judged[str(n)]['mark'] == '✓']
    block(f'## 二、错题 {len(bad)} 道 · 完整题目（题干 + 全部选项）', bad)
    A('---')
    A('')
    block(f'## 三、答对 {len(good)} 道 · 完整题目（题干 + 全部选项）', good)
    out = os.path.join(MOCK, cfg['out'].replace('.html', '.md'))
    io.open(out, 'w', encoding='utf-8').write(NL.join(o))
    print(f'  ↳ {os.path.basename(out)}  {os.path.getsize(out)/1024:.0f} KB')


if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else '1'
    build(p)
