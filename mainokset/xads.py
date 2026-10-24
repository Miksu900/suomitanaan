"""X Ads API -apuri GitHub Actionsiin (OAuth 1.0a). Ei tulosta avaimia.

Toiminnot:
  tila            tilit, kampanjat ja eilisen tulokset (vain luku)
  pysayta ID      pysäyttää yhden kampanjan (PAUSED, ei poistoa) – vain omistajan luvalla
Avaimet: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET (GitHubin salaisuudet).
"""
import os, sys, json, time, hmac, hashlib, base64, secrets, datetime, urllib.request, urllib.parse

API = "https://ads-api.x.com"
VERSIOT = ("12", "13", "11")
_ver = None


def _e(s):
    return urllib.parse.quote(str(s), safe="~-._")


def _allekirjoitus(tapa, url, param):
    ck, cs = os.environ["X_API_KEY"].strip(), os.environ["X_API_SECRET"].strip()
    at, ats = os.environ["X_ACCESS_TOKEN"].strip(), os.environ["X_ACCESS_SECRET"].strip()
    o = {"oauth_consumer_key": ck, "oauth_nonce": secrets.token_hex(16), "oauth_signature_method": "HMAC-SHA1",
         "oauth_timestamp": str(int(time.time())), "oauth_token": at, "oauth_version": "1.0"}
    kaikki = sorted([(_e(k), _e(v)) for k, v in list(param.items()) + list(o.items())])
    pohja = "&".join([tapa, _e(url), _e("&".join(f"{k}={v}" for k, v in kaikki))])
    o["oauth_signature"] = base64.b64encode(hmac.new(f"{_e(cs)}&{_e(ats)}".encode(), pohja.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_e(k)}="{_e(v)}"' for k, v in sorted(o.items()))


def kutsu(polku, param=None, tapa="GET"):
    """polku ilman versiota, esim. '/accounts'. Palauttaa JSONin tai {'virhe': koodi, 'vastaus': teksti}."""
    global _ver
    param = {k: str(v) for k, v in (param or {}).items()}
    for v in ([_ver] if _ver else VERSIOT):
        url = f"{API}/{v}{polku}"
        h = {"Authorization": _allekirjoitus(tapa, url, param)}
        if tapa == "GET":
            req = urllib.request.Request(url + ("?" + urllib.parse.urlencode(param) if param else ""), headers=h)
        else:
            h["content-type"] = "application/x-www-form-urlencoded"
            req = urllib.request.Request(url, urllib.parse.urlencode(param).encode(), h, method=tapa)
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=40).read() or b"{}")
            _ver = v
            return r
        except urllib.error.HTTPError as e:
            t = e.read().decode()[:1500]
            if e.code == 404 and not _ver and "NOT_FOUND" in t.upper() and polku == "/accounts":
                continue  # kokeillaan toista rajapintaversiota
            return {"virhe": e.code, "vastaus": t}
    return {"virhe": 404, "vastaus": "Rajapintaversiota ei löytynyt"}


def eur(mikro):
    return f"{(mikro or 0) / 1e6:.2f} €".replace(".", ",")


def tilit():
    v = kutsu("/accounts")
    if "virhe" in v:
        return v
    return [{"id": a["id"], "nimi": a.get("name"), "tila": a.get("approval_status")} for a in v.get("data", []) if not a.get("deleted")]


def kampanjat(tili):
    v = kutsu(f"/accounts/{tili}/campaigns", {"count": 200})
    if "virhe" in v:
        return v
    return [{"id": c["id"], "nimi": c.get("name"), "tila": c.get("entity_status"), "palvelu": c.get("servable"),
             "paiva": c.get("daily_budget_amount_local_micro"), "yht": c.get("total_budget_amount_local_micro"),
             "alku": (c.get("start_time") or "")[:10], "loppu": (c.get("end_time") or "")[:10]}
            for c in v.get("data", []) if not c.get("deleted")]


