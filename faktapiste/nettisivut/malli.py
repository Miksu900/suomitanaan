"""Mallisivustojen generaattori: tekee itsenäisen, mobiilioptimoidun yrityssivun datasta.

Jokainen sivu on oma kokonaisuus (ei Faktapiste-ylätunnistetta), teemaväri valitaan datasta.
Sama moottori tekee sekä palvelualojen sivut että yksinkertaiset verkkokauppamallit.
"""
import html

esc = html.escape

TEEMAT = {
    "sininen": ("#1557c0", "#0e3a85", "#eaf1fb"),
    "vihrea": ("#1f7a4d", "#145535", "#e7f4ec"),
    "oranssi": ("#d9631a", "#a84a11", "#fcefe4"),
    "musta": ("#1a1a1a", "#000000", "#f0f0f0"),
    "viininpunainen": ("#9c2742", "#6f1a2f", "#f8e9ed"),
    "petroli": ("#116b74", "#0b4a50", "#e4f2f3"),
    "ruskea": ("#7a5230", "#553820", "#f2ebe3"),
    "purppura": ("#5b3a9c", "#3f286e", "#efe9f8"),
}


def _nappi(teksti, href, toissijainen=False):
    lk = "nappi2" if toissijainen else "nappi"
    return f'<a class="{lk}" href="{esc(href)}">{esc(teksti)}</a>'


def _ikoni(nimi):
    i = {
        "puhelin": '<path d="M4 4h4l2 5-3 2a12 12 0 006 6l2-3 5 2v4a2 2 0 01-2 2A16 16 0 014 6a2 2 0 010-2z"/>',
        "sposti": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "sijainti": '<path d="M12 21s-7-6-7-11a7 7 0 1114 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
        "kello": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "tarkista": '<path d="M5 12l4 4 10-10"/>',
    }.get(nimi, "")
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{i}</svg>'


def sivu(d, demo=True):
    """d: yrityssivun data (dict). Palauttaa koko HTML-sivun."""
    p, p2, pehmea = TEEMAT.get(d.get("teema", "sininen"), TEEMAT["sininen"])
    nimi = d["nimi"]
    kauppa = d.get("tyyppi") == "kauppa"

    palvelut = "".join(
        f'<div class="kortti"><h3>{esc(s["nimi"])}</h3><p>{esc(s["kuvaus"])}</p>'
        + (f'<span class="hinta">{esc(s["hinta"])}</span>' if s.get("hinta") else "")
        + (f'<a class="osta" href="#yhteys">Tilaa</a>' if kauppa else "")
        + "</div>"
        for s in d.get("palvelut", []))

    arvostelut = ""
    if d.get("arvostelut"):
        arvostelut = '<section class="osio arv"><div class="w"><h2>Mitä asiakkaat sanovat</h2><div class="arvot">' + "".join(
            f'<figure><p>&ldquo;{esc(a["teksti"])}&rdquo;</p><figcaption>— {esc(a["nimi"])}</figcaption></figure>'
            for a in d["arvostelut"]) + "</div></div></section>"

    maksu = ""
    if kauppa:
        maksu = ('<section class="osio"><div class="w teksti" style="text-align:center"><h2>Verkkokauppa ja maksut</h2>'
                 '<p style="max-width:58ch;margin:0 auto">Verkkokaupassa asiakas voi maksaa tilauksensa suoraan sivuilla. '
                 'Pyydä maksupalvelun liittäminen kauppaasi itse, niin me integroimme sen. Maksupalvelun kulut ovat erikseen. '
                 'Ehdotamme sinulle sopivan palvelun, esimerkiksi Paytrail, Stripe tai Nexi. '
                 'Isommat verkkokaupat räätälöidään, pyydä tarjous.</p>'
                 f'<p style="margin-top:20px"><a class="nappi" href="mailto:info@netvo.fi?subject=Netvo%20-%20maksupalvelun%20integrointi%20verkkokauppaan">Pyydä maksupalvelu</a></p>'
                 '</div></section>')

    esittely = ""
    if d.get("esittely"):
        esittely = f'<section class="osio" id="meista"><div class="w kaksi"><div><h2>{esc(d.get("esittely_otsikko", "Meistä"))}</h2>' + \
            "".join(f"<p>{esc(x)}</p>" for x in d["esittely"]) + "</div>" + \
            (f'<ul class="edut">' + "".join(f'<li><span class="ik">{_ikoni("tarkista")}</span>{esc(e)}</li>' for e in d.get("edut", [])) + "</ul>" if d.get("edut") else "") + \
            "</div></section>"

    ajat = ""
    if d.get("aukiolo"):
        ajat = '<div class="aukiolo"><h3>Aukioloajat</h3><table>' + "".join(
            f"<tr><td>{esc(pv)}</td><td>{esc(aika)}</td></tr>" for pv, aika in d["aukiolo"]) + "</table></div>"

    yhteys_rivit = "".join(
        f'<a class="yht-rivi" href="{href}"><span class="ik">{_ikoni(ik)}</span>{esc(txt)}</a>'
        for ik, txt, href in [
            ("puhelin", d.get("puhelin", ""), "tel:" + d.get("puhelin", "").replace(" ", "")),
            ("sposti", d.get("sposti", ""), "mailto:" + d.get("sposti", "")),
            ("sijainti", d.get("osoite", ""), "#"),
        ] if txt)

    demopalkki = ('<div class="demopalkki">Tämä on <b>mallisivu</b>. Oma sivustosi näyttää tältä sisällölläsi ja väreilläsi. '
                  '<a href="/">Katso hinta ja ehdot →</a></div>') if demo else ""

    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(nimi)} – {esc(d.get("slogan", d.get("ala", "")))}</title>
