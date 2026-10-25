"""Netvo – myynti- ja ehtosivu sekä mallisivujen galleria. Oma brändi, erillään Faktapisteesta.

Reiluus on kärki: selkeä hinta, oma domain asiakkaalle, keskeytys 2 kk maksulla, ei loukkua.
"""
import html, pathlib
from .malli import sivu as mallisivu
from .data import DEMOT

esc = html.escape
YHTEYS = "miika@eduskuntaseuranta.fi"

HINTA_KK = 19
SITOUTUS = "12 tai 24 kuukautta"
SAKKO_KK = 2


def _demokortti(d):
    kauppa = d.get("tyyppi") == "kauppa"
    merkki = "Verkkokauppa" if kauppa else d["ala"]
    return f"""<a class="malli" href="/netvo/mallit/{d['slug']}/" target="_blank" rel="noopener">
<span class="malli-kuva teema-{d.get('teema','sininen')}"><b>{esc(d['nimi'])}</b><i>{esc(d.get('slogan',''))}</i></span>
<span class="malli-tieto"><span class="malli-ala">{esc(merkki)}</span>Katso malli →</span></a>"""


def _sivu(otsikko, kuvaus, runko):
    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}">
<meta name="robots" content="noindex">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}">
<style>
:root{{--p:#1557c0;--p2:#0e3a85;--ink:#17181c;--mute:#5b6069;--line:#e6e7ea;--pehmea:#eef3fc;--bg:#fff;--vihrea:#1f7a4d}}
*{{box-sizing:border-box}}
body{{margin:0;font:16px/1.65 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}}
.w{{max-width:1000px;margin:0 auto;padding:0 20px}}
a{{color:var(--p)}}
h1,h2,h3{{line-height:1.2;margin:0 0 .5em}}
header.top{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid var(--line)}}
.top .w{{display:flex;align-items:center;justify-content:space-between;height:66px}}
.logo{{font-weight:800;font-size:1.3rem;color:var(--p);text-decoration:none}}
.logo span{{color:var(--vihrea)}}
.nappi{{background:var(--p);color:#fff;text-decoration:none;font-weight:700;padding:11px 20px;border-radius:10px;display:inline-block}}
.nappi:hover{{background:var(--p2)}}
.nappi.iso{{padding:15px 28px;font-size:1.05rem}}
.hero{{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;padding:76px 0}}
.hero h1{{font-size:clamp(2.1rem,6vw,3.4rem);max-width:16ch}}
.hero p{{font-size:1.2rem;opacity:.95;max-width:44ch;margin:.4em 0 1.6em}}
.hero .alle{{margin-top:14px;font-size:.95rem;opacity:.9}}
.osio{{padding:60px 0}}
.osio h2{{font-size:clamp(1.6rem,4vw,2.2rem);text-align:center;margin-bottom:.8em}}
.askeleet{{display:grid;gap:22px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}}
.askel{{text-align:center;padding:10px}}
.askel .num{{width:46px;height:46px;border-radius:50%;background:var(--pehmea);color:var(--p);font-weight:800;font-size:1.2rem;display:flex;align-items:center;justify-content:center;margin:0 auto 14px}}
.hinnoittelu{{background:var(--pehmea)}}
.hintakortti{{max-width:460px;margin:0 auto;background:#fff;border:2px solid var(--p);border-radius:20px;padding:34px;text-align:center}}
.hintakortti .suuri{{font-size:3rem;font-weight:800;color:var(--p);line-height:1}}
.hintakortti .suuri small{{font-size:1.1rem;color:var(--mute);font-weight:600}}
.hintakortti .ilmainen{{display:inline-block;background:var(--vihrea);color:#fff;font-weight:700;padding:5px 14px;border-radius:999px;margin-bottom:14px}}
.hintakortti ul{{list-style:none;padding:0;margin:20px 0;text-align:left}}
.hintakortti li{{padding:8px 0 8px 30px;position:relative}}
.hintakortti li::before{{content:"✓";position:absolute;left:0;color:var(--vihrea);font-weight:800}}
.reilu{{background:var(--ink);color:#fff}}
.reilu h2{{color:#fff}}
.reilu .ruudut{{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-top:10px}}
.reilu .r{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:22px}}
.reilu .r h3{{color:#ffd24a;font-size:1.1rem}}
.reilu .r p{{color:#d4d6db;margin:0}}
.galleria{{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
.malli{{text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:block;transition:transform .15s}}
.malli:hover{{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.08)}}
.malli-kuva{{height:140px;display:flex;flex-direction:column;justify-content:center;align-items:center;color:#fff;text-align:center;padding:16px}}
.malli-kuva b{{font-size:1.3rem}}.malli-kuva i{{font-style:normal;opacity:.9;font-size:.9rem;margin-top:4px}}
.teema-sininen{{background:linear-gradient(135deg,#1557c0,#0e3a85)}}.teema-vihrea{{background:linear-gradient(135deg,#1f7a4d,#145535)}}
.teema-oranssi{{background:linear-gradient(135deg,#d9631a,#a84a11)}}.teema-musta{{background:linear-gradient(135deg,#333,#000)}}
.teema-viininpunainen{{background:linear-gradient(135deg,#9c2742,#6f1a2f)}}.teema-petroli{{background:linear-gradient(135deg,#116b74,#0b4a50)}}
.teema-ruskea{{background:linear-gradient(135deg,#7a5230,#553820)}}.teema-purppura{{background:linear-gradient(135deg,#5b3a9c,#3f286e)}}
.malli-tieto{{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;font-weight:700}}
.malli-ala{{color:var(--mute);font-weight:600;font-size:.88rem}}
.ukk details{{border-bottom:1px solid var(--line);padding:6px 0}}
.ukk summary{{cursor:pointer;font-weight:700;padding:12px 0;list-style:none}}
.ukk summary::-webkit-details-marker{{display:none}}
.ukk summary::before{{content:"+ ";color:var(--p)}}.ukk details[open] summary::before{{content:"– "}}
.ukk p{{color:var(--mute);margin:0 0 12px}}
.teksti{{max-width:720px;margin:0 auto}}
.teksti h2{{text-align:left;margin-top:1.4em}}
footer.jalka{{background:#0c0c0e;color:#9a9aa0;text-align:center;padding:30px 16px;font-size:.88rem}}
footer.jalka a{{color:#cfd0d4}}
.keskita{{text-align:center;margin-top:28px}}
</style></head>
<body>
<header class="top"><div class="w">
<a class="logo" href="/netvo/">Net<span>vo</span></a>
<a class="nappi" href="#yhteys">Ota yhteyttä</a>
</div></header>
{runko}
<footer class="jalka"><p><b>Netvo</b> – valmiit nettisivut suomalaisille yrityksille.</p>
<p>Yhteys: {esc(YHTEYS)} · <a href="/netvo/ehdot/">Sopimusehdot</a></p>
<p>Netvo on osa Faktapisteen palveluita.</p></footer>
</body></html>"""


def etusivu():
    palvelut = [d for d in DEMOT if d.get("tyyppi") != "kauppa"]
    kaupat = [d for d in DEMOT if d.get("tyyppi") == "kauppa"]
    runko = f"""
<section class="hero"><div class="w">
<h1>Ammattimaiset nettisivut yrityksellesi</h1>
<p>Saat valmiit, mobiilioptimoidut nettisivut ilman pystytysmaksua. Me teemme kaiken, sinä keskityt työhösi.</p>
<a class="nappi iso" href="#yhteys">Hanki sivut yrityksellesi</a>
<div class="alle">Pystytys 0 € · Oma verkkotunnus sinun nimiisi · Peru milloin vain {SAKKO_KK} kk maksulla</div>
</div></section>

<section class="osio"><div class="w"><h2>Näin se toimii</h2><div class="askeleet">
<div class="askel"><div class="num">1</div><h3>Kerro yrityksestäsi</h3><p>Täytät lyhyen lomakkeen: nimi, palvelut, yhteystiedot ja toiveesi väreistä.</p></div>
<div class="askel"><div class="num">2</div><h3>Me teemme sivut</h3><p>Rakennamme sivut puolestasi ja kirjoitamme tekstit valmiiksi. Näet vedoksen ja saat muutokset mukaan.</p></div>
<div class="askel"><div class="num">3</div><h3>Sivut julkaistaan</h3><p>Sivut tulevat nettiin omalla verkkotunnuksellasi. Me pidämme ne pystyssä ja ajan tasalla.</p></div>
</div></div></section>

<section class="osio hinnoittelu"><div class="w"><h2>Selkeä hinta, ei yllätyksiä</h2>
<div class="hintakortti">
<span class="ilmainen">Pystytys 0 €</span>
<div class="suuri">{HINTA_KK} €<small> / kk</small></div>
<p style="color:var(--mute);margin:6px 0 0">Sitoutuminen {SITOUTUS}, sitten jatkuu kuukausi kerrallaan.</p>
<ul>
<li>Valmiit sivut rakennettuna puolestasi</li>
<li>Oma verkkotunnus (esim. yrityksesi.fi) sinun nimiisi</li>
<li>Hosting, varmuuskopiot ja tietoturva</li>
<li>Pienet tekstimuutokset sisältyvät hintaan</li>
<li>Yhteydenottolomake suoraan sähköpostiisi</li>
<li>Toimii puhelimella, tabletilla ja tietokoneella</li>
</ul>
<a class="nappi iso" href="#yhteys">Aloita nyt</a>
</div></div></section>

<section class="osio reilu"><div class="w"><h2>Reilut ehdot – ei loukkua</h2>
<p style="text-align:center;color:#d4d6db;max-width:52ch;margin:0 auto">Moni "ilmainen sivu" -palvelu sitoo asiakkaan loukkuun. Me teemme toisin. Reiluus on lupauksemme.</p>
<div class="ruudut">
<div class="r"><h3>Oma verkkotunnus</h3><p>Verkkotunnus rekisteröidään sinun yrityksesi nimiin. Se on sinun, et jää siitä riippuvaiseksi meistä.</p></div>
<div class="r"><h3>Voit perua milloin vain</h3><p>Jos haluat lopettaa kesken sitoutumisajan, maksat vain {SAKKO_KK} kuukauden maksua vastaavan summan. Ei muuta.</p></div>
<div class="r"><h3>Ei automaattista kallistumista</h3><p>Sitoutumisajan jälkeen sopimus ei muutu kalliimmaksi, vaan jatkuu samalla hinnalla kuukausi kerrallaan.</p></div>
<div class="r"><h3>Selkeä hinta etukäteen</h3><p>Kerromme kaiken ennen kuin sitoudut mihinkään. Ei piilokuluja, ei pientä pränttiä.</p></div>
</div>
<p style="text-align:center;margin-top:24px"><a href="/netvo/ehdot/" style="color:#ffd24a;font-weight:700">Lue tarkat sopimusehdot →</a></p>
</div></section>

<section class="osio" id="mallit"><div class="w"><h2>Katso mallisivut</h2>
<p style="text-align:center;color:var(--mute);max-width:50ch;margin:0 auto 10px">Klikkaa mitä tahansa mallia nähdäksesi, miltä valmis sivusto näyttää. Omasi tehdään samalla laadulla, sinun sisällölläsi ja väreilläsi.</p>
<h3 style="margin-top:30px">Palvelualat</h3><div class="galleria">{''.join(_demokortti(d) for d in palvelut)}</div>
<h3 style="margin-top:34px">Verkkokaupat</h3><div class="galleria">{''.join(_demokortti(d) for d in kaupat)}</div>
</div></section>

<section class="osio" id="ukk"><div class="w teksti"><h2 style="text-align:center">Usein kysyttyä</h2><div class="ukk">
<details><summary>Onko pystytys oikeasti ilmainen?</summary><p>Kyllä. Et maksa sivujen tekemisestä mitään. Kuukausimaksu kattaa verkkotunnuksen, hostingin, ylläpidon ja pienet muutokset. Näin sivut pysyvät kunnossa koko ajan.</p></details>
<details><summary>Omistanko verkkotunnuksen itse?</summary><p>Kyllä. Verkkotunnus rekisteröidään sinun yrityksesi nimiin, ja se on sinun. Et jää meistä riippuvaiseksi.</p></details>
<details><summary>Mitä jos haluan lopettaa?</summary><p>Voit perua milloin vain. Jos lopetat kesken sitoutumisajan, maksat vain {SAKKO_KK} kuukauden maksua vastaavan summan. Sitoutumisajan jälkeen voit lopettaa ilman erillistä maksua.</p></details>
<details><summary>Voinko muuttaa sivujen sisältöä myöhemmin?</summary><p>Kyllä. Pienet tekstimuutokset, kuten aukioloajat, hinnat tai yhteystiedot, sisältyvät kuukausihintaan. Lähetät vain viestin, niin hoidamme ne.</p></details>
<details><summary>Saako verkkokaupan myös?</summary><p>Kyllä. Teemme myös yksinkertaisia verkkokauppoja tuotteiden esittelyyn ja tilaamiseen. Katso esimerkit mallisivuista.</p></details>
<details><summary>Kauanko sivujen tekeminen kestää?</summary><p>Yleensä muutaman päivän siitä, kun olet toimittanut tietosi. Saat vedoksen nähtäväksi ennen julkaisua.</p></details>
</div></div></section>

<section class="osio hinnoittelu" id="yhteys"><div class="w teksti" style="text-align:center">
<h2>Hanki nettisivut yrityksellesi</h2>
<p style="color:var(--mute);max-width:46ch;margin:0 auto 20px">Kerro lyhyesti yrityksestäsi, niin otamme yhteyttä ja kerromme lisää. Ei sitoumusta vielä tässä vaiheessa.</p>
<a class="nappi iso" href="mailto:{esc(YHTEYS)}?subject=Netvo%20-%20nettisivut%20yritykselleni">Lähetä sähköposti</a>
<p style="margin-top:16px;color:var(--mute)">tai sähköposti: <b>{esc(YHTEYS)}</b></p>
</div></section>
"""
    return _sivu("Netvo – valmiit nettisivut yrityksellesi ilman pystytysmaksua",
                 "Ammattimaiset nettisivut suomalaisille yrityksille. Pystytys 0 €, oma verkkotunnus, reilut ehdot. Peru milloin vain 2 kk maksulla.", runko)


def ehtosivu():
    runko = f"""<section class="osio"><div class="w teksti">
<h1>Sopimusehdot</h1>
<p style="color:var(--mute)">Nämä ehdot kuvaavat Netvo-palvelun sisällön ja hinnoittelun selkeästi ja reilusti. Ehdot täydentyvät tilauksen yhteydessä.</p>
<h2>1. Palvelun sisältö</h2>
<p>Netvo rakentaa asiakkaalle valmiit nettisivut ja pitää ne toiminnassa. Kuukausimaksu sisältää verkkotunnuksen, hostingin, varmuuskopiot, tietoturvan, yhteydenottolomakkeen ja pienet sisältömuutokset (kuten aukioloajat, hinnat ja yhteystiedot).</p>
<h2>2. Hinta</h2>
<p>Sivujen pystytys on maksuton. Palvelun kuukausihinta on {HINTA_KK} € (sis. alv). Hinta kerrotaan selkeästi ennen sopimuksen tekoa, eikä piilokuluja ole.</p>
<h2>3. Sitoutumisaika</h2>
<p>Asiakas valitsee sitoutumisajaksi {SITOUTUS}. Sitoutumisajan jälkeen sopimus jatkuu samalla hinnalla toistaiseksi, kuukauden irtisanomisajalla. Hinta ei nouse automaattisesti sitoutumisajan päättyessä.</p>
<h2>4. Palvelun keskeyttäminen kesken sitoutumisajan</h2>
<p>Asiakas voi lopettaa palvelun milloin tahansa myös kesken sitoutumisajan. Tällöin asiakas maksaa keskeytyksestä {SAKKO_KK} kuukauden maksua vastaavan summan, ei enempää. Tämä korvaa jäljellä olevan sitoutumisajan. Mitään muuta maksua ei peritä.</p>
<h2>5. Verkkotunnus</h2>
<p>Verkkotunnus (domain) rekisteröidään asiakkaan tai asiakkaan yrityksen nimiin, ja se on asiakkaan omaisuutta. Sopimuksen päättyessä asiakas voi siirtää verkkotunnuksen toiselle palveluntarjoajalle.</p>
<h2>6. Sivujen sisältö ja vastuu</h2>
<p>Asiakas vastaa toimittamiensa tietojen ja kuvien oikeellisuudesta ja siitä, että niillä on oikeus julkaista ne. Netvo vastaa sivujen teknisestä toiminnasta ja ylläpidosta.</p>
<h2>7. Sopimuksen päättyminen</h2>
<p>Sopimuksen päättyessä sivut poistetaan verkosta. Asiakas voi halutessaan pyytää sivujen sisällön itselleen. Verkkotunnus jää asiakkaalle.</p>
<p style="color:var(--mute);margin-top:30px">Kysymyksiä ehdoista? Ota yhteyttä: {esc(YHTEYS)}</p>
<p class="keskita"><a class="nappi" href="/netvo/">← Takaisin etusivulle</a></p>
</div></section>"""
    return _sivu("Sopimusehdot – Netvo", "Netvo-palvelun selkeät ja reilut sopimusehdot: hinta, sitoutumisaika ja keskeytys.", runko)


def rakenna_nettikoti(root):
    """Kirjoittaa Netvo-sivut kansioon <root>/netvo/."""
    root = pathlib.Path(root)
    (root / "netvo").mkdir(parents=True, exist_ok=True)
    (root / "netvo" / "index.html").write_text(etusivu(), encoding="utf-8")
    (root / "netvo" / "ehdot").mkdir(exist_ok=True)
    (root / "netvo" / "ehdot" / "index.html").write_text(ehtosivu(), encoding="utf-8")
    for d in DEMOT:
        kansio = root / "netvo" / "mallit" / d["slug"]
        kansio.mkdir(parents=True, exist_ok=True)
        (kansio / "index.html").write_text(mallisivu(d), encoding="utf-8")
    return len(DEMOT)
