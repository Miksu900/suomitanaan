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
// Jokaisella osastolla on oma värinsä; jutun kansikuva piirretään osaston väreistä (ei valokuvia, ei tekijänoikeusongelmia).
const VARIT = {
  Politiikka: ["#1d4ed8", "#93b4ff"], Talous: ["#0f766e", "#7fd8cb"], Kotimaa: ["#c2410c", "#ffb68a"], Kunnat: ["#7c3aed", "#c9b2ff"],
  Urheilu: ["#15803d", "#86e3a6"], Kulttuuri: ["#be185d", "#ff9fcb"], "Elämä": ["#d97706", "#ffd27a"], Ulkomaat: ["#0e7490", "#7fdcf0"],
  Hankinnat: ["#475569", "#b8c4d6"], "Pääkirjoitus": ["#9f1239", "#ff9fb1"],
};
const vari = k => VARIT[k] || VARIT.Kotimaa;
const katNimi = j => j.tyyppi === "paakirjoitus" ? "Pääkirjoitus" : (j.kategoria || "Kotimaa");
const katPolku = k => k === "Pääkirjoitus" ? "/paakirjoitus/" : "/aihe/" + slugify(k) + "/";

function hajautus(s) { let h = 2166136261; for (const c of String(s)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
// Abstrakti kansikuva: osaston väri + jutun tunnisteesta johdettu kuvio (sama juttu = aina sama kuva)
function kansi(j, luokka = "kansi") {
  const k = katNimi(j), [c1, c2] = vari(k), h = hajautus(j.slug || j.otsikko), r = n => ((h >>> (n * 3)) % 1000) / 1000;
  const malli = h % 4;
  let kuvio = "";
  if (malli === 0) kuvio = [0, 1, 2, 3].map(i => `<circle cx="${(r(i) * 640).toFixed(0)}" cy="${(r(i + 4) * 360).toFixed(0)}" r="${(60 + r(i + 2) * 170).toFixed(0)}" fill="${i % 2 ? c2 : "#fff"}" opacity="${(0.10 + r(i + 5) * 0.22).toFixed(2)}"/>`).join("");
  else if (malli === 1) kuvio = [0, 1, 2, 3, 4, 5].map(i => `<rect x="${-200 + i * 150 + r(i) * 60}" y="-120" width="${40 + r(i + 1) * 70}" height="700" fill="${i % 2 ? c2 : "#fff"}" opacity="${(0.10 + r(i + 3) * 0.18).toFixed(2)}" transform="rotate(${20 + r(7) * 25} 320 180)"/>`).join("");
  else if (malli === 2) { for (let y = 0; y < 8; y++) for (let x = 0; x < 14; x++) kuvio += `<circle cx="${30 + x * 46}" cy="${24 + y * 46}" r="${3 + ((h >> ((x + y) % 24)) & 3) * 2}" fill="#fff" opacity=".22"/>`; kuvio += `<circle cx="${420 + r(1) * 160}" cy="${150 + r(2) * 120}" r="${120 + r(3) * 60}" fill="${c2}" opacity=".45"/>`; }
  else kuvio = [0, 1, 2].map(i => `<path d="M0 ${200 + i * 60 + r(i) * 40} C 160 ${100 + r(i + 1) * 160}, 420 ${260 + r(i + 2) * 120}, 640 ${120 + i * 70}" stroke="${i % 2 ? c2 : "#fff"}" stroke-width="${18 + r(i + 3) * 30}" fill="none" opacity="${(0.18 + r(i + 4) * 0.2).toFixed(2)}"/>`).join("");
  return `<div class="${luokka}" style="--k1:${c1};--k2:${c2}" aria-hidden="true"><svg viewBox="0 0 640 360" preserveAspectRatio="xMidYMid slice"><rect width="640" height="360" fill="${c1}"/>${kuvio}</svg><span>${esc(k)}</span></div>`;
}

const CSS = `
:root{--bg:#f4f5f8;--paper:#ffffff;--ink:#111827;--mute:#5b6476;--line:#e2e6ee;--navy:#0b1f45;--navy-ink:#ffffff;--acc:#1d4ed8;
--serif:"Newsreader",Georgia,"Times New Roman",serif;--sans:"Public Sans",system-ui,-apple-system,Segoe UI,sans-serif;--r:14px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0a0e15;--paper:#131a25;--ink:#e9edf4;--mute:#9ca7ba;--line:#242e40;--navy:#060c19;--acc:#8fb2ff;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0a0e15;--paper:#131a25;--ink:#e9edf4;--mute:#9ca7ba;--line:#242e40;--navy:#060c19;--acc:#8fb2ff;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 var(--sans)}
a{color:inherit}.w{max-width:1140px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.mast{background:var(--navy);color:var(--navy-ink)}
.mast .w{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:8px 24px;padding-block:22px 16px}
.logo{font:700 clamp(32px,6.5vw,52px)/.95 var(--serif);letter-spacing:-.025em;text-decoration:none;color:#fff}
.logo i{font-style:normal;color:#ffd27a}
.isku{font:italic 15px/1.45 var(--serif);color:#c6d2ea;text-align:right}.paiva{font:700 11px var(--sans);font-style:normal;letter-spacing:.14em;text-transform:uppercase;color:#fff}
.raita{display:flex;height:5px}.raita b{flex:1}
nav.kat{background:var(--paper);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav.kat .w{display:flex;gap:6px;overflow-x:auto;padding-block:10px;scrollbar-width:none}nav.kat .w::-webkit-scrollbar{display:none}
nav.kat a{flex:0 0 auto;text-decoration:none;font:700 13px var(--sans);letter-spacing:.04em;text-transform:uppercase;color:var(--mute);padding:7px 12px;border-radius:999px;border:1px solid transparent}
nav.kat a:hover{border-color:var(--line);color:var(--ink)}nav.kat a.on{background:var(--k,var(--navy));color:#fff}
main{padding-block:26px 56px}
.kansi{position:relative;aspect-ratio:16/9;border-radius:var(--r);overflow:hidden;background:var(--k1);max-width:100%}
.kansi svg{position:absolute;inset:0;width:100%;height:100%;display:block}
.kansi span{position:absolute;left:14px;bottom:12px;font:800 12px var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#fff;background:rgba(0,0,0,.22);padding:5px 10px;border-radius:999px;backdrop-filter:blur(4px)}
.kortti .kansi span{display:none}.kansi.iso{aspect-ratio:21/9}.kansi.iso span{font-size:13px}
.huippu{display:grid;gap:22px;margin-bottom:34px}@media(min-width:900px){.huippu{grid-template-columns:1.6fr 1fr}}
.paajuttu a{display:grid;gap:14px;text-decoration:none}
.paajuttu h2{font:700 clamp(30px,4.6vw,48px)/1.06 var(--serif);margin:0;text-wrap:balance;letter-spacing:-.015em}
.paajuttu p{font-size:19px;color:var(--mute);margin:0}
.sivulista{display:grid;gap:14px;align-content:start}
.mini a{display:grid;grid-template-columns:110px 1fr;gap:12px;align-items:center;text-decoration:none}.mini .kansi{border-radius:10px}.mini .kansi span{display:none}
.mini h3{font:700 18px/1.22 var(--serif);margin:0 0 4px;text-wrap:balance}
.osio{margin-bottom:36px}.osio-otsikko{display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:4px solid var(--k);padding-top:10px;margin-bottom:16px}
.osio-otsikko h2{font:800 15px var(--sans);letter-spacing:.12em;text-transform:uppercase;margin:0;color:var(--k)}.osio-otsikko a{font:700 13px var(--sans);color:var(--mute);text-decoration:none}
.ruudukko{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.kortti a{display:grid;gap:10px;text-decoration:none}.kortti h3{font:700 21px/1.2 var(--serif);margin:0;text-wrap:balance}.kortti p{margin:0;color:var(--mute);font-size:15.5px;line-height:1.5}
a:hover h2,a:hover h3{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px;text-decoration-color:var(--k,var(--acc))}
.tag{font:800 11px var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--k,var(--acc))}
.meta{font-size:13px;color:var(--mute)}.ai{font:700 10px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--mute);border:1px solid var(--line);border-radius:999px;padding:1px 7px;margin-left:6px}
.kolme{display:grid;gap:16px;margin-bottom:36px}@media(min-width:760px){.kolme{grid-template-columns:repeat(3,1fr)}}
.laatikko{border-radius:var(--r);padding:18px;color:#fff;display:grid;gap:6px;text-decoration:none}
.laatikko b{font:800 12px var(--sans);letter-spacing:.12em;text-transform:uppercase;opacity:.85}.laatikko strong{font:700 21px/1.2 var(--serif)}.laatikko span{font-size:15px;opacity:.92}
.juttu{max-width:740px;margin:0 auto}.juttu .kansi{margin-bottom:22px}
.juttu h1{font:700 clamp(32px,5.4vw,50px)/1.06 var(--serif);margin:8px 0 14px;text-wrap:balance;letter-spacing:-.015em}
.juttu .ingressi{font:500 22px/1.5 var(--serif);margin:0 0 20px}
.juttu .teksti{font-size:18px;line-height:1.7}.juttu .teksti p{margin:0 0 1.05em}
.byline{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;border-block:1px solid var(--line);padding-block:12px;margin-bottom:24px;font-size:14px}
.lahteet{background:var(--paper);border-left:5px solid var(--k);border-radius:10px;padding:14px 18px;margin-top:30px;font-size:15px}
.lahteet ol{margin:6px 0 0;padding-left:20px}.lahteet a{color:var(--acc);overflow-wrap:anywhere}
.huom{font-size:13.5px;color:var(--mute);margin-top:16px;background:var(--paper);border-radius:10px;padding:12px 14px}
footer{background:var(--navy);color:#c6d2ea;padding-block:28px;font-size:14px}footer .w{display:grid;gap:10px}footer a{color:#fff}footer b{color:#fff}
.tyhja{background:var(--paper);border:1px dashed var(--line);border-radius:var(--r);padding:36px;text-align:center;color:var(--mute)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
`;

function kuori({ otsikko, kuvaus, polku, runko, ld, kat }) {
  const navi = ["Etusivu", ...KATEGORIAT, "Pääkirjoitus"].map(n => {
    const h = n === "Etusivu" ? "/" : katPolku(n);
    const k = n === "Etusivu" ? "" : ` style="--k:${vari(n)[0]}"`;
    return `<a href="${h}"${k}${kat === n ? ' class="on"' : ""}>${esc(n)}</a>`;
  }).join("");
  const raita = [...KATEGORIAT, "Pääkirjoitus"].map(k => `<b style="background:${vari(k)[0]}"></b>`).join("");
  const paiva = new Date().toLocaleDateString("fi-FI", { timeZone: "Europe/Helsinki", weekday: "long", day: "numeric", month: "long", year: "numeric" });
  return `<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>${esc(otsikko)}</title><meta name="description" content="${esc(kuvaus)}"><link rel="canonical" href="https://suomitanaan.fi${esc(polku)}">
<meta property="og:title" content="${esc(otsikko)}"><meta property="og:description" content="${esc(kuvaus)}"><meta property="og:site_name" content="${SIVU}"><meta property="og:locale" content="fi_FI"><meta name="theme-color" content="#0b1f45">
<link rel="alternate" type="application/rss+xml" title="${SIVU}" href="/rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=Public+Sans:wght@400;600;700;800&display=swap">
<style>${CSS}</style>${ld ? `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, "\\u003c")}</script>` : ""}</head><body>
<header class="mast"><div class="w"><a class="logo" href="/">Suomi <i>Tänään</i></a><div class="isku">${ISKU}<br><span class="paiva">${paiva}</span></div></div><div class="raita">${raita}</div></header>
<nav class="kat" aria-label="Osastot"><div class="w">${navi}</div></nav>
<main class="w">${runko}</main>
<footer><div class="w"><div><b>${SIVU}</b> · Vastaava päätoimittaja ${TOIMITTAJA} · <a href="mailto:${YHTEYS}">${YHTEYS}</a></div>
<div>Uutiset laaditaan tekoälyn avustuksella alkuperäislähteistä. Politiikan uutiset ja pääkirjoitukset toimittaja tarkistaa ennen julkaisua, muiden osastojen tekoälyn laatimat jutut on merkitty. Jokaisen jutun lopussa on lähteet. <a href="/tietoa/">Tietoa ja oikaisut</a></div>
<div>Katso myös: <a href="https://nytpuhutaan.fi">Nytpuhutaan.fi</a> · <a href="https://eduskuntaseuranta.fi">Eduskuntaseuranta.fi</a> · TikTok <a href="https://www.tiktok.com/@faktapiste">@faktapiste</a></div></div></footer>
</body></html>`;
}

