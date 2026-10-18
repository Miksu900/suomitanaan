import { toimitusSivu } from "./toimitus.js";
// Suomi Tänään – uutissivusto, toimituksen hyväksyntäjono ja rajapinta yhdessä Cloudflare Workerissa.
// Tallennus: KV (binding DB). Avaimet:
//   luonnos:<id>     luonnos (JSON)          luonnokset   luonnosten id-lista
//   juttu:<slug>     julkaistu juttu (JSON)  jutut        julkaistujen metatiedot, uusin ensin
//   nahdyt           jo käsiteltyjen lähteiden url-lista (ettei samasta lähteestä tehdä luonnosta kahdesti)
// Salaisuus: TOIMITUS_SALASANA (toimitussivu ja luonnosrajapinta).

const SIVU = "Suomi Tänään";
const ISKU = "Faktat kokonaan. Myös se, mitä muut eivät kerro.";
const TOIMITTAJA = "Miika Koskela";
const YHTEYS = "miika@eduskuntaseuranta.fi";
const KATEGORIAT = ["Politiikka", "Talous", "Kotimaa", "Kunnat", "Urheilu", "Kulttuuri", "Elämä", "Ulkomaat", "Hankinnat"];

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pvm = iso => { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleDateString("fi-FI", { timeZone: "Europe/Helsinki", day: "numeric", month: "numeric", year: "numeric" }); };
const klo = iso => { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleTimeString("fi-FI", { timeZone: "Europe/Helsinki", hour: "2-digit", minute: "2-digit" }); };
const slugify = s => String(s).toLowerCase().replace(/[äå]/g, "a").replace(/ö/g, "o").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 70);
const kplt = t => String(t || "").split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);

async function lue(env, k, oletus) { const v = await env.DB.get(k, "json"); return v ?? oletus; }
const tallenna = (env, k, v) => env.DB.put(k, JSON.stringify(v));

function sallittu(req, env) {
  const h = req.headers.get("authorization") || "";
  const annettu = h.startsWith("Bearer ") ? h.slice(7) : "";
  const oikea = env.TOIMITUS_SALASANA || "";
  if (!oikea || annettu.length !== oikea.length) return false;
  let ero = 0; for (let i = 0; i < oikea.length; i++) ero |= oikea.charCodeAt(i) ^ annettu.charCodeAt(i);
  return ero === 0;
}
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const html = (h, s = 200, cache = "public, max-age=60") => new Response(h, { status: s, headers: { "content-type": "text/html; charset=utf-8", "cache-control": cache } });

