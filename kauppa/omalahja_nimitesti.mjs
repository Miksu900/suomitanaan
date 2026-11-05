// Omalahja: käy läpi suunnittelijoiden kaikki ohjaimet kuin käyttäjä (Pixel 7, kosketus, hidas 4G) oikealla sivulla.
// Tarkistaa, että jokainen napautus/kirjoitus muuttaa esikatselua, ettei napautuksia peitä mikään ja ettei tule virheitä.
import { chromium, devices } from "playwright";
const POHJA = process.env.POHJA || "https://omalahja.fi";
const b = await chromium.launch();
const ctx = await b.newContext({ ...devices["Pixel 7"], locale: "fi-FI" });
const p = await ctx.newPage();
const cdp = await ctx.newCDPSession(p);
await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 1.6e6 / 8, uploadThroughput: 750e3 / 8 });
const virheet = [];
p.on("console", (m) => { if (m.type() === "error") virheet.push("konsoli: " + m.text().slice(0, 200)); });
p.on("pageerror", (e) => virheet.push("sivuvirhe: " + e.message.slice(0, 200)));
p.on("requestfailed", (r) => virheet.push("pyyntö epäonnistui: " + r.url().slice(0, 100) + " " + r.failure()?.errorText));
const ongelmat = [];
const tiiviste = () => p.evaluate(() => { const c = document.getElementById("cv"); const d = c.toDataURL("image/jpeg", 0.5); let h = 0; for (let i = 0; i < d.length; i += 7) h = (h * 31 + d.charCodeAt(i)) | 0; return h; });
async function napauta(sel, kuvaus, muuttaa = true) {
  const el = p.locator(sel).first();
  if (!(await el.count())) { ongelmat.push(`${kuvaus}: elementtiä ei löydy (${sel})`); return; }
  await el.scrollIntoViewIfNeeded().catch(() => {});
  // peittääkö jokin (esim. alapalkki tai tahmea esikatselu) napautuskohdan?
  const peitto = await el.evaluate((e) => { const r = e.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2; const t = document.elementFromPoint(x, y); return t && !e.contains(t) && !t.contains(e) ? (t.id || t.className || t.tagName) : ""; });
  if (peitto) ongelmat.push(`${kuvaus}: napautuskohdan peittää ${String(peitto).slice(0, 60)}`);
  const ennen = await tiiviste();
  try { await el.tap({ timeout: 5000 }); } catch (e) { ongelmat.push(`${kuvaus}: napautus epäonnistui ${e.message.slice(0, 80)}`); return; }
  await p.waitForTimeout(250);
  if (muuttaa && (await tiiviste()) === ennen) ongelmat.push(`${kuvaus}: esikatselu ei muuttunut`);
}
async function kirjoita(sel, teksti, kuvaus) {
  const el = p.locator(sel).first();
  if (!(await el.count())) { ongelmat.push(`${kuvaus}: kenttää ei löydy`); return; }
  await el.scrollIntoViewIfNeeded().catch(() => {});
  const ennen = await tiiviste();
  await el.tap().catch(() => {}); await el.fill(""); await el.type(teksti, { delay: 15 }); await p.waitForTimeout(300);
  if ((await tiiviste()) === ennen) ongelmat.push(`${kuvaus}: kirjoitus ei päivittänyt esikatselua`);
  // jääkö kenttä tahmean esikatselun alle?
  const piilossa = await el.evaluate((e) => { const r = e.getBoundingClientRect(); const t = document.elementFromPoint(r.left + 10, r.top + r.height / 2); return t && !e.contains(t) && t !== e ? (t.id || t.className || t.tagName) : ""; });
  if (piilossa) ongelmat.push(`${kuvaus}: kenttä peittyy (${String(piilossa).slice(0, 50)})`);
}
async function avaa(otsikko) { const s = p.locator("details.osio > summary", { hasText: otsikko }).first(); if (await s.count()) { const auki = await s.evaluate((e) => e.parentElement.open); if (!auki) { await s.scrollIntoViewIfNeeded(); await s.tap(); await p.waitForTimeout(200); } } else ongelmat.push("osiota ei löydy: " + otsikko); }

