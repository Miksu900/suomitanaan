"""Taksi Koskela (taxikoskela.fi) – paikallinen taksisivusto Ylivieska–Alavieska–Kalajoki-akselille.
Rakentaa staattiset sivut kansioon taxikoskela/public: python3 taxikoskela/rakenna.py
Haltija: Koskelan Autopalvelu Oy (Y-tunnus 3312391-2). Ylläpito: Netvo.
"""
import json, pathlib, html, datetime

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "public"
SITE = "https://taxikoskela.fi"

# ---- Perustiedot (tarkista ennen julkaisua) ----
NIMI = "Taksi Koskela"
YRITYS = "Koskelan Autopalvelu Oy"
YTUNNUS = "3312391-2"
# Tilausnumerot etusivulla (yökyydit): kuljettajat. Lisää veli tähän listaan: ("Nimi", "04x xxx xxxx", "+3584xxxxxxxx")
KULJETTAJAT = [("Markus", "040 663 9916", "+358406639916"), ("Miika", "044 777 7149", "+358447777149")]
PUH, PUH_TEL = KULJETTAJAT[0][1], KULJETTAJAT[0][2]  # päänumero (soittopainikkeet, Google-tiedot)
# Omistaja: vain Yhteystiedot-sivulla (ei etusivulla, ettei yökyytejä soiteta hänelle)
OMISTAJA = ("Eero Koskela", "040 632 7786", "+358406327786")
SPOSTI = ""  # jätetään pois, kunnes vahvistettu

esc = html.escape

KAUPUNGIT = {
    "ylivieska": {
        "nimi": "Ylivieska", "ines": "Ylivieskassa", "lta": "Ylivieskasta",
        "geo": (64.0833, 24.5333),
        "otsikko": "Taksi Ylivieska – tilaa taksi Ylivieskassa",
        "kuvaus": f"Taksi Ylivieskassa: kyydit asemalle, sairaalaan, kauppaan ja Kalajoelle. Tilaa {NIMI}: {PUH}.",
        "ingressi": "Paikallinen taksi Ylivieskassa. Kuljetamme rautatieasemalle, sairaalaan ja terveyskeskukseen, kauppaan, töihin ja kotiin – ja tarvittaessa Kalajoelle tai muualle Pohjois-Pohjanmaalle.",
        "paikat": ["Ylivieskan rautatieasema", "Oulaisten ja Ylivieskan sairaala-alue", "Ylivieskan keskusta ja kauppakeskukset", "Raudaskylä", "Niemelä", "Kantokylä"],
        "teksti": [
            "Ylivieska on Pohjois-Pohjanmaan risteysasema: juna pysähtyy täällä matkalla Ouluun, Kokkolaan ja Helsinkiin. Tilaa taksi valmiiksi junan saapumiseen, niin auto odottaa asemalla.",
            "Ajamme Ylivieskasta myös pidempiä matkoja, kuten Kalajoelle, Alavieskaan, Sieviin, Nivalaan ja Oulaisiin. Kerro matkasi puhelimessa, niin sovimme noudon.",
        ],
    },
    "kalajoki": {
        "nimi": "Kalajoki", "ines": "Kalajoella", "lta": "Kalajoelta",
        "geo": (64.2597, 23.9486),
        "otsikko": "Taksi Kalajoki – taksi Kalajoelle ja Hiekkasärkille",
        "kuvaus": f"Taksi Kalajoella: Hiekkasärkät, keskusta, Himanka ja Rahja. Kyydit Ylivieskan asemalle. Tilaa {NIMI}: {PUH}.",
        "ingressi": "Taksi Kalajoella ja Hiekkasärkillä. Kuljetamme matkailijat, mökkiläiset ja paikalliset – ja vien sinut Ylivieskan rautatieasemalle ajoissa.",
        "paikat": ["Kalajoen Hiekkasärkät", "Kalajoen keskusta", "Himanka", "Rahja", "Rautio", "Pohjankylä"],
        "teksti": [
            "Kalajoelle saavutaan usein junalla Ylivieskan asemalle. Tilaa taksi suoraan junalta Hiekkasärkille, hotellille tai mökille – matka sujuu ilman vaihtoja.",
            "Ajamme Kalajoen keskustan, Hiekkasärkkien, Himangan ja Raution alueella sekä Kalajoelta Ylivieskaan ja Alavieskaan.",
        ],
    },
    "alavieska": {
        "nimi": "Alavieska", "ines": "Alavieskassa", "lta": "Alavieskasta",
        "geo": (64.1667, 24.3000),
        "otsikko": "Taksi Alavieska – kyydit Ylivieskaan ja Kalajoelle",
        "kuvaus": f"Taksi Alavieskassa: kyydit Ylivieskan asemalle, terveyspalveluihin ja Kalajoelle. Tilaa {NIMI}: {PUH}.",
        "ingressi": "Alavieska on Ylivieskan ja Kalajoen puolivälissä. Kuljetamme Alavieskasta Ylivieskan asemalle, terveyspalveluihin, kauppaan ja Kalajoelle.",
        "paikat": ["Alavieskan keskusta", "Taluskylä", "Kähtävä", "Valtatie 27 Ylivieska–Kalajoki"],
        "teksti": [
            "Alavieskasta on lyhyt matka sekä Ylivieskaan että Kalajoelle. Taksi tuo sinut kotiovelta perille – myös silloin, kun linja-autoa ei kulje.",
        ],
    },
}

