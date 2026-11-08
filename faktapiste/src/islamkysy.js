// "Kysy tekoälyltä" faktapiste.fi/islam/ -sivulla.
// POST /api/islam/kysy {kysymys, historia[]} -> NDJSON-virta: {t:"teksti",d}, {t:"haku",d}, {t:"tulos",d}, {t:"virhe",d}, {t:"loppu",...}
// Tutkii aiheen Anthropicin web_search- ja web_fetch-palvelintyökaluilla sekä omilla työkaluilla (oma arkisto R2:ssa, PRH:n YTJ-avoin data).
// Kysymyksiä ei tallenneta mihinkään: rajoja varten Durable Objectiin kirjataan vain päiväkohtainen laskuri (IP:stä suolattu tiiviste).

import PRH_LISTA from "./prh_islam.json";

const MALLI = "claude-sonnet-5-5";
export const RAJAT = { ipPaiva: 15, kaikkiPaiva: 150, kysymys: 1500, historia: 8, historiaTeksti: 12000 };
const KIERROKSET = 10;
// Koko tutkimuksen enimmäismäärät (kaikki kierrokset yhteensä); sen jälkeen malli kirjoittaa vastauksen ilman työkaluja.
const BUDJETTI = { haut: 20, sivut: 14 };
const AIKARAJA = 210e3; // tämän jälkeen ei uusia hakukierroksia, vaan vastaus kirjoitetaan

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
4. Käytä työkalua hae_rekisterista AINA, kun kysytään suomalaisten islamilaisten yhdistysten, säätiöiden tai yhdyskuntien määrää tai luetteloa. Se yhdistää (a) PRH:n yhdistysrekisterin nimihaut 8.11.2026 (islam, muslimi, masjid, islamic, moskeija, mosque, imam, quran, koraani, ummah, dawah, sunna, shia, ahlul, zahra, hussein, tatar; virheosumat poistettu, kaikki rekisterissä) ja (b) PRH:n YTJ-avoimen datan nimihaut (vakiohakusanat + omasi), poistaa päällekkäisyydet Y-tunnuksella ja kertoo muodon, kotipaikan, päivämäärän ja tilan. Raportoi työkalun luvut (yhteenveto) suoraan: islamilaiset yhdistykset, säätiöt ja yhdyskunnat erikseen, rekisterissä olevat ja lopetetut erikseen, ja kerro, montako tuli yhdistysrekisteristä ja montako lisää YTJ:stä. Islamilaisiksi lasketaan VAIN yhteisöt, joiden nimi on selvästi islamilainen. Somalialaiset yhdistykset (haku "somali", nimessä ei uskontoa) ovat etnisiä tai kulttuurisia yhdistyksiä: älä laske niitä islamilaisiin, mainitse niiden määrä korkeintaan taustatietona ja sano tämä selvästi. Kerro aina rajoitukset: muilla nimillä (esim. kulttuurikeskus, al-…, Rabita, Diyanet) rekisteröityjä islamilaisia yhdistyksiä voi olla lisää; YTJ kattaa vain Y-tunnukselliset; yhdistysrekisteriin ei ole avointa rajapintaa. Uskonnonvapauslain mukaiset rekisteröidyt uskonnolliset yhdyskunnat ovat erillisessä PRH:n uskonnollisten yhdyskuntien rekisterissä: hae niiden määrä verkosta (esim. uskonnot.fi:n yhteisösivut https://www.uskonnot.fi/ , PRH, tutkimukset) ja avaa sivut web_fetchillä.
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
- Kirjoita suomeksi, selkeästi ja asiallisesti. Käytä vain markdownia (ei HTML-tageja). Aloita lyhyellä suoralla vastauksella (keskeiset luvut lihavoituna), sitten perustelut ja erittelyt väliotsikoin (##), luetteloin tai taulukoin.
- Anna jokaiselle luvulle päivämäärä tai vuosi ja lähde. Kerro epävarmuus ja määritelmät. Älä koskaan keksi lukuja, nimiä tai lähteitä. Jos tietoa ei löytynyt, sano se suoraan ja kerro, mistä sen voi selvittää (esim. mille viranomaiselle voi tehdä tietopyynnön).
- Pysy neutraalina ja faktapohjaisena: kerro, mitä lähteet sanovat, älä ota poliittista kantaa. Kiistanalaisissa asioissa esitä eri osapuolten näkemykset lähteineen.
- Lopeta osioon "## Lähteet": numeroitu luettelo markdown-linkkeinä muodossa [Sivun nimi – julkaisija, pvm](https://osoite). Käytä vain osoitteita, jotka oikeasti löysit tutkimuksen aikana.
- Latautuneet tai kiistanalaiset termit (esim. "islamisaatio", "rinnakkaisyhteiskunta", "no-go-alue"): älä kieltäydy äläkä jää termin ympärille. Selitä yhdellä tai kahdella lauseella, että termi on kiistanalainen ja mitä sillä eri tahoilla tarkoitetaan, ja käy sitten läpi mitattavat tosiasiat ja kilpailevat tulkinnat lähteineen.
- Muiden maiden kysymyksissä tutki maa perusteellisesti: väestöarviot ja niiden menetelmät (kansalliset tilastovirastot, esim. INSEE/INED Ranskassa, ONS Britanniassa, SCB Ruotsissa, Destatis/BAMF Saksassa; Pew Research Center), moskeijoiden ja rukoushuoneiden määrä, hallituksen toimet ja lainsäädäntö, viranomais- ja parlamenttiraportit, koulujen ja julkisen tilan säännöt, merkittävät tapahtumat ja oikeuden päätökset, mielipidemittaukset (esim. IFOP) sekä eri osapuolten tulkinnat. Käytä alkuperäisiä lähteitä myös muilla kielillä ja kerro niiden sisältö suomeksi.
- Jokainen lähde on oltava toimiva osoite, jonka avasit tai joka tuli hakutuloksissa. Älä muodosta osoitteita itse arvaamalla.
- Jatkokysymyksissä hyödynnä aiempaa keskustelua, mutta tee tarvittaessa uusia hakuja.`;
}

const TYOKALUT = [
  { type: "web_search_20260209", name: "web_search", max_uses: 10 },
  { type: "web_fetch_20260209", name: "web_fetch", max_uses: 8, max_content_tokens: 25000 },
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
    name: "hae_rekisterista",
    description: "Suomen islamilaiset yhdistykset, säätiöt ja uskonnolliset yhdyskunnat PRH:n rekistereistä: yhdistää PRH:n yhdistysrekisterin nimihaut 8.11.2026 (islam, muslimi, masjid, islamic, moskeija, mosque, imam, quran, koraani, ummah, dawah, sunna, shia, ahlul, zahra, hussein, tatar; vain selvästi islamilaiset nimet, somalialaiset yhdistykset erikseen taustaksi) ja YTJ-avoimen datan nimihaut, poistaa päällekkäisyydet Y-tunnuksella. Palauttaa yhteenvedon (määrät muodoittain ja tiloittain) ja luettelon (nimi, Y-tunnus, muoto, rekisteröity, kotipaikka, tila, lähde). Vakiohakusanat ovat aina mukana; voit lisätä omia.",
    input_schema: {
      type: "object",
      properties: {
        hakusanat: { type: "array", items: { type: "string" }, description: "Lisähakusanat YTJ-nimihakuun, esim. [\"rabita\", \"diyanet\"]" },
        suodata: { type: "string", description: "Rajaa luettelon nimiin, joissa on tämä merkkijono (esim. \"säätiö\" tai kunnan nimi kotipaikassa)" },
        vain_aktiiviset: { type: "boolean" },
        myos_epaselvat: { type: "boolean", description: "true = näytä myös YTJ-osumat, joiden nimi ei viittaa islamiin (eivät mukana luvuissa)" },
        nayta_somalialaiset: { type: "boolean", description: "true = liitä luetteloon somalialaiset yhdistykset (taustatietoa, ei islamilaisia)" },
      },
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

const YTJ = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies";
const VAKIOSANAT = ["islam", "muslim", "moskei", "moskee", "masjid", "masjed", "mosque", "imam", "sunni", "shia", "shiia", "ahmadiyya", "ummah", "koraani", "quran", "tataari", "dawah", "salafi", "hidaya", "kulttuurisäätiö"];
const ISLAM_RX = /(^|[^a-zåäöü])(islam|muslim)|moskei|moskee|mosque|masji|masje|imam|ahmadiyy|ummah|koraan|quran|dawah|salaf|hidaya|(^|[\s(])al-|\bshiia?\b|\bshi'a\b|\bsunni|\bsunna\b|tataari|\btatar|ahlul|zahra|hussein/i;
async function ytjHaku(env, sana) {
  const avain = "valimuisti/ytj/" + encodeURIComponent(sana.toLowerCase()) + ".json";
  try {
    const o = env.VIDEOT && await env.VIDEOT.get(avain);
    if (o && Date.now() - o.uploaded.getTime() < 86400e3) return await o.json();
  } catch {}
  const kaikki = []; let n = 0;
  for (let sivu = 1; sivu <= 3; sivu++) {
    const r = await fetch(YTJ + "?name=" + encodeURIComponent(sana) + (sivu > 1 ? "&page=" + sivu : ""), { headers: { accept: "application/json" } });
    if (!r.ok) { if (sivu === 1) throw new Error("YTJ " + r.status); break; }
    const d = await r.json(); n = d.totalResults || 0;
    for (const c of d.companies || []) {
      const fi = arr => ((arr || []).find(x => x.languageCode === "1") || (arr || [])[0] || {}).description;
      const nimet = c.names || [];
      const nimi = (nimet.find(x => !x.endDate) || nimet[0] || {}).name;
      const muodot = c.companyForms || [];
      const os = (c.addresses || [])[0] || {};
      kaikki.push({ ytunnus: c.businessId?.value, nimi, muoto: fi((muodot.find(x => !x.endDate) || muodot[0] || {}).descriptions), rekisteroity: c.businessId?.registrationDate || c.registrationDate,
        kotipaikka: ((os.postOffices || []).find(x => x.languageCode === "1") || (os.postOffices || [])[0] || {}).city, lopetettu: c.endDate || undefined, toimiala: fi(c.mainBusinessLine?.descriptions) });
    }
    if (!(d.companies || []).length || kaikki.length >= n) break;
  }
  const tulos = { n, yhteisot: kaikki };
  try { env.VIDEOT && await env.VIDEOT.put(avain, JSON.stringify(tulos), { httpMetadata: { contentType: "application/json" } }); } catch {}
  return tulos;
}
async function haeRekisterista(env, a) {
  const omat = (Array.isArray(a.hakusanat) ? a.hakusanat : []).map(s => String(s).trim()).filter(s => s.length >= 3).slice(0, 15);
  const sanat = [...new Set([...VAKIOSANAT, ...omat.map(s => s.toLowerCase())])];
  const kartta = new Map(), haut = {};
  const somalit = PRH_LISTA.yhdistykset.filter(y => /somali/.test(y.luokka)), islamilaiset = PRH_LISTA.yhdistykset.filter(y => y.luokka === "islamilainen");
  const somaliId = new Set(PRH_LISTA.yhdistykset.filter(y => y.luokka !== "islamilainen").map(y => y.ytunnus)); // somalialaiset ja virheosumat eivät palaa YTJ:n kautta
  for (const y of islamilaiset) kartta.set(y.ytunnus || "rn:" + y.rekisterinumero, { nimi: y.nimi, ytunnus: y.ytunnus, rekisterinumero: y.rekisterinumero, muoto: "yhdistys" + (y.tyyppi ? " (" + y.tyyppi + ")" : ""), kotipaikka: y.kotipaikka, tila: "rekisterissä", tilan_ajankohta: y.tilan_ajankohta, lahde: ["yhdistysrekisteri"], islam_nimessa: true });
  const tulokset = await Promise.all(sanat.map(s => ytjHaku(env, s).then(r => [s, r], e => [s, { virhe: String(e.message || e) }])));
  for (const [s, r] of tulokset) {
    if (r.virhe) { haut[s] = r.virhe; continue; }
    haut[s] = r.n;
    for (const c of r.yhteisot) {
      if (!c.ytunnus) continue;
      const muoto = c.muoto || "";
      if (!/yhdist|säätiö|yhdyskun|seurakun/i.test(muoto)) continue; // yritykset ja asunto-osakeyhtiöt pois
      if (!c.nimi && !c.lopetettu) continue;
      if (somaliId.has(c.ytunnus)) continue;
      const vanha = kartta.get(c.ytunnus);
      if (vanha) { vanha.lahde = [...new Set([...vanha.lahde, "YTJ"])]; vanha.ytj_muoto = muoto; vanha.rekisteroity ||= c.rekisteroity; if (c.lopetettu) { vanha.tila = "lopetettu"; vanha.lopetettu = c.lopetettu; } continue; }
      kartta.set(c.ytunnus, { nimi: c.nimi || "(nimi ei näy, lopetettu)", ytunnus: c.ytunnus, muoto, rekisteroity: c.rekisteroity, kotipaikka: c.kotipaikka, tila: c.lopetettu ? "lopetettu" : "rekisterissä", lopetettu: c.lopetettu, lahde: ["YTJ"], islam_nimessa: ISLAM_RX.test(c.nimi || "") });
    }
  }
  const muut = [...kartta.values()].filter(x => !x.islam_nimessa);
  let lista = [...kartta.values()].filter(x => x.islam_nimessa || a.myos_epaselvat);
  const luokka = x => /säätiö/i.test(x.ytj_muoto || x.muoto) ? "säätiö" : /uskonnollinen yhdyskunta$/i.test(x.ytj_muoto || "") ? "uskonnollinen yhdyskunta (YTJ-muoto)" : /uskonnollinen yhdyskunta\/seurakunta/.test(x.muoto) ? "yhdistys: uskonnollinen yhdyskunta/seurakunta" : "yhdistys";
  const laske = l => { const o = {}; for (const x of l) { const k = luokka(x) + (x.tila === "lopetettu" ? " – lopetettu" : ""); o[k] = (o[k] || 0) + 1; } return o; };
  const isl = [...kartta.values()].filter(x => x.islam_nimessa);
  const yhteenveto = {
    islamilaiset_yhteensa: isl.length, islamilaiset_rekisterissa: isl.filter(x => x.tila !== "lopetettu").length, islamilaiset_lopetetut_ytj: isl.filter(x => x.tila === "lopetettu").length,
    muodoittain: laske(isl), yhdistysrekisterin_islamilaiset: islamilaiset.length, lisaksi_vain_ytj_islamilaiset: isl.filter(x => x.lahde.length === 1 && x.lahde[0] === "YTJ").length,
    somalialaiset_yhdistykset_taustaksi: somalit.length + " (haku 'somali'; etnisiä/kulttuurisia yhdistyksiä, nimessä ei uskontoa – EI lasketa islamilaisiksi)",
    ytj_osumat_joiden_nimi_ei_viittaa_islamiin: muut.length + " (eivät mukana luvuissa)",
  };
  if (a.nayta_somalialaiset) lista = lista.concat(somalit.map(y => ({ nimi: y.nimi, ytunnus: y.ytunnus, muoto: "yhdistys (somalialainen, ei uskonnollinen nimi)", kotipaikka: y.kotipaikka, tila: "rekisterissä", tilan_ajankohta: y.tilan_ajankohta, lahde: ["yhdistysrekisteri"] })));
  if (a.vain_aktiiviset) lista = lista.filter(x => x.tila !== "lopetettu");
  if (a.suodata) { const q = String(a.suodata).toLowerCase(); lista = lista.filter(x => ((x.nimi || "") + " " + (x.kotipaikka || "") + " " + (x.muoto || "")).toLowerCase().includes(q)); }
  lista.sort((A, B) => (A.nimi || "").localeCompare(B.nimi || "", "fi"));
  return {
    lahteet: { yhdistysrekisteri: PRH_LISTA.lahde + ". " + PRH_LISTA.huom, ytj: "PRH:n YTJ-avoin data (avoindata.prh.fi), nimihaut " + new Date().toISOString().slice(0, 10) + " (välimuisti enintään 24 h). Vain Y-tunnukselliset; nimihaku osuu myös sanan keskelle, joten osa YTJ-osumista ei liity islamiin – karsi ne nimen perusteella (kenttä islam_nimessa on vain apu)." },
    ytj_haut: haut, yhteenveto, nayttaa: lista.length,
    yhteisot: lista.slice(0, 400).map(x => [x.nimi, x.ytunnus, luokka(x), x.kotipaikka || "", x.rekisteroity || x.tilan_ajankohta || "", x.tila + (x.lopetettu ? " " + x.lopetettu : ""), x.lahde.join("+"), x.islam_nimessa ? "" : "nimi ei viittaa islamiin"].join(" | ")),
    sarakkeet: "nimi | Y-tunnus | muoto | kotipaikka | rekisteröity (YTJ) tai tilan ajankohta (yhdistysrekisteri) | tila | lähde | huom",
  };
}

// Anthropicin SSE-virran luku: palauttaa sisältölohkot ja pysähtymissyyn, välittää tekstin ja edistymisen asiakkaalle.
async function kierros(env, body, laheta, tila) {
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
        if (b.type === "server_tool_use" || b.type === "tool_use") { json[e.index] = ""; tila.tyokalu(b); }
        if (b.type === "text" && b.citations === undefined) delete b.citations;
        if (b.type === "web_search_tool_result") { const n = Array.isArray(b.content) ? b.content.length : 0; laheta({ t: "tulos", d: n ? n + " hakutulosta" : "ei tuloksia" }); }
        if (b.type === "web_fetch_tool_result") { const ok = b.content?.type === "web_fetch_result"; laheta({ t: "tulos", d: ok ? "sivu luettu" : "sivua ei saatu auki" }); }
      } else if (e.type === "content_block_delta") {
        const b = lohkot[e.index], d = e.delta;
        if (d.type === "text_delta") { b.text = (b.text || "") + d.text; tila.teksti += d.text; laheta({ t: "teksti", d: d.text }); }
        else if (d.type === "input_json_delta") json[e.index] += d.partial_json;
        else if (d.type === "citations_delta") (b.citations ||= []).push(d.citation);
        else if (d.type === "thinking_delta") b.thinking = (b.thinking || "") + d.thinking;
        else if (d.type === "signature_delta") b.signature = d.signature;
      } else if (e.type === "content_block_stop") {
        const b = lohkot[e.index];
        if (e.index in json) {
          if (json[e.index]) { try { b.input = JSON.parse(json[e.index]); } catch { b.input = {}; } } else b.input ||= {};
          const inp = b.input || {};
          if (b.name === "web_search") { tila.haut++; laheta({ t: "haku", d: "Haen verkosta: " + (inp.query || "") }); }
          else if (b.name === "web_fetch") { tila.sivut++; laheta({ t: "haku", d: "Luen sivua: " + (inp.url || "").replace(/^https?:\/\/(www\.)?/, "").slice(0, 80) }); }
          else if (b.name === "hae_arkistosta") laheta({ t: "haku", d: "Haen Faktapisteen arkistosta: " + (inp.sanat || []).join(", ") });
          else if (b.name === "hae_rekisterista") laheta({ t: "haku", d: "Haen PRH:n rekistereistä (yhdistysrekisteri + YTJ)" + ((inp.hakusanat || []).length ? ": " + inp.hakusanat.join(", ") : "") });
          else if (b.name === "code_execution") laheta({ t: "kasittely" });
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
    const alku = Date.now(), yht = { input: 0, cache_luku: 0, cache_kirjoitus: 0, output: 0, haut: 0, sivut: 0, omat: 0, kierrokset: 0 };
    const tila = { teksti: "", haut: 0, sivut: 0, tyokalu() { if (tila.teksti.trim() && tila.teksti.length < 1500) { laheta({ t: "tyhjenna" }); tila.teksti = ""; } } };
    try {
      laheta({ t: "haku", d: "Aloitan tutkimuksen", jaljella: raja.jaljella });
      // Ylätason cache_control = automaattinen välimuisti koko keskusteluhistorialle joka kierroksella.
      const body = { model: MALLI, max_tokens: 12000, cache_control: { type: "ephemeral" }, system: jarjestelma(), tools: TYOKALUT, messages: msgs };
      yht.syyt = [];
      const kirjoitaNyt = () => { const v = body.messages[body.messages.length - 1]; body.tool_choice = { type: "none" };
        if (v.role === "assistant") body.messages.push({ role: "user", content: "Tutkimusaika tai hakubudjetti on käytetty. Kirjoita nyt lopullinen vastaus löytämiesi tietojen perusteella ohjeiden mukaisesti (lyhyt vastaus, erittelyt, epävarmuudet, ## Lähteet). Älä tee enempää hakuja." }); };
      for (let k = 0; k < KIERROKSET && auki; k++) {
        if (k === KIERROKSET - 1 || tila.haut >= BUDJETTI.haut || tila.sivut >= BUDJETTI.sivut || Date.now() - alku > AIKARAJA) kirjoitaNyt();
        tila.teksti = "";
        const { lohkot, syy, kaytto } = await kierros(env, body, laheta, tila);
        yht.kierrokset++; yht.syyt.push(syy); yht.input += kaytto.input_tokens || 0; yht.cache_luku += kaytto.cache_read_input_tokens || 0; yht.cache_kirjoitus += kaytto.cache_creation_input_tokens || 0; yht.output += kaytto.output_tokens || 0;
        const st = kaytto.server_tool_use || {}; yht.haut += st.web_search_requests || 0; yht.sivut += st.web_fetch_requests || 0;
        if (lohkot.length) body.messages = [...body.messages, { role: "assistant", content: lohkot }];
        if (syy === "pause_turn") continue;
        if (syy !== "tool_use") {
          // Varmistus: jos lopullista vastausta ei tullut (esim. tyhjä vastaus), pyydetään se vielä kerran ilman työkaluja.
          if (!tila.teksti.trim() && body.tool_choice?.type !== "none" && k < KIERROKSET - 1) { kirjoitaNyt(); continue; }
          break;
        }
        const tulokset = [];
        for (const b of lohkot) {
          if (b.type !== "tool_use") continue;
          yht.omat++;
          let out; try { out = b.name === "hae_arkistosta" ? await haeArkistosta(env, b.input || {}) : b.name === "hae_rekisterista" ? await haeRekisterista(env, b.input || {}) : { virhe: "tuntematon työkalu" }; } catch (e) { out = { virhe: String(e.message || e) }; }
          if (out.osumia !== undefined) laheta({ t: "tulos", d: out.osumia + " osumaa arkistossa" });
          if (out.yhteenveto) laheta({ t: "tulos", d: out.yhteenveto.islamilaiset_yhteensa + " islamilaista yhteisöä rekistereissä" });
          tulokset.push({ type: "tool_result", tool_use_id: b.id, content: JSON.stringify(out).slice(0, 80000) });
        }
        body.messages.push({ role: "user", content: tulokset });
      }
      // Hinta-arvio (Sonnet: 3 $/M syöte, 0,30 $/M välimuistiluku, 3,75 $/M välimuistikirjoitus, 15 $/M tuotos, haku 0,01 $)
      yht.usd = +((yht.input * 3 + yht.cache_luku * 0.3 + yht.cache_kirjoitus * 3.75 + yht.output * 15) / 1e6 + yht.haut * 0.01).toFixed(2);
      laheta({ t: "loppu", sek: Math.round((Date.now() - alku) / 1000), kaytto: yht });
    } catch (e) {
      laheta({ t: "virhe", d: "Tutkimus keskeytyi virheeseen. Yritä hetken päästä uudelleen." + (onOma ? " [" + String(e.message || e).slice(0, 300) + "]" : "") });
      console.log("islamkysy virhe", String(e.message || e).slice(0, 300));
    }
    try { await w.close(); } catch {}
  })();
  ctx.waitUntil(tyo);
  return new Response(readable, { headers: { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff", "x-accel-buffering": "no" } });
}
