// Faktapiste-keskustelu: Cloudflare Worker + SQLite Durable Object.
// Staattiset sivut tulevat public/-kansiosta, /api/* ohjataan Durable Objectille "main".
import { DurableObject } from "cloudflare:workers";

const MALLI = "claude-haiku-5-5";
const ES = "https://eduskuntaseuranta.fi";
const ES_HAKU = "https://arwenhbwzoavbonlwkdr.supabase.co/functions/v1/haku";
const ES_AVAIN = "sb_publishable_7baeuteHYaarCEv4-j8C_g_OLxcKzJp";
const ADMIN = ["miika@eduskuntaseuranta.fi"];
const PITUUS = 500;

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (u.hostname === "www.faktapiste.fi") return Response.redirect("https://faktapiste.fi" + u.pathname + u.search, 301);
    if (u.pathname.startsWith("/api/")) return env.FP.get(env.FP.idFromName("main")).fetch(req);
    return env.ASSETS.fetch(req);
  },
  async scheduled(ev, env, ctx) {
    ctx.waitUntil(env.FP.get(env.FP.idFromName("main")).fetch(new Request("https://sisainen/_sisaanluku", { method: "POST" })));
  },
};

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
      CREATE TABLE IF NOT EXISTS asetukset(k TEXT PRIMARY KEY, v TEXT);`);
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
    if (k) k.admin = ADMIN.includes(k.email);
    return k;
  }

  async fetch(req) {
    const u = new URL(req.url), p = u.pathname, m = req.method;
    try {
      if (p === "/_sisaanluku") return json(await this.sisaanluku());
      if (p === "/api/hallinta/sisaanluku" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) return json(await this.sisaanluku());
      if (p === "/api/hallinta/tila" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA)
        return json({ postit: this.kaikki("SELECT lahde, COUNT(*) AS n FROM postit GROUP BY lahde"), kayttajat: this.yksi("SELECT COUNT(*) AS n FROM kayttajat").n });
      if (p === "/api/hallinta/fakta" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        const d = await req.json(); return await this.fakta({ id: 0 }, d);
      }
      const minä = this.kayttaja(req);
      if (p === "/api/syote" && m === "GET") return json(this.syote(u, minä));
      if (p.startsWith("/api/posti/") && m === "GET") return json(this.ketju(+p.split("/")[3], minä));
      if (p === "/api/mina") return json({ kayttaja: minä ? { nimi: minä.nimi, admin: minä.admin } : null, kirjautuminen: this.env.KIRJAUTUMINEN !== "pois" });
      if (p === "/api/kirjaudu" && m === "POST") return await this.kirjaudu(req);
      if (p === "/api/vahvista" && m === "GET") return this.vahvista(u);
      if (p === "/api/ulos" && m === "POST") { const t = evaste(req, "fp_s"); if (t) this.sql.exec("DELETE FROM sessiot WHERE t=?", t); return json({ ok: true }, 200, { "set-cookie": "fp_s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" }); }
      if (m !== "POST") return virhe("Tuntematon osoite", 404);
      if (!minä) return virhe("Kirjaudu ensin.", 401);
      if (minä.esto) return virhe("Tilisi on suljettu.", 403);
      const d = await req.json().catch(() => ({}));
      if (p === "/api/nimi") return this.asetaNimi(minä, d);
      if (!minä.nimi) return virhe("Valitse ensin nimimerkki.", 400);
      if (p === "/api/posti") return await this.uusiPosti(minä, d);
      if (p === "/api/tykkaa") return this.tykkaa(minä, d);
      if (p === "/api/ilmoita") return await this.ilmoita(minä, d);
      if (p === "/api/poista") return this.poista(minä, d);
      if (p === "/api/fakta") return await this.fakta(minä, d);
      if (p === "/api/palauta" && minä.admin) { this.sql.exec("UPDATE postit SET piilotettu=0, ilmoitukset=0 WHERE id=?", +d.id); return json({ ok: true }); }
      return virhe("Tuntematon osoite", 404);
    } catch (e) {
      return virhe("Jokin meni pieleen: " + e.message, 500);
    }
  }

  // ---- kirjautuminen sähköpostilinkillä ----
  async kirjaudu(req) {
    if (this.env.KIRJAUTUMINEN === "pois") return virhe("Kirjautuminen avataan pian.", 503);
    const d = await req.json().catch(() => ({}));
    const email = puhdas(d.email).toLowerCase();
    if (!/^[^\s@]{1,64}@[^\s@]+\.[a-z]{2,}$/.test(email) || email.length > 120) return virhe("Tarkista sähköpostiosoite.");
    const ip = await tiiviste((req.headers.get("cf-connecting-ip") || "") + "fp");
    if (!this.raja("lk:" + email, 4, 3600) || !this.raja("li:" + ip, 15, 3600)) return virhe("Liian monta yritystä. Yritä hetken päästä uudelleen.", 429);
    const t = satunnainen();
    this.sql.exec("INSERT INTO linkit VALUES(?,?,?)", await tiiviste(t), email, nyt() + 30 * 60e3);
    const linkki = `https://faktapiste.fi/api/vahvista?t=${t}`;
    const html = `<div style="max-width:520px;margin:0 auto;font:16px/1.55 -apple-system,Segoe UI,sans-serif;color:#0f1626">
<div style="background:#0d1b3e;color:#fff;padding:16px 20px;border-radius:12px;font:700 22px Impact,sans-serif;letter-spacing:.03em">FAKTA<span style="color:#f5c542">PISTE.</span></div>
<p>Hei! Kirjaudu Faktapisteeseen alla olevasta painikkeesta. Linkki on voimassa 30 minuuttia.</p>
<p><a href="${linkki}" style="display:inline-block;background:#f5c542;color:#0d1b3e;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:700">Kirjaudu Faktapisteeseen</a></p>
<p style="color:#5a6273;font-size:14px">Jos et pyytänyt tätä viestiä, voit jättää sen huomiotta. Kukaan ei pääse tilillesi ilman tätä linkkiä.</p></div>`;
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
  asetaNimi(minä, d) {
    const n = puhdas(d.nimi).replace(/\s+/g, " ");
    if (!/^[A-Za-zÅÄÖåäöÜüÉé0-9_. -]{3,24}$/.test(n)) return virhe("Nimimerkissä 3–24 merkkiä: kirjaimia, numeroita, välilyönti, piste, viiva tai alaviiva.");
    if (/faktapiste|admin|yllapito|ylläpito|moderaattori|eduskuntaseuranta|suomi tänään|keräysvahti|korjausvahti/i.test(n)) return virhe("Tämä nimimerkki on varattu.");
    if (this.yksi("SELECT id FROM kayttajat WHERE nimi=? AND id<>?", n, minä.id)) return virhe("Nimimerkki on jo käytössä.");
    this.sql.exec("UPDATE kayttajat SET nimi=? WHERE id=?", n, minä.id);
    return json({ ok: true, nimi: n });
  }

  // ---- syöte ----
  muoto(r, minä) {
    let k = null; try { k = r.kortti ? JSON.parse(r.kortti) : null; } catch {}
    return { id: r.id, nimi: r.nimi || null, lahde: r.lahde, teksti: r.piilotettu ? "" : r.teksti, kortti: r.piilotettu ? null : k, vanhempi: r.vanhempi, luotu: r.luotu,
      tykkaykset: r.tykkaykset, vastaukset: r.vastaukset, piilotettu: !!r.piilotettu, oma: !!(minä && r.kayttaja === minä.id),
      tykkasin: !!(minä && this.yksi("SELECT 1 AS x FROM tykkaykset WHERE posti=? AND kayttaja=?", r.id, minä.id)) };
  }
  syote(u, minä) {
    const tab = u.searchParams.get("tab") || "suositut", sivu = Math.max(0, +u.searchParams.get("sivu") || 0);
    const pohja = "SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.vanhempi IS NULL AND p.piilotettu=0";
    let rivit;
    if (tab === "uusimmat") rivit = this.kaikki(pohja + " ORDER BY p.luotu DESC LIMIT 30 OFFSET ?", sivu * 30);
    else if (tab === "keskustelut") rivit = this.kaikki(pohja + " AND p.kayttaja IS NOT NULL ORDER BY p.luotu DESC LIMIT 30 OFFSET ?", sivu * 30);
    else {
      // Suositut: tykkäykset ja vastaukset painavat, ikä laskee. Käyttäjien postaukset saavat etusijan automaattisisältöön nähden.
      const ehd = this.kaikki(pohja + " AND p.luotu>? ORDER BY p.luotu DESC LIMIT 400", nyt() - 4 * 86400e3);
      const t = nyt();
      for (const r of ehd) {
        const h = (t - r.luotu) / 3600e3;
        const paino = r.kayttaja ? 1.6 : r.lahde === "eduskunta" ? 1.25 : 1;
        r._p = paino * (1 + r.tykkaykset * 2 + r.vastaukset * 3) / Math.pow(h + 2, 1.4);
      }
      ehd.sort((a, b) => b._p - a._p);
      // monipuolisuus: sama lähde enintään kahdesti peräkkäin
      const jarj = [], jono = [...ehd];
      while (jono.length) {
        const i = jono.findIndex(r => !(jarj.length >= 2 && jarj.at(-1).lahde === r.lahde && jarj.at(-2).lahde === r.lahde && r.lahde !== "kayttaja"));
        jarj.push(jono.splice(i < 0 ? 0 : i, 1)[0]);
      }
      rivit = jarj.slice(sivu * 30, sivu * 30 + 30);
    }
    return { postit: rivit.map(r => this.muoto(r, minä)), lisaa: rivit.length === 30 };
  }
  ketju(id, minä) {
    const r = this.yksi("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.id=?", id);
    if (!r) return { virhe: "Postausta ei löytynyt." };
    const vanh = r.vanhempi ? this.yksi("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.id=?", r.vanhempi) : null;
    const v = this.kaikki("SELECT p.*, k.nimi FROM postit p LEFT JOIN kayttajat k ON k.id=p.kayttaja WHERE p.vanhempi=? ORDER BY p.tykkaykset DESC, p.luotu ASC LIMIT 200", id);
    return { posti: this.muoto(r, minä), vanhempi: vanh ? this.muoto(vanh, minä) : null, vastaukset: v.map(x => this.muoto(x, minä)) };
  }

  // ---- kirjoittaminen ----
  async uusiPosti(minä, d) {
    const teksti = puhdas(d.teksti).replace(/\n{3,}/g, "\n\n");
    if (teksti.length < 2) return virhe("Kirjoita jotain.");
    if (teksti.length > PITUUS) return virhe(`Enintään ${PITUUS} merkkiä.`);
    if (!this.raja("p:" + minä.id, 15, 3600)) return virhe("Olet kirjoittanut paljon tunnin sisällä. Pidä pieni tauko.", 429);
    const vanhempi = d.vanhempi ? +d.vanhempi : null;
    if (vanhempi && !this.yksi("SELECT id FROM postit WHERE id=? AND piilotettu=0", vanhempi)) return virhe("Postausta ei enää ole.");
    let kortti = null;
    if (d.kortti && typeof d.kortti === "object" && d.kortti.tyyppi === "fakta") {
      const k = this.yksi("SELECT v FROM asetukset WHERE k=?", "fakta:" + String(d.kortti.avain || ""));
      if (k) kortti = k.v;
    }
    const tark = await this.tarkista(teksti);
    if (!tark.ok) return virhe("Postausta ei julkaistu: " + tark.syy + " Kirjoittaa saa kärkevästi ja olla eri mieltä, mutta uhkaukset, henkilötietojen levittäminen, kiihottaminen kansanryhmää vastaan ja roskaposti eivät käy.", 422);
    this.sql.exec("INSERT INTO postit(kayttaja, lahde, teksti, kortti, vanhempi, luotu) VALUES(?,?,?,?,?,?)", minä.id, "kayttaja", teksti, kortti, vanhempi, nyt());
    const id = this.yksi("SELECT last_insert_rowid() AS id").id;
    if (vanhempi) this.sql.exec("UPDATE postit SET vastaukset=vastaukset+1 WHERE id=?", vanhempi);
    return json({ ok: true, id });
  }
  async tarkista(teksti) {
    if (/(https?:\/\/\S+.*){4,}/i.test(teksti)) return { ok: false, syy: "liikaa linkkejä." };
    try {
      const v = jsonista(await claude(this.env,
        `Olet suomalaisen keskustelupalstan moderaattori. Estä VAIN selvästi laiton tai haitallinen sisältö: väkivallalla uhkaaminen, yksityishenkilön henkilötietojen (osoite, puhelinnumero, henkilötunnus) levittäminen, kiihottaminen kansanryhmää vastaan, lapsia seksualisoiva sisältö, kaupallinen roskaposti tai huijaus. SALLI kova poliittinen kritiikki, kiroilu, ivailu, kärkevät mielipiteet ja erimielisyys, myös poliitikkoja ja puolueita kohtaan. Vastaa vain JSON: {"ok":true} tai {"ok":false,"syy":"lyhyt syy suomeksi"}.`,
        teksti, 120));
      if (v && v.ok === false) return { ok: false, syy: String(v.syy || "sisältö rikkoo sääntöjä.").slice(0, 160) };
    } catch {}
    return { ok: true };
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
    let aan = null;
    const a = lahteet.find(s => /\/aanestys\/\d+/.test(s.url));
    if (a) { try { aan = await aanestysKortti(a.url.match(/\/aanestys\/(\d+)/)[1]); } catch {} }
    let tiivis = vastaus;
    if (vastaus.length > 420) {
      try { tiivis = (await claude(this.env, "Tiivistä annettu vastaus enintään kolmeen lyhyeen virkkeeseen suomeksi. Säilytä luvut, nimet ja päivämäärät täsmälleen. Älä lisää mitään uutta. Palauta pelkkä teksti.", vastaus, 300)).trim() || vastaus.slice(0, 420); } catch { tiivis = vastaus.slice(0, 420) + "…"; }
    }
    const kortti = { tyyppi: "fakta", kysymys: q, vastaus: tiivis, lahteet: lahteet.map(s => ({ url: s.url, otsikko: String(s.otsikko || s.url).slice(0, 140) })), aanestys: aan };
    const avain = satunnainen(8);
    this.sql.exec("INSERT INTO asetukset VALUES(?,?)", "fakta:" + avain, JSON.stringify(kortti));
    return json({ ok: true, avain, kortti });
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
    // Suomi Tänään
    try {
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
        n += this.lisaaAuto("korjausvahti", x.url, "", { tyyppi: "muutos", lahde: "Korjausvahti", media: x.media, ennen: x.ennen, nyt: x.nyt, url: x.url }, Date.parse(x.havaittu) || nyt());
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
        n += this.lisaaAuto("keraysvahti", x.l, "", { tyyppi: "varoitus", lahde: "Keräysvahti", otsikko: x.o, media: x.s, url: x.l }, Date.parse(x.a) || nyt());
      }
      tulos.keraysvahti = n;
    } catch (e) { tulos.keraysvahti = "virhe " + e.message; }
    // siivous
    this.sql.exec("DELETE FROM rajat WHERE vanhenee<?", nyt());
    this.sql.exec("DELETE FROM linkit WHERE vanhenee<?", nyt());
    return tulos;
  }
}
