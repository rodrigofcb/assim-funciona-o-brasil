"""Trilha original por cena, tocada com amostras de violão de náilon e amarrada aos tempos de timeline.js.

Uso: python3 trilha.py <pasta> [--out music.wav] [--bpm 72]
Linguagem: vocabulário do choro/valsa (baixaria, arpejo p-i-m-a, aproximação cromática, bordão), em andamento lento,
com silêncio ao redor dos impactos para a sonoplastia respirar. Seções escolhidas pelos beats existentes na timeline
(gancho → mergulho → Praça → "Os dois" → Esplanada → Legislativo → holofote). Beats ausentes são ignorados.
"""
import sys, json, re, pathlib, argparse, functools, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--out", default="music.wav"); ap.add_argument("--bpm", type=float, default=72)
ap.add_argument("--gain", type=float, default=0.7); a = ap.parse_args()
folder = pathlib.Path(a.folder).resolve()
TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", (folder / "timeline.js").read_text(encoding="utf-8")).rstrip().rstrip(";"))
B = TL["beats"]; END = TL["end"] + 0.5
SR = 44100; N = int((END + 3) * SR); L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(17)
SAMPLES = pathlib.Path(__file__).resolve().parent.parent / "musica" / "samples" / "nylon"
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
BEAT = 60 / a.bpm

@functools.lru_cache(maxsize=None)
def sample(m):
    m = int(min(108, max(21, m))); name = f"{NAMES[m % 12]}{m // 12 - 1}"; npy = SAMPLES / f"{name}.npy"
    if npy.exists(): return np.load(npy)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(SAMPLES / f"{name}.mp3"), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy(); i0 = int(np.argmax(np.abs(x) > 0.004)); x = x[max(0, i0 - 20):]; np.save(npy, x); return x
def note(m, vel, dur, harmonic=False):
    x = sample(m); n = min(len(x), int((dur + 0.5) * SR)); y = x[:n].copy()
    k0 = int(dur * SR)
    if k0 < n: y[k0:] *= np.exp(-np.arange(n - k0) / (0.08 * SR))
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    if harmonic:  # "harmônico": tira o ataque e deixa só o corpo doce
        y = sosfilt(butter(2, 2200 / (SR / 2), btype="low", output="sos"), y); y[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))
    return y * (0.2 + 0.8 * (vel / 127) ** 1.4)

# janelas de silêncio em volta dos impactos
IMPACTS = [B[k] for k in ("brasil", "praca", "osdois", "pres", "cong") if k in B]
def clear(t): return all(not (b - 0.06 <= t <= b + 0.28) for b in IMPACTS)
def place(sig, t, pan=0.0):
    o = max(0, int(t * SR)); n = min(len(sig), N - o)
    if n <= 0: return
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); L[o:o + n] += sig[:n] * gl; R[o:o + n] += sig[:n] * gr
def play(m, t, vel=60, dur=1.0, pan=0.0, harmonic=False, force=False):
    if not force and not clear(t): return
    place(note(m, vel * (0.92 + 0.16 * rng.random()), dur, harmonic), t + rng.normal(0, 0.008), pan)
def strum(chord, t, vel=62, dur=1.6, pan=0.25, spread=0.014):
    for j, m in enumerate(chord): play(m, t + j * spread, vel * (0.85 + 0.15 * j / len(chord)), dur, pan)

# harmonia (D maior): D  Bm  G  A7  |  Em  A7  D
D = [50, 57, 62, 66]; Bm = [47, 54, 59, 62]; G = [43, 55, 59, 62]; A7 = [45, 55, 61, 64]; Em = [40, 52, 59, 64]
def arp(chord, t0, t1, step, vel=52, pan=0.1, thin=1.0, add_oct=True):
    """arpejo p-i-m-a subindo e descendo, dentro de [t0, t1)"""
    tones = chord + ([chord[1] + 12] if add_oct else []); seq = tones + tones[-2:0:-1]; t = t0; i = 0
    while t < t1:
        if rng.random() < thin: play(seq[i % len(seq)], t, vel * (1.0 if i % len(seq) == 0 else 0.85), step * 2.2, pan)
        t += step; i += 1
