// Each scene: (ctx) => ({ update(t) }) ; t in seconds from clip start.
// Safe zone for 4:5: keep content within x∈[-3.2,3.2], y∈[-1.0,4.6] (subtitles sit at y≈-2.9).
export const SCENES = {};

function ground(ctx, y = -1.2) {
  const { THREE } = ctx.H;
  const g = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.ShadowMaterial({ opacity: 0.18 }));
  g.rotation.x = -Math.PI / 2; g.position.y = y; g.receiveShadow = true; ctx.scene.add(g); return g;
}

// ---------- 1. DECIBEL METER: loud noise ("un trattore resta un trattore")
SCENES.decibel = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, RoundedBoxGeometry } = ctx.H;
  const { scene, params } = ctx;
  ground(ctx, -1.25);
  const root = new THREE.Group(); root.position.y = -0.3; scene.add(root);
  const N = 10, segs = [];
  const geo = new RoundedBoxGeometry(2.2, 0.36, 0.6, 3, 0.1);
  const colors = [];
  for (let i = 0; i < N; i++) {
    const c = new THREE.Color(i < 5 ? PAL.green : i < 8 ? PAL.yellow : PAL.red); colors.push(c);
    const m = mat(0xd9d2c8, { emissive: new THREE.Color(0x000000) });
    const b = new THREE.Mesh(geo, m); b.position.y = -1 + i * 0.44; b.castShadow = true;
    root.add(b); segs.push(b);
  }
  const frame = new THREE.Mesh(new RoundedBoxGeometry(2.8, N * 0.44 + 0.4, 0.5, 4, 0.2), mat(PAL.ink, { roughness: 0.5 }));
  frame.position.set(0, -1 + (N - 1) * 0.22, -0.35); frame.castShadow = true; root.add(frame);
  const label = new THREE.Mesh(text(params.label || '100 dB', { size: 0.8, depth: 0.3 }), [mat(PAL.yellow), mat(PAL.ink)]);
  label.position.set(0, 3.95, 0.3); label.castShadow = true; root.add(label);
  // shock rings
  const rings = [];
  for (let i = 0; i < 3; i++) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(1, 0.06, 12, 80), new THREE.MeshBasicMaterial({ color: PAL.red, transparent: true }));
    r.position.set(0, 1.0, -1.2); scene.add(r); rings.push(r);
  }
  return {
    update(t) {
      const tgt = params.level ?? N;
      const lvl = params.drop ? Math.max(0, N - seg(t, 0.3, 1.3) * (N - tgt)) : Math.min(N, seg(t, 0.15, 1.0) * tgt + (t > 1.0 && tgt > 7 ? Math.sin(t * 22) * 0.6 : 0));
      segs.forEach((b, i) => {
        const on = i < lvl;
        b.material.color.set(on ? colors[i] : 0xd9d2c8);
        b.material.emissive.copy(on ? colors[i] : new THREE.Color(0)).multiplyScalar(on ? 0.15 : 0);
        b.scale.setScalar(on ? 1 : 0.92);
      });
      const pop = easeOutBack(seg(t, 0.0, 0.5));
      root.scale.setScalar((0.6 + 0.4 * pop) * 1.12);
      root.rotation.y = (1 - pop) * -0.9 + Math.sin(t * 1.3) * 0.18;
      const shake = (t > 0.9 && !params.drop && (params.level ?? N) > 7) ? 0.05 : 0;
      root.position.x = Math.sin(t * 63) * shake; root.position.z = Math.cos(t * 71) * shake;
      label.scale.setScalar(easeOutBack(seg(t, 0.6, 1.0), 2.5) * (1 + Math.max(0, Math.sin(t * 9)) * 0.06));
      rings.forEach((r, i) => {
        const p = ((t - 0.8 + i * 0.33) % 1 + 1) % 1; const vis = t > 0.8 && !params.drop && (params.level ?? N) > 7;
        r.scale.setScalar(1.5 + p * 3.5); r.material.opacity = vis ? (1 - p) * 0.7 : 0;
      });
    }
  };
};

// ---------- 2. PRICE: big 3D number with coins ("costa oltre 2000 euro")
SCENES.price = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, spring, rand } = ctx.H;
  const { scene, params } = ctx;
  ground(ctx, -1.0);
  const str = params.text || '2.000€';
  const g = text(str, { size: params.size || 0.95, depth: 0.6, bevel: 0.05 });
  const num = new THREE.Mesh(g, [mat(PAL.yellow, { roughness: 0.25 }), mat(0x2a2622)]);
  num.castShadow = true; num.position.y = 1.6; scene.add(num);
  const sub = params.sub ? new THREE.Mesh(text(params.sub, { size: 0.42, depth: 0.15, font: 'xbold' }), [mat(PAL.ink), mat(PAL.ink)]) : null;
  if (sub) { sub.position.y = 0.2; scene.add(sub); }
  let pstrike = null; if (params.strike) { pstrike = new THREE.Mesh(new THREE.BoxGeometry(1, 0.2, 0.2), mat(PAL.red)); pstrike.position.set(0, 1.6, 0.6); pstrike.rotation.z = 0.15; scene.add(pstrike); }
  const coinGeo = new THREE.CylinderGeometry(0.42, 0.42, 0.09, 48);
  const gold = new THREE.MeshPhysicalMaterial({ color: 0xf2c14e, metalness: 1, roughness: 0.22, envMapIntensity: 1.4 });
  const R = rand(7), coins = [];
  for (let i = 0; i < (params.coins ?? 18); i++) {
    const c = new THREE.Mesh(coinGeo, gold); c.castShadow = true;
    c.userData = { x: (R() - 0.5) * 6, z: -1.5 + R() * 2.5, d: 0.1 + R() * 1.0, rx: R() * 6, rz: R() * 6, sp: 2 + R() * 4 };
    scene.add(c); coins.push(c);
  }
  return {
    update(t) {
      const s = spring(seg(t, 0, 0.9), 2.2, 4.2);
      num.scale.setScalar(Math.max(0.001, s));
      num.rotation.y = (1 - easeOutBack(seg(t, 0, 0.8))) * Math.PI * 0.9 + Math.sin(t * 1.4) * 0.15;
      num.rotation.x = Math.sin(t * 1.1) * 0.06;
      if (sub) { sub.scale.setScalar(easeOutBack(seg(t, 0.45, 0.8))); }
      if (pstrike) pstrike.scale.x = Math.max(0.001, ctx.H.easeOutCubic(seg(t, 0.8, 1.05)) * 6.2);
      coins.forEach((c) => {
        const u = c.userData; const tt = t - u.d;
        const y = tt < 0 ? 12 : Math.max(-0.95, 8 - 0.5 * 22 * tt * tt);
        c.position.set(u.x, y, u.z);
        c.rotation.set(u.rx + tt * u.sp, 0, u.rz + tt * u.sp * 0.7);
        if (y <= -0.95) c.rotation.set(Math.PI / 2 * 0 + 0.02, u.rx, 0.02);
      });
    }
  };
};

// ---------- 3. AIRWAY: throat tube collapsing ("la gola si restringe / cannuccia schiacciata")
SCENES.airway = (ctx) => {
  const { THREE, PAL, seg, easeInOut, rand } = ctx.H;
  const { scene } = ctx;
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.8, 4.6, 0), new THREE.Vector3(0.4, 3.2, 0.3), new THREE.Vector3(0, 1.6, 0),
    new THREE.Vector3(-0.3, 0.2, -0.2), new THREE.Vector3(0.3, -1.0, 0)]);
  const TS = 160, RS = 48, R0 = 0.75;
  const geo = new THREE.TubeGeometry(curve, TS, R0, RS, false);
  const orig = geo.attributes.position.array.slice();
  const centers = []; for (let i = 0; i <= TS; i++) centers.push(curve.getPointAt(i / TS));
  const amode = ctx.params.mode || 'squeeze';
  const tubeMat = new THREE.MeshPhysicalMaterial({ color: amode === 'straw' ? 0xfff1a8 : amode === 'open' ? 0x9fd8ff : 0xf28b8b, roughness: 0.3, transmission: 0.55, thickness: 0.6, transparent: true, opacity: 0.85, side: THREE.DoubleSide, clearcoat: 1, envMapIntensity: 1.2 });
  const tube = new THREE.Mesh(geo, tubeMat); scene.add(tube);
  // air particles
  const R = rand(3), parts = [];
  const pGeo = new THREE.SphereGeometry(0.07, 12, 12);
  const pMat = new THREE.MeshBasicMaterial({ color: 0x4aa8ff }), pMatR = new THREE.MeshBasicMaterial({ color: PAL.red });
  for (let i = 0; i < 90; i++) { const m = new THREE.Mesh(pGeo, pMat); m.userData = { o: R(), a: R() * 6.28, r: R() * 0.45 }; scene.add(m); parts.push(m); }
  const SQ = 0.55; // squeeze location along tube
  const rings = []; for (let i = 0; i < 3; i++) { const r = new THREE.Mesh(new THREE.TorusGeometry(1, 0.05, 12, 64), new THREE.MeshBasicMaterial({ color: PAL.red, transparent: true, opacity: 0 })); r.position.copy(curve.getPointAt(SQ)); r.position.z = -0.6; scene.add(r); rings.push(r); }
  const alab = addLabel(ctx, ctx.params.label, -0.6, { size: 0.6, color: ctx.params.labelColor || 'ink', delay: 0.5 });
  const squeeze = (u, k) => 1 - k * Math.exp(-Math.pow((u - SQ) / 0.09, 2));
  return {
    update(t) {
      const k = amode === 'open' ? 0 : amode === 'vibrate' ? 0.62 : 0.78 * easeInOut(seg(t, 0.5, 1.6));
      const vib = amode === 'vibrate' ? Math.sin(t * 70) * 0.12 : (amode !== 'open' && t > 1.4) ? Math.sin(t * 70) * 0.06 : 0;
      rings.forEach((r, i) => { const p = ((t * 1.2 + i / 3) % 1); r.scale.setScalar(0.8 + p * 2.5); r.material.opacity = amode === 'vibrate' ? (1 - p) * 0.7 : 0; });
      const p = geo.attributes.position.array;
      for (let i = 0; i <= TS; i++) {
        const u = i / TS, f = squeeze(u, k + vib * Math.exp(-Math.pow((u - SQ) / 0.12, 2))), c = centers[i];
        for (let j = 0; j <= RS; j++) {
          const idx = (i * (RS + 1) + j) * 3;
          p[idx] = c.x + (orig[idx] - c.x) * f; p[idx + 1] = c.y + (orig[idx + 1] - c.y) * f; p[idx + 2] = c.z + (orig[idx + 2] - c.z) * f;
        }
      }
      geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
      tube.rotation.y = Math.sin(t * 0.8) * 0.35 + 0.2;
      parts.forEach((m) => {
        const d = m.userData; const speed = (amode === 'open' ? 0.6 : 0.35) * (1 - 0.6 * k);
        const u = (d.o + t * speed) % 1; const c = curve.getPointAt(u);
        const rr = d.r * squeeze(u, k) * R0;
        m.position.set(c.x + Math.cos(d.a + t * 3) * rr, c.y, c.z + Math.sin(d.a + t * 3) * rr);
        m.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), tube.rotation.y);
        m.material = (k > 0.5 && Math.abs(u - SQ) < 0.12) ? pMatR : pMat;
      });
      alab.update(t);
    }
  };
};

