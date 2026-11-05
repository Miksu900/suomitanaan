// Omalahja: live-kuvakaappaukset (puhelin 390 ja työpöytä 1280) suunnittelijoista ja etusivusta.
import { chromium, devices } from "playwright";
const P = "https://omalahja.fi";
const b = await chromium.launch();
async function sivu(polku, mob) {
  const ctx = await b.newContext(mob ? { ...devices["Pixel 7"], viewport: { width: 390, height: 900 }, deviceScaleFactor: 2 } : { viewport: { width: 1280, height: 800 } });
  const p = await ctx.newPage(); await p.addInitScript(() => { try { localStorage.clear(); } catch {} });
  await p.goto(P + polku + (polku.includes("?") ? "&" : "?") + "v=" + Date.now(), { waitUntil: "load", timeout: 90000 });
  await p.waitForFunction(() => !window.OLTesti || document.body.dataset.malli !== "kartta" || window.OLTesti.kartta(), null, { timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(1800); return p;
}
const kuva = async (p, n, koko = false) => { await p.screenshot({ path: `out/${n}.png`, fullPage: koko }); console.log(`::notice title=${n}::leveys ${await p.evaluate(() => document.documentElement.scrollWidth)}`); };
let p;
p = await sivu("/tee/", true); await kuva(p, "v3-valitsin-390", true); await p.context().close();
p = await sivu("/tee/nimijuliste/", true); await kuva(p, "v3-nimi-390");
await p.locator("summary", { hasText: "Muokkaa tyyliä" }).tap(); await p.waitForTimeout(400); await p.locator('[data-ryhma="asettelu"]').scrollIntoViewIfNeeded(); await p.waitForTimeout(400); await kuva(p, "v3-nimi-390-tyyli");
await p.locator("#jatka").tap(); await p.waitForTimeout(1500); await kuva(p, "v3-nimi-390-tilaus"); await p.context().close();
p = await sivu("/tee/nimijuliste/?esim=haat&tuote=kehys", false); await kuva(p, "v3-nimi-1280"); await p.context().close();
p = await sivu("/tee/kartta/", true); await kuva(p, "v3-kartta-390-helsinki"); await p.context().close();
p = await sivu("/tee/kartta/?esim=betlehem", false); await kuva(p, "v3-kartta-1280-betlehem"); await p.context().close();
p = await sivu("/tee/kartta/?esim=ylivieska&tuote=akryyli", true); await kuva(p, "v4-kartta-390-akryyli"); await p.context().close();
p = await sivu("/tee/nimijuliste/?esim=perhe&tuote=muki", true); await kuva(p, "v4-muki-390"); await p.context().close();
p = await sivu("/tee/nimijuliste/?esim=joulu&tuote=kortit", true); await kuva(p, "v4-kortit-390"); await p.context().close();
p = await sivu("/tee/kartta/?esim=helsinki&tuote=kalenteri", false); await kuva(p, "v4-kalenteri-1280"); await p.context().close();
p = await sivu("/tee/nimijuliste/?esim=jae&tuote=ripustin", false); await kuva(p, "v4-ripustin-1280"); await p.context().close();
p = await sivu("/", true); await kuva(p, "v4-etusivu-390-koko", true); await p.context().close();
await b.close();
