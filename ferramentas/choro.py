"""Trilha em linguagem de choro, sintetizada: violão de náilon por modelo físico (corda pulsada, Karplus-Strong estendido),
baixaria de 7 cordas, acordes em contratempo e pandeiro discreto. Composição original em Ré maior, 2/4.

Uso: python3 choro.py <pasta> [--bpm 92] [--dur 20] [--in 0.0] [--out music.wav]
Gera <pasta>/out/<out> (estéreo 44.1 kHz). Se <pasta>/timeline.js existir e --dur não for dado, usa TL.end + 0.5 e TL.music_in.
"""
import sys, json, re, pathlib, argparse, math
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--bpm", type=float, default=92)
ap.add_argument("--dur", type=float, default=None); ap.add_argument("--in", dest="tin", type=float, default=None); ap.add_argument("--out", default="music.wav")
a = ap.parse_args(); folder = pathlib.Path(a.folder).resolve()
TL = None
tl = folder / "timeline.js"
if tl.exists(): TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", tl.read_text(encoding="utf-8")).rstrip().rstrip(";"))
DUR = a.dur if a.dur is not None else (TL["end"] + 0.5 if TL else 20.0)
TIN = a.tin if a.tin is not None else (TL.get("music_in", 0.0) if TL else 0.0)
SR = 44100; N = int(SR * (DUR + 2.0)); rng = np.random.default_rng(11)
BEAT = 60.0 / a.bpm; S16 = BEAT / 4           # semínima e semicolcheia (compasso 2/4 = 2 tempos = 8 semicolcheias)
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc / (SR / 2), btype="low", output="sos"), x)

# ---------- corda pulsada (Karplus-Strong com perda ajustável, posição de palheta e decaimento por frequência)
def pluck(f0, dur, bright=0.55, pick=0.22, level=1.0):
    Np = int(round(SR / f0)); n_per = int(dur * f0) + 2
    ex = rng.uniform(-1, 1, Np)
    ex = lp(ex, 1200 + 6000 * bright)                            # excitação mais escura = náilon
    k = max(1, int(pick * Np)); ex = ex - np.roll(ex, k)          # filtro pente da posição da palheta
    ex /= (np.abs(ex).max() + 1e-9)
    buf = ex.copy(); out = np.empty(Np * n_per); g = 0.996 - 0.004 * (f0 / 440)   # cordas agudas morrem antes
    rho = 0.5 + 0.3 * (1 - bright)                                 # mais filtragem no laço = som mais redondo
    for i in range(n_per):
        out[i * Np:(i + 1) * Np] = buf
        buf = g * ((1 - rho) * buf + rho * np.roll(buf, 1))
    # afinação exata: reamostra de Np para SR/f0 real
    exact = SR / f0; idx = np.arange(0, len(out) - 1, Np / exact); y = np.interp(idx, np.arange(len(out)), out)
    n = int(dur * SR); y = y[:n] if len(y) >= n else np.pad(y, (0, n - len(y)))
    env = np.ones(n); fo = int(0.03 * SR); env[-fo:] *= np.linspace(1, 0, fo); att = int(0.002 * SR); env[:att] *= np.linspace(0, 1, att)
    return y * env * level
# corpo do violão: resposta ao impulso sintética (modos de caixa + ar)
def body_ir():
    n = int(0.25 * SR); t = np.arange(n) / SR; ir = np.zeros(n)
    for f, amp, dec in ((98, 0.55, 18), (195, 0.5, 22), (410, 0.42, 30), (610, 0.32, 40), (1300, 0.26, 60), (2400, 0.16, 80)):
        ir += amp * np.sin(2 * np.pi * f * t) * np.exp(-t * dec)
    ir += lp(rng.normal(0, 1, n), 2500) * np.exp(-t * 70) * 0.25
    ir[0] += 3.5; return ir / np.abs(ir).sum() * 6
IR = body_ir()
def reverb_ir():
    n = int(1.1 * SR); t = np.arange(n) / SR; ir = rng.normal(0, 1, n) * np.exp(-t * 4.5); ir = lp(ir, 5000); return ir / np.abs(ir).sum() * 1.6
RIR = reverb_ir()

# ---------- partitura (semicolcheias; 1 compasso = 8 posições). Notas MIDI: D4=62.
# Harmonia (16 compassos, parte A): D D A7 A7 A7 A7 D D | D7 G Gm D B7 Em A7 D
CH = ["D", "D", "A7", "A7", "A7", "A7", "D", "D", "D7", "G", "Gm", "D", "B7", "Em", "A7", "D"]
VOIC = {"D": [50, 57, 62, 66], "A7": [45, 55, 61, 64], "D7": [50, 57, 60, 66], "G": [43, 55, 59, 62], "Gm": [43, 55, 58, 62],
        "B7": [47, 57, 63, 66], "Em": [40, 55, 59, 64]}
