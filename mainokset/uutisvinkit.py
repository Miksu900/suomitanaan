"""Uutisvahti markkinointiin: etsii uutisista aiheita, joihin Faktapisteen palvelut vastaavat,
ja lähettää Telegramiin uutisen + valmiin postausluonnoksen. Tila: tiedosto nahdyt.json (haara uutisvinkit-tila)."""
import os, re, json, html, urllib.request, datetime

SYOTTEET = ["https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET", "https://www.hs.fi/rss/tuoreimmat.xml",
            "https://www.iltalehti.fi/rss/uutiset.xml", "https://www.is.fi/rss/tuoreimmat.xml",
            "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat"]
PALVELUT = {
    "keraysvahti": ("Keräysvahti", "https://keraysvahti.fi/", r"huija|kerääj|rahankeräy|keräysluv|lahjoit|valekerä|tekaistu|nettihuij|tekstiviestihuij|romanssihuij"),
    "yksityisyys": ("Yksityisyysvahti", "https://faktapiste.fi/yksityisyys/", r"sijaintitie|sijaintidat|tietovuo|henkilötie|tietosuoj|datakaup|seuranta.*sovellu|mainostunnis"),
    "pykalavahti": ("Pykälävahti", "https://pykalavahti.fi/", r"reklamaati|kuluttaja(riita|oikeu|asiamie)|takuu|perintä|vuokranant|vuokrasopim|riitalautakun|virheellinen tuote"),
}
UA = {"user-agent": "Faktapiste-uutisvinkit/1.0 (+https://faktapiste.fi)"}

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "replace")

def kohteet():
    for s in SYOTTEET:
        try: x = hae(s)
        except Exception: continue
        for it in re.findall(r"<item>([\s\S]*?)</item>", x)[:40]:
            g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", (re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>", it) or [None, ""])[1])).strip()
            if g("link"): yield {"otsikko": g("title"), "kuvaus": g("description")[:400], "url": g("link"), "media": re.sub(r"^www\.|\..*$", "", urllib.parse.urlparse(g("link")).netloc)}

def claude(uutinen, nimi, url):
    ohje = ("Kirjoitat Faktapisteelle lyhyen somepostauksen (X/Facebook) suomeksi ajankohtaisen uutisen pohjalta. "
            f"Postaus kytkee uutisen aiheen palveluun {nimi} ({url}). Max 270 merkkiä. Asiallinen, ei liioittelua, "
            "ei poliittista kantaa, ei väitteitä joita uutinen ei tue. Loppuun palvelun linkki. Vastaa pelkällä postauksella. "
            "Jos uutinen ei oikeasti liity palvelun aiheeseen, vastaa pelkästään: EI")
    d = json.dumps({"model": "claude-haiku-4-5", "max_tokens": 300, "system": ohje,
                    "messages": [{"role": "user", "content": f"Uutinen ({uutinen['media']}): {uutinen['otsikko']}\n{uutinen['kuvaus']}"}]}).encode()
    r = urllib.request.Request("https://api.anthropic.com/v1/messages", d, {"x-api-key": os.environ["AK"].strip(), "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())["content"][0]["text"].strip()

def laheta(t):
    d = json.dumps({"chat_id": "1893930799", "text": t, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{os.environ['TG'].strip()}/sendMessage", d, {"content-type": "application/json"}))

if __name__ == "__main__":
    import urllib.parse
    tila = "nahdyt.json"
    nahdyt = set(json.load(open(tila))) if os.path.exists(tila) else set()
    eka = not nahdyt
    uudet, lahetetty = [], 0
    testi = os.environ.get("TESTI") == "1"
    if testi: eka, nahdyt = False, set()
    for u in kohteet():
        if u["url"] in nahdyt: continue
        nahdyt.add(u["url"]); uudet.append(u)
    if not eka:
        for u in uudet:
            teksti = (u["otsikko"] + " " + u["kuvaus"]).lower()
            osuma = next((k for k, (_, _, rx) in PALVELUT.items() if re.search(rx, teksti)), None)
            if not osuma or lahetetty >= (1 if testi else 4): continue
            nimi, url, _ = PALVELUT[osuma]
            try: luonnos = claude(u, nimi, url)
            except Exception: continue
            if luonnos.strip().upper().startswith("EI"): continue
            laheta(f"📰 <b>Uutisvinkki – {nimi}</b>\n{html.escape(u['otsikko'])} ({u['media']})\n{u['url']}\n\n✍️ <b>Postausluonnos:</b>\n{html.escape(luonnos)}")
            lahetetty += 1
    if not testi: json.dump(sorted(nahdyt)[-3000:], open(tila, "w"))
    print(f"::notice title=Uutisvinkit::uusia {len(uudet)}, lähetetty {lahetetty}{' (ensiajo, vain tallennus)' if eka else ''}")
