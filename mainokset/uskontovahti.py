"""Miikan oma seuranta: julkiset uutiset, viranomaistiedotteet ja yhteisöjen omat tiedotteet islamista ja
muslimeista Suomessa. Kerää arkiston (90 pv), rakentaa yksityisen sivun (faktapiste.fi/api/oma/uskonto?k=...)
ja lähettää aamulla koonnin Telegramiin. Vain julkista tietoa; ei henkilöiden seurantaa eikä kommentointia.
Tila: uskontovahti.json (haara uutisvinkit-tila)."""
import os, re, json, html, hashlib, urllib.request, urllib.parse, datetime, email.utils

UA = {"user-agent": "Mozilla/5.0 (Faktapiste-seuranta; +https://faktapiste.fi)"}
GN = "https://news.google.com/rss/search?hl=fi&gl=FI&ceid=FI:fi&q="
HAUT = ["islam", "muslimi", "muslimit", "muslimien", "muslimeja", "moskeija", "moskeijan", "imaami", "islamilainen",
        "islamilaisen", "ramadan", "halal", "koraani", "huivi koulu", "Suomen islamilainen neuvosto", "islamin opetus",
        "muslimitaustainen", "islamofobia", "uskonnonvapaus"]
VIRANOMAISET = ["poliisi.fi", "valtioneuvosto.fi", "intermin.fi", "um.fi", "oph.fi", "migri.fi", "supo.fi", "eduskunta.fi",
                "hel.fi", "espoo.fi", "vantaa.fi", "turku.fi", "tampere.fi", "oulu.fi", "yhdenvertaisuus.fi", "okm.fi", "stm.fi", "thl.fi"]
SYOTTEET = [("media", "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET"), ("media", "https://www.hs.fi/rss/tuoreimmat.xml"),
            ("media", "https://www.iltalehti.fi/rss/uutiset.xml"), ("media", "https://www.is.fi/rss/tuoreimmat.xml"),
            ("media", "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat"), ("media", "https://www.uusisuomi.fi/rss"),
            ("media", "https://www.verkkouutiset.fi/feed/"), ("media", "https://www.kirkkojakaupunki.fi/rss"),
            ("media", "https://www.seurakuntalainen.fi/feed/"), ("media", "https://www.dagen.fi/feed/")]
SYOTTEET += [("media", GN + urllib.parse.quote(q + " when:3d")) for q in HAUT]
SYOTTEET += [("viranomainen", GN + urllib.parse.quote(f"site:{d} (islam OR muslimi OR muslimit OR moskeija OR uskonnollinen)")) for d in VIRANOMAISET]
# Muslimiyhteisöjen omat sivut: kokeillaan tavallisia syöteosoitteita; toimimattomat ohitetaan ja kirjataan lokiin.
YHTEISOT = ["sine.fi", "tatar.fi", "rabita.fi", "islamkeskus.fi", "islam.fi", "muslimit.fi", "hiks.fi", "fida.fi", "resalat.fi",
            "islamicsocietyfinland.fi", "jaafari.fi", "turunislam.fi", "oulunislam.fi", "tampereenislam.fi", "suomenmuslimit.fi", "dawa.fi"]
SYOTTEET += [("yhteiso", f"https://{d}{p}") for d in YHTEISOT for p in ("/feed/", "/rss")]
SYOTTEET += [("yhteiso", GN + urllib.parse.quote(f'"{n}"')) for n in ["Suomen Islamilainen Neuvosto", "Suomen Islam-seurakunta", "Helsingin Islamkeskus", "Rabita", "Suomen islamilainen yhdyskunta"]]

AIHE = re.compile(r"islam|muslim|moskei|moske|imaam|ramadan|ramazan|halal|koraan|hijab|burka|niqab|sharia|islamilai|uskonnonvapau|eid\b|tataari", re.I)
SUOMI = re.compile(r"suom|helsin|espoo|vantaa|tampere|turku|turun|oulu|jyväsky|kuopio|lahti|pori|vaasa|joensuu|lappeenran|rovanie|kotka|seinäjo|eduskun|yle\b|poliisi|ministeri|kunta|kaupun|koulu|kela|migri|thl|opetushallit|seurakun|kirkko|supo", re.I)
LUOKAT = {"media": "Media", "viranomainen": "Viranomainen", "yhteiso": "Muslimiyhteisöt"}

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")

