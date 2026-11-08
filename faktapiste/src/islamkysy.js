// "Kysy tekoälyltä" faktapiste.fi/islam/ -sivulla.
// POST /api/islam/kysy {kysymys, historia[]} -> NDJSON-virta: {t:"teksti",d}, {t:"haku",d}, {t:"tulos",d}, {t:"virhe",d}, {t:"loppu",...}
// Tutkii aiheen Anthropicin web_search- ja web_fetch-palvelintyökaluilla sekä omilla työkaluilla (oma arkisto R2:ssa, PRH:n YTJ-avoin data).
// Kysymyksiä ei tallenneta mihinkään: rajoja varten Durable Objectiin kirjataan vain päiväkohtainen laskuri (IP:stä suolattu tiiviste).

const MALLI = "claude-sonnet-5-5";
export const RAJAT = { ipPaiva: 15, kaikkiPaiva: 300, kysymys: 1500, historia: 8, historiaTeksti: 12000 };
const KIERROKSET = 12;

const fiPv = ms => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Helsinki" }).format(new Date(ms));
async function tiiviste(s) { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, "0")).join(""); }
export const omaKoodi = async env => env.HALLINTA ? (await tiiviste(env.HALLINTA + "-islamkysy")).slice(0, 32) : null;

function jarjestelma() {
  const tanaan = new Intl.DateTimeFormat("fi-FI", { timeZone: "Europe/Helsinki", day: "numeric", month: "numeric", year: "numeric" }).format(new Date());
  return `Olet Faktapisteen tutkimusavustaja (faktapiste.fi/islam/). Tehtäväsi on selvittää perusteellisesti mitä tahansa islamiin liittyvää: islam ja muslimit Suomessa, Euroopassa ja maailmassa, uskonto ja oppi, historia, järjestöt, moskeijat, väestö, politiikka, turvallisuus, lainsäädäntö, rahoitus ja ajankohtaiset uutiset. Tänään on ${tanaan}.

TYÖTAPA – tutki kuin huolellinen toimittaja tai tutkija:
1. Pilko kysymys osiin ja mieti, mistä kukin luku tai tieto löytyy luotettavimmin (ensisijaiset lähteet ensin).
2. Tee useita hakuja eri sanamuodoilla, suomeksi, ruotsiksi ja englanniksi tarvittaessa. Avaa web_fetch-työkalulla tärkeimmät sivut (rekisterit, tilastot, viranomaisten ja kuntien päätökset, tutkimukset, luettelot) äläkä tyydy hakutulosten katkelmiin, kun tarvitset tarkan luvun.
3. Käytä työkalua hae_arkistosta Faktapisteen omaan uutis- ja viranomaisarkistoon (n. 5 600 juttua, Suomi ja Eurooppa): se löytää esim. kuntien kaava- ja lupapäätöksiä, moskeijahankkeita ja paikallisuutisia. Käytä sanojen alkuosia (esim. "moskei", "rukoushuo", "islamilai").
4. Käytä työkalua hae_ytj, kun kysytään suomalaisista yhdistyksistä, säätiöistä, uskonnollisista yhdyskunnista tai yrityksistä: se hakee PRH:n YTJ-avoimesta datasta nimellä (tulos kattaa vain ne, joilla on Y-tunnus). Tee useita nimihakuja (esim. islam, islamilainen, islamic, muslim, moskeija, masjid, al-, imaami, ummah, somali, tataari) ja laske tulokset itse. Kerro selvästi, että tämä ei ole täydellinen luettelo.
5. Ristiintarkista luvut useasta lähteestä. Jos lähteet eroavat, kerro kaikki luvut, niiden päivämäärät ja syy eroon.
6. Jatka tutkimista, kunnes kysymykseen on kunnollinen vastaus tai olet todennut, ettei tietoa ole julkisesti saatavilla. Älä kirjoita mitään väliaikaista tekstiä hakujen välissä: kirjoita vastaus vasta, kun tutkimus on valmis.

TÄRKEITÄ LÄHTEITÄ (Suomi):
- PRH: yhdistysrekisteri, säätiörekisteri, YTJ (ytj.fi) ja uskonnollisten yhdyskuntien rekisteri. Rekisteröityjen islamilaisten yhdyskuntien määrä löytyy usein myös Uskonnot Suomessa -palvelusta (uskonnot.fi), opetus- ja kulttuuriministeriön yhdyskuntien valtionavustuspäätöksistä sekä tutkimuksista (esim. Tuomas Martikaisen, Teemu Pauhan ja Linda Hyökin julkaisut, Yearbook of Muslims in Europe -vuosikirjan Suomi-luku).
- Tilastokeskus (StatFin: väestö uskonnollisen yhdyskunnan mukaan), Opetushallitus (islamin opetus), Supo (katsaukset), Finlex (uskonnonvapauslaki), eduskunta (kysymykset ja aloitteet).
- Kuntien päätökset ja kaavoitus: esim. Helsingin päätökset (paatokset.hel.fi), Espoo, Vantaa, Turku, Tampere, Oulu; asemakaava- ja rakennuslupapäätökset; Lupapiste.
- Uutiset: Yle, HS, MTV, IL, IS, Kotimaa, STT, paikallislehdet. Muissa maissa vastaavat viranomaiset, tilastovirastot, tutkimuslaitokset (esim. Pew Research Center) ja suuret mediat.

MÄÄRITELMÄT, jotka pitää kertoa vastauksessa aina kun ne vaikuttavat lukuihin:
- Moskeija tarkoittaa Suomessa usein vuokrattua rukoushuonetta (liiketila, toimisto, asunto). Erottele: (a) moskeijaksi rakennetut tai kokonaan moskeijaksi muutetut rakennukset, (b) rukoushuoneet ja moskeijat vuokratiloissa, (c) rakenteilla olevat ja (d) suunnitteilla olevat hankkeet (kaavamuutos, rakennuslupa, tontinvaraus, rahoitus haettu) sekä (e) kaatuneet tai keskeytyneet hankkeet. Kerro kustakin paikkakunta, toimija, vaihe ja päivämäärä.
- Yhdistys (ry), säätiö (sr), rekisteröity uskonnollinen yhdyskunta ja rekisteröimätön yhteisö ovat eri asioita. Kerro, mitä kukin luku kattaa ja mihin päivään se on laskettu.
- Erota rekisteröityjen jäsenten määrä muslimitaustaisten arvioidusta määrästä.

VASTAUS:
- Kirjoita suomeksi, selkeästi ja asiallisesti. Aloita lyhyellä suoralla vastauksella (keskeiset luvut lihavoituna), sitten perustelut ja erittelyt väliotsikoin (##), luetteloin tai taulukoin.
- Anna jokaiselle luvulle päivämäärä tai vuosi ja lähde. Kerro epävarmuus ja määritelmät. Älä koskaan keksi lukuja, nimiä tai lähteitä. Jos tietoa ei löytynyt, sano se suoraan ja kerro, mistä sen voi selvittää (esim. mille viranomaiselle voi tehdä tietopyynnön).
- Pysy neutraalina ja faktapohjaisena: kerro, mitä lähteet sanovat, älä ota poliittista kantaa. Kiistanalaisissa asioissa esitä eri osapuolten näkemykset lähteineen.
- Lopeta osioon "## Lähteet": numeroitu luettelo markdown-linkkeinä muodossa [Sivun nimi – julkaisija, pvm](https://osoite). Käytä vain osoitteita, jotka oikeasti löysit tutkimuksen aikana.
- Jatkokysymyksissä hyödynnä aiempaa keskustelua, mutta tee tarvittaessa uusia hakuja.`;
}

