#!/usr/bin/env python3
"""Pykälävahdin staattiset sivut (public/). Ajetaan julkaisussa ennen Workerin päivitystä."""
import os, json, html

ROOT = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(ROOT, "public")
NIMI = os.environ.get("PALVELU_NIMI", "Pykälävahti")
SITE = os.environ.get("PALVELU_URL", "").rstrip("/")
YHTEYS = "miika@eduskuntaseuranta.fi"
esc = lambda s: html.escape(s or "", quote=True)

try:
    LAIT = json.load(open(os.path.join(PUB, "data", "lait.json"), encoding="utf-8"))
except Exception:
    LAIT = {"haettu": "", "lait": []}

LOGO = ('<svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect x="2" y="2" width="28" height="28" rx="8" fill="var(--acc)"/>'
        '<text x="16" y="23" text-anchor="middle" font-family="Georgia,serif" font-size="20" font-weight="700" fill="var(--acc-ink)">§</text></svg>')


def sivu(polku, otsikko, kuvaus, runko, skripti="", aktiivinen=""):
    nav = "".join(f'<a href="{u}"{" aria-current=page" if aktiivinen == k else ""}>{n}</a>' for k, u, n in
                  (("kysy", "/", "Kysy laista"), ("esitys", "/pohjaesitys/", "Pohjaesitys juristille"), ("toimistot", "/toimistot/", "Lakitoimistot")))
    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}"><meta property="og:type" content="website"><meta property="og:locale" content="fi_FI">
{f'<link rel="canonical" href="{SITE}{polku}"><meta property="og:url" content="{SITE}{polku}"><meta property="og:image" content="{SITE}/og.png">' if SITE else ''}
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#14213d">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,600;7..72,700&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/tyyli.css?v=3"></head>
<body><a class="skip" href="#sisalto">Siirry sisältöön</a>
<header class="hd"><div class="hd-in"><a class="brand" href="/">{LOGO}<span>{esc(NIMI)}</span></a><nav aria-label="Päävalikko">{nav}</nav></div></header>
<main id="sisalto" class="wrap">{runko}</main>
<footer class="ft"><div class="ft-in">
<p><b>{esc(NIMI)}</b> selittää Suomen lakia ajantasaisen lainsäädännön (Finlex) pohjalta. Vastaukset ovat yleistä tietoa, eivät oikeudellista neuvontaa, eikä palvelu ole asianajotoimisto. Tarkista tärkeät asiat aina juristilta.</p>
<p><a href="/tietoa/">Tietoa palvelusta ja tietosuoja</a> · <a href="/juristeille/">Juristeille</a> · Yhteys: <span class="mono">{YHTEYS}</span></p>
<p class="mute">Saman ylläpitäjän palveluja: <a href="https://keraysvahti.fi">Keräysvahti</a> · <a href="https://eduskuntaseuranta.fi">Eduskuntaseuranta</a> · <a href="https://nytpuhutaan.fi">Nytpuhutaan</a></p>
</div></footer>
<script src="/sovellus.js?v=3"></script>{skripti}
</body></html>"""


def kirjoita(polku, s):
    p = os.path.join(PUB, polku.strip("/"), "index.html") if polku != "/" else os.path.join(PUB, "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


ESIMERKIT = ["Ostamani pesukone hajosi puolen vuoden päästä. Onko kauppa velvollinen korjaamaan sen?",
             "Kuinka pitkä irtisanomisaika minulla on, kun olen ollut töissä 3 vuotta?",
             "Saako vuokranantaja pitää koko vuokravakuuden, jos seinissä on naulanreikiä?",
             "Mitä lakiosa tarkoittaa ja kuka sen saa?",
             "Milloin velka vanhenee?"]

VAROITUS = ('<p class="huom"><b>Älä kirjoita</b> nimiä, henkilötunnuksia, osoitteita tai muita tunnistettavia tietoja. '
            'Kysymystä ei tallenneta. Se välitetään tekoälypalvelulle vastauksen muodostamista varten.</p>')


def main():
    lait_lkm = len(LAIT["lait"])
    # ---- etusivu: kysy laista ----
    esim = "".join(f'<button type="button" class="esim" data-q="{esc(x)}">{esc(x)}</button>' for x in ESIMERKIT)
    runko = f"""<section class="hero">
