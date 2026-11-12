# -*- coding: utf-8 -*-
"""RapidOCR 高精度识别 + 双栏还原排序
用法: python ocr_rapid.py <pdf> <起始页1基> <结束页1基> <输出txt> [dpi]
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from rapidocr_onnxruntime import RapidOCR

BASE = r'F:/自己创建的skill/学习/中级经济师 - 金融学习'


def sort_boxes(res, row_tol=20):
    """把 OCR 行按「先上行、后左栏」排序，还原双栏阅读顺序"""
    if not res:
        return []
    items = []
    for box, txt, score in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append({'x': min(xs), 'y': min(ys), 'y2': max(ys), 'txt': txt, 's': score})
    items.sort(key=lambda d: (d['y'], d['x']))
    # 行聚类：y 差 < row_tol 视为同一行
    rows = []
    for it in items:
        if rows and abs(it['y'] - rows[-1][0]['y']) < row_tol:
            rows[-1].append(it)
        else:
            rows.append([it])
    out = []
    for r in rows:
        r.sort(key=lambda d: d['x'])
        out.append(' '.join(d['txt'] for d in r))
    return out


def main():
    imgdir, outp = sys.argv[1], sys.argv[2]
    files = sorted(f for f in os.listdir(imgdir) if f.lower().endswith('.png'))
    ocr = RapidOCR()
    parts = []
    t0 = time.time()
    for i, f in enumerate(files, 1):
        res = ocr(os.path.join(imgdir, f))[0]
        lines = sort_boxes(res)
        parts.append(f'\n===== {f.replace(".png","")} =====\n' + '\n'.join(lines))
        if i % 5 == 0 or i == len(files):
            el = time.time() - t0
            print(f'{f} | 已完成 {i}/{len(files)} | 累计 {el:.0f}s | 预计剩 {(len(files)-i)*el/i:.0f}s', flush=True)
    os.makedirs(os.path.dirname(outp) or '.', exist_ok=True)
    open(outp, 'w', encoding='utf-8').write(''.join(parts))
    print('DONE ->', outp, os.path.getsize(outp), 'bytes', flush=True)


if __name__ == '__main__':
    main()
