"""Miikan oma seuranta: julkiset uutiset, viranomais- ja kuntatiedot sekä yhteisöjen omat tiedotteet islamista ja
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
                "yhdenvertaisuus.fi", "okm.fi", "stm.fi", "thl.fi"]
KUNNAT = ["hel.fi", "espoo.fi", "vantaa.fi", "turku.fi", "tampere.fi", "oulu.fi", "jyvaskyla.fi", "kuopio.fi", "lahti.fi", "pori.fi",
          "vaasa.fi", "joensuu.fi", "lappeenranta.fi", "kouvola.fi", "hameenlinna.fi", "seinajoki.fi", "rovaniemi.fi", "kotka.fi",
          "kerava.fi", "jarvenpaa.fi", "porvoo.fi", "kokkola.fi", "ylivieska.fi", "kuntaliitto.fi"]
KUNTAHAUT = ["moskeija kaava", "moskeija rakennuslupa", "moskeijahanke", "rukoustila kaupunki", "islamilainen kulttuurikeskus",
             "muslimien hautausmaa", "islamilainen hautausmaa", "uskonnollinen yhdyskunta avustus kaupunki", "halal kouluruoka",
             "islamin opetus koulu", "rukoushuone kunta", "moskeija valtuusto", "moskeija lautakunta"]
SYOTTEET = [("media", "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET"), ("media", "https://www.hs.fi/rss/tuoreimmat.xml"),
            ("media", "https://www.iltalehti.fi/rss/uutiset.xml"), ("media", "https://www.is.fi/rss/tuoreimmat.xml"),
            ("media", "https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat"), ("media", "https://www.uusisuomi.fi/rss"),
            ("media", "https://www.verkkouutiset.fi/feed/"),
            ("media", "https://www.seurakuntalainen.fi/feed/")]
TAYSI = os.environ.get("TAYSI") == "1"   # kerralla myös vanhat jutut (ilman aikarajaa)
SYOTTEET += [("media", GN + urllib.parse.quote(q + ("" if TAYSI else " when:3d"))) for q in HAUT]
SYOTTEET += [("kunta", GN + urllib.parse.quote(f"site:{d} (islam OR muslimi OR muslimit OR moskeija OR rukoustila OR uskonnollinen yhdyskunta)")) for d in KUNNAT]
SYOTTEET += [("kunta", GN + urllib.parse.quote(q + ("" if TAYSI else " when:30d"))) for q in KUNTAHAUT]
if TAYSI:   # vanhat jutut vuosi kerrallaan (Google palauttaa max ~100 juttua hakua kohden)
    SYOTTEET += [("media", GN + urllib.parse.quote(f"{q} after:{v}-01-01 before:{v + 1}-01-01")) for v in range(2008, 2027)
                 for q in ["islam Suomi", "muslimit Suomi", "moskeija", "imaami", "islamilainen yhdyskunta", "muslimi Helsinki"]]
    SYOTTEET += [("kunta", GN + urllib.parse.quote(f"moskeija (kaava OR rakennuslupa OR valtuusto OR hanke) after:{v}-01-01 before:{v + 1}-01-01")) for v in range(2008, 2027)]
SYOTTEET += [("viranomainen", GN + urllib.parse.quote(f"site:{d} (islam OR muslimi OR muslimit OR moskeija OR uskonnollinen)")) for d in VIRANOMAISET]
# Muslimiyhteisöjen omat sivut: kokeillaan tavallisia syöteosoitteita; toimimattomat ohitetaan ja kirjataan lokiin.
YHTEISOT = ["sine.fi", "tatar.fi", "rabita.fi", "islamkeskus.fi", "islam.fi", "muslimit.fi", "hiks.fi", "fida.fi", "resalat.fi",
            "islamicsocietyfinland.fi", "jaafari.fi", "turunislam.fi", "oulunislam.fi", "tampereenislam.fi", "suomenmuslimit.fi", "dawa.fi"]
SYOTTEET += [("yhteiso", f"https://{d}{p}") for d in YHTEISOT for p in ("/feed/", "/rss")]
SYOTTEET += [("yhteiso", GN + urllib.parse.quote(f'"{n}"')) for n in ["Suomen Islamilainen Neuvosto", "Suomen Islam-seurakunta", "Helsingin Islamkeskus", "Rabita", "Suomen islamilainen yhdyskunta"]]

def gn(q, kieli):
    hl, gl = {"en": ("en-GB", "GB"), "sv": ("sv", "SE"), "de": ("de", "DE"), "fr": ("fr", "FR"), "nl": ("nl", "NL"), "da": ("da", "DK"), "no": ("no", "NO")}[kieli]
    return f"https://news.google.com/rss/search?hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}&q=" + urllib.parse.quote(q)
EUROOPPA = [("media", gn(q + " when:1d", kl)) for kl, q in [
    ("en", "Islam Europe"), ("en", "Muslims Europe"), ("en", "mosque Europe"), ("en", "Islamism Europe"), ("en", "Muslim Brotherhood Europe"),
    ("en", "Islam UK"), ("en", "mosque UK"), ("sv", "islam Sverige"), ("sv", "moské"), ("sv", "islamism"), ("de", "Islam Deutschland"),
    ("de", "Moschee"), ("de", "Islamismus"), ("fr", "islam France"), ("fr", "mosquée"), ("fr", "islamisme"), ("nl", "islam Nederland"),
    ("nl", "moskee"), ("da", "islam Danmark"), ("da", "moské Danmark"), ("no", "islam Norge")]]
EUROOPPA += [("viranomainen", gn(f"site:{d} (islam OR muslim OR mosque OR islamist OR Islamismus OR islamism)", "en")) for d in
             ["europa.eu", "europol.europa.eu", "fra.europa.eu", "europarl.europa.eu", "consilium.europa.eu", "coe.int", "osce.org",
              "sakerhetspolisen.se", "regeringen.se", "verfassungsschutz.de", "bmi.bund.de", "pet.dk", "pst.no", "gov.uk", "interieur.gouv.fr", "aivd.nl"]]
AIHE_EU = re.compile(r"islam|muslim|moské|moske|mosque|moschee|mosquée|moskee|imam|ramadan|halal|koran|quran|coran|sharia|charia|hijab|burka|niqab|jihad|musulman|salafi", re.I)
AIHE = re.compile(r"rukousti|rukoushuo|islam|muslim|moskei|moske|imaam|ramadan|ramazan|halal|koraan|hijab|burka|niqab|sharia|islamilai|uskonnonvapau|eid\b|tataari", re.I)
SUOMI = re.compile(r"suom|helsin|espoo|vantaa|tampere|turku|turun|oulu|jyväsky|kuopio|lahti|pori|vaasa|joensuu|lappeenran|rovanie|kotka|seinäjo|eduskun|yle\b|poliisi|ministeri|kunta|kaupun|koulu|kela|migri|thl|opetushallit|seurakun|kirkko|supo", re.I)
LUOKAT = {"media": "Media", "viranomainen": "Viranomainen", "kunta": "Kunnat", "yhteiso": "Muslimiyhteisöt"}

def hae(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")

def pvm(s):
    try: return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).isoformat()[:16]
    except Exception: return datetime.datetime.now(datetime.timezone.utc).isoformat()[:16]

def kohteet(loki):
    for luokka, s, alue in [(l, u, "fi") for l, u in SYOTTEET] + [(l, u, "eu") for l, u in EUROOPPA]:
        try: x = hae(s)
        except Exception as e:
            if luokka == "yhteiso" and "news.google" not in s: continue
            loki.append(f"VIRHE {s[:80]}: {str(e)[:60]}"); continue
        its = re.findall(r"<item>([\s\S]*?)</item>", x)[:(40 if alue == "eu" else 80)]
        if luokka == "yhteiso" and "news.google" not in s: loki.append(f"YHTEISÖSYÖTE OK {s} ({len(its)})")
        for it in its:
            g = lambda t: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", " ", (re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>", it) or [None, ""])[1])).strip()
            otsikko, kuvaus, linkki = g("title"), re.sub(r"\s+", " ", g("description"))[:300], g("link")
            lahde = g("source") or re.sub(r"^www\.", "", urllib.parse.urlparse(linkki).netloc)
            if "news.google" in s and " - " in otsikko: otsikko = otsikko.rsplit(" - ", 1)[0]
            if "news.google" in s: kuvaus = ""
            teksti = otsikko + " " + kuvaus
            if not linkki: continue
            if alue == "eu":
                if not AIHE_EU.search(teksti): continue
            elif luokka == "yhteiso" and "news.google" not in s: pass                     # yhteisön oma sivu: kaikki tiedotteet
            elif not AIHE.search(teksti): continue
            elif "news.google" in s and luokka == "media" and not SUOMI.search(teksti + " " + lahde): continue
            yield {"o": re.sub(r"\s+", " ", otsikko), "k": kuvaus, "l": lahde, "u": linkki, "t": pvm(g("pubDate")), "c": luokka, "a": alue}

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
.media{{color:var(--b)}} .viranomainen{{color:var(--c)}} .yhteiso{{color:var(--a)}} .kunta{{color:#b5543c}} .k{{font-size:.92rem;color:var(--m);margin:0}}
details{{background:var(--s);border:1px solid var(--l);border-radius:10px;padding:12px 14px}} summary{{cursor:pointer;font-weight:600}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}} td,th{{text-align:left;vertical-align:top;padding:7px 6px;border-bottom:1px solid var(--l)}} .tw{{overflow-x:auto}}
</style></head><body><main>
<header style="display:grid;gap:8px"><h1>Islam ja muslimit Suomessa ja Euroopassa</h1>
<p class="p">Julkiset uutiset, viranomaisten ja kuntien tiedot (esim. hankkeet ja kaavat) sekä muslimiyhteisöjen omat tiedotteet yhdessä paikassa. Päivittyy tunnin välein; ulkomaiset otsikot on käännetty suomeksi. Päivitetty {nyt}. Sivu on vain sinun käytössäsi.</p></header>
<input id="haku" type="search" placeholder="Hae otsikoista ja lähteistä, esim. moskeija, Turku, poliisi" aria-label="Haku">
<div class="chips" id="alueet"><button data-a="" aria-pressed="true">Suomi + Eurooppa</button><button data-a="fi" aria-pressed="false">Suomi</button><button data-a="eu" aria-pressed="false">Eurooppa</button></div>
<div class="chips" id="chips"><button data-c="" aria-pressed="true">Kaikki</button><button data-c="media" aria-pressed="false">Media</button><button data-c="viranomainen" aria-pressed="false">Viranomaiset</button><button data-c="kunta" aria-pressed="false">Kunnat ja hankkeet</button><button data-c="yhteiso" aria-pressed="false">Muslimiyhteisöt</button></div>
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
const D={data};const C={{media:"Media",viranomainen:"Viranomainen",kunta:"Kunta",yhteiso:"Muslimiyhteisö"}};let luokka="",alue="";
const L=document.getElementById("lista"),H=document.getElementById("haku"),M=document.getElementById("maara");
function pv(t){{const d=new Date(t+"Z");return d.toLocaleDateString("fi-FI",{{weekday:"long",day:"numeric",month:"numeric",year:"numeric"}})}}
function nayta(){{const q=H.value.trim().toLowerCase();const r=D.filter(x=>(!luokka||x.c===luokka)&&(!alue||(x.a||"fi")===alue)&&(!q||(x.o+" "+(x.oo||"")+" "+x.l+" "+x.k).toLowerCase().includes(q)));
M.textContent=r.length+" juttua"+(q||luokka||alue?" (suodatettu)":"")+" · koko arkisto";L.textContent="";let ed="";
for(const x of r){{const p=pv(x.t);if(p!==ed){{const h=document.createElement("h2");h.textContent=p.charAt(0).toUpperCase()+p.slice(1);L.append(h);ed=p}}
const a=document.createElement("article");const l=document.createElement("a");l.href=x.u;l.target="_blank";l.rel="noopener noreferrer";l.textContent=x.o;
const m=document.createElement("div");m.className="meta";const t=document.createElement("span");t.className="tag "+x.c;t.textContent=C[x.c];const s=document.createElement("span");s.textContent=(x.a==="eu"?"🇪🇺 ":"")+x.l;m.append(t,s);a.append(m,l);
if(x.oo){{const o=document.createElement("p");o.className="k";o.textContent="Alkuperäinen: "+x.oo;a.append(o)}}if(x.k){{const k=document.createElement("p");k.className="k";k.textContent=x.k;a.append(k)}}L.append(a)}}}}
H.addEventListener("input",nayta);document.querySelectorAll("#chips button").forEach(b=>b.onclick=()=>{{luokka=b.dataset.c;document.querySelectorAll("#chips button").forEach(x=>x.setAttribute("aria-pressed",x===b));nayta()}});document.querySelectorAll("#alueet button").forEach(b=>b.onclick=()=>{{alue=b.dataset.a;document.querySelectorAll("#alueet button").forEach(x=>x.setAttribute("aria-pressed",x===b));nayta()}});nayta();
</script></body></html>"""