<p class="eyebrow">Suomen laki selkokielellä</p>
<h1>Kysy laista. Saat vastauksen pykälineen.</h1>
<p class="lead">{esc(NIMI)} etsii vastauksen ajantasaisesta lainsäädännöstä ja kertoo, mitä laki sanoo ja mitä voit tehdä. Jokainen väite on merkitty pykälään, jonka voit tarkistaa itse.</p>
<form id="kysyLomake" class="kysy" onsubmit="return false">
<label for="kysymys" class="sr">Kysymyksesi</label>
<textarea id="kysymys" rows="4" maxlength="1500" placeholder="Kirjoita kysymyksesi omin sanoin…"></textarea>
<input type="text" id="hp" class="sr" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="rivi"><button type="submit" class="btn" id="kysyNappi">Kysy</button><span class="mute small" id="merkit">0 / 1500</span></div>
{VAROITUS}
</form>
<div class="esimerkit" aria-label="Esimerkkikysymyksiä">{esim}</div>
</section>
<section id="tulos" class="tulos" aria-live="polite" hidden></section>
<section class="kolme">
<a class="kortti" href="/pohjaesitys/"><b>Pohjaesitys juristille</b><span>Kuvaa tilanteesi, niin saat valmiin muistion. Juristi pääsee heti asiaan, ja säästät kuluissa.</span></a>
<a class="kortti" href="/toimistot/"><b>Löydä lakitoimisto</b><span>Kaikki asianajo- ja lakiasiaintoimistot paikkakunnittain. Näe lähimmät.</span></a>
<a class="kortti" href="/tietoa/"><b>Miten tämä toimii?</b><span>{lait_lkm} keskeistä lakia Finlexistä, päivitetään viikoittain.</span></a>
</section>"""
    kirjoita("/", sivu("/", f"{NIMI} – kysy Suomen laista, vastaus pykälineen",
                       "Kysy Suomen laista omin sanoin ja saat selkokielisen vastauksen, jossa on viittaukset ajantasaisiin pykäliin. Ilmainen.",
                       runko, '<script>Pv.kysy()</script>', "kysy"))

    # ---- pohjaesitys ----
    runko = f"""<h1>Pohjaesitys juristille</h1>
<p class="lead">Kuvaa tilanteesi, niin {esc(NIMI)} kokoaa siitä muistion: tosiseikat, sovellettavat pykälät, alustavan arvion ja avoimet kysymykset. Kun viet muistion juristille, hän pääsee heti asiaan, eikä sinun tarvitse maksaa selvitystyöstä.</p>
<form id="esitysLomake" class="kysy" onsubmit="return false">
<label for="kuvaus">Mitä on tapahtunut?</label>
<textarea id="kuvaus" rows="8" maxlength="4000" placeholder="Kerro tapahtumat aikajärjestyksessä: mitä sovittiin, mitä tapahtui, mitä toinen osapuoli on sanonut…"></textarea>
<label for="tavoite">Mitä haluaisit saavuttaa?</label>
<textarea id="tavoite" rows="2" maxlength="800" placeholder="Esim. rahat takaisin, sopimuksen purku, tieto omista oikeuksista"></textarea>
<label for="ajat">Tärkeät päivämäärät ja määräajat <span class="mute">(vapaaehtoinen)</span></label>
<input id="ajat" type="text" maxlength="400" placeholder="Esim. kauppa 3.4.2026, reklamoin 10.5.2026">
<input type="text" id="hp" class="sr" tabindex="-1" autocomplete="off" aria-hidden="true">
<button type="submit" class="btn" id="esitysNappi">Laadi pohjaesitys</button>
{VAROITUS.replace("Kysymystä", "Kuvausta")}
</form>
<section id="tulos" class="tulos" aria-live="polite" hidden></section>"""
    kirjoita("/pohjaesitys/", sivu("/pohjaesitys/", f"Pohjaesitys juristille | {NIMI}",
             "Kuvaa oikeudellinen tilanteesi ja saat juristille valmiin muistion pykälineen. Säästä juristin selvitystyössä.", runko,
             '<script>Pv.esitys()</script>', "esitys"))

    # ---- toimistot ----
    runko = """<h1>Lakitoimistot</h1>
