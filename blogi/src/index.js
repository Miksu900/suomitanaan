// Miika Koskelan blogi: staattiset sivut (public/) + kävijälaskuri, jakolaskurit ja kommentit (SQLite Durable Object).
import { DurableObject } from "cloudflare:workers";

const BOTIT = /bot|crawl|spider|slurp|facebookexternalhit|preview|fetch|curl|wget|python|headless|lighthouse|monitor|scan/i;
const KANAVAT = ["facebook", "x", "whatsapp", "telegram", "linkki"];
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function tiiviste(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].slice(0, 12).map(x => x.toString(16).padStart(2, "0")).join("");
}
const pv = () => new Date(Date.now() + 2 * 3600e3).toISOString().slice(0, 10);

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.hostname.startsWith("www.")) return Response.redirect(`https://${u.hostname.slice(4)}${u.pathname}${u.search}`, 301);
    const oma = (req.headers.get("cookie") || "").includes("bk_oma=1");

    // Omistajan tunnistus: kerran avattava linkki, jonka jälkeen omia käyntejä ei lasketa
    if (u.pathname === "/oma") {
      if (!env.HALLINTA || u.searchParams.get("k") !== env.HALLINTA) return new Response("Väärä koodi", { status: 403 });
      return new Response(`<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><body style="font:18px system-ui;padding:30px">✅ Tämä laite on nyt merkitty omaksesi. Omia käyntejäsi ei lasketa kävijöihin.<p><a href="/">Blogin etusivulle</a></p>`,
        { headers: { "content-type": "text/html; charset=utf-8", "set-cookie": "bk_oma=1; Path=/; Max-Age=315360000; Secure; SameSite=Lax" } });
    }

    if (u.pathname.startsWith("/api/")) {
      const ip = req.headers.get("cf-connecting-ip") || "";
      const ua = req.headers.get("user-agent") || "";
      const stub = env.BLOGI.get(env.BLOGI.idFromName("blogi"));
      return stub.kasittele({
        polku: u.pathname, haku: Object.fromEntries(u.searchParams), metodi: req.method,
        runko: req.method === "POST" ? await req.text() : "", tunnus: await tiiviste(ip + "|" + ua + "|" + pv()),
        iptunnus: await tiiviste(ip + "|blogi"), botti: BOTIT.test(ua) || !ua, oma, isanta: u.origin
      });
    }
    return env.ASSETS.fetch(req);
  }
};