const aikaMerk = j => `<div class="meta">${pvm(j.julkaistu)} klo ${klo(j.julkaistu)}${j.ai ? '<span class="ai">Tekoäly</span>' : ""}</div>`;
const kortti = j => `<article class="kortti" style="--k:${vari(katNimi(j))[0]}"><a href="/uutiset/${esc(j.slug)}/">${kansi(j)}<span class="tag">${esc(katNimi(j))}</span><h3>${esc(j.otsikko)}</h3><p>${esc(j.ingressi)}</p></a>${aikaMerk(j)}</article>`;
const mini = j => `<article class="mini" style="--k:${vari(katNimi(j))[0]}"><a href="/uutiset/${esc(j.slug)}/">${kansi(j)}<div><span class="tag">${esc(katNimi(j))}</span><h3>${esc(j.otsikko)}</h3></div></a></article>`;

const LAATIKOT = `<div class="kolme">
<a class="laatikko" style="background:linear-gradient(135deg,#1d4ed8,#0b1f45)" href="https://eduskuntaseuranta.fi"><b>Eduskuntaseuranta</b><strong>Miten edustajasi äänesti?</strong><span>Jokainen äänestys edustajittain ja puolueittain →</span></a>
<a class="laatikko" style="background:linear-gradient(135deg,#be185d,#7c3aed)" href="https://nytpuhutaan.fi"><b>Nytpuhutaan</b><strong>Mistä mediat puhuvat nyt?</strong><span>Kaikkien medioiden uutiset yhdessä paikassa →</span></a>
<a class="laatikko" style="background:linear-gradient(135deg,#0f766e,#15803d)" href="/tietoa/"><b>${SIVU}</b><strong>Uutiset suoraan lähteestä</strong><span>Jokaisessa jutussa linkit alkuperäislähteisiin →</span></a>
</div>`;

