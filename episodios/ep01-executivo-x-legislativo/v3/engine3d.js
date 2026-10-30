// Mini-engine 3D: projeta polilinhas (metros, z para cima) em SVG com câmera perspectiva.
// Modelos paramétricos do Congresso Nacional e do Palácio do Planalto (dimensões aproximadas).
window.E3 = (() => {
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const norm = a => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

  function camera(pos, target, fovDeg, W, H) {
    const f = norm(sub(target, pos));
    let r = norm(cross(f, [0, 0, 1])); if (!isFinite(r[0]) || Math.hypot(...r) < 1e-6) r = [1, 0, 0];
    const u = cross(r, f);
    const fl = (H / 2) / Math.tan(fovDeg * Math.PI / 360);
    return { pos, f, r, u, fl, W, H };
  }
  function project(c, p) {
    const d = sub(p, c.pos); const z = dot(d, c.f);
    if (z < 1) return null;
    return [c.W / 2 + dot(d, c.r) * c.fl / z, c.H / 2 - dot(d, c.u) * c.fl / z, z];
  }
  // polilinha 3D -> string de path SVG (corta segmentos atrás da câmera)
  function path(c, pts) {
    let s = "", pen = false;
    for (const p of pts) { const q = project(c, p); if (!q) { pen = false; continue; } s += (pen ? "L" : "M") + q[0].toFixed(1) + " " + q[1].toFixed(1); pen = true; }
    return s;
  }
  const box = (x0, x1, y0, y1, z0, z1) => {
    const P = (x, y, z) => [x, y, z];
    return [[P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), P(x0, y0, z0)],
            [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), P(x0, y0, z1)],
            [P(x0, y0, z0), P(x0, y0, z1)], [P(x1, y0, z0), P(x1, y0, z1)], [P(x1, y1, z0), P(x1, y1, z1)], [P(x0, y1, z0), P(x0, y1, z1)]];
  };
  const circle = (cx, cy, z, r, n = 48) => Array.from({ length: n + 1 }, (_, i) => { const a = 2 * Math.PI * i / n; return [cx + r * Math.cos(a), cy + r * Math.sin(a), z]; });
  // cúpula / concha: perfil r(h) de h=0 (base) a h=H (topo), com paralelos e meridianos
  function shell(cx, cy, z0, H, rOf, nPar = 5, nMer = 8) {
    const out = [];
    for (let k = 0; k <= nPar; k++) { const h = H * k / nPar; const r = rOf(h); if (r > 0.5) out.push(circle(cx, cy, z0 + h, r)); }
    for (let m = 0; m < nMer; m++) { const a = Math.PI * m / nMer; const pts = [];
      for (let k = -nPar * 2; k <= nPar * 2; k++) { const h = H * Math.abs(k) / (nPar * 2); const r = rOf(h) * Math.sign(k || 1); pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a), z0 + h]); }
      out.push(pts); }
    return out;
  }
  const T = (lines, dx, dy, dz = 0, rot = 0, k = 1) => lines.map(pl => pl.map(([x, y, z]) => {
    const c = Math.cos(rot), s = Math.sin(rot); x *= k; y *= k; z *= k; return [dx + x * c - y * s, dy + x * s + y * c, dz + z]; }));

  function congresso() {
    const L = [];
    L.push(...box(-40, 40, -120, 120, 0, 10));                                   // plataforma
    L.push(...shell(0, 60, 10, 24, h => 30 * Math.sqrt(Math.max(0, 1 - (h / 24) ** 2))));          // cúpula (Senado)
    L.push(...shell(0, -62, 10, 23, h => 9 + 27 * Math.pow(h / 23, 0.62)));                           // concha (Câmara)
    L.push(...box(-22, 22, 5, 17, 10, 100)); L.push(...box(-22, 22, -17, -5, 10, 100));            // torres
    L.push(...box(-22, 22, -5, 5, 46, 56));                                                           // passarela entre torres
    for (let z = 10 + 14.3; z < 99; z += 14.3) { L.push([[-22, 17, z], [22, 17, z]], [[-22, -17, z], [22, -17, z]], [[-22, 17, z], [-22, 5, z]], [[-22, -5, z], [-22, -17, z]]); }
    L.push([[-40, -126, 0], [-40, 126, 0]]);                                                          // espelho d'água (sugestão)
    return L;
  }
  function planalto() {
    const L = [];
    L.push(...box(-58, 58, -30, 30, 0, 1));                                                           // base
    L.push(...box(-50, 50, -22, 22, 1, 18));                                                          // volume de vidro
    L.push(...box(-56, 56, -28, 28, 18, 19.6));                                                       // laje de cobertura
    for (const side of [-1, 1]) for (let x = -50; x <= 50; x += 20) {                                 // colunas curvas
      const y0 = 28 * side, o = v => y0 + v * side;
      L.push([[x - 3, y0, 1], [x - 3.6, o(6.5), 6], [x - 2.4, o(5.5), 12], [x - 1, o(0.8), 19.6], [x + 1, o(0.8), 19.6], [x + 2.4, o(5.5), 12], [x + 3.6, o(6.5), 6], [x + 3, y0, 1], [x - 3, y0, 1]]);
    }
    L.push([[-20, -62, 0.4], [-4, -62, 0.4], [-4, -28, 6], [-20, -28, 6], [-20, -62, 0.4]]);        // rampa
    L.push([[-20, -62, 1.4], [-20, -28, 7]], [[-4, -62, 1.4], [-4, -28, 7]]);
    return L;
  }
  function grid(cx, cy, half, step) {
    const L = [];
    for (let v = -half; v <= half; v += step) { L.push([[cx - half, cy + v, 0], [cx + half, cy + v, 0]]); L.push([[cx + v, cy - half, 0], [cx + v, cy + half, 0]]); }
    return L;
  }
  const stf = () => planalto().map(pl => pl.map(([x, y, z]) => [x * 0.72, y * 0.72, z * 0.72]));
  return { camera, project, path, box, circle, shell, T, congresso, planalto, stf, grid, sub, dot, norm, cross };
})();