ROOT = {"D": 38, "A7": 33, "D7": 38, "G": 31, "Gm": 31, "B7": 35, "Em": 28}
FIFTH = {"D": 45, "A7": 40, "D7": 45, "G": 38, "Gm": 38, "B7": 42, "Em": 35}
# melodia: lista de (nota, duração em semicolcheias) por compasso; 0 = pausa
MEL = [
 [(69,1),(71,1),(73,1),(74,1),(78,2),(76,1),(74,1)],
 [(73,1),(74,1),(76,1),(78,1),(81,4)],
 [(79,1),(78,1),(76,1),(74,1),(73,2),(76,2)],
 [(79,1),(78,1),(76,1),(73,1),(69,4)],
 [(76,1),(77,1),(78,1),(79,1),(81,2),(79,1),(78,1)],
 [(76,1),(74,1),(73,1),(71,1),(73,4)],
 [(74,1),(78,1),(81,1),(86,1),(85,2),(81,2)],
 [(78,1),(79,1),(78,1),(76,1),(74,4)],
 [(74,1),(76,1),(78,1),(79,1),(81,2),(84,2)],
 [(83,1),(81,1),(79,1),(78,1),(79,2),(83,2)],
 [(82,1),(81,1),(79,1),(77,1),(79,2),(82,2)],
 [(81,1),(78,1),(74,1),(78,1),(81,4)],
 [(81,1),(80,1),(78,1),(76,1),(75,2),(78,2)],
 [(79,1),(78,1),(76,1),(74,1),(76,2),(79,2)],
 [(78,1),(76,1),(74,1),(73,1),(71,1),(73,1),(74,1),(76,1)],
 [(78,1),(76,1),(74,2),(74,4)],
]
L = np.zeros(N); R = np.zeros(N)
def place(sig, t, pan=0.0):
    o = max(0, int(t * SR)); n = min(len(sig), N - o)
    if n <= 0: return
    gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    L[o:o + n] += sig[:n] * gl; R[o:o + n] += sig[:n] * gr

nbars = int(math.ceil((DUR + 1.0) / (2 * BEAT)))
for bar in range(nbars):
    t0 = bar * 2 * BEAT; ch = CH[bar % 16]; nxt = CH[(bar + 1) % 16]
    # baixaria: tônica no 1, quinta no 2, aproximação cromática na última semicolcheia rumo ao próximo acorde
    place(pluck(midi(ROOT[ch]), 0.9, bright=0.32, pick=0.3, level=0.62), t0, pan=-0.1)
    place(pluck(midi(FIFTH[ch]), 0.7, bright=0.32, pick=0.3, level=0.5), t0 + BEAT, pan=-0.1)
    appr = ROOT[nxt] + (1 if rng.random() < 0.5 else -1)
    place(pluck(midi(appr), 0.35, bright=0.35, pick=0.3, level=0.42), t0 + 7 * S16, pan=-0.1)
    # acordes em contratempo (posições 2 e 5 e 7, com "rasgueado" de 10 ms entre cordas)
    for pos, lvl in ((2, 0.42), (5, 0.36), (7, 0.26)):
        if pos == 7 and rng.random() < 0.5: continue
        for j, nmidi in enumerate(VOIC[ch]):
            place(pluck(midi(nmidi), 0.55, bright=0.62, pick=0.18 + 0.05 * j, level=lvl * (0.8 + 0.2 * rng.random())), t0 + pos * S16 + j * 0.011, pan=0.35)
    # melodia (violão solista), com leve humanização de tempo e dinâmica
    pos = 0
    for nmidi, d in MEL[bar % 16]:
        if nmidi:
            dur = d * S16 * 0.95 + 0.25
            place(pluck(midi(nmidi), dur, bright=0.85, pick=0.12, level=1.0 * (0.85 + 0.3 * rng.random())), t0 + pos * S16 + rng.normal(0, 0.006), pan=0.08)
        pos += d
    # pandeiro: semicolcheias em "chacoalho" com acento no 1 e no 2, e grave (polegar) no 1
    for s in range(8):
        n = int(0.05 * SR); x = np.arange(n) / SR
        shk = sosfilt(butter(2, [3500 / (SR / 2), 9000 / (SR / 2)], btype="band", output="sos"), rng.normal(0, 1, n)) * np.exp(-x * 110)
        lvl = 0.16 if s in (0, 4) else (0.09 if s % 2 == 0 else 0.055)
        place(shk * lvl, t0 + s * S16 + rng.normal(0, 0.003), pan=-0.45)
        if s in (0, 4):
            m = int(0.12 * SR); xm = np.arange(m) / SR; thump = np.sin(2 * np.pi * (150 * np.exp(-xm * 25) + 70) * xm) * np.exp(-xm * 30) * 0.14
            place(thump, t0 + s * S16, pan=-0.3)

# corpo do violão e ambiente
L = fftconvolve(L, IR)[:N]; R = fftconvolve(R, IR)[:N]
wetL, wetR = fftconvolve(L, RIR)[:N], fftconvolve(R, RIR)[:N]
L = L + 0.22 * wetR; R = R + 0.22 * wetL
# equilíbrio: tira sub-grave e dá presença (shelf simples por soma de passa-alta)
hp = lambda x: sosfilt(butter(2, 60 / (SR / 2), btype='high', output='sos'), x)
sh = lambda x: sosfilt(butter(1, 1800 / (SR / 2), btype='high', output='sos'), x)
L = hp(L); R = hp(R); L = L + 0.9 * sh(L); R = R + 0.9 * sh(R)
mix = np.stack([L, R], 1); t = np.arange(N) / SR
g = np.clip((t - TIN) / 1.2, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1); mix *= g[:, None]
mix = mix[:int(DUR * SR)]; mix /= (np.abs(mix).max() + 1e-9); mix *= 0.7
(folder / "out").mkdir(exist_ok=True)
wavfile.write(folder / "out" / a.out, SR, (mix * 32767).astype(np.int16)); print("ok", folder / "out" / a.out, round(DUR, 1), "s,", a.bpm, "bpm, entra em", TIN, "s")
