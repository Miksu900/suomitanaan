// Tarkistaa netvo.fi:n Google-tagin ja konversioiden laukeamisen oikeassa selaimessa.
import { chromium } from "playwright";
const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 390, height: 800 } })).newPage();
const pyynnot = [];
p.on("request", r => { const u = r.url(); if (/googletagmanager|googleadservices|google\.com\/(pagead|ccm|rmkt)|doubleclick/.test(u)) pyynnot.push(u.slice(0, 160)); });
await p.goto("https://netvo.fi/", { waitUntil: "networkidle" });
const ennen = pyynnot.length;
console.log("::notice title=Sivun lataus::" + ennen + " Google-pyyntöä: " + pyynnot.map(u => u.split("?")[0]).join(" | ").slice(0, 900));
const nappi = await p.$('button[data-v="ok"]');
console.log("::notice title=Evästebanneri::" + (nappi ? "löytyi, hyväksytään" : "ei näkyvissä"));
if (nappi) await nappi.click();
await p.waitForTimeout(1500);
await p.evaluate(() => { document.addEventListener("click", e => { const a = e.target.closest && e.target.closest('a[href^="tel:"]'); if (a) e.preventDefault(); }, true); });
const tel = await p.$('a[href^="tel:"]');
console.log("::notice title=Puhelinlinkki::" + (tel ? "löytyi" : "EI LÖYTYNYT"));
if (tel) { await tel.click(); await p.waitForTimeout(3000); }
const konv = pyynnot.slice(ennen).filter(u => /conversion|pagead|ccm/.test(u));
console.log("::notice title=Konversio::" + (konv.length ? "LAUKESI: " + konv.join(" | ").slice(0, 900) : "ei konversiopyyntöä"));
await b.close();
