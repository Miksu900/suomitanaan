"""Kärkiuutiset – Miikan oma apuväline Facebook-postauksiin.
Lukee Uskontovahdin arkiston (uskontovahti.json), pisteyttää viimeisen 30 päivän uutiset sen mukaan, kuinka hyvä
ja helppo niistä on tehdä iskevä Facebook-postaus, ja
  * päivittää yksityisen sivun faktapiste.fi/api/oma/karki?k=...  (kuukauden TOP 10 + valmiit luonnokset)
  * lähettää aamulla Telegramiin "3 parasta tänään" valmiine teksteineen.
Tila: karki.json (haara karki-tila): pisteet ja luonnokset välimuistissa, lähetetyt.
Luonnokset perustuvat vain uutisen omiin tietoihin; mitään ei keksitä."""
import os, re, json, html, hashlib, urllib.request, datetime

AK = os.environ.get("AK", "").strip(); TG = os.environ.get("TG", "").strip()
CHAT = "1893930799"
UA = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
NYT = datetime.datetime.now(datetime.timezone.utc)
FI = datetime.timezone(datetime.timedelta(hours=2))

ARVIO = """Arvioit uutisia Miika Koskelan Facebook-sivua varten. Miika kirjoittaa suoria, islamkriittisiä ja maahanmuuttokriittisiä
kommentteja suomalaiselle yleisölle. Pisteytä jokainen uutinen 0–10 sen mukaan, kuinka hyvän ja helpon Facebook-postauksen siitä saa:
+ Suomi-kytkös (suomalainen kunta, raha, päätös, viranomainen, poliitikko) painaa eniten; Euroopan jutut ovat hyviä, jos ne ovat konkreettisia
+ konkreettisuus: luku, summa, nimi, päätös tai tapahtuma, jonka voi todentaa otsikosta
+ tunnereaktio: yllätys, ärtymys, epäkohta, kaksinaismoralismi, veronmaksajien raha
+ helppous: otsikon kuvakaappaus riittää todisteeksi, asia selviää yhdellä lauseella
+ tuoreus
- tylsä, abstrakti, pelkkä tilasto ilman kärkeä, urheilu, ulkomaiden sota ilman Suomi/Eurooppa-kytköstä, yksityishenkilöt
Vastaa pelkkänä JSON-listana: [{"i":0,"p":7,"miksi":"max 12 sanaa"}]"""

LUONNOS = """Kirjoitat Miika Koskelan Facebook-postauksen luonnoksen HÄNEN OMALLA TYYLILLÄÄN. Tyyliprofiili (hänen omista teksteistään):
- aloittaa väitteellä tai varoituksella ("Meidän suomalaisten ei pidä olla naiiveja…", "Ei kannata olla naiivi.")
- puhekielinen mutta vakava sävy: "No ei sillä, että…", "kuten arvaattekin", "niin", "kyllä"
- pitkän virkkeen jälkeen lyhyt isku: "Ei mitään. Ei yhtään mitään." / "Sitä ei enää takaisin saa."
- nimeää vastapuolen suoraan: "vihervasemmisto", "vasemmisto ja islamistit"
- vertaa usein Ruotsiin tai Eurooppaan: "Ruotsissa on jo…, joten ei pidä olla naiivi, etteikö täällä Suomessakin…"
- käyttää omaa kokemusta todisteena ("Kysyin itse…")
- lopettaa vaatimukseen tai johtopäätökseen ("Viranomaisten pitäisi vaatia ja määrätä…") tai joskus kysymykseen lukijalle
- ei hymiöitä, ei hashtageja, ei linkkejä, ei englanninkielisiä sanoja; 3–7 virkettä; oikeinkirjoitus kunnossa
ESIMERKKEJÄ hänen teksteistään:
1) "Meidän suomalaisten ei pidä olla naiiveja islamin motiivien suhteen. Ruotsissa on jo ollut valtavasti tätä naisten alistamista, joten ei pidä olla naiivi, etteikö sitä olisi täällä Suomessakin. Tämä on šarialain noudattamista ja vihervasemmiston mukaan sitä "parempaa" naisten alistamista."
2) "Läpinäkyvyys. Tällä Turun moskeija on mainostanut arvojaan. Läpinäkyvyydestä ei kuitenkaan ole tietoakaan. Kysyin itse säätiöltä, mistä varat ovat peräisin, ja kuten arvaattekin, vastauksena oli vastaamattomuus. Ei mitään. Ei yhtään mitään, vaan jälleen vastauksena hiljaisuus. Viranomaisten pitäisi vaatia ja määrätä, että koko moskeijahanke perutaan."
3) "Ei kannata olla naiivi. Niin vasemmistoa kuin islamisteja vetää yhteen voimakas viha Israelia kohtaan."
SÄÄNNÖT: Käytä VAIN uutisen tietoja (otsikko, kuvaus, teksti) – älä keksi lukuja, nimiä, tapahtumia tai omia kokemuksia, joita Miikalla ei uutisen perusteella ole.
Mielipide saa olla selvä, mutta faktat pitää pystyä todentamaan uutisesta. Älä yleistä kokonaista uskonto- tai kansanryhmää rikollisiksi
(puhu islamismista, islamisteista, päättäjistä tai järjestöistä, kun asia koskee niitä). Älä kehota poistamaan ihmisiä maasta uskonnon perusteella.
Vastaa pelkkänä JSON-objektina:
{"teksti": "postauksen teksti, viimeisellä rivillä 'Lähde: <media>'", "kuva": "mikä kuvakaappaus kannattaa ottaa (esim. otsikko + ingressi)",
 "koukku": "postauksen ydin yhdellä lauseella"}"""