PALVELUT = [
    ("Asemakyydit", "Ylivieskan rautatieasemalle ja asemalta kotiin, mökille tai Hiekkasärkille. Tilaa valmiiksi junan aikataulun mukaan."),
    ("Paikalliset kyydit", "Kauppaan, töihin, lääkäriin ja kotiin Ylivieskassa, Alavieskassa ja Kalajoella."),
    ("Hiekkasärkät ja mökit", "Matkailijat ja mökkiläiset Kalajoen Hiekkasärkille, hotelleille ja mökkikylille."),
    ("Ennakkotilaukset", "Varaa kyyti etukäteen aikaiseen aamuun, iltaan tai viikonlopulle."),
    ("Pidemmät matkat", "Kyydit naapurikuntiin ja sopimuksen mukaan pidemmillekin matkoille."),
    ("Yritykset", "Kyydit yritysten asiakkaille ja työntekijöille. Kysy laskutusmahdollisuutta."),
]

UKK = [
    ("Miten tilaan taksin?", f"Soita numeroon {PUH}. Kerro noutopaikka, kellonaika ja määränpää."),
    ("Ajatteko Ylivieskasta Kalajoelle?", "Kyllä. Ajamme koko Ylivieska–Alavieska–Kalajoki-akselilla, myös Hiekkasärkille, Himankaan ja Rautioon."),
    ("Voiko taksin tilata junalle Ylivieskan asemalle?", "Voi. Kerro junan saapumisaika, niin taksi on asemalla vastassa."),
    ("Voiko kyydin varata etukäteen?", "Voi. Ennakkotilaus kannattaa erityisesti aikaisille aamuille ja viikonlopuille."),
]

