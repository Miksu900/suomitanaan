// Pykälävahti: vastaa kysymyksiin Suomen laista ajantasaisen lainsäädännön (Finlex) pohjalta.
// 1) Kevyt malli valitsee kysymykseen liittyvät lait ja hakusanat, 2) pykälät pisteytetään,
// 3) varsinainen malli vastaa VAIN annettujen pykälien perusteella ja viittaa niihin.
// Kysymyksiä ei tallenneta. IP-osoitteesta lasketaan vain päivän tiiviste käyttörajaa varten.

const MALLI_HAKU = "claude-haiku-5-5";
const MALLI_VASTAUS = "claude-sonnet-5-5";
const RAJA_IP = 15;        // kysymystä / vuorokausi / käyttäjä
const RAJA_YHT = 400;      // kysymystä / vuorokausi yhteensä (kustannuskatto)

const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

// Poistetaan tunnistetiedot ennen kuin teksti lähtee tekoälylle
function siivoa(s) {
  return String(s || "")
    .replace(/\b\d{6}[-+A-FU-Y]\d{3}[0-9A-Y]\b/gi, "[henkilötunnus poistettu]")
    .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, "[sähköposti poistettu]")
    .replace(/(\+358|\b0)[\s-]?\d{1,3}([\s-]?\d){5,8}\b/g, "[puhelinnumero poistettu]")
    .replace(/\bFI\d{2}(\s?\d{4}){3}\s?\d{2}\b/gi, "[tilinumero poistettu]")
    .slice(0, 5000).trim();
}

async function tiiviste(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].slice(0, 12).map((x) => x.toString(16).padStart(2, "0")).join("");
}

async function rajoita(req, env) {
  const pv = new Date().toISOString().slice(0, 10);
  const ip = await tiiviste((req.headers.get("CF-Connecting-IP") || "") + pv + (env.SUOLA || "pv"));
  const [a, b] = await Promise.all([env.DB.get("ip:" + ip), env.DB.get("yht:" + pv)]);
  if (Number(a || 0) >= RAJA_IP) return "Päivän kysymysmäärä on täynnä. Voit jatkaa huomenna.";
  if (Number(b || 0) >= RAJA_YHT) return "Palvelun päivittäinen kysymysmäärä on täynnä. Yritä huomenna uudelleen.";
  await Promise.all([env.DB.put("ip:" + ip, String(Number(a || 0) + 1), { expirationTtl: 90000 }),
                     env.DB.put("yht:" + pv, String(Number(b || 0) + 1), { expirationTtl: 172800 })]);
  return null;
}

async function claude(env, malli, system, user, maxTokens) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: malli, max_tokens: maxTokens, system, messages: [{ role: "user", content: user }] }),
  });
  if (!r.ok) throw new Error("Tekoälypalvelu ei vastannut (" + r.status + " " + (await r.text()).slice(0, 160) + ")");
  const d = await r.json();
  const t = (d.content || []).filter((c) => c.type === "text").map((c) => c.text || "").join("");
  if (!t) throw new Error("tyhjä vastaus: " + d.stop_reason + " " + JSON.stringify((d.content || []).map((c) => c.type)) + " " + JSON.stringify(d.usage || {}));
  return t;
}

function jsonista(s) {
  const m = s.match(/\{[\s\S]*\}/);
  return m ? JSON.parse(m[0]) : null;
}

const cache = {};
async function data(env, origin, polku) {
  if (cache[polku]) return cache[polku];
  const r = await env.ASSETS.fetch(new Request(origin + polku));
  if (!r.ok) throw new Error("Aineistoa ei löytynyt: " + polku);
  return (cache[polku] = await r.json());
}

