"""Avatar: bandeira com a engrenagem recortada no globo (azul, faixa branca sem texto, estrelas)."""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
from make_avatar import gear_path, losango, S, CX, CY

HERE = pathlib.Path(__file__).parent
RG = 215  # raio do globo em px (um pouco maior que a engrenagem, para os dentes ficarem azuis)

# estrelas aproximadas (x, y em raios do globo, y para cima; r em px)
STARS = [
    (0.05, 0.74, 8),            # acima da faixa
    (-0.62, -0.04, 7),          # Procyon
    (-0.55, -0.36, 9), (-0.72, -0.33, 5), (-0.47, -0.54, 5), (-0.63, -0.62, 6), (-0.78, -0.5, 4),  # Cão Maior
    (-0.4, -0.74, 8),           # Canopus
    (0.02, -0.72, 9), (0.05, -0.34, 6), (-0.16, -0.5, 7), (0.22, -0.46, 5), (0.09, -0.56, 3),      # Cruzeiro do Sul
    (0.3, -0.78, 5), (0.44, -0.62, 5), (0.56, -0.74, 5),  # Triângulo Austral
    (0.55, -0.1, 8), (0.42, 0.02, 5), (0.4, -0.19, 5), (0.7, -0.22, 5), (0.8, -0.36, 5),
    (0.84, -0.5, 4), (0.76, -0.63, 4), (0.64, -0.7, 4),    # Escorpião
    (0.74, 0.18, 5), (0.86, 0.02, 4),                      # Hidra
    (0.0, -0.9, 4),                                        # Octante
]
# faixa: arco de círculo (centro abaixo do globo, deslocado para a direita = inclinação)
BAND_C = (0.6, -2.4); BAND_R = 2.65; BAND_W = 0.16

def px(x, y):
    return CX + x * RG, CY - y * RG

def globo_svg(with_hole):
    bx, by = px(*BAND_C)
    stars = "".join(f'<circle cx="{px(x,y)[0]:.1f}" cy="{px(x,y)[1]:.1f}" r="{r}" fill="#fff"/>' for x, y, r in STARS)
    hole = f'<circle cx="{CX}" cy="{CY}" r="54" fill="#FFDF00"/>' if with_hole else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
  <defs><clipPath id="gear"><path d="{gear_path()}"/></clipPath></defs>
  <rect width="{S}" height="{S}" fill="#00953A"/>
  <polygon points="{losango()}" fill="#FFDF00"/>
  <g clip-path="url(#gear)">
    <circle cx="{CX}" cy="{CY}" r="{RG+4}" fill="#002776"/>
    <circle cx="{bx:.1f}" cy="{by:.1f}" r="{BAND_R*RG:.1f}" fill="none" stroke="#fff" stroke-width="{BAND_W*RG:.1f}"/>
    {stars}
  </g>
  {hole}
</svg>'''

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": S, "height": S})
    for name, hole in (("C_verde_globo", True), ("D_verde_globo_sem_furo", False)):
        svg = globo_svg(hole)
        (HERE / f"avatar_{name}.svg").write_text(svg, encoding="utf-8")
        pg.set_content(f'<body style="margin:0">{svg}</body>')
        pg.screenshot(path=str(HERE / f"avatar_{name}.png"))
    b.close()

prev = Image.new("RGB", (1180, 620), "#111")
for i, name in enumerate(("C_verde_globo", "D_verde_globo_sem_furo")):
    im = Image.open(HERE / f"avatar_{name}.png").resize((500, 500), Image.LANCZOS)
    mask = Image.new("L", (500, 500), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 499, 499), fill=255)
    prev.paste(im, (60 + i * 560, 60), mask)
prev.save(HERE / "preview_globo.png")
print("ok")
