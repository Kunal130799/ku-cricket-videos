import numpy as np, wave

import sys
SR, DUR, BPM = 44100, float(sys.argv[1]), 104
N = int(SR * DUR)
t = np.arange(N) / SR
beat = 60 / BPM
out = np.zeros(N)

def f(m): return 440 * 2 ** ((m - 69) / 12)

def env(n, a=0.01, r=0.3):
    e = np.ones(n); ai = min(int(a * SR), n); ri = min(int(r * SR), n)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e

def add(start, length, midi, amp, kind="sine", a=0.01, r=0.3):
    s = int(start * SR); n = min(int(length * SR), N - s)
    if n <= 0: return
    tt = np.arange(n) / SR; fr = f(midi)
    if kind == "pad":
        w = sum(np.sin(2 * np.pi * fr * (1 + d) * tt) for d in (-0.003, 0, 0.003)) / 3
        w += 0.3 * np.sin(2 * np.pi * fr * 2 * tt)
    elif kind == "pluck":
        w = (np.sin(2 * np.pi * fr * tt) + 0.4 * np.sin(2 * np.pi * fr * 2 * tt)) * np.exp(-tt * 5)
    elif kind == "bass":
        w = np.sin(2 * np.pi * fr * tt) + 0.2 * np.sin(2 * np.pi * fr * 3 * tt)
    out[s:s + n] += amp * w * env(n, a, r)

# I - V - vi - IV in C major, one chord per 4 beats
chords = [[60, 64, 67], [55, 59, 62, 67], [57, 60, 64], [53, 57, 60, 65]]
bars = int(DUR / (4 * beat)) + 1
for b in range(bars):
    ch = chords[b % 4]; st = b * 4 * beat
    for m in ch: add(st, 4 * beat + 0.2, m, 0.07, "pad", a=0.4, r=0.6)
    add(st, 2 * beat, ch[0] - 24, 0.22, "bass", a=0.02, r=0.2)
    add(st + 2 * beat, 2 * beat, ch[0] - 24, 0.18, "bass", a=0.02, r=0.2)
    arp = ch + [ch[1] + 12]
    for i in range(8):
        add(st + i * beat / 2, beat, arp[i % len(arp)] + 12, 0.10, "pluck", r=0.2)

# soft kick + hat
for k in range(int(DUR / beat) + 1):
    s = int(k * beat * SR); n = min(int(0.25 * SR), N - s)
    if n > 0:
        tt = np.arange(n) / SR
        out[s:s + n] += 0.35 * np.sin(2 * np.pi * (50 + 80 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
    s2 = int((k + 0.5) * beat * SR); n2 = min(int(0.05 * SR), N - s2)
    if n2 > 0:
        out[s2:s2 + n2] += 0.04 * np.random.randn(n2) * np.exp(-np.arange(n2) / SR * 80)

# fade in/out, normalize
fi, fo = int(0.8 * SR), int(1.5 * SR)
out[:fi] *= np.linspace(0, 1, fi); out[-fo:] *= np.linspace(1, 0, fo)
out = out / np.max(np.abs(out)) * 0.8
# simple stereo widen
L = out; R = np.roll(out, int(0.012 * SR))
data = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print("ok")