const TYOKALUT = [
  { type: "web_search_20260209", name: "web_search", max_uses: 15 },
  { type: "web_fetch_20260209", name: "web_fetch", max_uses: 12, max_content_tokens: 30000 },
  {
    name: "hae_arkistosta",
    description: "Hakee Faktapisteen omasta islam-uutisarkistosta (n. 5 600 uutista sekä viranomais-, kunta- ja yhteisötiedotetta Suomesta ja Euroopasta; ulkomaiset otsikot käännetty suomeksi). Haku osuu otsikkoon, alkuperäiseen otsikkoon, tiivistelmään ja lähteen nimeen. Palauttaa osuvimmat jutut uusimmasta alkaen otsikon, päivämäärän, lähteen ja linkin kanssa.",
    input_schema: {
      type: "object",
      properties: {
        sanat: { type: "array", items: { type: "string" }, description: "Hakusanat tai sanojen alkuosat, esim. [\"moskei\", \"Turku\"]. Jutun pitää sisältää vähintään yksi; useampi osuma nostaa sijoitusta." },
        kaikki: { type: "boolean", description: "true = jutun pitää sisältää kaikki sanat" },
        maa: { type: "string", description: "Maakoodi: fi, se, no, dk, de, fr, nl, be, at, uk, eu" },
        luokka: { type: "string", enum: ["media", "viranomainen", "kunta", "yhteiso"] },
        alkaen: { type: "string", description: "Päivämäärä YYYY-MM-DD" },
        asti: { type: "string", description: "Päivämäärä YYYY-MM-DD" },
        maara: { type: "integer", description: "Tulosten enimmäismäärä (oletus 25, enintään 60)" },
      },
      required: ["sanat"],
    },
  },
  {
    name: "hae_ytj",
    description: "Hakee Patentti- ja rekisterihallituksen YTJ-avoimesta datasta (avoindata.prh.fi) suomalaisia yhteisöjä nimen osalla: yhdistykset, säätiöt, uskonnolliset yhdyskunnat, yritykset. Palauttaa Y-tunnuksen, nimen, yhteisömuodon, rekisteröintipäivän, kotipaikan, toimialan ja tilan. Kattaa vain yhteisöt, joilla on Y-tunnus (moni pieni yhdistys puuttuu).",
    input_schema: {
      type: "object",
      properties: {
        nimet: { type: "array", items: { type: "string" }, description: "Yksi tai useampi nimihaku, esim. [\"islamilainen\", \"islamic\", \"muslim\"]" },
        vain_aktiiviset: { type: "boolean", description: "true = jätä lakanneet pois (oletus false: lakanneet merkitään)" },
      },
      required: ["nimet"],
    },
  },
];

