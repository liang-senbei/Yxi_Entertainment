#!/usr/bin/env python3
"""云曦节拍 · 曲子和谱面生成器（我们自己的曲子，版权归我们）

老板 2026-09-06 问「这些歌都能用吗，会不会侵权」——答案是别人的歌不能用（见 rhythm-prd.md 第 1 节）。
所以这三首是**这个脚本合成出来的**：音符、和声、鼓点全在下面的 SONGS 里写死，
渲染成 ogg，同时把**谱面**从同一份乐谱里导出来 —— 曲子和谱面天生对齐，不用手对拍。

    python3 make_songs.py <输出目录>
        <输出目录>/yx_<id>.ogg              进 App 的 res/raw
        <输出目录>/chart_<id>_<难度>.json   进 App 的 assets/charts

谱面难度：easy = 只留拍上的音（四分/八分），hard = 全部旋律音 + 部分鼓点。
"""
import json, math, os, subprocess, sys, wave
import numpy as np

SR = 44100

# ── 音高：以 A4 = 440 为基准，用 "C4" "A#3" 这种写法 ───────────────────────────
STEPS = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def hz(name):
    n, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((STEPS[n] + (octv - 4) * 12 - 9) / 12)


def env(n, a, d, s, r, sus=0.7):
    """ADSR 包络，长度 n 个采样点，a/d/r 是秒，s 是延音段长度（秒）"""
    a, d, s, r = [max(1, int(x * SR)) for x in (a, d, s, r)]
    e = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sus, d),
        np.full(s, sus),
        np.linspace(sus, 0, r),
    ])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def osc(kind, f, n, detune=0.0):
    t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    if kind == 'sine':
        w = np.sin(ph)
    elif kind == 'tri':
        w = 2 / np.pi * np.arcsin(np.sin(ph))
    elif kind == 'square':
        w = np.sign(np.sin(ph)) * 0.6 + 0.4 * np.sin(ph)      # 方波太刺，掺一点正弦
    else:                                                      # saw
        w = 2 * (t * f - np.floor(0.5 + t * f))
    if detune:
        w = 0.6 * w + 0.4 * osc(kind, f * 2 ** (detune / 1200), n)
    return w


_FIR = {}


def lowpass(x, cut, taps=63):
    """窗函数低通（np.convolve，向量化；不引 scipy）。锯齿叠出来的音色不压一道会很刺。"""
    k = _FIR.get(cut)
    if k is None:
        n = np.arange(taps) - (taps - 1) / 2
        fc = cut / SR
        k = np.sinc(2 * fc * n) * np.hamming(taps)
        k /= k.sum()
        _FIR[cut] = k
    return np.convolve(x, k, mode='same')


def reverb(x, mix=0.22):
    """三个延时抽头的廉价混响：给旋律和铺底一点空间，别让它干得像蜂鸣器。"""
    out = x.copy()
    for d, g in ((0.031, .5), (0.057, .34), (0.093, .22)):
        n = int(d * SR)
        out[n:] += x[:-n] * g * mix
    return out


# ── 乐器 ──────────────────────────────────────────────────────────────────────
def kick(n):
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 28) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def snare(n):
    t = np.arange(n) / SR
    noise = np.random.default_rng(7).normal(0, 1, n) * np.exp(-t * 22)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 26)
    return 0.7 * noise + 0.35 * tone


def hat(n, open_=False):
    t = np.arange(n) / SR
    rng = np.random.default_rng(11)
    return rng.normal(0, 1, n) * np.exp(-t * (9 if open_ else 55)) * 0.32


def bass(f, n):
    return lowpass(osc('square', f, n), 420) * env(n, .005, .05, max(0, n / SR - .25), .18, .55) * 0.9


def lead(f, n):
    body = lowpass(osc('saw', f, n, detune=9), max(2200, f * 6)) * 0.5 + osc('sine', f * 2, n) * 0.18
    return reverb(body * env(n, .008, .07, max(0, n / SR - .3), .22, .6)) * 0.42


def pad(freqs, n):
    out = np.zeros(n)
    for f in freqs:
        out += osc('saw', f, n, detune=6) * 0.3
    # 铺底压得最狠：它只负责厚度，亮的部分让给旋律
    return reverb(lowpass(out, 1500) * env(n, .35, .3, max(0, n / SR - 1.1), .45, .75), .3) * 0.22


def pluck(f, n):
    return reverb(osc('tri', f, n) * env(n, .003, .12, 0, .12, .0)) * 0.3


