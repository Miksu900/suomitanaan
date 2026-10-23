"""Videokone: valitsee päivän aiheen Faktapisteen palveluista ja kirjoittaa käsikirjoituksen.

Vuorottelu päivän mukaan: otsikkomuutos (Korjausvahti), huijausvaroitus (Keräysvahti), eduskunnan päätös, Suomi Tänään -uutinen näkökulmineen.
Jos päivän tyypille ei ole tuoretta aihetta, kokeillaan seuraavaa. Käytetyt aiheet luetaan tiedostosta kaytetyt.json.
Kirjoittaa aihe.json: {tyyppi, data, lauseet[5], koukku, kuvateksti, ...}.
Aja: python3 videokone/aiheet.py [tyyppi]
"""
import json, os, re, sys, html, datetime, urllib.request

UA = {"User-Agent": "Faktapiste-videokone/1.0 (+https://faktapiste.fi)"}
ES = "https://eduskuntaseuranta.fi"
TYYPIT = ["korjaus", "huijaus", "eduskunta", "uutinen"]
KAYTETYT = os.environ.get("KAYTETYT", "kaytetyt.json")


def hae(url, tyyppi="json"):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        b = r.read().decode("utf-8")
    return json.loads(b) if tyyppi == "json" else b


def aika(s):
    try:
        return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


NYT = datetime.datetime.now(datetime.timezone.utc)
try:
    kaytetyt = set(json.load(open(KAYTETYT)))
except Exception:
    kaytetyt = set()


def ehdokas_korjaus():
    j = hae("https://nytpuhutaan.fi/muutokset/nostot.json")
    ok = [x for x in j.get("nostot", []) if x.get("url") and x["url"] not in kaytetyt
          and (a := aika(x.get("havaittu"))) and (NYT - a).total_seconds() < 48 * 3600]
    ok.sort(key=lambda x: -(x.get("pisteet") or 0))
    if not ok:
        return None
    x = ok[0]
    return {"avain": x["url"], "media": x.get("media", ""), "ennen": x.get("ennen", ""), "nyt": x.get("nyt", ""),
            "poistettiin": x.get("poistettiin", [])[:4], "lisattiin": x.get("lisattiin", [])[:4], "url": x["url"]}


def ehdokas_huijaus():
    j = hae("https://keraysvahti.fi/huijaukset/varoitukset.json")
    ok = [x for x in j.get("u", []) if x.get("l") and x["l"] not in kaytetyt
          and (a := aika(x.get("a"))) and (NYT - a).total_seconds() < 72 * 3600]
    if not ok:
        return None
    x = ok[0]
    return {"avain": x["l"], "otsikko": re.sub(r"^[^|]{0,25}\|\s*", "", x.get("o", "")), "media": x.get("s", ""), "url": x["l"]}


def ryhmat(id_):
    h = hae(f"{ES}/aanestys/{id_}/", "text")
    t = re.search(r"<table><tr><th>Ryhmä</th>[\s\S]*?</table>", h)
    out = []
    if t:
        for m in re.finditer(r'<tr><td>([^<]+)</td><td class="jaa">(\d+)</td><td class="ei">(\d+)</td><td class="tyhja">(\d+)</td><td class="poissa">(\d+)</td></tr>', t.group(0)):
            out.append({"r": html.unescape(m.group(1)), "jaa": int(m.group(2)), "ei": int(m.group(3)), "tyhja": int(m.group(4)), "poissa": int(m.group(5))})
    return out


