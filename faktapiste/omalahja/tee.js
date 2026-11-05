// Omalahja – tuotesuunnittelija (nimijuliste ja karttajuliste). Esikatselu ja painotiedosto piirretään samalla koodilla.
(function () {
  const C = window.OL_CONFIG, MALLI = document.body.dataset.malli, KV = window.OLKuviot, KA = window.OLKartta;
  const $ = (s, el = document) => el.querySelector(s);
  const h = (tag, at = {}, ...lapset) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(at)) { if (k === "on") for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f); else if (k === "class") e.className = v; else if (k === "html") e.innerHTML = v; else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v); } lapset.flat().forEach((l) => l != null && e.append(l)); return e; };
  const euro = (s) => (s / 100).toFixed(s % 100 ? 2 : 0).replace(".", ",") + " €";

  const FONTIT = [
    { id: "klassinen", nimi: "Klassinen", o: "Fraunces", ow: 600, t: "Nunito Sans", tw: 400 },
    { id: "elegantti", nimi: "Elegantti", o: "Playfair Display", ow: 700, t: "Lato", tw: 400 },
    { id: "kasiala", nimi: "Käsiala", o: "Great Vibes", ow: 400, t: "Cormorant Garamond", tw: 500, kasi: true },
    { id: "leikkisa", nimi: "Leikkisä", o: "Dancing Script", ow: 700, t: "Quicksand", tw: 500, kasi: true },
    { id: "moderni", nimi: "Moderni", o: "Montserrat", ow: 700, t: "Montserrat", tw: 400, isot: true, vali: 0.08 },
    { id: "naytava", nimi: "Näyttävä", o: "Abril Fatface", ow: 400, t: "Raleway", tw: 500 },
    { id: "rento", nimi: "Rento", o: "Amatic SC", ow: 700, t: "Josefin Sans", tw: 400, kerroin: 1.25 },
    { id: "juhlava", nimi: "Juhlava", o: "Cinzel", ow: 600, t: "EB Garamond", tw: 400 },
    { id: "pehmea", nimi: "Pehmeä", o: "Pacifico", ow: 400, t: "Nunito", tw: 400, kasi: true, kerroin: 0.85 },
    { id: "skandi", nimi: "Skandi", o: "Josefin Sans", ow: 300, t: "Josefin Sans", tw: 400, isot: true, vali: 0.18 },
  ];
  const PALETIT = {
    kerma: { nimi: "Kerma", b: "#f7f1e8", i: "#2b2321", a: "#7a2e2e", s: "#e6d5bf" },
    valkoinen: { nimi: "Valkoinen ja kulta", b: "#ffffff", i: "#222222", a: "#b08d57", s: "#ece6dc" },
    yonsininen: { nimi: "Yönsininen", b: "#1d2a44", i: "#f4ede1", a: "#d8b26a", s: "#33456a" },
    salvia: { nimi: "Salvia", b: "#e3e8dc", i: "#2f3b2c", a: "#6b7f5a", s: "#c9d4bd" },
    roosa: { nimi: "Roosa", b: "#f8e6e3", i: "#4a2c2c", a: "#c46a6a", s: "#efcbc5" },
    hiili: { nimi: "Hiili ja kulta", b: "#222222", i: "#f1f1f1", a: "#c9a45c", s: "#3a3a3a" },
    terrakotta: { nimi: "Terrakotta", b: "#f2e2d2", i: "#4a2a1d", a: "#c0623b", s: "#e6c6aa" },
    laventeli: { nimi: "Laventeli", b: "#ece6f3", i: "#3b3050", a: "#8a6fb0", s: "#d8cbe8" },
    metsa: { nimi: "Metsä", b: "#23362b", i: "#f1ead9", a: "#c9b37e", s: "#33503f" },
    meri: { nimi: "Meri", b: "#e2eef2", i: "#1f3a48", a: "#2f7c95", s: "#c0dae4" },
    hiekka: { nimi: "Hiekka", b: "#efe6d6", i: "#3e3428", a: "#a07a46", s: "#dccbab" },
    mustavalko: { nimi: "Mustavalko", b: "#ffffff", i: "#111111", a: "#111111", s: "#e4e4e4" },
  };
  const JAKEET = [
    ["Herra on minun paimeneni, ei minulta mitään puutu.", "Ps. 23:1"],
    ["Sillä niin on Jumala maailmaa rakastanut, että hän antoi ainokaisen Poikansa, ettei yksikään, joka häneen uskoo, hukkuisi, vaan hänellä olisi iankaikkinen elämä.", "Joh. 3:16"],
    ["Niin pysyvät nyt usko, toivo, rakkaus, nämä kolme; mutta suurin näistä on rakkaus.", "1. Kor. 13:13"],
    ["Rakkaus on pitkämielinen, rakkaus on lempeä.", "1. Kor. 13:4"],
    ["Mutta minä ja minun perheeni palvelemme Herraa.", "Joos. 24:15"],
    ["Herra siunatkoon sinua ja varjelkoon sinua.", "4. Moos. 6:24"],
    ["Älä pelkää, sillä minä olen lunastanut sinut, minä olen kutsunut sinut nimeltä; sinä olet minun.", "Jes. 43:1"],
    ["Kaikki minä voin hänessä, joka minua vahvaksi tekee.", "Fil. 4:13"],
    ["Herra varjelee sinun lähtemisesi ja tulemisesi, nyt ja iankaikkisesti.", "Ps. 121:8"],
    ["Ja katso, minä olen teidän kanssanne joka päivä maailman loppuun asti.", "Matt. 28:20"],
    ["Jumala on meidän turvamme ja voimamme, apumme hädässä aivan vahva.", "Ps. 46:2"],
    ["Minä olen tie ja totuus ja elämä.", "Joh. 14:6"],
  ];
  const ASETTELUT = {
    keskitetty: { nimi: "Keskitetty", kuvio: "lehva", esim: { nimi: "Aino & Eero", ala: "Rakkaudella", pvm: "14.6.2025", lisa: "Koti on siellä, missä sydän on" } },
    sydanviiva: { nimi: "Sydänviiva", kuvio: "ei", esim: { nimi: "Aino & Eero", ala: "Tästä alkoi meidän tarinamme", pvm: "14.6.2025", lisa: "" } },
    minimal: { nimi: "Minimalistinen", kuvio: "ei", esim: { nimi: "Virtanen", ala: "Perhe", pvm: "Koti vuodesta 2018", lisa: "" } },
    perhe: { nimi: "Perhe ja nimet", kuvio: "sydan", esim: { nimi: "Perhe Virtanen", ala: "Meidän koti", pvm: "Ylivieska 2026", lisa: "", jasenet: "Matti\nLiisa\nAino\nEero\nMusti" } },
    kehys: { nimi: "Kehys", kuvio: "koristekulma", esim: { nimi: "Aino & Eero", ala: "Yhdessä", pvm: "14.6.2025", lisa: "" } },
    monogrammi: { nimi: "Monogrammi", kuvio: "ei", esim: { nimi: "Aino", ala: "Rakas tyttäremme", pvm: "3.3.2026", lisa: "" } },
    vauva: { nimi: "Vauvajuliste", kuvio: "pilvet", esim: { nimi: "Aino", ala: "Tervetuloa maailmaan", pvm: "3.3.2026", lisa: "Oulu", paino: "3 450 g", pituus: "50 cm", klo: "14.25" } },
    haat: { nimi: "Hääjuliste", kuvio: "sormukset", esim: { nimi: "Aino & Eero", ala: "Menivät naimisiin", pvm: "14.6.2025", lisa: "Ylivieskan kirkko" } },
    jae: { nimi: "Raamatunlause", kuvio: "kyyhky", esim: { nimi: "Perhe Virtanen", ala: "", pvm: "", lisa: "", jae: JAKEET[0][0], viite: JAKEET[0][1] } },
  };
  const KARTTAMUODOT = { koko: "Suorakulmio", pyorea: "Pyöristetty", ympyra: "Ympyrä", sydan: "Sydän" };
  const REUNUKSET = { valja: "Väljä", kapea: "Kapea", ei: "Ei reunusta" };
  const TEKSTISIJ = { alla: "Kartan alla", paalla: "Kartan päällä", ei: "Ei tekstiä" };
  const PAKSUUS = { ohut: ["Ohut", 0.7], normaali: ["Normaali", 1], paksu: ["Paksu", 1.45] };

  // ---------- Tila ----------
  const OLETUS = MALLI === "kartta"
    ? { tuote: "juliste", koko: "50x70", vari: "musta", suunta: "pysty", lat: 60.1699, lon: 24.9384, sade: 2.5, teema: "klassinen", muoto: "koko", reunus: "valja", tekstiSij: "alla",
        otsikko: "Helsinki", ala: "Suomi", koord: "", jae: "", viite: "", fontti: "moderni", paksuus: "normaali", kuvio: "ei", kuvioSij: "kulmat", kuvioKoko: "normaali", vainSuomi: true }
    : { tuote: "juliste", koko: "30x40", vari: "musta", suunta: "pysty", asettelu: "keskitetty", fontti: "klassinen", paletti: "kerma", isot: false, kuvio: "lehva", kuvioSij: "yla", kuvioKoko: "normaali",
        ...ASETTELUT.keskitetty.esim, jasenet: "", paino: "", pituus: "", klo: "", jae: "", viite: "" };
  const AVAIN = "omalahja-" + MALLI;
  let S = { ...OLETUS };
  try { const v = JSON.parse(localStorage.getItem(AVAIN) || "null"); if (v && typeof v === "object") S = { ...OLETUS, ...v }; } catch {}
  // Valmiit esimerkit (etusivun galleria linkittää: /tee/nimijuliste/?esim=perhe)
  const ESIMERKIT = {
    nimi: {
      perhe: { asettelu: "perhe", paletti: "salvia", fontti: "elegantti", kuvio: "lehva", kuvioSij: "yla", kuvioKoko: "normaali", nimi: "Perhe Virtanen", ala: "Meidän koti", pvm: "Ylivieska 2026", lisa: "", jasenet: "Matti\nLiisa\nAino\nEero\nMusti", jae: "", viite: "" },
      vauva: { asettelu: "vauva", paletti: "roosa", fontti: "kasiala", kuvio: "pilvet", kuvioSij: "yla", kuvioKoko: "normaali", nimi: "Aino", ala: "Tervetuloa maailmaan", pvm: "3.3.2026", paino: "3 450 g", pituus: "50 cm", klo: "14.25", lisa: "Oulu", jae: "", viite: "" },
      haat: { asettelu: "haat", paletti: "valkoinen", fontti: "juhlava", kuvio: "laakeri", kuvioSij: "tausta", kuvioKoko: "normaali", nimi: "Aino & Eero", ala: "Menivät naimisiin", pvm: "14.6.2025", lisa: "Ylivieskan kirkko", jae: "", viite: "" },
      jae: { asettelu: "jae", paletti: "kerma", fontti: "kasiala", kuvio: "kyyhky", kuvioSij: "yla", kuvioKoko: "normaali", nimi: "Perhe Virtanen", ala: "", pvm: "", lisa: "", jae: JAKEET[0][0], viite: JAKEET[0][1] },
      joulu: { asettelu: "keskitetty", paletti: "metsa", fontti: "juhlava", kuvio: "lumi", kuvioSij: "kuvio", kuvioKoko: "normaali", nimi: "Hyvää joulua", ala: "Perhe Virtanen", pvm: "2026", lisa: "", jae: "", viite: "" },
      muisto: { asettelu: "keskitetty", paletti: "hiili", fontti: "klassinen", kuvio: "oliivi", kuvioSij: "yla", kuvioKoko: "normaali", nimi: "Eino Virtanen", ala: "Rakkaudella muistaen", pvm: "1948–2026", lisa: "", jae: "Herra on minun paimeneni, ei minulta mitään puutu.", viite: "Ps. 23:1" },
      kaste: { asettelu: "keskitetty", paletti: "meri", fontti: "leikkisa", kuvio: "kala", kuvioSij: "yla", kuvioKoko: "normaali", nimi: "Eero", ala: "Kastettu", pvm: "12.4.2026", lisa: "Ylivieskan kirkko", jae: "Älä pelkää, sillä minä olen lunastanut sinut, minä olen kutsunut sinut nimeltä; sinä olet minun.", viite: "Jes. 43:1" },
    },
    kartta: {
      helsinki: { lat: 60.1699, lon: 24.9384, sade: 2.2, teema: "klassinen", muoto: "koko", reunus: "valja", tekstiSij: "alla", otsikko: "Helsinki", ala: "Suomi", koord: "", jae: "", viite: "", fontti: "moderni", kuvio: "ei", paksuus: "normaali" },
      ylivieska: { lat: 64.0736, lon: 24.5341, sade: 1.8, teema: "yo", muoto: "ympyra", reunus: "valja", tekstiSij: "alla", otsikko: "Ylivieska", ala: "Koti", koord: "", jae: "", viite: "", fontti: "juhlava", kuvio: "ei", paksuus: "normaali" },
      betlehem: { lat: 31.7049, lon: 35.2023, sade: 1.3, teema: "hiekka", muoto: "pyorea", reunus: "valja", tekstiSij: "alla", otsikko: "Betlehem", ala: "", koord: "", jae: "Sillä teille on tänä päivänä syntynyt Vapahtaja, joka on Kristus, Herra, Daavidin kaupungissa.", viite: "Luuk. 2:11", fontti: "juhlava", kuvio: "tahti", kuvioSij: "yla", paksuus: "normaali" },
      tampere: { lat: 61.4981, lon: 23.761, sade: 2.2, teema: "ruusu", muoto: "sydan", reunus: "valja", tekstiSij: "alla", otsikko: "Tampere", ala: "Täällä kaikki alkoi", koord: "", jae: "", viite: "", fontti: "elegantti", kuvio: "ei", paksuus: "normaali" },
    },
  };
  try { const e = new URLSearchParams(location.search).get("esim"); const ex = e && (ESIMERKIT[MALLI] || {})[e]; if (ex) S = { ...OLETUS, tuote: S.tuote, koko: S.koko, vari: S.vari, ...ex, kuvioValittu: true }; } catch {}
  // Tallennettu tila tarkistetaan: rikkinäinen tai vanha tallennus ei saa kaataa sivua.
  function puhdista(x) {
    const o = { ...OLETUS };
    for (const k of Object.keys(OLETUS)) if (x && x[k] !== undefined && typeof x[k] === typeof OLETUS[k]) o[k] = x[k];
    if (x && x.kuvioValittu) o.kuvioValittu = true;
    const fontit = Object.fromEntries(FONTIT.map((f) => [f.id, 1])), kuviot = { ei: 1, ...KV.K };
    const enumit = MALLI === "kartta" ? { teema: KA.TEEMAT, muoto: KARTTAMUODOT, reunus: REUNUKSET, tekstiSij: TEKSTISIJ, paksuus: PAKSUUS, fontti: fontit, kuvio: kuviot, kuvioSij: KV.SIJAINNIT, kuvioKoko: KV.KOOT }
      : { asettelu: ASETTELUT, paletti: PALETIT, fontti: fontit, kuvio: kuviot, kuvioSij: KV.SIJAINNIT, kuvioKoko: KV.KOOT };
    for (const [k, m] of Object.entries(enumit)) if (!Object.prototype.hasOwnProperty.call(m, o[k])) o[k] = OLETUS[k];
    if (!["pysty", "vaaka"].includes(o.suunta)) o.suunta = "pysty";
    if (!C.tuotteet[o.tuote] || !C.tuotteet[o.tuote].koot[o.koko]) { o.tuote = OLETUS.tuote; o.koko = OLETUS.koko; }
    if (!C.tuotteet.kehys.varit[o.vari]) o.vari = Object.keys(C.tuotteet.kehys.varit)[0];
    if (MALLI === "kartta") { if (!isFinite(o.lat) || Math.abs(o.lat) > 85 || !isFinite(o.lon) || Math.abs(o.lon) > 180) { o.lat = OLETUS.lat; o.lon = OLETUS.lon; } o.sade = Math.min(16, Math.max(0.4, +o.sade || OLETUS.sade)); }
    return o;
  }
  S = puhdista(S);
  const tallenna = () => { try { localStorage.setItem(AVAIN, JSON.stringify(S)); } catch {} };

  const tuote = () => C.tuotteet[S.tuote];
  const koko = () => tuote().koot[S.koko];
  const hinta = () => koko().hinta;
  const tuoteNimi = () => `${tuote().nimi} ${S.koko.replace("x", "×")} cm${S.tuote === "kehys" ? ", " + tuote().varit[S.vari].nimi.toLowerCase() : ""}, ${S.suunta === "vaaka" ? "vaaka" : "pysty"}`;
  const nakyva = () => { const [a, b] = koko().mm; return S.suunta === "vaaka" ? [b, a] : [a, b]; };
  const fontti = () => FONTIT.find((f) => f.id === S.fontti) || FONTIT[0];

  // ---------- Fonttien lataus canvasia varten ----------
  const ladatut = new Set();
  function varmistaFontit(f) {
    const tarve = [`${f.ow} 40px "${f.o}"`, `${f.tw} 40px "${f.t}"`].filter((x) => !ladatut.has(x));
    if (!tarve.length || !document.fonts) return null;
    return Promise.all(tarve.map((x) => document.fonts.load(x, "AaÄäÖö").then(() => ladatut.add(x)).catch(() => ladatut.add(x))));
  }

  // ---------- Tekstimoottori ----------
  const fnt = (it, px, f) => `${it.perhe === "o" ? f.ow : f.tw} ${px}px "${it.perhe === "o" ? f.o : f.t}", Georgia, serif`;
  function rivita(c, t, maxW) {
    const ulos = [];
    for (const kpl of t.split("\n")) { let r = ""; for (const s of kpl.split(/\s+/).filter(Boolean)) { const k = r ? r + " " + s : s; if (c.measureText(k).width > maxW && r) { ulos.push(r); r = s; } else r = k; } ulos.push(r); }
    return ulos;
  }
  function mittaa(c, it, maxW, u, f) {
    if (it.k !== "t") return;
    let teksti = String(it.teksti || "").trim(); if (!teksti) { it.h = 0; it.tyhja = true; return; }
    const isot = it.isot && !(it.perhe === "o" && f.kasi);
    if (isot) teksti = teksti.toLocaleUpperCase("fi");
    let px = it.koko * u * (it.perhe === "o" ? f.kerroin || 1 : 1);
    const vali = isot ? (it.vali ?? (it.perhe === "o" ? f.vali || 0.06 : 0.14)) : 0;
    for (let n = 0; n < 60; n++) {
      c.font = fnt(it, px, f); if ("letterSpacing" in c) c.letterSpacing = vali * px + "px";
      const rivit = it.wrap ? rivita(c, teksti, maxW) : teksti.split("\n");
      const lev = Math.max(...rivit.map((r) => c.measureText(r).width));
      if ((lev <= maxW && (!it.maxRivit || rivit.length <= it.maxRivit)) || px < 3) { it.rivit = rivit; break; }
      px *= 0.94;
    }
    it.px = px; it.vali = vali; it.rv = it.rivivali || (it.perhe === "o" ? (f.kasi ? 1.3 : 1.12) : 1.35); it.h = it.rivit.length * px * it.rv;
  }
  function piirraTeksti(c, it, x, y, f, tasaus) {
    c.font = fnt(it, it.px, f); if ("letterSpacing" in c) c.letterSpacing = it.vali * it.px + "px";
    c.fillStyle = it.vari; c.textAlign = tasaus; c.textBaseline = "middle";
    it.rivit.forEach((r, i) => c.fillText(r, x, y + it.px * it.rv * (i + 0.5)));
    if ("letterSpacing" in c) c.letterSpacing = "0px";
  }
  // Pino: kohteet piirretään pystysuunnassa alueeseen [y0, y1]
  function pino(c, kohteet, alue, f, u, tasaus = "center", sijainti = "keski") {
    const maxW = alue.w; kohteet = kohteet.filter(Boolean);
    kohteet.forEach((it) => mittaa(c, it, maxW, u, f));
    kohteet = kohteet.filter((it) => !it.tyhja);
    const kork = (it) => (it.k === "t" ? it.h : it.k === "vali" ? it.h * u : it.k === "motiivi" ? it.s : it.k === "viiva" ? u * 3 : it.k === "sydanviiva" ? u * 7 : it.k === "lista" ? it.h : it.k === "tilastot" ? u * 13 : 0);
    kohteet.forEach((it) => { if (it.k === "lista") { const n = it.rivit.length, sar = n > 5 ? 2 : 1, rivit = Math.ceil(n / sar); it.sar = sar; it.px = it.koko * u * (sar === 2 ? 0.9 : 1); it.h = rivit * it.px * 1.55; } });
    // poista peräkkäiset tyhjät välit
    const tot = kohteet.reduce((a, it) => a + kork(it), 0);
    let y = sijainti === "ala" ? alue.y + alue.h - tot : sijainti === "yla" ? alue.y : alue.y + (alue.h - tot) / 2;
    const x = tasaus === "left" ? alue.x : alue.x + alue.w / 2;
    for (const it of kohteet) {
      const kh = kork(it);
      if (it.k === "t") piirraTeksti(c, it, x, y, f, tasaus);
      else if (it.k === "motiivi") KV.yksi(c, it.id, tasaus === "left" ? alue.x + it.s / 2 : x, y + kh / 2, it.s, it.v);
      else if (it.k === "viiva") { c.fillStyle = it.vari; const w = it.w * u; c.fillRect(tasaus === "left" ? alue.x : x - w / 2, y + kh / 2 - u * 0.15, w, u * 0.3); }
      else if (it.k === "sydanviiva") { c.strokeStyle = it.vari; c.lineWidth = u * 0.25; const w = u * 22; c.beginPath(); c.moveTo(x - w, y + kh / 2); c.lineTo(x - u * 3.2, y + kh / 2); c.moveTo(x + u * 3.2, y + kh / 2); c.lineTo(x + w, y + kh / 2); c.stroke();
        c.fillStyle = it.vari2; c.beginPath(); KV.sydan(c, x, y + kh / 2 + u * 0.2, u * 4.4); c.fill(); }
      else if (it.k === "lista") { c.font = `${f.tw} ${it.px}px "${f.t}", Georgia, serif`; c.fillStyle = it.vari; c.textBaseline = "middle"; c.textAlign = "center";
        const rivit = Math.ceil(it.rivit.length / it.sar), lev = alue.w / it.sar;
        it.rivit.forEach((r, i) => { const s = Math.floor(i / rivit), rr = i % rivit; c.fillText(r, alue.x + lev * (s + 0.5), y + it.px * 1.55 * (rr + 0.5), lev * 0.95); }); }
      else if (it.k === "tilastot") { const arvot = it.arvot.filter((a) => a[1]); const lev = alue.w / Math.max(1, arvot.length);
        arvot.forEach(([ots, arvo], i) => { const cx = alue.x + lev * (i + 0.5);
          c.textAlign = "center"; c.textBaseline = "middle"; c.fillStyle = it.vari2; c.font = `${f.tw} ${u * 2.3}px "${f.t}", Georgia, serif`; if ("letterSpacing" in c) c.letterSpacing = u * 0.35 + "px";
          c.fillText(ots.toLocaleUpperCase("fi"), cx, y + u * 3.5); if ("letterSpacing" in c) c.letterSpacing = "0px";
          c.fillStyle = it.vari; c.font = `${f.ow} ${u * 4.6 * (f.kerroin || 1)}px "${f.o}", Georgia, serif`; c.fillText(arvo, cx, y + u * 8.4, lev * 0.92);
          if (i) { c.fillStyle = it.vari2; c.fillRect(alue.x + lev * i - u * 0.1, y + u * 2, u * 0.2, u * 9); } }); }
      y += kh;
    }
  }

  // ---------- Nimijulisteen piirto ----------
  function piirraNimi(c, W, H) {
    const p = PALETIT[S.paletti] || PALETIT.kerma, f = fontti(), u = W / 100, v = { a: p.a, i: p.i, s: p.s, b: p.b };
    c.fillStyle = p.b; c.fillRect(0, 0, W, H);
    const kuvio = S.kuvio !== "ei" && KV.K[S.kuvio], sij = S.kuvioSij, kk = (KV.KOOT[S.kuvioKoko] || KV.KOOT.normaali)[1];
    if (kuvio && !["yla", "ala"].includes(sij)) KV.sivulle(c, S.kuvio, sij, S.kuvioKoko, W, H, v);
    const vaaka = W > H, mot = (kuvio && (sij === "yla" || sij === "ala")) ? { k: "motiivi", id: S.kuvio, s: Math.min(W, H) * 0.24 * kk, v } : null;
    const T = (teksti, perhe, koko, vari, lisa = {}) => ({ k: "t", teksti, perhe, koko, vari, ...lisa });
    const isot = S.isot || f.isot;
    const N = (koko = 13) => T(S.nimi, "o", koko * (vaaka ? 0.8 : 1), p.i, { isot, wrap: false });
    const ala = (koko = 3.8) => T(S.ala, "t", koko, p.a, { isot: true, wrap: true, maxRivit: 2 });
    const pvm = (koko = 3.6) => T(S.pvm, "t", koko, p.i, { wrap: true, maxRivit: 2 });
    const lisa = (koko = 3.2) => T(S.lisa, "t", koko, p.i, { wrap: true, maxRivit: 3 });
    const jae = (koko = 3.1) => S.jae ? [{ k: "vali", h: 3 }, T(S.jae, "t", koko, p.i, { wrap: true, maxRivit: 6 }), T(S.viite, "t", koko * 0.8, p.a, { isot: true })] : [];
    const vali = (x) => ({ k: "vali", h: x });
    let m = (vaaka ? H : W) * 0.11, my = 0, tasaus = "center", sijainti = "keski", k = [];
    // Kulma- ja reunuskuviot vievät tilaa: pidä teksti niiden sisäpuolella
    const D = Math.min(W, H);
    if (sij === "reunus" && kuvio) m = Math.max(m, D * 0.045 + D * 0.055 * kk + D * 0.04);
    if (sij === "kulmat" && kuvio) { m *= 1.15; my = D * 0.06 + D * 0.17 * kk + D * 0.03; }
    switch (S.asettelu) {
      case "sydanviiva": k = [N(), vali(3), { k: "sydanviiva", vari: p.i, vari2: p.a }, vali(3), pvm(4), vali(1.5), ala(), lisa(), ...jae()]; break;
      case "minimal": tasaus = "left"; sijainti = "ala"; k = [ala(3.2), vali(1), N(11), vali(1), { k: "viiva", w: 14, vari: p.a }, vali(1), pvm(3.4), lisa(), ...jae()]; break;
      case "perhe": { const lista = String(S.jasenet || "").split("\n").map((x) => x.trim()).filter(Boolean).slice(0, 14);
        k = [N(9), vali(1), ala(), vali(4), lista.length ? { k: "lista", rivit: lista, koko: 4.4, vari: p.i } : null, vali(4), { k: "viiva", w: 10, vari: p.a }, vali(3), pvm(3.4), lisa(), ...jae()]; break; }
      case "kehys": { m *= 1.25; c.strokeStyle = p.a; c.lineWidth = u * 0.35; const r1 = W * 0.05, r2 = W * 0.065; c.strokeRect(r1, r1, W - 2 * r1, H - 2 * r1); c.lineWidth = u * 0.15; c.strokeRect(r2, r2, W - 2 * r2, H - 2 * r2);
        k = [N(12), vali(2), ala(), vali(3), pvm(), lisa(), ...jae()]; break; }
      case "monogrammi": { const kir = (S.nimi || "").trim().charAt(0).toLocaleUpperCase("fi");
        if (kir) { c.save(); c.font = `${f.ow} ${Math.min(W, H) * 0.78}px "${f.o}", Georgia, serif`; c.textAlign = "center"; c.textBaseline = "middle"; c.fillStyle = p.s; c.fillText(kir, W / 2, H * 0.45); c.restore(); }
        sijainti = "ala"; k = [N(12), vali(1.5), ala(), vali(2), pvm(), lisa(), ...jae()]; break; }
      case "vauva": k = [ala(3.6), vali(2), N(15), vali(2), pvm(4), vali(4), { k: "tilastot", arvot: [["Paino", S.paino], ["Pituus", S.pituus], ["Kello", S.klo]], vari: p.i, vari2: p.a }, vali(3), lisa(), ...jae()]; break;
      case "haat": k = [N(12), vali(3), ala(), vali(2), { k: "viiva", w: 12, vari: p.a }, vali(2), pvm(4.4), vali(1), lisa(), ...jae()]; break;
      case "jae": k = [T(S.jae, "o", 6.2, p.i, { wrap: true, maxRivit: 8, rivivali: f.kasi ? 1.35 : 1.25 }), vali(2.5), T(S.viite, "t", 3.2, p.a, { isot: true }), vali(6), T(S.nimi, "t", 3.6, p.i, { isot: true }), pvm(3.2), lisa(3), ala(3)]; break;
      default: k = [N(), vali(2.5), ala(), vali(4), pvm(), vali(1), lisa(), ...jae()];
    }
    if (mot) { if (sij === "yla") k.unshift(mot, vali(4)); else k.push(vali(4), mot); }
    my = Math.max(my, m);
    pino(c, k, { x: m, y: my, w: W - 2 * m, h: H - 2 * my }, f, u, tasaus, sijainti);
  }

  // ---------- Karttajulisteen piirto ----------
  let kartta = null, karttaNakyma = null;
  function karttaAlue(W, H) {
    const m = { valja: 0.075, kapea: 0.035, ei: 0 }[S.reunus] * Math.min(W, H);
    const tekstiH = S.tekstiSij === "alla" ? H * (S.jae ? 0.23 : 0.19) : 0;
    let a = { x: m, y: m, w: W - 2 * m, h: H - 2 * m - tekstiH + (S.reunus === "ei" && tekstiH ? 0 : 0) };
    if (S.tekstiSij === "alla" && m === 0) a.h = H - tekstiH;
    let muoto = { ...a };
    if (S.muoto === "ympyra" || S.muoto === "sydan") { const d = Math.min(a.w, a.h) * (S.muoto === "sydan" ? 0.98 : 0.94); muoto = { x: a.x + (a.w - d) / 2, y: a.y + (a.h - d) / 2, w: d, h: d }; }
    return { m, tekstiH, a, muoto };
  }
  function polkuMuoto(c, r) {
    c.beginPath();
    if (S.muoto === "ympyra") c.arc(r.x + r.w / 2, r.y + r.h / 2, r.w / 2, 0, 2 * Math.PI);
    else if (S.muoto === "sydan") { const x = r.x + r.w / 2, y = r.y, w = r.w, hh = r.h;
      c.moveTo(x, y + hh * 0.98); c.bezierCurveTo(x - w * 0.62, y + hh * 0.55, x - w * 0.52, y - hh * 0.05, x, y + hh * 0.22); c.bezierCurveTo(x + w * 0.52, y - hh * 0.05, x + w * 0.62, y + hh * 0.55, x, y + hh * 0.98); }
    else if (S.muoto === "pyorea") { const rr = Math.min(r.w, r.h) * 0.07; c.roundRect ? c.roundRect(r.x, r.y, r.w, r.h, rr) : c.rect(r.x, r.y, r.w, r.h); }
    else c.rect(r.x, r.y, r.w, r.h);
  }
  function piirraKartta(c, W, H) {
    const t = KA.TEEMAT[S.teema] || KA.TEEMAT.klassinen, f = fontti(), u = W / 100, L = karttaAlue(W, H);
    c.fillStyle = t.bg; c.fillRect(0, 0, W, H);
    c.save(); polkuMuoto(c, L.muoto); c.clip();
    KA.piirra(c, kartta, { lat: S.lat, lon: S.lon, sade: S.sade }, L.muoto, t, PAKSUUS[S.paksuus][1]);
    c.restore();
    if (S.muoto !== "koko" || L.m > 0) { c.save(); c.strokeStyle = t.tie; c.globalAlpha = 0.85; c.lineWidth = u * 0.18; polkuMuoto(c, L.muoto); c.stroke(); c.restore(); }
    const v = { a: t.korostus, i: t.teksti, s: t.vesi, b: t.bg };
    if (S.kuvio !== "ei" && KV.K[S.kuvio] && ["kulmat", "reunus"].includes(S.kuvioSij)) KV.sivulle(c, S.kuvio, S.kuvioSij, S.kuvioKoko, W, H, v);
    const koord = S.koord || KA.koordinaatit(S.lat, S.lon);
    const T = (teksti, perhe, koko, vari, lisa = {}) => ({ k: "t", teksti, perhe, koko, vari, ...lisa });
    const kk = (KV.KOOT[S.kuvioKoko] || KV.KOOT.normaali)[1];
    const mot = S.kuvio !== "ei" && KV.K[S.kuvio] && S.kuvioSij === "yla" ? [{ k: "motiivi", id: S.kuvio, s: u * 7 * kk, v }, { k: "vali", h: 1.5 }] : [];
    const kohteet = [...mot, T(S.otsikko, "o", 9.5, t.teksti, { isot: true, vali: f.kasi ? 0 : 0.22 }), { k: "vali", h: 1.2 }, T(S.ala, "t", 3.2, t.teksti, { isot: true, vali: 0.3 }), { k: "vali", h: 1.6 },
      T(koord, "t", 2.4, t.korostus, { isot: false }), ...(S.jae ? [{ k: "vali", h: 1.6 }, T(S.jae, "t", 2.5, t.teksti, { wrap: true, maxRivit: 3 }), T(S.viite, "t", 2.1, t.korostus, { isot: true })] : [])];
    if (S.tekstiSij === "alla") pino(c, kohteet, { x: L.m + u * 3, y: L.a.y + L.a.h + u * 1, w: W - 2 * L.m - u * 6, h: L.tekstiH - u * 1 - Math.max(L.m * 0.4, u * 2.5) }, f, u);
    else if (S.tekstiSij === "paalla") {
      const bh = H * (S.jae ? 0.27 : 0.22), y0 = L.a.y + L.a.h - bh;
      c.save(); polkuMuoto(c, L.muoto); c.clip(); const g = c.createLinearGradient(0, y0, 0, y0 + bh * 0.45); g.addColorStop(0, t.bg + "00"); g.addColorStop(1, t.bg + "f2"); c.fillStyle = g; c.fillRect(L.a.x, y0, L.a.w, bh); c.restore();
      if (S.muoto !== "koko") { c.fillStyle = t.bg + "e6"; c.fillRect(L.a.x, y0 + bh * 0.3, L.a.w, bh * 0.7); }
      pino(c, kohteet, { x: L.a.x + u * 4, y: y0 + bh * 0.3, w: L.a.w - u * 8, h: bh * 0.66 }, f, u);
    }
    // ODbL-lähdemerkintä
    c.save(); c.font = `400 ${u * 1.25}px "Nunito Sans", Arial, sans-serif`; c.textAlign = "right"; c.textBaseline = "bottom"; c.fillStyle = t.teksti; c.globalAlpha = 0.7;
    const am = Math.max(L.m * 0.35, u * 1.8);
    if (L.m === 0 && S.tekstiSij !== "alla") { const tw = c.measureText("© OpenStreetMap contributors").width; c.globalAlpha = 0.75; c.fillStyle = t.bg; c.fillRect(W - am - tw - u * 0.8, H - am - u * 2, tw + u * 1.6, u * 2.4); c.fillStyle = t.teksti; }
    c.fillText("© OpenStreetMap contributors", W - am, H - am); c.restore();
  }

  const piirraSuunnitelma = (c, W, H) => (MALLI === "kartta" ? piirraKartta(c, W, H) : piirraNimi(c, W, H));

  // ---------- Esikatselu (kehystetty mockup seinällä) ----------
  const cv = $("#cv"), taulu = $("#taulu"), seina = $("#seina");
  let rafId = 0, historia = [], edellinen = "", histAjastin = 0, pikkuAjastin = 0;
  function paivita() {
    tallenna(); kirjaaHistoria(); paivitaHinta();
    if (!rafId) rafId = requestAnimationFrame(() => { rafId = 0; piirraEsikatselu(); });
    clearTimeout(pikkuAjastin); pikkuAjastin = setTimeout(piirraPikkukuvat, 350);
  }
  function kirjaaHistoria() {
    clearTimeout(histAjastin);
    histAjastin = setTimeout(() => { const j = JSON.stringify(S); if (j !== edellinen) { if (edellinen) historia.push(edellinen); if (historia.length > 40) historia.shift(); edellinen = j; const k = $("#kumoa"); if (k) k.disabled = !historia.length; } }, 450);
  }
  function asetaTila(uusi) { Object.keys(S).forEach((k) => delete S[k]); Object.assign(S, puhdista(uusi)); }
  function kumoa() { const j = historia.pop(); if (!j) return; edellinen = j; asetaTila(JSON.parse(j)); rakennaOhjaimet(); paivita(); varmistaKartta(); $("#kumoa").disabled = !historia.length; }
  function alusta() {
    if (!confirm("Aloitetaanko alusta? Nykyinen suunnitelma korvataan oletuksella.")) return;
    try { localStorage.removeItem(AVAIN); } catch {}
    asetaTila({ ...OLETUS }); delete S.kuvioValittu; rakennaOhjaimet(); paivita(); varmistaKartta();
  }
  function piirraEsikatselu() {
    const f = fontti(), lupaus = varmistaFontit(f); if (lupaus) lupaus.then(() => paivita());
    const [vw, vh] = nakyva(), tila = seina.getBoundingClientRect();
    const kehysMm = S.tuote === "kehys" ? (S.koko === "30x40" ? 12 : 14) : 0, kerroin = 1 + (2 * kehysMm) / vw;
    const reuna = Math.max(18, Math.min(tila.width, tila.height) * 0.08);
    const maxW = Math.max(100, tila.width - 2 * reuna), maxH = Math.max(120, tila.height - 2 * reuna);
    let w = maxW / kerroin, hh = (w * vh) / vw; if (hh * kerroin > maxH) { hh = maxH / kerroin; w = (hh * vw) / vh; }
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = Math.round(w * dpr); cv.height = Math.round(hh * dpr); cv.style.width = w + "px"; cv.style.height = hh + "px";
    taulu.className = "taulu " + S.tuote;
    taulu.style.setProperty("--kehys", S.tuote === "kehys" ? tuote().varit[S.vari].css : "transparent");
    taulu.style.setProperty("--kp", S.tuote === "kehys" ? (w * (kerroin - 1)) / 2 + "px" : "0px");
    const c = cv.getContext("2d"); c.setTransform(1, 0, 0, 1, 0, 0); c.scale(cv.width / w, cv.height / hh);
    piirraSuunnitelma(c, w, hh);
  }
  addEventListener("resize", paivita);

  // ---------- Painotiedosto ----------
  function painoMitat() {
    const [vw, vh] = nakyva(), r = tuote().reuna, fw = vw + 2 * r, fh = vh + 2 * r;
    let k = C.dpi / 25.4; if (fw * k * fh * k > C.maxPikselit) k = Math.sqrt(C.maxPikselit / (fw * fh));
    return { vw, vh, r, fw, fh, k, W: Math.round(fw * k), H: Math.round(fh * k), dpi: Math.round(k * 25.4) };
  }
  async function painoKuva() {
    await (varmistaFontit(fontti()) || Promise.resolve());
    if (MALLI === "kartta") await odotaKartta();
    const m = painoMitat(), cnv = document.createElement("canvas"); cnv.width = m.W; cnv.height = m.H;
    const c = cnv.getContext("2d");
    const bg = MALLI === "kartta" ? (KA.TEEMAT[S.teema] || KA.TEEMAT.klassinen).bg : (PALETIT[S.paletti] || PALETIT.kerma).b;
    c.fillStyle = bg; c.fillRect(0, 0, m.W, m.H);
    c.translate(m.r * m.k, m.r * m.k); piirraSuunnitelma(c, m.vw * m.k, m.vh * m.k);
    const blob = await new Promise((ok) => cnv.toBlob(ok, "image/jpeg", 0.93));
    cnv.width = cnv.height = 1;
    return { blob, ...m };
  }
  async function esikuva(leveys = 1000, laatu = 0.86) {
    await (varmistaFontit(fontti()) || Promise.resolve()); if (document.fonts) await document.fonts.ready;
    if (MALLI === "kartta") await odotaKartta();
    const [vw, vh] = nakyva(), c = document.createElement("canvas"); c.width = leveys; c.height = Math.round((leveys * vh) / vw);
    piirraSuunnitelma(c.getContext("2d"), c.width, c.height);
    return c.toDataURL("image/jpeg", laatu);
  }

  // ---------- Kartan data: lataus Workerin kautta, selkeä tila ja aikaraja ----------
  let lataus = null, latausAjastin = 0;
  const latausEl = $("#lataus");
  function naytaLataus(teksti, virhe) {
    if (!latausEl) return; latausEl.hidden = !teksti; latausEl.innerHTML = "";
    latausEl.classList.toggle("virhe", !!virhe);
    if (teksti) latausEl.append(virhe ? "" : h("span", { class: "pyora", "aria-hidden": "true" }), h("span", {}, teksti),
      virhe ? h("button", { type: "button", class: "nappi pieni", on: { click: () => varmistaKartta(true) } }, "Yritä uudelleen") : "");
  }
  function varmistaKartta(heti) {
    if (MALLI !== "kartta") return;
    const n = { lat: S.lat, lon: S.lon, sade: S.sade };
    if (KA.kattaa(kartta, n)) { naytaLataus(""); return; }
    clearTimeout(latausAjastin);
    latausAjastin = setTimeout(async () => {
      if (lataus) { lataus.ac.abort(); clearTimeout(lataus.hidas); }
      const ac = new AbortController(), oma = { ac, n }; lataus = oma;
      naytaLataus("Ladataan karttaa…");
      oma.hidas = setTimeout(() => { if (lataus === oma) naytaLataus("Ladataan karttaa… ison alueen aineisto voi viedä hetken."); }, 9000);
      oma.hidas2 = setTimeout(() => { if (lataus === oma) naytaLataus("Karttapalvelu on juuri nyt hidas. Yritetään edelleen…"); }, 35000);
      let d = null;
      for (let yritys = 0; yritys < 1 && !d; yritys++) {
        try { d = await KA.lataa(n.lat, n.lon, n.sade, ac.signal); }
        catch (e) { if (ac.signal.aborted && lataus !== oma) return; if (yritys === 0) await new Promise((r) => setTimeout(r, 1500)); }
      }
      clearTimeout(oma.hidas); clearTimeout(oma.hidas2);
      if (lataus !== oma) return;
      lataus = null;
      if (d) { kartta = d; naytaLataus(""); paivita(); } else naytaLataus("Kartan lataus ei onnistunut. Tarkista yhteys ja yritä uudelleen.", true);
    }, heti ? 0 : 700);
  }
  async function odotaKartta() {
    const n = { lat: S.lat, lon: S.lon, sade: S.sade };
    if (KA.kattaa(kartta, n)) return;
    kartta = await KA.lataa(n.lat, n.lon, n.sade); paivita();
  }

  // ---------- Ohjaimet ----------
  const ohj = $("#ohj");
  function osio(otsikko, auki, ...sis) { return h("details", { class: "osio", open: auki }, h("summary", {}, h("span", {}, otsikko)), h("div", { class: "osio-sis" }, ...sis)); }
  function kentta(nimi, avain, tyyppi = "text", lisa = {}) {
    const id = "k-" + avain;
    const inp = tyyppi === "textarea" ? h("textarea", { id, rows: lisa.rivit || 3, maxlength: lisa.max || 400, placeholder: lisa.ph || "" }) : h("input", { id, type: tyyppi, maxlength: lisa.max || 80, placeholder: lisa.ph || "", autocomplete: "off", enterkeyhint: "done" });
    inp.value = S[avain] ?? "";
    inp.addEventListener("input", () => { S[avain] = inp.value; paivita(); });
    return h("label", { class: "kentta", "data-kentta": avain }, h("span", {}, nimi), inp, lisa.vihje ? h("small", {}, lisa.vihje) : null);
  }
  function valinta(nimi, avain, vaihtoehdot, opts = {}) {
    const ryhma = h("div", { class: "valinnat" + (opts.luokka ? " " + opts.luokka : ""), role: "radiogroup", "aria-label": nimi });
    const piirto = () => { ryhma.innerHTML = ""; for (const [arvo, sisalto] of vaihtoehdot()) {
      const b = h("button", { type: "button", role: "radio", class: "valinta", "aria-checked": String(S[avain] === arvo), "data-arvo": arvo,
        on: { click: () => { S[avain] = arvo; opts.muutos && opts.muutos(arvo); ryhma.querySelectorAll(".valinta").forEach((x) => x.setAttribute("aria-checked", String(x.dataset.arvo === arvo))); paivita(); } } });
      typeof sisalto === "string" ? (b.textContent = sisalto) : b.append(sisalto); ryhma.append(b); } };
    piirto(); ryhma._piirra = piirto;
    return h("div", { class: "ryhma", "data-ryhma": avain }, nimi ? h("div", { class: "ryhma-otsikko" }, nimi) : null, ryhma);
  }
  const piirraRyhma = (avain) => { const r = document.querySelector(`[data-ryhma="${avain}"] .valinnat`); if (r && r._piirra) r._piirra(); };
  function kuvioKuva(id, v) { const k = h("canvas", { width: 96, height: 96, class: "kuvake" }); const c = k.getContext("2d"); c.fillStyle = v.b; c.fillRect(0, 0, 96, 96); if (id !== "ei") KV.yksi(c, id, 48, 48, 78, v); else { c.strokeStyle = v.i; c.globalAlpha = 0.35; c.lineWidth = 2; c.beginPath(); c.moveTo(30, 30); c.lineTo(66, 66); c.stroke(); } return k; }
  const varitNyt = () => { if (MALLI === "kartta") { const t = KA.TEEMAT[S.teema] || KA.TEEMAT.klassinen; return { a: t.korostus, i: t.teksti, s: t.vesi, b: t.bg }; } const p = PALETIT[S.paletti]; return { a: p.a, i: p.i, s: p.s, b: p.b }; };
  function kuvioOsat(sijainnit) {
    return [valinta("Kuvio", "kuvio", () => [["ei", h("span", { class: "kuvake-k" }, kuvioKuva("ei", varitNyt()), h("small", {}, "Ei kuviota"))], ...Object.entries(KV.K).map(([id, m]) => [id, h("span", { class: "kuvake-k" }, kuvioKuva(id, varitNyt()), h("small", {}, m.nimi))])],
      { luokka: "kuviot", muutos: () => { S.kuvioValittu = true; } }),
      valinta("Kuvion paikka", "kuvioSij", () => Object.entries(KV.SIJAINNIT).filter(([k]) => sijainnit.includes(k)), { luokka: "sirut" }),
      valinta("Kuvion koko", "kuvioKoko", () => Object.entries(KV.KOOT).map(([k, v]) => [k, v[0]]), { luokka: "segmentti" })];
  }
  // Pikkukuvat: asettelut piirretään oikeilla teksteillä ja väreillä
  function miniKuva(muutos, w = 84) {
    const [vw, vh] = nakyva(), hgt = Math.round((w * vh) / vw), k = h("canvas", { width: w * 2, height: hgt * 2, class: "mini", style: `width:${w}px;height:${hgt}px` });
    const vanha = {}; for (const a of Object.keys(muutos)) vanha[a] = S[a];
    Object.assign(S, muutos); try { const c = k.getContext("2d"); c.scale(2, 2); piirraSuunnitelma(c, w, hgt); } catch {} Object.assign(S, vanha);
    return k;
  }
  function piirraPikkukuvat() { if (MALLI === "nimi") piirraRyhma("asettelu"); }
  function tuoteOsio() {
    const tyyppiR = valinta("", "tuote", () => Object.entries(C.tuotteet).map(([k, t]) => [k, h("span", { class: "tuote-k" }, h("i", { class: "tuote-ikoni " + k, "aria-hidden": "true" }), h("b", {}, t.nimi), h("small", {}, "alk. " + euro(Math.min(...Object.values(t.koot).map((x) => x.hinta)))))]),
      { luokka: "tuotteet", muutos: () => { if (!tuote().koot[S.koko]) S.koko = Object.keys(tuote().koot)[0]; piirraRyhma("koko"); varit.hidden = S.tuote !== "kehys"; kuvausEl.textContent = tuote().kuvaus + "."; } });
    const kokoR = valinta("Koko", "koko", () => Object.entries(tuote().koot).map(([k, x]) => [k, h("span", { class: "koko-k" }, h("b", {}, k.replace("x", " × ") + " cm"), h("small", {}, euro(x.hinta)))]), { luokka: "segmentti" });
    const varit = valinta("Kehyksen väri", "vari", () => Object.entries(C.tuotteet.kehys.varit).map(([k, x]) => [k, h("span", { class: "savy-k" }, h("i", { style: `background:${x.css}` }), h("small", {}, x.nimi))]), { luokka: "savyt" });
    varit.hidden = S.tuote !== "kehys";
    const kuvausEl = h("p", { class: "vihje" }, tuote().kuvaus + ".");
    return osio("Tuote ja koko", true, tyyppiR, kuvausEl, kokoR, varit, valinta("Suunta", "suunta", () => [["pysty", "Pysty"], ["vaaka", "Vaaka"]], { luokka: "segmentti" }));
  }
  function pohjatOsio() {
    const lista = MALLI === "kartta" ? [["helsinki", "Helsinki"], ["ylivieska", "Ylivieska"], ["tampere", "Sydänkartta"], ["betlehem", "Betlehem"]]
      : [["perhe", "Perhe"], ["haat", "Häät"], ["vauva", "Vauva"], ["jae", "Raamatunlause"], ["joulu", "Joulu"], ["kaste", "Kaste"], ["muisto", "Muisto"]];
    const rulla = h("div", { class: "pohjat" }, ...lista.map(([id, nimi]) => h("button", { type: "button", class: "pohja", "data-pohja": id, on: { click: () => {
      const ex = ESIMERKIT[MALLI][id]; asetaTila({ ...S, ...ex, kuvioValittu: true }); S._edAsettelu = S.asettelu; rakennaOhjaimet(); paivita(); varmistaKartta(true);
      if (matchMedia("(max-width: 899px)").matches) scrollTo({ top: 0, behavior: "smooth" }); } } },
      h("img", { src: `/kuvat/${MALLI}-${id}.jpg`, alt: "", loading: "lazy", width: 1000, height: MALLI === "kartta" ? 1400 : 1333 }), h("span", {}, nimi))));
    return h("section", { class: "pohjat-osio" }, h("div", { class: "ryhma-otsikko" }, "Aloita valmiista pohjasta"), rulla);
  }

  function rakennaNimi() {
    const tekstit = osio("Tekstit", true,
      kentta("Nimi tai nimet", "nimi", "textarea", { rivit: 2, max: 80, vihje: "Rivinvaihto jakaa nimen kahdelle riville." }),
      kentta("Yläteksti", "ala", "text", { max: 70 }),
      kentta("Päivämäärä", "pvm", "text", { max: 40, ph: "esim. 14.6.2025" }),
      kentta("Lisärivi", "lisa", "text", { max: 90 }),
      kentta("Perheenjäsenet, yksi per rivi", "jasenet", "textarea", { rivit: 5, max: 300 }),
      h("div", { class: "rinnakkain", "data-kentta": "vauva" }, kentta("Paino", "paino", "text", { max: 14 }), kentta("Pituus", "pituus", "text", { max: 14 }), kentta("Kello", "klo", "text", { max: 10 })));
    const jaeValinta = h("select", { id: "jaevalinta", on: { change: (e) => { const j = JAKEET[+e.target.value]; if (!j || e.target.value === "") return; S.jae = j[0]; S.viite = j[1]; $("#k-jae").value = j[0]; $("#k-viite").value = j[1]; paivita(); } } },
      h("option", { value: "" }, "Valitse valmis jae"), ...JAKEET.map(([t, v], i) => h("option", { value: i }, `${v}: ${t.slice(0, 44)}${t.length > 44 ? "…" : ""}`)));
    const jae = osio("Raamatunlause", S.asettelu === "jae", h("label", { class: "kentta" }, h("span", {}, "Valmiit jakeet (Raamattu 1933/38)"), jaeValinta),
      kentta("Jae", "jae", "textarea", { rivit: 3, max: 260 }), kentta("Jaeviite", "viite", "text", { max: 30, ph: "esim. Ps. 23:1" }), h("p", { class: "vihje" }, "Jätä tyhjäksi, jos et halua jaetta."));
    const tyyli = osio("Muokkaa tyyliä", false,
      valinta("Asettelu", "asettelu", () => Object.entries(ASETTELUT).map(([k, a]) => [k, h("span", { class: "asettelu-k" }, miniKuva({ asettelu: k, ...(S.asettelu === k ? {} : {}) }, 66), h("small", {}, a.nimi))]), { luokka: "asettelut", muutos: vaihdaAsettelu }),
      valinta("Fontti", "fontti", () => FONTIT.map((f) => [f.id, h("span", { class: "fontti-k" }, h("b", { style: `font-family:'${f.o}';font-weight:${f.ow}` }, "Aino"), h("small", {}, f.nimi))]), { luokka: "fontit" }),
      valinta("Värit", "paletti", () => Object.entries(PALETIT).map(([k, p]) => [k, h("span", { class: "paletti-k" }, h("i", { style: `background:linear-gradient(135deg,${p.b} 0 50%,${p.a} 50% 75%,${p.i} 75%)` }), h("small", {}, p.nimi))]),
        { luokka: "paletit", muutos: () => piirraRyhma("kuvio") }),
      ...kuvioOsat(["yla", "ala", "tausta", "kuvio", "kulmat", "reunus"]),
      h("label", { class: "rasti" }, Object.assign(h("input", { type: "checkbox", on: { change: (e) => { S.isot = e.target.checked; paivita(); } } }), { checked: !!S.isot }), "Nimi isoilla kirjaimilla"));
    ohj.append(pohjatOsio(), tekstit, tuoteOsio(), tyyli, jae);
    nakyvyys();
  }
  function nakyvyys() {
    if (MALLI !== "nimi") return;
    const nayta = (k, ehto) => document.querySelectorAll(`[data-kentta="${k}"]`).forEach((e) => (e.hidden = !ehto));
    nayta("jasenet", S.asettelu === "perhe"); nayta("vauva", S.asettelu === "vauva");
  }
  function vaihdaAsettelu(uusi) {
    const vanha = ASETTELUT[S._edAsettelu || "keskitetty"] || ASETTELUT.keskitetty, a = ASETTELUT[uusi];
    for (const [k, v] of Object.entries(a.esim)) { const nyk = S[k] ?? ""; if (!nyk || nyk === (vanha.esim[k] ?? "")) { S[k] = v; const el = $("#k-" + k); if (el) el.value = v; } }
    for (const [k, v] of Object.entries(vanha.esim)) if (!(k in a.esim) && S[k] === v) { S[k] = ""; const el = $("#k-" + k); if (el) el.value = ""; }
    if (!S.kuvioValittu) { S.kuvio = a.kuvio; S.kuvioSij = a.kuvio === "koristekulma" ? "kulmat" : "yla"; piirraRyhma("kuvio"); piirraRyhma("kuvioSij"); }
    if (uusi === "jae") { const d = [...document.querySelectorAll("details.osio")].find((x) => x.querySelector("#k-jae")); if (d) d.open = true; }
    S._edAsettelu = uusi; nakyvyys();
  }

  function rakennaKartta() {
    const tulokset = h("div", { class: "tulokset", role: "list" });
    const hakuKentta = h("input", { type: "search", id: "haku", placeholder: "Kaupunki, kylä tai osoite", maxlength: 120, autocomplete: "off", enterkeyhint: "search" });
    const vainSuomi = Object.assign(h("input", { type: "checkbox", on: { change: (e) => { S.vainSuomi = e.target.checked; tallenna(); } } }), { checked: S.vainSuomi !== false });
    const asetaPaikka = (p, jae) => {
      S.lat = p.lat; S.lon = p.lon; S.sade = p.sade || S.sade; S.otsikko = p.nimi; S.ala = p.ala || ""; S.koord = "";
      if (jae !== undefined) { S.jae = jae ? p.jae || "" : ""; S.viite = jae ? p.viite || "" : ""; }
      ["otsikko", "ala", "koord", "jae", "viite"].forEach((k) => { const el = $("#k-" + k); if (el) el.value = S[k] || ""; });
      paivitaZoom(); paivita(); varmistaKartta(true);
      if (matchMedia("(max-width: 899px)").matches) scrollTo({ top: 0, behavior: "smooth" });
    };
    let hakuKaynnissa = false;
    const tee = async () => {
      const q = hakuKentta.value.trim(); if (q.length < 2 || hakuKaynnissa) return;
      hakuKentta.blur(); hakuKaynnissa = true; tulokset.innerHTML = ""; tulokset.append(h("p", { class: "vihje" }, "Haetaan…"));
      try {
        const r = await KA.hae(q, S.vainSuomi !== false); tulokset.innerHTML = "";
        if (!r.length) tulokset.append(h("p", { class: "vihje" }, S.vainSuomi !== false ? "Ei osumia Suomesta. Kokeile toista nimeä tai poista rajaus Vain Suomi." : "Ei osumia. Kokeile toista nimeä."));
        r.forEach((p) => tulokset.append(h("button", { type: "button", class: "tulos", role: "listitem", on: { click: () => { asetaPaikka(p, false); tulokset.innerHTML = ""; } } }, h("b", {}, p.nimi), h("small", {}, p.kuvaus))));
      } catch { tulokset.innerHTML = ""; tulokset.append(h("p", { class: "vihje" }, "Haku ei onnistunut juuri nyt. Yritä hetken päästä uudelleen.")); }
      hakuKaynnissa = false;
    };
    hakuKentta.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); tee(); } });
    const pikat = (lista, jae) => h("div", { class: "pikat" }, ...lista.map((p) => h("button", { type: "button", class: "pika", on: { click: () => asetaPaikka(p, jae) } }, p.nimi)));
    const zoom = h("input", { type: "range", min: 0, max: 100, step: 1, id: "zoom", "aria-label": "Alueen laajuus" });
    const zArvo = h("output", { class: "vihje" });
    const z2s = (z) => 0.4 * Math.pow(40, z / 100), s2z = (s) => (100 * Math.log(s / 0.4)) / Math.log(40);
    function paivitaZoom() { zoom.value = Math.round(s2z(S.sade)); zArvo.textContent = "Näkyvä alue noin " + (S.sade * 2).toFixed(S.sade < 2.5 ? 1 : 0).replace(".", ",") + " km"; }
    zoom.addEventListener("input", () => { S.sade = Math.round(z2s(+zoom.value) * 100) / 100; paivitaZoom(); paivita(); varmistaKartta(); });
    const askel = (dx, dy) => () => { const n = KA.siirra(S, dx, dy, 200); S.lat = n.lat; S.lon = n.lon; S.koord = ""; const el = $("#k-koord"); if (el) el.value = ""; paivita(); varmistaKartta(); };
    const zoomNappi = (k) => () => { S.sade = Math.min(16, Math.max(0.4, S.sade * k)); paivitaZoom(); paivita(); varmistaKartta(); };
    const paikka = osio("Paikka", true,
      h("div", { class: "hakurivi" }, hakuKentta, h("button", { type: "button", class: "nappi", on: { click: tee } }, "Hae")),
      h("label", { class: "rasti" }, vainSuomi, "Vain Suomi"), tulokset,
      h("div", { class: "ryhma-otsikko" }, "Suosittuja Suomessa"), pikat(KA.SUOMI, false),
      h("div", { class: "ryhma-otsikko" }, "Raamatun paikat"), pikat(KA.RAAMATTU, true),
      h("div", { class: "ryhma-otsikko" }, "Rajaus"),
      h("div", { class: "zoomrivi" }, h("button", { type: "button", class: "nappi pieni", "aria-label": "Kauemmas", on: { click: zoomNappi(1.25) } }, "−"), zoom, h("button", { type: "button", class: "nappi pieni", "aria-label": "Lähemmäs", on: { click: zoomNappi(0.8) } }, "+")), zArvo,
      h("div", { class: "nuolet" }, ...[["↑", 0, 20, "Ylös"], ["←", 20, 0, "Vasemmalle"], ["→", -20, 0, "Oikealle"], ["↓", 0, -20, "Alas"]].map(([t, x, y, l]) => h("button", { type: "button", class: "nappi pieni", "aria-label": l, on: { click: askel(x, y) } }, t))),
      h("p", { class: "vihje" }, "Voit myös siirtää karttaa vetämällä esikatselua."));
    paivitaZoom();
    const tekstit = osio("Tekstit", true, kentta("Otsikko", "otsikko", "text", { max: 40 }), kentta("Alaotsikko", "ala", "text", { max: 60 }),
      kentta("Koordinaatit", "koord", "text", { max: 60, ph: "Lasketaan automaattisesti" }),
      kentta("Jae tai oma lause", "jae", "textarea", { rivit: 2, max: 200 }), kentta("Jaeviite", "viite", "text", { max: 30 }));
    const tyyli = osio("Muokkaa tyyliä", false,
      valinta("Väriteema", "teema", () => Object.entries(KA.TEEMAT).map(([k, t]) => [k, h("span", { class: "paletti-k" }, h("i", { style: `background:linear-gradient(135deg,${t.bg} 0 50%,${t.vesi} 50% 75%,${t.tie} 75%)` }), h("small", {}, t.nimi))]),
        { luokka: "paletit", muutos: () => piirraRyhma("kuvio") }),
      valinta("Kartan muoto", "muoto", () => Object.entries(KARTTAMUODOT), { luokka: "segmentti" }),
      valinta("Tekstin paikka", "tekstiSij", () => Object.entries(TEKSTISIJ), { luokka: "segmentti" }),
      valinta("Reunus", "reunus", () => Object.entries(REUNUKSET), { luokka: "segmentti" }),
      valinta("Teiden paksuus", "paksuus", () => Object.entries(PAKSUUS).map(([k, v]) => [k, v[0]]), { luokka: "segmentti" }),
      valinta("Fontti", "fontti", () => FONTIT.map((f) => [f.id, h("span", { class: "fontti-k" }, h("b", { style: `font-family:'${f.o}';font-weight:${f.ow}` }, "Oulu"), h("small", {}, f.nimi))]), { luokka: "fontit" }),
      ...kuvioOsat(["yla", "kulmat", "reunus"]));
    ohj.append(pohjatOsio(), paikka, tekstit, tuoteOsio(), tyyli);
  }
  if (MALLI === "kartta") {
    let veto = null;
    cv.addEventListener("pointerdown", (e) => { veto = { x: e.clientX, y: e.clientY, lat: S.lat, lon: S.lon }; cv.setPointerCapture(e.pointerId); });
    cv.addEventListener("pointermove", (e) => { if (!veto) return; const L = karttaAlue(cv.clientWidth, cv.clientHeight);
      const n = KA.siirra({ lat: veto.lat, lon: veto.lon, sade: S.sade }, e.clientX - veto.x, e.clientY - veto.y, L.muoto.w); S.lat = n.lat; S.lon = n.lon; S.koord = ""; paivita(); });
    const loppu = () => { if (veto) { veto = null; const el = $("#k-koord"); if (el) el.value = ""; varmistaKartta(); } };
    cv.addEventListener("pointerup", loppu); cv.addEventListener("pointercancel", loppu);
    cv.style.touchAction = "none"; cv.style.cursor = "grab";
  }
  function rakennaOhjaimet() { ohj.innerHTML = ""; if (MALLI === "kartta") rakennaKartta(); else rakennaNimi(); }

  // ---------- Hinta, toimitusarvio ja tilaus ----------
  function arkipaivat(alku, n) { const d = new Date(alku); let k = 0; while (k < n) { d.setDate(d.getDate() + 1); if (d.getDay() % 6) k++; } return d; }
  function toimitusArvio() {
    const a = arkipaivat(new Date(), 8), b = arkipaivat(new Date(), 14);
    return a.getMonth() === b.getMonth() ? `${a.getDate()}.–${b.getDate()}.${b.getMonth() + 1}.` : `${a.getDate()}.${a.getMonth() + 1}.–${b.getDate()}.${b.getMonth() + 1}.`;
  }
  function paivitaHinta() {
    $("#hinta").textContent = euro(hinta()); $("#tuotenimi").textContent = tuoteNimi();
    const t = $("#toimitus"); if (t) t.textContent = "Perillä arviolta " + toimitusArvio();
  }
  function kuvaus() {
    if (MALLI === "kartta") return `Karttajuliste: ${S.otsikko} (${S.lat.toFixed(4)}, ${S.lon.toFixed(4)}), ${(S.sade * 2).toFixed(1)} km, teema ${KA.TEEMAT[S.teema].nimi}, muoto ${KARTTAMUODOT[S.muoto]}`;
    return `Nimijuliste: ”${(S.nimi || "").replace(/\n/g, " / ")}”, asettelu ${ASETTELUT[S.asettelu].nimi}, fontti ${fontti().nimi}, värit ${PALETIT[S.paletti].nimi}, kuvio ${S.kuvio === "ei" ? "ei" : KV.K[S.kuvio].nimi}`;
  }
  function tarkistettavat() {
    const r = MALLI === "kartta" ? [["Otsikko", S.otsikko], ["Alaotsikko", S.ala], ["Koordinaatit", S.koord || KA.koordinaatit(S.lat, S.lon)], ["Jae", S.jae], ["Jaeviite", S.viite]]
      : [["Nimi", S.nimi], ["Yläteksti", S.ala], ["Päivämäärä", S.pvm], ["Lisärivi", S.lisa], ...(S.asettelu === "perhe" ? [["Perheenjäsenet", S.jasenet]] : []),
        ...(S.asettelu === "vauva" ? [["Paino", S.paino], ["Pituus", S.pituus], ["Kello", S.klo]] : []), ["Jae", S.jae], ["Jaeviite", S.viite]];
    return r.filter(([, v]) => String(v || "").trim());
  }
  const kassa = $("#kassa"), lomake = $("#tilauslomake");
  async function avaaKassa() {
    kassa.hidden = false; document.body.classList.add("kassa-auki");
    $("#kassa-yht").textContent = `${tuoteNimi()} · ${euro(hinta())}`;
    $("#kassa-toimitus").textContent = "Perillä arviolta " + toimitusArvio() + " (8–14 arkipäivää)";
    const ul = $("#kassa-tekstit"); ul.innerHTML = ""; tarkistettavat().forEach(([k, v]) => ul.append(h("li", {}, h("span", {}, k), h("b", {}, String(v).replace(/\n/g, " / ")))));
    const img = $("#kassa-kuva"); img.removeAttribute("src"); img.className = "kassa-kuva " + S.tuote; img.style.setProperty("--kehys", S.tuote === "kehys" ? tuote().varit[S.vari].css : "transparent");
    $("#kassa .sulje").focus();
    try { img.src = await esikuva(700, 0.85); } catch { img.alt = "Esikatselu ei ole saatavilla"; }
  }
  function suljeKassa() { kassa.hidden = true; document.body.classList.remove("kassa-auki"); $("#jatka").focus(); }
  $("#jatka").addEventListener("click", avaaKassa);
  kassa.addEventListener("click", (e) => { if (e.target === kassa || e.target.closest(".sulje")) suljeKassa(); });
  addEventListener("keydown", (e) => { if (e.key === "Escape" && !kassa.hidden) suljeKassa(); });
  if (lomake) lomake.addEventListener("submit", async (e) => {
    e.preventDefault();
    const viesti = $("#lomakeviesti"), nappi = $("#maksa");
    const d = Object.fromEntries(new FormData(lomake).entries());
    const virhe = (t) => { viesti.textContent = t; viesti.className = "viesti virhe"; };
    if (!C.avoinna) return virhe("Tilaukset avautuvat pian. Suunnitelmasi on tallessa tällä laitteella.");
    if (!d.tarkistettu) return virhe("Tarkista tekstit ja rastita kohta “Tekstit ovat oikein”.");
    if (!/^\d{5}$/.test((d.postinro || "").trim())) return virhe("Tarkista postinumero (5 numeroa).");
    if (!d.hyvaksy) return virhe("Hyväksy toimitusehdot ennen tilaamista.");
    nappi.disabled = true; viesti.className = "viesti"; viesti.textContent = "Valmistellaan painotiedostoa…";
    try {
      const kuva = await painoKuva();
      viesti.textContent = `Lähetetään painotiedostoa (${(kuva.blob.size / 1e6).toFixed(1).replace(".", ",")} Mt)…`;
      const r1 = await fetch("/api/tiedosto", { method: "POST", headers: { "content-type": "image/jpeg" }, body: kuva.blob }).then((r) => r.json());
      if (!r1.id) throw new Error(r1.virhe || "Tiedoston lähetys epäonnistui.");
      viesti.textContent = "Siirrytään maksamaan…";
      const r2 = await fetch("/api/tilaus", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
        malli: MALLI, tuote: S.tuote, koko: S.koko, vari: S.vari, suunta: S.suunta, tiedosto: r1.id, kuvaus: kuvaus(), suunnitelma: S,
        nimi: d.nimi, email: d.email, puhelin: d.puhelin, osoite: d.osoite, postinro: d.postinro, kaupunki: d.kaupunki, hyvaksy: !!d.hyvaksy }) }).then((r) => r.json());
      if (!r2.url) throw new Error(r2.virhe || "Tilauksen luonti epäonnistui.");
      location.href = r2.url;
    } catch (err) { nappi.disabled = false; virhe(err.message || "Jokin meni vikaan. Yritä uudelleen."); }
  });

  // ---------- Työkalut: suurenna, kumoa, alusta; näppäimistö mobiilissa ----------
  const iso = $("#suurenna");
  if (iso) iso.addEventListener("click", () => { const on = document.body.classList.toggle("iso-esikatselu"); iso.textContent = on ? "Pienennä" : "Suurenna"; iso.setAttribute("aria-pressed", String(on)); paivita(); });
  $("#kumoa").addEventListener("click", kumoa);
  $("#alusta").addEventListener("click", alusta);
  ohj.addEventListener("focusin", (e) => { if (e.target.matches("input[type=text],input[type=search],textarea") && matchMedia("(max-width: 899px)").matches) { document.body.classList.add("kirjoittaa"); paivita(); setTimeout(() => e.target.scrollIntoView({ block: "center", behavior: "smooth" }), 280); } });
  ohj.addEventListener("focusout", () => { setTimeout(() => { if (!ohj.contains(document.activeElement) || !document.activeElement.matches("input,textarea")) { document.body.classList.remove("kirjoittaa"); paivita(); } }, 120); });

  S._edAsettelu = S.asettelu;
  rakennaOhjaimet();
  if (MALLI === "kartta") varmistaKartta(true);
  edellinen = JSON.stringify(S);
  paivita();
  window.OLTesti = { S, painoKuva, painoMitat, paivita, esikuva, kartta: () => kartta, toimitusArvio };
})();