// ---------- Ulkoasu ----------
const CSS = `
:root{--bg:#f6f7f9;--paper:#ffffff;--ink:#121722;--mute:#5a6475;--line:#dde2ea;--acc:#123f8c;--acc-ink:#fff;--tag:#e7eefb;
--serif:"Newsreader",Georgia,"Times New Roman",serif;--sans:"Public Sans",system-ui,-apple-system,Segoe UI,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1118;--paper:#141a24;--ink:#e8ecf3;--mute:#9aa5b8;--line:#263044;--acc:#8fb2ff;--acc-ink:#0d1118;--tag:#1c2740;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0d1118;--paper:#141a24;--ink:#e8ecf3;--mute:#9aa5b8;--line:#263044;--acc:#8fb2ff;--acc-ink:#0d1118;--tag:#1c2740;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 var(--sans)}
a{color:inherit}.w{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.mast{background:var(--paper);border-bottom:3px solid var(--ink)}
.mast .w{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 20px;padding-block:18px 12px}
.logo{font:700 clamp(30px,6vw,46px)/1 var(--serif);letter-spacing:-.02em;text-decoration:none}
.logo span{color:var(--acc)}
.isku{font:italic 15px/1.4 var(--serif);color:var(--mute)}.paiva{font:600 12px var(--sans);font-style:normal;letter-spacing:.08em;text-transform:uppercase;color:var(--ink)}
nav.kat{background:var(--paper);border-bottom:1px solid var(--line)}
nav.kat .w{display:flex;gap:4px 18px;flex-wrap:wrap;padding-block:8px;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
nav.kat a{text-decoration:none;color:var(--mute)}nav.kat a:hover,nav.kat a.on{color:var(--acc)}
main{padding-block:24px 48px}
.paa{display:grid;gap:28px}@media(min-width:900px){.paa{grid-template-columns:2fr 1fr}}
.paajuttu h2{font:700 clamp(28px,4.5vw,42px)/1.12 var(--serif);margin:6px 0 10px;text-wrap:balance}
.paajuttu p{font-size:19px;color:var(--mute);margin:0}
.lista{display:grid;gap:0}.lista article{padding-block:16px;border-top:1px solid var(--line)}
.lista h3{font:600 21px/1.25 var(--serif);margin:4px 0 6px;text-wrap:balance}.lista p{margin:0;color:var(--mute);font-size:16px}
article a{text-decoration:none}article a:hover h2,article a:hover h3{color:var(--acc)}
.meta{font-size:13px;color:var(--mute);letter-spacing:.02em}
.tag{display:inline-block;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--acc)}
aside .laatikko{background:var(--paper);border:1px solid var(--line);padding:16px;margin-bottom:16px}
aside h4{margin:0 0 8px;font:700 13px var(--sans);text-transform:uppercase;letter-spacing:.08em}
aside p{margin:0 0 8px;font-size:15px}
.juttu{max-width:700px}.juttu h1{font:700 clamp(30px,5vw,46px)/1.1 var(--serif);margin:8px 0 14px;text-wrap:balance}
.juttu .ingressi{font:500 21px/1.5 var(--serif);margin:0 0 18px}
.juttu .teksti p{margin:0 0 1em}.byline{display:flex;gap:10px;align-items:center;border-block:1px solid var(--line);padding-block:10px;margin-bottom:22px;font-size:14px}
.lahteet{background:var(--paper);border:1px solid var(--line);padding:14px 16px;margin-top:28px;font-size:15px}
.lahteet ol{margin:6px 0 0;padding-left:20px}.lahteet a{color:var(--acc);overflow-wrap:anywhere}
.huom{font-size:13px;color:var(--mute);margin-top:14px}
footer{border-top:3px solid var(--ink);background:var(--paper);padding-block:22px;font-size:14px;color:var(--mute)}
footer .w{display:grid;gap:8px}footer a{color:var(--ink)}
.tyhja{background:var(--paper);border:1px dashed var(--line);padding:28px;text-align:center;color:var(--mute)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
`;

function kuori({ otsikko, kuvaus, polku, runko, ld, kat }) {
  const navi = ["Etusivu", ...KATEGORIAT, "Pääkirjoitus"].map(n => {
    const h = n === "Etusivu" ? "/" : n === "Pääkirjoitus" ? "/paakirjoitus/" : "/aihe/" + slugify(n) + "/";
    return `<a href="${h}"${kat === n ? ' class="on"' : ""}>${esc(n)}</a>`;
  }).join("");
  return `<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>${esc(otsikko)}</title><meta name="description" content="${esc(kuvaus)}"><link rel="canonical" href="https://suomitanaan.fi${esc(polku)}">
<meta property="og:title" content="${esc(otsikko)}"><meta property="og:description" content="${esc(kuvaus)}"><meta property="og:site_name" content="${SIVU}"><meta property="og:locale" content="fi_FI">
<link rel="alternate" type="application/rss+xml" title="${SIVU}" href="/rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=Public+Sans:wght@400;600;700&display=swap">
<style>${CSS}</style>${ld ? `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, "\\u003c")}</script>` : ""}</head><body>
<header class="mast"><div class="w"><a class="logo" href="/">Suomi <span>Tänään</span></a><div class="isku">${ISKU}<br><span class="paiva">${new Date().toLocaleDateString("fi-FI",{timeZone:"Europe/Helsinki",weekday:"long",day:"numeric",month:"long",year:"numeric"})}</span></div></div></header>
<nav class="kat" aria-label="Osastot"><div class="w">${navi}</div></nav>
<main class="w">${runko}</main>
<footer><div class="w"><div><b>${SIVU}</b> · Vastaava päätoimittaja ${TOIMITTAJA} · <a href="mailto:${YHTEYS}">${YHTEYS}</a></div>
<div>Uutiset laaditaan tekoälyn avustuksella alkuperäislähteistä. Politiikan uutiset ja pääkirjoitukset toimittaja tarkistaa ennen julkaisua, muiden osastojen tekoälyn laatimat jutut on merkitty. Jokaisen jutun lopussa on lähteet. <a href="/tietoa/">Tietoa ja oikaisut</a></div>
<div>Katso myös: <a href="https://nytpuhutaan.fi">Nytpuhutaan.fi</a> · <a href="https://eduskuntaseuranta.fi">Eduskuntaseuranta.fi</a> · TikTok <a href="https://www.tiktok.com/@faktapiste">@faktapiste</a></div></div></footer>
</body></html>`;
}

