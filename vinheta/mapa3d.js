// Mapa multi-escala (país → cidade → Praça) em canvas, com câmera por (alvo, altitude, pitch, rumo).
// Requer: TL (timeline.js), BRASIL (brasil.js), MAPA (mapa.js, detalhe local), E3 (engine3d.js), opcional AVIAO (aviao.js).
window.Mapa3D = (() => {
  const W = 1080, H = 1920; const deg = Math.PI / 180;
  const sm = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
  const lerp = (a, b, k) => a + (b - a) * k;
  const COL = { line: '184,228,255', g: '43,214,110', y: '255,223,0', br: '255,236,120' };
  let ctx, cv;

  // ---- câmera: [t, tx, ty, h, pitch(graus, 0=zenital), rumo(graus: de onde a câmera olha; 270 = norte para cima)]
  function camAt(t, keys) {
    let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const a = keys[i], b = keys[i + 1]; const k = sm((t - a[0]) / Math.max(1e-6, b[0] - a[0]));
    const h = Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), k));
    // o alvo se aproxima proporcionalmente à altitude: o destino final fica parado na tela
    const r = (h - b[3]) / Math.max(1e-6, a[3] - b[3]); const rr = a[3] === b[3] ? 1 - k : Math.max(0, Math.min(1, r));
    const tx = b[1] + (a[1] - b[1]) * rr, ty = b[2] + (a[2] - b[2]) * rr;
    const pitch = lerp(a[4], b[4], k) * deg, yaw = lerp(a[5], b[5], k) * deg;
    const pos = [tx + h * Math.sin(pitch) * Math.cos(yaw), ty + h * Math.sin(pitch) * Math.sin(yaw), h * Math.cos(pitch) + (pitch > 0 ? 0 : 0)];
    const up = [-Math.cos(yaw), -Math.sin(yaw), 0];
    return make(pos, [tx, ty, 0], 50, up, h);
  }
  function make(pos, target, fovDeg, up, h) {
    const f = E3.norm(E3.sub(target, pos)); let r = E3.norm(E3.cross(f, up)); if (!isFinite(r[0]) || Math.hypot(...r) < 1e-6) r = [1, 0, 0];
    const u = E3.cross(r, f); const fl = (H / 2) / Math.tan(fovDeg * Math.PI / 360);
    return { pos, f, r, u, fl, dist: Math.hypot(...E3.sub(target, pos)), h, target };
  }
  const P = (c, p) => { const d = E3.sub(p, c.pos); const z = E3.dot(d, c.f); if (z < 2) return null; return [W / 2 + E3.dot(d, c.r) * c.fl / z, H / 2 - E3.dot(d, c.u) * c.fl / z, z]; };
  const onScreen = q => q && q[0] > -300 && q[0] < W + 300 && q[1] > -300 && q[1] < H + 300;

  function batch(c, lines, z, closeIt, lim2) {
    let any = false; ctx.beginPath();
    for (const pl of lines) {
      if (lim2) { const dx = pl[0][0] - c.target[0], dy = pl[0][1] - c.target[1]; if (dx * dx + dy * dy > lim2) continue; }
      let vis = false; const pts = [];
      for (let i = 0; i < pl.length; i++) { const q = P(c, [pl[i][0], pl[i][1], z]); if (!q) continue; pts.push(q); if (onScreen(q)) vis = true; }
      if (!vis || pts.length < 2) continue; any = true;
      ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      if (closeIt) ctx.closePath();
    }
    return any;
  }
  function stroke(c, lines, width, alpha, col = COL.line, closeIt = false, lim2 = 0) {
    if (alpha <= 0.003 || !batch(c, lines, 0, closeIt, lim2)) return;
    ctx.lineWidth = width; ctx.strokeStyle = `rgba(${col},${alpha})`; ctx.stroke();
  }
  function fill(c, lines, alpha, col, lim2 = 0) {
    if (alpha <= 0.003 || !batch(c, lines, 0, true, lim2)) return;
    ctx.fillStyle = `rgba(${col},${alpha})`; ctx.fill();
  }
  function path3d(c, lines, frac = 1) {
    ctx.beginPath(); const nTot = lines.length; const nFull = Math.floor(frac * nTot);
    for (let li = 0; li < nTot; li++) { const pl = lines[li]; let upto = pl.length; if (li > nFull) break;
      if (li === nFull) { upto = Math.max(2, Math.ceil((frac * nTot - nFull) * pl.length)); if (frac >= 1) upto = pl.length; }
      let pen = false; for (let i = 0; i < upto; i++) { const q = P(c, pl[i]); if (!q) { pen = false; continue; } if (!pen) { ctx.moveTo(q[0], q[1]); pen = true; } else ctx.lineTo(q[0], q[1]); } }
  }
  function stroke3d(c, lines, width, alpha, col = COL.line, frac = 1, glow = 0) {
    if (alpha <= 0.003) return; path3d(c, lines, frac);
    if (glow > 0) { ctx.lineWidth = width * 5; ctx.strokeStyle = `rgba(${col},${alpha * 0.18 * glow})`; ctx.stroke(); }
    ctx.lineWidth = width; ctx.strokeStyle = `rgba(${col},${alpha})`; ctx.stroke();
  }
  function extrude(ring, h) { const bot = ring.map(([x, y]) => [x, y, 0]), top = ring.map(([x, y]) => [x, y, h]); const L = [bot, top];
    const step = Math.max(1, Math.floor(ring.length / 6)); for (let i = 0; i < ring.length - 1; i += step) L.push([bot[i], top[i]]); return L; }
  const cen = r => { let x = 0, y = 0; for (const p of r) { x += p[0]; y += p[1]; } return [x / r.length, y / r.length]; };

  // ---- camadas
  const BR = window.BRASIL, M = window.MAPA, AV = window.AVIAO || null;
  const ufRings = []; for (const k in BR.uf) for (const r of BR.uf[k].rings) ufRings.push(r);
  const capPts = Object.entries(BR.capitais);
  const extr = M ? M.bld.filter(b => b[0] >= 15).map(b => ({ h: b[0], lines: extrude(b.slice(1), b[0]), c: cen(b.slice(1)) })) : [];
  const foot = M ? M.bld.map(b => b.slice(1)) : [];
  const fadeIn = (h, a, b) => sm((Math.log(a) - Math.log(h)) / (Math.log(a) - Math.log(b)));   // 0 em h=a (alto), 1 em h=b (baixo)

  function drawBase(c, t, opts) {
    const h = c.h; const px = m => Math.max(0.6, Math.min(5, m * c.fl / c.dist));
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    // névoa radial no alvo
    const tq = P(c, c.target) || [W / 2, H / 2]; const g = ctx.createRadialGradient(tq[0], tq[1], 0, tq[0], tq[1], 1300);
    g.addColorStop(0, 'rgba(70,120,220,0.20)'); g.addColorStop(1, 'rgba(70,120,220,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // país (some abaixo de ~40 km; o DF permanece até ~8 km)
    const aPais = 1 - fadeIn(h, 60000, 25000);
    if (aPais > 0) {
      stroke(c, BR.viz, 1.2, 0.16 * aPais);
      fill(c, BR.br, 0.07 * aPais, '120,180,255'); stroke(c, ufRings, 1.1, 0.30 * aPais);
      stroke(c, BR.br, 2.4, 0.95 * aPais, COL.br);
      // capitais
      const aCap = aPais * (1 - fadeIn(h, 2500000, 700000));
      if (aCap > 0.01) for (const [sig, p] of capPts) { const q = P(c, [p[0], p[1], 0]); if (!onScreen(q)) continue;
        ctx.beginPath(); ctx.arc(q[0], q[1], sig === 'DF' ? 0 : 4, 0, 7); ctx.fillStyle = `rgba(${COL.line},${0.55 * aCap})`; ctx.fill(); }
    }
    const aDF = 1 - fadeIn(h, 12000, 5000);
    if (aDF > 0 && BR.uf.DF) stroke(c, BR.uf.DF.rings, 1.6, 0.6 * aDF * fadeIn(h, 5000000, 400000), COL.line);
    // Brasília pulsando enquanto é um ponto
    const aDot = (1 - fadeIn(h, 140000, 60000)) * fadeIn(h, 9000000, 5000000);
    if (aDot > 0.01) { const q = P(c, [0, 0, 0]); const pul = 0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 1.1);
      ctx.beginPath(); ctx.arc(q[0], q[1], 9 + 18 * pul, 0, 7); ctx.strokeStyle = `rgba(${COL.y},${aDot * (0.9 - 0.7 * pul)})`; ctx.lineWidth = 3; ctx.stroke();
      ctx.beginPath(); ctx.arc(q[0], q[1], 7, 0, 7); ctx.fillStyle = `rgba(${COL.y},${aDot})`; ctx.fill(); }
    // cidade (avião): vias principais da região, do nível ~150 km até o detalhe
    const aCid = fadeIn(h, 450000, 60000);
    if (aCid > 0 && AV) {
      fill(c, AV.water, 0.18 * aCid, '80,150,255'); stroke(c, AV.water, px(6), 0.35 * aCid, '120,190,255', true);
      stroke(c, AV.roads.sec, px(14), 0.22 * aCid); stroke(c, AV.roads.pri, px(26), 0.55 * aCid);
      stroke(c, AV.roads.eixo, px(140), 0.18 * aCid, COL.br); stroke(c, AV.roads.eixo, px(40), 0.95 * aCid, COL.br);
    }
    // detalhe local (Esplanada): entra abaixo de ~20 km
    const aLoc = fadeIn(h, 20000, 4000);
    if (aLoc > 0 && M) {
      const lim2 = (2.4 * c.dist + 500) ** 2;
      fill(c, M.water, 0.10 * aLoc, '80,150,255', lim2);
      if (batch(c, foot, 0, true, lim2)) { ctx.fillStyle = `rgba(120,180,255,${0.07 * aLoc})`; ctx.fill(); ctx.lineWidth = px(1.2); ctx.strokeStyle = `rgba(${COL.line},${0.22 * aLoc})`; ctx.stroke(); }
      stroke(c, M.roads.minor, px(1.0), 0.16 * aLoc, COL.line, false, lim2);
      stroke(c, M.roads.mid, px(2.2), 0.32 * aLoc, COL.line, false, lim2);
      stroke(c, M.roads.major, px(4.5), 0.55 * aLoc * (AV ? 1 - 0.5 * aCid * (1 - aLoc) : 1), COL.line, false, lim2);
      const aEx = fadeIn(h, 9000, 3000);
      if (aEx > 0) { ctx.beginPath(); let any = false;
        for (const e of extr) { const d = Math.hypot(e.c[0] - c.pos[0], e.c[1] - c.pos[1]); if (d > 2.2 * c.dist + 400) continue; const q = P(c, [e.c[0], e.c[1], 0]); if (!onScreen(q)) continue; any = true;
          for (const pl of e.lines) { let pen = false; for (const p of pl) { const qq = P(c, p); if (!qq) { pen = false; continue; } if (!pen) { ctx.moveTo(qq[0], qq[1]); pen = true; } else ctx.lineTo(qq[0], qq[1]); } } }
        if (any) { ctx.lineWidth = px(1.4); ctx.strokeStyle = `rgba(${COL.line},${0.35 * aEx})`; ctx.stroke(); } }
    }
    return { px, aLoc };
  }
  function init(canvasId) { cv = document.getElementById(canvasId); cv.width = W; cv.height = H; ctx = cv.getContext('2d'); return ctx; }
  return { init, camAt, make, P, onScreen, drawBase, stroke3d, extrude, fill, stroke, COL, sm, lerp, deg, ctx: () => ctx };
})();
