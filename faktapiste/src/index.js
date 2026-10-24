// Faktapiste-keskustelu: Cloudflare Worker + SQLite Durable Object.
// Staattiset sivut tulevat public/-kansiosta, /api/* ohjataan Durable Objectille "main".
import { DurableObject } from "cloudflare:workers";
import KUNNAT from "../kunnat.json";
const KUNTA = new Map(KUNNAT.map(k => [k.toLowerCase(), k]));

const MALLI = "claude-haiku-5-5";
const ES = "https://eduskuntaseuranta.fi";
const ES_HAKU = "https://arwenhbwzoavbonlwkdr.supabase.co/functions/v1/haku";
const ES_AVAIN = "sb_publishable_7baeuteHYaarCEv4-j8C_g_OLxcKzJp";
const ADMIN = ["miika@eduskuntaseuranta.fi", "miika.koskela990@gmail.com", "eduskuntaseuranta@gmail.com"];
// Testivaiheessa (KIRJAUTUMINEN = "testi") vain nämä osoitteet voivat kirjautua.
const TESTAAJAT = ADMIN;
// Keskustelu käydään omalla nimellä: etu- ja sukunimi, isot alkukirjaimet, väliviiva sallittu (Anna-Liisa).
const OSA = "[A-ZÅÄÖÜÉ][a-zåäöüéè']+(?:-[A-ZÅÄÖÜÉ][a-zåäöüéè']+)*";
const NIMI_RX = new RegExp("^" + OSA + "(?: " + OSA + ")+$");
const oikeaNimi = n => !!n && n.length <= 60 && NIMI_RX.test(n);
const isot = n => n.toLowerCase().replace(/(^|[\s-])([a-zåäöüé])/g, (m, a, b) => a + b.toUpperCase());
const PITUUS = 100000; // käytännössä rajaton, suojaa vain tietokantaa
const VIDEO_MAX = 100 * 1024 * 1024, VIDEO_KESTO = 180, VIDEO_TYYPIT = ["video/mp4", "video/webm", "video/quicktime"];
const KUVAT_MAX = 4, KUVA_MAX = 1800000; // kuvia per postaus, tavua per kuva (SQLite-rivin raja 2 Mt)
const TAATTU = 30;        // jokainen postaus näytetään vähintään näin monelle lukijalle
const SYOTE_MAX = 25;     // Sinulle-syöte loppuu tähän
// syötteen säätimien luokat: k=keskustelut, u=uutiset, m=otsikkomuutokset, h=huijausvaroitukset, e=päätökset
const TIEDOTTEET = [
  { id: "yksityisyysvahti", aika: "2026-10-23T15:30:00Z", url: "/yksityisyys/",
    teksti: "HS:n selvityksen mukaan lähes 800 000 suomalaisen sijaintitietoja on päätynyt myyntiin sovellusten kautta. Tein työkalun, jolla sen voi estää omasta puhelimesta muutamassa minuutissa.",
    otsikko: "Yksityisyysvahti: onko sijaintisi myynnissä?",
    kuvaus: "Tarkistuslista Androidille ja iPhonelle sekä valmis tietosuojapyyntö, jolla vaadit yritystä kertomaan tai poistamaan tietosi. Maksuton." },
];
// Suomi Tänään -uutiset tauolla syötteestä viikon (Hei 24.10.2026); palaavat automaattisesti.
const ST_TAUKO_ASTI = Date.parse("2026-10-31T13:00:00Z");
const LUOKKA = { kayttaja: "k", suomitanaan: "u", korjausvahti: "m", keraysvahti: "h", eduskunta: "e" };
const KERROIN = [0, 1, 2.5];
const MS_CLIENT = "a5c26010-4549-400f-806a-4db7204ab906", MS_PALUU = "https://faktapiste.fi/api/oauth/microsoft";

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (u.hostname === "www.faktapiste.fi") return Response.redirect("https://faktapiste.fi" + u.pathname + u.search, 301);
    if (u.pathname.startsWith("/api/")) return env.FP.get(env.FP.idFromName("main")).fetch(req);
    const jm = u.pathname.match(/^\/p\/(\d+)\/?$/);
    if (jm) return jakosivu(env, u, +jm[1]);
    return env.ASSETS.fetch(req);
  },
  async scheduled(ev, env, ctx) {
    ctx.waitUntil(env.FP.get(env.FP.idFromName("main")).fetch(new Request("https://sisainen/_sisaanluku", { method: "POST" })));
  },
};

// Jaettava postauslinkki /p/<id>: sama sovellus, mutta esikatselu (X, Facebook, WhatsApp) näyttää postauksen tekstin ja kuvan.
async function jakosivu(env, u, id) {
  const sivu = await env.ASSETS.fetch(new Request(u.origin + "/"));
  let p = null;
  try { const r = await env.FP.get(env.FP.idFromName("main")).fetch(new Request(u.origin + "/api/posti/" + id)); p = (await r.json()).posti || null; } catch {}
  if (!p || p.piilotettu) return sivu;
  const teksti = String(p.teksti || (p.kortti && (p.kortti.otsikko || p.kortti.kysymys)) || "").replace(/\s+/g, " ").trim();
  const kuvaus = teksti.length > 200 ? teksti.slice(0, 197).replace(/\s+\S*$/, "") + "…" : teksti || (p.video ? "Katso video Faktapisteessä." : "Keskustelu Faktapisteessä.");
  const otsikko = (p.nimi ? p.nimi + " Faktapisteessä" : "Faktapiste");
  const kuva = p.video && p.video.kansi ? `https://faktapiste.fi/api/video/${p.video.id}/kansi` : p.kuvat && p.kuvat[0] ? `https://faktapiste.fi/api/kuva/${p.kuvat[0].id}` : "https://faktapiste.fi/og.png";
  const url = `https://faktapiste.fi/p/${id}`;
  const aseta = (sel, arvo) => ({ element(e) { e.setAttribute("content", arvo); } });
  return new HTMLRewriter()
    .on('meta[property="og:title"]', aseta(0, otsikko)).on('meta[property="og:description"]', aseta(0, kuvaus))
    .on('meta[name="description"]', aseta(0, kuvaus)).on('meta[property="og:image"]', aseta(0, kuva))
    .on('meta[property="og:url"]', aseta(0, url)).on('link[rel="canonical"]', { element(e) { e.setAttribute("href", url); } })
    .on("title", { element(e) { e.setInnerContent(otsikko); } })
    .on("head", { element(e) { e.append(`<script>history.replaceState(null,"","/?p=${id}")</script>`, { html: true }); } })
    .transform(new Response(sivu.body, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=300" } }));
}

// Onko uutinen maksumuurin takana? Julkaisijat merkitsevät maksulliset jutut hakukoneille (schema.org isAccessibleForFree).
// Palauttaa true / false, tai null jos sivua ei saatu luettua.
async function maksumuuri(url) {
  try {
    const r = await fetch(url, { headers: { "user-agent": "Mozilla/5.0 (compatible; Faktapiste/1.0; +https://faktapiste.fi)" }, signal: AbortSignal.timeout(6000), redirect: "follow" });
    if (!r.ok) return null;
    const h = (await r.text()).slice(0, 400000);
    if (/"isAccessibleForFree"\s*:\s*(false|"false")/i.test(h) || /<meta[^>]+(content_tier|article:content_tier)[^>]+(locked|metered)/i.test(h)) return true;
    if (/"isAccessibleForFree"\s*:\s*(true|"true")/i.test(h)) return false;
    return /\bhs\.fi\/[^"]*\/art-|\/plus\/|paywall|maksumuuri/i.test(url + " " + (h.match(/<meta[^>]+og:url[^>]+>/i) || [""])[0]) ? true : false;
  } catch { return null; }
}

// ---------- apurit ----------
const json = (d, s = 200, h = {}) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...h } });
const virhe = (v, s = 400) => json({ virhe: v }, s);
const nyt = () => Date.now();
function satunnainen(n = 32) { const b = new Uint8Array(n); crypto.getRandomValues(b); return [...b].map(x => x.toString(16).padStart(2, "0")).join(""); }
async function tiiviste(s) { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, "0")).join(""); }
function evaste(req, nimi) { const m = (req.headers.get("cookie") || "").match(new RegExp("(?:^|;\\s*)" + nimi + "=([^;]+)")); return m ? m[1] : null; }
const puhdas = s => String(s || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").trim();
const xmlPurku = s => String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/<[^>]+>/g, "").trim();

