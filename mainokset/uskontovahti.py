"""Miikan oma seuranta: julkiset uutiset ja tiedotteet islamista ja muslimeista Suomessa.
Kerran päivässä koonti Telegramiin (otsikko, lähde, linkki). Ei kommentointia eikä henkilöiden seurantaa.
Tila: uskontovahti.json (haara uutisvinkit-tila)."""
import os, re, json, html, urllib.request, urllib.parse, datetime

UA = {"user-agent": "Mozilla/5.0 (Faktapiste-seuranta)"}
GN = "https://news.google.com/rss/search?hl=fi&gl=FI&ceid=FI:fi&q="
SYOTTEET = [
    "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET", "https://www.hs.fi/rss/tuoreimmat.xml",
    "https://www.iltalehti.fi/rss/uutiset.xml", "https://www.is.fi/rss/tuoreimmat.xml",
    "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat", "https://www.kotimaa.fi/feed/",
] + [GN + urllib.parse.quote(q) for q in [
    "islam Suomi when:2d", "muslimit Suomi when:2d", "moskeija when:2d", "imaami when:2d",
    "islam eduskunta OR ministeriö OR poliisi when:3d", "Suomen islamilainen neuvosto when:7d"]]
AIHE = re.compile(r"islam|muslim|moskei|moske|imaam|ramadan|ramazan|halal|koraan|hijab|burka|niqab|sharia|islamilai", re.I)
SUOMI = re.compile(r"suom|helsin|espoo|vantaa|tampere|turku|oulu|jyväsky|kuopio|lahti|eduskun|yle|poliisi|ministeri|kunta|koulu|kela|migri|thl|opetushallit|seurakun|kirkko", re.I)

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")

def kohteet():
    for s in SYOTTEET:
        try: x = hae(s)
        except Exception: continue
        for it in re.findall(r"<item>([\s\S]*?)</item>", x)[:60]:
            g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", " ", (re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>", it) or [None, ""])[1])).strip()
            otsikko, kuvaus, linkki = g("title"), g("description")[:500], g("link")
            lahde = g("source") or re.sub(r"^www\.", "", urllib.parse.urlparse(linkki).netloc)
            if "news.google" in s and " - " in otsikko: otsikko = otsikko.rsplit(" - ", 1)[0]
            if linkki and AIHE.search(otsikko + " " + kuvaus) and ("news.google" in s and SUOMI.search(otsikko + " " + kuvaus + " " + lahde) or "news.google" not in s):
                yield {"otsikko": re.sub(r"\s+", " ", otsikko), "lahde": lahde, "url": linkki}

def laheta(t):
    d = json.dumps({"chat_id": "1893930799", "text": t, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{os.environ['TG'].strip()}/sendMessage", d, {"content-type": "application/json"}))

if __name__ == "__main__":
    tila = "uskontovahti.json"
    try: nahdyt = set(json.load(open(tila)))
    except Exception: nahdyt = set()
    testi = os.environ.get("TESTI") == "1"
    uudet, otsikot = [], set()
    for u in kohteet():
        avain = re.sub(r"\W+", "", u["otsikko"].lower())[:60]
        if (u["url"] in nahdyt or avain in nahdyt) and not testi: continue
        if avain in otsikot: continue
        otsikot.add(avain); nahdyt.update([u["url"], avain]); uudet.append(u)
    pv = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.")
    if uudet:
        rivit = [f"• {html.escape(u['otsikko'])} <i>({html.escape(u['lahde'])})</i>\n{u['url']}" for u in uudet[:25]]
        osa, osat = f"🕌⛪ <b>Islam ja muslimit Suomessa – {pv}</b> ({len(uudet)} uutta)\n\n", []
        for r in rivit:
            if len(osa) + len(r) > 3800: osat.append(osa); osa = ""
            osa += r + "\n\n"
        osat.append(osa)
        for o in osat: laheta(o)
    else:
        laheta(f"🕌⛪ <b>Islam ja muslimit Suomessa – {pv}</b>\nEi uusia uutisia viimeisen vuorokauden aikana.")
    json.dump(sorted(nahdyt)[-3000:], open(tila, "w"), ensure_ascii=False)
    print(f"::notice title=Uskontovahti::{len(uudet)} uutta")