def pvm(s):
    try: return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).isoformat()[:16]
    except Exception: return datetime.datetime.now(datetime.timezone.utc).isoformat()[:16]

def kohteet(loki):
    for luokka, s in SYOTTEET:
        try: x = hae(s)
        except Exception as e:
            if luokka == "yhteiso" and "news.google" not in s: continue
            loki.append(f"VIRHE {s[:80]}: {str(e)[:60]}"); continue
        its = re.findall(r"<item>([\s\S]*?)</item>", x)[:80]
        if luokka == "yhteiso" and "news.google" not in s: loki.append(f"YHTEISÖSYÖTE OK {s} ({len(its)})")
        for it in its:
            g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", " ", (re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>", it) or [None, ""])[1])).strip()
            otsikko, kuvaus, linkki = g("title"), re.sub(r"\s+", " ", g("description"))[:300], g("link")
            lahde = g("source") or re.sub(r"^www\.", "", urllib.parse.urlparse(linkki).netloc)
            if "news.google" in s and " - " in otsikko: otsikko = otsikko.rsplit(" - ", 1)[0]
            if "news.google" in s: kuvaus = ""
            teksti = otsikko + " " + kuvaus
            if not linkki: continue
            if luokka == "yhteiso" and "news.google" not in s: pass                     # yhteisön oma sivu: kaikki tiedotteet
            elif not AIHE.search(teksti): continue
            elif "news.google" in s and luokka == "media" and not SUOMI.search(teksti + " " + lahde): continue
            yield {"o": re.sub(r"\s+", " ", otsikko), "k": kuvaus, "l": lahde, "u": linkki, "t": pvm(g("pubDate")), "c": luokka}

