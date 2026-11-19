"""Puoluevahti – Miikan oma seuranta: mitä maahanmuutto- ja kehitysapupolitiikkaa puolueet Suomessa ja Euroopassa
tekevät tai haluavat tehdä. Lähteet: Google Newsin hakusyötteet (puolue + aihe, paikallisilla kielillä) sekä
eduskunnan ja valtioneuvoston tiedotteet. Claude luokittelee jokaisen uutisen: puolue, maa, aihe, suunta
(tiukentaa / löysentää / lisää / leikkaa / muu), tekeekö vai haluaako tehdä, ja yhden lauseen tiivistelmä suomeksi.
Tulokset: yksityinen sivu faktapiste.fi/api/oma/puolueet?k=... ja Telegram (Suomen uudet heti aamulla, Euroopan koonti maanantaisin).
Tila: puoluevahti.json (haara puoluevahti-tila). Vain julkista tietoa puolueiden ja poliitikkojen julkisesta toiminnasta."""
import os, re, json, html, hashlib, urllib.request, urllib.parse, datetime, email.utils

AK = os.environ.get("AK", "").strip(); TG = os.environ.get("TG", "").strip(); CHAT = "1893930799"
UA = {"user-agent": "Mozilla/5.0 (Faktapiste-seuranta; +https://faktapiste.fi)"}
NYT = datetime.datetime.now(datetime.timezone.utc); FI = datetime.timezone(datetime.timedelta(hours=2))
TAYSI = os.environ.get("TAYSI") == "1"

def gn(q, kieli="fi"):
    hl, gl = {"fi": ("fi", "FI"), "sv": ("sv", "SE"), "da": ("da", "DK"), "no": ("no", "NO"), "de": ("de", "DE"), "fr": ("fr", "FR"),
              "nl": ("nl", "NL"), "en": ("en-GB", "GB")}[kieli]
    return f"https://news.google.com/rss/search?hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}&q=" + urllib.parse.quote(q + ("" if TAYSI else " when:3d"))

AIKA = {"fi": "(maahanmuutto OR turvapaikka OR kehitysapu OR kehitysyhteistyö OR pakolaiskiintiö OR perheenyhdistäminen OR kansalaisuus)",
        "sv": "(invandring OR migration OR asyl OR bistånd OR flyktingkvot OR medborgarskap)",
        "da": "(indvandring OR asyl OR udviklingsbistand OR flygtninge)",
        "no": "(innvandring OR asyl OR bistand OR flyktninger)",
        "de": "(Migration OR Asyl OR Entwicklungshilfe OR Abschiebung OR Einbürgerung)",
        "fr": "(immigration OR asile OR \"aide au développement\" OR expulsions)",
        "nl": "(migratie OR asiel OR ontwikkelingshulp OR immigratie)",
        "en": "(immigration OR asylum OR \"foreign aid\" OR \"overseas aid\" OR deportation)"}
PUOLUEET = {   # maa: (kieli, [puolueet])
    "Suomi": ("fi", ["SDP", "Kokoomus", "perussuomalaiset", "keskusta", "vihreät", "vasemmistoliitto", "RKP", "kristillisdemokraatit", "Liike Nyt"]),
    "Ruotsi": ("sv", ["Socialdemokraterna", "Moderaterna", "Sverigedemokraterna", "Vänsterpartiet", "Miljöpartiet", "Liberalerna", "Kristdemokraterna", "Centerpartiet"]),
    "Tanska": ("da", ["Socialdemokratiet", "Venstre", "Dansk Folkeparti", "Danmarksdemokraterne", "Enhedslisten", "SF"]),
    "Norja": ("no", ["Arbeiderpartiet", "Høyre", "Fremskrittspartiet", "SV"]),
    "Saksa": ("de", ["SPD", "CDU", "AfD", "Grüne", "Linke", "CSU"]),
    "Ranska": ("fr", ["Rassemblement national", "Renaissance", "LFI", "Les Républicains"]),
    "Alankomaat": ("nl", ["PVV", "VVD", "GroenLinks-PvdA", "NSC"]),
    "Iso-Britannia": ("en", ["Labour", "Conservatives", "Reform UK"]),
    "EU": ("en", ["European Parliament migration pact", "European Commission migration", "EPP migration", "S&D migration", "Renew migration", "Patriots for Europe"]),
}
SYOTTEET = []
for maa, (kl, ps) in PUOLUEET.items():
    for p in ps: SYOTTEET.append((maa, gn(f'"{p}" {AIKA[kl]}' if maa != "EU" else p, kl)))
