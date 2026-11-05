// Netvo Oppaat -kauppa (netvo.fi/oppaat): Visma Pay -maksu, PDF-oppaiden toimitus R2:sta (VIDEOT-säiliö, avain oppaat/<id>.pdf).
// Tilaukset tallennetaan R2:een (kauppa/tilaukset/<tilausnumero>.json). Myyjä: Taksiliikenne Koskela Oy (Netvo).

export const TUOTTEET = {
  "01": { nimi: "Nettisivut – tee itse tekoälyn avulla", hinta: 1900 },
  "02": { nimi: "Verkkokauppa – perusta oma kauppa", hinta: 1900 },
  "03": { nimi: "Puhelinsovellus – oma sovellus ilman koodaamista", hinta: 2400 },
  "04": { nimi: "Domain ja sähköposti", hinta: 1900 },
  "05": { nimi: "Digituotteiden myynti", hinta: 1900 },
  "06": { nimi: "Itsestään päivittyvä sivusto", hinta: 1900 },
  "07": { nimi: "Tekoälyvideot", hinta: 1900 },
  "08": { nimi: "Somemarkkinointi", hinta: 1900 },
  "kaikki": { nimi: "Kaikki 8 opasta", hinta: 4900, sisalto: ["01", "02", "03", "04", "05", "06", "07", "08"] },
};
const VP = "https://www.vismapay.com/pbwapi";
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const hex = (b) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
async function hmac(avain, viesti) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(avain), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(viesti))).toUpperCase();
}
const satunnainen = (n = 24) => hex(crypto.getRandomValues(new Uint8Array(n)));
const tiedostot = (t) => (TUOTTEET[t].sisalto || [t]).map((id) => ({ id, nimi: TUOTTEET[id].nimi }));
const lue = async (env, nro) => { const o = await env.VIDEOT.get(`kauppa/tilaukset/${nro}.json`); return o ? o.json() : null; };
const tallenna = (env, t) => env.VIDEOT.put(`kauppa/tilaukset/${t.nro}.json`, JSON.stringify(t));

async function lahetaLinkki(env, t) {
  if (!env.BREVO_API_KEY) return;
  const url = `https://netvo.fi/oppaat/kiitos/?t=${t.avain}`;
  const lista = tiedostot(t.tuote).map((x) => "- " + x.nimi).join("\n");
  const teksti = `Hei,\n\nkiitos tilauksestasi! Oppaasi ovat ladattavissa tästä linkistä 60 päivän ajan:\n${url}\n\nTilaus ${t.nro}:\n${lista}\nYhteensä ${(t.summa / 100).toFixed(2).replace(".", ",")} € (sis. alv 25,5 %)\n\nJos tarvitset apua, vastaa tähän viestiin.\n\nNetvo – netvo.fi\nTaksiliikenne Koskela Oy (Y-tunnus 3425681-3)\ninfo@netvo.fi`;
  await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST", headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json" },
    body: JSON.stringify({ sender: { email: "info@netvo.fi", name: "Netvo" }, replyTo: { email: "info@netvo.fi" }, to: [{ email: t.email }], bcc: [{ email: "info@netvo.fi" }],
      subject: `Tilausvahvistus ${t.nro} – Netvo Oppaat`, textContent: teksti }) });
}
async function ilmoitaTelegram(env, t) {
  if (!env.TELEGRAM_BOT_TOKEN) return;
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TG_CHAT || "1893930799", text: `💶 Netvo Oppaat: myynti ${(t.summa / 100).toFixed(2)} € – ${TUOTTEET[t.tuote].nimi} (${t.nro})` }) });
}

// Paluu- ja ilmoitusosoitteen tarkistus: AUTHCODE = HMAC(yksityinen avain, RETURN_CODE|ORDER_NUMBER[|SETTLED][|CONTACT_ID][|INCIDENT_ID])
async function kasittelePaluu(env, p) {
  const osat = ["RETURN_CODE", "ORDER_NUMBER", "SETTLED", "CONTACT_ID", "INCIDENT_ID"].filter((k) => p.has(k)).map((k) => p.get(k));
  if (!p.get("AUTHCODE") || (await hmac(env.VISMAPAY_PRIVATE_KEY, osat.join("|"))) !== p.get("AUTHCODE").toUpperCase()) return { virhe: "tarkiste" };
  const t = await lue(env, p.get("ORDER_NUMBER"));
  if (!t) return { virhe: "tilaus" };
  if (p.get("RETURN_CODE") === "0" && t.tila !== "maksettu") {
    t.tila = "maksettu"; t.maksettu = new Date().toISOString(); await tallenna(env, t);
    await Promise.allSettled([lahetaLinkki(env, t), ilmoitaTelegram(env, t)]);
  }
  return { t, ok: p.get("RETURN_CODE") === "0" };
}

