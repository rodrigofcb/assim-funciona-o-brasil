"""Toca um MIDI (piano ou violão) com amostras reais de violão de náilon (FluidR3, CC BY), em arranjo para violões.

Uso: python3 violao.py <arquivo.mid> <saida.wav> [--dur 30] [--in 0] [--tempo 1.0] [--start 0]
  - MIDI de piano (2 pistas): mão direita = violão solista (centro), mão esquerda = violão de acompanhamento (direita),
    com rasgueado de 10 ms nos acordes e graves reforçados uma oitava abaixo quando a nota é a mais grave do acorde.
  - MIDI de violão (1 pista): toca como está.
  --tempo escala o andamento (0.9 = 10% mais lento). --start pula os primeiros segundos da peça. --dur corta a saída (com fade).
"""
import sys, pathlib, argparse, subprocess, functools
import numpy as np
import mido
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument("mid"); ap.add_argument("out")
ap.add_argument("--dur", type=float, default=None); ap.add_argument("--in", dest="tin", type=float, default=0.0)
ap.add_argument("--tempo", type=float, default=1.0); ap.add_argument("--start", type=float, default=0.0)
ap.add_argument("--gain", type=float, default=0.8)
a = ap.parse_args()
SR = 44100
HERE = pathlib.Path(__file__).resolve().parent
SAMPLES = HERE.parent / "musica" / "samples" / "nylon"
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
rng = np.random.default_rng(5)

@functools.lru_cache(maxsize=None)
def sample(m):
    """amostra mono float32 da nota MIDI m (decodifica o mp3 com ffmpeg; cache em .npy)"""
    m = int(min(108, max(21, m))); name = f"{NAMES[m % 12]}{m // 12 - 1}"
    npy = SAMPLES / f"{name}.npy"
    if npy.exists(): return np.load(npy)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(SAMPLES / f"{name}.mp3"), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    # corta silêncio inicial do mp3 (latência do codec)
    i0 = int(np.argmax(np.abs(x) > 0.004)); x = x[max(0, i0 - 20):]
    np.save(npy, x); return x

def note(m, vel, dur):
    x = sample(m)
    n = min(len(x), int((dur + 0.35) * SR))                 # deixa a corda soar 350 ms além do note-off
    y = x[:n].copy()
    rel = int(0.25 * SR); k0 = int(dur * SR)
    if k0 < n:                                             # release suave após o note-off
        env = np.ones(n); env[k0:] = np.exp(-np.arange(n - k0) / (rel / 4)); y *= env
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return y * (0.25 + 0.75 * (vel / 127) ** 1.3)

# ---- lê o MIDI em eventos absolutos (segundos)
mf = mido.MidiFile(a.mid)
events = []   # (t, dur, nota, vel, pista)
for ti, tr in enumerate(mf.tracks):
    pass
# mido.MidiFile iteração mesclada já converte ticks em segundos com os tempos corretos
t = 0.0; on = {}; track_of = {}
for msg in mido.merge_tracks(mf.tracks):
    pass
# para saber a pista de cada nota, percorremos pista a pista com o mapa de tempo global
tempo_map = []; tick = 0
for msg in mido.merge_tracks(mf.tracks):
    tick += msg.time
    if msg.type == "set_tempo": tempo_map.append((tick, msg.tempo))
if not tempo_map or tempo_map[0][0] > 0: tempo_map.insert(0, (0, 500000))
def tick2sec(tk):
    s = 0.0; last_tick, last_tempo = 0, tempo_map[0][1]
    for tt, tp in tempo_map:
        if tt >= tk: break
        s += (tt - last_tick) * last_tempo / 1e6 / mf.ticks_per_beat; last_tick, last_tempo = tt, tp
    return s + (tk - last_tick) * last_tempo / 1e6 / mf.ticks_per_beat
