"""Sonoplastia procedural a partir de timeline.js.

Uso: python3 sfx.py <pasta>   -> <pasta>/out/sfx.wav (estéreo, 44.1 kHz, duração TL.end + 0.5)

Sons: tick (clique curto), pop (entrada de título), impact (grave + ar), thrum (zumbido grave que acende algo),
whoosh (ar passando, para transições), fill (trem de tiques ascendentes para preenchimento), sweep (varredura lenta).
"""
import sys, json, re, pathlib
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

folder = pathlib.Path(sys.argv[1]).resolve()
TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", (folder / "timeline.js").read_text(encoding="utf-8")).rstrip().rstrip(";"))
SR = 44100
N = int((TL["end"] + 0.5) * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(3)

def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"), x)
def lp(x, fc, order=2):
    return sosfilt(butter(order, fc / (SR / 2), btype="low", output="sos"), x)
def env(n, a, d, curve=6.0):
    """ataque linear de a s, depois decaimento exponencial com constante d s"""
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / d)
    return e
def sweep_noise(n, f0, f1, q=1.0):
    """ruído com passa-banda cujo centro desliza de f0 a f1 (em blocos de 10 ms)"""
    x = rng.normal(0, 1, n); out = np.zeros(n); blk = int(0.01 * SR)
    for i in range(0, n, blk):
        k = i / n; fc = f0 * (f1 / f0) ** k; lo, hi = fc / (1 + q), min(fc * (1 + q), SR / 2 - 100)
        out[i:i + blk] = bp(x[max(0, i - blk):i + blk], lo, hi)[-min(blk, n - i):]
    return out

def tick(f=1400):
    n = int(0.045 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * env(n, 0.001, 0.008) + rng.normal(0, .3, n) * env(n, 0.0005, 0.002)) * 0.5
def pop():
    n = int(0.16 * SR); t = np.arange(n) / SR; f = 520 * np.exp(-t * 22) + 180
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.045) + bp(rng.normal(0, 1, n), 800, 5000) * env(n, 0.001, 0.012) * 0.6) * 0.7
def impact():
    n = int(0.9 * SR); t = np.arange(n) / SR; f = 95 * np.exp(-t * 9) + 46
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.004, 0.15)
    air = lp(rng.normal(0, 1, n), 900) * env(n, 0.002, 0.06)
    return (body * 0.9 + air * 0.5) * 0.95
def thrum():
    n = int(1.4 * SR); t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 62 * t) + 0.5 * np.sin(2 * np.pi * 124 * t + 1) + 0.25 * np.sin(2 * np.pi * 186 * t)) * (1 + 0.25 * np.sin(2 * np.pi * 7 * t))
    shimmer = bp(rng.normal(0, 1, n), 2500, 7000) * env(n, 0.3, 0.3) * 0.08
    return (tone * env(n, 0.08, 0.45) * 0.45 + shimmer)
def whoosh():
    n = int(0.55 * SR)
    return sweep_noise(n, 250, 3200, 0.8) * env(n, 0.22, 0.09) * 0.9
def sweep():
    n = int(2.1 * SR); t = np.arange(n) / SR
    base = bp(rng.normal(0, 1, n), 500, 1800) * (0.5 - 0.5 * np.cos(2 * np.pi * t / (n / SR)))  # sino no tempo
    return base * 0.35
def fill(opts=None):
    o = {**TL.get("fill", {}), **(opts or {})}; k, dt = o.get("ticks", 6), o.get("dt", 0.1)
    n = int((k * dt + 0.1) * SR); out = np.zeros(n)
    for i in range(k):
        s = tick(900 * (1.09 ** i)); o = int(i * dt * SR); out[o:o + len(s)] += s * (0.7 + 0.3 * i / k)
    return out

BANK = {"tick": tick, "pop": pop, "impact": impact, "thrum": thrum, "whoosh": whoosh, "sweep": sweep, "fill": fill}
PAN = {"whoosh": None, "sweep": "RL"}  # whoosh: pan aleatório por evento; sweep: direita→esquerda

def place(sig, t, pan=0.0, move=None):
    o = int(t * SR); n = min(len(sig), N - o)
    if n <= 0: return
    sig = sig[:n]
    if move is None:
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        L[o:o + n] += sig * gl; R[o:o + n] += sig * gr
    else:
        p = np.linspace(move[0], move[1], n); L[o:o + n] += sig * np.cos((p + 1) * np.pi / 4); R[o:o + n] += sig * np.sin((p + 1) * np.pi / 4)

for ev in TL["sfx"]:
    beat, kind = ev[0], ev[1]; opts = ev[2] if len(ev) > 2 else None
    t = TL["beats"][beat]; sig = BANK[kind](opts) if kind == "fill" else BANK[kind]()
    if kind == "whoosh": d = rng.choice([-1, 1]); place(sig, t, move=(-0.8 * d, 0.8 * d))
    elif kind == "sweep": place(sig, t, move=(0.8, -0.8))
    elif kind in ("thrum",): place(sig, t, pan=-0.35 if "pres" in beat else (0.35 if "cong" in beat else 0))
    else: place(sig, t, pan=rng.uniform(-0.15, 0.15))

# riser opcional: ruído subindo + drone grave crescente durante a janela TL.riser
if TL.get("riser"):
    t0, t1 = TL["riser"]; n = int((t1 - t0) * SR); tt = np.arange(n) / SR; k = tt / (t1 - t0)
    ris = sweep_noise(n, 120, 2600, 0.7) * (k ** 1.6) * 0.5
    drone = np.sin(2 * np.pi * (38 + 14 * k) * tt) * (k ** 2) * 0.35
    place(ris + drone, t0, pan=0.0)
mix = np.stack([L, R], 1)
peak = np.abs(mix).max(); mix = mix / peak * 0.8 if peak > 0 else mix
(folder / "out").mkdir(exist_ok=True)
wavfile.write(folder / "out" / "sfx.wav", SR, (mix * 32767).astype(np.int16))
print("ok sfx.wav", round(N / SR, 2), "s,", len(TL["sfx"]), "eventos")