async function etusivu(env, kat) {
  let jutut = await lue(env, "jutut", []);
  const polku = kat ? katPolku(kat) : "/";
  const otsikko = kat ? `${kat} | ${SIVU}` : `${SIVU}: uutiset alkuperäislähteistä`;
  const kuvaus = "Uutiset suoraan alkuperäislähteistä: eduskunta, viranomaiset, urheilu ja kulttuuri. Jokaisessa jutussa lähteet.";
  if (kat === "Pääkirjoitus") jutut = jutut.filter(j => j.tyyppi === "paakirjoitus");
  else if (kat) jutut = jutut.filter(j => j.kategoria === kat && j.tyyppi !== "paakirjoitus");
  let runko;
  if (!jutut.length) runko = `<div class="tyhja">${kat ? "Tässä osastossa ei ole vielä juttuja." : "Ensimmäiset uutiset julkaistaan pian."}</div>${LAATIKOT}`;
  else {
    const [eka, ...muut] = jutut;
    const huippu = `<section class="huippu"><article class="paajuttu" style="--k:${vari(katNimi(eka))[0]}"><a href="/uutiset/${esc(eka.slug)}/">${kansi(eka, "kansi iso")}<h2>${esc(eka.otsikko)}</h2><p>${esc(eka.ingressi)}</p></a>${aikaMerk(eka)}</article>
<div class="sivulista">${muut.slice(0, 4).map(mini).join("")}</div></section>`;
    let osiot;
    if (kat) osiot = `<div class="ruudukko">${muut.slice(4, 64).map(kortti).join("")}</div>`;
    else {
      const kaytetty = new Set([eka, ...muut.slice(0, 4)].map(j => j.slug));
      osiot = [...KATEGORIAT, "Pääkirjoitus"].map(k => {
        const l = jutut.filter(j => katNimi(j) === k && !kaytetty.has(j.slug)).slice(0, 6);
        return l.length ? `<section class="osio" style="--k:${vari(k)[0]}"><div class="osio-otsikko"><h2>${esc(k)}</h2><a href="${katPolku(k)}">Kaikki →</a></div><div class="ruudukko">${l.map(kortti).join("")}</div></section>` : "";
      }).join("");
    }
    runko = huippu + (kat ? "" : LAATIKOT) + osiot;
  }
  return kuori({ otsikko, kuvaus, polku, runko, kat: kat || "Etusivu", ld: { "@context": "https://schema.org", "@type": "WebSite", name: SIVU, url: "https://suomitanaan.fi/", inLanguage: "fi" } });
}

