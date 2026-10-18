// Päivittäiset uutisluonnokset alkuperäislähteistä Suomi Tänään -toimitukselle.
// 1) Hakee lähteet: Eduskuntaseurannan äänestykset ja viranomaistiedotteet (eduskuntaseuranta.fi/data/halytyslahteet.json)
// 2) Painottaa aiheita, joista mediat juuri nyt puhuvat (nytpuhutaan.fi/feed.json)
// 3) Lukee jokaisen lähteen alkuperäisen sivun ja pyytää Claudea kirjoittamaan luonnoksen PELKÄSTÄÄN lähteen perusteella
// 4) Lähettää luonnokset toimituksen hyväksyntäjonoon (Worker /api/luonnokset). Mitään ei julkaista ilman hyväksyntää.
const WORKER = (process.env.WORKER_URL || "").replace(/\/$/, "");
const PW = process.env.TOIMITUS_SALASANA || "";
const KEY = process.env.ANTHROPIC_API_KEY || "";
const MALLI = process.env.MALLI || "claude-sonnet-5-5";
const MAX = Number(process.env.MAX_LUONNOKSET || 10);
const KATEGORIAT = ["Politiikka", "Talous", "Kotimaa", "Kunnat", "Urheilu", "Kulttuuri", "Elämä", "Ulkomaat", "Hankinnat"];
const UA = "Mozilla/5.0 (compatible; SuomiTanaan/1.0; +https://suomitanaan.fi)";

const huomio = (otsikko, viesti) => console.log(`::notice title=${otsikko}::${String(viesti).replace(/\n/g, " ").slice(0, 400)}`);

async function haeJson(url) { const r = await fetch(url, { headers: { "user-agent": UA } }); if (!r.ok) throw new Error(url + " " + r.status); return r.json(); }

async function haeTeksti(url) {
  const ctl = new AbortController(); const to = setTimeout(() => ctl.abort(), 20000);
  try {
    const r = await fetch(url, { headers: { "user-agent": UA, accept: "text/html,*/*" }, signal: ctl.signal });
    if (!r.ok) throw new Error("HTTP " + r.status);
    let h = await r.text();
    h = h.replace(/<(script|style|nav|header|footer|noscript|svg)[\s\S]*?<\/\1>/gi, " ");
    const main = h.match(/<(main|article)[\s\S]*?<\/\1>/i); if (main) h = main[0];
    return h.replace(/<br\s*\/?>|<\/(p|div|li|h\d|tr)>/gi, "\n").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;|&rsquo;/g, "'")
      .replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n").trim().slice(0, 9000);
  } finally { clearTimeout(to); }
}

const STOP = new Set("joka jotka mutta myös kuten koska sekä tämä tämän nämä niiden heidän olla ollut ovat oli olivat ensi viime vuoden vuonna kertoo kertoi mukaan uusi uuden suomen suomi tänään eilen huomenna tiedote tiedotteet".split(" "));
const vartalot = t => String(t).toLowerCase().replace(/[^a-zåäö0-9 ]/g, " ").split(/\s+/).filter(w => w.length >= 5 && !STOP.has(w)).map(w => w.slice(0, 5));

async function kuumat() {
  try {
    const f = await haeJson("https://nytpuhutaan.fi/feed.json");
    const raja = Date.now() - 24 * 3600e3, c = new Map();
    for (const u of f.u || []) { if (!u.a || new Date(u.a).getTime() < raja) continue; for (const v of new Set(vartalot(u.o))) c.set(v, (c.get(v) || 0) + 1); }
    return new Map([...c].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).slice(0, 150));
  } catch (e) { console.log("Nytpuhutaan ohitettu:", e.message); return new Map(); }
}

