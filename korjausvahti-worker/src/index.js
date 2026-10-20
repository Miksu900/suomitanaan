// Korjausvahdin sinetöijä (Cloudflare Worker, ajastus 5 min välein).
// Hakee nytpuhutaan.fi:n muutokset.json:n ja sinetöi Sepoliaan:
//  1) tilannekuvan, jos uusia otsikkomuutoksia on tullut (hiljaisina hetkinä ei mitään),
//  2) päättyneen päivän koko listan kerran.
// Sormenjälki: [linkki, ennen, nyt, havaintoaika] aikajärjestyksessä, tiivis JSON, SHA-256.
import { ethers } from "ethers";

const ABI = [
  "function sinetoi(bytes32 sormenjalki, string selite)",
  "function tarkista(bytes32 sormenjalki) view returns (bool loytyi, uint64 aika, string selite)",
  "function omistaja() view returns (address)",
];
const hkiPaiva = (iso) => new Date(iso).toLocaleDateString("sv-SE", { timeZone: "Europe/Helsinki" });

async function sha256hex(teksti) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(teksti));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
async function tiiviste(lista) {
  const rivit = lista.slice().sort((a, b) => (a.t < b.t ? -1 : a.t > b.t ? 1 : a.l < b.l ? -1 : a.l > b.l ? 1 : 0)).map((m) => [m.l, m.vanha, m.uusi, m.t]);
  return sha256hex(JSON.stringify(rivit));
}

async function aja(env) {
  const loki = [];
  if (!env.SINETOIJA_KEY || !env.SOPIMUS) return ["avain tai sopimus puuttuu"];
  const r = await fetch(env.DATA_URL + "?t=" + Date.now(), { cf: { cacheTtl: 0 } });
  if (!r.ok) return [`muutokset.json ${r.status}`];
  const data = await r.json();
  const kaikki = data.m || [];
  if (!kaikki.length) return ["ei muutoksia"];
  const rpc = new ethers.JsonRpcProvider(env.RPC || "https://ethereum-sepolia-rpc.publicnode.com", undefined, { staticNetwork: true });
  const lompakko = new ethers.Wallet(env.SINETOIJA_KEY, rpc);
  const sop = new ethers.Contract(env.SOPIMUS, ABI, lompakko);
  const laheta = async (h, selite) => {
    const [loytyi] = await sop.tarkista("0x" + h);
    if (loytyi) return null;
    const tx = await sop.sinetoi("0x" + h, selite);
    return tx.hash;   // ei odoteta vahvistusta: seuraava ajo näkee tilan ketjusta
  };

  // 1) Tilannekuva: 48 h ikkuna uusimpaan havaintoon asti
  const loppu = kaikki.reduce((a, m) => (m.t > a ? m.t : a), "");
  const viimeisin = await env.DB.get("tilannekuva");
  if (loppu !== viimeisin) {
    const alku = new Date(new Date(loppu).getTime() - 48 * 3600e3).toISOString().slice(0, 19);
    const ikkuna = kaikki.filter((m) => m.t > alku && m.t <= loppu);
    const h = await tiiviste(ikkuna);
    const tx = await laheta(h, `nytpuhutaan.fi tilannekuva: muutokset t > ${alku} ja t <= ${loppu} (${ikkuna.length} kpl)`);
    await env.DB.put("tilannekuva", loppu);
    loki.push(`tilannekuva ${ikkuna.length} kpl ${tx || "(jo ketjussa)"}`);
  }
  // 2) Päättyneet päivät
  const tanaan = hkiPaiva(new Date().toISOString());
  const paivat = {};
  for (const m of kaikki) (paivat[hkiPaiva(m.t)] ||= []).push(m);
  for (const p of Object.keys(paivat).sort()) {
    if (p >= tanaan || (await env.DB.get("paiva:" + p))) continue;
    const h = await tiiviste(paivat[p]);
    const tx = await laheta(h, `nytpuhutaan.fi muutetut otsikot ${p} (${paivat[p].length} kpl)`);
    await env.DB.put("paiva:" + p, JSON.stringify({ sha256: h, kpl: paivat[p].length, tx }));
    loki.push(`päivä ${p}: ${paivat[p].length} kpl ${tx || "(jo ketjussa)"}`);
    break;   // yksi päivä per ajo, ettei tapahtumat mene päällekkäin
  }
  await env.DB.put("viimeksi", JSON.stringify({ aika: new Date().toISOString(), loki }));
  return loki.length ? loki : ["ei uusia muutoksia"];
}

export default {
  async scheduled(_e, env, ctx) { ctx.waitUntil(aja(env).catch((e) => env.DB.put("virhe", String(e?.shortMessage || e?.message || e).slice(0, 500)))); },
  async fetch(req, env) {
    // Julkinen tila: lompakon osoite, saldo ja viimeisin ajo (ei salaisuuksia)
    const u = new URL(req.url);
    let osoite = null, saldo = null;
    if (env.SINETOIJA_KEY) {
      osoite = new ethers.Wallet(env.SINETOIJA_KEY).address;
      try { saldo = ethers.formatEther(await new ethers.JsonRpcProvider(env.RPC || "https://ethereum-sepolia-rpc.publicnode.com", undefined, { staticNetwork: true }).getBalance(osoite)); } catch {}
    }
    if (u.pathname === "/aja" && u.searchParams.get("k") === env.AJO_AVAIN) return Response.json({ loki: await aja(env).catch((e) => [String(e?.shortMessage || e?.message || e)]) });
    return Response.json({ palvelu: "Korjausvahdin sinetöijä", osoite, saldo, sopimus: env.SOPIMUS || null,
      viimeksi: JSON.parse((await env.DB.get("viimeksi")) || "null"), virhe: await env.DB.get("virhe") });
  },
};