def eilen(tili, ids):
    """Eilisen klikit, näytöt ja kulu kampanjoittain (Suomen aika)."""
    if not ids:
        return {}
    nyt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
    alku = nyt - datetime.timedelta(days=1)
    v = kutsu(f"/stats/accounts/{tili}", {"entity": "CAMPAIGN", "entity_ids": ",".join(ids[:20]),
                                           "start_time": alku.isoformat(), "end_time": nyt.isoformat(),
                                           "granularity": "TOTAL", "placement": "ALL_ON_TWITTER",
                                           "metric_groups": "ENGAGEMENT,BILLING"})
    if "virhe" in v:
        return v
    out = {}
    for d in v.get("data", []):
        m = ((d.get("id_data") or [{}])[0].get("metrics") or {})
        s = lambda k: sum(m.get(k) or [0])
        out[d["id"]] = {"klikit": s("url_clicks") or s("clicks"), "naytot": s("impressions"), "kulu": s("billed_charge_local_micro")}
    return out


def ilmoita(otsikko, teksti):
    for rivi in str(teksti).splitlines() or [""]:
        [print(f"::notice title={otsikko}::{rivi[i:i+3500]}") for i in range(0, max(len(rivi), 1), 3500)]


def raporttirivit():
    """Rivit päivittäiseen Telegram-raporttiin."""
    t = tilit()
    if isinstance(t, dict):
        return [f"🐦 <b>X</b>: virhe {t.get('virhe')}"]
    rivit = ["🐦 <b>X</b>"]
    for a in t:
        k = kampanjat(a["id"])
        if isinstance(k, dict):
            rivit.append(f"  virhe {k.get('virhe')}"); continue
        aktiiv = [c for c in k if c["tila"] == "ACTIVE"]
        st = eilen(a["id"], [c["id"] for c in aktiiv])
        st = st if isinstance(st, dict) and "virhe" not in st else {}
        for c in aktiiv:
            s = st.get(c["id"], {})
            rivit.append(f"  • {c['nimi']}: {s.get('klikit', 0)} klikkiä, {s.get('naytot', 0)} näyttöä, {eur(s.get('kulu'))}"
                         + (f" (päättyy {c['loppu']})" if c["loppu"] else ""))
        if not aktiiv:
            rivit.append("  ei käynnissä olevia kampanjoita")
    return rivit


if __name__ == "__main__":
    toiminto = sys.argv[1] if len(sys.argv) > 1 else "tila"
    if toiminto == "tila":
        t = tilit()
        if isinstance(t, dict):
            ilmoita("Yhteys", f"virhe {t.get('virhe')}: {t.get('vastaus')}")
            sys.exit(1)
        ilmoita("Yhteys", f"OK, rajapintaversio {_ver}, tilejä {len(t)}")
        for a in t:
            ilmoita("Tili", json.dumps(a, ensure_ascii=False))
            k = kampanjat(a["id"])
            ilmoita("Kampanjat", json.dumps(k, ensure_ascii=False))
            if isinstance(k, list):
                ilmoita("Eilen", json.dumps(eilen(a["id"], [c["id"] for c in k if c["tila"] == "ACTIVE"]), ensure_ascii=False))
    elif toiminto == "tutki":
        # Tulostaa olemassa olevan kampanjan rakenteen (vain luku), jotta uusi voidaan tehdä samalla mallilla.
        tili = tilit()[0]["id"]
        for nimi, polku, p in [("Rahoitus", f"/accounts/{tili}/funding_instruments", {}),
                               ("Kampanjat", f"/accounts/{tili}/campaigns", {}),
                               ("Mainosryhmät", f"/accounts/{tili}/line_items", {}),
                               ("Kohdennus", f"/accounts/{tili}/targeting_criteria", {"line_item_ids": ",".join(l["id"] for l in kutsu(f"/accounts/{tili}/line_items").get("data", [])[:20])}),
                               ("Mainostetut", f"/accounts/{tili}/promoted_tweets", {}),
                               ("Mainostettavat käyttäjät", f"/accounts/{tili}/promotable_users", {})]:
            ilmoita(nimi, json.dumps(kutsu(polku, p), ensure_ascii=False)[:6000])
    elif toiminto == "pysayta":
        tili, kid = sys.argv[2], sys.argv[3]
        v = kutsu(f"/accounts/{tili}/campaigns/{kid}", {"entity_status": "PAUSED"}, "PUT")
        ilmoita("Pysäytys", json.dumps(v.get("data", v), ensure_ascii=False)[:2000])