// ---------- 4. WORD3D: big extruded words that spring in (lines: [{t, color, size}])
SCENES.word3d = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, spring } = ctx.H;
  const { scene, params } = ctx;
  ground(ctx, -1.1);
  const lines = params.lines || [{ t: 'CIAO' }];
  const meshes = [];
  const totalH = lines.reduce((a, l) => a + (l.size || 0.9) * 1.35, 0);
  let y = 1.7 + totalH / 2;
  lines.forEach((l, i) => {
    const sz = l.size || 0.9; y -= sz * 1.35 / 2 + (i ? 0 : 0);
    const col = l.color === 'ink' ? PAL.ink : l.color === 'red' ? PAL.red : l.color === 'white' ? 0xffffff : l.color === 'green' ? PAL.green : PAL.yellow;
    const side = l.color === 'ink' ? 0x4a4440 : 0x2a2622;
    const m = new THREE.Mesh(text(l.t, { size: sz, depth: sz * 0.55, bevel: sz * 0.05 }), [mat(col, { roughness: 0.28 }), mat(side)]);
    m.castShadow = true; m.position.y = y; m.userData = { y, d: i * 0.18 }; scene.add(m); meshes.push(m);
    y -= sz * 1.35 / 2;
  });
  // decorative floating shapes
  const deco = [];
  const shapes = [new THREE.TorusGeometry(0.28, 0.1, 16, 40), new THREE.IcosahedronGeometry(0.28, 0), new THREE.SphereGeometry(0.22, 24, 24)];
  const pos = [[-2.6, 4.2, -1], [2.7, 3.6, -0.5], [-2.4, -0.2, 0.3], [2.5, 0.2, -1.2]];
  pos.forEach((p, i) => { const m = new THREE.Mesh(shapes[i % 3], mat(i % 2 ? PAL.yellow : 0xffffff)); m.position.set(...p); m.castShadow = true; scene.add(m); deco.push(m); });
  // optional strike-through bar
  let strike = null;
  if (params.strike) { strike = new THREE.Mesh(new THREE.BoxGeometry(1, 0.22, 0.22), mat(PAL.red)); strike.position.set(0, meshes[params.strike - 1].position.y, 0.6); strike.rotation.z = -0.12; scene.add(strike); }
  return {
    update(t) {
      meshes.forEach((m) => {
        const u = seg(t, m.userData.d, m.userData.d + 0.7);
        m.scale.setScalar(Math.max(0.001, spring(u, 2.0, 4.5)));
        m.rotation.x = (1 - easeOutBack(u)) * -1.2;
        m.rotation.y = Math.sin(t * 1.2 + m.userData.d * 5) * 0.12;
        m.position.y = m.userData.y + Math.sin(t * 2 + m.userData.d * 4) * 0.05;
      });
      deco.forEach((m, i) => { const u = easeOutBack(seg(t, 0.2 + i * 0.08, 0.7 + i * 0.08)); m.scale.setScalar(Math.max(0.001, u)); m.rotation.set(t * (0.8 + i * 0.2), t * (1 + i * 0.3), 0); m.position.y = pos[i][1] + Math.sin(t * 1.5 + i) * 0.15; });
      if (strike) { const u = ctx.H.easeOutCubic(seg(t, params.strikeAt || 0.8, (params.strikeAt || 0.8) + 0.25)); strike.scale.x = Math.max(0.001, u * (params.strikeW || 5.6)); }
    }
  };
};

// ---------- 5. CLOCK: alarm/clock with spinning hands (params.from,to in hours ; label)
SCENES.clock = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, easeInOut } = ctx.H;
  const { scene, params } = ctx;
  ground(ctx, -1.3);
  const g = new THREE.Group(); g.position.y = 1.7; scene.add(g);
  const body = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 0.6, 72), mat(params.body || PAL.yellow)); body.rotation.x = Math.PI / 2; body.castShadow = true; g.add(body);
  const face = new THREE.Mesh(new THREE.CylinderGeometry(1.75, 1.75, 0.62, 72), mat(0xfaf6ef, { clearcoat: 0.2 })); face.rotation.x = Math.PI / 2; face.position.z = 0.01; g.add(face);
  for (let i = 0; i < 12; i++) { const tk = new THREE.Mesh(new THREE.BoxGeometry(0.08, i % 3 ? 0.18 : 0.32, 0.05), mat(PAL.ink)); const a = i / 12 * Math.PI * 2; tk.position.set(Math.sin(a) * 1.5, Math.cos(a) * 1.5, 0.33); tk.rotation.z = -a; g.add(tk); }
  const mkHand = (len, w, c) => { const h = new THREE.Group(); const m = new THREE.Mesh(new THREE.BoxGeometry(w, len, 0.06), mat(c)); m.position.y = len / 2 - 0.12; h.add(m); h.position.z = 0.38; g.add(h); return h; };
  const hh = mkHand(0.95, 0.14, PAL.ink), mh = mkHand(1.35, 0.09, PAL.ink), sh = mkHand(1.4, 0.035, PAL.red);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.1, 24), mat(PAL.red)); hub.rotation.x = Math.PI / 2; hub.position.z = 0.42; g.add(hub);
  // bells
  const bells = [];
  [-1, 1].forEach((s) => { const b = new THREE.Mesh(new THREE.SphereGeometry(0.62, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), mat(params.body || PAL.yellow)); b.position.set(s * 1.25, 1.75, -0.1); b.rotation.z = -s * 0.6; b.castShadow = true; g.add(b); bells.push(b); });
  const label = params.label ? new THREE.Mesh(text(params.label, { size: 0.75, depth: 0.32 }), [mat(params.labelColor === 'red' ? PAL.red : PAL.ink), mat(0x2a2622)]) : null;
  if (label) { label.position.set(0, -1.05, 0.6); label.castShadow = true; scene.add(label); }
  const from = params.from ?? 1, to = params.to ?? 3;
  return {
    update(t) {
      g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5))));
      const hrs = from + (to - from) * easeInOut(seg(t, 0.2, 1.4));
      hh.rotation.z = -hrs / 12 * Math.PI * 2; mh.rotation.z = -(hrs % 1) * Math.PI * 2; sh.rotation.z = -t * 6;
      const ring = params.ring ? Math.sin(t * 60) * 0.06 : 0;
      g.rotation.z = ring; g.rotation.y = Math.sin(t * 0.9) * 0.25 - 0.15;
      if (label) label.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.4, 0.8), 2.2)));
    }
  };
};

// ---------- 6. CALENDAR: grid of days, marks appear (params.marks: indices; params.all: true; label)
SCENES.calendar = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, RoundedBoxGeometry } = ctx.H;
  const { scene, params } = ctx;
  ground(ctx, -1.3);
  const g = new THREE.Group(); g.position.y = 1.6; scene.add(g);
  const board = new THREE.Mesh(new RoundedBoxGeometry(5.2, 5.4, 0.3, 4, 0.25), mat(0xfaf6ef)); board.castShadow = true; g.add(board);
  const top = new THREE.Mesh(new RoundedBoxGeometry(5.2, 1.0, 0.36, 4, 0.2), mat(params.topColor === 'yellow' ? PAL.yellow : PAL.red)); top.position.set(0, 2.25, 0.04); g.add(top);
  const ttl = new THREE.Mesh(text(params.title || 'NOTTI', { size: 0.42, depth: 0.1, font: 'xbold', bevel: 0.01 }), [mat(params.topColor === 'yellow' ? PAL.ink : 0xffffff), mat(0xdddddd)]); ttl.position.set(0, 2.25, 0.3); g.add(ttl);
  const cells = []; const marks = new Set(params.all ? [...Array(28).keys()] : (params.marks || [3, 11, 19]));
  const xg = new THREE.BoxGeometry(0.5, 0.11, 0.08);
  for (let i = 0; i < 28; i++) {
    const r = Math.floor(i / 7), c = i % 7;
    const cell = new THREE.Mesh(new RoundedBoxGeometry(0.6, 0.72, 0.12, 2, 0.06), mat(0xe9e1d4)); cell.position.set(-2.1 + c * 0.7, 1.15 - r * 0.86, 0.18); g.add(cell);
    if (marks.has(i)) {
      const x = new THREE.Group(); const a = new THREE.Mesh(xg, mat(params.markColor === 'green' ? PAL.green : PAL.red)); const b = a.clone(); a.rotation.z = 0.78; b.rotation.z = -0.78; x.add(a, b);
      x.position.set(cell.position.x, cell.position.y, 0.3); x.userData.i = i; g.add(x); cells.push(x);
    }
  }
  const order = [...cells].sort((a, b) => a.userData.i - b.userData.i);
  const label = params.label ? new THREE.Mesh(text(params.label, { size: 0.7, depth: 0.3 }), [mat(PAL.yellow), mat(0x2a2622)]) : null;
  if (label) { label.position.set(0, -1.75, 0.8); label.castShadow = true; scene.add(label); }
  const span = params.span || 1.0;
  return {
    update(t) {
      g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5))));
      g.rotation.y = Math.sin(t * 0.8) * 0.22 - 0.1; g.rotation.x = -0.08;
      order.forEach((x, k) => { const st = 0.35 + (k / Math.max(1, order.length)) * span; x.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, st, st + 0.18), 3))); });
      if (label) label.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.5, 0.9), 2)));
    }
  };
};