def baixaria(t0, t1, roots, vel=58):
    """baixo caminhando em semínimas: tônica, quinta, e cromatismo rumo à próxima tônica"""
    t = t0; i = 0
    while t < t1:
        r = roots[(i // 2) % len(roots)]; nxt = roots[(i // 2 + 1) % len(roots)]
        if i % 2 == 0: play(r, t, vel, BEAT * 1.1, pan=-0.15)
        else:
            play(r + 7 if rng.random() < 0.6 else r + 4, t, vel * 0.8, BEAT * 0.6, pan=-0.15)
            appr = nxt + (1 if rng.random() < 0.5 else -1); play(appr, t + BEAT * 0.5, vel * 0.7, BEAT * 0.5, pan=-0.15)
        t += BEAT; i += 1
def motif(t, base=69, vel=70, pan=0.05):
    """assinatura: subida cromática até a tônica, salto de terça e repouso"""
    offs = [0, .22, .44, .66, .88, 1.5, 2.0]
    for k, (m, d) in enumerate([(base, .22), (base + 2, .22), (base + 3, .22), (base + 4, .22), (base + 5, .7), (base + 9, .5), (base + 12, 1.6)]):
        play(m, t + offs[k], vel * (0.8 + 0.2 * (k / 6)), d + 0.3, pan, force=True)

g = lambda k, d=None: B.get(k, d)
# --- 1) gancho: silêncio; depois do impacto, um harmônico isolado
if g("brasil") is not None: play(74, g("brasil") + 0.5, 48, 2.5, 0.0, harmonic=True, force=True)
# --- 2) mergulho (até a Praça): bordões graves espaçados + harmônicos, sem pulso
t0, t1 = g("brasil", 0) + 1.0, g("praca", 5.2)
t = t0; k = 0
while t < t1 - 0.3:
    play([38, 45, 38, 43][k % 4], t, 50, 2.8, -0.1);
    if k % 2 == 1: play([69, 74, 78][k % 3], t + BEAT, 44, 2.0, 0.15, harmonic=True)
    t += 2 * BEAT; k += 1
# --- 3) Praça (presidente / Congresso): arpejo em D, ralo, que encorpa quando o Congresso acende
pr, cg, s1o = g("pres", t1 + 1.2), g("cong", t1 + 2.7), g("s1out", t1 + 4.7)
arp(D, t1 + 0.4, pr, BEAT / 2, vel=48, thin=0.6)
arp(G, pr, cg, BEAT / 2, vel=50, thin=0.8)
arp(A7, cg, s1o - 0.2, BEAT / 2, vel=54, thin=1.0)
# --- 4) "Os dois": acorde cheio no impacto e a assinatura; segundo acorde em "mas"
if g("osdois") is not None:
    strum(D, g("osdois") + 0.05, vel=66, dur=2.4)
    motif(g("osdois") + 0.35)
    if g("mas") is not None: strum(Bm, g("mas") + 0.05, vel=58, dur=2.0);
# --- 5) Esplanada (Executivo administra): baixaria + acordes em contratempo, acento em cada ministério
ex, s2b = g("exec", g("s2aout", 12.2) + 1.0), g("s2bout", 17.9)
if ex is not None:
    baixaria(ex, s2b - 0.3, [38, 43, 45, 38], vel=56)
    t = ex + BEAT * 0.5; i = 0
    while t < s2b - 0.6:
        strum([D, G, A7, D][(i // 2) % 4][1:], t, vel=40, dur=0.35, pan=0.35, spread=0.01); t += BEAT; i += 1
    for k, m in (("din", 74), ("obr", 78), ("ser", 81)):
        if g(k) is not None: play(m, g(k) + 0.03, 72, 1.2, 0.0, force=True)
# --- 6) Legislativo: Em → A7 arpejo lento; intervalos em "cria" e "fiscaliza"
lg, bm = g("legis", s2b + 0.8), g("beam", s2b + 3.2)
arp(Em, lg, bm, BEAT, vel=46, thin=0.7, add_oct=False)
for k, iv in (("cria", (71, 74)), ("fisc", (69, 73))):
    if g(k) is not None: play(iv[0], g(k) + 0.03, 64, 1.4, -0.1, force=True); play(iv[1], g(k) + 0.05, 60, 1.4, 0.1, force=True)
# --- 7) holofote → fim: a assinatura uma oitava acima sobre acorde de D, e deixa soar
if g("beam") is not None:
    strum(D, g("beam") + 0.2, vel=60, dur=3.5); motif(g("beam") + 0.6, base=81, vel=64)
    arp(D, g("beam") + 3.0, END - 1.0, BEAT, vel=44, thin=0.6)

# sala pequena, corte de sub-grave, normalização
n = int(0.9 * SR); ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6); ir = sosfilt(butter(2, 4500 / (SR / 2), btype="low", output="sos"), ir); ir /= np.abs(ir).sum() / 1.4
wetL, wetR = fftconvolve(L, ir)[:N], fftconvolve(R, ir)[:N]; L = L + 0.18 * wetR; R = R + 0.18 * wetL
hp = butter(2, 55 / (SR / 2), btype="high", output="sos"); L = sosfilt(hp, L); R = sosfilt(hp, R)
mix = np.stack([L, R], 1)[:int(END * SR)]; tt = np.arange(len(mix)) / SR
mix *= np.clip((END - tt) / 1.8, 0, 1)[:, None]
mix /= (np.abs(mix).max() + 1e-9); mix *= a.gain
(folder / "out").mkdir(exist_ok=True); wavfile.write(folder / "out" / a.out, SR, (mix * 32767).astype(np.int16))
print("ok", folder / "out" / a.out, round(END, 1), "s")
