"""Faktapiste.fi – kattosivusto. Rakentaa staattiset sivut kansioon public/.

Etusivu esittelee kaikki palvelut. /palvelut/ on mainoksiin sopiva versio ilman poliittisia palveluita.
Aja: python3 faktapiste/rakenna.py
"""
import os, html, datetime, pathlib

ROOT = pathlib.Path(__file__).parent / "public"
SITE = os.environ.get("FAKTAPISTE_URL", "https://faktapiste.fi")
PV = os.environ.get("PYKALAVAHTI_URL", "https://pykalavahti.fi")
YHTEYS = "miika@eduskuntaseuranta.fi"
VER = "7"
esc = html.escape

# avain, nimi, osoite, iskulause, kuvaus, merkki, poliittinen
PALVELUT = [
    ("kv", "Keräysvahti", "https://keraysvahti.fi", "Onko keräyksellä lupa?",
     "Tarkista ennen lahjoittamista, onko rahankeräyksellä poliisin lupa ja kuuluuko tilinumero oikealle järjestölle. Haku kattaa kaikki voimassa olevat luvat.",
     "Ilmainen haku", False),
    ("hj", "Huijausapu", "https://keraysvahti.fi/huijaukset/", "Epäiletkö huijausta?",
     "Tunnista tavallisimmat huijaukset, tarkista epäilyttävä viesti ja katso, mitä tehdä heti, jos rahaa on jo mennyt.",
     "Viestintarkistin", False),
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
<meta name="theme-color" content="#0d1b3e">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"Faktapiste","url":"{SITE}/","logo":"{SITE}/og.png","email":"{YHTEYS}","description":"Ilmaisia palveluita julkisista lähteistä: Keräysvahti, Pykälävahti, Korjausvahti, Nytpuhutaan ja Eduskuntaseuranta."}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/tyyli.css?v={VER}">
</head><body>
<a class="skip" href="#sisalto">Siirry sisältöön</a>
<header class="hd"><div class="w hdw"><a class="brand" href="/" aria-label="Faktapiste – etusivu">{LOGO}</a><nav aria-label="Päävalikko">{navh}{tili}</nav></div></header>
<main id="sisalto">{runko}</main>
<footer class="ft"><div class="w">{LOGO}
<p>Faktapiste kokoaa yhteen ilmaisia palveluita, jotka perustuvat julkisiin lähteisiin: poliisin lupatietoihin, Finlexiin, eduskunnan avoimeen dataan ja uutismedian otsikoihin.</p>
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
<div id="fp-opastus"></div>
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
<p>Faktapiste on yksityinen, puolueeton avoimuushanke, joka kokoaa yhteen julkisiin lähteisiin perustuvia palveluita. Palvelut eivät ole viranomaisen palveluita, eivätkä ne liity poliisiin, Finlexiin, oikeusministeriöön tai eduskuntaan.</p>
<h2>Ylläpitäjä</h2>
<p>Miika Koskela, Ylivieska. Yhteys: <span class="mono">{YHTEYS}</span>.</p>
<h2>Tietosuoja</h2>
<p>Palveluiden sivut eivät käytä seurantaevästeitä eivätkä mainosseurantaa. Sivusto toimii Cloudflaren palvelussa, joka voi tallentaa teknisiä lokitietoja (kuten IP-osoitteen) palvelun toiminnan ja turvallisuuden vuoksi. Fontit ladataan Googlen Fonts-palvelusta. Kunkin palvelun omat tietosuojatiedot löytyvät palvelun sivuilta.</p>
<p><b>Keskustelu.</b> Jos kirjaudut keskusteluun, tallennamme sähköpostiosoitteesi, nimimerkkisi, postauksesi, tykkäyksesi ja ilmoituksesi. Sähköpostiosoitetta käytetään vain kirjautumislinkkien lähettämiseen, eikä sitä näytetä muille. Kirjautuminen käyttää yhtä välttämätöntä evästettä (fp_s), joka pitää sinut kirjautuneena 60 päivää. Lukukertojen laskemiseen (taattu yleisö ja syötteen loppuminen) selain tallentaa satunnaisen lukijatunnisteen, jonka avulla palvelin muistaa, mitkä postaukset olet jo nähnyt. Tunnistetta ei yhdistetä henkilöön eikä käytetä mainontaan, ja tieto poistuu muutamassa päivässä. Syötteen säädöt ja paikkakunta tallentuvat vain selaimeesi. Kirjautumisviestit lähetetään Brevo-palvelun kautta. Postaukset tarkistetaan julkaisuhetkellä automaattisesti tekoälyllä (Anthropic) selvästi lainvastaisen sisällön varalta, ja faktahaut käsitellään samalla tavalla. Tietoja ei myydä eikä käytetä mainontaan. Voit pyytää tilisi ja tietojesi poistamista osoitteesta <span class="mono">{YHTEYS}</span>.</p>
<h2 id="keskustelu">Keskustelun säännöt</h2>
<ul>
<li>Saa olla eri mieltä, kritisoida kovasti ja kirjoittaa kärkevästi, myös päättäjistä ja puolueista.</li>
<li>Kiellettyä on väkivallalla uhkaaminen, yksityishenkilöiden henkilötietojen levittäminen, kiihottaminen kansanryhmää vastaan, kunnianloukkaus, lapsia seksualisoiva sisältö sekä mainostus ja huijaukset.</li>
<li>Kirjoittaja vastaa itse kirjoituksestaan. Postaukset julkaistaan heti, ja selvästi lainvastaiset estetään automaattisesti.</li>
<li>Jokaisessa postauksessa on Ilmoita-toiminto. Kun kolme käyttäjää on ilmoittanut postauksesta, se piilotetaan tarkistusta varten. Ylläpitäjä poistaa lainvastaisen sisällön viipymättä ja voi sulkea sääntöjä rikkovan tilin.</li>
<li>Ilmoituksen voi tehdä myös sähköpostilla osoitteeseen <span class="mono">{YHTEYS}</span>. Kerro postauksen linkki ja syy.</li>
<li>Syötteen järjestys: Sinulle-näkymä näyttää ensin uudet postaukset, joita ei ole vielä nähnyt 30 lukijaa (taattu yleisö), ja sen jälkeen tykkäysten, vastausten ja tuoreuden mukaan. Näkymä näyttää vain sellaista, mitä et ole vielä nähnyt, ja loppuu, kun tärkeimmät on katsottu. Voit säätää, paljonko näet keskusteluja, uutisia, otsikkomuutoksia, huijausvaroituksia ja päätöksiä, ja jokaisessa postauksessa kerrotaan, miksi näet sen. Uusimmat-näkymä on aikajärjestyksessä ja Lähellä-näkymä näyttää valitsemasi paikkakunnan postaukset ja uutiset. Automaattinen sisältö tulee Faktapisteen omista palveluista (Suomi Tänään, Korjausvahti, Eduskuntaseuranta, Keräysvahti) ja on merkitty.</li>
<li>Faktahaun vastaukset kokoaa tekoäly eduskunnan avoimesta datasta. Ne voivat sisältää virheitä, joten tarkista tärkeät asiat lähteestä.</li>
</ul>
<h2>Käyttöehdot</h2>
<p>Palvelut ovat tällä hetkellä maksuttomia. Ylläpitäjä pidättää oikeuden muuttaa palveluita ja niiden ehtoja sekä ottaa käyttöön maksullisia ominaisuuksia; muutoksista kerrotaan etukäteen. Tiedot ovat yleistä tietoa eivätkä oikeudellista tai taloudellista neuvontaa.</p>
</section>"""
kirjoita("/tietoa/", sivu("/tietoa/", "Tietoa ja tietosuoja | Faktapiste", "Kuka ylläpitää Faktapistettä, tietosuoja, keskustelun säännöt ja käyttöehdot.", runko))

(ROOT / "404.html").write_text(sivu("/404", "Sivua ei löytynyt | Faktapiste", "Sivua ei löytynyt.",
    '<section class="w teksti"><h1>Sivua ei löytynyt</h1><p><a href="/">Takaisin etusivulle</a></p></section>', noindex=True), encoding="utf-8")

(ROOT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#0d1b3e"/><text x="32" y="30" font-family="Anton,Impact,sans-serif" font-size="17" fill="#fff" text-anchor="middle">FAKTA</text><text x="32" y="48" font-family="Anton,Impact,sans-serif" font-size="17" fill="#f5c542" text-anchor="middle">PISTE.</text></svg>', encoding="utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + "".join(f"<url><loc>{SITE}{p}</loc></url>" for p in ["/", "/palvelut/", "/tietoa/"]) + "</urlset>", encoding="utf-8")
print("Faktapiste rakennettu:", ROOT)