const OHJE = `Olet Suomi Tänään -uutissivuston uutistoimittaja. Kirjoitat uutisen suomeksi YKSINOMAAN annetun alkuperäislähteen perusteella.
Säännöt:
- Käytä vain lähteessä olevia tietoja. Älä lisää mitään omasta tiedostasi, älä arvaa lukuja, nimiä, päivämääriä tai syitä.
- Neutraali, asiallinen uutiskieli. Ei kannanottoja, ei arvottavia adjektiiveja, ei klikkiotsikoita.
- Kerro aina, kuka sanoo tai päättää mitä ("ministeriön mukaan", "eduskunta hyväksyi"). Väite ja tosiasia pidetään erillään.
- Jos lähde on yksipuolinen (esim. järjestön tai yrityksen tiedote), kerro selvästi, että kyse on sen omasta näkemyksestä.
- Äänestyksistä: kerro mitä päätettiin, äänet (jaa/ei/tyhjä/poissa jos lähteessä) ja puolueiden kannat jos ne ovat lähteessä.
- Pituus 120–280 sanaa. Otsikko enintään 90 merkkiä, ingressi yksi tai kaksi virkettä.
- Osastot: Politiikka (eduskunta, hallitus, puolueet, poliittiset päätökset), Talous, Kotimaa, Kunnat, Urheilu (tulokset, ottelut, siirrot, kisat), Kulttuuri (taide, musiikki, teatteri, elokuvat, kirjat, palkinnot), Elämä (terveys, ruoka, asuminen, liikenne, matkailu, arjen palvelut), Ulkomaat, Hankinnat.
- Urheilussa kerro tulos, tärkeimmät tapahtumat ja mitä se tarkoittaa sarjatilanteelle, jos lähde kertoo sen. Kulttuurissa ja Elämässä kerro lukijalle hyödyllinen ydin.
- Aseta "hylkaa": true, jos lähde on yrityksen tuote- tai markkinointitiedote, mainos, rekrytointi, pelkkä tapahtumailmoitus tai rutiinitiedote ilman uutta tietoa.
Lisäksi kirjoita TikTok-käsikirjoitus (noin 30 sekuntia, 60–80 sanaa): vahva koukku ensimmäiseen lauseeseen, suora ja iskevä kieli, nimeä päättäjät jos ne ovat lähteessä, faktat tarkasti lähteen mukaan, loppuun "Koko juttu ja lähteet: linkki biossa."
Vastaa PELKÄLLÄ JSON-oliolla, ei muuta tekstiä:
{"hylkaa":false,"syy":"","otsikko":"","ingressi":"","teksti":"kappale 1\\n\\nkappale 2","kategoria":"${KATEGORIAT.join("|")}","tarkistettavat":["väite tai luku, joka toimittajan kannattaa tarkistaa lähteestä"],"tiktok":{"koukku":"","teksti":"","sivusto":"Suomi Tänään"}}`;

async function claude(system, user, maxTokens = 2500) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: MALLI, max_tokens: maxTokens, system, messages: [{ role: "user", content: user }] }),
  });
  if (!r.ok) throw new Error("Claude " + r.status + " " + (await r.text()).slice(0, 200));
  const t = ((await r.json()).content || []).map(c => c.text || "").join("");
  return JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1));
}

const TARKISTUS = `Olet uutistoimituksen faktantarkistaja. Saat alkuperäislähteen ja siitä kirjoitetun jutun.
Käy läpi JOKAINEN jutun väite: luvut, nimet, päivämäärät, tulokset, lainaukset, syy-seuraussuhteet ja tittelit.
Väite on kunnossa vain, jos se löytyy lähteestä tai seuraa siitä suoraan. Kaikki muu on virhe, myös lähteen ulkopuolinen taustatieto.
Vastaa PELKÄLLÄ JSON-oliolla: {"ok":true|false,"virheet":["väite ja miksi se ei ole lähteessä"]}`;

async function tarkista(lahdeTeksti, j) {
  const juttu = `OTSIKKO: ${j.otsikko}\nINGRESSI: ${j.ingressi}\nTEKSTI:\n${j.teksti}`;
  try { return await claude(TARKISTUS, `ALKUPERÄISLÄHDE:\n${lahdeTeksti}\n\nJUTTU:\n${juttu}`, 1200); }
  catch (e) { return { ok: false, virheet: ["Tarkistus epäonnistui: " + e.message] }; }
}

