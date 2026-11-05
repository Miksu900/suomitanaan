// Omalahja (omalahja.fi/api/*): painotiedostojen vastaanotto, tilaukset, Visma Pay -maksu ja tilauksen välitys Gelatolle.
// Hinnat, Gelaton tuotetunnukset ja tilausten avaus (avoinna) ovat yhdessä paikassa: faktapiste/omalahja/tuotteet.json.
// R2 (env.VIDEOT): omalahja/tiedostot/<id>.jpg|png, omalahja/tilaukset/<nro>.json, omalahja/avaimet/<avain> -> nro.
import CONFIG from "../omalahja/tuotteet.json";

const VP = "https://www.vismapay.com/pbwapi";
const GELATO = "https://order.gelatoapis.com/v4/orders";
const SIVU = "https://omalahja.fi";
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const hex = (b) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
const satunnainen = (n = 24) => hex(crypto.getRandomValues(new Uint8Array(n)));
const euro = (s) => (s / 100).toFixed(s % 100 ? 2 : 0).replace(".", ",") + " €";
async function hmac(avain, viesti) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(avain), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(viesti))).toUpperCase();
}
const lue = async (env, nro) => { const o = await env.VIDEOT.get(`omalahja/tilaukset/${nro}.json`); return o ? o.json() : null; };
const tallenna = (env, t) => env.VIDEOT.put(`omalahja/tilaukset/${t.nro}.json`, JSON.stringify(t), { httpMetadata: { contentType: "application/json" } });

export function tuoteTiedot(tuote, koko, vari, suunta) {
  const t = CONFIG.tuotteet[tuote]; if (!t) return null;
  const k = t.koot[koko]; if (!k) return null;
  const vaaka = !t.eiSuuntaa && suunta === "vaaka";
  let uid = (vaaka && k.uidVaaka ? k.uidVaaka : k.uid).replace("{s}", vaaka ? "hor" : "ver"), hinta = k.hinta, kulu = k.kulu;
  let nimi = `${t.nimi} ${k.nimi || koko.replace("x", "×") + " cm"}`;
  if (uid.includes("{v}") || t.varit) { const v = (t.varit || {})[vari]; if (!v) return null; uid = uid.replace("{v}", v.v); nimi += `, ${v.nimi.toLowerCase()}`; hinta += v.lisa || 0; }
  if (!t.eiSuuntaa) nimi += vaaka ? ", vaaka" : ", pysty";
  return { uid, nimi, hinta, kulu, pdf: !!t.pdf };
}

// Kuvatiedoston tarkistus: vain JPEG/PNG, mitat luetaan tiedoston otsakkeesta.
function kuvanMitat(b) {
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return { tyyppi: "png", w: (b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19], h: (b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23] };
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) {
    let i = 2;
    while (i + 9 < b.length) {
      if (b[i] !== 0xff) { i++; continue; }
      const m = b[i + 1], pit = (b[i + 2] << 8) | b[i + 3];
      if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) return { tyyppi: "jpg", h: (b[i + 5] << 8) | b[i + 6], w: (b[i + 7] << 8) | b[i + 8] };
      if (m === 0xd8 || m === 0x01 || (m >= 0xd0 && m <= 0xd7)) { i += 2; continue; }
      i += 2 + pit;
    }
  }
  return null;
}

async function telegram(env, teksti) {
  if (!env.TELEGRAM_BOT_TOKEN) return;
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TG_CHAT || "1893930799", text: teksti.slice(0, 3900), disable_web_page_preview: true }) }).catch(() => {});
}

