'use strict';
/* =====================================================================
   LIVE STANDINGS — daily data-driven motion engine (Canvas2D, deterministic)
   120 BPM -> 1 beat = 0.5 s.
   URL params: fmt=h|p  pool  main  raffle  multi  date  ends  left  round
               top = JSON [[name, wagered, prize], ...] rank order, up to 5
   ===================================================================== */
const Q = new URLSearchParams(location.search);
const FMT = Q.get('fmt') || 'h';
const V = FMT === 'v' || FMT === 'p', P4 = FMT === 'p';
const W = V ? 1080 : 1920, H = P4 ? 1350 : V ? 1920 : 1080, FPS = 30;
const POOL = Math.max(10000, Math.round(+(Q.get('pool') || 13053)));
const PRZ = [
  Math.round(+(Q.get('main') || POOL * 0.9)),
  Math.round(+(Q.get('raffle') || Math.floor(POOL * 0.05))),
  Math.round(+(Q.get('multi') || Math.floor(POOL * 0.05))),
];
const DATE = (Q.get('date') || 'FRI OCT 9').toUpperCase();
const ENDS = (Q.get('ends') === null ? 'OCT 15' : Q.get('ends')).toUpperCase();
const LEFT = Q.get('left') === null ? 6 : parseInt(Q.get('left'), 10);
const ROUND = Q.get('round') === null ? '01' : Q.get('round');
const INTRO = Math.max(0, parseInt(Q.get('intro') || '0', 10)) % 4;   // daily-rotating intro style
const HEAD = Math.max(0, parseInt(Q.get('head') || '0', 10));           // headline pick for the slam intro
const HL = [Q.get('h1'), Q.get('h2')].filter(s => s && s.trim()).map(s => s.trim().toUpperCase().slice(0, 22));   // today's headline (1-2 lines)
const PLATE = Q.get('plate') === '1';   // plate mode: transparent graphics, composited over the Higgsfield footage by render.py
if (PLATE) { document.documentElement.style.background = 'transparent'; document.body.style.background = 'transparent'; }
const TOP = (() => {
  try { const a = JSON.parse(Q.get('top') || 'null'); if (Array.isArray(a)) return a.slice(0, 5).map(r => ({ name: String(r[0]), wag: +r[1], prize: +r[2] })); } catch (e) { }
  return [['Inne****', 276431.57, 4111], ['Jame********', 108574.22, 1762], ['AkaC***', 75255.58, 1174], ['Fros*********', 62400.94, 704], ['Span*****', 57289.29, 587]]
    .map(r => ({ name: r[0], wag: r[1], prize: r[2] }));
})();
const GOLD = '#EEAF0E', GOLD_L = '#FFD34D', GOLD_D = '#D99A00', INK = '#0A0A0A';
const GOLD_RGB = [238, 175, 14];
const money = v => '$' + Math.round(v).toLocaleString('en-US');

const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const SUB = document.createElement('canvas'); SUB.width = W; SUB.height = H;
const sctx = SUB.getContext('2d');
const MC = document.createElement('canvas').getContext('2d');
/* ---------------- math ---------------- */
const clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x;
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, t0, d) => clamp((t - t0) / d);
const E = {
  lin: t => t,
  inQuad: t => t * t, outQuad: t => 1 - (1 - t) * (1 - t),
  inCubic: t => t * t * t, outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  inQuart: t => t * t * t * t, outQuart: t => 1 - Math.pow(1 - t, 4),
  inOutQuart: t => t < .5 ? 8 * t ** 4 : 1 - Math.pow(-2 * t + 2, 4) / 2,
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inExpo: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
  inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  inBack: (t, s = 1.70158) => (s + 1) * t * t * t - s * t * t,
};
function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
const beatPulse = (t, k = 6) => { if (t < 0) return 0; const lb = Math.floor(t / 0.5) * 0.5; return Math.exp(-(t - lb) * k); };

/* ---------------- master timeline (14.0 s) ----------------
   0.0  hook: WHO'S WINNING? + live date
   1.5  total pool odometer, lands on 3.0, then shrinks into the header
   4.0  standings tower: 5th -> 2nd on the beat, 1st lands on 6.5; prize ticker runs underneath
   9.0  flip-clock: days left in the round
   10.5 end card (Roobet / code / site)                         */
const TL = { x1: 1.5, c0: 1.75, c1: 3.0, m0: 3.45, m1: 3.95, rows: [6.5, 5.5, 5.0, 4.5, 4.0], tick0: 4.1,
  x2: 9.0, flip: 9.5, x3: 10.5, end: 10.55, fin: 13.0, DUR: 14.0 };
const BARS = 0.36;   // shutter transition length, centred on x1 / x2 / x3
const IMPACTS = [
  [0.00, 9, 9], [1.50, 7, 10], [3.00, 24, 6.5],
  [4.00, 5, 12], [4.50, 5, 12], [5.00, 6, 12], [5.50, 7, 12], [6.50, 22, 7],
  [9.00, 7, 10], [9.50, 12, 9],
  [TL.end + 0.15, 9, 10], [TL.end + 0.78, 11, 10], [TL.fin, 7, 10],
];
const FLASHES = [
  [3.00, [255, 255, 255], 0.40, 9], [6.50, GOLD_RGB, 0.30, 8], [9.50, GOLD_RGB, 0.12, 10],
  [TL.end + 0.15, GOLD_RGB, 0.16, 10], [TL.fin, GOLD_RGB, 0.14, 8],
];
window.CUES = { IMPACTS, FLASHES, TL, POOL, PRZ, TOP };
function shake(t) {
  let x = 0, y = 0, r = 0;
  for (const [ti, a, k] of IMPACTS) {
    if (t < ti) continue; const p = t - ti; const e = a * Math.exp(-p * k);
    if (e < 0.05) continue;
    x += e * (Math.cos(p * 71.3 + ti * 3.1) * 0.65 + Math.sin(p * 131.7 + ti) * 0.35);
    y += e * (Math.sin(p * 83.9 + ti * 1.7) * 0.65 + Math.cos(p * 117.1 + ti * 2.3) * 0.35);
    r += e * 0.00035 * Math.sin(p * 61.0 + ti);
  }
  return { x, y, r };
}

/* ---------------- assets ---------------- */
const A = {};
let LOGO = null, RIDGE = null;
function loadImg(k, src) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => { A[k] = i; res(); }; i.onerror = rej; i.src = src; }); }
const CAP = {};
async function init() {
  const base = './';
  await Promise.all([
    loadImg('graph', base + 'assets/Graph-Master.png'),
    loadImg('mascot', base + 'assets/Mascot-Transparent.png'),
    loadImg('p90', base + 'assets/Prize-90-Percent.png'),
    loadImg('p5', base + 'assets/Prize-5-Percent.png'),
    loadImg('ticket', base + 'assets/Raffle-Ticket.png'),
    loadImg('reels', base + 'assets/Slot-Reels.png'),
    document.fonts.load('100px PB'), document.fonts.load('100px PBI'),
    document.fonts.load('100px PM'), document.fonts.load('100px PR'),
  ]);
  const lg = await (await fetch(base + 'logo_groups.json')).json();
  LOGO = lg.map(g => ({ path: new Path2D(g.d), bbox: g.bbox }));
  const ring = LOGO.find(g => g.bbox[0] > 50 && g.bbox[0] < 60);
  const ec = [(ring.bbox[0] + ring.bbox[2]) / 2, (ring.bbox[1] + ring.bbox[3]) / 2];
  LOGO.forEach(g => {
    const cx = (g.bbox[0] + g.bbox[2]) / 2, cy = (g.bbox[1] + g.bbox[3]) / 2;
    g.c = [cx, cy];
    g.kind = g === ring ? 'ring' : g.bbox[0] < 600 ? 'dash' : 'letter';
    g.ang = Math.atan2(cy - ec[1], cx - ec[0]);
  });
  LOGO.ec = ec;
  LOGO.filter(g => g.kind === 'dash').sort((a, b) => a.ang - b.ang).forEach((g, i) => g.idx = i);
  LOGO.filter(g => g.kind === 'letter').sort((a, b) => a.bbox[0] - b.bbox[0]).forEach((g, i) => g.idx = i);
  // ridge polyline (hand-cleaned vertices of the beam's top edge, image px)
  const VV = [[39, 784], [323, 637], [421, 636], [471, 640], [700, 506], [787, 504], [845, 512], [1032, 368], [1122, 363], [1159, 371], [1273, 272], [1333, 268], [1365, 272], [1468, 174], [1516, 169], [1545, 176], [1672, 43], [1900, -196]];
  const ys = new Float32Array(1901);
  for (let x = 0; x <= 1900; x++) {
    let j = 0; while (j < VV.length - 2 && VV[j + 1][0] < x) j++;
    const [x0, y0] = VV[j], [x1, y1] = VV[j + 1];
    ys[x] = x <= x0 ? y0 : y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }
  const sm = new Float32Array(1901); const R = 170;
  for (let x = 0; x <= 1900; x++) { let s = 0, n = 0; for (let k = -R; k <= R; k += 4) { const xx = Math.min(1900, Math.max(0, x + k)); s += ys[xx]; n++; } sm[x] = s / n; }
  RIDGE = { ys, sm };
  for (const f of ['PB', 'PBI', 'PM', 'PR']) { MC.font = `100px ${f}`; CAP[f] = MC.measureText('H').actualBoundingBoxAscent / 100; }
  window.ready = true;
}
const ridgeY = x => RIDGE.ys[Math.max(0, Math.min(1900, Math.round(x)))];
const ridgeS = x => RIDGE.sm[Math.max(0, Math.min(1900, Math.round(x)))];
/* ---------------- text helpers ---------------- */
const LCACHE = new Map();
function lay(fam, size, ls, text) {
  const k = fam + '|' + size + '|' + ls + '|' + text;
  let v = LCACHE.get(k); if (v) return v;
  MC.font = `${size}px ${fam}`; MC.letterSpacing = ls + 'px';
  const xs = []; for (let i = 0; i <= text.length; i++) xs.push(MC.measureText(text.slice(0, i)).width);
  v = { xs, w: xs[text.length] - (text.length ? ls : 0) }; LCACHE.set(k, v); return v;
}
const capH = (fam, size) => CAP[fam] * size;
function font(g, fam, size, ls = 0) { g.font = `${size}px ${fam}`; g.letterSpacing = ls + 'px'; }
function alignX(x, w, align) { return align === 'center' ? x - w / 2 : align === 'right' ? x - w : x; }

