'use strict';
/* =====================================================================
   DAILY POOL UPDATE — data-driven motion engine (Canvas2D, deterministic)
   render(t) is a pure function of time. 120 BPM -> 1 beat = 0.5 s.
   URL params: fmt=h|p  pool  main  raffle  multi  date  ends  left  round
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
const DATE = (Q.get('date') || 'FRI OCT 10').toUpperCase();        // today, shown on the hook
const ENDS = (Q.get('ends') === null ? 'OCT 15' : Q.get('ends')).toUpperCase();   // '' -> no end-date card text
const LEFT = Q.get('left') === null ? 5 : parseInt(Q.get('left'), 10); // days left, <0 hides the chip
const ROUND = Q.get('round') || '';                                  // e.g. '01'
const GOLD = '#EEAF0E', GOLD_L = '#FFD34D', GOLD_D = '#D99A00', INK = '#0A0A0A';
const GOLD_RGB = [238, 175, 14];
const money = v => '$' + Math.round(v).toLocaleString('en-US');

const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const SUB = document.createElement('canvas'); SUB.width = W; SUB.height = H;
const sctx = SUB.getContext('2d');
const MC = document.createElement('canvas').getContext('2d'); // measuring
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

/* ---------------- master timeline (13.5 s) ----------------
   0.0  hook: POOL UPDATE + live date
   1.5  graph world, $10,000 -> today's pool (lands on 3.5)
   5.0  3 ways to win, with today's dollar amounts
   8.5  round ends card
   10.0 end card (Roobet / code / site)                       */
const TL = { w1: 1.38, g0: 1.5, tag: 2.05, c0: 2.0, c1: 3.5, ways0: 5.0, ways: 5.28, ends0: 8.5, endsIn: 8.62, endsSlam: 9.0,
  end0: 9.88, end: 10.0, fin: 12.5, DUR: 13.5 };
// [time, shake px, shake decay]
const IMPACTS = [
  [0.00, 9, 9], [1.50, 6, 10], [3.50, 26, 6.5], [5.28, 16, 8.5], [9.00, 14, 9],
  [TL.end + 0.15, 9, 10], [TL.end + 0.78, 11, 10], [TL.fin, 7, 10],
];
// [time, color, alpha, decay]
const FLASHES = [
  [3.50, [255, 255, 255], 0.42, 9], [9.00, GOLD_RGB, 0.18, 9],
  [TL.end + 0.15, GOLD_RGB, 0.16, 10], [TL.fin, GOLD_RGB, 0.14, 8],
];
window.CUES = { IMPACTS, FLASHES, TL, POOL, PRZ };
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
/* ---------------- diagonal band wipe ---------------- */
function bandWipe(g, t, t0, dur, drawNew, dir = 1, bandCol = GOLD) {
  const u = E.inOutCubic(prog(t, t0, dur)); const slant = 0.42 * H, bw = 230, gap = 26, thin = 34;
  const xs = -slant - bw - gap - thin - 40, xe = W + bw + gap + thin + 40;
  const x = lerp(xs, xe, u);
  const edge = (off) => { // polygon left of the line x+off at bottom, slanted forward
    const bx = x + off, tx = x + off + slant;
    return dir > 0 ? [[-300, -300], [tx + (tx - bx) * 300 / H, -300], [bx - (tx - bx) * 300 / H, H + 300], [-300, H + 300]]
      : [[W + 300, -300], [W - tx - (tx - bx) * 300 / H, -300], [W - bx + (tx - bx) * 300 / H, H + 300], [W + 300, H + 300]];
  };
  const poly = (pts) => { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) g.lineTo(p[0], p[1]); g.closePath(); };
  // new scene (left of trailing edge)
  g.save(); poly(edge(-bw - gap - thin)); g.clip(); drawNew(g, t); g.restore();
  // thick band
  g.save(); poly(edge(0)); g.clip(); poly(edge(-bw)); g.rect(-400, -400, W + 800, H + 800); g.clip('evenodd');
  g.fillStyle = bandCol; g.fillRect(-400, -400, W + 800, H + 800); g.restore();
  // thin band
  g.save(); poly(edge(-bw - gap)); g.clip(); poly(edge(-bw - gap - thin)); g.rect(-400, -400, W + 800, H + 800); g.clip('evenodd');
  g.fillStyle = INK; g.fillRect(-400, -400, W + 800, H + 800); g.restore();
}
function iris(g, t, t0, dur, cx, cy, drawNew, ring = GOLD) {
  const u = E.inCubic(prog(t, t0, dur)); if (u <= 0) return; const r = 1250 * u;
  g.save(); g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.clip(); drawNew(g, t); g.restore();
  g.save(); g.strokeStyle = ring; g.lineWidth = 26 * (1 - u) + 4; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.stroke(); g.restore();
}
function drawPct(g, img, cb, x, y, sc, sqx = 1, sqy = 1) {
  const ccx = (cb[0] + cb[2]) / 2, bot = cb[3];
  g.save(); g.translate(x, y + (bot - (cb[1] + cb[3]) / 2) * sc); g.scale(sc * sqx, sc * sqy); g.translate(-ccx, -bot);
  g.imageSmoothingQuality = 'high'; g.drawImage(img, 0, 0); g.restore();
}
const CB90 = [67, 156, 1504, 873], CB5 = [70, 68, 1482, 946], CBT = [82, 313, 1187, 975], CBR = [69, 195, 1466, 846];
function dropAnim(t, t0, tl, h = 950) { // returns {dy, sx, sy}
  if (t < tl) { const u = E.inQuad(prog(t, t0, tl - t0)); return { dy: -(1 - u) * h, sx: 0.95, sy: 1.07 }; }
  const p = t - tl; const k = Math.exp(-p * 12) * Math.cos(p * 32);
  return { dy: -Math.abs(Math.sin(p * 16)) * 26 * Math.exp(-p * 9), sx: 1 + 0.07 * k, sy: 1 - 0.1 * k };
}
function drawPctBottom(g, img, cb, x, bottom, sc, sqx = 1, sqy = 1) {
  const ccx = (cb[0] + cb[2]) / 2;
  g.save(); g.translate(x, bottom); g.scale(sc * sqx, sc * sqy); g.translate(-ccx, -cb[3]); g.imageSmoothingQuality = 'high'; g.drawImage(img, 0, 0); g.restore();
}

