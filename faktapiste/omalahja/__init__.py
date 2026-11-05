"""Omalahja (omalahja.fi): personoidut julisteet ja taulut, painatus tilauksesta (Gelato). Sivut kirjoitetaan kansioon <root>/omalahja/.
Hinnat ja tilausten avaus: tuotteet.json ("avoinna": true/false). Suunnittelija: tee.js + kuviot.js + kartta.js."""
import html, json, pathlib, shutil
esc = html.escape
HAKEMISTO = pathlib.Path(__file__).parent
YRITYS = "Taksiliikenne Koskela Oy"
YTUNNUS = "3425681-3"
OSOITE = "Riihikatu 3 B 20, 84100 Ylivieska"
EMAIL = "info@omalahja.fi"
PUH = "044 777 7149"
PV = "5.11.2026"
CONFIG = json.loads((HAKEMISTO / "tuotteet.json").read_text(encoding="utf-8"))
VERSIO = "20261105"

def euro(sentit):
    return (f"{sentit / 100:.2f}".replace(".", ",") if sentit % 100 else str(sentit // 100)) + " €"

def julkinen_config():
    """Selaimelle vain tarvittava: ei Gelaton tuotetunnuksia eikä kustannuksia."""
    t = {}
    for k, v in CONFIG["tuotteet"].items():
        t[k] = {"nimi": v["nimi"], "kuvaus": v["kuvaus"], "reuna": v["reuna"], "koot": {kk: {"mm": x["mm"], "hinta": x["hinta"]} for kk, x in v["koot"].items()}}
        if "varit" in v: t[k]["varit"] = {vk: {"nimi": vv["nimi"], "css": vv["css"]} for vk, vv in v["varit"].items()}
    return {"avoinna": CONFIG["avoinna"], "dpi": CONFIG["dpi"], "maxPikselit": CONFIG["maxPikselit"], "tuotteet": t}

FONTIT_URL = ("https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Amatic+SC:wght@700&family=Cinzel:wght@600&family=Cormorant+Garamond:wght@500"
              "&family=Dancing+Script:wght@700&family=EB+Garamond&family=Great+Vibes&family=Josefin+Sans:wght@300;400&family=Lato&family=Montserrat:wght@400;700"
              "&family=Nunito&family=Pacifico&family=Playfair+Display:wght@700&family=Quicksand:wght@500&family=Raleway:wght@500&display=swap")

PERUS_CSS = """
:root{--bg:#fbf6ef;--card:#fffdf9;--ink:#2b2321;--mute:#6f625c;--line:#ebe0d3;--accent:#7a2e2e;--accent2:#c9822b;--seina:#ece3d6;--tint:#f4e6df}
@media (prefers-color-scheme:dark){:root{--bg:#1d1715;--card:#26201d;--ink:#f3ebe3;--mute:#b8aaa1;--line:#3a312c;--accent:#e08a7a;--accent2:#e6b06a;--seina:#2b2420;--tint:#3a2925;color-scheme:dark}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 "Nunito Sans",system-ui,sans-serif;overflow-x:hidden}
.w{max-width:1040px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left))}
header.yla{padding:12px 0;border-bottom:1px solid var(--line);background:var(--bg)}header.yla .w{display:flex;justify-content:space-between;align-items:center;gap:12px;max-width:1200px}
header.yla nav{display:flex;gap:18px;align-items:center;font-weight:700;font-size:.95rem}header.yla nav a{text-decoration:none;color:var(--ink)}header.yla nav a:hover{color:var(--accent)}
header.yla nav .nav-cta{display:none;background:var(--accent);color:#fff;padding:9px 16px;border-radius:99px}
@media (min-width:720px){header.yla nav .nav-cta{display:inline-block}}
@media (max-width:420px){header.yla nav{gap:12px;font-size:.88rem}}
.logo{display:inline-flex;align-items:center;gap:8px;font-family:Fraunces,Georgia,serif;font-weight:650;font-size:1.45rem;color:var(--accent);text-decoration:none;letter-spacing:-.01em}
.logo svg{width:26px;height:26px;flex:none}
header.yla.paalla{position:absolute;left:0;right:0;top:auto;z-index:10;background:transparent;border-bottom-color:#ffffff2e}
header.yla.paalla .logo,header.yla.paalla nav a{color:#fff8ef}header.yla.paalla .logo svg{color:#a8473a}header.yla.paalla nav .nav-cta{background:#fff8ef;color:#5a2020}
h1,h2,h3{font-family:Fraunces,Georgia,serif;font-weight:650;line-height:1.15;margin:0 0 .5em}h1{font-size:clamp(2.1rem,6vw,3.6rem)}h2{font-size:1.6rem;margin-top:1.6em}
a{color:var(--accent)}.mute{color:var(--mute)}
.hero{padding:48px 0 28px}.hero p{font-size:1.15rem;max-width:40em}
.badge{display:inline-block;background:var(--accent2);color:#2b1a08;font-weight:700;border-radius:99px;padding:4px 14px;font-size:.85rem;margin-bottom:16px}
.kortit{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));margin:24px 0 48px}
.kortti{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;display:flex;flex-direction:column;gap:8px;text-decoration:none;color:inherit}
a.kortti:hover{border-color:var(--accent)}.kortti h3{font-size:1.3rem;margin:0}.kortti p{margin:0;color:var(--mute)}.hinta{font-family:Fraunces,serif;font-size:1.3rem;color:var(--ink)}
.kortti .nappi{align-self:flex-start;margin-top:auto}
.nappi{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 24px;border-radius:99px;border:0;background:var(--accent);color:#fff;font:700 1rem "Nunito Sans",system-ui,sans-serif;letter-spacing:.01em;text-decoration:none;cursor:pointer;transition:background .2s,transform .2s}
.nappi:hover{filter:brightness(.94)}.nappi:active{transform:translateY(1px)}
:focus-visible{outline:2px solid var(--accent2);outline-offset:3px}
@media (prefers-color-scheme:dark){.nappi{color:#1d1715}}
.nappi.pieni{min-height:44px;min-width:44px;padding:0 12px;background:var(--card);color:var(--ink);border:1px solid var(--line)}
.nappi:disabled{opacity:.55;cursor:wait}
.teksti{max-width:760px;padding:36px 0 64px}
table.hinnat{border-collapse:collapse;width:100%;font-size:.95rem}table.hinnat td,table.hinnat th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left}
footer.ala{background:#1e2b27;color:#c9c3b8;padding:72px 0 32px;font-size:.95rem;margin-top:0}footer.ala a{color:#e9e3d8;text-decoration:none}footer.ala a:hover{color:#e9bf85}
@media (prefers-color-scheme:dark){footer.ala{background:#141c19}}
footer.ala .w{max-width:1200px}.ala-sar{display:grid;gap:36px 28px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
footer.ala .logo{color:#fff8ef;font-size:2.2rem}footer.ala .logo svg{color:#a8473a;width:34px;height:34px}footer.ala p{margin:12px 0 0;line-height:1.6;max-width:22em}
footer.ala h4{font-family:"Nunito Sans",sans-serif;font-variant-caps:all-small-caps;letter-spacing:.09em;color:#e9bf85;font-size:1.02rem;font-weight:700;margin:0 0 12px}footer.ala ul{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.ala-pohja{border-top:1px solid #ffffff1f;margin-top:48px;padding-top:20px;font-size:.85rem;display:flex;flex-wrap:wrap;gap:6px 22px;color:#9e988e}
"""

TEE_CSS = """
body{padding-bottom:84px}
.tee{display:grid;grid-template-columns:minmax(0,1fr)}
.esikatselu{position:sticky;top:0;z-index:5;height:46vh;min-height:270px;background:var(--seina);display:flex;align-items:center;justify-content:center;border-bottom:1px solid var(--line);overflow:hidden}
body.iso-esikatselu .esikatselu{height:80vh}
.taulu{position:relative;line-height:0;background:var(--kehys,transparent)}
.taulu canvas{display:block}
.taulu.juliste canvas{box-shadow:0 1px 3px #0003,0 10px 26px #0003}
.taulu.canvas canvas{box-shadow:4px 4px 0 #00000026,0 14px 28px #0004}
.taulu.kehys{padding:var(--kp);box-shadow:0 2px 4px #0004,0 14px 30px #0004;outline:1px solid #0002}
.taulu.kehys canvas{box-shadow:inset 0 0 6px #0003}
#suurenna{position:absolute;right:10px;top:10px;min-height:36px;font-size:.85rem;padding:0 12px;border-radius:99px}
#lataus{position:absolute;left:10px;bottom:10px;right:10px;display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 12px;line-height:1.4;font-weight:600;font-size:.95rem}
#lataus[hidden]{display:none}
.ohjaimet{padding:8px 16px 24px}
.otsake{padding:16px 16px 0}.otsake h1{font-size:1.7rem;margin:0 0 4px}.otsake p{margin:0;color:var(--mute)}
details.osio{border-bottom:1px solid var(--line)}
details.osio>summary{list-style:none;cursor:pointer;padding:16px 0;font-family:Fraunces,Georgia,serif;font-weight:650;font-size:1.2rem;display:flex;justify-content:space-between;align-items:center}
details.osio>summary::-webkit-details-marker{display:none}
details.osio>summary::after{content:"+";font-family:"Nunito Sans",sans-serif;font-size:1.4rem;color:var(--mute)}details.osio[open]>summary::after{content:"–"}
.osio-sis{padding:0 0 18px;display:flex;flex-direction:column;gap:14px}
.ryhma-otsikko{font-weight:700;font-size:.92rem;margin-bottom:6px}
.valinnat{display:flex;flex-wrap:wrap;gap:8px}
.valinta{min-height:44px;padding:8px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);color:var(--ink);font:600 .95rem "Nunito Sans",system-ui,sans-serif;cursor:pointer;text-align:left}
.valinta[aria-checked="true"]{border-color:var(--accent);background:var(--tint);box-shadow:0 0 0 1px var(--accent)}
.valinnat.tuotteet,.valinnat.paletit,.valinnat.fontit{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr))}
.tuote-k{display:flex;flex-direction:column;line-height:1.25}.tuote-k small{color:var(--mute);font-weight:600}
.fontti-k{display:flex;flex-direction:column;align-items:center;gap:2px;line-height:1.2}.fontti-k b{font-size:1.45rem;font-weight:inherit}.fontti-k small{color:var(--mute)}
.valinnat.fontit .valinta,.valinnat.paletit .valinta{text-align:center}
.paletti-k{display:flex;flex-wrap:wrap;justify-content:center;gap:4px;align-items:center}.paletti-k i{width:22px;height:22px;border-radius:50%;display:inline-block}.paletti-k small{flex-basis:100%;text-align:center;color:var(--mute);font-size:.8rem}
.valinnat.kuviot{display:grid;grid-template-columns:repeat(auto-fill,minmax(78px,1fr))}
.valinnat.kuviot .valinta{padding:6px;text-align:center}
.kuvake-k{display:flex;flex-direction:column;align-items:center;gap:4px;line-height:1.15}.kuvake-k small{font-size:.7rem;color:var(--mute);overflow-wrap:anywhere;max-width:100%}
canvas.kuvake{width:52px;height:52px;border-radius:8px}
.kehysvari{display:flex;align-items:center;gap:8px}.kehysvari i{width:20px;height:20px;border-radius:4px;box-shadow:inset 0 0 0 1px #0003}
.kentta{display:flex;flex-direction:column;gap:4px;font-weight:600;font-size:.95rem}.kentta small{font-weight:400;color:var(--mute)}
.kentta input,.kentta textarea,.kentta select,.hakurivi input{font:inherit;font-weight:400;font-size:16px;padding:11px 12px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--ink);width:100%;min-height:46px}
.kentta textarea{resize:vertical}
.rinnakkain{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
[hidden]{display:none!important}
.rasti{display:flex;gap:10px;align-items:flex-start;font-weight:600;cursor:pointer}.rasti input{width:22px;height:22px;flex:none;margin-top:2px;accent-color:var(--accent)}
.vihje{margin:0;color:var(--mute);font-size:.9rem}
.hakurivi{display:flex;gap:8px}
.tulokset{display:flex;flex-direction:column;gap:6px}
.tulos{text-align:left;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit;cursor:pointer;display:flex;flex-direction:column;line-height:1.3}.tulos small{color:var(--mute)}
.pikat{display:flex;flex-wrap:wrap;gap:6px}.pika{min-height:40px;padding:6px 12px;border-radius:99px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:600 .9rem "Nunito Sans",sans-serif;cursor:pointer}
.zoomrivi{display:flex;gap:10px;align-items:center}.zoomrivi input{flex:1;accent-color:var(--accent);height:44px}
.nuolet{display:flex;gap:8px}
.alapalkki{position:fixed;left:0;right:0;bottom:0;z-index:20;background:var(--card);border-top:1px solid var(--line);padding:10px max(16px,env(safe-area-inset-left)) calc(10px + env(safe-area-inset-bottom));display:flex;justify-content:space-between;align-items:center;gap:12px}
.alapalkki .nappi{white-space:nowrap;flex:none}.alapalkki>div{min-width:0}.alapalkki b{font-family:Fraunces,serif;font-size:1.45rem;display:block;line-height:1.1}.alapalkki span{font-size:.8rem;color:var(--mute);display:block;line-height:1.3}
.kassa{padding:8px 16px 40px;max-width:640px}
.kassa form{display:flex;flex-direction:column;gap:12px}
.ilmoitus{background:var(--tint);border:1px solid var(--accent);border-radius:12px;padding:14px 16px;font-weight:600}
.viesti{min-height:1.4em;margin:0;font-weight:600}.viesti.virhe{color:#b3261e}
@media (prefers-color-scheme:dark){.viesti.virhe{color:#ff8a80}}
@media (min-width:900px){
 .tee{grid-template-columns:minmax(0,1.15fr) minmax(380px,.85fr);gap:28px;max-width:1280px;margin:0 auto;padding:16px}
 .esikatselu{top:16px;height:calc(100vh - 200px);min-height:420px;border:1px solid var(--line);border-radius:18px}
 .otsake,.ohjaimet{padding-left:0;padding-right:0}
 .kassa{margin:0 auto}
}
"""

LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="currentColor"/><path d="M8 14h16v12H8zM6 10h20v4H6zM16 10v16" stroke="#fff6ec" stroke-width="2" fill="none"/></svg>'

def sivu(otsikko, kuvaus, runko, polku, malli=None, lisapaa="", ylapalkki="", header_luokka=""):
    keho = f' data-malli="{malli}"' if malli else ""
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}"><link rel="canonical" href="https://omalahja.fi{polku}">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}"><meta property="og:url" content="https://omalahja.fi{polku}"><meta property="og:locale" content="fi_FI"><meta property="og:type" content="website">
<meta property="og:image" content="https://omalahja.fi/kuvat/nimi-perhe.jpg">
<meta name="theme-color" content="#7a2e2e"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%237a2e2e'/%3E%3Cpath d='M8 14h16v12H8zM6 10h20v4H6zM16 10v16' stroke='%23fff6ec' stroke-width='2' fill='none'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;0,9..144,650;1,9..144,500&family=Nunito+Sans:wght@400;600;700&display=swap">
{lisapaa}<style>{PERUS_CSS}</style></head><body{keho}>{ylapalkki}
<header class="yla {header_luokka}"><div class="w"><a class="logo" href="/">{LOGO}Omalahja</a><nav aria-label="Päävalikko"><a href="/tee/nimijuliste/">Nimijuliste</a><a href="/tee/kartta/">Karttajuliste</a><a class="nav-cta" href="/tee/nimijuliste/">Suunnittele</a></nav></div></header>
<main>{runko}</main>
<footer class="ala"><div class="w"><div class="ala-sar">
<div><a class="logo" href="/">{LOGO}Omalahja</a><p>Personoidut julisteet ja taulut suomeksi. Suunnittelet itse – me painamme ja toimitamme kotiin.</p></div>
<div><h4>Suunnittele</h4><ul><li><a href="/tee/nimijuliste/">Nimijuliste</a></li><li><a href="/tee/kartta/">Karttajuliste</a></li><li><a href="/tee/nimijuliste/?esim=jae">Raamatunlause</a></li><li><a href="/tee/kartta/?esim=betlehem">Raamatun paikat</a></li></ul></div>
<div><h4>Asiakaspalvelu</h4><ul><li><a href="/toimitusehdot/">Toimitus- ja maksuehdot</a></li><li><a href="/tietosuoja/">Tietosuojaseloste</a></li><li><a href="/yhteystiedot/">Yhteystiedot</a></li><li><a href="mailto:{EMAIL}">{EMAIL}</a></li></ul></div>
<div><h4>Yritys</h4><p>{YRITYS}<br>Y-tunnus {YTUNNUS}<br>{OSOITE}<br>puh. {PUH}</p></div></div>
<div class="ala-pohja"><span>© 2026 Omalahja</span><span>Karttatiedot © OpenStreetMap contributors</span><span>Kuvat: <a href="https://unsplash.com" rel="noopener">Unsplash</a></span></div></div></footer>
</body></html>"""

def alin_hinta():
    return min(k["hinta"] for t in CONFIG["tuotteet"].values() for k in t["koot"].values())

def hintataulukko():
    rivit = "".join(f"<tr><td>{esc(t['nimi'])}</td><td>{kk.replace('x', ' × ')} cm</td><td>{euro(k['hinta'])}</td></tr>" for t in CONFIG["tuotteet"].values() for kk, k in t["koot"].items())
    return f'<table class="hinnat"><thead><tr><th>Tuote</th><th>Koko</th><th>Hinta</th></tr></thead><tbody>{rivit}</tbody></table>'

HERO_ID = "photo-1618221195710-dd6b41faaea6"   # Unsplash: valoisa olohuone, tyhjä seinä (tarkistettu 5.11.2026)
SEINA_ID = "photo-1555041469-a586c61ea9bc"  # Unsplash: vihreä sohva tyhjän seinän edessä (tarkistettu 5.11.2026)

def unsplash(pid, w, q=72):
    return f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w={w}&q={q}"

def srcset(pid, leveydet=(640, 960, 1280, 1920, 2560)):
    return ", ".join(f"{unsplash(pid, w)} {w}w" for w in leveydet)

# Esimerkkikuvat (renderöity omalla suunnittelijalla, faktapiste/omalahja/kuvat/). (tiedosto, otsikko, kuvaus, linkki, leveys, korkeus, luokat, kehys)
ESIMERKIT = [
    ("nimi-perhe", "Perhejuliste", "Koko perheen nimet ja lehvä", "/tee/nimijuliste/?esim=perhe", 1000, 1333, "nimet", "puu"),
    ("kartta-helsinki", "Helsinki", "Kotikaupunki klassisena karttana", "/tee/kartta/?esim=helsinki", 1000, 1400, "kartat", "musta"),
    ("nimi-vauva", "Vauvajuliste", "Nimi, syntymäaika, paino ja pituus", "/tee/nimijuliste/?esim=vauva", 1000, 1333, "nimet", "valk"),
    ("kartta-betlehem", "Betlehem", "Raamatun paikka ja jouluevankeliumin jae", "/tee/kartta/?esim=betlehem", 1000, 1400, "kartat raamattu", "puu"),
    ("nimi-haat", "Hääjuliste", "Hääpäivä laakeriseppeleen keskellä", "/tee/nimijuliste/?esim=haat", 1000, 1333, "nimet", "musta"),
    ("kartta-ylivieska", "Ylivieska", "Ympyräkartta yön sävyissä", "/tee/kartta/?esim=ylivieska", 1000, 1400, "kartat", "valk"),
    ("nimi-jae", "Raamatunlause", "Psalmi kaunokirjoituksella", "/tee/nimijuliste/?esim=jae", 1000, 1333, "nimet raamattu", "puu"),
    ("kartta-tampere", "Sydänkartta", "Paikka, josta kaikki alkoi", "/tee/kartta/?esim=tampere", 1000, 1400, "kartat", "valk"),
    ("nimi-kaste", "Kastejuliste", "Nimi, kastepäivä ja siunaava jae", "/tee/nimijuliste/?esim=kaste", 1000, 1333, "nimet raamattu", "musta"),
]
TILAISUUDET = [("Joulu", "/tee/nimijuliste/?esim=joulu", "nimi-joulu"), ("Häät", "/tee/nimijuliste/?esim=haat", "nimi-haat"),
               ("Vauva", "/tee/nimijuliste/?esim=vauva", "nimi-vauva"), ("Kotikaupunki", "/tee/kartta/?esim=helsinki", "kartta-helsinki"),
               ("Rippijuhlat ja kaste", "/tee/nimijuliste/?esim=kaste", "nimi-kaste"), ("Muistolahja", "/tee/nimijuliste/?esim=muisto", "nimi-muisto")]
KARTTA_SEINA_ID = "photo-1513694203232-719a280e022f"  # Unsplash: tyhjä vaalea seinä, musta sohva ja lipasto (tarkistettu 5.11.2026)

ETUSIVU_CSS = """
:root{--seina:#e9e1d5;--kuusi:#1e2b27;--puolukka:#7a2e2e;--hunaja:#e9bf85;--hius:#d9cfc1}
@media (prefers-color-scheme:dark){:root{--seina:#2a2420;--kuusi:#141c19;--hius:#3d342e}}
""" + """.tiedote{background:#3d2a22;color:#fbefe2;text-align:center;font-size:.9rem;font-weight:600;padding:9px 16px;line-height:1.4}
.tiedote a{color:#f4c98d;white-space:nowrap}
.sankari{position:relative;isolation:isolate;min-height:min(92svh,860px);display:flex;align-items:stretch;color:#fff8ef;overflow:hidden;background:#3a2c24}
.sankari-kuva{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:60% 50%;z-index:-2}
.sankari::before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(32,22,16,.78) 0%,rgba(32,22,16,.55) 45%,rgba(32,22,16,.35) 70%,rgba(32,22,16,.6) 100%)}
.sankari-sis{width:100%;max-width:1200px;margin:0 auto;padding:96px max(18px,env(safe-area-inset-left)) 40px;display:grid;gap:30px;align-content:center}
.ylateksti{text-transform:uppercase;letter-spacing:.18em;font-size:.78rem;font-weight:700;color:#f4c98d;margin:0 0 14px}
.sankari h1{font-size:clamp(2.6rem,10vw,4.6rem);line-height:1.02;margin:0 0 18px;letter-spacing:-.02em;text-wrap:balance}
.sankari h1 em{font-style:italic;font-weight:500;color:#f4c98d}
.sankari p.ingressi{font-size:1.12rem;line-height:1.55;max-width:34em;margin:0 0 26px;color:#f6ebe0}
.napit{display:flex;flex-wrap:wrap;gap:12px}
.nappi.iso{min-height:54px;padding:0 26px;font-size:1.05rem;border-radius:99px;background:#f4c98d;color:#2f1c12;box-shadow:0 8px 24px #0004}
.nappi.iso:hover{background:#ffd9a6}
.nappi.haamu{min-height:54px;padding:0 22px;border-radius:99px;background:transparent;border:1.5px solid #fff8efb0;color:#fff8ef}
@media (max-width:520px){.napit .nappi{width:100%}.sankari h1{font-size:2.55rem}.sankari p.ingressi{font-size:1.04rem}.sankari-sis{padding-top:88px}}
.pikaedut{list-style:none;padding:0;margin:22px 0 0;display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.92rem;font-weight:600;color:#f6ebe0}
.pikaedut li::before{content:"✓";color:#f4c98d;margin-right:6px}
.mockup{position:relative;height:min(78vw,420px);margin-top:6px}
.kehys{position:absolute;margin:0;background:#1d1a18;padding:2.2%;box-shadow:0 2px 3px #0005,0 18px 40px #000a,0 40px 70px #0005}
.kehys img{display:block;width:100%;height:auto;box-shadow:inset 0 0 0 1px #0002}
.kehys.puu{background:linear-gradient(135deg,#d6b48a,#b98d5e 50%,#caa275)}
.kehys.valk{background:#f4f1ec}
.kehys.k1{width:46%;left:6%;top:4%;transform:rotate(-1.2deg)}
.kehys.k2{width:41%;right:6%;top:16%;transform:rotate(1.4deg)}
@media (min-width:900px){
 .sankari-sis{grid-template-columns:1.05fr .95fr;align-items:center;padding-top:110px;gap:40px}
 .sankari::before{background:linear-gradient(90deg,rgba(32,22,16,.82) 0%,rgba(32,22,16,.62) 42%,rgba(32,22,16,.18) 75%,rgba(32,22,16,.1) 100%)}
 .mockup{height:560px}.kehys.k1{width:50%;left:4%;top:2%}.kehys.k2{width:43%;right:2%;top:20%}
}
""" + """
.js .ilmesty{opacity:0;transform:translateY(14px);transition:opacity .9s ease,transform .9s cubic-bezier(.2,.7,.2,1)}
.js .ilmesty.nakyy{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.js .ilmesty{opacity:1;transform:none;transition:none}}
.osio{padding:clamp(72px,11vw,140px) 0}.osio .w{max-width:1200px}
.osio h2{font-family:Fraunces,Georgia,serif;font-weight:400;font-variation-settings:"opsz" 144;font-size:clamp(2.1rem,6.4vw,4rem);line-height:1.04;letter-spacing:-.025em;margin:0;text-wrap:balance}
.osio .johdanto{font-size:1.08rem;line-height:1.6;color:var(--mute);max-width:30em;margin:18px 0 0}
.pienet{font-variant-caps:all-small-caps;letter-spacing:.09em;font-weight:700;font-size:1.02rem;color:var(--puolukka);margin:0 0 14px}
@media (prefers-color-scheme:dark){.pienet{color:var(--accent)}}
.linkki{color:var(--ink);font-weight:700;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:5px;text-decoration-color:var(--puolukka)}
.linkki:hover{color:var(--puolukka)}
/* Esimerkit: seinä ja vaakarulla */
.seinaosa{background:var(--seina);background-image:radial-gradient(120% 80% at 20% 0%,#ffffff55,transparent 60%),url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.3 0 0 0 0 0.25 0 0 0 0 0.2 0 0 0 .06 0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
.otsikkorivi{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:24px 40px}
.suodin{display:flex;gap:22px;margin-top:34px;flex-wrap:wrap}
.suodin button{background:none;border:0;padding:6px 0;font:600 1rem "Nunito Sans",sans-serif;color:var(--mute);cursor:pointer;border-bottom:1.5px solid transparent;min-height:40px}
.suodin button[aria-pressed="true"]{color:var(--ink);border-bottom-color:var(--puolukka)}
.selaa{display:none;gap:10px}
.selaa button{width:48px;height:48px;border-radius:50%;border:1px solid var(--hius);background:transparent;color:var(--ink);font-size:1.2rem;cursor:pointer}
.selaa button:hover{border-color:var(--ink)}
@media (min-width:900px){.selaa{display:flex}}
.rulla{display:flex;gap:clamp(28px,5vw,64px);overflow-x:auto;scroll-snap-type:x mandatory;scroll-padding-inline:max(18px,calc((100vw - 1200px)/2 + 18px));padding:44px max(18px,calc((100vw - 1200px)/2 + 18px)) 20px;scrollbar-width:none;overscroll-behavior-x:contain}
.rulla::-webkit-scrollbar{display:none}
.juliste{flex:0 0 min(74vw,330px);scroll-snap-align:start;text-decoration:none;color:inherit;display:flex;flex-direction:column}
.juliste[hidden]{display:none}
.juliste .seinakehys2{background:#1d1a18;padding:3.2%;box-shadow:0 1px 1px rgba(0,0,0,.08),0 8px 12px -6px rgba(40,25,15,.25),0 30px 50px -18px rgba(40,25,15,.45);transition:transform .5s cubic-bezier(.2,.7,.2,1)}
.seinakehys2.puu{background:linear-gradient(135deg,#d8b78e,#b78b5c 55%,#c9a174)}.seinakehys2.valk{background:#f6f3ee}
.seinakehys2 img{display:block;width:100%;height:auto;box-shadow:inset 0 0 0 1px #0001}
.juliste:hover .seinakehys2{transform:translateY(-4px)}
.juliste h3{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.35rem;margin:26px 0 4px;letter-spacing:-.01em}
.juliste p{margin:0 0 10px;color:var(--mute);font-size:.95rem;line-height:1.45}
.juliste .linkki{font-size:.92rem;margin-top:auto}
/* Vaiheet */
.vaiheet2{list-style:none;margin:56px 0 0;padding:0;display:grid;gap:44px;position:relative}
.vaiheet2::before{content:"";position:absolute;left:27px;top:8px;bottom:8px;width:1px;background:var(--hius)}
.vaiheet2 li{display:grid;grid-template-columns:56px 1fr;gap:22px;position:relative;align-content:start;align-items:start}
.numero{font-family:Fraunces,Georgia,serif;font-weight:300;font-variation-settings:"opsz" 144;font-size:3.4rem;line-height:1;height:1em;color:var(--puolukka);background:var(--bg);text-align:center;padding:4px 0;box-sizing:content-box}
@media (prefers-color-scheme:dark){.numero{color:var(--accent)}}
.vaiheet2 h3{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.5rem;margin:6px 0 6px}.vaiheet2 p{margin:0;color:var(--mute);max-width:24em}
@media (min-width:860px){
 .vaiheet2{grid-template-columns:repeat(3,1fr);gap:48px}
 .vaiheet2::before{left:0;right:0;top:44px;bottom:auto;width:auto;height:1px}
 .vaiheet2 li{grid-template-columns:1fr;gap:18px}.numero{font-size:5.2rem;text-align:left;padding:0 18px 0 0;justify-self:start}
}
/* Suunnittelijapaneelit */
.paneelit{display:grid;grid-template-columns:minmax(0,1fr)}
@media (min-width:860px){.paneelit{grid-template-columns:1fr 1fr}}
.paneeli{position:relative;isolation:isolate;overflow:hidden;aspect-ratio:4/5;color:#fff8ef;text-decoration:none;display:flex;align-items:flex-end;background:#d9d4cc}
.paneeli>img.tausta{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2;transition:transform 1.2s cubic-bezier(.2,.7,.2,1)}
.paneeli:hover>img.tausta{transform:scale(1.03)}
.paneeli::after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,transparent 45%,rgba(22,18,15,.25) 62%,rgba(22,18,15,.8) 100%)}
.paneeli figure{position:absolute;margin:0;transform:translateX(-50%);padding:1.6%;box-shadow:0 1px 2px rgba(0,0,0,.18),0 10px 18px -8px rgba(30,20,10,.4),0 26px 40px -16px rgba(30,20,10,.45)}
.paneeli figure img{display:block;width:100%;height:auto}
.paneeli .teksti-osa{padding:0 clamp(22px,4vw,48px) clamp(26px,4vw,44px);max-width:34em}
.paneeli h3{font-family:Fraunces,Georgia,serif;font-weight:400;font-variation-settings:"opsz" 144;font-size:clamp(2rem,5vw,3rem);line-height:1.05;margin:0 0 10px;letter-spacing:-.02em}
.paneeli p{margin:0 0 20px;color:#f3e9de;line-height:1.55}
.nappi.vaalea{background:#fff8ef;color:#2b2321;border-radius:99px;min-height:50px;padding:0 24px}
.paneeli:hover .nappi.vaalea{background:var(--hunaja)}
/* Hinnat */
.hinnasto{display:grid;gap:48px}
@media (min-width:900px){.hinnasto{grid-template-columns:.8fr 1.2fr;gap:80px;align-items:start}.hinnasto .otsikko{position:sticky;top:40px}}
.hintarivi{display:grid;grid-template-columns:76px minmax(0,1fr);gap:8px 22px;padding:30px 0;border-top:1px solid var(--hius)}
.hintarivi:last-child{border-bottom:1px solid var(--hius)}
.hintarivi .pikku{grid-row:span 2;align-self:start;background:var(--seina);padding:10px;display:flex;justify-content:center}
.hintarivi .pikku span{display:block;width:100%;box-shadow:0 6px 10px -6px rgba(40,25,15,.45)}
.hintarivi .pikku img{display:block;width:100%;height:auto}
.hintarivi .pikku .canvas{box-shadow:3px 3px 0 rgba(0,0,0,.18),0 6px 10px -6px rgba(40,25,15,.45)}
.hintarivi .pikku .kehyksessa{padding:7%;background:#2a2522}
.hintarivi h3{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.45rem;margin:0}
.hintarivi .kuvaus{margin:2px 0 0;color:var(--mute);font-size:.95rem}
.koot{grid-column:2;list-style:none;margin:10px 0 0;padding:0}
.koot li{display:flex;align-items:baseline;gap:10px;padding:7px 0;font-size:1.02rem}
.koot li::after{content:"";order:1;flex:1;border-bottom:1px dotted var(--hius);transform:translateY(-4px)}
.koot li b{order:2;font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.2rem}
.savyt{grid-column:2;display:flex;flex-wrap:wrap;gap:14px 18px;margin-top:14px;list-style:none;padding:0}
.savyt li{display:flex;flex-direction:column;align-items:center;gap:6px;font-size:.78rem;color:var(--mute);width:58px;text-align:center;line-height:1.2}
.savyt i{width:30px;height:30px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(0,0,0,.18),0 1px 2px rgba(0,0,0,.12)}
.hinta-huom{color:var(--mute);font-size:.95rem;margin:18px 0 0}
/* Lahjaideat */
.ideat .rulla{padding-top:36px}
.idea{flex:0 0 min(42vw,200px);scroll-snap-align:start;text-decoration:none;color:inherit}
.idea .alusta{background:var(--seina);aspect-ratio:1;display:flex;align-items:center;justify-content:center}
.idea .alusta span{width:46%;background:#fff;padding:3%;box-shadow:0 1px 1px rgba(0,0,0,.08),0 10px 16px -8px rgba(40,25,15,.45);transition:transform .5s cubic-bezier(.2,.7,.2,1)}
.idea:hover .alusta span{transform:translateY(-3px)}
.idea .alusta img{display:block;width:100%;height:auto}
.idea b{display:block;font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.12rem;margin-top:12px}
/* Luottamus */
.luottorivi{list-style:none;margin:0;padding:34px 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px 22px;border-top:1px solid var(--hius);border-bottom:1px solid var(--hius)}
@media (min-width:900px){.luottorivi{grid-template-columns:repeat(4,1fr)}}
.luottorivi li{display:flex;flex-direction:column;gap:10px;font-size:.95rem;line-height:1.4;color:var(--mute)}
.luottorivi svg{width:30px;height:30px;color:var(--ink)}
.luottorivi b{color:var(--ink);font-weight:700}
/* Loppu */
.loppu2{text-align:center}
.loppu2 h2{max-width:14em;margin:0 auto}
.loppu2 .napit{justify-content:center;margin-top:34px}
.nappi.tumma{background:var(--puolukka);color:#fff;border-radius:99px;min-height:54px;padding:0 28px;font-size:1.05rem}
.nappi.tumma:hover{background:#63231f}
"""

LUOTTO_IKONIT = {
    "paino": '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.25" aria-hidden="true"><path d="M8 12V4h16v8M8 22H5V12h22v10h-3"/><path d="M8 18h16v10H8z"/></svg>',
    "laatu": '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.25" aria-hidden="true"><rect x="7" y="4" width="18" height="24"/><rect x="10" y="7" width="12" height="15"/><path d="M12 18l3-4 2 2.5 1.5-1.5 2 3"/></svg>',
    "maksu": '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.25" aria-hidden="true"><rect x="7" y="14" width="18" height="13" rx="1.5"/><path d="M11 14V10a5 5 0 0 1 10 0v4M16 19v3"/></svg>',
    "suomi": '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.25" aria-hidden="true"><path d="M16 4c-4 5-9 7-9 14a9 9 0 0 0 18 0c0-7-5-9-9-14z"/><path d="M16 28V14M16 20l4-3M16 23l-4-3"/></svg>',
}

def etusivu():
    a = euro(alin_hinta())
    kuva = lambda nimi, alt, w, h: f'<img src="/kuvat/{nimi}.jpg" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
    julisteet = "".join(f'<a class="juliste ilmesty" data-luokat="{lk}" href="{l}"><div class="seinakehys2 {kh}">{kuva(f, t + ": esimerkkijuliste", w, h)}</div><h3>{esc(t)}</h3><p>{esc(k)}</p><span class="linkki">Muokkaa omaksi</span></a>'
                        for f, t, k, l, w, h, lk, kh in ESIMERKIT)
    ideat = "".join(f'<a class="idea" href="{l}"><div class="alusta"><span>{kuva(f, "", 1000, 1333)}</span></div><b>{esc(t)}</b></a>' for t, l, f in TILAISUUDET)
    t = CONFIG["tuotteet"]
    pikku = {"juliste": ("nimi-vauva", ""), "canvas": ("kartta-tampere", "canvas"), "kehys": ("nimi-perhe", "kehyksessa")}
    hinnat = ""
    for avain, x in t.items():
        kuvatiedosto, luokka = pikku.get(avain, ("nimi-perhe", ""))
        koot = "".join(f"<li><span>{kk.replace('x', ' × ')} cm</span><b>{euro(k['hinta'])}</b></li>" for kk, k in x["koot"].items())
        savyt = ('<ul class="savyt" aria-label="Kehysvärit">' + "".join(f'<li><i style="background:{v["css"]}"></i>{esc(v["nimi"])}</li>' for v in x["varit"].values()) + "</ul>") if "varit" in x else ""
        hinnat += f'<div class="hintarivi ilmesty"><div class="pikku"><span class="{luokka}">{kuva(kuvatiedosto, "", 1000, 1333)}</span></div><div><h3>{esc(x["nimi"])}</h3><p class="kuvaus">{esc(x["kuvaus"])}.</p></div><ul class="koot">{koot}</ul>{savyt}</div>'
    tiedote = "" if CONFIG["avoinna"] else '<div class="tiedote">Tilaukset avautuvat pian – ehdit hyvin jouluun. <a href="/tee/nimijuliste/">Suunnittele jo nyt</a></div>'
    runko = f"""<section class="sankari">
<img class="sankari-kuva" src="{unsplash(HERO_ID, 1280)}" srcset="{srcset(HERO_ID)}" sizes="100vw" alt="" fetchpriority="high" decoding="async">
<div class="sankari-sis"><div>
<p class="ylateksti">Personoidut julisteet ja taulut</p>
<h1>Lahja, jossa on <em>tarina.</em></h1>
<p class="ingressi">Nimet, tärkeät päivät ja rakkaat paikat kauniiksi julisteeksi. Suunnittelet itse ja näet lopputuloksen heti – me painamme sen juuri sinulle.</p>
<div class="napit"><a class="nappi iso" href="/tee/nimijuliste/">Suunnittele oma lahja</a><a class="nappi haamu" href="/tee/kartta/">Tee karttajuliste</a></div>
<ul class="pikaedut"><li>Alkaen {a}</li><li>Toimitus sisältyy hintaan</li><li>Painettu EU:ssa</li></ul></div>
<div class="mockup" aria-hidden="true"><figure class="kehys k1 puu"><img src="/kuvat/nimi-perhe.jpg" alt="" width="1000" height="1333" decoding="async"></figure><figure class="kehys k2"><img src="/kuvat/kartta-helsinki.jpg" alt="" width="1000" height="1400" decoding="async"></figure></div>
</div></section>

<section class="osio seinaosa" aria-labelledby="esim-otsikko"><div class="w"><div class="otsikkorivi"><div><p class="pienet">Esimerkkejä</p><h2 id="esim-otsikko" class="ilmesty">Valitse pohja,<br>tee siitä oma</h2>
<p class="johdanto">Jokainen esimerkki on tehty samalla suunnittelijalla, jota sinäkin käytät. Avaa se ja vaihda nimet, värit, fontti ja kuvio.</p></div>
<div class="selaa"><button type="button" data-suunta="-1" aria-label="Edelliset esimerkit">‹</button><button type="button" data-suunta="1" aria-label="Seuraavat esimerkit">›</button></div></div>
<div class="suodin" role="group" aria-label="Näytä esimerkit"><button type="button" data-suodin="kaikki" aria-pressed="true">Kaikki</button><button type="button" data-suodin="nimet" aria-pressed="false">Nimet</button><button type="button" data-suodin="kartat" aria-pressed="false">Kartat</button><button type="button" data-suodin="raamattu" aria-pressed="false">Raamattu</button></div></div>
<div class="rulla" id="esimerkit">{julisteet}</div></section>

<section class="osio" aria-labelledby="vaiheet-otsikko"><div class="w"><h2 id="vaiheet-otsikko" class="ilmesty">Näin lahja syntyy</h2>
<ol class="vaiheet2"><li class="ilmesty"><span class="numero">1</span><div><h3>Suunnittele</h3><p>Kirjoita nimet tai hae paikka. Valitse fontti, värit ja kuvio, ja katso esikatselusta, miltä juliste näyttää.</p></div></li>
<li class="ilmesty"><span class="numero">2</span><div><h3>Tilaa</h3><p>Valitse juliste, canvastaulu tai kehystetty juliste. Maksa verkkopankilla, mobiilimaksulla tai kortilla.</p></div></li>
<li class="ilmesty"><span class="numero">3</span><div><h3>Saat kotiin</h3><p>Painamme tuotteen juuri sinulle. Se tulee kotiin tai noutopisteeseen 8–14 arkipäivässä.</p></div></li></ol></div></section>

<section class="paneelit" aria-label="Suunnittelijat">
<a class="paneeli" href="/tee/nimijuliste/"><img class="tausta" src="{unsplash(SEINA_ID, 1280)}" srcset="{srcset(SEINA_ID, (640, 960, 1280, 1920))}" sizes="(min-width:860px) 50vw, 100vw" alt="" loading="lazy" decoding="async" style="object-position:50% 50%">
<figure class="puu" style="left:50%;top:7%;width:22%;background:linear-gradient(135deg,#d8b78e,#b78b5c 55%,#c9a174)">{kuva("nimi-haat", "Hääjuliste seinällä", 1000, 1333)}</figure>
<div class="teksti-osa"><h3>Nimijuliste</h3><p>Perheen, lapsen tai hääparin nimet. Yhdeksän asettelua, kymmenen fonttiparia ja yli 20 koristekuviota – myös Raamatunlause.</p><span class="nappi vaalea">Suunnittele nimijuliste</span></div></a>
<a class="paneeli" href="/tee/kartta/"><img class="tausta" src="{unsplash(KARTTA_SEINA_ID, 1280)}" srcset="{srcset(KARTTA_SEINA_ID, (640, 960, 1280, 1920))}" sizes="(min-width:860px) 50vw, 100vw" alt="" loading="lazy" decoding="async" style="object-position:42.5% 50%">
<figure style="left:42.5%;top:12%;width:27%;background:#1d1a18">{kuva("kartta-ylivieska", "Karttajuliste seinällä", 1000, 1400)}</figure>
<div class="teksti-osa"><h3>Karttajuliste</h3><p>Kotikaupunki, mökkiranta tai rakas paikka maailmalla. Sydän- ja ympyräkartat sekä valmiit Raamatun paikat.</p><span class="nappi vaalea">Suunnittele karttajuliste</span></div></a>
</section>

<section class="osio" aria-labelledby="hinnat-otsikko"><div class="w hinnasto"><div class="otsikko"><p class="pienet">Hinnat</p><h2 id="hinnat-otsikko" class="ilmesty">Paperille, kankaalle tai kehykseen</h2>
<p class="johdanto">Hinnat sisältävät arvonlisäveron ja toimituksen Suomeen. Jokainen tuote painetaan tilauksesta.</p></div>
<div>{hinnat}</div></div></section>

<section class="osio ideat seinaosa" aria-labelledby="ideat-otsikko"><div class="w"><h2 id="ideat-otsikko" class="ilmesty">Jokaiseen juhlaan ja muistoon</h2></div>
<div class="rulla">{ideat}</div>
<div class="w"><ul class="luottorivi" style="margin-top:72px">
<li>{LUOTTO_IKONIT["paino"]}<span><b>Painettu tilauksesta EU:ssa.</b> Ei varastoa eikä hukkaa.</span></li>
<li>{LUOTTO_IKONIT["laatu"]}<span><b>Laadukkaat materiaalit.</b> 200 g/m² paperi, canvas ja pleksilasi.</span></li>
<li>{LUOTTO_IKONIT["maksu"]}<span><b>Turvallinen maksu.</b> Visma Pay: pankki, mobiili tai kortti.</span></li>
<li>{LUOTTO_IKONIT["suomi"]}<span><b>Suomalainen yritys.</b> {YRITYS}, Ylivieska.</span></li></ul></div></section>

<section class="osio loppu2"><div class="w"><h2 class="ilmesty">Tee lahja, joka jää seinälle</h2>
<p class="johdanto" style="margin-inline:auto">{'Tilaukset avautuvat pian. Suunnitelmasi säilyy, joten voit aloittaa jo nyt.' if not CONFIG['avoinna'] else 'Toimitus 8–14 arkipäivässä.'}</p>
<div class="napit"><a class="nappi tumma" href="/tee/nimijuliste/">Suunnittele nimijuliste</a><a class="nappi tumma" style="background:transparent;color:var(--ink);border:1px solid var(--ink)" href="/tee/kartta/">Tee karttajuliste</a></div></div></section>
<script>
document.documentElement.classList.add("js");
(function(){{var r=document.getElementById("esimerkit");
document.querySelectorAll(".suodin button").forEach(function(b){{b.addEventListener("click",function(){{var s=b.dataset.suodin;
document.querySelectorAll(".suodin button").forEach(function(x){{x.setAttribute("aria-pressed",String(x===b))}});
r.querySelectorAll(".juliste").forEach(function(j){{j.hidden=!(s==="kaikki"||(" "+j.dataset.luokat+" ").indexOf(" "+s+" ")>=0)}});r.scrollTo({{left:0,behavior:"smooth"}})}})}});
document.querySelectorAll(".selaa button").forEach(function(b){{b.addEventListener("click",function(){{r.scrollBy({{left:+b.dataset.suunta*r.clientWidth*.8,behavior:"smooth"}})}})}});
var el=document.querySelectorAll(".ilmesty");if(!("IntersectionObserver" in window)){{el.forEach(function(e){{e.classList.add("nakyy")}});return}}
var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add("nakyy");io.unobserve(e.target)}}}})}},{{rootMargin:"0px 0px -8% 0px",threshold:.08}});
el.forEach(function(e){{io.observe(e)}})}})();
</script>"""
    paa = f'<script>document.documentElement.classList.add("js")</script><link rel="preload" as="image" href="{unsplash(HERO_ID, 1280)}" imagesrcset="{srcset(HERO_ID)}" imagesizes="100vw" fetchpriority="high"><style>{ETUSIVU_CSS}</style>'
    return sivu("Omalahja – personoidut julisteet ja taulut suomeksi", "Personoidut nimijulisteet ja karttajulisteet suomeksi. Valitse fontti, värit ja kuviot – painetaan tilauksesta ja toimitetaan kotiin.", runko, "/",
                lisapaa=paa, ylapalkki=tiedote, header_luokka="paalla")

def suunnittelija(malli):
    nimi = "Nimijuliste" if malli == "nimi" else "Karttajuliste"
    kuvaus = ("Kirjoita nimet ja valitse asettelu, fontti, värit ja koristekuvio. Esikatselu päivittyy heti." if malli == "nimi"
              else "Hae paikka tai valitse valmis kohde, rajaa kartta ja valitse väriteema. Esikatselu päivittyy heti.")
    if CONFIG["avoinna"]:
        maksu = '<button class="nappi" id="maksa" type="submit">Siirry maksamaan</button>'
    else:
        maksu = '<div class="ilmoitus" id="maksa">Tilaukset avautuvat pian. Voit jo suunnitella tuotteesi – suunnitelma säilyy tällä laitteella.</div>'
    runko = f"""<div class="tee">
<div class="esikatselu" id="esi" aria-label="Esikatselu"><div class="taulu" id="taulu"><canvas id="cv" role="img" aria-label="{nimi}n esikatselu"></canvas></div><div id="lataus" hidden></div><button type="button" class="nappi pieni" id="suurenna">Suurenna</button></div>
<div><div class="otsake"><h1>{nimi}</h1><p>{kuvaus}</p></div><div class="ohjaimet" id="ohj"></div></div></div>
<section class="kassa w" id="kassa" hidden><h2>Tilaus</h2><p id="yht" class="mute"></p>
<form id="tilauslomake">
<label class="kentta"><span>Nimi</span><input name="nimi" required maxlength="80" autocomplete="name"></label>
<label class="kentta"><span>Sähköposti</span><input name="email" type="email" required maxlength="120" autocomplete="email"></label>
<label class="kentta"><span>Puhelin</span><input name="puhelin" type="tel" required maxlength="20" autocomplete="tel"></label>
<label class="kentta"><span>Katuosoite</span><input name="osoite" required maxlength="100" autocomplete="street-address"></label>
<div class="rinnakkain" style="grid-template-columns:minmax(0,1fr) minmax(0,2fr)"><label class="kentta"><span>Postinumero</span><input name="postinro" required inputmode="numeric" pattern="[0-9]{{5}}" maxlength="5" autocomplete="postal-code"></label>
<label class="kentta"><span>Postitoimipaikka</span><input name="kaupunki" required maxlength="60" autocomplete="address-level2"></label></div>
<p class="vihje">Toimitamme toistaiseksi vain Suomeen. Toimitusaika 8–14 arkipäivää.</p>
<label class="rasti"><input type="checkbox" name="hyvaksy" required> <span>Hyväksyn <a href="/toimitusehdot/" target="_blank">toimitusehdot</a> ja ymmärrän, että personoidulla tuotteella ei ole peruuttamisoikeutta.</span></label>
{maksu}<p class="viesti" id="lomakeviesti" aria-live="polite"></p></form></section>
<div class="alapalkki"><div><b id="hinta"></b><span id="tuotenimi"></span></div><button type="button" class="nappi" id="jatka">Jatka tilaamaan</button></div>
<script>window.OL_CONFIG={json.dumps(julkinen_config(), ensure_ascii=False)};</script>
<script src="/kuviot.js?v={VERSIO}"></script>{'<script src="/kartta.js?v=' + VERSIO + '"></script>' if malli == "kartta" else ''}<script src="/tee.js?v={VERSIO}"></script>"""
    otsikko = f"{nimi} – suunnittele oma | Omalahja"
    seo = ("Tee oma nimijuliste: nimet, päivämäärä, fontti, värit ja koristekuviot. Juliste, canvastaulu tai kehystetty juliste." if malli == "nimi"
           else "Tee oma karttajuliste kotikaupungista tai mistä tahansa paikasta, myös Raamatun paikoista. Juliste, canvas tai kehystetty.")
    lisapaa = f'<link rel="stylesheet" href="{FONTIT_URL}"><style>{TEE_CSS}</style>'
    return sivu(otsikko, seo, runko, "/tee/nimijuliste/" if malli == "nimi" else "/tee/kartta/", malli, lisapaa)

def kiitos():
    runko = """<div class="w teksti"><h1>Kiitos tilauksestasi!</h1><div id="tila"><p class="mute">Tarkistetaan tilausta…</p></div>
<p>Lähetämme tilausvahvistuksen sähköpostiisi. Jos sinulla on kysyttävää, vastaa vahvistusviestiin tai kirjoita osoitteeseen <a href="mailto:info@omalahja.fi">info@omalahja.fi</a>.</p></div>
<script>(async()=>{const t=new URLSearchParams(location.search).get("t")||"",el=document.getElementById("tila");
const e=(s)=>String(s).replace(/[&<>"]/g,(c)=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
for(let i=0;i<6;i++){try{const r=await fetch("/api/tilaus?t="+encodeURIComponent(t)).then(r=>r.json());
if(r.nro){el.innerHTML=`<p><b>Tilausnumero ${e(r.nro)}</b><br>${e(r.tuote)}<br>Yhteensä ${e(r.summa)}</p><p>Tilauksesi on maksettu ja siirtyy painoon. Arvioitu toimitus 8–14 arkipäivää.</p>`;return}
if(r.virhe&&r.tila!=="odottaa"){el.innerHTML=`<p>${e(r.virhe)}</p>`;return}}catch{}await new Promise(r=>setTimeout(r,2500))}
el.innerHTML="<p>Maksun vahvistus voi kestää hetken. Saat vahvistuksen sähköpostiisi.</p>"})();</script>"""
    return sivu("Kiitos tilauksestasi – Omalahja", "Tilausvahvistus.", runko, "/kiitos/")

def yhteystiedot():
    runko = f"""<div class="w teksti"><h1>Yhteystiedot</h1>
<p><b>Omalahja</b> on {YRITYS}:n verkkokauppa.</p>
<p>{YRITYS}<br>Y-tunnus {YTUNNUS}<br>{OSOITE}</p>
<p>Sähköposti: <a href="mailto:{EMAIL}">{EMAIL}</a><br>Puhelin: {PUH}</p>
<p class="mute">Vastaamme viesteihin yleensä yhden arkipäivän kuluessa.</p></div>"""
    return sivu("Yhteystiedot – Omalahja", "Omalahjan yhteystiedot.", runko, "/yhteystiedot/")

def toimitusehdot():
    runko = f"""<div class="w teksti"><h1>Toimitus- ja maksuehdot</h1><p class="mute">Voimassa {PV} alkaen.</p>
<h2>Myyjä</h2><p>{YRITYS} (Y-tunnus {YTUNNUS}), {OSOITE}. Sähköposti {EMAIL}, puhelin {PUH}. Verkkokaupan nimi on Omalahja.</p>
<h2>Tuotteet ja hinnat</h2><p>Myymme personoituja painotuotteita: julisteita, canvastauluja ja kehystettyjä julisteita (esimerkiksi nimijulisteet ja karttajulisteet). Tuotteet valmistetaan asiakkaan verkkokaupassa tekemän suunnitelman mukaan. Hinnat ovat euroja ja sisältävät arvonlisäveron 25,5 % sekä toimituksen Suomeen.</p>
{hintataulukko()}
<p>Tuotteiden värit voivat poiketa hieman näytöllä näkyvistä väreistä näyttöjen eroista johtuen. Karttajulisteiden karttatiedot ovat OpenStreetMapin avointa dataa (© OpenStreetMap contributors), ja ne voivat sisältää puutteita.</p>
<h2>Tilaus</h2><p>Tilaus syntyy, kun maksu on hyväksytty. Saat tilausvahvistuksen sähköpostiisi. Tarkista personointitiedot (nimet, päivämäärät, tekstit ja kartan rajaus) huolellisesti esikatselusta ennen tilaamista, sillä tuote valmistetaan juuri niiden mukaan.</p>
<h2>Toimitus</h2><p>Tuotteet valmistetaan tilauksesta yhteistyökumppanimme Gelaton painossa EU:ssa ja toimitetaan kotiin tai lähimpään noutopisteeseen. Toimitamme toistaiseksi vain Suomeen. Arvioitu toimitusaika on 8–14 arkipäivää tilauksesta. Ilmoitamme, jos toimitus viivästyy.</p>
<h2>Peruuttamisoikeus</h2><p>Kuluttajansuojalain 6 luvun 16 §:n mukaan peruuttamisoikeutta ei ole tavaroihin, jotka valmistetaan tai muokataan selvästi kuluttajan yksilöllisten vaatimusten mukaisesti. Kaikki Omalahjan tuotteet ovat personoituja, joten niillä ei ole 14 päivän peruuttamisoikeutta. Voit kuitenkin perua tilauksen maksutta ottamalla yhteyttä mahdollisimman pian, ennen kuin tuote on siirtynyt valmistukseen.</p>
<h2>Virheet ja reklamaatiot</h2><p>Jos tuote on vaurioitunut, painovirheellinen tai muuten virheellinen, ilmoita siitä 14 päivän kuluessa vastaanottamisesta osoitteeseen {EMAIL} ja liitä mukaan kuva. Toimitamme uuden tuotteen tai palautamme rahat. Virheeksi ei katsota asiakkaan itse kirjoittamia kirjoitusvirheitä. Kuluttaja voi viedä riita-asian kuluttajariitalautakunnan käsiteltäväksi (kuluttajariita.fi); ennen sitä kannattaa olla yhteydessä kuluttajaneuvontaan.</p>
<h2>Maksaminen ja maksupalveluntarjoaja</h2><p>Maksunvälityspalvelun toteuttajana ja maksupalveluntarjoajana toimii Visma Payments Oy (Y-tunnus 2486559-4), joka on rekisteröity Finanssivalvonnan ylläpitämään maksulaitosrekisteriin. Voit maksaa verkkopankkitunnuksilla, mobiilimaksulla tai maksukortilla. Visma Payments Oy:n yhteystiedot: Laserkatu 6, 53850 Lappeenranta, helpdesk@vismapay.com.</p>
<h2>Tekijänoikeudet</h2><p>Asiakas vastaa siitä, että hänellä on oikeus käyttää tilaukseen kirjoittamiaan tekstejä. Emme valmista tuotteita, joiden sisältö on lainvastaista tai loukkaavaa.</p></div>"""
    return sivu("Toimitus- ja maksuehdot – Omalahja", "Omalahjan toimitus- ja maksuehdot.", runko, "/toimitusehdot/")

def tietosuoja():
    runko = f"""<div class="w teksti"><h1>Tietosuojaseloste</h1><p class="mute">EU:n yleinen tietosuoja-asetus (2016/679). Päivitetty {PV}.</p>
<h2>Rekisterinpitäjä</h2><p>{YRITYS} (Y-tunnus {YTUNNUS}), {OSOITE}. Yhteyshenkilö: Miika Koskela, {EMAIL}.</p>
<h2>Mitä tietoja käsittelemme</h2><p>Tilauksen yhteydessä: nimi, toimitusosoite, sähköposti, puhelinnumero, tilauksen sisältö ja personointitiedot (tekstit ja painotiedosto) sekä maksun tila. Emme näe tai tallenna maksukorttitietoja.</p>
<h2>Käsittelyn tarkoitus ja peruste</h2><p>Tilausten toimittaminen ja asiakaspalvelu (sopimus), kirjanpito (lakisääteinen velvoite). Jos tilaat uutiskirjeen, lähetämme sitä suostumuksesi perusteella.</p>
<h2>Tietojen vastaanottajat</h2><p>Tuotteen valmistaja ja toimittaja Gelato (toimitusosoite, yhteystiedot ja painotiedosto), maksunvälittäjä Visma Payments Oy, sähköpostipalvelu Brevo sekä palvelinpalvelu Cloudflare. Tietoja ei myydä eteenpäin.</p>
<h2>Karttahaku</h2><p>Karttajulisteen paikkahaku ja karttatiedot haetaan selaimestasi suoraan OpenStreetMapin palveluista (Nominatim ja Overpass API). Niille välittyy hakusana ja IP-osoitteesi. Hakuja ei tallenneta Omalahjaan.</p>
<h2>Säilytysaika</h2><p>Tilaustiedot säilytetään kirjanpitolain vaatiman ajan (6 vuotta tilikauden päättymisestä). Painotiedostot poistetaan, kun tilaus on toimitettu ja reklamaatioaika päättynyt. Keskeneräinen suunnitelma tallentuu vain omaan selaimeesi.</p>
<h2>Evästeet</h2><p>Sivusto käyttää vain toiminnan kannalta välttämättömiä tietoja. Jos otamme käyttöön mainonnan tai analytiikan evästeitä, pyydämme niihin erikseen suostumuksen.</p>
<h2>Oikeutesi</h2><p>Voit pyytää pääsyä tietoihisi, niiden oikaisua tai poistamista sekä vastustaa käsittelyä. Ota yhteyttä {EMAIL}. Voit myös tehdä valituksen tietosuojavaltuutetulle (tietosuoja.fi).</p></div>"""
    return sivu("Tietosuojaseloste – Omalahja", "Omalahjan tietosuojaseloste.", runko, "/tietosuoja/")

SIVUT = [("", etusivu), ("tee/nimijuliste", lambda: suunnittelija("nimi")), ("tee/kartta", lambda: suunnittelija("kartta")), ("kiitos", kiitos),
         ("yhteystiedot", yhteystiedot), ("toimitusehdot", toimitusehdot), ("tietosuoja", tietosuoja)]

def rakenna(root):
    r = pathlib.Path(root) / "omalahja"
    for polku, f in SIVUT:
        (r / polku).mkdir(parents=True, exist_ok=True); (r / polku / "index.html").write_text(f(), encoding="utf-8")
    (r / "tee" / "index.html").write_text('<!doctype html><meta http-equiv="refresh" content="0;url=/tee/nimijuliste/"><link rel="canonical" href="https://omalahja.fi/tee/nimijuliste/">', encoding="utf-8")
    for js in ["tee.js", "kuviot.js", "kartta.js"]:
        shutil.copy(HAKEMISTO / js, r / js)
    if (HAKEMISTO / "kuvat").is_dir():
        shutil.copytree(HAKEMISTO / "kuvat", r / "kuvat", dirs_exist_ok=True)
    (r / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /kiitos/\nSitemap: https://omalahja.fi/sitemap.xml\n", encoding="utf-8")
    (r / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>https://omalahja.fi{u}</loc></url>" for u in ["/", "/tee/nimijuliste/", "/tee/kartta/", "/toimitusehdot/", "/tietosuoja/", "/yhteystiedot/"]) + "</urlset>", encoding="utf-8")
