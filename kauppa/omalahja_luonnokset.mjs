// Omalahja: luo live-suunnittelijalla painotiedostot (muki, kortit, kalenteri, juliste), lataa ne ja testaa Gelato-LUONNOStilauksen
// Workerin kautta (/api/hallinta/luonnostesti poistaa luonnoksen heti). Ei oikeita tilauksia eikä maksuja.
import { chromium } from "playwright";
const AV = process.env.HALLINTA;
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 900 } });
await p.addInitScript(() => { try { localStorage.clear(); } catch {} });
await p.goto("https://omalahja.fi/tee/nimijuliste/?esim=joulu&v=" + Date.now(), { waitUntil: "load" }); await p.waitForTimeout(2500);
for (const [tuote, koko, vari] of [["muki", "11oz", "valkoinen"], ["kortit", "a6", ""], ["kalenteri", "a4", ""], ["ripustin", "30x40", "luonnonpuu"], ["puu", "30x40", ""], ["akryyli", "30x40", ""]]) {
  const tulos = await p.evaluate(async ([tuote, koko, vari, AV]) => {
    const S = window.OLTesti.S; S.tuote = tuote; S.koko = koko; if (vari) S.vari = vari; if (tuote === "kortit") S.sisa = "Siunattua joulua!"; window.OLTesti.paivita();
    const k = await window.OLTesti.painoKuva();
    const r1 = await fetch("/api/tiedosto", { method: "POST", headers: { "content-type": k.tyyppi }, body: k.blob }).then((r) => r.json());
    if (!r1.url) return { virhe: "lataus: " + JSON.stringify(r1) };
    const r2 = await fetch("/api/hallinta/luonnostesti", { method: "POST", headers: { "content-type": "application/json", "x-avain": AV }, body: JSON.stringify({ tuote, koko, vari, suunta: "pysty", tiedosto: r1.url }) }).then((r) => r.json());
    return { koko: Math.round(k.blob.size / 1024) + " kt", tyyppi: k.tyyppi, ...r2 };
  }, [tuote, koko, vari, AV]);
  console.log(`::notice title=Luonnos ${tuote}::${JSON.stringify(tulos).slice(0, 900)}`);
}
await b.close();