const kortti = (j, iso) => `<article><a href="/uutiset/${esc(j.slug)}/"><span class="tag">${esc(j.tyyppi === "paakirjoitus" ? "Pääkirjoitus" : j.kategoria)}</span>
${iso ? `<h2>${esc(j.otsikko)}</h2>` : `<h3>${esc(j.otsikko)}</h3>`}<p>${esc(j.ingressi)}</p></a><div class="meta">${pvm(j.julkaistu)} klo ${klo(j.julkaistu)}</div></article>`;

const SIVUPALKKI = `<aside>
<div class="laatikko"><h4>Mitä tämä on</h4><p>${SIVU} kirjoittaa uutiset suoraan alkuperäislähteistä: eduskunnan äänestyksistä, viranomaisten tiedotteista, tilastoista ja virallisista asiakirjoista.</p><p>Jokaisessa jutussa on linkit lähteisiin, joten voit tarkistaa kaiken itse.</p></div>
<div class="laatikko"><h4>Miten edustajasi äänesti?</h4><p>Jokainen eduskunnan äänestys edustajittain ja puolueittain.</p><p><a href="https://eduskuntaseuranta.fi">Eduskuntaseuranta.fi →</a></p></div>
<div class="laatikko"><h4>Mistä mediat puhuvat</h4><p>Kaikkien suomalaisten medioiden uutiset yhdessä paikassa.</p><p><a href="https://nytpuhutaan.fi">Nytpuhutaan.fi →</a></p></div>
</aside>`;

async function etusivu(env, kat) {
  let jutut = await lue(env, "jutut", []);
  if (kat === "Pääkirjoitus") jutut = jutut.filter(j => j.tyyppi === "paakirjoitus");
  else if (kat) jutut = jutut.filter(j => j.kategoria === kat && j.tyyppi !== "paakirjoitus");
  const [eka, ...muut] = jutut;
  const runko = eka
    ? `<div class="paa"><div><div class="paajuttu">${kortti(eka, true)}</div><div class="lista">${muut.slice(0, 60).map(j => kortti(j)).join("")}</div></div>${SIVUPALKKI}</div>`
    : `<div class="paa"><div class="tyhja">${kat ? "Tässä osastossa ei ole vielä juttuja." : "Ensimmäiset uutiset julkaistaan pian."}</div>${SIVUPALKKI}</div>`;
  const otsikko = kat ? `${kat} | ${SIVU}` : `${SIVU}: uutiset alkuperäislähteistä`;
  return kuori({ otsikko, kuvaus: "Uutiset suoraan alkuperäislähteistä: eduskunta, viranomaiset ja tilastot. Jokaisessa jutussa lähteet.", polku: kat ? (kat === "Pääkirjoitus" ? "/paakirjoitus/" : "/aihe/" + slugify(kat) + "/") : "/", runko, kat: kat || "Etusivu",
    ld: { "@context": "https://schema.org", "@type": "WebSite", name: SIVU, url: "https://suomitanaan.fi/", inLanguage: "fi" } });
}

