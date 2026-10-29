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
// Arvonnat aktiivisten kirjoittajien kesken (säännöt: /arvonta/). Arpa = oma kirjoitus tai kommentti.
const ARVONNAT = [
  // Kuukausittaiset 100 €:n arvonnat poistettiin 25.10.2026 klo 16.
  { kausi: "suuri-2026-11", alku: Date.parse("2026-10-25T00:00:00+03:00"), loppu: Date.parse("2026-11-30T23:59:59+02:00"),
    palkinto: "jopa 1000 euroa rahana tai lahjakorttina haluamaasi kauppaan", lyhyt: "jopa 1000 €", valinta: true, arvontaPv: "1.12.2026",
    // Palkinto kasvaa käyttäjämäärän mukaan (omalla nimellä rekisteröityneet, ei suljettuja tilejä), laskettu arvontahetkellä.
    // Muutettu 25.10.2026: alle 500 käyttäjällä isoa palkintoa ei arvota.
    tasot: [{ min: 0, summa: 0 }, { min: 500, summa: 250 }, { min: 1000, summa: 500 }, { min: 5000, summa: 1000 }], veroKk: "joulukuun", veroPv: "12.2.2027" },
];
const ARPA = { minPituus: 0, vali: 30e3, kutsuArvat: 10, kutsuPaivat: 2, kutsuHalytys: 20 };
// Suomen aikaa: päivämäärä (YYYY-MM-DD) ja päivän alku/loppu millisekunteina
const fiPv = ms => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Helsinki" }).format(new Date(ms));
function fiPaiva(pv) {
  const h = +new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Helsinki", hour: "2-digit", hourCycle: "h23" }).format(new Date(Date.parse(pv + "T12:00:00Z")));
  const alku = Date.parse(pv + "T00:00:00Z") - (h - 12) * 3600e3; return [alku, alku + 86400e3 - 1];
}
// Väärinkäytösten esto: kertakäyttöiset sähköpostit eivät kelpaa, ja Gmailin pisteet/+-päätteet tulkitaan samaksi osoitteeksi.
const KERTAKAYTTO = new Set(("10minutemail.com 10minutemail.net 20minutemail.com guerrillamail.com guerrillamail.net guerrillamail.org guerrillamailblock.com sharklasers.com grr.la " +
  "mailinator.com mailinator.net maildrop.cc yopmail.com yopmail.fr yopmail.net temp-mail.org temp-mail.io tempmail.com tempmail.net tempmailo.com tempr.email " +
  "throwawaymail.com trashmail.com trashmail.de trashmail.net getnada.com nada.email dispostable.com fakeinbox.com mintemail.com mohmal.com emailondeck.com " +
  "mailnesia.com mytemp.email spamgourmet.com tmail.ws tmpmail.org tmpmail.net burnermail.io inboxkitten.com mailpoof.com moakt.com emailfake.com " +
  "fakemail.net luxusmail.org 1secmail.com 1secmail.org 1secmail.net mail.tm mail.gw harakirimail.com discard.email spambox.us mailcatch.com " +
  "dropmail.me 33mail.com anonaddy.me simplelogin.co duck.com").split(" "));
const PLUS_PALVELUT = new Set(["gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com", "mac.com", "proton.me", "protonmail.com", "pm.me", "fastmail.com"]);
function perusEmail(e) {
  let [n, d] = String(e).toLowerCase().split("@"); if (!d) return e;
  if (d === "googlemail.com") d = "gmail.com";
  if (PLUS_PALVELUT.has(d)) n = n.split("+")[0];
  if (d === "gmail.com") n = n.replace(/\./g, "");
  return n + "@" + d;
}
const onAdmin = e => !!e && ADMIN.some(a => perusEmail(a) === perusEmail(e));
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
    if (u.hostname === "www.netvo.fi") return Response.redirect("https://netvo.fi" + u.pathname + u.search, 301);
    if (u.pathname === "/api/kauppias") return kauppias(req, env);
    if (u.hostname === "netvo.fi") {
      const np = "/netvo" + (u.pathname === "/" ? "/" : u.pathname);
      return env.ASSETS.fetch(new Request(u.origin + np + u.search));
    }
    // Vanha polku faktapiste.fi/netvo/* ohjataan kanoniseen netvo.fi:hin
    if (u.hostname === "faktapiste.fi" && (u.pathname === "/netvo" || u.pathname.startsWith("/netvo/"))) {
      const rest = u.pathname.replace(/^\/netvo/, "") || "/";
      return Response.redirect("https://netvo.fi" + rest + u.search, 301);
    }
    if (u.pathname === "/api/video" && req.method === "POST") return lataaVideo(req, env, u);
    if (u.pathname.startsWith("/api/")) return env.FP.get(env.FP.idFromName("main")).fetch(req);
    const jm = u.pathname.match(/^\/p\/(\d+)\/?$/);
    if (jm) return jakosivu(env, u, +jm[1]);
    return env.ASSETS.fetch(req);
  },
  async scheduled(ev, env, ctx) {
    ctx.waitUntil(env.FP.get(env.FP.idFromName("main")).fetch(new Request("https://sisainen/_sisaanluku", { method: "POST" })));
  },
};

// Videon lataus: tiedosto kulkee suoraan Workerista R2:een (ei Durable Objectin kautta).
// Durable Object tarkistaa kirjautumisen ja rajat ennen latausta ja kirjaa videon sen jälkeen.
async function lataaVideo(req, env, u) {
  const vastaus = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
  if (!env.VIDEOT) return vastaus({ virhe: "Videoiden lataus ei ole vielä käytössä." }, 503);
  const fp = env.FP.get(env.FP.idFromName("main"));
  const otsakkeet = { "content-type": "application/json", cookie: req.headers.get("cookie") || "" };
  const tiedot = { tyyppi: (req.headers.get("content-type") || "").split(";")[0].trim(), koko: +req.headers.get("content-length") || 0,
    kesto: +req.headers.get("x-kesto") || 0, w: +req.headers.get("x-leveys") || 0, h: +req.headers.get("x-korkeus") || 0 };
  const l = await (await fp.fetch(new Request(u.origin + "/api/video/lupa", { method: "POST", headers: otsakkeet, body: JSON.stringify(tiedot) }))).json();
  if (!l.avain) return vastaus({ virhe: l.virhe || "Videon lataus ei onnistunut." }, 400);
  try {
    const { readable, writable } = new FixedLengthStream(tiedot.koko);
    await Promise.all([env.VIDEOT.put(l.avain, readable, { httpMetadata: { contentType: tiedot.tyyppi } }), req.body.pipeTo(writable)]);
  } catch (e) { return vastaus({ virhe: "Videon tallennus keskeytyi. Yritä uudelleen." }, 502); }
  const v = await (await fp.fetch(new Request(u.origin + "/api/video/valmis", { method: "POST", headers: otsakkeet, body: JSON.stringify({ avain: l.avain, ...tiedot }) }))).json();
  return vastaus(v, v.id ? 200 : 400);
}

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
  if (!url || /^https?:\/\/(news\.google\.com|nytpuhutaan\.fi)\//.test(url)) return null;  // ohjauslinkeistä ei voi päätellä
  try {
    const r = await fetch(url, { headers: { "user-agent": "Mozilla/5.0 (compatible; Faktapiste/1.0; +https://faktapiste.fi)" }, signal: AbortSignal.timeout(6000), redirect: "follow" });
    if (!r.ok) return null;
    const h = await r.text();
    // Sanoma (HS, IS ym.): sivun oma tila, tai jutun paidType (ensimmäinen esiintymä on itse juttu)
    const sanoma = (h.match(/"page_paywall_status"\s*:\s*"(\w+)"/) || h.match(/"paidType"\s*:\s*"(\w+)"/) || [])[1];
    if (sanoma) return sanoma.toLowerCase() !== "free";
    if (/"isAccessibleForFree"\s*:\s*(false|"false")/i.test(h) || /<meta[^>]+(content_tier|article:content_tier)[^>]+(locked|metered)/i.test(h)) return true;
    if (/"isAccessibleForFree"\s*:\s*(true|"true")/i.test(h)) return false;
    return null;
  } catch { return null; }
}

