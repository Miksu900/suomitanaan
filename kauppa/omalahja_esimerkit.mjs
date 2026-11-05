// Renderöi Omalahjan esimerkkituotteet live-suunnittelijalla (out/<nimi>.jpg, ~1000 px, < 200 kt).
// Karttapalveluja kohtuudella: 4 karttaa, tauko välissä.
import { chromium } from "playwright";
import sharp from "sharp";
import fs from "fs";
const LISTA = [["nimi", "perhe"], ["nimi", "vauva"], ["nimi", "haat"], ["nimi", "jae"], ["nimi", "joulu"], ["nimi", "muisto"], ["nimi", "kaste"],
  ["kartta", "helsinki"], ["kartta", "ylivieska"], ["kartta", "betlehem"], ["kartta", "tampere"]];
const b = await chromium.launch();
for (const [malli, id] of LISTA) {
  const p = await b.newPage({ viewport: { width: 1200, height: 900 } });
  p.on("pageerror", (e) => console.log("VIRHE", id, e.message));
  await p.addInitScript(() => { try { localStorage.clear(); } catch {} });
  const polku = malli === "nimi" ? "nimijuliste" : "kartta";
  await p.goto(`https://omalahja.fi/tee/${polku}/?esim=${id}&v=${Date.now()}`, { waitUntil: "networkidle" });
  await p.waitForTimeout(1500);
  let d = null;
  for (let yritys = 0; yritys < 3 && !d; yritys++) {
    try { d = await p.evaluate(() => window.OLTesti.esikuva(1000, 0.92)); } catch (e) { console.log("yritys", id, e.message); await p.waitForTimeout(20000); }
  }
  if (d) {
    const buf = Buffer.from(d.split(",")[1], "base64");
    let q = 82, out;
    do { out = await sharp(buf).jpeg({ quality: q, mozjpeg: true }).toBuffer(); q -= 6; } while (out.length > 195000 && q > 40);
    fs.writeFileSync(`out/${malli}-${id}.jpg`, out);
    console.log(`::notice title=${malli}-${id}::${out.length} tavua, laatu ${q + 6}`);
  } else console.log(`::warning title=${id}::ei kuvaa`);
  await p.close();
  if (malli === "kartta") await new Promise((r) => setTimeout(r, 8000));
}
await b.close();
