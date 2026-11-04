"""Kokeilee ehdokassyötteitä (kaupallisesti käytettävät lähteet: ei Yleä eikä Google Newsia) ja raportoi toimivat."""
import urllib.request, re, sys
UA = {"user-agent": "Mozilla/5.0 (Netvo Mediaseuranta; +https://netvo.fi)"}
pohjat = {
 "kalajokilaakso.fi": ["/feed/rss", "/rss", "/feed", "/rss.xml"], "keskipohjanmaa.fi": ["/feed/rss", "/rss", "/feed", "/rss.xml"],
 "kaleva.fi": ["/feedit/rss/managed-listing/rss-uusimmat/", "/feed/rss", "/rss"], "pyhajokiseutu.fi": ["/feed/rss", "/rss"],
 "ilkkapohjalainen.fi": ["/feed/rss", "/rss"], "maaseuduntulevaisuus.fi": ["/feed/rss", "/rss"], "uusisuomi.fi": ["/rss"],
 "ylivieska.fi": ["/feed/", "/rss", "/ajankohtaista/rss", "/feed"], "kalajoki.fi": ["/feed/", "/rss"], "nivala.fi": ["/feed/", "/rss"],
 "oulu.fi": ["/rss", "/fi/rss"], "sttinfo.fi": ["/rss", "/rss/releases", "/feed"], "valtioneuvosto.fi": ["/rss", "/-/rss", "/ajankohtaista/rss"],
 "kauppalehti.fi": ["/rss/uusimmat", "/rss"], "talouselama.fi": ["/rss.xml", "/rss"], "verkkouutiset.fi": ["/feed/"],
 "hs.fi": ["/rss/tuoreimmat.xml"], "is.fi": ["/rss/tuoreimmat.xml"], "iltalehti.fi": ["/rss/uutiset.xml"],
 "mtvuutiset.fi": ["/api/feed/rss/uutiset_uusimmat"], "kuntalehti.fi": ["/feed", "/rss"], "kuntaliitto.fi": ["/rss.xml", "/feed"],
 "maaseuduntulevaisuus.fi/": [], "rakennuslehti.fi": ["/feed/"], "yrittajat.fi": ["/feed/", "/rss"], "aamulehti.fi": ["/rss", "/feed/rss"],
 "satakunnankansa.fi": ["/rss"], "lapinkansa.fi": ["/feed/rss"], "savonsanomat.fi": ["/feed/rss"], "ksml.fi": ["/feed/rss"],
 "pohjalainen.fi": ["/feed/rss"], "vasabladet.fi": ["/rss"], "hbl.fi": ["/rss"], "turunsanomat.fi": ["/rss"], "karjalainen.fi": ["/feed/rss"],
}
for d, ps in pohjat.items():
    for p in ps:
        u = f"https://www.{d}{p}" if not d.startswith("www") else f"https://{d}{p}"
        try:
            x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=15).read().decode("utf-8", "replace")
            n = len(re.findall(r"<item[ >]|<entry[ >]", x))
            if n: print(f"OK {n:3} {u}"); break
        except Exception as e: pass
    else: print(f"-- {d}")