// ---------- apurit ----------
const json = (d, s = 200, h = {}) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...h } });
const virhe = (v, s = 400) => json({ virhe: v }, s);
const nyt = () => Date.now();
function satunnainen(n = 32) { const b = new Uint8Array(n); crypto.getRandomValues(b); return [...b].map(x => x.toString(16).padStart(2, "0")).join(""); }
// Salasanat: PBKDF2-SHA256 (100 000 kierrosta, satunnainen suola). Selkokielistä salasanaa ei tallenneta.
async function pbkdf2(s, suola, n) {
  const avain = await crypto.subtle.importKey("raw", new TextEncoder().encode(s), "PBKDF2", false, ["deriveBits"]);
  const b = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: suola, iterations: n }, avain, 256);
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}
async function teeSalasana(s) {
  const suola = new Uint8Array(16); crypto.getRandomValues(suola);
  return `pbkdf2$100000$${[...suola].map(x => x.toString(16).padStart(2, "0")).join("")}$${await pbkdf2(s, suola, 100000)}`;
}
async function tarkistaSalasana(s, tallennettu) {
  const [laji, n, suola, h] = String(tallennettu).split("$"); if (laji !== "pbkdf2") return false;
  const x = await pbkdf2(s, new Uint8Array(suola.match(/../g).map(c => parseInt(c, 16))), +n);
  let ero = x.length ^ h.length; for (let i = 0; i < x.length && i < h.length; i++) ero |= x.charCodeAt(i) ^ h.charCodeAt(i);
  return ero === 0;
}
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