async function juttusivu(env, slug) {
  const j = await lue(env, "juttu:" + slug, null);
  if (!j) return null;
  const runko = `<article class="juttu"><span class="tag">${esc(j.tyyppi === "paakirjoitus" ? "Pääkirjoitus" : j.kategoria)}</span><h1>${esc(j.otsikko)}</h1>
<p class="ingressi">${esc(j.ingressi)}</p><div class="byline"><span><b>${esc(j.kirjoittaja || TOIMITTAJA)}</b></span><span class="meta">${pvm(j.julkaistu)} klo ${klo(j.julkaistu)}${j.muokattu ? " · päivitetty " + pvm(j.muokattu) : ""}</span></div>
<div class="teksti">${kplt(j.teksti).map(p => `<p>${esc(p)}</p>`).join("")}</div>
${(j.lahteet || []).length ? `<div class="lahteet"><b>Lähteet</b><ol>${j.lahteet.map(l => `<li><a href="${esc(l.url)}" rel="noopener">${esc(l.nimi || l.url)}</a></li>`).join("")}</ol></div>` : ""}
${j.tyyppi === "paakirjoitus" ? `<p class="huom">Pääkirjoitus on kirjoittajan oma kannanotto.</p>` : j.ai ? `<p class="huom"><b>Tekoälyn laatima juttu.</b> Juttu on kirjoitettu automaattisesti alkuperäislähteen perusteella, eikä toimittaja ole tarkistanut sitä ennen julkaisua. Tarkista tiedot lähteestä. Huomasitko virheen? <a href="mailto:${YHTEYS}?subject=${encodeURIComponent("Oikaisupyyntö: " + j.otsikko)}">Ilmoita siitä</a>.</p>` : `<p class="huom">Juttu on laadittu tekoälyn avustuksella alkuperäislähteistä, ja toimittaja on tarkistanut sen ennen julkaisua. Huomasitko virheen? <a href="mailto:${YHTEYS}?subject=${encodeURIComponent("Oikaisupyyntö: " + j.otsikko)}">Lähetä oikaisupyyntö</a>.</p>`}
</article>`;
  return kuori({ otsikko: `${j.otsikko} | ${SIVU}`, kuvaus: j.ingressi, polku: `/uutiset/${slug}/`, runko, kat: j.tyyppi === "paakirjoitus" ? "Pääkirjoitus" : j.kategoria,
    ld: { "@context": "https://schema.org", "@type": "NewsArticle", headline: j.otsikko, description: j.ingressi, datePublished: j.julkaistu, dateModified: j.muokattu || j.julkaistu,
      author: { "@type": "Person", name: j.kirjoittaja || TOIMITTAJA }, publisher: { "@type": "Organization", name: SIVU }, inLanguage: "fi", mainEntityOfPage: `https://suomitanaan.fi/uutiset/${slug}/` } });
}

