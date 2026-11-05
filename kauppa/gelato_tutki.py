"""Gelato-tutkimus: tarkistaa avaimen, listaa julistekatalogin ja hakee hinnat + toimitukset Suomeen."""
import os, json, urllib.request, urllib.error
K = os.environ["GK"].strip()
def api(url, data=None):
    r = urllib.request.Request(url, json.dumps(data).encode() if data else None, {"X-API-KEY": K, "content-type": "application/json", "user-agent": "NetvoKauppa/1.0", "accept": "application/json"})
    try: return json.loads(urllib.request.urlopen(r, timeout=40).read())
    except urllib.error.HTTPError as e: return {"VIRHE": e.code, "viesti": e.read().decode()[:400]}
kat = api("https://product.gelatoapis.com/v3/catalogs")
print("KATALOGIT:", json.dumps([c.get("catalogUid") for c in kat.get("data", kat if isinstance(kat, list) else [])])[:1500] if "VIRHE" not in kat else kat)
for cat in ["posters", "framed-posters", "mugs", "canvas"]:
    h = api(f"https://product.gelatoapis.com/v3/catalogs/{cat}/products:search", {"limit": 200, "offset": 0})
    if "VIRHE" in h: print(cat, h); continue
    ps = h.get("products", [])
    print(f"\n== {cat}: {len(ps)} tuotetta (näyte) ==")
    valitut = [p for p in ps if any(s in p["productUid"] for s in ("300x400", "500x700", "a3", "a4", "11-oz", "30x40", "50x70"))][:8] or ps[:6]
    for p in valitut:
        uid = p["productUid"]
        hinnat = api(f"https://product.gelatoapis.com/v3/products/{uid}/prices?country=FI&currency=EUR")
        hh = hinnat[0]["price"] if isinstance(hinnat, list) and hinnat else hinnat
        print(uid, "| hinta FI:", hh)
sm = api("https://shipment.gelatoapis.com/v1/shipment-methods?country=FI")
print("\nTOIMITUSTAVAT FI:", json.dumps(sm)[:1200])
