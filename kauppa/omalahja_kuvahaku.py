"""Omalahja: Unsplash-kuvaehdokkaat etusivulle. Hakee ehdokkaat, lataa pienet esikatselut ja tekee kontaktiarkit (out/)."""
import json, re, urllib.request, urllib.parse, io, os
from PIL import Image, ImageDraw
UA = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36", "accept": "application/json,text/html"}
HAUT = os.environ.get("HAUT", "empty frame wall|scandinavian interior wall|blank poster frame|cozy living room wall art|minimal beige wall interior|nordic living room|picture frame mockup|frames on wall interior").split("|")
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()
ehd, nahty = [], set()
for q in HAUT:
    loydot = []
    try:
        d = json.loads(get("https://unsplash.com/napi/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": 20, "orientation": "landscape"})))
        for r in d.get("results", []):
            raw = r["urls"]["raw"]
            if "plus.unsplash.com" in raw or r.get("premium") or r.get("plus"): continue
            pid = re.search(r"(photo-[0-9a-f-]+)", raw)
            if pid: loydot.append({"id": pid.group(1), "alt": r.get("alt_description"), "tekija": r.get("user", {}).get("name"), "w": r.get("width"), "h": r.get("height")})
    except Exception as e:
        print("napi", q, e)
        try:
            h = get("https://unsplash.com/s/photos/" + urllib.parse.quote(q.replace(" ", "-"))).decode("utf8", "ignore")
            loydot = [{"id": x, "alt": "", "tekija": ""} for x in dict.fromkeys(re.findall(r"images\.unsplash\.com/(photo-[0-9a-f]{10,}-[0-9a-f]{6,})", h))]
        except Exception as e2: print("html", q, e2)
    print(q, len(loydot))
    for l in loydot:
        if l["id"] in nahty: continue
        nahty.add(l["id"]); l["haku"] = q; ehd.append(l)
os.makedirs("out", exist_ok=True)
kuvat = []
for i, e in enumerate(ehd[:96]):
    try:
        b = get(f"https://images.unsplash.com/{e['id']}?auto=format&fit=crop&w=420&h=280&q=60&fm=jpg")
        kuvat.append((i, Image.open(io.BytesIO(b)).convert("RGB").resize((420, 280))))
        e["n"] = i
    except Exception as x: print("lataus", e["id"], x)
for a in range(0, len(kuvat), 12):
    arkki = Image.new("RGB", (3 * 430, 4 * 300), "white"); dr = ImageDraw.Draw(arkki)
    for j, (n, im) in enumerate(kuvat[a:a + 12]):
        x, y = (j % 3) * 430, (j // 3) * 300; arkki.paste(im, (x, y)); dr.rectangle([x, y, x + 46, y + 26], fill="black"); dr.text((x + 6, y + 6), str(n), fill="white")
    arkki.save(f"out/arkki-{a // 12 + 1}.jpg", quality=80)
json.dump(ehd, open("out/ehdokkaat.json", "w"), ensure_ascii=False, indent=1)
print("ehdokkaita", len(ehd), "kuvia", len(kuvat))
