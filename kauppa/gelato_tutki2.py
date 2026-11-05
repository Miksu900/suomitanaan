"""Gelato: etsi juliste- ja kehystetyt juliste-UIDt (30x40, 50x70) ja laske hinta + toimitus Ylivieskaan."""
import os, json, urllib.request, urllib.error
K = os.environ["GK"].strip()
H = {"X-API-KEY": K, "content-type": "application/json", "user-agent": "NetvoKauppa/1.0", "accept": "application/json"}
def api(url, data=None):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, json.dumps(data).encode() if data else None, H), timeout=40).read())
    except urllib.error.HTTPError as e: return {"VIRHE": e.code, "viesti": e.read().decode()[:300]}
def etsi(cat, ehdot, maks=1500):
    tulos = []
    for off in range(0, maks, 100):
        h = api(f"https://product.gelatoapis.com/v3/catalogs/{cat}/products:search", {"limit": 100, "offset": off})
        ps = h.get("products", []) if "VIRHE" not in h else []
        tulos += [p["productUid"] for p in ps if all(e in p["productUid"] for e in ehdot)]
        if len(ps) < 100: break
    return tulos
valitut = []
for cat, ehdot in [("posters", ["300x400", "_ver"]), ("posters", ["500x700", "_ver"]), ("framed-posters", ["300x400", "_ver", "black"]), ("framed-posters", ["500x700", "_ver", "black"])]:
    u = etsi(cat, ehdot); print(f"{cat} {ehdot}: {len(u)}"); [print("  ", x) for x in u[:6]]
    halvin = [x for x in u if "uncoated" in x and "200-gsm" in x] or u
    if halvin: valitut.append(halvin[0])
valitut += ["mug_product_msz_11-oz_mmat_ceramic-white_cl_4-0", "canvas_12x16-inch-300x400-mm_canvas_wood-fsc-slim_4-0_ver"]
for uid in valitut:
    q = api("https://order.gelatoapis.com/v4/orders:quote", {"orderReferenceId": "testi-1", "customerReferenceId": "netvo", "currency": "EUR",
        "recipient": {"country": "FI", "firstName": "Testi", "lastName": "Asiakas", "addressLine1": "Riihikatu 3", "city": "Ylivieska", "postCode": "84100", "email": "info@netvo.fi"},
        "products": [{"itemReferenceId": "1", "productUid": uid, "quantity": 1, "files": [{"type": "default", "url": "https://faktapiste.fi/og.png"}]}]})
    if "VIRHE" in q: print("QUOTE", uid[:90], q); continue
    for qu in q.get("quotes", []):
        print("QUOTE", uid[:110], "\n   tuotanto:", qu.get("fulfillmentCountry"), "tuote:", [(pp.get("price"), pp.get("currency")) for pp in qu.get("products", [])],
              "\n   toimitus:", [(m.get("name"), m.get("price"), m.get("minDeliveryDays"), m.get("maxDeliveryDays")) for m in qu.get("shipmentMethods", [])][:3])