// plain text with letter spacing & alignment
function text(g, s, x, base, fam, size, color, { ls = 0, align = 'left', alpha = 1 } = {}) {
  const L = lay(fam, size, ls, s); font(g, fam, size, ls); g.textAlign = 'left'; g.fillStyle = color;
  const a0 = g.globalAlpha; g.globalAlpha = a0 * alpha; g.fillText(s, alignX(x, L.w, align), base); g.globalAlpha = a0; g.letterSpacing = '0px';
  return L.w;
}
// letters rise from behind a mask (and optionally rise out)
function riseText(g, s, x, base, fam, size, color, t0, t, o = {}) {
  const { ls = 0, align = 'left', stagger = 0.022, dur = 0.55, out = null, outDur = 0.28, alpha = 1, from = 1.25 } = o;
  if (t < t0) return;
  const L = lay(fam, size, ls, s); const x0 = alignX(x, L.w, align); const cap = capH(fam, size);
  g.save(); g.beginPath(); g.rect(x0 - size, base - cap - size * 0.32, L.w + size * 2, cap + size * 0.62); g.clip();
  font(g, fam, size, 0); g.fillStyle = color; g.textAlign = 'left'; g.globalAlpha *= alpha;
  for (let i = 0; i < s.length; i++) {
    const u = E.outExpo(prog(t, t0 + i * stagger, dur)); if (u <= 0) continue;
    let dy = (1 - u) * cap * from;
    if (out !== null) { const v = E.inCubic(prog(t, out + i * stagger * 0.5, outDur)); if (v >= 1) continue; dy -= v * (cap + size * 0.4); }
    g.fillText(s[i], x0 + L.xs[i], base + dy);
  }
  g.restore();
}
// typewriter
function typeText(g, s, x, base, fam, size, color, t0, cps, t, o = {}) {
  if (t < t0) return; const n = Math.min(s.length, Math.floor((t - t0) * cps) + 1);
  text(g, s.slice(0, n), x, base, fam, size, color, o);
}
function roundRect(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function chip(g, s, x, y, fam, size, ls, bg, fg, padX, padY, t0, t, align = 'left') {
  if (t < t0) return;
  const L = lay(fam, size, ls, s); const cap = capH(fam, size);
  const w = L.w + padX * 2, h = cap + padY * 2; const x0 = alignX(x, w, align);
  const u = E.outBack(prog(t, t0, 0.35), 2.2); const sc = Math.max(0, u);
  g.save(); g.translate(x0, y + h / 2); g.scale(Math.min(1, sc * 1.0) , sc); g.translate(0, -h / 2);
  g.fillStyle = bg; roundRect(g, 0, 0, w, h, h * 0.22); g.fill();
  text(g, s, padX, padY + cap, fam, size, fg, { ls });
  g.restore();
  return { w, h };
}
function radial(g, x, y, r, c, a) {
  const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, rgba(c, a)); gr.addColorStop(0.45, rgba(c, a * 0.45)); gr.addColorStop(1, rgba(c, 0));
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
}
function sunburst(g, x, y, r, n, rot, c, a) {
  g.save(); g.translate(x, y); g.rotate(rot); g.fillStyle = rgba(c, a); g.beginPath();
  for (let i = 0; i < n; i++) { const a0 = i * 2 * Math.PI / n; g.moveTo(0, 0); g.arc(0, 0, r, a0, a0 + Math.PI / n); g.closePath(); }
  g.fill(); g.restore();
}
function vignette(g, a, c = [0, 0, 0]) {
  const gr = g.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
  gr.addColorStop(0, rgba(c, 0)); gr.addColorStop(1, rgba(c, a)); g.fillStyle = gr; g.fillRect(-50, -50, W + 100, H + 100);
}
// big slam (scale-in) text, scaled about its optical centre
function slam(g, s, cx, base, fam, size, color, t0, t, o = {}) {
  const { ls = 0, s0 = 1.9, dur = 0.34, echo = true, glow = 0, rot0 = 0, align = 'center' } = o;
  if (t < t0) return;
  const p = t - t0; const k = E.outExpo(clamp(p / dur));
  const sc = s0 + (1 - s0) * k; const cap = capH(fam, size); const L = lay(fam, size, ls, s);
  const x0 = alignX(0, L.w, align) + (align === 'left' ? 0 : 0);
  const pivotX = align === 'left' ? cx + L.w / 2 : align === 'right' ? cx - L.w / 2 : cx;
  g.save(); g.translate(pivotX, base - cap / 2); g.rotate(rot0 * (1 - k)); g.scale(sc, sc);
  font(g, fam, size, ls); g.textAlign = 'left';
  const dx = -L.w / 2, dy = cap / 2;
  if (echo) {
    for (let j = 0; j < 3; j++) {
      const eu = prog(p - j * 0.05, 0, 0.5); if (eu <= 0 || eu >= 1) continue;
      const es = 1 + (0.10 + 0.09 * j) * E.outCubic(eu);
      g.save(); g.scale(es, es); g.globalAlpha *= (1 - eu) * 0.55; g.strokeStyle = color; g.lineWidth = 3 / es;
      g.strokeText(s, dx, dy); g.restore();
    }
  }
  if (glow) { g.shadowColor = rgba(GOLD_RGB, 0.85); g.shadowBlur = glow; }
  g.fillStyle = color; g.globalAlpha *= clamp(p / 0.03 + 0.35); g.fillText(s, dx, dy);
  g.restore(); g.letterSpacing = '0px';
}

/* ---------------- logo ---------------- */
function drawLogo(g, x, y, w, color, t, t0 = null) {
  const s = w / 2000; g.save(); g.translate(x, y); g.scale(s, s); g.fillStyle = color;
  const [ecx, ecy] = LOGO.ec;
  for (const gp of LOGO) {
    if (t0 === null) { g.fill(gp.path); continue; }
    g.save();
    if (gp.kind === 'dash') {
      const ti = t0 + gp.idx * 0.03; const u = E.outExpo(prog(t, ti, 0.45)); if (u <= 0) { g.restore(); continue; }
      const rot = (1 - u) * -2.1, push = (1 - u) * 300;
      g.translate(ecx, ecy); g.rotate(rot); g.translate(Math.cos(gp.ang) * push, Math.sin(gp.ang) * push); g.translate(-ecx, -ecy);
      g.globalAlpha *= clamp((t - ti) / 0.08);
    } else if (gp.kind === 'ring') {
      const u = E.outBack(prog(t, t0 + 0.06, 0.5), 2.0); if (u <= 0) { g.restore(); continue; }
      g.translate(ecx, ecy); g.scale(u, u); g.rotate((1 - u) * 1.2); g.translate(-ecx, -ecy);
    } else {
      const ti = t0 + 0.16 + gp.idx * 0.045; const u = E.outExpo(prog(t, ti, 0.5)); if (u <= 0) { g.restore(); continue; }
      g.translate(0, (1 - u) * 140); g.globalAlpha *= clamp((t - ti) / 0.12);
    }
    g.fill(gp.path); g.restore();
  }
  g.restore();
}

/* =====================================================================
   STAGE — black set with a moving gold perspective floor (broadcast feel)
   ===================================================================== */
