"""Mediahälytys: ilmoittaa Telegramiin heti (n. 5 min viiveellä), kun päämedioihin tulee maahanmuuttoon tai islamiin liittyvä juttu.
Seuraa Ylen, HS:n, IS:n, Iltalehden, MTV:n, Uuden Suomen ja Suomen Uutisten RSS-virtoja sekä Google Uutisten Suomi-hakuja.
Kuuma aihe: kun sama asia nousee kahteen tai neljään eri mediaan, tulee erillinen 🔥-viesti.
Tila: halytys.json (haara halytys-tila). Vain julkisia otsikkoja ja linkkejä; ei henkilöiden seurantaa."""
import os, re, json, html, hashlib, urllib.request, urllib.parse, datetime, email.utils
import xml.etree.ElementTree as ET

UA = {"user-agent": "Mozilla/5.0 (Faktapiste-mediahalytys; +https://faktapiste.fi)"}
CHAT = "1893930799"
GN = "https://news.google.com/rss/search?hl=fi&gl=FI&ceid=FI:fi&q="
SYOTTEET = [("Yle", "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET"),
            ("Helsingin Sanomat", "https://www.hs.fi/rss/tuoreimmat.xml"),
            ("Ilta-Sanomat", "https://www.is.fi/rss/tuoreimmat.xml"),
            ("Iltalehti", "https://www.iltalehti.fi/rss/uutiset.xml"),
            ("MTV Uutiset", "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat"),
            ("Uusi Suomi", "https://www.uusisuomi.fi/rss"),
            ("Suomen Uutiset", "https://www.suomenuutiset.fi/feed/")]
GNHAUT = ["islam OR muslimi OR moskeija OR imaami OR islamilainen when:1d",
          "maahanmuutto OR turvapaikanhakija OR karkotus OR oleskelulupa OR kansalaisuuslaki OR maahanmuuttovirasto when:1d"]
ISLAM = re.compile(r"\b(islam(?!abad)\w*|muslim\w*|moskei\w*|imaam\w*|imaami\w*|šaria\w*|sharia\w*|d?[jž]ihad\w*|hijab\w*|burka\w*|nikab\w*|kalifaat\w*|koraani\w*|ramadan\w*|halal\w*)", re.I)
MAAHAN = re.compile(r"\b(maahanmuu\w*|turvapaik\w*|pakolai\w*|ulkomaalais\w*|kotoutu\w*|kotouttam\w*|kansalaisuuslaki\w*|kansalaisuuskoe\w*|kaksoiskansalaisuu\w*|kansalaisuuden (?:menetys|menettä|peruut)\w*|oleskelulup\w*|karkot\w*|rajaturva\w*|monikulttuur\w*|maahantul\w*|perheenyhdist\w*|migri\w*|vastaanottokesk\w*|paperittom\w*|pakkoavio\w*|ulkomaalaistaustai\w*|maahanmuuttovirasto\w*)", re.I)
STOP = set("""ja tai mutta että kun jos kuin on ovat oli olivat ei eivät hän he se ne tämä nämä joka jotka mikä miten miksi missä
mitä kuka nyt jo vielä myös vain sekä eli koska vaikka kanssa mukaan jälkeen ennen aikana yli alle ilman vuoksi saa sai voi
pitää tulee olla uusi uuden suuri iso paljon kaikki sitten tänään eilen kertoo kertoi sanoo sanoi video kuvat live suomi suomen""".split())
RX = re.compile(r"[a-zäöå0-9]+(?:-[a-zäöå0-9]+)*", re.I)
SAILYTYS_H = 72

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={**UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"}), timeout=30).read()

def canon(u):
    p = urllib.parse.urlsplit(u.strip())
    if "news.google" in p.netloc: return u.strip()
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", ""))

def puhdista(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).replace("\xad", "").strip()

def aika(s):
    if not s: return None
    try: d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc)

