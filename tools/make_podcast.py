# -*- coding: utf-8 -*-
"""考前错题播客合成器：文字稿 md → SAPI(Huihui) wav 段 → 拼接 → MP3

用法：
  1) python tools/make_podcast.py split   # 解析文字稿 → tmp2/podcast/segments.json
  2) powershell 段合成（make_podcast.ps1）
  3) python tools/make_podcast.py join    # 拼接 wav → mp3 成品
"""
import io, os, re, sys, wave, struct, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
MD = os.path.join(ROOT, 'exams', '错题本', '播客', '金融考前错题播客_文字稿.md')
WORK = os.path.join(ROOT, 'tmp2', 'podcast')
SEGS = os.path.join(WORK, 'segs')
OUT_MP3 = os.path.join(ROOT, 'exams', '错题本', '播客', '金融考前错题播客.mp3')

# TTS 文本清理：保留可读符号，去掉 markdown 残留
def clean(t):
    t = t.strip()
    t = re.sub(r'^>.*$', '', t, flags=re.M)
    t = t.replace('|', '，').replace('#', '').replace('*', '')
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def speak_title(inner):
    """【第三章 · 商业银行 · 错20道】 → 「第三章，商业银行，错20道。」"""
    parts = [p.strip() for p in inner.split('·') if p.strip()]
    return '，'.join(parts) + '。'


def split():
    raw = io.open(MD, encoding='utf-8').read()
    blocks = [b.strip() for b in re.split(r'\n-{3,}\n', raw)]
    segs = []
    started = False
    for b in blocks:
        # 首个【标题】之前的稿件头（h1 + 引述）不读
        if not started:
            if '【' not in b:
                continue
            started = True
        # 【标题】→ 口播转场，单独成段
        titles = re.findall(r'【([^】]*)】', b)
        for t in titles:
            segs.append(speak_title(t))
        b = re.sub(r'【[^】]*】\s*', '', b)
        txt = clean(b)
        if len(txt) < 8:
            continue
        # 按句切长段（SAPI 一次读 >800 字偶发断流），~450 字一段
        parts = re.split(r'(?<=[。！？])', txt)
        cur = ''
        for p in parts:
            if len(cur) + len(p) > 450 and cur:
                segs.append(cur)
                cur = p
            else:
                cur += p
        if cur.strip():
            segs.append(cur.strip())
    os.makedirs(WORK, exist_ok=True)
    json.dump(segs, io.open(os.path.join(WORK, 'segments.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print('分段 %d 段，总字数 %d' % (len(segs), sum(len(s) for s in segs)))


def encode(idxs, segs, out_path):
    """把指定段号合成一个 mp3，返回时长秒数。"""
    import lameenc
    pcm = bytearray()
    sr = None
    for k, i in enumerate(idxs):
        f = os.path.join(SEGS, 'seg%03d.wav' % i)
        w = wave.open(f, 'rb')
        sr = sr or w.getframerate()
        assert w.getframerate() == sr and w.getnchannels() == 1 and w.getsampwidth() == 2, f
        txt = segs[i]
        gap = 0.90 if (txt.startswith('第') or txt.startswith('开场') or txt.startswith('结尾')) else 0.28
        if k > 0:
            pcm += b'\x00\x00' * int(sr * gap)
        pcm += w.readframes(w.getnframes())
        w.close()
    enc = lameenc.Encoder()
    enc.set_bit_rate(64)
    enc.set_in_sample_rate(sr)
    enc.set_channels(1)
    enc.set_quality(3)
    mp3 = enc.encode(bytes(pcm)) + enc.flush()
    io.open(out_path, 'wb').write(mp3)
    return len(pcm) / 2.0 / sr


def _files():
    files = sorted(f for f in os.listdir(SEGS) if f.endswith('.wav'))
    if not files:
        raise SystemExit('❌ 没有 wav 段，先跑 make_podcast.ps1')
    return files


def join():
    files = _files()
    segs = json.load(io.open(os.path.join(WORK, 'segments.json'), encoding='utf-8'))
    secs = encode(range(len(files)), segs, OUT_MP3)
    print('✅ %s（%.1f MB，%d 分 %d 秒，%d 段）'
          % (OUT_MP3, os.path.getsize(OUT_MP3) / 1048576.0, secs // 60, secs % 60, len(files)))


def chapters():
    """按章切出可单听的小段：开场 / 12 章 / 结尾。"""
    files = _files()
    segs = json.load(io.open(os.path.join(WORK, 'segments.json'), encoding='utf-8'))
    marks = [i for i, t in enumerate(segs)
             if (re.match(r'^第[一二三四五六七八九十]+章，', t) and len(t) <= 30)
             or t.startswith('结尾')]
    marks = [0] + marks + [len(files)]
    out_dir = os.path.join(ROOT, 'exams', '错题本', '播客', '分章')
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for k in range(len(marks) - 1):
        a, b = marks[k], marks[k + 1]
        title = segs[a].rstrip('。')
        name = '%02d_%s.mp3' % (k, re.sub(r'[\\/:*?"<>|，]', '_', title)[:28])
        secs = encode(range(a, b), segs, os.path.join(out_dir, name))
        total += secs
        print('  %s  %d 分 %d 秒' % (name, secs // 60, secs % 60))
    print('✅ 分章 %d 个文件，合计 %d 分 %d 秒 → %s'
          % (len(marks) - 1, total // 60, int(total) % 60, out_dir))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'split'
    {'split': split, 'join': join, 'chapters': chapters}.get(cmd, split)()


if __name__ == '__main__':
    {'split': split, 'join': join}.get(sys.argv[1] if len(sys.argv) > 1 else 'split',
                                       split)()