// Arkisto pidetään muistissa 10 min (sama isolaatti palvelee useita kysymyksiä).
let ARKISTO = null, ARKISTO_T = 0;
async function arkisto(env) {
  if (ARKISTO && Date.now() - ARKISTO_T < 600e3) return ARKISTO;
  const o = env.VIDEOT ? await env.VIDEOT.get("julkinen/islam.json") : null;
  if (!o) return [];
  const d = await o.json();
  ARKISTO = (d.jutut || []).map(x => ({ x, h: (x.o + " " + (x.oo || "") + " " + (x.k || "") + " " + x.l).toLowerCase() }));
  ARKISTO_T = Date.now();
  return ARKISTO;
}
async function haeArkistosta(env, a) {
  const sanat = (Array.isArray(a.sanat) ? a.sanat : [String(a.sanat || "")]).map(s => String(s).toLowerCase().trim()).filter(Boolean).slice(0, 12);
  if (!sanat.length) return { virhe: "anna hakusanat" };
  const max = Math.min(60, Math.max(1, +a.maara || 25));
  const tulos = [];
  for (const { x, h } of await arkisto(env)) {
    if (a.luokka && x.c !== a.luokka) continue;
    if (a.maa) { const m = x.a === "eu" ? (x.m || "eu") : "fi"; if (m !== a.maa) continue; }
    const pv = (x.t || "").slice(0, 10);
    if (a.alkaen && pv < a.alkaen) continue;
    if (a.asti && pv > a.asti) continue;
    let p = 0; for (const s of sanat) if (h.includes(s)) p++;
    if (!p || (a.kaikki && p < sanat.length)) continue;
    tulos.push([p, x]);
  }
  tulos.sort((A, B) => B[0] - A[0] || (B[1].t > A[1].t ? 1 : -1));
  return {
    osumia: tulos.length,
    jutut: tulos.slice(0, max).map(([, x]) => ({ pvm: (x.t || "").slice(0, 10), otsikko: x.o, alkuperainen: x.oo || undefined, tiivistelma: x.k || undefined, lahde: x.l, maa: x.a === "eu" ? (x.m || "eu") : "fi", luokka: x.c, url: x.u })),
  };
}

