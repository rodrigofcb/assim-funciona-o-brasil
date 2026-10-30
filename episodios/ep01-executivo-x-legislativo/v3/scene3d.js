// Renderizador do cenário (canvas 2D + projeção própria). Chamado por seek(t) a cada frame.
(() => {
  const W = 1080, H = 1920;
  const cv = document.getElementById('cv'); cv.width = W; cv.height = H; const ctx = cv.getContext('2d');
  const M = window.MAPA, N = M.named, B = TL.beats;
  const COL = { line: '184,228,255', glow: '79,184,255', g: '43,214,110', y: '255,223,0' };
  const sm = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
  const lerp = (a, b, k) => a + (b - a) * k;
  const deg = Math.PI / 180;

  // ---- modelos nas posições reais (rotações a partir do eixo principal das plantas do OSM)
  const models = {
    congresso: E3.T(E3.congresso(), N.congresso.x, N.congresso.y, 0, N.congresso.rot - 90 * deg),
    planalto:  E3.T(E3.planalto(),  N.planalto.x,  N.planalto.y,  0, N.planalto.rot - 180 * deg),
    stf:       E3.T(E3.stf(),       N.stf.x,       N.stf.y,       0, N.stf.rot + 180 * deg),
  };
  const topoTorre = [N.congresso.x, N.congresso.y, 110];

  // ---- câmera interpolada (smoothstep entre keyframes)
  function camAt(t) {
    if (TL.zoom && t < TL.handoff) return Mapa3D.camAt(t, TL.zoom);
    const K = TL.cam; let i = 0; while (i < K.length - 2 && t > K[i + 1][0]) i++;
    const a = K[i], b = K[i + 1]; const k = sm((t - a[0]) / Math.max(1e-6, b[0] - a[0]));
    const v = j => lerp(a[j], b[j], k);
    const pos = [v(1), v(2), v(3)], tgt = [v(4), v(5), v(6)], fov = v(7);
    const ua = a[8] || [0, 0, 1], ub = b[8] || [0, 0, 1]; const up = E3.norm([lerp(ua[0], ub[0], k), lerp(ua[1], ub[1], k), lerp(ua[2], ub[2], k)]);
    return Mapa3D.make(pos, tgt, fov, up, pos[2]);
  }
  function cameraUp(pos, target, fovDeg, up) {
    const f = E3.norm(E3.sub(target, pos));
    let r = E3.norm(E3.cross(f, up)); if (!isFinite(r[0]) || Math.hypot(...r) < 1e-6) r = [1, 0, 0];
    const u = E3.cross(r, f); const fl = (H / 2) / Math.tan(fovDeg * Math.PI / 360);
    return { pos, f, r, u, fl, W, H, dist: Math.hypot(...E3.sub(target, pos)) };
  }
  const P = (c, p) => { const d = E3.sub(p, c.pos); const z = E3.dot(d, c.f); if (z < 2) return null; return [W / 2 + E3.dot(d, c.r) * c.fl / z, H / 2 - E3.dot(d, c.u) * c.fl / z, z]; };
  const onScreen = q => q && q[0] > -200 && q[0] < W + 200 && q[1] > -200 && q[1] < H + 200;

  // desenha um lote de polilinhas (2D no chão, z=0) numa só path
  function batch(c, lines, z, closeIt) {
    let any = false; ctx.beginPath(); const lim = (2.4 * c.dist + 500) ** 2;
    for (const pl of lines) {
      const dx = pl[0][0] - c.pos[0], dy = pl[0][1] - c.pos[1]; if (dx * dx + dy * dy > lim) continue;
      let pen = false, vis = false; const pts = [];
      for (let i = 0; i < pl.length; i++) { const q = P(c, [pl[i][0], pl[i][1], z]); if (!q) { pen = false; continue; } pts.push(q); if (onScreen(q)) vis = true; }
      if (!vis) continue; any = true;
      for (let i = 0; i < pts.length; i++) { if (i === 0) ctx.moveTo(pts[i][0], pts[i][1]); else ctx.lineTo(pts[i][0], pts[i][1]); }
      if (closeIt) ctx.closePath();
    }
    return any;
  }
  function strokeLines(c, lines, width, alpha, col = COL.line, closeIt = false, z = 0) {
    if (!batch(c, lines, z, closeIt)) return;
    ctx.lineWidth = width; ctx.strokeStyle = `rgba(${col},${alpha})`; ctx.stroke();
  }
  // polilinhas 3D genéricas (modelos, extrusões): path única
  function path3d(c, lines, frac = 1) {
    ctx.beginPath(); const nTot = lines.length; const nFull = Math.floor(frac * nTot);
    for (let li = 0; li < nTot; li++) {
      const pl = lines[li]; let upto = pl.length;
      if (li > nFull) break;
      if (li === nFull) { upto = Math.max(2, Math.ceil((frac * nTot - nFull) * pl.length)); if (frac >= 1) upto = pl.length; }
      let pen = false;
      for (let i = 0; i < upto; i++) { const q = P(c, pl[i]); if (!q) { pen = false; continue; } if (!pen) { ctx.moveTo(q[0], q[1]); pen = true; } else ctx.lineTo(q[0], q[1]); }
    }
  }
  function stroke3d(c, lines, width, alpha, col = COL.line, frac = 1, glow = 0) {
    path3d(c, lines, frac);
    if (glow > 0) { ctx.lineWidth = width * 5; ctx.strokeStyle = `rgba(${col},${alpha * 0.18 * glow})`; ctx.stroke(); }
    ctx.lineWidth = width; ctx.strokeStyle = `rgba(${col},${alpha})`; ctx.stroke();
  }
  // caixa extrudada a partir de uma planta
  function extrude(ring, h) {
    const bot = ring.map(([x, y]) => [x, y, 0]), top = ring.map(([x, y]) => [x, y, h]); const L = [bot, top];
    const step = Math.max(1, Math.floor(ring.length / 6)); for (let i = 0; i < ring.length - 1; i += step) L.push([bot[i], top[i]]);
    return L;
  }
  const extr = M.bld.filter(b => b[0] >= 15).map(b => ({ h: b[0], ring: b.slice(1), lines: extrude(b.slice(1), b[0]), c: cen(b.slice(1)) }));
  function cen(r) { let x = 0, y = 0; for (const p of r) { x += p[0]; y += p[1]; } return [x / r.length, y / r.length]; }
  const foot = M.bld.map(b => b.slice(1));
  const hlKeys = Object.keys(TL.hl || {});
  const hlRings = {}; for (const k of hlKeys) hlRings[k] = N[k].ring;

  // ---- holofote: cone do topo das torres até o chão, varrendo a Esplanada
  function beam(c, t) {
    const b0 = B.beam, k = (t - b0) / 2.2; if (k < 0 || k > 1) return;
    const alpha = Math.sin(Math.PI * Math.min(1, k)) ** 0.6 * 0.55;
    const ang = lerp(-17.9 * deg + 28 * deg, -17.9 * deg - 22 * deg, sm(k)) + Math.PI; // aponta para oeste (Esplanada), varrendo
    const reach = 1200, spread = 9 * deg, cx = topoTorre[0], cy = topoTorre[1];
    const pts = []; for (let a = -spread; a <= spread + 1e-6; a += spread / 6) pts.push([cx + reach * Math.cos(ang + a), cy + reach * Math.sin(ang + a), 0]);
    const apex = P(c, topoTorre); if (!apex) return;
    ctx.beginPath(); ctx.moveTo(apex[0], apex[1]); let ok = true;
    for (const p of pts) { const q = P(c, p); if (!q) { ok = false; break; } ctx.lineTo(q[0], q[1]); }
    if (!ok) return; ctx.closePath();
    const far = P(c, pts[6]); const gr = ctx.createLinearGradient(apex[0], apex[1], far[0], far[1]);
    gr.addColorStop(0, `rgba(${COL.y},${alpha})`); gr.addColorStop(1, `rgba(${COL.y},0)`); ctx.fillStyle = gr; ctx.fill();
    // mancha no chão
    const hit = [cx + 700 * Math.cos(ang), cy + 700 * Math.sin(ang)]; const ring = E3.circle(hit[0], hit[1], 0.5, 160, 36);
    ctx.beginPath(); let first = true; for (const p of ring) { const q = P(c, p); if (!q) return; if (first) { ctx.moveTo(q[0], q[1]); first = false; } else ctx.lineTo(q[0], q[1]); }
    ctx.fillStyle = `rgba(${COL.y},${alpha * 0.35})`; ctx.fill();
  }

  // ---- pinos (ícones DOM) sobre os ministérios destacados
  const pins = {}; for (const el of document.querySelectorAll('.pin')) pins[el.dataset.key] = el;

  window.draw3d = function (t) {
    const c = camAt(t);
    const D = c.dist; const px = m => Math.max(0.6, Math.min(5, m * c.fl / D));
    Mapa3D.drawBase(c, t, {});
    // destaques dos ministérios
    for (const k of hlKeys) { const b = B[TL.hl[k]]; const a = sm((t - b) / 0.6); if (a <= 0) continue;
      const ring = hlRings[k], lines = extrude(ring, 38);
      ctx.beginPath(); for (const p of ring) { const q = P(c, [p[0], p[1], 38]); if (!q) break; ctx.lineTo(q[0], q[1]); } ctx.closePath(); ctx.fillStyle = `rgba(${COL.g},${0.35 * a})`; ctx.fill();
      stroke3d(c, lines, px(1.8), 0.95 * a, COL.g, 1, 1.2); }
    // modelos (construção progressiva + brilho)
    for (const [k, win] of Object.entries(TL.build)) { const f = sm((t - win[0]) / (win[1] - win[0])); if (f <= 0) continue;
      const lit = k === 'planalto' ? sm((t - B.pres) / 0.8) : k === 'congresso' ? sm((t - B.cong) / 0.8) : 0;
      const pulse = k === 'congresso' ? 0.5 + 0.5 * Math.sin(2 * Math.PI * (t - B.cria) * 1.2) * sm((t - B.cria) / 0.4) * (1 - sm((t - B.cria - 2.4) / 0.6)) : 0;
      const col = k === 'planalto' ? (lit > 0 ? COL.g : COL.line) : k === 'congresso' ? (lit > 0 ? COL.y : COL.line) : COL.line;
      stroke3d(c, models[k], px(k === 'stf' ? 1.6 : 2.0), 0.55 + 0.45 * Math.max(lit, f < 1 ? 1 : 0), col, f, 0.6 + 1.4 * lit + 1.5 * pulse); }
    beam(c, t);
    // pinos
    for (const k in pins) { const b = B[TL.hl[k]]; const el = pins[k]; const q = P(c, [N[k].x, N[k].y, k === 'saude' ? 150 : 70]);
      if (t < b || t > B.s2bout + 0.45 || !onScreen(q)) { el.style.display = 'none'; continue; }
      el.style.display = ''; el.style.transform = `translate(${q[0].toFixed(1)}px,${q[1].toFixed(1)}px) translate(-50%,-100%)`; }
  };
})();
