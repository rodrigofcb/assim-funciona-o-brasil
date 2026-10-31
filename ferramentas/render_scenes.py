"""Renderiza scene.html (dirigido por timeline.js) em um MP4 por cena e junta tudo.

Uso:
  python3 render_scenes.py <pasta> preview 1.2,3.4,...   -> PNGs em <pasta>/preview/
  python3 render_scenes.py <pasta> full                   -> <pasta>/out/<cena>.mp4 + <pasta>/out/video.mp4 (sem áudio)
  python3 render_scenes.py <pasta> full s2                -> só a cena s2 (e junta de novo)
Tema (opcional): TEMA=day python3 render_scenes.py ...   -> abre scene.html?tema=day e escreve em out-day/ e preview-day/
"""
import sys, json, re, subprocess, pathlib, os
from playwright.sync_api import sync_playwright

folder = pathlib.Path(sys.argv[1]).resolve()
mode = sys.argv[2]
arg = sys.argv[3] if len(sys.argv) > 3 else None
TL = json.loads(re.sub(r"^\s*window\.TL\s*=\s*", "", (folder / "timeline.js").read_text(encoding="utf-8")).rstrip().rstrip(";"))
FPS = TL["fps"]
TEMA = os.environ.get("TEMA", "")
SUF = f"-{TEMA}" if TEMA else ""
html = (folder / "scene.html").as_uri() + (f"?tema={TEMA}" if TEMA else "")

def encode(name, t0, t1, pg):
    out = folder / f"out{SUF}"; out.mkdir(exist_ok=True)
    tmp = out / f"_{name}.tmp.mp4"; final = out / f"{name}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-vcodec", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", str(tmp)], stdin=subprocess.PIPE)
    n0, n1 = round(t0 * FPS), round(t1 * FPS)
    for i in range(n0, n1):
        pg.evaluate("t => seek(t)", int(round(i * 1000 / FPS)))
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        if (i - n0) % 90 == 0: print(f"{name}: {i-n0}/{n1-n0}", flush=True)
    ff.stdin.close(); rc = ff.wait()
    if rc != 0: sys.exit(f"ffmpeg falhou na cena {name}")
    os.replace(tmp, final); print("ok", final.name)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    pg.goto(html); pg.wait_for_timeout(300)
    print("animations:", pg.evaluate("seek(0)"), "end:", TL["end"])
    if mode == "preview":
        prev = folder / f"preview{SUF}"; prev.mkdir(exist_ok=True)
        for t in [float(x) for x in arg.split(",")]:
            pg.evaluate("t => seek(t)", int(t * 1000)); pg.screenshot(path=str(prev / f"t{t:05.2f}.png"))
    else:
        for name, t0, t1 in TL["scenes"]:
            if arg and name != arg: continue
            encode(name, t0, t1, pg)
    b.close()

if mode == "full":
    out = folder / f"out{SUF}"
    lst = out / "list.txt"
    lst.write_text("".join(f"file '{(out / f'{n}.mp4').as_posix()}'\n" for n, _, _ in TL["scenes"]))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "video.mp4")], check=True)
    print("ok video.mp4")
