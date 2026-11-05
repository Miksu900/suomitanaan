"""Omalahja: uusien tuotetyyppien selvitys Gelatosta. Listaa katalogien tuotteet (suodattimilla), tuotetiedot ja hinnat Ylivieskaan."""
import os, sys, json, urllib.request, urllib.error
K = os.environ["GK"].strip()
H = {"X-API-KEY": K, "content-type": "application/json", "user-agent": "NetvoKauppa/1.0", "accept": "application/json"}
def api(url, data=None):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, json.dumps(data).encode() if data is not None else None, H), timeout=60).read())
    except urllib.error.HTTPError as e: return {"VIRHE": e.code, "viesti": e.read().decode()[:300]}
def n(t, m): print(f"::notice title={t}::{m}"[:3800], flush=True)
tila = sys.argv[1]
if tila == "katalogit":
    c = api("https://product.gelatoapis.com/v3/catalogs")
    n("Katalogit", " ; ".join(x.get("catalogUid", "") for x in (c.get("data") or c if isinstance(c, list) else c.get("data", []))) if "VIRHE" not in c else json.dumps(c))
    for cat, ehdot in json.loads(os.environ["HAUT"]):
        tulos = []
        for off in range(0, 3000, 100):
            h = api(f"https://product.gelatoapis.com/v3/catalogs/{cat}/products:search", {"limit": 100, "offset": off})
            ps = h.get("products", []) if "VIRHE" not in h else []
            tulos += [p["productUid"] for p in ps if all(e in p["productUid"] for e in ehdot)]
            if len(ps) < 100: break
        n(f"{cat} {ehdot} ({len(tulos)})", " ; ".join(tulos[:40]))
elif tila == "tiedot":
    RECIP = {"country": "FI", "firstName": "Testi", "lastName": "Tilaus", "addressLine1": "Riihikatu 3 B 20", "city": "Ylivieska", "postCode": "84100", "email": "info@omalahja.fi"}
    for uid in [x.strip() for x in os.environ["UIDS"].split(",") if x.strip()]:
        d = api(f"https://product.gelatoapis.com/v3/products/{uid}")
        dims = {k: v.get("value") for k, v in (d.get("dimensions") or {}).items()} if "VIRHE" not in d else d
        q = api("https://order.gelatoapis.com/v4/orders:quote", {"orderReferenceId": "ol-t", "customerReferenceId": "omalahja", "currency": "EUR", "recipient": RECIP,
            "products": [{"itemReferenceId": "1", "productUid": uid, "quantity": int(os.environ.get("MAARA", "1")), "files": [{"type": "default", "url": "https://omalahja.fi/kuvat/nimi-perhe.jpg"}]}]})
        hq = "VIRHE " + json.dumps(q)[:200] if "VIRHE" in q else " | ".join(f"{x.get('fulfillmentCountry')} tuote {[pp.get('price') for pp in x.get('products', [])]} toim {[(m.get('name'), m.get('price'), m.get('minDeliveryDays'), m.get('maxDeliveryDays')) for m in x.get('shipmentMethods', [])][:2]}" for x in q.get("quotes", []))
        n("UID " + uid[-70:], f"mitat {json.dumps(dims)[:600]} || hinta {hq}")