CSS = """:root{--bg:#0f1115;--bg2:#171a21;--card:#1d212a;--line:#2a2f3a;--txt:#f2f3f5;--mut:#a9afba;--y:#ffc400;--y2:#ffdb4d}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--txt);font:17px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--y)}img{max-width:100%}.w{width:min(1120px,100% - 32px);margin:0 auto}
header{position:sticky;top:0;z-index:20;background:rgba(15,17,21,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;gap:14px;height:68px}.logo{display:flex;align-items:center;gap:10px;color:var(--txt);text-decoration:none;font-weight:800;font-size:1.25rem;letter-spacing:.01em}
.logo i{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:9px;background:var(--y);color:#111;font-style:normal;font-size:.8rem;font-weight:900;letter-spacing:.05em}
nav.m{display:flex;gap:18px;margin-left:auto}nav.m a{color:var(--mut);text-decoration:none;font-weight:600;font-size:.95rem}nav.m a:hover{color:var(--txt)}
.call{display:inline-flex;align-items:center;gap:8px;background:var(--y);color:#111;text-decoration:none;font-weight:800;padding:11px 18px;border-radius:999px;white-space:nowrap;box-shadow:0 6px 24px rgba(255,196,0,.25)}
.call:hover{background:var(--y2)}.call svg{width:18px;height:18px}
@media(max-width:820px){nav.m{display:none}.bar .call{margin-left:auto}}
.hero{position:relative;overflow:hidden;padding:clamp(56px,9vw,110px) 0 clamp(40px,7vw,80px);background:radial-gradient(1200px 500px at 80% -10%,rgba(255,196,0,.16),transparent 60%),linear-gradient(180deg,#12151b,#0f1115)}
.hero .g{display:grid;grid-template-columns:1.1fr .9fr;gap:40px;align-items:center}@media(max-width:900px){.hero .g{grid-template-columns:1fr}}
.kick{display:inline-flex;gap:8px;align-items:center;font-weight:700;font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--y);margin-bottom:14px}
.kick b{width:8px;height:8px;border-radius:50%;background:#2ecc71;box-shadow:0 0 0 4px rgba(46,204,113,.18)}
h1{font-size:clamp(2.4rem,6vw,4.4rem);line-height:1.03;margin:0 0 18px;letter-spacing:-.02em;text-wrap:balance}h1 em{font-style:normal;color:var(--y)}
.lead{font-size:clamp(1.05rem,2vw,1.25rem);color:var(--mut);max-width:40ch;margin:0 0 28px}
.cta{display:flex;flex-wrap:wrap;gap:12px;align-items:center}.big{font-size:1.25rem;padding:16px 26px}
.ghost{color:var(--txt);text-decoration:none;font-weight:700;padding:15px 20px;border:1px solid var(--line);border-radius:999px}.ghost:hover{border-color:var(--mut)}
.drv{margin:18px 0 0;color:var(--mut);font-size:1.15rem;line-height:1.9}.drv a{color:var(--txt);font-weight:700;text-decoration:none;white-space:nowrap}.drv b{color:var(--y)}
.form{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:clamp(20px,4vw,34px);max-width:760px}
.form .two{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:620px){.form .two{grid-template-columns:1fr}}
.form label{display:block;font-weight:700;margin:0 0 6px;font-size:.95rem}.form .f{margin-bottom:14px}
.form input,.form textarea,.form select{width:100%;padding:14px 15px;border-radius:12px;border:1px solid var(--line);background:#0f1115;color:var(--txt);font:inherit}
.form input:focus,.form textarea:focus,.form select:focus{outline:2px solid var(--y);border-color:transparent}
.form .when{display:flex;gap:10px;flex-wrap:wrap}.form .when label{display:flex;align-items:center;gap:8px;font-weight:600;border:1px solid var(--line);border-radius:999px;padding:10px 16px;cursor:pointer;margin:0}
.form .when input{width:auto;accent-color:var(--y)}.form button{border:0;cursor:pointer;font:inherit}.form .err{color:#ff8a8a;min-height:1.2em;margin:4px 0 10px;font-weight:600}
.form .note{color:var(--mut);font-size:.88rem;margin:14px 0 0}.ok{background:rgba(46,204,113,.12);border:1px solid rgba(46,204,113,.4);border-radius:14px;padding:16px;margin-top:14px;display:none}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:26px}.chips span{font-size:.85rem;color:var(--mut);border:1px solid var(--line);padding:6px 12px;border-radius:999px}
.map{background:var(--bg2);border:1px solid var(--line);border-radius:22px;padding:18px;box-shadow:0 30px 80px rgba(0,0,0,.45)}
.map svg{display:block;width:100%;height:auto}
section{padding:clamp(56px,8vw,96px) 0}section.alt{background:var(--bg2);border-block:1px solid var(--line)}
h2{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.1;margin:0 0 14px;letter-spacing:-.01em}h3{margin:0 0 6px;font-size:1.15rem}
.sub{color:var(--mut);max-width:60ch;margin:0 0 34px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px}.card p{margin:0;color:var(--mut)}
.card .ic{width:44px;height:44px;border-radius:12px;background:rgba(255,196,0,.12);color:var(--y);display:grid;place-items:center;margin-bottom:14px}.card .ic svg{width:22px;height:22px}
.areas{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.area{display:block;text-decoration:none;color:var(--txt);background:var(--card);border:1px solid var(--line);border-radius:18px;padding:26px;transition:border-color .2s,transform .2s}
.area:hover{border-color:var(--y);transform:translateY(-2px)}.area b{font-size:1.4rem}.area p{color:var(--mut);margin:8px 0 14px}.area span{color:var(--y);font-weight:700}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;counter-reset:s}
.step{position:relative;padding:24px 24px 24px 74px;background:var(--card);border:1px solid var(--line);border-radius:18px}
.step:before{counter-increment:s;content:counter(s);position:absolute;left:22px;top:22px;width:36px;height:36px;border-radius:50%;background:var(--y);color:#111;font-weight:900;display:grid;place-items:center}
.step p{margin:0;color:var(--mut)}
details{border-bottom:1px solid var(--line);padding:6px 0}summary{cursor:pointer;font-weight:700;padding:14px 0;list-style:none}summary::-webkit-details-marker{display:none}
summary:before{content:"+";color:var(--y);font-weight:900;margin-right:10px}details[open] summary:before{content:"–"}details p{color:var(--mut);margin:0 0 14px}
.band{text-align:center;background:linear-gradient(135deg,#ffc400,#ffdb4d);color:#111;border-radius:26px;padding:clamp(36px,6vw,64px) 24px}
.band h2{color:#111}.band p{margin:0 0 22px;font-size:1.1rem}.band .call{background:#111;color:var(--y);box-shadow:none}
.place{columns:2;gap:24px;padding:0;margin:0 0 10px;list-style:none}.place li{padding:6px 0 6px 22px;position:relative;color:var(--txt)}.place li:before{content:"";position:absolute;left:0;top:15px;width:8px;height:8px;border-radius:2px;background:var(--y)}
@media(max-width:560px){.place{columns:1}}
.crumb{font-size:.9rem;color:var(--mut);margin-bottom:12px}.crumb a{color:var(--mut)}
footer{padding:40px 0 110px;color:var(--mut);font-size:.92rem;border-top:1px solid var(--line)}.fc{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}
footer h4{color:var(--txt);margin:0 0 10px}footer ul{list-style:none;padding:0;margin:0}footer li{padding:3px 0}footer a{color:var(--mut)}
.float{position:fixed;left:16px;right:16px;bottom:14px;z-index:30;display:none;justify-content:center}.float .call{width:100%;justify-content:center;font-size:1.15rem;padding:16px}
@media(max-width:820px){.float{display:flex}}"""