// ======================= shared builders =======================
function colorOf(PAL, c, def) { return c === 'ink' ? PAL.ink : c === 'red' ? PAL.red : c === 'green' ? PAL.green : c === 'white' ? 0xffffff : c === 'blue' ? PAL.blue : c === 'yellow' ? PAL.yellow : (c ?? def); }
function addLabel(ctx, str, y = -1.0, { size = 0.62, color = 'yellow', delay = 0.35, z = 0.8 } = {}) {
  if (!str) return { update() {} };
  const { THREE, PAL, mat, text, seg, easeOutBack } = ctx.H;
  const col = colorOf(PAL, color, PAL.yellow);
  const m = new THREE.Mesh(text(str, { size, depth: size * 0.45, bevel: size * 0.05, maxW: 5.4 }), [mat(col, { roughness: 0.28 }), mat(color === 'ink' ? 0x4a4440 : 0x2a2622)]);
  m.position.set(0, y, z); m.castShadow = true; ctx.scene.add(m);
  return { mesh: m, update(t) { const u = seg(t, delay, delay + 0.45); m.scale.setScalar(Math.max(0.001, easeOutBack(u, 2.2))); m.rotation.y = Math.sin(t * 1.3) * 0.1; } };
}
function checkMark(ctx, color, s = 1) {
  const { THREE, mat } = ctx.H; const g = new THREE.Group(); const m = mat(color);
  const a = new THREE.Mesh(new THREE.BoxGeometry(0.22 * s, 0.6 * s, 0.22 * s), m); a.position.set(-0.22 * s, -0.08 * s, 0); a.rotation.z = 0.75;
  const b = new THREE.Mesh(new THREE.BoxGeometry(0.22 * s, 1.1 * s, 0.22 * s), m); b.position.set(0.18 * s, 0.12 * s, 0); b.rotation.z = -0.6;
  a.castShadow = b.castShadow = true; g.add(a, b); return g;
}
function xMark(ctx, color, s = 1) {
  const { THREE, mat } = ctx.H; const g = new THREE.Group(); const m = mat(color);
  const a = new THREE.Mesh(new THREE.BoxGeometry(0.22 * s, 1.0 * s, 0.22 * s), m); a.rotation.z = 0.78;
  const b = a.clone(); b.rotation.z = -0.78; a.castShadow = b.castShadow = true; g.add(a, b); return g;
}
function pawn(ctx, color) {
  const { THREE, mat } = ctx.H; const g = new THREE.Group(); const m = mat(color);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 0.7, 8, 24), m); body.position.y = 0.55; body.scale.set(1, 1, 0.8);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.36, 32, 24), m); head.position.y = 1.55;
  body.castShadow = head.castShadow = true; g.add(body, head); return g;
}
function heartShape(THREE, s = 1) {
  const sh = new THREE.Shape(); const x = 0, y = 0;
  sh.moveTo(x, y + 0.35 * s);
  sh.bezierCurveTo(x, y + 0.6 * s, x - 0.55 * s, y + 0.75 * s, x - 0.7 * s, y + 0.35 * s);
  sh.bezierCurveTo(x - 0.85 * s, y - 0.05 * s, x - 0.3 * s, y - 0.35 * s, x, y - 0.7 * s);
  sh.bezierCurveTo(x + 0.3 * s, y - 0.35 * s, x + 0.85 * s, y - 0.05 * s, x + 0.7 * s, y + 0.35 * s);
  sh.bezierCurveTo(x + 0.55 * s, y + 0.75 * s, x, y + 0.6 * s, x, y + 0.35 * s);
  return sh;
}
function extrude(THREE, shape, depth = 0.3, bevel = 0.06) {
  const g = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 3, curveSegments: 24 });
  g.center(); return g;
}
function biteGeometry(THREE, w = 1.6, d = 1.9, t = 0.32, h = 0.42) {
  // U-shaped tray (horseshoe) seen from above
  const sh = new THREE.Shape(); const N = 40;
  for (let i = 0; i <= N; i++) { const a = Math.PI * i / N; const x = Math.cos(a) * w, y = Math.sin(a) * d; i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
  for (let i = N; i >= 0; i--) { const a = Math.PI * i / N; sh.lineTo(Math.cos(a) * (w - t), Math.sin(a) * (d - t)); }
  sh.closePath();
  const g = new THREE.ExtrudeGeometry(sh, { depth: h, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.06, bevelSegments: 3, curveSegments: 12 });
  g.center(); g.rotateX(-Math.PI / 2); return g;
}
function biteMesh(ctx, color = 0x9fd4ff) {
  const { THREE } = ctx.H; const g = new THREE.Group();
  const m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.15, transmission: 0.6, thickness: 0.5, transparent: true, opacity: 0.92, clearcoat: 1, envMapIntensity: 1.3 });
  const up = new THREE.Mesh(biteGeometry(THREE), m); up.position.y = 0.26; up.castShadow = true;
  const lo = new THREE.Mesh(biteGeometry(THREE), m); lo.position.y = -0.26; lo.castShadow = true;
  // teeth hints
  const tm = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.3, clearcoat: 0.5 });
  [up, lo].forEach((tray, k) => { for (let i = 0; i < 12; i++) { const a = Math.PI * (i + 0.5) / 12; const tt = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.22, 0.2), tm); tt.position.set(Math.cos(a) * 1.44, k ? -0.0 : 0.0, -Math.sin(a) * 1.74 + 0.95); tt.rotation.y = a - Math.PI / 2; tray.add(tt); } });
  g.add(up, lo); g.userData = { up, lo }; return g;
}
function cardboardBox(ctx, color = 0xc9a26b, w = 2.2, h = 1.6, d = 2.0) {
  const { THREE, mat } = ctx.H; const g = new THREE.Group(); const m = mat(color, { clearcoat: 0, roughness: 0.8 });
  const t = 0.06;
  const parts = [[w, t, d, 0, -h / 2, 0], [w, h, t, 0, 0, d / 2], [w, h, t, 0, 0, -d / 2], [t, h, d, w / 2, 0, 0], [t, h, d, -w / 2, 0, 0]];
  parts.forEach(([a, b, c, x, y, z]) => { const p = new THREE.Mesh(new THREE.BoxGeometry(a, b, c), m); p.position.set(x, y, z); p.castShadow = true; g.add(p); });
  const flaps = [];
  [[0, d / 2, 0], [0, -d / 2, Math.PI]].forEach(([x, z, r]) => { const piv = new THREE.Group(); piv.position.set(x, h / 2, z); piv.rotation.y = r; const f = new THREE.Mesh(new THREE.BoxGeometry(w, t, d / 2), m); f.position.z = -d / 4; f.castShadow = true; piv.add(f); g.add(piv); flaps.push(piv); });
  const tape = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.02, d * 0.98), mat(0xe8d3a8)); tape.position.y = h / 2 + 0.04; g.add(tape);
  g.userData = { flaps, tape, h }; return g;
}

// ======================= more scenes =======================
SCENES.face = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, rand } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 1.7; scene.add(g);
  const mood = params.mood || 'angry';
  const head = new THREE.Mesh(new THREE.SphereGeometry(1.9, 64, 48), mat(mood === 'angry' ? 0xff8a3d : PAL.yellow, { roughness: 0.3 })); head.castShadow = true; g.add(head);
  const eyeW = mat(0xffffff), pup = mat(PAL.ink);
  const eyes = [-0.62, 0.62].map((x) => { const e = new THREE.Mesh(new THREE.SphereGeometry(0.36, 32, 24), eyeW); e.position.set(x, 0.35, 1.7); e.scale.z = 0.5; const p = new THREE.Mesh(new THREE.SphereGeometry(0.17, 24, 16), pup); p.position.set(0, -0.05, 0.3); e.add(p); g.add(e); return e; });
  const brows = [-1, 1].map((s) => { const b = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.16, 0.2), pup); b.position.set(s * 0.62, 0.92, 1.72); b.rotation.z = mood === 'angry' ? s * 0.45 : mood === 'tired' ? s * 0.25 : 0; g.add(b); return b; });
  const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.09, 16, 40, Math.PI), pup); mouth.position.set(0, mood === 'happy' ? -0.35 : -0.75, 1.72); mouth.rotation.z = mood === 'happy' ? Math.PI : 0; g.add(mouth);
  if (mood === 'tired') eyes.forEach((e) => e.scale.y = 0.35);
  const R = rand(5), puffs = [];
  if (mood === 'angry') for (let i = 0; i < 10; i++) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.25 + R() * 0.2, 16, 12), mat(0xffffff, { transparent: true, opacity: 0.85 })); p.userData = { x: (R() < 0.5 ? -1 : 1) * (1.2 + R() * 0.4), o: R() }; scene.add(p); puffs.push(p); }
  const lab = addLabel(ctx, params.label, -1.15, { size: 0.6, color: params.labelColor || 'ink' });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2)));
    g.rotation.y = Math.sin(t * 1.1) * 0.2; g.rotation.z = mood === 'angry' ? Math.sin(t * 40) * 0.02 : 0;
    puffs.forEach((p) => { const u = (t * 0.9 + p.userData.o) % 1; p.position.set(p.userData.x * (1 + u * 0.3), 3.4 + u * 1.6, 0); p.scale.setScalar(Math.max(0.001, (0.6 + u) * (t > 0.3 ? 1 : 0))); p.material.opacity = 0.85 * (1 - u); });
    lab.update(t);
  } };
};

SCENES.battery = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, easeInOut, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.25);
  const g = new THREE.Group(); g.position.y = 1.7; g.rotation.z = 0; scene.add(g);
  const shell = new THREE.Mesh(new RoundedBoxGeometry(4.2, 2.2, 1.1, 5, 0.3), new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.05, transmission: 0.85, thickness: 0.4, transparent: true, opacity: 0.6, clearcoat: 1 }));
  const frame = new THREE.Mesh(new RoundedBoxGeometry(4.35, 2.35, 1.0, 5, 0.32), mat(PAL.ink)); frame.position.z = -0.12; frame.castShadow = true;
  const cap = new THREE.Mesh(new RoundedBoxGeometry(0.35, 0.9, 0.7, 3, 0.1), mat(PAL.ink)); cap.position.x = 2.3;
  const fill = new THREE.Mesh(new RoundedBoxGeometry(3.8, 1.8, 0.8, 4, 0.2), mat(PAL.green, { emissive: new THREE.Color(0) }));
  g.add(frame, fill, shell, cap);
  let bolt = null;
  if (params.bolt) { const sh = new THREE.Shape(); sh.moveTo(0.2, 0.9); sh.lineTo(-0.45, -0.1); sh.lineTo(-0.02, -0.1); sh.lineTo(-0.25, -0.9); sh.lineTo(0.45, 0.15); sh.lineTo(0.02, 0.15); sh.closePath(); bolt = new THREE.Mesh(extrude(THREE, sh, 0.25, 0.04), mat(0xffffff)); bolt.position.z = 0.7; g.add(bolt); }
  const from = params.from ?? 1, to = params.to ?? 0.12;
  const lab = addLabel(ctx, params.label, -0.75, { size: 0.65, color: params.labelColor || 'ink' });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2)));
    g.rotation.y = Math.sin(t * 0.9) * 0.3 - 0.15; g.rotation.x = 0.1;
    const lv = Math.max(0.03, from + (to - from) * easeInOut(seg(t, 0.35, 1.5)));
    fill.scale.x = lv; fill.position.x = -1.9 * (1 - lv);
    const c = lv < 0.3 ? PAL.red : lv < 0.6 ? PAL.yellow : PAL.green; fill.material.color.set(c);
    const blink = lv < 0.25 ? (Math.sin(t * 14) > 0 ? 0.35 : 0) : 0.1; fill.material.emissive.set(c).multiplyScalar(blink);
    if (bolt) bolt.scale.setScalar(1 + Math.sin(t * 8) * 0.08);
    lab.update(t);
  } };
};