function gridFloor(g, t, a = 1) {
  const hy = H * (V ? 0.60 : 0.62), vx = W / 2, n = 13, ph = (t * 0.8) % 1;
  g.save(); g.lineWidth = 2;
  for (let i = 0; i < n; i++) {
    const z = (i + ph) / n; const y = hy + (H - hy) * 1.12 * z * z;
    if (y > H + 4) continue;
    g.strokeStyle = rgba(GOLD_RGB, a * 0.30 * Math.min(1, z * 1.6)); g.beginPath(); g.moveTo(-50, y); g.lineTo(W + 50, y); g.stroke();
  }
  const grd = g.createLinearGradient(0, hy, 0, H); grd.addColorStop(0, rgba(GOLD_RGB, 0)); grd.addColorStop(1, rgba(GOLD_RGB, a * 0.30));
  g.strokeStyle = grd;
  for (let k = -14; k <= 14; k++) { g.beginPath(); g.moveTo(vx + k * 8, hy); g.lineTo(vx + k * W * 0.13, H + 10); g.stroke(); }
  const hg = g.createLinearGradient(0, hy - 140, 0, hy + 50); hg.addColorStop(0, rgba(GOLD_RGB, 0)); hg.addColorStop(0.75, rgba(GOLD_RGB, 0.16 * a)); hg.addColorStop(1, rgba(GOLD_RGB, 0));
  g.fillStyle = hg; g.fillRect(0, hy - 140, W, 190);
  g.restore();
}
function stage(g, t, floor = 1, glow = 0.12, dark = 0.5) {
  if (PLATE) {   // footage shows through: only a soft dark scrim so type reads, plus a faint beat glow
    const gr = g.createRadialGradient(W / 2, H / 2, H * 0.1, W / 2, H / 2, W * 0.75);
    gr.addColorStop(0, `rgba(0,0,0,${dark})`); gr.addColorStop(1, `rgba(0,0,0,${dark * 0.35})`);
    g.fillStyle = gr; g.fillRect(-200, -200, W + 400, H + 400);
    radial(g, W / 2, H * 0.4, Math.max(W, H) * 0.6, GOLD_RGB, 0.05 * beatPulse(t, 4));
    return;
  }
  g.fillStyle = '#070707'; g.fillRect(-200, -200, W + 400, H + 400);
  radial(g, W / 2, H * 0.36, Math.max(W, H) * 0.7, GOLD_RGB, glow + 0.06 * beatPulse(t, 4));
  gridFloor(g, t, floor);
  vignette(g, 0.62);
}

/* ---------------- shutter transition: alternating gold / ink bars ---------------- */
function shutter(g, t, tc, drawOld, drawNew) {
  const t0 = tc - BARS / 2, n = 7, bh = H / n + 1, st = 0.015, dur = BARS / 2 - st * (n - 1) - 0.01;
  (t < tc ? drawOld : drawNew)(g, t);
  for (let i = 0; i < n; i++) {
    const fromLeft = i % 2 === 0; let a0, a1;
    if (t < tc) { const u = E.outCubic(clamp((t - t0 - i * st) / dur)); if (u <= 0) continue; a0 = 0; a1 = u; }
    else { const u = E.inCubic(clamp((t - tc - i * st) / dur)); if (u >= 1) continue; a0 = u; a1 = 1; }
    const x0 = fromLeft ? a0 * W : W - a1 * W, x1 = fromLeft ? a1 * W : W - a0 * W;
    g.fillStyle = i % 2 === 0 ? GOLD : INK; g.fillRect(x0 - 2, i * (H / n) - 1, x1 - x0 + 4, bh + 1);
    g.fillStyle = i % 2 === 0 ? GOLD_D : GOLD; const ex = fromLeft ? x1 - 6 : x0; g.fillRect(ex, i * (H / n) - 1, 6, bh + 1);
  }
}

/* =====================================================================
   HOOK (0.0 – 1.5)   WHO'S / WINNING?  + live pill
   ===================================================================== */
function livePill(g, cx, y, size, t0, t) {
  if (t < t0) return 0;
  const s1 = 'LIVE', s2 = DATE; const ls = 4;
  const L1 = lay('PB', size, ls, s1), L2 = lay('PB', size, ls, s2), cap = capH('PB', size);
  const dot = size * 0.42, gapD = size * 0.42, sep = size * 0.9, padX = size * 0.75, padY = size * 0.5;
  const w = padX * 2 + dot + gapD + L1.w + sep + L2.w, h = cap + padY * 2, x0 = cx - w / 2;
  const u = E.outBack(prog(t, t0, 0.38), 2.0);
  g.save(); g.translate(cx, y + h / 2); g.scale(Math.max(0, u), Math.max(0, u)); g.translate(-cx, -(y + h / 2));
  g.fillStyle = GOLD; roundRect(g, x0, y, w, h, h / 2); g.fill();
  const blink = 0.55 + 0.45 * Math.cos((t - t0) * Math.PI * 4) ** 2;
  g.fillStyle = `rgba(214,30,30,${blink})`; g.beginPath(); g.arc(x0 + padX + dot / 2, y + h / 2, dot / 2, 0, Math.PI * 2); g.fill();
  let x = x0 + padX + dot + gapD;
  text(g, s1, x, y + padY + cap, 'PB', size, INK, { ls }); x += L1.w;
  g.fillStyle = INK; g.beginPath(); g.arc(x + sep / 2, y + h / 2, size * 0.08, 0, Math.PI * 2); g.fill(); x += sep;
  text(g, s2, x, y + padY + cap, 'PB', size, INK, { ls });
  g.restore();
  return h;
}
/* the intro rotates daily (?intro=0..3, ?head=n picks the headline for the slam style) */
const HEADS = [["WHO'S", 'WINNING?'], ['THE POOL', 'KEEPS CLIMBING'], ['NEW DAY.', 'NEW LEADER?'], ['STILL', 'NO MAX CAP'], ['CHECK', 'THE BOARD']];
function hookFrame(g, t, mainH, drawMain) {   // eyebrow + main block + live pill, vertically centred
  stage(g, t, 1, 0.10);
  const es = P4 ? 30 : 34, ps = P4 ? 40 : 44, ce = capH('PB', es), ph = capH('PB', ps) + ps;
  const g1 = P4 ? 54 : 44, g3 = P4 ? 64 : 54;
  const total = ce + g1 + mainH + g3 + ph; const top = (H - total) / 2;
  const be = top + ce, mt = be + g1, py = mt + mainH + g3;
  const sc = 1 + 0.10 * (1 - E.outExpo(prog(t, 0, 0.45))) + 0.035 * E.inOutSine(prog(t, 0.45, 1.05));
  g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-W / 2, -H / 2);
  const ey = ROUND ? `PROGRESSIVE LEADERBOARD  ·  ROUND ${ROUND}` : 'PROGRESSIVE LEADERBOARD';
  riseText(g, ey, W / 2 + 4, be, 'PB', es, '#CFCFCF', 0.12, t, { ls: 8, align: 'center', stagger: 0.006, dur: 0.4 });
  drawMain(mt);
  livePill(g, W / 2, py, ps, 0.32, t);
  g.restore();
}
function hookSlam(g, t, l1, l2) {
  const TW = P4 ? 940 : 1240;
  const s = Math.min(P4 ? 230 : 300, TW / Math.max(lay('PBI', 100, -3, l1).w, lay('PBI', 100, -3, l2).w) * 100); const cap = capH('PB', s), gp = cap * 0.2;
  hookFrame(g, t, l2 ? cap * 2 + gp : cap, (mt) => {
    riseText(g, l1, W / 2, mt + cap, 'PBI', s, l2 ? '#FFFFFF' : GOLD, -0.04, t, { ls: -3, align: 'center', stagger: 0.02, dur: 0.38, from: 1.2 });
    if (l2) riseText(g, l2, W / 2, mt + cap * 2 + gp, 'PBI', s, GOLD, 0.02, t, { ls: -3, align: 'center', stagger: 0.018, dur: 0.38, from: 1.2 });
  });
}
function hookType(g, t) {   // typewriter + blinking cursor + scanlines
  const l1 = HL.length ? HL[0] : 'DAILY', l2 = HL.length ? (HL[1] || '') : 'BOARD CHECK', TW = P4 ? 900 : 1150;
  const s = Math.min(P4 ? 200 : 260, TW / Math.max(lay('PB', 100, 2, l1).w, lay('PB', 100, 2, l2).w) * 100), cap = capH('PB', s), gp = cap * 0.22;
  const cps = Math.max(24, (l1.length + l2.length) / 0.95), t2 = 0.02 + l1.length / cps + 0.04;
  hookFrame(g, t, l2 ? cap * 2 + gp : cap, (mt) => {
    const n1 = Math.min(l1.length, Math.max(0, Math.floor((t - 0.02) * cps) + 1)), n2 = Math.min(l2.length, Math.max(0, Math.floor((t - t2) * cps) + 1));
    const L1 = lay('PB', s, 2, l1), L2 = lay('PB', s, 2, l2), x1 = W / 2 - Math.max(L1.w, L2.w) / 2;
    if (n1 > 0) text(g, l1.slice(0, n1), x1, mt + cap, 'PB', s, '#FFFFFF', { ls: 2 });
    if (l2 && n2 > 0) text(g, l2.slice(0, n2), x1, mt + cap * 2 + gp, 'PB', s, GOLD, { ls: 2 });
    const onL2 = l2 && t >= t2, n = onL2 ? n2 : n1, LL = onL2 ? L2 : L1, cb = onL2 ? mt + cap * 2 + gp : mt + cap;
    if (Math.floor(t * 4) % 2 === 0 || n < (onL2 ? l2.length : l1.length)) { g.fillStyle = GOLD; g.fillRect(x1 + LL.xs[n] + s * 0.06, cb - cap, s * 0.09, cap); }
  });
  g.save(); g.fillStyle = 'rgba(0,0,0,0.16)'; for (let y = (t * 120) % 6; y < H; y += 6) g.fillRect(0, y, W, 2); g.restore();
}
function hookScramble(g, t) {  // "how big is the pool today?" with the digits still spinning
  const q = HL.length ? HL.join(' ') : 'HOW BIG IS THE POOL TODAY?';
  const s = P4 ? 210 : 270, cap = capH('PB', s), qs = Math.min(P4 ? 50 : 62, (W * 0.86) / lay('PBI', 100, 0, q).w * 100), qc = capH('PBI', qs), gq = P4 ? 40 : 34;
  hookFrame(g, t, qc + gq + cap, (mt) => {
    riseText(g, q, W / 2, mt + qc, 'PBI', qs, '#FFFFFF', -0.02, t, { align: 'center', stagger: 0.008, dur: 0.36 });
    const str = '$' + Math.floor(POOL).toLocaleString('en-US'); const L = lay('PB', s, 0, str); const x0 = W / 2 - L.w / 2, b = mt + qc + gq + cap;
    const u = E.outExpo(prog(t, 0.08, 0.4)); if (u <= 0) return;
    g.save(); g.globalAlpha *= u; g.shadowColor = rgba(GOLD_RGB, 0.7); g.shadowBlur = 40; font(g, 'PB', s, 0); g.textAlign = 'center';
    for (let i = 0; i < str.length; i++) {
      const c = str[i], cx = x0 + (L.xs[i] + L.xs[i + 1]) / 2;
      // every digit is a bouncing "?" -- never a fake number someone could screenshot
      const ch = c >= '0' && c <= '9' ? '?' : c; const hop = ch === '?' ? -Math.abs(Math.sin((t - 0.1) * 7 + i * 0.9)) * cap * 0.12 : 0;
      g.fillStyle = c === '$' ? GOLD : ch === '?' ? (i % 2 ? GOLD : '#FFFFFF') : '#FFFFFF'; g.fillText(ch, cx, b + (1 - u) * cap * 0.6 + hop);
    }
    g.restore(); g.textAlign = 'left';
  });
}
function hookCountdown(g, t) {   // days left as the hook
  const ok = ENDS.length > 0 && LEFT >= 0; if (!ok) return HL.length ? hookSlam(g, t, HL[0], HL[1] || '') : hookSlam(g, t, ...HEADS[HEAD % HEADS.length]);
  const big = LEFT === 0 ? 'LAST' : String(LEFT), r1 = LEFT === 0 ? 'DAY' : LEFT === 1 ? 'DAY LEFT' : 'DAYS LEFT', r2 = HL.length ? HL.join(' ') : 'TO CLIMB THE BOARD';
  const bs = P4 ? 300 : 420, bc = capH('PBI', bs), rs = P4 ? 92 : 120, rc = capH('PBI', rs);
  const r2s = Math.min(P4 ? 40 : 48, (P4 ? 560 : 900) / lay('PB', 100, 4, r2).w * 100), r2c = capH('PB', r2s);
  const Lb = lay('PBI', bs, -6, big), Lr = Math.max(lay('PBI', rs, -2, r1).w, lay('PB', r2s, 4, r2).w), gapX = P4 ? 36 : 56;
  const tw = Lb.w + gapX + Lr; const x0 = W / 2 - tw / 2;
  hookFrame(g, t, bc, (mt) => {
    slam(g, big, x0, mt + bc, 'PBI', bs, GOLD, 0.0, t, { ls: -6, s0: 2.2, dur: 0.34, glow: 50, align: 'left' });
    const rx = x0 + Lb.w + gapX, rb1 = mt + bc / 2 - 6, rb2 = rb1 + 26 + r2c;
    riseText(g, r1, rx, rb1, 'PBI', rs, '#FFFFFF', 0.1, t, { ls: -2, stagger: 0.016, dur: 0.38 });
    riseText(g, r2, rx + 4, rb2, 'PB', r2s, '#CFCFCF', 0.18, t, { ls: 4, stagger: 0.008, dur: 0.38 });
  });
}
function sceneHook(g, t) {
  if (INTRO === 1) return hookType(g, t);
  if (INTRO === 2) return hookScramble(g, t);
  if (INTRO === 3) return hookCountdown(g, t);
  return HL.length ? hookSlam(g, t, HL[0], HL[1] || '') : hookSlam(g, t, ...HEADS[HEAD % HEADS.length]);
}

