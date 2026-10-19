// Toimittajan muokkaus ja julkaisu komentoriviltä: lukee toimitus/muutos.json, etsii luonnoksen otsikolla,
// lisää kappaleen ja lähteen ja julkaisee sen (sama kuin Julkaise-nappi toimitussivulla).
import fs from "node:fs";
const URL = process.env.WORKER_URL, PW = process.env.TOIMITUS_SALASANA;
const m = JSON.parse(fs.readFileSync("toimitus/muutos.json", "utf8"));
const api = async (p, b) => { const r = await fetch(URL + p, { method: b ? "POST" : "GET", headers: { authorization: "Bearer " + PW, "content-type": "application/json" }, body: b ? JSON.stringify(b) : undefined }); return r.json(); };
const luonn = await api("/api/luonnokset");
const x = luonn.find(l => (l.otsikko || "").toLowerCase().includes(m.etsi.toLowerCase()));
if (!x) { console.log(`::error::Luonnosta ei löytynyt (${luonn.length} luonnosta)`); process.exit(1); }
if (m.vain_nayta) { fs.mkdirSync("out", { recursive: true }); fs.writeFileSync("out/luonnos.json", JSON.stringify(x, null, 2));
  console.log("::notice title=Luonnos::" + x.id + " " + (x.lahteet || []).map(l => l.url).join(" ")); process.exit(0); }
const teksti = (m.korvaa_teksti || x.teksti || "").trim() + (m.lisaa_kappale ? "\n\n" + m.lisaa_kappale.trim() : "");
const lahteet = [...(x.lahteet || []), ...(m.lisaa_lahde ? [m.lisaa_lahde] : [])];
if (m.vain_luonnos) {  // päivitä luonnos jonoon julkaisematta
  const r2 = await api("/api/luonnokset", { ...x, teksti, lahteet, tarkistettavat: m.tarkistettavat ?? x.tarkistettavat });
  console.log(r2.ok ? `::notice title=Luonnos päivitetty::${x.otsikko}` : `::error::${JSON.stringify(r2)}`); process.exit(r2.ok ? 0 : 1);
}
const r = await api("/api/julkaise", { id: x.id, tyyppi: "uutinen", otsikko: m.otsikko || x.otsikko, ingressi: m.ingressi || x.ingressi, teksti, kategoria: x.kategoria, lahteet, tiktok: x.tiktok || null });
console.log(r.ok ? `::notice title=Julkaistu::${URL}/uutiset/${r.slug}/` : `::error::Julkaisu epäonnistui ${JSON.stringify(r)}`);
if (!r.ok) process.exit(1);
