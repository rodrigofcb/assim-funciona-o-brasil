import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
DUR = 16.5
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

# D - A - Bm - G (triads, midi), one bar each, loop
CHORDS = [[62, 66, 69], [57, 61, 64], [59, 62, 66], [55, 59, 62]]

N = int(SR * DUR)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)

def lowpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x)

def env_adsr(n, a, d, s, r):
    e = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[na:na + nd] = np.linspace(1, s, nd)
    e[na + nd:] = s
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

# ---- pad: detuned saws per chord tone, crossfaded per bar
pad = np.zeros(N)
nbars = int(np.ceil(DUR / BAR))
for bi in range(nbars):
    ch = CHORDS[bi % 4]
    s0 = int(bi * BAR * SR); s1 = min(N, int((bi + 1) * BAR * SR) + int(0.4 * SR))
    n = s1 - s0
    tt = np.arange(n) / SR
    seg = np.zeros(n)
    for m in ch:
        f = midi(m - 12)
        for det in (-0.4, 0.4):
            ph = 2 * np.pi * f * (2 ** (det / 1200)) * tt
            seg += (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.12
    seg *= env_adsr(n, 0.35, 0.1, 0.9, 0.4)
    pad[s0:s1] += seg
pad = lowpass(pad, 900, 2)

# ---- pluck arpeggio on 8th notes
pluck = np.zeros(N)
pan = np.zeros(N)
step = BEAT / 2
k = 0
pattern = [0, 1, 2, 3, 2, 1, 2, 3]   # index into chord tones (+octave)
vel = [1.0, .7, .8, .6, .9, .6, .8, .5]
tt_step = 0.0
while tt_step < DUR:
    bi = int(tt_step // BAR) % 4
    ch = CHORDS[bi]
    tones = ch + [ch[0] + 12]
    m = tones[pattern[k % 8]] + 12
    f = midi(m)
    n = int(0.45 * SR)
    s0 = int(tt_step * SR); n = min(n, N - s0)
    if n <= 0: break
    x = np.arange(n) / SR
    note = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2 * f * x) + 0.12 * np.sin(2 * np.pi * 3 * f * x))
    note *= np.exp(-x * 9) * vel[k % 8] * 0.22
    pluck[s0:s0 + n] += note
    pan[s0:s0 + n] = 0.5 + 0.35 * np.sin(k * 1.3)
    k += 1; tt_step += step

# ---- kick (beats 1 and 3) and hat (off-beats), soft
kick = np.zeros(N); hat = np.zeros(N)
rng = np.random.default_rng(7)
b = 0.0; i = 0
while b < DUR:
    s0 = int(b * SR)
    if i % 2 == 0:
        n = int(0.22 * SR); n = min(n, N - s0)
        x = np.arange(n) / SR
        fr = 110 * np.exp(-x * 28) + 42
        kick[s0:s0 + n] += np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 14) * 0.5
    hs = int((b + BEAT / 2) * SR)
    n = int(0.035 * SR); n = min(n, N - hs)
    if n > 0:
        hat[hs:hs + n] += rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 160) * 0.05
    b += BEAT; i += 1
hat = hat - lowpass(hat, 5000, 2)   # crude highpass

# ---- mix
L = pad * 0.85 + pluck * (1 - pan) + kick + hat
R = np.roll(pad, int(0.011 * SR)) * 0.85 + pluck * pan + kick + hat
mix = np.stack([L, R], axis=1)

# fade in/out
fi = int(0.6 * SR); fo = int(1.6 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.6
wavfile.write("music.wav", SR, (mix * 32767).astype(np.int16))
print("ok", mix.shape)
