import math, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).parent
S = 1080
CX = CY = S / 2

def gear_path(ro=205, ri=165, teeth=8, tooth_half=8.5, root_half=13.5):
    pts = []
    for k in range(teeth):
        b = k * 360 / teeth
        a = [b - root_half, b - tooth_half, b + tooth_half, b + root_half]
        r = [ri, ro, ro, ri]
        pts.append([(r[i], a[i]) for i in range(4)])
    def xy(r, a):
        return CX + r * math.cos(math.radians(a - 90)), CY + r * math.sin(math.radians(a - 90))
    d = []
    for k, t in enumerate(pts):
        x0, y0 = xy(*t[0])
        d.append(("M" if k == 0 else "L") + f"{x0:.1f} {y0:.1f}")
        for r, a in t[1:]:
            x, y = xy(r, a)
            d.append(f"L{x:.1f} {y:.1f}")
        # arc along root radius to next tooth start
        nxt = pts[(k + 1) % len(pts)][0]
        x, y = xy(*nxt)
        d.append(f"A{ri} {ri} 0 0 1 {x:.1f} {y:.1f}")
    d.append("Z")
    return " ".join(d)

def losango(w=820, h=560):
    return f"{CX},{CY-h/2} {CX+w/2},{CY} {CX},{CY+h/2} {CX-w/2},{CY}"

VARIANTS = {
    "A_verde": dict(bg="#00953A", los="#FFDF00", gear="#08204F"),
    "B_navy":  dict(bg="#08204F", los="#FFDF00", gear="#08204F"),
}

def svg(c):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
  <rect width="{S}" height="{S}" fill="{c['bg']}"/>
  <polygon points="{losango()}" fill="{c['los']}"/>
  <path d="{gear_path()}" fill="{c['gear']}"/>
  <circle cx="{CX}" cy="{CY}" r="64" fill="{c['los']}"/>
</svg>'''

if __name__ == "__main__":
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": S, "height": S})
        for name, c in VARIANTS.items():
            (HERE / f"avatar_{name}.svg").write_text(svg(c), encoding="utf-8")
            pg.set_content(f'<body style="margin:0">{svg(c)}</body>')
            pg.screenshot(path=str(HERE / f"avatar_{name}.png"))
        b.close()

    # circular preview of both, side by side, as Instagram would crop
    prev = Image.new("RGB", (1180, 620), "#111")
    for i, name in enumerate(VARIANTS):
        im = Image.open(HERE / f"avatar_{name}.png").resize((500, 500), Image.LANCZOS)
        mask = Image.new("L", (500, 500), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 499, 499), fill=255)
        prev.paste(im, (60 + i * 560, 60), mask)
    prev.save(HERE / "preview_circulos.png")
    print("ok")