<p class="lead">Kaikki Suomen asianajotoimistot ja lakiasiaintoimistot kaupparekisterin avoimesta datasta. Hae paikkakunnalla tai nimellä, tai näe lähimmät toimistot.</p>
<div class="haku"><label for="th" class="sr">Hae</label><input id="th" type="search" placeholder="Paikkakunta tai toimiston nimi, esim. Ylivieska" autocomplete="off">
<button type="button" class="btn toissij" id="lahin">Näytä lähimmät</button></div>
<div class="suodin" role="group" aria-label="Toimiston laji"><label><input type="radio" name="laji" value="" checked> Kaikki</label><label><input type="radio" name="laji" value="Asianajotoimisto"> Asianajotoimistot</label><label><input type="radio" name="laji" value="Lakiasiaintoimisto"> Lakiasiaintoimistot</label></div>
<p id="tl" class="mute">Ladataan…</p>
<div id="toimistot" class="lista"></div>
<aside class="huom"><b>Asianajaja vai lakimies?</b> Asianajotoimistossa työskentelee yleensä asianajajia, jotka ovat Suomen Asianajajaliiton jäseniä ja valvottuja. Lakiasiaintoimistossa voi työskennellä myös muita lakimiehiä. Jos tulosi ovat pienet, voit saada <a href="https://oikeus.fi/oikeusapu" rel="noopener">julkista oikeusapua</a> valtion oikeusaputoimistosta.</aside>
<aside class="huom"><b>Vertaa hintoja:</b> pyydä toimistoilta hinta-arvio ja liitä mukaan <a href="/pohjaesitys/">pohjaesitys</a>. Kun asia on valmiiksi jäsennelty, arvio on helpompi antaa, ja selvitystyön osuus laskusta pienenee.</aside>"""
    kirjoita("/toimistot/", sivu("/toimistot/", f"Lakitoimistot ja asianajotoimistot paikkakunnittain | {NIMI}",
             "Löydä lähin asianajotoimisto tai lakiasiaintoimisto. Kaikki toimistot kaupparekisterin avoimesta datasta.", runko,
             '<script>Pv.toimistot()</script>', "toimistot"))

    # ---- tietoa ----
    lait = "".join(f'<li>{esc(l["nimi"])} ({esc(l["lyh"])})</li>' for l in LAIT["lait"])
    runko = f"""<h1>Tietoa palvelusta</h1><div class="proosa">