const TIETOA = `<article class="juttu"><h1>Tietoa ${SIVU} -sivustosta</h1>
<p class="ingressi">${ISKU}</p>
<div class="teksti"><p>${SIVU} kirjoittaa uutiset suoraan alkuperäislähteistä: eduskunnan äänestyksistä ja asiakirjoista, ministeriöiden, virastojen ja kuntien tiedotteista, tilastoista ja julkisista hankinnoista. Emme kirjoita muiden medioiden juttuja uudelleen.</p>
<p>Uutiset laaditaan tekoälyn avustuksella. Politiikan uutiset ja pääkirjoitukset toimittaja lukee ja tarkistaa alkuperäislähteistä ennen julkaisua. Urheilun, kulttuurin, elämän ja muiden osastojen jutut kirjoitetaan automaattisesti virallisista lähteistä, kuten sarjojen, liittojen, kulttuurilaitosten ja viranomaisten tiedotteista. Ne on merkitty tekoälyn laatimiksi. Jokaisen jutun lopussa on linkit lähteisiin.</p>
<p>Kiistanalaisissa asioissa kerromme aina, kuka väittää mitä ja mikä asian virallinen tai oikeudellinen tila on. Syytös ja tuomio pidetään erillään. Uutiset ja kannanotot pidetään erillään: pääkirjoitukset ovat kirjoittajan omia näkemyksiä ja ne on merkitty selvästi.</p>
<p>Vastaava päätoimittaja on ${TOIMITTAJA}. Oikaisupyynnöt ja palaute: <a href="mailto:${YHTEYS}">${YHTEYS}</a>. Käsittelemme oikaisupyynnöt viipymättä.</p></div></article>`;

// ---------- Rajapinta ----------
const AI_KIRJOITTAJA = "Suomi Tänään (tekoälyn laatima)";
async function julkaiseJuttu(env, b, ai) {
  const nyt = new Date().toISOString();
  const slug = slugify(b.otsikko) + "-" + crypto.randomUUID().slice(0, 4);
  const juttu = { slug, tyyppi: b.tyyppi || "uutinen", otsikko: String(b.otsikko).trim(), ingressi: String(b.ingressi || "").trim(), teksti: String(b.teksti).trim(), kategoria: b.kategoria || "Kotimaa",
    lahteet: b.lahteet || [], kirjoittaja: ai ? AI_KIRJOITTAJA : TOIMITTAJA, ai: !!ai, julkaistu: nyt, tiktok: b.tiktok || null };
  await tallenna(env, "juttu:" + slug, juttu);
  const { teksti, ...meta } = juttu;
  const jutut = await lue(env, "jutut", []); jutut.unshift(meta); await tallenna(env, "jutut", jutut.slice(0, 3000));
  return slug;
}

async function rajapinta(req, env, polku) {
  if (polku === "/api/tila") return json({ ok: true, jutut: (await lue(env, "jutut", [])).length, luonnokset: (await lue(env, "luonnokset", [])).length });
  if (!sallittu(req, env)) return json({ virhe: "Ei oikeutta" }, 401);
  if (polku === "/api/nahdyt") return json(await lue(env, "nahdyt", []));
  if (polku === "/api/julkaistut") return json(await lue(env, "jutut", []));
  if (polku === "/api/luonnokset" && req.method === "GET") {
    const ids = await lue(env, "luonnokset", []);
    const out = (await Promise.all(ids.map(id => lue(env, "luonnos:" + id, null)))).filter(Boolean);
    return json(out.sort((a, b) => String(b.luotu).localeCompare(String(a.luotu))));
  }
  const b = await req.json().catch(() => ({}));
  if (polku === "/api/luonnokset") {
    const uudet = Array.isArray(b) ? b : [b];
    const ids = await lue(env, "luonnokset", []); const nahdyt = await lue(env, "nahdyt", []);
    for (const l of uudet) {
      if (!l) continue;
      if (l.lahde_url && !nahdyt.includes(l.lahde_url)) nahdyt.push(l.lahde_url);
      if (l.vain_nahty || !l.otsikko) continue;
      if (l.automaattinen) { await julkaiseJuttu(env, l, true); continue; }
      const id = l.id || crypto.randomUUID().slice(0, 8);
      await tallenna(env, "luonnos:" + id, { ...l, id, luotu: l.luotu || new Date().toISOString() });
      if (!ids.includes(id)) ids.push(id);
    }
    await tallenna(env, "luonnokset", ids.slice(-200)); await tallenna(env, "nahdyt", nahdyt.slice(-5000));
    return json({ ok: true, maara: uudet.length });
  }
  if (polku === "/api/hylkaa") {
    await env.DB.delete("luonnos:" + b.id);
    await tallenna(env, "luonnokset", (await lue(env, "luonnokset", [])).filter(x => x !== b.id));
    return json({ ok: true });
  }
  if (polku === "/api/julkaise") {
    if (!b.otsikko || !b.teksti) return json({ ok: false, virhe: "Otsikko ja teksti tarvitaan" }, 400);
    const slug = await julkaiseJuttu(env, b, false);
    if (b.id) { await env.DB.delete("luonnos:" + b.id); await tallenna(env, "luonnokset", (await lue(env, "luonnokset", [])).filter(x => x !== b.id)); }
    return json({ ok: true, slug });
  }
  if (polku === "/api/poista") {
    await env.DB.delete("juttu:" + b.slug);
    await tallenna(env, "jutut", (await lue(env, "jutut", [])).filter(j => j.slug !== b.slug));
    return json({ ok: true });
  }
  return json({ virhe: "Tuntematon" }, 404);
}