export function vahvistusTeksti(t) {
  const a = t.asiakas;
  return `Hei ${a.nimi.split(" ")[0]},\n\nkiitos tilauksestasi Omalahjasta! Tuotteesi valmistetaan juuri sinulle ja toimitetaan sinulle arviolta 8–14 arkipäivän kuluessa.\n\n` +
    `Tilausnumero: ${t.nro}\nTuote: ${t.tuoteNimi}\n${t.kuvaus}\nYhteensä: ${euro(t.hinta)} (sis. alv 25,5 % ja toimituksen)\n\n` +
    `Toimitusosoite:\n${a.nimi}\n${a.osoite}\n${a.postinro} ${a.kaupunki}\n\n` +
    `Jos huomaat tilauksessa virheen, vastaa tähän viestiin mahdollisimman pian, niin korjaamme sen ennen painoa.\n\n` +
    `Lämpimin terveisin\nOmalahja – omalahja.fi\nTaksiliikenne Koskela Oy (Y-tunnus 3425681-3)\nRiihikatu 3 B 20, 84100 Ylivieska\ninfo@omalahja.fi`;
}
async function vahvistusEmail(env, t) {
  if (!env.BREVO_API_KEY) return "ei avainta";
  const r = await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST", headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ sender: { email: "info@netvo.fi", name: "Omalahja" }, replyTo: { email: "info@omalahja.fi", name: "Omalahja" }, to: [{ email: t.asiakas.email, name: t.asiakas.nimi }],
      bcc: [{ email: "info@omalahja.fi" }], subject: `Tilausvahvistus ${t.nro} – Omalahja`, textContent: vahvistusTeksti(t) }) }).catch((e) => ({ ok: false, status: String(e) }));
  return r.ok ? "ok" : "virhe " + r.status;
}

// Gelato-tilaus. luonnos=true → orderType "draft" (testit). Palauttaa { id } tai { virhe }.
export function gelatoRunko(t, luonnos) {
  const a = t.asiakas, osat = a.nimi.trim().split(/\s+/);
  return { orderType: luonnos ? "draft" : "order", orderReferenceId: t.nro, customerReferenceId: "omalahja", currency: "EUR",
    items: [{ itemReferenceId: t.nro + "-1", productUid: t.uid, quantity: 1, files: [{ type: "default", url: t.tiedosto.url }] }],
    shipmentMethodUid: "normal",
    shippingAddress: { firstName: osat[0], lastName: osat.slice(1).join(" ") || osat[0], addressLine1: a.osoite, city: a.kaupunki, postCode: a.postinro, country: "FI", email: a.email, phone: a.puhelin } };
}
async function gelatoPyynto(env, url, metodi = "GET", runko) {
  const r = await fetch(url, { method: metodi, headers: { "X-API-KEY": env.GELATO_API_KEY, "user-agent": "NetvoKauppa/1.0", accept: "application/json", "content-type": "application/json" }, body: runko ? JSON.stringify(runko) : undefined });
  const teksti = await r.text(); let d; try { d = teksti ? JSON.parse(teksti) : {}; } catch { d = { raaka: teksti.slice(0, 300) }; }
  return { ok: r.ok, status: r.status, d };
}
async function lahetaGelatoon(env, t, luonnos = false) {
  if (!env.GELATO_API_KEY) return { virhe: "GELATO_API_KEY puuttuu" };
  try {
    const r = await gelatoPyynto(env, GELATO, "POST", gelatoRunko(t, luonnos));
    if (!r.ok || !r.d.id) return { virhe: `Gelato ${r.status}: ${JSON.stringify(r.d).slice(0, 400)}` };
    return { id: r.d.id, tila: r.d.fulfillmentStatus, tyyppi: r.d.orderType };
  } catch (e) { return { virhe: String(e).slice(0, 300) }; }
}

// Maksun jälkeen: Gelato → Telegram → asiakkaan vahvistus. Gelaton virhe ei kadota tilausta: Miika saa Telegramiin ohjeen uudelleenyritykseen.
async function kasitteleMaksettu(env, t) {
  const g = await lahetaGelatoon(env, t);
  if (g.id) { t.gelato = { id: g.id, aika: new Date().toISOString() }; delete t.gelatoVirhe; } else t.gelatoVirhe = g.virhe;
  t.tila = "maksettu"; await tallenna(env, t);
  const a = t.asiakas;
  await telegram(env, `🎁 Omalahja: uusi tilaus ${t.nro} – ${euro(t.hinta)}\n${t.tuoteNimi}\n${t.kuvaus}\nAsiakas: ${a.nimi}, ${a.postinro} ${a.kaupunki}\nPainotiedosto: ${t.tiedosto.url}\n` +
    (g.id ? `✅ Gelato-tilaus luotu: ${g.id}` : `⚠️ Gelato-tilaus EPÄONNISTUI: ${g.virhe}\nTilaus on tallessa. Yritä uudelleen: POST https://omalahja.fi/api/hallinta/gelato?nro=${t.nro} (x-avain), tai pyydä Claudea tekemään se.`));
  t.email = await vahvistusEmail(env, t); await tallenna(env, t);
}