async function haeYtj(a) {
  const nimet = (Array.isArray(a.nimet) ? a.nimet : [String(a.nimet || "")]).map(s => String(s).trim()).filter(Boolean).slice(0, 10);
  const nahty = new Map(), haut = {};
  await Promise.all(nimet.map(async n => {
    try {
      const r = await fetch("https://avoindata.prh.fi/opendata-ytj-api/v3/companies?name=" + encodeURIComponent(n), { headers: { accept: "application/json" } });
      if (!r.ok) { haut[n] = "virhe " + r.status; return; }
      const d = await r.json(); haut[n] = d.totalResults ?? (d.companies || []).length;
      for (const c of d.companies || []) {
        const id = c.businessId?.value; if (!id || nahty.has(id)) continue;
        const fi = arr => ((arr || []).find(x => x.languageCode === "1") || {}).description;
        const nimi = ((c.names || []).find(x => !x.endDate) || (c.names || [])[0] || {}).name;
        const muoto = fi(((c.companyForms || []).find(x => !x.endDate) || (c.companyForms || [])[0] || {}).descriptions);
        const os = (c.addresses || [])[0] || {};
        const kunta = ((os.postOffices || []).find(x => x.languageCode === "1") || (os.postOffices || [])[0] || {}).city;
        nahty.set(id, { ytunnus: id, nimi, muoto, rekisteroity: c.businessId?.registrationDate || c.registrationDate, kotipaikka: kunta, toimiala: fi(c.mainBusinessLine?.descriptions), paattynyt: c.endDate || undefined });
      }
    } catch (e) { haut[n] = "virhe"; }
  }));
  let lista = [...nahty.values()];
  if (a.vain_aktiiviset) lista = lista.filter(x => !x.paattynyt);
  return { haut, yhteensa: lista.length, huom: "Vain Y-tunnuksen saaneet yhteisöt. Nimihaku osuu myös sanan keskelle, joten karsi epäolennaiset (esim. asunto-osakeyhtiöt).", yhteisot: lista.slice(0, 150) };
}