async function rss(env) {
  const jutut = (await lue(env, "jutut", [])).slice(0, 50);
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>${SIVU}</title><link>https://suomitanaan.fi/</link><description>${esc(ISKU)}</description><language>fi</language>
${jutut.map(j => `<item><title>${esc(j.otsikko)}</title><link>https://suomitanaan.fi/uutiset/${j.slug}/</link><guid>https://suomitanaan.fi/uutiset/${j.slug}/</guid><pubDate>${new Date(j.julkaistu).toUTCString()}</pubDate><description>${esc(j.ingressi)}</description></item>`).join("")}</channel></rss>`,
    { headers: { "content-type": "application/rss+xml; charset=utf-8", "cache-control": "public, max-age=300" } });
}
async function sitemap(env) {
  const jutut = await lue(env, "jutut", []);
  const urls = ["/", "/tietoa/", "/paakirjoitus/", ...KATEGORIAT.map(k => "/aihe/" + slugify(k) + "/"), ...jutut.map(j => `/uutiset/${j.slug}/`)];
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map(u => `<url><loc>https://suomitanaan.fi${u}</loc></url>`).join("")}</urlset>`,
    { headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "public, max-age=600" } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.hostname === "www.suomitanaan.fi") return Response.redirect("https://suomitanaan.fi" + url.pathname + url.search, 301);
    let p = url.pathname;
    if (p.startsWith("/api/")) return rajapinta(req, env, p.replace(/\/$/, ""));
    if (p === "/toimitus" || p === "/toimitus/") return html(toimitusSivu(KATEGORIAT), 200, "no-store");
    if (p === "/rss.xml") return rss(env);
    if (p === "/sitemap.xml") return sitemap(env);
    if (p === "/robots.txt") return new Response("User-agent: *\nDisallow: /toimitus\nDisallow: /api/\nSitemap: https://suomitanaan.fi/sitemap.xml\n", { headers: { "content-type": "text/plain" } });
    if (!p.endsWith("/")) p += "/";
    if (p === "/") return html(await etusivu(env));
    if (p === "/tietoa/") return html(kuori({ otsikko: `Tietoa | ${SIVU}`, kuvaus: "Miten Suomi Tänään tekee uutiset.", polku: "/tietoa/", runko: TIETOA }));
    if (p === "/paakirjoitus/") return html(await etusivu(env, "Pääkirjoitus"));
    let m = p.match(/^\/aihe\/([a-z0-9-]+)\/$/);
    if (m) { const k = KATEGORIAT.find(x => slugify(x) === m[1]); if (k) return html(await etusivu(env, k)); }
    m = p.match(/^\/uutiset\/([a-z0-9-]+)\/$/);
    if (m) { const h = await juttusivu(env, m[1]); if (h) return html(h); }
    return html(kuori({ otsikko: `Sivua ei löytynyt | ${SIVU}`, kuvaus: "", polku: p, runko: `<div class="tyhja">Sivua ei löytynyt. <a href="/">Etusivulle</a></div>` }), 404);
  },
};
