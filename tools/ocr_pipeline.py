import fitz, os, sys, subprocess, shutil, time, re, json

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'F:/自己创建的skill/学习/中级经济师 - 金融学习'
TMP_ROOT = os.path.join(BASE, 'tmp', 'pages')
OUT = os.path.join(BASE, 'notes', '真题库', 'ocr')
PS = os.path.join(BASE, 'tools', 'ocr_win.ps1')
os.makedirs(OUT, exist_ok=True)

# 中文去空格 + 常见OCR修正
def clean(t):
    t = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', t)
    t = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[，。、；：？！（）《》“”])', '', t)
    t = re.sub(r'(?<=[，。、；：？！（）《》“”])\s+(?=[\u4e00-\u9fa5])', '', t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def run(pdf, name, dpi=200):
    src = os.path.join(BASE, pdf)
    if not os.path.exists(src):
        print('MISSING', pdf); return
    TMP = os.path.join(TMP_ROOT, re.sub(r'[^\w]', '_', name))
    doc = fitz.open(src)
    n = doc.page_count
    os.makedirs(TMP, exist_ok=True)
    t0 = time.time()
    for i in range(n):
        doc[i].get_pixmap(dpi=dpi).save(os.path.join(TMP, f'p{i+1:04d}.png'))
    doc.close()
    print(f'[{name}] 渲染 {n} 页 {time.time()-t0:.0f}s', flush=True)
    r = subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',PS,
                        '-InDir',TMP,'-OutDir',os.path.join(TMP,'txt')],
                       capture_output=True, text=True, encoding='utf-8', errors='ignore')
    tail = [l for l in (r.stdout or '').splitlines() if l.startswith(('DONE','FAIL'))]
    print(f'[{name}] OCR {time.time()-t0:.0f}s', tail[-1] if tail else r.stdout[-300:], flush=True)
    parts = []
    for i in range(n):
        p = os.path.join(TMP,'txt',f'p{i+1:04d}.txt')
        if os.path.exists(p):
            parts.append(f'\n===== P{i+1} =====\n' + clean(open(p,encoding='utf-8-sig').read()))
    txt = '\n'.join(parts)
    op = os.path.join(OUT, name + '.txt')
    open(op,'w',encoding='utf-8').write(txt)
    print(f'[{name}] -> {op}  {len(txt)}字', flush=True)

if __name__ == '__main__':
    jobs = json.loads(sys.argv[1])
    for pdf, name in jobs:
        run(pdf, name)