/* =====================================================================
   POOL (1.5 – 4.0) odometer lands on today's pool, then shrinks into the header
   ===================================================================== */
function counterValue(t) {
  if (t < TL.c0) return 10000;
  const u = clamp((t - TL.c0) / (TL.c1 - TL.c0));
  return 10000 + (POOL - 10000) * Math.pow(u, 1.8);
}
let FRAME_T = 0;
const ND = Math.max(5, String(Math.floor(POOL)).length);
function drawCounter(g, v, x, base, size, t, intro = null, col = '#FFFFFF') {
  const fam = 'PB'; const cap = capH(fam, size);
  const vf = counterValue(FRAME_T); const spd = Math.abs(counterValue(FRAME_T + 0.01) - counterValue(FRAME_T - 0.01)) / 0.02;
  MC.font = `${size}px ${fam}`; MC.letterSpacing = '0px';
  const cw = MC.measureText('0').width, dw = MC.measureText('$').width, kw = MC.measureText(',').width;
  const lh = cap * 1.45;
  font(g, fam, size, 0); g.textAlign = 'center';
  let cx = x; let cell = 0;
  const introDy = (i) => { if (!intro) return 0; const u = E.outBack(prog(t, intro + i * 0.035, 0.42), 1.6); return -(1 - u) * cap * 1.6; };
  const introA = (i) => { if (!intro) return 1; return clamp((t - intro - i * 0.035) / 0.08); };
  g.save(); g.fillStyle = GOLD; g.globalAlpha *= introA(0); g.fillText('$', cx + dw / 2, base + introDy(0)); g.restore(); cx += dw + size * 0.015; cell++;
  for (let k = ND - 1; k >= 0; k--) {
    const p = Math.pow(10, k); let w;
    if (spd / p / FPS > 0.45) w = Math.floor(vf / p) % 10;
    else if (k === 0) w = v % 10; else { const b = Math.floor(v / p); const rem = v - b * p; w = (b % 10) + clamp(rem - (p - 1), 0, 1); }
    const d = Math.floor(w) % 10, f = w - Math.floor(w);
    g.save(); g.beginPath(); g.rect(cx - 4, base - cap - size * 0.12, cw + 8, cap + size * 0.24); g.clip();
    g.globalAlpha *= introA(cell); const idy = introDy(cell);
    g.fillStyle = col; g.fillText(String(d), cx + cw / 2, base - f * lh + idy);
    if (f > 0.001) g.fillText(String((d + 1) % 10), cx + cw / 2, base + (1 - f) * lh + idy);
    g.restore(); cx += cw; cell++;
    if (k % 3 === 0 && k > 0) { g.save(); g.globalAlpha *= introA(cell); g.fillStyle = col; g.fillText(',', cx + kw / 2, base + introDy(cell)); g.restore(); cx += kw; cell++; }
  }
  g.textAlign = 'left';
  return { w: cx - x, cap };
}
function counterWidth(size) {
  MC.font = `${size}px PB`; MC.letterSpacing = '0px';
  return MC.measureText('$').width + size * 0.015 + ND * MC.measureText('0').width + Math.floor((ND - 1) / 3) * MC.measureText(',').width;
}
const XSPARK = (() => { const r = rng(55); const a = []; for (let i = 0; i < 70; i++) a.push({ ang: r() * Math.PI * 2, sp: 1400 + r() * 2600, len: 40 + r() * 90, w: 2 + r() * 4, life: 0.25 + r() * 0.3 }); return a; })();
const CONFETTI = (() => { const r = rng(99); const a = []; for (let i = 0; i < 90; i++) { const ang = -Math.PI * (0.05 + r() * 0.9); const sp = 700 + r() * 1300; a.push({ vx: Math.cos(ang) * sp * 1.1, vy: Math.sin(ang) * sp, rot: r() * 6, vr: (r() - 0.5) * 22, w: 10 + r() * 14, h: 6 + r() * 8, c: r() < 0.62 ? GOLD : r() < 0.6 ? GOLD_L : '#FFFFFF', ph: r() * 6 }); } return a; })();
function burst(g, t, t0, cxr, cyr, k = 1) {
  const p = t - t0; if (p < 0 || p > 1.8) return;
  radial(g, cxr, cyr, (500 + 900 * p) * k, [255, 226, 140], 0.5 * Math.exp(-p * 7));
  if (p < 0.6) { const u = E.outCubic(p / 0.6); g.save(); g.strokeStyle = rgba(GOLD_RGB, (1 - u) * 0.9); g.lineWidth = 34 * (1 - u) + 2; g.beginPath(); g.arc(cxr, cyr, (60 + 1200 * u) * k, 0, Math.PI * 2); g.stroke(); g.restore(); }
  g.save(); g.lineCap = 'round';
  for (const q of XSPARK) {
    if (p > q.life) continue; const d = q.sp * k * p * (1 - p / (2 * q.life)); const a = 1 - p / q.life;
    const x1 = cxr + Math.cos(q.ang) * d, y1 = cyr + Math.sin(q.ang) * d, x0 = cxr + Math.cos(q.ang) * Math.max(0, d - q.len), y0 = cyr + Math.sin(q.ang) * Math.max(0, d - q.len);
    g.strokeStyle = `rgba(255,${200 + Math.floor(40 * a)},90,${a})`; g.lineWidth = q.w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  g.restore();
  for (const q of CONFETTI) {
    const px = cxr + q.vx * k * p * 0.9, py = cyr + q.vy * k * p + 1500 * p * p; if (py > H + 60) continue;
    g.save(); g.translate(px, py); g.rotate(q.rot + q.vr * p); g.scale(Math.abs(Math.cos(q.ph + p * 9)) * 0.9 + 0.1, 1);
    g.globalAlpha *= clamp((1.8 - p) / 0.4); g.fillStyle = q.c; g.fillRect(-q.w / 2, -q.h / 2, q.w, q.h); g.restore();
  }
}

// layout of the standings board, per format
const BD = P4
  ? { title: 58, tx: 60, tb: 178, eb: 102, es: 22, poolS: 70, px: 1020, rx: 60, rw: 960, ry: 274, rh: 146, rg: 14, two: true, ch: 252, name: 50, wag: 32, prize: 46,
      tk: { y: 1176, h: 84, s: 34, sp: 230 }, big: { s: 190, base: 760, lab: 520, chip: 850 } }
  : { title: 74, tx: 160, tb: 196, eb: 112, es: 26, poolS: 96, px: 1760, rx: 160, rw: 1600, ry: 292, rh: 108, rg: 12, two: false, ch: 274, name: 52, wag: 46, prize: 50,
      tk: { y: 944, h: 78, s: 34, sp: 300 }, big: { s: 250, base: 640, lab: 380, chip: 730 } };

function poolCounter(g, t) {   // big centre -> header (right aligned)
  const m = E.inOutExpo(prog(t, TL.m0, TL.m1 - TL.m0));
  const S0 = BD.big.s, S1 = BD.poolS, cw0 = counterWidth(S0);
  const x0 = W / 2 - cw0 / 2, b0 = BD.big.base;
  const x1 = BD.px - counterWidth(S1), b1 = BD.tb;
  const k = lerp(1, S1 / S0, m); const ox = lerp(x0, x1, m), ob = lerp(b0, b1, m);
  const cap = capH('PB', S0);
  let pop = 1; if (t >= TL.c1) { const p = t - TL.c1; pop = 1 + 0.10 * Math.exp(-p * 9) * Math.cos(p * 26); }
  else pop = 1 + 0.08 * Math.pow(prog(t, TL.c0, TL.c1 - TL.c0), 2);
  if (t > TL.m1) pop = 1 + 0.02 * beatPulse(t, 8);
  g.save(); g.translate(ox, ob - cap * k / 2); g.scale(k * pop, k * pop); g.translate(0, cap / 2);
  if (t >= TL.c0 - 0.2 && t < TL.c1 + 0.6) {        // light streaks behind the spinning wheels
    const a = clamp((t - TL.c0 + 0.2) / 0.2) * (1 - clamp((t - TL.c1) / 0.6));
    const lg = g.createLinearGradient(-200, 0, cw0 + 200, 0); lg.addColorStop(0, rgba(GOLD_RGB, 0)); lg.addColorStop(0.5, rgba(GOLD_RGB, 0.22 * a)); lg.addColorStop(1, rgba(GOLD_RGB, 0));
    g.fillStyle = lg; g.fillRect(-200, -cap * 1.3, cw0 + 400, cap * 1.6);
  }
  drawCounter(g, counterValue(t), 0, 0, S0, t, TL.x1 + 0.02, '#FFFFFF');
  g.restore();
}
function scenePool(g, t) {
  stage(g, t, t < TL.m0 ? 1 : lerp(1, 0.45, E.inOutSine(prog(t, TL.m0, 0.6))), 0.12, t < TL.m0 ? 0.55 : lerp(0.55, 0.62, E.inOutSine(prog(t, TL.m0, 0.6))));
  const fade = 1 - E.inCubic(prog(t, TL.m0 - 0.05, 0.25));
  if (fade > 0) {
    g.save(); g.globalAlpha *= fade;
    riseText(g, 'TOTAL PRIZE POOL', W / 2 + 5, BD.big.lab, 'PB', P4 ? 38 : 44, '#D8D8D8', TL.x1 + 0.05, t, { ls: 12, align: 'center', stagger: 0.008, dur: 0.4 });
    if (t >= TL.c1 + 0.08) {
      const L = lay('PBI', P4 ? 46 : 52, 0, 'NO MAX CAP'); const u = E.outBack(prog(t, TL.c1 + 0.08, 0.36), 2.2);
      chip(g, 'NO MAX CAP', W / 2, BD.big.chip, 'PBI', P4 ? 46 : 52, 2, GOLD, INK, 26, 16, TL.c1 + 0.08, t, 'center');
    }
    g.restore();
  }
  burst(g, t, TL.c1, W / 2, BD.big.base - capH('PB', BD.big.s) / 2, P4 ? 0.8 : 1);
  poolCounter(g, t);
}

/* =====================================================================
   STANDINGS (4.0 – 9.0) the board: header + 5 rows + prize ticker
   ===================================================================== */
const SUFFIX = ['ST', 'ND', 'RD', 'TH', 'TH'];
function crown(g, x, y, s, col) {
  g.save(); g.translate(x, y); g.scale(s, s); g.fillStyle = col; g.beginPath();
  g.moveTo(-30, 14); g.lineTo(-34, -16); g.lineTo(-16, 0); g.lineTo(0, -24); g.lineTo(16, 0); g.lineTo(34, -16); g.lineTo(30, 14); g.closePath(); g.fill();
  g.fillRect(-30, 18, 60, 8); g.restore();
}
function fitSize(fam, size, ls, s, maxW) { const w = lay(fam, size, ls, s).w; return w > maxW ? Math.floor(size * maxW / w) : size; }
function row(g, t, i) {
  const r = TOP[i]; if (!r) return;
  const ta = TL.rows[i]; if (t < ta - 0.1) return;
  const y = BD.ry + i * (BD.rh + BD.rg), x = BD.rx, w = BD.rw, h = BD.rh, lead = i === 0;
  const u = E.outExpo(prog(t, ta - 0.1, 0.42)); const dx = (1 - u) * W * 0.7;
  const land = t >= ta ? Math.exp(-(t - ta) * 10) * Math.cos((t - ta) * 30) : 0;
  g.save(); g.translate(dx, 0); g.globalAlpha *= clamp((t - ta + 0.1) / 0.1);
  g.translate(x + w / 2, y + h / 2); g.scale(1 + 0.025 * land, 1 - 0.05 * land); g.translate(-(x + w / 2), -(y + h / 2));
  // panel
  if (lead) {
    g.save(); g.shadowColor = rgba(GOLD_RGB, 0.55 + 0.25 * beatPulse(t, 5)); g.shadowBlur = 40;
    const gr = g.createLinearGradient(0, y, 0, y + h); gr.addColorStop(0, '#FFD54A'); gr.addColorStop(0.55, '#F2B418'); gr.addColorStop(1, '#D99A00');
    g.fillStyle = gr; roundRect(g, x, y, w, h, 18); g.fill(); g.restore();
  } else {
    g.fillStyle = 'rgba(20,19,16,0.94)'; roundRect(g, x, y, w, h, 18); g.fill();
    g.strokeStyle = rgba(GOLD_RGB, 0.32); g.lineWidth = 2; roundRect(g, x + 1, y + 1, w - 2, h - 2, 17); g.stroke();
  }
  // rank block
  g.save(); roundRect(g, x, y, h, h, 18); g.clip(); g.fillStyle = lead ? INK : GOLD; g.fillRect(x, y, h, h); g.restore();
  const rs = h * 0.56, rc = capH('PBI', rs); const n = String(i + 1); const Ln = lay('PBI', rs, 0, n), Ls = lay('PB', h * 0.18, 1, SUFFIX[i]);
  const rx0 = x + h / 2 - (Ln.w + Ls.w + 4) / 2, rb = y + h / 2 + rc / 2 + (lead ? h * 0.08 : 0);
  text(g, n, rx0, rb, 'PBI', rs, lead ? GOLD : INK);
  text(g, SUFFIX[i], rx0 + Ln.w + 4, rb - rc + capH('PB', h * 0.18), 'PB', h * 0.18, lead ? GOLD : INK, { ls: 1 });
  if (lead) crown(g, x + h / 2, y + h * 0.2, h / 150, GOLD);
  // prize pill (right)
  const ps = BD.prize, pc = capH('PB', ps), ptxt = money(r.prize), Lp = lay('PB', ps, 1, ptxt);
  const pw = Lp.w + ps * 0.9, ph = pc + ps * 0.62, pxr = x + w - (BD.two ? 22 : 28), py = y + h / 2 - ph / 2;
  const pu = E.outBack(prog(t, ta + 0.12, 0.34), 2.2);
  if (pu > 0) {
    g.save(); g.translate(pxr - pw / 2, y + h / 2); g.scale(pu, pu); g.translate(-(pxr - pw / 2), -(y + h / 2));
    g.fillStyle = lead ? INK : GOLD; roundRect(g, pxr - pw, py, pw, ph, ph * 0.28); g.fill();
    text(g, ptxt, pxr - pw + ps * 0.45, py + ps * 0.31 + pc, 'PB', ps, lead ? GOLD : INK, { ls: 1 });
    g.restore();
  }
  // name + wagered
  const nx = x + h + (BD.two ? 30 : 40), wroll = Math.round(r.wag * E.outQuart(prog(t, ta, 0.7)));
  if (BD.two) {
    const ns = fitSize('PB', BD.name, 1, r.name, pxr - pw - nx - 24);
    text(g, r.name, nx, y + 70, 'PB', ns, lead ? INK : '#FFFFFF', { ls: 1 });
    text(g, 'WAGERED', nx, y + 118, 'PB', 24, lead ? 'rgba(10,10,10,0.65)' : GOLD, { ls: 5 });
    text(g, money(wroll), nx + lay('PB', 24, 5, 'WAGERED').w + 16, y + 120, 'PM', BD.wag + 2, lead ? INK : '#E8E3D8', { ls: 1 });
  } else {
    const wx = x + w * 0.50; const ns = fitSize('PB', BD.name, 1, r.name, wx - nx - 30);
    text(g, r.name, nx, y + h / 2 + capH('PB', ns) / 2, 'PB', ns, lead ? INK : '#FFFFFF', { ls: 1 });
    text(g, money(wroll), wx, y + h / 2 + capH('PM', BD.wag) / 2, 'PM', BD.wag, lead ? INK : '#E8E3D8', { ls: 1 });
  }
  // leader shine
  if (lead) for (const ts of [ta + 0.15, ta + 1.7]) {
    const su = prog(t, ts, 0.6); if (su <= 0 || su >= 1) continue; const sx = lerp(x - 300, x + w + 300, E.inOutCubic(su));
    g.save(); roundRect(g, x, y, w, h, 18); g.clip(); g.transform(1, 0, -0.35, 1, 0, 0);
    const lg = g.createLinearGradient(sx - 140 + 0.35 * y, 0, sx + 140 + 0.35 * y, 0); lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,0.6)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = lg; g.fillRect(sx - 140 + 0.35 * y, y - 10, 280, h + 20); g.restore();
  }
  g.restore();
}
function colHeads(g, t) {
  const t0 = TL.rows[TL.rows.length - 1] - 0.25, s = P4 ? 26 : 30, y = BD.ch, h = BD.rh, x = BD.rx;
  const o = { ls: 8, stagger: 0.01, dur: 0.4 };
  riseText(g, 'RANK', x + h / 2 + 4, y, 'PB', s, GOLD, t0, t, { ...o, align: 'center' });
  if (BD.two) riseText(g, 'PLAYER  ·  WAGERED', x + h + 30, y, 'PB', s, GOLD, t0 + 0.04, t, o);
  else {
    riseText(g, 'PLAYER', x + h + 40, y, 'PB', s, GOLD, t0 + 0.04, t, o);
    riseText(g, 'WAGERED', x + BD.rw * 0.50, y, 'PB', s, GOLD, t0 + 0.08, t, o);
  }
  riseText(g, 'PRIZE', x + BD.rw - (BD.two ? 22 : 28), y, 'PB', s, GOLD, t0 + 0.12, t, { ...o, align: 'right' });
}
function ticker(g, t) {
  const T0 = TL.tick0; if (t < T0) return;
  const k = BD.tk, u = E.outExpo(prog(t, T0, 0.4)), y = k.y + (1 - u) * (k.h + 60);
  g.save();
  g.fillStyle = '#0E0D0A'; g.fillRect(-20, y, W + 40, k.h); g.fillStyle = GOLD; g.fillRect(-20, y, W + 40, 4);
  const lab = 'TODAY', ls = lay('PB', k.s, 6, lab), lw = ls.w + 56;
  const items = [[['RAFFLE ', '#FFFFFF'], [money(PRZ[1]), GOLD]], [['SLOT MULTI LEADERBOARD ', '#FFFFFF'], [money(PRZ[2]), GOLD]],
    [['TOP 20 WIN CASH', GOLD]], [['WAGER LEADERBOARD ', '#FFFFFF'], [money(PRZ[0]), GOLD]], [['NO MAX CAP', '#FFFFFF']], [['USE CODE DYLANGG', '#FFFFFF']]];
  const sepW = k.s * 1.6; const widths = items.map(it => lay('PB', k.s, 3, it.map(p => p[0]).join('')).w); const loop = widths.reduce((a, b) => a + b + sepW, 0);
  g.save(); g.beginPath(); g.rect(lw, y + 4, W - lw, k.h - 4); g.clip();
  let x = lw + 40 - ((t - T0) * k.sp) % loop; const base = y + 4 + (k.h - 4) / 2 + capH('PB', k.s) / 2;
  while (x < W + 20) {
    for (let j = 0; j < items.length; j++) {
      if (x + widths[j] > lw - 20 && x < W + 20) { let xx = x; for (const [s_, c_] of items[j]) { text(g, s_, xx, base, 'PB', k.s, c_, { ls: 3 }); xx += lay('PB', k.s, 3, s_).w + 3; } }
      x += widths[j];
      const dx = x + sepW / 2, dy = base - capH('PB', k.s) / 2, d = k.s * 0.22;
      g.fillStyle = GOLD; g.beginPath(); g.moveTo(dx, dy - d); g.lineTo(dx + d, dy); g.lineTo(dx, dy + d); g.lineTo(dx - d, dy); g.closePath(); g.fill();
      x += sepW;
    }
  }
  g.restore();
  g.fillStyle = GOLD; g.fillRect(-20, y, lw + 20, k.h);
  g.fillStyle = INK; g.beginPath(); g.moveTo(lw, y); g.lineTo(lw + 22, y + k.h / 2); g.lineTo(lw, y + k.h); g.closePath(); g.fillStyle = GOLD; g.fill();
  text(g, lab, 28, y + k.h / 2 + capH('PB', k.s) / 2, 'PB', k.s, INK, { ls: 6 });
  g.restore();
}
function sceneBoard(g, t) {
  scenePool(g, t);
  if (t < TL.m0) return;
  // header
  const ey = (P4 ? '' : 'LIVE STANDINGS  ·  ') + (ROUND ? `ROUND ${ROUND}  ·  ` : '') + DATE;
  riseText(g, ey, BD.tx + 2, BD.eb, 'PB', BD.es, '#9A9384', TL.m0 + 0.15, t, { ls: 7, stagger: 0.006, dur: 0.4 });
  riseText(g, P4 ? 'LIVE STANDINGS' : 'PROGRESSIVE LEADERBOARD', BD.tx, BD.tb, 'PBI', BD.title, '#FFFFFF', TL.m0 + 0.1, t, { ls: -1, stagger: 0.014, dur: 0.42 });
  riseText(g, 'TOTAL POOL', BD.px, BD.eb, 'PB', BD.es, '#9A9384', TL.m1 - 0.05, t, { ls: 7, align: 'right', stagger: 0.008, dur: 0.4 });
  { const u = E.outExpo(prog(t, TL.m0 + 0.2, 0.5)); g.fillStyle = rgba(GOLD_RGB, 0.5); g.fillRect(BD.tx, BD.tb + (P4 ? 22 : 26), (BD.px - BD.tx) * u, 2); }
  colHeads(g, t);
  for (let i = TOP.length - 1; i >= 0; i--) row(g, t, i);
  burst(g, t, TL.rows[0], BD.rx + BD.rh / 2, BD.ry + BD.rh / 2, 0.7);
  ticker(g, t);
}