// AUTHCODE = HMAC(yksityinen avain, RETURN_CODE|ORDER_NUMBER[|SETTLED][|CONTACT_ID][|INCIDENT_ID])
async function kasittelePaluu(env, p) {
  const osat = ["RETURN_CODE", "ORDER_NUMBER", "SETTLED", "CONTACT_ID", "INCIDENT_ID"].filter((k) => p.has(k)).map((k) => p.get(k));
  if (!p.get("AUTHCODE") || (await hmac(env.VISMAPAY_PRIVATE_KEY, osat.join("|"))) !== p.get("AUTHCODE").toUpperCase()) return { virhe: "tarkiste" };
  const nro = p.get("ORDER_NUMBER"); if (!/^OL[0-9A-Z]{6,24}$/.test(nro || "")) return { virhe: "tilaus" };
  let t = await lue(env, nro);
  if (!t) return { virhe: "tilaus" };
  if (p.get("RETURN_CODE") !== "0") return { t, ok: false };
  if (t.tila === "odottaa") {
    // Paluu- ja ilmoituspyyntö voivat tulla yhtä aikaa: varaus + uudelleenluku, jotta Gelato-tilaus syntyy vain kerran.
    const lukko = satunnainen(8); t.tila = "kasittelyssa"; t.lukko = lukko; t.maksettu = new Date().toISOString(); await tallenna(env, t);
    await new Promise((r) => setTimeout(r, 1200));
    t = await lue(env, nro);
    if (t.lukko === lukko && t.tila === "kasittelyssa") await kasitteleMaksettu(env, t);
  }
  return { t, ok: true };
}