# ── 乐谱 ──────────────────────────────────────────────────────────────────────
# mel: (小节内第几拍, 音名, 几拍长)。拍 = 四分音符。
SONGS = [
    dict(
        id='snow', zh='初雪', bpm=96, bars=24, key='A',
        # Am - F - C - G
        chords=[['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['C3', 'E3', 'G3'], ['G3', 'B3', 'D4']],
        bassline=[0, 0, 3.5],                                   # 每小节第 1、3.5 拍
        drums='soft',
        mel=[  # (小节内起拍, 音名, 时值)；曲子会按 8 小节一段循环，主歌 / 副歌各一套
            [(0, 'A4', 1), (1, 'C5', .5), (1.5, 'B4', .5), (2, 'A4', 1), (3, 'E4', 1)],
            [(0, 'F4', 1), (1, 'A4', .5), (1.5, 'G4', .5), (2, 'F4', 2)],
            [(0, 'E4', .5), (.5, 'G4', .5), (1, 'C5', 2), (3, 'B4', 1)],
            [(0, 'D5', 1.5), (1.5, 'C5', .5), (2, 'B4', 1), (3, 'A4', 1)],
            [(0, 'C5', .5), (.5, 'E5', .5), (1, 'D5', 1), (2, 'C5', .5), (2.5, 'B4', .5), (3, 'A4', 1)],
            [(0, 'F4', .5), (.5, 'A4', .5), (1, 'C5', 1), (2, 'B4', 2)],
            [(0, 'E5', 1), (1, 'D5', .5), (1.5, 'C5', .5), (2, 'B4', 1), (3, 'G4', 1)],
            [(0, 'A4', 3), (3, 'E4', 1)],
        ],
    ),
    dict(
        id='yunxi', zh='云曦', bpm=128, bars=32, key='D',
        # Dm - B♭ - F - C
        chords=[['D3', 'F3', 'A3'], ['A#2', 'D3', 'F3'], ['F3', 'A3', 'C4'], ['C3', 'E3', 'G3']],
        bassline=[0, 1.5, 2, 3],
        drums='four',
        mel=[
            [(0, 'D5', .5), (.5, 'F5', .5), (1, 'E5', .5), (1.5, 'D5', .5), (2, 'A4', 1), (3, 'D5', 1)],
            [(0, 'A#4', .5), (.5, 'D5', .5), (1, 'F5', 1), (2, 'E5', .5), (2.5, 'D5', .5), (3, 'C5', 1)],
            [(0, 'F5', .5), (.5, 'G5', .5), (1, 'A5', 1), (2, 'F5', .5), (2.5, 'E5', .5), (3, 'D5', 1)],
            [(0, 'C5', .5), (.5, 'E5', .5), (1, 'G5', 1), (2, 'E5', 1), (3, 'C5', 1)],
            [(0, 'D5', .5), (.5, 'E5', .5), (1, 'F5', .5), (1.5, 'G5', .5), (2, 'A5', 2)],
            [(0, 'A#5', .5), (.5, 'A5', .5), (1, 'G5', .5), (1.5, 'F5', .5), (2, 'D5', 2)],
            [(0, 'F5', .5), (.5, 'A5', .5), (1, 'C6', 1), (2, 'A5', .5), (2.5, 'G5', .5), (3, 'F5', 1)],
            [(0, 'E5', .5), (.5, 'G5', .5), (1, 'C6', 1.5), (2.5, 'A5', .5), (3, 'D5', 1)],
        ],
    ),
    dict(
        id='abyss', zh='入渊', bpm=152, bars=40, key='E',
        # Em - C - G - D
        chords=[['E3', 'G3', 'B3'], ['C3', 'E3', 'G3'], ['G2', 'B2', 'D3'], ['D3', 'F#3', 'A3']],
        bassline=[0, .5, 1.5, 2, 2.5, 3.5],
        drums='drive',
        mel=[
            [(0, 'E5', .5), (.5, 'B4', .5), (1, 'E5', .5), (1.5, 'G5', .5), (2, 'F#5', .5), (2.5, 'E5', .5), (3, 'B4', 1)],
            [(0, 'C5', .5), (.5, 'E5', .5), (1, 'G5', .5), (1.5, 'E5', .5), (2, 'D5', 1), (3, 'C5', 1)],
            [(0, 'B4', .5), (.5, 'D5', .5), (1, 'G5', .5), (1.5, 'D5', .5), (2, 'B4', .5), (2.5, 'G4', .5), (3, 'D5', 1)],
            [(0, 'A4', .5), (.5, 'D5', .5), (1, 'F#5', .5), (1.5, 'A5', .5), (2, 'F#5', 1), (3, 'D5', 1)],
            [(0, 'E5', .25), (.25, 'F#5', .25), (.5, 'G5', .5), (1, 'B5', 1), (2, 'A5', .5), (2.5, 'G5', .5), (3, 'F#5', 1)],
            [(0, 'E5', .5), (.5, 'G5', .5), (1, 'C6', 1), (2, 'B5', .5), (2.5, 'A5', .5), (3, 'G5', 1)],
            [(0, 'D5', .25), (.25, 'E5', .25), (.5, 'F#5', .5), (1, 'G5', 1), (2, 'F#5', .5), (2.5, 'E5', .5), (3, 'D5', 1)],
            [(0, 'E5', .5), (.5, 'B5', .5), (1, 'E6', 1.5), (2.5, 'D6', .5), (3, 'B5', 1)],
        ],
    ),
]


def render(song):
    spb = 60.0 / song['bpm']                                   # 一拍几秒
    total = int((song['bars'] * 4 * spb + 2.5) * SR)
    mix = np.zeros(total)
    events = []                                                # 谱面用：(秒, 音高, 时长秒, 来源)

    def put(buf, at_beat, amp=1.0):
        i = int(at_beat * spb * SR)
        j = min(total, i + len(buf))
        if i < total:
            mix[i:j] += buf[:j - i] * amp

    for bar in range(song['bars']):
        b0 = bar * 4
        ch = song['chords'][bar % len(song['chords'])]
        intro = bar < 2
        outro = bar >= song['bars'] - 2
        chorus = 8 <= bar % 16 < 16

        # 铺底和弦
        put(pad([hz(x) for x in ch], int(4 * spb * SR)), b0, 0.9 if not intro else 0.6)

        # 贝斯
        if not intro:
            for bt in song['bassline']:
                put(bass(hz(ch[0]) / 2, int(max(.4, spb * .9) * SR)), b0 + bt, 0.9)

        # 鼓
        if not intro:
            style = song['drums']
            beats = {'soft': [0, 2], 'four': [0, 1, 2, 3], 'drive': [0, 1, 2, 3]}[style]
            for bt in beats:
                put(kick(int(.3 * SR)), b0 + bt, 0.95)
            for bt in ([2] if style == 'soft' else [1, 3]):
                put(snare(int(.25 * SR)), b0 + bt, 0.55)
            hats = [0.5, 1.5, 2.5, 3.5] if style == 'soft' else [x * 0.5 for x in range(8)]
            for bt in hats:
                put(hat(int(.12 * SR), open_=(bt == 3.5)), b0 + bt, 0.5)

        # 旋律：主歌用前四句，副歌用后四句；开头两小节只有铺底
        if not intro and not outro:
            line = song['mel'][(bar % 4) + (4 if chorus else 0)]
            for bt, name, dur in line:
                n = int(dur * spb * SR)
                put(lead(hz(name), n), b0 + bt, 1.0 if chorus else 0.85)
                events.append(((b0 + bt) * spb, name, dur * spb, 'mel'))
                if chorus:                                     # 副歌加一层八度上的点缀
                    put(pluck(hz(name) * 2, int(.25 * SR)), b0 + bt, 0.5)
        if outro:
            put(pad([hz(x) for x in ch], int(4 * spb * SR)), b0, 0.7)

    # 收尾：软限幅 + 淡入淡出
    mix = np.tanh(mix * 0.8) * 0.85
    fade = int(0.05 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
    return mix, events


def lines(song):
    """
    判定线的动作（老板 2026-09-06 看了 Phigros 之后要的）。

    ⚠️ **数值是我们自己定的**。参考视频量出来的是「人家怎么做」——绕线中心转、整条上下沉、
       缓入缓出、音符跟着线走——那是做法；具体转几度、沉多少、什么时候动，属于**谱面数据**，
       抄不得。所以这里按我们自己的曲子结构来：小节线上轻轻沉一下，段落转换处慢慢侧一下。
       幅度也比参考里的小（转 ±2.5° 不是 ±4°，沉 0.012 不是 0.03）—— 我们的谱是给随手玩的人打的，
       晃太狠会看不清。
    """
    spb = 60.0 / song['bpm']
    out = []
    # ① 每两小节的第一拍，线往下沉一下再弹回来（跟着鼓点，幅度很小）
    for bar in range(2, song['bars'] - 2, 2):
        t = bar * 4 * spb
        d = 0.012 if song['drums'] == 'soft' else 0.016
        out.append(dict(t=round(t, 3), dur=0.06, op='move_y', **{'from': 0.0, 'to': d}, ease='easeOut'))
        out.append(dict(t=round(t + 0.06, 3), dur=0.34, op='move_y', **{'from': d, 'to': 0.0}, ease='cubicInOut'))
    # ② 每 8 小节（段落）侧一下：往一边转，两小节后转回来。方向左右交替
    side = 1
    for bar in range(8, song['bars'] - 4, 8):
        a = 2.5 * side
        out.append(dict(t=round(bar * 4 * spb, 3), dur=0.9, op='rotate', **{'from': 0.0, 'to': a}, ease='cubicInOut'))
        out.append(dict(t=round((bar + 2) * 4 * spb, 3), dur=0.9, op='rotate', **{'from': a, 'to': 0.0}, ease='cubicInOut'))
        side = -side
    return sorted(out, key=lambda e: e['t'])


def chart(song, events, hard):
    """从乐谱直接出谱面。音高分四轨；音块类型按**乐句里的位置**来分，不是随机撒 —— 谱面要"跟着音乐"。

    四种（老板 2026-09-06 定的）：
      tick  点一下          —— 默认
      slide 长按滑          —— 长音（≥1.45 拍）
      trace 拖到隔壁轨      —— 相邻两个音**跨轨且时间很近**时，后一个变成"从前一个拖过来"
      swipe 落下时左/右滑   —— 乐句最后一个音（收尾的那下），方向按旋律走向
    easy 只留拍上的音，且**不出 trace**（拖动对新手太难）。
    """
    spb = 60.0 / song['bpm']
    raw = []
    pitches = sorted({hz(p) for _, p, _, _ in events})
    lo, hi = pitches[0], pitches[-1]
    for t, name, dur, _ in events:
        on_beat = abs((t / spb) % 1) < 1e-6
        if not hard and not on_beat:
            continue
        f = hz(name)
        lane = min(3, int((math.log2(f / lo) / max(1e-6, math.log2(hi / lo))) * 4))
        raw.append([round(t, 4), lane, dur / spb])          # 时刻 / 轨 / 时值（拍）

    raw.sort(key=lambda r: (r[0], r[1]))
    # 先去重，再按配额分配特殊音块 —— 不设配额的话，快歌里"换轨又挨得近"到处都是，
    # 一半音符会变成 trace（实测 abyss_hard 230 个里 107 个），那就不是点缀是刑罚了。
    uniq, seen = [], set()
    for t, lane, beats in raw:
        k = (round(t, 3), lane)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((t, lane, beats))

    n = len(uniq)
    # 各占一成上下，剩下的是 tick / slide。轻松难度不出 trace（拖动对新手太难），但给几个 swipe，
    # 免得四种音块新手只见过两种。
    quota = {'trace': int(n * 0.11) if hard else 0, 'swipe': int(n * (0.10 if hard else 0.06))}
    used = {'trace': 0, 'swipe': 0}
    out = []
    last_kind = None
    for i, (t, lane, beats) in enumerate(uniq):
        prev = uniq[i - 1] if i else None
        nxt = uniq[i + 1] if i + 1 < n else None
        kind, dur, dr = 'tick', 0.0, 0
        if beats >= 1.45:
            kind, dur = 'slide', round(beats * spb, 4)       # 长音 = 长按滑
        else:
            gap_after = (nxt[0] - t) / spb if nxt else 99
            # 乐句收尾（后面空一拍以上）→ swipe，方向按旋律往哪走
            if (gap_after >= 1.0 and used['swipe'] < quota['swipe'] and last_kind != 'swipe'):
                dr = 1 if (prev is None or lane >= prev[1]) else -1
                kind = 'swipe'; used['swipe'] += 1
            # 跨了两条轨、又挨得很近 → trace（从上一个拖过来）。**跨一条轨不算**，那太频繁
            # 跨轨越多、挨得越近，越像"拖过去"。放宽到一拍以内是量出来的：
            # 跨 2 轨且 ≤0.4 拍在我们这三首里一个都没有（旋律没那么跳），≤1.1 拍才有 3%。
            elif (hard and prev and 0 < t - prev[0] <= 1.1 * spb and abs(prev[1] - lane) >= 2
                  and used['trace'] < quota['trace'] and last_kind != 'trace'):
                kind, dr = 'trace', (1 if lane > prev[1] else -1)
                used['trace'] += 1
        out.append(dict(t=round(t, 4), lane=lane, type=kind, dur=dur, dir=dr))
        last_kind = kind
    return dict(song=song['id'], zh=song['zh'], bpm=song['bpm'],
                difficulty='hard' if hard else 'easy', offset=0, notes=out, lines=lines(song))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for s in SONGS:
        mix, events = render(s)
        wav = os.path.join(out, f'yx_{s["id"]}.wav')
        with wave.open(wav, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
        ogg = os.path.join(out, f'yx_{s["id"]}.ogg')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav,
                        '-c:a', 'libvorbis', '-q:a', '3', '-ar', '44100', ogg], check=True)
        os.remove(wav)
        for hard in (False, True):
            c = chart(s, events, hard)
            with open(os.path.join(out, f'chart_{s["id"]}_{c["difficulty"]}.json'), 'w') as f:
                json.dump(c, f, ensure_ascii=False, separators=(',', ':'))
            print(f'{s["zh"]:4} {c["difficulty"]:4} {len(c["notes"]):3} 个音符  '
                  f'{len(mix)/SR:.1f}s  {os.path.getsize(ogg)//1024}KB')


if __name__ == '__main__':
    main()