/* =====================================================================
   FLIP CLOCK (9.0 – 10.5) days left in the round
   ===================================================================== */
function cardHalf(g, ch, x, y, w, h, half, sy) {   // half: 0 top, 1 bottom; sy: vertical scale about the hinge
  const hy = y + h / 2;
  g.save(); g.beginPath(); g.rect(x - 4, half ? hy : y - 4, w + 8, h / 2 + 4); g.clip();
  g.translate(0, hy); g.scale(1, Math.max(0.001, sy)); g.translate(0, -hy);
  const gr = g.createLinearGradient(0, y, 0, y + h); gr.addColorStop(0, '#1C1A16'); gr.addColorStop(0.5, '#121110'); gr.addColorStop(0.5, '#0C0B0A'); gr.addColorStop(1, '#151411');
  g.fillStyle = gr; roundRect(g, x, y, w, h, w * 0.1); g.fill();
  g.strokeStyle = rgba(GOLD_RGB, 0.55); g.lineWidth = 3; roundRect(g, x + 1.5, y + 1.5, w - 3, h - 3, w * 0.1); g.stroke();
  const s = h * 0.74, cap = capH('PB', s); font(g, 'PB', s, 0); g.textAlign = 'center'; g.fillStyle = GOLD;
  g.fillText(ch, x + w / 2, hy + cap / 2); g.textAlign = 'left';
  if (sy < 1) { g.fillStyle = `rgba(0,0,0,${0.55 * (1 - sy)})`; g.fillRect(x, y, w, h); }
  g.restore();
}
function flipCard(g, x, y, w, h, a, b, t0, t) {
  const u = prog(t, t0, 0.36);
  if (u <= 0 || a === b) { cardHalf(g, a === b || u <= 0 ? a : b, x, y, w, h, 0, 1); cardHalf(g, a === b || u <= 0 ? a : b, x, y, w, h, 1, 1); }
  else if (u >= 1) { cardHalf(g, b, x, y, w, h, 0, 1); cardHalf(g, b, x, y, w, h, 1, 1); }
  else {
    cardHalf(g, b, x, y, w, h, 0, 1); cardHalf(g, a, x, y, w, h, 1, 1);
    if (u < 0.5) cardHalf(g, a, x, y, w, h, 0, 1 - E.inQuad(u * 2));
    else cardHalf(g, b, x, y, w, h, 1, E.outBack((u - 0.5) * 2, 1.6));
  }
  g.fillStyle = 'rgba(0,0,0,0.85)'; g.fillRect(x, y + h / 2 - 2, w, 4);
}
function sceneEnds(g, t) {
  stage(g, t, 0.8, 0.14);
  const has = ENDS.length > 0 && LEFT >= 0;
  const last = has && LEFT === 0;
  const eyebrow = has ? `${ROUND ? `ROUND ${ROUND} ` : ''}ENDS ${ENDS}` : 'BI-WEEKLY  ·  TOP 20 GET PAID';
  const val = has ? LEFT : 20, from = has ? LEFT + 1 : 20;
  const digits = String(Math.max(val, from)).length;
  const A = String(from).padStart(digits, ' '), B = String(val).padStart(digits, ' ');
  const lab = has ? (LEFT === 1 ? ['DAY', 'LEFT'] : ['DAYS', 'LEFT']) : ['TOP', 'WIN'];
  const cw = P4 ? 240 : 290, chh = P4 ? 340 : 400, gap = 24;
  const cards = (digits * cw + (digits - 1) * gap);
  const es = P4 ? 40 : 44;
  const sc = 1 + 0.03 * E.inOutSine(prog(t, TL.x2, 1.5));
  g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-W / 2, -H / 2);
  if (last) {
    const top = H / 2 - 160;
    riseText(g, eyebrow, W / 2 + 5, top, 'PB', es, '#D8D8D8', TL.x2 + 0.05, t, { ls: 10, align: 'center', stagger: 0.01, dur: 0.4 });
    const s2 = Math.min(P4 ? 230 : 300, (P4 ? 920 : 1300) / lay('PBI', 100, -4, 'LAST DAY!').w * 100);
    slam(g, 'LAST DAY!', W / 2, top + 80 + capH('PBI', s2), 'PBI', s2, GOLD, TL.flip, t, { ls: -4, s0: 2.6, dur: 0.36, glow: 60, rot0: -0.2 });
    g.restore(); return;
  }
  const ls = P4 ? 120 : 190, lc = capH('PBI', ls), lw = Math.max(lay('PBI', ls, -3, lab[0]).w, lay('PBI', ls, -3, lab[1]).w);
  let cx0, cy0, eb, lx, lb1, lb2;
  if (P4) { cy0 = 430; cx0 = W / 2 - cards / 2; eb = 360; lx = W / 2; lb1 = cy0 + chh + 70 + lc; lb2 = lb1; }
  else { const tw = cards + 80 + lw; cx0 = W / 2 - tw / 2; cy0 = 330; eb = 250; lx = cx0 + cards + 80; lb1 = cy0 + chh / 2 - 16; lb2 = lb1 + 28 + lc; }
  riseText(g, eyebrow, W / 2 + 5, eb, 'PB', es, '#D8D8D8', TL.x2 + 0.05, t, { ls: 10, align: 'center', stagger: 0.01, dur: 0.4 });
  const ci = E.outBack(prog(t, TL.x2 + 0.02, 0.4), 1.8);
  for (let d = 0; d < digits; d++) {
    const x = cx0 + d * (cw + gap); if (A[d] === ' ' && B[d] === ' ') continue;
    g.save(); g.translate(x + cw / 2, cy0 + chh / 2); g.scale(ci, ci); g.translate(-(x + cw / 2), -(cy0 + chh / 2));
    flipCard(g, x, cy0, cw, chh, A[d] === ' ' ? '' : A[d], B[d] === ' ' ? '' : B[d], TL.flip + d * 0.05, t);
    g.restore();
  }
  if (P4) riseText(g, lab.join(' '), lx, lb1, 'PBI', ls, '#FFFFFF', TL.flip + 0.08, t, { ls: -3, align: 'center', stagger: 0.02, dur: 0.4 });
  else {
    riseText(g, lab[0], lx, lb1, 'PBI', ls, '#FFFFFF', TL.flip + 0.06, t, { ls: -3, stagger: 0.02, dur: 0.4 });
    riseText(g, lab[1], lx, lb2, 'PBI', ls, GOLD, TL.flip + 0.12, t, { ls: -3, stagger: 0.02, dur: 0.4 });
  }
  g.restore();
}
/* =====================================================================
   END CARD (14.4 – 20.0)  only on ROOBET / use code DylanGG / dylanjames.gg
   ===================================================================== */
