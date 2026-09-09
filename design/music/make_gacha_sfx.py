#!/usr/bin/env python3
"""祈愿出货的声音 —— 跟音游那套一样，**我们自己合成，没有采样包**。

    python3 make_gacha_sfx.py <片子目录>
        读该目录下的 out_{blue,purple,gold,red}.mp4，
        给每一条按它自己的**实际时长**配一条音轨，混进去，写成 mix_*.mp4

为什么要做这个：老板给的 AI 片子**音轨是数字静音**（实测 RMS −128dB）。
一段有起有落的动画配全程静音，观感就是「没播完就被掐了」——他反馈的
「戛然而止」有一半是耳朵听出来的，不是眼睛。

一条音轨分三段，跟画面严格对齐：
    蓄力 0 → bloom      手心聚光。底噪一层慢慢开的气声 + 越来越密的碎星铃音，
                        音高整体往上爬 —— 「有什么要来了」。
    爆闪 bloom          白光那一下。一记亮铃 + 一道短促气流，是全曲最响的点。
    揭晓 bloom → 末尾   按品质给不同动机（见 MOTIF），最后 0.45 秒淡出到零。
                        ⚠️ **尾巴必须自己衰减干净**：末尾还有声音的话，
                        画面切走的那一刻会被听成「咔」的一声断，正是要修的毛病。

品质越稀有，动机的音越多、越亮、低频越足（蓝 2 音 → 红 和弦 + 低频涌）。
音阶用 A 大调五声（A C# E），四条听起来是同一个世界的东西。
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
BLOOM = 5.31          # 白光爆闪的位置（通用段从 1.06 起，到 6.62 接缝）
TAIL = 0.45           # 收尾淡出

# 音名 → 频率（A 大调五声：A C# E）
def hz(n):
    return 440.0 * 2 ** (n / 12)

A4, CS5, E5, A5, CS6, E6 = hz(0), hz(4), hz(7), hz(12), hz(16), hz(19)
A3, E4 = hz(-12), hz(-5)

# 每档：(动机音符 [(起始秒, 频率, 音量)], 低频涌的音量)
MOTIF = {
    'blue':   ([(0.02, E5, 0.34), (0.20, A5, 0.30)], 0.00),
    'purple': ([(0.02, A4, 0.30), (0.16, CS5, 0.30), (0.34, E5, 0.32)], 0.05),
    'gold':   ([(0.02, A4, 0.30), (0.14, CS5, 0.30), (0.28, E5, 0.32),
                (0.44, A5, 0.36), (0.72, CS6, 0.22)], 0.10),
    'red':    ([(0.02, A3, 0.26), (0.02, E4, 0.24), (0.02, A4, 0.28),
                (0.30, E5, 0.30), (0.52, A5, 0.34), (0.86, E6, 0.26)], 0.22),
}


def bell(n, f, amp, decay=3.2):
    """一记铃音：基频 + 几个非整数倍泛音，各自衰减。倍数取非整数才有金属感。"""
    t = np.arange(n) / SR
    x = np.zeros(n)
    for mult, w, d in ((1.0, 1.00, 1.0), (2.76, 0.42, 1.7), (5.40, 0.18, 2.6), (8.93, 0.08, 3.4)):
        x += np.sin(2 * np.pi * f * mult * t) * w * np.exp(-t * decay * d)
    a = int(0.002 * SR)                      # 2ms 软起音，去掉咔哒
    x[:a] *= np.linspace(0, 1, a)
    return x * amp


def place(track, at, x):
    """把一小段叠到总轨的 at 秒处，超出末尾就截断。"""
    i = int(at * SR)
    if i >= len(track):
        return
    n = min(len(x), len(track) - i)
    track[i:i + n] += x[:n]


def charge(track, rng):
    """蓄力：气声底 + 越来越密的碎星，整体音高往上爬。"""
    n = int(BLOOM * SR)
    t = np.arange(n) / SR
    p = t / BLOOM                                        # 0 → 1

    # 气声：白噪声过一个慢慢打开的一阶低通，音量按 p^2 涨
    cut = 400 + 5200 * p ** 2
    a = np.exp(-2 * np.pi * cut / SR)
    noise = rng.normal(0, 1, n)
    air = np.empty(n)
    y = 0.0
    for i in range(n):                                   # 一阶 IIR，系数逐样本变
        y = (1 - a[i]) * noise[i] + a[i] * y
        air[i] = y
    track[:n] += air * (p ** 2) * 0.16

    # 碎星：越往后越密，音高跟着 p 往上爬。
    # ⚠️ **开头必须疏**（老板 2026-09-07：「刚开始得得得得得很急促，放缓一点」）——
    #    一秒一颗起步，到爆闪前才密到每秒十几颗；密度是这段的紧张感来源，
    #    起手就密等于一上来把话说完，后面反而没地方涨。
    #    早期那几颗衰减也放慢（decay 随 q 变），听着是「叮——」不是「得」。
    at = 0.45
    while at < BLOOM - 0.05:
        q = at / BLOOM
        f = hz(np.interp(q, [0, 1], [7, 24])) * rng.choice([1.0, 1.5])
        place(track, at, bell(int(0.9 * SR), f, 0.05 + 0.11 * q, decay=4.0 + 5.0 * q))
        at += rng.uniform(1.0, 1.6) / (1.1 + 12 * q)

    # 低频托底：从 bloom 前 1.2 秒开始涌起来，撑住「要来了」
    m = int(1.2 * SR)
    tt = np.arange(m) / SR
    swell = np.sin(2 * np.pi * 55 * tt) * (tt / tt[-1]) ** 2 * 0.18
    place(track, BLOOM - 1.2, swell)


def bloom(track, rng):
    """白光那一下：一记亮铃 + 一道短气流。全曲最响。"""
    place(track, BLOOM - 0.01, bell(int(2.2 * SR), A5, 0.46, decay=1.6))
    place(track, BLOOM - 0.01, bell(int(1.6 * SR), E6, 0.22, decay=2.4))
    m = int(0.35 * SR)
    tt = np.arange(m) / SR
    place(track, BLOOM - 0.06, rng.normal(0, 1, m) * np.exp(-tt * 14) * 0.20)


def reveal(track, kind, dur):
    """揭晓段的动机。剩多长就写多长，尾巴留给 fade。"""
    notes, sub = MOTIF[kind]
    room = dur - BLOOM
    for at, f, amp in notes:
        if at < room:
            place(track, BLOOM + at, bell(int(2.6 * SR), f, amp, decay=1.5))
    if sub > 0:
        m = int(min(1.4, room) * SR)
        tt = np.arange(m) / SR
        place(track, BLOOM, np.sin(2 * np.pi * 82 * tt) * np.exp(-tt * 2.2) * sub)


def build(kind, dur, seed):
    rng = np.random.default_rng(seed)
    track = np.zeros(int(dur * SR))
    charge(track, rng)
    bloom(track, rng)
    reveal(track, kind, dur)
    track = np.tanh(track * 1.25) * 0.86                 # 软限幅，别削顶
    f = int(TAIL * SR)
    track[-f:] *= np.linspace(1, 0, f) ** 1.5            # ⚠️ 尾巴衰减干净，画面切走时不能还有声
    return track


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    for i, kind in enumerate(('blue', 'purple', 'gold', 'red')):
        mp4 = os.path.join(d, f'out_{kind}.mp4')
        dur = float(subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4],
            capture_output=True, text=True, check=True).stdout.strip())

        x = build(kind, dur, seed=11 + i)
        assert abs(len(x) / SR - dur) < 0.02, '音轨得跟画面一样长'
        assert abs(x[-1]) < 1e-3, '尾巴没衰减干净，切走会听成咔哒'
        assert np.max(np.abs(x)) < 1.0, '削顶了'

        wav = os.path.join(d, f'a_{kind}.wav')
        with wave.open(wav, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())

        out = os.path.join(d, f'mix_{kind}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4, '-i', wav,
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k', '-shortest',
                        '-movflags', '+faststart', out], check=True)
        os.remove(wav)
        print(f'{kind:7s} {dur:5.2f}s  峰值 {np.max(np.abs(x)):.2f}  '
              f'{os.path.getsize(out) // 1024}KB')


if __name__ == '__main__':
    main()
