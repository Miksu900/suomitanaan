"""Omalahja: Gelato-selvitys. Tila 'tutki': tuotetiedot, kehysvärit, hinnat Ylivieskaan.
Tila 'luonnos': lataa testitiedosto omalahja.fi:hin, luo LUONNOS-tilaus (orderType draft), tarkista ja poista se.
Ei koskaan luo oikeaa tilausta."""
import os, sys, json, urllib.request, urllib.error
K = os.environ["GK"].strip()
H = {"X-API-KEY": K, "content-type": "application/json", "user-agent": "NetvoKauppa/1.0", "accept": "application/json"}
def api(url, data=None, method=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, json.dumps(data).encode() if data is not None else None, H, method=method), timeout=60)
        b = r.read(); return json.loads(b) if b.strip() else {"OK": r.status}
    except urllib.error.HTTPError as e: return {"VIRHE": e.code, "viesti": e.read().decode()[:600]}
def notice(t, m): print(f"::notice title={t}::{m}"[:3900])

def etsi(cat, ehdot, maks=3000):
    tulos = []
    for off in range(0, maks, 100):
        h = api(f"https://product.gelatoapis.com/v3/catalogs/{cat}/products:search", {"limit": 100, "offset": off})
        ps = h.get("products", []) if "VIRHE" not in h else []
        tulos += [p["productUid"] for p in ps if all(e in p["productUid"] for e in ehdot)]
        if len(ps) < 100: break
    return tulos

RECIP = {"country": "FI", "firstName": "Testi", "lastName": "Tilaus", "addressLine1": "Riihikatu 3 B 20", "city": "Ylivieska", "postCode": "84100", "email": "info@omalahja.fi"}
def quote(uid):
    q = api("https://order.gelatoapis.com/v4/orders:quote", {"orderReferenceId": "ol-testi", "customerReferenceId": "omalahja", "currency": "EUR", "recipient": RECIP,
        "products": [{"itemReferenceId": "1", "productUid": uid, "quantity": 1, "files": [{"type": "default", "url": "https://faktapiste.fi/og.png"}]}]})
    if "VIRHE" in q: return f"VIRHE {q['VIRHE']} {q['viesti'][:200]}"
    out = []
    for qu in q.get("quotes", []):
        out.append(f"{qu.get('fulfillmentCountry')} tuote {[pp.get('price') for pp in qu.get('products', [])]} toim {[(m.get('name'), m.get('price'), m.get('minDeliveryDays'), m.get('maxDeliveryDays')) for m in qu.get('shipmentMethods', [])][:2]}")
    return " | ".join(out)

tila = sys.argv[1] if len(sys.argv) > 1 else "tutki"
if tila == "tutki":
    for uid in ["flat_12x16-inch-300x400-mm_200-gsm-80lb-uncoated_4-0_ver", "canvas_12x16-inch-300x400-mm_canvas_wood-fsc-slim_4-0_ver",
                "frame_and_poster_product_frs_300x400-mm_frc_black_frm_aluminum_frp_w10xt22-mm_gt_plexiglass__pf_300x400-mm_pt_200-gsm-uncoated_cl_4-0_ct_none_prt_none_ver"]:
        d = api(f"https://product.gelatoapis.com/v3/products/{uid}")
        notice("Tuote " + uid[:40], json.dumps({k: d.get(k) for k in ("dimensions", "attributes", "VIRHE", "viesti")}, ensure_ascii=False)[:1500])
    for koko in ["300x400", "500x700"]:
        f = etsi("framed-posters", [koko, "_ver", "200-gsm-uncoated", "pf_" + koko, "ct_none", "prt_none"])
        notice(f"Kehykset {koko}", f"{len(f)}: " + " ; ".join(x.replace("frame_and_poster_product_", "") for x in f)[:3500])
    c = etsi("canvas", ["slim", "_ver", "4-0"])
    notice("Canvas slim", " ; ".join(c)[:3500])
    p = etsi("posters", ["200-gsm-80lb-uncoated", "_ver"])
    notice("Julisteet", " ; ".join(x.replace("flat_", "") for x in p)[:3500])
    extra = [x.strip() for x in os.environ.get("UIDS", "").split(",") if x.strip()]
    for uid in ["flat_12x16-inch-300x400-mm_200-gsm-80lb-uncoated_4-0_hor", "flat_20x28-inch-500x700-mm_200-gsm-80lb-uncoated_4-0_ver",
                "canvas_20x28-inch-500x700-mm_canvas_wood-fsc-slim_4-0_ver", "canvas_12x16-inch-300x400-mm_canvas_wood-fsc-slim_4-0_hor"] + extra:
        notice("Hinta " + uid[-60:], quote(uid))

elif tila == "luonnos":
    url = os.environ["TIEDOSTO"]
    uid = os.environ.get("UID") or "flat_12x16-inch-300x400-mm_200-gsm-80lb-uncoated_4-0_ver"
    d = api("https://order.gelatoapis.com/v4/orders", {"orderType": "draft", "orderReferenceId": "OLTESTI-" + os.environ.get("GITHUB_RUN_ID", "0"),
        "customerReferenceId": "omalahja-testi", "currency": "EUR",
        "items": [{"itemReferenceId": "1", "productUid": uid, "quantity": 1, "files": [{"type": "default", "url": url}]}],
        "shipmentMethodUid": "normal",
        "shippingAddress": {**RECIP, "phone": "0447777149"}})
    if "VIRHE" in d: notice("Luonnos EPÄONNISTUI", json.dumps(d, ensure_ascii=False)[:1500]); sys.exit(1)
    oid = d.get("id")
    notice("Luonnos luotu", json.dumps({k: d.get(k) for k in ("id", "orderType", "fulfillmentStatus", "financialStatus", "currency")}, ensure_ascii=False))
    g = api(f"https://order.gelatoapis.com/v4/orders/{oid}")
    it = (g.get("items") or [{}])[0]
    notice("Luonnoksen tiedot", json.dumps({"orderType": g.get("orderType"), "status": g.get("fulfillmentStatus"), "tuote": it.get("productUid"), "tiedostot": it.get("files"),
        "osoite": (g.get("shippingAddress") or {}).get("city"), "hinta": (g.get("receipts") or [{}])[0].get("totalInclVat") if g.get("receipts") else None}, ensure_ascii=False)[:1800])
    x = api(f"https://order.gelatoapis.com/v4/orders/{oid}", method="DELETE")
    notice("Luonnos poistettu", json.dumps(x)[:300])
    g2 = api(f"https://order.gelatoapis.com/v4/orders/{oid}")
    notice("Tarkistus poiston jälkeen", json.dumps({k: g2.get(k) for k in ("VIRHE", "orderType", "fulfillmentStatus")})[:300])
