"""Faktapiste.fi – kattosivusto. Rakentaa staattiset sivut kansioon public/.

Etusivu esittelee kaikki palvelut. /palvelut/ on mainoksiin sopiva versio ilman poliittisia palveluita.
Aja: python3 faktapiste/rakenna.py
"""
import os, html, datetime, pathlib

ROOT = pathlib.Path(__file__).parent / "public"
SITE = os.environ.get("FAKTAPISTE_URL", "https://faktapiste.fi")
PV = os.environ.get("PYKALAVAHTI_URL", "https://pykalavahti.fi")
YHTEYS = "miika@eduskuntaseuranta.fi"
VER = "42"
esc = html.escape

# avain, nimi, osoite, iskulause, kuvaus, merkki, poliittinen
PALVELUT = [
    ("kv", "Keräysvahti", "https://keraysvahti.fi", "Onko keräyksellä lupa?",
     "Tarkista ennen lahjoittamista, onko rahankeräyksellä poliisin lupa ja kuuluuko tilinumero oikealle järjestölle. Haku kattaa kaikki voimassa olevat luvat.",
     "Ilmainen haku", False),
    ("hj", "Huijausapu", "https://keraysvahti.fi/huijaukset/", "Epäiletkö huijausta?",
     "Tunnista tavallisimmat huijaukset, tarkista epäilyttävä viesti ja katso, mitä tehdä heti, jos rahaa on jo mennyt.",
     "Viestintarkistin", False),
    ("yv", "Yksityisyysvahti", "/yksityisyys/", "Onko sijaintisi myynnissä?",
     "Sammuta puhelimesi sijainti- ja mainosseuranta muutamassa minuutissa ja pyydä yrityksiä poistamaan tietosi valmiilla viestipohjalla.",
     "Uusi", False),
    ("pv", "Pykälävahti", PV, "Mitä laki sanoo?",
     "Kysy arkisesta lakiasiasta ja saat vastauksen suoraan voimassa olevista pykälistä lähteineen. Kirjoittaa myös reklamaation tai muun vaatimuksen puolestasi.",
     "Valmis kirje", False),
    ("kr", "Korjausvahti", "https://nytpuhutaan.fi/muutokset/", "Mitä otsikossa muutettiin?",
     "Seuraa, miten uutisotsikot muuttuvat julkaisun jälkeen. Näet alkuperäisen ja uuden otsikon rinnakkain.",
     "Otsikkomuutokset", False),
    ("np", "Nytpuhutaan", "https://nytpuhutaan.fi", "Mistä Suomessa puhutaan nyt?",
     "Päivän uutiset suomalaisista lähteistä yhdessä paikassa, ilman algoritmia ja ilman kirjautumista.",
     "Uutiskooste", False),
    ("es", "Eduskuntaseuranta", "https://eduskuntaseuranta.fi", "Miten edustajasi äänestää?",
     "Jokaisen kansanedustajan äänet, poissaolot ja ryhmästä poikkeamiset eduskunnan avoimesta datasta.",
     "Äänestystiedot", True),
]

IKONIT = {
    "kv": '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
    "hj": '<path d="M12 3l9 16H3L12 3z"/><path d="M12 10v4M12 17h.01"/>',
    "pv": '<text x="12" y="18" text-anchor="middle" font-size="19" font-weight="700" fill="currentColor" stroke="none" font-family="Georgia,serif">§</text>',
    "kr": '<path d="M4 7h10M4 12h16M4 17h7"/><path d="M15 15l4 4M19 15l-4 4"/>',
    "np": '<path d="M4 5h13a3 3 0 013 3v11H7a3 3 0 01-3-3V5z"/><path d="M8 9h8M8 13h8M8 17h5"/>',
    "yv": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/><path d="M4 4l16 16"/>',
    "es": '<path d="M3 21h18M5 21V10M19 21V10M9 21v-7M15 21v-7"/><path d="M2 10l10-6 10 6"/>',
}

LOGO = '<span class="logo" aria-hidden="true"><b>FAKTA</b><i>PISTE.</i></span>'

def kortti(p, iso=False):
    k, nimi, url, isku, kuvaus, merkki, _ = p
    return f"""<a class="palvelu{' iso' if iso else ''}" href="{esc(url)}" rel="noopener">
<span class="ik" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{IKONIT[k]}</svg></span>
<span class="pt"><span class="merkki">{esc(merkki)}</span>
<strong>{esc(nimi)}</strong>
<span class="isku">{esc(isku)}</span>
<span class="kuv">{esc(kuvaus)}</span>
<span class="osoite">{esc(url.replace('https://', '').rstrip('/'))} →</span></span></a>"""

def sivu(polku, otsikko, kuvaus, runko, noindex=False):
    can = SITE + polku
    nav = [("/", "Keskustelu"), ("/palvelut/", "Palvelut"), ("/tietoa/", "Tietoa")]
    navh = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == polku else ""}>{t}</a>' for h, t in nav)
    vuosi = datetime.date.today().year
    tili = '<span id="fp-tili"></span>' if polku == "/" else ""
    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}">
