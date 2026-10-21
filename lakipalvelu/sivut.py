#!/usr/bin/env python3
"""Pykälävahdin staattiset sivut (public/). Ajetaan julkaisussa ennen Workerin päivitystä."""
import os, json, html

ROOT = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(ROOT, "public")
NIMI = os.environ.get("PALVELU_NIMI", "Pykälävahti")
SITE = os.environ.get("PALVELU_URL", "").rstrip("/")
YHTEYS = "miika@eduskuntaseuranta.fi"
MYYJA = os.environ.get("PALVELU_MYYJA", "Miika Koskela, Ylivieska")
HINTA = "29"
VOIMASSA = "21.10.2026"
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
<link rel="stylesheet" href="/tyyli.css?v=4"></head>
<body><a class="skip" href="#sisalto">Siirry sisältöön</a>
<header class="hd"><div class="hd-in"><a class="brand" href="/">{LOGO}<span>{esc(NIMI)}</span></a><nav aria-label="Päävalikko">{nav}</nav></div></header>
<main id="sisalto" class="wrap">{runko}</main>
<footer class="ft"><div class="ft-in">
<p><b>{esc(NIMI)}</b> selittää Suomen lakia ajantasaisen lainsäädännön (Finlex) pohjalta. Vastaukset ovat yleistä tietoa, eivät oikeudellista neuvontaa, eikä palvelu ole asianajotoimisto. Tarkista tärkeät asiat aina juristilta.</p>
<p><a href="/tietoa/">Tietoa palvelusta</a> · <a href="/ehdot/">Käyttöehdot</a> · <a href="/tietosuoja/">Tietosuoja</a> · <a href="/juristeille/">Juristeille</a> · Yhteys: <span class="mono">{YHTEYS}</span></p>
<p class="mute">Saman ylläpitäjän palveluja: <a href="https://keraysvahti.fi">Keräysvahti</a> · <a href="https://eduskuntaseuranta.fi">Eduskuntaseuranta</a> · <a href="https://nytpuhutaan.fi">Nytpuhutaan</a></p>
</div></footer>
<script src="/sovellus.js?v=4"></script>{skripti}
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
<p class="hinta" id="hinta"></p>
<label class="ehdot" id="ehdotRivi" hidden><input type="checkbox" id="ehdot"> <span>Hyväksyn <a href="/ehdot/" target="_blank">käyttöehdot</a> ja pyydän, että pohjaesitys toimitetaan heti. Ymmärrän, että peruuttamisoikeus päättyy, kun esitys on toimitettu.</span></label>
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
<h2>Tietosuoja ja ehdot</h2><p>Kysymyksiä ja kuvauksia ei tallenneta. Tarkemmin: <a href="/tietosuoja/">tietosuojaseloste</a> ja <a href="/ehdot/">käyttöehdot</a>.</p>
<h2>Ylläpitäjä</h2><p>Miika Koskela, Ylivieska. Yhteys: <span class="mono">{YHTEYS}</span>. Palvelu on yksityinen, eikä se liity Finlexiin, oikeusministeriöön tai Suomen Asianajajaliittoon.</p></div>"""
    kirjoita("/tietoa/", sivu("/tietoa/", f"Tietoa palvelusta ja tietosuoja | {NIMI}", "Miten Pykälävahdin vastaukset syntyvät, mitä lakeja on mukana ja miten tietosuoja on hoidettu.", runko))


    # ---- käyttöehdot ----
    runko = f"""<h1>Käyttöehdot</h1><div class="proosa"><p class="mute">Voimassa {VOIMASSA} alkaen.</p>
