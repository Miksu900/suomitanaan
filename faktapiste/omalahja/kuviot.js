// Omalahja – koristekuviot. Kaikki kuviot on piirretty itse canvas-poluilla (alkuperäisiä, ei lisensoituja kuvia).
// Jokainen kuvio piirretään origon ympärille laatikkoon, jonka sivu on s. Värit v = { a: korostus, i: muste, s: pehmeä, b: tausta }.
(function () {
  const PI = Math.PI;
  const rnd = (siemen) => () => ((siemen = (siemen * 16807) % 2147483647) - 1) / 2147483646;
  function sydan(c, x, y, w) {
    c.moveTo(x, y + w * 0.32);
    c.bezierCurveTo(x - w * 0.58, y - w * 0.04, x - w * 0.34, y - w * 0.52, x, y - w * 0.2);
    c.bezierCurveTo(x + w * 0.34, y - w * 0.52, x + w * 0.58, y - w * 0.04, x, y + w * 0.32);
  }
  function lehti(c, x, y, l, a, lev = 0.36) {
    c.save(); c.translate(x, y); c.rotate(a); c.beginPath(); c.moveTo(0, 0);
    c.quadraticCurveTo(l * 0.5, -l * lev, l, 0); c.quadraticCurveTo(l * 0.5, l * lev, 0, 0); c.fill(); c.restore();
  }
  function tahti(c, x, y, r, sakarat = 5, sisa = 0.45, kierto = -PI / 2) {
    c.beginPath();
    for (let k = 0; k < sakarat * 2; k++) { const rr = k % 2 ? r * sisa : r, a = kierto + (k * PI) / sakarat; c.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    c.closePath(); c.fill();
  }
  function kuu(c, x, y, r, d = 0.55) {
    const dd = r * d * 2, yy = Math.sqrt(Math.max(0, r * r - (dd * dd) / 4)), al = Math.atan2(yy, dd / 2);
    c.beginPath(); c.arc(x, y, r, al, -al + 2 * PI, false); c.arc(x + dd, y, r, -PI + al, PI - al, true); c.closePath(); c.fill();
  }
  function kuusi(c, x, y, h) {
    const w = h * 0.42; c.beginPath();
    for (let k = 0; k < 3; k++) { const yt = y - h + k * h * 0.26, yb = yt + h * 0.42, ww = w * (0.55 + k * 0.22);
      c.moveTo(x, yt); c.lineTo(x + ww, yb); c.lineTo(x - ww, yb); c.closePath(); }
    c.rect(x - h * 0.035, y - h * 0.12, h * 0.07, h * 0.12); c.fill();
  }
  function lintu(c, x, y, w) {
    c.beginPath(); c.moveTo(x - w / 2, y - w * 0.12); c.quadraticCurveTo(x - w * 0.22, y - w * 0.3, x, y);
    c.quadraticCurveTo(x + w * 0.22, y - w * 0.3, x + w / 2, y - w * 0.12); c.stroke();
  }
  function kukka(c, x, y, r, v1, v2) {
    c.fillStyle = v1; for (let k = 0; k < 5; k++) { const a = (k * 2 * PI) / 5; c.beginPath(); c.ellipse(x + Math.cos(a) * r * 0.55, y + Math.sin(a) * r * 0.55, r * 0.5, r * 0.32, a, 0, 2 * PI); c.fill(); }
    c.fillStyle = v2; c.beginPath(); c.arc(x, y, r * 0.28, 0, 2 * PI); c.fill();
  }
  function oksa(c, s, v, lehtia = 7, kaari = 0.25, oliivit = false) {
    // kaareva varsi vasemmalta alhaalta oikealle ylös; lehdet vuorotellen
    const p = (t) => [(-0.45 + 0.9 * t) * s, (0.3 - 0.6 * t) * s + Math.sin(t * PI) * kaari * s * -0.5];
    c.strokeStyle = v.a; c.lineWidth = s * 0.018; c.lineCap = "round"; c.beginPath();
    for (let t = 0; t <= 1.001; t += 0.05) { const [x, y] = p(t); t ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
    for (let k = 1; k <= lehtia; k++) {
      const t = k / (lehtia + 0.6), [x, y] = p(t), [x2, y2] = p(t + 0.01), a = Math.atan2(y2 - y, x2 - x), puoli = k % 2 ? -1 : 1;
      c.fillStyle = k % 3 === 0 ? v.i : v.a; lehti(c, x, y, s * (oliivit ? 0.2 : 0.17), a + puoli * 0.75, oliivit ? 0.22 : 0.38);
      if (oliivit && k % 2 === 0) { c.fillStyle = v.i; c.beginPath(); c.ellipse(x + Math.cos(a - puoli) * s * 0.05, y + Math.sin(a - puoli) * s * 0.05, s * 0.028, s * 0.04, a, 0, 2 * PI); c.fill(); }
    }
    const [xe, ye] = p(1); c.fillStyle = v.a; lehti(c, xe, ye, s * 0.14, -PI / 4, 0.36);
  }
  function blobi(c, x, y, r, sat, n = 9) {
    c.beginPath();
    for (let k = 0; k <= n; k++) { const a = (k / n) * 2 * PI, rr = r * (0.8 + sat() * 0.35); const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr; k ? c.lineTo(px, py) : c.moveTo(px, py); }
    c.closePath(); c.fill();
  }

  const K = {
    sydamet: { nimi: "Sydämet", p(c, s, v) { c.fillStyle = v.a; c.beginPath(); sydan(c, 0, s * 0.06, s * 0.62); c.fill(); c.fillStyle = v.i; c.beginPath(); sydan(c, -s * 0.36, -s * 0.24, s * 0.2); c.fill(); c.beginPath(); sydan(c, s * 0.38, -s * 0.3, s * 0.14); c.fill(); } },
    sydan: { nimi: "Yksi sydän", p(c, s, v) { c.fillStyle = v.a; c.beginPath(); sydan(c, 0, s * 0.05, s * 0.8); c.fill(); } },
    lehva: { nimi: "Lehvä", p(c, s, v) { oksa(c, s, v, 9, 0.3); } },
    oliivi: { nimi: "Öljypuun oksa", p(c, s, v) { oksa(c, s, v, 8, 0.18, true); } },
    kukat: { nimi: "Niittykukat", p(c, s, v) {
      c.strokeStyle = v.i; c.lineWidth = s * 0.016; c.lineCap = "round";
      [[-0.22, -0.18, 0.11], [0.05, -0.34, 0.13], [0.27, -0.12, 0.1]].forEach(([x, y, r], k) => {
        c.beginPath(); c.moveTo(0, s * 0.45); c.quadraticCurveTo(x * s * 0.4, s * 0.1, x * s, y * s); c.stroke();
        c.fillStyle = v.i; lehti(c, x * s * 0.3, s * 0.18, s * 0.16, -PI / 2 + (k - 1) * 0.9, 0.3);
        kukka(c, x * s, y * s, r * s, v.a, k === 1 ? v.b : v.i); });
    } },
    tahdet: { nimi: "Tähdet ja kuu", p(c, s, v) { c.fillStyle = v.a; kuu(c, -s * 0.08, 0, s * 0.3); c.fillStyle = v.i;
      [[0.3, -0.28, 0.07], [0.36, 0.1, 0.045], [0.14, 0.34, 0.035], [-0.38, -0.36, 0.04], [0.42, -0.02, 0.025]].forEach(([x, y, r]) => tahti(c, x * s, y * s, r * s)); } },
    tahti: { nimi: "Pohjantähti", p(c, s, v) { c.fillStyle = v.a; tahti(c, 0, 0, s * 0.45, 4, 0.18); c.fillStyle = v.i; tahti(c, 0, 0, s * 0.24, 4, 0.25, -PI / 4); } },
    pohjoinen: { nimi: "Pohjolan kahdeksankanta", p(c, s, v) {
      for (let k = 0; k < 8; k++) { c.save(); c.rotate((k * PI) / 4); c.fillStyle = k % 2 ? v.i : v.a; c.beginPath();
        c.moveTo(0, 0); c.lineTo(s * 0.12, -s * 0.2); c.lineTo(0, -s * 0.46); c.lineTo(-s * 0.12, -s * 0.2); c.closePath(); c.fill(); c.restore(); }
      c.fillStyle = v.b; c.beginPath(); c.arc(0, 0, s * 0.05, 0, 2 * PI); c.fill();
      c.fillStyle = v.a; for (let k = 0; k < 8; k++) { const a = (k * PI) / 4 + PI / 8; c.beginPath(); c.arc(Math.cos(a) * s * 0.4, Math.sin(a) * s * 0.4, s * 0.025, 0, 2 * PI); c.fill(); }
    } },
    aallot: { nimi: "Aallot", p(c, s, v) { c.lineWidth = s * 0.035; c.lineCap = "round";
      for (let r = 0; r < 3; r++) { c.strokeStyle = r === 1 ? v.i : v.a; c.beginPath();
        for (let x = -0.45; x <= 0.451; x += 0.01) { const y = (r - 1) * 0.2 + Math.sin((x + r * 0.1) * PI * 4) * 0.055; x > -0.45 ? c.lineTo(x * s, y * s) : c.moveTo(x * s, y * s); } c.stroke(); } } },
    vuoret: { nimi: "Tunturit", p(c, s, v) {
      const v3 = [[-0.18, 0.62, 0.62, v.i], [0.2, 0.75, 0.55, v.a], [-0.45, 0.5, 0.45, v.a]];
      v3.forEach(([x, h, w, col]) => { c.fillStyle = col; c.beginPath(); c.moveTo((x - w / 2) * s, 0.32 * s); c.lineTo(x * s, (0.32 - h) * s); c.lineTo((x + w / 2) * s, 0.32 * s); c.closePath(); c.fill();
        c.fillStyle = v.b; c.beginPath(); const hh = h * 0.24, ww = (w / 2) * 0.24; c.moveTo(x * s, (0.32 - h) * s); c.lineTo((x + ww) * s, (0.32 - h + hh) * s); c.lineTo((x + ww * 0.3) * s, (0.32 - h + hh * 0.8) * s);
        c.lineTo((x - ww * 0.2) * s, (0.32 - h + hh * 1.05) * s); c.lineTo((x - ww) * s, (0.32 - h + hh) * s); c.closePath(); c.fill(); });
      c.fillStyle = v.a; c.fillRect(-0.48 * s, 0.32 * s, 0.96 * s, s * 0.02); } },
    metsa: { nimi: "Kuusimetsä", p(c, s, v) { [[-0.36, 0.5, v.a], [-0.15, 0.72, v.i], [0.06, 0.58, v.a], [0.25, 0.8, v.i], [0.42, 0.48, v.a]].forEach(([x, h, col]) => { c.fillStyle = col; kuusi(c, x * s, 0.38 * s, h * s); }); } },
    lumi: { nimi: "Lumihiutale", p(c, s, v) { c.strokeStyle = v.a; c.lineWidth = s * 0.03; c.lineCap = "round";
      for (let k = 0; k < 6; k++) { c.save(); c.rotate((k * PI) / 3); c.beginPath(); c.moveTo(0, 0); c.lineTo(0, -s * 0.45);
        [0.18, 0.3].forEach((t, j) => { const l = s * (0.12 - j * 0.03); c.moveTo(0, -s * t); c.lineTo(l * 0.8, -s * t - l); c.moveTo(0, -s * t); c.lineTo(-l * 0.8, -s * t - l); }); c.stroke(); c.restore(); }
      c.fillStyle = v.i; c.beginPath(); c.arc(0, 0, s * 0.05, 0, 2 * PI); c.fill(); } },
    linnut: { nimi: "Linnut", p(c, s, v) { c.lineWidth = s * 0.03; c.lineCap = "round"; [[-0.22, 0.1, 0.34, v.a], [0.15, -0.12, 0.26, v.i], [0.32, 0.18, 0.18, v.a]].forEach(([x, y, w, col]) => { c.strokeStyle = col; lintu(c, x * s, y * s, w * s); }); } },
    terrazzo: { nimi: "Terrazzo", p(c, s, v) { const r = rnd(7); for (let k = 0; k < 14; k++) { c.fillStyle = [v.a, v.i, v.s][k % 3]; blobi(c, (r() - 0.5) * s * 0.9, (r() - 0.5) * s * 0.9, s * (0.03 + r() * 0.06), r, 6); } } },
    pilkut: { nimi: "Pilkut", p(c, s, v) { c.fillStyle = v.a; for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) { c.beginPath(); c.arc(x * s * 0.3 + (y % 2 ? s * 0.15 : 0), y * s * 0.3, s * 0.06, 0, 2 * PI); c.fill(); } } },
    artdeco: { nimi: "Art deco", p(c, s, v) { c.strokeStyle = v.a; c.lineWidth = s * 0.014;
      for (let k = 0; k <= 12; k++) { const a = PI + (k * PI) / 12; c.beginPath(); c.moveTo(Math.cos(a) * s * 0.12, s * 0.2 + Math.sin(a) * s * 0.12); c.lineTo(Math.cos(a) * s * 0.48, s * 0.2 + Math.sin(a) * s * 0.48); c.stroke(); }
      c.strokeStyle = v.i; [0.12, 0.3, 0.5].forEach((r) => { c.beginPath(); c.arc(0, s * 0.2, r * s, PI, 2 * PI); c.stroke(); });
      c.beginPath(); c.moveTo(-s * 0.5, s * 0.2); c.lineTo(s * 0.5, s * 0.2); c.stroke(); } },
    pilvet: { nimi: "Pilvet", p(c, s, v) {
      const pilvi = (x, y, w) => { c.beginPath(); c.arc(x - w * 0.25, y, w * 0.22, 0, 2 * PI); c.arc(x + w * 0.02, y - w * 0.12, w * 0.28, 0, 2 * PI); c.arc(x + w * 0.28, y + w * 0.02, w * 0.2, 0, 2 * PI); c.rect(x - w * 0.25, y, w * 0.53, w * 0.22); c.fill(); };
      c.fillStyle = v.a; pilvi(-s * 0.1, s * 0.05, s * 0.6); c.fillStyle = v.i; pilvi(s * 0.28, -s * 0.28, s * 0.3); tahti(c, -s * 0.36, -s * 0.3, s * 0.05); } },
    ilmapallot: { nimi: "Ilmapallot", p(c, s, v) {
      [[-0.2, -0.12, v.a], [0.12, -0.24, v.i], [0.22, 0.0, v.a]].forEach(([x, y, col]) => {
        c.strokeStyle = v.i; c.lineWidth = s * 0.008; c.beginPath(); c.moveTo(x * s, (y + 0.17) * s); c.quadraticCurveTo((x + 0.05) * s, 0.3 * s, 0, 0.46 * s); c.stroke();
        c.fillStyle = col; c.beginPath(); c.ellipse(x * s, y * s, s * 0.13, s * 0.16, 0, 0, 2 * PI); c.fill();
        c.beginPath(); c.moveTo(x * s, (y + 0.15) * s); c.lineTo((x - 0.025) * s, (y + 0.19) * s); c.lineTo((x + 0.025) * s, (y + 0.19) * s); c.fill(); }); } },
    sormukset: { nimi: "Vihkisormukset", p(c, s, v) { c.lineWidth = s * 0.05; c.strokeStyle = v.a; c.beginPath(); c.arc(-s * 0.12, s * 0.06, s * 0.22, 0, 2 * PI); c.stroke();
      c.strokeStyle = v.i; c.beginPath(); c.arc(s * 0.12, s * 0.06, s * 0.22, 0, 2 * PI); c.stroke();
      c.fillStyle = v.a; c.beginPath(); c.moveTo(-s * 0.12, -s * 0.3); c.lineTo(-s * 0.06, -s * 0.22); c.lineTo(-s * 0.12, -s * 0.13); c.lineTo(-s * 0.18, -s * 0.22); c.closePath(); c.fill(); } },
    laakeri: { nimi: "Laakeriseppele", p(c, s, v) {
      for (const puoli of [-1, 1]) { c.strokeStyle = v.a; c.lineWidth = s * 0.014; c.beginPath(); c.arc(0, 0, s * 0.4, PI / 2 + puoli * 0.15, PI / 2 + puoli * 2.5, puoli < 0); c.stroke();
        for (let k = 0; k < 9; k++) { const a = PI / 2 + puoli * (0.3 + k * 0.25), x = Math.cos(a) * s * 0.4, y = Math.sin(a) * s * 0.4;
          c.fillStyle = k % 2 ? v.i : v.a; lehti(c, x, y, s * 0.13, a + puoli * PI / 2 + 0.5, 0.36); lehti(c, x, y, s * 0.11, a + puoli * PI / 2 + PI - 0.4, 0.36); } } } },
    risti: { nimi: "Risti", p(c, s, v) { c.fillStyle = v.a; const w = s * 0.075; c.fillRect(-w / 2, -s * 0.42, w, s * 0.84); c.fillRect(-s * 0.24, -s * 0.2, s * 0.48, w);
      c.strokeStyle = v.i; c.lineWidth = s * 0.008; for (let k = 0; k < 16; k++) { const a = (k * PI) / 8; c.beginPath(); c.moveTo(Math.cos(a) * s * 0.3, -s * 0.16 + Math.sin(a) * s * 0.3); c.lineTo(Math.cos(a) * s * 0.36, -s * 0.16 + Math.sin(a) * s * 0.36); c.stroke(); } } },
    kyyhky: { nimi: "Kyyhky ja oksa", p(c, s, v) {
      c.fillStyle = v.a; c.beginPath();
      c.moveTo(-0.42 * s, 0.05 * s); c.quadraticCurveTo(-0.2 * s, 0.02 * s, -0.05 * s, 0.08 * s);
      c.quadraticCurveTo(-0.12 * s, -0.25 * s, -0.36 * s, -0.42 * s); c.quadraticCurveTo(0.05 * s, -0.36 * s, 0.12 * s, -0.02 * s);
      c.quadraticCurveTo(0.2 * s, -0.1 * s, 0.3 * s, -0.08 * s); c.lineTo(0.4 * s, -0.04 * s); c.lineTo(0.3 * s, 0.0);
      c.quadraticCurveTo(0.25 * s, 0.18 * s, 0.02 * s, 0.2 * s); c.lineTo(-0.2 * s, 0.32 * s); c.lineTo(-0.16 * s, 0.18 * s); c.quadraticCurveTo(-0.3 * s, 0.14 * s, -0.42 * s, 0.05 * s); c.fill();
      c.fillStyle = v.b; c.beginPath(); c.arc(0.27 * s, -0.06 * s, s * 0.012, 0, 2 * PI); c.fill();
      c.strokeStyle = v.i; c.lineWidth = s * 0.012; c.beginPath(); c.moveTo(0.39 * s, -0.035 * s); c.quadraticCurveTo(0.45 * s, 0.05 * s, 0.44 * s, 0.16 * s); c.stroke();
      c.fillStyle = v.i; [[0.42, 0.04, 0.5], [0.45, 0.1, -0.3], [0.43, 0.15, 0.9]].forEach(([x, y, a]) => lehti(c, x * s, y * s, s * 0.08, a, 0.3)); } },
    kala: { nimi: "Kala (ikhthys)", p(c, s, v) { c.strokeStyle = v.a; c.lineWidth = s * 0.04; c.lineCap = "round"; c.beginPath();
      c.moveTo(-0.42 * s, -0.2 * s); c.quadraticCurveTo(0.05 * s, 0.32 * s, 0.42 * s, 0); c.quadraticCurveTo(0.05 * s, -0.32 * s, -0.42 * s, 0.2 * s); c.stroke(); } },
    aurinko: { nimi: "Aurinko", p(c, s, v) { c.fillStyle = v.a; c.beginPath(); c.arc(0, 0, s * 0.2, 0, 2 * PI); c.fill(); c.strokeStyle = v.i; c.lineWidth = s * 0.025; c.lineCap = "round";
      for (let k = 0; k < 12; k++) { const a = (k * PI) / 6; c.beginPath(); c.moveTo(Math.cos(a) * s * 0.28, Math.sin(a) * s * 0.28); c.lineTo(Math.cos(a) * s * (k % 2 ? 0.38 : 0.45), Math.sin(a) * s * (k % 2 ? 0.38 : 0.45)); c.stroke(); } } },
    vesivari: { nimi: "Vesiväriläiskät", p(c, s, v) { const r = rnd(11); c.globalAlpha *= 0.35;
      for (let k = 0; k < 9; k++) { c.fillStyle = [v.a, v.s, v.i][k % 3]; blobi(c, (r() - 0.5) * s * 0.55, (r() - 0.5) * s * 0.4, s * (0.14 + r() * 0.14), r, 14); } } },
    koristekulma: { nimi: "Koristekiehkura", p(c, s, v) { c.strokeStyle = v.a; c.lineWidth = s * 0.02; c.lineCap = "round";
      c.beginPath(); c.moveTo(-0.45 * s, 0.1 * s); c.bezierCurveTo(-0.2 * s, -0.25 * s, 0.1 * s, 0.25 * s, 0.32 * s, -0.05 * s); c.stroke();
      c.beginPath(); c.arc(0.22 * s, -0.08 * s, s * 0.1, 0.2, PI * 1.6); c.stroke(); c.beginPath(); c.arc(-0.3 * s, 0.1 * s, s * 0.07, PI * 1.2, PI * 2.6); c.stroke();
      c.fillStyle = v.i; lehti(c, -0.05 * s, 0.02 * s, s * 0.12, -1.2, 0.4); lehti(c, -0.05 * s, 0.02 * s, s * 0.1, 2.0, 0.4); c.beginPath(); c.arc(0.4 * s, -0.12 * s, s * 0.025, 0, 2 * PI); c.fill(); } },
  };

  // Sijoittelut: palauttaa, piirretäänkö kuvio tekstipinon osana ("yla"/"ala") vai erikseen koko sivulle.
  const SIJAINNIT = { yla: "Tekstin yläpuolella", ala: "Tekstin alapuolella", tausta: "Isona taustalla", kuvio: "Toistuva kuvio", kulmat: "Kulmissa", reunus: "Reunuksena" };
  const KOOT = { pieni: ["Pieni", 0.7], normaali: ["Normaali", 1], suuri: ["Suuri", 1.35] };

  function yksi(c, id, x, y, s, v, kierto = 0, peili = false) {
    const m = K[id]; if (!m) return;
    c.save(); c.translate(x, y); if (kierto) c.rotate(kierto); if (peili) c.scale(-1, 1); m.p(c, s, v); c.restore();
  }
  // Koko sivun sijoittelut (tausta, kuvio, kulmat, reunus). W,H = näkyvä alue pikseleinä.
  function sivulle(c, id, sij, koko, W, H, v) {
    if (!K[id]) return;
    const k = (KOOT[koko] || KOOT.normaali)[1], D = Math.min(W, H);
    if (sij === "tausta") { c.save(); c.globalAlpha = 0.16; yksi(c, id, W / 2, H * 0.47, Math.min(W, H) * 0.82 * k, v); c.restore(); }
    else if (sij === "kuvio") {
      const s = D * 0.085 * k, d = s * 1.9, r = rnd(3); c.save(); c.globalAlpha = 0.22;
      for (let y = d * 0.5, rivi = 0; y < H; y += d, rivi++) for (let x = (rivi % 2 ? d : d / 2); x < W; x += d) yksi(c, id, x, y, s, v, (r() - 0.5) * 0.6);
      c.restore();
    } else if (sij === "kulmat") {
      const s = D * 0.17 * k, m = D * 0.06 + s / 2;
      yksi(c, id, m, m, s, v, 0); yksi(c, id, W - m, m, s, v, 0, true); yksi(c, id, m, H - m, s, v, PI, true); yksi(c, id, W - m, H - m, s, v, PI);
    } else if (sij === "reunus") {
      const s = D * 0.055 * k, m = D * 0.045 + s / 2, nx = Math.max(3, Math.round((W - 2 * m) / (s * 1.5))), ny = Math.max(3, Math.round((H - 2 * m) / (s * 1.5)));
      for (let i = 0; i <= nx; i++) { const x = m + ((W - 2 * m) * i) / nx; yksi(c, id, x, m, s, v); yksi(c, id, x, H - m, s, v); }
      for (let i = 1; i < ny; i++) { const y = m + ((H - 2 * m) * i) / ny; yksi(c, id, m, y, s, v); yksi(c, id, W - m, y, s, v); }
    }
  }
  window.OLKuviot = { K, SIJAINNIT, KOOT, yksi, sivulle, sydan, tahti };
})();