// ---------- haku ----------
async function haePykalat(env, origin, kysymys) {
  const luettelo = await data(env, origin, "/data/lait.json");
  const lista = luettelo.lait.map((l) => `${l.id} | ${l.nimi} (${l.lyh}) | ${l.aihe}`).join("\n");
  const sys = "Olet suomalaisen oikeuden asiantuntija. Tehtäväsi on valita, mistä laeista vastaus kysymykseen löytyy, ja antaa hakusanat. Vastaa vain JSON-muodossa.";
  const u = `Lakiluettelo (tunniste | nimi | aiheet):\n${lista}\n\nKysymys:\n"""${kysymys}"""\n\nPalauta JSON:\n{"lait": ["tunniste", ...] (1–4 todennäköisintä lakia luettelosta, tärkein ensin),\n "sanat": ["sanavartalo", ...] (8–16 suomenkielistä hakusanan vartaloa ilman taivutuspäätteitä, esim. "irtisano", "koeai", "vuokranantaj", "virhe", "reklam"),\n "pykalat": ["tunniste|luku|pykälä", ...] (enintään 6 pykälää, jotka tiedät varmasti olennaisiksi, esim. "1978-38|5 luku|16 §"; jätä tyhjäksi jos et ole varma),\n "aihe": "lyhyt kuvaus oikeudellisesta kysymyksestä"}`;
  let v, diag = "";
  try { const raaka = await claude(env, MALLI_HAKU, sys, u, 600); v = jsonista(raaka); if (!v) diag = "jäsennys: " + raaka.slice(0, 120); } catch (e) { v = null; diag = String(e.message || e); }
  const tunnetut = new Set(luettelo.lait.map((l) => l.id));
  const lait = ((v && v.lait) || []).filter((x) => tunnetut.has(x)).slice(0, 4);
  if (!lait.length) return { lait: [], osumat: [], aihe: "", diag };
  const sanat = ((v && v.sanat) || []).map((s) => String(s).toLowerCase().trim()).filter((s) => s.length >= 3).slice(0, 16);
  const vihjeet = new Set(((v && v.pykalat) || []).map((s) => String(s).replace(/\s+/g, " ").trim()));
  const osumat = [];
  for (const [li, id] of lait.entries()) {
    const laki = await data(env, origin, `/data/laki/${id}.json`);
    for (const p of laki.p) {
      const ots = (p.ots || "").toLowerCase(), t = (p.t || "").toLowerCase();
      let pist = 0;
      for (const s of sanat) {
        if (ots.includes(s)) pist += 4;
        let i = t.indexOf(s), n = 0;
        while (i !== -1 && n < 6) { n++; i = t.indexOf(s, i + s.length); }
        pist += Math.min(n, 4);
      }
      const luku = (p.luku.match(/^\d+\s*[a-z]?\s*luku/i) || [""])[0].replace(/\s+/g, " ");
      if (vihjeet.has(`${id}|${luku}|${p.num}`) || (!luku && [...vihjeet].some((x) => x.startsWith(id + "|") && x.endsWith("|" + p.num)))) pist += 25;
      pist *= 1 - li * 0.12;   // ensisijainen laki painavampi
      if (pist > 0) osumat.push({ pist, laki: laki.nimi, lyh: `${laki.nro}/${laki.vuosi}`, url: laki.url, ...p });
    }
  }
  osumat.sort((a, b) => b.pist - a.pist);
  // enintään 12 pykälää ja noin 22 000 merkkiä
  const valitut = []; let merkit = 0;
  for (const o of osumat) {
    if (valitut.length >= 12) break;
    const t = o.t.slice(0, 3500);
    if (merkit + t.length > 22000 && valitut.length >= 4) continue;
    valitut.push({ ...o, t }); merkit += t.length;
  }
  return { lait, osumat: valitut, aihe: (v && v.aihe) || "" };
}

function lahteet(osumat) {
  return osumat.map((o, i) => `[${i + 1}] ${o.laki} (${o.lyh}) ${o.luku ? o.luku + ", " : ""}${o.num} ${o.ots}\n${o.t}`).join("\n\n");
}
const julki = (osumat) => osumat.map((o, i) => ({ n: i + 1, laki: o.laki, lyh: o.lyh, luku: o.luku, num: o.num, ots: o.ots, url: o.url, ote: o.t.slice(0, 600) }));

const YHTEISET = `Kirjoita selkeää yleiskieltä, jota tavallinen ihminen ymmärtää. Perusta jokainen oikeudellinen väite VAIN annettuihin pykäliin ja merkitse lähde hakasulkeisiin, esim. [2]. Älä keksi pykäliä, numeroita, määräaikoja tai ennakkopäätöksiä, joita aineistossa ei ole. Jos annetut pykälät eivät riitä vastaamaan, sano se suoraan ja kerro, millaista lisätietoa tai asiantuntijaa tarvitaan. Huomaa, että sopimukset, työehtosopimukset, taloyhtiön yhtiöjärjestys ja oikeuskäytäntö voivat muuttaa lopputulosta. Muotoilu: väliotsikot rivin alussa "## ", luettelot "- ", lihavointi **näin**. Ei taulukoita.`;