<link rel="canonical" href="{can}">{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}">
<meta property="og:url" content="{can}"><meta property="og:type" content="website"><meta property="og:locale" content="fi_FI">
<meta property="og:image" content="{SITE}/og.png"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#160a26">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Faktapiste"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"Faktapiste","url":"{SITE}/","logo":"{SITE}/og.png","email":"{YHTEYS}","description":"Suomalainen keskustelupalvelu, jossa jokainen postaus näytetään vähintään 30 ihmiselle, sekä ilmaisia palveluita julkisista lähteistä."}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/tyyli.css?v={VER}">
</head><body>
<a class="skip" href="#sisalto">Siirry sisältöön</a>
<header class="hd"><div class="w hdw"><a class="brand" href="/" aria-label="Faktapiste – etusivu">{LOGO}</a><nav aria-label="Päävalikko">{navh}{tili}</nav></div></header>
<main id="sisalto">{runko}</main>
<footer class="ft"><div class="w">{LOGO}
<p>Faktapiste on suomalainen keskustelupalvelu, jossa sinut nähdään. Keskustelun tukena ovat ilmaiset palvelut, jotka perustuvat julkisiin lähteisiin: poliisin lupatietoihin, Finlexiin, eduskunnan avoimeen dataan ja uutismedian otsikoihin.</p>
<p><a href="/">Keskustelu</a> · <a href="/palvelut/">Palvelut</a> · <a href="/tietoa/">Tietoa, säännöt ja tietosuoja</a> · <span class="mono">{YHTEYS}</span></p>
<p class="mute">© {vuosi} Faktapiste</p></div></footer>
</body></html>"""

def kirjoita(polku, sisalto):
    f = ROOT / polku.strip("/") / "index.html" if polku != "/" else ROOT / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(sisalto, encoding="utf-8")

ROOT.mkdir(parents=True, exist_ok=True)
import shutil; shutil.copy(pathlib.Path(__file__).parent / "kunnat.json", ROOT / "kunnat.json")

# ---- etusivu: keskustelu + palvelut ----
def minikortti(p):
    k, nimi, url, isku, _, _, _ = p
    return f'<a class="mini" href="{esc(url)}" rel="noopener"><span class="ik" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{IKONIT[k]}</svg></span><span><b>{esc(nimi)}</b><small>{esc(isku)}</small></span></a>'
runko = f"""<section class="fp-intro"><div class="w">
<p class="beta">Beta</p>
<h1>Täällä sinut <span class="hl">nähdään.</span></h1>
<p class="lead">Suomalainen keskustelu, jossa jokainen postaus näytetään vähintään 30 ihmiselle, vaikka sinulla ei olisi yhtään seuraajaa. Sinä säädät syötteesi, ja se loppuu, kun olet nähnyt tärkeimmät.</p>
</div></section>
<div class="w fp-grid">
<div class="fp-keski">
<div id="fp-paa">
<div id="fp-asenna"></div>
<div id="fp-opastus"></div>
<div id="fp-arvonta"></div>
<div id="fp-kirjoita"></div>
<div class="tabit" id="fp-tabit" role="tablist" aria-label="Syöte"></div>
<div class="saato" id="fp-saato" hidden></div>
<div id="fp-syote" aria-live="polite"><noscript><p class="lataa">Keskustelu vaatii JavaScriptin.</p></noscript></div>
</div>
<div id="fp-ketju" hidden></div>
</div>
<aside class="fp-sivu">
<div class="laatikko"><h2>Faktapisteen palvelut</h2>{''.join(minikortti(p) for p in PALVELUT)}</div>
<div class="laatikko"><h2>Säännöt lyhyesti</h2><ul><li>Jokainen postaus näytetään vähintään 30 ihmiselle.</li><li>Saa olla eri mieltä ja kärkevä.</li><li>Ei uhkailua, henkilötietojen levittämistä, kiihottamista kansanryhmää vastaan eikä roskapostia.</li><li>Kolme ilmoitusta piilottaa postauksen tarkistusta varten.</li></ul><a href="/tietoa/#keskustelu">Säännöt ja tietosuoja →</a></div>
</aside>
</div>
<dialog id="fp-kirjaudu" aria-label="Kirjaudu"></dialog>
<div id="fp-toast" class="toast" role="status" aria-live="polite"></div>
<script src="/sovellus.js?v={VER}" defer></script>"""
kirjoita("/", sivu("/", "Faktapiste – täällä sinut nähdään",
                   "Suomalainen keskustelu, jossa jokainen postaus näytetään vähintään 30 ihmiselle. Säädä syötettä itse, seuraa oman paikkakuntasi keskustelua ja liitä faktat postaukseesi.", runko))

# ---- palvelut: mainoksiin sopiva versio ----
ARKI = [p for p in PALVELUT if not p[6] and p[0] != "np"]
runko = f"""<section class="hero pieni"><div class="w">
<p class="eyebrow">Faktapisteen palvelut</p>
<h1>Apua arjen <span class="hl">tarkistuksiin.</span></h1>
<p class="lead">Ilmaisia työkaluja, joilla tarkistat keräyksen, tunnistat huijauksen ja selvität oikeutesi ilman kirjautumista.</p>
</div></section>
<section class="w"><div class="ruudukko">{''.join(kortti(p, iso=True) for p in ARKI)}</div></section>"""
kirjoita("/palvelut/", sivu("/palvelut/", "Palvelut | Faktapiste",
                            "Tarkista keräyksen lupa, tunnista huijaus ja selvitä, mitä laki sanoo. Ilmaiset palvelut ilman kirjautumista.", runko))

# ---- tietoa ----
runko = f"""<section class="w teksti">
<p class="eyebrow">Tietoa</p><h1>Tietoa Faktapisteestä</h1>
<p>Faktapiste on suomalainen keskustelupalvelu, jossa jokainen postaus näytetään vähintään 30 ihmiselle, vaikka kirjoittajalla ei olisi yhtään seuraajaa. Keskustelu käydään omalla nimellä, syötettä voi säätää itse ja se loppuu, kun tärkeimmät on nähty.</p>
<p>Keskustelun tukena ovat Faktapisteen ilmaiset palvelut, jotka perustuvat julkisiin lähteisiin.</p>
<h2 id="palvelut">Faktapisteen palvelut</h2>
<ul class="palvelulista">{''.join(f'<li><a href="{esc(p[2])}" rel="noopener"><b>{esc(p[1])}</b></a> – {esc(p[4])}</li>' for p in PALVELUT)}
<li><a href="https://suomitanaan.fi" rel="noopener"><b>Suomi Tänään</b></a> – Uutiset suoraan alkuperäislähteistä, kuten eduskunnasta, ministeriöistä ja viranomaisilta. Poliittisten juttujen lopussa on erikseen merkitty toimituksen näkökulma.</li></ul>
<p>Faktapiste on yksityinen ja puolueeton hanke. Palvelut eivät ole viranomaisen palveluita, eivätkä ne liity poliisiin, Finlexiin, oikeusministeriöön tai eduskuntaan.</p>
<h2>Ylläpitäjä</h2>
<p>Miika Koskela, Ylivieska. Yhteys: <span class="mono">{YHTEYS}</span>.</p>
<h2>Tietosuoja</h2>
<p>Palveluiden sivut eivät käytä seurantaevästeitä eivätkä mainosseurantaa. Sivusto toimii Cloudflaren palvelussa, joka voi tallentaa teknisiä lokitietoja (kuten IP-osoitteen) palvelun toiminnan ja turvallisuuden vuoksi. Fontit ladataan Googlen Fonts-palvelusta. Kunkin palvelun omat tietosuojatiedot löytyvät palvelun sivuilta.</p>
<p><b>Keskustelu.</b> Jos kirjaudut keskusteluun, tallennamme sähköpostiosoitteesi, nimesi, postauksesi, tykkäyksesi ja ilmoituksesi. Sähköpostiosoitetta käytetään vain kirjautumislinkkien lähettämiseen, eikä sitä näytetä muille. Kirjautuminen käyttää yhtä välttämätöntä evästettä (fp_s), joka pitää sinut kirjautuneena 60 päivää. Lukukertojen laskemiseen (taattu yleisö ja syötteen loppuminen) selain tallentaa satunnaisen lukijatunnisteen, jonka avulla palvelin muistaa, mitkä postaukset olet jo nähnyt. Tunnistetta ei yhdistetä henkilöön eikä käytetä mainontaan, ja tieto poistuu muutamassa päivässä. Syötteen säädöt ja paikkakunta tallentuvat vain selaimeesi. Kertakäyttöisillä sähköpostiosoitteilla ei voi liittyä, ja Gmailin pisteelliset ja +-päätteiset muunnelmat tulkitaan samaksi osoitteeksi, jotta yhdellä sähköpostilla ei voi luoda useita tilejä.</p>
<p id="valetilit"><b>Valetilien ja väärinkäytösten estäminen.</b> Kun kirjaudut tai käytät keskustelua, tallennamme tiliisi liitettynä kaksi tunnistetta: tiivisteen IP-osoitteesi verkko-osasta ja tiivisteen selaimesi satunnaisesta lukijatunnisteesta. Tiiviste on yksisuuntainen salattu muoto, josta IP-osoitetta ei voi lukea, mutta sen avulla voidaan havaita, käytetäänkö useaa tiliä samalta laitteelta tai samasta verkosta. Tietoa käytetään vain valetilien, arvontahuijausten ja muun väärinkäytön estämiseen (oikeutettu etu, tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta), esimerkiksi kutsuarpoja ei anneta, jos kutsuttu tili on luotu samalla laitteella kuin kutsujan tili. Tunnisteita ei näytetä muille, ei käytetä mainontaan eikä luovuteta eteenpäin, ja ne poistuvat automaattisesti 180 päivän kuluessa. Päätöksiä ei tehdä pelkästään automaattisesti: ylläpitäjä tarkistaa arvonnan voittajan ennen palkinnon antamista. Voit vastustaa käsittelyä tai pyytää tietojasi ottamalla yhteyttä osoitteeseen <span class="mono">{YHTEYS}</span>.</p>
<p><b>Arvonnat.</b> Arvontaan käytetään nimeäsi, sähköpostiosoitettasi, kirjoitustesi määrää ja edellä kuvattuja väärinkäytöstunnisteita. Voittajalta pyydetään palkinnon toimittamista varten tilinumero (rahapalkinto) tai osoite lahjakortille. Voittajan nimi, palkinto ja maksutiedot säilytetään kirjanpitoa ja arpajaisveroa varten kirjanpitolain edellyttämän ajan, muiden osallistujien arvontatiedot poistetaan arvonnan jälkeen tarpeettomina.</p>
<p> Kirjautumisviestit lähetetään Brevo-palvelun kautta. Faktahaut käsitellään tekoälyllä (Anthropic). Tietoja ei myydä eikä käytetä mainontaan. Voit pyytää tilisi ja tietojesi poistamista osoitteesta <span class="mono">{YHTEYS}</span>.</p>
<h2 id="keskustelu">Keskustelun säännöt</h2>
<ul>
<li>Keskustelu käydään omalla nimellä. Etu- ja sukunimesi näkyvät postaustesi yhteydessä. Toisena henkilönä tai keksityllä nimellä esiintyvä tili voidaan sulkea.</li>
<li>Saa olla eri mieltä, kritisoida kovasti ja kirjoittaa kärkevästi, myös päättäjistä ja puolueista.</li>
<li>Kiellettyä on väkivallalla uhkaaminen, yksityishenkilöiden henkilötietojen levittäminen, kiihottaminen kansanryhmää vastaan, kunnianloukkaus, lapsia seksualisoiva sisältö, pornografia ja muu seksuaalinen tai hyvän tavan vastainen sisältö sekä mainostus, lainatarjoukset ja huijaukset.</li>
<li>Kirjoittaja vastaa itse kirjoituksestaan. Postauksia ei tarkisteta etukäteen, vaan ne julkaistaan heti.</li>
<li>Jokaisessa postauksessa on Ilmoita-toiminto. Kun kolme käyttäjää on ilmoittanut postauksesta, se piilotetaan tarkistusta varten. Ylläpitäjä poistaa lainvastaisen sisällön viipymättä ja voi sulkea sääntöjä rikkovan tilin.</li>
<li>Ilmoituksen voi tehdä myös sähköpostilla osoitteeseen <span class="mono">{YHTEYS}</span>. Kerro postauksen linkki ja syy.</li>
<li>Syötteen järjestys: Sinulle-näkymä näyttää ensin uudet postaukset, joita ei ole vielä nähnyt 30 lukijaa (taattu yleisö), ja sen jälkeen tykkäysten, vastausten ja tuoreuden mukaan. Näkymä näyttää vain sellaista, mitä et ole vielä nähnyt, ja loppuu, kun tärkeimmät on katsottu. Voit säätää, paljonko näet keskusteluja, uutisia, otsikkomuutoksia, huijausvaroituksia ja päätöksiä, ja jokaisessa postauksessa kerrotaan, miksi näet sen. Uusimmat-näkymä on aikajärjestyksessä ja Lähellä-näkymä näyttää valitsemasi paikkakunnan postaukset ja uutiset. Automaattinen sisältö tulee Faktapisteen omista palveluista (Suomi Tänään, Korjausvahti, Eduskuntaseuranta, Keräysvahti) ja on merkitty.</li>
<li>Faktahaun vastaukset kokoaa tekoäly eduskunnan avoimesta datasta. Ne voivat sisältää virheitä, joten tarkista tärkeät asiat lähteestä.</li>
</ul>
<h2>Käyttöehdot</h2>
<p>Palvelut ovat tällä hetkellä maksuttomia. Ylläpitäjä pidättää oikeuden muuttaa palveluita ja niiden ehtoja sekä ottaa käyttöön maksullisia ominaisuuksia; muutoksista kerrotaan etukäteen. Tiedot ovat yleistä tietoa eivätkä oikeudellista tai taloudellista neuvontaa.</p>
</section>"""
ARVONTA_RUNKO = f"""<section class="teksti w">
<h1>Arvonnat: 100 € joka kuukausi ja jopa 500 €</h1>
<p>Faktapiste arpoo aktiivisten kirjoittajien kesken joka kuukausi 100 euron K-ryhmän lahjakortin ja lisäksi pidemmältä kaudelta ison palkinnon, joka kasvaa käyttäjämäärän mukana jopa 500 euroon. Ison palkinnon voittaja saa valita rahana tai K-ryhmän lahjakorttina. Osallistuminen on maksutonta, eikä se edellytä ostoa. Mitä ahkerammin kirjoitat ja kommentoit, sitä enemmän sinulla on arpoja ja sitä todennäköisemmin voitat.</p>
<ul class="lista">
<li><b>100 euron K-ryhmän lahjakortti joka kuukausi:</b> marraskuu (25.10.–30.11.2026, arvonta 1.12.2026), joulukuu (1.–31.12.2026, arvonta 1.1.2027) ja tammikuu (1.–31.1.2027, arvonta 1.2.2027).</li>
<li><b>Iso arvonta, jopa 500 euroa rahana tai K-ryhmän lahjakorttina:</b> kausi 25.10.2026–31.1.2027, arvonta 1.2.2027. Palkinnon suuruus riippuu Faktapisteen käyttäjämäärästä arvontahetkellä:
<ul><li>alle 250 käyttäjää: 100 €</li><li>250–999 käyttäjää: 250 €</li><li>vähintään 1000 käyttäjää: 500 €</li></ul>
Käyttäjiksi lasketaan omalla nimellä rekisteröityneet tilit, joita ei ole suljettu. Ajantasainen käyttäjämäärä näkyy keskustelusivun arvontalaatikossa.</li>
</ul>
<h2>Säännöt</h2>
<p class="pieni">Säännöt päivitetty 25.10.2026: arpojen päiväraja poistettiin ja kutsuarvat nostettiin 10 arpaan.</p>
<ul class="lista">
<li><b>Järjestäjä:</b> Faktapiste, ylläpitäjä Miika Koskela, Ylivieska. Yhteys: <span class="mono">{YHTEYS}</span></li>
<li><b>Kuka voi osallistua:</b> 18 vuotta täyttäneet Suomessa asuvat Faktapisteen käyttäjät, jotka kirjoittavat omalla nimellään. Ylläpitäjä ei osallistu.</li>
<li><b>Arvat:</b> jokainen oma kirjoitus ja kommentti on yksi arpa, kun siinä on vähintään 20 merkkiä. Arpojen määrää ei ole rajoitettu: mitä enemmän kirjoitat, sitä enemmän sinulla on arpoja. Sama teksti useaan kertaan lasketaan yhtenä, ja alle minuutin välein kirjoitetut viestit lasketaan yhdeksi arvaksi. Sama arpa on mukana sekä kuukauden arvonnassa että isossa arvonnassa, kun se osuu niiden kauteen.</li>
<li><b>Kutsuarvat:</b> jokaisella käyttäjällä on oma kutsulinkki (näkyy keskustelusivun arvontalaatikossa). Saat <b>10 lisäarpaa</b> molempiin arvontoihin jokaisesta kaverista, joka liittyy Faktapisteeseen linkkisi kautta arvontakauden aikana ja kirjoittaa kauden aikana vähintään yhden arpaan kelpaavan kirjoituksen tai kommentin. Kutsuarpoja voi saada enintään 10 kaverista kautta kohden. Omien tai keksittyjen tilien kutsuminen on kielletty, ja ylläpitäjä hylkää tällaiset arvat ja voi sulkea tilit. Kutsuarpoja ei anneta, jos kutsuttu tili on luotu samalla laitteella tai selaimella kuin kutsujan tili tai toisen kutsutun tili.</li>
<li><b>Yksi henkilö, yksi tili:</b> kukin saa osallistua vain yhdellä tilillä. Kertakäyttöisillä sähköpostiosoitteilla ei voi liittyä. Väärinkäytösten havaitsemiseksi Faktapiste tallentaa tunnisteet laitteesta ja verkosta salattuna tiivisteenä (<a href="/tietoa/#valetilit">tietosuoja</a>).</li>
<li><b>Ei roskapostia:</b> poistetut tai sääntöjen vastaiset kirjoitukset eivät ole arpoja. Jos kirjoitat pelkästään arpojen keräämiseksi merkityksetöntä, toistuvaa tai kopioitua tekstiä, menetät sen päivän kaikki arvat. Toistuvasta roskapostituksesta menetät koko arvontakauden arvat. Tekoäly merkitsee epäilyttävät viestit, mutta arpoja ei poisteta automaattisesti: ylläpitäjä tarkistaa tilanteen ja tekee päätöksen. Tavallinen keskustelu ja lyhyetkin aidot kommentit ovat aina sallittuja. Ylläpitäjä voi sulkea tilin, joka rikkoo keskustelun sääntöjä.</li>
<li><b>Arvonta:</b> voittaja arvotaan sattumanvaraisesti tietokoneella. Jokaisen osallistujan voittomahdollisuus on suhteessa hänen arpojensa määrään. Sama henkilö voi voittaa useamman arvonnan.</li>
<li><b>Voittajalle ilmoittaminen:</b> voittajalle ilmoitetaan sähköpostilla siihen osoitteeseen, jolla hän kirjautuu Faktapisteeseen. Voittajan etunimi julkaistaan Faktapisteessä. Jos voittaja ei vastaa 14 päivässä, voittaja arvotaan uudelleen.</li>
<li><b>Voittajan tarkistus:</b> ylläpitäjä tarkistaa ennen palkinnon antamista, että voittaja on noudattanut sääntöjä. Voittajan on pyydettäessä osoitettava, että hänen nimensä Faktapisteessä on hänen oikea nimensä. Rahapalkinto maksetaan vain voittajan omissa nimissä olevalle pankkitilille. Jos voittaja on rikkonut sääntöjä (esimerkiksi useita tilejä tai valetilejä), voitto hylätään ja voittaja arvotaan uudelleen.</li>
<li><b>Palkinnot:</b> kuukausittain 100 euron K-ryhmän lahjakortti, jota ei voi vaihtaa rahaksi, sekä ison arvonnan palkinto (100, 250 tai 500 euroa käyttäjämäärän mukaan), jonka voittaja valitsee joko tilisiirtona tai K-ryhmän lahjakorttina. Järjestäjä maksaa arpajaisveron, joten palkinto on voittajalle verovapaa.</li>
<li><b>Tietosuoja:</b> arvonnassa käytetään Faktapisteeseen tallennettuja tietoja (nimi, sähköposti, kirjoitusten määrä sekä väärinkäytösten estoon tallennetut laite- ja verkkotiivisteet). Voittajalta pyydetään lisäksi palkinnon toimittamiseen tarvittavat tiedot. Tietoja ei luovuteta eteenpäin. Lisätietoja <a href="/tietoa/#valetilit">tietosuojaselosteessa</a>.</li>
<li>Arvonta ei ole K-ryhmän (Kesko), Metan, X:n tai minkään muun yrityksen järjestämä tai sponsoroima, eikä se liity niihin.</li>
</ul>
<p><a class="nappi" href="/">Kirjoita keskusteluun →</a></p>
</section>"""
kirjoita("/arvonta/", sivu("/arvonta/", "Arvonnat: 100 € joka kuukausi ja jopa 500 € | Faktapiste", "Faktapiste arpoo joka kuukausi 100 euron K-ryhmän lahjakortin ja lisäksi jopa 500 euroa käyttäjämäärän mukaan. Säännöt ja ehdot.", ARVONTA_RUNKO))
kirjoita("/tietoa/", sivu("/tietoa/", "Tietoa ja tietosuoja | Faktapiste", "Mikä Faktapiste on, kuka sitä ylläpitää, keskustelun säännöt, tietosuoja ja käyttöehdot.", runko))

# ---- Yksityisyysvahti ----
ANDROID = [
    ("Rajaa sovellusten sijaintilupa", "Asetukset → Sijainti → Sovellusten sijaintiluvat. Käy läpi lista ja valitse jokaiselle <b>Ei sallittu</b> tai <b>Salli vain käytön aikana</b>. Sijaintia tarvitsevat yleensä vain kartat, navigointi ja taksi- tai kuljetussovellukset."),
    ("Poista tarkka sijainti", "Avaa sovellus samasta listasta ja sammuta <b>Käytä tarkkaa sijaintia</b>. Esimerkiksi sääsovellukselle riittää likimääräinen sijainti."),
    ("Poista mainostunniste", "Asetukset → Tietosuoja ja suojaus (joissain puhelimissa Google → Kaikki palvelut) → Mainokset → <b>Poista mainostunnus</b>. Tunnisteella eri sovellusten keräämät tiedot yhdistetään sinuun."),
    ("Tarkista sijaintihistoria", "Asetukset → Sijainti → Sijaintipalvelut → <b>Aikajana</b> (aiemmin Googlen sijaintihistoria). Sammuta se tai poista tallennetut tiedot, jos et käytä sitä."),
    ("Katso, mitkä sovellukset ovat käyttäneet sijaintia", "Asetukset → Tietosuoja ja suojaus → <b>Yksityisyyden hallintapaneeli</b> (Privacy dashboard). Näet, mikä sovellus on käyttänyt sijaintia viimeisen vuorokauden aikana."),
    ("Poista sovellukset, joita et käytä", "Vanha peli tai sääsovellus voi kerätä sijaintia taustalla, vaikka et avaisi sitä. Poista turhat sovellukset kokonaan."),
]
IPHONE = [
    ("Estä sovelluksia seuraamasta sinua", "Asetukset → Tietosuoja ja turvallisuus → Seuranta → sammuta <b>Salli appien pyytää seurantaa</b>. Jos olet aiemmin antanut lupia, valitse <b>Pyydä appeja lopettamaan seuranta</b>."),
    ("Rajaa sovellusten sijaintilupa", "Asetukset → Tietosuoja ja turvallisuus → Sijaintipalvelut. Käy läpi lista ja valitse jokaiselle <b>Ei koskaan</b> tai <b>Käytettäessä appia</b>. Vältä vaihtoehtoa <b>Aina</b>."),
    ("Poista tarkka sijainti", "Avaa sovellus samasta listasta ja sammuta <b>Tarkka sijainti</b>. Esimerkiksi sääsovellukselle riittää likimääräinen sijainti."),
    ("Tarkista merkittävät sijainnit", "Sijaintipalvelut → Järjestelmäpalvelut → <b>Merkittävät sijainnit</b>. Sammuta, jos et tarvitse, ja tyhjennä historia."),
    ("Katso, mitkä sovellukset ovat käyttäneet sijaintia", "Asetukset → Tietosuoja ja turvallisuus → <b>Appien tietosuojaraportti</b>. Näet, mitkä sovellukset ovat käyttäneet sijaintia ja milloin."),
    ("Poista sovellukset, joita et käytä", "Vanha peli tai sääsovellus voi kerätä sijaintia, vaikka et avaisi sitä. Poista turhat sovellukset kokonaan."),
]
RISKI = [
    ("Sää- ja taskulamppusovellukset", "Tarvitsevat harvoin tarkkaa sijaintia, mutta pyytävät sitä usein."),
    ("Ilmaiset pelit", "Rahoitetaan usein mainoksilla, joihin liittyy sijainti- ja mainostunnistedataa."),
    ("Liikunta- ja juoksusovellukset", "Tallentavat reitit; tarkista, ovatko reitit julkisia ja mihin tietoja jaetaan."),
    ("Kauppojen ja tarjousten sovellukset", "Voivat seurata, missä liikkeissä käyt."),
    ("Sovellukset, joilla on lupa <b>Aina</b>", "Keräävät sijaintia myös silloin, kun sovellus on kiinni."),
]
def askeleet(lista, tunnus):
    return "".join(f'<li><label class="yv-ask"><input type="checkbox" data-yv="{tunnus}{i}"><span><b>{otsikko}</b><small>{teksti}</small></span></label></li>' for i, (otsikko, teksti) in enumerate(lista))
runko = f"""<section class="hero pieni"><div class="w">
<p class="eyebrow">Yksityisyysvahti</p>
<h1>Onko sijaintisi <span class="hl">myynnissä?</span></h1>
<p class="lead">Helsingin Sanomien selvityksen mukaan lähes 800 000 suomalaisen puhelimen paikannustietoja oli hankittavissa datamarkkinoilta. Tiedoista selviää, missä asut, missä käyt töissä ja missä vietät vapaa-aikaasi. Tieto kertyy tavallisista sovelluksista, ja lupa annetaan usein huomaamatta. Näin suljet hanat muutamassa minuutissa.</p>
</div></section>
<section class="w yv">
<h2 class="osio">1. Sammuta seuranta puhelimestasi</h2>
<div class="yv-valinta" role="tablist"><button type="button" class="nappi" data-yvtab="a" aria-pressed="true">Android</button><button type="button" class="nappi toissijainen" data-yvtab="i" aria-pressed="false">iPhone</button></div>
<p class="yv-edistys"><span class="tpb"><i id="yv-palkki"></i></span> <span id="yv-luku">0 / 6 tehty</span></p>
<ol class="yv-lista" id="yv-a">{askeleet(ANDROID, "a")}</ol>
<ol class="yv-lista" id="yv-i" hidden>{askeleet(IPHONE, "i")}</ol>
<p class="pieni mute">Valikoiden nimet voivat vaihdella puhelinmallin ja käyttöjärjestelmän version mukaan. Rastit tallentuvat vain tähän selaimeen.</p>