// Anthropicin SSE-virran luku: palauttaa sisältölohkot ja pysähtymissyyn, välittää tekstin ja edistymisen asiakkaalle.
async function kierros(env, body, laheta) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ ...body, stream: true }),
  });
  if (!r.ok || !r.body) { const t = await r.text().catch(() => ""); throw new Error("API " + r.status + " " + t.slice(0, 300)); }
  const lohkot = [], json = {}; let syy = null, kaytto = {};
  const rd = r.body.pipeThrough(new TextDecoderStream()).getReader(); let pus = "";
  for (;;) {
    const { value, done } = await rd.read(); if (done) break;
    pus += value; let i;
    while ((i = pus.indexOf("\n\n")) >= 0) {
      const ev = pus.slice(0, i); pus = pus.slice(i + 2);
      const dl = ev.split("\n").filter(l => l.startsWith("data:")).map(l => l.slice(5).trim()).join("");
      if (!dl) continue; let e; try { e = JSON.parse(dl); } catch { continue; }
      if (e.type === "message_start") kaytto = { ...e.message?.usage };
      else if (e.type === "content_block_start") {
        const b = { ...e.content_block }; lohkot[e.index] = b;
        if (b.type === "server_tool_use" || b.type === "tool_use") json[e.index] = "";
        if (b.type === "text" && b.citations === undefined) delete b.citations;
        if (b.type === "web_search_tool_result") { const n = Array.isArray(b.content) ? b.content.length : 0; laheta({ t: "tulos", d: n ? n + " hakutulosta" : "ei tuloksia" }); }
        if (b.type === "web_fetch_tool_result") { const ok = b.content?.type === "web_fetch_result"; laheta({ t: "tulos", d: ok ? "sivu luettu" : "sivua ei saatu auki" }); }
      } else if (e.type === "content_block_delta") {
        const b = lohkot[e.index], d = e.delta;
        if (d.type === "text_delta") { b.text = (b.text || "") + d.text; laheta({ t: "teksti", d: d.text }); }
        else if (d.type === "input_json_delta") json[e.index] += d.partial_json;
        else if (d.type === "citations_delta") (b.citations ||= []).push(d.citation);
        else if (d.type === "thinking_delta") b.thinking = (b.thinking || "") + d.thinking;
        else if (d.type === "signature_delta") b.signature = d.signature;
      } else if (e.type === "content_block_stop") {
        const b = lohkot[e.index];
        if (e.index in json) {
          try { b.input = json[e.index] ? JSON.parse(json[e.index]) : {}; } catch { b.input = {}; }
          const inp = b.input || {};
          if (b.name === "web_search") laheta({ t: "haku", d: "Haen verkosta: " + (inp.query || "") });
          else if (b.name === "web_fetch") laheta({ t: "haku", d: "Luen sivua: " + (inp.url || "").replace(/^https?:\/\/(www\.)?/, "").slice(0, 80) });
          else if (b.name === "hae_arkistosta") laheta({ t: "haku", d: "Haen Faktapisteen arkistosta: " + (inp.sanat || []).join(", ") });
          else if (b.name === "hae_ytj") laheta({ t: "haku", d: "Haen PRH:n YTJ-rekisteristä: " + (inp.nimet || []).join(", ") });
          else if (b.type === "server_tool_use") laheta({ t: "haku", d: "Käsittelen hakutuloksia" });
        }
      } else if (e.type === "message_delta") { syy = e.delta?.stop_reason || syy; if (e.usage) kaytto = { ...kaytto, ...e.usage }; }
      else if (e.type === "error") throw new Error(e.error?.message || "virhe");
    }
  }
  return { lohkot: lohkot.filter(Boolean), syy, kaytto };
}

