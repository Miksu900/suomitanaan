"""Hankintavahti – julkiset tarjouspyynnöt selkokielellä pienyrittäjille.

Vaiheet:
  1. hae()      Hilman avoimesta rajapinnasta (CC BY 4.0) kaikki voimassa olevat hankintailmoitukset
  2. tiivista() uusille ilmoituksille Claude-tiivistelmä (selkokieli, kunta, maakunta, ala, sopivuus pienyritykselle);
                tiivistelmät talletetaan data/tiivistelmat.json, ettei samaa tehdä kahdesti
  3. rakenna()  staattiset sivut kansioon public/

Aja:  HILMA_API_KEY=... ANTHROPIC_API_KEY=... python3 hankintavahti/rakenna.py
      TESTI=naytte.json python3 hankintavahti/rakenna.py   (paikallinen testi ilman avaimia)
"""
import json, os, re, html, datetime as dt, urllib.request, pathlib, concurrent.futures as cf, unicodedata, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scripts'))
from tietosuoja import seloste

HERE = pathlib.Path(__file__).parent
PUB = pathlib.Path(os.environ.get("PUB_DIR", HERE / "public"))
DATA = pathlib.Path(os.environ.get("DATA_DIR", HERE / "data"))
SIVU = "https://hankintavahti.com"
NIMI = "Hankintavahti"
NYT = dt.datetime.now(dt.timezone.utc)

MAAKUNNAT = ["Uusimaa", "Varsinais-Suomi", "Satakunta", "Kanta-Häme", "Pirkanmaa", "Päijät-Häme", "Kymenlaakso",
             "Etelä-Karjala", "Etelä-Savo", "Pohjois-Savo", "Pohjois-Karjala", "Keski-Suomi", "Etelä-Pohjanmaa",
             "Pohjanmaa", "Keski-Pohjanmaa", "Pohjois-Pohjanmaa", "Kainuu", "Lappi", "Ahvenanmaa"]
ALAT = ["Rakentaminen ja korjaus", "Sähkö, LVI ja talotekniikka", "Kiinteistöhuolto ja siivous", "Kuljetus ja logistiikka",
        "Ruoka ja ateriapalvelut", "IT ja ohjelmistot", "Konsultointi ja asiantuntijat", "Sosiaali- ja terveyspalvelut",
        "Kalusteet ja tarvikkeet", "Ajoneuvot ja koneet", "Maa-, metsä- ja ympäristötyöt", "Koulutus ja kulttuuri",
        "Markkinointi ja viestintä", "Muut"]

def slug(s):
    s = unicodedata.normalize("NFKD", s.lower().replace("ä", "a").replace("ö", "o").replace("å", "a"))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

# ---------- 1. haku ----------
SELECT = ("noticeId,titleFi,organisationNameFi,organisationNationalRegistrationNumber,cpvCodes,nutsCodes,datePublished,"
          "expirationDate,estimatedValue,procedureType,procurementTypeCode,mainType,eFormsId,procurementDocumentsUrl,descriptionFi")
def hae():
    if os.environ.get("TESTI"):
        return [n for n in json.load(open(os.environ["TESTI"]))["value"] if n.get("expirationDate")]
    key = os.environ["HILMA_API_KEY"].strip(); out, skip = [], 0
    raja = NYT.strftime("%Y-%m-%dT%H:%M:%SZ")
    while True:
        body = {"search": "*", "top": 100, "skip": skip, "count": True, "orderby": "datePublished desc", "select": SELECT,
                "filter": f"mainType eq 'ContractNotices' and expirationDate ge {raja}"}
        r = urllib.request.Request("https://api.hankintailmoitukset.fi/avp/eformnotices/docs/search", json.dumps(body).encode(),
                                   {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=60).read())
        out += d["value"]; skip += 100
        if len(d["value"]) < 100 or skip >= 3000: break
    print(f"::notice title=Hilma::haettu {len(out)} voimassa olevaa ilmoitusta (rajapinta kertoo {d.get('@odata.count')})")
    return out

