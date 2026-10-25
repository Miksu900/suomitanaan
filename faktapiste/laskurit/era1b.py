"""Erä 1b: asuminen, energia, auto ja arki (puhdasta matematiikkaa)."""
from ._yht import K, L

ASU = "Asuminen ja remontti"
ENE = "Sähkö ja energia"
AUTO = "Auto ja liikenne"
ARKI = "Arki ja aika"

ERA1B = [
L("maalimenekki", "Maalimenekkilaskuri", ASU,
  "Maalimenekkilaskuri – paljonko maalia tarvitaan?",
  "Laske, montako litraa maalia tarvitset seinien maalaamiseen. Huomioi ikkunat, ovet ja maalauskerrat.",
  "Laske tarvittava maalimäärä seinien mittojen perusteella.",
  [K("pituus", "Seinien yhteispituus", 16, "m"), K("korkeus", "Seinän korkeus", 2.5, "m"), K("aukot", "Ikkunat ja ovet yhteensä", 4, "m²"),
   K("kerrat", "Maalauskerrat", 2, "kertaa"), K("menekki", "Maalin riittoisuus (purkin kyljestä)", 8, "m²/l")],
  """var A=v.pituus*v.korkeus-(v.aukot||0); if(!(A>0)||!(v.menekki>0)||!(v.kerrat>0)) return null; var l=A*v.kerrat/v.menekki;
return [["Maalia tarvitaan",f.n(l,1)+" l",1],["Maalattava pinta-ala",f.n(A,1)+" m²"],["Suositus varan kanssa (+10 %)",f.n(l*1.1,1)+" l"]];""",
  """<p>Maalin tarve lasketaan maalattavasta pinta-alasta, maalauskerroista ja maalin riittoisuudesta. Riittoisuus (m²/l) on merkitty maalipurkin kylkeen, ja se on tyypillisesti 6–10 m² litralla.</p>
<p>Seinien yhteispituus on huoneen piiri. Esimerkiksi 4 × 4 metrin huoneessa se on 16 metriä. Vähennä ikkunoiden ja ovien pinta-ala, jos ne ovat suuria.</p>
<p>Varaa noin 10 % ylimääräistä, koska karhea tai imukykyinen pinta kuluttaa enemmän maalia ja jälkikorjauksiin tarvitaan samaa sävyä.</p>""",
  [("Montako kertaa seinä pitää maalata?", "Yleensä kaksi kertaa. Jos sävy vaihtuu paljon tai pinta on uusi, voi tarvita pohjamaalin lisäksi."),
   ("Mistä löydän riittoisuuden?", "Maalipurkin kyljestä tai valmistajan tuotetiedoista, yleensä muodossa m²/l.")]),

L("laattamenekki", "Laattalaskuri", ASU,
  "Laattalaskuri – montako laattaa tarvitaan?",
  "Laske laattojen määrä lattiaan tai seinään laatan koon ja hukan mukaan. Laattamenekkilaskuri remonttiin.",
  "Laske tarvittavien laattojen määrä pinta-alasta ja laatan koosta.",
  [K("ala", "Laatoitettava pinta-ala", 6, "m²"), K("lev", "Laatan leveys", 30, "cm"), K("kor", "Laatan korkeus", 30, "cm"), K("hukka", "Hukka ja leikkuuvara", 10, "%"), K("paketti", "Laattoja paketissa (valinnainen)", "", "kpl")],
  """var a=v.ala,l=v.lev/100*v.kor/100; if(!(a>0)||!(l>0)) return null; var n=Math.ceil(a/l*(1+(v.hukka||0)/100));
var r=[["Laattoja tarvitaan",f.n(n,0)+" kpl",1],["Pinta-ala hukan kanssa",f.n(a*(1+(v.hukka||0)/100),2)+" m²"],["Yhden laatan ala",f.n(l,3)+" m²"]];
if(v.paketti>0) r.push(["Paketteja",f.n(Math.ceil(n/v.paketti),0)+" kpl"]); return r;""",
  """<p>Laattojen määrä saadaan jakamalla pinta-ala yhden laatan pinta-alalla ja lisäämällä hukka. Leikkauksissa, kulmissa ja rikkoutumisissa kuluu laattoja, joten hukaksi kannattaa varata 10 %. Vinoon tai kuvioon ladottaessa varaa 15 %.</p>
<p>Osta kaikki laatat samasta erästä, koska sävy voi vaihdella erien välillä. Säästä muutama ylimääräinen laatta myöhempiä korjauksia varten.</p>""",
  [("Paljonko hukkaa kannattaa varata?", "Suorassa ladonnassa noin 10 %, vinoladonnassa ja pienissä tiloissa 15 %."),
   ("Lasketaanko saumat mukaan?", "Saumat ovat niin kapeita, ettei niitä tarvitse huomioida laattamäärässä.")]),

L("betonilaskuri", "Betonilaskuri", ASU,
  "Betonilaskuri – paljonko betonia tarvitaan?",
  "Laske laatan tai valun betonimäärä kuutioina ja säkkeinä. Betonilaskuri pihalaatalle, perustukselle ja valuille.",
  "Laske valun betonimäärä mittojen perusteella.",
  [K("pituus", "Pituus", 4, "m"), K("leveys", "Leveys", 3, "m"), K("paksuus", "Paksuus", 10, "cm"), K("sakki", "Säkin koko", 25, "kg")],
  """var m3=v.pituus*v.leveys*v.paksuus/100; if(!(m3>0)) return null; var kg=m3*2200;
var r=[["Betonia tarvitaan",f.n(m3,2)+" m³",1],["Litroina",f.n(m3*1000,0)+" l"]]; if(v.sakki>0) r.push(["Säkkejä (kuivabetoni) noin",f.n(Math.ceil(kg/v.sakki),0)+" kpl"]); return r;""",
  """<p>Betonin tilavuus on pituus × leveys × paksuus. Muista muuttaa paksuus metreiksi: 10 cm on 0,1 m.</p>
<p>Säkkimäärä on arvio. Valmiiksi kuivasekoitetusta betonista syntyy noin 1 kuutio valmista betonia noin 2 200 kilosta kuivaseosta, mutta tarkka riittoisuus on merkitty säkkiin. Isoissa valuissa valmisbetoni autolla tulee yleensä edullisemmaksi.</p>
<p>Varaa 5–10 % ylimääräistä, koska muotit painuvat ja pohja ei ole koskaan täysin tasainen.</p>""",
  [("Kannattaako tilata valmisbetonia?", "Yli noin puolen kuution valuissa valmisbetoni on yleensä nopeampi ja edullisempi kuin säkkibetoni."),
   ("Kuinka paksu pihalaatan pitää olla?", "Kevyessä käytössä noin 8–10 cm, autoille ja raskaalle kuormalle enemmän ja raudoitettuna.")]),

L("neliohintalaskuri", "Neliöhintalaskuri", ASU,
  "Neliöhintalaskuri – asunnon hinta neliöltä",
  "Laske asunnon neliöhinta ja velaton neliöhinta. Vertaa asuntoja neliöhinnan perusteella.",
  "Laske asunnon hinta neliötä kohden.",
  [K("hinta", "Myyntihinta", 150000, "€"), K("velka", "Velkaosuus (taloyhtiön laina)", 0, "€"), K("ala", "Asuinpinta-ala", 60, "m²")],
  """var h=v.hinta,a=v.ala; if(!(h>0)||!(a>0)) return null; var vh=h+(v.velka||0);
return [["Velaton neliöhinta",f.e(vh/a)+" /m²",1],["Neliöhinta (myyntihinta)",f.e(h/a)+" /m²"],["Velaton hinta",f.e(vh)]];""",
  """<p>Neliöhinta on asunnon hinta jaettuna asuinpinta-alalla. Asuntoja vertaillessa kannattaa käyttää <b>velatonta neliöhintaa</b>, jossa taloyhtiön lainaosuus on lisätty myyntihintaan. Muuten kaksi saman hintaista asuntoa voivat olla todellisuudessa hyvin eri hintaisia.</p>
<p>Huomaa myös rahoitusvastike: jos taloyhtiöllä on lainaa, maksat sitä kuukausittain vastikkeen lisäksi.</p>""",
  [("Mikä on velaton hinta?", "Myyntihinta lisättynä asunnon osuudella taloyhtiön lainasta. Se kertoo asunnon todellisen hinnan."),
   ("Lasketaanko parveke pinta-alaan?", "Ei yleensä. Asuinpinta-alaan lasketaan vain asuintilat.")]),

L("vuokratuottolaskuri", "Vuokratuottolaskuri", ASU,
  "Vuokratuottolaskuri – sijoitusasunnon brutto- ja nettotuotto",
  "Laske sijoitusasunnon vuokratuotto prosentteina. Huomioi vastike ja muut kulut. Ilmainen vuokratuottolaskuri.",
  "Laske, paljonko sijoitusasunto tuottaa vuodessa ennen veroja.",
  [K("hinta", "Velaton kauppahinta", 120000, "€"), K("vuokra", "Vuokra kuukaudessa", 700, "€"), K("vastike", "Vastike kuukaudessa", 200, "€"),
   K("muut", "Muut kulut vuodessa (remontit, vakuutus)", 500, "€"), K("tyhja", "Tyhjät kuukaudet vuodessa", 0.5, "kk")],
  """var H=v.hinta; if(!(H>0)||!(v.vuokra>0)) return null; var tulot=v.vuokra*(12-(v.tyhja||0)), kulut=(v.vastike||0)*12+(v.muut||0), net=tulot-kulut;
return [["Nettovuokratuotto",f.p(net/H*100,2),1],["Bruttovuokratuotto",f.p(v.vuokra*12/H*100,2)],["Nettotulo vuodessa",f.e(net)],["Nettotulo kuukaudessa",f.e(net/12)]];""",
  """<p><b>Bruttovuokratuotto</b> on vuosivuokra jaettuna kauppahinnalla. Se on helppo laskea, mutta antaa liian ruusuisen kuvan. <b>Nettovuokratuotto</b> huomioi vastikkeen, muut kulut ja tyhjät kuukaudet, joten se kertoo todellisen tuoton paremmin.</p>
<p>Laskuri ei huomioi lainan korkoja, verotusta eikä asunnon arvonmuutosta. Vuokratulo on pääomatuloa, josta maksetaan veroa.</p>""",
  [("Mikä on hyvä vuokratuotto?", "Nettovuokratuotto 3–5 % on tavallinen. Korkeampi tuotto liittyy usein suurempaan riskiin tai heikompaan sijaintiin."),
   ("Pitääkö lainan korot huomioida?", "Jos ostat velalla, korot pienentävät oman pääoman tuottoa. Tämä laskuri näyttää tuoton koko kauppahinnalle.")]),

L("sahkonkulutus", "Laitteen sähkönkulutus", ENE,
  "Sähkönkulutuslaskuri – paljonko laite kuluttaa sähköä?",
  "Laske laitteen sähkönkulutus ja sähkökulut tehon ja käyttöajan perusteella. Esimerkiksi lämmitin, sauna, pakastin tai tietokone.",
  "Laske laitteen kulutus kilowattitunteina ja euroina.",
  [K("teho", "Laitteen teho", 2000, "W"), K("tunnit", "Käyttö päivässä", 1, "h"), K("hinta", "Sähkön hinta siirtoineen", 15, "snt/kWh")],
  """var kwh=v.teho/1000*v.tunnit; if(!(kwh>=0)||!(v.hinta>=0)) return null; var e=kwh*v.hinta/100;
return [["Kulut kuukaudessa",f.e2(e*30.4),1],["Kulut vuodessa",f.e(e*365)],["Kulutus päivässä",f.n(kwh,2)+" kWh"],["Kulutus vuodessa",f.n(kwh*365,0)+" kWh"]];""",
  """<p>Sähkönkulutus lasketaan kertomalla laitteen teho kilowatteina käyttötunneilla: 2 000 watin lämmitin kuluttaa tunnissa 2 kWh. Kun kulutus kerrotaan sähkön hinnalla, saadaan kustannus.</p>
<p>Laske hintaan mukaan sekä energia että siirto, koska molemmat maksetaan kulutuksen mukaan. Tyypillinen kokonaishinta on 10–25 senttiä kilowattitunnilta sopimuksesta riippuen.</p>
<p>Termostaatilla toimivat laitteet, kuten jääkaappi tai lämmitin, eivät käy koko ajan täydellä teholla. Arvioi silloin todellinen käyntiaika.</p>""",
  [("Mistä löydän laitteen tehon?", "Laitteen arvokilvestä tai käyttöohjeesta. Teho ilmoitetaan watteina (W)."),
   ("Mikä kuluttaa kotona eniten sähköä?", "Lämmitys, lämmin käyttövesi, sauna ja sähköauton lataus ovat yleensä suurimmat kuluttajat.")]),

L("sahkosopimusvertailu", "Sähkösopimusten vertailu", ENE,
  "Pörssisähkö vai kiinteä? Vertaa sähkösopimusten vuosihintaa",
  "Vertaa kiinteähintaisen sähkösopimuksen ja pörssisähkön vuosikustannusta omalla kulutuksellasi.",
  "Syötä kulutuksesi ja tarjousten hinnat, niin näet, kumpi tulee halvemmaksi.",
  [K("kulutus", "Sähkönkulutus vuodessa", 5000, "kWh"),
   K("kiintea", "Kiinteä: energian hinta", 9, "snt/kWh"), K("kperus", "Kiinteä: perusmaksu", 4, "€/kk"),
   K("porssi", "Pörssi: arvioitu keskihinta", 7, "snt/kWh"), K("marg", "Pörssi: marginaali", 0.5, "snt/kWh"), K("pperus", "Pörssi: perusmaksu", 3, "€/kk")],
  """var k=v.kulutus; if(!(k>0)) return null; var a=k*v.kiintea/100+12*(v.kperus||0), b=k*((v.porssi||0)+(v.marg||0))/100+12*(v.pperus||0);
return [[a<b?"Kiinteä on halvempi":"Pörssisähkö on halvempi",f.e(Math.abs(a-b))+" / vuosi",1],["Kiinteä vuodessa",f.e(a)],["Pörssisähkö vuodessa",f.e(b)],["Pörssin tasapainohinta",f.n((a-12*(v.pperus||0))/k*100-(v.marg||0),2)+" snt/kWh"]];""",
  """<p>Laskuri vertaa sähköenergian vuosikustannusta. Siirtomaksu on sama sopimuksesta riippumatta, joten sitä ei tarvitse huomioida vertailussa.</p>
<p>Pörssisähkön hinta vaihtelee tunneittain, joten sen vuosihinta on arvio. <b>Tasapainohinta</b> kertoo, mikä pörssisähkön keskihinnan pitäisi olla, jotta molemmat sopimukset maksaisivat saman verran. Jos uskot keskihinnan jäävän tätä alemmaksi, pörssisähkö kannattaa.</p>
<p>Pörssisähkössä voit säästää siirtämällä kulutusta halvoille tunneille, esimerkiksi lataamalla auton tai lämmittämällä vettä yöllä.</p>""",
  [("Kenelle pörssisähkö sopii?", "Niille, jotka voivat siirtää kulutusta halvoille tunneille ja kestävät hintavaihtelun."),
   ("Mistä arvioin pörssisähkön keskihinnan?", "Edellisten kuukausien toteutuneet keskihinnat antavat suuntaa, mutta tulevaa hintaa ei voi tietää varmasti.")]),

L("polttoainekulut", "Matkan polttoainekulut", AUTO,
  "Polttoainelaskuri – paljonko matka maksaa bensassa?",
  "Laske automatkan polttoainekulut matkan pituuden, kulutuksen ja polttoaineen hinnan mukaan. Jaa kulut kyytiläisten kesken.",
  "Laske matkan polttoainekulut ja hinta per henkilö.",
  [K("km", "Matkan pituus", 300, "km"), K("kulutus", "Auton kulutus", 6.5, "l/100 km"), K("hinta", "Polttoaineen hinta", 1.85, "€/l"), K("hlot", "Kyydissä henkilöitä", 1, "hlö")],
  """var l=v.km*v.kulutus/100; if(!(l>=0)||!(v.hinta>0)) return null; var e=l*v.hinta, h=Math.max(1,Math.round(v.hlot||1));
return [["Polttoainekulut",f.e2(e),1],["Per henkilö",f.e2(e/h)],["Polttoainetta kuluu",f.n(l,1)+" l"],["Meno-paluu",f.e2(e*2)]];""",
  """<p>Polttoainekulut lasketaan kertomalla matkan pituus auton kulutuksella ja polttoaineen hinnalla. Esimerkiksi 300 km matka 6,5 l/100 km kuluttavalla autolla vie noin 19,5 litraa, eli noin 36 euroa 1,85 euron litrahinnalla.</p>
<p>Moottoritiellä ja kovalla nopeudella kulutus on suurempi kuin kaupunkiajossa tai tasaisessa maantienopeudessa. Talvella kulutus kasvaa tyypillisesti 10–20 %.</p>
<p>Laskuri huomioi vain polttoaineen. Auton todellisiin kuluihin kuuluvat myös vakuutus, vero, huolto ja arvonalennus.</p>""",
  [("Mistä tiedän autoni kulutuksen?", "Ajotietokoneesta tai tankkaamalla täyteen ja jakamalla tankatut litrat ajetuilla kilometreillä × 100."),
   ("Miten kyytimaksu kannattaa jakaa?", "Yleinen tapa on jakaa polttoainekulut tasan kaikkien kyydissä olevien kesken.")]),

L("sahkoauton-lataus", "Sähköauton latauskulut", AUTO,
  "Sähköauton latauslaskuri – paljonko lataus maksaa?",
  "Laske sähköauton latauksen hinta ja ajokustannus 100 kilometrillä. Vertaa kotilatausta ja julkista latausta.",
  "Laske latauksen hinta ja sähköauton ajokustannus.",
  [K("akku", "Akun koko", 60, "kWh"), K("alku", "Varaus alussa", 20, "%"), K("loppu", "Ladataan", 80, "%"),
   K("hinta", "Sähkön hinta", 15, "snt/kWh"), K("havio", "Latausvirta-häviö", 10, "%"), K("kulutus", "Auton kulutus", 17, "kWh/100 km")],
  """var e=v.akku*(v.loppu-v.alku)/100; if(!(e>0)||!(v.hinta>=0)) return null; var ost=e/(1-(v.havio||0)/100), hinta=ost*v.hinta/100;
var r=[["Latauksen hinta",f.e2(hinta),1],["Akkuun ladattu energia",f.n(e,1)+" kWh"],["Verkosta otettu energia",f.n(ost,1)+" kWh"]];
if(v.kulutus>0){ r.push(["Ajokustannus",f.e2(v.kulutus/(1-(v.havio||0)/100)*v.hinta/100)+" / 100 km"]); r.push(["Toimintamatka tällä latauksella",f.n(e/v.kulutus*100,0)+" km"]); } return r;""",
  """<p>Latauksen hinta riippuu siitä, paljonko energiaa akkuun ladataan, sähkön hinnasta ja latauksen häviöistä. Kotilatauksessa häviöt ovat tyypillisesti 5–15 %.</p>
<p>Kotona sähkön hinta sisältää energian ja siirron. Julkisessa pikalatauksessa hinta on usein moninkertainen kotilataukseen verrattuna, joten ajokustannus voi olla lähellä polttoaineautoa.</p>
<p>Akun käyttöiän kannalta päivittäisessä ajossa suositellaan usein lataamista noin 80 prosenttiin.</p>""",
  [("Paljonko sähköauto kuluttaa?", "Tyypillisesti 15–22 kWh sadalla kilometrillä, talvella enemmän."),
   ("Onko kotilataus aina halvempaa?", "Yleensä kyllä, erityisesti pörssisähköllä yöllä ladattaessa.")]),

L("auton-kustannukset", "Auton kokonaiskustannukset", AUTO,
  "Auton kustannuslaskuri – paljonko auto maksaa kilometrillä?",
  "Laske auton todelliset kulut kuukaudessa ja kilometriä kohden: polttoaine, vakuutus, vero, huolto ja arvonalennus.",
  "Laske, paljonko auton omistaminen oikeasti maksaa.",
  [K("km", "Ajokilometrit vuodessa", 15000, "km"), K("kulutus", "Kulutus", 6.5, "l/100 km"), K("hinta", "Polttoaineen hinta", 1.85, "€/l"),
   K("vakuutus", "Vakuutukset vuodessa", 600, "€"), K("vero", "Ajoneuvovero vuodessa", 250, "€"), K("huolto", "Huollot ja renkaat vuodessa", 700, "€"), K("arvo", "Arvonalennus vuodessa", 1500, "€")],
  """var km=v.km; if(!(km>0)) return null; var pa=km*v.kulutus/100*v.hinta, muut=(v.vakuutus||0)+(v.vero||0)+(v.huolto||0)+(v.arvo||0), yht=pa+muut;
return [["Kulut kilometrillä",f.e2(yht/km)+" / km",1],["Kulut kuukaudessa",f.e(yht/12)],["Kulut vuodessa",f.e(yht)],["Polttoaineen osuus",f.p(pa/yht*100,0)]];""",
  """<p>Auton todellinen hinta on paljon enemmän kuin polttoaine. Vakuutus, ajoneuvovero, huollot, renkaat ja arvonalennus muodostavat usein yli puolet kuluista.</p>
<p><b>Arvonalennus</b> on se, paljonko auton arvo laskee vuodessa. Uudella autolla se on suurin kulu, käytetyllä pienempi. Arvioi se esimerkiksi vertaamalla vastaavien, vuoden vanhempien autojen hintoja.</p>
<p>Kilometrikohtainen hinta auttaa vertaamaan autoilua julkiseen liikenteeseen, kimppakyyteihin tai yhteiskäyttöautoon.</p>""",
  [("Mikä on auton suurin kulu?", "Uudella autolla yleensä arvonalennus, vanhalla polttoaine ja korjaukset."),
   ("Mitä kilometrihinta kertoo?", "Se kertoo, paljonko jokainen ajettu kilometri todella maksaa, kun kaikki kulut huomioidaan.")]),

L("ikalaskuri", "Ikälaskuri", ARKI,
  "Ikälaskuri – kuinka vanha olet vuosina, kuukausina ja päivinä?",
  "Laske tarkka ikä vuosina, kuukausina ja päivinä sekä päivät seuraavaan syntymäpäivään.",
  "Laske tarkka ikä syntymäpäivän perusteella.",
  [K("syntynyt", "Syntymäpäivä", "1990-01-01", "", tyyppi="pvm")],
  """var s=new Date(v.syntynyt+"T12:00:00"); if(isNaN(s)) return null; var n=new Date(); n.setHours(12,0,0,0); if(s>n) return null;
var y=n.getFullYear()-s.getFullYear(), m=n.getMonth()-s.getMonth(), d=n.getDate()-s.getDate();
if(d<0){m--; d+=new Date(n.getFullYear(),n.getMonth(),0).getDate();} if(m<0){y--; m+=12;}
var paivat=Math.round((n-s)/864e5), seur=new Date(n.getFullYear(),s.getMonth(),s.getDate(),12); if(seur<n) seur.setFullYear(n.getFullYear()+1);
var jaljella=Math.round((seur-n)/864e5);
return [["Ikä",y+" v "+m+" kk "+d+" pv",1],["Ikä päivinä",f.n(paivat,0)+" päivää"],["Seuraavaan syntymäpäivään",jaljella===0?"Hyvää syntymäpäivää!":f.n(jaljella,0)+" päivää"]];""",
  """<p>Ikälaskuri laskee tarkan iän vuosina, kuukausina ja päivinä sekä kertoo, montako päivää on elätty ja montako päivää on seuraavaan syntymäpäivään.</p>
<p>Laskuri huomioi karkausvuodet ja kuukausien eri pituudet. Laskenta tehdään selaimessasi, eikä syntymäpäivää tallenneta minnekään.</p>""",
  [("Tallennetaanko syntymäpäiväni?", "Ei. Laskenta tapahtuu omassa selaimessasi."),
   ("Miten karkausvuodet huomioidaan?", "Laskuri käyttää todellista kalenteria, joten karkauspäivät ovat mukana automaattisesti.")]),

L("paivalaskuri", "Päivälaskuri", ARKI,
  "Päivälaskuri – montako päivää on kahden päivämäärän välillä?",
  "Laske päivät, viikot ja arkipäivät kahden päivämäärän välillä. Päivälaskuri määräaikoihin, lomiin ja laskutukseen.",
  "Laske päivien määrä kahden päivämäärän välillä.",
  [K("alku", "Alkupäivä", "2026-01-01", "", tyyppi="pvm"), K("loppu", "Loppupäivä", "2026-12-31", "", tyyppi="pvm")],
  """var a=new Date(v.alku+"T12:00:00"), b=new Date(v.loppu+"T12:00:00"); if(isNaN(a)||isNaN(b)) return null; var mer=1; if(b<a){var t=a;a=b;b=t;mer=-1;}
var p=Math.round((b-a)/864e5), ark=0, d=new Date(a); for(var i=0;i<p&&i<40000;i++){d.setDate(d.getDate()+1); var w=d.getDay(); if(w!==0&&w!==6) ark++;}
return [["Päiviä välissä",f.n(p,0)+" päivää",1],["Viikkoina",f.n(p/7,1)+" viikkoa"],["Arkipäiviä (ma–pe)",f.n(ark,0)+" päivää"],["Päiviä, kun molemmat päivät lasketaan",f.n(p+1,0)+" päivää"]];""",
  """<p>Päivälaskuri laskee päivien määrän kahden päivämäärän välillä. Se kertoo myös arkipäivien määrän, mikä on hyödyllistä esimerkiksi määräaikojen, toimitusaikojen tai lomien laskemisessa.</p>
<p>Arkipäivät ovat maanantaista perjantaihin. Laskuri ei vähennä arkipyhiä, kuten joulua tai juhannusta, joten tarkista ne erikseen, jos lasket esimerkiksi työpäiviä.</p>
<p>Laskenta tapa "molemmat päivät mukaan" sopii esimerkiksi tilanteisiin, joissa sekä alku- että loppupäivä ovat käyttöpäiviä.</p>""",
  [("Lasketaanko alkupäivä mukaan?", "Päiviä välissä -luvussa ei. Jos haluat molemmat päivät mukaan, katso viimeinen rivi."),
   ("Huomioiko laskuri arkipyhät?", "Ei. Arkipäiviksi lasketaan kaikki maanantait–perjantait.")]),

L("bmi-laskuri", "BMI-laskuri", ARKI,
  "BMI-laskuri – laske painoindeksi",
  "Laske painoindeksi (BMI) pituuden ja painon perusteella. Näet myös, mihin painoindeksiluokkaan tulos kuuluu.",
  "Laske painoindeksi pituuden ja painon perusteella.",
  [K("pituus", "Pituus", 175, "cm"), K("paino", "Paino", 75, "kg")],
  """var h=v.pituus/100,p=v.paino; if(!(h>0.5)||!(p>10)) return null; var b=p/(h*h);
var l=b<18.5?"alipaino":b<25?"normaalipaino":b<30?"lievä ylipaino":b<35?"merkittävä ylipaino":b<40?"vaikea ylipaino":"sairaalloinen ylipaino";
return [["Painoindeksi (BMI)",f.n(b,1),1],["Luokka",l],["Normaalipainon alue pituudellesi",f.n(18.5*h*h,0)+"–"+f.n(25*h*h,0)+" kg"]];""",
  """<p>Painoindeksi lasketaan jakamalla paino kilogrammoina pituuden neliöllä metreinä: <i>BMI = paino / pituus²</i>. Aikuisilla normaalipainon alue on 18,5–24,9.</p>
<p>Painoindeksi on suuntaa antava mittari. Se ei erota lihasta ja rasvaa, joten esimerkiksi lihaksikkaalla ihmisellä BMI voi olla korkea, vaikka rasvaa on vähän. Vyötärön ympärys kertoo terveysriskeistä usein enemmän.</p>
<p>Laskuri on tarkoitettu aikuisille. Lasten ja nuorten painoa arvioidaan iän ja sukupuolen mukaisilla kasvukäyrillä.</p>""",
  [("Mikä on normaali BMI?", "Aikuisilla 18,5–24,9."),
   ("Sopiiko BMI kaikille?", "Ei täysin. Se ei huomioi kehon koostumusta, joten se on vain suuntaa antava.")]),

L("leivontamuunnin", "Desilitroista grammoiksi", ARKI,
  "Desilitra grammoiksi – leivonnan mittamuunnin",
  "Muunna desilitrat grammoiksi ja grammat desilitroiksi leivonnassa: vehnäjauho, sokeri, kaurahiutale, voi ja muut.",
  "Muunna leivonnan aineet desilitroista grammoiksi.",
  [K("aine", "Aine", "60", "", valinnat=[("60", "Vehnäjauho"), ("85", "Sokeri"), ("35", "Kaurahiutale"), ("95", "Voi tai margariini"), ("100", "Vesi tai maito"),
                                        ("85", "Riisi"), ("65", "Ruisjauho"), ("55", "Tomusokeri"), ("40", "Kaakaojauhe"), ("140", "Hunaja tai siirappi")]),
   K("dl", "Määrä", 2, "dl")],
  """var g=+v.aine; if(!(g>0)||!(v.dl>=0)) return null;
return [["Grammoina noin",f.n(g*v.dl,0)+" g",1],["Yksi desilitra",f.n(g,0)+" g"],["100 grammaa on",f.n(100/g,1)+" dl"]];""",
  """<p>Leivontaohjeissa aineet ilmoitetaan joko tilavuutena (dl) tai painona (g). Muunnos riippuu aineen tiheydestä: desilitra vehnäjauhoja painaa noin 60 grammaa, mutta desilitra sokeria noin 85 grammaa.</p>
<p>Luvut ovat keskimääräisiä. Jauhojen paino vaihtelee sen mukaan, kuinka tiiviisti ne on mitattu. Kun tarkkuus on tärkeää, esimerkiksi leivässä tai macaronsissa, punnitse aina vaa'alla.</p>""",
  [("Paljonko desilitra jauhoja painaa?", "Vehnäjauhoja noin 60 g, ruisjauhoja noin 65 g."),
   ("Miksi muunnokset vaihtelevat lähteittäin?", "Jauhot painuvat kasaan, joten sama desilitra voi painaa eri määrän riippuen mittaustavasta.")]),
]