async function juttusivu(env, slug) {
  const j = await lue(env, "juttu:" + slug, null);
  if (!j) return null;
  const k = katNimi(j);
  const runko = `<article class="juttu" style="--k:${vari(k)[0]}">${kansi(j, "kansi iso")}<a class="tag" href="${katPolku(k)}" style="text-decoration:none">${esc(k)}</a><h1>${esc(j.otsikko)}</h1>
<p class="ingressi">${esc(j.ingressi)}</p><div class="byline"><span><b>${esc(j.kirjoittaja || TOIMITTAJA)}</b></span><span class="meta">${pvm(j.julkaistu)} klo ${klo(j.julkaistu)}${j.muokattu ? " · päivitetty " + pvm(j.muokattu) : ""}</span></div>
<div class="teksti">${kplt(j.teksti).map(p => `<p>${esc(p)}</p>`).join("")}</div>
${(j.lahteet || []).length ? `<div class="lahteet"><b>Lähteet</b><ol>${j.lahteet.map(l => `<li><a href="${esc(l.url)}" rel="noopener">${esc(l.nimi || l.url)}</a></li>`).join("")}</ol></div>` : ""}
${j.tyyppi === "paakirjoitus" ? `<p class="huom">Pääkirjoitus on kirjoittajan oma kannanotto.</p>` : j.ai ? `<p class="huom"><b>Tekoälyn laatima juttu.</b> Juttu on kirjoitettu automaattisesti alkuperäislähteen perusteella, eikä toimittaja ole tarkistanut sitä ennen julkaisua. Tarkista tiedot lähteestä. Huomasitko virheen? <a href="mailto:${YHTEYS}?subject=${encodeURIComponent("Oikaisupyyntö: " + j.otsikko)}">Ilmoita siitä</a>.</p>` : `<p class="huom">Juttu on laadittu tekoälyn avustuksella alkuperäislähteistä, ja toimittaja on tarkistanut sen ennen julkaisua. Huomasitko virheen? <a href="mailto:${YHTEYS}?subject=${encodeURIComponent("Oikaisupyyntö: " + j.otsikko)}">Lähetä oikaisupyyntö</a>.</p>`}
</article>`;
  return kuori({ otsikko: `${j.otsikko} | ${SIVU}`, kuvaus: j.ingressi, polku: `/uutiset/${slug}/`, runko, kat: k,
    ld: { "@context": "https://schema.org", "@type": "NewsArticle", headline: j.otsikko, description: j.ingressi, datePublished: j.julkaistu, dateModified: j.muokattu || j.julkaistu,
      author: { "@type": j.ai ? "Organization" : "Person", name: j.kirjoittaja || TOIMITTAJA }, publisher: { "@type": "Organization", name: SIVU }, inLanguage: "fi", mainEntityOfPage: `https://suomitanaan.fi/uutiset/${slug}/` } });
}