def ehdokas_eduskunta():
    a = hae(f"{ES}/data/aanestykset.json")
    ok = [v for v in a if re.search(r"hyväksyminen JAA / hylkääminen", v.get("lisaotsikko") or "", re.I)
          and f"es:{v['id']}" not in kaytetyt and (t := aika(v.get("alkoi"))) and (NYT - t).days < 14]
    if not ok:
        return None
    ok.sort(key=lambda v: v.get("alkoi") or "", reverse=True)
    # tuoreista valitaan tiukin tulos: kiinnostavin
    tuoreet = [v for v in ok if v["alkoi"][:10] == ok[0]["alkoi"][:10]] or ok[:1]
    v = min(tuoreet, key=lambda v: abs(v["jaa"] - v["ei"]))
    otsikko = re.sub(r"^Hallituksen esitys eduskunnalle\s+", "", v["otsikko"]).strip()
    return {"avain": f"es:{v['id']}", "id": v["id"], "otsikko": otsikko[:1].upper() + otsikko[1:], "pv": v["alkoi"][:10],
            "jaa": v["jaa"], "ei": v["ei"], "tyhja": v.get("tyhja", 0), "poissa": v.get("poissa", 0),
            "hyvaksyttiin": v["jaa"] > v["ei"], "ryhmat": ryhmat(v["id"]), "url": f"{ES}/aanestys/{v['id']}/"}