def sivu(arkisto, nyt):
    data = json.dumps(arkisto, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Islam Suomessa – seuranta</title><style>
:root{{--bg:#f6f7f4;--s:#fff;--f:#1d2420;--m:#5c6862;--l:#dde2dc;--a:#1f6b55;--b:#2d4f7c;--c:#8a6a2f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141917;--s:#1c2320;--f:#e7ece8;--m:#9aa7a0;--l:#2c3531;--a:#7fcfb2;--b:#8fb1e0;--c:#d9b673;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--f);font:17px/1.5 system-ui,sans-serif;padding:20px max(16px,env(safe-area-inset-left)) 60px}}
main{{max-width:820px;margin:auto;display:grid;gap:18px}} h1{{font:650 1.7rem/1.2 Georgia,serif;margin:0}} h2{{font:650 1.15rem Georgia,serif;margin:18px 0 0}}
.p{{color:var(--m);font-size:.95rem;margin:0}} input{{width:100%;box-sizing:border-box;font:inherit;padding:11px 13px;border:1px solid var(--l);border-radius:9px;background:var(--s);color:var(--f)}}
.chips{{display:flex;gap:8px;flex-wrap:wrap}} .chips button{{font:inherit;font-size:.9rem;padding:6px 12px;border-radius:99px;border:1px solid var(--l);background:var(--s);color:var(--f);cursor:pointer}}
.chips button[aria-pressed=true]{{background:var(--a);color:var(--bg);border-color:var(--a)}}
article{{background:var(--s);border:1px solid var(--l);border-radius:10px;padding:12px 14px;display:grid;gap:4px}}
article a{{color:var(--f);font-weight:600;text-decoration:none}} article a:hover{{text-decoration:underline}}
.meta{{font-size:.82rem;color:var(--m);display:flex;gap:8px;flex-wrap:wrap;align-items:center}} .tag{{font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;font-weight:700}}
.media{{color:var(--b)}} .viranomainen{{color:var(--c)}} .yhteiso{{color:var(--a)}} .k{{font-size:.92rem;color:var(--m);margin:0}}
details{{background:var(--s);border:1px solid var(--l);border-radius:10px;padding:12px 14px}} summary{{cursor:pointer;font-weight:600}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}} td,th{{text-align:left;vertical-align:top;padding:7px 6px;border-bottom:1px solid var(--l)}} .tw{{overflow-x:auto}}
</style></head><body><main>
<header style="display:grid;gap:8px"><h1>Islam ja muslimit Suomessa</h1>
<p class="p">Julkiset uutiset, viranomaisten tiedotteet ja muslimiyhteisöjen omat tiedotteet yhdessä paikassa. Päivittyy noin kolmen tunnin välein. Päivitetty {nyt}. Sivu on vain sinun käytössäsi.</p></header>
<input id="haku" type="search" placeholder="Hae otsikoista ja lähteistä, esim. moskeija, Turku, poliisi" aria-label="Haku">
<div class="chips" id="chips"><button data-c="" aria-pressed="true">Kaikki</button><button data-c="media" aria-pressed="false">Media</button><button data-c="viranomainen" aria-pressed="false">Viranomaiset</button><button data-c="yhteiso" aria-pressed="false">Muslimiyhteisöt</button></div>
<p class="p" id="maara"></p><div id="lista" style="display:grid;gap:10px"></div>
<details><summary>Kristinusko ja islam – vertailu</summary><div class="tw"><table>
<tr><th>Aihe</th><th>Kristinusko</th><th>Islam</th></tr>
<tr><td>Jumala</td><td>Yksi Jumala kolmessa persoonassa (kolminaisuus)</td><td>Yksi Jumala (Allah), ehdoton ykseys; kolminaisuus torjutaan</td></tr>
<tr><td>Jeesus</td><td>Jumalan Poika, kuoli ja nousi kuolleista</td><td>Suuri profeetta (Isa) ja Messias, ei Jumalan poika; ei ristiinnaulittu</td></tr>
<tr><td>Pyhä kirja</td><td>Raamattu</td><td>Koraani, lisäksi hadithit</td></tr>
<tr><td>Keskeinen henkilö</td><td>Jeesus Kristus</td><td>Muhammad, viimeinen profeetta</td></tr>
<tr><td>Pelastus</td><td>Armosta uskon kautta</td><td>Usko ja teot; Jumala tuomitsee ja armahtaa</td></tr>
<tr><td>Synti</td><td>Perisynti</td><td>Ei perisyntiä</td></tr>
<tr><td>Rukous</td><td>Vapaa, jumalanpalvelus sunnuntaina</td><td>Viisi päivittäistä rukousta, perjantairukous</td></tr>
<tr><td>Käytännöt</td><td>Kaste ja ehtoollinen</td><td>Viisi pilaria: tunnustus, rukous, almuvero, paasto, pyhiinvaellus</td></tr>
<tr><td>Laki</td><td>Ei uskonnollista lakikokoelmaa</td><td>Sharia-ohjeisto, tulkinnat vaihtelevat; Suomessa noudatetaan Suomen lakia</td></tr>
<tr><td>Ruoka</td><td>Ei yleisiä sääntöjä</td><td>Sianliha ja alkoholi kielletty, halal</td></tr>
<tr><td>Kannattajia</td><td>n. 2,3 mrd</td><td>n. 2 mrd</td></tr></table></div>
<p class="p">Suomessa arviolta noin 130 000 muslimitaustaista (tutkija-arvio, MTV Uutiset). Laajempi vertailu: Claude-sivu "Kristinusko ja islam".</p></details>
</main><script>
const D={data};const C={{media:"Media",viranomainen:"Viranomainen",yhteiso:"Muslimiyhteisö"}};let luokka="";
const L=document.getElementById("lista"),H=document.getElementById("haku"),M=document.getElementById("maara");
function pv(t){{const d=new Date(t+"Z");return d.toLocaleDateString("fi-FI",{{weekday:"long",day:"numeric",month:"numeric",year:"numeric"}})}}
function nayta(){{const q=H.value.trim().toLowerCase();const r=D.filter(x=>(!luokka||x.c===luokka)&&(!q||(x.o+" "+x.l+" "+x.k).toLowerCase().includes(q)));
M.textContent=r.length+" juttua"+(q||luokka?" (suodatettu)":"")+" · viimeiset 90 päivää";L.textContent="";let ed="";
for(const x of r){{const p=pv(x.t);if(p!==ed){{const h=document.createElement("h2");h.textContent=p.charAt(0).toUpperCase()+p.slice(1);L.append(h);ed=p}}
const a=document.createElement("article");const l=document.createElement("a");l.href=x.u;l.target="_blank";l.rel="noopener noreferrer";l.textContent=x.o;
const m=document.createElement("div");m.className="meta";const t=document.createElement("span");t.className="tag "+x.c;t.textContent=C[x.c];const s=document.createElement("span");s.textContent=x.l;m.append(t,s);a.append(m,l);
if(x.k){{const k=document.createElement("p");k.className="k";k.textContent=x.k;a.append(k)}}L.append(a)}}}}
H.addEventListener("input",nayta);document.querySelectorAll("#chips button").forEach(b=>b.onclick=()=>{{luokka=b.dataset.c;document.querySelectorAll("#chips button").forEach(x=>x.setAttribute("aria-pressed",x===b));nayta()}});nayta();
</script></body></html>"""

def laheta(t):
    d = json.dumps({"chat_id": "1893930799", "text": t, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{os.environ['TG'].strip()}/sendMessage", d, {"content-type": "application/json"}))

if __name__ == "__main__":
    tila = "uskontovahti.json"
    try: vanha = json.load(open(tila))
    except Exception: vanha = {}
    if isinstance(vanha, list): vanha = {}
    arkisto, lahetetyt = vanha.get("arkisto", []), set(vanha.get("lahetetyt", []))
    avain = lambda x: re.sub(r"\W+", "", x["o"].lower())[:70]
    nahty = {avain(x) for x in arkisto} | {x["u"] for x in arkisto}
    loki, uudet = [], []
    for x in kohteet(loki):
        if avain(x) in nahty or x["u"] in nahty: continue
        nahty.update([avain(x), x["u"]]); uudet.append(x); arkisto.append(x)
    raja = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)).isoformat()[:16]
    arkisto = sorted([x for x in arkisto if x["t"] >= raja], key=lambda x: x["t"], reverse=True)[:3000]
    nyt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.%Y klo %H.%M")
    hallinta = hashlib.sha256((os.environ["CF"].strip() + "-faktapiste").encode()).hexdigest()[:40]
    k = hashlib.sha256(("oma-uskonto" + hallinta).encode()).hexdigest()[:32]
    url = f"https://faktapiste.fi/api/oma/uskonto?k={k}"
    r = urllib.request.Request("https://faktapiste.fi/api/hallinta/oma", json.dumps({"nimi": "uskonto", "html": sivu(arkisto, nyt)}).encode(),
                               {"content-type": "application/json", "x-avain": hallinta, **UA})
    print("::notice title=Sivu::" + urllib.request.urlopen(r, timeout=30).read().decode()[:200])
    for l in loki: print(l)
    print(f"::notice title=Uskontovahti::{len(uudet)} uutta, arkistossa {len(arkisto)}")
    tunti = datetime.datetime.now(datetime.timezone.utc).hour
    if os.environ.get("KOONTI") == "1" or (os.environ.get("TAPAHTUMA") == "schedule" and tunti in (5, 6)):
        tuoreet = [x for x in arkisto if x["u"] not in lahetetyt][:25]
        pv = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.")
        rivit = [f"• {html.escape(x['o'])} <i>({html.escape(x['l'])})</i>" for x in tuoreet]
        laheta(f"🕌⛪ <b>Islam ja muslimit Suomessa – {pv}</b>\n{len(tuoreet)} uutta juttua.\n\n" + "\n".join(rivit)[:3300] + f"\n\n📖 <a href=\"{url}\">Avaa koko seurantasivu</a>")
        lahetetyt.update(x["u"] for x in arkisto)
    json.dump({"arkisto": arkisto, "lahetetyt": sorted(lahetetyt)[-5000:]}, open(tila, "w"), ensure_ascii=False)