<h2 class="osio">2. Tunnista riskisovellukset</h2>
<p>Sijaintitietoa kertyy sovelluksista, joiden et ehkä edes muista olevan puhelimessasi. Tarkista erityisesti nämä:</p>
<ul class="lista">{''.join(f"<li><b>{a}.</b> {b}</li>" for a, b in RISKI)}</ul>

<h2 class="osio">3. Pyydä tietojesi poistoa</h2>
<p>EU:n tietosuoja-asetuksen nojalla voit kysyä yritykseltä, mitä tietoja sillä on sinusta, ja vaatia niiden poistamista. Yrityksen on vastattava kuukauden kuluessa. Yrityksen yhteystiedon löydät sovelluksen tietosuojaselosteesta, yleensä sovelluskaupan sivulta.</p>
<form id="yv-kirje" class="yv-kirje">
<label>Yrityksen tai sovelluksen nimi<input name="yritys" required placeholder="esim. Sääsovellus Oy"></label>
<label>Oma nimesi<input name="nimi" required autocomplete="name"></label>
<label>Sähköpostisi, jolla olet käyttänyt palvelua<input name="email" type="email" autocomplete="email"></label>
<label>Puhelimen mainostunniste (vapaaehtoinen)<input name="maid" placeholder="esim. 38400000-8cf0-11bd-b23e-10b96e40000d"></label>
<fieldset><legend>Mitä pyydät</legend>
<label class="rasti"><input type="checkbox" name="p15" checked> Kerro, mitä tietoja minusta on ja kenelle niitä on luovutettu</label>
<label class="rasti"><input type="checkbox" name="p17" checked> Poista tietoni</label>
<label class="rasti"><input type="checkbox" name="p7" checked> Peruutan suostumukseni sijaintitietojen käyttöön ja luovuttamiseen</label>
<label class="rasti"><input type="checkbox" name="p21" checked> Vastustan tietojeni käyttöä markkinointiin ja profilointiin</label></fieldset>
<button class="nappi">Luo viesti</button></form>
<div id="yv-tulos" hidden><textarea id="yv-teksti" rows="16" readonly></textarea>
<div class="rivi"><button type="button" class="nappi" id="yv-kopioi">Kopioi viesti</button><a class="nappi toissijainen" id="yv-posti" href="#">Avaa sähköpostissa</a></div>
<p class="pieni mute">Viestipohja on yleistä tietoa, ei oikeudellista neuvontaa. Jos yritys ei vastaa kuukauden kuluessa, voit tehdä ilmoituksen tietosuojavaltuutetun toimistoon osoitteessa tietosuoja.fi.</p></div>
</section>
<section class="w yv yv-varoita"><h2>Varoita läheistä</h2>
<p>Moni ei tiedä, että sääsovellus tai ilmainen peli voi myydä sijainnin eteenpäin. Lähetä vinkki perheelle tai kaverille – se vie viisi sekuntia.</p>
<button type="button" class="nappi" id="yv-jaa">📲 Lähetä vinkki</button></section>
<script>(function(){{
document.getElementById("yv-jaa").onclick=function(){{var t="Tiesitkö, että lähes 800 000 suomalaisen sijaintitietoja on päätynyt myyntiin sovellusten kautta? Tällä estät sen omasta puhelimesta muutamassa minuutissa:",u="https://faktapiste.fi/yksityisyys/";if(navigator.share)navigator.share({{text:t,url:u}}).catch(function(){{}});else location.href="https://wa.me/?text="+encodeURIComponent(t+" "+u)}};
var tab="a";try{{tab=localStorage.getItem("yv_tab")||"a"}}catch(e){{}}
function lue(k){{try{{return localStorage.getItem(k)}}catch(e){{return null}}}}function kirj(k,v){{try{{localStorage.setItem(k,v)}}catch(e){{}}}}
function paivita(){{var l=document.querySelectorAll("#yv-"+tab+" input"),n=0;l.forEach(function(x){{if(x.checked)n++}});document.getElementById("yv-luku").textContent=n+" / "+l.length+" tehty"+(n===l.length?" – hienoa!":"");document.getElementById("yv-palkki").style.width=(100*n/l.length)+"%"}}
function nayta(t){{tab=t;kirj("yv_tab",t);document.getElementById("yv-a").hidden=t!=="a";document.getElementById("yv-i").hidden=t!=="i";document.querySelectorAll("[data-yvtab]").forEach(function(b){{var on=b.dataset.yvtab===t;b.setAttribute("aria-pressed",on);b.className="nappi"+(on?"":" toissijainen")}});paivita()}}
document.querySelectorAll("[data-yv]").forEach(function(x){{x.checked=lue("yv_"+x.dataset.yv)==="1";x.addEventListener("change",function(){{kirj("yv_"+x.dataset.yv,x.checked?"1":"0");paivita()}})}});
document.querySelectorAll("[data-yvtab]").forEach(function(b){{b.onclick=function(){{nayta(b.dataset.yvtab)}}}});
if(/iphone|ipad/i.test(navigator.userAgent)&&!lue("yv_tab"))tab="i";nayta(tab);
document.getElementById("yv-kirje").addEventListener("submit",function(e){{e.preventDefault();var f=e.target,y=f.yritys.value.trim(),n=f.nimi.value.trim(),em=f.email.value.trim(),m=f.maid.value.trim(),p=[];
if(f.p15.checked)p.push("Pyydän tietosuoja-asetuksen 15 artiklan nojalla tiedon siitä, mitä henkilötietoja minusta käsittelette, mihin tarkoitukseen, mistä tiedot on saatu ja kenelle niitä on luovutettu. Pyydän myös jäljennöksen tiedoista.");
if(f.p17.checked)p.push("Pyydän tietosuoja-asetuksen 17 artiklan nojalla, että poistatte kaikki minua koskevat henkilötiedot, mukaan lukien sijaintitiedot, ja ilmoitatte poistosta myös niille, joille tietoja on luovutettu (19 artikla).");
if(f.p7.checked)p.push("Peruutan tietosuoja-asetuksen 7 artiklan 3 kohdan nojalla kaikki antamani suostumukset sijaintitietojeni keräämiseen, käyttöön ja luovuttamiseen.");
if(f.p21.checked)p.push("Vastustan tietosuoja-asetuksen 21 artiklan nojalla tietojeni käsittelyä suoramarkkinointiin ja profilointiin.");
var t="Aihe: Tietosuojapyyntö – "+n+"\\n\\nHei,\\n\\nolen käyttänyt palveluanne "+y+"."+(em?" Käyttämäni sähköpostiosoite on "+em+".":"")+(m?" Puhelimeni mainostunniste on "+m+".":"")+"\\n\\n"+p.join("\\n\\n")+"\\n\\nPyydän vastaamaan tietosuoja-asetuksen 12 artiklan mukaisesti viimeistään kuukauden kuluessa tämän viestin vastaanottamisesta.\\n\\nYstävällisin terveisin\\n"+n+(em?"\\n"+em:"");
document.getElementById("yv-teksti").value=t;var R=document.getElementById("yv-tulos");R.hidden=false;
document.getElementById("yv-posti").href="mailto:?subject="+encodeURIComponent("Tietosuojapyyntö – "+n)+"&body="+encodeURIComponent(t.replace(/^Aihe:.*\\n\\n/,""));R.scrollIntoView({{behavior:"smooth"}})}});
document.getElementById("yv-kopioi").onclick=function(){{var t=document.getElementById("yv-teksti");t.select();try{{navigator.clipboard.writeText(t.value)}}catch(e){{document.execCommand("copy")}}this.textContent="Kopioitu!"}};
}})()</script>"""
kirjoita("/yksityisyys/", sivu("/yksityisyys/", "Yksityisyysvahti – onko sijaintisi myynnissä? | Faktapiste",
    "Sammuta puhelimesi sijainti- ja mainosseuranta Androidissa ja iPhonessa ja pyydä yrityksiä poistamaan tietosi valmiilla viestipohjalla.", runko))

(ROOT / "404.html").write_text(sivu("/404", "Sivua ei löytynyt | Faktapiste", "Sivua ei löytynyt.",
    '<section class="w teksti"><h1>Sivua ei löytynyt</h1><p><a href="/">Takaisin etusivulle</a></p></section>', noindex=True), encoding="utf-8")

(ROOT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#160a26"/><text x="32" y="30" font-family="Anton,Impact,sans-serif" font-size="17" fill="#fff" text-anchor="middle">FAKTA</text><text x="32" y="48" font-family="Anton,Impact,sans-serif" font-size="17" fill="#f5c542" text-anchor="middle">PISTE.</text></svg>', encoding="utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + "".join(f"<url><loc>{SITE}{p}</loc></url>" for p in ["/", "/palvelut/", "/tietoa/", "/yksityisyys/", "/arvonta/"]) + "</urlset>", encoding="utf-8")
print("Faktapiste rakennettu:", ROOT)
