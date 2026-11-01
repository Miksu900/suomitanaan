"""Yleistä tietoa -ohjesivut (SEO/GEO). Vain yleistä tietoa laista, ei neuvontaa yksittäistapaukseen."""
import json, html
esc = lambda s: html.escape(str(s), quote=True)

SIVUT = [
    ("reklamaatio", "Reklamaatio – mitä kuluttajansuojalaki sanoo?",
     "Yleistä tietoa reklamaatiosta: milloin virheestä pitää ilmoittaa, mitä myyjältä voi vaatia ja mistä saa maksutonta apua.",
     "Reklamaatio tarkoittaa ilmoitusta myyjälle tuotteen virheestä. Kuluttajansuojalain mukaan virheestä pitää ilmoittaa kohtuullisessa ajassa sen havaitsemisesta, ja kahden kuukauden kuluessa tehty ilmoitus on aina ajoissa.",
     [("Mikä on reklamaatio?", "Reklamaatio on ilmoitus myyjälle siitä, että ostettu tavara tai palvelu on virheellinen. Kuluttajakaupassa tavaran virheestä säädetään kuluttajansuojalain 5 luvussa."),
      ("Kuinka nopeasti virheestä pitää ilmoittaa?", "Virheestä on ilmoitettava myyjälle kohtuullisessa ajassa siitä, kun virhe havaittiin tai se olisi pitänyt havaita. Kuluttajansuojalain mukaan kuluttaja saa aina vedota virheeseen, jos hän ilmoittaa siitä kahden kuukauden kuluessa havaitsemisesta."),
      ("Mitä myyjältä voi vaatia?", "Ensisijainen keino on virheen oikaisu eli korjaus tai virheettömän tavaran toimittaminen. Jos oikaisu ei onnistu, kuluttaja voi vaatia hinnanalennusta tai, jos virhe ei ole vähäinen, kaupan purkua. Lisäksi kuluttajalla voi olla oikeus pidättää maksu ja saada vahingonkorvausta."),
      ("Miten reklamaatio kannattaa tehdä?", "Tee ilmoitus kirjallisesti, esimerkiksi sähköpostilla, jotta siitä jää todiste. Kerro, mitä ostit ja milloin, mikä virhe on ja mitä vaadit. Säilytä kuitti ja kuvat virheestä."),
      ("Mistä saa maksutonta apua?", "Kuluttajaneuvonta (Kilpailu- ja kuluttajavirasto) neuvoo maksutta. Jos myyjän kanssa ei päästä sopuun, asian voi viedä kuluttajariitalautakuntaan, jonka käsittely on maksutonta.")]),
    ("takuu-loppui", "Takuu loppui – onko myyjä silti vastuussa virheestä?",
     "Yleistä tietoa takuusta ja lakisääteisestä virhevastuusta: miksi takuun päättyminen ei aina tarkoita, että myyjän vastuu loppuu.",
     "Takuu on myyjän tai valmistajan lupaama lisäetu. Lakisääteinen virhevastuu on erillinen asia, eikä se pääty takuun mukana: vastuun kesto riippuu siitä, kuinka kauan tuotteen voidaan kohtuudella odottaa kestävän.",
     [("Mitä eroa on takuulla ja virhevastuulla?", "Takuu on vapaaehtoinen lupaus, jonka ehdot myyjä tai valmistaja määrittää. Virhevastuu perustuu lakiin: myyjä vastaa kuluttajansuojalain mukaan tavaran virheistä riippumatta siitä, onko tuotteella takuuta."),
      ("Kuinka pitkään myyjän virhevastuu kestää?", "Laissa ei ole kiinteää vuosimäärää. Vastuun kesto arvioidaan sen perusteella, kuinka kauan vastaavan tuotteen voidaan tavallisessa käytössä odottaa kestävän. Kalliimmalta ja kestävämmältä tuotteelta voi odottaa pidempää käyttöikää."),
      ("Voiko myyjä vedota siihen, että takuu on loppunut?", "Takuun päättyminen ei yksinään poista lakisääteistä virhevastuuta. Ratkaisevaa on, onko kyse virheestä, joka on johtunut tuotteen ominaisuuksista, eikä esimerkiksi kulumisesta tai väärästä käytöstä."),
      ("Mitä teen, jos myyjä kieltäytyy?", "Tee reklamaatio kirjallisesti ja kerro, miksi pidät tuotetta virheellisenä. Jos sopua ei synny, kysy neuvoa kuluttajaneuvonnasta ja tarvittaessa vie asia kuluttajariitalautakuntaan.")]),
]


def rakenna(sivu, kirjoita):
    urls = []
    for slug, otsikko, kuvaus, tiivis, kys in SIVUT:
        osat = "".join(f"<h2>{esc(k)}</h2><p>{esc(v)}</p>" for k, v in kys)
        muut = "".join(f'<li><a href="/{s}/">{esc(o)}</a></li>' for s, o, *_ in SIVUT if s != slug)
        ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": k, "acceptedAnswer": {"@type": "Answer", "text": v}} for k, v in kys]}
        runko = (f'<h1>{esc(otsikko)}</h1><div class="prose"><p class="lead"><b>Lyhyesti:</b> {esc(tiivis)}</p>'
                 f'<p><a class="btn" href="/">Kysy omasta tilanteestasi →</a></p>{osat}'
                 f'<h2>Lue myös</h2><ul>{muut}<li><a href="/toimistot/">Lakitoimistot paikkakunnittain</a></li></ul>'
                 f'<p class="pieni mute">Tämä on yleistä tietoa laista, ei oikeudellista neuvontaa. Yksittäistapauksessa kysy neuvoa kuluttajaneuvonnasta tai lakimieheltä.</p></div>')
        skripti = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}</script>'
        kirjoita(f"/{slug}/", sivu(f"/{slug}/", f"{otsikko} | Pykälävahti", kuvaus, runko, skripti))
        urls.append(f"/{slug}/")
    return urls


def llms(site):
    r = ["# Pykälävahti", "", "> Ilmainen suomalainen palvelu, joka selittää Suomen lakia ajantasaisen lainsäädännön (Finlex) pohjalta ja ohjaa lakitoimistoihin. Vastaukset ovat yleistä tietoa, eivät oikeudellista neuvontaa. Osa Faktapistettä (faktapiste.fi).", "", "## Ohjeet", ""]
    r += [f"- [{o}]({site}/{s}/): {k}" for s, o, k, *_ in SIVUT]
    r += ["", "## Palvelu", "", f"- [Kysy laista]({site}/): vastaus pykälineen", f"- [Lakitoimistot]({site}/toimistot/): asianajo- ja lakiasiaintoimistot paikkakunnittain", f"- [Tietoa]({site}/tietoa/)", ""]
    return "\n".join(r)
