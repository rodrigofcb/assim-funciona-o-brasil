// Renderizador do cenário (canvas 2D + projeção própria). Chamado por seek(t) a cada frame.
(() => {
  const W = 1080, H = 1920;
  const cv = document.getElementById('cv'); cv.width = W; cv.height = H; const ctx = cv.getContext('2d');
  const M = window.MAPA, N = M.named, B = TL.beats;
  // tema (window.THEME): col = cores compartilhadas com a base; col3d = sub (prédios-tema), no ("não"/"contra"), dim (assento vazio); glow = intensidades
  const T = window.THEME || {};
  const COL = Object.assign({ line: '184,228,255', glow: '79,184,255', g: '43,214,110', y: '255,223,0', w: '255,255,255' }, T.col || {});
  Object.assign(COL, { sub: COL.line, no: COL.line, dim: COL.line }, T.col3d || {});
  const GL = Object.assign({ model: 0.6, lit: 1.4, pulse: 1.5, hl: 1.2, seat: 0.08 }, T.glow || {});
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
  // cúpula da Câmara: deslocada do centro das torres ao longo do eixo da plataforma (lado norte)
  const ax = [Math.cos(N.congresso.rot), Math.sin(N.congresso.rot)];
  const cupula = [N.congresso.x + 75 * ax[0], N.congresso.y + 75 * ax[1], 45];
  const planaltoTopo = [N.planalto.x, N.planalto.y, 30];

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
  const P = (c, p) => { const d = E3.sub(p, c.pos); const z = E3.dot(d, c.f); if (z < 2) return null; return [W / 2 + E3.dot(d, c.r) * c.fl / z, H / 2 - E3.dot(d, c.u) * c.fl / z, z]; };
  const onScreen = q => q && q[0] > -200 && q[0] < W + 200 && q[1] > -200 && q[1] < H + 200;

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
  const hlKeys = Object.keys(TL.hl || {});
  const hlRings = {}; for (const k of hlKeys) hlRings[k] = N[k].ring;
  const pulseAt = (t, b, dur = 1.6, hz = 1.3) => b === undefined ? 0 : (0.5 + 0.5 * Math.sin(2 * Math.PI * (t - b) * hz)) * sm((t - b) / 0.3) * (1 - sm((t - b - dur) / 0.5));

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

  // ---- cena 3: a lei viaja entre Congresso e Planalto (arco luminoso com rastro)
  function arc(A, Bp, s) { const z = lerp(A[2], Bp[2], s) + 110 * Math.sin(Math.PI * s); return [lerp(A[0], Bp[0], s), lerp(A[1], Bp[1], s), z]; }
  function token(c, t) {
    const legs = [[B.viaja1, cupula, planaltoTopo, COL.y], [B.viaja2, planaltoTopo, cupula, COL.g]];
    for (const [t0, A, Bp, col] of legs) {
      if (t0 === undefined || t < t0 - 0.4) continue;
      const s = sm((t - t0) / (TL.travel || 1.1)); const hold = t > t0 + (TL.travel || 1.1) ? 1 - sm((t - t0 - (TL.travel || 1.1) - 0.6) / 0.5) : 1;
      if (hold <= 0) continue;
      // rastro
      const s0 = Math.max(0, s - 0.42); const pts = []; for (let k = 0; k <= 24; k++) pts.push(P(c, arc(A, Bp, lerp(s0, s, k / 24))));
      if (pts.every(Boolean) && s > 0.001) {
        for (let k = 1; k <= 24; k++) { ctx.beginPath(); ctx.moveTo(pts[k - 1][0], pts[k - 1][1]); ctx.lineTo(pts[k][0], pts[k][1]);
          ctx.lineWidth = 2 + 8 * (k / 24); ctx.strokeStyle = `rgba(${col},${0.85 * hold * (k / 24) ** 1.5})`; ctx.stroke(); }
      }
      // cabeça: "documento" (retângulo pequeno) com brilho; antes de partir pulsa no ponto de origem
      const head = P(c, arc(A, Bp, s)); if (!head) continue;
      const pre = t < t0 ? 0.5 + 0.5 * Math.sin((t - t0) * 14) : 1;
      const g = ctx.createRadialGradient(head[0], head[1], 0, head[0], head[1], 70); g.addColorStop(0, `rgba(${col},${0.55 * hold * pre})`); g.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(head[0], head[1], 70, 0, 7); ctx.fill();
      ctx.save(); ctx.translate(head[0], head[1]); ctx.rotate(-0.25);
      ctx.fillStyle = `rgba(255,255,255,${0.95 * hold})`; ctx.fillRect(-14, -19, 28, 38);
      ctx.fillStyle = `rgba(${col},${0.9 * hold})`; for (let k = 0; k < 4; k++) ctx.fillRect(-9, -12 + k * 8, k === 3 ? 10 : 18, 3);
      ctx.restore();
    }
  }

  // ---- cenas 4 e 5: hemiciclo de 513 assentos no gramado da Esplanada, de frente para o Congresso
  const u = E3.norm([N.torre.x - N.congresso.x, N.torre.y - N.congresso.y, 0]);      // eixo monumental, do Congresso para a Torre
  const e1 = [-u[0], -u[1]], e2 = [-u[1], u[0]];                                      // e1 aponta para o Congresso; e2 = direita na tela
  const HC = [N.congresso.x + 700 * u[0], N.congresso.y + 700 * u[1]];                // centro do hemiciclo (diâmetro perpendicular ao eixo)
  const R0 = 58, SP = 7.6, SEAT = 2.6;                                                   // raio interno, passo entre fileiras/assentos, raio do ponto
  const seats = [];
  (function build() {
    let r = R0, rows = [];
    while (seats.length + rows.reduce((a, b) => a + b.length, 0) < 513) {
      const n = Math.round(Math.PI * r / SP); const row = [];
      for (let i = 0; i < n; i++) { const ph = Math.PI * (i + 0.5) / n; row.push({ r, ph }); }
      rows.push(row); r += SP;
    }
    let all = rows.flat(); const extra = all.length - 513; const last = rows[rows.length - 1];
    if (extra > 0) { const keep = last.filter((_, i) => i >= Math.floor(extra / 2) && i < last.length - Math.ceil(extra / 2)); all = rows.slice(0, -1).flat().concat(keep); }
    for (const s of all) { s.x = HC[0] + s.r * (Math.cos(s.ph) * e2[0] - Math.sin(s.ph) * e1[0]); s.y = HC[1] + s.r * (Math.cos(s.ph) * e2[1] - Math.sin(s.ph) * e1[1]); }
    all.sort((a, b) => b.ph - a.ph || a.r - b.r);   // da esquerda (ph=π) para a direita (ph=0)
    all.forEach((s, i) => { s.i = i; seats.push(s); });
  })();
  const RMAX = seats.reduce((m, s) => Math.max(m, s.r), 0);
  const seatAt = (i) => seats[Math.max(0, Math.min(seats.length - 1, i))];
  const polar = (r, ph, z = 0) => [HC[0] + r * (Math.cos(ph) * e2[0] - Math.sin(ph) * e1[0]), HC[1] + r * (Math.cos(ph) * e2[1] - Math.sin(ph) * e1[1]), z];
  const V4 = { sim: 252, nao: 176, quorum: 257 }, V5 = { com: 345, div: 63, contra: 86 };
  function seatState(s, t) {
    // devolve [cor, alpha, cheio?] para o assento s no instante t
    const idx = s.i, fromR = seats.length - 1 - idx;
    const dim = [COL.dim, 0.22, false];
    if (B.reset !== undefined && t >= B.reset) {
      const k = 1 - 0.75 * (1 - sm((t - B.reset) / 0.35));
      if (idx < V5.com * sm((t - B.com) / 1.6)) return [COL.g, 0.95, true];
      if (idx >= V5.com && idx < V5.com + V5.div * sm((t - B.div) / 0.7)) return [COL.w, 0.9, false];
      if (fromR < V5.contra * sm((t - B.contra) / 0.9)) return [COL.no, 0.95, true];
      return [COL.dim, 0.22 * k, false];
    }
    if (idx < V4.sim * sm((t - B.sim) / 1.6)) return [COL.y, 0.95, true];
    if (fromR < V4.nao * sm((t - B.nao) / 1.2)) return [COL.no, 0.95, true];
    if (B.rej !== undefined && t >= B.rej && idx >= V4.sim && idx < V4.quorum) return [COL.w, 0.45 + 0.5 * pulseAt(t, B.rej, 2.4, 2.2), false];
    return dim;
  }
  function hemiciclo(c, t) {
    if (B.seats === undefined || t < B.seats) return;
    const appear = sm((t - B.seats) / 0.9); const gone = B.fade !== undefined ? 1 - sm((t - B.fade + 0.6) / 0.6) : 1; if (gone <= 0) return;
    const px = SEAT * c.fl; let glowList = [];
    for (const s of seats) {
      if (s.i > appear * (seats.length + 40)) break;
      const q = P(c, [s.x, s.y, 0]); if (!q || !onScreen(q)) continue;
      const d = E3.norm(E3.sub([s.x, s.y, 0], c.pos)); const rr = px / q[2], ry = rr * Math.max(0.25, Math.abs(d[2]));
      const [col, a, full] = seatState(s, t);
      ctx.beginPath(); ctx.ellipse(q[0], q[1], rr, ry, 0, 0, 7);
      if (full) { ctx.fillStyle = `rgba(${col},${a * gone})`; ctx.fill(); glowList.push([q, rr, col, a]); }
      else { ctx.lineWidth = Math.max(1, rr * 0.35); ctx.strokeStyle = `rgba(${col},${a * gone})`; ctx.stroke(); }
    }
    // brilho suave dos cheios (uma passada só, barata)
    ctx.globalCompositeOperation = 'lighter';
    for (const [q, rr, col, a] of glowList) { ctx.beginPath(); ctx.arc(q[0], q[1], rr * 2.2, 0, 7); ctx.fillStyle = `rgba(${col},${GL.seat * a * gone})`; ctx.fill(); }
    ctx.globalCompositeOperation = 'source-over';
    // linha do quórum (257) na cena 4
    if (B.lim !== undefined && t >= B.lim && (B.reset === undefined || t < B.reset)) {
      const a = sm((t - B.lim) / 0.4) * (B.reset !== undefined ? 1 - sm((t - B.reset + 0.3) / 0.3) : 1);
      const ph = seatAt(V4.quorum).ph; const p0 = P(c, polar(R0 - 14, ph)), p1 = P(c, polar(RMAX + 26, ph));
      if (p0 && p1) { ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.lineWidth = 7; ctx.strokeStyle = `rgba(255,255,255,${0.25 * a})`; ctx.stroke(); ctx.lineWidth = 3; ctx.strokeStyle = `rgba(255,255,255,${0.95 * a})`; ctx.stroke(); }
    }
  }
  // ponto 3D de ancoragem para rótulos pinados
  const anchors = {
    congresso: () => [cupula[0], cupula[1], 125], planalto: () => [N.planalto.x, N.planalto.y, 95],
    quorum: () => polar(RMAX + 40, seatAt(V4.quorum).ph, 0), hemi: () => polar(RMAX + 30, Math.PI / 2, 0),
  };
  for (const k of hlKeys) anchors[k] = () => [N[k].x, N[k].y, k === 'saude' ? 150 : 70];

  // ---- rótulos DOM pinados a pontos 3D
  const pins = [...document.querySelectorAll('.pin, .lab')].map(el => {
    const key = el.dataset.key; const inB = el.dataset.from ? B[el.dataset.from] : B[TL.hl[key]]; const outB = el.dataset.to ? B[el.dataset.to] : B.s2bout;
    return { el, key, inB, outB: outB + 0.45 };
  });

  window.__dbg = { P, camAt, HC, u, polar, RMAX, N };
  window.draw3d = function (t) {
    const c = camAt(t);
    const D = c.dist; const px = m => Math.max(0.6, Math.min(5, m * c.fl / D));
    Mapa3D.drawBase(c, t, {});
    // destaques dos ministérios
    const hlOff = B.s3t !== undefined ? 1 - sm((t - B.s3t + 0.8) / 0.6) : 1;
    for (const k of hlKeys) { const b = B[TL.hl[k]]; const a = sm((t - b) / 0.6) * hlOff; if (a <= 0) continue;
      const ring = hlRings[k], lines = extrude(ring, 38);
      ctx.beginPath(); for (const p of ring) { const q = P(c, [p[0], p[1], 38]); if (!q) break; ctx.lineTo(q[0], q[1]); } ctx.closePath(); ctx.fillStyle = `rgba(${COL.g},${0.35 * a})`; ctx.fill();
      stroke3d(c, lines, px(1.8), 0.95 * a, COL.g, 1, GL.hl); }
    hemiciclo(c, t);
    // modelos (construção progressiva + brilho)
    for (const [k, win] of Object.entries(TL.build)) { const f = sm((t - win[0]) / (win[1] - win[0])); if (f <= 0) continue;
      const lit = k === 'planalto' ? sm((t - B.pres) / 0.8) : k === 'congresso' ? sm((t - B.cong) / 0.8) : 0;
      let pulse = 0, col = k === 'planalto' ? (lit > 0 ? COL.g : COL.sub) : k === 'congresso' ? (lit > 0 ? COL.y : COL.sub) : COL.sub;
      if (k === 'congresso') pulse = Math.max(pulseAt(t, B.cria, 2.4, 1.2), pulseAt(t, B.aprova, 0.9, 1.6), pulseAt(t, B.derruba, 1.6, 1.4));
      if (k === 'planalto') { pulse = Math.max(pulseAt(t, B.sanc, 1.0, 1.6), pulseAt(t, B.veta, 0.7, 3.0)); if (B.veta !== undefined && t >= B.veta && t < B.veta + 0.7) col = COL.w; }
      stroke3d(c, models[k], px(k === 'stf' ? 1.6 : 2.0), 0.55 + 0.45 * Math.max(lit, f < 1 ? 1 : 0), col, f, GL.model + GL.lit * lit + GL.pulse * pulse); }
    beam(c, t);
    token(c, t);
    // rótulos pinados
    for (const p of pins) { const el = p.el;
      if (p.inB === undefined || t < p.inB || t > p.outB) { el.style.display = 'none'; continue; }
      const q = P(c, anchors[p.key]()); if (!onScreen(q)) { el.style.display = 'none'; continue; }
      el.style.display = '';
      const hw = el.classList.contains('lab') ? el.firstElementChild.offsetWidth / 2 + 28 : 0; const x = Math.max(hw, Math.min(W - hw, q[0]));
      el.style.transform = `translate(${x.toFixed(1)}px,${q[1].toFixed(1)}px) translate(-50%,-100%)`; }
  };
})();