SCENES.coffee = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, rand } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -0.6);
  const n = params.count || 3, cups = [];
  for (let i = 0; i < n; i++) {
    const g = new THREE.Group();
    const pts = []; for (let k = 0; k <= 10; k++) { const u = k / 10; pts.push(new THREE.Vector2(0.55 + u * 0.18, u * 1.2)); }
    const cup = new THREE.Mesh(new THREE.LatheGeometry(pts, 48), mat(i === n - 1 ? PAL.yellow : 0xffffff, { side: THREE.DoubleSide }));
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.06, 48), cup.material); base.position.y = 0.03;
    const coffee = new THREE.Mesh(new THREE.CylinderGeometry(0.68, 0.68, 0.04, 48), mat(0x4a2a17, { roughness: 0.2 })); coffee.position.y = 1.05;
    const handle = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.07, 12, 32), cup.material); handle.position.set(0.75, 0.6, 0); handle.rotation.z = -0.2;
    const plate = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.9, 0.08, 48), mat(0xffffff)); plate.position.y = -0.02;
    [cup, base, handle, plate].forEach((m) => m.castShadow = true);
    g.add(cup, base, coffee, handle, plate); g.position.set((i - (n - 1) / 2) * 2.1, -0.55, 0); g.scale.setScalar(0.95);
    scene.add(g); cups.push(g);
  }
  const R = rand(9), steam = [];
  for (let i = 0; i < 18; i++) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.14, 12, 10), mat(0xffffff, { transparent: true, opacity: 0.7 })); p.userData = { c: i % n, o: R(), x: (R() - 0.5) * 0.4 }; scene.add(p); steam.push(p); }
  const lab = addLabel(ctx, params.label, 3.5, { size: 0.85, color: 'yellow', delay: 0.9 });
  return { update(t) {
    cups.forEach((c, i) => { const u = seg(t, i * 0.32, i * 0.32 + 0.45); c.position.y = -0.55 + (1 - easeOutBack(u, 1.5)) * 6; c.rotation.y = Math.sin(t + i) * 0.3; c.visible = u > 0; });
    steam.forEach((p) => { const c = cups[p.userData.c]; const u = (t * 0.7 + p.userData.o) % 1; p.position.set(c.position.x + p.userData.x + Math.sin(u * 6 + p.userData.o * 9) * 0.15, c.position.y + 1.3 + u * 1.4, 0); p.material.opacity = 0.6 * (1 - u) * (c.visible ? 1 : 0); p.scale.setScalar(0.6 + u); });
    lab.update(t);
  } };
};

SCENES.couple = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, easeInOut } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.0);
  const a = pawn(ctx, PAL.yellow), b = pawn(ctx, 0x6b8fb3); a.position.y = b.position.y = -1.0; scene.add(a, b);
  const hg = extrude(THREE, heartShape(THREE, 0.9), 0.35);
  const hm = mat(PAL.red); const hL = new THREE.Mesh(hg, hm), hR = new THREE.Mesh(hg, hm);
  // split heart into halves via clipping planes
  hL.material = hm.clone(); hR.material = hm.clone();
  hL.material.clippingPlanes = [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0)]; hR.material.clippingPlanes = [new THREE.Plane(new THREE.Vector3(1, 0, 0), 0)];
  const hgrp = new THREE.Group(); hgrp.add(hL, hR); hgrp.position.y = 3.2; scene.add(hgrp);
  let wall = null;
  if (params.wall) { wall = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.6, 2.2), mat(0xd8cbb8)); wall.castShadow = true; wall.position.y = -2.8; scene.add(wall); }
  const sep = params.sep ?? 1.8;
  const lab = addLabel(ctx, params.label, 4.1, { size: 0.6, color: 'ink', delay: 0.6 });
  return { update(t) {
    const app = easeOutBack(seg(t, 0, 0.45));
    const d = 0.55 + sep * easeInOut(seg(t, 0.55, 1.3));
    a.position.x = -d; b.position.x = d; a.scale.setScalar(Math.max(0.001, app)); b.scale.setScalar(Math.max(0.001, app));
    a.rotation.y = 0.5 * seg(t, 0.55, 1.2); b.rotation.y = -0.5 * seg(t, 0.55, 1.2);
    const br = seg(t, 0.6, 1.4);
    hgrp.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.1, 0.45), 2.5)));
    hL.position.set(-br * 0.6, -br * br * 1.5, 0); hL.rotation.z = br * 0.6; hR.position.set(br * 0.6, -br * br * 1.5, 0); hR.rotation.z = -br * 0.6;
    if (wall) { wall.position.y = -2.8 + 3.4 * easeOutBack(seg(t, 0.9, 1.4), 1.2); }
    lab.update(t);
  } };
};

SCENES.beds = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, easeInOut } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -0.9);
  const mk = (c) => { const g = new THREE.Group(); const fr = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.4, 2.6), mat(0x9b7652)); fr.position.y = 0.2; const mt = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.5, 0.35, 2.5, 3, 0.12), mat(0xffffff)); mt.position.y = 0.55; const du = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.56, 0.2, 1.7, 3, 0.08), mat(c)); du.position.set(0, 0.78, 0.42); const pl = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.1, 0.25, 0.55, 3, 0.12), mat(0xf4ece0)); pl.position.set(0, 0.85, -0.85); const hb = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.2, 0.15), mat(0x9b7652)); hb.position.set(0, 0.6, -1.3); [fr, mt, du, pl, hb].forEach(m => m.castShadow = true); g.add(fr, mt, du, pl, hb); g.position.y = -0.9; g.rotation.x = 0.35; scene.add(g); return g; };
  const A = mk(PAL.yellow), B = mk(0x6b8fb3);
  let wall = new THREE.Mesh(new THREE.BoxGeometry(0.25, 3.0, 3.0), mat(0xd8cbb8)); wall.castShadow = true; scene.add(wall);
  const lab = addLabel(ctx, params.label, 3.6, { size: 0.65, color: 'ink', delay: 0.6 });
  return { update(t) {
    const app = easeOutBack(seg(t, 0, 0.45)); const d = 0.82 + 1.2 * easeInOut(seg(t, 0.4, 1.1));
    A.position.x = -d; B.position.x = d; A.scale.setScalar(Math.max(0.001, app)); B.scale.setScalar(Math.max(0.001, app));
    A.rotation.y = 0.2 + Math.sin(t) * 0.05; B.rotation.y = -0.2 - Math.sin(t) * 0.05;
    wall.position.y = -3.5 + 4.2 * easeOutBack(seg(t, 0.8, 1.3), 1.2) ;
    lab.update(t);
  } };
};

SCENES.checklist = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  const items = params.items || [{ t: 'VOCE', mark: 'x', at: 0.3 }];
  const rows = []; const n = items.length; const gapY = 1.35;
  items.forEach((it, i) => {
    const g = new THREE.Group(); g.position.y = 1.7 + (n - 1) * gapY / 2 - i * gapY;
    const pill = new THREE.Mesh(new RoundedBoxGeometry(6.2, 1.05, 0.35, 4, 0.3), mat(0xffffff)); pill.castShadow = true; g.add(pill);
    const isX = it.mark === 'x';
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.25, 40), mat(isX ? PAL.red : PAL.green)); disc.rotation.x = Math.PI / 2; disc.position.set(-2.5, 0, 0.25); g.add(disc);
    const mk = isX ? xMark(ctx, 0xffffff, 0.5) : checkMark(ctx, 0xffffff, 0.5); mk.position.set(-2.5, 0, 0.45); g.add(mk);
    const tx = new THREE.Mesh(text(it.t, { size: 0.42, depth: 0.12, font: 'xbold', bevel: 0.01, maxW: 4.4 }), [mat(PAL.ink), mat(PAL.ink)]);
    tx.geometry.computeBoundingBox(); const bw = tx.geometry.boundingBox.max.x - tx.geometry.boundingBox.min.x;
    tx.position.set(-2.0 + bw / 2, 0, 0.25); g.add(tx);
    let strike = null; if (isX && params.strike !== false) { strike = new THREE.Mesh(new THREE.BoxGeometry(1, 0.08, 0.05), mat(PAL.red)); strike.position.set(-2.0, 0, 0.4); g.add(strike); strike.userData.w = bw; }
    scene.add(g); rows.push({ g, mk, disc, strike, at: it.at ?? i * 0.4 });
  });
  return { update(t) {
    rows.forEach((r, i) => { const u = seg(t, r.at - 0.1, r.at + 0.3); r.g.scale.setScalar(Math.max(0.001, easeOutBack(u, 1.8))); r.g.rotation.x = (1 - u) * 0.8; r.g.rotation.y = Math.sin(t * 1.2 + i) * 0.06;
      const v = easeOutBack(seg(t, r.at + 0.2, r.at + 0.45), 3); r.mk.scale.setScalar(Math.max(0.001, v)); r.disc.scale.setScalar(Math.max(0.001, 0.6 + 0.4 * v));
      if (r.strike) { const w = r.strike.userData.w * ctx.H.easeOutCubic(seg(t, r.at + 0.3, r.at + 0.55)); r.strike.scale.x = Math.max(0.001, w); r.strike.position.x = -2.0 + w / 2; } });
  } };
};