const CODE = 'DylanGG';
const REEL_CH = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789$#';
const REELS = (() => { const r = rng(5); return CODE.split('').map((ch, i) => { const n = 14 + i * 3; const arr = []; for (let k = 0; k < n; k++) arr.push(REEL_CH[Math.floor(r() * REEL_CH.length)]); arr.push(ch); return arr; }); })();
const BOKEH = (() => { const r = rng(3); const a = []; for (let i = 0; i < 46; i++) a.push({ x: r() * W, y: r() * H, s: 2 + r() * 5, v: 20 + r() * 50, ph: r() * 6, f: 1 + r() * 2 }); return a; })();
function sceneEnd(g, t) {
  const _PL = typeof PLATE !== 'undefined' && PLATE;
  const spot = 0.35 * clamp((t - TL.end + 0.05) / 0.3) + 0.65 * clamp((t - TL.end - 0.45) / 0.5); const bp = beatPulse(t, 4);
  const mcx = V ? 540 : 1500, mcy = P4 ? 1080 : V ? 1480 : 560;
  if (_PL) {   // footage (spotlight stage) shows through; darken the text column so it reads
    const lg = g.createLinearGradient(0, 0, W * 0.62, 0); lg.addColorStop(0, 'rgba(0,0,0,0.72)'); lg.addColorStop(0.75, 'rgba(0,0,0,0.45)'); lg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = lg; g.fillRect(-200, -200, W * 0.62 + 200, H + 400);
  } else {
    g.fillStyle = '#050505'; g.fillRect(-200, -200, W + 400, H + 400);
    radial(g, mcx, mcy, 1000, GOLD_RGB, (0.20 + 0.08 * bp) * spot);
    sunburst(g, mcx, mcy, 1500, 20, (t - 14) * 0.12, GOLD_RGB, 0.055 * spot);
    radial(g, V ? 540 : 520, V ? 640 : 620, 900, GOLD_RGB, 0.07);
    vignette(g, 0.7);
  }
  // bokeh
  g.save();
  for (const b of BOKEH) { const y = ((b.y - (t - 14) * b.v) % (H + 40) + H + 40) % (H + 40) - 20; const a = (0.25 + 0.35 * Math.sin(t * b.f + b.ph) ** 2) * clamp((t - TL.end) / 0.6);
    g.fillStyle = rgba(GOLD_RGB, a); g.beginPath(); g.arc(b.x, y, b.s, 0, Math.PI * 2); g.fill(); }
  g.restore();
  // mascot
  const M0 = TL.end + 0.45;
  if (t >= M0) {
    const u = prog(t, M0, 0.33); const e = E.outBack(u, 1.25);
    const ms = P4 ? 0.56 : V ? 0.62 : 0.70; const mw = 1024 * ms, mh = 1536 * ms;
    const x = (V ? W / 2 - mw / 2 + 20 : 1180) + (1 - e) * 1100, bottom = (P4 ? 716 + mh : H + 18) - 42 * Math.sin(Math.PI * prog(t, TL.fin, 0.32));
    const groove = t > M0 + 0.45 ? beatPulse(t, 7) : 0; const sway = t > M0 + 0.45 ? 0.012 * Math.sin((t - M0 - 0.45) * Math.PI) : 0;
    g.save(); g.translate(x + mw / 2, bottom); g.rotate(0.22 * (1 - e) + sway); g.scale(1 + 0.008 * groove, 1 - 0.014 * groove); g.translate(-mw / 2, -mh);
    g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 50; g.shadowOffsetX = -20;
    g.drawImage(A.mascot, 0, 0, mw, mh); g.restore();
  }
  // left column
  const EC = P4 ? { al: 'center', x: W / 2, only: 128, lw: 560, ly: 150, use: 374, by: 400, url: 682, cs: 150, bh: 200, us: 66 } : V ? { al: 'center', x: W / 2, only: 206, lw: 700, ly: 236, use: 548, by: 580, url: 922 } : { al: 'left', x: 154, only: 222, lw: 650, ly: 250, use: 528, by: 560, url: 880 };
  riseText(g, 'ONLY ON', EC.x + (V ? 6 : 0), EC.only, 'PM', P4 ? 34 : 38, '#C8C8C8', TL.end - 0.06, t, { ls: 13, stagger: 0.025, align: EC.al });
  drawLogo(g, V ? W / 2 - EC.lw / 2 : 150, EC.ly, EC.lw, GOLD, t, TL.end - 0.06);
  riseText(g, 'USE CODE', EC.x + (V ? 5 : 0), EC.use, 'PB', P4 ? 46 : 50, '#FFFFFF', TL.end + 0.12, t, { ls: 11, stagger: 0.02, align: EC.al });
  // code box
  const B0 = TL.end + 0.15;
  if (t >= B0) {
    const size = EC.cs || 168; const L = lay('PB', size, 2, CODE); const cap = capH('PB', size);
    const bw = L.w + 130, bh = EC.bh || 228, bx = V ? W / 2 - bw / 2 : 150, by = EC.by;
    const u = E.outExpo(prog(t, B0, 0.4)); const uy = E.outBack(prog(t, B0, 0.45), 2.5);
    const pk = t >= TL.fin ? 1 + 0.06 * Math.exp(-(t - TL.fin) * 9) : 1;
    g.save(); g.translate(bx + bw / 2, by + bh / 2); g.scale(pk, pk); g.translate(-bx - bw / 2, -by - bh / 2);
    g.translate(bx, by + bh / 2); g.scale(u, Math.max(0.05, uy)); g.translate(-bx, -(by + bh / 2));
    // glow
    g.save(); g.shadowColor = rgba(GOLD_RGB, 0.75); g.shadowBlur = 40 + 45 * bp * clamp((t - B0 - 0.6) / 0.3);
    const gr = g.createLinearGradient(0, by, 0, by + bh); gr.addColorStop(0, '#FFD54A'); gr.addColorStop(0.55, '#F2B418'); gr.addColorStop(1, '#D99A00');
    g.fillStyle = gr; roundRect(g, bx, by, bw, bh, 28); g.fill(); g.restore();
    g.strokeStyle = 'rgba(255,245,210,0.7)'; g.lineWidth = 3; roundRect(g, bx + 5, by + 5, bw - 10, bh - 10, 24); g.stroke();
    // reel letters
    g.save(); roundRect(g, bx, by, bw, bh, 28); g.clip();
    font(g, 'PB', size, 0); g.textAlign = 'left'; g.fillStyle = INK;
    const tx = bx + 64, base = by + bh / 2 + cap / 2; const lh = bh * 0.9;
    for (let i = 0; i < CODE.length; i++) {
      const R = REELS[i]; const tl = B0 + 0.1 + i * 0.07; const pu = E.outBack(prog(t, B0, tl - B0 + 0.12), 1.3);
      const pos = pu * (R.length - 1); const k = Math.floor(pos), f = pos - k;
      const cxl = tx + L.xs[i];
      const chW = L.xs[i + 1] - L.xs[i];
      const a = R[Math.min(R.length - 1, Math.max(0, k))], b = R[Math.min(R.length - 1, k + 1)];
      g.save(); g.beginPath(); g.rect(cxl - 6, by, chW + 6, bh); g.clip();
      const cw = (ch) => { MC.font = `${size}px PB`; MC.letterSpacing = '0px'; return MC.measureText(ch).width; };
      g.fillText(a, cxl + (chW - 2 - cw(a)) / 2 * (a === CODE[i] ? 0 : 1), base - f * lh);
      if (f > 0.001) g.fillText(b, cxl + (chW - 2 - cw(b)) / 2 * (b === CODE[i] ? 0 : 1), base + (1 - f) * lh);
      g.restore();
    }
    // shine sweep
    for (const ts of [TL.end + 1.6, TL.fin - 0.08]) {
      const su = prog(t, ts, 0.55); if (su <= 0 || su >= 1) continue; const sx = lerp(bx - 300, bx + bw + 300, E.inOutCubic(su));
      const lg = g.createLinearGradient(sx - 120, 0, sx + 120, 0); lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,0.65)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
      g.save(); g.transform(1, 0, -0.35, 1, 0, 0); g.fillStyle = lg; g.fillRect(sx - 120 + 0.35 * by, by - 10, 240, bh + 20); g.restore();
    }
    g.restore();
    g.restore();
    g.restore();
  }
  // url
  const U0 = TL.end + 0.7;
  if (t >= U0) {
    const s = 'Roobet.com'; const n = Math.min(s.length, Math.floor((t - U0) * 40) + 1);
    const us = EC.us || 76; const Lf = lay('PM', us, 1, s); const ux = V ? W / 2 - (Lf.w + 70) / 2 : 154;
    const w = text(g, s.slice(0, n), ux, EC.url, 'PM', us, '#FFFFFF', { ls: 1 });
    const uu = E.outExpo(prog(t, U0 + 0.25, 0.45));
    g.fillStyle = GOLD; g.fillRect(ux + 2, EC.url + us * 0.37, Lf.w * uu, 7);
    // arrow
    const ua = E.outBack(prog(t, U0 + 0.35, 0.35), 2); if (ua > 0) { g.save(); g.translate(ux + Lf.w + 58 + 8 * Math.sin((t - U0) * Math.PI * 2), EC.url - 26); g.scale(ua, ua); g.strokeStyle = GOLD; g.lineWidth = 7; g.lineCap = 'round'; g.lineJoin = 'round';
      g.beginPath(); g.moveTo(-18, 0); g.lineTo(18, 0); g.moveTo(4, -15); g.lineTo(19, 0); g.lineTo(4, 15); g.stroke(); g.restore(); }
  }
  // bottom line: more info @ dylanjames.gg
  {
    const a = E.outCubic(prog(t, TL.end + 1.0, 0.4)); const dy = (1 - a) * 18;
    const s1 = 'More info at ', s2 = 'dylanjames.gg', sz = V ? 42 : 38;
    const L1 = lay('PM', sz, 1, s1), L2 = lay('PB', sz, 1, s2);
    if (V) { // fade the mascot's hoodie into black so the line reads
      const gh = P4 ? 150 : 330;
      const gr = g.createLinearGradient(0, H - gh, 0, H); gr.addColorStop(0, 'rgba(5,5,5,0)'); gr.addColorStop(0.55, 'rgba(5,5,5,0.85)'); gr.addColorStop(1, 'rgba(5,5,5,0.97)');
      g.fillStyle = gr; g.fillRect(-100, H - gh, W + 200, gh + 110);
    }
    const bx = V ? W / 2 - (L1.w + L2.w) / 2 : 154, bb = (P4 ? H - 52 : V ? H - 70 : 996) + dy;
    text(g, s1, bx, bb, 'PM', sz, '#BDBDBD', { ls: 1, alpha: a });
    text(g, s2, bx + L1.w, bb, 'PB', sz, '#FFFFFF', { ls: 1, alpha: a });
  }
  if (V) text(g, '18+  |  Gamble responsibly', W / 2, P4 ? 60 : 104, 'PR', P4 ? 24 : 26, '#8A8A8A', { ls: 1, align: 'center', alpha: clamp((t - TL.end - 0.5) / 0.4) });
  else text(g, '18+  |  Gamble responsibly', 154, 1046, 'PR', 22, '#7E7E7E', { ls: 1, alpha: clamp((t - TL.end - 0.5) / 0.4) });
}
// vertical push transition
function pushUp(g, t, t0, dur, drawOld, drawNew) {
  const u = E.inOutExpo(prog(t, t0, dur)); const off = u * H;
  g.save(); g.translate(0, -off); g.beginPath(); g.rect(-300, -300, W + 600, H + 300); g.clip(); drawOld(g, t); g.restore();
  g.save(); g.translate(0, H - off); g.beginPath(); g.rect(-300, 0, W + 600, H + 300); g.clip(); drawNew(g, t); g.restore();
  g.fillStyle = GOLD; g.fillRect(-300, H - off - 7, W + 600, 14);
}