/* =====================================================================
   HOOK (0.0 – 1.5)   PROGRESSIVE LEADERBOARD / POOL / UPDATE / ● LIVE · date
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
function sceneHook(g, t) {
  g.fillStyle = '#050505'; g.fillRect(-200, -200, W + 400, H + 400);
  radial(g, W / 2, H / 2, Math.max(W, H) * 0.75, GOLD_RGB, 0.08 + 0.12 * beatPulse(t, 4));
  sunburst(g, W / 2, H / 2, 1600, 24, t * 0.3, [255, 255, 255], 0.018);
  vignette(g, 0.55);
  const TW = P4 ? 940 : 1080;
  const s1 = TW / lay('PB', 100, 0, 'POOL').w * 100, s2 = TW / lay('PB', 100, 0, 'UPDATE').w * 100;
  const es = P4 ? 36 : 38, ps = P4 ? 40 : 44;
  const ce = capH('PB', es), c1 = capH('PB', s1), c2 = capH('PB', s2), ph = capH('PB', ps) + ps;
  const g1 = P4 ? 56 : 46, gp = c1 * 0.15, g3 = P4 ? 62 : 50;
  const total = ce + g1 + c1 + gp + c2 + g3 + ph;
  const top = (H - total) / 2;
  const be = top + ce, b1 = be + g1 + c1, b2 = b1 + gp + c2, py = b2 + g3;
  const sc = 1 + 0.09 * (1 - E.outExpo(prog(t, 0, 0.4))) + 0.03 * E.inOutSine(prog(t, 0.4, 1.1));
  g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-W / 2, -H / 2);
  riseText(g, 'PROGRESSIVE LEADERBOARD', W / 2 + 5, be, 'PB', es, '#D9D9D9', 0.10, t, { ls: 10, align: 'center', stagger: 0.008, dur: 0.4 });
  riseText(g, 'POOL', W / 2, b1, 'PB', s1, '#FFFFFF', -0.04, t, { align: 'center', stagger: 0.014, dur: 0.36, from: 1.15 });
  riseText(g, 'UPDATE', W / 2, b2, 'PB', s2, GOLD, 0.0, t, { align: 'center', stagger: 0.012, dur: 0.36, from: 1.15 });
  livePill(g, W / 2, py, ps, 0.30, t);
  g.restore();
}

/* =====================================================================
   GRAPH WORLD (1.5 – 5.0)  camera flies up the beam, counter lands on today's pool
   ===================================================================== */
const IW = 1672, IH = 941, HX1 = +(Q.get('hx1') || (P4 ? 1100 : 1490));
const K3 = +(Q.get('k3') || 0);
function headX(t) {
  if (t <= TL.c0) return 39;
  if (t <= TL.c1) return 39 + (HX1 - 39) * Math.pow((t - TL.c0) / (TL.c1 - TL.c0), 1.6);
  return HX1 + 80 * (1 - Math.exp(-(t - TL.c1) * 1.2));     // still creeping: the pool never stops growing
}
function smax(a, b, k) { return (a + b + Math.sqrt((a - b) * (a - b) + k * k)) / 2; }
function smin(a, b, k) { return (a + b - Math.sqrt((a - b) * (a - b) + k * k)) / 2; }
function camAt(t) {
  let S; const K = P4 ? [1.92, 1.82, 2.10, K3 || 2.0, 0.04] : V ? [2.36, 2.24, 2.62, 2.10, 0.05] : [1.64, 1.55, 1.78, 1.30, 0.05];
  if (t < TL.c0) S = lerp(K[0], K[1], E.inOutSine(prog(t, TL.g0 - 0.3, TL.c0 - TL.g0 + 0.3)));
  else if (t < TL.c1) S = lerp(K[1], K[2], E.inOutSine(prog(t, TL.c0, TL.c1 - TL.c0)));
  else S = lerp(K[2], K[3], E.outExpo(prog(t, TL.c1, 0.65))) + K[4] * prog(t, TL.c1 + 0.6, 1.4);
  const rot = t > TL.c0 && t < TL.c1 + 0.6 ? -0.03 * Math.sin(Math.PI * prog(t, TL.c0, TL.c1 - TL.c0 + 0.6)) : 0;
  const hx = headX(t); const P = P4 ? [600, 960] : V ? [560, 1240] : [1200, 560];
  let cx = hx - (P[0] - W / 2) / S, cy = ridgeS(Math.min(hx, 1672)) - (P[1] - H / 2) / S;
  const c = Math.abs(Math.cos(rot)), s = Math.abs(Math.sin(rot)), m = 22 / S;
  const hw = (W / 2 * c + H / 2 * s) / S + m, hh = (W / 2 * s + H / 2 * c) / S + m;
  cx = smin(smax(cx, hw, 60), IW - hw, 60); cy = smin(smax(cy, hh, 60), IH - hh, 60);
  return { S, cx, cy, rot };
}
function camApply(g, c) { g.translate(W / 2, H / 2); g.rotate(c.rot); g.scale(c.S, c.S); g.translate(-c.cx, -c.cy); }
function toScr(c, x, y) { const dx = (x - c.cx) * c.S, dy = (y - c.cy) * c.S, co = Math.cos(c.rot), si = Math.sin(c.rot); return [W / 2 + dx * co - dy * si, H / 2 + dx * si + dy * co]; }