<meta name="description" content="{esc(d.get("meta", nimi))}">
<meta name="robots" content="noindex">
<style>
:root{{--p:{p};--p2:{p2};--pehmea:{pehmea};--ink:#1b1b1f;--mute:#5c6066;--line:#e4e4e8;--bg:#fff}}
*{{box-sizing:border-box}}
body{{margin:0;font:16px/1.65 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}}
.w{{max-width:1040px;margin:0 auto;padding:0 20px}}
a{{color:var(--p)}}
h1,h2,h3{{line-height:1.2;margin:0 0 .5em}}
.demopalkki{{background:#111;color:#fff;text-align:center;padding:9px 16px;font-size:.9rem}}
.demopalkki a{{color:#ffd24a;font-weight:600;white-space:nowrap}}
header.top{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid var(--line)}}
.top .w{{display:flex;align-items:center;justify-content:space-between;height:66px}}
.logo{{font-weight:800;font-size:1.25rem;color:var(--p);text-decoration:none;letter-spacing:-.01em}}
.top nav{{display:flex;gap:4px;align-items:center}}
.top nav a{{color:var(--ink);text-decoration:none;font-weight:600;font-size:.95rem;padding:8px 10px;border-radius:8px}}
.top nav a.nappi{{color:#fff}}
@media(max-width:680px){{.top nav a:not(.nappi){{display:none}}}}
.nappi{{background:var(--p);color:#fff;text-decoration:none;font-weight:700;padding:11px 20px;border-radius:10px;display:inline-block}}
.nappi:hover{{background:var(--p2)}}
.nappi2{{background:transparent;color:#fff;border:1.5px solid rgba(255,255,255,.7);text-decoration:none;font-weight:700;padding:11px 20px;border-radius:10px;display:inline-block}}
.hero{{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;padding:72px 0}}
.hero h1{{font-size:clamp(2rem,6vw,3.3rem);margin-bottom:.3em}}
.hero p{{font-size:1.2rem;opacity:.95;max-width:30ch;margin:0 0 1.6em}}
.hero .toim{{display:flex;gap:12px;flex-wrap:wrap}}
.osio{{padding:56px 0}}
.osio h2{{font-size:clamp(1.5rem,4vw,2rem);text-align:center;margin-bottom:1em}}
.ruudut{{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}}
.kortti{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px}}
.kortti h3{{font-size:1.15rem}}.kortti p{{color:var(--mute);margin:0 0 10px}}
.kortti .hinta{{font-weight:800;color:var(--p);font-size:1.1rem}}
.kortti .osta{{display:inline-block;margin-top:10px;background:var(--pehmea);color:var(--p2);font-weight:700;text-decoration:none;padding:8px 16px;border-radius:9px}}
.kaksi{{display:grid;gap:36px;grid-template-columns:1fr 1fr;align-items:start}}
@media(max-width:720px){{.kaksi{{grid-template-columns:1fr}}}}
.edut{{list-style:none;padding:0;margin:0;display:grid;gap:12px}}
.edut li{{display:flex;gap:12px;align-items:flex-start;font-weight:600}}
.edut .ik,.yht-rivi .ik{{width:26px;height:26px;flex:none;color:var(--p)}}
.edut .ik svg,.yht-rivi .ik svg{{width:100%;height:100%}}
.arv{{background:var(--pehmea)}}
.arvot{{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
.arvot figure{{margin:0;background:#fff;border-radius:16px;padding:22px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}
.arvot p{{font-size:1.05rem}}.arvot figcaption{{color:var(--mute);font-weight:700;margin-top:10px}}
#yhteys{{background:var(--ink);color:#fff}}
#yhteys h2{{color:#fff}}
.yht-grid{{display:grid;gap:30px;grid-template-columns:1fr 1fr}}
@media(max-width:720px){{.yht-grid{{grid-template-columns:1fr}}}}
.yht-rivi{{display:flex;gap:12px;align-items:center;color:#fff;text-decoration:none;padding:10px 0;font-weight:600;border-bottom:1px solid rgba(255,255,255,.15)}}
.yht-rivi .ik{{color:#fff}}
.aukiolo table{{width:100%;border-collapse:collapse;margin-top:8px}}
.aukiolo td{{padding:7px 0;border-bottom:1px solid rgba(255,255,255,.15);color:#dcdce0}}
.aukiolo td:last-child{{text-align:right;font-weight:700;color:#fff}}
footer.jalka{{background:#0c0c0e;color:#9a9aa0;text-align:center;padding:26px 16px;font-size:.88rem}}
.lomake{{display:grid;gap:12px}}
.lomake input,.lomake textarea{{width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.08);color:#fff;font:inherit}}
.lomake input::placeholder,.lomake textarea::placeholder{{color:#aaa}}
.lomake button{{background:var(--p);color:#fff;border:0;font:700 1rem inherit;padding:13px;border-radius:10px;cursor:pointer}}
</style></head>
<body>
{demopalkki}
<header class="top"><div class="w">
<a class="logo" href="#">{esc(nimi)}</a>
<nav><a href="#palvelut">{"Tuotteet" if kauppa else "Palvelut"}</a>{'<a href="#meista">Meistä</a>' if d.get("esittely") else ""}<a href="#yhteys">Yhteys</a>{_nappi("Soita" if d.get("puhelin") else "Ota yhteyttä", "tel:" + d.get("puhelin", "").replace(" ", "") if d.get("puhelin") else "#yhteys")}</nav>
</div></header>
<section class="hero"><div class="w">
<h1>{esc(d.get("slogan", nimi))}</h1>
<p>{esc(d.get("lupaus", ""))}</p>
<div class="toim">{_nappi(d.get("cta", "Varaa aika"), "#yhteys")}{_nappi("Katso " + ("tuotteet" if kauppa else "palvelut"), "#palvelut", True)}</div>
</div></section>
<section class="osio" id="palvelut"><div class="w"><h2>{esc(d.get("palvelut_otsikko", "Tuotteet" if kauppa else "Palvelut"))}</h2><div class="ruudut">{palvelut}</div></div></section>
{esittely}
{arvostelut}
{maksu}
<section class="osio" id="yhteys" style="padding:56px 0"><div class="w"><h2>Ota yhteyttä</h2><div class="yht-grid">
<div>{yhteys_rivit}{ajat}</div>
<form class="lomake" onsubmit="return false">
<input placeholder="Nimesi" required><input placeholder="Sähköposti tai puhelin" required>
<textarea placeholder="Viestisi" rows="4"></textarea>
<button type="submit">Lähetä viesti</button>
<p style="color:#9a9aa0;font-size:.82rem;margin:0">Mallisivulla lomake ei lähetä viestiä. Oikealla sivustolla viesti tulee suoraan sähköpostiisi.</p>
</form>
</div></div></section>
<footer class="jalka">© {esc(nimi)} · {esc(d.get("osoite", ""))} · Sivuston toteuttaa Netvo</footer>
</body></html>"""