export async function kauppa(req, env, u) {
  if (!env.VIDEOT) return json({ virhe: "Kauppa ei ole käytössä." }, 503);
  const p = u.pathname.replace("/api/kauppa/", "");
  const vp = !!(env.VISMAPAY_API_KEY && env.VISMAPAY_PRIVATE_KEY);

  if (p === "maksutavat") {
    if (!vp) return json({ tavat: [] });
    const v = await fetch(`${VP}/merchant_payment_methods`, { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ version: "2", api_key: env.VISMAPAY_API_KEY, currency: "EUR", authcode: await hmac(env.VISMAPAY_PRIVATE_KEY, env.VISMAPAY_API_KEY) }) }).then((r) => r.json()).catch(() => ({}));
    const tavat = (v.payment_methods || []).map((m) => ({ nimi: m.name, kuva: m.img, ryhma: m.group }));
    return new Response(JSON.stringify({ tavat }), { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=3600" } });
  }

  if (p === "osto" && req.method === "POST") {
    if (!vp) return json({ virhe: "Maksaminen avautuu pian." }, 503);
    const d = await req.json().catch(() => ({}));
    const email = String(d.email || "").trim().toLowerCase();
    if (!TUOTTEET[d.tuote]) return json({ virhe: "Tuntematon tuote." }, 400);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 120) return json({ virhe: "Tarkista sähköpostiosoite." }, 400);
    if (!d.hyvaksy) return json({ virhe: "Hyväksy toimitusehdot ja välitön toimitus." }, 400);
    const nro = "NV" + Date.now().toString(36).toUpperCase() + satunnainen(3).toUpperCase();
    const t = { nro, tuote: d.tuote, email, summa: TUOTTEET[d.tuote].hinta, tila: "odottaa", luotu: new Date().toISOString(), avain: satunnainen(), lataukset: 0 };
    await tallenna(env, t); await env.VIDEOT.put("kauppa/avaimet/" + t.avain, nro);
    const vastaus = await fetch(`${VP}/auth_payment`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
      version: "w3.1", api_key: env.VISMAPAY_API_KEY, order_number: nro, amount: t.summa, currency: "EUR", email,
      authcode: await hmac(env.VISMAPAY_PRIVATE_KEY, `${env.VISMAPAY_API_KEY}|${nro}`),
      payment_method: { type: "e-payment", return_url: "https://netvo.fi/api/kauppa/paluu", notify_url: "https://netvo.fi/api/kauppa/ilmoitus", lang: "fi" },
      customer: { email },
      products: [{ id: d.tuote, title: TUOTTEET[d.tuote].nimi, count: 1, pretax_price: Math.round(t.summa / 1.255), tax: 25.5, price: t.summa, type: 1 }],
    }) }).then((r) => r.json()).catch((e) => ({ result: -1, virhe: String(e) }));
    if (vastaus.result !== 0 || !vastaus.token) { console.log("Visma Pay auth_payment", JSON.stringify(vastaus)); return json({ virhe: "Maksun aloitus epäonnistui. Yritä hetken päästä uudelleen." }, 502); }
    return json({ url: `${VP}/token/${vastaus.token}` });
  }

  if (p === "paluu") {
    const r = await kasittelePaluu(env, u.searchParams);
    if (r.ok) return Response.redirect(`https://netvo.fi/oppaat/kiitos/?t=${r.t.avain}`, 302);
    return Response.redirect("https://netvo.fi/oppaat/?maksu=peruttu", 302);
  }
  if (p === "ilmoitus") { await kasittelePaluu(env, u.searchParams); return new Response("OK"); }

  if (p === "tilaus" || p === "lataa") {
    const avain = u.searchParams.get("t") || "";
    if (!/^[0-9a-f]{48}$/.test(avain)) return json({ virhe: "Virheellinen linkki." }, 400);
    const ao = await env.VIDEOT.get("kauppa/avaimet/" + avain); const nro = ao ? await ao.text() : null;
    const t = nro && (await lue(env, nro));
    if (!t) return json({ virhe: "Tilausta ei löytynyt." }, 404);
    if (t.tila !== "maksettu") return json({ tila: t.tila, virhe: "Maksua ei ole vielä vahvistettu. Päivitä sivu hetken päästä." }, 409);
    if (Date.now() - Date.parse(t.maksettu) > 60 * 86400e3) return json({ virhe: "Latauslinkki on vanhentunut. Ota yhteyttä info@netvo.fi." }, 410);
    if (p === "tilaus") return json({ nro: t.nro, tuote: TUOTTEET[t.tuote].nimi, tiedostot: tiedostot(t.tuote).map((x) => ({ ...x, url: `/api/kauppa/lataa?t=${avain}&f=${x.id}` })) });
    const f = u.searchParams.get("f");
    if (!tiedostot(t.tuote).some((x) => x.id === f)) return json({ virhe: "Tiedostoa ei kuulu tilaukseen." }, 403);
    if (t.lataukset >= 50) return json({ virhe: "Latausraja täynnä. Ota yhteyttä info@netvo.fi." }, 429);
    const o = await env.VIDEOT.get(`oppaat/${f}.pdf`);
    if (!o) return json({ virhe: "Tiedosto puuttuu. Lähetämme sen sähköpostilla – ota yhteyttä info@netvo.fi." }, 404);
    t.lataukset++; await tallenna(env, t);
    return new Response(o.body, { headers: { "content-type": "application/pdf", "content-disposition": `attachment; filename="Netvo-opas-${f}.pdf"`, "cache-control": "no-store" } });
  }
  return json({ virhe: "Ei löytynyt." }, 404);
}