<p>{esc(NIMI)} auttaa ymmärtämään, mitä Suomen laki sanoo omassa tilanteessasi, ja valmistautumaan juristin tapaamiseen.</p>
<h2>Miten vastaus syntyy</h2>
<ol><li>Kysymyksesi perusteella valitaan, mistä laeista vastaus todennäköisimmin löytyy.</li>
<li>Laeista haetaan olennaisimmat pykälät ajantasaisesta lainsäädännöstä (Finlexin avoin data).</li>
<li>Tekoäly muotoilee vastauksen <b>vain näiden pykälien perusteella</b> ja merkitsee jokaiseen väitteeseen lähteen. Pykälät näkyvät vastauksen alla, joten voit tarkistaa ne itse.</li></ol>
<h2>Rajoitukset</h2>
<p>Vastaukset ovat yleistä tietoa laista, eivät oikeudellista neuvontaa. Palvelu ei ole asianajotoimisto, eikä sen ylläpitäjä ole asianajaja. Tekoäly voi tulkita väärin, ja lopputulokseen voivat vaikuttaa myös sopimukset, työehtosopimukset, yhtiöjärjestykset ja tuomioistuinten ratkaisut, joita palvelu ei vielä kata. Jos asialla on sinulle merkitystä tai siinä on määräaika, käänny juristin puoleen.</p>
<h2>Mukana olevat lait</h2><p>Aineisto haettu Finlexistä {esc(LAIT.get("haettu", ""))}. Päivitetään viikoittain.</p><ul class="lait">{lait}</ul>
<h2>Lakitoimistot</h2><p>Toimistoluettelo perustuu Patentti- ja rekisterihallituksen avoimeen dataan (YTJ, päätoimiala 69101 asianajotoimistot ja 69102 muut lakiasiainpalvelut). Kuntien sijainnit: © OpenStreetMapin tekijät.</p>
<h2>Tietosuoja</h2>
<p>Kysymyksiä ja kuvauksia <b>ei tallenneta</b>. Ne välitetään tekoälypalvelulle (Anthropic) vastauksen muodostamista varten. Palveluntarjoaja voi säilyttää viestejä rajoitetun ajan väärinkäytösten estämiseksi, mutta ei käytä niitä mallien kouluttamiseen. Ennen lähettämistä tekstistä poistetaan automaattisesti henkilötunnukset, sähköpostiosoitteet, puhelinnumerot ja tilinumerot. Käyttömäärien rajoittamiseksi IP-osoitteesta lasketaan päivittäin vaihtuva tunnistamaton tiiviste, joka poistuu vuorokaudessa. Kävijämäärät lasketaan evästeettömällä Cloudflare Web Analyticsilla.</p>
<h2>Ylläpitäjä</h2><p>Miika Koskela, Ylivieska. Yhteys: <span class="mono">{YHTEYS}</span>. Palvelu on yksityinen, eikä se liity Finlexiin, oikeusministeriöön tai Suomen Asianajajaliittoon.</p></div>"""
    kirjoita("/tietoa/", sivu("/tietoa/", f"Tietoa palvelusta ja tietosuoja | {NIMI}", "Miten Pykälävahdin vastaukset syntyvät, mitä lakeja on mukana ja miten tietosuoja on hoidettu.", runko))

    # ---- juristeille ----
    runko = f"""<h1>Juristeille ja lakitoimistoille</h1><div class="proosa">
<p>{esc(NIMI)} ohjaa ihmisiä, joilla on oikeudellinen ongelma, ymmärtämään tilanteensa ja ottamaan yhteyttä juristiin. Asiakas tulee usein valmiin <b>pohjaesityksen</b> kanssa: tosiseikat, sovellettavat säännökset ja avoimet kysymykset on jo jäsennelty.</p>
<h2>Kumppaniksi</h2>
<ul><li><b>Näkyvyys:</b> toimistonne korostetaan omalla paikkakunnallanne ja hakutuloksissa.</li>
<li><b>Asiakasyhteydenotot:</b> asiakas voi lähettää pohjaesityksensä suoraan teille hinta-arviota varten (tulossa).</li>
<li><b>Tarkistuspalvelu:</b> asiakas pyytää juristia tarkistamaan tekoälyn laatiman muistion kiinteään hintaan.</li></ul>
<p>Kiinnostaako? Ota yhteyttä: <span class="mono">{YHTEYS}</span></p>
<h2>Onko toimistonne tiedoissa virhe?</h2><p>Toimistotiedot tulevat kaupparekisteristä. Ilmoita korjaus tai lisätieto (esim. verkkosivu tai erikoisalat) yllä olevaan osoitteeseen.</p></div>"""
    kirjoita("/juristeille/", sivu("/juristeille/", f"Juristeille ja lakitoimistoille | {NIMI}", "Asiakkaita valmiiksi jäsennellyn pohjaesityksen kanssa. Tule kumppaniksi.", runko))

    # ---- 404, robots, sivukartta ----
    open(os.path.join(PUB, "404.html"), "w", encoding="utf-8").write(sivu("/404", f"Sivua ei löytynyt | {NIMI}", "", '<h1>Sivua ei löytynyt</h1><p><a class="btn" href="/">Etusivulle</a></p>'))
    if SITE:
        open(os.path.join(PUB, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {SITE}/sitemap.xml\n")
        open(os.path.join(PUB, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in ("/", "/pohjaesitys/", "/toimistot/", "/tietoa/", "/juristeille/")) + "</urlset>\n")
    print("sivut valmiit")


if __name__ == "__main__":
    main()
