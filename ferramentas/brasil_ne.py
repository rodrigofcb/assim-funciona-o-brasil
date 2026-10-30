"""Brasil, estados e vizinhos (Natural Earth, domínio público) em metros, projeção azimutal equidistante centrada em Brasília.

Uso: python3 brasil_ne.py <ne_10m_admin_1.geojson> <ne_50m_admin_0.geojson> <saida.js>
Saída: window.BRASIL = {br: [anéis], uf: {sigla: {rings, cx, cy, nome}}, viz: [anéis], capitais: {sigla:[x,y]}}
A mesma projeção (azeq) deve ser usada para todos os dados do mapa; perto de Brasília ela coincide com o plano métrico local.
"""
import sys, json, math
R = 6371008.8
LAT0, LON0 = math.radians(-15.7997), math.radians(-47.8644)
def azeq(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    c = math.acos(max(-1, min(1, math.sin(LAT0) * math.sin(phi) + math.cos(LAT0) * math.cos(phi) * math.cos(lam - LON0))))
    k = 1.0 if c < 1e-12 else c / math.sin(c)
    x = R * k * math.cos(phi) * math.sin(lam - LON0)
    y = R * k * (math.cos(LAT0) * math.sin(phi) - math.sin(LAT0) * math.cos(phi) * math.cos(lam - LON0))
    return (round(x), round(y))
def rings_of(geom):
    if geom["type"] == "Polygon": return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon": return [p[0] for p in geom["coordinates"]]
    return []
import sys as _s; _s.setrecursionlimit(20000)
def simplify(pts, tol):
    # Douglas-Peucker simples (em metros)
    if len(pts) < 3: return pts
    def dp(a, b):
        if b - a < 2: return [pts[a], pts[b]]
        ax, ay = pts[a]; bx, by = pts[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1
        imax, dmax = a, -1
        for i in range(a + 1, b):
            px, py = pts[i]; d = abs(dy * px - dx * py + bx * ay - by * ax) / L
            if d > dmax: imax, dmax = i, d
        if dmax > tol: return dp(a, imax)[:-1] + dp(imax, b)
        return [pts[a], pts[b]]
    if pts[0] == pts[-1]:   # anel fechado: divide no ponto mais distante do início
        k = max(range(1, len(pts) - 1), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
        return dp(0, k)[:-1] + dp(k, len(pts) - 1)
    return dp(0, len(pts) - 1)

a1, a0, dst = sys.argv[1:4]
A1 = json.load(open(a1, encoding="utf-8")); A0 = json.load(open(a0, encoding="utf-8"))
uf = {}; br = []
for f in A1["features"]:
    p = f["properties"]
    if p.get("adm0_a3") != "BRA": continue
    sig = (p.get("postal") or p.get("iso_3166_2", "").split("-")[-1]).upper()
    rings = [simplify([azeq(*c) for c in r], 1500) for r in rings_of(f["geometry"])]
    rings = [r for r in rings if len(r) >= 4]
    if not rings: continue
    big = max(rings, key=len); cx = sum(x for x, _ in big) / len(big); cy = sum(y for _, y in big) / len(big)
    uf[sig] = {"nome": p.get("name"), "rings": rings, "cx": round(cx), "cy": round(cy)}
viz = []
for f in A0["features"]:
    p = f["properties"]; iso = p.get("ADM0_A3") or p.get("adm0_a3")
    if iso == "BRA":
        br = [simplify([azeq(*c) for c in r], 1500) for r in rings_of(f["geometry"])]; br = [r for r in br if len(r) >= 4]
    elif iso in ("ARG", "URY", "PRY", "BOL", "PER", "COL", "VEN", "GUY", "SUR", "GUF", "FRA", "CHL", "ECU"):
        for r in rings_of(f["geometry"]):
            s = simplify([azeq(*c) for c in r], 4000)
            if len(s) >= 4 and min(math.hypot(x, y) for x, y in s) < 3.2e6: viz.append(s)
capitais = {"AC": (-67.81, -9.97), "AL": (-35.73, -9.67), "AP": (-51.07, 0.03), "AM": (-60.02, -3.12), "BA": (-38.51, -12.97), "CE": (-38.54, -3.72),
            "DF": (-47.86, -15.80), "ES": (-40.31, -20.32), "GO": (-49.25, -16.68), "MA": (-44.30, -2.53), "MT": (-56.10, -15.60), "MS": (-54.62, -20.44),
            "MG": (-43.94, -19.92), "PA": (-48.50, -1.46), "PB": (-34.86, -7.12), "PR": (-49.27, -25.43), "PE": (-34.88, -8.05), "PI": (-42.80, -5.09),
            "RJ": (-43.17, -22.91), "RN": (-35.21, -5.79), "RS": (-51.23, -30.03), "RO": (-63.90, -8.76), "RR": (-60.67, 2.82), "SC": (-48.55, -27.60),
            "SP": (-46.63, -23.55), "SE": (-37.07, -10.91), "TO": (-48.33, -10.18)}
cap = {k: azeq(*v) for k, v in capitais.items()}
js = "window.BRASIL=" + json.dumps({"br": br, "uf": uf, "viz": viz, "capitais": cap}, separators=(",", ":"), ensure_ascii=False) + ";"
open(dst, "w", encoding="utf-8").write(js)
print("UFs:", len(uf), sorted(uf)[:6], "... anéis BR:", len(br), "pontos BR:", sum(len(r) for r in br), "vizinhos:", len(viz), "tamanho: %.2f MB" % (len(js) / 1e6))