<h2>1. Palvelu</h2><p>{esc(NIMI)} ({esc(SITE or "")}) on verkkopalvelu, joka selittää Suomen lainsäädäntöä tekoälyn avulla ajantasaisen lainsäädännön (Finlex) pohjalta, laatii käyttäjän kuvauksen perusteella pohjaesityksiä juristille ja näyttää lakitoimistojen yhteystietoja. Palvelun tarjoaa {esc(MYYJA)}.</p>
<h2>2. Ei oikeudellista neuvontaa</h2><p>Palvelun vastaukset ja pohjaesitykset ovat yleistä tietoa laista ja juristin tarkistettavaksi tarkoitettuja luonnoksia. Ne eivät ole oikeudellista neuvontaa eivätkä korvaa juristia. Palvelu ei ole asianajotoimisto, eikä palveluntarjoaja ole asianajaja. Tekoäly voi erehtyä, ja lopputulokseen voivat vaikuttaa seikat, joita palvelu ei tunne, kuten sopimukset, työehtosopimukset ja oikeuskäytäntö. Käyttäjä vastaa itse siitä, miten hän käyttää palvelun antamaa tietoa.</p>
<h2>3. Maksut</h2><p>Kysymykset laista ovat maksuttomia. Pohjaesitys juristille maksaa {HINTA} euroa (sis. arvonlisäveron), ellei sitä tarjota maksutta esimerkiksi avajaiskaudella. Hinta näkyy ennen maksamista. Maksu suoritetaan Stripe-maksupalvelun kautta, eikä palveluntarjoaja näe kortin tietoja.</p>
<h2>4. Toimitus ja peruuttamisoikeus</h2><p>Pohjaesitys on digitaalista sisältöä, joka toimitetaan heti maksun jälkeen näytölle. Käyttäjä pyytää toimitusta ennen peruuttamisajan päättymistä ja hyväksyy, että peruuttamisoikeus päättyy, kun esitys on toimitettu (kuluttajansuojalaki 6 luku 16 §). Jos pohjaesitystä ei teknisen vian vuoksi saada laadittua, käyttäjä voi yrittää uudelleen samalla maksulla tai pyytää maksun palautusta osoitteesta <span class="mono">{YHTEYS}</span>.</p>
<h2>5. Vastuunrajoitus</h2><p>Palveluntarjoaja ei vastaa vahingoista, jotka aiheutuvat palvelun antaman tiedon käyttämisestä, palvelun keskeytyksistä tai tekoälyn virheistä, ellei pakottavasta lainsäädännöstä muuta johdu. Vastuu rajoittuu enintään käyttäjän palvelusta maksamaan hintaan.</p>
<h2>6. Lakitoimistojen tiedot</h2><p>Toimistotiedot perustuvat kaupparekisterin avoimeen dataan. Palvelu ei suosittele mitään toimistoa eikä vastaa toimistojen palveluista tai hinnoista.</p>
<h2>7. Muutokset palveluun, hinnoitteluun ja ehtoihin</h2><p><b>Palveluntarjoaja pidättää oikeuden muuttaa palvelun sisältöä, hinnoittelua, ansaintamallia ja näitä käyttöehtoja.</b> Palveluun voidaan esimerkiksi lisätä tarjouspyyntöjen välitys lakitoimistoille ja siihen liittyvä välitys- tai säästöön perustuva palkkio. Muutokset tulevat voimaan, kun ne on julkaistu tällä sivulla. Muutokset eivät koske jo maksettuja tilauksia.</p>
<h2>8. Sovellettava laki ja riidat</h2><p>Ehtoihin sovelletaan Suomen lakia. Kuluttaja voi saattaa riidan kuluttajariitalautakunnan käsiteltäväksi. Ennen sitä kannattaa olla yhteydessä kuluttajaneuvontaan. Lisätietoja: <a href="https://www.kuluttajariita.fi" rel="noopener">kuluttajariita.fi</a>.</p>
<h2>9. Yhteystiedot</h2><p>{esc(MYYJA)}<br>Sähköposti: <span class="mono">{YHTEYS}</span></p></div>"""
    kirjoita("/ehdot/", sivu("/ehdot/", f"Käyttöehdot | {NIMI}", "Pykälävahdin käyttöehdot: palvelun luonne, maksut, toimitus, peruuttamisoikeus ja muutokset.", runko))

    # ---- tietosuojaseloste ----
    runko = f"""<h1>Tietosuojaseloste</h1><div class="proosa"><p class="mute">EU:n yleisen tietosuoja-asetuksen (2016/679) 13 artikla. Päivitetty {VOIMASSA}.</p>