/* =====================================================================
   MASTER TIMELINE
   ===================================================================== */
const DURATION = TL.DUR;
function renderScene(g, t) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none'; g.shadowBlur = 0; g.shadowColor = 'rgba(0,0,0,0)';
  if (PLATE) g.clearRect(0, 0, W, H); else { g.fillStyle = '#000'; g.fillRect(0, 0, W, H); }
  const sh = shake(t); g.translate(W / 2 + sh.x, H / 2 + sh.y); g.rotate(sh.r); g.translate(-W / 2, -H / 2);
  const B = BARS / 2;
  if (t < TL.x1 - B) sceneHook(g, t);
  else if (t < TL.x1 + B) shutter(g, t, TL.x1, sceneHook, sceneBoard);
  else if (t < TL.x2 - B) sceneBoard(g, t);
  else if (t < TL.x2 + B) shutter(g, t, TL.x2, sceneBoard, sceneEnds);
  else if (t < TL.x3 - B) sceneEnds(g, t);
  else if (t < TL.x3 + B) shutter(g, t, TL.x3, sceneEnds, sceneEnd);
  else sceneEnd(g, t);
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (const [tf, c, a, k] of FLASHES) { if (t < tf) continue; const e = a * Math.exp(-(t - tf) * k); if (e < 0.004) continue; g.fillStyle = rgba(c, e); g.fillRect(0, 0, W, H); }
}

window.renderFrame = (t, N = 8, shutter = 0.5) => {
  if (PLATE) {   // transparent motion blur: add each sub-frame at 1/N ('lighter' sums premultiplied colour and alpha)
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < N; i++) {
      const ti = N === 1 ? t : t + ((i + 0.5) / N - 0.5) * shutter / FPS; FRAME_T = t;
      renderScene(sctx, Math.max(0, ti));
      ctx.globalAlpha = 1 / N; ctx.drawImage(SUB, 0, 0);
    }
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1; return true;
  }
  for (let i = 0; i < N; i++) {
    const ti = N === 1 ? t : t + ((i + 0.5) / N - 0.5) * shutter / FPS; FRAME_T = t;
    renderScene(sctx, Math.max(0, ti));
    ctx.globalAlpha = 1 / (i + 1); ctx.drawImage(SUB, 0, 0);
  }
  ctx.globalAlpha = 1; return true;
};
window.DURATION = DURATION;
init();