def claude(system, user, malli, tokens):
    if not AK: return None
    for m in (malli, "claude-haiku-4-5"):
        d = json.dumps({"model": m, "max_tokens": tokens, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.anthropic.com/v1/messages", d,
                {"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"}), timeout=180).read())
            return r["content"][0]["text"]
        except Exception as e: print("CLAUDE-VIRHE", m, str(e)[:200])
    return None

def json_osa(t, a="["):
    try: return json.loads(t[t.index(a):t.rindex("]" if a == "[" else "}") + 1])
    except Exception: return None

def teksti(url):
    if "news.google.com" in url: return ""
    try: s = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "replace")
    except Exception: return ""
    kpl = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p))).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", s, re.S | re.I)]
    return "\n".join(p for p in kpl if len(p) > 40 and not re.search(r"evästeet|cookie|tilaa |kirjaudu", p, re.I))[:8000]

def tg(t):
    if not TG: print(t[:500]); return
    d = json.dumps({"chat_id": CHAT, "text": t, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    try: urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TG}/sendMessage", d, {"content-type": "application/json"}), timeout=30)
    except Exception as e: print("TG-VIRHE", e)

def pvm(t): return f"{int(t[8:10])}.{int(t[5:7])}."

def sivu(top, paivitetty):
    kortit = []
    for n, x in enumerate(top, 1):
        l = x.get("luonnos", {})
        kortit.append(f"""<article><div class="n">{n}</div><div class="b">
<div class="m"><span class="p">{x['p']}/10</span> {html.escape(x.get('l',''))} · {pvm(x['t'])}{' · Eurooppa' if x.get('a') == 'eu' else ''}</div>
<h2><a href="{html.escape(x['u'])}" target="_blank" rel="noopener noreferrer">{html.escape(x['o'])}</a></h2>
<p class="miksi">🎯 {html.escape(x.get('miksi',''))}</p>
{f'<p class="kuva">📸 {html.escape(l.get("kuva",""))}</p>' if l.get('kuva') else ''}
{f'<div class="t"><pre>{html.escape(l.get("teksti",""))}</pre><button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);this.textContent=&quot;Kopioitu ✓&quot;">Kopioi teksti</button></div>' if l.get('teksti') else ''}
</div></article>""")
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kärkiuutiset</title><meta name="robots" content="noindex,nofollow"><style>
:root{{--bg:#f6f5f2;--card:#fff;--tx:#1b1d22;--mu:#666;--ac:#c62828;--bd:#e3e0da}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--card:#1d2026;--tx:#eceae6;--mu:#9a9a9a;--ac:#ff6b5e;--bd:#2c3038}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,sans-serif}}main{{max-width:760px;margin:auto;padding:16px}}
h1{{font-size:24px;margin:8px 0 4px}}.sub{{color:var(--mu);margin:0 0 16px}}
article{{display:flex;gap:12px;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px;margin:12px 0}}
.n{{font-weight:800;font-size:22px;color:var(--ac);min-width:28px}}.b{{flex:1;min-width:0}}.m{{color:var(--mu);font-size:14px}}
.p{{background:var(--ac);color:#fff;border-radius:6px;padding:1px 7px;font-weight:700}}h2{{font-size:18px;margin:6px 0}}
h2 a{{color:inherit}}.miksi,.kuva{{margin:4px 0;font-size:15px}}pre{{white-space:pre-wrap;font:15px/1.5 system-ui;background:var(--bg);border-radius:8px;padding:10px;margin:8px 0}}
button{{border:0;border-radius:8px;padding:8px 14px;background:var(--ac);color:#fff;font-weight:700}}</style></head><body><main>
<h1>Kuukauden kärkiuutiset</h1><p class="sub">Viimeisen 30 päivän parhaat aiheet Facebook-postaukseen. Päivitetty {paivitetty}.</p>
{''.join(kortit) or '<p>Ei vielä pisteytettyjä uutisia.</p>'}</main></body></html>"""

if __name__ == "__main__":
    try: tila = json.load(open("karki.json"))
    except Exception: tila = {}
    pisteet, luonnokset, lahetetyt = tila.get("pisteet", {}), tila.get("luonnokset2", {}), set(tila.get("lahetetyt", []))
    arkisto = json.load(open("uskontovahti.json")).get("arkisto", [])
    raja30 = (NYT - datetime.timedelta(days=30)).isoformat()[:16]
    kk = [x for x in arkisto if x.get("t", "") >= raja30 and x.get("u")]
    uudet = [x for x in kk if x["u"] not in pisteet]
    print(f"30 pv: {len(kk)} uutista, pisteyttämättä {len(uudet)}")
    for i in range(0, len(uudet), 50):
        osa = uudet[i:i + 50]
        t = claude(ARVIO, json.dumps([{"i": n, "o": x["o"], "k": (x.get("k") or "")[:200], "l": x.get("l", ""),
                                         "alue": "Eurooppa" if x.get("a") == "eu" else "Suomi"} for n, x in enumerate(osa)], ensure_ascii=False),
                   "claude-haiku-4-5", 4000)
        for r in json_osa(t) or []:
            try: pisteet[osa[int(r["i"])]["u"]] = {"p": int(r["p"]), "miksi": str(r.get("miksi", ""))[:120]}
            except Exception: pass
    for x in kk: x.update(pisteet.get(x["u"], {"p": 0, "miksi": ""}))
    jarj = sorted(kk, key=lambda x: (x["p"], x["t"]), reverse=True)
    # samasta aiheesta vain yksi (otsikon alun perusteella)
    nahty, top = set(), []
    for x in jarj:
        a = re.sub(r"\W+", "", x["o"].lower())[:40]
        if a in nahty: continue
        nahty.add(a); top.append(x)
        if len(top) == 10: break
    raja3 = (NYT - datetime.timedelta(days=3)).isoformat()[:16]
    tanaan = [x for x in jarj if x["t"] >= raja3 and x["u"] not in lahetetyt and x["p"] >= 6][:3]
    for x in {id(y): y for y in top + tanaan}.values():
        if x["u"] in luonnokset: continue
        t = claude(LUONNOS, f"OTSIKKO: {x['o']}\nMEDIA: {x.get('l','')}\nPVM: {x['t'][:10]}\nKUVAUS: {x.get('k','')}\n\nTEKSTI:\n{teksti(x['u']) or '(ei saatavilla – käytä vain otsikkoa ja kuvausta)'}",
                   "claude-sonnet-4-5", 1200)
        l = json_osa(t, "{")
        if l: luonnokset[x["u"]] = l
    for x in top + tanaan: x["luonnos"] = luonnokset.get(x["u"], {})
    nyt = NYT.astimezone(FI).strftime("%-d.%-m.%Y klo %H.%M")
    hallinta = hashlib.sha256((os.environ["CF"].strip() + "-faktapiste").encode()).hexdigest()[:40]
    k = hashlib.sha256(("oma-karki" + hallinta).encode()).hexdigest()[:32]
    url = f"https://faktapiste.fi/api/oma/karki?k={k}"
    r = urllib.request.Request("https://faktapiste.fi/api/hallinta/oma", json.dumps({"nimi": "karki", "html": sivu(top, nyt)}).encode(),
                               {"content-type": "application/json", "x-avain": hallinta, **UA})
    print("::notice title=Sivu::" + urllib.request.urlopen(r, timeout=30).read().decode()[:200])
    if os.environ.get("TAPAHTUMA") == "schedule" or os.environ.get("LAHETA") == "1":
        if tanaan:
            osat = []
            for n, x in enumerate(tanaan, 1):
                l = x["luonnos"]
                osat.append(f"<b>{n}. {html.escape(x['o'])}</b>\n<i>{html.escape(x.get('l',''))}, {pvm(x['t'])} · {x['p']}/10</i>\n🎯 {html.escape(x['miksi'])}\n"
                            + (f"📸 {html.escape(l.get('kuva',''))}\n\n<code>{html.escape(l.get('teksti',''))}</code>\n" if l else "") + f"{x['u']}")
            viesti = "🔥 <b>Päivän 3 kärkiuutista Faceen</b>\n(paina tekstiä, niin se kopioituu)\n\n" + "\n\n➖➖➖\n\n".join(osat) + f"\n\n📋 <a href=\"{url}\">Kuukauden TOP 10</a>"
            if len(viesti) > 4000:   # Telegramin raja: lähetetään erikseen
                tg("🔥 <b>Päivän 3 kärkiuutista Faceen</b>\n(paina tekstiä, niin se kopioituu)")
                for o in osat: tg(o[:4000])
                tg(f"📋 <a href=\"{url}\">Kuukauden TOP 10</a>")
            else: tg(viesti)
            lahetetyt.update(x["u"] for x in tanaan)
        else: tg(f"Ei uusia kärkiuutisia tänään. 📋 <a href=\"{url}\">Kuukauden TOP 10</a>")
    pidettavat = {x["u"] for x in arkisto if x.get("t", "") >= (NYT - datetime.timedelta(days=45)).isoformat()[:16]}
    json.dump({"pisteet": {u: v for u, v in pisteet.items() if u in pidettavat}, "luonnokset2": {u: v for u, v in luonnokset.items() if u in pidettavat},
               "lahetetyt": sorted(lahetetyt)[-3000:]}, open("karki.json", "w"), ensure_ascii=False)
    print(f"::notice title=Kärkiuutiset::TOP {len(top)}, tänään {len(tanaan)}; sivu {url[:45]}…")
