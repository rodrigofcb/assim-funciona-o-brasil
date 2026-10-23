"""Tratamento de narração gravada no celular.

Uso: python3 voz.py entrada.wav saida_prefixo [--noise 0.2:1.9] [--trim 1.6:23.4]

Gera três versões:
  <prefixo>_A_acabamento.wav   só limpeza, EQ, compressão e normalização
  <prefixo>_B_timbre_leve.wav  pitch -1.4 st, formantes x0.96
  <prefixo>_C_timbre_forte.wav pitch -3.0 st, formantes x0.92
Entonação, ritmo e pausas ficam intactos; só o timbre muda.
"""
import sys, subprocess, pathlib, argparse
import numpy as np
from scipy.io import wavfile
import pyworld as pw

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("prefix")
ap.add_argument("--noise", default="0.2:1.9", help="trecho só com ruído, para o perfil (s:s)")
ap.add_argument("--trim", default=None, help="corte final start:end em segundos")
ap.add_argument("--lufs", type=float, default=-16.0)
ap.add_argument("--only", default=None, help="gera só esta versão (A, B ou C)")
a = ap.parse_args()
out = pathlib.Path(a.prefix); out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.parent / "_tmp"; tmp.mkdir(exist_ok=True)

def ff(args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args, check=True)

# 1) limpeza: passa-alta + redução de ruído com perfil medido num trecho silencioso
n0, n1 = a.noise.split(":")
den = tmp / "denoised.wav"
ff(["-i", a.inp, "-af",
    f"highpass=f=75,asendcmd=c='{n0} afftdn sn start\\; {n1} afftdn sn stop',afftdn=nr=14:nf=-60:om=o",
    "-ar", "44100", "-ac", "1", str(den)])

# 2) timbre via vocoder WORLD (f0 e envelope espectral separados)
sr, x = wavfile.read(den); x = x.astype(np.float64) / 32768
f0, t = pw.harvest(x, sr, f0_floor=60.0, f0_ceil=400.0)
f0 = pw.stonemask(x, f0, t, sr)
sp = pw.cheaptrick(x, f0, t, sr)
apr = pw.d4c(x, f0, t, sr)
print(f"f0 mediana: {np.median(f0[f0>0]):.0f} Hz")

def timbre(semitones, alpha):
    f0n = f0 * 2 ** (semitones / 12)
    bins = np.arange(sp.shape[1])
    spn = np.vstack([np.interp(bins / alpha, bins, row) for row in sp])  # alpha<1 desce as formantes
    y = pw.synthesize(f0n, np.ascontiguousarray(spn), apr, sr)
    y = y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))
    return (np.clip(y, -1, 1) * 32767).astype(np.int16)

versions = {"A_acabamento": None, "B_timbre_leve": (-1.4, 0.96), "C_timbre_forte": (-3.0, 0.92)}

# 3) acabamento: EQ (tira embolado, dá presença), de-esser, compressor, loudness para redes
trim = f"atrim={a.trim.replace(':', ':end=')}," if a.trim else ""
if a.trim: trim = f"atrim=start={a.trim.split(':')[0]}:end={a.trim.split(':')[1]},asetpts=PTS-STARTPTS,"
chain = (trim + "equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1:g=2.5,deesser=i=0.3,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=4,"
         f"loudnorm=I={a.lufs}:TP=-1.5:LRA=9,afade=t=in:d=0.05")
for name, params in versions.items():
    if a.only and not name.startswith(a.only): continue
    src = den
    if params:
        src = tmp / f"{name}.wav"
        wavfile.write(src, sr, timbre(*params))
    ff(["-i", str(src), "-af", chain, "-ar", "44100", f"{out}_{name}.wav"])
    ff(["-i", f"{out}_{name}.wav", "-c:a", "aac", "-b:a", "192k", f"{out}_{name}.m4a"])
    print("ok", name)