export class Blogi extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.env = env;
    this.sql = ctx.storage.sql;
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS kaynnit(pv TEXT, tunnus TEXT, polku TEXT, PRIMARY KEY(pv, tunnus, polku));
      CREATE TABLE IF NOT EXISTS jaot(polku TEXT, kanava TEXT, n INTEGER DEFAULT 0, PRIMARY KEY(polku, kanava));
      CREATE TABLE IF NOT EXISTS kommentit(id INTEGER PRIMARY KEY AUTOINCREMENT, polku TEXT, nimi TEXT, teksti TEXT, aika INTEGER, ip TEXT, piilotettu INTEGER DEFAULT 0);
      CREATE INDEX IF NOT EXISTS kommentit_polku ON kommentit(polku, aika);
    `);
  }

  rivit(q, ...a) { return [...this.sql.exec(q, ...a)]; }

  async kasittele(r) {
    const p = r.polku;
    const kirjoitus = (r.haku.polku || "").replace(/[^a-z0-9\-\/]/gi, "").slice(0, 120) || "/";

    if (p === "/api/kaynti" && r.metodi === "POST") {
      if (!r.botti && !r.oma) {
        this.sql.exec("INSERT OR IGNORE INTO kaynnit VALUES (?,?,?)", pv(), r.tunnus, kirjoitus);
        this.sql.exec("INSERT OR IGNORE INTO kaynnit VALUES (?,?,?)", pv(), r.tunnus, "*");
      }
      return json(this.tilastot(kirjoitus));
    }
    if (p === "/api/tilastot") return json(this.tilastot(kirjoitus));

    if (p === "/api/jaa" && r.metodi === "POST") {
      const k = (r.haku.kanava || "").toLowerCase();
      if (!KANAVAT.includes(k)) return json({ virhe: "kanava" }, 400);
      if (!r.botti) this.sql.exec("INSERT INTO jaot VALUES (?,?,1) ON CONFLICT(polku, kanava) DO UPDATE SET n = n + 1", kirjoitus, k);
      return json(this.tilastot(kirjoitus));
    }

    if (p === "/api/kommentit" && r.metodi === "GET") {
      return json({ kommentit: this.rivit("SELECT id, nimi, teksti, aika FROM kommentit WHERE polku = ? AND piilotettu = 0 ORDER BY aika ASC LIMIT 500", kirjoitus) });
    }
    if (p === "/api/kommentit" && r.metodi === "POST") {
      let d = {}; try { d = JSON.parse(r.runko); } catch {}
      if (d.kotisivu) return json({ ok: true });            // ansakenttä roboteille
      const nimi = String(d.nimi || "").trim().slice(0, 40) || "Nimetön";
      const teksti = String(d.teksti || "").trim();
      if (teksti.length < 2) return json({ virhe: "Kirjoita kommentti." }, 400);
      if (teksti.length > 2000) return json({ virhe: "Kommentti on liian pitkä (enintään 2000 merkkiä)." }, 400);
      if ((teksti.match(/https?:\/\//g) || []).length > 2) return json({ virhe: "Liian monta linkkiä." }, 400);
      if (r.botti) return json({ virhe: "Kommentointi ei onnistunut." }, 400);
      const tunti = Date.now() - 3600e3;
      const [{ n }] = this.rivit("SELECT COUNT(*) n FROM kommentit WHERE ip = ? AND aika > ?", r.iptunnus, tunti);
      if (n >= 5) return json({ virhe: "Olet kommentoinut paljon lyhyessä ajassa. Yritä hetken päästä uudelleen." }, 429);
      const aika = Date.now();
      this.sql.exec("INSERT INTO kommentit(polku, nimi, teksti, aika, ip) VALUES (?,?,?,?,?)", kirjoitus, nimi, teksti, aika, r.iptunnus);
      const [{ id }] = this.rivit("SELECT last_insert_rowid() id");
      await this.ilmoita(`💬 Uusi kommentti blogiin (${kirjoitus})\n${nimi}: ${teksti.slice(0, 600)}\n\nPoista: ${r.isanta}/api/hallinta/poista?id=${id}&k=${this.env.HALLINTA}`);
      return json({ ok: true, kommentti: { id, nimi, teksti, aika } });
    }

    if (p === "/api/hallinta/poista") {
      if (!this.env.HALLINTA || r.haku.k !== this.env.HALLINTA) return new Response("Ei oikeutta", { status: 403 });
      const id = Number(r.haku.id);
      const k = this.rivit("SELECT nimi, teksti, piilotettu FROM kommentit WHERE id = ?", id)[0];
      if (!k) return new Response("Kommenttia ei löytynyt", { status: 404 });
      if (r.metodi === "POST") {
        this.sql.exec("UPDATE kommentit SET piilotettu = 1 WHERE id = ?", id);
        return new Response(`<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><body style="font:18px system-ui;padding:30px">🗑️ Kommentti poistettu.`, { headers: { "content-type": "text/html; charset=utf-8" } });
      }
      return new Response(`<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><body style="font:18px system-ui;padding:30px">
        <p><b>${esc(k.nimi)}:</b> ${esc(k.teksti)}</p>${k.piilotettu ? "<p>Tämä kommentti on jo poistettu.</p>" :
        `<form method=post><button style="font:inherit;padding:12px 20px;background:#9b1c1c;color:#fff;border:0;border-radius:10px">Poista kommentti</button></form>`}`,
        { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (p === "/api/hallinta/yhteenveto") {
      if (!this.env.HALLINTA || r.haku.k !== this.env.HALLINTA) return json({ virhe: "ei oikeutta" }, 403);
      return json({
        kavijat: this.rivit("SELECT pv, COUNT(*) n FROM kaynnit WHERE polku = '*' GROUP BY pv ORDER BY pv DESC LIMIT 30"),
        kirjoitukset: this.rivit("SELECT polku, COUNT(*) n FROM kaynnit WHERE polku != '*' GROUP BY polku ORDER BY n DESC"),
        jaot: this.rivit("SELECT * FROM jaot ORDER BY n DESC"),
        kommentteja: this.rivit("SELECT COUNT(*) n FROM kommentit WHERE piilotettu = 0")[0].n
      });
    }
    return json({ virhe: "tuntematon" }, 404);
  }

  tilastot(kirjoitus) {
    const yht = this.rivit("SELECT COUNT(*) n FROM kaynnit WHERE polku = '*'")[0].n;
    const t = { kavijat: yht };
    if (kirjoitus !== "/") {
      t.lukijat = this.rivit("SELECT COUNT(*) n FROM kaynnit WHERE polku = ?", kirjoitus)[0].n;
      t.jaot = Object.fromEntries(KANAVAT.map(k => [k, 0]));
      for (const { kanava, n } of this.rivit("SELECT kanava, n FROM jaot WHERE polku = ?", kirjoitus)) t.jaot[kanava] = n;
      t.kommentteja = this.rivit("SELECT COUNT(*) n FROM kommentit WHERE polku = ? AND piilotettu = 0", kirjoitus)[0].n;
    } else {
      t.lukijat_kirjoituksittain = Object.fromEntries(this.rivit("SELECT polku, COUNT(*) n FROM kaynnit WHERE polku != '*' GROUP BY polku").map(x => [x.polku, x.n]));
      t.kommentit_kirjoituksittain = Object.fromEntries(this.rivit("SELECT polku, COUNT(*) n FROM kommentit WHERE piilotettu = 0 GROUP BY polku").map(x => [x.polku, x.n]));
    }
    return t;
  }

  async ilmoita(teksti) {
    if (!this.env.TELEGRAM_BOT_TOKEN) return;
    try {
      await fetch(`https://api.telegram.org/bot${this.env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ chat_id: this.env.TG_CHAT, text: teksti, disable_web_page_preview: true })
      });
    } catch {}
  }
}
