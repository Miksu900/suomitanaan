"""Omalahja (omalahja.fi): personoidut lahjat, painatus tilauksesta (Gelato). Sivut kirjoitetaan kansioon <root>/omalahja/."""
import html, pathlib, datetime
esc = html.escape
YRITYS = "Taksiliikenne Koskela Oy"
YTUNNUS = "3425681-3"
OSOITE = "Riihikatu 3 B 20, 84100 Ylivieska"
EMAIL = "info@omalahja.fi"
PUH = "044 777 7149"
PV = "5.11.2026"

def sivu(otsikko, kuvaus, runko, polku):
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}"><link rel="canonical" href="https://omalahja.fi{polku}">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}"><meta property="og:url" content="https://omalahja.fi{polku}"><meta property="og:locale" content="fi_FI">
<meta name="theme-color" content="#7a2e2e"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%237a2e2e'/%3E%3Cpath d='M8 14h16v12H8zM6 10h20v4H6zM16 10v16' stroke='%23fff6ec' stroke-width='2' fill='none'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Nunito+Sans:wght@400;600;700&display=swap">
<style>
:root{{--bg:#fbf6ef;--card:#fffdf9;--ink:#2b2321;--mute:#6f625c;--line:#ebe0d3;--accent:#7a2e2e;--accent2:#c9822b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1d1715;--card:#26201d;--ink:#f3ebe3;--mute:#b8aaa1;--line:#3a312c;--accent:#e08a7a;--accent2:#e6b06a;color-scheme:dark}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 "Nunito Sans",system-ui,sans-serif}}
.w{{max-width:1040px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left))}}
header.yla{{padding:18px 0;border-bottom:1px solid var(--line)}}header.yla .w{{display:flex;justify-content:space-between;align-items:center;gap:12px}}
.logo{{font-family:Fraunces,Georgia,serif;font-weight:650;font-size:1.5rem;color:var(--accent);text-decoration:none}}
h1,h2,h3{{font-family:Fraunces,Georgia,serif;font-weight:650;line-height:1.15;margin:0 0 .5em}}h1{{font-size:clamp(2.2rem,6vw,3.6rem)}}h2{{font-size:1.6rem;margin-top:1.6em}}
a{{color:var(--accent)}}.mute{{color:var(--mute)}}
.hero{{padding:56px 0 36px}}.hero p{{font-size:1.15rem;max-width:40em}}
.badge{{display:inline-block;background:var(--accent2);color:#2b1a08;font-weight:700;border-radius:99px;padding:4px 14px;font-size:.85rem;margin-bottom:16px}}
.kortit{{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));margin:28px 0 56px}}
.kortti{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px}}.kortti h3{{font-size:1.25rem}}.kortti p{{margin:0;color:var(--mute)}}.hinta{{font-family:Fraunces,serif;font-size:1.4rem;margin-top:10px;color:var(--ink)}}
.teksti{{max-width:760px;padding:40px 0 64px}}
footer{{border-top:1px solid var(--line);padding:28px 0 40px;font-size:.92rem;color:var(--mute)}}footer a{{color:var(--mute)}}
</style></head><body>
<header class="yla"><div class="w"><a class="logo" href="/">Omalahja</a><a href="mailto:{EMAIL}">{EMAIL}</a></div></header>
<main>{runko}</main>
<footer><div class="w"><p><b>Omalahja</b> · {YRITYS} (Y-tunnus {YTUNNUS}) · {OSOITE} · <a href="mailto:{EMAIL}">{EMAIL}</a> · puh. {PUH}</p>
<p><a href="/toimitusehdot/">Toimitus- ja maksuehdot</a> · <a href="/tietosuoja/">Tietosuojaseloste</a> · <a href="/yhteystiedot/">Yhteystiedot</a></p></div></footer>
</body></html>"""

TUOTTEET = [("Nimijuliste 50×70", "Perheen tai lapsen nimi kauniina julisteena. Valitse tyyli ja värit.", "59 €"),
            ("Kotikaupunki-kartta 50×70", "Oma kaupunki, kylä tai mökkiranta karttajulisteena, nimellä ja koordinaateilla.", "59 €"),
            ("Canvastaulu 30×40", "Valitsemasi kuva tai teksti tukevalle kankaalle puukehyksessä.", "69 €"),
            ("Kehystetty juliste 30×40", "Valmiiksi kehystetty personoitu juliste – heti seinälle.", "79 €")]

def etusivu():
    k = "".join(f'<div class="kortti"><h3>{esc(n)}</h3><p>{esc(t)}</p><div class="hinta">{h}</div></div>' for n, t, h in TUOTTEET)
    runko = f"""<section class="hero"><div class="w"><span class="badge">Avautuu pian</span>
