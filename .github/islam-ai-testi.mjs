// Live-testi faktapiste.fi/api/islam/kysy -päätepisteelle: kysyy kysymykset, tulostaa vastaukset ja ajat lokiin ja out/-kansioon.
import { writeFileSync } from "node:fs";
const U = "https://faktapiste.fi/api/islam/kysy";
const KYS = (process.env.KYS || "").split("|").map(s => s.trim()).filter(Boolean);
const OLETUS = [
  ["Montako moskeijaa Suomeen on rakennettu, montako on rakenteilla tai suunnitteilla?", "Missä kaupungeissa suunnitteilla olevat hankkeet ovat ja mikä niiden tilanne on tällä hetkellä?"],
  ["Montako islamilaista säätiötä tai yhdistystä Suomessa on?"],
];
const ketjut = KYS.length ? KYS.map(k => k.split(">>").map(s => s.trim())) : OLETUS;

async function kysy(kysymys, historia, nimi) {
  const alku = Date.now(); let eka = null, ekaTeksti = null, teksti = "", loppu = null; const tapahtumat = [];
  const r = await fetch(U, { method: "POST", headers: { "content-type": "application/json", "x-oma": process.env.OMA || "" }, body: JSON.stringify({ kysymys, historia }) });
  if (!r.ok) { const t = await r.text(); return { virhe: r.status + " " + t, aika: (Date.now() - alku) / 1000 }; }
  const rd = r.body.pipeThrough(new TextDecoderStream()).getReader(); let pus = "";
  for (;;) {
    const { value, done } = await rd.read(); if (done) break;
    if (eka === null) eka = (Date.now() - alku) / 1000;
    pus += value; let i;
    while ((i = pus.indexOf("\n")) >= 0) {
      const l = pus.slice(0, i); pus = pus.slice(i + 1); if (!l.trim()) continue;
      const e = JSON.parse(l);
      if (e.t === "teksti") { if (ekaTeksti === null) ekaTeksti = (Date.now() - alku) / 1000; teksti += e.d; }
      else if (e.t === "loppu") loppu = e;
      else tapahtumat.push(`[${((Date.now() - alku) / 1000).toFixed(0)}s] ${e.t}: ${e.d || ""}`);
    }
  }
  return { aika: (Date.now() - alku) / 1000, eka, ekaTeksti, teksti, loppu, tapahtumat, nimi };
}

await Promise.all(ketjut.map(async (ketju, ki) => {
  const historia = []; let loki = "";
  for (const [qi, q] of ketju.entries()) {
    const v = await kysy(q, historia.slice(), `k${ki + 1}-${qi + 1}`);
    loki += `\n\n==================== KYSYMYS ${ki + 1}.${qi + 1}: ${q}\n`;
    loki += `aika ${v.aika?.toFixed(1)} s, ensimmäinen tapahtuma ${v.eka} s, ensimmäinen teksti ${v.ekaTeksti} s, ${JSON.stringify(v.loppu || v.virhe)}\n`;
    loki += (v.tapahtumat || []).join("\n") + "\n--------------------\n" + (v.teksti || "");
    historia.push({ rooli: "user", teksti: q }, { rooli: "assistant", teksti: v.teksti || "" });
  }
  writeFileSync(`out/ketju${ki + 1}.txt`, loki);
}));
for (let ki = 0; ki < ketjut.length; ki++) console.log((await import("node:fs")).readFileSync(`out/ketju${ki + 1}.txt`, "utf8"));