// head profile with jaw / tongue / airway (side view, face to the right)
SCENES.jaw = (ctx) => {
  const { THREE, PAL, mat, seg, easeInOut, easeOutBack, text } = ctx.H; const { scene, params } = ctx;
  const mode = params.mode || 'back';
  const g = new THREE.Group(); g.position.set(-0.3, 1.5, 0); g.scale.setScalar(1.05); scene.add(g);
  // head silhouette
  const sh = new THREE.Shape();
  const P = [[-1.6, 3.2], [0.2, 3.5], [1.4, 2.9], [1.8, 1.9], [1.75, 1.2], [2.25, 0.5], [1.85, 0.25], [1.95, -0.05], [1.8, -0.25], [1.85, -0.55], [1.55, -0.9], [1.3, -1.25], [0.6, -1.35], [0.2, -1.3], [-0.2, -2.6], [-1.6, -2.6], [-1.75, -0.8], [-2.2, 0.6], [-2.1, 2.2]];
  sh.moveTo(...P[0]); P.slice(1).forEach(p => sh.lineTo(...p)); sh.closePath();
  const headPts = new THREE.Shape(sh.getSpacedPoints(160));
  const head = new THREE.Mesh(extrude(THREE, headPts, 0.4, 0.15), new THREE.MeshPhysicalMaterial({ color: 0xf2d3bf, roughness: 0.4, transparent: true, opacity: 0.45, depthWrite: false }));
  head.position.set(0, 0.45, -0.6); g.add(head);
  // upper jaw/teeth (fixed)
  const upper = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.4, 0.32, 0.6, 3, 0.12), mat(0xffffff)); upper.position.set(1.05, 0.12, 0); g.add(upper);
  // lower jaw group pivoting near ear
  const jawPiv = new THREE.Group(); jawPiv.position.set(-0.6, 0.6, 0); g.add(jawPiv);
  const jawShape = new THREE.Shape(); jawShape.moveTo(0, 0); jawShape.lineTo(0.25, 0); jawShape.lineTo(0.35, -1.15); jawShape.lineTo(2.25, -1.0); jawShape.lineTo(2.3, -0.68); jawShape.lineTo(0.7, -0.75); jawShape.lineTo(0.6, -0.1); jawShape.closePath();
  const jaw = new THREE.Mesh(extrude(THREE, jawShape, 0.5, 0.08), mat(0xfaf4ea)); jaw.position.set(1.0, -0.55, 0); jaw.castShadow = true; jawPiv.add(jaw);
  const lowTeeth = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.25, 0.28, 0.6, 3, 0.1), mat(0xffffff)); lowTeeth.position.set(1.55, -0.28, 0); jawPiv.add(lowTeeth);
  const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.75, 32, 24), mat(0xe8707a, { roughness: 0.45 })); tongue.scale.set(1.3, 0.55, 0.6); tongue.position.set(0.95, -0.45, 0); jawPiv.add(tongue);
  // airway behind the tongue: vertical tube whose radius = f(jaw position)
  const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(0.9, 1.7, 0), new THREE.Vector3(0.05, 1.2, 0), new THREE.Vector3(-0.45, 0.2, 0), new THREE.Vector3(-0.5, -1.0, 0), new THREE.Vector3(-0.55, -2.5, 0)]);
  const TS = 80, RS = 24, R0 = 0.32; const ageo = new THREE.TubeGeometry(curve, TS, R0, RS, false); const orig = ageo.attributes.position.array.slice();
  const cs = []; for (let i = 0; i <= TS; i++) cs.push(curve.getPointAt(i / TS));
  const amat = new THREE.MeshPhysicalMaterial({ color: 0x7cc4ff, roughness: 0.2, transparent: true, opacity: 0.8, emissive: new THREE.Color(0x1d5f99), emissiveIntensity: 0.3 });
  const air = new THREE.Mesh(ageo, amat); air.position.z = -0.05; g.add(air);
  // bite on teeth (forward/openclose modes)
  let bite = null; if (mode === 'forward' || mode === 'openclose') { bite = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(1.5, 0.75, 0.75, 3, 0.2), new THREE.MeshPhysicalMaterial({ color: 0x9fd4ff, transmission: 0.6, thickness: 0.4, roughness: 0.1, transparent: true, opacity: 0.85 })); bite.position.set(1.2, -0.08, 0); g.add(bite); }
  // arrow
  const arrow = new THREE.Group(); const ac = mode === 'back' ? PAL.red : PAL.green; const shaft = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.2, 0.2), mat(ac)); const tip = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.5, 24), mat(ac)); tip.rotation.z = -Math.PI / 2; tip.position.x = 0.65; arrow.add(shaft, tip); arrow.position.set(1.6, -1.7, 0.4); if (mode === 'back') arrow.rotation.z = Math.PI; g.add(arrow);
  if (mode === 'nose' || mode === 'openclose') arrow.visible = false;
  // nose markers
  let noseM = null, throatM = null;
  if (mode === 'nose') { noseM = checkMark(ctx, PAL.green, 0.5); noseM.position.set(2.7, 0.7, 0.4); g.add(noseM); throatM = xMark(ctx, PAL.red, 0.6); throatM.position.set(-1.35, -0.3, 0.6); g.add(throatM); }
  const lab = addLabel(ctx, params.label, -1.55, { size: 0.55, color: params.labelColor || 'ink', delay: 0.4 });
  const squeeze = (u, k) => 1 - k * Math.exp(-Math.pow((u - 0.45) / 0.14, 2));
  return { update(t) {
    g.scale.setScalar(1.05 * Math.max(0.001, easeOutBack(seg(t, 0, 0.45), 1.5)));
    g.rotation.y = Math.sin(t * 0.7) * 0.15;
    let back = 0, open = 0;
    if (mode === 'back') back = easeInOut(seg(t, 0.5, 1.8));
    if (mode === 'forward') back = 1 - easeInOut(seg(t, 0.4, 1.4));
    if (mode === 'nose') back = 0.85;
    if (mode === 'openclose') open = Math.max(0, Math.sin((t - 0.3) * 3.2)) * (t > 0.3 ? 1 : 0);
    jawPiv.position.x = -0.6 - back * 0.45; jawPiv.rotation.z = -open * 0.35 + back * 0.08;
    tongue.position.x = 0.95 - back * 0.25; tongue.scale.y = 0.55 + back * 0.1;
    if (bite) { bite.position.x = 1.2 - back * 0.45; bite.rotation.z = -open * 0.15; bite.position.y = -0.08 - open * 0.25; }
    const k = 0.85 * back; const p = ageo.attributes.position.array;
    for (let i = 0; i <= TS; i++) { const f = squeeze(i / TS, k), c = cs[i]; for (let j = 0; j <= RS; j++) { const id = (i * (RS + 1) + j) * 3; p[id] = c.x + (orig[id] - c.x) * f; p[id + 1] = c.y + (orig[id + 1] - c.y) * f; p[id + 2] = c.z + (orig[id + 2] - c.z) * f; } }
    ageo.attributes.position.needsUpdate = true; ageo.computeVertexNormals();
    amat.color.set(back > 0.5 ? 0xff6b6b : 0x7cc4ff); amat.emissive.set(back > 0.5 ? 0x991d1d : 0x1d5f99);
    arrow.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.4, 0.7), 2))); arrow.position.x = 1.6 + Math.sin(t * 6) * 0.08;
    if (noseM) { noseM.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.3, 0.6), 3))); throatM.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 1.4, 1.7), 3))); }
    lab.update(t);
  } };
};

SCENES.bite = (ctx) => {
  const { THREE, PAL, seg, easeOutBack, easeInOut } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -0.9);
  const mode = params.mode || 'spin';
  const b = biteMesh(ctx, params.color || 0x9fd4ff); b.position.y = 1.6; b.scale.setScalar(1.25); scene.add(b);
  const arrows = [];
  if (mode === 'flex') [-1, 1].forEach((s) => { const a = new THREE.Group(); const sh = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.16, 0.16), ctx.H.mat(PAL.yellow)); const tp = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.45, 24), ctx.H.mat(PAL.yellow)); tp.rotation.z = -Math.PI / 2; tp.position.x = 0.5; a.add(sh, tp); a.position.set(s * 2.75, 1.6, 0.5); a.rotation.z = s > 0 ? 0 : Math.PI; scene.add(a); arrows.push(a); });
  let sparkles = [];
  for (let i = 0; i < 8; i++) { const s = new THREE.Mesh(new THREE.OctahedronGeometry(0.12, 0), ctx.H.mat(0xffffff, { emissive: new THREE.Color(0xffffff), emissiveIntensity: 0.6 })); const a = i / 8 * Math.PI * 2; s.position.set(Math.cos(a) * 2.6, 1.6 + Math.sin(a) * 1.7, 0); scene.add(s); sparkles.push(s); }
  const lab = addLabel(ctx, params.label, -0.55, { size: params.labelSize || 0.58, color: params.labelColor || 'ink', delay: 0.45 });
  return { update(t) {
    const app = easeOutBack(seg(t, 0, 0.55), 1.6);
    b.scale.setScalar(1.25 * Math.max(0.001, app));
    if (mode === 'spin') { b.rotation.set(0.5 + Math.sin(t * 0.8) * 0.15, t * 1.4 - 0.5, 0); }
    else { b.rotation.set(0.85, Math.sin(t * 0.7) * 0.25, 0); }
    if (mode === 'flex') { const f = 1 + Math.sin((t - 0.4) * 5) * 0.12 * seg(t, 0.4, 0.7); b.scale.x = 1.25 * app * f; arrows.forEach((a, i) => { a.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.4, 0.7), 2))); a.position.x = (i ? 1 : -1) * (2.75 + (f - 1) * 6); }); }
    if (mode === 'squish') { const s = 1 - 0.35 * Math.max(0, Math.sin((t - 0.5) * 4)) * (t > 0.5 ? 1 : 0); b.scale.y = 1.25 * app * s; b.scale.x = 1.25 * app * (1 + (1 - s) * 0.4); }
    if (mode === 'open') { const o = Math.max(0, Math.sin((t - 0.4) * 3)) * (t > 0.4 ? 1 : 0); b.userData.up.position.y = 0.26 + o * 0.5; b.userData.up.rotation.x = -o * 0.35; }
    sparkles.forEach((s, i) => { s.rotation.y = t * 3; s.scale.setScalar(Math.max(0.001, Math.sin(t * 4 + i) * 0.5 + 0.5) * seg(t, 0.3, 0.6)); });
    lab.update(t);
  } };
};

