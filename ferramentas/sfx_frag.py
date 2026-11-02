"""Sonoplastia musical: toca os eventos de TL.sfx com fragmentos de peças (saída de fragmentos.py) em vez de sons sintéticos.

Uso: python3 sfx_frag.py <pasta> [--banco musica/fragmentos/rebolico[,musica/fragmentos/choro]] [--chao] [--out sfx_frag.wav]
  --banco  pastas de fragmentos, em ordem de preferência (cada papel cicla entre os fragmentos disponíveis)
  --chao   acrescenta um "chão" mínimo durante as cenas de contagem: a baixaria da primeira peça, bem baixa e abafada,
           nas janelas TL.chao (lista de [t0, t1]) ou, se não houver, em volta dos eventos "fill"
Os fragmentos são re-tocados a partir das notas (.json) com as amostras de náilon, então 'fill' e 'sweep' são esticados
ou comprimidos para a duração pedida pelo evento sem mudar a altura.
"""
import sys, json, re, pathlib, argparse, functools, subprocess
import numpy as np, mido
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--banco", default="musica/fragmentos/rebolico,musica/fragmentos/choro")
ap.add_argument("--chao", action="store_true"); ap.add_argument("--out", default="sfx_frag.wav"); ap.add_argument("--chao-db", type=float, default=-17)
a = ap.parse_args()
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
folder = pathlib.Path(a.folder).resolve()
TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", (folder / "timeline.js").read_text(encoding="utf-8")).rstrip().rstrip(";"))
B = TL["beats"]; SR = 44100; N = int((TL["end"] + 0.5) * SR); L = np.zeros(N); R = np.zeros(N)
SAMPLES = ROOT / "musica" / "samples" / "nylon"; NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']; rng = np.random.default_rng(11)

@functools.lru_cache(maxsize=None)
def sample(m):
    m = int(min(108, max(21, m))); name = f"{NAMES[m % 12]}{m // 12 - 1}"; npy = SAMPLES / f"{name}.npy"
    if npy.exists(): return np.load(npy)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(SAMPLES / f"{name}.mp3"), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy(); i0 = int(np.argmax(np.abs(x) > 0.004)); x = x[max(0, i0 - 20):]; np.save(npy, x); return x
def note(m, vel, dur):
    x = sample(m); n = min(len(x), int((dur + 0.35) * SR)); y = x[:n].copy(); k0 = int(dur * SR)
    if k0 < n: y[k0:] *= np.exp(-np.arange(n - k0) / (0.0625 * SR))
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR)); return y * (0.25 + 0.75 * (vel / 127) ** 1.3)
n_ = int(0.7 * SR); IR = rng.normal(0, 1, n_) * np.exp(-np.arange(n_) / SR * 7); IR = sosfilt(butter(2, 4500 / (SR / 2), btype="low", output="sos"), IR); IR /= np.abs(IR).sum() / 1.2
def render(notes, tail=0.6, lp=None):
    T = max(t + d for t, d, _, _ in notes) + tail; M = int((T + 0.4) * SR); l = np.zeros(M); r = np.zeros(M)
    for t, d, m, v in notes:
        y = note(m, v, d); o = int(t * SR); k = min(len(y), M - o); pan = 0.05 + rng.normal(0, 0.03)
        l[o:o + k] += y[:k] * np.cos((pan + 1) * np.pi / 4); r[o:o + k] += y[:k] * np.sin((pan + 1) * np.pi / 4)
    l, r = l + 0.14 * fftconvolve(r, IR)[:M], r + 0.14 * fftconvolve(l, IR)[:M]
    if lp: sos = butter(2, lp / (SR / 2), btype="low", output="sos"); l, r = sosfilt(sos, l), sosfilt(sos, r)
    x = np.stack([l, r], 1)[:int(T * SR)]; f = int(0.25 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x / (np.abs(x).max() + 1e-9)

# ---- banco de fragmentos
bancos = [(ROOT / b) if not pathlib.Path(b).is_absolute() else pathlib.Path(b) for b in a.banco.split(",")]
FR = {}
for b in bancos:
    for j in sorted(b.glob("*.json")):
        d = json.loads(j.read_text(encoding="utf-8")); FR.setdefault(d["papel"], []).append((b.name, j.stem, d["notas"]))
counter = {}
def pick(kind):
    lst = FR.get(kind) or FR.get({"sweep": "fill", "thrum": "impact", "pop": "tick"}.get(kind, kind)) or FR["tick"]
    i = counter.get(kind, 0); counter[kind] = i + 1; return lst[i % len(lst)]
def retime(notes, target):
    """comprime/estica a lista de notas para durar `target` s (último ataque em target), sem mudar altura"""
    span = max(t for t, _, _, _ in notes) + 1e-6; f = target / span
    return [(t * f, max(0.06, d * min(f, 1.0)), p, v) for t, d, p, v in notes]

GAIN = {"tick": 0.45, "pop": 0.6, "impact": 0.95, "thrum": 0.55, "whoosh": 0.55, "fill": 0.5, "sweep": 0.5, "marca": 0.95}
CUT = {"tick": 0.16, "pop": 0.6, "impact": 1.6, "thrum": 1.8, "marca": 2.6}
def place(sig, t, pan=0.0, move=None):
    o = int(t * SR); n = min(len(sig), N - o)
    if n <= 0: return
    s = sig[:n]
    if move is None: gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); L[o:o + n] += s[:, 0] * gl * 1.4; R[o:o + n] += s[:, 1] * gr * 1.4
    else: p = np.linspace(move[0], move[1], n); mono = s.mean(1); L[o:o + n] += mono * np.cos((p + 1) * np.pi / 4); R[o:o + n] += mono * np.sin((p + 1) * np.pi / 4)