const TIETOA = `<article class="juttu"><h1>Tietoa ${SIVU} -sivustosta</h1>
<p class="ingressi">${ISKU}</p>
<div class="teksti"><p>${SIVU} kirjoittaa uutiset suoraan alkuperäislähteistä: eduskunnan äänestyksistä ja asiakirjoista, ministeriöiden, virastojen ja kuntien tiedotteista, tilastoista ja julkisista hankinnoista. Emme kirjoita muiden medioiden juttuja uudelleen.</p>
<p>Uutiset laaditaan tekoälyn avustuksella. Politiikan uutiset ja pääkirjoitukset toimittaja lukee ja tarkistaa alkuperäislähteistä ennen julkaisua. Urheilun, kulttuurin, elämän ja muiden osastojen jutut kirjoitetaan automaattisesti virallisista lähteistä, kuten sarjojen, liittojen, kulttuurilaitosten ja viranomaisten tiedotteista. Ne on merkitty tekoälyn laatimiksi. Jokaisen jutun lopussa on linkit lähteisiin.</p>
<p>Kiistanalaisissa asioissa kerromme aina, kuka väittää mitä ja mikä asian virallinen tai oikeudellinen tila on. Syytös ja tuomio pidetään erillään. Uutiset ja kannanotot pidetään erillään: pääkirjoitukset ovat kirjoittajan omia näkemyksiä ja ne on merkitty selvästi.</p>
<p>Vastaava päätoimittaja on ${TOIMITTAJA}. Oikaisupyynnöt ja palaute: <a href="mailto:${YHTEYS}">${YHTEYS}</a>. Käsittelemme oikaisupyynnöt viipymättä.</p></div></article>`;