<h2>1. Rekisterinpitäjä</h2><p>{esc(MYYJA)}<br>Yhteys tietosuoja-asioissa: <span class="mono">{YHTEYS}</span></p>
<h2>2. Mitä tietoja käsitellään ja miksi</h2>
<ul><li><b>Kysymykset ja pohjaesitysten kuvaukset.</b> Käsitellään vain vastauksen muodostamiseksi. Niitä <b>ei tallenneta</b> palveluun. Ennen käsittelyä tekstistä poistetaan automaattisesti henkilötunnukset, sähköpostiosoitteet, puhelinnumerot ja tilinumerot. Käyttäjää pyydetään olemaan kirjoittamatta tunnistettavia tietoja. Peruste: käyttäjän pyytämän palvelun tuottaminen (sopimus, 6 art. 1 b).</li>
<li><b>Maksutiedot.</b> Maksun käsittelee Stripe. Palvelu saa tiedon maksun onnistumisesta ja maksutunnuksen, joka säilytetään 30 päivää maksun käytön valvomiseksi. Kirjanpitoon liittyvät tiedot säilytetään kirjanpitolain edellyttämän ajan. Peruste: sopimus ja lakisääteinen velvoite (6 art. 1 b ja c).</li>
<li><b>Tekniset tiedot.</b> Käyttömäärien rajoittamiseksi IP-osoitteesta lasketaan päivittäin vaihtuva tunnistamaton tiiviste, joka poistuu vuorokauden kuluessa. Kävijämäärät mitataan evästeettömästi. Peruste: oikeutettu etu palvelun turvallisuuteen ja väärinkäytösten estämiseen (6 art. 1 f).</li></ul>
<h2>3. Vastaanottajat ja siirrot EU:n ulkopuolelle</h2>
<ul><li><b>Anthropic PBC</b> (tekoäly, Yhdysvallat): kysymys ja siihen liittyvät lakitekstit välitetään vastauksen muodostamiseksi. Anthropic ei käytä rajapinnan kautta tulevia tietoja mallien kouluttamiseen ja säilyttää niitä rajoitetun ajan väärinkäytösten valvontaa varten. Siirto perustuu EU:n komission vakiosopimuslausekkeisiin.</li>
<li><b>Cloudflare</b> (palvelin ja kävijämittaus) ja <b>Stripe</b> (maksut). Molemmat käsittelevät tietoja palveluntarjoajan lukuun ja käyttävät tarvittaessa vakiosopimuslausekkeita.</li></ul>
<p>Tietoja ei myydä eikä luovuteta markkinointiin.</p>
<h2>4. Säilytys</h2><p>Kysymyksiä ja kuvauksia ei säilytetä. Maksutunniste 30 päivää, kirjanpitoaineisto lain edellyttämän ajan, tekniset tiivisteet enintään vuorokauden.</p>
<h2>5. Oikeutesi</h2><p>Sinulla on oikeus saada tietoa käsittelystä, tarkastaa ja oikaista tietosi, pyytää poistamista ja vastustaa käsittelyä. Koska kysymyksiä ei tallenneta, niistä ei ole jälkikäteen tarkastettavaa tietoa. Pyynnöt: <span class="mono">{YHTEYS}</span>. Voit tehdä valituksen tietosuojavaltuutetulle: <a href="https://tietosuoja.fi" rel="noopener">tietosuoja.fi</a>.</p>
<h2>6. Tulevat toiminnot</h2><p>Jos palveluun lisätään tarjouspyyntöjen välitys lakitoimistoille, käyttäjän yhteystietoja ja asian kuvaus välitetään käyttäjän valitsemille toimistoille vain hänen erillisellä pyynnöstään. Tämä seloste päivitetään ennen toiminnon käyttöönottoa.</p></div>"""
    kirjoita("/tietosuoja/", sivu("/tietosuoja/", f"Tietosuojaseloste | {NIMI}", "Pykälävahdin tietosuojaseloste: kysymyksiä ei tallenneta.", runko))

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


    # ---- seuranta (ylläpitäjälle, ei hakukoneisiin) ----
    lnimet = json.dumps({l["id"]: l["nimi"] for l in LAIT["lait"]}, ensure_ascii=False)
    runko = """<h1>Seuranta</h1><p class="lead">Kysymysten ja pohjaesitysten määrät päivittäin sekä suosituimmat lait (30 päivää). Kysymysten sisältöä ei tallenneta.</p>
