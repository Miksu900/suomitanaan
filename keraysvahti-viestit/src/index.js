// Keräysvahti: nimettömät huijauskertomukset. Viesti tallennetaan Cloudflare KV:hen (12 kk) ja
// lähetetään ylläpitäjän sähköpostiin. IP-osoitetta ei tallenneta: siitä lasketaan vain päivittäin
// vaihtuvalla suolalla tiiviste, jota käytetään tunnin ajan roskapostin rajoittamiseen.
const SALLITUT = ["https://keraysvahti.fi", "https://www.keraysvahti.fi", "http://localhost:8765"];
const TYYPIT = ["Valekerääjä", "Puhelu", "Tekstiviesti tai sähköposti", "Some tai nettikauppa", "Sijoitus tai krypto", "Romanssi", "Muu"];
const cors = (o) => ({ "Access-Control-Allow-Origin": SALLITUT.includes(o) ? o : SALLITUT[0], "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "content-type", "Vary": "Origin" });
const vastaus = (o, data, status = 200) => new Response(JSON.stringify(data), { status, headers: { ...cors(o), "content-type": "application/json" } });
const e = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function tiiviste(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].slice(0, 12).map((x) => x.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(req, env) {
    const o = req.headers.get("Origin") || "";
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(o) });
    if (req.method === "GET" && url.pathname === "/") return vastaus(o, { palvelu: "Keräysvahti: nimettömät huijauskertomukset", ok: true });
    if (req.method !== "POST" || url.pathname !== "/viesti") return vastaus(o, { virhe: "Ei löydy" }, 404);
    if (!SALLITUT.includes(o)) return vastaus(o, { virhe: "Kielletty" }, 403);
    let b;
    try { b = await req.json(); } catch { return vastaus(o, { virhe: "Virheellinen pyyntö" }, 400); }
    // roskapostisuojat: piilokenttä, liian nopea lähetys, pituus
    if (b.hp) return vastaus(o, { ok: true });
    if (!(Number(b.kesto) >= 4)) return vastaus(o, { virhe: "Odota hetki ja yritä uudelleen." }, 429);
    const teksti = String(b.teksti || "").trim().slice(0, 4000);
    if (teksti.length < 20) return vastaus(o, { virhe: "Kirjoita vähintään pari lausetta." }, 400);
    const tyyppi = TYYPIT.includes(b.tyyppi) ? b.tyyppi : "Muu";
    const kunta = String(b.kunta || "").trim().slice(0, 60);
    const lupa = b.lupa === true;
    // rajoitus: enintään 5 viestiä tunnissa samasta osoitteesta (IP:tä ei tallenneta)
    const paiva = new Date().toISOString().slice(0, 10);
    const avain = "raja:" + (await tiiviste((req.headers.get("CF-Connecting-IP") || "") + paiva + (env.SUOLA || "kv")));
    const n = Number((await env.DB.get(avain)) || 0);
    if (n >= 5) return vastaus(o, { virhe: "Liian monta viestiä. Yritä myöhemmin uudelleen." }, 429);
    await env.DB.put(avain, String(n + 1), { expirationTtl: 3600 });
    const aika = new Date().toISOString();
    const id = aika.replace(/[-:.TZ]/g, "").slice(0, 14) + "-" + crypto.randomUUID().slice(0, 6);
    const viesti = { id, aika, tyyppi, kunta, teksti, lupa };
    await env.DB.put("viesti:" + id, JSON.stringify(viesti), { expirationTtl: 365 * 86400 });
    if (env.BREVO_API_KEY) {
      const html = `<div style="font:15px/1.55 system-ui,sans-serif;max-width:620px">
<p style="font:700 12px sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#1e6b4f">Keräysvahti · nimetön kertomus</p>
<p><b>Tyyppi:</b> ${e(tyyppi)}${kunta ? ` · <b>Paikkakunta:</b> ${e(kunta)}` : ""}</p>
<div style="white-space:pre-wrap;background:#f4f6f3;border-radius:10px;padding:12px 14px">${e(teksti)}</div>
<p style="padding:10px 12px;border-radius:10px;background:${lupa ? "#e1efe7" : "#fbebe2"}"><b>${lupa ? "Lupa käyttää nimettömänä varoituksissa ja mainonnassa: KYLLÄ" : "Ei lupaa käyttää julkisesti – vain tiedoksi"}</b></p>
<p style="color:#5a6860;font-size:13px">Tunniste ${e(id)} · ${e(aika)}. Lähettäjästä ei tallennettu tunnistetietoja.</p></div>`;
      try {
        await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST",
          headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
          body: JSON.stringify({ sender: { email: env.LAHETTAJA || "miika@eduskuntaseuranta.fi", name: "Keräysvahti" },
            to: [{ email: env.VASTAANOTTAJA || "miika.koskela990@gmail.com" }],
            subject: `Keräysvahti: uusi huijauskertomus (${tyyppi})${lupa ? " – saa käyttää" : ""}`, htmlContent: html }) });
      } catch {}
    }
    return vastaus(o, { ok: true });
  },
};
