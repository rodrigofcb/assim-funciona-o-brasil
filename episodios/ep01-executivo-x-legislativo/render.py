import sys, os, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
HTML = (HERE / "scene.html").resolve().as_uri()
FPS = 30
DUR = 16.5

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
        print("animations:", n)
        if mode == "preview":
            for t in [0.8, 2.6, 3.55, 6.2, 8.0, 10.2, 13.0, 15.6]:
                pg.evaluate("t => seek(t)", int(t * 1000))
                pg.screenshot(path=str(out / f"t{t:05.2f}.png"))
        else:
            total = int(DUR * FPS)
            for i in range(total):
                pg.evaluate("t => seek(t)", int(round(i * 1000 / FPS)))
                pg.screenshot(path=str(out / f"f{i:04d}.png"))
                if i % 60 == 0:
                    print("frame", i, "/", total, flush=True)
        b.close()

if __name__ == "__main__":
    main()