SYOTTEET += [("Suomi", gn(f"site:{d} {AIKA['fi']}")) for d in ("eduskunta.fi", "valtioneuvosto.fi", "intermin.fi", "um.fi")]

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")

def pvm(s):
    try: return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).isoformat()[:16]
    except Exception: return NYT.isoformat()[:16]

def kohteet():
    out = []
    for maa, url in SYOTTEET:
        try: x = hae(url)
        except Exception as e: print("SYÖTEVIRHE", maa, str(e)[:80]); continue
        for it in re.findall(r"<item>(.*?)</item>", x, re.S):
            g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", (re.search(rf"<{t}[^>]*>(.*?)</{t}>", it, re.S) or [None, ""])[1])).strip()
            o, l = g("title"), g("source")
            if " - " in o and not l: o, l = o.rsplit(" - ", 1)
            elif l and o.endswith(" - " + l): o = o[: -len(l) - 3]
            out.append({"o": o, "u": g("link"), "t": pvm(g("pubDate")), "l": l, "maa": maa})
    return out

def claude(system, user, tokens=6000):
    if not AK: return None
    d = json.dumps({"model": "claude-haiku-4-5", "max_tokens": tokens, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.anthropic.com/v1/messages", d,
            {"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"}), timeout=180).read())
        return r["content"][0]["text"]
    except Exception as e: print("CLAUDE-VIRHE", str(e)[:200]); return None

LUOKITTELU = """Luokittele uutisotsikot. Seuraamme, mitä maahanmuutto- ja kehitysapupolitiikkaa puolueet (tai hallitukset, EU) tekevät tai haluavat tehdä.
Jokaisesta palauta:
{"i":0, "olennainen":true/false (koskeeko maahanmuutto-, turvapaikka-, kansalaisuus-, kotouttamis- tai kehitysapupolitiikkaa ja jonkin puolueen/hallituksen kantaa tai päätöstä),
 "puolue":"puolueen nimi suomeksi tai lyhenne (tai Hallitus / EU-komissio / Europarlamentti)",
 "aihe":"maahanmuutto" | "kehitysapu",
 "suunta":"tiukentaa" | "löysentää" | "lisää rahaa" | "leikkaa rahaa" | "muu",
 "vaihe":"tekee" (päätös, laki, budjetti, äänestys) | "haluaa" (ehdotus, vaatimus, ohjelma, kannanotto),
 "tiivis":"yksi neutraali lause suomeksi: kuka, mitä, mihin suuntaan (max 20 sanaa)"}
Vastaa pelkkänä JSON-listana. Neutraali, tarkka, ei omia tulkintoja."""

def luokittele(uudet):
    for i in range(0, len(uudet), 40):
        osa = uudet[i:i + 40]
        t = claude(LUOKITTELU, json.dumps([{"i": n, "o": x["o"], "maa": x["maa"], "l": x["l"]} for n, x in enumerate(osa)], ensure_ascii=False))
        try: lista = json.loads(t[t.index("["):t.rindex("]") + 1])
        except Exception: lista = []
        for r in lista:
            try:
                x = osa[int(r["i"])]
                x["ok"] = bool(r.get("olennainen"))
                for k in ("puolue", "aihe", "suunta", "vaihe", "tiivis"): x[k] = str(r.get(k, ""))[:200]
            except Exception: pass
        for x in osa: x.setdefault("ok", False)