PHONE_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>'
ICONS = {
    "Asemakyydit": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 11h14M9 21l-2-4M15 21l2-4"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/></svg>',
    "Paikalliset kyydit": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 1 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "Hiekkasärkät ja mökit": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="17" cy="7" r="3"/><path d="M2 19c3-2 6-2 9 0s6 2 9 0M2 15c3-2 6-2 9 0s6 2 9 0"/></svg>',
    "Ennakkotilaukset": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
    "Pidemmät matkat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19 10 5h4l6 14M12 7v2M12 12v2M12 17v2"/></svg>',
    "Yritykset": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
}

MAP_SVG = """<svg viewBox="0 0 520 360" role="img" aria-label="Kartta: Kalajoki – Alavieska – Ylivieska">
<defs><linearGradient id="rd" x1="0" x2="1"><stop offset="0" stop-color="#ffc400"/><stop offset="1" stop-color="#ffdb4d"/></linearGradient>
<pattern id="gr" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="#252a34" stroke-width="1"/></pattern></defs>
<rect width="520" height="360" rx="14" fill="#141820"/><rect width="520" height="360" rx="14" fill="url(#gr)"/>
<path d="M0 70 C40 90 70 60 95 95 S120 160 80 200 S40 290 0 300 Z" fill="#12324a" opacity=".9"/>
<text x="18" y="150" fill="#5d86a8" font-size="13" font-family="system-ui" font-style="italic">Perämeri</text>
<path d="M70 170 C150 150 200 190 255 175 S370 120 455 150" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="16" stroke-linecap="round"/>
<path d="M70 170 C150 150 200 190 255 175 S370 120 455 150" fill="none" stroke="url(#rd)" stroke-width="7" stroke-linecap="round"/>
<path d="M70 170 C150 150 200 190 255 175 S370 120 455 150" fill="none" stroke="#111" stroke-width="1.5" stroke-dasharray="7 9"/>
<g font-family="system-ui" font-weight="800">
<circle cx="70" cy="170" r="11" fill="#ffc400" stroke="#111" stroke-width="3"/><text x="56" y="214" fill="#f2f3f5" font-size="19">Kalajoki</text><text x="58" y="234" fill="#a9afba" font-size="12" font-weight="600">Hiekkasärkät · Himanka</text>
<circle cx="255" cy="175" r="9" fill="#ffc400" stroke="#111" stroke-width="3"/><text x="222" y="214" fill="#f2f3f5" font-size="17">Alavieska</text>
<circle cx="455" cy="150" r="11" fill="#ffc400" stroke="#111" stroke-width="3"/><text x="398" y="118" fill="#f2f3f5" font-size="19">Ylivieska</text><text x="384" y="194" fill="#a9afba" font-size="12" font-weight="600">Rautatieasema</text>
</g>
<g transform="translate(300 290)"><rect x="-120" y="-26" width="240" height="52" rx="26" fill="#1d212a" stroke="#2a2f3a"/>
<text x="0" y="6" text-anchor="middle" fill="#f2f3f5" font-family="system-ui" font-size="15" font-weight="700">Vt 27 · noin 50 km</text></g>
</svg>"""


def call(cls="call", label=None):
    return f'<a class="{cls}" href="tel:{PUH_TEL}">{PHONE_SVG}{esc(label or "Soita " + PUH)}</a>'