// ---- Karttadata: Overpass ja Nominatim Workerin kautta, välimuistissa (Cache API + R2) ----
const UA = "Omalahja/1.0 (+https://omalahja.fi; info@omalahja.fi)";
const KARTTA_TASOT = [0.6, 1, 1.6, 2.5, 4, 6.5, 10, 16];
const OVERPASS = [["https://overpass-api.de/api/interpreter", 0], ["https://overpass.private.coffee/api/interpreter", 3000], ["https://overpass.kumi.systems/api/interpreter", 9000]];
export function karttaRuutu(lat, lon, sade) {
  const ti = Math.max(0, KARTTA_TASOT.findIndex((x) => x >= sade * 0.999)), t = ti < 0 ? KARTTA_TASOT.length - 1 : ti, taso = KARTTA_TASOT[t === -1 ? 7 : t];
  const askelLat = (taso * 0.6) / 111.32, i = Math.round(lat / askelLat), la = i * askelLat;
  const askelLon = askelLat / Math.max(0.05, Math.cos((la * Math.PI) / 180)), j = Math.round(lon / askelLon), lo = j * askelLon;
  const dlat = (taso * 1.7) / 111.32, dlon = dlat / Math.max(0.05, Math.cos((la * Math.PI) / 180));
  return { taso, t: KARTTA_TASOT.indexOf(taso), i, j, lat: la, lon: lo, rajat: { s: la - dlat * 1.45, n: la + dlat * 1.45, w: lo - dlon, e: lo + dlon } };
}
export function overpassKysely(r) {
  const b = r.rajat, bb = `${b.s.toFixed(5)},${b.w.toFixed(5)},${b.n.toFixed(5)},${b.e.toFixed(5)}`, s = r.taso;
  const ryhmat = [["t3.3", 'way["highway"~"^(motorway|trunk|motorway_link|trunk_link)$"]'], ["t2.7", 'way["highway"~"^(primary|primary_link)$"]'],
    ["t2.3", 'way["highway"~"^(secondary|secondary_link)$"]'], ["t1.9", 'way["highway"~"^(tertiary|tertiary_link)$"]']];
  if (s <= 10) ryhmat.push(["t1.2", 'way["highway"~"^(unclassified|residential|living_street)$"]']);
  if (s <= 1.6) ryhmat.push(["t0.85", 'way["highway"~"^(pedestrian|service)$"]']);
  if (s <= 1) ryhmat.push(["t0.45", 'way["highway"~"^(footway|path|cycleway|track|steps)$"]']);
  ryhmat.push(["rata", 'way["railway"="rail"]'], ["vesi", 'way["natural"="water"]'], ["vesi", 'way["waterway"="riverbank"]'], ["vr", 'relation["natural"="water"]'],
    ["j2.4", 'way["waterway"="river"]'], ["j1.6", 'way["waterway"="canal"]'], ["ranta", 'way["natural"="coastline"]']);
  if (s <= 4) ryhmat.push(["j0.7", 'way["waterway"="stream"]']);
  return `[out:json][timeout:40][maxsize:300000000];` + ryhmat.map(([g, q]) => `make r g="${g}";out;${q}(${bb});out skel geom qt;`).join("");
}
async function haeOverpass(kysely) {
  // Porrastetut rinnakkaiset pyynnöt peileihin: seuraava käynnistyy, jos edellinen ei ole vastannut 9 sekunnissa.
  const ohjaimet = [];
  const yksi = (url, viive) => new Promise((ok, ei) => setTimeout(async () => {
    const ac = new AbortController(); ohjaimet.push(ac); const aika = setTimeout(() => ac.abort(), 85000);
    try {
      const r = await fetch(url, { method: "POST", body: "data=" + encodeURIComponent(kysely), headers: { "content-type": "application/x-www-form-urlencoded", "user-agent": UA, accept: "application/json" }, signal: ac.signal });
      if (!r.ok) throw new Error(url + " " + r.status);
      const b = new Uint8Array(await r.arrayBuffer()); clearTimeout(aika);
      const loppu = new TextDecoder().decode(b.subarray(Math.max(0, b.length - 400)));
      if (b[0] !== 0x7b || (/"remark"/.test(loppu) && /error|timed out|out of memory/i.test(loppu))) throw new Error(url + " remark");
      ok({ b, url });
    } catch (e) { clearTimeout(aika); ei(e); }
  }, viive));
  try { const t = await Promise.any(OVERPASS.map(([u, viive]) => yksi(u, viive))); ohjaimet.forEach((a) => a.abort()); return t; }
  catch (e) { throw new Error("overpass: " + (e.errors || []).map((x) => x.message).join(" | ")); }
}
async function karttaAlue(env, u, ctx) {
  const lat = +u.searchParams.get("lat"), lon = +u.searchParams.get("lon"), sade = +u.searchParams.get("sade");
  if (!isFinite(lat) || !isFinite(lon) || !(sade > 0) || Math.abs(lat) > 85 || Math.abs(lon) > 180) return json({ virhe: "lat, lon ja sade" }, 400);
  const r = karttaRuutu(lat, lon, Math.min(sade, 16));
  const avain = `omalahja/kartta/v1/${r.t}/${r.i}_${r.j}.json`, valimuisti = caches.default, cu = new Request(`https://omalahja.fi/_kartta/v1/${r.t}/${r.i}_${r.j}`);
  const otsakkeet = { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=604800", "access-control-allow-origin": "*", "x-omalahja-ruutu": `${r.t}/${r.i}_${r.j}` };
  const c = await valimuisti.match(cu); if (c) { const h = new Headers(c.headers); h.set("x-lahde", "cache"); return new Response(c.body, { headers: h }); }
  const o = await env.VIDEOT.get(avain);
  if (o) { const vas = new Response(o.body, { headers: { ...otsakkeet, "x-lahde": "r2" } }); ctx && ctx.waitUntil(valimuisti.put(cu, vas.clone())); return vas; }
  let t; const alkuAika = Date.now();
  try { t = await haeOverpass(overpassKysely(r)); } catch (e) { console.log(String(e)); return json({ virhe: "Karttapalvelu ei vastannut. Yritä hetken päästä uudelleen.", syy: String(e).slice(0, 300), ms: Date.now() - alkuAika }, 503); }
  const alku = new TextEncoder().encode(`{"ruutu":${JSON.stringify({ taso: r.taso, lat: r.lat, lon: r.lon, rajat: r.rajat, lahde: t.url.split("/")[2] })},"osm":`);
  const runko = new Uint8Array(alku.length + t.b.length + 1); runko.set(alku); runko.set(t.b, alku.length); runko[runko.length - 1] = 0x7d;
  ctx && ctx.waitUntil(Promise.all([env.VIDEOT.put(avain, runko, { httpMetadata: { contentType: "application/json" } }), valimuisti.put(cu, new Response(runko, { headers: otsakkeet }))]));
  return new Response(runko, { headers: { ...otsakkeet, "x-lahde": t.url.split("/")[2] } });
}
function karttaKaare(lat, lon, sade) { return karttaRuutu(lat, lon, Math.min(sade, 16)); }
const karttaAvain = (r) => `omalahja/kartta/v1/${r.t}/${r.i}_${r.j}.json`;
function karttaKysely(u) {
  const lat = +u.searchParams.get("lat"), lon = +u.searchParams.get("lon"), sade = +u.searchParams.get("sade");
  if (!isFinite(lat) || !isFinite(lon) || !(sade > 0)) return json({ virhe: "lat, lon ja sade" }, 400);
  const r = karttaKaare(lat, lon, sade);
  return new Response(JSON.stringify({ ruutu: { taso: r.taso, lat: r.lat, lon: r.lon, rajat: r.rajat }, avain: `${r.t}/${r.i}_${r.j}`, kysely: overpassKysely(r) }),
    { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=86400" } });
}
// Ylläpito: esilasketun Overpass-vastauksen tallennus (GitHub Actions hakee datan ja lähettää sen tänne)
async function karttaTallenna(req, env, u) {
  const lat = +u.searchParams.get("lat"), lon = +u.searchParams.get("lon"), sade = +u.searchParams.get("sade");
  if (!isFinite(lat) || !isFinite(lon) || !(sade > 0)) return json({ virhe: "lat, lon ja sade" }, 400);
  const b = new Uint8Array(await req.arrayBuffer());
  if (b.length < 50 || b.length > 60e6 || b[0] !== 0x7b) return json({ virhe: "virheellinen data" }, 400);
  const r = karttaKaare(lat, lon, sade);
  const alku = new TextEncoder().encode(`{"ruutu":${JSON.stringify({ taso: r.taso, lat: r.lat, lon: r.lon, rajat: r.rajat, lahde: "esilaskettu" })},"osm":`);
  const runko = new Uint8Array(alku.length + b.length + 1); runko.set(alku); runko.set(b, alku.length); runko[runko.length - 1] = 0x7d;
  await env.VIDEOT.put(karttaAvain(r), runko, { httpMetadata: { contentType: "application/json" } });
  await caches.default.delete(new Request(`https://omalahja.fi/_kartta/v1/${r.t}/${r.i}_${r.j}`));
  return json({ ok: true, ruutu: `${r.t}/${r.i}_${r.j}`, koko: runko.length });
}
async function karttaOnko(env, u) {
  const r = karttaKaare(+u.searchParams.get("lat"), +u.searchParams.get("lon"), +u.searchParams.get("sade"));
  const o = await env.VIDEOT.head(karttaAvain(r)); return json({ on: !!o, koko: o ? o.size : 0, ruutu: `${r.t}/${r.i}_${r.j}` });
}
async function karttaHaku(env, u, ctx) {
  const q = (u.searchParams.get("q") || "").trim().slice(0, 120), fi = u.searchParams.get("fi") === "1";
  if (q.length < 2) return json([]);
  const avain = hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode((fi ? "fi:" : "kaikki:") + q.toLowerCase()))).slice(0, 40);
  const cu = new Request(`https://omalahja.fi/_haku/v1/${avain}`), c = await caches.default.match(cu);
  if (c) return c;
  const o = await env.VIDEOT.get(`omalahja/haku/v1/${avain}.json`);
  const otsakkeet = { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=86400" };
  if (o) return new Response(o.body, { headers: otsakkeet });
  const nu = new URL("https://nominatim.openstreetmap.org/search");
  nu.search = new URLSearchParams({ q, format: "jsonv2", limit: "6", "accept-language": "fi", addressdetails: "1", ...(fi ? { countrycodes: "fi" } : {}) });
  const r = await fetch(nu, { headers: { "user-agent": UA, accept: "application/json", referer: "https://omalahja.fi/" }, signal: AbortSignal.timeout(12000) }).catch(() => null);
  if (!r || !r.ok) return json({ virhe: "Paikkahaku ei vastannut. Yritä hetken päästä uudelleen." }, 503);
  const b = await r.text();
  ctx && ctx.waitUntil(Promise.all([env.VIDEOT.put(`omalahja/haku/v1/${avain}.json`, b), caches.default.put(cu, new Response(b, { headers: otsakkeet }))]));
  return new Response(b, { headers: otsakkeet });
}

const tarkista = (env, req) => !!(env.HALLINTA && req.headers.get("x-avain") === env.HALLINTA);

export async function omalahja(req, env, u, ctx) {
  if (!env.VIDEOT) return json({ virhe: "Palvelu ei ole käytössä." }, 503);
  const p = u.pathname.replace(/^\/api\//, "");
  const vp = !!(env.VISMAPAY_API_KEY && env.VISMAPAY_PRIVATE_KEY);

  if (p === "kartta/alue" && req.method === "GET") return karttaAlue(env, u, ctx);
  if (p === "kartta/haku" && req.method === "GET") return karttaHaku(env, u, ctx);
  if (p === "kartta/kysely" && req.method === "GET") return karttaKysely(u);
  if (p === "tila") return json({ ok: true, avoinna: !!CONFIG.avoinna, maksu: vp, gelato: !!env.GELATO_API_KEY, posti: !!env.BREVO_API_KEY, telegram: !!env.TELEGRAM_BOT_TOKEN });

  // Painotiedoston lataus (selain renderöi suunnitelman painoresoluutiolla)
  if (p === "tiedosto" && req.method === "POST") {
    const pituus = +req.headers.get("content-length") || 0;
    if (pituus > 40e6) return json({ virhe: "Tiedosto on liian suuri." }, 413);
    const b = new Uint8Array(await req.arrayBuffer());
    if (b.length > 40e6) return json({ virhe: "Tiedosto on liian suuri." }, 413);
    if (b.length < 5000) return json({ virhe: "Tiedosto on liian pieni." }, 400);
    const pdf = b[0] === 0x25 && b[1] === 0x50 && b[2] === 0x44 && b[3] === 0x46; // %PDF
    const m = pdf ? { tyyppi: "pdf", w: 0, h: 0 } : kuvanMitat(b);
    if (!m) return json({ virhe: "Vain JPEG-, PNG- tai PDF-tiedostot kelpaavat." }, 415);
    if (!pdf && (m.w < 1000 || m.h < 900 || m.w > 12000 || m.h > 12000)) return json({ virhe: "Kuvan mitat eivät kelpaa painoon." }, 400);
    const id = satunnainen(20) + "." + m.tyyppi;
    await env.VIDEOT.put("omalahja/tiedostot/" + id, b, { httpMetadata: { contentType: m.tyyppi === "png" ? "image/png" : m.tyyppi === "pdf" ? "application/pdf" : "image/jpeg" }, customMetadata: { luotu: new Date().toISOString(), w: String(m.w), h: String(m.h) } });
    return json({ id, url: `${SIVU}/api/tiedosto/${id}`, w: m.w, h: m.h });
  }
  const tm = p.match(/^tiedosto\/([0-9a-f]{40}\.(jpg|png|pdf))$/);
  if (tm && (req.method === "GET" || req.method === "HEAD")) {
    const o = await env.VIDEOT.get("omalahja/tiedostot/" + tm[1]);
    if (!o) return new Response("Ei löytynyt", { status: 404 });
    return new Response(req.method === "HEAD" ? null : o.body, { headers: { "content-type": o.httpMetadata?.contentType || "image/jpeg", "content-length": String(o.size), "cache-control": "private, max-age=86400", "x-robots-tag": "noindex" } });
  }

  if (p === "tilaus" && req.method === "POST") {
    if (!CONFIG.avoinna) return json({ virhe: "Tilaukset avautuvat pian." }, 503);
    if (!vp) return json({ virhe: "Maksaminen avautuu pian." }, 503);
    const d = await req.json().catch(() => ({}));
    const tt = tuoteTiedot(d.tuote, d.koko, d.vari, d.suunta);
    if (!tt) return json({ virhe: "Tuntematon tuote." }, 400);
    const s = (x, n) => String(x || "").trim().replace(/\s+/g, " ").slice(0, n);
    const a = { nimi: s(d.nimi, 80), email: s(d.email, 120).toLowerCase(), puhelin: s(d.puhelin, 20), osoite: s(d.osoite, 100), postinro: s(d.postinro, 5), kaupunki: s(d.kaupunki, 60) };
    if (a.nimi.length < 3) return json({ virhe: "Kirjoita nimesi." }, 400);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(a.email)) return json({ virhe: "Tarkista sähköpostiosoite." }, 400);
    if (!/^\+?[0-9 ()-]{6,20}$/.test(a.puhelin)) return json({ virhe: "Tarkista puhelinnumero." }, 400);
    if (a.osoite.length < 4 || a.kaupunki.length < 2) return json({ virhe: "Tarkista osoite." }, 400);
    if (!/^\d{5}$/.test(a.postinro)) return json({ virhe: "Tarkista postinumero." }, 400);
    if (!d.hyvaksy) return json({ virhe: "Hyväksy toimitusehdot." }, 400);
    if (!/^[0-9a-f]{40}\.(jpg|png|pdf)$/.test(d.tiedosto || "")) return json({ virhe: "Painotiedosto puuttuu." }, 400);
    if (tt.pdf !== d.tiedosto.endsWith(".pdf")) return json({ virhe: "Painotiedoston muoto ei sovi tuotteeseen." }, 400);
    const kuva = await env.VIDEOT.head("omalahja/tiedostot/" + d.tiedosto);
    if (!kuva) return json({ virhe: "Painotiedosto puuttuu. Yritä uudelleen." }, 400);
    const nro = "OL" + Date.now().toString(36).toUpperCase() + satunnainen(3).toUpperCase();
    const suunnitelma = JSON.stringify(d.suunnitelma || {}).slice(0, 8000);
    const t = { nro, avain: satunnainen(), luotu: new Date().toISOString(), tila: "odottaa", malli: d.malli === "kartta" ? "kartta" : "nimi", tuote: d.tuote, koko: d.koko, vari: d.vari, suunta: d.suunta === "vaaka" ? "vaaka" : "pysty",
      uid: tt.uid, tuoteNimi: tt.nimi, hinta: tt.hinta, kuvaus: s(d.kuvaus, 400), suunnitelma, tiedosto: { id: d.tiedosto, url: `${SIVU}/api/tiedosto/${d.tiedosto}` }, asiakas: a, gelato: null };
    await tallenna(env, t); await env.VIDEOT.put("omalahja/avaimet/" + t.avain, nro);
    const osat = a.nimi.split(" ");
    const vastaus = await fetch(`${VP}/auth_payment`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
      version: "w3.1", api_key: env.VISMAPAY_API_KEY, order_number: nro, amount: t.hinta, currency: "EUR", email: a.email,
      authcode: await hmac(env.VISMAPAY_PRIVATE_KEY, `${env.VISMAPAY_API_KEY}|${nro}`),
      payment_method: { type: "e-payment", return_url: `${SIVU}/api/paluu`, notify_url: `${SIVU}/api/ilmoitus`, lang: "fi" },
      customer: { firstname: osat[0], lastname: osat.slice(1).join(" "), email: a.email, address_street: a.osoite, address_city: a.kaupunki, address_zip: a.postinro, address_country: "FI" },
      products: [{ id: `${t.tuote}-${t.koko}`, title: `Omalahja: ${tt.nimi}`.slice(0, 120), count: 1, pretax_price: Math.round(t.hinta / 1.255), tax: 25.5, price: t.hinta, type: 1 }],
    }) }).then((r) => r.json()).catch((e) => ({ result: -1, virhe: String(e) }));
    if (vastaus.result !== 0 || !vastaus.token) { console.log("Visma Pay auth_payment (omalahja)", JSON.stringify(vastaus)); return json({ virhe: "Maksun aloitus epäonnistui. Yritä hetken päästä uudelleen." }, 502); }
    return json({ url: `${VP}/token/${vastaus.token}` });
  }
  if (p === "tilaus" && req.method === "GET") {
    const avain = u.searchParams.get("t") || "";
    if (!/^[0-9a-f]{48}$/.test(avain)) return json({ virhe: "Virheellinen linkki." }, 400);
    const ao = await env.VIDEOT.get("omalahja/avaimet/" + avain); const nro = ao ? await ao.text() : null;
    const t = nro && (await lue(env, nro));
    if (!t) return json({ virhe: "Tilausta ei löytynyt." }, 404);
    if (t.tila !== "maksettu") return json({ tila: "odottaa", virhe: "Maksua ei ole vielä vahvistettu." }, 409);
    return json({ nro: t.nro, tuote: t.tuoteNimi, summa: euro(t.hinta) });
  }
  if (p === "paluu") {
    const r = await kasittelePaluu(env, u.searchParams);
    if (r.ok) return Response.redirect(`${SIVU}/kiitos/?t=${r.t.avain}`, 302);
    return Response.redirect(`${SIVU}/tee/${r.t && r.t.malli === "kartta" ? "kartta" : "nimijuliste"}/?maksu=peruttu`, 302);
  }
  if (p === "ilmoitus") { await kasittelePaluu(env, u.searchParams); return new Response("OK"); }

  // ---- Ylläpito (x-avain = HALLINTA) ----
  if (p.startsWith("hallinta/")) {
    if (!tarkista(env, req)) return json({ virhe: "Ei oikeutta." }, 403);
    const nro = u.searchParams.get("nro") || "";
    if (p === "hallinta/kartta" && req.method === "PUT") return karttaTallenna(req, env, u);
    if (p === "hallinta/kartta" && req.method === "GET") return karttaOnko(env, u);
    if (p === "hallinta/tilaus") { const t = await lue(env, nro); return t ? json(t) : json({ virhe: "Ei löytynyt." }, 404); }
    if (p === "hallinta/tilaukset") {
      const l = await env.VIDEOT.list({ prefix: "omalahja/tilaukset/", limit: 200 });
      return json({ tilaukset: l.objects.map((o) => ({ nro: o.key.split("/").pop().replace(".json", ""), aika: o.uploaded })) });
    }
    // Uudelleenyritys: lähetä maksettu tilaus Gelatolle (jos se ei jo ole siellä)
    if (p === "hallinta/gelato" && req.method === "POST") {
      const t = await lue(env, nro); if (!t) return json({ virhe: "Ei löytynyt." }, 404);
      if (!["maksettu", "kasittelyssa"].includes(t.tila)) return json({ virhe: `Tilausta ei ole maksettu (tila ${t.tila}).` }, 409);
      if (t.gelato && t.gelato.id && u.searchParams.get("pakota") !== "1") return json({ virhe: "Tilaus on jo Gelatossa.", gelato: t.gelato }, 409);
      const g = await lahetaGelatoon(env, t);
      if (g.id) { t.gelato = { id: g.id, aika: new Date().toISOString() }; delete t.gelatoVirhe; t.tila = "maksettu"; } else t.gelatoVirhe = g.virhe;
      await tallenna(env, t);
      await telegram(env, g.id ? `✅ Omalahja ${t.nro}: Gelato-tilaus luotu uudelleenyrityksellä (${g.id}).` : `⚠️ Omalahja ${t.nro}: Gelato epäonnistui edelleen: ${g.virhe}`);
      return json(g, g.id ? 200 : 502);
    }
    // Luonnostesti: koko tilausputki Gelaton LUONNOS-tilauksella (orderType draft), joka poistetaan heti. Ei maksua, ei sähköpostia.
    if (p === "hallinta/luonnostesti" && req.method === "POST") {
      const d = await req.json().catch(() => ({}));
      const tt = tuoteTiedot(d.tuote || "juliste", d.koko || "30x40", d.vari || "musta", d.suunta || "pysty");
      const url = String(d.tiedosto || "");
      if (!tt || !url.startsWith(SIVU + "/api/tiedosto/")) return json({ virhe: "tuote tai tiedosto puuttuu" }, 400);
      const t = { nro: "OLTESTI" + Date.now().toString(36).toUpperCase(), uid: tt.uid, tuoteNimi: tt.nimi, hinta: tt.hinta, kuvaus: "Testi", tiedosto: { url },
        asiakas: { nimi: "Testi Tilaus", email: "info@omalahja.fi", puhelin: "0447777149", osoite: "Riihikatu 3 B 20", postinro: "84100", kaupunki: "Ylivieska" } };
      const g = await lahetaGelatoon(env, t, true);
      const tulos = { tuote: tt.nimi, uid: tt.uid, luonnos: g };
      if (g.id) {
        const nyt = await gelatoPyynto(env, `${GELATO}/${g.id}`);
        tulos.haettu = { status: nyt.status, orderType: nyt.d.orderType, tila: nyt.d.fulfillmentStatus, tuote: nyt.d.items?.[0]?.productUid, kaupunki: nyt.d.shippingAddress?.city };
        const pois = await gelatoPyynto(env, `${GELATO}/${g.id}`, "DELETE");
        tulos.poisto = { status: pois.status };
      }
      if (d.telegram) await telegram(env, `🧪 Omalahja-testi: Gelato-luonnos ${g.id ? "OK (" + g.id + ", poistettu)" : "EPÄONNISTUI: " + g.virhe}`);
      return json(tulos, g.id ? 200 : 502);
    }
    return json({ virhe: "Ei löytynyt." }, 404);
  }
  return json({ virhe: "Ei löytynyt." }, 404);
}
