// Omalahja – karttajulisteen data ja piirto. Tiedot: © OpenStreetMap contributors (ODbL), haku Nominatim, tiet ja vedet Overpass API.
(function () {
  const PI = Math.PI;
  const X = (lon) => (lon * PI) / 180;
  const Y = (lat) => Math.log(Math.tan(PI / 4 + (lat * PI) / 360));
  const LAT = (y) => (360 / PI) * Math.atan(Math.exp(y)) - 90;
  const LON = (x) => (x * 180) / PI;

  const TEEMAT = {
    klassinen: { nimi: "Klassinen", bg: "#fbfaf6", vesi: "#d8e3e8", tie: "#232323", teksti: "#1f1f1f", korostus: "#7a2e2e" },
    yo: { nimi: "Yö ja kulta", bg: "#18263f", vesi: "#0a1322", tie: "#e2bd6b", teksti: "#f1e5c6", korostus: "#e2bd6b" },
    mustavalko: { nimi: "Mustavalko", bg: "#ffffff", vesi: "#e9e9e9", tie: "#000000", teksti: "#000000", korostus: "#000000" },
    hiili: { nimi: "Hiili", bg: "#1c1c1c", vesi: "#2d2d2d", tie: "#f2f2f2", teksti: "#f2f2f2", korostus: "#c9a45c" },
    salvia: { nimi: "Salvia", bg: "#e7ecdf", vesi: "#b9cfc8", tie: "#33432f", teksti: "#2a3826", korostus: "#6b7f5a" },
    ruusu: { nimi: "Ruusu", bg: "#f8e5e1", vesi: "#ecc9c4", tie: "#6c2d3a", teksti: "#5a2430", korostus: "#b85d6e" },
    meri: { nimi: "Meri", bg: "#eef4f6", vesi: "#9cc4d6", tie: "#1d3a49", teksti: "#1d3a49", korostus: "#2f7c95" },
    hiekka: { nimi: "Hiekka", bg: "#f0e6d3", vesi: "#bdd2d2", tie: "#594632", teksti: "#4a3a29", korostus: "#a07a46" },
    terrakotta: { nimi: "Terrakotta", bg: "#f4e2d2", vesi: "#cbd9d6", tie: "#a3492a", teksti: "#5b2a18", korostus: "#c0623b" },
    metsa: { nimi: "Metsä", bg: "#1f3329", vesi: "#16261e", tie: "#e9dfc4", teksti: "#efe6cf", korostus: "#c9b37e" },
    laventeli: { nimi: "Laventeli", bg: "#efe9f5", vesi: "#d3c8e6", tie: "#3d3152", teksti: "#3d3152", korostus: "#8a6fb0" },
    sininen: { nimi: "Sinikopio", bg: "#1e4a7a", vesi: "#173b62", tie: "#ffffff", teksti: "#ffffff", korostus: "#bcd4ee" },
  };

  // Valmiit paikat. Raamatun paikkojen jakeet: Raamattu 1933/38 (vapaa käyttö).
  const RAAMATTU = [
    { id: "jerusalem", nimi: "Jerusalem", ala: "Vanha kaupunki", lat: 31.7767, lon: 35.2345, sade: 0.9, jae: "Meidän jalkamme seisovat sinun porteissasi, Jerusalem.", viite: "Ps. 122:2" },
    { id: "betlehem", nimi: "Betlehem", ala: "", lat: 31.7049, lon: 35.2023, sade: 1.3, jae: "Sillä teille on tänä päivänä syntynyt Vapahtaja, joka on Kristus, Herra, Daavidin kaupungissa.", viite: "Luuk. 2:11" },
    { id: "nasaret", nimi: "Nasaret", ala: "", lat: 32.7019, lon: 35.2978, sade: 1.6, jae: "Voiko Nasaretista tulla mitään hyvää? Filippus sanoi hänelle: Tule ja katso.", viite: "Joh. 1:46" },
    { id: "galilea", nimi: "Galilean järvi", ala: "Gennesaretin järvi", lat: 32.83, lon: 35.585, sade: 11, jae: "Seuratkaa minua, niin minä teen teistä ihmisten kalastajia.", viite: "Matt. 4:19" },
    { id: "kapernaum", nimi: "Kapernaum", ala: "Galilean järven rannalla", lat: 32.8807, lon: 35.5751, sade: 1.4, jae: "Ja he menivät Kapernaumiin.", viite: "Mark. 1:21" },
    { id: "jordan", nimi: "Jordan-joki", ala: "Kastepaikka Qasr al-Yahud", lat: 31.838, lon: 35.539, sade: 1.8, jae: "Tämä on minun rakas Poikani, johon minä olen mielistynyt.", viite: "Matt. 3:17" },
    { id: "jeriko", nimi: "Jeriko", ala: "", lat: 31.8667, lon: 35.45, sade: 2.2, jae: "Sillä Ihmisen Poika on tullut etsimään ja pelastamaan sitä, mikä kadonnut on.", viite: "Luuk. 19:10" },
    { id: "kaana", nimi: "Kaanaan Kaana", ala: "Kafr Kanna", lat: 32.7466, lon: 35.342, sade: 1.1, jae: "Tämän ensimmäisen tunnustekonsa Jeesus teki Kaanaassa Galileassa ja ilmoitti kirkkautensa.", viite: "Joh. 2:11" },
    { id: "oljymaki", nimi: "Öljymäki", ala: "Jerusalem", lat: 31.7784, lon: 35.244, sade: 1.0, jae: "Älköön kuitenkaan tapahtuko minun tahtoni, vaan sinun.", viite: "Luuk. 22:42" },
    { id: "emmaus", nimi: "Emmaus", ala: "", lat: 31.8393, lon: 34.9895, sade: 1.8, jae: "Jää meidän tykömme, sillä ilta joutuu, ja päivä on jo laskenut.", viite: "Luuk. 24:29" },
    { id: "sinai", nimi: "Siinainvuori", ala: "Jebel Musa", lat: 28.5392, lon: 33.975, sade: 3.5, jae: "Minä olen Herra, sinun Jumalasi.", viite: "2. Moos. 20:2" },
    { id: "betania", nimi: "Betania", ala: "", lat: 31.7717, lon: 35.26, sade: 1.1, jae: "Minä olen ylösnousemus ja elämä; joka uskoo minuun, se elää, vaikka olisi kuollut.", viite: "Joh. 11:25" },
  ];
  const SUOMI = [
    { id: "helsinki", nimi: "Helsinki", ala: "Suomi", lat: 60.1699, lon: 24.9384, sade: 2.5 },
    { id: "tampere", nimi: "Tampere", ala: "Suomi", lat: 61.4981, lon: 23.761, sade: 2.5 },
    { id: "turku", nimi: "Turku", ala: "Suomi", lat: 60.4518, lon: 22.2666, sade: 2.5 },
    { id: "oulu", nimi: "Oulu", ala: "Suomi", lat: 65.0121, lon: 25.4651, sade: 2.5 },
    { id: "jyvaskyla", nimi: "Jyväskylä", ala: "Suomi", lat: 62.2426, lon: 25.7473, sade: 2.5 },
    { id: "kuopio", nimi: "Kuopio", ala: "Suomi", lat: 62.8924, lon: 27.677, sade: 2.5 },
    { id: "rovaniemi", nimi: "Rovaniemi", ala: "Suomi", lat: 66.5039, lon: 25.7294, sade: 2.5 },
    { id: "ylivieska", nimi: "Ylivieska", ala: "Suomi", lat: 64.0736, lon: 24.5341, sade: 2 },
  ];

  // ---- Paikkahaku ja karttadata omalahja.fi:n kautta (Worker välimuistittaa Nominatimin ja Overpassin) ----
  let viimeHaku = 0;
  async function hae(teksti, vainSuomi) {
    const odota = 1100 - (Date.now() - viimeHaku); if (odota > 0) await new Promise((r) => setTimeout(r, odota));
    viimeHaku = Date.now();
    const r = await fetch(`/api/kartta/haku?q=${encodeURIComponent(teksti)}&fi=${vainSuomi ? 1 : 0}`, { signal: AbortSignal.timeout ? AbortSignal.timeout(15000) : undefined });
    if (!r.ok) throw new Error("haku " + r.status);
    const j = await r.json(); if (!Array.isArray(j)) throw new Error("haku");
    return j.map((p) => {
      const a = p.address || {}, nimi = a.city || a.town || a.village || a.municipality || a.hamlet || a.suburb || p.name || p.display_name.split(",")[0];
      const laji = p.addresstype || p.type, sade = { city: 2.5, town: 2, municipality: 2.5, village: 1, hamlet: 0.8, suburb: 1.5, neighbourhood: 0.8, island: 2, lake: 4 }[laji] || 1.5;
      return { nimi: p.name || nimi, ala: a.country || "", kuvaus: p.display_name, lat: +p.lat, lon: +p.lon, sade };
    });
  }
  const TASOT = [0.6, 1, 1.6, 2.5, 4, 6.5, 10, 16];
  const taso = (sade) => TASOT.find((x) => x >= sade * 0.999) || 16;
  function rajat(lat, lon, sade, kerroin = 1.7) {
    const dlat = ((sade * kerroin) / 6371) * (180 / PI), dlon = dlat / Math.cos((lat * PI) / 180);
    return { s: lat - dlat * 1.45, n: lat + dlat * 1.45, w: lon - dlon, e: lon + dlon };
  }
  async function lataa(lat, lon, sade, signaali) {
    const ac = new AbortController(), aika = setTimeout(() => ac.abort(), 70000);
    if (signaali) signaali.addEventListener("abort", () => ac.abort());
    try {
      const r = await fetch(`/api/kartta/alue?lat=${lat.toFixed(4)}&lon=${lon.toFixed(4)}&sade=${sade}`, { signal: ac.signal });
      if (!r.ok) throw new Error("kartta " + r.status);
      const j = await r.json();
      return { ...jasenna(j.osm.elements || [], j.ruutu.taso), rajat: j.ruutu.rajat, taso: j.ruutu.taso, lat, lon, sade };
    } finally { clearTimeout(aika); }
  }

  const LUOKKA = { motorway: 3.4, trunk: 3.2, primary: 2.7, secondary: 2.3, tertiary: 1.9, motorway_link: 1.8, trunk_link: 1.8, primary_link: 1.6, secondary_link: 1.5, tertiary_link: 1.4,
    unclassified: 1.25, residential: 1.2, living_street: 1.05, pedestrian: 0.9, service: 0.75, footway: 0.45, path: 0.45, cycleway: 0.5, track: 0.5, steps: 0.4 };
  const sama = (a, b) => a[0] === b[0] && a[1] === b[1];
  function liita(osat, suunnattu) {
    const ketjut = []; const jl = osat.filter((p) => p.length > 1).map((p) => p.slice());
    while (jl.length) {
      let k = jl.pop(), muuttui = true;
      while (muuttui) {
        muuttui = false; if (k.length > 3 && sama(k[0], k[k.length - 1])) break;
        for (let i = 0; i < jl.length; i++) {
          const o = jl[i];
          if (sama(k[k.length - 1], o[0])) k = k.concat(o.slice(1));
          else if (sama(k[0], o[o.length - 1])) k = o.concat(k.slice(1));
          else if (!suunnattu && sama(k[k.length - 1], o[o.length - 1])) k = k.concat(o.slice(0, -1).reverse());
          else if (!suunnattu && sama(k[0], o[0])) k = o.slice().reverse().concat(k.slice(1));
          else continue;
          jl.splice(i, 1); muuttui = true; break;
        }
      }
      ketjut.push(k);
    }
    return ketjut;
  }
  function ohenna(p, tol) { // poistetaan pisteet, jotka ovat liian lähellä edellistä (nopeampi piirto)
    if (p.length < 4) return p; const u = [p[0]]; let [x0, y0] = p[0];
    for (let i = 1; i < p.length - 1; i++) { const [x, y] = p[i]; if (Math.abs(x - x0) + Math.abs(y - y0) > tol) { u.push(p[i]); x0 = x; y0 = y; } }
    u.push(p[p.length - 1]); return u;
  }
  function jasenna(el, tasoKm = 2.5) {
    const tiet = [], radat = [], vedet = [], joet = [], rannat = [];
    const tol = tasoKm / 6371 / 900;
    const pisteet = (g) => (g || []).filter(Boolean).map((p) => [X(p.lon), Y(p.lat)]);
    let g = "";
    for (const e of el) {
      if (!e.geometry && !e.members && e.tags && e.tags.g) { g = e.tags.g; continue; }
      if (e.type === "way") {
        const p = pisteet(e.geometry); if (p.length < 2) continue;
        if (g[0] === "t") tiet.push({ l: parseFloat(g.slice(1)) || 1, p: ohenna(p, tol) });
        else if (g === "rata") radat.push(ohenna(p, tol));
        else if (g === "ranta") rannat.push(p);
        else if (g === "vesi") vedet.push({ ulko: [ohenna(p, tol)], sisa: [] });
        else if (g[0] === "j") joet.push({ l: parseFloat(g.slice(1)) || 1, p: ohenna(p, tol) });
      } else if (e.type === "relation" && e.members) {
        const ulko = [], sisa = [];
        for (const m of e.members) if (m.type === "way" && m.geometry) (m.role === "inner" ? sisa : ulko).push(pisteet(m.geometry));
        vedet.push({ ulko: liita(ulko), sisa: liita(sisa) });
      }
    }
    tiet.sort((a, b) => a.l - b.l);
    return { tiet, radat, vedet, joet, rannat: liita(rannat, true) };
  }

  // ---- Meren täyttö rantaviivasta (OSM: maa on rantaviivan vasemmalla puolella) ----
  function leikkaa(viiva, R) {
    // Liang–Barsky janoittain; palauttaa palat, joilla on sisääntulo- ja poistumispiste suorakulmion reunalla
    const palat = []; let nyk = null;
    for (let i = 0; i < viiva.length - 1; i++) {
      const [x0, y0] = viiva[i], [x1, y1] = viiva[i + 1], dx = x1 - x0, dy = y1 - y0;
      let t0 = 0, t1 = 1; const p = [-dx, dx, -dy, dy], q = [x0 - R.x0, R.x1 - x0, y0 - R.y0, R.y1 - y0]; let ok = true;
      for (let j = 0; j < 4; j++) { if (p[j] === 0) { if (q[j] < 0) { ok = false; break; } } else { const r = q[j] / p[j]; if (p[j] < 0) { if (r > t1) { ok = false; break; } if (r > t0) t0 = r; } else { if (r < t0) { ok = false; break; } if (r < t1) t1 = r; } } }
      if (!ok) { if (nyk) { palat.push(nyk); nyk = null; } continue; }
      const a = [x0 + t0 * dx, y0 + t0 * dy], b = [x0 + t1 * dx, y0 + t1 * dy];
      if (!nyk || t0 > 0) { if (nyk) palat.push(nyk); nyk = { p: [a], sisaan: t0 > 0 }; }
      nyk.p.push(b);
      if (t1 < 1) { nyk.ulos = true; palat.push(nyk); nyk = null; }
    }
    if (nyk) palat.push(nyk);
    return palat.filter((x) => x.sisaan && x.ulos && x.p.length > 1);
  }
  function meri(rannat, R) {
    const W = R.x1 - R.x0, H = R.y1 - R.y0, P = 2 * (W + H), eps = 1e-12;
    const tt = ([x, y]) => { // kehäparametri vastapäivään (y ylöspäin) vasemmasta alakulmasta
      const dl = Math.abs(x - R.x0), dr = Math.abs(x - R.x1), db = Math.abs(y - R.y0), dt = Math.abs(y - R.y1), m = Math.min(dl, dr, db, dt);
      if (m === db) return x - R.x0; if (m === dr) return W + (y - R.y0); if (m === dt) return W + H + (R.x1 - x); return 2 * W + H + (R.y1 - y);
    };
    const kulmat = [[W, [R.x1, R.y0]], [W + H, [R.x1, R.y1]], [2 * W + H, [R.x0, R.y1]], [0, [R.x0, R.y0]]];
    const sis = (p) => p[0] > R.x0 && p[0] < R.x1 && p[1] > R.y0 && p[1] < R.y1;
    const palat = [], saaret = [];
    for (let k of rannat) {
      const suljettu = k.length > 3 && sama(k[0], k[k.length - 1]);
      if (suljettu && k.every(sis)) { saaret.push(k); continue; }
      if (suljettu) { const i = k.findIndex((p) => !sis(p)); if (i < 0) continue; k = k.slice(i, -1).concat(k.slice(0, i + 1)); }
      palat.push(...leikkaa(k, R));
    }
    palat.forEach((p) => { p.ts = tt(p.p[0]); p.te = tt(p.p[p.p.length - 1]); });
    const maat = []; const kayt = new Set();
    for (let a = 0; a < palat.length; a++) {
      if (kayt.has(a)) continue;
      const poly = []; let cur = a, kierros = 0;
      while (kierros++ < palat.length + 2) {
        kayt.add(cur); poly.push(...palat[cur].p);
        const te = palat[cur].te; let paras = -1, pd = Infinity;
        for (let b = 0; b < palat.length; b++) { if (kayt.has(b) && b !== a) continue; let d = (palat[b].ts - te + P) % P; if (d < eps && b === cur) d = P; if (d < pd) { pd = d; paras = b; } }
        if (paras < 0) break;
        kulmat.map(([t, xy]) => [(t - te + P) % P, xy]).filter(([d]) => d > eps && d < pd).sort((x, y) => x[0] - y[0]).forEach(([, xy]) => poly.push(xy));
        if (paras === a) break; cur = paras;
      }
      maat.push(poly);
    }
    return { maat, saaret, onMeri: palat.length > 0 || saaret.length > 0 };
  }

  // ---- Piirto ----
  // n = näkymä: { lat, lon, sade } ; alue = { x, y, w, h } pikseleinä ; t = teema ; paksuus kerroin
  function piirra(c, d, n, alue, t, paksuus = 1) {
    const cx = X(n.lon), cy = Y(n.lat), cos = Math.cos((n.lat * PI) / 180);
    const yks = n.sade / 6371 / cos; // mercator-yksiköt puolelle leveydelle
    const k = alue.w / 2 / yks, ox = alue.x + alue.w / 2, oy = alue.y + alue.h / 2;
    const px = (p) => [ox + (p[0] - cx) * k, oy - (p[1] - cy) * k];
    const polku = (pts, sulje) => { for (let i = 0; i < pts.length; i++) { const [x, y] = px(pts[i]); i ? c.lineTo(x, y) : c.moveTo(x, y); } if (sulje) c.closePath(); };
    c.fillStyle = t.bg; c.fillRect(alue.x, alue.y, alue.w, alue.h);
    if (!d) return;
    // Meri
    if (d.rannat.length) {
      const b = d.rajat, R = { x0: X(b.w), x1: X(b.e), y0: Y(b.s), y1: Y(b.n) };
      const m = meri(d.rannat, R);
      if (m.onMeri) {
        c.fillStyle = t.vesi; c.fillRect(alue.x, alue.y, alue.w, alue.h);
        c.fillStyle = t.bg; c.beginPath(); if (!m.maat.length && !m.saaret.length) { /* pelkkää merta */ }
        m.maat.forEach((p) => polku(p, true)); m.saaret.forEach((p) => polku(p, true)); c.fill("nonzero");
      }
    }
    c.fillStyle = t.vesi; c.beginPath();
    for (const v of d.vedet) { v.ulko.forEach((r) => polku(r, true)); v.sisa.forEach((r) => polku(r, true)); }
    c.fill("evenodd");
    const perus = (alue.w / 900) * paksuus * Math.max(0.75, Math.min(2.2, Math.sqrt(3 / n.sade)));
    c.lineCap = "round"; c.lineJoin = "round"; c.strokeStyle = t.vesi;
    for (const j of d.joet) { c.lineWidth = perus * j.l * 1.4; c.beginPath(); polku(j.p); c.stroke(); }
    c.strokeStyle = t.tie; c.globalAlpha = 0.55; c.lineWidth = perus * 0.7; c.setLineDash([perus * 3, perus * 2]);
    for (const r of d.radat) { c.beginPath(); polku(r); c.stroke(); }
    c.setLineDash([]); c.globalAlpha = 1;
    let edl = -1;
    for (const tie of d.tiet) { if (tie.l !== edl) { if (edl >= 0) c.stroke(); c.beginPath(); c.lineWidth = perus * tie.l; edl = tie.l; } polku(tie.p); }
    if (edl >= 0) c.stroke();
  }
  // Onko näkymä vielä ladatun alueen sisällä?
  function kattaa(d, n) {
    if (!d) return false; const b = d.rajat, r = rajat(n.lat, n.lon, n.sade, 1.05);
    return taso(n.sade) === d.taso && r.s >= b.s && r.n <= b.n && r.w >= b.w && r.e <= b.e;
  }

  function koordinaatit(lat, lon) {
    const f = (v, pos, neg) => { const a = Math.abs(v), d = Math.floor(a), m = Math.floor((a - d) * 60), s = Math.round(((a - d) * 60 - m) * 60);
      return `${d}°${String(m).padStart(2, "0")}′${String(s % 60).padStart(2, "0")}″ ${v >= 0 ? pos : neg}`; };
    return `${f(lat, "P", "E")}  ·  ${f(lon, "I", "L")}`;
  }
  function siirra(n, dxPx, dyPx, leveysPx) {
    const cos = Math.cos((n.lat * PI) / 180), yks = n.sade / 6371 / cos, k = leveysPx / 2 / yks;
    return { ...n, lon: LON(X(n.lon) - dxPx / k), lat: LAT(Y(n.lat) + dyPx / k) };
  }
  window.OLKartta = { TEEMAT, RAAMATTU, SUOMI, hae, lataa, piirra, kattaa, koordinaatit, siirra, _meri: meri, _jasenna: jasenna };
})();
