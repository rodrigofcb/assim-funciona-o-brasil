"""Recorta de um MIDI de violão os trechos que servem como efeitos sonoros (vocabulário do sfx.py) e os toca com as
amostras de náilon, gerando um catálogo para escolher.

Uso: python3 fragmentos.py <arquivo.mid> [<arquivo2.mid> ...] [--out musica/fragmentos] [--por 3]

Papéis procurados (mesmos nomes de sfx.py):
  tick    nota grave curta e isolada (clique)            pop     acorde de 3 notas, médio (entrada de título)
  impact  acorde cheio e grave (impacto)                 thrum   nota grave longa ou nota repetida (zumbido que acende)
  whoosh  corrida de 5 a 9 notas, comprimida para 0,55 s   fill    corrida ascendente de 6 a 16 notas (preenchimento/contagem)
  sweep   frase ascendente longa (> 1,2 s)               marca   acorde final da peça (cadência)
Saída: <out>/<peça>/<papel>_<n>.wav (cada um começa no ataque), <out>/<peça>/indice.md com instante de origem e notas,
e <out>/catalogo.wav + catalogo.txt com tudo em sequência (dois bipes entre papéis, um bipe entre fragmentos).
"""
import sys, pathlib, argparse, subprocess, functools
import numpy as np, mido
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("mids", nargs="+"); ap.add_argument("--out", default="musica/fragmentos"); ap.add_argument("--por", type=int, default=3)
a = ap.parse_args()
SR = 44100; HERE = pathlib.Path(__file__).resolve().parent; SAMPLES = HERE.parent / "musica" / "samples" / "nylon"
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']; rng = np.random.default_rng(5)
OUT = (HERE.parent / a.out) if not pathlib.Path(a.out).is_absolute() else pathlib.Path(a.out); OUT.mkdir(parents=True, exist_ok=True)

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
n = int(0.7 * SR); IR = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 7); IR = sosfilt(butter(2, 4500 / (SR / 2), btype="low", output="sos"), IR); IR /= np.abs(IR).sum() / 1.2
HP = butter(2, 55 / (SR / 2), btype="high", output="sos")

