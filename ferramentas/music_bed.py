"""Cama musical procedural, escura e contínua (pad + pulso grave + pluck esparso).

Uso: python3 music_bed.py <pasta> [--bpm 84] [--key B] [--in 2.0]
Gera <pasta>/out/music.wav com duração TL.end + 0.5, entrando em --in segundos (fade de 1,5 s).
"""
import sys, json, re, pathlib, argparse
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--bpm", type=float, default=84)
ap.add_argument("--in", dest="tin", type=float, default=None); a = ap.parse_args()
folder = pathlib.Path(a.folder).resolve()
TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", (folder / "timeline.js").read_text(encoding="utf-8")).rstrip().rstrip(";"))
SR = 44100; DUR = TL["end"] + 0.5; N = int(SR * DUR); t = np.arange(N) / SR
BEAT = 60 / a.bpm; BAR = 4 * BEAT
TIN = a.tin if a.tin is not None else TL.get("music_in", 0)
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc / (SR / 2), btype="low", output="sos"), x)
# Si menor: Bm  G  D  A  | Bm  G  Em  F#m  (progressão de 8 compassos)
CH = [[59, 62, 66], [55, 59, 62], [50, 54, 57], [57, 61, 64], [59, 62, 66], [55, 59, 62], [52, 55, 59], [54, 57, 61]]

pad = np.zeros(N)
for bi in range(int(np.ceil(DUR / BAR))):
    s0 = int(bi * BAR * SR); s1 = min(N, int((bi + 1) * BAR * SR) + int(0.8 * SR)); n = s1 - s0; tt = np.arange(n) / SR
    seg = np.zeros(n)
    for m in CH[bi % 8]:
        for det, octv in ((-5, -12), (5, -12), (0, 0)):
            f = midi(m + octv) * 2 ** (det / 1200)
            seg += (2 * ((f * tt) % 1) - 1) * (0.07 if octv else 0.035)
    e = np.ones(n); fa = int(0.6 * SR); e[:fa] = np.linspace(0, 1, fa); e[-int(0.8 * SR):] *= np.linspace(1, 0, int(0.8 * SR))
    pad[s0:s1] += seg * e
# filtro que "respira" devagar
cut = 500 + 300 * np.sin(2 * np.pi * t / 9)
blk = int(0.02 * SR); out = np.zeros(N)
for i in range(0, N, blk):
    out[i:i + blk] = lp(pad[max(0, i - 4 * blk):i + blk], float(cut[i]))[-min(blk, N - i):]
pad = out

# pulso grave suave nos tempos 1 e 3
sub = np.zeros(N); b = 0.0; i = 0
while b < DUR:
    if i % 2 == 0:
        s0 = int(b * SR); n = min(int(0.5 * SR), N - s0); x = np.arange(n) / SR
        root = midi(CH[int(b // BAR) % 8][0] - 24)
        sub[s0:s0 + n] += np.sin(2 * np.pi * root * x) * np.exp(-x * 7) * 0.5
    b += BEAT; i += 1

# pluck esparso (oitava alta), 1 nota a cada 2 tempos, com eco
pl = np.zeros(N); k = 0; tt_ = 0.0; pat = [0, 2, 1, 2, 0, 1, 2, 1]
while tt_ < DUR:
    ch = CH[int(tt_ // BAR) % 8]; f = midi(ch[pat[k % 8]] + 12)
    s0 = int(tt_ * SR); n = min(int(1.2 * SR), N - s0)
    if n <= 0: break
    x = np.arange(n) / SR
    note = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-x * 4) * 0.16
    pl[s0:s0 + n] += note
    e0 = s0 + int(BEAT * 0.75 * SR); ne = min(n, N - e0)
    if ne > 0: pl[e0:e0 + ne] += note[:ne] * 0.4
    k += 1; tt_ += 2 * BEAT

L = pad + sub + pl * 0.8; R = np.roll(pad, int(0.013 * SR)) + sub + pl * 1.0
mix = np.stack([L, R], 1)
# entrada em TIN com fade de 1,5 s; saída em 1,5 s
g = np.clip((t - TIN) / 1.5, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1)
mix *= g[:, None]
mix /= np.abs(mix).max() + 1e-9; mix *= 0.6
(folder / "out").mkdir(exist_ok=True)
wavfile.write(folder / "out" / "music.wav", SR, (mix * 32767).astype(np.int16)); print("ok music.wav", DUR, "s, entra em", TIN, "s")
