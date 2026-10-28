"""Netvon kuukausittainen laskutusyhteenveto → Telegram (teksti + CSV kirjanpitäjälle).
Ajetaan GitHub Actionsissa (.github/workflows/laskutus.yml). Syöte: kaupat.json ja muutokset.json (wrangler d1 --json) + asiakkaat.json."""
import csv, datetime, io, json, os, pathlib, sys, urllib.request

HERE = pathlib.Path(__file__).parent
PLAN = int(os.environ.get("PLAN_PRICE_CENTS", "2900"))
ADDON = {"ai": ("Tekoälytekstit", 900), "marketing": ("Ostoskorimuistutus ja uutiskirje", 900), "shipping": ("Lähetysten seuranta", 700),
         "booking": ("Ajanvaraus", 1200), "discounts": ("Alennuskoodit", 500), "accounting": ("Kirjanpitovienti", 500), "chat": ("Tekoälyasiakaspalvelu", 1500)}
KIND = {"order": "Uusi tilaus", "update": "Tietojen muutos", "cancel": "Irtisanominen", "addon_on": "Lisäosa päälle", "addon_off": "Lisäosa pois"}
eur = lambda c: f"{c / 100:.2f}".replace(".", ",") + " €"
fi = lambda s: (datetime.date.fromisoformat(s[:10]).strftime("%-d.%-m.%Y") if s else "")


def rows(path):
    try:
        d = json.loads(pathlib.Path(path).read_text())
        return d[0]["results"] if isinstance(d, list) else d.get("results", [])
    except Exception as e:
        print("lukuvirhe", path, e, file=sys.stderr)
        return None


def main():
    today = datetime.date.today()
    prev = (today.replace(day=1) - datetime.timedelta(days=1))
    kk = prev.strftime("%-m/%Y")
    kaupat, muutokset = rows("kaupat.json"), rows("muutokset.json")
    man = json.loads((HERE / "asiakkaat.json").read_text())
    L = [f"🧾 NETVO – LASKUTUSYHTEENVETO {today.strftime('%-d.%-m.%Y')}", f"(muutokset ajalta {kk})", ""]
    csvbuf = io.StringIO(); w = csv.writer(csvbuf, delimiter=";")
    w.writerow(["Asiakas", "Y-tunnus", "Palvelu", "Kk-maksu sis. ALV 25,5 %", "Yhteyshenkilö", "Sähköposti", "Puhelin", "Laskutusosoite", "Verkkolaskuosoite", "Operaattori", "Laskutus alkaa", "Sitoutuminen kk", "Sitoutuminen päättyy", "Irtisanottu", "Huom"])
    total = 0
    L.append("NETVO KAUPPA – laskulla maksavat kaupat:")
    if kaupat is None:
        L.append("⚠️ Tietokantaa ei saatu luettua – tarkista GitHub Actions -ajon loki.")
    elif not kaupat:
        L.append("– ei laskulla maksavia kauppoja")
    for s in kaupat or []:
        ad = [a for a in (s.get("addons") or "").split(",") if a in ADDON]
        m = PLAN + sum(ADDON[a][1] for a in ad)
        cancelled = bool(s.get("cancel_requested_at"))
        huom = ""
        if cancelled:
            ends = s.get("commitment_ends_at") or ""
            huom = f"Irtisanottu {fi(s['cancel_requested_at'])}" + (" – kesken sitoutumisen: laskuta 2 kk maksu" if ends and s["cancel_requested_at"][:10] < ends[:10] else "")
        elif s.get("billing_starts_at") and s["billing_starts_at"][:10] > today.isoformat():
            huom = f"Laskutus alkaa {fi(s['billing_starts_at'])}"
        else:
            total += m
        pal = "Netvo Kauppa" + (" + " + ", ".join(ADDON[a][0] for a in ad) if ad else "")
        L.append(f"• {s.get('billing_company') or s.get('name')} ({s.get('billing_business_id') or '–'}): {eur(m)}/kk – {pal}" + (f" ⚠️ {huom}" if huom else ""))
        w.writerow([s.get("billing_company") or s.get("name"), s.get("billing_business_id"), pal, eur(m), s.get("billing_contact"), s.get("billing_email"), s.get("billing_phone"),
                    s.get("billing_address"), s.get("einvoice_address"), s.get("einvoice_operator"), fi(s.get("billing_starts_at")), s.get("commitment_months"), fi(s.get("commitment_ends_at")), fi(s.get("cancel_requested_at")), huom])
    L += ["", f"MUUTOKSET {kk}:"]
    if muutokset:
        for e in muutokset:
            L.append(f"• {fi(e['created_at'])} {e.get('billing_company') or e.get('name')}: {KIND.get(e['kind'], e['kind'])}" + (f" – {e['detail']}" if e.get("detail") else "") + (f" → {eur(e['monthly_cents'])}/kk" if e.get("monthly_cents") else ""))
    else:
        L.append("– ei muutoksia" if muutokset is not None else "⚠️ ei saatu luettua")
    L += ["", "MUUT NETVON ASIAKKAAT:"]
    for p in man.get("palvelut", []):
        h = p.get("kk_hinta_eur")
        L.append(f"• {p['asiakas']} ({p.get('ytunnus', '–')}): {p['palvelu']} – " + (f"{h:.2f} €/kk".replace(".", ",") if h else "ei kuukausilaskua") + (f" ({p['huom']})" if p.get("huom") else ""))
        if h: total += round(h * 100)
        w.writerow([p["asiakas"], p.get("ytunnus"), p["palvelu"], eur(round(h * 100)) if h else "", "", "", "", "", "", "", "", "", "", "", p.get("huom", "")])
    soon = [d for d in man.get("verkkotunnukset", []) if (datetime.date.fromisoformat(d["uusiutuu"]) - today).days <= 45]
    L += ["", "VERKKOTUNNUSTEN UUSIMISET (45 pv sisällä):"]
    L += [f"• {d['nimi']} uusiutuu {fi(d['uusiutuu'])} – {d['hinta']} ({d['rekisteri']}), haltija {d['haltija']}" for d in soon] or ["– ei uusittavia"]
    L += ["", f"KUUKAUSILASKUTUS YHTEENSÄ: {eur(total)} (sis. ALV)", "", "Liitteenä CSV kirjanpitäjälle (avautuu Excelissä)."]
    text = "\n".join(L)
    print(text)
    tok, chat = os.environ.get("TG"), os.environ.get("TG_CHAT")
    if not tok or not chat:
        print("Telegram-tunnukset puuttuvat – ei lähetetty"); return
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", json.dumps({"chat_id": chat, "text": text[:4000]}).encode(), {"content-type": "application/json"})
    print(urllib.request.urlopen(req).status)
    bnd = "----netvo" + today.strftime("%Y%m%d")
    fname = f"netvo-laskutus-{today.strftime('%Y-%m')}.csv"
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat}\r\n"
            f"--{bnd}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{fname}\"\r\nContent-Type: text/csv\r\n\r\n").encode() + ("﻿" + csvbuf.getvalue()).encode("utf-8") + f"\r\n--{bnd}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendDocument", body, {"content-type": f"multipart/form-data; boundary={bnd}"})
    print(urllib.request.urlopen(req).status)


if __name__ == "__main__":
    main()
