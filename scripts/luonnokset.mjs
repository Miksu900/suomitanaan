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
const KATEGORIAT = ["Politiikka", "Talous", "Kotimaa", "Kunnat", "Ulkomaat", "Hankinnat"];
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
- Suomi Tänään kertoo politiikasta, päätöksistä, julkisesta taloudesta, viranomaisista ja yhteiskunnasta. Aseta "hylkaa": true, jos lähde on urheilua, viihdettä, yrityksen tuote- tai markkinointitiedote, tapahtumailmoitus tai rutiinitiedote ilman uutta tietoa.
Lisäksi kirjoita TikTok-käsikirjoitus (noin 30 sekuntia, 60–80 sanaa): vahva koukku ensimmäiseen lauseeseen, suora ja iskevä kieli, nimeä päättäjät jos ne ovat lähteessä, faktat tarkasti lähteen mukaan, loppuun "Koko juttu ja lähteet: linkki biossa."
Vastaa PELKÄLLÄ JSON-oliolla, ei muuta tekstiä:
{"hylkaa":false,"syy":"","otsikko":"","ingressi":"","teksti":"kappale 1\\n\\nkappale 2","kategoria":"${KATEGORIAT.join("|")}","tarkistettavat":["väite tai luku, joka toimittajan kannattaa tarkistaa lähteestä"],"tiktok":{"koukku":"","teksti":"","sivusto":"Suomi Tänään"}}`;

async function kirjoita(ehdokas, teksti) {
  const sisalto = `Lähteen tyyppi: ${ehdokas.tyyppi}\nLähde: ${ehdokas.lahde}\nOsoite: ${ehdokas.url}\nPäivämäärä: ${ehdokas.aika || "ei tiedossa"}\nOtsikko: ${ehdokas.otsikko}\n${ehdokas.lisa || ""}\n\nLähteen sisältö:\n${teksti}`;
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: MALLI, max_tokens: 2500, system: OHJE, messages: [{ role: "user", content: sisalto }] }),
  });
  if (!r.ok) throw new Error("Claude " + r.status + " " + (await r.text()).slice(0, 200));
  const d = await r.json();
  const t = (d.content || []).map(c => c.text || "").join("");
  const j = JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1));
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
  // STT Infosta vain julkishallinnon, eduskunnan ja puolueiden tiedotteet (ei urheilua, viihdettä eikä yritysten markkinointia)
  const JULKINEN = /ministeri|valtioneuvosto|eduskun|virasto|kela|poliisi|puolue|kunta|kaupun|hyvinvointialue|tilastokeskus|verohallinto|traficom|thl|tuomioistu|syyttäj|puolustusvoim|rajavartio|suojelupoliisi|ulkoministeri|presidentti/i;
  const tiedotteet = (lahteet.tiedotteet || []).filter(t => tuore(t.aika, 48) && !nahdyt.has(t.url) &&
      (t.ryhma === "Valtio ja virastot" || t.ryhma === "Kunnat" || (t.lahde === "STT Info: tiedotteet" && JULKINEN.test(t.otsikko))))
    .map(t => ({ tyyppi: "Viranomaisen tai organisaation tiedote", lahde: t.lahde, url: t.url, otsikko: t.otsikko, aika: t.aika, oletusKategoria: t.ryhma === "Kunnat" ? "Kunnat" : "Kotimaa", p: pisteet(t.otsikko) + (t.ryhma === "Valtio ja virastot" ? 5 : 0) }));

  // Kaksi kolmasosaa äänestyksiä ja virastojen tiedotteita, loput kuumimmista aiheista
  const valitut = [...aanestykset.sort((a, b) => b.p - a.p).slice(0, Math.ceil(MAX * 0.4)), ...tiedotteet.sort((a, b) => b.p - a.p)].slice(0, MAX * 2);
  const valmiit = [];
  for (const e of valitut) {
    if (valmiit.length >= MAX) break;
    try {
      const teksti = await haeTeksti(e.url);
      if (teksti.length < 200) { console.log("Liian lyhyt lähde:", e.url); continue; }
      const j = await kirjoita(e, teksti);
      if (j.hylkaa) { console.log("Hylätty (ei uutisarvoa):", e.otsikko, j.syy); valmiit.hylatyt = [...(valmiit.hylatyt || []), { vain_nahty: true, lahde_url: e.url }]; continue; }
      valmiit.push({ ...j, lahde_url: e.url, lahdetyyppi: e.tyyppi, lahteet: [{ nimi: `${e.lahde}: ${e.otsikko}`.slice(0, 200), url: e.url }] });
      console.log("Luonnos:", j.otsikko);
    } catch (err) { console.log("Epäonnistui:", e.url, err.message); }
  }
  if (valmiit.length || valmiit.hylatyt) {
    const r = await fetch(WORKER + "/api/luonnokset", { method: "POST", headers: { authorization: "Bearer " + PW, "content-type": "application/json" }, body: JSON.stringify([...valmiit, ...(valmiit.hylatyt || [])]) });
    huomio("Luonnokset", `${valmiit.length} uutta luonnosta toimitukseen (${r.status}). Ehdokkaita oli ${aanestykset.length} äänestystä ja ${tiedotteet.length} tiedotetta.`);
  } else huomio("Luonnokset", `Ei uusia luonnoksia. Ehdokkaita ${aanestykset.length} äänestystä, ${tiedotteet.length} tiedotetta.`);
}
main().catch(e => { huomio("Virhe", e.message); process.exit(1); });
