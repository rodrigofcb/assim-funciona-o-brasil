import sys, os, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
HTML = (HERE / "scene.html").resolve().as_uri()
FPS = 30

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    out = HERE / ("preview" if mode == "preview" else "frames")
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto(HTML)
        pg.wait_for_timeout(300)
        n = pg.evaluate("seek(0)")
        DUR = pg.evaluate("window.TOTAL")
        print("animations:", n, "duration:", DUR)
        if mode == "preview":
            for t in [float(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else "0.8,3.55,8,13".split(","))]:
                pg.evaluate("t => seek(t)", int(t * 1000))
                pg.screenshot(path=str(out / f"t{t:05.2f}.png"))
        else:
            total = int(DUR * FPS)
            for i in range(total):
                f = out / f"f{i:04d}.png"
                if f.exists():
                    continue  # retoma render interrompido
                pg.evaluate("t => seek(t)", int(round(i * 1000 / FPS)))
                pg.screenshot(path=str(f))
                if i % 60 == 0:
                    print("frame", i, "/", total, flush=True)
        b.close()

if __name__ == "__main__":
    main()