export async function islamKysy(req, env, ctx) {
  const vastaa = (d, s) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
  if (req.method !== "POST") return vastaa({ virhe: "POST" }, 405);
  if (!env.ANTHROPIC_API_KEY) return vastaa({ virhe: "Tekoäly ei ole käytössä." }, 503);
  let d; try { d = await req.json(); } catch { return vastaa({ virhe: "Virheellinen pyyntö." }, 400); }
  const kysymys = String(d.kysymys || "").trim();
  if (!kysymys) return vastaa({ virhe: "Kirjoita kysymys." }, 400);
  if (kysymys.length > RAJAT.kysymys) return vastaa({ virhe: `Kysymys on liian pitkä (enintään ${RAJAT.kysymys} merkkiä).` }, 400);

  // Rajat: IP:stä vain suolattu tiiviste, ei kysymyksen tekstiä.
  const oma = await omaKoodi(env), onOma = !!oma && req.headers.get("x-oma") === oma;
  const ip = (await tiiviste((req.headers.get("cf-connecting-ip") || "?") + "|islamkysy|" + (env.HALLINTA || ""))).slice(0, 24);
  const rr = await env.FP.get(env.FP.idFromName("main")).fetch(new Request("https://sisainen/_islamraja", { method: "POST", body: JSON.stringify({ ip, pv: fiPv(Date.now()), oma: onOma }) }));
  const raja = await rr.json();
  if (!raja.ok) return vastaa({ virhe: raja.syy === "kaikki"
    ? "Tekoälyavustajan päivittäinen kokonaiskiintiö on käytetty. Palvelu avautuu taas huomenna. Kiitos kärsivällisyydestä!"
    : `Olet esittänyt tänään jo ${RAJAT.ipPaiva} kysymystä, mikä on päivittäinen enimmäismäärä. Voit jatkaa huomenna.`, raja: true }, 429);

  // Historia: vuorottelevat user/assistant-viestit, vain tekstit.
  const msgs = [];
  for (const h of (Array.isArray(d.historia) ? d.historia : []).slice(-RAJAT.historia)) {
    const rooli = h.rooli === "assistant" ? "assistant" : "user", teksti = String(h.teksti || "").slice(0, RAJAT.historiaTeksti).trim();
    if (!teksti) continue;
    if (msgs.length && msgs[msgs.length - 1].role === rooli) msgs[msgs.length - 1].content += "\n\n" + teksti;
    else msgs.push({ role: rooli, content: teksti });
  }
  while (msgs.length && msgs[0].role !== "user") msgs.shift();
  if (msgs.length && msgs[msgs.length - 1].role === "user") msgs.pop();
  msgs.push({ role: "user", content: kysymys });

  const { readable, writable } = new TransformStream();
  const w = writable.getWriter(), enc = new TextEncoder();
  let auki = true;
  const laheta = o => { if (!auki) return; w.write(enc.encode(JSON.stringify(o) + "\n")).catch(() => { auki = false; }); };
  const tyo = (async () => {
    const alku = Date.now(), yht = { input_tokens: 0, output_tokens: 0, haut: 0, sivut: 0, omat: 0 };
    try {
      laheta({ t: "haku", d: "Aloitan tutkimuksen", jaljella: raja.jaljella });
      const body = { model: MALLI, max_tokens: 12000, system: [{ type: "text", text: jarjestelma(), cache_control: { type: "ephemeral" } }], tools: TYOKALUT, messages: msgs };
      for (let k = 0; k < KIERROKSET && auki; k++) {
        const { lohkot, syy, kaytto } = await kierros(env, body, laheta);
        yht.input_tokens += (kaytto.input_tokens || 0) + (kaytto.cache_read_input_tokens || 0) + (kaytto.cache_creation_input_tokens || 0); yht.output_tokens += kaytto.output_tokens || 0;
        const st = kaytto.server_tool_use || {}; yht.haut += st.web_search_requests || 0; yht.sivut += st.web_fetch_requests || 0;
        body.messages = [...body.messages, { role: "assistant", content: lohkot }];
        if (syy === "pause_turn") continue;
        if (syy !== "tool_use") break;
        const tulokset = [];
        for (const b of lohkot) {
          if (b.type !== "tool_use") continue;
          yht.omat++;
          let out; try { out = b.name === "hae_arkistosta" ? await haeArkistosta(env, b.input || {}) : b.name === "hae_ytj" ? await haeYtj(b.input || {}) : { virhe: "tuntematon työkalu" }; } catch (e) { out = { virhe: String(e.message || e) }; }
          if (out.osumia !== undefined) laheta({ t: "tulos", d: out.osumia + " osumaa arkistossa" });
          if (out.yhteensa !== undefined) laheta({ t: "tulos", d: out.yhteensa + " yhteisöä YTJ:ssä" });
          tulokset.push({ type: "tool_result", tool_use_id: b.id, content: JSON.stringify(out).slice(0, 60000) });
        }
        body.messages.push({ role: "user", content: tulokset });
        laheta({ t: "kierros" });
      }
      laheta({ t: "loppu", sek: Math.round((Date.now() - alku) / 1000), kaytto: yht });
    } catch (e) {
      laheta({ t: "virhe", d: "Tutkimus keskeytyi virheeseen. Yritä hetken päästä uudelleen." });
      console.log("islamkysy virhe", String(e.message || e).slice(0, 300));
    }
    try { await w.close(); } catch {}
  })();
  ctx.waitUntil(tyo);
  return new Response(readable, { headers: { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff", "x-accel-buffering": "no" } });
}