const SPARKS = (() => { const r = rng(7); const a = []; for (let i = 0; i < 320; i++) { const te = TL.c0 - 0.05 + i / 90; a.push({ te, ang: Math.PI * (0.75 + r() * 0.9), sp: 160 + r() * 420, life: 0.28 + r() * 0.55, w: 1.5 + r() * 2.5 }); } return a; })();
const XSPARK = (() => { const r = rng(55); const a = []; for (let i = 0; i < 70; i++) a.push({ ang: r() * Math.PI * 2, sp: 1400 + r() * 2600, len: 40 + r() * 90, w: 2 + r() * 4, life: 0.25 + r() * 0.3 }); return a; })();
const CONFETTI = (() => { const r = rng(99); const a = []; for (let i = 0; i < 90; i++) { const ang = -Math.PI * (0.05 + r() * 0.9); const sp = 700 + r() * 1300; a.push({ vx: Math.cos(ang) * sp * 1.1, vy: Math.sin(ang) * sp, rot: r() * 6, vr: (r() - 0.5) * 22, w: 10 + r() * 14, h: 6 + r() * 8, c: r() < 0.62 ? GOLD : r() < 0.6 ? GOLD_L : INK, ph: r() * 6 }); } return a; })();

function drawTrace(g, c, hx, t, alpha) {
  const pts = []; const x1 = Math.min(hx, 1890);
  for (let x = 39; x < x1; x += 3) pts.push(toScr(c, x, ridgeY(x) - 1));
  pts.push(toScr(c, x1, ridgeY(x1) - 1));
  if (pts.length < 2) return;
  g.save(); g.lineJoin = 'round'; g.lineCap = 'round'; g.globalAlpha *= alpha;
  const path = new Path2D(); path.moveTo(pts[0][0], pts[0][1]); for (const p of pts) path.lineTo(p[0], p[1]);
  g.strokeStyle = 'rgba(255,196,40,0.16)'; g.lineWidth = 30; g.stroke(path);
  g.strokeStyle = 'rgba(255,190,30,0.45)'; g.lineWidth = 13; g.stroke(path);
  g.strokeStyle = '#FFE7A3'; g.lineWidth = 4.5; g.stroke(path);
  g.restore();
}
function drawHead(g, x, y, a, t) {
  if (a <= 0) return; g.save(); g.globalAlpha *= a;
  const fl = 1 + 0.12 * Math.sin(t * 40);
  radial(g, x, y, 120 * fl, GOLD_RGB, 0.55); radial(g, x, y, 40, [255, 240, 200], 0.9);
  const lg = g.createLinearGradient(x - 220, y, x + 220, y); lg.addColorStop(0, 'rgba(255,220,120,0)'); lg.addColorStop(0.5, 'rgba(255,240,200,0.95)'); lg.addColorStop(1, 'rgba(255,220,120,0)');
  g.fillStyle = lg; g.fillRect(x - 220, y - 2, 440, 4);
  const lv = g.createLinearGradient(x, y - 90, x, y + 90); lv.addColorStop(0, 'rgba(255,220,120,0)'); lv.addColorStop(0.5, 'rgba(255,240,200,0.8)'); lv.addColorStop(1, 'rgba(255,220,120,0)');
  g.fillStyle = lv; g.fillRect(x - 1.5, y - 90, 3, 180);
  g.fillStyle = '#FFFFFF'; g.beginPath(); g.arc(x, y, 8, 0, Math.PI * 2); g.fill();
  g.restore();
}
function drawGraphWorld(g, t) {
  const c = camAt(t);
  g.fillStyle = '#EDEDED'; g.fillRect(-200, -200, W + 400, H + 400);
  g.save(); camApply(g, c); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; g.drawImage(A.graph, 0, 0); g.restore();
  const hx = headX(t);
  if (t >= TL.c0 - 0.1) {
    drawTrace(g, c, hx, t, clamp((t - TL.c0 + 0.1) / 0.1));
    g.save(); g.lineCap = 'round';
    for (const p of SPARKS) {
      if (t < p.te || t > p.te + p.life || p.te > TL.c1 + 0.2) continue;
      const age = t - p.te; const hxe = headX(p.te); const [ex, ey] = [hxe, ridgeY(hxe) - 1];
      const vx = Math.cos(p.ang) * p.sp, vy = Math.sin(p.ang) * p.sp;
      const x = ex + vx * age, y = ey + vy * age + 520 * age * age;
      const [sx, sy] = toScr(c, x, y); const [sx2, sy2] = toScr(c, x - vx * 0.035, y - (vy + 1040 * age) * 0.035);
      g.strokeStyle = `rgba(255,${190 + Math.floor(50 * (1 - age / p.life))},60,${(1 - age / p.life) * 0.95})`; g.lineWidth = p.w;
      g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx2, sy2); g.stroke();
    }
    g.restore();
  }
  {
    const a = t >= TL.g0 + 0.2 ? clamp((t - TL.g0 - 0.2) / 0.3) : 0;
    const pre = t < TL.c0 ? 0.75 + 0.25 * beatPulse(t, 7) : 1;
    const [sx, sy] = toScr(c, hx, ridgeY(hx) - 1); drawHead(g, sx, sy, a * pre, t);
  }
}