def jutut(media, data, google=False):
    try: root = ET.fromstring(data)
    except Exception:
        try:   # rikkinäinen XML: siivoa ohjausmerkit ja irralliset &-merkit
            t = data.decode("utf-8", "replace")
            t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", "", t)
            t = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", t)
            root = ET.fromstring(t.encode("utf-8"))
        except Exception as e:
            print("::warning title=RSS::" + media + " ei aukea: " + str(e)[:80]); return
    for it in list(root.iter("item")) + list(root.iter("{http://www.w3.org/2005/Atom}entry")):
        def g(*n):
            for x in n:
                e = it.find(x)
                if e is not None and (e.text or "").strip(): return e.text.strip()
            return ""
        otsikko = puhdista(g("title", "{http://www.w3.org/2005/Atom}title"))
        linkki = g("link")
        if not linkki:
            e = it.find("{http://www.w3.org/2005/Atom}link")
            linkki = e.get("href", "") if e is not None else ""
        kuvaus = puhdista(g("description", "{http://www.w3.org/2005/Atom}summary"))[:300]
        t = aika(g("pubDate", "{http://www.w3.org/2005/Atom}updated", "{http://www.w3.org/2005/Atom}published"))
        lahde = media
        if google:
            s = it.find("source")
            lahde = (s.text or "").strip() if s is not None and s.text else "Google Uutiset"
            otsikko = re.sub(r"\s+-\s+" + re.escape(lahde) + r"\s*$", "", otsikko)
            kuvaus = ""
        if otsikko and linkki: yield {"o": otsikko, "k": kuvaus, "u": linkki.strip(), "m": lahde, "t": (t or datetime.datetime.now(datetime.timezone.utc)).isoformat(timespec="seconds"), "g": google}

def luokat(x):
    teksti = x["o"] + " " + x["k"]
    return [n for n, rx in (("Islam", ISLAM), ("Maahanmuutto", MAAHAN)) if rx.search(teksti)]

def vartalot(o):
    return {w[:4] if len(w) > 4 else w for w in RX.findall(o.lower()) if w not in STOP and len(w) >= 3}

def sama(a, b):
    yhteiset = len(a & b)
    return yhteiset >= 3 and yhteiset / max(1, min(len(a), len(b))) >= 0.45

def nimi_samaksi(m):
    return {"HS.fi": "Helsingin Sanomat", "Hs.fi": "Helsingin Sanomat", "Yle Uutiset": "Yle", "yle.fi": "Yle", "Is.fi": "Ilta-Sanomat", "IS.fi": "Ilta-Sanomat",
            "mtvuutiset.fi": "MTV Uutiset", "Mtvuutiset.fi": "MTV Uutiset", "MTV Uutiset": "MTV Uutiset", "Iltalehti.fi": "Iltalehti"}.get(m, m)

def laheta(t, hiljaa=False):
    tg = os.environ.get("TG", "").strip()
    if not tg:
        print("[ei TG-avainta] " + t.replace("\n", " | ")[:200]); return True
    d = json.dumps({"chat_id": CHAT, "text": t, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_notification": hiljaa}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tg}/sendMessage", d, {"content-type": "application/json"}), timeout=20); return True
    except Exception as e:
        print("::warning title=Telegram::" + str(e)[:120]); return False

def keraa(testidir=None):
    kaikki, loki = [], []
    if testidir:
        for f in sorted(os.listdir(testidir)):
            kaikki += list(jutut(f.rsplit(".", 1)[0], open(os.path.join(testidir, f), "rb").read()))
        return kaikki, loki
    for media, url in SYOTTEET:
        try: kaikki += list(jutut(media, hae(url)))
        except Exception as e: loki.append(f"{media}: {str(e)[:80]}")
    for q in GNHAUT:
        try: kaikki += list(jutut("Google Uutiset", hae(GN + urllib.parse.quote(q)), google=True))
        except Exception as e: loki.append(f"Google: {str(e)[:80]}")
    return kaikki, loki

