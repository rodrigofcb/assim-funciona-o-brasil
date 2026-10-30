"""Converte dados/brasilia_osm.geojson em um JS compacto (window.MAPA) em metros, com origem no Congresso.

Uso: python3 mapa_osm.py <geojson> <saida.js>
Saída: roads {major, mid, minor}, bld [[h, ring...]], water [ring...], named {chave:{x,y,rot,w,l}}
"""
import sys, json, math
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
LAT0, LON0 = -15.7997, -47.8644          # origem: centro aproximado do Congresso
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110574
def xy(c): return (round((c[0] - LON0) * KX, 1), round((c[1] - LAT0) * KY, 1))

MAJOR = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
MID = {"secondary", "tertiary", "secondary_link", "tertiary_link", "residential", "unclassified", "pedestrian", "living_street"}
roads = {"major": [], "mid": [], "minor": []}; bld = []; water = []
named = {}
WANT = {  # chave: regex do nome; usa o polígono com área mais próxima de 'area' m² quando há repetidos
    "congresso": ("Congresso Nacional do Brasil", None), "planalto": ("Palácio do Planalto", None), "stf": ("Supremo Tribunal Federal", None),
    "fazenda": ("Ministério da Fazenda", 5000), "saude": ("Ministério da Saúde", 5000), "educacao": ("Ministério da Educação", 5000),
    "transportes": ("Ministério das Comunicações / Infraestrutura", 5000), "itamaraty": ("Palácio Itamaraty", None), "torre": ("Torre de TV", 2500),
    "justica": ("Palácio da Justiça", None), "catedral": ("Catedral Metropolitana Nossa Senhora Aparecida", None),
}
def ring_stats(ring):
    P = np.array(ring, float); c = P.mean(0); Q = P - c
    cov = Q.T @ Q / len(Q); w, v = np.linalg.eigh(cov); ax = v[:, 1]   # eixo principal
    rot = math.atan2(ax[1], ax[0]); proj = Q @ v
    L = proj[:, 1].max() - proj[:, 1].min(); W = proj[:, 0].max() - proj[:, 0].min()
    x, y = P[:, 0], P[:, 1]; area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return c, rot, W, L, area

def near_core(ring_or_line):
    # mantém detalhe fino só no núcleo (Esplanada + Praça): faixa ao longo do Eixo
    for x, y in ring_or_line[::max(1, len(ring_or_line) // 6)]:
        ax = y - math.tan(math.radians(-17.9)) * x      # distância vertical ao Eixo (passa pela origem)
        if -1300 < x < 700 and abs(ax) < 520: return True
    return False

for f in d["features"]:
    p, g = f["properties"], f["geometry"]
    if g["type"] == "LineString" and "highway" in p:
        line = [xy(c) for c in g["coordinates"]]; hw = p["highway"]
        if hw in MAJOR: roads["major"].append(line)
        elif hw in MID: roads["mid"].append(line)
        elif near_core(line): roads["minor"].append(line)
    elif g["type"] == "Polygon":
        ring = [xy(c) for c in g["coordinates"][0]]
        if "building" in p or "building:part" in p:
            h = 0.0
            if p.get("height"):
                try: h = float(str(p["height"]).replace("m", "").strip())
                except ValueError: h = 0.0
            elif p.get("building:levels"):
                try: h = float(p["building:levels"]) * 3.3
                except ValueError: h = 0.0
            bld.append([round(h, 1)] + [list(c) for c in ring])
            n = p.get("name", "")
            for key, (pat, area_want) in WANT.items():
                if n == pat:
                    c, rot, W, L, area = ring_stats(ring)
                    cand = {"x": round(float(c[0]), 1), "y": round(float(c[1]), 1), "rot": round(rot, 4), "w": round(W, 1), "l": round(L, 1), "area": round(area), "h": h,
                            "ring": [list(c_) for c_ in ring]}
                    if key not in named or (area_want and abs(area - area_want) < abs(named[key]["area"] - area_want)):
                        named[key] = cand
        elif p.get("natural") == "water":
            water.append([list(c) for c in ring])

for k, v in named.items(): print(f"{k:12s} centro=({v['x']:7.1f},{v['y']:7.1f}) rot={math.degrees(v['rot']):6.1f}° WxL={v['w']:.0f}x{v['l']:.0f} m h={v['h']}")
print("vias:", {k: len(v) for k, v in roads.items()}, "prédios:", len(bld), "extrudados(h>=15):", sum(1 for b in bld if b[0] >= 15), "água:", len(water))
js = "window.MAPA=" + json.dumps({"roads": roads, "bld": bld, "water": water, "named": named}, separators=(",", ":")) + ";"
open(dst, "w", encoding="utf-8").write(js); print("ok", dst, round(len(js) / 1e6, 2), "MB")
