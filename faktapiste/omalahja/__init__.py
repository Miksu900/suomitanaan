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
header.yla{padding:14px 0;border-bottom:1px solid var(--line)}header.yla .w{display:flex;justify-content:space-between;align-items:center;gap:12px}
header.yla nav{display:flex;gap:16px;font-weight:600;font-size:.95rem}header.yla nav a{text-decoration:none}
.logo{font-family:Fraunces,Georgia,serif;font-weight:650;font-size:1.5rem;color:var(--accent);text-decoration:none}
h1,h2,h3{font-family:Fraunces,Georgia,serif;font-weight:650;line-height:1.15;margin:0 0 .5em}h1{font-size:clamp(2.1rem,6vw,3.6rem)}h2{font-size:1.6rem;margin-top:1.6em}
a{color:var(--accent)}.mute{color:var(--mute)}
.hero{padding:48px 0 28px}.hero p{font-size:1.15rem;max-width:40em}
.badge{display:inline-block;background:var(--accent2);color:#2b1a08;font-weight:700;border-radius:99px;padding:4px 14px;font-size:.85rem;margin-bottom:16px}
.kortit{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));margin:24px 0 48px}
.kortti{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;display:flex;flex-direction:column;gap:8px;text-decoration:none;color:inherit}
a.kortti:hover{border-color:var(--accent)}.kortti h3{font-size:1.3rem;margin:0}.kortti p{margin:0;color:var(--mute)}.hinta{font-family:Fraunces,serif;font-size:1.3rem;color:var(--ink)}
.kortti .nappi{align-self:flex-start;margin-top:auto}
.nappi{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;border-radius:12px;border:0;background:var(--accent);color:#fff;font:700 1rem "Nunito Sans",system-ui,sans-serif;text-decoration:none;cursor:pointer}
@media (prefers-color-scheme:dark){.nappi{color:#1d1715}}
.nappi.pieni{min-height:44px;min-width:44px;padding:0 12px;background:var(--card);color:var(--ink);border:1px solid var(--line)}
.nappi:disabled{opacity:.55;cursor:wait}
.teksti{max-width:760px;padding:36px 0 64px}
table.hinnat{border-collapse:collapse;width:100%;font-size:.95rem}table.hinnat td,table.hinnat th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left}
footer{border-top:1px solid var(--line);padding:28px 0 40px;font-size:.92rem;color:var(--mute)}footer a{color:var(--mute)}
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

def sivu(otsikko, kuvaus, runko, polku, malli=None, lisapaa=""):
    keho = f' data-malli="{malli}"' if malli else ""
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}"><link rel="canonical" href="https://omalahja.fi{polku}">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}"><meta property="og:url" content="https://omalahja.fi{polku}"><meta property="og:locale" content="fi_FI">
<meta name="theme-color" content="#7a2e2e"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%237a2e2e'/%3E%3Cpath d='M8 14h16v12H8zM6 10h20v4H6zM16 10v16' stroke='%23fff6ec' stroke-width='2' fill='none'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,650&family=Nunito+Sans:wght@400;600;700&display=swap">
{lisapaa}<style>{PERUS_CSS}</style></head><body{keho}>
<header class="yla"><div class="w"><a class="logo" href="/">Omalahja</a><nav><a href="/tee/nimijuliste/">Nimijuliste</a><a href="/tee/kartta/">Karttajuliste</a></nav></div></header>
<main>{runko}</main>
<footer><div class="w"><p><b>Omalahja</b> · {YRITYS} (Y-tunnus {YTUNNUS}) · {OSOITE} · <a href="mailto:{EMAIL}">{EMAIL}</a> · puh. {PUH}</p>
<p><a href="/toimitusehdot/">Toimitus- ja maksuehdot</a> · <a href="/tietosuoja/">Tietosuojaseloste</a> · <a href="/yhteystiedot/">Yhteystiedot</a></p></div></footer>
</body></html>"""

def alin_hinta():
    return min(k["hinta"] for t in CONFIG["tuotteet"].values() for k in t["koot"].values())

def hintataulukko():
    rivit = "".join(f"<tr><td>{esc(t['nimi'])}</td><td>{kk.replace('x', ' × ')} cm</td><td>{euro(k['hinta'])}</td></tr>" for t in CONFIG["tuotteet"].values() for kk, k in t["koot"].items())
    return f'<table class="hinnat"><thead><tr><th>Tuote</th><th>Koko</th><th>Hinta</th></tr></thead><tbody>{rivit}</tbody></table>'

def etusivu():
    a = euro(alin_hinta())
    kortit = f"""<a class="kortti" href="/tee/nimijuliste/"><h3>Nimijuliste</h3><p>Perheen, lapsen tai hääparin nimet kauniina julisteena. Kymmenen fonttiparia, kaksitoista väripalettia, yhdeksän asettelua ja yli 20 koristekuviota – myös Raamatunlause.</p><div class="hinta">alk. {a}</div><span class="nappi">Suunnittele</span></a>
<a class="kortti" href="/tee/kartta/"><h3>Karttajuliste</h3><p>Kotikaupunki, mökkiranta tai rakas paikka maailmalla kartaksi nimellä ja koordinaateilla. Mukana myös Raamatun paikat, kuten Betlehem ja Nasaret.</p><div class="hinta">alk. {a}</div><span class="nappi">Suunnittele</span></a>"""
    tyypit = "".join(f'<div class="kortti"><h3>{esc(t["nimi"])}</h3><p>{esc(t["kuvaus"])}.</p><div class="hinta">{" · ".join(kk.replace("x", "×") + " " + euro(k["hinta"]) for kk, k in t["koot"].items())}</div></div>' for t in CONFIG["tuotteet"].values())
    tila = '<p class="mute">Suunnittelija on jo käytössä. Tilaukset avautuvat aivan pian – ehdit hyvin jouluun.</p>' if not CONFIG["avoinna"] else '<p class="mute">Toimitus 8–14 arkipäivässä kotiin tai noutopisteeseen.</p>'
    runko = f"""<section class="hero"><div class="w">{'' if CONFIG['avoinna'] else '<span class="badge">Tilaukset avautuvat pian</span>'}
<h1>Lahja, jossa on nimi.</h1>
<p>Omalahja tekee personoituja julisteita ja tauluja suomeksi: nimet, päivämäärät, kotikaupungit ja omat tekstit. Näet lopputuloksen heti, ja jokainen tuote painetaan tilauksesta juuri sinulle.</p>{tila}</div></section>
<section><div class="w"><h2>Suunnittele oma</h2><div class="kortit">{kortit}</div>
<h2>Tuotteet ja hinnat</h2><p class="mute">Hinnat sisältävät arvonlisäveron ja toimituksen Suomeen.</p><div class="kortit">{tyypit}</div></div></section>"""
    return sivu("Omalahja – personoidut julisteet ja taulut suomeksi", "Personoidut nimijulisteet ja karttajulisteet suomeksi. Valitse fontti, värit ja kuviot – painetaan tilauksesta ja toimitetaan kotiin.", runko, "/")

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
    (r / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /kiitos/\nSitemap: https://omalahja.fi/sitemap.xml\n", encoding="utf-8")
    (r / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>https://omalahja.fi{u}</loc></url>" for u in ["/", "/tee/nimijuliste/", "/tee/kartta/", "/toimitusehdot/", "/tietosuoja/", "/yhteystiedot/"]) + "</urlset>", encoding="utf-8")