def ajo(tila, kaikki, nyt):
    """Palauttaa (viestit, uusi tila). Viesti = (teksti, [kanoniset linkit])."""
    ensiajo = not tila.get("stories") and not tila.get("urls")
    stories, urls = tila.get("stories", []), set(tila.get("urls", [])) | set(tila.get("nahdyt", []))
    raja = (nyt - datetime.timedelta(hours=SAILYTYS_H)).isoformat(timespec="seconds")
    stories = [s for s in stories if s["t"] >= raja]
    vanhin = (nyt - datetime.timedelta(hours=8)).isoformat(timespec="seconds")
    uudet = []
    for x in sorted(kaikki, key=lambda y: y["t"]):
        x["m"] = nimi_samaksi(x["m"]); c = canon(x["u"])
        if c in urls: continue
        k = luokat(x)
        if not k: continue
        urls.add(c)
        if x["t"] < vanhin: continue          # vanha juttu, jonka virta nosti uudelleen
        x["c"], x["k2"] = c, k
        uudet.append(x)
    viestit, muuttuneet = [], {}
    for x in uudet:
        v = vartalot(x["o"]); osuma = None
        for s in stories:
            if sama(v, set(s["v"])): osuma = s; break
        if osuma is None:
            osuma = {"id": hashlib.sha1(x["c"].encode()).hexdigest()[:10], "t": x["t"], "v": sorted(v), "luokat": x["k2"], "jutut": [], "kuuma": 0, "uusi": True}
            stories.append(osuma)
        if all(j["m"] != x["m"] for j in osuma["jutut"]) or not osuma["jutut"]:
            osuma["jutut"].append({"m": x["m"], "o": x["o"], "u": x["u"]})
            muuttuneet[osuma["id"]] = osuma
        osuma["v"] = sorted(set(osuma["v"]) | v)
    for s in muuttuneet.values():
        n = len({j["m"] for j in s["jutut"]})
        em = "".join({"Islam": "🕌", "Maahanmuutto": "🛂"}[k] for k in s["luokat"])
        luokka = " + ".join(s["luokat"])
        if s.pop("uusi", False):
            j = s["jutut"][0]
            if n >= 2:
                s["kuuma"] = 2 if n < 4 else 4
                teksti = f"🔥 {em} <b>{luokka}</b> · {n} mediaa kertoo\n<b>{html.escape(j['o'])}</b>\n{html.escape(' · '.join(x['m'] for x in s['jutut']))}\n{j['u']}"
            else:
                teksti = f"{em} <b>{luokka}</b> · {html.escape(j['m'])}\n<b>{html.escape(j['o'])}</b>\n{j['u']}"
            viestit.append((teksti, [canon(x["u"]) for x in s["jutut"]]))
        else:
            kynnys = 4 if n >= 4 else 2 if n >= 2 else 0
            if kynnys > s["kuuma"]:
                s["kuuma"] = kynnys; j = s["jutut"][-1]
                teksti = f"🔥 {em} <b>Kuuma aihe: {n} mediaa kertoo</b>\n<b>{html.escape(s['jutut'][0]['o'])}</b>\n{html.escape(' · '.join(x['m'] for x in s['jutut']))}\n{j['u']}"
                viestit.append((teksti, [canon(x["u"]) for x in s["jutut"]]))
    for s in stories: s.pop("uusi", None)
    return ensiajo, viestit, {"stories": stories, "urls": sorted(urls)[-4000:]}, uudet

if __name__ == "__main__":
    nyt = datetime.datetime.now(datetime.timezone.utc)
    testidir = os.environ.get("MH_TESTI_DIR")
    tilatiedosto = os.environ.get("MH_TILA", "halytys.json")
    try: tila = json.load(open(tilatiedosto))
    except Exception: tila = {}
    kaikki, loki = keraa(testidir)
    for l in loki: print("::warning title=Syöte::" + l)
    if kaikki == [] and loki: raise SystemExit("ei yhtään syötettä saatu")
    ensiajo, viestit, uusi, uudet = ajo(tila, kaikki, nyt)
    print(f"::notice title=Mediahälytys::{len(kaikki)} juttua, {len(uudet)} uutta osuvaa, {len(viestit)} viestiä" + (" (ensiajo)" if ensiajo else ""))
    if ensiajo and not os.environ.get("MH_LAHETA_ENSIAJO"):
        esim = "\n".join(f"• {html.escape(x['o'])} <i>({html.escape(x['m'])})</i>" for x in sorted(uudet, key=lambda y: y["t"], reverse=True)[:4])
        laheta("✅ <b>Mediahälytys päällä</b>\nSeuraan Yleä, HS:ää, IS:ää, Iltalehteä, MTV:tä, Uutta Suomea ja Suomen Uutisia sekä Google Uutisia: maahanmuutto ja islam. Tarkistus n. 5 min välein. 🔥 = sama aihe kahdessa tai useammassa mediassa." + (f"\n\nViimeisimmät osumat (vain esimerkki, ei uusia):\n{esim}" if esim else ""))
        viestit = []
    lahetetyt = set(); jono = viestit[:10]
    for teksti, linkit in jono:
        if laheta(teksti): lahetetyt.update(linkit)
        else: print("::warning title=Telegram::viesti jäi lähettämättä")
    if len(viestit) > 10:
        laheta(f"➕ {len(viestit) - 10} muuta osumaa; katso Nytpuhutaan.fi/politiikka/maahanmutto ja /politiikka/islam", hiljaa=True)
    uusi["halytetyt"] = sorted(set(tila.get("halytetyt", [])) | lahetetyt)[-3000:]
    json.dump(uusi, open(tilatiedosto, "w"), ensure_ascii=False)
