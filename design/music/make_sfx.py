#!/usr/bin/env python3
"""云曦节拍 · 打击音效（同样是我们自己合成的，没有采样包）

    python3 make_sfx.py <输出目录>
        yx_tick.ogg / yx_slide.ogg / yx_trace.ogg / yx_swipe.ogg

**四种音块各一个音**（老板 2026-09-06：「四种音块的点击音效要各不相同」），跟四种配色配形对上：
    tick  淡橙 · 点一下      → 短促的亮击（22ms）——最干脆的那个，一局响得最多，不能烦
    slide 浅蓝 · 长按滑      → 带一点气声的软起音（55ms），像"接住"而不是"敲中"
    trace 樱粉 · 拖动换位    → 向上滑的小音高（45ms），耳朵能听出"挪过去了"
    swipe 浅绿 · 左右划      → 一记短促的风声（40ms），高频扫过
四个都在同一个家族里（都很短、都不刺耳），只在音色上分 —— 不然连打起来像四个不同的游戏。
「完美/不错」仍然靠音量和速率分，不再做第二套文件。

音色参考竞品：Phigros 是金属感的「嗒」，Cytus 偏电子。我们的 App 整体克制、偏玻璃质感，
所以做成**短促的木质 + 一点金属泛音**：不吵，连打三十下也不烦。
"""
import os, subprocess, sys, wave
import numpy as np


def _lowpass(x, cut, taps=41):
    n = np.arange(taps) - (taps - 1) / 2
    k = np.sinc(2 * cut / SR * n) * np.hamming(taps)
    return np.convolve(x, k / k.sum(), mode='same')

SR = 44100


def _env(n, decay):
    t = np.arange(n) / SR
    return np.exp(-t * decay)


def tick():
    """点一下：最短最亮的那个。参照实测的打击音（4ms 衰到 10%、三成能量在 6kHz 以上）。"""
    n = int(0.022 * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(5)
    noise = _lowpass(rng.normal(0, 1, n), 11000) * _env(n, 420) * 0.50
    ping = (np.sin(2 * np.pi * 2600 * t) * 0.34 + np.sin(2 * np.pi * 5200 * t) * 0.17) * _env(n, 300)
    body = np.sin(2 * np.pi * 620 * t) * _env(n, 220) * 0.30
    return _finish(noise + ping + body)


def slide():
    """长按滑：软一点、长一点，像"接住"。起音有 6 毫秒的爬升，不是一下子撞上去。"""
    n = int(0.055 * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(11)
    air = _lowpass(rng.normal(0, 1, n), 4200) * _env(n, 90) * 0.30
    body = (np.sin(2 * np.pi * 430 * t) * 0.34 + np.sin(2 * np.pi * 860 * t) * 0.16) * _env(n, 110)
    x = air + body
    a = int(0.006 * SR)
    x[:a] *= np.linspace(0, 1, a)                      # 软起音：这是"按住"不是"敲中"
    return _finish(x)


def trace():
    """拖动换位：一个向上滑的小音高，耳朵能听出"挪过去了"。"""
    n = int(0.045 * SR); t = np.arange(n) / SR
    f = 520 + 900 * (t / t[-1]) ** 1.6                 # 520 → 1420Hz 往上滑
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) * 0.42 + np.sin(2 * ph) * 0.12) * _env(n, 130)
    rng = np.random.default_rng(3)
    x += _lowpass(rng.normal(0, 1, n), 7000) * _env(n, 300) * 0.12
    return _finish(x)


def swipe():
    """左右划：一记短促的风声，高频扫过。"""
    n = int(0.040 * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(17)
    raw = rng.normal(0, 1, n)
    # 由亮到暗扫一遍：分两段各压一次，拼起来就有"刷"的走向
    half = n // 2
    x = np.concatenate([_lowpass(raw[:half], 12000), _lowpass(raw[half:], 5000)]) * _env(n, 200) * 0.55
    x += np.sin(2 * np.pi * 1800 * t) * _env(n, 260) * 0.14
    a = int(0.002 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return _finish(x)


def _finish(x):
    x = np.tanh(x * 1.5) * 0.85
    a = int(0.0008 * SR)
    x[:a] *= np.linspace(0, 1, a)
    r = int(0.003 * SR)
    x[-r:] *= np.linspace(1, 0, r)                     # 收尾淡出，别留咔哒
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in (('tick', tick), ('slide', slide), ('trace', trace), ('swipe', swipe)):
        x = fn()
        wav = os.path.join(out, f'yx_{name}.wav')
        with wave.open(wav, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
        ogg = os.path.join(out, f'yx_{name}.ogg')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav,
                        '-c:a', 'libvorbis', '-q:a', '4', ogg], check=True)
        os.remove(wav)
        F = np.abs(np.fft.rfft(x * np.hanning(len(x)))); f = np.fft.rfftfreq(len(x), 1 / SR)
        print(f'yx_{name}.ogg  {len(x)/SR*1000:.0f}ms  {os.path.getsize(ogg)}B  '
              f'谱重心 {int((F*f).sum()/F.sum())}Hz  >6kHz {float(F[f>=6000].sum()/F.sum()):.0%}')


if __name__ == '__main__':
    main()