// ---- Netvo "Puhuva kauppias": asiakas kysyy tai tilaa puhumalla, vastaus kauppiaan äänellä
const KAUPPIAAT = {
  "kauppa-leipomo": {
    aani: "3OArekHEkHv5XvmZirVD",
    kuvaus: `Olet Ville, Kotileipomo Ruis -nimisen pienen leipomon leipuri Ylivieskassa (kolmannen polven leipuri, sama juuri vuodesta 1962).
Puhut lämpimästi, rennosti ja lyhyesti kevyellä pohjalaisella puhekielellä (esim. "mää", "sää", "ny", "kyllä se", "otappa"), mutta selkeästi niin että jokainen ymmärtää.
Tuotteet (id: nimi, hinta, tiedot):
1: Juurileipä (ruis) 4,50 € – hapanjuuri, 600 g, vegaaninen, laktoositon, maidoton
2: Saaristolaisleipä 5,90 € – makeahko maltaileipä rusinoilla, 500 g, laktoositon
3: Korvapuustit 6 kpl 7,90 € – suosituin, voi ja raesokeri; vehnä, maito, muna
4: Karjalanpiirakat 10 kpl 8,50 € – laktoositon; munavoin kanssa
5: Täytekakku tilauksesta alk. 35 € – 8/12/16 hlöä (35/45/59 €), täytteet mansikka-vanilja, suklaa-vadelma, kinuski-banaani, sitruuna-mustikka; gluteeniton +5 €; tilattava 3 vrk ennen
6: Gluteenittomat kaurasämpylät 6 kpl 6,90 € – gluteeniton, laktoositon, vegaaninen, oma linja
7: Mustikkapiirakka 12,90 € – sesonki, 8 palaa
8: Lihapiirakka 3,20 € – kpl
Toimitus: nouto leipomosta (Leipurinkuja 2, Ylivieska) ilmaiseksi tai kotiinkuljetus 4,90 € Ylivieskaan, Alavieskaan, Sieviin ja Nivalaan ma–la. Yli 35 € tilaukset ilmainen toimitus. Tilaa klo 20 mennessä, niin leivotaan aamuksi. Auki ma–pe 7–17, la 8–14, su kiinni. Viikkotilaus −10 %.`,
  },
};
const kauppiasLaskuri = new Map();
async function kauppias(req, env) {
  const vas = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
  if (req.method !== "POST") return vas({ virhe: "POST" }, 405);
  const ip = req.headers.get("cf-connecting-ip") || "?", nyt = Date.now();
  const l = (kauppiasLaskuri.get(ip) || []).filter(t => nyt - t < 600000);
  if (l.length >= 25) return vas({ vastaus: "Nyt tuli niin paljon kysymyksiä, että pidetään pieni tauko. Kokeile hetken päästä uudestaan!" });
  l.push(nyt); kauppiasLaskuri.set(ip, l);
  const d = await req.json().catch(() => ({}));
  const k = KAUPPIAAT[d.kauppa];
  if (!k) return vas({ virhe: "tuntematon kauppa" }, 404);
  const viesti = puhdas(d.viesti).slice(0, 300);
  if (!viesti) return vas({ virhe: "tyhjä" }, 400);
  const historia = (Array.isArray(d.historia) ? d.historia : []).slice(-6).map(h => `${h.r === "a" ? "Asiakas" : "Sinä"}: ${puhdas(h.t).slice(0, 300)}`).join("\n");
  const kori = (Array.isArray(d.kori) ? d.kori : []).slice(0, 20).map(x => `${+x.id} x${+x.q}`).join(", ") || "tyhjä";
  const system = k.kuvaus + `

Tehtäväsi: auta asiakasta verkkokaupassa. Asiakas puhuu sinulle ääneen (teksti on puheentunnistuksesta, voi sisältää pieniä virheitä).
- Vastaa 1–3 lyhyellä lauseella (vastaus luetaan ääneen). Ei listoja, ei emojeita, ei markdownia. Kirjoita hinnat sanoina tai muodossa "7,90".
- Jos asiakas haluaa tilata tai laittaa jotain koriin, lisää tuotteet "lisaa"-kenttään ja kerro mitä lisäsit. Älä lisää mitään, ellei asiakas pyydä.
- Täytekakkua (id 5) ei lisätä suoraan: laita "avaa": 5, niin asiakas valitsee koon ja täytteen.
- Kun suosittelet tuotteita, laita niiden id:t "nayta"-kenttään.
- Jos asiakas haluaa maksaa tai mennä kassalle, laita "kassalle": true.
- Älä keksi tuotteita, hintoja tai palveluita, joita ei ole listassa. Jos et tiedä, sano että asiakas voi soittaa 040 111 2233.
- Pysy leipomon asioissa; muihin aiheisiin vastaa ystävällisesti, että autat vain leipomon tilauksissa.
Asiakkaan nykyinen kori (id x määrä): ${kori}
Palauta VAIN JSON: {"vastaus":"...","lisaa":[{"id":3,"q":2}],"nayta":[1],"avaa":null,"kassalle":false}`;
  let o;
  try { o = jsonista(await claude(env, system, (historia ? "Aiempi keskustelu:\n" + historia + "\n\n" : "") + "Asiakas: " + viesti, 400)); } catch (e) { o = null; }
  if (!o || !o.vastaus) return vas({ vastaus: "Anteeks, nyt meni ohi korvien. Sanotko uuestaan?" });
  const ok = new Set([1, 2, 3, 4, 5, 6, 7, 8]);
  const tulos = {
    vastaus: String(o.vastaus).slice(0, 400),
    lisaa: (Array.isArray(o.lisaa) ? o.lisaa : []).filter(x => x && ok.has(+x.id) && +x.id !== 5).map(x => ({ id: +x.id, q: Math.max(1, Math.min(20, Math.round(+x.q || 1))) })),
    nayta: (Array.isArray(o.nayta) ? o.nayta : []).map(Number).filter(i => ok.has(i)).slice(0, 4),
    avaa: ok.has(+o.avaa) ? +o.avaa : null,
    kassalle: !!o.kassalle,
  };
  if (env.ELEVENLABS_API_KEY && d.aani !== false) {
    try {
      const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${k.aani}?output_format=mp3_44100_64`, {
        method: "POST", headers: { "xi-api-key": env.ELEVENLABS_API_KEY, "content-type": "application/json" },
        body: JSON.stringify({ text: tulos.vastaus, model_id: "eleven_multilingual_v2", voice_settings: { stability: 0.45, similarity_boost: 0.8, style: 0.35, speed: 1.05 } }),
      });
      if (r.ok) {
        const b = new Uint8Array(await r.arrayBuffer());
        let s = ""; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
        tulos.aani = "data:audio/mpeg;base64," + btoa(s);
      }
    } catch {}
  }
  return vas(tulos);
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
      CREATE TABLE IF NOT EXISTS omakutsu(kayttaja INTEGER PRIMARY KEY, koodi TEXT UNIQUE);
      CREATE TABLE IF NOT EXISTS suositukset(kutsuttu INTEGER PRIMARY KEY, kutsuja INTEGER, luotu INTEGER);
      CREATE INDEX IF NOT EXISTS suositukset_kutsuja ON suositukset(kutsuja);
      CREATE TABLE IF NOT EXISTS seuraukset(seuraaja INTEGER, seurattava INTEGER, luotu INTEGER, PRIMARY KEY(seuraaja, seurattava));
      CREATE INDEX IF NOT EXISTS seuraukset_kohde ON seuraukset(seurattava);
      CREATE TABLE IF NOT EXISTS jaljet(kayttaja INTEGER, tyyppi TEXT, tunniste TEXT, luotu INTEGER, PRIMARY KEY(kayttaja, tyyppi, tunniste));
      CREATE INDEX IF NOT EXISTS jaljet_t ON jaljet(tyyppi, tunniste);
      CREATE TABLE IF NOT EXISTS arpaepailyt(posti INTEGER PRIMARY KEY, kayttaja INTEGER, pv TEXT, syy TEXT, luotu INTEGER);
      CREATE TABLE IF NOT EXISTS arpahylkays(id INTEGER PRIMARY KEY, kayttaja INTEGER, alku INTEGER, loppu INTEGER, kausi TEXT, syy TEXT, luotu INTEGER);
      CREATE TABLE IF NOT EXISTS laskurit(sivu TEXT, pv TEXT, nayt INTEGER DEFAULT 0, kaytot INTEGER DEFAULT 0, PRIMARY KEY(sivu, pv));`);
    // nimet eivät ole enää yksilöllisiä (oikeat nimet voivat toistua): taulu rakennetaan kerran uudelleen
    if ((this.sql.exec("SELECT v FROM asetukset WHERE k='skeema'").toArray()[0] || {}).v !== "2") {
      this.sql.exec(`CREATE TABLE IF NOT EXISTS kayttajat2(id INTEGER PRIMARY KEY, email TEXT UNIQUE, nimi TEXT, luotu INTEGER, esto INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO kayttajat2(id, email, nimi, luotu, esto) SELECT id, email, nimi, luotu, esto FROM kayttajat;
        DROP TABLE kayttajat; ALTER TABLE kayttajat2 RENAME TO kayttajat;
        INSERT OR REPLACE INTO asetukset VALUES('skeema', '2');`);
    }
    for (const a of ["ALTER TABLE kayttajat ADD COLUMN salasana TEXT", "ALTER TABLE postit ADD COLUMN nakymat INTEGER DEFAULT 0", "ALTER TABLE postit ADD COLUMN kunta TEXT", "ALTER TABLE postit ADD COLUMN muokattu INTEGER"]) { try { this.sql.exec(a); } catch {} }
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
    const k = this.yksi("SELECT k.id, k.email, k.nimi, k.esto, k.salasana IS NOT NULL AS sala FROM sessiot s JOIN kayttajat k ON k.id=s.kayttaja WHERE s.t=? AND s.vanhenee>?", t, nyt());
    if (k) { k.admin = onAdmin(k.email); k.nimiOk = oikeaNimi(k.nimi); }
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
      if (p === "/api/hallinta/laskurit" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        // Laskurien näytöt ja käytöt viimeisiltä päiviltä, suosituin ensin
        const pv = Math.min(90, Math.max(1, +u.searchParams.get("pv") || 7));
        const raja = new Date(Date.now() - pv * 86400e3).toISOString().slice(0, 10);
        return json({ pv, laskurit: this.kaikki("SELECT sivu, SUM(nayt) AS nayt, SUM(kaytot) AS kaytot FROM laskurit WHERE pv>=? GROUP BY sivu ORDER BY nayt DESC, kaytot DESC", raja) });
      }
      if (p === "/api/hallinta/holvi" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        // Ylläpidon salaisuusholvi (esim. mainostilien kirjautumisavaimet); ei koskaan julkisesti luettavissa.
        const d = await req.json(); const k = "holvi:" + String(d.nimi || "");
        if (typeof d.arvo === "string") { this.sql.exec("INSERT OR REPLACE INTO asetukset VALUES(?,?)", k, d.arvo); return json({ ok: true }); }
        const r = this.yksi("SELECT v FROM asetukset WHERE k=?", k); return json({ arvo: r ? r.v : null });
      }
      if (p === "/api/hallinta/mm" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        const out = [];
        for (const url of (u.searchParams.get("u") || "").split(" ").filter(Boolean).slice(0, 6)) {
          try {
            const r = await fetch(url, { headers: { "user-agent": "Mozilla/5.0 (compatible; Faktapiste/1.0; +https://faktapiste.fi)" }, signal: AbortSignal.timeout(8000) });
            const h = await r.text(); const os = {};
            for (const sana of ["isAccessibleForFree", "isPaid", "paid\"", "\"premium", "accessLevel", "subscriber", "\"locked", "contentTier", "\"plus\"", "paywallType", "\"free\""]) {
              const i = h.indexOf(sana); if (i >= 0) os[sana] = h.slice(Math.max(0, i - 60), i + 90);
            }
            out.push({ url, status: r.status, osumat: os });
          } catch (e) { out.push({ url, virhe: String(e.message || e) }); }
        }
        return json(out);
      }
      if (p === "/api/hallinta/arpahylkays" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) return json(await this.arpaHylkays(await req.json()));
      if (p === "/api/hallinta/arvonta" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) return json(await this.arvo(u.searchParams.get("pakota") === "1", u.searchParams.get("kausi") || "", +u.searchParams.get("hylkaa") || 0));
      if (p === "/api/hallinta/fakta" && this.env.HALLINTA && req.headers.get("x-avain") === this.env.HALLINTA) {
        const d = await req.json(); return await this.fakta({ id: 0 }, d);
      }
      const minä = this.kayttaja(req);
      const lukija = this.lukija(req, minä);
      if (p === "/api/arvonta" && m === "GET") return json(this.arvontaTila(minä));
      if (p === "/api/kutsulinkki" && m === "GET") return minä && minä.nimiOk ? json(this.omaKutsu(minä)) : virhe("Kirjaudu ensin.", 401);
      if (p === "/api/syote" && m === "GET") return json(this.syote(u, minä, lukija));
      if (p === "/api/nahty" && m === "POST") return json(this.nahty(lukija, await req.json().catch(() => ({}))));
      if (p === "/api/laskuri" && m === "POST") return json(await this.laskuriTilasto(req, await req.json().catch(() => ({}))));
      if (p.startsWith("/api/kuva/") && m === "GET") return this.naytaKuva(+p.split("/")[3]);
      if (p === "/api/kuva" && m === "POST") return await this.lataaKuva(req, minä);
      if (p === "/api/video/kansi" && m === "POST") return await this.lataaKansi(req, minä, +u.searchParams.get("id"));
      const vm = p.match(/^\/api\/video\/(\d+)(\/kansi)?$/);
      if (vm && m === "GET") return vm[2] ? this.naytaKansi(+vm[1]) : await this.naytaVideo(+vm[1], req);
      if (p.startsWith("/api/posti/") && m === "GET") return json(this.ketju(+p.split("/")[3], minä));
      if (p === "/api/mina" && minä) await this.jalki(req, minä.id);
      if (p === "/api/mina") return json({ kayttaja: minä ? { nimi: minä.nimi, nimiOk: minä.nimiOk, admin: minä.admin, salasana: !!minä.sala } : null,
        tilasto: minä && minä.admin ? { kayttajat: this.yksi("SELECT COUNT(*) AS n FROM kayttajat").n, nimelliset: this.yksi("SELECT COUNT(*) AS n FROM kayttajat WHERE nimi IS NOT NULL").n,
          kirjoittajat: this.yksi("SELECT COUNT(DISTINCT kayttaja) AS n FROM postit WHERE kayttaja IS NOT NULL").n, lukijat7: this.yksi("SELECT COUNT(DISTINCT katsoja) AS n FROM nahdyt WHERE luotu>?", nyt() - 7 * 86400e3).n } : null, jasenia: this.kayttajia(), kirjautuminen: this.env.KIRJAUTUMINEN === "auki", video: !!this.env.VIDEOT, testi: this.env.KIRJAUTUMINEN === "testi" });
      if (p === "/api/kirjaudu" && m === "POST") return await this.kirjaudu(req);
      if (p === "/api/vahvista" && m === "GET") return await this.vahvista(u, req);
      if (p === "/api/ulos" && m === "POST") { const t = evaste(req, "fp_s"); if (t) this.sql.exec("DELETE FROM sessiot WHERE t=?", t); return json({ ok: true }, 200, { "set-cookie": "fp_s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" }); }
      if (m !== "POST") return virhe("Tuntematon osoite", 404);
      if (!minä) return virhe("Kirjaudu ensin.", 401);
      if (minä.esto) return virhe("Tilisi on suljettu.", 403);
      const d = await req.json().catch(() => ({}));
      if (p === "/api/nimi") return await this.asetaNimi(minä, d, req);
      if (p === "/api/salasana") return await this.asetaSalasana(minä, d);
      if (!minä.nimiOk) return virhe("Lisää ensin oma nimesi (etu- ja sukunimi).", 400);
      if (p === "/api/posti") return await this.uusiPosti(minä, d, lukija);
      if (p === "/api/video/lupa") return this.videoLupa(minä, d);
      if (p === "/api/video/valmis") return await this.videoValmis(minä, d);
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
  // Laskurisivujen seuranta: näyttö (n) ja käyttö (k). Sama IP lasketaan kerran päivässä per sivu ja laji.
  async laskuriTilasto(req, d) {
    const sivu = String(d.s || "").replace(/[^a-z0-9-]/g, "").slice(0, 60), laji = d.t === "k" ? "k" : "n";
    if (!sivu) return { ok: false };
    const ip = (await tiiviste((req.headers.get("cf-connecting-ip") || "") + "lask")).slice(0, 16);
    if (!this.raja(`ls:${laji}:${sivu}:${ip}`, 1, 86400)) return { ok: true };
    const pv = new Date().toISOString().slice(0, 10);
    this.sql.exec(`INSERT INTO laskurit(sivu, pv, nayt, kaytot) VALUES(?,?,?,?) ON CONFLICT(sivu, pv) DO UPDATE SET ${laji === "k" ? "kaytot=kaytot+1" : "nayt=nayt+1"}`,
      sivu, pv, laji === "n" ? 1 : 0, laji === "k" ? 1 : 0);
    return { ok: true };
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
    const osoite = puhdas(d.email).toLowerCase();
    if (!/^[^\s@]{1,64}@[^\s@]+\.[a-z]{2,}$/.test(osoite) || osoite.length > 120) return virhe("Tarkista sähköpostiosoite.");
    const email = perusEmail(osoite), olemassa = this.loydaEmail(email);
    if (!olemassa && KERTAKAYTTO.has(email.split("@")[1])) return virhe("Kertakäyttöisellä sähköpostiosoitteella ei voi liittyä. Käytä omaa sähköpostiosoitettasi.");
    if (this.env.KIRJAUTUMINEN !== "auki" && !TESTAAJAT.some(a => perusEmail(a) === email) && !olemassa) {
      // Beta: uusi käyttäjä tarvitsee voimassa olevan kutsukoodin
      const k = this.yksi("SELECT koodi FROM kutsut WHERE koodi=? AND kayttoja<max", String(d.kutsu || ""));
      if (!k) return virhe("Keskustelu on beta-testissä. Tarvitset kutsulinkin, jotta voit liittyä.", 403);
      this.sql.exec("UPDATE kutsut SET kayttoja=kayttoja+1 WHERE koodi=?", k.koodi);
    }
    const ip = await tiiviste((req.headers.get("cf-connecting-ip") || "") + "fp");
    if (typeof d.salasana === "string" && d.salasana) {
      // Salasanakirjautuminen
      if (!this.raja("ls:" + email, 10, 3600) || !this.raja("lsi:" + ip, 40, 3600)) return virhe("Liian monta yritystä. Yritä hetken päästä uudelleen.", 429);
      const k = olemassa && this.yksi("SELECT id, salasana FROM kayttajat WHERE id=?", olemassa.id);
      if (!k) return json({ uusi: true });
      if (!k.salasana) return json({ eiSalasanaa: true });
      if (!(await tarkistaSalasana(d.salasana, k.salasana))) return virhe("Väärä sähköposti tai salasana.", 401);
      await this.jalki(req, k.id);
      return json({ ok: true, sisaan: true }, 200, { "set-cookie": this.uusiSessio(k.id) });
    }
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
      body: JSON.stringify({ sender: { email: "miika@eduskuntaseuranta.fi", name: "Faktapiste" }, to: [{ email: osoite }], subject: "Kirjautumislinkki Faktapisteeseen", htmlContent: html }) });
    if (!r.ok) return virhe("Viestin lähetys ei onnistunut. Yritä myöhemmin.", 502);
    return json({ ok: true });
  }
  // Etsii tilin myös Gmailin piste- ja +-muunnelmilla (vanhat tilit on voitu luoda muunnelmalla).
  loydaEmail(email) {
    const k = this.yksi("SELECT id, email FROM kayttajat WHERE email=?", email); if (k) return k;
    const d = email.split("@")[1];
    return this.kaikki("SELECT id, email FROM kayttajat WHERE email LIKE ?", "%@" + (d === "gmail.com" ? "g%mail.com" : d)).find(x => perusEmail(x.email) === email) || null;
  }
  // Tallentaa tiivisteen IP-verkosta ja selaimen satunnaistunnisteesta valetilien tunnistamiseen (ei selkokielistä IP:tä). Poistuu 180 päivässä.
  async jalki(req, kid) {
    const suola = (this.env.HALLINTA || "") + "fp-jalki", t = nyt();
    let ip = req.headers.get("cf-connecting-ip") || "";
    if (ip.includes(":")) ip = ip.split(":").slice(0, 4).join(":"); // IPv6: sama kotiverkko (/64)
    if (ip) this.sql.exec("INSERT OR REPLACE INTO jaljet VALUES(?,?,?,?)", kid, "ip", (await tiiviste(ip + suola)).slice(0, 32), t);
    const l = (req.headers.get("x-lukija") || "").replace(/[^a-f0-9]/g, "").slice(0, 32);
    if (l.length === 32) this.sql.exec("INSERT OR REPLACE INTO jaljet VALUES(?,?,?,?)", kid, "laite", (await tiiviste(l + suola)).slice(0, 32), t);
  }
  async vahvista(u, req) {
    const h = await tiiviste(u.searchParams.get("t") || "");
    const l = this.yksi("SELECT email, vanhenee FROM linkit WHERE t=?", h);
    this.sql.exec("DELETE FROM linkit WHERE t=? OR vanhenee<?", h, nyt());
    if (!l || l.vanhenee < nyt()) return new Response(null, { status: 302, headers: { location: "/?kirjautuminen=vanhentunut" } });
    let k = this.loydaEmail(l.email);
    if (!k) { this.sql.exec("INSERT INTO kayttajat(email, luotu) VALUES(?,?)", l.email, nyt()); k = this.yksi("SELECT id FROM kayttajat WHERE email=?", l.email); }
    await this.jalki(req, k.id);
    this.sql.exec("DELETE FROM jaljet WHERE luotu<?", nyt() - 180 * 86400e3);
    return new Response(null, { status: 302, headers: { location: "/?tervetuloa=1", "set-cookie": this.uusiSessio(k.id) } });
  }
  uusiSessio(kid) {
    const s = satunnainen();
    this.sql.exec("INSERT INTO sessiot VALUES(?,?,?)", s, kid, nyt() + 60 * 86400e3);
    this.sql.exec("DELETE FROM sessiot WHERE vanhenee<?", nyt());
    return `fp_s=${s}; Path=/; Max-Age=${60 * 86400}; HttpOnly; Secure; SameSite=Lax`;
  }
  async asetaSalasana(minä, d) {
    const s = String(d.salasana || "");
    if (s.length < 8) return virhe("Salasanassa pitää olla vähintään 8 merkkiä.");
    if (s.length > 200) return virhe("Salasana on liian pitkä.");
    if (!this.raja("ss:" + minä.id, 10, 3600)) return virhe("Liian monta yritystä. Yritä hetken päästä uudelleen.", 429);
    this.sql.exec("UPDATE kayttajat SET salasana=? WHERE id=?", await teeSalasana(s), minä.id);
    return json({ ok: true });
  }
  async asetaNimi(minä, d, req) {
    const n = isot(puhdas(d.nimi).replace(/\s+/g, " "));
    if (!oikeaNimi(n)) return virhe("Kirjoita oma etu- ja sukunimesi, esimerkiksi Matti Virtanen.");
    if (/faktapiste|ylläpito|moderaattori/i.test(n)) return virhe("Tätä nimeä ei voi käyttää.");
    this.sql.exec("UPDATE kayttajat SET nimi=? WHERE id=?", n, minä.id);
    if (req) await this.jalki(req, minä.id);
    if (!minä.nimiOk && d.suosittelija) {
      const k = this.yksi("SELECT kayttaja FROM omakutsu WHERE koodi=?", String(d.suosittelija).toLowerCase().slice(0, 12));
      if (k && k.kayttaja !== minä.id) {
        this.sql.exec("INSERT OR IGNORE INTO suositukset VALUES(?,?,?)", minä.id, k.kayttaja, nyt());
        await this.kutsuHalytys(k.kayttaja);
      }
    }
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
  // ---- arvonta ----
  arvat(a) {
    // 1 arpa jokaisesta kirjoituksesta tai kommentista (ei pituusvaatimusta, ei piilotettu). Ei päivärajaa.
    // Sama teksti lasketaan kerran, ja alle minuutin välein kirjoitetut viestit lasketaan yhdeksi.
    // Ylläpitäjän hylkäämät päivät (arpahylkays.alku–loppu) ja kaudet (arpahylkays.kausi) eivät tuota arpoja.
    const l = this.kaikki(`SELECT p.kayttaja, k.nimi, k.email, COUNT(DISTINCT CASE WHEN p.teksti <> '' THEN p.teksti ELSE 'kuva' || p.id END) AS arvat FROM postit p JOIN kayttajat k ON k.id=p.kayttaja
      WHERE p.kayttaja IS NOT NULL AND p.piilotettu=0 AND length(p.teksti) >= ? AND p.luotu BETWEEN ? AND ? AND k.esto=0 AND k.nimi IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM postit q WHERE q.kayttaja=p.kayttaja AND q.piilotettu=0 AND length(q.teksti) >= ? AND q.luotu < p.luotu AND q.luotu > p.luotu - ?)
        AND NOT EXISTS (SELECT 1 FROM arpahylkays h WHERE h.kayttaja=p.kayttaja AND h.kausi IS NULL AND p.luotu BETWEEN h.alku AND h.loppu)
      GROUP BY p.kayttaja`, ARPA.minPituus, a.alku, a.loppu, ARPA.minPituus, ARPA.vali)
      .filter(r => !onAdmin(r.email));
    // Kutsubonus: 10 arpaa jokaisesta kaverista, joka liittyi kauden aikana kutsulinkillä ja kirjoitti kauden aikana vähintään kahtena eri päivänä. Ei ylärajaa.
    const bonus = new Map(this.kaikki(`SELECT s.kutsuja, COUNT(DISTINCT s.kutsuttu) AS n FROM suositukset s JOIN kayttajat k ON k.id=s.kutsuttu
      WHERE k.esto=0 AND k.nimi IS NOT NULL AND s.luotu BETWEEN ? AND ?
        AND (SELECT COUNT(DISTINCT date(p.luotu / 1000, 'unixepoch', '+2 hours')) FROM postit p WHERE p.kayttaja=s.kutsuttu AND p.piilotettu=0 AND length(p.teksti) >= ? AND p.luotu BETWEEN ? AND ?) >= ?
        AND NOT EXISTS (SELECT 1 FROM jaljet j1 JOIN jaljet j2 ON j2.tyyppi='laite' AND j2.tunniste=j1.tunniste WHERE j1.tyyppi='laite' AND j1.kayttaja=s.kutsuttu AND j2.kayttaja=s.kutsuja)
        AND NOT EXISTS (SELECT 1 FROM suositukset s2 JOIN jaljet j1 ON j1.kayttaja=s2.kutsuttu AND j1.tyyppi='laite' JOIN jaljet j2 ON j2.kayttaja=s.kutsuttu AND j2.tyyppi='laite' AND j2.tunniste=j1.tunniste
          WHERE s2.kutsuja=s.kutsuja AND s2.kutsuttu<s.kutsuttu)
      GROUP BY s.kutsuja`, a.alku, a.loppu, ARPA.minPituus, a.alku, a.loppu, ARPA.kutsuPaivat).map(r => [r.kutsuja, r.n]));
    for (const r of l) { r.kutsut = bonus.get(r.kayttaja) || 0; r.arvat += r.kutsut * ARPA.kutsuArvat; bonus.delete(r.kayttaja); }
    // kutsuja, joka ei itse ole kirjoittanut kaudella, saa silti kutsuarpansa
    for (const [kid, n] of bonus) {
      const k = this.yksi("SELECT id, nimi, email, esto FROM kayttajat WHERE id=?", kid);
      if (k && !k.esto && k.nimi && !onAdmin(k.email)) l.push({ kayttaja: k.id, nimi: k.nimi, email: k.email, arvat: n * ARPA.kutsuArvat, kutsut: n });
    }
    const kaudelta = new Set(this.kaikki("SELECT kayttaja FROM arpahylkays WHERE kausi=?", a.kausi).map(r => r.kayttaja));
    return l.filter(r => !kaudelta.has(r.kayttaja) && r.arvat > 0);
  }
  omaKutsu(minä) {
    let r = this.yksi("SELECT koodi FROM omakutsu WHERE kayttaja=?", minä.id);
    if (!r) {
      const aakk = "abcdefghjkmnpqrstuvwxyz23456789";
      for (let i = 0; i < 5 && !r; i++) {
        const b = new Uint8Array(6); crypto.getRandomValues(b); const koodi = [...b].map(x => aakk[x % aakk.length]).join("");
        try { this.sql.exec("INSERT INTO omakutsu VALUES(?,?)", minä.id, koodi); r = { koodi }; } catch {}
      }
    }
    const kutsutut = this.yksi("SELECT COUNT(*) AS n FROM suositukset s JOIN kayttajat k ON k.id=s.kutsuttu WHERE s.kutsuja=? AND k.esto=0", minä.id).n;
    const kirjoittaneet = this.yksi(`SELECT COUNT(*) AS n FROM suositukset s WHERE s.kutsuja=? AND
      (SELECT COUNT(DISTINCT date(p.luotu / 1000, 'unixepoch', '+2 hours')) FROM postit p WHERE p.kayttaja=s.kutsuttu AND p.piilotettu=0 AND length(p.teksti) >= ?) >= ?`, minä.id, ARPA.minPituus, ARPA.kutsuPaivat).n;
    return { koodi: r.koodi, url: "https://faktapiste.fi/?k=" + r.koodi, kutsutut, kirjoittaneet, arvatPerKaveri: ARPA.kutsuArvat };
  }
  // Ilmoitus ylläpitäjälle, kun joku on kutsunut 20, 40, 60... kaveria: lista kutsutuista tarkistusta varten.
  async kutsuHalytys(kid) {
    try {
      const n = this.yksi("SELECT COUNT(*) AS n FROM suositukset WHERE kutsuja=?", kid).n;
      if (!n || n % ARPA.kutsuHalytys !== 0) return;
      const kutsuja = this.yksi("SELECT nimi, luotu FROM kayttajat WHERE id=?", kid) || {};
      const lista = this.kaikki(`SELECT k.id, k.nimi, k.luotu, (SELECT COUNT(*) FROM postit p WHERE p.kayttaja=k.id AND p.piilotettu=0 AND length(p.teksti) >= ?) AS kirj,
          EXISTS (SELECT 1 FROM jaljet j1 JOIN jaljet j2 ON j2.tyyppi=j1.tyyppi AND j2.tunniste=j1.tunniste WHERE j1.kayttaja=k.id AND j2.kayttaja=? AND j1.tyyppi='ip') AS verkko
        FROM suositukset s JOIN kayttajat k ON k.id=s.kutsuttu WHERE s.kutsuja=? ORDER BY s.luotu DESC LIMIT 25`, ARPA.minPituus, kid, kid);
      const verkossa = lista.filter(r => r.verkko).length, hiljaiset = lista.filter(r => !r.kirj).length;
      await telegram(this.env, `👥 ${kutsuja.nimi || "Käyttäjä"} (tili #${kid}) on kutsunut nyt ${n} kaveria Faktapisteeseen.\n` +
        `Viimeisimmät ${lista.length}: ${hiljaiset} ei ole vielä kirjoittanut, ${verkossa} samasta verkosta kuin kutsuja.\n` +
        lista.slice(0, 15).map(r => `– ${r.nimi || "(ei nimeä)"} #${r.id}, ${r.kirj} kirjoitusta${r.verkko ? ", sama verkko" : ""}`).join("\n") +
        `\n\nJos kutsutut näyttävät oikeilta ihmisiltä, älä tee mitään. Valetileistä voit hylätä kutsujan kauden arvat GitHubissa "Arpojen tarkistus" (toiminto=kausi, kayttaja=${kid}).`);
    } catch {}
  }
  kayttajia() { return this.yksi("SELECT COUNT(*) AS n FROM kayttajat WHERE nimi IS NOT NULL AND esto=0").n; }
  taso(a, n) { return a.tasot ? a.tasot.filter(x => n >= x.min).at(-1) : null; }
  arvontaTila(minä) {
    const t = nyt();
    const kaynnissa = ARVONNAT.filter(a => t >= a.alku && t <= a.loppu).map(a => {
      const l = this.arvat(a);
      const n = a.tasot ? this.kayttajia() : null, ta = a.tasot ? this.taso(a, n) : null, seur = a.tasot ? a.tasot.find(x => x.min > n) : null;
      return { kausi: a.kausi, palkinto: a.palkinto, lyhyt: a.lyhyt, arvontaPv: a.arvontaPv, osallistujia: l.length, arvoja: l.reduce((s, r) => s + r.arvat, 0),
        kayttajia: n, nyt: ta ? ta.summa : null, seuraava: seur ? { min: seur.min, summa: seur.summa } : null, tasot: a.tasot || null,
        omat: minä ? (l.find(r => r.kayttaja === minä.id) || { arvat: 0 }).arvat : null };
    });
    return { arvonnat: kaynnissa, kaynnissa: kaynnissa.length > 0, kutsuArvat: ARPA.kutsuArvat, yllapitaja: !!(minä && minä.admin) };
  }
  // Arpoo kaikki päättyneet, arpomattomat kaudet (tai pakotettuna yhden kauden). Voittomahdollisuus on suhteessa arpojen määrään.
  // Ylläpidon tarkistuslista voittajasta: tilin ikä, kirjoitukset ja yhteiset laitteet/verkot muiden osallistujien tai kutsuttujen kanssa.
  riski(v, l, a) {
    const k = this.yksi("SELECT luotu FROM kayttajat WHERE id=?", v.kayttaja) || {};
    const pv = Math.floor((nyt() - (k.luotu || nyt())) / 86400e3);
    const n = this.yksi("SELECT COUNT(*) AS n FROM postit WHERE kayttaja=? AND piilotettu=0 AND length(teksti)>=? AND luotu BETWEEN ? AND ?", v.kayttaja, ARPA.minPituus, a.alku, a.loppu).n;
    const nimi = new Map(l.map(r => [r.kayttaja, r.nimi]));
    const yhteiset = tyyppi => [...new Set(this.kaikki(`SELECT DISTINCT j2.kayttaja AS id FROM jaljet j1 JOIN jaljet j2 ON j2.tyyppi=j1.tyyppi AND j2.tunniste=j1.tunniste
      WHERE j1.kayttaja=? AND j1.tyyppi=? AND j2.kayttaja<>?`, v.kayttaja, tyyppi, v.kayttaja).map(r => r.id))];
    const kutsutut = new Set(this.kaikki("SELECT kutsuttu FROM suositukset WHERE kutsuja=?", v.kayttaja).map(r => r.kutsuttu));
    const kuvaa = ids => ids.map(id => (nimi.get(id) || "tili #" + id) + (kutsutut.has(id) ? " (kutsuttu)" : "")).slice(0, 6).join(", ");
    const laite = yhteiset("laite"), verkko = yhteiset("ip");
    const ep = this.yksi("SELECT COUNT(*) AS n FROM arpaepailyt WHERE kayttaja=? AND luotu BETWEEN ? AND ?", v.kayttaja, a.alku, a.loppu).n;
    const hy = this.yksi("SELECT COUNT(*) AS n FROM arpahylkays WHERE kayttaja=?", v.kayttaja).n;
    const varoitukset = [];
    if (pv < 7) varoitukset.push(`tili on vain ${pv} päivää vanha`);
    if (ep) varoitukset.push(`${ep} roskaksi epäiltyä viestiä kaudella`);
    if (hy) varoitukset.push(`${hy} aiempaa arpojen hylkäystä`);
    if (laite.length) varoitukset.push(`sama laite/selain kuin: ${kuvaa(laite)}`);
    if (verkko.filter(id => kutsutut.has(id)).length >= 2) varoitukset.push(`${verkko.filter(id => kutsutut.has(id)).length} kutsuttua samasta verkosta`);
    return `\n\n🔎 Tarkista ennen palkinnon antamista (tili #${v.kayttaja}):\n– tilin ikä ${pv} pv, ${n} arpaan kelpaavaa kirjoitusta kaudella, ${v.kutsut || 0} kutsuttua kaveria\n` +
      (verkko.length ? `– sama verkko kuin: ${kuvaa(verkko)} (voi olla sama koti tai mobiiliverkko)\n` : "") +
      (varoitukset.length ? "⚠️ " + varoitukset.join("; ") + "\n" : "✅ ei varoituksia\n") +
      `Lue voittajan kirjoitukset Faktapisteessä. Rahapalkinto maksetaan vain voittajan omissa nimissä olevalle tilille.\n` +
      `Jos hylkäät: aja GitHubissa \"Faktapisteen arvonta\" kausi=${a.kausi}, hylkaa=${v.kayttaja}.`;
  }
  async arvo(pakota, kausi, hylkaa) {
    const tulokset = [];
    for (const a of ARVONNAT) {
      if (kausi && a.kausi !== kausi) continue;
      const avain = "arvonta:" + a.kausi, hk = "arvonta-hylatyt:" + a.kausi;
      if (hylkaa && kausi) {
        // Uudelleenarvonta: hylätty voittaja suljetaan pois ja kausi arvotaan uudelleen.
        const h = JSON.parse((this.yksi("SELECT v FROM asetukset WHERE k=?", hk) || { v: "[]" }).v);
        if (!h.includes(hylkaa)) h.push(hylkaa);
        this.sql.exec("INSERT OR REPLACE INTO asetukset VALUES(?,?)", hk, JSON.stringify(h));
        this.sql.exec("DELETE FROM asetukset WHERE k=?", avain);
      }
      const hylatyt = new Set(JSON.parse((this.yksi("SELECT v FROM asetukset WHERE k=?", hk) || { v: "[]" }).v));
      const vanha = this.yksi("SELECT v FROM asetukset WHERE k=?", avain);
      if (vanha) { tulokset.push({ kausi: a.kausi, jo: true }); continue; }
      if (nyt() <= a.loppu && !(pakota && kausi) && !(hylkaa && kausi)) continue;
      if (a.tasot && !this.taso(a, this.kayttajia()).summa) {
        // Käyttäjiä alle ensimmäisen palkintotason: isoa palkintoa ei arvota
        const tulos = { kausi: a.kausi, eiPalkintoa: true, kayttajia: this.kayttajia(), aika: new Date().toISOString() };
        this.sql.exec("INSERT INTO asetukset VALUES(?,?)", avain, JSON.stringify(tulos));
        await telegram(this.env, `ℹ️ Faktapisteen iso arvonta (${a.kausi}): käyttäjiä ${tulos.kayttajia}, alle ${a.tasot[1].min} → isoa palkintoa ei arvota sääntöjen mukaan. Ei arpajaisveroa tästä.`);
        tulokset.push(tulos); continue;
      }
      const l = this.arvat(a).filter(r => !hylatyt.has(r.kayttaja)), yht = l.reduce((s, r) => s + r.arvat, 0);
      if (!yht) { tulokset.push({ kausi: a.kausi, virhe: "Ei osallistujia." }); continue; }
      const r = new Uint32Array(1); crypto.getRandomValues(r);
      let x = r[0] % yht, voittaja = l[0];
      for (const o of l) { if (x < o.arvat) { voittaja = o; break; } x -= o.arvat; }
      const ta = a.tasot ? this.taso(a, this.kayttajia()) : null;
      const palkinto = ta ? `${ta.summa} euroa rahana tai lahjakorttina voittajan valitsemaan kauppaan` : a.palkinto;
      const vero = ta ? `${Math.round(ta.summa * 0.3)} € arpajaisveroa (${this.kayttajia()} käyttäjää → ${ta.summa} €). Ilmoita ja maksa ${a.veroKk || ""} arpajaisvero OmaVerossa viimeistään ${a.veroPv || ""}` : a.vero;
      const tulos = { kausi: a.kausi, uusinta: hylatyt.size || undefined, summa: ta ? ta.summa : null, voittaja: voittaja.nimi, arvat: voittaja.arvat, osallistujia: l.length, arvoja: yht, aika: new Date().toISOString() };
      this.sql.exec("INSERT INTO asetukset VALUES(?,?)", avain, JSON.stringify(tulos));
      await telegram(this.env, `🎁 Faktapisteen arvonta (${ta ? ta.summa + " €" : a.lyhyt}, ${a.kausi}): voittaja ${voittaja.nimi} (${voittaja.email}), ${voittaja.arvat}/${yht} arpaa, ${l.length} osallistujaa.\n` +
        (a.valinta ? `Palkinto: ${palkinto}. Kysy voittajalta, haluaako hän sen rahana vai lahjakorttina ja mihin kauppaan, ja maksa tai lähetä se. Ilmoita` : `Lähetä ${a.palkinto.replace("lahjakortin", "lahjakortti")} voittajalle ja ilmoita`) + ` voitosta Faktapisteessä etunimellä.\nVero: ${vero}. Palkinto on voittajalle verovapaa.` + (hylatyt.size ? `\n(Uusinta-arvonta, hylättyjä: ${hylatyt.size})` : "") + this.riski(voittaja, l, a));
      tulokset.push(tulos);
    }
    return { tulokset };
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
  videoLupa(minä, d) {
    if (!this.env.VIDEOT) return virhe("Videoiden lataus ei ole vielä käytössä.", 503);
    if (!VIDEO_TYYPIT.includes(d.tyyppi)) return virhe("Videon muoto ei kelpaa. Käytä MP4-, MOV- tai WebM-videota.");
    if (!(d.koko > 1000)) return virhe("Video on tyhjä.");
    if (d.koko > VIDEO_MAX) return virhe("Video on liian suuri (enintään 100 Mt).");
    if (d.kesto > VIDEO_KESTO + 1) return virhe("Video on liian pitkä (enintään 3 minuuttia).");
    if (!this.raja("video:" + minä.id, 10, 86400)) return virhe("Olet ladannut tänään jo 10 videota. Jatka huomenna.", 429);
    // liittämättömät videot siivotaan vuorokauden kuluttua
    this.poistaVideot(this.kaikki("SELECT id, avain FROM videot WHERE posti IS NULL AND luotu<?", nyt() - 86400e3));
    const avain = "v/" + minä.id + "/" + satunnainen();
    this.sql.exec("INSERT OR REPLACE INTO asetukset VALUES(?,?)", "vlupa:" + avain, JSON.stringify({ k: minä.id, t: nyt() }));
    return json({ ok: true, avain });
  }
  async videoValmis(minä, d) {
    const lupa = this.yksi("SELECT v FROM asetukset WHERE k=?", "vlupa:" + String(d.avain || ""));
    let l = null; try { l = lupa ? JSON.parse(lupa.v) : null; } catch {}
    if (!l || l.k !== minä.id || nyt() - l.t > 3 * 3600e3) return virhe("Videon lupa on vanhentunut. Yritä uudelleen.", 403);
    const o = await this.env.VIDEOT.head(d.avain);
    if (!o) return virhe("Videon tallennus ei onnistunut. Yritä uudelleen.");
    this.sql.exec("DELETE FROM asetukset WHERE k=?", "vlupa:" + d.avain);
    const w = Math.min(10000, +d.w || 0), h = Math.min(10000, +d.h || 0);
    this.sql.exec("INSERT INTO videot(kayttaja, posti, avain, tyyppi, koko, w, h, kesto, luotu) VALUES(?,?,?,?,?,?,?,?,?)", minä.id, null, d.avain, d.tyyppi, o.size, w, h, +d.kesto || 0, nyt());
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
    if (!this.raja("p:" + minä.id, 60, 3600)) return virhe("Olet kirjoittanut paljon tunnin sisällä. Pidä pieni tauko.", 429);
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
    this.ctx.waitUntil(this.arpaTarkistus(id, minä, teksti));
    return json({ ok: true, id });
  }
  // Arvonnan roskaviestien tunnistus: tekoäly vain MERKITSEE epäilyttävän viestin ja ilmoittaa ylläpitäjälle Telegramiin.
  // Arpoja ei poisteta automaattisesti; ylläpitäjä päättää (/api/hallinta/arpahylkays, GitHubin "Arpojen tarkistus").
  async arpaTarkistus(id, minä, teksti) {
    try {
      const t = nyt();
      if (!teksti || onAdmin(minä.email) || !ARVONNAT.some(a => t >= a.alku && t <= a.loppu)) return;
      const pv = fiPv(t), [alku] = fiPaiva(pv);
      // Vastaus toisen käyttäjän viestiin: mukaan alkuperäinen viesti, jotta väittelyä ei tulkita roskaksi.
      const ylempi = this.yksi("SELECT p.teksti, p.kayttaja FROM postit p JOIN postit u ON u.vanhempi=p.id WHERE u.id=?", id);
      const keskustelu = ylempi && ylempi.kayttaja !== minä.id ? "\n\nViesti on VASTAUS toisen käyttäjän viestiin:\n" + String(ylempi.teksti || "").slice(0, 400) : "";
      const aiemmat = this.kaikki("SELECT teksti FROM postit WHERE kayttaja=? AND id<>? AND luotu>=? ORDER BY id DESC LIMIT 6", minä.id, id, alku).map(r => "- " + r.teksti.slice(0, 200));
      const v = jsonista(await claude(this.env,
        `Faktapisteessä jokainen kirjoitus on arpa kuukausiarvonnassa. Arvioi, onko UUSI viesti selvästi pelkkää arpojen keräämistä varten tehtyä roskaa: merkityksetöntä täytettä, sanasalaattia, samaa asiaa toistavaa sarjapostausta, pelkkää "osallistun arvontaan" -tyyppistä tekstiä tai muualta kopioitua massaa. Lyhyt mutta aito kommentti, mielipide, kysymys tai kärkeväkin kannanotto EI ole roskaa. Keskustelu ja väittely muiden kanssa EI KOSKAAN ole roskaa, vaikka viestejä tulisi paljon, ne olisivat lyhyitä tai samoja perusteluja toistettaisiin: jos viesti vastaa toisen ihmisen viestiin asiaan liittyen, vastaa false. Viestien määrä ei yksinään ole koskaan peruste. Jos olet epävarma, vastaa false. Vastaa vain JSON: {"roska":false} tai {"roska":true,"syy":"lyhyt syy suomeksi"}.`,
        "UUSI viesti:\n" + teksti.slice(0, 800) + keskustelu + "\n\nSaman käyttäjän aiemmat viestit tänään:\n" + (aiemmat.join("\n") || "(ei muita)"), 120));
      if (!v || v.roska !== true) return;
      this.sql.exec("INSERT OR REPLACE INTO arpaepailyt VALUES(?,?,?,?,?)", id, minä.id, pv, String(v.syy || "").slice(0, 160), t);
      const n = this.yksi("SELECT COUNT(*) AS n FROM arpaepailyt WHERE kayttaja=? AND pv=?", minä.id, pv).n;
      if (![1, 5, 15, 40].includes(n)) return; // ei tulvaa: ilmoitus 1., 5., 15. ja 40. epäilystä päivässä
      const kirj = this.yksi("SELECT COUNT(DISTINCT teksti) AS n FROM postit WHERE kayttaja=? AND piilotettu=0 AND length(teksti)>=? AND luotu>=?", minä.id, ARPA.minPituus, alku).n;
      const k = this.yksi("SELECT luotu FROM kayttajat WHERE id=?", minä.id) || {};
      const ika = Math.floor((t - (k.luotu || t)) / 86400e3);
      const hy = this.yksi("SELECT COUNT(*) AS n FROM arpahylkays WHERE kayttaja=?", minä.id).n;
      const kaudet = ARVONNAT.filter(a => t >= a.alku && t <= a.loppu).map(a => a.kausi).join(" tai ");
      await telegram(this.env, `🚩 Mahdollista arpaspämmiä: ${minä.nimi} (tili #${minä.id}, tili ${ika} pv vanha)\n` +
        `Tänään ${pv}: ${kirj} kirjoitusta, joista tekoäly epäilee ${n}. Aiempia hylkäyksiä: ${hy}.\n` +
        `Syy: ${v.syy || "–"}\nViesti: "${teksti.slice(0, 220)}"\nhttps://faktapiste.fi/p/${id}\n\n` +
        `Mitään ei ole poistettu. Tarkista käyttäjän viestit ja päätä itse. GitHubissa "Arpojen tarkistus":\n` +
        `– päivän arvat pois: toiminto=paiva, kayttaja=${minä.id}, pv=${pv}\n– koko kauden arvat pois: toiminto=kausi, kayttaja=${minä.id}, kausi=${kaudet}\n– jos kaikki on kunnossa, älä tee mitään.`);
    } catch {}
  }
  async arpaHylkays(d) {
    const kid = +d.kayttaja, k = this.yksi("SELECT id, nimi FROM kayttajat WHERE id=?", kid);
    if (!k) return { virhe: "Käyttäjää ei löytynyt." };
    if (d.toiminto === "paiva") {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(d.pv || "")) return { virhe: "Anna päivä muodossa 2026-10-25." };
      const [alku, loppu] = fiPaiva(d.pv);
      this.sql.exec("INSERT INTO arpahylkays(kayttaja, alku, loppu, syy, luotu) VALUES(?,?,?,?,?)", kid, alku, loppu, "pv " + d.pv, nyt());
    } else if (d.toiminto === "kausi") {
      for (const kausi of String(d.kausi || "").split(/[\s,]+|\stai\s/).filter(x => ARVONNAT.some(a => a.kausi === x)))
        this.sql.exec("INSERT INTO arpahylkays(kayttaja, kausi, syy, luotu) VALUES(?,?,?,?)", kid, kausi, "kausi " + kausi, nyt());
    } else if (d.toiminto === "palauta") {
      this.sql.exec("DELETE FROM arpahylkays WHERE kayttaja=?", kid);
    } else return { virhe: "Toiminto: paiva, kausi tai palauta." };
    const voimassa = this.kaikki("SELECT syy FROM arpahylkays WHERE kayttaja=?", kid).map(r => r.syy);
    const arvat = ARVONNAT.filter(a => nyt() <= a.loppu + 30 * 86400e3).map(a => `${a.kausi}: ${(this.arvat(a).find(r => r.kayttaja === kid) || { arvat: 0 }).arvat}`).join(", ");
    await telegram(this.env, `✅ Arpojen tarkistus: ${k.nimi} (#${kid}) – ${d.toiminto}.\nVoimassa olevat hylkäykset: ${voimassa.join(", ") || "ei"}\nArvat nyt: ${arvat}`);
    return { ok: true, voimassa, arvat };
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
        const mm = await maksumuuri(x.juttu);
        n += this.lisaaAuto("korjausvahti", x.url, "", { tyyppi: "muutos", lahde: "Korjausvahti", media: x.media, ennen: x.ennen, nyt: x.nyt, url: x.url, juttu: x.juttu || null, maksumuuri: mm, mmv: 3 }, Date.parse(x.havaittu) || nyt());
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
        n += this.lisaaAuto("keraysvahti", x.l, "", { tyyppi: "varoitus", lahde: "Keräysvahti", otsikko: x.o, media: x.s, url: x.l, maksumuuri: mm, mmv: 3 }, Date.parse(x.a) || nyt());
      }
      tulos.keraysvahti = n;
    } catch (e) { tulos.keraysvahti = "virhe " + e.message; }
    // Faktapisteen omat palvelutiedotteet (lisätään kerran)
    let tn = 0;
    for (const x of TIEDOTTEET) tn += this.lisaaAuto("faktapiste", "tiedote:" + x.id, x.teksti, { tyyppi: "uutinen", lahde: "Uusi palvelu", otsikko: x.otsikko, kuvaus: x.kuvaus, url: x.url }, Date.parse(x.aika));
    tulos.faktapiste = tn;
    // Maksumuurimerkintä myös aiemmin tuoduille uutisille (enintään 8 kerralla). Korjausvahdissa tarkistetaan alkuperäinen juttu.
    let tm = 0, jutut = null;
    for (const r of this.kaikki("SELECT id, lahde, kortti FROM postit WHERE lahde IN ('korjausvahti','keraysvahti') AND luotu>? AND kortti NOT LIKE '%\"mmv\":3%' ORDER BY luotu DESC LIMIT 8", nyt() - 5 * 86400e3)) {
      try {
        const k = JSON.parse(r.kortti);
        if (r.lahde === "korjausvahti" && !k.juttu) {
          if (!jutut) { jutut = {}; try { for (const x of (await hae("https://nytpuhutaan.fi/muutokset/nostot.json")).nostot || []) jutut[x.url] = x.juttu; } catch {} }
          k.juttu = jutut[k.url] || null;
        }
        k.maksumuuri = await maksumuuri(r.lahde === "korjausvahti" ? k.juttu : k.url); k.mmv = 3;
        this.sql.exec("UPDATE postit SET kortti=? WHERE id=?", JSON.stringify(k), r.id); tm++;
      } catch {}
    }
    tulos.maksumuuri = tm;
    // siivous
    this.sql.exec("DELETE FROM rajat WHERE vanhenee<?", nyt());
    this.sql.exec("DELETE FROM linkit WHERE vanhenee<?", nyt());
    return tulos;
  }
}