def schema(page_url, city=None):
    areas = [{"@type": "City", "name": c["nimi"]} for c in KAUPUNGIT.values()] + [{"@type": "Place", "name": n} for n in ("Kalajoen Hiekkasärkät", "Himanka", "Rautio")]
    data = {
        "@context": "https://schema.org", "@type": "TaxiService", "@id": SITE + "/#taksi",
        "name": NIMI, "url": SITE + "/", "telephone": PUH_TEL,
        "provider": {"@type": "LocalBusiness", "name": NIMI, "legalName": YRITYS, "vatID": "FI" + YTUNNUS.replace("-", ""), "telephone": PUH_TEL, "url": SITE + "/",
                     "address": {"@type": "PostalAddress", "addressLocality": "Ylivieska", "addressRegion": "Pohjois-Pohjanmaa", "addressCountry": "FI"},
                     "areaServed": areas},
        "areaServed": areas if not city else [{"@type": "City", "name": city["nimi"]}] + areas,
    }
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": NIMI, "item": SITE + "/"}]
              + ([{"@type": "ListItem", "position": 2, "name": f"Taksi {city['nimi']}", "item": page_url}] if city else [])}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in UKK]}
    out = [data, crumbs] + ([] if city else [faq])
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>' for d in out)


def layout(title, desc, path, body, city=None):
    url = SITE + path
    nav = "".join(f'<a href="/taksi-{k}/">Taksi {esc(c["nimi"])}</a>' for k, c in KAUPUNGIT.items())
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">
<meta name="geo.region" content="FI-14"><meta name="geo.placename" content="{esc(city['nimi'] if city else 'Ylivieska, Alavieska, Kalajoki')}">
{f'<meta name="geo.position" content="{city["geo"][0]};{city["geo"][1]}"><meta name="ICBM" content="{city["geo"][0]}, {city["geo"][1]}">' if city else ''}
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}"><meta property="og:locale" content="fi_FI">
<meta property="og:image" content="{SITE}/og.png"><meta name="theme-color" content="#0f1115"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>{CSS}</style>{schema(url, city)}</head><body>
<header><div class="w bar"><a class="logo" href="/" aria-label="{NIMI} etusivu"><i>TAXI</i>{NIMI}</a><nav class="m" aria-label="Alueet">{nav}<a href="/yhteystiedot/">Yhteystiedot</a></nav>{call()}</div></header>
<main>{body}</main>
<footer><div class="w fc"><div><h4>{NIMI}</h4><p>Paikallinen taksi Ylivieskassa, Alavieskassa ja Kalajoella.</p><p>{call('call', 'Soita ' + PUH)}</p></div>
<div><h4>Alueet</h4><ul>{''.join(f'<li><a href="/taksi-{k}/">Taksi {esc(c["nimi"])}</a></li>' for k, c in KAUPUNGIT.items())}<li><a href="/taksi-kalajoki/#hiekkasarkat">Taksi Hiekkasärkät</a></li></ul></div>
<div><h4>Yritys</h4><ul><li>{YRITYS}</li><li>Y-tunnus {YTUNNUS}</li>{''.join(f'<li>Tilaukset: <a href="tel:{t}">{esc(n)} {esc(p)}</a></li>' for n, p, t in KULJETTAJAT)}<li><a href="/yhteystiedot/">Kaikki yhteystiedot</a></li></ul></div></div>
<div class="w" style="margin-top:24px;font-size:.82rem;opacity:.7">© {datetime.date.today().year} {YRITYS} · Sivut: <a href="https://netvo.fi/">Netvo</a></div></footer>
<div class="float">{call('call', 'Soita taksi · ' + PUH)}</div>
</body></html>"""


def lomake():
    nums = json.dumps([t for _, _, t in KULJETTAJAT])
    nimet = " ja ".join(n for n, _, _ in KULJETTAJAT)
    return f"""<section class="alt" id="tilaa" style="scroll-margin-top:70px"><div class="w"><h2>Tilaa kyyti viestillä</h2>
