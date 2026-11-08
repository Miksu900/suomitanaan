// Mobiilikuvat faktapiste.fi/islam/ -sivun tekoälyavustajasta (390 px, Android Chrome -tyyppinen). Tallentaa out/-kansioon.
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const laite = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
    userAgent: "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36" };
  // Tumma tila, pelkkä yläosa
  const t = await b.newPage({ ...laite, colorScheme: "dark" });
  await t.goto("https://faktapiste.fi/islam/?v=" + Date.now(), { waitUntil: "networkidle" });
  await t.waitForTimeout(800); await t.screenshot({ path: "out/1-yla-tumma.png" }); await t.close();

  const p = await b.newPage({ ...laite, colorScheme: "light" });
  p.on("console", m => { if (m.type() === "error") console.log("KONSOLI:", m.text()); });
  await p.goto("https://faktapiste.fi/islam/?oma=" + (process.env.OMA || "") + "&v=" + Date.now(), { waitUntil: "networkidle" });
  await p.waitForTimeout(800);
  await p.screenshot({ path: "out/2-yla.png" });
  console.log("::notice title=Vaakavieritys::" + await p.evaluate(() => document.documentElement.scrollWidth) + " px, URL " + p.url().replace(/oma=[^&]*/, "oma=***"));
  const kysymys = process.env.KYSYMYS || "Montako moskeijaa Suomessa on suunnitteilla?";
  await p.fill("#ai-kentta", kysymys);
  await p.click("#ai-laheta");
  const alku = Date.now();
  await p.waitForTimeout(9000);
  await p.screenshot({ path: "out/3-tutkii.png" });
  await p.evaluate(() => document.querySelector(".tila")?.setAttribute("open", ""));
  await p.waitForTimeout(25000);
  await p.screenshot({ path: "out/3b-tutkii-hakulista.png" });
  let kirjoittaa = false;
  while (Date.now() - alku < 420e3) {
    await p.waitForTimeout(3000);
    const tila = await p.evaluate(() => ({ nappi: document.getElementById("ai-laheta").textContent, teksti: (document.querySelector(".vas .md")?.textContent || "").length }));
    if (!kirjoittaa && tila.teksti > 600) { kirjoittaa = true; await p.screenshot({ path: "out/4-kirjoittaa.png" }); }
    if (tila.nappi === "Kysy") break;
  }
  console.log("::notice title=Vastausaika::" + Math.round((Date.now() - alku) / 1000) + " s");
  await p.evaluate(() => document.querySelector(".vas")?.scrollIntoView({ block: "start" }));
  await p.waitForTimeout(500);
  await p.screenshot({ path: "out/5-vastaus-alku.png" });
  await p.evaluate(() => { const t = document.querySelector(".vas .toim"); t && t.scrollIntoView({ block: "end" }); });
  await p.waitForTimeout(500);
  await p.screenshot({ path: "out/6-vastaus-loppu.png" });
  const ai = await p.$("#kysy");
  await ai.screenshot({ path: "out/7-koko-keskustelu.jpg", type: "jpeg", quality: 75 });
  console.log("::notice title=Vaakavieritys lopussa::" + await p.evaluate(() => document.documentElement.scrollWidth) + " px");
  console.log("VASTAUS:\n" + await p.evaluate(() => document.querySelector(".vas .md")?.innerText || ""));
  await b.close();
})();
