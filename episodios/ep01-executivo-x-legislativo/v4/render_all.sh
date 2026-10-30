#!/usr/bin/env bash
# Render completo do ep. 1 v4: vídeo cena a cena, efeitos, trilha, mix e master. Rodar da raiz do repo:
#   nohup bash episodios/ep01-executivo-x-legislativo/v4/render_all.sh > episodios/ep01-executivo-x-legislativo/v4/render.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/../../.."
V=episodios/ep01-executivo-x-legislativo/v4
python3 ferramentas/render_scenes.py "$V" full
python3 ferramentas/sfx.py "$V"
python3 ferramentas/trilha.py "$V" --bpm 72 --gain 0.7
ffmpeg -y -loglevel error -i "$V/out/music.wav" -i "$V/out/sfx.wav" -filter_complex \
  "[1:a]asplit=2[s1][s2];[0:a]volume=-9dB[m];[m][s1]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=300:makeup=1[md];[md][s2]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]" \
  -map "[out]" -ar 44100 "$V/out/mix.wav"
ffmpeg -y -loglevel error -i "$V/out/video.mp4" -i "$V/out/mix.wav" -map 0:v -map 1:a -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest "$V/ep1_v4.mp4"
ffmpeg -y -loglevel error -i "$V/ep1_v4.mp4" -vf scale=720:1280 -c:v libx264 -crf 24 -c:a copy -movflags +faststart "$V/preview_ep1_v4.mp4"
echo "RENDER OK"; ls -la "$V/ep1_v4.mp4" "$V/preview_ep1_v4.mp4"