<p class="sub">Täytä tiedot ja paina <b>Tilaa kyyti</b>. Puhelimesi viestisovellus aukeaa valmiilla tekstiviestillä {esc(nimet)}lle – paina siellä vielä <b>Lähetä</b>. Kuljettaja vahvistaa kyydin soittamalla tai viestillä.</p>
<form class="form" id="tf" novalidate>
<div class="two"><div class="f"><label for="t-nimi">Nimi *</label><input id="t-nimi" autocomplete="name" maxlength="60" required placeholder="Kuka tilaa"></div>
<div class="f"><label for="t-puh">Puhelinnumero *</label><input id="t-puh" type="tel" autocomplete="tel" maxlength="20" required placeholder="040 123 4567"></div></div>
<div class="f"><label for="t-mista">Mistä haetaan *</label><input id="t-mista" autocomplete="street-address" maxlength="120" required placeholder="Esim. Ylivieskan rautatieasema tai Katu 1, Kalajoki"></div>
<div class="f"><label for="t-minne">Minne mennään</label><input id="t-minne" maxlength="120" placeholder="Esim. Hiekkasärkät"></div>
<div class="f"><label>Milloin</label><div class="when"><label><input type="radio" name="t-kun" value="heti" checked> Heti</label><label><input type="radio" name="t-kun" value="aika"> Tiettyyn aikaan</label></div>
<input id="t-aika" type="datetime-local" style="display:none;margin-top:10px" aria-label="Noutoaika"></div>
<div class="f"><label for="t-lisa">Lisätietoja</label><input id="t-lisa" maxlength="140" placeholder="Esim. 3 henkilöä, matkalaukkuja, juna saapuu 18.05"></div>
<p class="err" id="t-err" role="alert"></p>
<button class="call big" type="submit">{PHONE_SVG}Tilaa kyyti</button>
<div class="ok" id="t-ok" role="status"></div>
<p class="note">Viesti lähtee omasta puhelimestasi tavallisena tekstiviestinä (operaattorisi hinnoittelun mukaan). Tietojasi käytetään vain kyydin hoitamiseen. Kiireessä soita: {' / '.join(f'<a href="tel:{t}">{esc(n)} {esc(p)}</a>' for n, p, t in KULJETTAJAT)}.</p>
</form></div></section>
<script>(function(){{var N={nums},f=document.getElementById('tf'),e=document.getElementById('t-err'),ok=document.getElementById('t-ok'),a=document.getElementById('t-aika');
f.addEventListener('change',function(x){{if(x.target.name==='t-kun')a.style.display=x.target.value==='aika'?'block':'none'}});
function v(i){{return document.getElementById(i).value.trim()}}
f.addEventListener('submit',function(x){{x.preventDefault();e.textContent='';var nimi=v('t-nimi'),puh=v('t-puh'),mista=v('t-mista');
if(!nimi||puh.replace(/\\D/g,'').length<7||!mista){{e.textContent='Täytä nimi, puhelinnumero ja mistä haetaan.';return}}
var kun='Heti';if(f.querySelector('input[name=t-kun]:checked').value==='aika'){{if(!a.value){{e.textContent='Valitse noutoaika.';return}}var d=new Date(a.value);kun=d.toLocaleDateString('fi-FI',{{weekday:'short',day:'numeric',month:'numeric'}})+' klo '+d.toLocaleTimeString('fi-FI',{{hour:'2-digit',minute:'2-digit'}})}}
var t='KYYTITILAUS (taxikoskela.fi)\\nNimi: '+nimi+'\\nPuh: '+puh+'\\nMistä: '+mista+(v('t-minne')?'\\nMinne: '+v('t-minne'):'')+'\\nMilloin: '+kun+(v('t-lisa')?'\\nLisätiedot: '+v('t-lisa'):'');
var ios=/iPad|iPhone|iPod/.test(navigator.userAgent),body=encodeURIComponent(t);
var url=ios?'sms:/open?addresses='+N.join(',')+'&body='+body:'sms:'+N.join(',')+'?body='+body;
ok.style.display='block';ok.innerHTML='<b>Viestisovellus avautuu.</b> Paina siellä <b>Lähetä</b>, niin tilaus tulee kuljettajalle. Jos viestisovellus ei auennut (esim. tietokoneella), soita: '+{json.dumps(' / '.join(f'<a href="tel:{t}">{n} {p}</a>' for n, p, t in KULJETTAJAT))}+'.';
location.href=url}});}})();</script>"""


def etusivu():
    alue_kortit = "".join(f'<a class="area" href="/taksi-{k}/"><b>Taksi {esc(c["nimi"])}</b><p>{esc(c["ingressi"][:150].rsplit(" ", 1)[0])}…</p><span>Lue lisää →</span></a>' for k, c in KAUPUNGIT.items())
    palvelut = "".join(f'<div class="card"><div class="ic">{ICONS[t]}</div><h3>{esc(t)}</h3><p>{esc(p)}</p></div>' for t, p in PALVELUT)
    ukk = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in UKK)
    body = f"""<section class="hero"><div class="w g"><div>
