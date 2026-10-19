// Toimittajan muokkaus ja julkaisu komentoriviltä: lukee toimitus/muutos.json, etsii luonnoksen otsikolla,
// lisää kappaleen ja lähteen ja julkaisee sen (sama kuin Julkaise-nappi toimitussivulla).
import fs from "node:fs";
const URL = process.env.WORKER_URL, PW = process.env.TOIMITUS_SALASANA;
const m = JSON.parse(fs.readFileSync("toimitus/muutos.json", "utf8"));
const api = async (p, b) => { const r = await fetch(URL + p, { method: b ? "POST" : "GET", headers: { authorization: "Bearer " + PW, "content-type": "application/json" }, body: b ? JSON.stringify(b) : undefined }); return r.json(); };
const luonn = await api("/api/luonnokset");
const x = luonn.find(l => (l.otsikko || "").toLowerCase().includes(m.etsi.toLowerCase()));
if (!x) { console.log(`::error::Luonnosta ei löytynyt (${luonn.length} luonnosta)`); process.exit(1); }
const teksti = (x.teksti || "").trim() + (m.lisaa_kappale ? "\n\n" + m.lisaa_kappale.trim() : "");
const lahteet = [...(x.lahteet || []), ...(m.lisaa_lahde ? [m.lisaa_lahde] : [])];
const r = await api("/api/julkaise", { id: x.id, tyyppi: "uutinen", otsikko: m.otsikko || x.otsikko, ingressi: m.ingressi || x.ingressi, teksti, kategoria: x.kategoria, lahteet, tiktok: x.tiktok || null });
console.log(r.ok ? `::notice title=Julkaistu::${URL}/uutiset/${r.slug}/` : `::error::Julkaisu epäonnistui ${JSON.stringify(r)}`);
if (!r.ok) process.exit(1);
