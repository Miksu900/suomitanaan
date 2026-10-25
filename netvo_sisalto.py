# -*- coding: utf-8 -*-
"""Netvo – 4 viikon sisältökalenteri (28 julkaisua, 1/pv) + julkaisukuvat."""
import datetime

ALKU = datetime.date(2026, 10, 26)  # ma 26.10.2026
LINKKI = "netvo.fi"

# teema_vari: sininen, vihrea, oranssi, musta, viininpunainen, petroli, ruskea, purppura
# jokainen: (teema, aika, kuva_otsikko, kuva_ala, teksti, hashtagit, vari)
POSTIT = [
 ("Avaus", "18:30", "Netvo on täällä", "Valmiit nettisivut yrityksellesi",
  "Uusi yrityksesi, uudet asiakkaat – mutta nettisivut puuttuu?\n\n"
  "Netvo tekee ammattimaiset nettisivut puolestasi. Sinä keskityt työhösi, me hoidamme sivut.\n\n"
  "✅ Pystytys 0 €\n✅ Oma verkkotunnus sinun nimiisi\n✅ Reilut ehdot – peru milloin vain\n\n"
  "Katso mallisivut ja hinta 👉 netvo.fi",
  "#nettisivut #yrittäjä #pienyritys #verkkosivut #Suomi", "sininen"),

 ("Myytti", "18:30", "1500 € nettisivuista?", "Ei enää.",
  "\"Nettisivujen teko maksaa 1500 €.\" Niinhän se ennen oli.\n\n"
  "Netvolla pystytys on 0 € ja maksat vain selkeän kuukausihinnan, joka kattaa verkkotunnuksen, ylläpidon ja pienet muutokset.\n\n"
  "Ei suurta kertamaksua. Ei yllätyksiä.\n\n"
  "👉 netvo.fi",
  "#nettisivut #yrittäjä #hinta #pienyritys", "vihrea"),

 ("Näin toimii", "12:00", "Näin se toimii", "3 helppoa askelta",
  "Nettisivut valmiiksi kolmessa askeleessa:\n\n"
  "1️⃣ Kerrot lyhyesti yrityksestäsi\n"
  "2️⃣ Me rakennamme sivut ja kirjoitamme tekstit\n"
  "3️⃣ Sivut julkaistaan omalla verkkotunnuksellasi\n\n"
  "Näet vedoksen ennen julkaisua ja saat muutokset mukaan.\n\n"
  "👉 netvo.fi",
  "#nettisivut #yrittäjä #helppo #verkkosivut", "petroli"),

 ("Reiluus", "18:30", "Oma verkkotunnus", "Se on sinun – ei meidän",
  "Moni \"ilmainen sivu\" sitoo asiakkaan loukkuun. Me teemme toisin.\n\n"
  "Verkkotunnus (esim. yrityksesi.fi) rekisteröidään SINUN yrityksesi nimiin. Se on sinun omaisuuttasi – et jää meistä riippuvaiseksi.\n\n"
  "Reiluus on lupauksemme.\n\n"
  "👉 netvo.fi",
  "#nettisivut #verkkotunnus #yrittäjä #reiluus", "sininen"),

 ("Malli parturi", "17:30", "Parturi-kampaamo", "Katso mallisivu",
  "Miltä valmis sivusto näyttää? Katso esimerkki parturi-kampaamolle.\n\n"
  "Selkeä etusivu, palvelut, aukioloajat ja yhteydenotto – kaikki yhdessä paikassa, toimii puhelimella.\n\n"
  "Omasi tehdään samalla laadulla, sinun väreilläsi ja sisällölläsi.\n\n"
  "👉 netvo.fi/mallit/parturi/",
  "#parturi #kampaamo #nettisivut #yrittäjä", "purppura"),

 ("Löydettävyys", "18:30", "Löytyykö yrityksesi?", "Asiakkaat etsivät netistä",
  "Kun joku etsii palveluasi, hän googlaa. Jos sivuja ei ole, hän löytää kilpailijan.\n\n"
  "Nettisivut tekevät yrityksestäsi löydettävän ja luotettavan – ympäri vuorokauden, ilman että sinun tarvitsee olla paikalla.\n\n"
  "👉 netvo.fi",
  "#löydettävyys #google #nettisivut #pienyritys", "oranssi"),

 ("Ehdot", "12:00", "Reilut ehdot", "Ei loukkua, ei pientä pränttiä",
  "Lupaamme reilut ehdot:\n\n"
  "✅ Oma verkkotunnus sinun nimiisi\n"
  "✅ Voit perua milloin vain – vain 2 kk maksu kesken sitoutumisajan\n"
  "✅ Ei automaattista hinnankorotusta\n"
  "✅ Selkeä hinta etukäteen\n\n"
  "Lue tarkat ehdot 👉 netvo.fi/ehdot/",
  "#reiluus #nettisivut #yrittäjä #ehdot", "vihrea"),

 ("Malli putki", "17:30", "Putki- ja LVI-palvelut", "Katso mallisivu",
  "Esimerkki ammattimaisista sivuista putki- ja LVI-yritykselle.\n\n"
  "Palvelut selkeästi, soittonappi heti näkyvillä ja yhteydenottolomake – juuri se mitä asiakas kaipaa hädän hetkellä.\n\n"
  "👉 netvo.fi/mallit/putki/",
  "#putkimies #LVI #nettisivut #yrittäjä", "sininen"),

 ("Mobiili", "18:30", "Toimii puhelimella", "Siellä asiakkaasi ovat",
  "Yli puolet nettiselailusta tapahtuu puhelimella. Jos sivusi eivät toimi mobiilissa, menetät asiakkaita.\n\n"
  "Netvon sivut rakennetaan toimimaan täydellisesti puhelimella, tabletilla ja tietokoneella – automaattisesti.\n\n"
  "👉 netvo.fi",
  "#mobiili #nettisivut #yrittäjä #responsiivinen", "petroli"),

 ("Lomake", "12:00", "Yhteydenotto suoraan", "Viesti sähköpostiisi",
  "Jokaisella Netvon sivulla on yhteydenottolomake. Kun asiakas täyttää sen, viesti tulee suoraan sähköpostiisi.\n\n"
  "Ei menetettyjä yhteydenottoja. Ei monimutkaisia järjestelmiä.\n\n"
  "👉 netvo.fi",
  "#yhteydenotto #nettisivut #asiakkaat #yrittäjä", "sininen"),

 ("Malli ravintola", "17:30", "Ravintola & kahvila", "Katso mallisivu",
  "Esimerkki ravintolan sivuista: menu, aukioloajat, sijainti ja varaukset selkeästi esillä.\n\n"
  "Nälkäinen asiakas löytää sinut ja tietää heti mitä tarjoat.\n\n"
  "👉 netvo.fi/mallit/ravintola/",
  "#ravintola #kahvila #nettisivut #yrittäjä", "viininpunainen"),

 ("Peru", "18:30", "Peru milloin vain", "Vain 2 kk maksu",
  "Monilla palveluilla pitkä sitoutuminen tarkoittaa loukkua. Netvolla ei.\n\n"
  "Jos haluat lopettaa kesken sitoutumisajan, maksat vain 2 kuukauden maksua vastaavan summan. Ei muuta. Ei kyttäystä.\n\n"
  "👉 netvo.fi/ehdot/",
  "#reiluus #nettisivut #yrittäjä #ehdot", "vihrea"),

 ("Verkkokauppa", "12:00", "Verkkokauppa myös", "Tuotteesi myyntiin",
  "Haluatko myydä tuotteita netissä? Teemme myös selkeitä verkkokauppoja.\n\n"
  "Tuotteiden esittely, tilaaminen ja yhteydenotto – kaikki yhdessä paikassa, samalla reilulla mallilla.\n\n"
  "👉 netvo.fi",
  "#verkkokauppa #nettisivut #yrittäjä #myynti", "oranssi"),

 ("Google", "18:30", "Näy Googlessa", "Ilman jatkuvaa kyttäystä",
  "Hyvin rakennetut sivut auttavat yritystäsi löytymään Googlesta. Sivut tekevät työtä puolestasi vuorokauden ympäri.\n\n"
  "Me huolehdimme teknisestä toteutuksesta – sinä saat asiakkaita.\n\n"
  "👉 netvo.fi",
  "#google #SEO #nettisivut #löydettävyys", "petroli"),

 ("Malli siivous", "17:30", "Siivouspalvelu", "Katso mallisivu",
  "Esimerkki siivousyrityksen sivuista: palvelut, hinnoittelu ja helppo yhteydenotto.\n\n"
  "Luottamus syntyy heti, kun sivut näyttävät ammattimaisilta.\n\n"
  "👉 netvo.fi/mallit/siivous/",
  "#siivous #nettisivut #yrittäjä #palvelu", "sininen"),

 ("Muutokset", "12:00", "Pienet muutokset", "Sisältyvät hintaan",
  "Aukioloajat muuttuvat? Uusi hinta tai palvelu? Lähetät vain viestin, me päivitämme.\n\n"
  "Pienet tekstimuutokset sisältyvät kuukausihintaan. Sivusi pysyvät aina ajan tasalla.\n\n"
  "👉 netvo.fi",
  "#nettisivut #ylläpito #yrittäjä #palvelu", "vihrea"),

 ("Tekninen", "18:30", "Me hoidamme tekniikan", "Sinä teet työsi",
  "Hosting, varmuuskopiot, tietoturva, päivitykset – kuulostaako vaikealta?\n\n"
  "Ei tarvitse osata mitään näistä. Netvo hoitaa kaiken teknisen puolen puolestasi. Sinä keskityt siihen minkä osaat parhaiten.\n\n"
  "👉 netvo.fi",
  "#nettisivut #ylläpito #tietoturva #yrittäjä", "musta"),

 ("Malli remontti", "17:30", "Remontti & rakennus", "Katso mallisivu",
  "Esimerkki remontti- ja rakennusalan sivuista: referenssit, palvelut ja tarjouspyyntö helposti.\n\n"
  "Näytä osaamisesi ja saat enemmän tarjouspyyntöjä.\n\n"
  "👉 netvo.fi/mallit/remontti/",
  "#remontti #rakennus #nettisivut #yrittäjä", "ruskea"),

 ("UKK", "12:00", "Onko se oikeasti ilmaista?", "Kyllä on",
  "Yleisin kysymys: \"Onko pystytys oikeasti ilmainen?\"\n\n"
  "Kyllä. Et maksa sivujen tekemisestä mitään. Kuukausimaksu kattaa verkkotunnuksen, hostingin, ylläpidon ja pienet muutokset – näin sivut pysyvät kunnossa koko ajan.\n\n"
  "👉 netvo.fi",
  "#UKK #nettisivut #yrittäjä #hinta", "sininen"),

 ("Ei korotusta", "18:30", "Hinta ei nouse", "Sitoutumisajan jälkeenkään",
  "Monella palvelulla hinta nousee huomaamatta. Netvolla ei.\n\n"
  "Sitoutumisajan jälkeen sopimus jatkuu samalla hinnalla kuukausi kerrallaan. Ei automaattista kallistumista.\n\n"
  "👉 netvo.fi/ehdot/",
  "#reiluus #nettisivut #hinta #yrittäjä", "vihrea"),

 ("Malli hyvinvointi", "17:30", "Hyvinvointi & kauneus", "Katso mallisivu",
  "Esimerkki hyvinvointi- ja kauneusalan sivuista: palvelut, ajanvaraus ja tunnelma esillä.\n\n"
  "Kaunis sivu kertoo laadusta jo ennen ensimmäistä käyntiä.\n\n"
  "👉 netvo.fi/mallit/hyvinvointi/",
  "#hyvinvointi #kauneus #nettisivut #yrittäjä", "purppura"),

 ("Paikallinen", "18:30", "Paikallinen yrittäjä?", "Tehdään sivut yhdessä",
  "Oletko pienyrittäjä ja mietit nettisivuja? Et tarvitse isoa budjettia etkä teknistä osaamista.\n\n"
  "Netvo tekee sivut puolestasi, reiluilla ehdoilla ja ilman pystytysmaksua. Autamme mielellämme.\n\n"
  "👉 netvo.fi",
  "#pienyritys #yrittäjä #nettisivut #paikallinen", "petroli"),

 ("Malli autokorjaamo", "17:30", "Autokorjaamo", "Katso mallisivu",
  "Esimerkki autokorjaamon sivuista: palvelut, ajanvaraus ja yhteystiedot selkeästi.\n\n"
  "Asiakas löytää sinut ja varaa ajan helposti.\n\n"
  "👉 netvo.fi/mallit/autokorjaamo/",
  "#autokorjaamo #nettisivut #yrittäjä #auto", "musta"),

 ("Vuodenvaihde", "12:00", "Uudet sivut 2027", "Aloita vuosi näkyvästi",
  "Uusi vuosi lähestyy. Olisiko aika hankkia yrityksellesi kunnon nettisivut?\n\n"
  "Pystytys 0 €, valmista muutamassa päivässä. Aloita ensi vuosi näkyvämmin kuin koskaan.\n\n"
  "👉 netvo.fi",
  "#uusivuosi #nettisivut #yrittäjä #2027", "viininpunainen"),

 ("Malli maalaus", "17:30", "Maalaus & pinnoitus", "Katso mallisivu",
  "Esimerkki maalausalan sivuista: työnäytteet, palvelut ja tarjouspyyntö.\n\n"
  "Kuvat töistäsi myyvät – näytä ne ammattimaisilla sivuilla.\n\n"
  "👉 netvo.fi/mallit/maalaus/",
  "#maalaus #remontti #nettisivut #yrittäjä", "oranssi"),

 ("Tilaus", "18:30", "Näin tilaat", "Selkeä lasku, ei korttikikkailua",
  "Tilaaminen on helppoa: kerrot yrityksestäsi, me teemme sivut ja saat selkeän laskun.\n\n"
  "Ei kolmansien osapuolien maksupalveluita, ei korttitietojen syöttämistä. Vain tavallinen lasku.\n\n"
  "👉 netvo.fi",
  "#nettisivut #yrittäjä #lasku #helppo", "sininen"),

 ("Malli verkkokauppa", "17:30", "Verkkokauppa-malli", "Katso esimerkki",
  "Esimerkki pienen verkkokaupan sivuista – esim. leipomo tai käsityöt.\n\n"
  "Tuotteet esille, tilaus helpoksi, oma ilme. Myynti ei vaadi isoa alustaa.\n\n"
  "👉 netvo.fi",
  "#verkkokauppa #käsityö #leipomo #nettisivut", "vihrea"),

 ("Yhteenveto CTA", "18:30", "Valmis alkamaan?", "Pystytys 0 €",
  "Ammattimaiset nettisivut yrityksellesi:\n\n"
  "✅ Pystytys 0 €\n✅ Oma verkkotunnus sinun nimiisi\n✅ Reilut ehdot, peru milloin vain\n✅ Me hoidamme kaiken teknisen\n\n"
  "Katso mallit ja hanki omasi 👉 netvo.fi",
  "#nettisivut #yrittäjä #pienyritys #netvo", "sininen"),
]

def kalenteri():
    rivit = []
    for i, (teema, aika, otsikko, ala, teksti, tagit, vari) in enumerate(POSTIT):
        pvm = ALKU + datetime.timedelta(days=i)
        rivit.append(dict(nro=i+1, pvm=pvm, aika=aika, teema=teema, otsikko=otsikko,
                          ala=ala, teksti=teksti, tagit=tagit, vari=vari,
                          kuva=f"netvo-{i+1:02d}.png"))
    return rivit

if __name__ == "__main__":
    for r in kalenteri():
        print(r["nro"], r["pvm"].strftime("%a %d.%m."), r["aika"], "-", r["otsikko"])
    print("Yhteensä:", len(POSTIT))