SCENES.pot = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, rand } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.0);
  const g = new THREE.Group(); g.position.y = -0.2; scene.add(g);
  const pts = []; for (let i = 0; i <= 12; i++) pts.push(new THREE.Vector2(1.9 + (i === 0 ? -1.9 : 0), i * 0.17));
  const pot = new THREE.Mesh(new THREE.LatheGeometry([new THREE.Vector2(0, 0), new THREE.Vector2(1.9, 0), new THREE.Vector2(1.95, 2.0), new THREE.Vector2(2.05, 2.05)], 64), new THREE.MeshPhysicalMaterial({ color: 0xc0c4c8, metalness: 1, roughness: 0.25, side: THREE.DoubleSide })); pot.castShadow = true; g.add(pot);
  [-1, 1].forEach(s => { const h = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.08, 12, 24, Math.PI), mat(PAL.ink)); h.position.set(s * 2.15, 1.75, 0); h.rotation.z = -s * Math.PI / 2; g.add(h); });
  const water = new THREE.Mesh(new THREE.CylinderGeometry(1.88, 1.88, 0.05, 64), new THREE.MeshPhysicalMaterial({ color: 0x8fd0ff, roughness: 0.05, transmission: 0.3, transparent: true, opacity: 0.9 })); water.position.y = 1.7; g.add(water);
  const R = rand(4), bub = [];
  for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.08 + R() * 0.12, 12, 10), mat(0xffffff, { transparent: true, opacity: 0.9 })); const a = R() * 6.28, r = R() * 1.6; m.userData = { x: Math.cos(a) * r, z: Math.sin(a) * r, o: R() }; g.add(m); bub.push(m); }
  const steam = []; for (let i = 0; i < 14; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.3, 14, 10), mat(0xffffff, { transparent: true, opacity: 0.6 })); m.userData = { x: (R() - 0.5) * 2.5, o: R() }; g.add(m); steam.push(m); }
  const b = biteMesh(ctx); b.scale.setScalar(0.55); g.add(b);
  const lab = addLabel(ctx, params.label, 4.1, { size: 0.62, color: params.labelColor || 'red', delay: 0.5 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45))));
    g.rotation.x = 0.45; g.rotation.y = Math.sin(t * 0.6) * 0.2;
    bub.forEach((m) => { const u = (t * 1.6 + m.userData.o) % 1; m.position.set(m.userData.x, 1.72 + Math.sin(u * Math.PI) * 0.12, m.userData.z); m.scale.setScalar(Math.max(0.001, Math.sin(u * Math.PI))); });
    steam.forEach((m) => { const u = (t * 0.5 + m.userData.o) % 1; m.position.set(m.userData.x + Math.sin(u * 5) * 0.2, 2.0 + u * 2.5, 0); m.material.opacity = 0.5 * (1 - u); m.scale.setScalar(0.6 + u * 1.2); });
    const d = seg(t, 0.5, 1.1); b.position.set(0, 4.5 - d * 2.7, 0); b.rotation.set(t * 2, t, 0.3);
    lab.update(t);
  } };
};

SCENES.drawer = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, easeInOut } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 0.3; scene.add(g);
  const wood = mat(0xb88a5c, { clearcoat: 0.2, roughness: 0.55 });
  const cab = new THREE.Group(); const parts = [[4.2, 0.15, 3, 0, 1.5, 0], [4.2, 0.15, 3, 0, -1.5, 0], [0.15, 3.15, 3, 2.05, 0, 0], [0.15, 3.15, 3, -2.05, 0, 0], [4.2, 3.15, 0.15, 0, 0, -1.45], [4.2, 0.12, 3, 0, 0.02, 0]];
  parts.forEach(([a, b, c, x, y, z]) => { const p = new THREE.Mesh(new THREE.BoxGeometry(a, b, c), wood); p.position.set(x, y, z); p.castShadow = true; cab.add(p); }); g.add(cab);
  const dr = new THREE.Group(); const dm = mat(0xc99a6a, { clearcoat: 0.3 });
  [[3.9, 0.1, 2.8, 0, -0.65, 0], [0.1, 1.3, 2.8, 1.9, 0, 0], [0.1, 1.3, 2.8, -1.9, 0, 0], [3.9, 1.3, 0.1, 0, 0, -1.35]].forEach(([a, b, c, x, y, z]) => { const p = new THREE.Mesh(new THREE.BoxGeometry(a, b, c), dm); p.position.set(x, y, z); dr.add(p); });
  const front = new THREE.Mesh(new ctx.H.RoundedBoxGeometry(4.0, 1.45, 0.18, 3, 0.06), dm); front.position.z = 1.45; front.castShadow = true; dr.add(front);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 12), mat(PAL.ink)); knob.position.set(0, 0, 1.62); dr.add(knob);
  dr.position.y = 0.75; g.add(dr);
  const b = biteMesh(ctx); b.scale.setScalar(0.5); b.position.set(0, -0.38, 0.2); dr.add(b);
  const lab = addLabel(ctx, params.label, 3.3, { size: 0.65, color: params.labelColor || 'ink', delay: 0.3 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45))));
    g.rotation.set(0.38, -0.45 + Math.sin(t * 0.6) * 0.1, 0);
    const open = seg(t, 0, 0.35) - easeInOut(seg(t, 0.9, 1.5)); dr.position.z = 2.2 * Math.max(0, Math.min(1, open < 1 ? (t < 0.9 ? 1 : 1 - easeInOut(seg(t, 0.9, 1.5))) : 1));
    lab.update(t);
  } };
};

SCENES.zzz = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, rand } = ctx.H; const { scene, params } = ctx;
  scene.background = ctx.H.gradientTexture('#1f2a44', '#0f1526');
  const moonS = new THREE.Shape(); moonS.absarc(0, 0, 1.5, 0.982, Math.PI * 2 - 0.982, false); moonS.absarc(0.75, 0, 1.25, Math.PI * 2 - 1.504, 1.504, true);
  const moon = new THREE.Mesh(extrude(THREE, moonS, 0.5, 0.12), mat(PAL.yellow, { emissive: new THREE.Color(0xffd200), emissiveIntensity: 0.25 })); moon.position.set(-0.6, 2.1, 0); scene.add(moon);
  const zs = [0, 1, 2].map((i) => { const z = new THREE.Mesh(text('Z', { size: 0.5 + i * 0.25, depth: 0.25 }), [mat(0xffffff), mat(0xc9d4ff)]); scene.add(z); return z; });
  const R = rand(11), stars = [];
  for (let i = 0; i < 30; i++) { const s = new THREE.Mesh(new THREE.OctahedronGeometry(0.06 + R() * 0.06, 0), new THREE.MeshBasicMaterial({ color: 0xffffff })); s.position.set((R() - 0.5) * 7, -1 + R() * 6.5, -2 - R() * 2); s.userData.o = R() * 6; scene.add(s); stars.push(s); }
  const lab = addLabel(ctx, params.label, -0.7, { size: 0.7, color: params.labelColor || 'yellow', delay: 0.4 });
  return { update(t) {
    moon.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 1.8))); moon.rotation.set(0, Math.sin(t * 0.8) * 0.3, -0.3 + Math.sin(t) * 0.05);
    zs.forEach((z, i) => { const u = ((t * 0.55) + i / 3) % 1; z.position.set(1.0 + u * 1.4 + i * 0.1, 2.0 + u * 2.4, 0.5); z.rotation.z = 0.3 - u * 0.3; z.scale.setScalar(Math.max(0.001, Math.sin(u * Math.PI) * 1.2 * seg(t, 0.2, 0.5))); });
    stars.forEach((s) => { s.scale.setScalar(0.5 + 0.5 * Math.sin(t * 3 + s.userData.o)); });
    lab.update(t);
  } };
};

SCENES.box = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, easeInOut, rand } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const mode = params.mode || 'open';
  if (mode === 'pile') {
    const R = rand(13), boxes = [];
    for (let i = 0; i < 9; i++) { const b = cardboardBox(ctx, [0xc9a26b, 0xd8b47e, 0xb88f5a][i % 3], 1.2 + R() * 0.6, 0.8 + R() * 0.5, 1.2 + R() * 0.5); b.userData.flaps.forEach(f => f.rotation.x = 0); const col = i % 3, row = Math.floor(i / 3); b.userData.tx = (col - 1) * 1.9 + (R() - 0.5) * 0.3; b.userData.ty = -0.75 + row * 1.15; b.userData.r = (R() - 0.5) * 0.4; b.userData.d = i * 0.1; scene.add(b); boxes.push(b); }
    const lab = addLabel(ctx, params.label, 4.3, { size: 0.6, color: 'ink', delay: 0.8 });
    return { update(t) { boxes.forEach((b) => { const u = seg(t, b.userData.d, b.userData.d + 0.4); b.position.set(b.userData.tx, b.userData.ty + (1 - easeOutBack(u, 1.3)) * 7, 0); b.rotation.y = b.userData.r + Math.sin(t) * 0.05; b.visible = u > 0; }); lab.update(t); } };
  }
  const box = cardboardBox(ctx); box.position.y = 0; scene.add(box);
  const item = params.item === 'coin' ? new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 0.15, 48), new THREE.MeshPhysicalMaterial({ color: 0xf2c14e, metalness: 1, roughness: 0.2 })) : biteMesh(ctx);
  if (params.item === 'coin') item.rotation.x = Math.PI / 2; else item.scale.setScalar(0.6);
  scene.add(item);
  let ring = null;
  if (mode === 'return') { ring = new THREE.Group(); const tor = new THREE.Mesh(new THREE.TorusGeometry(2.3, 0.14, 16, 80, Math.PI * 1.6), mat(PAL.green)); const tip = new THREE.Mesh(new THREE.ConeGeometry(0.35, 0.6, 24), mat(PAL.green)); tip.position.set(2.3, 0, 0); tip.rotation.z = Math.PI; ring.add(tor, tip); ring.position.set(0, 0.8, -0.6); scene.add(ring); }
  const lab = addLabel(ctx, params.label, mode === 'return' ? 4.2 : 4.3, { size: 0.62, color: params.labelColor || 'ink', delay: 0.6 });
  return { update(t) {
    box.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45)))); box.rotation.set(0.35, -0.5 + Math.sin(t * 0.7) * 0.15, 0);
    if (mode === 'open') { const o = easeOutBack(seg(t, 0.35, 0.75)); box.userData.flaps.forEach((f) => f.rotation.x = -o * 2.1); box.userData.tape.visible = t < 0.35;
      const u = easeOutBack(seg(t, 0.6, 1.1), 1.4); item.position.set(0, 0.2 + u * 2.4, 0); item.rotation.set(0.5, t * 2, 0); item.visible = t > 0.55; }
    else { // return: item drops in, flaps close, arrow spins
      const d = seg(t, 0.2, 0.6); item.position.set(0, 3.6 - d * 3.4, 0); item.rotation.set(t, t * 2, 0); item.visible = d < 1;
      const c = easeInOut(seg(t, 0.6, 0.95)); box.userData.flaps.forEach((f) => f.rotation.x = -2.1 * (1 - c));
      ring.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.9, 1.25)))); ring.rotation.z = -t * 2.2; }
    lab.update(t);
  } };
};