def ehdokas_uutinen():
    """Suomi Tänään -uutinen, jossa on toimituksen näkökulmakappale (poliittiset jutut)."""
    x = hae("https://suomitanaan.fi/rss.xml", "text")
    for it in re.findall(r"<item>([\s\S]*?)</item>", x)[:20]:
        g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", (re.search(f"<{t}>([\\s\\S]*?)</{t}>", it) or [None, ""])[1])).strip()
        url = g("link")
        if not url or url in kaytetyt:
            continue
        p = aika(datetime.datetime.strptime(g("pubDate"), "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=datetime.timezone.utc).isoformat()) if g("pubDate") else None
        if p and (NYT - p).total_seconds() > 72 * 3600:
            continue
        try:
            sivu = hae(url, "text")
        except Exception:
            continue
        kpl = [html.unescape(re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"<p[^>]*>([\s\S]*?)</p>", sivu)]
        kpl = [k for k in kpl if len(k) > 40]
        nako = next((k for k in kpl if k.startswith("Suomi Tänään -näkökulma")), None)
        if not nako:
            continue
        runko = [k for k in kpl if k != nako and "Suomi Tänään" not in k[:20]][:5]
        return {"avain": url, "otsikko": g("title"), "ingressi": g("description"), "kappaleet": runko,
                "nakokulma": nako.split(":", 1)[1].strip(), "url": url}
    return None


EHDOKAS = {"korjaus": ehdokas_korjaus, "huijaus": ehdokas_huijaus, "eduskunta": ehdokas_eduskunta, "uutinen": ehdokas_uutinen}

OHJE = {
    "korjaus": """Aihe: suomalainen media muutti uutisensa otsikkoa julkaisun jälkeen (Korjausvahti havaitsi muutoksen).
Lauseet: 1) koukku, joka saa pysähtymään (mainitse media), 2) alkuperäinen otsikko luettuna ("Ensin otsikko kuului: ..."), 3) uusi otsikko ("Nyt: ..."), 4) lyhyt toteava huomio siitä, mitä poistettiin tai muuttui (ei arvailua syistä, ei syytöksiä), 5) kehotus: "Seuraa otsikkomuutoksia Korjausvahdista, nytpuhutaan piste fi." Pitkän otsikon saa lyhentää luettaessa järkevästä kohdasta.""",
    "huijaus": """Aihe: tuore uutinen huijauksesta. Tavoite on varoittaa ja auttaa.
Lauseet: 1) koukku, joka saa pysähtymään, 2) mitä tapahtui uutisen mukaan (vain otsikon tiedot), 3) ja 4) kaksi lyhyttä yleistä suojautumisvinkkiä, jotka sopivat juuri tähän huijaustyyppiin, 5) kehotus: "Tarkista epäilyttävä viesti tai keräys Keräysvahdista, keräysvahti piste fi." Anna lisäksi kentässä "vinkit" samat kaksi vinkkiä näytölle lyhyinä (enintään 32 merkkiä kumpikin).""",
    "uutinen": """Aihe: Suomi Tänään -uutissivuston poliittinen uutinen ja toimituksen konservatiivinen näkökulma.
Lauseet: 1) iskevä koukku uutisen ytimestä, 2) ja 3) tärkeimmät faktat jutusta (vain jutun tiedot, nimeä henkilöt ja luvut), 4) lause alkaa sanoilla "Suomi Tänään -näkökulma:" ja kertoo toimituksen näkökulman jutun näkökulmakappaleen pohjalta (mielipide saa olla suora, mutta ei uusia tosiasioita eikä ihmisryhmien leimaamista), 5) kehotus: "Lue koko juttu, suomi tänään piste fi." Anna lisäksi kenttä "nakokulma_naytolle": näkökulma näytölle enintään 90 merkkiä.""",
    "eduskunta": """Aihe: eduskunnan äänestys lakiehdotuksen hyväksymisestä.
Lauseet: 1) koukku: mitä päätös tarkoittaa tavalliselle ihmiselle, jos se selviää otsikosta, muuten mistä äänestettiin, 2) tulos luvuin (jaa ja ei), 3) miten suurimmat ryhmät äänestivät (nimeä puolueet), 4) lyhyt toteava huomio (esim. hallitus vastaan oppositio, jos luvuista näkyy niin), 5) kehotus: "Katso, miten oma edustajasi äänesti, eduskuntaseuranta piste fi." Älä ota kantaa päätöksen puolesta tai vastaan.""",
}


def kasikirjoitus(tyyppi, data):
    system = ("Kirjoitat suomenkielisen lyhytvideon (TikTok, Reels, Shorts) puheen. Tyyli: suora, iskevä, puhekielinen mutta asiallinen. "
              "Käytä VAIN annettuja tietoja, älä keksi lukuja, nimiä tai syitä. Kirjoita luvut puheeseen numeroina. "
              "Täsmälleen 5 lausetta, yhteensä 45–70 sanaa (noin 25 sekuntia). Jokainen lause päättyy pisteeseen, kysymysmerkkiin tai huutomerkkiin, eikä lauseen sisällä saa olla muita pisteitä. "
              "Vastaa vain JSON: {\"lauseet\":[5 lausetta], \"koukku\":\"näytölle iso teksti, enintään 26 merkkiä, ilman pistettä\", "
              "\"kuvateksti\":\"somejulkaisun saateteksti 1–2 virkettä + linkki\", \"hashtagit\":[\"4–6 suomenkielistä tunnistetta ilman #\"], \"vinkit\":[]}")
    user = OHJE[tyyppi] + "\n\nData:\n" + json.dumps({k: v for k, v in data.items() if k not in ("avain",)}, ensure_ascii=False)
    body = {"model": "claude-sonnet-5-5", "max_tokens": 900, "system": system, "messages": [{"role": "user", "content": user}], "thinking": {"type": "disabled"}}
    def kutsu(b):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(b).encode(), method="POST",
                                     headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    try:
        d = kutsu(body)
    except urllib.error.HTTPError as e:
        if e.code != 400:
            raise
        body.pop("thinking"); body["max_tokens"] = 4000
        d = kutsu(body)
    t = "".join(c.get("text", "") for c in d.get("content", []) if c.get("type") == "text")
    k = json.loads(re.search(r"\{[\s\S]*\}", t).group(0))
    k["lauseet"] = [re.sub(r"\s+", " ", s).strip() for s in k["lauseet"]][:5]
    assert len(k["lauseet"]) == 5, k
    return k


def main():
    pyydetty = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in TYYPIT else None
    alku = TYYPIT.index(pyydetty) if pyydetty else datetime.date.today().toordinal() % len(TYYPIT)
    for i in range(len(TYYPIT)):
        tyyppi = TYYPIT[(alku + i) % len(TYYPIT)]
        try:
            data = EHDOKAS[tyyppi]()
        except Exception as e:
            print("ehdokashaku epäonnistui", tyyppi, e)
            data = None
        if data:
            break
    else:
        print("Ei aiheita tänään"); sys.exit(2)
    k = kasikirjoitus(tyyppi, data)
    out = {"tyyppi": tyyppi, "data": data, **k}
    json.dump(out, open("aihe.json", "w"), ensure_ascii=False, indent=1)
    kaytetyt.add(data["avain"])
    json.dump(sorted(kaytetyt)[-500:], open(KAYTETYT, "w"), ensure_ascii=False)
    print(tyyppi, "|", " ".join(k["lauseet"]))


if __name__ == "__main__":
    main()