async function vastaa(env, origin, kysymys) {
  const h = await haePykalat(env, origin, kysymys);
  if (!h.osumat.length) return { diag: h.diag, vastaus: "En löytänyt tähän kysymykseen sopivia säännöksiä palvelun lakiaineistosta. Palvelussa on tällä hetkellä noin 40 tavallisimmin tarvittua lakia. Kokeile muotoilla kysymys toisin tai kysy juristilta.", lahteet: [] };
  const sys = `Olet Pykälävahti, palvelu joka selittää Suomen lakia tavallisille ihmisille ajantasaisen lainsäädännön pohjalta. Et ole asianajaja etkä anna sitovaa oikeudellista neuvontaa, vaan yleistä tietoa laista. ${YHTEISET}`;
  const u = `Ajantasaiset pykälät (Finlex):\n\n${lahteet(h.osumat)}\n\n---\nKäyttäjän kysymys:\n"""${kysymys}"""\n\nVastaa rakenteella:\n## Lyhyesti\n(1–3 virkettä)\n## Mitä laki sanoo\n(selitys lähdeviittein)\n## Mitä voit tehdä\n(käytännön askeleet, määräajat jos laissa)\n## Milloin kannattaa kysyä juristilta\n(1–3 kohtaa)`;
  const t = await claude(env, MALLI_VASTAUS, sys, u, 1800);
  return { vastaus: t, lahteet: julki(h.osumat), aihe: h.aihe };
}

async function esitys(env, origin, b) {
  const kuvaus = siivoa(b.kuvaus), tavoite = siivoa(b.tavoite), ajat = siivoa(b.ajat);
  const h = await haePykalat(env, origin, `${kuvaus}\nTavoite: ${tavoite}`);
  const sys = `Olet Pykälävahti. Laadit juristille pohjaesityksen (muistion) asiakkaan tilanteesta, jotta juristi pääsee nopeasti asiaan ja asiakas säästää kuluissa. Muistio ei ole oikeudellinen neuvo, vaan juristin tarkistettava luonnos. Kirjoita asiallisesti ja tiiviisti. ${YHTEISET}`;
  const u = `Ajantasaiset pykälät (Finlex):\n\n${h.osumat.length ? lahteet(h.osumat) : "(ei osumia aineistosta)"}\n\n---\nAsiakkaan kuvaus tilanteesta:\n"""${kuvaus}"""\nMitä asiakas haluaa saavuttaa:\n"""${tavoite || "ei kerrottu"}"""\nMääräajat ja päivämäärät:\n"""${ajat || "ei kerrottu"}"""\n\nLaadi muistio rakenteella:\n## Tiivistelmä\n## Tosiseikat asiakkaan kertomana\n(luettelona; merkitse epäselvät kohdat)\n## Oikeudelliset kysymykset\n## Sovellettavat säännökset\n(lähdeviittein)\n## Alustava arvio\n(vahvuudet ja heikkoudet, varovaisesti)\n## Mahdolliset toimintavaihtoehdot\n## Määräajat ja kiireellisyys\n## Avoimet kysymykset juristille\n## Asiakirjat, jotka kannattaa ottaa mukaan`;
  const t = await claude(env, MALLI_VASTAUS, sys, u, 2600);
  return { vastaus: t, lahteet: julki(h.osumat), aihe: h.aihe };
}