for ti, tr in enumerate(mf.tracks):
    tk = 0; on = {}
    for msg in tr:
        tk += msg.time
        if msg.type == "note_on" and msg.velocity > 0: on[(msg.channel, msg.note)] = (tk, msg.velocity)
        elif msg.type in ("note_off", "note_on"):
            key = (msg.channel, msg.note)
            if key in on:
                t0, v = on.pop(key); events.append((tick2sec(t0) / a.tempo, max(0.05, (tick2sec(tk) - tick2sec(t0)) / a.tempo), msg.note, v, ti))
events.sort()
# pistas duplicadas (partitura + tablatura): mantém só a primeira
tracks_with_notes = sorted({e[4] for e in events})
keysets = {ti: {(round(e[0], 3), e[2]) for e in events if e[4] == ti} for ti in tracks_with_notes}
drop = set()
for i, ti in enumerate(tracks_with_notes):
    for tj in tracks_with_notes[i + 1:]:
        if tj in drop: continue
        inter = len(keysets[ti] & keysets[tj])
        if inter > 0.8 * min(len(keysets[ti]), len(keysets[tj])): drop.add(tj)
if drop: events = [e for e in events if e[4] not in drop]; print("pistas duplicadas removidas:", sorted(drop))
tracks_with_notes = sorted({e[4] for e in events})
piano = len(tracks_with_notes) >= 2
if piano:
    # pista mais aguda em média = mão direita
    means = {ti: np.mean([e[2] for e in events if e[4] == ti]) for ti in tracks_with_notes}
    rh = max(means, key=means.get)
events = [e for e in events if e[0] >= a.start]
t_end = max(e[0] + e[1] for e in events) - a.start + 1.5
DUR = a.dur if a.dur else t_end
N = int((DUR + 2.5) * SR); L = np.zeros(N); R = np.zeros(N)
def place(sig, t, pan):
    o = max(0, int(t * SR)); n = min(len(sig), N - o)
    if n <= 0: return
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[o:o + n] += sig[:n] * gl; R[o:o + n] += sig[:n] * gr

# agrupa notas simultâneas por pista para o rasgueado
from collections import defaultdict
groups = defaultdict(list)
for (t0, d, m, v, ti) in events: groups[(ti, round(t0, 3))].append((t0, d, m, v))
for (ti, _), g in groups.items():
    g.sort(key=lambda e: e[2])
    solo = (not piano) or ti == rh
    for j, (t0, d, m, v) in enumerate(g):
        tt = t0 - a.start + (j * 0.011 if (not solo and len(g) > 1) else 0) + rng.normal(0, 0.004)
        vel = v * (1.0 if solo else 0.78)
        if piano and not solo and j == 0 and len(g) > 1 and m >= 40: place(note(m - 12, vel * 0.7, d), tt, pan=0.0)   # bordão (7ª corda)
        place(note(m, vel, d), tt, pan=(0.05 if solo else 0.4) + rng.normal(0, 0.03))

# ambiente leve (sala pequena) e corte de sub-grave
n = int(0.9 * SR); ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6); ir = sosfilt(butter(2, 4500 / (SR / 2), btype="low", output="sos"), ir); ir /= np.abs(ir).sum() / 1.4
wetL, wetR = fftconvolve(L, ir)[:N], fftconvolve(R, ir)[:N]
L = L + 0.16 * wetR; R = R + 0.16 * wetL
hp = butter(2, 55 / (SR / 2), btype="high", output="sos"); L = sosfilt(hp, L); R = sosfilt(hp, R)
mix = np.stack([L, R], 1)[:int(DUR * SR)]; tt = np.arange(len(mix)) / SR
g = np.clip((tt - a.tin) / 1.0, 0, 1) * np.clip((DUR - tt) / 2.0, 0, 1); mix *= g[:, None]
mix /= (np.abs(mix).max() + 1e-9); mix *= a.gain
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
wavfile.write(a.out, SR, (mix * 32767).astype(np.int16))
print(f"ok {a.out}: {len(events)} notas, {'piano→2 violões' if piano else 'violão'}, {DUR:.1f} s")