// ---------- Nimijuliste ----------
await p.goto(POHJA + "/tee/nimijuliste/?v=" + Date.now(), { waitUntil: "load", timeout: 90000 });
await p.waitForTimeout(1500);
await p.screenshot({ path: "out/nimi-alku.png" });
await napauta('[data-ryhma="tuote"] [data-arvo="kehys"]', "Tuote kehys");
await napauta('[data-ryhma="vari"] [data-arvo="valkoinen"]', "Kehysväri valkoinen", false);
await napauta('[data-ryhma="koko"] [data-arvo="50x70"]', "Koko 50x70");
await napauta('[data-ryhma="suunta"] [data-arvo="vaaka"]', "Suunta vaaka");
await napauta('[data-ryhma="suunta"] [data-arvo="pysty"]', "Suunta pysty");
await napauta('[data-ryhma="tuote"] [data-arvo="canvas"]', "Tuote canvas");
await avaa("Muokkaa tyyliä");
for (const a of ["sydanviiva", "minimal", "perhe", "kehys", "monogrammi", "vauva", "haat", "jae", "keskitetty"]) await napauta(`[data-ryhma="asettelu"] [data-arvo="${a}"]`, "Asettelu " + a);
await avaa("Tekstit");
await kirjoita("#k-nimi", "Testi Nimi", "Nimi");
await kirjoita("#k-ala", "Alaotsikko", "Alaotsikko");
await kirjoita("#k-pvm", "1.1.2027", "Päivämäärä");
await kirjoita("#k-lisa", "Lisärivi tähän", "Lisärivi");
await avaa("Raamatunlause");
await p.locator("#jaevalinta").selectOption("2").catch((e) => ongelmat.push("jaevalinta: " + e.message.slice(0, 80)));
await p.waitForTimeout(300);
await kirjoita("#k-viite", "Ps. 1:1", "Jaeviite");
for (const f of ["elegantti", "kasiala", "moderni"]) await napauta(`[data-ryhma="fontti"] [data-arvo="${f}"]`, "Fontti " + f);
for (const v of ["yonsininen", "salvia"]) await napauta(`[data-ryhma="paletti"] [data-arvo="${v}"]`, "Paletti " + v);
for (const k of ["sydamet", "lumi", "risti"]) await napauta(`[data-ryhma="kuvio"] [data-arvo="${k}"]`, "Kuvio " + k);
for (const s of ["kulmat", "reunus", "tausta", "yla"]) await napauta(`[data-ryhma="kuvioSij"] [data-arvo="${s}"]`, "Kuvion paikka " + s);
await napauta('[data-ryhma="kuvioKoko"] [data-arvo="suuri"]', "Kuvion koko suuri");
await p.evaluate(() => scrollTo(0, 0));
await napauta("#suurenna", "Suurenna", false);
await p.screenshot({ path: "out/nimi-suurennettu.png" });
await napauta("#suurenna", "Pienennä", false);
await napauta("#jatka", "Jatka tilaamaan", false);
await p.waitForTimeout(1200);
const kassa = await p.evaluate(() => { const k = document.getElementById("kassa"); return { nakyy: !k.hidden && k.getBoundingClientRect().height > 300, teksti: k.innerText }; });
if (!kassa.nakyy) ongelmat.push("Jatka tilaamaan: tilausikkuna ei avautunut");
if (!/avautuvat pian/i.test(kassa.teksti)) ongelmat.push("Tilausikkuna ei kerro, että tilaukset avautuvat pian");
await p.screenshot({ path: "out/nimi-kassa.png" });
await p.locator("#kassa .sulje").tap(); await p.waitForTimeout(300);
// rikkinäinen tallennus ei saa kaataa sivua
await p.evaluate(() => localStorage.setItem("omalahja-nimi", '{"tuote":"xx","koko":"99","asettelu":"eiole","fontti":"x","paletti":"y","kuvio":"z","nimi":5}'));
await p.reload({ waitUntil: "load" }); await p.waitForTimeout(1200);
const ok = await p.evaluate(() => !!document.querySelector("#ohj .osio") && document.getElementById("cv").width > 50);
if (!ok) ongelmat.push("Rikkinäinen localStorage kaatoi sivun");
await p.screenshot({ path: "out/nimi-rikkinainen-tallennus.png" });