// ---------- maksut (Stripe Checkout) ----------
// Maksu on käytössä vasta, kun STRIPE_SECRET_KEY on asetettu. Siihen asti pohjaesitys on ilmainen (avajaiskausi).
const HINTA_SNT = 2900;
const maksullinen = (env) => !!env.STRIPE_SECRET_KEY;
async function stripe(env, polku, data) {
  const r = await fetch("https://api.stripe.com/v1/" + polku, {
    method: data ? "POST" : "GET",
    headers: { Authorization: "Bearer " + env.STRIPE_SECRET_KEY, ...(data ? { "content-type": "application/x-www-form-urlencoded" } : {}) },
    body: data ? new URLSearchParams(data).toString() : undefined,
  });
  return r.json();
}
async function aloitaMaksu(env, origin) {
  const s = await stripe(env, "checkout/sessions", {
    mode: "payment", locale: "fi",
    "line_items[0][quantity]": "1",
    "line_items[0][price_data][currency]": "eur",
    "line_items[0][price_data][unit_amount]": String(HINTA_SNT),
    "line_items[0][price_data][product_data][name]": "Pohjaesitys juristille",
    "line_items[0][price_data][product_data][description]": "Tekoälyn laatima muistio oikeudellisesta tilanteesta pykäläviittauksineen. Toimitetaan heti.",
    success_url: origin + "/pohjaesitys/?maksu={CHECKOUT_SESSION_ID}",
    cancel_url: origin + "/pohjaesitys/?peruttu=1",
    "custom_text[submit][message]": "Pohjaesitys toimitetaan heti maksun jälkeen. Peruuttamisoikeus päättyy, kun esitys on toimitettu.",
  });
  if (!s.url) throw new Error("Maksun aloitus epäonnistui");
  return s.url;
}
async function tarkistaMaksu(env, id) {
  if (!/^cs_[A-Za-z0-9_]+$/.test(id || "")) return "Maksutunnus puuttuu.";
  const k = "maksu:" + id, n = Number((await env.DB.get(k)) || 0);
  if (n >= 3) return "Tällä maksulla on jo laadittu pohjaesitys. Ota yhteyttä, jos tarvitset apua.";
  const s = await stripe(env, "checkout/sessions/" + id);
  if (s.payment_status !== "paid") return "Maksua ei ole vahvistettu.";
  await env.DB.put(k, String(n + 1), { expirationTtl: 30 * 86400 });
  return null;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) {
      if (req.method !== "POST" && url.pathname !== "/api/tila") return json({ virhe: "Vain POST" }, 405);
      const o = req.headers.get("Origin");
      if (o && new URL(o).host !== url.host) return json({ virhe: "Kielletty" }, 403);
      let b = {}; if (req.method === "POST") { try { b = await req.json(); } catch { return json({ virhe: "Virheellinen pyyntö" }, 400); } }
      if (b.hp) return json({ virhe: "Virheellinen pyyntö" }, 400);
      try {
        if (url.pathname === "/api/kysy") {
          const k = siivoa(b.kysymys);
          if (k.length < 10) return json({ virhe: "Kirjoita kysymys vähintään yhdellä virkkeellä." }, 400);
          if (k.length > 1500) return json({ virhe: "Kysymys on liian pitkä (enintään 1500 merkkiä). Pidempää tilannetta varten käytä pohjaesitystä." }, 400);
          const raja = await rajoita(req, env); if (raja) return json({ virhe: raja }, 429);
          return json(await vastaa(env, url.origin, k));
        }
        if (url.pathname === "/api/tila") return json({ maksullinen: maksullinen(env), hinta: HINTA_SNT / 100 });
        if (url.pathname === "/api/maksu") {
          if (!maksullinen(env)) return json({ virhe: "Maksu ei ole käytössä." }, 400);
          if (b.ehdot !== true) return json({ virhe: "Hyväksy ehdot ennen maksamista." }, 400);
          return json({ url: await aloitaMaksu(env, url.origin) });
        }
        if (url.pathname === "/api/esitys") {
          if (siivoa(b.kuvaus).length < 40) return json({ virhe: "Kuvaa tilanne vähintään parilla virkkeellä." }, 400);
          if (maksullinen(env)) { const m = await tarkistaMaksu(env, b.maksu); if (m) return json({ virhe: m }, 402); }
          else { const raja = await rajoita(req, env); if (raja) return json({ virhe: raja }, 429); }
          return json(await esitys(env, url.origin, b));
        }
      } catch (e) {
        return json({ virhe: "Vastauksen muodostaminen epäonnistui. Yritä hetken kuluttua uudelleen." }, 502);
      }
      return json({ virhe: "Ei löydy" }, 404);
    }
    return env.ASSETS.fetch(req);
  },
};