// ---------- Päivän kooste sähköpostiin (klo 13 Suomen aikaa) ----------
async function kooste(env, pakota = false) {
  const nyt = new Date();
  const tunti = Number(nyt.toLocaleString("en-GB", { timeZone: "Europe/Helsinki", hour: "2-digit", hour12: false }));
  const paiva = nyt.toLocaleDateString("fi-FI", { timeZone: "Europe/Helsinki" });
  if (!pakota && tunti !== 13) return { ohitettu: "ei klo 13" };
  if (!pakota && await env.DB.get("kooste:" + paiva)) return { ohitettu: "jo lähetetty" };
  if (!env.BREVO_API_KEY) return { virhe: "BREVO_API_KEY puuttuu" };
  const url = (env.SIVU_URL || "https://suomitanaan.fi").replace(/\/$/, "");
  const raja = Date.now() - 26 * 3600e3;
  const ids = await lue(env, "luonnokset", []);
  const luonn = (await Promise.all(ids.map(id => lue(env, "luonnos:" + id, null)))).filter(Boolean);
  const julk = (await lue(env, "jutut", [])).filter(j => new Date(j.julkaistu).getTime() > raja);
  const auto = julk.filter(j => j.ai);
  const tt = [...luonn, ...julk].filter(x => x.tiktok && x.tiktok.koukku);
  const e = esc, h3 = t => `<h2 style="font:700 18px Georgia,serif;margin:28px 0 10px;border-top:3px solid #0b1f45;padding-top:10px">${t}</h2>`;
  const htmlSisalto = `<div style="max-width:640px;margin:0 auto;font:15px/1.55 -apple-system,Segoe UI,sans-serif;color:#111827">
<div style="background:#0b1f45;color:#fff;padding:18px 20px;border-radius:12px"><div style="font:700 26px Georgia,serif">Suomi <span style="color:#ffd27a">Tänään</span></div><div style="opacity:.8">Päivän kooste ${paiva}</div></div>
${h3(`Hyväksyttävänä ${luonn.length} juttua`)}
${luonn.length ? luonn.map(l => `<div style="margin:0 0 12px"><b>${e(l.otsikko)}</b><br><span style="color:#5b6476">${e(l.kategoria)} · ${e(l.ingressi)}</span></div>`).join("") : "<p>Ei uusia luonnoksia.</p>"}
<p><a href="${url}/toimitus" style="display:inline-block;background:#11734f;color:#fff;padding:12px 18px;border-radius:10px;text-decoration:none;font-weight:700">Avaa toimitus ja hyväksy</a></p>
${h3(`TikTok-käsikirjoitukset (${tt.length})`)}
${tt.map((x, i) => `<div style="background:#f4f5f8;border-radius:10px;padding:12px 14px;margin:0 0 12px"><div style="font:700 12px sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#1d4ed8">${i + 1}. Ohjaa: ${e(x.tiktok.sivusto || "Suomi Tänään")}</div><div style="font:700 17px Georgia,serif;margin:6px 0">${e(x.tiktok.koukku)}</div><div style="white-space:pre-wrap">${e(x.tiktok.teksti)}</div></div>`).join("") || "<p>Ei käsikirjoituksia tänään.</p>"}
${h3(`Julkaistu automaattisesti (${auto.length})`)}
${auto.map(j => `<div style="margin:0 0 8px"><a href="${url}/uutiset/${e(j.slug)}/" style="color:#1d4ed8;font-weight:700;text-decoration:none">${e(j.otsikko)}</a> <span style="color:#5b6476">· ${e(j.kategoria)}</span></div>`).join("") || "<p>Ei automaattisia julkaisuja.</p>"}
<p style="color:#5b6476;font-size:13px;margin-top:28px">Virheellisen jutun voit poistaa toimituksen Julkaistut-välilehdeltä.</p></div>`;
  const r = await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST", headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ sender: { email: env.KOOSTE_LAHETTAJA || "miika@eduskuntaseuranta.fi", name: "Suomi Tänään" }, to: [{ email: env.KOOSTE_EMAIL || "miika.koskela990@gmail.com" }],
      subject: `Suomi Tänään ${paiva}: ${luonn.length} hyväksyttävää, ${tt.length} TikTok-käsikirjoitusta`, htmlContent: htmlSisalto }) });
  if (!r.ok) return { virhe: "Brevo " + r.status + " " + (await r.text()).slice(0, 200) };
  await env.DB.put("kooste:" + paiva, "1", { expirationTtl: 3 * 86400 });
  return { ok: true, luonnokset: luonn.length, tiktok: tt.length, auto: auto.length };
}

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
  if (polku === "/api/kooste") return json(await kooste(env, true));
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
  async scheduled(event, env, ctx) { ctx.waitUntil(kooste(env).then(r => console.log("kooste", JSON.stringify(r)))); },
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