log = []
for ev in TL["sfx"]:
    beat, kind = ev[0], ev[1]; opts = ev[2] if len(ev) > 2 else None; t = B[beat]
    src, name, notes = pick(kind); notes = [tuple(x) for x in notes]
    if kind == "fill":
        o = {**TL.get("fill", {}), **(opts or {})}; dur = o.get("ticks", 6) * o.get("dt", 0.1)
        if len(notes) > o.get("ticks", 6) + 2: notes = notes[:o.get("ticks", 6) + 2]
        notes = retime(notes, dur); sig = render(notes, tail=0.5)
    elif kind == "sweep": sig = render(retime(notes, 1.9), tail=0.8)
    elif kind == "whoosh": sig = render(notes, tail=0.4)
    else:
        c = CUT[kind]; nn = [(t_, max(0.05, min(d, c - t_)), p, v) for t_, d, p, v in notes if t_ < c]; sig = render(nn, tail=0.2 if kind == "tick" else 0.5)
        sig = sig[:int((c + 0.3) * SR)]; f = int(0.1 * SR); sig[-f:] *= np.linspace(1, 0, f)[:, None]
    sig = sig * GAIN[kind]
    if kind == "whoosh": d = rng.choice([-1, 1]); place(sig, t, move=(-0.8 * d, 0.8 * d))
    elif kind == "sweep": place(sig, t, move=(0.8, -0.8))
    elif kind == "thrum": place(sig, t, pan=-0.35 if "pres" in beat else (0.35 if "cong" in beat else 0))
    else: place(sig, t, pan=rng.uniform(-0.15, 0.15))
    log.append(f"{t:6.2f}  {beat:8s} {kind:7s} ← {src}/{name}")

# ---- chão: baixaria da primeira peça, abafada e baixa, só nas janelas de contagem
if a.chao:
    mid = next(iter(ROOT.glob(f"musica/midi/{bancos[0].name}*.mid")))
    mf = mido.MidiFile(mid); tempo = 500000; tk = 0; on = {}; ev_ = []
    for msg in mido.merge_tracks(mf.tracks):
        tk += msg.time
        if msg.type == "set_tempo": tempo = msg.tempo
    t = 0.0
    for msg in mf:   # iteração do MidiFile já entrega tempo em segundos
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0: on[msg.note] = (t, msg.velocity)
        elif msg.type in ("note_off", "note_on") and msg.note in on: t0, v = on.pop(msg.note); ev_.append((t0, max(0.1, t - t0), msg.note, v))
    ev_.sort()
    # baixaria = nota mais grave de cada ataque, só graves
    bass = []; last = -9
    for t0, d, p, v in ev_:
        if p > 55: continue
        if t0 - last < 0.03: continue
        bass.append((t0, d, p, v)); last = t0
    wins = TL.get("chao")
    if not wins:   # em volta dos fills: da 1ª nota do fill até o próximo whoosh/impact, com margem
        fills = sorted(B[e[0]] for e in TL["sfx"] if e[1] == "fill"); wins = []
        for f in fills:
            if wins and f <= wins[-1][1] + 1.5: wins[-1][1] = f + 3.0
            else: wins.append([f - 0.8, f + 3.0])
    g = 10 ** (a.chao_db / 20)
    for w0, w1 in wins:
        dur = w1 - w0; start = rng.uniform(0, max(0.1, bass[-1][0] - dur - 1)); seg = [(t0 - start, d, p, int(v * 0.7)) for t0, d, p, v in bass if start <= t0 < start + dur]
        if not seg: continue
        x = render(seg, tail=0.8, lp=1100) * g; f0, f1 = int(0.9 * SR), int(1.2 * SR); x[:f0] *= np.linspace(0, 1, f0)[:, None]; x[-f1:] *= np.linspace(1, 0, f1)[:, None]
        place(x, w0, pan=-0.2); log.append(f"{w0:6.2f}  chão {dur:.1f} s ← {bancos[0].name} baixaria (de {start:.1f} s)")

mix = np.stack([L, R], 1); peak = np.abs(mix).max(); mix = mix / peak * 0.85 if peak > 0 else mix
(folder / "out").mkdir(exist_ok=True); wavfile.write(folder / "out" / a.out, SR, (mix * 32767).astype(np.int16))
(folder / "out" / (pathlib.Path(a.out).stem + ".log")).write_text("\n".join(log) + "\n", encoding="utf-8")
print("ok", a.out, f"{N / SR:.1f} s, {len(TL['sfx'])} eventos" + (", com chão" if a.chao else ""))
