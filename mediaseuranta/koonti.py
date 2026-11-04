"""Netvo Mediaseuranta: kokoaa asiakkaan aiheen jutut sallituista lähteistä (ei Yle eikä Google News) ja tekee koontiviestin.
Käyttö: python3 koonti.py asiakas.json -> koonti.html"""
import sys, re, json, html, urllib.request, email.utils, datetime
UA = {"user-agent": "Mozilla/5.0 (Netvo Mediaseuranta; +https://netvo.fi)"}
MEDIA = {"HS": "https://www.hs.fi/rss/tuoreimmat.xml", "Ilta-Sanomat": "https://www.is.fi/rss/tuoreimmat.xml",
         "Iltalehti": "https://www.iltalehti.fi/rss/uutiset.xml", "MTV Uutiset": "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat",
         "Kaleva": "https://www.kaleva.fi/feedit/rss/managed-listing/rss-uusimmat/", "Maaseudun Tulevaisuus": "https://www.maaseuduntulevaisuus.fi/rss",
         "Talouselämä": "https://www.talouselama.fi/rss.xml", "Verkkouutiset": "https://www.verkkouutiset.fi/feed/",
         "Kuntalehti": "https://www.kuntalehti.fi/feed", "Kuntaliitto": "https://www.kuntaliitto.fi/rss.xml",
         "Rakennuslehti": "https://www.rakennuslehti.fi/feed/", "Savon Sanomat": "https://www.savonsanomat.fi/feed/rss",
         "Keskisuomalainen": "https://www.ksml.fi/feed/rss", "Karjalainen": "https://www.karjalainen.fi/feed/rss",
         "Vasabladet": "https://www.vasabladet.fi/rss", "HBL": "https://www.hbl.fi/rss"}
def hae(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read().decode("utf-8", "replace")
def jutut(nimi, u):
    try: x = hae(u)
    except Exception as e: print("VIRHE", nimi, e); return
    for it in re.findall(r"<item>([\s\S]*?)</item>", x):
        g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", " ", (re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>", it) or [None, ""])[1])).strip()
        try: t = email.utils.parsedate_to_datetime(g("pubDate"))
        except Exception: t = datetime.datetime.now(datetime.timezone.utc)
        yield {"o": re.sub(r"\s+", " ", g("title")), "k": re.sub(r"\s+", " ", g("description"))[:240], "u": g("link"), "l": nimi, "t": t}
def main():
    a = json.load(open(sys.argv[1])); sana = re.compile(a["hakusanat"], re.I)
    raja = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=a.get("tunnit", 48))
    loydot, nahty = [], set()
    for nimi, u in a.get("omat", {}).items():          # asiakkaan omat lähteet: kaikki uudet
        for j in jutut(nimi, u) or []:
            if j["t"] >= raja and j["u"] not in nahty: nahty.add(j["u"]); j["r"] = "oma"; loydot.append(j)
    for nimi, u in MEDIA.items():
        for j in jutut(nimi, u) or []:
            if j["t"] >= raja and j["u"] not in nahty and sana.search(j["o"] + " " + j["k"]): nahty.add(j["u"]); j["r"] = "media"; loydot.append(j)
    loydot.sort(key=lambda j: j["t"], reverse=True)
    pv = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.%Y")
    def osio(otsikko, lista):
        if not lista: return f'<h2 style="font:600 17px Georgia,serif;margin:26px 0 8px;color:#1d2420">{otsikko}</h2><p style="color:#5c6862;margin:0">Ei uusia juttuja.</p>'
        r = "".join(f'<div style="padding:12px 0;border-bottom:1px solid #e3e6e1"><div style="font-size:12px;color:#5c6862;text-transform:uppercase;letter-spacing:.04em">{html.escape(j["l"])} · {j["t"].astimezone(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m. klo %H.%M")}</div><a href="{html.escape(j["u"])}" style="color:#1d2420;font-weight:600;font-size:16px;text-decoration:none">{html.escape(j["o"])}</a></div>' for j in lista)
        return f'<h2 style="font:600 17px Georgia,serif;margin:26px 0 4px;color:#1d2420">{otsikko} ({len(lista)})</h2>{r}'
    sisalto = (f'<div style="max-width:620px;margin:auto;font-family:system-ui,sans-serif;color:#1d2420;padding:20px">'
      f'<div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#1f6b55;font-weight:700">Netvo Mediaseuranta · esimerkki</div>'
      f'<h1 style="font:650 24px Georgia,serif;margin:6px 0 4px">{html.escape(a["otsikko"])}</h1><p style="color:#5c6862;margin:0">Aamukoonti {pv} · viimeiset {a.get("tunnit",48)} tuntia</p>'
      + osio(a.get("omat_otsikko", "Omat tiedotteet"), [j for j in loydot if j["r"] == "oma"])
      + osio("Mediassa", [j for j in loydot if j["r"] == "media"])
      + '<p style="color:#5c6862;font-size:13px;margin-top:28px">Tämä koonti tulee joka aamu sähköpostiin. Seuranta räätälöidään omien aiheiden mukaan.<br>Netvo · netvo.fi · info@netvo.fi</p></div>')
    open("koonti.html", "w").write(f'<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(a["otsikko"])}</title></head><body style="margin:0;background:#f6f7f4">{sisalto}</body></html>')
    print(f"::notice title=Koonti::{len(loydot)} juttua")
main()