def render(notes, tail=0.6):
    """notes: lista (t, dur, pitch, vel) relativa ao início do fragmento → estéreo float, normalizado"""
    T = max(t + d for t, d, _, _ in notes) + tail; N = int((T + 0.4) * SR); L = np.zeros(N); R = np.zeros(N)
    for t, d, m, v in notes:
        y = note(m, v, d); o = int(t * SR); k = min(len(y), N - o); pan = 0.05 + rng.normal(0, 0.03)
        L[o:o + k] += y[:k] * np.cos((pan + 1) * np.pi / 4); R[o:o + k] += y[:k] * np.sin((pan + 1) * np.pi / 4)
    L, R = L + 0.14 * fftconvolve(R, IR)[:N], R + 0.14 * fftconvolve(L, IR)[:N]
    L, R = sosfilt(HP, L), sosfilt(HP, R); x = np.stack([L, R], 1)[:int(T * SR)]
    f = int(0.25 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x / (np.abs(x).max() + 1e-9) * 0.9

def read(mid):
    mf = mido.MidiFile(mid); tempo_map = []; tick = 0
    for msg in mf.tracks[0]:
        tick += msg.time
        if msg.type == "set_tempo": tempo_map.append((tick, msg.tempo))
    for tr in mf.tracks[1:]:
        tick = 0
        for msg in tr:
            tick += msg.time
            if msg.type == "set_tempo": tempo_map.append((tick, msg.tempo))
    tempo_map.sort()
    if not tempo_map or tempo_map[0][0] > 0: tempo_map.insert(0, (0, 500000))
    def sec(tk):
        s = 0.0; lt, ltp = 0, tempo_map[0][1]
        for tt, tp in tempo_map:
            if tt >= tk: break
            s += (tt - lt) * ltp / 1e6 / mf.ticks_per_beat; lt, ltp = tt, tp
        return s + (tk - lt) * ltp / 1e6 / mf.ticks_per_beat
    ev = []
    for ti, tr in enumerate(mf.tracks):
        tk = 0; on = {}
        for msg in tr:
            tk += msg.time
            if msg.type == "note_on" and msg.velocity > 0: on[(msg.channel, msg.note)] = (tk, msg.velocity)
            elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in on:
                t0, v = on.pop((msg.channel, msg.note)); ev.append((sec(t0), max(0.05, sec(tk) - sec(t0)), msg.note, v, ti))
    ev.sort()
    # pistas duplicadas (tablatura): mantém a primeira
    tracks = sorted({e[4] for e in ev}); keys = {ti: {(round(e[0], 3), e[2]) for e in ev if e[4] == ti} for ti in tracks}; drop = set()
    for i, ti in enumerate(tracks):
        for tj in tracks[i + 1:]:
            if tj not in drop and len(keys[ti] & keys[tj]) > 0.8 * min(len(keys[ti]), len(keys[tj])): drop.add(tj)
    return [e[:4] for e in ev if e[4] not in drop]

def attacks(ev):
    """agrupa notas com ataque a menos de 25 ms: lista de (t, [notas])"""
    out = []
    for e in ev:
        if out and e[0] - out[-1][0] < 0.025: out[-1][1].append(e)
        else: out.append([e[0], [e]])
    return out

def find(ev):
    A = attacks(ev); C = {k: [] for k in ("tick", "pop", "impact", "thrum", "whoosh", "fill", "sweep", "marca")}
    def seg(i, j): return [e for _, g in A[i:j + 1] for e in g]
    def gap_after(i): return (A[i + 1][0] - A[i][0]) if i + 1 < len(A) else 9
    def gap_before(i): return (A[i][0] - A[i - 1][0]) if i > 0 else 9
    for i, (t, g) in enumerate(A):
        pitches = [e[2] for e in g]; lo = min(pitches)
        if len(g) == 1 and lo <= 50 and g[0][1] <= 0.35 and gap_after(i) >= 0.18: C["tick"].append((-(g[0][3]) + lo * 0.5, i, i))
        if len(g) == 1 and lo <= 52 and g[0][1] >= 1.0: C["thrum"].append((-g[0][1], i, i))
        if len(g) == 3 and 48 <= lo <= 64: C["pop"].append((-(sum(e[3] for e in g)), i, i))
        if len(g) >= 4 and lo <= 50: C["impact"].append((-(len(g) * 10 + (60 - lo)), i, i))
    # nota repetida (tremolo) ≥ 4 vezes
    i = 0
    while i < len(A):
        j = i
        while j + 1 < len(A) and len(A[j + 1][1]) == 1 and len(A[i][1]) == 1 and A[j + 1][1][0][2] == A[i][1][0][2] and gap_after(j) <= 0.2: j += 1
        if j - i >= 3: C["thrum"].append((-(j - i), i, j))
        i = j + 1
    # corridas de notas simples (≤ 2 notas por ataque), monotônicas
    i = 0
    while i < len(A):
        j = i
        while j + 1 < len(A) and len(A[j + 1][1]) <= 2 and gap_after(j) <= 0.24: j += 1
        if j - i + 1 >= 5:
            # subdivide em trechos monotônicos
            k = i
            while k < j:
                m = k; p = [max(e[2] for e in A[m][1])]
                d = 0
                while m + 1 <= j:
                    q = max(e[2] for e in A[m + 1][1]); dd = np.sign(q - p[-1])
                    if dd != 0 and d != 0 and dd != d: break
                    if dd != 0: d = dd
                    p.append(q); m += 1
                nn = m - k + 1; dur = A[m][0] - A[k][0] + 0.1
                if nn >= 5:
                    if dur <= 1.6 and nn <= 9: C["whoosh"].append((-(nn / dur), k, m))   # tocado acelerado (0,55 s) na renderização
                    if d > 0 and 6 <= nn <= 16 and dur <= 2.2: C["fill"].append((-nn, k, m))
                    if d > 0 and dur >= 1.2: C["sweep"].append((-dur, k, m))
                k = m if m > k else k + 1
        i = j + 1
    C["marca"].append((0, len(A) - 1, len(A) - 1))
    sel = {}
    for k, lst in C.items():
        lst.sort(); used = []; pick = []
        for sc, i, j in lst:
            if any(not (j < u0 - 2 or i > u1 + 2) for u0, u1 in used): continue   # evita trechos repetidos/vizinhos
            pick.append((i, j)); used.append((i, j))
            if len(pick) >= (1 if k == "marca" else a.por): break
        sel[k] = [(A[i][0], seg(i, j)) for i, j in pick]
    return sel

CUT = {"tick": 0.14, "pop": 0.5, "impact": 1.4, "thrum": 1.6, "whoosh": None, "fill": None, "sweep": None, "marca": 2.2}
beep1 = (np.sin(2 * np.pi * 880 * np.arange(int(0.1 * SR)) / SR) * np.exp(-np.arange(int(0.1 * SR)) / SR * 30) * 0.25)
beep1 = np.stack([beep1, beep1], 1); sil = lambda s: np.zeros((int(s * SR), 2))
cat = []; idx = []; pos = 0.0
for mid in a.mids:
    name = pathlib.Path(mid).stem.split("-")[0]; d = OUT / name; d.mkdir(exist_ok=True); ev = read(mid); sel = find(ev)
    lines = [f"# {pathlib.Path(mid).name}\n", "| arquivo | papel | origem (s) | notas | duração |", "|---|---|---|---|---|"]
    for k, items in sel.items():
        if not items: continue
        cat += [beep1, sil(0.12), beep1, sil(0.4)]; pos += (2 * len(beep1) + int(0.52 * SR)) / SR
        for n_, (t0, notes) in enumerate(items, 1):
            rel = [(t - t0, (min(dur, CUT[k]) if CUT[k] else dur), p, v) for t, dur, p, v in notes]
            if k == "whoosh":   # comprime a corrida para 0,55 s, como um rasgueado rápido
                span = max(t for t, _, _, _ in rel) + 1e-6; f_ = 0.55 / span; rel = [(t * f_, max(0.08, dd * f_), p, v) for t, dd, p, v in rel]
            if CUT[k]: rel = [(t, max(0.05, min(dd, CUT[k] - t)), p, v) for t, dd, p, v in rel if t < CUT[k]]
            x = render(rel, tail=0.25 if k == "tick" else 0.6)
            if CUT[k]: x = x[:int((CUT[k] + 0.35) * SR)]; f = int(0.12 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
            fn = d / f"{k}_{n_}.wav"; wavfile.write(fn, SR, (x * 32767).astype(np.int16))
            ns = " ".join(f"{NAMES[p % 12]}{p // 12 - 1}" for _, _, p, _ in rel[:10]) + (" …" if len(rel) > 10 else "")
            lines.append(f"| {fn.name} | {k} | {t0:.1f} | {ns} | {len(x) / SR:.2f} s |")
            idx.append((pos, f"{name} {k} {n_}  (origem {t0:.1f} s)")); cat += [beep1, sil(0.2), x, sil(0.7)]; pos += (len(beep1) + int(0.9 * SR) + len(x)) / SR
    (d / "indice.md").write_text("\n".join(lines) + "\n", encoding="utf-8"); print("ok", name, {k: len(v) for k, v in sel.items()})
y = np.concatenate(cat); wavfile.write(OUT / "catalogo.wav", SR, (y * 32767).astype(np.int16))
with open(OUT / "catalogo.txt", "w", encoding="utf-8") as f:
    for p, l in idx: m, s = divmod(int(p), 60); f.write(f"{m}:{s:02d}  {l}\n")
print("catálogo:", OUT / "catalogo.wav", f"{len(y) / SR:.0f} s")