SCENES.badge = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 2.0; scene.add(g);
  // scalloped medal
  const sh = new THREE.Shape(); const N = 48; for (let i = 0; i <= N; i++) { const a = i / N * Math.PI * 2; const r = 1.9 + (i % 2 ? 0.12 : 0); const x = Math.cos(a) * r, y = Math.sin(a) * r; i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
  const medal = new THREE.Mesh(extrude(THREE, sh, 0.35, 0.08), mat(params.color === 'green' ? PAL.green : PAL.yellow, { roughness: 0.25 })); medal.castShadow = true; g.add(medal);
  const inner = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 0.5, 64), mat(0xffffff)); inner.rotation.x = Math.PI / 2; g.add(inner);
  let icon;
  if (params.icon === 'check') { icon = checkMark(ctx, PAL.green, 1.2); }
  else if (params.icon === 'text') { icon = new THREE.Mesh(text(params.iconText || '60', { size: 1.0, depth: 0.3, maxW: 2.4 }), [mat(PAL.ink), mat(0x4a4440)]); }
  else { icon = new THREE.Group(); const m = mat(PAL.red); const a = new THREE.Mesh(new THREE.BoxGeometry(0.55, 1.8, 0.4), m), b = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.55, 0.4), m); icon.add(a, b); }
  icon.position.z = 0.4; g.add(icon);
  // ribbons
  [-1, 1].forEach((s) => { const r = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.8, 0.1), mat(params.ribbon === 'blue' ? PAL.blue : PAL.red)); r.position.set(s * 0.7, -2.2, -0.3); r.rotation.z = s * 0.35; r.castShadow = true; g.add(r); });
  const lab = addLabel(ctx, params.label, -0.95, { size: params.labelSize || 0.56, color: params.labelColor || 'ink', delay: 0.4 });
  return { update(t) { g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2))); g.rotation.y = (1 - ctx.H.easeOutCubic(seg(t, 0, 0.8))) * Math.PI * 2 + Math.sin(t * 1.2) * 0.2; icon.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.3, 0.6), 3))); lab.update(t); } };
};

SCENES.people = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack } = ctx.H; const { scene, params } = ctx;
  const rows = 4, cols = 7, ps = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { const p = pawn(ctx, (r + c) % 5 === 0 ? PAL.yellow : 0xffffff); p.scale.setScalar(0.42); p.position.set((c - (cols - 1) / 2) * 0.88, -0.9 + r * 0.05, -r * 1.1); p.userData.d = 0.05 * (r * cols + c) * 0.5; scene.add(p); ps.push(p); }
  ground(ctx, -0.9);
  const target = params.number || 50000; const fmt = (n) => n.toLocaleString('it-IT');
  let numMesh = null, lastStr = '';
  const numMat = [mat(PAL.yellow, { roughness: 0.25 }), mat(0x2a2622)];
  const lab = addLabel(ctx, params.label, 2.75, { size: 0.55, color: 'ink', delay: 0.6, z: 0 });
  return { update(t) {
    ps.forEach((p) => { const u = seg(t, p.userData.d, p.userData.d + 0.35); p.scale.setScalar(Math.max(0.001, 0.42 * easeOutBack(u, 2))); p.position.y = -0.9 + Math.abs(Math.sin(t * 6 + p.userData.d * 30)) * 0.05; });
    const u = ctx.H.easeOutCubic(seg(t, 0.15, 1.2)); const n = Math.round(target * u / (target >= 1000 ? 1000 : 1)) * (target >= 1000 ? 1000 : 1); const str = fmt(n) + (params.suffix || '');
    if (str !== lastStr) { if (numMesh) { scene.remove(numMesh); numMesh.geometry.dispose(); } numMesh = new THREE.Mesh(text(str, { size: 1.15, depth: 0.55, bevel: 0.05 }), numMat); numMesh.position.set(0, 4.1, 0.3); numMesh.castShadow = true; scene.add(numMesh); lastStr = str; }
    numMesh.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.4), 2))); numMesh.rotation.y = Math.sin(t * 1.2) * 0.12;
    lab.update(t);
  } };
};

SCENES.shield = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 1.9; scene.add(g);
  const sh = new THREE.Shape(); sh.moveTo(0, 2.1); sh.bezierCurveTo(0.9, 1.7, 1.6, 1.75, 1.9, 1.7); sh.bezierCurveTo(1.95, 0.2, 1.4, -1.3, 0, -2.2); sh.bezierCurveTo(-1.4, -1.3, -1.95, 0.2, -1.9, 1.7); sh.bezierCurveTo(-1.6, 1.75, -0.9, 1.7, 0, 2.1);
  const outer = new THREE.Mesh(extrude(THREE, sh, 0.5, 0.12), mat(PAL.yellow, { roughness: 0.22 })); outer.castShadow = true; g.add(outer);
  const innerG = extrude(THREE, sh, 0.5, 0.05); const inner = new THREE.Mesh(innerG, mat(0xffffff)); inner.scale.set(0.82, 0.82, 1); inner.position.z = 0.12; g.add(inner);
  const big = new THREE.Mesh(text(params.big || '60', { size: 1.25, depth: 0.35, maxW: 2.6 }), [mat(PAL.ink), mat(0x4a4440)]); big.position.set(0, 0.45, 0.55); g.add(big);
  const small = new THREE.Mesh(text(params.small || 'GIORNI', { size: 0.42, depth: 0.15, font: 'xbold', maxW: 2.4 }), [mat(PAL.ink), mat(PAL.ink)]); small.position.set(0, -0.65, 0.55); g.add(small);
  const ck = checkMark(ctx, PAL.green, 0.8); ck.position.set(1.7, 1.7, 0.7); g.add(ck);
  const lab = addLabel(ctx, params.label, -1.0, { size: params.labelSize || 0.52, color: params.labelColor || 'ink', delay: 0.5 });
  return { update(t) { g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2))); g.rotation.y = (1 - ctx.H.easeOutCubic(seg(t, 0, 0.7))) * -Math.PI + Math.sin(t * 1.1) * 0.18; ck.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.55, 0.85), 3))); lab.update(t); } };
};

SCENES.gears = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const gear = (r, teeth) => { const sh = new THREE.Shape(); const N = teeth * 4; for (let i = 0; i <= N; i++) { const a = i / N * Math.PI * 2; const rr = (i % 4 < 2) ? r + 0.28 : r; const x = Math.cos(a) * rr, y = Math.sin(a) * rr; i ? sh.lineTo(x, y) : sh.moveTo(x, y); } const h = new THREE.Path(); h.absarc(0, 0, r * 0.35, 0, Math.PI * 2, true); sh.holes.push(h); return extrude(THREE, sh, 0.45, 0.05); };
  const g1 = new THREE.Mesh(gear(1.35, 12), mat(PAL.yellow)), g2 = new THREE.Mesh(gear(0.9, 8), mat(PAL.ink)), g3 = new THREE.Mesh(gear(0.7, 6), mat(0xffffff));
  g1.position.set(-0.75, 2.1, 0); g2.position.set(1.48, 2.85, 0); g3.position.set(1.2, 0.75, 0); [g1, g2, g3].forEach(m => { m.castShadow = true; scene.add(m); });
  const lab = addLabel(ctx, params.label, -0.6, { size: 0.6, color: params.labelColor || 'ink', delay: 0.4 });
  return { update(t) { const s = Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2)); [g1, g2, g3].forEach(m => m.scale.setScalar(s)); g1.rotation.z = t * 1.2; g2.rotation.z = -t * 1.2 * 12 / 8 + 0.2; g3.rotation.z = -t * 1.2 * 12 / 6; scene.rotation.y = Math.sin(t * 0.7) * 0.2; lab.update(t); } };
};

SCENES.card = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, easeInOut, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const card = new THREE.Group(); const body = new THREE.Mesh(new RoundedBoxGeometry(3.4, 2.15, 0.08, 3, 0.03), mat(0x1f3b63, { roughness: 0.3 })); body.castShadow = true; card.add(body);
  const chip = new THREE.Mesh(new RoundedBoxGeometry(0.55, 0.42, 0.04, 2, 0.02), new THREE.MeshPhysicalMaterial({ color: 0xe8c45a, metalness: 1, roughness: 0.25 })); chip.position.set(-1.05, 0.25, 0.05); card.add(chip);
  const stripe = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.14, 0.02), mat(PAL.yellow)); stripe.position.set(0, -0.6, 0.05); card.add(stripe);
  card.position.set(0, 2.9, 0); scene.add(card);
  const b = biteMesh(ctx); b.scale.setScalar(0.85); b.position.set(0, 0.6, 0); scene.add(b);
  const lab = addLabel(ctx, params.label, -0.75, { size: 0.55, color: params.labelColor || 'ink', delay: 0.5 });
  return { update(t) {
    const s = Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2)); card.scale.setScalar(s); b.scale.setScalar(0.85 * s);
    const r = easeInOut(seg(t, 0.4, 1.2)); card.rotation.set(-0.15, Math.sin(t * 0.9) * 0.25 + r * 0.9, 0); b.rotation.set(0.35 + r * 1.0, -0.4 + t * 0.6, 0);
    lab.update(t);
  } };
};

SCENES.glass = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.0);
  const gl = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.7, 2.4, 48, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transmission: 0.95, roughness: 0.03, thickness: 0.2, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
  const wat = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.68, 1.6, 48), new THREE.MeshPhysicalMaterial({ color: 0x6fc3ff, transmission: 0.5, roughness: 0.05, transparent: true, opacity: 0.85 }));
  const glass = new THREE.Group(); glass.add(gl, wat); wat.position.y = -0.38; glass.position.set(-1.5, 0.2, 0); scene.add(glass);
  const bubble = new THREE.Group(); const bb = new THREE.Mesh(new RoundedBoxGeometry(2.6, 1.6, 0.4, 4, 0.5), mat(0xffffff)); bb.castShadow = true; const tail = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.7, 3), mat(0xffffff)); tail.position.set(-0.8, -0.95, 0); tail.rotation.z = 0.5; bubble.add(bb, tail);
  const dots = [0, 1, 2].map(i => { const d = new THREE.Mesh(new THREE.SphereGeometry(0.18, 20, 16), mat(PAL.ink)); d.position.set(-0.6 + i * 0.6, 0, 0.3); bubble.add(d); return d; });
  bubble.position.set(1.2, 2.9, 0); scene.add(bubble);
  const lab = addLabel(ctx, params.label, -0.6, { size: 0.58, color: params.labelColor || 'ink', delay: 0.5 });
  return { update(t) {
    glass.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45), 2))); glass.rotation.z = Math.sin(t * 2) * 0.05;
    bubble.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.25, 0.65), 2.5))); bubble.rotation.y = Math.sin(t * 1.2) * 0.2;
    dots.forEach((d, i) => d.position.y = Math.max(0, Math.sin(t * 7 - i * 0.8)) * 0.18);
    wat.scale.y = 1 - 0.1 * Math.sin(t * 2); lab.update(t);
  } };
};