// ---------- Kartta: ohjaimet ----------
await p.evaluate(() => localStorage.clear());
await p.goto(POHJA + "/tee/kartta/?esim=ylivieska&v=" + Date.now(), { waitUntil: "load", timeout: 90000 });
await p.waitForFunction(() => window.OLTesti && window.OLTesti.kartta(), null, { timeout: 90000 }).catch(() => ongelmat.push("Kartta: data ei latautunut 90 s:ssa"));
await avaa("Muokkaa tyyliä");
for (const t of ["salvia", "hiili"]) await napauta(`[data-ryhma="teema"] [data-arvo="${t}"]`, "Teema " + t);
for (const m of ["sydan", "ympyra", "pyorea", "koko"]) await napauta(`[data-ryhma="muoto"] [data-arvo="${m}"]`, "Muoto " + m);
for (const r of ["kapea", "ei", "valja"]) await napauta(`[data-ryhma="reunus"] [data-arvo="${r}"]`, "Reunus " + r);
await napauta('[data-ryhma="paksuus"] [data-arvo="paksu"]', "Paksuus");
for (const t of ["paalla", "ei", "alla"]) await napauta(`[data-ryhma="tekstiSij"] [data-arvo="${t}"]`, "Tekstin paikka " + t);
await kirjoita("#k-otsikko", "Kotimme", "Kartan otsikko");
await kirjoita("#k-ala", "Rakas paikka", "Kartan alaotsikko");
await napauta('.nuolet button >> nth=0', "Siirrä ylös");
await napauta('[data-ryhma="kuvio"] [data-arvo="lumi"]', "Kartan kuvio");
// ---------- Helpoin polku etusivulta maksuvaiheeseen: napautusten määrä ----------
await p.evaluate(() => localStorage.clear());
let napautukset = 0; const n = async (sel) => { const el = p.locator(sel).first(); await el.scrollIntoViewIfNeeded(); await el.tap(); napautukset++; await p.waitForTimeout(500); };
await p.goto(POHJA + "/?v=" + Date.now(), { waitUntil: "load" });
await n('.sankari .nappi.iso'); await p.waitForLoadState("load");
await n('.polku[href="/tee/nimijuliste/"]'); await p.waitForLoadState("load"); await p.waitForTimeout(1200);
await n('.pohja[data-pohja="perhe"]');
await n('#k-nimi'); await p.locator('#k-nimi').fill('Perhe Koskela');
await n('#jatka'); await p.waitForTimeout(800);
await n('input[name="tarkistettu"]');
for (const [k, v] of [["nimi", "Testi Asiakas"], ["email", "testi@example.com"], ["puhelin", "0401234567"], ["osoite", "Riihikatu 3"], ["postinro", "84100"], ["kaupunki", "Ylivieska"]]) { await n(`#tilauslomake input[name="${k}"]`); await p.locator(`#tilauslomake input[name="${k}"]`).fill(v); }
await n('input[name="hyvaksy"]');
const maksuNappi = await p.evaluate(() => { const b = document.getElementById("maksa"); return b ? b.innerText + (b.disabled ? " (ei vielä käytössä)" : "") : "?"; });
console.log(`::notice title=Napautukset etusivulta maksuun::${napautukset + 1} napautusta (maksunappi: ${maksuNappi}), joista 6 on yhteystietokenttiä`);
await p.screenshot({ path: "out/polku-maksuvaihe.png" });
console.log(`::notice title=Ongelmia::${ongelmat.length}`);
for (const o of ongelmat) console.log(`::warning title=Ongelma::${o}`);
for (const v of [...new Set(virheet)].slice(0, 15)) console.log(`::warning title=Virhe::${v}`);
await p.screenshot({ path: "out/kartta-ohjaimet.png" });
await b.close();
