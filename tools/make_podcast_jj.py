# -*- coding: utf-8 -*-
"""对谈版播客合成器：双人对谈 md → WinRT(Kangkang+Yaoyao) wav 段 → 拼接 → MP3

用法：
  1) python tools/make_podcast_dlg.py split    # 解析对谈稿 → tmp2/podcast_dlg/segments.json
  2) powershell -File tools/make_podcast_dlg.ps1 -SegJson ... -OutDir tmp2/podcast_dlg/segs
  3) python tools/make_podcast_dlg.py join      # 拼接 → 对谈版.mp3
  4) python tools/make_podcast_dlg.py chapters  # 按章切分 → 分章_对谈/
"""
import io, os, re, sys, wave, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
MD = os.path.join(ROOT, 'exams', '错题本', '播客', '经基考前锚点播客_对谈版文字稿.md')
WORK = os.path.join(ROOT, 'tmp2', 'podcast_jj')
SEGS = os.path.join(WORK, 'segs')
OUT_MP3 = os.path.join(ROOT, 'exams', '错题本', '播客', '经基考前锚点播客_对谈版.mp3')
CH_DIR = os.path.join(ROOT, 'exams', '错题本', '播客', '经基分章_对谈')


def clean(t):
    t = t.strip()
    t = re.sub(r'^>.*$', '', t, flags=re.M)
    t = t.replace('|', '，').replace('#', '').replace('*', '')
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def speak_title(inner):
    parts = [p.strip() for p in inner.split('·') if p.strip()]
    return '，'.join(parts)


def is_title(t):
    return bool(re.match(r'^第[一二三四五六七八九十]+章，', t)) or t.startswith('结尾') or t.startswith('开场')


def split():
    raw = io.open(MD, encoding='utf-8').read()
    blocks = [b.strip() for b in re.split(r'\n-{3,}\n', raw)]
    segs = []          # [{"s":"K"|"Y","t":text}]
    chapters = []      # 章名列表
    ch = -1
    started = False
    for b in blocks:
        if not started:
            if '【' not in b:
                continue
            started = True
        titles = re.findall(r'【([^】]*)】', b)
        for t in titles:
            ch += 1
            chapters.append(speak_title(t))
        b = re.sub(r'【[^】]*】\s*', '', b)
        for line in b.split('\n'):
            m = re.match(r'^([康雅])：(.*)$', line.strip())
            if not m:
                continue
            spk = 'K' if m.group(1) == '康' else 'Y'
            txt = clean(m.group(2))
            if len(txt) < 2:
                continue
            # 长句保险切分（SAPI/WinRT 长文本偶发断流）
            parts = re.split(r'(?<=[。！？])', txt)
            cur = ''
            for p in parts:
                if len(cur) + len(p) > 450 and cur:
                    segs.append({'s': spk, 't': cur})
                    cur = p
                else:
                    cur += p
            if cur.strip():
                segs.append({'s': spk, 't': cur.strip()})
    os.makedirs(WORK, exist_ok=True)
    json.dump({'segs': segs, 'chapters': chapters},
              io.open(os.path.join(WORK, 'segments.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    n_k = sum(1 for s in segs if s['s'] == 'K')
    n_y = len(segs) - n_k
    print('分段 %d 段（康 %d / 雅 %d），总字数 %d，章 %d 个'
          % (len(segs), n_k, n_y, sum(len(s['t']) for s in segs), len(chapters)))


def _load():
    meta = json.load(io.open(os.path.join(WORK, 'segments.json'), encoding='utf-8'))
    segs = meta['segs']
    files = sorted(f for f in os.listdir(SEGS) if f.endswith('.wav'))
    if not files:
        raise SystemExit('没有 wav 段，先跑 make_podcast_dlg.ps1')
    assert len(files) == len(segs), 'wav 段数 %d != json 段数 %d' % (len(files), len(segs))
    return meta, segs


def encode(idxs, segs, out_path):
    import lameenc
    pcm = bytearray()
    sr = None
    prev = None
    for k, i in enumerate(idxs):
        f = os.path.join(SEGS, 'seg%03d.wav' % i)
        w = wave.open(f, 'rb')
        sr = sr or w.getframerate()
        assert w.getframerate() == sr and w.getnchannels() == 1 and w.getsampwidth() == 2, f
        if k > 0:
            gap = 0.32 if segs[i]['s'] != prev else 0.14
            pcm += b'\x00\x00' * int(sr * gap)
        pcm += w.readframes(w.getnframes())
        w.close()
        prev = segs[i]['s']
    enc = lameenc.Encoder()
    enc.set_bit_rate(64)
    enc.set_in_sample_rate(sr)
    enc.set_channels(1)
    enc.set_quality(3)
    mp3 = enc.encode(bytes(pcm)) + enc.flush()
    io.open(out_path, 'wb').write(mp3)
    return len(pcm) / 2.0 / sr


def join():
    meta, segs = _load()
    secs = encode(range(len(segs)), segs, OUT_MP3)
    print('OK %s（%.1f MB，%d 分 %d 秒，%d 段）'
          % (OUT_MP3, os.path.getsize(OUT_MP3) / 1048576.0, secs // 60, secs % 60, len(segs)))


def chapters():
    """按章切：开场 / 12 章 / 结尾。章界 = 章标题段之后的第一个turn。

    split 时每章第一段（章标题后的第一句）已隐含章界，这里用
    「上一段是某章开头标志」不可靠，改为：跟踪段文本命中章标题首句。
    简化实现：预先在 split 里记录每章首段索引。
    """
    # 重新计算章界：每章第一段 = 出现在章标题文本之后的第一个段。
    # 由于章标题不单独成段（对谈稿里章题由康的台词隐含），这里按
    # chapters 列表 + 段落顺序切：检索每章第一段文本的开头若干字。
    meta, segs = _load()
    chapters_names = meta['chapters']
    # split 时已把每章第一段的起始文本规律化：康的引子句包含「第X章」
    # 这里直接用另一个思路——重新扫 md 找章内第一段索引。
    raw = io.open(MD, encoding='utf-8').read()
    blocks = [b.strip() for b in re.split(r'\n-{3,}\n', raw)]
    marks = []
    seg_i = 0
    started = False
    for b in blocks:
        if not started:
            if '【' not in b:
                continue
            started = True
        n_turn = 0
        for line in b.split('\n'):
            m = re.match(r'^([康雅])：(.*)$', line.strip())
            if not m:
                continue
            txt = clean(m.group(2))
            if len(txt) < 2:
                continue
            n_turn += 1
        if n_turn:
            marks.append(seg_i)
            seg_i += n_turn
    marks.append(len(segs))
    os.makedirs(CH_DIR, exist_ok=True)
    total = 0
    for k in range(len(marks) - 1):
        a, b = marks[k], marks[k + 1]
        name = '%02d_%s.mp3' % (k, re.sub(r'[\\/:*?"<>|，]', '_', chapters_names[k])[:28])
        secs = encode(range(a, b), segs, os.path.join(CH_DIR, name))
        total += secs
        print('  %s  %d 分 %d 秒' % (name, secs // 60, secs % 60))
    print('OK 分章 %d 个文件，合计 %d 分 %d 秒 → %s'
          % (len(marks) - 1, total // 60, int(total) % 60, CH_DIR))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'split'
    {'split': split, 'join': join, 'chapters': chapters}.get(cmd, split)()
