// Omalahja: karttasuunnittelijan testi oikealla sivulla mobiiliemulaatiolla (Pixel 7). Mittaa karttojen latausajat,
// kirjaa konsolivirheet ja karttapyynnöt (Overpass/Nominatim/oma rajapinta) ja ottaa kuvakaappaukset out/-kansioon.
import { chromium, devices } from "playwright";
const POHJA = process.env.POHJA || "https://omalahja.fi";
const TAPAUKSET = [
  { nimi: "helsinki-oletus", polku: "/tee/kartta/" },
  { nimi: "ylivieska", polku: "/tee/kartta/?esim=ylivieska" },
  { nimi: "betlehem", polku: "/tee/kartta/?esim=betlehem" },
  { nimi: "haku-kuopio", polku: "/tee/kartta/", haku: "Kuopio" },
];
const b = await chromium.launch();
const tulokset = [];
for (const t of TAPAUKSET) {
  const ctx = await b.newContext({ ...devices["Pixel 7"], locale: "fi-FI" });
  const p = await ctx.newPage();
  const loki = [];
  p.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") loki.push(`konsoli ${m.type()}: ${m.text().slice(0, 200)}`); });
  p.on("pageerror", (e) => loki.push("sivuvirhe: " + e.message.slice(0, 200)));
  const alku = new Map();
  p.on("request", (r) => { if (/overpass|nominatim|mail\.ru|\/api\/kartta/.test(r.url())) alku.set(r, Date.now()); });
  p.on("requestfinished", async (r) => { if (!alku.has(r)) return; const v = await r.response(); let koko = 0; try { koko = (await v.body()).length; } catch {}
    loki.push(`pyyntö ${r.method()} ${r.url().slice(0, 110)} -> ${v ? v.status() : "?"} ${koko} t ${Date.now() - alku.get(r)} ms`); });
  p.on("requestfailed", (r) => { if (alku.has(r)) loki.push(`EPÄONNISTUI ${r.url().slice(0, 110)} ${r.failure()?.errorText} ${Date.now() - alku.get(r)} ms`); });
  await p.addInitScript(() => { try { localStorage.clear(); } catch {} });
  const t0 = Date.now();
  await p.goto(POHJA + t.polku + (t.polku.includes("?") ? "&" : "?") + "v=" + Date.now(), { waitUntil: "domcontentloaded", timeout: 60000 });
  let h0 = t0;
  if (t.haku) {
    await p.waitForFunction(() => window.OLTesti && window.OLTesti.kartta(), null, { timeout: 90000 }).catch(() => {});
    await p.fill("#haku", t.haku); h0 = Date.now(); await p.click(".hakurivi button");
    await p.waitForSelector(".tulos", { timeout: 20000 }).catch(() => loki.push("hakutuloksia ei tullut"));
    loki.push(`haku ${Date.now() - h0} ms`);
    h0 = Date.now(); await p.click(".tulos").catch(() => {});
    await p.waitForTimeout(300);
  }
  let ok = true;
  try {
    await p.waitForFunction((ots) => { const k = window.OLTesti && window.OLTesti.kartta(); const l = document.getElementById("lataus");
      return k && (!l || l.hidden) && (!ots || Math.abs(k.lat - window.OLTesti.S.lat) < 0.2); }, t.haku ? true : null, { timeout: 90000, polling: 250 });
  } catch { ok = false; }
  const ms = Date.now() - h0;
  const tila = await p.evaluate(() => ({ teksti: document.getElementById("lataus")?.innerText || "", tiet: window.OLTesti?.kartta()?.tiet?.length || 0 }));
  await p.waitForTimeout(400);
  await p.screenshot({ path: `out/kartta-${t.nimi}.png` });
  tulokset.push({ nimi: t.nimi, ok, ms, ...tila });
  console.log(`::notice title=${t.nimi}::${ok ? "OK" : "EI LATAUTUNUT"} ${ms} ms, teitä ${tila.tiet}, tila "${tila.teksti}"`);
  for (const r of loki.slice(0, 12)) console.log(`::notice title=${t.nimi} loki::${r}`);
  await ctx.close();
}
await b.close();
console.log(JSON.stringify(tulokset));