async function claude(env, system, user, max = 600) {
  if (!env.ANTHROPIC_API_KEY) throw new Error("ei avainta");
  const kutsu = lisa => fetch("https://api.anthropic.com/v1/messages", {
    method: "POST", headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: MALLI, system, messages: [{ role: "user", content: user }], ...lisa }),
  });
  let r = await kutsu({ max_tokens: max, thinking: { type: "disabled" } });
  if (r.status === 400) r = await kutsu({ max_tokens: max * 4 });
  if (!r.ok) throw new Error("tekoäly " + r.status);
  const d = await r.json();
  return (d.content || []).filter(c => c.type === "text").map(c => c.text).join("");
}
const jsonista = s => { const m = String(s).match(/\{[\s\S]*\}/); try { return m ? JSON.parse(m[0]) : null; } catch { return null; } };

async function telegram(env, teksti) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TG_CHAT) return;
  try {
    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id: env.TG_CHAT, text: teksti.slice(0, 3900), disable_web_page_preview: true }) });
  } catch {}
}

// Äänestyssivun puolueittainen taulukko
async function aanestysKortti(id) {
  const r = await fetch(`${ES}/aanestys/${id}/`, { headers: { "user-agent": "Faktapiste/1.0" } });
  if (!r.ok) return null;
  const h = await r.text();
  const otsikko = xmlPurku((h.match(/<title>([^<]+)<\/title>/) || [])[1] || "").replace(/\s*\|\s*Eduskuntaseuranta.*$/, "");
  const ryhmat = [];
  const t = h.match(/<table><tr><th>Ryhmä<\/th>[\s\S]*?<\/table>/);
  if (t) for (const m of t[0].matchAll(/<tr><td>([^<]+)<\/td><td class="jaa">(\d+)<\/td><td class="ei">(\d+)<\/td><td class="tyhja">(\d+)<\/td><td class="poissa">(\d+)<\/td><\/tr>/g))
    ryhmat.push({ r: xmlPurku(m[1]), jaa: +m[2], ei: +m[3], tyhja: +m[4], poissa: +m[5] });
  const sum = k => ryhmat.reduce((a, x) => a + x[k], 0);
  return { tyyppi: "aanestys", id: +id, otsikko, url: `${ES}/aanestys/${id}/`, jaa: sum("jaa"), ei: sum("ei"), tyhja: sum("tyhja"), poissa: sum("poissa"), ryhmat };
}

const lyhennaLaki = s => String(s || "").replace(/^Hallituksen esitys eduskunnalle\s+/i, "Hallituksen esitys: ").replace(/\s+/g, " ").trim();