SCENES.tag = (ctx) => {
  const { THREE, PAL, mat, text, seg, easeOutBack, rand } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.3);
  const g = new THREE.Group(); g.position.y = 1.8; scene.add(g);
  const sh = new THREE.Shape(); sh.moveTo(-2.2, 1.2); sh.lineTo(1.4, 1.2); sh.lineTo(2.4, 0); sh.lineTo(1.4, -1.2); sh.lineTo(-2.2, -1.2); sh.closePath(); const h = new THREE.Path(); h.absarc(1.55, 0, 0.22, 0, Math.PI * 2, true); sh.holes.push(h);
  const tag = new THREE.Mesh(extrude(THREE, sh, 0.3, 0.1), mat(params.color === 'red' ? PAL.red : PAL.yellow, { roughness: 0.25 })); tag.castShadow = true; g.add(tag);
  const tx = new THREE.Mesh(text(params.text || '-53%', { size: 1.0, depth: 0.25, maxW: 3.2 }), [mat(params.color === 'red' ? 0xffffff : PAL.ink), mat(0x4a4440)]); tx.position.set(-0.45, 0, 0.35); g.add(tx);
  const R = rand(21), conf = [];
  for (let i = 0; i < 26; i++) { const c = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.24, 0.02), mat([PAL.yellow, PAL.red, PAL.green, PAL.blue, 0xffffff][i % 5])); c.userData = { x: (R() - 0.5) * 7, o: R() * 0.6, r: R() * 6, s: 1 + R() * 2 }; scene.add(c); conf.push(c); }
  const lab = addLabel(ctx, params.label, -0.85, { size: 0.56, color: params.labelColor || 'ink', delay: 0.5 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5), 2.2))); g.rotation.set(0, (1 - ctx.H.easeOutCubic(seg(t, 0, 0.8))) * Math.PI * 2 + Math.sin(t * 1.4) * 0.2, Math.sin(t * 2) * 0.06);
    conf.forEach((c) => { const tt = t - c.userData.o; c.position.set(c.userData.x + Math.sin(tt * 3 + c.userData.r) * 0.3, 6 - tt * 3.2, -0.5); c.rotation.set(tt * c.userData.s * 3, tt * 2, c.userData.r); c.visible = tt > 0; });
    lab.update(t);
  } };
};

SCENES.gift = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = -0.2; scene.add(g);
  const boxM = mat(PAL.red), rib = mat(PAL.yellow);
  const base = new THREE.Mesh(new RoundedBoxGeometry(2.4, 1.8, 2.4, 3, 0.08), boxM); base.castShadow = true; g.add(base);
  const r1 = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.82, 2.42), rib), r2 = new THREE.Mesh(new THREE.BoxGeometry(2.42, 1.82, 0.4), rib); g.add(r1, r2);
  const lid = new THREE.Group(); const lb = new THREE.Mesh(new RoundedBoxGeometry(2.65, 0.45, 2.65, 3, 0.08), boxM); lb.castShadow = true; const l1 = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.47, 2.67), rib), l2 = new THREE.Mesh(new THREE.BoxGeometry(2.67, 0.47, 0.42), rib);
  const bow1 = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.12, 12, 32), rib); bow1.position.set(-0.3, 0.45, 0); bow1.rotation.y = 0.4; const bow2 = bow1.clone(); bow2.position.x = 0.3; bow2.rotation.y = -0.4; lid.add(lb, l1, l2, bow1, bow2); lid.position.y = 1.1; g.add(lid);
  // items: travel case + toothbrush
  const caseM = new THREE.Mesh(new THREE.CapsuleGeometry(0.55, 0.9, 8, 24), mat(0x2b2b2b)); caseM.rotation.z = Math.PI / 2; caseM.scale.set(1, 1, 0.6);
  const brush = new THREE.Group(); const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.8, 16), mat(0x9fd4ff)); const head = new THREE.Mesh(new RoundedBoxGeometry(0.22, 0.45, 0.2, 2, 0.06), mat(0xffffff)); head.position.y = 1.0; brush.add(handle, head);
  scene.add(caseM, brush);
  const lab = addLabel(ctx, params.label, 4.5, { size: 0.62, color: params.labelColor || 'ink', delay: 0.7 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45)))); g.rotation.set(0.25, -0.5 + Math.sin(t * 0.7) * 0.15, 0);
    const o = seg(t, 0.45, 0.8); lid.position.set(o * 1.8, 1.1 + o * 2.2 - o * o * 1.2, 0); lid.rotation.z = -o * 1.2;
    const u = easeOutBack(seg(t, 0.6, 1.0), 1.5); caseM.position.set(-1.0, 1.0 + u * 2.0, 0.6); caseM.rotation.y = t; caseM.visible = t > 0.6; brush.position.set(1.0, 1.0 + u * 2.0, 0.6); brush.rotation.set(0, t, -0.5); brush.visible = t > 0.6;
    lab.update(t);
  } };
};

SCENES.target = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 1.9; scene.add(g);
  [2.2, 1.7, 1.2, 0.7, 0.3].forEach((r, i) => { const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.3 + i * 0.04, 64), mat(i % 2 ? 0xffffff : PAL.red)); c.rotation.x = Math.PI / 2; c.position.z = i * 0.02; c.castShadow = true; g.add(c); });
  const dart = new THREE.Group(); const body = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 1.6, 16), mat(PAL.ink)); body.rotation.x = Math.PI / 2; const tip = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.35, 16), mat(0xcccccc)); tip.rotation.x = -Math.PI / 2; tip.position.z = -0.95; const fl = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.02, 0.5), mat(PAL.yellow)); fl.position.z = 0.7; const fl2 = fl.clone(); fl2.rotation.z = Math.PI / 2; dart.add(body, tip, fl, fl2); scene.add(dart);
  const lab = addLabel(ctx, params.label, -0.85, { size: 0.6, color: params.labelColor || 'ink', delay: 0.7 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45)))); g.rotation.y = Math.sin(t * 0.8) * 0.25 - 0.2;
    const u = seg(t, 0.35, 0.65); const hit = u >= 1; dart.position.set(3.5 * (1 - u), 1.9 + 2.5 * (1 - u), 1.2 + 6 * (1 - u)); dart.rotation.set(-0.25, 0.4, 0);
    if (hit) { const w = Math.exp(-(t - 0.65) * 6) * Math.sin((t - 0.65) * 40) * 0.08; dart.rotation.x = -0.25 + w; g.position.z = -w; }
    lab.update(t);
  } };
};

SCENES.button = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.2);
  const g = new THREE.Group(); g.position.y = 0.6; scene.add(g);
  const base = new THREE.Mesh(new RoundedBoxGeometry(4.6, 0.6, 2.4, 4, 0.28), mat(PAL.ink)); base.castShadow = true; g.add(base);
  const btn = new THREE.Mesh(new RoundedBoxGeometry(4.0, 0.7, 1.8, 5, 0.3), mat(PAL.yellow, { roughness: 0.25 })); btn.position.y = 0.55; btn.castShadow = true; g.add(btn);
  const tx = new THREE.Mesh(ctx.H.text(params.btn || 'SCOPRI DI PIÙ', { size: 0.36, depth: 0.08, font: 'xbold', maxW: 3.4 }), [mat(PAL.ink), mat(PAL.ink)]); tx.rotation.x = -Math.PI / 2; tx.position.y = 0.95; tx.visible = false;
  const arrow = new THREE.Group(); const sh = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.2, 0.4), mat(PAL.red)); const tp = new THREE.Mesh(new THREE.ConeGeometry(0.6, 0.8, 32), mat(PAL.red)); tp.rotation.z = Math.PI; tp.position.y = -0.9; arrow.add(sh, tp); arrow.position.set(0, 3.6, 0.5); scene.add(arrow);
  const lab = addLabel(ctx, params.label, 4.9, { size: 0.6, color: params.labelColor || 'ink', delay: 0.3, z: 0 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.45)))); g.rotation.set(0.55, Math.sin(t * 0.8) * 0.15, 0);
    const press = Math.max(0, Math.sin((t - 0.5) * 6)); btn.position.y = 0.55 - (t > 0.5 ? press * 0.3 : 0);
    arrow.position.y = 3.3 + (t > 0.5 ? -press * 0.5 : 0) + Math.sin(t * 3) * 0.05; arrow.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.2, 0.5), 2)));
    lab.update(t);
  } };
};

SCENES.bed = (ctx) => {
  const { THREE, PAL, mat, seg, easeOutBack, RoundedBoxGeometry } = ctx.H; const { scene, params } = ctx;
  ground(ctx, -1.0);
  const g = new THREE.Group(); g.position.y = -0.6; scene.add(g);
  const wood = mat(0x9b7652);
  const fr = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.5, 4.2), wood); fr.position.y = 0.25; const mt = new THREE.Mesh(new RoundedBoxGeometry(3.4, 0.45, 4.0, 3, 0.15), mat(0xffffff)); mt.position.y = 0.72;
  const du = new THREE.Mesh(new RoundedBoxGeometry(3.5, 0.3, 2.8, 3, 0.12), mat(PAL.yellow)); du.position.set(0, 1.0, 0.65); const hb = new THREE.Mesh(new RoundedBoxGeometry(3.6, 1.9, 0.25, 3, 0.1), wood); hb.position.set(0, 1.0, -2.05);
  const p1 = new THREE.Mesh(new RoundedBoxGeometry(1.4, 0.35, 0.8, 3, 0.15), mat(0xf4ece0)); p1.position.set(-0.85, 1.1, -1.4); const p2 = p1.clone(); p2.position.x = 0.85;
  [fr, mt, du, hb, p1, p2].forEach(m => { m.castShadow = true; g.add(m); });
  const heart = new THREE.Mesh(extrude(THREE, heartShape(THREE, 0.8), 0.35), mat(PAL.red)); heart.position.set(0, 3.4, 0); scene.add(heart);
  const lab = addLabel(ctx, params.label, 4.7, { size: 0.58, color: params.labelColor || 'ink', delay: 0.5, z: 0 });
  return { update(t) {
    g.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0, 0.5)))); g.rotation.set(0.45, -0.4 + Math.sin(t * 0.6) * 0.15, 0);
    heart.scale.setScalar(Math.max(0.001, easeOutBack(seg(t, 0.35, 0.7), 3)) * (1 + Math.max(0, Math.sin(t * 7)) * 0.08)); heart.rotation.y = Math.sin(t * 1.3) * 0.3;
    lab.update(t);
  } };
};

// ---- extend existing scenes with params

