"""Vias principais e água da região de Brasília (o "avião") → vinheta/aviao.js, na projeção azimutal centrada em Brasília.

Uso: python3 aviao_osm.py <brasilia_aviao.geojson> <saida.js>
Classes: eixo (Eixo Monumental + Eixo Rodoviário: trunk/motorway dentro do Plano Piloto), pri (motorway/trunk/primary), sec (secondary).
"""
import sys, json, math
R = 6371008.8
LAT0, LON0 = math.radians(-15.7997), math.radians(-47.8644)
def azeq(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    c = math.acos(max(-1, min(1, math.sin(LAT0) * math.sin(phi) + math.cos(LAT0) * math.cos(phi) * math.cos(lam - LON0))))
    k = 1.0 if c < 1e-12 else c / math.sin(c)
    return (round(R * k * math.cos(phi) * math.sin(lam - LON0), 1), round(R * k * (math.cos(LAT0) * math.sin(phi) - math.sin(LAT0) * math.cos(phi) * math.cos(lam - LON0)), 1))
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
roads = {"eixo": [], "pri": [], "sec": []}; water = []
EIXO_NAMES = ("Eixo Monumental", "Eixo Rodoviário", "Eixo Rodoviario", "Eixo Rodoviário Norte", "Eixo Rodoviário Sul", "Eixo L", "Eixo W", "Eixão")
def dedupe(pts):
    out = []
    for p in pts:
        if not out or out[-1] != p: out.append(list(p))
    return out
nE = 0
for f in d["features"]:
    p, g = f["properties"], f["geometry"]
    if g["type"] == "LineString" and "highway" in p:
        line = dedupe([azeq(*c) for c in g["coordinates"]]); hw = p["highway"]; name = p.get("name", "") or ""
        if any(name.startswith(n) for n in EIXO_NAMES): roads["eixo"].append(line); nE += 1
        elif hw in ("motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"): roads["pri"].append(line)
        else: roads["sec"].append(line)
    elif g["type"] in ("Polygon", "MultiPolygon") and p.get("natural") == "water":
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [poly[0] for poly in g["coordinates"]]
        for r in rings:
            ring = dedupe([azeq(*c) for c in r])
            if len(ring) >= 4: water.append(ring)
names = {}
for f in d["features"]:
    n = f["properties"].get("name")
    if n and "Eixo" in n: names[n] = names.get(n, 0) + 1
print("eixo:", nE, "pri:", len(roads["pri"]), "sec:", len(roads["sec"]), "água:", len(water), "pontos água:", sum(len(r) for r in water))
print("nomes com 'Eixo':", sorted(names.items(), key=lambda x: -x[1])[:12])
js = "window.AVIAO=" + json.dumps({"roads": roads, "water": water}, separators=(",", ":")) + ";"
open(dst, "w", encoding="utf-8").write(js); print("ok", dst, round(len(js) / 1e6, 2), "MB")