def sivu(arkisto, nyt):
    data = json.dumps([{k: x.get(k, "") for k in ("o", "u", "t", "l", "maa", "puolue", "aihe", "suunta", "vaihe", "tiivis")} for x in arkisto if x.get("ok")],
                      ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Puoluevahti</title><meta name="robots" content="noindex,nofollow"><style>
:root{{--bg:#f6f5f2;--card:#fff;--tx:#1b1d22;--mu:#666;--ac:#1f5fbf;--bd:#e3e0da}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--card:#1d2026;--tx:#eceae6;--mu:#9a9a9a;--ac:#6ea8ff;--bd:#2c3038}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,sans-serif}}main{{max-width:820px;margin:auto;padding:16px}}
select,input{{font:inherit;padding:8px;border-radius:8px;border:1px solid var(--bd);background:var(--card);color:var(--tx);margin:4px 4px 4px 0;max-width:100%}}
article{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 14px;margin:10px 0}}
.m{{color:var(--mu);font-size:14px}}.tag{{display:inline-block;border-radius:6px;padding:0 6px;margin-right:4px;font-size:13px;font-weight:700;color:#fff}}
.tiukentaa,.leikkaa{{background:#2e7d32}}.löysentää,.lisää{{background:#c62828}}.muu{{background:#757575}}.vaihe{{background:var(--ac)}}
a{{color:inherit}}</style></head><body><main><h1>Puoluevahti</h1><p class="m">Maahanmuutto- ja kehitysapupolitiikka – Suomi ja Eurooppa. Päivitetty {nyt}.</p>
<div><input id="h" placeholder="Hae (puolue, aihe…)"><select id="maa"><option value="">Kaikki maat</option></select>
<select id="aihe"><option value="">Molemmat aiheet</option><option>maahanmuutto</option><option>kehitysapu</option></select>
<select id="suunta"><option value="">Kaikki suunnat</option><option>tiukentaa</option><option>löysentää</option><option>lisää rahaa</option><option>leikkaa rahaa</option><option>muu</option></select>
<select id="vaihe"><option value="">Tekee + haluaa</option><option value="tekee">Tekee (päätökset)</option><option value="haluaa">Haluaa (ehdotukset)</option></select></div>
<p class="m" id="n"></p><div id="L"></div></main><script>
const D={data};const $=i=>document.getElementById(i);
[...new Set(D.map(x=>x.maa))].sort().forEach(m=>{{const o=document.createElement("option");o.textContent=m;$("maa").append(o)}});
function nayta(){{const h=$("h").value.toLowerCase(),f=x=>(!$("maa").value||x.maa===$("maa").value)&&(!$("aihe").value||x.aihe===$("aihe").value)&&(!$("suunta").value||x.suunta===$("suunta").value)&&(!$("vaihe").value||x.vaihe===$("vaihe").value)&&(!h||(x.o+" "+x.tiivis+" "+x.puolue).toLowerCase().includes(h));
const r=D.filter(f).slice(0,400);$("n").textContent=r.length+" juttua";$("L").replaceChildren(...r.map(x=>{{const a=document.createElement("article");
const m=document.createElement("div");m.className="m";m.textContent=x.maa+" · "+x.puolue+" · "+x.t.slice(8,10)+"."+x.t.slice(5,7)+"."+x.t.slice(0,4)+" · "+x.l;
const tg=document.createElement("div");for(const [c,t] of [[(x.suunta||"muu").split(" ")[0],x.suunta],["vaihe",x.vaihe],["muu",x.aihe]]){{if(!t)continue;const s=document.createElement("span");s.className="tag "+c;s.textContent=t;tg.append(s)}}
const p=document.createElement("p");p.textContent=x.tiivis;const l=document.createElement("a");l.href=x.u;l.target="_blank";l.rel="noopener noreferrer";l.textContent=x.o;
a.append(m,tg,p,l);return a}}))}}
["h","maa","aihe","suunta","vaihe"].forEach(i=>$(i).addEventListener("input",nayta));nayta();
</script></body></html>"""

def tg(t):
    if not TG: print(t[:400]); return
    d = json.dumps({"chat_id": CHAT, "text": t[:4000], "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    try: urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TG}/sendMessage", d, {"content-type": "application/json"}), timeout=30)
    except Exception as e: print("TG-VIRHE", e)

if __name__ == "__main__":
    try: tila = json.load(open("puoluevahti.json"))
    except Exception: tila = {}
    arkisto, lahetetyt = tila.get("arkisto", []), set(tila.get("lahetetyt", []))
    avain = lambda x: re.sub(r"\W+", "", x["o"].lower())[:70]
    nahty = {avain(x) for x in arkisto} | {x["u"] for x in arkisto}
    uudet = []
    for x in kohteet():
        if avain(x) in nahty or x["u"] in nahty: continue
        nahty.update([avain(x), x["u"]]); uudet.append(x)
    luokittele(uudet)
    arkisto = sorted(arkisto + uudet, key=lambda x: x["t"], reverse=True)[:20000]
    ok = [x for x in uudet if x.get("ok")]
    print(f"::notice title=Puoluevahti::{len(uudet)} uutta, joista olennaisia {len(ok)}; arkistossa {sum(1 for x in arkisto if x.get('ok'))}")
    nyt = NYT.astimezone(FI).strftime("%-d.%-m.%Y klo %H.%M")
    hallinta = hashlib.sha256((os.environ["CF"].strip() + "-faktapiste").encode()).hexdigest()[:40]
    k = hashlib.sha256(("oma-puolueet" + hallinta).encode()).hexdigest()[:32]
    url = f"https://faktapiste.fi/api/oma/puolueet?k={k}"
    r = urllib.request.Request("https://faktapiste.fi/api/hallinta/oma", json.dumps({"nimi": "puolueet", "html": sivu(arkisto, nyt)}).encode(),
                               {"content-type": "application/json", "x-avain": hallinta, **UA})
    print("::notice title=Sivu::" + urllib.request.urlopen(r, timeout=60).read().decode()[:200])
    tapahtuma = os.environ.get("TAPAHTUMA"); paiva = NYT.astimezone(FI)
    if tapahtuma == "schedule" or os.environ.get("LAHETA") == "1":
        raja = (NYT - datetime.timedelta(days=2)).isoformat()[:16]
        rivi = lambda x: f"• <b>{html.escape(x.get('puolue',''))}</b> ({html.escape(x.get('suunta',''))}, {html.escape(x.get('vaihe',''))}): {html.escape(x.get('tiivis') or x['o'])}\n{x['u']}"
        fi = [x for x in arkisto if x.get("ok") and x["maa"] == "Suomi" and x["t"] >= raja and x["u"] not in lahetetyt][:10]
        if fi:
            tg("🏛 <b>Puolueet: maahanmuutto ja kehitysapu – Suomi</b>\n\n" + "\n\n".join(map(rivi, fi)) + f"\n\n📋 <a href=\"{url}\">Koko Puoluevahti</a>")
            lahetetyt.update(x["u"] for x in fi)
        if paiva.weekday() == 0 or os.environ.get("LAHETA") == "1":   # maanantaina Euroopan viikkokoonti
            raja7 = (NYT - datetime.timedelta(days=7)).isoformat()[:16]
            eu = [x for x in arkisto if x.get("ok") and x["maa"] != "Suomi" and x["t"] >= raja7 and x["u"] not in lahetetyt]
            tehty = [x for x in eu if x.get("vaihe") == "tekee"][:8] + [x for x in eu if x.get("vaihe") != "tekee"][:6]
            if tehty:
                tg("🇪🇺 <b>Puolueet Euroopassa – viikon maahanmuutto- ja kehitysapupolitiikka</b>\n\n"
                   + "\n\n".join(f"{x['maa']}: " + rivi(x) for x in tehty) + f"\n\n📋 <a href=\"{url}\">Koko Puoluevahti</a>")
                lahetetyt.update(x["u"] for x in tehty)
    json.dump({"arkisto": arkisto, "lahetetyt": sorted(lahetetyt)[-5000:]}, open("puoluevahti.json", "w"), ensure_ascii=False)
