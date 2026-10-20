#!/usr/bin/env python3
"""Lakitoimistot YTJ:n avoimesta datasta (PRH): päätoimiala 69101 asianajotoimistot ja 69102 muut lakiasiainpalvelut.
Kuntien koordinaatit OpenStreetMapin Nominatimista (välimuisti data/kunnat.json), jotta selain voi etsiä lähimmät."""
import json, os, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data", "toimistot.json")
KOORD = os.path.join(ROOT, "data", "kunnat.json")
YTJ = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies?mainBusinessLine={c}&page={p}"
UA = {"User-Agent": "Pykalavahti/1.0 (miika@eduskuntaseuranta.fi)"}
LAJI = {"69101": "Asianajotoimisto", "69102": "Lakiasiaintoimisto"}


def hae(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e; time.sleep(4 * (i + 1))
    raise err


def nimi(c):
    n = [x for x in c.get("names", []) if not x.get("endDate") and str(x.get("type")) == "1"]
    return (n or c.get("names") or [{"name": "?"}])[0]["name"]


def main():
    toim = []
    for koodi in LAJI:
        p = 1
        while True:
            d = hae(YTJ.format(c=koodi, p=p))
            cs = d.get("companies", [])
            for c in cs:
                if c.get("companySituations") or c.get("endDate") or str(c.get("status")) != "2":
                    continue
                ad = sorted(c.get("addresses", []), key=lambda a: a.get("type", 9))
                a = ad[0] if ad else {}
                kunta = next((x["city"] for x in a.get("postOffices", []) if str(x.get("languageCode")) == "1"), "")
                katu = " ".join(x for x in (a.get("street", ""), a.get("buildingNumber", ""), a.get("entrance", "")) if x)
                web = (c.get("website") or {}).get("url", "")
                if web and not web.startswith("http"):
                    web = "https://" + web
                toim.append({"n": nimi(c), "y": c["businessId"]["value"], "l": LAJI[koodi], "k": kunta.title(), "o": katu.title(),
                             "pn": a.get("postCode", ""), "w": web})
            if len(cs) < 100:
                break
            p += 1
            time.sleep(0.5)
        print(koodi, "valmis, yhteensä", len(toim))
    # kuntien koordinaatit
    koord = json.load(open(KOORD, encoding="utf-8")) if os.path.exists(KOORD) else {}
    for k in sorted({t["k"] for t in toim if t["k"]}):
        if k in koord:
            continue
        q = urllib.parse.urlencode({"q": f"{k}, Finland", "format": "json", "limit": 1, "countrycodes": "fi"})
        try:
            r = hae("https://nominatim.openstreetmap.org/search?" + q)
            koord[k] = [round(float(r[0]["lat"]), 4), round(float(r[0]["lon"]), 4)] if r else None
        except Exception:
            koord[k] = None
        time.sleep(1.1)
    json.dump(koord, open(KOORD, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    for t in toim:
        t["c"] = koord.get(t["k"])
    toim.sort(key=lambda t: (t["k"], t["n"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"haettu": time.strftime("%Y-%m-%d"), "t": toim}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("toimistoja", len(toim), "kuntia", len({t['k'] for t in toim}))


if __name__ == "__main__":
    main()
