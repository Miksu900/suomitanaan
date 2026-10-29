"""Yhteinen tietosuojaselosteen runko (EU:n tietosuoja-asetus 2016/679, 13 art.) Miikan sivustoille.
Käyttö: from tietosuoja import seloste; html = seloste(palvelu=..., rekisterinpitaja=..., yhteys=..., tiedot=[...], ...)"""
import html as _h

def _e(s): return _h.escape(str(s), quote=True)

def seloste(palvelu, rekisterinpitaja, yhteys, tiedot, tarkoitus, kasittelijat, sailytys, evasteet, paivitetty="29.10.2026", lisa=""):
    """tiedot/kasittelijat: lista (otsikko, teksti). Palauttaa <article>-HTML:n (ei sivupohjaa)."""
    li = lambda xs: "<ul>" + "".join(f"<li><b>{_e(a)}</b> – {_e(b)}</li>" for a, b in xs) + "</ul>"
    return f"""<article class="tietosuoja"><h1>Tietosuojaseloste</h1>
<p><i>{_e(palvelu)} · EU:n yleisen tietosuoja-asetuksen (2016/679) 13 artikla · päivitetty {_e(paivitetty)}</i></p>
<h2>1. Rekisterinpitäjä</h2><p>{_e(rekisterinpitaja)}<br>Yhteydenotot tietosuoja-asioissa: <a href="mailto:{_e(yhteys)}">{_e(yhteys)}</a></p>
<h2>2. Mitä tietoja käsitellään</h2>{li(tiedot)}
<h2>3. Käsittelyn tarkoitus ja oikeusperuste</h2><p>{_e(tarkoitus)}</p>
<h2>4. Palveluntarjoajat ja tietojen siirrot</h2><p>Tietoja ei myydä eikä luovuteta markkinointiin. Palvelun toteuttamisessa käytetään seuraavia palveluntarjoajia, jotka käsittelevät tietoja rekisterinpitäjän lukuun:</p>{li(kasittelijat)}
<p>Osa palveluntarjoajista voi käsitellä tietoja myös EU:n ja ETA-alueen ulkopuolella. Tällöin siirto perustuu Euroopan komission hyväksymiin vakiolausekkeisiin tai muuhun tietosuoja-asetuksen mukaiseen siirtoperusteeseen.</p>
<h2>5. Säilytysaika</h2><p>{_e(sailytys)}</p>
<h2>6. Evästeet ja selaimen tallennus</h2><p>{_e(evasteet)}</p>
{lisa}
<h2>7. Sinun oikeutesi</h2><p>Sinulla on oikeus saada tietää, mitä tietoja sinusta käsitellään, sekä pyytää tietojen oikaisemista tai poistamista, vastustaa käsittelyä, rajoittaa sitä ja saada tietosi siirretyksi. Jos käsittely perustuu suostumukseen, voit perua sen milloin tahansa. Pyynnöt voi lähettää sähköpostilla yllä olevaan osoitteeseen, ja niihin vastataan kuukauden kuluessa.</p>
<p>Jos katsot, että tietojasi käsitellään lainvastaisesti, voit tehdä valituksen tietosuojavaltuutetun toimistolle (<a href="https://tietosuoja.fi">tietosuoja.fi</a>).</p>
</article>"""