# ---------- 2. tiivistelmät ----------
OHJE = ("Olet Hankintavahti-palvelun toimittaja. Saat julkisen hankintailmoituksen. Kirjoita pienyrittäjälle selkokielinen tiivistelmä "
        "ja luokittele ilmoitus. Vastaa PELKÄLLÄ JSON-oliolla, ei muuta tekstiä:\n"
        '{"otsikko": "lyhyt selkeä otsikko, max 70 merkkiä, mitä ostetaan ja missä",'
        ' "selko": "2–3 lyhyttä lausetta: mitä ostetaan, mihin ja millä aikataululla/kestolla. Ei virkakieltä, ei arvailua.",'
        ' "kunta": "kunta tai kaupunki, jossa työ tehdään tai tavara toimitetaan; tyhjä jos ei selviä",'
        f' "maakunta": "yksi näistä tai tyhjä: {", ".join(MAAKUNNAT)}",'
        f' "ala": "yksi näistä: {", ".join(ALAT)}",'
        ' "pienyritys": "sopii" jos pieni yritys voi realistisesti tarjota (pieni tai paikallinen työ, osiin jaettu, puitesopimus jossa monta toimittajaa), "iso" jos vaatii suuren toimijan, muuten "ehka",'
        ' "perustelu": "yksi lyhyt lause sopivuudesta"}\n'
        "Käytä vain ilmoituksen tietoja. Jos jokin ei selviä, jätä tyhjäksi.")
def claude(n):
    teksti = (f"Otsikko: {n.get('titleFi','')}\nHankintayksikkö: {n.get('organisationNameFi','')}\nLaji: {n.get('procurementTypeCode','')}\n"
              f"Arvioitu arvo: {n.get('estimatedValue') or 'ei ilmoitettu'}\nNUTS: {n.get('nutsCodes','')}\nKuvaus: {(n.get('descriptionFi') or '')[:3500]}")
    d = json.dumps({"model": "claude-haiku-5-5", "max_tokens": 900, "thinking": {"type": "disabled"}, "system": OHJE, "messages": [{"role": "user", "content": teksti}]}).encode()
    r = urllib.request.Request("https://api.anthropic.com/v1/messages", d, {"x-api-key": os.environ["ANTHROPIC_API_KEY"].strip(),
                               "anthropic-version": "2023-06-01", "content-type": "application/json"})
    vast = json.loads(urllib.request.urlopen(r, timeout=90).read())
    t = "".join(c.get("text", "") for c in vast.get("content", []) if c.get("type") == "text")
    j = json.loads(t[t.index("{"):t.rindex("}") + 1])
    if j.get("maakunta") not in MAAKUNNAT: j["maakunta"] = ""
    if j.get("ala") not in ALAT: j["ala"] = "Muut"
    if j.get("pienyritys") not in ("sopii", "iso", "ehka"): j["pienyritys"] = "ehka"
    return j
def tiivista(ilm):
    DATA.mkdir(exist_ok=True); p = DATA / "tiivistelmat.json"
    tv = json.load(open(p)) if p.exists() else {}
    uudet = [n for n in ilm if str(n["noticeId"]) not in tv]
    if os.environ.get("TESTI") and not os.environ.get("ANTHROPIC_API_KEY"):
        for n in uudet:  # paikallinen testi: tekaistu luokittelu
            tv[str(n["noticeId"])] = {"otsikko": n.get("titleFi", "")[:70], "selko": (n.get("descriptionFi") or "")[:220], "kunta": "",
                                      "maakunta": MAAKUNNAT[n["noticeId"] % 19], "ala": ALAT[n["noticeId"] % 14],
                                      "pienyritys": ["sopii", "ehka", "iso"][n["noticeId"] % 3], "perustelu": ""}
    else:
        import time
        uudet.sort(key=lambda n: n["datePublished"], reverse=True)
        uudet = uudet[:int(os.environ.get("MAX_UUSIA", "400"))]  # yhden ajon katto; loput seuraavassa ajossa
        print("tiivistetään", len(uudet), "uutta"); alku = time.time(); perakkain = 0
        with cf.ThreadPoolExecutor(3) as ex:
            for n, res in zip(uudet, ex.map(lambda n: _turva(claude, n), uudet)):
                if res: tv[str(n["noticeId"])] = res; perakkain = 0
                else: perakkain += 1
                if perakkain >= 8 or time.time() - alku > 1500:
                    STOP[0] = True
        json.dump(tv, open(p, "w"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"::notice title=Tiivistelmät::uusia {len(uudet)}, virheitä {len(VIRHEET)}" + (" – esim. " + VIRHEET[0][:300] if VIRHEET else ""))
    voimassa = {str(n["noticeId"]) for n in ilm}
    tv = {k: v for k, v in tv.items() if k in voimassa}  # vanhentuneet pois
    json.dump(tv, open(p, "w"), ensure_ascii=False, indent=0, sort_keys=True)
    return tv
VIRHEET = []; STOP = [False]
def _turva(f, n):
    import time, urllib.error
    if STOP[0]: return None
    for i in range(4):
        try: return f(n)
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read()[:200]!r}"
            if e.code not in (429, 500, 502, 503, 529): break
            time.sleep(min(40, 5 * 2 ** i))
        except Exception as e:
            err = repr(e)[:200]; time.sleep(3)
    VIRHEET.append(f"{n['noticeId']}: {err}"); return None