<div class="kick"><b></b>Ylivieska · Alavieska · Kalajoki</div>
<h1>{NIMI} – <em>taksi Ylivieska ja Kalajoki</em></h1>
<p class="lead">Paikallinen taksi Ylivieskan ja Kalajoen välillä. Asemakyydit, Hiekkasärkät, kauppa- ja lääkärimatkat sekä ennakkotilaukset – yhdellä puhelulla.</p>
<div class="cta">{call('call big', 'Soita ' + PUH)}<a class="ghost" href="#tilaa">Tilaa kyyti viestillä</a></div>
<p class="drv">{'<br>'.join(f'<a href="tel:{t}">{esc(n)} · {esc(p)}</a>' for n, p, t in KULJETTAJAT)}<br><b>Myös illat ja yöt</b></p>
<div class="chips"><span>Ylivieskan rautatieasema</span><span>Kalajoen Hiekkasärkät</span><span>Himanka</span><span>Alavieska</span><span>Rautio</span></div>
</div><div class="map">{MAP_SVG}</div></div></section>
{lomake()}
<section id="palvelut"><div class="w"><h2>Taksipalvelut Ylivieska–Kalajoki-alueella</h2><p class="sub">Ajamme valtatien 27 varrella Ylivieskasta Alavieskan kautta Kalajoelle ja Hiekkasärkille – ja kaikkialla niiden välillä.</p><div class="cards">{palvelut}</div></div></section>
<section class="alt" id="alueet"><div class="w"><h2>Alueet</h2><p class="sub">Valitse paikkakunta, niin näet tarkemmin, minne ajamme.</p><div class="areas">{alue_kortit}</div></div></section>
<section><div class="w"><h2>Näin tilaat taksin</h2><p class="sub">Nopein tapa on soittaa. Ennakkotilaukset onnistuvat samasta numerosta.</p>
<div class="steps"><div class="step"><h3>Soita</h3><p>{'<br>'.join(f'<a href="tel:{t}">{esc(n)} {esc(p)}</a>' for n, p, t in KULJETTAJAT)}</p></div><div class="step"><h3>Kerro matka</h3><p>Noutopaikka, aika ja määränpää – esimerkiksi juna, Hiekkasärkät tai koti.</p></div><div class="step"><h3>Taksi tulee</h3><p>Auto on paikalla sovittuna aikana.</p></div></div></div></section>
<section class="alt" id="ukk"><div class="w" style="max-width:820px"><h2>Usein kysyttyä</h2>{ukk}</div></section>
<section><div class="w"><div class="band"><h2>Tarvitsetko taksin nyt?</h2><p>Ylivieska, Alavieska, Kalajoki ja Hiekkasärkät.</p>{call('call big', 'Soita ' + PUH)}</div></div></section>"""
    return layout(f"{NIMI} – Taksi Ylivieska ja Kalajoki | Tilaa: {PUH}",
                  f"Paikallinen taksi Ylivieskassa, Alavieskassa ja Kalajoella: asemakyydit, Hiekkasärkät, ennakkotilaukset. Tilaa {NIMI}: {PUH}.", "/", body)


def kaupunkisivu(k, c):
    muut = "".join(f'<a class="area" href="/taksi-{kk}/"><b>Taksi {esc(cc["nimi"])}</b><span>→</span></a>' for kk, cc in KAUPUNGIT.items() if kk != k)
    palvelut = "".join(f'<div class="card"><div class="ic">{ICONS[t]}</div><h3>{esc(t)}</h3><p>{esc(p)}</p></div>' for t, p in PALVELUT[:4])
    hs = ('<div id="hiekkasarkat" style="scroll-margin-top:90px;margin-top:34px" class="card"><h3>Taksi Kalajoen Hiekkasärkille</h3><p>Kuljetamme Hiekkasärkkien hotelleille, kylpylään, leirintäalueelle ja mökkikyliin – myös suoraan Ylivieskan rautatieasemalta. Tilaa kyyti junan saapumisajan mukaan.</p></div>' if k == "kalajoki" else "")
    body = f"""<section class="hero"><div class="w g"><div>
