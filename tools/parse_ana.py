# -*- coding: utf-8 -*-
"""解析 tools/ana/*.md（题号块 + key: value / - 列表）-> {no: {...}}"""
import io, os, re, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))
ANA_DIR = os.path.join(HERE, 'ana')

def parse_file(path):
    txt = io.open(path, encoding='utf-8').read()
    out = {}
    cur = None
    key = None
    for line in txt.split('\n'):
        m = re.match(r'^###\s+(\d+)\s*$', line)
        if m:
            cur = int(m.group(1)); out[cur] = {}; key = None
            continue
        if cur is None:
            continue
        m = re.match(r'^([a-zA-Z]+):\s*(.*)$', line)
        if m and not line.startswith('  ') and not line.startswith('-'):
            key = m.group(1); val = m.group(2).strip()
            if val:
                out[cur][key] = val
            else:
                out[cur][key] = []
            continue
        m = re.match(r'^-\s+(.*)$', line)
        if m and key:
            out[cur][key].append(m.group(1).strip())
            continue
        if line.strip() == '' or line.startswith('#'):
            continue
    return out

def load_all(ana_dir=None):
    d = {}
    src = ana_dir or ANA_DIR
    # 只加载 ana/ana2 的解析文件，避免被 corrections.md / patches.md 覆盖
    pats = ['ana_[0-9]*.md', 'ana2_[0-9]*.md'] if os.path.basename(src) == 'ana2' else ['ana_[0-9]*.md']
    for p in pats:
        for f in sorted(glob.glob(os.path.join(src, p))):
            for k, v in parse_file(f).items():
                d[k] = v
    return d

if __name__ == '__main__':
    d = load_all()
    print('解析到 %d 条' % len(d))
    miss = [k for k, v in d.items() if not v.get('analysis')]
    print('缺 analysis：', miss)
    print('题号范围：', min(d), '-', max(d))