async function kirjoita(ehdokas, teksti) {
  const sisalto = `Lähteen tyyppi: ${ehdokas.tyyppi}\nLähde: ${ehdokas.lahde}\nOsoite: ${ehdokas.url}\nPäivämäärä: ${ehdokas.aika || "ei tiedossa"}\nOtsikko: ${ehdokas.otsikko}\n${ehdokas.lisa || ""}\n\nLähteen sisältö:\n${teksti}`;
  const j = await claude(OHJE, sisalto);
  if (!KATEGORIAT.includes(j.kategoria)) j.kategoria = ehdokas.oletusKategoria || "Kotimaa";
  return j;
}

async function main() {
  if (!WORKER || !PW || !KEY) { huomio("Puuttuu", "WORKER_URL, TOIMITUS_SALASANA tai ANTHROPIC_API_KEY puuttuu"); process.exit(1); }
  const nahdyt = new Set(await (await fetch(WORKER + "/api/nahdyt", { headers: { authorization: "Bearer " + PW } })).json().catch(() => []));
  const lahteet = await haeJson("https://eduskuntaseuranta.fi/data/halytyslahteet.json");
  const kuuma = await kuumat();
  const pisteet = o => vartalot(o).reduce((s, v) => s + (kuuma.get(v) || 0), 0);
  const tuore = (iso, h) => iso && Date.now() - new Date(iso).getTime() < h * 3600e3;

  const aanestykset = (lahteet.aanestykset || []).filter(v => tuore(v.aika, 96) && !nahdyt.has(v.url))
    .map(v => ({ tyyppi: "Eduskunnan täysistunnon äänestys", lahde: "Eduskuntaseuranta.fi (eduskunnan avoin data)", url: v.url, otsikko: v.otsikko, aika: v.aika, oletusKategoria: "Politiikka",
      lisa: `Aihe: ${v.aiheNimi || ""}\nÄänet: jaa ${v.jaa ?? "?"}, ei ${v.ei ?? "?"}`, p: 50 + pisteet(v.otsikko) }));
  const JULKINEN = /ministeri|valtioneuvosto|eduskun|virasto|kela|poliisi|puolue|kunta|kaupun|hyvinvointialue|tilastokeskus|verohallinto|traficom|thl|tuomioistu|syyttäj|puolustusvoim|rajavartio|suojelupoliisi|presidentti/i;
  const URHEILU = /liiga|sarja|ottelu|mestaruu|olympi|paralymp|MM-|EM-|maajoukku|huuhkaj|leijon|susijen|pelaaja|valmentaja|joukkue|voitti|kisat|cup\b|turnau|urheilu|hiihto|jalkapallo|jääkiekko|salibandy|koripallo|lentopallo|yleisurheilu|ravi/i;
  const KULTTUURI = /teatteri|ooppera|baletti|museo|näyttely|festivaali|konsertti|elokuva|kirja|kirjailija|palkinto|taide|taitelij|taiteilij|musiikki|orkesteri|kulttuuri|ensi-ilta|esitys/i;
  const ELAMA = /terveys|ruoka|ravitsem|asumi|asunto|hyvinvoin|liikunta|perhe|lapsi|lemmik|matkail|liikenne|sää|energia|sähkö|kuluttaja|hinta|eläke|kela/i;
  const tied = (lahteet.tiedotteet || []).filter(t => tuore(t.aika, 40) && !nahdyt.has(t.url));
  const tee = (t, tyyppi, kat, p) => ({ tyyppi, lahde: t.lahde, url: t.url, otsikko: t.otsikko, aika: t.aika, oletusKategoria: kat, p });
  const viranomaiset = tied.filter(t => t.ryhma === "Valtio ja virastot" || t.ryhma === "Kunnat" || (t.lahde === "STT Info: tiedotteet" && JULKINEN.test(t.otsikko)))
    .map(t => tee(t, "Viranomaisen tai organisaation tiedote", t.ryhma === "Kunnat" ? "Kunnat" : "Kotimaa", pisteet(t.otsikko) + (t.ryhma === "Valtio ja virastot" ? 5 : 0)));
  const stt = tied.filter(t => t.lahde === "STT Info: tiedotteet" && !JULKINEN.test(t.otsikko));
  const urheilu = stt.filter(t => URHEILU.test(t.otsikko)).map(t => tee(t, "Urheilusarjan, -liiton tai -seuran tiedote", "Urheilu", 10 + pisteet(t.otsikko)));
  const kulttuuri = stt.filter(t => !URHEILU.test(t.otsikko) && KULTTUURI.test(t.otsikko)).map(t => tee(t, "Kulttuurilaitoksen tai -toimijan tiedote", "Kulttuuri", 5 + pisteet(t.otsikko)));
  const elama = stt.filter(t => !URHEILU.test(t.otsikko) && !KULTTUURI.test(t.otsikko) && ELAMA.test(t.otsikko)).map(t => tee(t, "Organisaation tiedote", "Elämä", pisteet(t.otsikko)));
  const jarj = l => l.sort((a, b) => b.p - a.p);
  // Kiintiöt: politiikka toimittajalle, muut osastot automaattisesti
  const KIINTIO = { politiikka: MAX, muut: Number(process.env.MAX_AUTO || 10) };
  const valitut = [...jarj(aanestykset).slice(0, 6), ...jarj(viranomaiset).slice(0, 10), ...jarj(urheilu).slice(0, 6), ...jarj(kulttuuri).slice(0, 3), ...jarj(elama).slice(0, 3)];
  let nPol = 0, nAuto = 0;
  const valmiit = [];
  for (const e of valitut) {
    if (nPol >= KIINTIO.politiikka && nAuto >= KIINTIO.muut) break;
    try {
      const teksti = await haeTeksti(e.url);
      if (teksti.length < 200) { console.log("Liian lyhyt lähde:", e.url); continue; }
      const j = await kirjoita(e, teksti);
      if (j.hylkaa) { console.log("Hylätty:", e.otsikko, j.syy); valmiit.hylatyt = [...(valmiit.hylatyt || []), { vain_nahty: true, lahde_url: e.url }]; continue; }
      // Politiikka (ja kaikki äänestykset) toimittajan hyväksyttäväksi, muut osastot julkaistaan automaattisesti tekoälymerkinnällä
      const politiikka = j.kategoria === "Politiikka" || e.tyyppi.startsWith("Eduskunnan");
      if (politiikka) { if (nPol >= KIINTIO.politiikka) continue; nPol++; j.kategoria = "Politiikka"; }
      else { if (nAuto >= KIINTIO.muut) continue; nAuto++; }
      let automaattinen = !politiikka;
      if (automaattinen) {
        const t = await tarkista(teksti, j);
        if (!t.ok) { automaattinen = false; j.tarkistettavat = [...(t.virheet || []).map(v => "Faktantarkistus: " + v), ...(j.tarkistettavat || [])]; console.log("Ei läpäissyt tarkistusta, toimitukseen:", j.otsikko); nAuto--; nPol++; }
      }
      valmiit.push({ ...j, automaattinen, lahde_url: e.url, lahdetyyppi: e.tyyppi, lahteet: [{ nimi: `${e.lahde}: ${e.otsikko}`.slice(0, 200), url: e.url }] });
      console.log(politiikka ? "Toimitukseen:" : "Automaattisesti:", j.kategoria, j.otsikko);
    } catch (err) { console.log("Epäonnistui:", e.url, err.message); }
  }
  if (valmiit.length || valmiit.hylatyt) {
    const r = await fetch(WORKER + "/api/luonnokset", { method: "POST", headers: { authorization: "Bearer " + PW, "content-type": "application/json" }, body: JSON.stringify([...valmiit, ...(valmiit.hylatyt || [])]) });
    huomio("Luonnokset", `${nPol} politiikan luonnosta toimitukseen, ${nAuto} juttua julkaistu automaattisesti (${r.status}). Ehdokkaat: ${aanestykset.length} äänestystä, ${viranomaiset.length} viranomaista, ${urheilu.length} urheilua, ${kulttuuri.length} kulttuuria, ${elama.length} elämää.`);
  } else huomio("Luonnokset", `Ei uusia juttuja. Ehdokkaat: ${aanestykset.length} äänestystä, ${viranomaiset.length} viranomaista, ${urheilu.length} urheilua, ${kulttuuri.length} kulttuuria, ${elama.length} elämää.`);
}
main().catch(e => { huomio("Virhe", e.message); process.exit(1); });