def kaanna(uudet):
    """Kääntää ulkomaiset otsikot suomeksi (Claude Haiku); alkuperäinen jää kenttään oo."""
    eu = [x for x in uudet if x.get("a") == "eu" and "oo" not in x]
    ak = os.environ.get("AK", "").strip()
    for i in range(0, len(eu), 40):
        osa = eu[i:i + 40]
        if not ak: return
        d = json.dumps({"model": "claude-haiku-4-5", "max_tokens": 4000,
            "system": "Käännä jokainen uutisotsikko suomeksi tarkasti ja neutraalisti, lisäämättä mitään. Vastaa pelkkänä JSON-listana merkkijonoja samassa järjestyksessä.",
            "messages": [{"role": "user", "content": json.dumps([x["o"] for x in osa], ensure_ascii=False)}]}).encode()
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.anthropic.com/v1/messages", d,
                {"x-api-key": ak, "anthropic-version": "2023-06-01", "content-type": "application/json"}), timeout=90).read())
            t = r["content"][0]["text"]; lista = json.loads(t[t.index("["):t.rindex("]") + 1])
            if len(lista) == len(osa):
                for x, f in zip(osa, lista): x["oo"], x["o"] = x["o"], str(f)
        except Exception as e: print("KÄÄNNÖSVIRHE", e)

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
    kaanna(uudet)
    arkisto = sorted(arkisto, key=lambda x: x["t"], reverse=True)[:30000]   # arkisto säilyy, vanhatkin jutut
    nyt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.%Y klo %H.%M")
    hallinta = hashlib.sha256((os.environ["CF"].strip() + "-faktapiste").encode()).hexdigest()[:40]
    k = hashlib.sha256(("oma-uskonto" + hallinta).encode()).hexdigest()[:32]
    url = f"https://faktapiste.fi/api/oma/uskonto?k={k}"
    nayt = [dict(x) for x in arkisto]
    h = sivu(nayt, nyt)
    if len(h.encode()) >= 1_800_000:            # sivun kokoraja: yli vuoden vanhoista jätetään kuvaus pois
        vuosi = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)).isoformat()[:16]
        for x in nayt:
            if x["t"] < vuosi: x["k"] = ""
        h = sivu(nayt, nyt)
    while len(h.encode()) >= 1_800_000 and len(nayt) > 100:
        nayt = nayt[:int(len(nayt) * 0.9)]; h = sivu(nayt, nyt)
    r = urllib.request.Request("https://faktapiste.fi/api/hallinta/oma", json.dumps({"nimi": "uskonto", "html": h}).encode(),
                               {"content-type": "application/json", "x-avain": hallinta, **UA})
    print("::notice title=Sivu::" + urllib.request.urlopen(r, timeout=30).read().decode()[:200])
    for l in loki: print(l)
    print(f"::notice title=Uskontovahti::{len(uudet)} uutta, arkistossa {len(arkisto)}")
    tunti = datetime.datetime.now(datetime.timezone.utc).hour
    rivi = lambda x: f"• {html.escape(x['o'])} <i>({html.escape(x['l'])})</i>"
    # Pikahälytys: uudet Suomen jutut heti (ei vanhojen juttujen haussa)
    if os.environ.get("TAYSI") != "1":
        tuore = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)).isoformat()[:16]
        heti = [x for x in uudet if x.get("a") != "eu" and x["t"] >= tuore and x["u"] not in lahetetyt][:12]
        if heti:
            laheta("🔔 <b>Uutta: islam ja muslimit Suomessa</b>\n\n" + "\n".join(f"{rivi(x)}\n{x['u']}" for x in heti)[:3500])
            lahetetyt.update(x["u"] for x in heti)
    if os.environ.get("KOONTI") == "1" or (os.environ.get("TAPAHTUMA") == "schedule" and tunti in (5, 6)):
        pv = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%-d.%-m.")
        raja = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()[:16]
        fi = [x for x in arkisto if x.get("a") != "eu" and x["t"] >= raja][:15]
        eu = [x for x in arkisto if x.get("a") == "eu" and x["t"] >= raja]
        euv = [x for x in eu if x["c"] == "viranomainen"][:5] + [x for x in eu if x["c"] != "viranomainen"][:10]
        laheta(f"🕌⛪ <b>Islam Suomessa ja Euroopassa – {pv}</b>\n\n<b>Suomi ({len(fi)})</b>\n" + ("\n".join(map(rivi, fi)) or "Ei uutta.")[:1700]
               + f"\n\n<b>Eurooppa ({len(eu)})</b>\n" + ("\n".join(map(rivi, euv)) or "Ei uutta.")[:1500] + f"\n\n📖 <a href=\"{url}\">Avaa koko seurantasivu</a>")
        lahetetyt.update(x["u"] for x in arkisto)
    json.dump({"arkisto": arkisto, "lahetetyt": sorted(lahetetyt)[-5000:]}, open(tila, "w"), ensure_ascii=False)
