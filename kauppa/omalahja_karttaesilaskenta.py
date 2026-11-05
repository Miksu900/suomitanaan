"""Omalahja: esilaskee karttojen data valmiille paikoille ja suurimmille kaupungeille (Overpass GitHub Actionsista) ja tallentaa sen R2:een Workerin kautta.
Kunnioittaa Overpassin käyttöehtoja: yksi pyyntö kerrallaan, tauko välissä, tunnistettava User-Agent."""
import os, json, time, urllib.request, urllib.parse, urllib.error
POHJA = "https://omalahja.fi"; AV = os.environ["HALLINTA"]; UA = "Omalahja/1.0 (+https://omalahja.fi; info@omalahja.fi)"
def get(u, h=None, t=60): return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": UA, **(h or {})}), timeout=t).read())
PAIKAT = [(60.1699, 24.9384, 2.5), (60.1699, 24.9384, 2.2), (61.4981, 23.761, 2.5), (61.4981, 23.761, 2.2), (60.4518, 22.2666, 2.5), (65.0121, 25.4651, 2.5), (62.2426, 25.7473, 2.5),
          (62.8924, 27.677, 2.5), (66.5039, 25.7294, 2.5), (64.0736, 24.5341, 2), (64.0736, 24.5341, 1.8),
          (31.7767, 35.2345, 0.9), (31.7049, 35.2023, 1.3), (32.7019, 35.2978, 1.6), (32.83, 35.585, 11), (32.8807, 35.5751, 1.4), (31.838, 35.539, 1.8), (31.8667, 35.45, 2.2),
          (32.7466, 35.342, 1.1), (31.7784, 35.244, 1), (31.8393, 34.9895, 1.8), (28.5392, 33.975, 3.5), (31.7717, 35.26, 1.1)]
KAUPUNGIT = os.environ.get("KAUPUNGIT", "Helsinki,Espoo,Tampere,Vantaa,Oulu,Turku,Jyväskylä,Kuopio,Lahti,Pori,Kouvola,Joensuu,Lappeenranta,Hämeenlinna,Vaasa,Seinäjoki,Rovaniemi,Mikkeli,Kotka,Salo,Porvoo,Kokkola,Lohja,Hyvinkää,Nurmijärvi,Järvenpää,Rauma,Kirkkonummi,Tuusula,Kajaani,Savonlinna,Kerava,Nokia,Ylöjärvi,Kangasala,Vihti,Riihimäki,Raahe,Imatra,Raisio,Kemi,Tornio,Iisalmi,Ylivieska,Kalajoki,Nivala,Haapajärvi,Pietarsaari,Lapua,Kuusamo").split(",")
SADE = {"city": 2.5, "town": 2, "municipality": 2.5, "village": 1, "hamlet": 0.8, "suburb": 1.5, "neighbourhood": 0.8, "island": 2, "lake": 4}
for k in KAUPUNGIT:
    try:
        r = get(f"{POHJA}/api/kartta/haku?q={urllib.parse.quote(k)}&fi=1")
        if r: p = r[0]; PAIKAT.append((round(float(p["lat"]), 4), round(float(p["lon"]), 4), SADE.get(p.get("addresstype") or p.get("type"), 1.5)))
    except Exception as e: print("haku", k, e)
    time.sleep(1.2)
tehty = set(); ok = ohi = virhe = 0
for lat, lon, sade in PAIKAT:
    q = f"lat={lat:.4f}&lon={lon:.4f}&sade={sade}"
    try:
        k = get(f"{POHJA}/api/kartta/kysely?{q}")
        if k["avain"] in tehty: continue
        tehty.add(k["avain"])
        if get(f"{POHJA}/api/hallinta/kartta?{q}", {"x-avain": AV}).get("on"): ohi += 1; print("on jo", k["avain"]); continue
        data = None
        for url in ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]:
            try:
                t0 = time.time(); data = urllib.request.urlopen(urllib.request.Request(url, urllib.parse.urlencode({"data": k["kysely"]}).encode(), {"user-agent": UA}), timeout=200).read()
                if data[:1] == b"{" and b'"elements"' in data[:2000] and not (b'"remark"' in data[-400:] and b"rror" in data[-400:]): print(k["avain"], url.split("/")[2], len(data), round(time.time() - t0), "s"); break
                data = None
            except Exception as e: print("overpass", url, e); data = None
        if not data: virhe += 1; continue
        req = urllib.request.Request(f"{POHJA}/api/hallinta/kartta?{q}", data, {"x-avain": AV, "content-type": "application/json", "user-agent": UA}, method="PUT")
        print(" tallennettu", urllib.request.urlopen(req, timeout=120).read()[:120]); ok += 1
    except Exception as e: virhe += 1; print("virhe", lat, lon, e)
    time.sleep(3)
print(f"::notice title=Esilaskenta::uusia {ok}, valmiina {ohi}, virheitä {virhe}, ruutuja {len(tehty)}")