<div class="crumb"><a href="/">{NIMI}</a> › Taksi {esc(c['nimi'])}</div>
<h1>Taksi <em>{esc(c['nimi'])}</em></h1><p class="lead">{esc(c['ingressi'])}</p>
<div class="cta">{call('call big', 'Soita ' + PUH)}<a class="ghost" href="/#tilaa">Tilaa kyyti viestillä</a></div></div><div class="map">{MAP_SVG}</div></div></section>
<section><div class="w"><h2>Minne ajamme {esc(c['ines'])}</h2>
<ul class="place">{''.join(f'<li>{esc(p)}</li>' for p in c['paikat'])}</ul>
{''.join(f'<p class="sub" style="margin-bottom:14px">{esc(t)}</p>' for t in c['teksti'])}{hs}</div></section>
<section class="alt"><div class="w"><h2>Taksipalvelut {esc(c['ines'])}</h2><div class="cards">{palvelut}</div></div></section>
<section><div class="w"><h2>Myös lähialueilla</h2><div class="areas">{muut}</div></div></section>
<section style="padding-top:0"><div class="w"><div class="band"><h2>Taksi {esc(c['nimi'])} – soita</h2><p>Tilaukset ja ennakkotilaukset samasta numerosta.</p>{call('call big', 'Soita ' + PUH)}</div></div></section>"""
    return layout(f"{c['otsikko']} | {NIMI} {PUH}", c["kuvaus"], f"/taksi-{k}/", body, c)


def yhteystiedot():
    kulj = "".join(f'<div class="card"><h3>{esc(n)}</h3><p>Taksitilaukset – myös illat ja yöt</p><p style="margin-top:14px">{call("call", p)}</p></div>'.replace(f'href="tel:{PUH_TEL}"', f'href="tel:{t}"') for n, p, t in KULJETTAJAT)
    on, op, ot = OMISTAJA
    body = f"""<section class="hero"><div class="w"><div class="crumb"><a href="/">{NIMI}</a> › Yhteystiedot</div>
<h1>Yhteystiedot</h1><p class="lead">Taksin tilaat nopeimmin soittamalla kuljettajalle. Yritysasioissa ja päiväajan kysymyksissä voit olla yhteydessä omistajaan.</p></div></section>
<section style="padding-top:0"><div class="w"><h2>Tilaa taksi</h2><div class="cards">{kulj}</div></div></section>
<section class="alt"><div class="w"><h2>Omistaja</h2><div class="cards"><div class="card"><h3>{esc(on)}</h3><p>Omistaja, {esc(YRITYS)}. Yritysasiat, laskutus ja päiväajan kysymykset.</p><p style="margin-top:14px"><a class="ghost" href="tel:{ot}">{esc(op)}</a></p></div>
<div class="card"><h3>Yritystiedot</h3><p>{esc(YRITYS)}<br>Y-tunnus {YTUNNUS}<br>Toiminta-alue: Ylivieska, Alavieska, Kalajoki</p></div></div></div></section>"""
    return layout(f"Yhteystiedot – {NIMI} | Taksi Ylivieska ja Kalajoki", f"{NIMI} yhteystiedot: taksitilaukset {PUH}. Ylivieska, Alavieska ja Kalajoki.", "/yhteystiedot/", body)


def favicon():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#ffc400"/><text x="32" y="40" text-anchor="middle" font-family="Arial,sans-serif" font-weight="900" font-size="20" fill="#111">TAXI</text></svg>'


def og_kuva(path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    def f(size, bold=True):
        for fp in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
            try:
                return ImageFont.truetype(fp, size)
            except OSError:
                pass
        return ImageFont.load_default()
    im = Image.new("RGB", (1200, 630), "#0f1115"); d = ImageDraw.Draw(im)
    d.rounded_rectangle((80, 90, 230, 190), 20, fill="#ffc400"); d.text((155, 140), "TAXI", font=f(44), fill="#111", anchor="mm")
    d.text((80, 250), NIMI, font=f(92), fill="#f2f3f5")
    d.text((80, 370), "Ylivieska · Alavieska · Kalajoki", font=f(44, False), fill="#ffc400")
    d.rounded_rectangle((80, 470, 640, 550), 40, fill="#ffc400"); d.text((360, 510), f"Soita {PUH}", font=f(38), fill="#111", anchor="mm")
    im.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    og_kuva(OUT / "og.png")
    (OUT / "index.html").write_text(etusivu(), encoding="utf-8")
    for k, c in KAUPUNGIT.items():
        d = OUT / f"taksi-{k}"; d.mkdir(exist_ok=True)
        (d / "index.html").write_text(kaupunkisivu(k, c), encoding="utf-8")
    (OUT / "yhteystiedot").mkdir(exist_ok=True)
    (OUT / "yhteystiedot" / "index.html").write_text(yhteystiedot(), encoding="utf-8")
    (OUT / "favicon.svg").write_text(favicon(), encoding="utf-8")
    today = datetime.date.today().isoformat()
    urls = ["/"] + [f"/taksi-{k}/" for k in KAUPUNGIT] + ["/yhteystiedot/"]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (OUT / "404.html").write_text(layout(f"Sivua ei löytynyt – {NIMI}", "Sivua ei löytynyt.", "/404", f'<section class="hero"><div class="w"><h1>Sivua ei löytynyt</h1><p class="lead">Tarvitsetko taksin? Soita {PUH}.</p>{call("call big")}</div></section>'), encoding="utf-8")
    print("valmis:", OUT)


if __name__ == "__main__":
    main()