<h1>Lahja, jossa on nimi.</h1>
<p>Omalahja tekee personoituja julisteita ja tauluja suomeksi: nimet, päivämäärät, kotikaupungit ja omat tekstit. Jokainen tuote painetaan tilauksesta juuri sinulle ja toimitetaan kotiin.</p>
<p class="mute">Verkkokauppa avautuu marraskuussa 2026 – ehdit hyvin jouluun.</p></div></section>
<section><div class="w"><h2>Tulossa valikoimaan</h2><div class="kortit">{k}</div></div></section>"""
    return sivu("Omalahja – personoidut lahjat suomeksi", "Personoidut julisteet ja taulut suomeksi: nimet, kotikaupungit ja omat tekstit. Painetaan tilauksesta.", runko, "/")

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
<h2>Tuotteet ja hinnat</h2><p>Myymme personoituja painotuotteita, kuten julisteita ja tauluja, jotka valmistetaan asiakkaan antamien tietojen mukaan. Hinnat ovat euroja ja sisältävät arvonlisäveron 25,5 %. Toimituskulut näytetään ennen maksamista.</p>
<h2>Tilaus</h2><p>Tilaus syntyy, kun maksu on hyväksytty. Saat tilausvahvistuksen sähköpostiisi. Tarkista personointitiedot (nimet, päivämäärät, tekstit) huolellisesti ennen tilaamista, sillä tuote valmistetaan niiden mukaan.</p>
<h2>Toimitus</h2><p>Tuotteet valmistetaan tilauksesta yhteistyökumppanimme painossa EU:ssa ja toimitetaan kotiin tai lähimpään noutopisteeseen. Arvioitu toimitusaika on 8–14 arkipäivää tilauksesta. Ilmoitamme, jos toimitus viivästyy.</p>
<h2>Peruuttamisoikeus</h2><p>Kuluttajansuojalain 6 luvun 16 §:n mukaan peruuttamisoikeutta ei ole tavaroihin, jotka valmistetaan tai muokataan selvästi kuluttajan yksilöllisten vaatimusten mukaisesti. Personoiduilla tuotteilla ei siksi ole 14 päivän peruuttamisoikeutta. Voit kuitenkin perua tilauksen maksutta ottamalla yhteyttä ennen kuin tuote on siirtynyt valmistukseen.</p>
<h2>Virheet ja reklamaatiot</h2><p>Jos tuote on vaurioitunut, painovirheellinen tai muuten virheellinen, ilmoita siitä 14 päivän kuluessa vastaanottamisesta osoitteeseen {EMAIL} ja liitä mukaan kuva. Toimitamme uuden tuotteen tai palautamme rahat. Kuluttaja voi viedä riita-asian kuluttajariitalautakunnan käsiteltäväksi (kuluttajariita.fi); ennen sitä kannattaa olla yhteydessä kuluttajaneuvontaan.</p>
<h2>Maksaminen ja maksupalveluntarjoaja</h2><p>Maksunvälityspalvelun toteuttajana ja maksupalveluntarjoajana toimii Visma Payments Oy (Y-tunnus 2486559-4), joka on rekisteröity Finanssivalvonnan ylläpitämään maksulaitosrekisteriin. Voit maksaa verkkopankkitunnuksilla, mobiilimaksulla tai maksukortilla. Visma Payments Oy:n yhteystiedot: Laserkatu 6, 53850 Lappeenranta, helpdesk@vismapay.com.</p>
<h2>Tekijänoikeudet</h2><p>Asiakas vastaa siitä, että hänellä on oikeus käyttää tilaukseen lähettämiään kuvia ja tekstejä.</p></div>"""
    return sivu("Toimitus- ja maksuehdot – Omalahja", "Omalahjan toimitus- ja maksuehdot.", runko, "/toimitusehdot/")

def tietosuoja():
    runko = f"""<div class="w teksti"><h1>Tietosuojaseloste</h1><p class="mute">EU:n yleinen tietosuoja-asetus (2016/679). Päivitetty {PV}.</p>
<h2>Rekisterinpitäjä</h2><p>{YRITYS} (Y-tunnus {YTUNNUS}), {OSOITE}. Yhteyshenkilö: Miika Koskela, {EMAIL}.</p>
<h2>Mitä tietoja käsittelemme</h2><p>Tilauksen yhteydessä: nimi, toimitusosoite, sähköposti, puhelinnumero, tilauksen sisältö ja personointitiedot sekä maksun tila. Emme näe tai tallenna maksukorttitietoja.</p>
<h2>Käsittelyn tarkoitus ja peruste</h2><p>Tilausten toimittaminen ja asiakaspalvelu (sopimus), kirjanpito (lakisääteinen velvoite). Jos tilaat uutiskirjeen, lähetämme sitä suostumuksesi perusteella.</p>
<h2>Tietojen vastaanottajat</h2><p>Tuotteen valmistaja ja toimittaja Gelato (toimitusosoite ja tuotetiedot), maksunvälittäjä Visma Payments Oy, sähköpostipalvelu Brevo sekä palvelinpalvelu Cloudflare. Tietoja ei myydä eteenpäin.</p>
<h2>Säilytysaika</h2><p>Tilaustiedot säilytetään kirjanpitolain vaatiman ajan (6 vuotta tilikauden päättymisestä). Personointikuvat poistetaan, kun tilaus on toimitettu ja reklamaatioaika päättynyt.</p>
<h2>Evästeet</h2><p>Sivusto käyttää vain toiminnan kannalta välttämättömiä tietoja. Jos otamme käyttöön mainonnan tai analytiikan evästeitä, pyydämme niihin erikseen suostumuksen.</p>
<h2>Oikeutesi</h2><p>Voit pyytää pääsyä tietoihisi, niiden oikaisua tai poistamista sekä vastustaa käsittelyä. Ota yhteyttä {EMAIL}. Voit myös tehdä valituksen tietosuojavaltuutetulle (tietosuoja.fi).</p></div>"""
    return sivu("Tietosuojaseloste – Omalahja", "Omalahjan tietosuojaseloste.", runko, "/tietosuoja/")

def rakenna(root):
    r = pathlib.Path(root) / "omalahja"
    for polku, f in [("", etusivu), ("yhteystiedot", yhteystiedot), ("toimitusehdot", toimitusehdot), ("tietosuoja", tietosuoja)]:
        (r / polku).mkdir(parents=True, exist_ok=True); (r / polku / "index.html").write_text(f(), encoding="utf-8")
    (r / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://omalahja.fi/sitemap.xml\n", encoding="utf-8")
    (r / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>https://omalahja.fi{u}</loc></url>" for u in ["/", "/toimitusehdot/", "/tietosuoja/", "/yhteystiedot/"]) + "</urlset>", encoding="utf-8")