# ---------- 3. sivut ----------
def e(s): return html.escape(str(s or ""), quote=True)
def pvm(s):
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=2)))
    return f"{d.day}.{d.month}.{d.year}"
def paivia(s): return (dt.datetime.fromisoformat(s.replace("Z", "+00:00")) - NYT).days
def euro(v):
    if not v: return ""
    return f"{int(v):,} €".replace(",", " ")

CSS = """
:root{--bg:#f6f4ee;--paper:#fffdf8;--ink:#13201c;--mute:#5d6b66;--line:#e3ded2;--green:#0f5c4a;--green2:#0b4638;--amber:#e8a33d;--amberbg:#fbf0dc;--red:#b4432f;--ok:#1f7a4d;--okbg:#e2f2e8}
@media (prefers-color-scheme:dark){:root{--bg:#0f1513;--paper:#16201d;--ink:#e9efe9;--mute:#9fb0a9;--line:#26332f;--green:#5fc3a4;--green2:#7fd6bb;--amber:#f0b354;--amberbg:#2c2416;--red:#e07a63;--ok:#7fd6a5;--okbg:#17302a}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Inter",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--green)}.wrap{max-width:1040px;margin:0 auto;padding:0 16px}
header.top{border-bottom:1px solid var(--line);background:var(--paper)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;font-size:19px;color:var(--ink);text-decoration:none;letter-spacing:-.01em}
.logo i{width:30px;height:30px;border-radius:8px;background:var(--green);display:grid;place-items:center;color:#fff;font-style:normal;font-size:16px}
nav a{color:var(--mute);text-decoration:none;margin-left:18px;font-size:15px}nav a:hover{color:var(--ink)}
.hero{padding:44px 0 26px}.hero h1{font-size:clamp(30px,5.4vw,50px);line-height:1.08;margin:0 0 14px;letter-spacing:-.025em;font-weight:800;max-width:780px}
.hero h1 em{font-style:normal;color:var(--green)}.hero p{color:var(--mute);font-size:18px;max-width:640px;margin:0 0 22px}
.stat{display:flex;gap:26px;flex-wrap:wrap;margin:6px 0 0}.stat b{display:block;font-size:26px;letter-spacing:-.02em}.stat span{color:var(--mute);font-size:14px}
.haku{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:12px;margin:22px 0 10px}
.haku input,.haku select{width:100%;font:inherit;padding:11px 12px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink)}
.haku label{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--mute);grid-column:1/-1}
@media(max-width:720px){.haku{grid-template-columns:1fr}nav a.n2{display:none}}
.maara{color:var(--mute);font-size:14px;margin:6px 2px 14px}
.lista{display:grid;gap:12px;margin-bottom:40px}
.kortti{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px 18px 16px;text-decoration:none;color:inherit;display:block;transition:border-color .15s}
.kortti:hover{border-color:var(--green)}
.kortti h3{margin:6px 0 6px;font-size:19px;line-height:1.3;letter-spacing:-.01em}
.kortti p{margin:0 0 10px;color:var(--mute);font-size:15px}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;color:var(--mute)}.meta b{color:var(--ink);font-weight:600}
.tag{display:inline-block;font-size:12.5px;font-weight:600;padding:3px 9px;border-radius:99px;background:var(--bg);border:1px solid var(--line);color:var(--mute);margin-right:6px}
.tag.ok{background:var(--okbg);border-color:transparent;color:var(--ok)}
.dl{font-weight:700;color:var(--ink)}.dl.kiire{color:var(--red)}
.sec{margin:34px 0}.sec h2{font-size:22px;letter-spacing:-.01em;margin:0 0 12px}
.ruudut{display:flex;flex-wrap:wrap;gap:8px}.ruudut a{background:var(--paper);border:1px solid var(--line);border-radius:99px;padding:7px 13px;text-decoration:none;color:var(--ink);font-size:14.5px}
.ruudut a span{color:var(--mute)}.ruudut a:hover{border-color:var(--green)}
.vahti{background:var(--green);color:#fff;border-radius:18px;padding:26px;margin:30px 0}.vahti h2{margin:0 0 8px;font-size:24px}
.vahti p{margin:0;opacity:.9;max-width:620px}
.yks{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:24px;margin:22px 0}
.yks h1{font-size:clamp(24px,4vw,34px);line-height:1.2;margin:8px 0 12px;letter-spacing:-.02em}
.tiedot{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0}
.tiedot div{background:var(--bg);border-radius:10px;padding:12px}.tiedot span{display:block;font-size:13px;color:var(--mute)}.tiedot b{font-size:16px}
.nappi{display:inline-block;background:var(--green);color:#fff;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:10px;margin:6px 8px 6px 0}
.nappi.toinen{background:transparent;color:var(--green);border:1.5px solid var(--green)}
.huom{background:var(--amberbg);border-radius:10px;padding:12px 14px;font-size:14.5px}
details{margin-top:14px}summary{cursor:pointer;color:var(--mute);font-size:14.5px}details p{white-space:pre-line;font-size:14.5px;color:var(--mute)}
footer{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--mute);font-size:14px;margin-top:40px}
.yks-hero{padding:40px 0 18px;text-align:center}.yks-hero h1{margin:0 auto 10px;font-size:clamp(38px,8vw,64px)}.yks-hero p{margin:0 auto}
.iso{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:14px;display:grid;grid-template-columns:2fr 1fr;gap:10px;box-shadow:0 8px 30px rgba(0,0,0,.06);margin:8px 0 6px}
.iso input,.iso select{font:inherit;font-size:18px;padding:15px 14px;border:1.5px solid var(--line);border-radius:12px;background:var(--bg);color:var(--ink);width:100%}
.iso input:focus{outline:none;border-color:var(--green)}
.pika{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:7px}.pika button{font:inherit;font-size:14.5px;padding:7px 12px;border-radius:99px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.pika button.on{background:var(--green);border-color:var(--green);color:#fff}.pika .pk{border-color:var(--ok);color:var(--ok)}.pika .pk.on{background:var(--ok);color:#fff}
@media(max-width:720px){.iso{grid-template-columns:1fr}}
.askeleet{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:26px 0}.askeleet div{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:14px;font-size:15px}
.askeleet b{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--green);color:#fff;margin-bottom:8px}
@media(max-width:720px){.askeleet{grid-template-columns:1fr}}
details.sec summary{font-weight:700;color:var(--ink);font-size:17px}
.kortti .tag.ok{margin-bottom:4px}
.murupolku{font-size:14px;color:var(--mute);margin-top:18px}.murupolku a{color:var(--mute)}
"""
def kehys(otsikko, kuvaus, polku, sisalto, ld=None):
    can = SIVU + polku
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(otsikko)}</title><meta name="description" content="{e(kuvaus)}"><link rel="canonical" href="{can}">
<meta property="og:title" content="{e(otsikko)}"><meta property="og:description" content="{e(kuvaus)}"><meta property="og:url" content="{can}"><meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f5c4a'/%3E%3Ctext x='16' y='22' font-size='17' text-anchor='middle' fill='white' font-family='Arial' font-weight='700'%3EH%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap">
<style>{CSS}</style>{f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ''}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="/"><i>H</i>{NIMI}</a><nav><a href="/">Hankinnat</a><a class="n2" href="/#alueet">Alueet</a><a href="/tietoa/">Tietoa</a></nav></div></header>
<main class="wrap">{sisalto}</main>
<footer><div class="wrap">{NIMI} kokoaa julkiset tarjouspyynnöt selkokielellä pienyrittäjille. Ilmoitusten tiedot: <a href="https://www.hankintailmoitukset.fi/">Hilma – hankintailmoitukset.fi</a> (Hansel Oy), lisenssi CC BY 4.0. Tiivistelmät on tehty tekoälyllä – tarkista aina alkuperäinen tarjouspyyntö ennen tarjouksen jättämistä. · <a href="/tietoa/">Tietoa palvelusta</a> · <a href="/tietosuoja/">Tietosuoja</a></div></footer>
</body></html>"""

def lyhyt(x, n=150):
    x = (x or "").strip(); i = x.find(". ")
    x = x[:i + 1] if 40 < i < n else x
    return x if len(x) <= n else x[:n].rsplit(" ", 1)[0] + "…"
def kortti(n, t):
    dl = paivia(n["expirationDate"]); kiire = dl <= 7
    paikka = t.get("kunta") or t.get("maakunta") or ""
    sop = '<span class="tag ok">✓ Sopii pienelle yritykselle</span>' if t["pienyritys"] == "sopii" else ""
    return (f'<a class="kortti" href="/h/{n["noticeId"]}/" data-mk="{e(t.get("maakunta"))}" data-ala="{e(t["ala"])}" data-pk="{t["pienyritys"]}" '
            f'data-q="{e((t["otsikko"] + " " + n.get("titleFi","") + " " + (n.get("organisationNameFi") or "") + " " + paikka + " " + t["ala"] + " " + t["selko"]).lower())}">'
            f'{sop}<h3>{e(t["otsikko"] or n.get("titleFi"))}</h3><p>{e(lyhyt(t["selko"]))}</p><div class="meta">'
            + (f'<span>📍 {e(paikka)}</span>' if paikka else "")
            + f'<span class="dl{" kiire" if kiire else ""}">⏰ {dl} pv jäljellä</span>'
            + (f'<span>💶 {euro(n.get("estimatedValue"))}</span>' if n.get("estimatedValue") else "")
            + '</div></a>')

SUODATIN = """<script>
(()=>{const q=document.getElementById('q'),mk=document.getElementById('mk'),al=document.getElementById('al'),pk=document.getElementById('pk'),m=document.getElementById('maara');
const k=[...document.querySelectorAll('.lista .kortti')];
function f(){const s=q.value.trim().toLowerCase();let n=0;for(const c of k){const ok=(!s||c.dataset.q.includes(s))&&(!mk.value||c.dataset.mk===mk.value)&&(!al.value||c.dataset.ala===al.value)&&(!pk.checked||c.dataset.pk==='sopii');c.style.display=ok?'':'none';if(ok)n++}m.textContent=n+' avointa hankintaa'}
[q,mk,al,pk].forEach(x=>x.addEventListener('input',f));
const u=new URLSearchParams(location.search);if(u.get('q'))q.value=u.get('q');f();})();
</script>"""

ETUSUODATIN = """<script>
(()=>{const q=document.getElementById('q'),mk=document.getElementById('mk'),al=document.getElementById('al'),pk=document.getElementById('pk'),m=document.getElementById('maara'),L=document.getElementById('lista'),B=document.getElementById('lisaa');
let K=null,osumat=[],n=40;const tmp=document.createElement('div');
const sopii=c=>{const s=q.value.trim().toLowerCase();return(!s||c.dataset.q.includes(s))&&(!mk.value||c.dataset.mk===mk.value)&&(!al.value||c.dataset.ala===al.value)&&(!pk.checked||c.dataset.pk==='sopii')};
function piirra(){if(!K)return;osumat=K.filter(sopii);L.replaceChildren(...osumat.slice(0,n));m.textContent=osumat.length+(osumat.length===1?' hankinta':' avointa hankintaa');B.style.display=osumat.length>n?'':'none'}
function f(){n=40;piirra()}
fetch('/kaikki.json').then(r=>r.json()).then(a=>{K=a.map(h=>{tmp.innerHTML=h;return tmp.firstElementChild});const u=new URLSearchParams(location.search);if(u.get('q'))q.value=u.get('q');piirra()});
[q,mk,al,pk].forEach(x=>x.addEventListener('input',f));B.addEventListener('click',()=>{n+=40;piirra()});
document.querySelectorAll('.pika button[data-ala]').forEach(b=>b.addEventListener('click',()=>{const on=al.value===b.dataset.ala;al.value=on?'':b.dataset.ala;document.querySelectorAll('.pika button[data-ala]').forEach(x=>x.classList.toggle('on',!on&&x===b));f()}));
const pkb=document.getElementById('pkb');pkb.addEventListener('click',()=>{pk.checked=!pk.checked;pkb.classList.toggle('on',pk.checked);f()});})();
</script>"""

def hakupalkki(nayta_mk=True, nayta_ala=True):
    mk = '<select id="mk" aria-label="Maakunta"><option value="">Kaikki maakunnat</option>' + "".join(f'<option>{m}</option>' for m in MAAKUNNAT) + "</select>"
    al = '<select id="al" aria-label="Toimiala"><option value="">Kaikki toimialat</option>' + "".join(f'<option>{a}</option>' for a in ALAT) + "</select>"
    return (f'<div class="haku"><input id="q" type="search" placeholder="Hae: siivous, sähkö, Kalajoki…" aria-label="Hae">'
            f'{mk if nayta_mk else "<select id=mk hidden><option value=\"\"></option></select>"}{al if nayta_ala else "<select id=al hidden><option value=\"\"></option></select>"}'
            '<label><input id="pk" type="checkbox" style="width:auto"> Näytä vain pienyritykselle sopivat</label></div><div class="maara" id="maara"></div>')

def kirjoita(polku, s):
    p = PUB / polku.strip("/") / "index.html" if polku != "/" else PUB / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)

def rakenna(ilm, tv):
    import shutil
    shutil.rmtree(PUB, ignore_errors=True); PUB.mkdir()
    ilm = [n for n in ilm if str(n["noticeId"]) in tv]
    ilm.sort(key=lambda n: n["datePublished"], reverse=True)
    T = lambda n: tv[str(n["noticeId"])]
    sopii = sum(1 for n in ilm if T(n)["pienyritys"] == "sopii")
    vk = sum(1 for n in ilm if (NYT - dt.datetime.fromisoformat(n["datePublished"].replace("Z", "+00:00"))).days < 7)
    mk_n = {m: sum(1 for n in ilm if T(n).get("maakunta") == m) for m in MAAKUNNAT}
    al_n = {a: sum(1 for n in ilm if T(n)["ala"] == a) for a in ALAT}
    ruudut = lambda d, pre: "".join(f'<a href="/{pre}/{slug(k)}/">{k} <span>{v}</span></a>' for k, v in d.items() if v)
    PIKA = [("Rakentaminen", "Rakentaminen ja korjaus"), ("Sähkö & LVI", "Sähkö, LVI ja talotekniikka"), ("Siivous & kiinteistöt", "Kiinteistöhuolto ja siivous"),
            ("Kuljetus", "Kuljetus ja logistiikka"), ("Ruoka", "Ruoka ja ateriapalvelut"), ("IT", "IT ja ohjelmistot"), ("Kalusteet", "Kalusteet ja tarvikkeet"),
            ("Metsä & ympäristö", "Maa-, metsä- ja ympäristötyöt"), ("Konsultointi", "Konsultointi ja asiantuntijat"), ("Sote", "Sosiaali- ja terveyspalvelut")]
    mksel = '<select id="mk" aria-label="Alue"><option value="">📍 Koko Suomi</option>' + "".join(f'<option>{m}</option>' for m in MAAKUNNAT) + "</select>"
    etusivu = (f'<section class="hero yks-hero"><h1>Kunnat ostavat.<br><em>Sinä myyt.</em></h1>'
               f'<p>Kaikki julkiset tarjouspyynnöt yhdessä paikassa, selkokielellä ja ilmaiseksi.</p></section>'
               f'<div class="iso"><input id="q" type="search" placeholder="🔍 Mitä yrityksesi tekee?" aria-label="Mitä yrityksesi tekee?">{mksel}'
               '<select id="al" hidden><option value=""></option>' + "".join(f'<option>{a}</option>' for a in ALAT) + '</select>'
               '<div class="pika">' + "".join(f'<button type="button" data-ala="{e(v)}">{e(k)}</button>' for k, v in PIKA)
               + '<button type="button" id="pkb" class="pk">✓ Vain pienelle sopivat</button></div><input id="pk" type="checkbox" hidden></div>'
               f'<div class="maara" id="maara">{len(ilm)} avointa hankintaa</div>'
               + '<div class="lista" id="lista">' + "".join(kortti(n, T(n)) for n in ilm[:40]) + '</div><p style="text-align:center"><button id="lisaa" class="nappi" style="border:0;cursor:pointer;font:inherit;font-weight:700">Näytä lisää</button></p>'
               + '<section class="askeleet"><div><b>1</b>Kirjoita, mitä yrityksesi tekee</div><div><b>2</b>Valitse alue</div><div><b>3</b>Avaa hankinta ja jätä tarjous</div></section>'
               + f'<details class="sec" id="alueet"><summary>Selaa alueittain ja toimialoittain</summary><h2>Maakunnat</h2><div class="ruudut">{ruudut(mk_n, "maakunta")}</div><h2>Toimialat</h2><div class="ruudut">{ruudut(al_n, "ala")}</div></details>' + ETUSUODATIN)
    (PUB / "kaikki.json").write_text(json.dumps([kortti(n, T(n)) for n in ilm], ensure_ascii=False))
    kirjoita("/", kehys(f"{NIMI} – julkiset tarjouspyynnöt selkokielellä pienyrittäjille",
                        f"{len(ilm)} avointa julkista hankintaa selkokielellä. Katso mitä kunnat ja hyvinvointialueet ostavat ja löydä sopivat tarjouspyynnöt pienyrityksellesi.", "/", etusivu,
                        {"@context": "https://schema.org", "@type": "WebSite", "name": NIMI, "url": SIVU}))
    urls = ["/"]
    for laji, nimet, avain, pre in (("maakunta", MAAKUNNAT, "maakunta", "maakunta"), ("ala", ALAT, "ala", "ala")):
        for k in nimet:
            osa = [n for n in ilm if T(n).get(avain) == k]
            if not osa: continue
            pol = f"/{pre}/{slug(k)}/"; urls.append(pol)
            otsikko = f"Avoimet julkiset hankinnat: {k}" if laji == "maakunta" else f"Julkiset hankinnat: {k}"
            sis = (f'<div class="murupolku"><a href="/">Hankinnat</a> › {e(k)}</div><section class="hero" style="padding-top:20px"><h1>{e(otsikko)}</h1>'
                   f'<p>{len(osa)} avointa tarjouspyyntöä {"alueella " + k if laji == "maakunta" else "toimialalla " + k.lower()}. Päivitetään joka yö.</p></section>'
                   + hakupalkki(laji != "maakunta", laji != "ala") + '<div class="lista">' + "".join(kortti(n, T(n)) for n in osa) + "</div>" + SUODATIN)
            kirjoita(pol, kehys(f"{otsikko} | {NIMI}", f"{len(osa)} avointa julkista tarjouspyyntöä: {k}. Selkokieliset tiivistelmät ja jättöpäivät.", pol, sis))
    for n in ilm:
        t = T(n); pol = f"/h/{n['noticeId']}/"; urls.append(pol)
        hilma = f"https://hankintailmoitukset.fi/fi/notice/{n.get('eFormsId') or n['noticeId']}"
        tiedot = [("Hankintayksikkö", n.get("organisationNameFi")), ("Paikka", t.get("kunta") or t.get("maakunta")), ("Toimiala", t["ala"]),
                  ("Arvioitu arvo", euro(n.get("estimatedValue")) + (" (alv 0 %)" if n.get("estimatedValue") else "")),
                  ("Viimeinen jättöpäivä", f'{pvm(n["expirationDate"])} · {paivia(n["expirationDate"])} pv jäljellä'), ("Julkaistu", pvm(n["datePublished"]))]
        sop = {"sopii": ("Sopii pienyritykselle", "ok"), "iso": ("Vaatii todennäköisesti suuren toimijan", ""), "ehka": ("Sopivuus riippuu yrityksestä", "")}[t["pienyritys"]]
        sis = (f'<div class="murupolku"><a href="/">Hankinnat</a> › ' + (f'<a href="/maakunta/{slug(t["maakunta"])}/">{e(t["maakunta"])}</a> › ' if t.get("maakunta") else "") + 'Tarjouspyyntö</div>'
               f'<article class="yks"><span class="tag">{e(t["ala"])}</span><span class="tag {sop[1]}">{sop[0]}</span><h1>{e(t["otsikko"] or n.get("titleFi"))}</h1>'
               f'<p style="font-size:17px">{e(t["selko"])}</p>' + (f'<p class="huom">{e(t["perustelu"])}</p>' if t.get("perustelu") else "")
               + '<div class="tiedot">' + "".join(f'<div><span>{a}</span><b>{e(b)}</b></div>' for a, b in tiedot if b) + "</div>"
               + (f'<a class="nappi" href="{e(n["procurementDocumentsUrl"])}" rel="nofollow noopener" target="_blank">Avaa tarjouspyyntö ja asiakirjat</a>' if n.get("procurementDocumentsUrl") else "")
               + f'<a class="nappi toinen" href="{e(hilma)}" rel="nofollow noopener" target="_blank">Ilmoitus Hilmassa</a>'
               + f'<details><summary>Alkuperäinen kuvaus: {e(n.get("titleFi"))}</summary><p>{e(n.get("descriptionFi"))}</p></details></article>')
        kirjoita(pol, kehys(f"{t['otsikko'] or n.get('titleFi')} | {NIMI}", (t["selko"] or "")[:155], pol, sis))
    tietoa = ('<article class="yks"><h1>Tietoa Hankintavahdista</h1>'
              '<p>Julkinen sektori ostaa Suomessa vuosittain kymmenillä miljardeilla euroilla palveluita, tavaroita ja urakoita. Suuri osa tarjouspyynnöistä sopisi myös pienille ja paikallisille yrityksille, mutta ne hukkuvat virkakieleen ja hajallaan oleviin portaaleihin.</p>'
              f'<p>{NIMI} hakee joka yö kaikki voimassa olevat hankintailmoitukset Hilmasta, tekee niistä tekoälyllä selkokielisen tiivistelmän ja arvioi, sopiiko hankinta pienyritykselle. Tarjoukset jätetään aina hankintayksikön omassa järjestelmässä – linkki löytyy jokaisen ilmoituksen sivulta.</p>'
              '<h2>Tietolähde</h2><p>Ilmoitusten tiedot ovat peräisin julkisten hankintojen ilmoituskanava Hilmasta (hankintailmoitukset.fi, Hansel Oy), lisenssi CC BY 4.0. Tiivistelmät ja luokittelu on tehty tekoälyllä, ja ne voivat sisältää virheitä. Tarkista aina alkuperäinen tarjouspyyntö.</p>'
              '<h2>Ylläpitäjä</h2><p>Palvelun tuottaa Taksiliikenne Koskela Oy (Y-tunnus 3425681-3). Yhteys: info@netvo.fi.</p></article>')
    kirjoita("/tietoa/", kehys(f"Tietoa | {NIMI}", f"Mikä {NIMI} on ja mistä tiedot tulevat.", "/tietoa/", tietoa)); urls.append("/tietoa/")
    ts = seloste(palvelu=f"{NIMI} (hankintavahti.com)", rekisterinpitaja="Taksiliikenne Koskela Oy (Y-tunnus 3425681-3), palvelun nimi Hankintavahti", yhteys="info@netvo.fi",
        tiedot=[("Tekniset lokitiedot", "kun avaat sivun, palvelin käsittelee laitteesi IP-osoitteen, selaimen tiedot ja pyydetyn sivun. Tietoja käytetään vain sivuston toimittamiseen ja tietoturvaan."),
                ("Ei rekisteröitymistä", "palvelua käytetään ilman kirjautumista. Emme kerää nimeä, sähköpostia tai muita yhteystietoja, ellet itse lähetä meille sähköpostia."),
                ("Sähköpostit", "jos otat yhteyttä sähköpostilla, käsittelemme viestisi ja yhteystietosi vastataksemme sinulle.")],
        tarkoitus="Tietoja käsitellään sivuston teknistä toimittamista ja tietoturvaa varten sekä yhteydenottoihin vastaamiseksi. Peruste on oikeutettu etu (palvelun toimivuus ja turvallisuus) ja yhteydenotoissa oma pyyntösi.",
        kasittelijat=[("Cloudflare, Inc.", "sivuston palvelin ja tietoturva"), ("Google LLC (Google Fonts)", "kirjasintiedostot ladataan Googlen palvelimelta, jolloin laitteesi IP-osoite välittyy Googlelle")],
        sailytys="Tekniset lokitiedot poistuvat palveluntarjoajan järjestelmistä lyhyen ajan kuluessa. Sähköpostit säilytetään niin kauan kuin asian hoitaminen vaatii.",
        evasteet="Sivusto ei käytä seuranta- tai mainosevästeitä eikä kävijäanalytiikkaa.")
    kirjoita("/tietosuoja/", kehys(f"Tietosuojaseloste | {NIMI}", f"{NIMI}n tietosuojaseloste.", "/tietosuoja/", f'<div class="yks">{ts}</div>')); urls.append("/tietosuoja/")
    (PUB / "404.html").write_text(kehys(f"Sivua ei löydy | {NIMI}", "Sivua ei löydy", "/404", '<article class="yks"><h1>Sivua ei löytynyt</h1><p>Hankinta on ehkä jo päättynyt. <a href="/">Katso avoimet hankinnat</a>.</p></article>'))
    (PUB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{SIVU}{u}</loc></url>" for u in urls) + "</urlset>")
    (PUB / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SIVU}/sitemap.xml\n")
    print(f"::notice title=Sivut::{len(urls)} sivua, {len(ilm)} hankintaa, sopii pienyritykselle {sopii}")

if __name__ == "__main__":
    ilm = hae(); tv = tiivista(ilm); rakenna(ilm, tv)