// ---------- Durable Object ----------
export class Faktapiste extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS kayttajat(id INTEGER PRIMARY KEY, email TEXT UNIQUE, nimi TEXT UNIQUE COLLATE NOCASE, luotu INTEGER, esto INTEGER DEFAULT 0);
      CREATE TABLE IF NOT EXISTS sessiot(t TEXT PRIMARY KEY, kayttaja INTEGER, vanhenee INTEGER);
      CREATE TABLE IF NOT EXISTS linkit(t TEXT PRIMARY KEY, email TEXT, vanhenee INTEGER);
      CREATE TABLE IF NOT EXISTS postit(id INTEGER PRIMARY KEY, kayttaja INTEGER, lahde TEXT, teksti TEXT, kortti TEXT, vanhempi INTEGER, luotu INTEGER,
        tykkaykset INTEGER DEFAULT 0, vastaukset INTEGER DEFAULT 0, ilmoitukset INTEGER DEFAULT 0, piilotettu INTEGER DEFAULT 0, ext TEXT UNIQUE);
      CREATE INDEX IF NOT EXISTS postit_aika ON postit(luotu);
      CREATE INDEX IF NOT EXISTS postit_vanhempi ON postit(vanhempi);
      CREATE TABLE IF NOT EXISTS tykkaykset(posti INTEGER, kayttaja INTEGER, PRIMARY KEY(posti, kayttaja));
      CREATE TABLE IF NOT EXISTS ilmoitukset(posti INTEGER, kayttaja INTEGER, syy TEXT, luotu INTEGER, PRIMARY KEY(posti, kayttaja));
      CREATE TABLE IF NOT EXISTS rajat(avain TEXT PRIMARY KEY, n INTEGER, vanhenee INTEGER);
      CREATE TABLE IF NOT EXISTS asetukset(k TEXT PRIMARY KEY, v TEXT);
      CREATE TABLE IF NOT EXISTS kutsut(koodi TEXT PRIMARY KEY, kayttoja INTEGER DEFAULT 0, max INTEGER, luotu INTEGER);
      CREATE TABLE IF NOT EXISTS nahdyt(posti INTEGER, katsoja TEXT, luotu INTEGER, PRIMARY KEY(posti, katsoja));
      CREATE INDEX IF NOT EXISTS nahdyt_katsoja ON nahdyt(katsoja, luotu);
      CREATE TABLE IF NOT EXISTS kuvat(id INTEGER PRIMARY KEY, kayttaja INTEGER, posti INTEGER, data BLOB, tyyppi TEXT, w INTEGER, h INTEGER, luotu INTEGER);
      CREATE INDEX IF NOT EXISTS kuvat_posti ON kuvat(posti);
      CREATE TABLE IF NOT EXISTS videot(id INTEGER PRIMARY KEY, kayttaja INTEGER, posti INTEGER, avain TEXT, tyyppi TEXT, koko INTEGER, w INTEGER, h INTEGER, kesto REAL, kansi BLOB, luotu INTEGER);
      CREATE INDEX IF NOT EXISTS videot_posti ON videot(posti);
      CREATE TABLE IF NOT EXISTS seuraukset(seuraaja INTEGER, seurattava INTEGER, luotu INTEGER, PRIMARY KEY(seuraaja, seurattava));
      CREATE INDEX IF NOT EXISTS seuraukset_kohde ON seuraukset(seurattava);`);
    // nimet eivät ole enää yksilöllisiä (oikeat nimet voivat toistua): taulu rakennetaan kerran uudelleen
    if ((this.sql.exec("SELECT v FROM asetukset WHERE k='skeema'").toArray()[0] || {}).v !== "2") {
      this.sql.exec(`CREATE TABLE IF NOT EXISTS kayttajat2(id INTEGER PRIMARY KEY, email TEXT UNIQUE, nimi TEXT, luotu INTEGER, esto INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO kayttajat2(id, email, nimi, luotu, esto) SELECT id, email, nimi, luotu, esto FROM kayttajat;
        DROP TABLE kayttajat; ALTER TABLE kayttajat2 RENAME TO kayttajat;
        INSERT OR REPLACE INTO asetukset VALUES('skeema', '2');`);
    }
    for (const a of ["ALTER TABLE postit ADD COLUMN nakymat INTEGER DEFAULT 0", "ALTER TABLE postit ADD COLUMN kunta TEXT", "ALTER TABLE postit ADD COLUMN muokattu INTEGER"]) { try { this.sql.exec(a); } catch {} }
  }
  yksi(q, ...p) { return this.sql.exec(q, ...p).toArray()[0] || null; }
  kaikki(q, ...p) { return this.sql.exec(q, ...p).toArray(); }

  raja(avain, max, sek) {
    const t = nyt(), r = this.yksi("SELECT n, vanhenee FROM rajat WHERE avain=?", avain);
    if (!r || r.vanhenee < t) { this.sql.exec("INSERT OR REPLACE INTO rajat VALUES(?,?,?)", avain, 1, t + sek * 1000); return true; }
    if (r.n >= max) return false;
    this.sql.exec("UPDATE rajat SET n=n+1 WHERE avain=?", avain); return true;
  }

  kayttaja(req) {
    const t = evaste(req, "fp_s");
    if (!t) return null;
    const k = this.yksi("SELECT k.id, k.email, k.nimi, k.esto FROM sessiot s JOIN kayttajat k ON k.id=s.kayttaja WHERE s.t=? AND s.vanhenee>?", t, nyt());
    if (k) { k.admin = ADMIN.includes(k.email); k.nimiOk = oikeaNimi(k.nimi); }
    return k;
  }

  async fetch(req) {
    const u = new URL(req.url), p = u.pathname, m = req.method;
    try {
      if (p === "/_sisaanluku") return json(await this.sisaanluku());
      if (p === "/api/hallinta/sisaanluku" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) return json(await this.sisaanluku());
      if (p === "/api/hallinta/tila" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA)
        return json({ postit: this.kaikki("SELECT lahde, COUNT(*) AS n FROM postit GROUP BY lahde"), kayttajat: this.yksi("SELECT COUNT(*) AS n FROM kayttajat").n });
      if (p === "/api/hallinta/kutsu" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        const d = await req.json().catch(() => ({})); const koodi = satunnainen(5);
        this.sql.exec("INSERT INTO kutsut(koodi, max, luotu) VALUES(?,?,?)", koodi, Math.min(500, +d.max || 20), nyt());
        return json({ koodi, linkki: "https://faktapiste.fi/?kutsu=" + koodi });
      }
      // Microsoft Advertising -kirjautuminen (ylläpitäjän kertaluonteinen lupa); avaimet vain holviin.
      if (p === "/api/oauth/microsoft/alku" && m === "GET") {
        const ts = String(nyt()); const tila = ts + "." + (await tiiviste(ts + (this.env.HALLINTA || ""))).slice(0, 24);
        const q = new URLSearchParams({ client_id: MS_CLIENT, response_type: "code", redirect_uri: MS_PALUU, scope: "https://ads.microsoft.com/msads.manage offline_access", state: tila, prompt: "select_account" });
        return Response.redirect("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + q, 302);
      }
      if (p === "/api/oauth/microsoft" && m === "GET") {
        const sivu = (t, s = 200) => new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><body style="font:18px system-ui;padding:40px;max-width:520px;margin:auto"><h2>Faktapiste</h2><p>${t}</p></body>`, { status: s, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
        const [ts, sig] = String(u.searchParams.get("state") || "").split(".");
        const ok = ts && sig && sig === (await tiiviste(ts + (this.env.HALLINTA || ""))).slice(0, 24) && nyt() - Number(ts) < 2 * 3600e3;
        if (!ok) return sivu('Kirjautumislinkki on vanhentunut. <a href="/api/oauth/microsoft/alku">Aloita uudelleen</a>.', 400);
        if (!u.searchParams.get("code")) return sivu("Lupaa ei annettu: " + puhdas(u.searchParams.get("error_description") || u.searchParams.get("error")).slice(0, 200), 400);
        const v = await (await fetch("https://login.microsoftonline.com/common/oauth2/v2.0/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ client_id: MS_CLIENT, client_secret: this.env.MSADS_CLIENT_SECRET || "", grant_type: "authorization_code", code: u.searchParams.get("code"), redirect_uri: MS_PALUU, scope: "https://ads.microsoft.com/msads.manage offline_access" }) })).json();
        if (!v.refresh_token) return sivu("Avaimen vaihto epäonnistui: " + puhdas(v.error_description || v.error).slice(0, 300), 400);
        this.sql.exec("INSERT OR REPLACE INTO asetukset VALUES(?,?)", "holvi:msads_refresh", v.refresh_token);
        await telegram(this.env, "🔑 Microsoft Advertising -lupa tallennettu Faktapisteen holviin.");
        return sivu("Valmis! Microsoft Advertising on nyt yhdistetty. Voit sulkea tämän sivun.");
      }
      if (p === "/api/hallinta/holvi" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        // Ylläpidon salaisuusholvi (esim. mainostilien kirjautumisavaimet); ei koskaan julkisesti luettavissa.
        const d = await req.json(); const k = "holvi:" + String(d.nimi || "");
        if (typeof d.arvo === "string") { this.sql.exec("INSERT OR REPLACE INTO asetukset VALUES(?,?)", k, d.arvo); return json({ ok: true }); }
        const r = this.yksi("SELECT v FROM asetukset WHERE k=?", k); return json({ arvo: r ? r.v : null });
      }
      if (p === "/api/hallinta/fakta" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        const d = await req.json(); return await this.fakta({ id: 0 }, d);
      }
      const minä = this.kayttaja(req);
      const lukija = this.lukija(req, minä);
      if (p === "/api/syote" && m === "GET") return json(this.syote(u, minä, lukija));
      if (p === "/api/nahty" && m === "POST") return json(this.nahty(lukija, await req.json().catch(() => ({}))));
      if (p.startsWith("/api/kuva/") && m === "GET") return this.naytaKuva(+p.split("/")[3]);
      if (p === "/api/kuva" && m === "POST") return await this.lataaKuva(req, minä);
      if (p === "/api/video" && m === "POST") return await this.lataaVideo(req, minä);
      if (p === "/api/video/kansi" && m === "POST") return await this.lataaKansi(req, minä, +u.searchParams.get("id"));
      const vm = p.match(/^\/api\/video\/(\d+)(\/kansi)?$/);
      if (vm && m === "GET") return vm[2] ? this.naytaKansi(+vm[1]) : await this.naytaVideo(+vm[1], req);
      if (p.startsWith("/api/posti/") && m === "GET") return json(this.ketju(+p.split("/")[3], minä));
      if (p === "/api/mina") return json({ kayttaja: minä ? { nimi: minä.nimi, nimiOk: minä.nimiOk, admin: minä.admin } : null,
        tilasto: minä && minä.admin ? { kayttajat: this.yksi("SELECT COUNT(*) AS n FROM kayttajat").n, nimelliset: this.yksi("SELECT COUNT(*) AS n FROM kayttajat WHERE nimi IS NOT NULL").n,
          kirjoittajat: this.yksi("SELECT COUNT(DISTINCT kayttaja) AS n FROM postit WHERE kayttaja IS NOT NULL").n, lukijat7: this.yksi("SELECT COUNT(DISTINCT katsoja) AS n FROM nahdyt WHERE luotu>?", nyt() - 7 * 86400e3).n } : null, kirjautuminen: this.env.KIRJAUTUMINEN === "auki", video: !!this.env.VIDEOT, testi: this.env.KIRJAUTUMINEN === "testi" });
      if (p === "/api/kirjaudu" && m === "POST") return await this.kirjaudu(req);
      if (p === "/api/vahvista" && m === "GET") return this.vahvista(u);
      if (p === "/api/ulos" && m === "POST") { const t = evaste(req, "fp_s"); if (t) this.sql.exec("DELETE FROM sessiot WHERE t=?", t); return json({ ok: true }, 200, { "set-cookie": "fp_s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" }); }
      if (m !== "POST") return virhe("Tuntematon osoite", 404);
      if (!minä) return virhe("Kirjaudu ensin.", 401);
      if (minä.esto) return virhe("Tilisi on suljettu.", 403);
      const d = await req.json().catch(() => ({}));
      if (p === "/api/nimi") return await this.asetaNimi(minä, d);
      if (!minä.nimiOk) return virhe("Lisää ensin oma nimesi (etu- ja sukunimi).", 400);
      if (p === "/api/posti") return await this.uusiPosti(minä, d, lukija);
      if (p === "/api/tykkaa") return this.tykkaa(minä, d);
      if (p === "/api/seuraa") return this.seuraa(minä, d);
      if (p === "/api/ilmoita") return await this.ilmoita(minä, d);
      if (p === "/api/poista") return this.poista(minä, d);
      if (p === "/api/muokkaa") {
        const r = this.yksi("SELECT kayttaja, piilotettu FROM postit WHERE id=?", +d.id);
        if (!r || r.piilotettu) return virhe("Postausta ei löytynyt.");
        if (r.kayttaja !== minä.id) return virhe("Voit muokata vain omia postauksiasi.", 403);
        const t = puhdas(d.teksti).replace(/\n{3,}/g, "\n\n");
        const kuvat = Array.isArray(d.kuvat) ? this.liitaKuvat(+d.id, minä, d.kuvat) : this.kuvaIdt(+d.id);
        if (t.length < 2 && !kuvat.length) return virhe("Kirjoita jotain tai lisää kuva.");
        if (t.length > PITUUS) return virhe("Teksti on liian pitkä.");
        this.sql.exec("UPDATE postit SET teksti=?, muokattu=? WHERE id=?", t, nyt(), +d.id);
        return json({ ok: true, kuvat: this.kuvaIdt(+d.id) });
      }
      if (p === "/api/fakta") return await this.fakta(minä, d);
      if (p === "/api/palauta" && minä.admin) { this.sql.exec("UPDATE postit SET piilotettu=0, ilmoitukset=0 WHERE id=?", +d.id); return json({ ok: true }); }
      return virhe("Tuntematon osoite", 404);
    } catch (e) {
      return virhe("Jokin meni pieleen: " + e.message, 500);
    }
  }

  // Lukijatunniste: kirjautuneelle käyttäjätunnus, muille selaimen satunnainen tunniste (ei henkilötieto, ei mainontaan).
  lukija(req, minä) {
    if (minä) return "k" + minä.id;
    const v = (req.headers.get("x-lukija") || "").replace(/[^a-f0-9]/g, "").slice(0, 32);
    return v.length === 32 ? "v" + v : null;
  }
  nahty(lukija, d) {
    if (!lukija) return { ok: false };
    if (!this.raja("n:" + lukija, 400, 3600)) return { ok: false };
    let n = 0;
    for (const id of (Array.isArray(d.idt) ? d.idt : []).slice(0, 60).map(Number).filter(Boolean)) {
      const c = this.sql.exec("INSERT OR IGNORE INTO nahdyt VALUES(?,?,?)", id, lukija, nyt());
      if (c.rowsWritten > 0) { this.sql.exec("UPDATE postit SET nakymat=nakymat+1 WHERE id=?", id); n++; }
    }
    return { ok: true, uusia: n };
  }

  // ---- kirjautuminen sähköpostilinkillä ----
  async kirjaudu(req) {
    if (this.env.KIRJAUTUMINEN === "pois") return virhe("Kirjautuminen avataan pian.", 503);
    const d = await req.json().catch(() => ({}));
    const email = puhdas(d.email).toLowerCase();
    if (!/^[^\s@]{1,64}@[^\s@]+\.[a-z]{2,}$/.test(email) || email.length > 120) return virhe("Tarkista sähköpostiosoite.");
    if (this.env.KIRJAUTUMINEN !== "auki" && !TESTAAJAT.includes(email) && !this.yksi("SELECT id FROM kayttajat WHERE email=?", email)) {
      // Beta: uusi käyttäjä tarvitsee voimassa olevan kutsukoodin
      const k = this.yksi("SELECT koodi FROM kutsut WHERE koodi=? AND kayttoja<max", String(d.kutsu || ""));
      if (!k) return virhe("Keskustelu on beta-testissä. Tarvitset kutsulinkin, jotta voit liittyä.", 403);
      this.sql.exec("UPDATE kutsut SET kayttoja=kayttoja+1 WHERE koodi=?", k.koodi);
    }
    const ip = await tiiviste((req.headers.get("cf-connecting-ip") || "") + "fp");
    if (!this.raja("lk:" + email, 4, 3600) || !this.raja("li:" + ip, 15, 3600)) return virhe("Liian monta yritystä. Yritä hetken päästä uudelleen.", 429);
    const t = satunnainen();
    this.sql.exec("INSERT INTO linkit VALUES(?,?,?)", await tiiviste(t), email, nyt() + 30 * 60e3);
    const linkki = `https://faktapiste.fi/api/vahvista?t=${t}`;
    const html = `<div style="max-width:520px;margin:0 auto;font:16px/1.55 -apple-system,Segoe UI,sans-serif;color:#1b1228">
<div style="background:#160a26;color:#fff;padding:16px 20px;border-radius:12px;font:700 22px Impact,sans-serif;letter-spacing:.03em">FAKTA<span style="color:#f5c542">PISTE.</span></div>
<p>Hei! Kirjaudu Faktapisteeseen alla olevasta painikkeesta. Linkki on voimassa 30 minuuttia.</p>
<p><a href="${linkki}" style="display:inline-block;background:#f5c542;color:#160a26;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:700">Kirjaudu Faktapisteeseen</a></p>
<p style="color:#65597a;font-size:14px">Jos et pyytänyt tätä viestiä, voit jättää sen huomiotta. Kukaan ei pääse tilillesi ilman tätä linkkiä.</p></div>`;
    const r = await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST", headers: { "api-key": this.env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ sender: { email: "miika@eduskuntaseuranta.fi", name: "Faktapiste" }, to: [{ email }], subject: "Kirjautumislinkki Faktapisteeseen", htmlContent: html }) });
    if (!r.ok) return virhe("Viestin lähetys ei onnistunut. Yritä myöhemmin.", 502);
    return json({ ok: true });
  }
  async vahvista(u) {
    const h = await tiiviste(u.searchParams.get("t") || "");
    const l = this.yksi("SELECT email, vanhenee FROM linkit WHERE t=?", h);
    this.sql.exec("DELETE FROM linkit WHERE t=? OR vanhenee<?", h, nyt());
    if (!l || l.vanhenee < nyt()) return new Response(null, { status: 302, headers: { location: "/?kirjautuminen=vanhentunut" } });
    let k = this.yksi("SELECT id FROM kayttajat WHERE email=?", l.email);
    if (!k) { this.sql.exec("INSERT INTO kayttajat(email, luotu) VALUES(?,?)", l.email, nyt()); k = this.yksi("SELECT id FROM kayttajat WHERE email=?", l.email); }
    const s = satunnainen();
    this.sql.exec("INSERT INTO sessiot VALUES(?,?,?)", s, k.id, nyt() + 60 * 86400e3);
    this.sql.exec("DELETE FROM sessiot WHERE vanhenee<?", nyt());
    return new Response(null, { status: 302, headers: { location: "/?tervetuloa=1", "set-cookie": `fp_s=${s}; Path=/; Max-Age=${60 * 86400}; HttpOnly; Secure; SameSite=Lax` } });
  }
  async asetaNimi(minä, d) {
    const n = isot(puhdas(d.nimi).replace(/\s+/g, " "));
    if (!oikeaNimi(n)) return virhe("Kirjoita oma etu- ja sukunimesi, esimerkiksi Matti Virtanen.");
    if (/faktapiste|ylläpito|moderaattori/i.test(n)) return virhe("Tätä nimeä ei voi käyttää.");
    this.sql.exec("UPDATE kayttajat SET nimi=? WHERE id=?", n, minä.id);
    if (!minä.nimiOk) {
      const yht = this.yksi("SELECT COUNT(*) AS n FROM kayttajat WHERE nimi IS NOT NULL").n;
      await telegram(this.env, `👤 Uusi käyttäjä liittyi Faktapisteeseen: ${n}\nKäyttäjiä yhteensä: ${yht}\nhttps://faktapiste.fi`);
    }
    return json({ ok: true, nimi: n });
  }

  // ---- syöte ----
  muoto(r, minä) {
    let k = null; try { k = r.kortti ? JSON.parse(r.kortti) : null; } catch {}
    return { id: r.id, nimi: r.nimi || null, lahde: r.lahde, teksti: r.piilotettu ? "" : r.teksti, kortti: r.piilotettu ? null : k, vanhempi: r.vanhempi, luotu: r.luotu,
      tykkaykset: r.tykkaykset, vastaukset: r.vastaukset, piilotettu: !!r.piilotettu, oma: !!(minä && r.kayttaja === minä.id),
      kuvat: r.piilotettu ? [] : this.kuvaIdt(r.id), nakymat: r.nakymat || 0, muokattu: r.muokattu || null, kunta: r.kunta || null, syy: r._syy || null, taattu: TAATTU,
      tykkasin: !!(minä && this.yksi("SELECT 1 AS x FROM tykkaykset WHERE posti=? AND kayttaja=?", r.id, minä.id)),
      kirjoittaja: r.kayttaja || null,
      video: r.piilotettu ? null : this.videoTieto(r.id),
      seuraan: !!(minä && r.kayttaja && r.kayttaja !== minä.id && this.yksi("SELECT 1 AS x FROM seuraukset WHERE seuraaja=? AND seurattava=?", minä.id, r.kayttaja)) };
  }
  syote(u, minä, lukija) {
    const tab = u.searchParams.get("tab") || "sinulle", sivu = Math.max(0, +u.searchParams.get("sivu") || 0);
    const pohja = "SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.vanhempi IS NULL AND p.piilotettu=0" + (nyt() < ST_TAUKO_ASTI ? " AND p.lahde<>'suomitanaan'" : "");
    const ulos = (rivit, lisa = {}) => ({ postit: rivit.map(r => this.muoto(r, minä)), ...lisa });
    if (tab === "seuratut") {
      if (!minä) return ulos([], { kirjauduSeuraa: true });
      const r = this.kaikki(pohja + " AND p.kayttaja IN (SELECT seurattava FROM seuraukset WHERE seuraaja=?) ORDER BY p.luotu DESC LIMIT 30 OFFSET ?", minä.id, sivu * 30);
      return ulos(r, { lisaa: r.length === 30, seurattuja: this.yksi("SELECT COUNT(*) AS n FROM seuraukset WHERE seuraaja=?", minä.id).n });
    }
    if (tab === "uusimmat") { const r = this.kaikki(pohja + " ORDER BY p.luotu DESC LIMIT 30 OFFSET ?", sivu * 30); return ulos(r, { lisaa: r.length === 30 }); }
    if (tab === "lahella") {
      const kunta = KUNTA.get(String(u.searchParams.get("kunta") || "").toLowerCase());
      if (!kunta) return ulos([], { kuntaPuuttuu: true });
      // oman paikkakunnan postaukset + uutiset, joissa paikkakunta mainitaan (taivutusmuodot: vartalo ilman viimeistä vokaalia)
      const vartalo = kunta.toLowerCase().replace(/[aeiouyäö]$/, "");
      const r = this.kaikki(pohja + " AND (p.kunta=? OR (p.kayttaja IS NULL AND lower(p.kortti) LIKE ?)) ORDER BY p.luotu DESC LIMIT 30 OFFSET ?", kunta, "%" + vartalo + "%", sivu * 30);
      for (const x of r) x._syy = x.kunta === kunta ? `Kirjoitettu paikkakunnalla ${kunta}.` : `Uutinen mainitsee paikkakunnan ${kunta}.`;
      return ulos(r, { lisaa: r.length === 30, kunta });
    }
    // Sinulle: säädettävä algoritmi, taattu yleisö ja syöte, joka loppuu.
    const saato = String(u.searchParams.get("s") || "").split(",");
    const kerroin = luokka => { const i = "kumhe".indexOf(luokka); const v = Number(saato[i]); return KERROIN[Number.isInteger(v) && v >= 0 && v <= 2 ? v : 1]; };
    const t = nyt();
    const ehd = this.kaikki(pohja + " AND p.luotu>? ORDER BY p.luotu DESC LIMIT 400", t - 4 * 86400e3);
    const seuratut = new Set(minä ? this.kaikki("SELECT seurattava FROM seuraukset WHERE seuraaja=?", minä.id).map(x => x.seurattava) : []);
    const nahdyt = new Set(lukija ? this.kaikki("SELECT posti FROM nahdyt WHERE katsoja=? AND luotu>?", lukija, t - 5 * 86400e3).map(x => x.posti) : []);
    const tanaan = lukija ? this.yksi("SELECT COUNT(*) AS n FROM nahdyt WHERE katsoja=? AND luotu>?", lukija, t - 18 * 3600e3).n : 0;
    const uudet = [], muut = [];
    for (const r of ehd) {
      if (nahdyt.has(r.id) || (minä && r.kayttaja === minä.id && r.nakymat >= TAATTU)) continue;
      const luokka = LUOKKA[r.lahde] || "u", k = kerroin(luokka);
      if (k === 0) continue;
      const h = (t - r.luotu) / 3600e3;
      // Taattu yleisö: alle TAATTU lukijan saaneet tuoreet käyttäjäpostaukset nostetaan kärkeen.
      if (r.kayttaja && r.nakymat < TAATTU && h < 48) {
        r._syy = `Uusi postaus, jonka on nähnyt vasta ${r.nakymat} ${r.nakymat === 1 ? "lukija" : "lukijaa"}. Faktapiste näyttää jokaisen postauksen vähintään ${TAATTU} ihmiselle, vaikka kirjoittajalla ei olisi seuraajia.`;
        r._p = 1000 - r.nakymat; uudet.push(r); continue;
      }
      const [paino, puoli] = r.kayttaja ? [4, 12] : ({ eduskunta: [0.9, 20], suomitanaan: [1.2, 8], korjausvahti: [1, 8], keraysvahti: [0.8, 12], faktapiste: [2, 36] })[r.lahde] || [1, 8];
      r._p = k * paino * (1 + r.tykkaykset * 2 + r.vastaukset * 3) * Math.pow(0.5, h / puoli) * (seuratut.has(r.kayttaja) ? 3 : 1);
      const nimi = { suomitanaan: "uutisia", korjausvahti: "otsikkomuutoksia", keraysvahti: "huijausvaroituksia", eduskunta: "päätöksiä" }[r.lahde];
      r._syy = r.kayttaja
        ? (r.tykkaykset + r.vastaukset > 0 ? `Keskustelu, jossa ${r.tykkaykset} tykkäystä ja ${r.vastaukset} vastausta.` : "Tuore keskustelu.") + (k > 1 ? " Valitsit: enemmän keskusteluja." : "")
        : r.lahde === "faktapiste" ? "Uusi palvelu Faktapisteeltä." : `Tuore ${r.lahde === "eduskunta" ? "päätös" : r.lahde === "suomitanaan" ? "uutinen" : r.lahde === "korjausvahti" ? "otsikkomuutos" : "huijausvaroitus"}.` + (r.tykkaykset + r.vastaukset > 0 ? ` Herättänyt keskustelua (${r.vastaukset} vastausta).` : "") + (k > 1 ? ` Valitsit: enemmän ${nimi}.` : "");
      if (seuratut.has(r.kayttaja)) r._syy = "Seuraat kirjoittajaa. " + r._syy;
      muut.push(r);
    }
    uudet.sort((a, b) => b._p - a._p); muut.sort((a, b) => b._p - a._p);
    // monipuolisuus: sama lähde enintään kahdesti peräkkäin
    const jarj = [], jono = [...muut];
    while (jono.length) {
      const i = jono.findIndex(r => !(jarj.length >= 2 && jarj.at(-1).lahde === r.lahde && jarj.at(-2).lahde === r.lahde && r.lahde !== "kayttaja"));
      jarj.push(jono.splice(i < 0 ? 0 : i, 1)[0]);
    }
    // uudet äänet joka toiseen paikkaan alussa
    const tulos = [];
    while ((uudet.length || jarj.length) && tulos.length < SYOTE_MAX) {
      if (uudet.length && (tulos.length % 2 === 0 || !jarj.length)) tulos.push(uudet.shift()); else if (jarj.length) tulos.push(jarj.shift());
    }
    return ulos(tulos, { loppu: true, tanaan });
  }
  ketju(id, minä) {
    const r = this.yksi("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.id=?", id);
    if (!r) return { virhe: "Postausta ei löytynyt." };
    const vanh = r.vanhempi ? this.yksi("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.id=?", r.vanhempi) : null;
    const v = this.kaikki("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.vanhempi=? ORDER BY p.tykkaykset DESC, p.luotu ASC LIMIT 200", id);
    return { posti: this.muoto(r, minä), vanhempi: vanh ? this.muoto(vanh, minä) : null, vastaukset: v.map(x => this.muoto(x, minä)) };
  }

  // ---- kuvat ----
  // Selain pienentää kuvan (max 1600 px) ja poistaa samalla sijainti- ym. metatiedot ennen latausta.
  kuvaIdt(posti) { return this.kaikki("SELECT id, w, h FROM kuvat WHERE posti=? ORDER BY id", posti).map(k => ({ id: k.id, w: k.w, h: k.h })); }
  async lataaKuva(req, minä) {
    if (!minä) return virhe("Kirjaudu ensin.", 401);
    if (minä.esto) return virhe("Tilisi on suljettu.", 403);
    if (!minä.nimiOk) return virhe("Lisää ensin oma nimesi (etu- ja sukunimi).", 400);
    const tyyppi = (req.headers.get("content-type") || "").split(";")[0].trim();
    if (!["image/jpeg", "image/png", "image/webp"].includes(tyyppi)) return virhe("Kuvan muoto ei kelpaa.");
    if (!this.raja("kuva:" + minä.id, 40, 3600)) return virhe("Olet ladannut paljon kuvia tunnin sisällä. Pidä pieni tauko.", 429);
    const data = new Uint8Array(await req.arrayBuffer());
    if (data.length < 100) return virhe("Kuva on tyhjä.");
    if (data.length > KUVA_MAX) return virhe("Kuva on liian suuri.");
    const w = Math.min(10000, +req.headers.get("x-leveys") || 0), h = Math.min(10000, +req.headers.get("x-korkeus") || 0);
    // liittämättömät kuvat siivotaan vuorokauden kuluttua
    this.sql.exec("DELETE FROM kuvat WHERE posti IS NULL AND luotu<?", nyt() - 86400e3);
    this.sql.exec("INSERT INTO kuvat(kayttaja, posti, data, tyyppi, w, h, luotu) VALUES(?,?,?,?,?,?,?)", minä.id, null, data, tyyppi, w, h, nyt());
    return json({ ok: true, id: this.yksi("SELECT last_insert_rowid() AS id").id, w, h });
  }
  // Asettaa postauksen kuviksi annetut: omat liittämättömät liitetään, listalta puuttuvat poistetaan.
  liitaKuvat(posti, minä, idt) {
    const halutut = [...new Set(idt.map(Number).filter(Boolean))].slice(0, KUVAT_MAX);
    for (const k of this.kaikki("SELECT id FROM kuvat WHERE posti=?", posti)) if (!halutut.includes(k.id)) this.sql.exec("DELETE FROM kuvat WHERE id=?", k.id);
    for (const id of halutut) this.sql.exec("UPDATE kuvat SET posti=? WHERE id=? AND kayttaja=? AND posti IS NULL", posti, id, minä.id);
    return this.kuvaIdt(posti);
  }
  // ---- videot (Cloudflare R2) ----
  // Video tallennetaan R2:een sellaisenaan. Selain ottaa videosta kansikuvan, joka näkyy myös linkin esikatselussa.
  videoTieto(posti) {
    const v = this.yksi("SELECT id, w, h, kesto, kansi IS NOT NULL AS kansi FROM videot WHERE posti=? ORDER BY id LIMIT 1", posti);
    return v ? { id: v.id, w: v.w, h: v.h, kesto: v.kesto, kansi: !!v.kansi } : null;
  }
  poistaVideot(rivit) {
    for (const v of rivit) { try { this.env.VIDEOT && this.ctx.waitUntil(this.env.VIDEOT.delete(v.avain)); } catch {} this.sql.exec("DELETE FROM videot WHERE id=?", v.id); }
  }
  async lataaVideo(req, minä) {
    if (!this.env.VIDEOT) return virhe("Videoiden lataus ei ole vielä käytössä.", 503);
    if (!minä) return virhe("Kirjaudu ensin.", 401);
    if (minä.esto) return virhe("Tilisi on suljettu.", 403);
    if (!minä.nimiOk) return virhe("Lisää ensin oma nimesi (etu- ja sukunimi).", 400);
    const tyyppi = (req.headers.get("content-type") || "").split(";")[0].trim();
    if (!VIDEO_TYYPIT.includes(tyyppi)) return virhe("Videon muoto ei kelpaa. Käytä MP4-, MOV- tai WebM-videota.");
    const koko = +req.headers.get("content-length") || 0;
    if (koko < 1000) return virhe("Video on tyhjä.");
    if (koko > VIDEO_MAX) return virhe("Video on liian suuri (enintään 100 Mt).");
    const kesto = Math.max(0, +req.headers.get("x-kesto") || 0);
    if (kesto > VIDEO_KESTO + 1) return virhe("Video on liian pitkä (enintään 3 minuuttia).");
    if (!this.raja("video:" + minä.id, 10, 86400)) return virhe("Olet ladannut tänään jo 10 videota. Jatka huomenna.", 429);
    // liittämättömät videot siivotaan vuorokauden kuluttua
    this.poistaVideot(this.kaikki("SELECT id, avain FROM videot WHERE posti IS NULL AND luotu<?", nyt() - 86400e3));
    const avain = "v/" + minä.id + "/" + satunnainen();
    const { readable, writable } = new FixedLengthStream(koko);
    const putki = req.body.pipeTo(writable);
    await Promise.all([this.env.VIDEOT.put(avain, readable, { httpMetadata: { contentType: tyyppi } }), putki]);
    const w = Math.min(10000, +req.headers.get("x-leveys") || 0), h = Math.min(10000, +req.headers.get("x-korkeus") || 0);
    this.sql.exec("INSERT INTO videot(kayttaja, posti, avain, tyyppi, koko, w, h, kesto, luotu) VALUES(?,?,?,?,?,?,?,?,?)", minä.id, null, avain, tyyppi, koko, w, h, kesto, nyt());
    return json({ ok: true, id: this.yksi("SELECT last_insert_rowid() AS id").id });
  }
  async lataaKansi(req, minä, id) {
    if (!minä) return virhe("Kirjaudu ensin.", 401);
    if ((req.headers.get("content-type") || "").split(";")[0].trim() !== "image/jpeg") return virhe("Kansikuvan muoto ei kelpaa.");
    const data = new Uint8Array(await req.arrayBuffer());
    if (data.length < 100 || data.length > 600000) return virhe("Kansikuva ei kelpaa.");
    this.sql.exec("UPDATE videot SET kansi=? WHERE id=? AND kayttaja=?", data, id, minä.id);
    return json({ ok: true });
  }
  async naytaVideo(id, req) {
    const v = this.yksi("SELECT v.avain, v.tyyppi FROM videot v JOIN postit p ON p.id=v.posti WHERE v.id=? AND p.piilotettu=0", id);
    if (!v || !this.env.VIDEOT) return new Response("Videota ei löytynyt", { status: 404, headers: { "cache-control": "no-store" } });
    const o = await this.env.VIDEOT.get(v.avain, { range: req.headers });
    if (!o) return new Response("Videota ei löytynyt", { status: 404 });
    const h = new Headers({ "content-type": v.tyyppi, "accept-ranges": "bytes", "cache-control": "public, max-age=86400", "x-content-type-options": "nosniff", etag: o.httpEtag });
    if (o.range && req.headers.get("range")) {
      const alku = o.range.offset || 0, pit = o.range.length ?? (o.size - alku);
      h.set("content-range", `bytes ${alku}-${alku + pit - 1}/${o.size}`); h.set("content-length", String(pit));
      return new Response(o.body, { status: 206, headers: h });
    }
    h.set("content-length", String(o.size));
    return new Response(o.body, { headers: h });
  }
  naytaKansi(id) {
    const v = this.yksi("SELECT v.kansi FROM videot v JOIN postit p ON p.id=v.posti WHERE v.id=? AND p.piilotettu=0 AND v.kansi IS NOT NULL", id);
    if (!v) return new Response("Ei kansikuvaa", { status: 404, headers: { "cache-control": "no-store" } });
    return new Response(v.kansi, { headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=86400", "x-content-type-options": "nosniff" } });
  }
  naytaKuva(id) {
    const k = this.yksi("SELECT k.data, k.tyyppi FROM kuvat k JOIN postit p ON p.id=k.posti WHERE k.id=? AND p.piilotettu=0", id);
    if (!k) return new Response("Kuvaa ei löytynyt", { status: 404, headers: { "cache-control": "no-store" } });
    return new Response(k.data, { headers: { "content-type": k.tyyppi, "cache-control": "private, max-age=3600", "x-content-type-options": "nosniff", "content-security-policy": "default-src 'none'" } });
  }

  // ---- kirjoittaminen ----
  async uusiPosti(minä, d, lukija) {
    const teksti = puhdas(d.teksti).replace(/\n{3,}/g, "\n\n");
    const kuvaPyynto = Array.isArray(d.kuvat) ? d.kuvat.map(Number).filter(Boolean).slice(0, KUVAT_MAX) : [];
    const videoPyynto = +d.video || 0;
    if (teksti.length < 2 && !kuvaPyynto.length && !videoPyynto) return virhe("Kirjoita jotain tai lisää kuva tai video.");
    if (teksti.length > PITUUS) return virhe("Teksti on liian pitkä.");
    if (!this.raja("p:" + minä.id, 15, 3600)) return virhe("Olet kirjoittanut paljon tunnin sisällä. Pidä pieni tauko.", 429);
    const vanhempi = d.vanhempi ? +d.vanhempi : null;
    if (vanhempi && !this.yksi("SELECT id FROM postit WHERE id=? AND piilotettu=0", vanhempi)) return virhe("Postausta ei enää ole.");
    let kortti = null;
    if (d.kortti && typeof d.kortti === "object" && d.kortti.tyyppi === "fakta") {
      const k = this.yksi("SELECT v FROM asetukset WHERE k=?", "fakta:" + String(d.kortti.avain || ""));
      if (k) kortti = k.v;
    }
    const kunta = KUNTA.get(String(d.kunta || "").toLowerCase()) || null;
    this.sql.exec("INSERT INTO postit(kayttaja, lahde, teksti, kortti, vanhempi, luotu, kunta) VALUES(?,?,?,?,?,?,?)", minä.id, "kayttaja", teksti, kortti, vanhempi, nyt(), kunta);
    const id = this.yksi("SELECT last_insert_rowid() AS id").id;
    if (kuvaPyynto.length) this.liitaKuvat(id, minä, kuvaPyynto);
    if (videoPyynto) this.sql.exec("UPDATE videot SET posti=? WHERE id=? AND kayttaja=? AND posti IS NULL", id, videoPyynto, minä.id);
    if (lukija) this.sql.exec("INSERT OR IGNORE INTO nahdyt VALUES(?,?,?)", id, lukija, nyt()); // oma postaus ei kasvata lukijamäärää
    if (vanhempi) this.sql.exec("UPDATE postit SET vastaukset=vastaukset+1 WHERE id=?", vanhempi);
    return json({ ok: true, id });
  }
  async tarkista(teksti) {
    if (/(https?:\/\/\S+.*){4,}/i.test(teksti)) return { ok: false, syy: "liikaa linkkejä." };
    try {
      const v = jsonista(await claude(this.env,
        `Olet suomalaisen keskustelupalstan moderaattori. Estä VAIN selvästi laiton tai haitallinen sisältö: väkivallalla uhkaaminen, yksityishenkilön henkilötietojen (osoite, puhelinnumero, henkilötunnus) levittäminen, kiihottaminen kansanryhmää vastaan, lapsia seksualisoiva sisältö, pornografia tai muu seksuaalinen tai hyvän tavan vastainen sisältö, lainatarjoukset, kaupallinen roskaposti tai huijaus. SALLI kova poliittinen kritiikki, kiroilu, ivailu, kärkevät mielipiteet ja erimielisyys, myös poliitikkoja ja puolueita kohtaan. Vastaa vain JSON: {"ok":true} tai {"ok":false,"syy":"lyhyt syy suomeksi"}.`,
        teksti, 120));
      if (v && v.ok === false) return { ok: false, syy: String(v.syy || "sisältö rikkoo sääntöjä.").slice(0, 160) };
    } catch {}
    return { ok: true };
  }
  seuraa(minä, d) {
    const k = +d.kayttaja;
    if (!k || k === minä.id) return virhe("Et voi seurata itseäsi.");
    if (!this.yksi("SELECT id FROM kayttajat WHERE id=? AND nimi IS NOT NULL", k)) return virhe("Käyttäjää ei löytynyt.");
    const on = this.yksi("SELECT 1 AS x FROM seuraukset WHERE seuraaja=? AND seurattava=?", minä.id, k);
    if (on) this.sql.exec("DELETE FROM seuraukset WHERE seuraaja=? AND seurattava=?", minä.id, k);
    else {
      if (!this.raja("seuraa:" + minä.id, 200, 86400)) return virhe("Liikaa seurauksia tänään. Yritä huomenna.", 429);
      this.sql.exec("INSERT INTO seuraukset VALUES(?,?,?)", minä.id, k, nyt());
    }
    return json({ ok: true, seuraan: !on, seuraajat: this.yksi("SELECT COUNT(*) AS n FROM seuraukset WHERE seurattava=?", k).n });
  }
  tykkaa(minä, d) {
    const id = +d.id;
    if (!this.yksi("SELECT id FROM postit WHERE id=?", id)) return virhe("Postausta ei löytynyt.");
    if (this.yksi("SELECT 1 AS x FROM tykkaykset WHERE posti=? AND kayttaja=?", id, minä.id)) {
      this.sql.exec("DELETE FROM tykkaykset WHERE posti=? AND kayttaja=?", id, minä.id); this.sql.exec("UPDATE postit SET tykkaykset=MAX(0,tykkaykset-1) WHERE id=?", id);
    } else {
      this.sql.exec("INSERT INTO tykkaykset VALUES(?,?)", id, minä.id); this.sql.exec("UPDATE postit SET tykkaykset=tykkaykset+1 WHERE id=?", id);
    }
    const r = this.yksi("SELECT tykkaykset FROM postit WHERE id=?", id);
    return json({ ok: true, tykkaykset: r.tykkaykset });
  }
  async ilmoita(minä, d) {
    const id = +d.id, syy = puhdas(d.syy).slice(0, 200);
    const r = this.yksi("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.id=?", id);
    if (!r) return virhe("Postausta ei löytynyt.");
    if (this.yksi("SELECT 1 AS x FROM ilmoitukset WHERE posti=? AND kayttaja=?", id, minä.id)) return json({ ok: true, jo: true });
    this.sql.exec("INSERT INTO ilmoitukset VALUES(?,?,?,?)", id, minä.id, syy, nyt());
    this.sql.exec("UPDATE postit SET ilmoitukset=ilmoitukset+1 WHERE id=?", id);
    const n = r.ilmoitukset + 1;
    if (n >= 3 || minä.admin) this.sql.exec("UPDATE postit SET piilotettu=1 WHERE id=?", id);
    await telegram(this.env, `🚩 Faktapiste: ilmoitus postauksesta #${id} (${n}/3${n >= 3 ? ", piilotettu" : ""})\n${r.nimi || r.lahde}: ${r.teksti.slice(0, 300)}\nSyy: ${syy || "-"}\nhttps://faktapiste.fi/?p=${id}`);
    return json({ ok: true });
  }
  poista(minä, d) {
    const r = this.yksi("SELECT kayttaja, vanhempi FROM postit WHERE id=?", +d.id);
    if (!r) return virhe("Postausta ei löytynyt.");
    if (r.kayttaja !== minä.id && !minä.admin) return virhe("Voit poistaa vain omia postauksiasi.", 403);
    this.sql.exec("UPDATE postit SET piilotettu=1, teksti='', kortti=NULL WHERE id=?", +d.id);
    this.sql.exec("DELETE FROM kuvat WHERE posti=?", +d.id);
    this.poistaVideot(this.kaikki("SELECT id, avain FROM videot WHERE posti=?", +d.id));
    return json({ ok: true });
  }

  // ---- Kysy fakta ----
  async fakta(minä, d) {
    const q = puhdas(d.kysymys).slice(0, 300);
    if (q.length < 3) return virhe("Kirjoita kysymys.");
    if (!this.raja("f:" + minä.id, 30, 86400) || !this.raja("f:kaikki", 800, 86400)) return virhe("Päivän faktahaut ovat täynnä. Yritä huomenna.", 429);
    let vastaus = "", lahteet = [];
    try {
      const r = await fetch(ES_HAKU, { method: "POST", headers: { "content-type": "application/json", apikey: ES_AVAIN, authorization: "Bearer " + ES_AVAIN }, body: JSON.stringify({ q, laaja: false }) });
      const j = await r.json();
      if (j.virhe) return virhe(j.virhe, 502);
      vastaus = String(j.vastaus || "").trim(); lahteet = (j.lahteet || []).filter(s => s && s.url).slice(0, 5);
    } catch { return virhe("Faktahaku ei vastannut juuri nyt. Yritä hetken päästä.", 502); }
    if (!vastaus) return virhe("Tähän ei löytynyt vastausta Eduskuntaseurannan tiedoista. Kokeile toisin sanoin.", 404);
    // Täydennetään puolueittaisilla luvuilla: valitaan lähteistä asian lopullinen äänestys ja haetaan sen ryhmätaulukko.
    let aan = null, tiivis = vastaus;
    try {
      const kaikki = await this.aanestykset();
      const idt = lahteet.map(s => (s.url.match(/\/aanestys\/(\d+)/) || [])[1]).filter(Boolean).map(Number);
      const ehd = [];
      for (const id of idt.slice(0, 3)) {
        const v = kaikki.get(id); if (!v) continue;
        const sama = [...kaikki.values()].filter(y => y.otsikko === v.otsikko).sort((x, y) => (y.alkoi || "").localeCompare(x.alkoi || ""));
        ehd.push(sama.find(y => /hyväksyminen JAA \/ hylkääminen/i.test(y.lisaotsikko || "")) || v);
      }
      const valittu = ehd[0];
      if (valittu) {
        const k = await aanestysKortti(valittu.id);
        if (k) {
          aan = { ...k, otsikko: lyhennaLaki(valittu.otsikko), lisaotsikko: valittu.lisaotsikko || "", pv: (valittu.alkoi || "").slice(0, 10) };
          const taulu = k.ryhmat.map(g => `${g.r}: jaa ${g.jaa}, ei ${g.ei}, tyhjää ${g.tyhja}, poissa ${g.poissa}`).join("\n");
          tiivis = (await claude(this.env,
            "Vastaat suomeksi lyhyesti (enintään 3 virkettä) kysymykseen eduskunnan äänestyksestä annetun datan perusteella. Käytä vain annettuja lukuja ja tietoja, älä keksi mitään. Tunnista puhekieliset puoluenimet (persut = Perussuomalaiset, demarit = SDP, kepu = Keskusta, kokkarit = Kokoomus, vassarit = Vasemmistoliitto, kristityt = Kristillisdemokraatit). Jaa- ja Ei-vaihtoehtojen merkitys tulee VAIN tarkenteesta (esim. 'Lakiehdotuksen hyväksyminen JAA / hylkääminen EI' tarkoittaa, että Jaa = lain hyväksyminen). Jos kysymys koskee puoluetta, kerro sen ryhmän luvut. Palauta pelkkä vastausteksti.",
            `Kysymys: ${q}\n\nÄänestys ${aan.pv}: ${valittu.otsikko}\nTarkenne: ${valittu.lisaotsikko || "-"}\nYhteensä: jaa ${k.jaa}, ei ${k.ei}, tyhjää ${k.tyhja}, poissa ${k.poissa}\nRyhmittäin:\n${taulu}`, 350)).trim() || vastaus;
          if (!lahteet.some(s => s.url === aan.url)) lahteet.unshift({ url: aan.url, otsikko: "Äänestys " + aan.pv + ": " + aan.otsikko });
        }
      }
    } catch {}
    if (!aan && tiivis.length > 420) {
      try { tiivis = (await claude(this.env, "Tiivistä annettu vastaus enintään kolmeen lyhyeen virkkeeseen suomeksi. Säilytä luvut, nimet ja päivämäärät täsmälleen. Älä lisää mitään uutta. Palauta pelkkä teksti.", vastaus, 300)).trim() || vastaus.slice(0, 420); } catch { tiivis = vastaus.slice(0, 420) + "…"; }
    }
    const kortti = { tyyppi: "fakta", kysymys: q, vastaus: tiivis, lahteet: lahteet.map(s => ({ url: s.url, otsikko: String(s.otsikko || s.url).slice(0, 140) })), aanestys: aan };
    const avain = satunnainen(8);
    this.sql.exec("INSERT INTO asetukset VALUES(?,?)", "fakta:" + avain, JSON.stringify(kortti));
    return json({ ok: true, avain, kortti });
  }

  async aanestykset() {
    if (this._aan && this._aanAika > nyt() - 3600e3) return this._aan;
    const r = await fetch(`${ES}/data/aanestykset.json`, { headers: { "user-agent": "Faktapiste/1.0" } });
    const a = await r.json();
    this._aan = new Map(a.map(v => [v.id, v])); this._aanAika = nyt();
    return this._aan;
  }

  // ---- automaattisisältö kaikilta palveluilta ----
  lisaaAuto(lahde, ext, teksti, kortti, aika) {
    if (this.yksi("SELECT id FROM postit WHERE ext=?", ext)) return 0;
    this.sql.exec("INSERT INTO postit(kayttaja, lahde, teksti, kortti, luotu, ext) VALUES(NULL,?,?,?,?,?)", lahde, teksti, JSON.stringify(kortti), Math.min(aika || nyt(), nyt()), ext);
    return 1;
  }
  async sisaanluku() {
    const tulos = {};
    const hae = async (url, tyyppi = "json") => { const r = await fetch(url, { headers: { "user-agent": "Faktapiste/1.0 (+https://faktapiste.fi)" } }); if (!r.ok) throw new Error(url + " " + r.status); return tyyppi === "json" ? r.json() : r.text(); };
    const ensim = !this.yksi("SELECT id FROM postit WHERE kayttaja IS NULL LIMIT 1");
    // Suomi Tänään (ei haeta tauon aikana, jotta tauon jälkeen syöte ei täyty vanhoilla uutisilla)
    if (nyt() >= ST_TAUKO_ASTI) try {
      const x = await hae("https://suomitanaan.fi/rss.xml", "text"); let n = 0;
      for (const it of [...x.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, 8)) {
        const g = t => xmlPurku((it[1].match(new RegExp(`<${t}>([\\s\\S]*?)</${t}>`)) || [])[1]);
        const url = g("link"); if (!url) continue;
        n += this.lisaaAuto("suomitanaan", url, "", { tyyppi: "uutinen", lahde: "Suomi Tänään", otsikko: g("title"), kuvaus: g("description").slice(0, 300), url }, Date.parse(g("pubDate")) || nyt());
      }
      tulos.suomitanaan = n;
    } catch (e) { tulos.suomitanaan = "virhe " + e.message; }
    // Korjausvahti: otsikkomuutokset
    try {
      const j = await hae("https://nytpuhutaan.fi/muutokset/nostot.json"); let n = 0;
      for (const x of (j.nostot || []).slice(0, ensim ? 6 : 10)) {
        if (!x.url) continue;
        if (this.yksi("SELECT id FROM postit WHERE ext=?", x.url)) continue;
        const mm = await maksumuuri(x.url);
        n += this.lisaaAuto("korjausvahti", x.url, "", { tyyppi: "muutos", lahde: "Korjausvahti", media: x.media, ennen: x.ennen, nyt: x.nyt, url: x.url, maksumuuri: mm }, Date.parse(x.havaittu) || nyt());
      }
      tulos.korjausvahti = n;
    } catch (e) { tulos.korjausvahti = "virhe " + e.message; }
    // Eduskunta: lopulliset äänestykset (yksi per asia ja päivä)
    try {
      const a = await hae(`${ES}/data/aanestykset.json`);
      a.sort((x, y) => (y.alkoi || "").localeCompare(x.alkoi || ""));
      const nahty = new Set(); let n = 0;
      for (const v of a.slice(0, 60)) {
        const avain = (v.alkoi || "").slice(0, 10) + v.otsikko;
        if (nahty.has(avain)) continue;
        const lopullinen = /hyväksyminen JAA \/ hylkääminen/i.test(v.lisaotsikko || "");
        const ryhma = a.filter(y => (y.alkoi || "").slice(0, 10) + y.otsikko === avain);
        const valittu = ryhma.find(y => /hyväksyminen JAA \/ hylkääminen/i.test(y.lisaotsikko || "")) || ryhma[0];
        nahty.add(avain);
        if (!lopullinen && valittu !== v) continue;
        if (nahty.size > (ensim ? 4 : 12)) break;
        const hyv = /hyväksyminen JAA/i.test(valittu.lisaotsikko || "");
        const kortti = { tyyppi: "aanestys", id: valittu.id, otsikko: lyhennaLaki(valittu.otsikko), lisaotsikko: valittu.lisaotsikko || "", pv: (valittu.alkoi || "").slice(0, 10),
          jaa: valittu.jaa, ei: valittu.ei, tyhja: valittu.tyhja, poissa: valittu.poissa, url: `${ES}/aanestys/${valittu.id}/`,
          tulos: hyv ? (valittu.jaa > valittu.ei ? "Hyväksyttiin" : "Hylättiin") : (valittu.jaa > valittu.ei ? "Jaa voitti" : "Ei voitti") };
        try { const k = await aanestysKortti(valittu.id); if (k && k.ryhmat.length) kortti.ryhmat = k.ryhmat; } catch {}
        n += this.lisaaAuto("eduskunta", "es:" + valittu.id, "", kortti, Date.parse(valittu.alkoi) || nyt());
      }
      tulos.eduskunta = n;
    } catch (e) { tulos.eduskunta = "virhe " + e.message; }
    // Keräysvahti: huijausvaroitukset
    try {
      const j = await hae("https://keraysvahti.fi/huijaukset/varoitukset.json"); let n = 0;
      for (const x of (j.u || []).slice(0, ensim ? 3 : 6)) {
        if (!x.l) continue;
        if (this.yksi("SELECT id FROM postit WHERE ext=?", x.l)) continue;
        const mm = await maksumuuri(x.l);
        n += this.lisaaAuto("keraysvahti", x.l, "", { tyyppi: "varoitus", lahde: "Keräysvahti", otsikko: x.o, media: x.s, url: x.l, maksumuuri: mm }, Date.parse(x.a) || nyt());
      }
      tulos.keraysvahti = n;
    } catch (e) { tulos.keraysvahti = "virhe " + e.message; }
    // Faktapisteen omat palvelutiedotteet (lisätään kerran)
    let tn = 0;
    for (const x of TIEDOTTEET) tn += this.lisaaAuto("faktapiste", "tiedote:" + x.id, x.teksti, { tyyppi: "uutinen", lahde: "Uusi palvelu", otsikko: x.otsikko, kuvaus: x.kuvaus, url: x.url }, Date.parse(x.aika));
    tulos.faktapiste = tn;
    // Maksumuurimerkintä myös aiemmin tuoduille uutisille (enintään 8 kerralla)
    let tm = 0;
    for (const r of this.kaikki("SELECT id, kortti FROM postit WHERE lahde IN ('korjausvahti','keraysvahti') AND luotu>? AND kortti NOT LIKE '%\"maksumuuri\"%' ORDER BY luotu DESC LIMIT 8", nyt() - 5 * 86400e3)) {
      try { const k = JSON.parse(r.kortti); k.maksumuuri = await maksumuuri(k.url); this.sql.exec("UPDATE postit SET kortti=? WHERE id=?", JSON.stringify(k), r.id); tm++; } catch {}
    }
    tulos.maksumuuri = tm;
    // siivous
    this.sql.exec("DELETE FROM rajat WHERE vanhenee<?", nyt());
    this.sql.exec("DELETE FROM linkit WHERE vanhenee<?", nyt());
    return tulos;
  }
}