<div class="kolme" id="yht"></div><h2>Päivittäin</h2><div id="pv" class="lista"></div><h2>Suosituimmat lait</h2><div id="lait" class="lista"></div>
<style>.pal{display:flex;align-items:center;gap:8px;font-size:.9rem}.pal i{display:block;height:12px;background:var(--gold);border-radius:3px}.pal span{min-width:92px;color:var(--mute)}</style>"""
    js = "<script>var N=" + lnimet + r""";fetch('/api/seuranta').then(r=>r.json()).then(d=>{var k=0,e=0,L={};d.forEach(x=>{k+=x.kysymys||0;e+=x.esitys||0;for(var l in (x.lait||{}))L[l]=(L[l]||0)+x.lait[l]});
document.getElementById('yht').innerHTML='<div class="kortti"><b>'+k+'</b><span>kysymystä 30 pv</span></div><div class="kortti"><b>'+e+'</b><span>pohjaesitystä 30 pv</span></div><div class="kortti"><b>'+(d[0].kysymys||0)+'</b><span>kysymystä tänään</span></div>';
var m=Math.max(1,...d.map(x=>x.kysymys||0));document.getElementById('pv').innerHTML=d.map(x=>'<div class="pal"><span>'+x.pv.slice(8,10)+'.'+x.pv.slice(5,7)+'.</span><i style="width:'+Math.round(200*(x.kysymys||0)/m)+'px"></i>'+(x.kysymys||0)+' / '+(x.esitys||0)+'</div>').join('');
var t=Object.entries(L).sort((a,b)=>b[1]-a[1]).slice(0,15),mm=Math.max(1,...t.map(x=>x[1]));document.getElementById('lait').innerHTML=t.map(x=>'<div class="pal"><span>'+x[1]+'</span><i style="width:'+Math.round(200*x[1]/mm)+'px"></i>'+(N[x[0]]||x[0])+'</div>').join('')||'<p class="mute">Ei vielä kysymyksiä.</p>'})</script>"""
    kirjoita("/seuranta/", sivu("/seuranta/", f"Seuranta | {NIMI}", "", runko, js).replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1))

    # ---- 404, robots, sivukartta ----
    open(os.path.join(PUB, "404.html"), "w", encoding="utf-8").write(sivu("/404", f"Sivua ei löytynyt | {NIMI}", "", '<h1>Sivua ei löytynyt</h1><p><a class="btn" href="/">Etusivulle</a></p>'))
    if SITE:
        open(os.path.join(PUB, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /seuranta/\nSitemap: {SITE}/sitemap.xml\n")
        open(os.path.join(PUB, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in ("/", "/pohjaesitys/", "/toimistot/", "/tietoa/", "/juristeille/", "/ehdot/", "/tietosuoja/")) + "</urlset>\n")
    print("sivut valmiit")


if __name__ == "__main__":
    main()