/* ---------------- the counter: $10,000 -> today's pool, lands on the beat ---------------- */
function counterValue(t) {
  if (t < TL.c0) return 10000;
  const u = clamp((t - TL.c0) / (TL.c1 - TL.c0));
  return 10000 + (POOL - 10000) * Math.pow(u, 1.8);
}
let FRAME_T = 0;
function drawCounter(g, v, x, base, size, t, intro = null, col = INK) {
  const fam = 'PB'; const cap = capH(fam, size);
  const vf = counterValue(FRAME_T); const spd = Math.abs(counterValue(FRAME_T + 0.01) - counterValue(FRAME_T - 0.01)) / 0.02;
  MC.font = `${size}px ${fam}`; MC.letterSpacing = '0px';
  const cw = MC.measureText('0').width, dw = MC.measureText('$').width, kw = MC.measureText(',').width;
  const nd = Math.max(5, String(Math.floor(POOL)).length); const lh = cap * 1.45;
  font(g, fam, size, 0); g.textAlign = 'center';
  let cx = x; let cell = 0;
  const introDy = (i) => { if (!intro) return 0; const u = E.outBack(prog(t, intro + i * 0.035, 0.42), 1.6); return -(1 - u) * cap * 1.6; };
  const introA = (i) => { if (!intro) return 1; return clamp((t - intro - i * 0.035) / 0.08); };
  g.save(); g.fillStyle = col === INK ? GOLD_D : GOLD; g.globalAlpha *= introA(0); g.fillText('$', cx + dw / 2, base + introDy(0)); g.restore(); cx += dw + size * 0.015; cell++;
  for (let k = nd - 1; k >= 0; k--) {
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
  return { w: cx - x, cap };
}
function counterWidth(size) {
  MC.font = `${size}px PB`; MC.letterSpacing = '0px';
  const nd = Math.max(5, String(Math.floor(POOL)).length);
  return MC.measureText('$').width + size * 0.015 + nd * MC.measureText('0').width + Math.floor((nd - 1) / 3) * MC.measureText(',').width;
}
// landing pop: overshoot then settle, then a gentle beat pulse
function landScale(t) {
  if (t < TL.c1) return 1 + 0.10 * Math.pow(prog(t, TL.c0, TL.c1 - TL.c0), 2);
  const p = t - TL.c1; return 1 + 0.10 * Math.exp(-p * 9) * Math.cos(p * 26) + 0.012 * beatPulse(t, 8);
}
function burst(g, t, cxr, cyr) {
  const p = t - TL.c1; if (p < 0 || p > 1.8) return;
  radial(g, cxr, cyr, 500 + 900 * p, [255, 226, 140], 0.6 * Math.exp(-p * 7));
  if (p < 0.6) { const u = E.outCubic(p / 0.6); g.save(); g.strokeStyle = rgba(GOLD_RGB, (1 - u) * 0.9); g.lineWidth = 40 * (1 - u) + 2; g.beginPath(); g.arc(cxr, cyr, 60 + 1300 * u, 0, Math.PI * 2); g.stroke(); g.restore(); }
  g.save(); g.lineCap = 'round';
  for (const q of XSPARK) {
    if (p > q.life) continue; const d = q.sp * p * (1 - p / (2 * q.life)); const a = 1 - p / q.life;
    const x1 = cxr + Math.cos(q.ang) * d, y1 = cyr + Math.sin(q.ang) * d, x0 = cxr + Math.cos(q.ang) * Math.max(0, d - q.len), y0 = cyr + Math.sin(q.ang) * Math.max(0, d - q.len);
    g.strokeStyle = `rgba(255,${200 + Math.floor(40 * a)},90,${a})`; g.lineWidth = q.w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  g.restore();
  for (const q of CONFETTI) {
    const px = cxr + q.vx * p * 0.9, py = cyr + q.vy * p + 1500 * p * p; if (py > H + 60) continue;
    g.save(); g.translate(px, py); g.rotate(q.rot + q.vr * p); g.scale(Math.abs(Math.cos(q.ph + p * 9)) * 0.9 + 0.1, 1);
    g.globalAlpha *= clamp((1.8 - p) / 0.4); g.fillStyle = q.c; g.fillRect(-q.w / 2, -q.h / 2, q.w, q.h); g.restore();
  }
}
// "[NO] MAX CAP!  ↑" one-line badge that slams in on the landing
function noMaxCapLine(g, t, x, base, size, col, align = 'left') {
  const p = t - TL.c1 - 0.08; if (p < 0) return;
  const u = E.outExpo(clamp(p / 0.36));
  const Ln = lay('PBI', size, -1, 'NO'), Lm = lay('PBI', size, -1, 'MAX CAP!');
  const cap = capH('PBI', size), pad = size * 0.16, gap = size * 0.24;
  const tw = Ln.w + pad * 2 + gap + Lm.w; const x0 = align === 'center' ? x - tw / 2 : x;
  const s = lerp(2.0, 1, u) * (1 + 0.02 * (p > 0.45 ? beatPulse(t, 8) : 0));
  const pcx = x0 + tw / 2, pcy = base - cap / 2;
  g.save(); g.translate(pcx, pcy); g.rotate(-0.06 * (1 - u)); g.scale(s, s); g.translate(-pcx, -pcy);
  g.globalAlpha *= clamp(p / 0.05 + 0.25);
  g.fillStyle = GOLD; roundRect(g, x0, base - cap - pad, Ln.w + pad * 2, cap + pad * 2, size * 0.12); g.fill();
  text(g, 'NO', x0 + pad, base, 'PBI', size, INK, { ls: -1 });
  text(g, 'MAX CAP!', x0 + Ln.w + pad * 2 + gap, base, 'PBI', size, col, { ls: -1 });
  g.restore();
}
function upArrow(g, x, y, s, col) {
  g.save(); g.translate(x, y); g.scale(s, s); g.fillStyle = col;
  g.beginPath(); g.moveTo(0, -20); g.lineTo(17, 4); g.lineTo(6, 4); g.lineTo(6, 20); g.lineTo(-6, 20); g.lineTo(-6, 4); g.lineTo(-17, 4); g.closePath(); g.fill(); g.restore();
}
function tagline(g, t, x, base, size, col, arrowCol) {
  if (t < TL.tag) return;
  const ex = E.inExpo(prog(t, TL.c1 - 0.06, 0.2)); if (ex >= 1) return;
  g.save(); g.translate(-ex * 900, 0); g.globalAlpha *= 1 - ex;
  const s = 'EVERY WAGER GROWS THE POOL'; const n = Math.min(s.length, Math.floor((t - TL.tag) * 75) + 1);
  const w = text(g, s.slice(0, n), x, base, 'PB', size, col, { ls: 3 });
  if (n === s.length) { const u = E.outBack(prog(t, TL.tag + 0.36, 0.3), 2); upArrow(g, x + w + size * 0.9, base - capH('PB', size) / 2, u * size / 40, arrowCol); }
  g.restore();
}

function sceneGraph(g, t) {
  drawGraphWorld(g, t);
  if (V) return hudVertical(g, t);
  { const a = clamp((t - TL.g0) / 0.25); g.save(); g.globalAlpha = a; drawLogo(g, 150, 64, 250, INK, t); g.restore(); }
  chip(g, 'TOTAL PRIZE POOL', 150, 196, 'PB', 32, 8, INK, '#FFFFFF', 22, 15, TL.g0, t);
  tagline(g, t, 152, 548, 40, INK, GOLD_D);
  const size = 190, x = 146, base = 420;
  const sc = landScale(t); const cap = capH('PB', size);
  g.save(); g.translate(x, base - cap / 2); g.scale(sc, sc); g.translate(-x, -(base - cap / 2));
  drawCounter(g, counterValue(t), x, base, size, t, TL.g0);
  g.restore();
  burst(g, t, x + counterWidth(size) / 2, base - cap / 2);
  noMaxCapLine(g, t, 150, 572, 80, INK);
  if (t >= TL.c1 + 0.3) {          // still climbing
    const a = clamp((t - TL.c1 - 0.3) / 0.25);
    g.save(); g.globalAlpha *= a; text(g, 'AND STILL CLIMBING', 154, 668, 'PB', 38, '#262626', { ls: 5 });
    upArrow(g, 154 + lay('PB', 38, 5, 'AND STILL CLIMBING').w + 32, 668 - capH('PB', 38) / 2 - 2 * Math.sin(t * 8), 0.85, GOLD_D); g.restore();
  }
}

// vertical: a black scoreboard card keeps the numbers readable while the beam passes behind
function hudVertical(g, t) {
  { const a = clamp((t - TL.g0) / 0.25); g.save(); g.globalAlpha = a; drawLogo(g, 70, 96, 270, INK, t); g.restore(); }
  const cu = E.outBack(prog(t, TL.g0 - 0.04, 0.42), 1.4); if (cu <= 0) return;
  const cx = 56, cy = P4 ? 206 : 236, cw = 968, ch = 400;
  const pk = t >= TL.c1 ? 1 + 0.05 * Math.exp(-(t - TL.c1) * 10) : 1;
  g.save(); g.translate(cx + cw / 2, cy + ch / 2); g.scale(cu * pk, cu * pk); g.translate(-cx - cw / 2, -cy - ch / 2);
  g.save(); g.shadowColor = 'rgba(0,0,0,0.35)'; g.shadowBlur = 50; g.shadowOffsetY = 18; g.fillStyle = '#0B0B0B'; roundRect(g, cx, cy, cw, ch, 40); g.fill(); g.restore();
  g.strokeStyle = rgba(GOLD_RGB, 0.55 + 0.45 * (t >= TL.c1 ? Math.exp(-(t - TL.c1) * 3) : 0)); g.lineWidth = 3; roundRect(g, cx + 1.5, cy + 1.5, cw - 3, ch - 3, 39); g.stroke();
  g.save(); roundRect(g, cx, cy, cw, ch, 40); g.clip();
  radial(g, cx + cw * 0.3, cy + ch * 0.55, 700, GOLD_RGB, 0.10 + (t >= TL.c1 ? 0.3 * Math.exp(-(t - TL.c1) * 2.5) : 0));
  chip(g, 'TOTAL PRIZE POOL', cx + 46, cy + 40, 'PB', 30, 8, GOLD, INK, 20, 14, TL.g0 + 0.05, t);
  tagline(g, t, cx + 48, cy + 340, 34, '#FFFFFF', GOLD);
  const size = 168, x = cx + 44, base = cy + 248;
  const sc = landScale(t); const cap = capH('PB', size);
  g.save(); g.translate(x, base - cap / 2); g.scale(sc, sc); g.translate(-x, -(base - cap / 2));
  drawCounter(g, counterValue(t), x, base, size, t, TL.g0 + 0.05, '#FFFFFF');
  g.restore();
  noMaxCapLine(g, t, cx + 48, cy + 350, 56, '#FFFFFF');
  g.restore();
  g.restore();
  if (t >= TL.c1) burst(g, t, x + counterWidth(size) / 2, base - cap / 2);
  if (t >= TL.c1 + 0.3) {          // still climbing, under the card
    const a = clamp((t - TL.c1 - 0.3) / 0.25); const s = 'AND STILL CLIMBING', sz = 44, by = H - 120 + 30 * (1 - E.outCubic(a));
    const Lw = lay('PB', sz, 5, s).w; const x0 = W / 2 - (Lw + 54) / 2;
    g.save(); g.globalAlpha *= a;
    g.fillStyle = 'rgba(10,10,10,0.88)'; roundRect(g, x0 - 30, by - capH('PB', sz) - 22, Lw + 54 + 60, capH('PB', sz) + 44, 30); g.fill();
    text(g, s, x0, by, 'PB', sz, '#FFFFFF', { ls: 5 });
    upArrow(g, x0 + Lw + 34, by - capH('PB', sz) / 2 - 2 * Math.sin(t * 8), 0.95, GOLD); g.restore();
  }
}

/* =====================================================================
   3 WAYS TO WIN — with today's dollar amounts (5.0 – 8.5)
   ===================================================================== */
const WY = P4 ? { hy: 250, hs: 64, bottoms: [610, 912, 1214], xs: [290, 290, 290], sc: 0.325, lx: 590, ls: 54, as: 64, row: true }
  : { hy: 132, hs: 64, bottoms: [640, 640, 640], xs: [362, 962, 1558], sc: 0.385, ls: 48, as: 72, row: false };
function amountPill(g, v, x, y, size, t0, t, align = 'left') {   // black pill, gold rolling dollars; y = top
  if (t < t0) return;
  const s = money(v); const L = lay('PB', size, 1, s); const cap = capH('PB', size);
  const padX = size * 0.42, padY = size * 0.3; const w = L.w + padX * 2, h = cap + padY * 2; const x0 = alignX(x, w, align);
  const u = E.outBack(prog(t, t0, 0.35), 2.0);
  const roll = E.outQuart(prog(t, t0 + 0.05, 0.75)); const shown = Math.round(v * roll);
  const lock = t >= t0 + 0.8 ? 1 + 0.08 * Math.exp(-(t - t0 - 0.8) * 10) : 1;
  g.save(); g.translate(x0 + w / 2, y + h / 2); g.scale(Math.max(0, u) * lock, Math.max(0, u) * lock); g.translate(-(x0 + w / 2), -(y + h / 2));
  g.save(); g.shadowColor = 'rgba(0,0,0,0.25)'; g.shadowBlur = 18; g.shadowOffsetY = 6; g.fillStyle = INK; roundRect(g, x0, y, w, h, h * 0.28); g.fill(); g.restore();
  // digits are laid out on the final string's grid so the pill never jumps in width
  const fs = money(shown).padStart(s.length, ' ');
  font(g, 'PB', size, 0); g.textAlign = 'center'; g.fillStyle = GOLD;
  for (let i = 0; i < s.length; i++) { const ch = fs[i]; if (ch === ' ') continue; g.fillText(ch, x0 + padX + (L.xs[i] + L.xs[i + 1] - 1) / 2, y + padY + cap); }
  if (t > t0 + 0.8 && t < t0 + 1.4) {   // glint on lock
    const su = prog(t, t0 + 0.8, 0.5); const sx = lerp(x0 - 80, x0 + w + 80, E.inOutCubic(su));
    g.save(); roundRect(g, x0, y, w, h, h * 0.28); g.clip(); const lg = g.createLinearGradient(sx - 50, 0, sx + 50, 0);
    lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,240,200,0.35)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = lg; g.fillRect(sx - 50, y, 100, h); g.restore();
  }
  g.restore();
  g.textAlign = 'left';
}
function sceneWays(g, t) {
  g.fillStyle = '#FFFFFF'; g.fillRect(-200, -200, W + 400, H + 400);
  const bg = g.createRadialGradient(W / 2, H * 0.55, 100, W / 2, H * 0.55, Math.max(W, H)); bg.addColorStop(0, '#FFFFFF'); bg.addColorStop(1, '#E2E2E2'); g.fillStyle = bg; g.fillRect(-100, -100, W + 200, H + 200);
  const pz = 1 + 0.03 * E.inOutSine(prog(t, TL.ways + 0.4, TL.ends0 - TL.ways - 0.4));
  g.translate(W / 2, H * 0.52); g.scale(pz, pz); g.translate(-W / 2, -H * 0.52);
  if (V) drawLogo(g, 70, 96, 270, INK, t); else drawLogo(g, 150, 64, 250, INK, t);
  {
    const t0 = TL.ways; const u = E.outExpo(prog(t, t0 - 0.04, 0.34)); if (u > 0) {
      const hs = WY.hs; const L3 = lay('PBI', hs * 1.35, 0, '3'); const Lw = lay('PB', hs, 4, 'WAYS TO WIN'); const cap = capH('PB', hs);
      const padX = 36, gap = 22, w = padX * 2 + L3.w + gap + Lw.w, h = cap + 56; const x0 = W / 2 - w / 2, y0 = WY.hy - h / 2;
      const sc = lerp(1.9, 1, u);
      g.save(); g.translate(W / 2, WY.hy); g.scale(sc, sc); g.translate(-W / 2, -WY.hy); g.globalAlpha *= clamp((t - t0 + 0.02) / 0.05 + 0.3);
      g.fillStyle = INK; roundRect(g, x0, y0, w, h, h / 2); g.fill();
      text(g, '3', x0 + padX, WY.hy + capH('PBI', hs * 1.35) / 2, 'PBI', hs * 1.35, GOLD);
      text(g, 'WAYS TO WIN', x0 + padX + L3.w + gap, WY.hy + cap / 2, 'PB', hs, '#FFFFFF', { ls: 4 });
      g.restore();
    }
  }
  const cols = [
    { img: A.p90, cb: CB90, k: 1.0, l: ['WAGER', 'LEADERBOARD'], prop: null },
    { img: A.p5, cb: CB5, k: 0.93, l: ['RAFFLE'], prop: 'ticket' },
    { img: A.p5, cb: CB5, k: 0.93, l: ['SLOT MULTI', 'LEADERBOARD'], prop: 'reels' },
  ];
  cols.forEach((c, i) => {
    const t0 = TL.ways - 0.12 + i * 0.025; if (t < t0) return;
    const x = WY.xs[i], bot = WY.bottoms[i]; const sc = WY.sc * c.k;
    const d = dropAnim(t, t0, t0 + 0.12, V ? 900 : 760);
    const cw = (c.cb[2] - c.cb[0]) * sc;
    g.save(); g.globalAlpha = 0.2 * clamp(1 + d.dy / 700); g.fillStyle = '#000'; g.beginPath(); g.ellipse(x, bot + 10, cw * 0.45, 16, 0, 0, Math.PI * 2); g.filter = 'blur(10px)'; g.fill(); g.restore();
    const fl = t > t0 + 0.4 ? 5 * Math.sin((t - t0) * Math.PI * 1.3) * prog(t, t0 + 0.4, 0.3) : 0;
    drawPctBottom(g, c.img, c.cb, x, bot + d.dy + fl, sc, d.sx, d.sy);
    if (c.prop) {
      const pu = E.outBack(prog(t, t0 + 0.16, 0.32), 2.2); if (pu > 0) {
        const px = x + cw * (V ? 0.46 : 0.40), py = bot - (V ? 30 : 22) + fl; const img = c.prop === 'ticket' ? A.ticket : A.reels; const cb = c.prop === 'ticket' ? CBT : CBR;
        const ps = (c.prop === 'ticket' ? 0.125 : 0.115) * (V ? 0.95 : 1) * pu;
        g.save(); g.translate(px, py); g.rotate((c.prop === 'ticket' ? -0.2 : -0.05) - 0.5 * (1 - pu)); g.scale(ps, ps); g.drawImage(img, -(cb[0] + cb[2]) / 2, -(cb[1] + cb[3]) / 2); g.restore();
      }
    }
    const ls = WY.ls; const ta = TL.ways + 0.22 + i * 0.16;
    if (WY.row) {
      const lx = WY.lx; const two = c.l.length === 2; const b2 = bot - 114, b1 = two ? b2 - ls * 1.1 : b2;
      riseText(g, c.l[0], lx, b1, 'PB', ls, INK, t0 + 0.06, t, { stagger: 0.012, dur: 0.4 });
      if (two) riseText(g, c.l[1], lx, b2, 'PB', ls, INK, t0 + 0.1, t, { stagger: 0.012, dur: 0.4 });
      amountPill(g, PRZ[i], lx - 2, bot - 90, WY.as, ta, t, "left");
    } else {
      const b1 = bot + 104, b2 = bot + 104 + ls * 1.1;
      riseText(g, c.l[0], x, b1, 'PB', ls, INK, t0 + 0.06, t, { stagger: 0.012, dur: 0.4, align: 'center' });
      if (c.l[1]) riseText(g, c.l[1], x, b2, 'PB', ls, INK, t0 + 0.1, t, { stagger: 0.012, dur: 0.4, align: 'center' });
      amountPill(g, PRZ[i], x, bot + 104 + ls * 1.1 + 34, WY.as, ta, t, 'center');
    }
  });
  vignette(g, 0.06);
}

/* =====================================================================
   ROUND ENDS (8.5 – 10.0)
   ===================================================================== */
function sceneEnds(g, t) {
  g.fillStyle = '#060606'; g.fillRect(-200, -200, W + 400, H + 400);
  const bp = beatPulse(t, 5);
  radial(g, W / 2, H / 2 + 40, 1000, GOLD_RGB, 0.12 + 0.2 * bp * (t >= TL.endsSlam ? 1 : 0.4));
  sunburst(g, W / 2, H / 2, 1800, 22, 0.3 + (t - 8) * 0.45, GOLD_RGB, 0.06);
  vignette(g, 0.7);
  const has = ENDS.length > 0;
  const l1 = has ? (ROUND ? `ROUND ${ROUND} ENDS` : 'ROUND ENDS') : 'BI-WEEKLY', l2 = has ? ENDS : 'LEADERBOARD';
  const TW = P4 ? 900 : 1240; const s2 = Math.min(P4 ? 300 : 330, TW / lay('PBI', 100, -4, l2).w * 100);
  const s1 = P4 ? 64 : 76, c1 = capH('PB', s1), c2 = capH('PBI', s2);
  const chipS = P4 ? 60 : 64, chipH = capH('PB', chipS) + chipS * 0.62;
  const g1 = P4 ? 60 : 54, g2 = P4 ? 70 : 60; const showChip = has && LEFT >= 0;
  const total = c1 + g1 + c2 + (showChip ? g2 + chipH : 0); const top = (H - total) / 2;
  const b1 = top + c1, b2 = b1 + g1 + c2, cy = b2 + g2;
  const sc = 1 + 0.04 * E.inOutSine(prog(t, TL.endsIn, 1.5));
  g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-W / 2, -H / 2);
  riseText(g, l1, W / 2 + 5, b1, 'PB', s1, '#FFFFFF', TL.endsIn, t, { ls: 10, align: 'center', stagger: 0.014, dur: 0.42 });
  slam(g, l2, W / 2, b2, 'PBI', s2, GOLD, TL.endsSlam, t, { ls: -4, s0: 2.6, dur: 0.36, glow: 60, rot0: -0.2 });
  if (showChip) {
    const s = LEFT === 0 ? 'LAST DAY!' : LEFT === 1 ? '1 DAY LEFT' : `${LEFT} DAYS LEFT`;
    chip(g, s, W / 2, cy, 'PB', chipS, 6, '#FFFFFF', INK, chipS * 0.5, chipS * 0.31, TL.endsSlam + 0.16, t, 'center');
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
  g.fillStyle = '#050505'; g.fillRect(-200, -200, W + 400, H + 400);
  const spot = 0.35 * clamp((t - TL.end + 0.05) / 0.3) + 0.65 * clamp((t - TL.end - 0.45) / 0.5); const bp = beatPulse(t, 4);
  const mcx = V ? 540 : 1500, mcy = P4 ? 1080 : V ? 1480 : 560;
  radial(g, mcx, mcy, 1000, GOLD_RGB, (0.20 + 0.08 * bp) * spot);
  sunburst(g, mcx, mcy, 1500, 20, (t - 14) * 0.12, GOLD_RGB, 0.055 * spot);
  radial(g, V ? 540 : 520, V ? 640 : 620, 900, GOLD_RGB, 0.07);
  vignette(g, 0.7);
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
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  const sh = shake(t); g.translate(W / 2 + sh.x, H / 2 + sh.y); g.rotate(sh.r); g.translate(-W / 2, -H / 2);
  if (t < TL.w1) sceneHook(g, t);
  else if (t < TL.w1 + 0.3) { sceneHook(g, t); bandWipe(g, t, TL.w1, 0.3, sceneGraph, 1); }
  else if (t < TL.ways0) sceneGraph(g, t);
  else if (t < TL.ways0 + 0.3) { sceneGraph(g, t); bandWipe(g, t, TL.ways0, 0.3, sceneWays, -1); }
  else if (t < TL.ends0) sceneWays(g, t);
  else if (t < TL.ends0 + 0.3) { sceneWays(g, t); iris(g, t, TL.ends0, 0.3, W / 2, H / 2, sceneEnds); }
  else if (t < TL.end0) sceneEnds(g, t);
  else if (t < TL.end0 + 0.26) pushUp(g, t, TL.end0, 0.26, sceneEnds, sceneEnd);
  else sceneEnd(g, t);
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (const [tf, c, a, k] of FLASHES) { if (t < tf) continue; const e = a * Math.exp(-(t - tf) * k); if (e < 0.004) continue; g.fillStyle = rgba(c, e); g.fillRect(0, 0, W, H); }
}

window.renderFrame = (t, N = 8, shutter = 0.5) => {
  for (let i = 0; i < N; i++) {
    const ti = N === 1 ? t : t + ((i + 0.5) / N - 0.5) * shutter / FPS; FRAME_T = t;
    renderScene(sctx, Math.max(0, ti));
    ctx.globalAlpha = 1 / (i + 1); ctx.drawImage(SUB, 0, 0);
  }
  ctx.globalAlpha = 1; return true;
};
window.DURATION = DURATION;
init();
