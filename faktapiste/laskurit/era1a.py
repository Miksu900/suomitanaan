"""Erä 1a: raha, lainat ja palkka (puhdasta matematiikkaa, ei viranomaislukuja)."""
from ._yht import K, L

RAHA = "Raha ja lainat"
TYO = "Palkka ja työ"

ERA1A = [
L("lainalaskuri", "Lainalaskuri", RAHA,
  "Lainalaskuri – paljonko lainan kuukausierä on?",
  "Laske lainan kuukausierä, maksettavat korot ja kokonaishinta. Ilmainen lainalaskuri tasaerälainalle ilman rekisteröitymistä.",
  "Syötä lainasumma, korko ja laina-aika, niin näet kuukausierän ja sen, paljonko laina maksaa yhteensä.",
  [K("summa", "Lainasumma", 20000, "€"), K("korko", "Vuosikorko", 5, "%"), K("vuodet", "Laina-aika", 5, "vuotta")],
  """var S=v.summa,r=v.korko/100/12,n=Math.round(v.vuodet*12); if(!(S>0)||!(n>0)||!(r>=0)) return null;
var e=r>0?S*r/(1-Math.pow(1+r,-n)):S/n, yht=e*n;
return [["Kuukausierä",f.e2(e),1],["Maksat yhteensä",f.e(yht)],["Korkoja yhteensä",f.e(yht-S)],["Erien määrä",f.n(n,0)+" kpl"]];""",
  """<p>Laskuri laskee <b>tasaerälainan</b> eli annuiteettilainan kuukausierän. Tasaerälainassa maksat joka kuukausi saman summan, ja erässä on sekä lyhennystä että korkoa. Alussa korkojen osuus on suurempi, ja laina-ajan lopussa erä on lähes kokonaan lyhennystä.</p>
<p>Kaava on <i>erä = S · r / (1 − (1 + r)<sup>−n</sup>)</i>, jossa S on lainasumma, r kuukausikorko ja n erien määrä. Esimerkiksi 20 000 euron laina 5 prosentin korolla viideksi vuodeksi maksaa noin 377 euroa kuukaudessa, ja korkoja kertyy yhteensä noin 2 650 euroa.</p>
<p>Laskelma ei sisällä pankin avausmaksua, tilinhoitomaksuja eikä koron muutoksia. Vaihtuvakorkoisessa lainassa erä muuttuu, kun viitekorko muuttuu.</p>""",
  [("Mitä tasaerälaina tarkoittaa?", "Tasaerälainassa kuukausierä pysyy samana koko laina-ajan, jos korko ei muutu. Erä sisältää lyhennyksen ja koron."),
   ("Miksi korkoja kertyy niin paljon?", "Korko lasketaan jäljellä olevasta lainasta. Mitä pidempi laina-aika, sitä kauemmin maksat korkoa suurelle summalle.")]),

L("asuntolainalaskuri", "Asuntolainalaskuri", RAHA,
  "Asuntolainalaskuri – kuukausierä ja korkojen nousun vaikutus",
  "Laske asuntolainan kuukausierä, korot ja se, paljonko erä nousee, jos korko nousee. Asuntolainalaskuri tasaerälainalle.",
  "Laske asuntolainan kuukausierä ja testaa, mitä tapahtuu, jos korko nousee.",
  [K("summa", "Lainasumma", 200000, "€"), K("korko", "Korko yhteensä (viitekorko + marginaali)", 3.5, "%"), K("vuodet", "Laina-aika", 25, "vuotta"), K("nousu", "Testaa koron nousua", 2, "%-yks.")],
  """var S=v.summa,n=Math.round(v.vuodet*12); if(!(S>0)||!(n>0)) return null;
function era(k){var r=k/100/12;return r>0?S*r/(1-Math.pow(1+r,-n)):S/n;}
var e=era(v.korko), e2=era(v.korko+(v.nousu||0));
return [["Kuukausierä nyt",f.e2(e),1],["Korkoja koko laina-aikana",f.e(e*n-S)],["Erä, jos korko nousee "+f.n(v.nousu||0,1)+" %-yks.",f.e2(e2)],["Erä nousisi",f.e2(e2-e)+" / kk"]];""",
  """<p>Asuntolaina on useimmilla elämän suurin velka, joten kuukausierän lisäksi kannattaa katsoa, miten koron nousu vaikuttaa. Laskuri näyttää erän nykyisellä korolla ja erän, jos korko nousee valitsemasi määrän.</p>
<p>Syötä korkoon <b>koko korko</b> eli viitekorko (esimerkiksi euribor) ja pankin marginaali yhteen laskettuna. Jos viitekorko on 2,5 % ja marginaali 0,8 %, kirjoita 3,3.</p>
<p>Pankit testaavat lainanhakijan maksukyvyn yleensä selvästi nykyistä korkeammalla korolla. Jos erä nousisi niin paljon, ettei se mahtuisi budjettiisi, harkitse pidempää laina-aikaa, pienempää lainaa tai korkosuojaa.</p>""",
  [("Mikä on marginaali?", "Marginaali on pankin oma lisä viitekoron päälle. Se sovitaan lainaa otettaessa ja pysyy yleensä samana koko laina-ajan."),
   ("Kannattaako pidempi laina-aika?", "Pidempi laina-aika pienentää kuukausierää mutta kasvattaa maksettavia korkoja yhteensä.")]),

L("korkoa-korolle", "Korkoa korolle -laskuri", RAHA,
  "Korkoa korolle -laskuri – paljonko säästösi kasvavat?",
  "Laske, paljonko säännöllinen säästäminen ja sijoittaminen kasvaa korkoa korolle. Syötä alkusumma, kuukausisäästö, tuotto ja aika.",
  "Näe, miten säästösi kasvavat, kun tuotto alkaa itse tuottaa.",
  [K("alku", "Alkupääoma", 1000, "€"), K("kk", "Kuukausisäästö", 100, "€"), K("tuotto", "Vuosituotto", 5, "%"), K("vuodet", "Säästöaika", 10, "vuotta")],
  """var P=v.alku||0,m=v.kk||0,n=Math.round(v.vuodet*12),r=v.tuotto/100/12; if(!(n>0)||!(r>-1)) return null;
var a=Math.pow(1+r,n), FV=P*a+(r!==0?m*(a-1)/r:m*n), oma=P+m*n;
return [["Säästöt lopussa",f.e(FV),1],["Omat sijoitukset",f.e(oma)],["Tuottoa kertyi",f.e(FV-oma)]];""",
  """<p>Korkoa korolle tarkoittaa, että saamasi tuotto alkaa itse tuottaa. Mitä pidempään säästät, sitä suurempi osa loppusummasta on tuottoa eikä omaa rahaa.</p>
<p>Esimerkiksi 100 euron kuukausisäästö 5 prosentin vuosituotolla kasvaa 30 vuodessa noin 83 000 euroon, vaikka omaa rahaa on laitettu vain 36 000 euroa.</p>
<p>Laskuri olettaa tasaisen tuoton ja kuukausittaisen korkoutuksen. Todellisuudessa sijoitusten arvo vaihtelee, eikä mennyt tuotto takaa tulevaa. Laskelma ei huomioi veroja eikä kuluja.</p>""",
  [("Mikä tuotto-oletus on realistinen?", "Säästötilillä tuotto on yleensä alle inflaation. Osakesijoittamisen pitkän aikavälin tuotto on historiallisesti ollut korkeampi, mutta vuosittaiset vaihtelut ovat suuria."),
   ("Kannattaako aloittaa pienellä summalla?", "Kyllä. Aika on korkoa korolle -ilmiössä tärkeämpää kuin summa, joten aikainen aloitus pienelläkin summalla on tehokasta.")]),

L("saastolaskuri", "Säästölaskuri", RAHA,
  "Säästölaskuri – paljonko pitää säästää kuukaudessa tavoitteeseen?",
  "Laske, paljonko sinun pitää säästää kuukaudessa, jotta saavutat säästötavoitteesi halutussa ajassa.",
  "Kerro tavoite ja aikataulu, niin laskuri kertoo tarvittavan kuukausisäästön.",
  [K("tavoite", "Säästötavoite", 5000, "€"), K("kuukaudet", "Aikaa", 24, "kuukautta"), K("alku", "Säästöjä jo nyt", 0, "€"), K("tuotto", "Vuosituotto tai korko", 0, "%")],
  """var T=v.tavoite,n=Math.round(v.kuukaudet),P=v.alku||0,r=(v.tuotto||0)/100/12; if(!(T>0)||!(n>0)) return null;
var a=Math.pow(1+r,n), puuttuu=T-P*a, m=r!==0?puuttuu*r/(a-1):puuttuu/n;
if(m<=0) return [["Kuukausisäästö","Tavoite täyttyy jo nykyisillä säästöillä",1]];
return [["Säästä kuukaudessa",f.e2(m),1],["Viikossa",f.e2(m*12/52)],["Päivässä",f.e2(m*12/365)]];""",
  """<p>Säästötavoite on helpompi saavuttaa, kun sen pilkkoo kuukausierään. Laskuri kertoo, paljonko sinun pitää säästää joka kuukausi, jotta tavoite täyttyy ajallaan.</p>
<p>Jos säästöt ovat korkoa tuottavalla tilillä tai sijoituksissa, voit lisätä tuoton. Silloin tarvittava kuukausisäästö pienenee hieman.</p>
<p>Vinkki: tee säästöstä automaattinen. Kun summa siirtyy säästötilille heti palkkapäivänä, sitä ei ehdi käyttää muuhun.</p>""",
  [("Paljonko kannattaa säästää?", "Yleinen nyrkkisääntö on pitää puskurina noin kolmen kuukauden menot. Sen jälkeen voi säästää isompiin tavoitteisiin."),
   ("Mihin säästöt kannattaa laittaa?", "Lyhyen ajan säästöt sopivat säästötilille. Yli viiden vuoden säästöissä voi harkita sijoittamista, mutta arvo voi vaihdella.")]),

L("osamaksulaskuri", "Osamaksulaskuri", RAHA,
  "Osamaksulaskuri – todellinen vuosikorko ja luoton hinta",
  "Laske osamaksun todellinen vuosikorko ja paljonko maksat lisää käteishintaan verrattuna. Vertaa osamaksua ja käteisostoa.",
  "Selvitä, paljonko osamaksu oikeasti maksaa, ja vertaa sitä käteisostoon.",
  [K("hinta", "Käteishinta", 1500, "€"), K("kasiraha", "Käsiraha", 0, "€"), K("era", "Kuukausierä", 70, "€"), K("kk", "Erien määrä", 24, "kpl"), K("avaus", "Avaus- ja muut kertamaksut", 0, "€")],
  """var L=v.hinta-(v.kasiraha||0)-(v.avaus||0),e=v.era,n=Math.round(v.kk); if(!(L>0)||!(e>0)||!(n>0)) return null;
var yht=(v.kasiraha||0)+(v.avaus||0)+e*n; if(e*n<=L) return [["Maksat yhteensä",f.e(yht),1],["Luoton hinta","ei lisäkuluja"]];
function nv(i){return e*(1-Math.pow(1+i,-n))/i-L;} var a=1e-6,b=1; for(var k=0;k<200;k++){var c=(a+b)/2; if(nv(c)>0) a=c; else b=c;}
var vk=Math.pow(1+(a+b)/2,12)-1;
return [["Todellinen vuosikorko",f.p(vk*100),1],["Maksat yhteensä",f.e(yht)],["Luoton hinta",f.e(yht-v.hinta)],["Lisähinta käteiseen verrattuna",f.p((yht-v.hinta)/v.hinta*100)]];""",
  """<p>Osamaksu näyttää usein edulliselta, koska kuukausierä on pieni. Todellinen hinta paljastuu vasta, kun laskee kaikki erät ja maksut yhteen ja vertaa niitä käteishintaan.</p>
<p><b>Todellinen vuosikorko</b> kertoo luoton kokonaiskustannuksen vuotuisena korkona, johon on laskettu mukaan myös avaus- ja muut kertamaksut. Sen avulla eri luottoja voi verrata keskenään. Laskuri ratkaisee todellisen vuosikoron numeerisesti erien perusteella.</p>
<p>Laskuri ei huomioi kuukausittaisia laskutus- tai tilinhoitomaksuja. Jos sellaisia on, lisää ne kuukausierään. Myyjän ilmoittama todellinen vuosikorko on aina sitova.</p>""",
  [("Mikä on hyvä todellinen vuosikorko?", "Mitä pienempi, sitä parempi. Jos vuosikorko on kymmeniä prosentteja, säästäminen ja käteisosto tulee lähes aina halvemmaksi."),
   ("Onko korottomassa osamaksussa kuluja?", "Usein on avaus- tai laskutusmaksu. Lisää ne laskuriin, niin näet todellisen hinnan.")]),

L("prosenttilaskuri", "Prosenttilaskuri", RAHA,
  "Prosenttilaskuri – laske prosentti luvusta, alennus ja korotus",
  "Laske nopeasti, paljonko on X % luvusta, sekä hinta alennuksen tai korotuksen jälkeen. Helppo prosenttilaskuri.",
  "Laske prosenttiosuus, alennettu hinta ja korotettu hinta kerralla.",
  [K("luku", "Luku tai hinta", 250, ""), K("prosentti", "Prosentti", 20, "%")],
  """var x=v.luku,p=v.prosentti; if(!isFinite(x)||!isFinite(p)) return null; var o=x*p/100;
return [[f.n(p,1)+" % luvusta "+f.n(x,2),f.n(o,2),1],["Luku + "+f.n(p,1)+" %",f.n(x+o,2)],["Luku − "+f.n(p,1)+" % (alennus)",f.n(x-o,2)],["Kuinka monta % "+f.n(p,1)+" on luvusta "+f.n(x,2),f.p(x!==0?p/x*100:NaN,2)]];""",
  """<p>Prosenttilaskuri laskee yleisimmät prosenttilaskut yhdellä kertaa: paljonko on tietty prosentti luvusta, mitä luku on korotuksen jälkeen ja paljonko jää alennuksen jälkeen.</p>
<p>Esimerkki: tuote maksaa 250 euroa, ja alennus on 20 %. Alennus on 50 euroa, ja hinnaksi jää 200 euroa.</p>
<p>Muista, että prosenttimuutokset eivät kumoa toisiaan. Jos hinta nousee 20 % ja laskee sitten 20 %, lopputulos on 4 % alkuperäistä pienempi.</p>""",
  [("Miten prosentti lasketaan luvusta?", "Kerro luku prosentilla ja jaa sadalla. Esimerkiksi 20 % luvusta 250 on 250 × 20 / 100 = 50."),
   ("Miten alennus lasketaan?", "Vähennä alkuperäisestä hinnasta alennuksen määrä, tai kerro hinta luvulla (1 − alennus/100).")]),

L("prosenttimuutos", "Prosenttimuutos-laskuri", RAHA,
  "Prosenttimuutos – laske muutos prosentteina kahden luvun välillä",
  "Laske, montako prosenttia luku on noussut tai laskenut. Prosenttimuutoslaskuri hinnoille, palkoille ja muille luvuille.",
  "Vertaa vanhaa ja uutta lukua ja näe muutos prosentteina.",
  [K("vanha", "Vanha arvo", 80, ""), K("uusi", "Uusi arvo", 100, "")],
  """var a=v.vanha,b=v.uusi; if(!isFinite(a)||!isFinite(b)||a===0) return null; var m=(b-a)/Math.abs(a)*100;
return [["Muutos",(m>0?"+":"")+f.p(m,2),1],["Ero",(b-a>0?"+":"")+f.n(b-a,2)],["Uusi arvo on vanhasta",f.p(b/a*100,2)]];""",
  """<p>Prosenttimuutos kertoo, kuinka paljon luku on muuttunut suhteessa alkuperäiseen. Kaava on <i>(uusi − vanha) / vanha × 100</i>.</p>
<p>Esimerkki: jos hinta nousee 80 eurosta 100 euroon, muutos on (100 − 80) / 80 × 100 = 25 %. Jos hinta laskee 100 eurosta 80 euroon, muutos on −20 %. Sama euromäärä on siis eri prosenttimäärä riippuen siitä, mistä lähdetään.</p>
<p>Prosenttimuutos ei ole sama asia kuin prosenttiyksikkö. Jos korko nousee 2 %:sta 3 %:iin, se nousee yhden prosenttiyksikön mutta 50 prosenttia.</p>""",
  [("Mikä ero on prosentilla ja prosenttiyksiköllä?", "Prosenttiyksikkö on kahden prosenttiluvun erotus. Prosentti kertoo suhteellisen muutoksen."),
   ("Miksi nousu ja lasku eivät ole samat?", "Koska prosentti lasketaan aina lähtöarvosta, ja lähtöarvo on eri suunnasta katsottuna eri.")]),

L("katelaskuri", "Katelaskuri", RAHA,
  "Katelaskuri – myyntihinta, kate ja kateprosentti",
  "Laske tuotteen myyntihinta halutulla kateprosentilla tai kate ostohinnan ja myyntihinnan perusteella. Katelaskuri yrittäjälle.",
  "Laske myyntihinta, kate ja hinnoittelukerroin ostohinnasta.",
  [K("osto", "Ostohinta (veroton)", 50, "€"), K("kate", "Tavoiteltu kateprosentti", 30, "%")],
  """var o=v.osto,k=v.kate/100; if(!(o>0)||!(k<1)||!(k>=0)) return null; var m=o/(1-k);
return [["Myyntihinta (veroton)",f.e2(m),1],["Kate euroina",f.e2(m-o)],["Hinnoittelukerroin",f.n(m/o,3)+" ×"],["Lisäys ostohintaan",f.p((m-o)/o*100)]];""",
  """<p><b>Kateprosentti</b> lasketaan myyntihinnasta: kate / myyntihinta × 100. Siksi 30 %:n kate ei tarkoita, että ostohintaan lisätään 30 %. Oikea myyntihinta on ostohinta / (1 − 0,30), eli 50 euron tuote myydään noin 71,43 eurolla.</p>
<p>Ero kateprosentin ja lisäyksen välillä on yleinen virhe hinnoittelussa. Jos lisäät ostohintaan 30 %, kateprosentiksi jää vain noin 23 %.</p>
<p>Laskuri käsittelee verottomia hintoja. Lisää arvonlisävero myyntihintaan erikseen, jos myyt kuluttajille.</p>""",
  [("Mikä ero on katteella ja lisäyksellä?", "Kate lasketaan myyntihinnasta, lisäys (markup) ostohinnasta. Sama euromäärä on siksi eri prosentti."),
   ("Mikä on hyvä kateprosentti?", "Se riippuu alasta. Kaupassa kate voi olla 20–50 %, palveluissa enemmän. Katteen pitää kattaa kaikki muut kulut ja voitto.")]),

L("tuntipalkka-kuukausipalkaksi", "Tuntipalkka kuukausipalkaksi", TYO,
  "Tuntipalkka kuukausipalkaksi – paljonko tuntipalkka on kuukaudessa?",
  "Muunna tuntipalkka kuukausi- ja vuosipalkaksi viikkotuntien mukaan. Laskuri tuntipalkan ja kuukausipalkan vertailuun.",
  "Muunna tuntipalkka kuukausi- ja vuosipalkaksi.",
  [K("tunti", "Tuntipalkka", 15, "€/h"), K("tunnit", "Työtunnit viikossa", 37.5, "h")],
  """var t=v.tunti,h=v.tunnit; if(!(t>0)||!(h>0)) return null; var kk=t*h*52/12;
return [["Kuukausipalkka",f.e(kk),1],["Vuosipalkka",f.e(t*h*52)],["Viikkopalkka",f.e2(t*h)]];""",
  """<p>Kuukausipalkka saadaan kertomalla tuntipalkka viikkotunneilla ja viikkojen määrällä vuodessa (52) ja jakamalla 12 kuukaudella. Kuukaudessa on keskimäärin noin 4,33 viikkoa.</p>
<p>Esimerkki: 15 euron tuntipalkka ja 37,5 tunnin työviikko tekevät noin 2 440 euroa kuukaudessa.</p>
<p>Luku on bruttopalkka eli palkka ennen veroja. Laskuri ei huomioi lomarahaa, ilta- tai viikonloppulisiä eikä ylitöitä.</p>""",
  [("Montako tuntia kuukaudessa on?", "Kokoaikatyössä noin 160 tuntia: 37,5 h × 52 viikkoa / 12 kuukautta ≈ 162,5 tuntia."),
   ("Onko tämä nettopalkka?", "Ei. Tulos on bruttopalkka. Verot ja työntekijän maksut vähennetään tästä.")]),

L("kuukausipalkka-tuntipalkaksi", "Kuukausipalkka tuntipalkaksi", TYO,
  "Kuukausipalkka tuntipalkaksi – mikä on tuntipalkkasi?",
  "Laske, mikä on kuukausipalkkasi tuntipalkkana. Vertaa töitä ja tarjouksia tuntipalkan perusteella.",
  "Selvitä, mitä kuukausipalkkasi on tuntia kohden.",
  [K("kk", "Kuukausipalkka", 3000, "€"), K("tunnit", "Työtunnit viikossa", 37.5, "h")],
  """var k=v.kk,h=v.tunnit; if(!(k>0)||!(h>0)) return null; var t=k*12/(h*52);
return [["Tuntipalkka",f.e2(t),1],["Vuosipalkka",f.e(k*12)],["Tunteja kuukaudessa",f.n(h*52/12,1)+" h"]];""",
  """<p>Tuntipalkka lasketaan jakamalla vuosipalkka vuoden työtunneilla: <i>kuukausipalkka × 12 / (viikkotunnit × 52)</i>.</p>
<p>Esimerkki: 3 000 euron kuukausipalkka 37,5 tunnin viikoilla on noin 18,46 euroa tunnilta.</p>
<p>Tuntipalkan avulla on helppo verrata töitä, joissa on eri työaika, tai arvioida, kannattaako ylimääräinen keikka.</p>""",
  [("Pitäisikö lomat vähentää tunneista?", "Kuukausipalkkaa maksetaan myös lomalta, joten tavallisessa vertailussa lomia ei vähennetä."),
   ("Miksi tuntipalkka tuntuu pieneltä?", "Muista, että tulos on bruttopalkkaa. Lisäksi työnantaja maksaa sivukuluja palkan päälle.")]),

L("palkankorotuslaskuri", "Palkankorotuslaskuri", TYO,
  "Palkankorotuslaskuri – paljonko korotus on euroina?",
  "Laske, paljonko prosenttikorotus nostaa palkkaasi kuukaudessa ja vuodessa. Palkankorotuslaskuri yleiskorotuksille.",
  "Näe, mitä prosenttikorotus tarkoittaa euroina.",
  [K("palkka", "Nykyinen kuukausipalkka", 3000, "€"), K("korotus", "Korotus", 3, "%")],
  """var p=v.palkka,k=v.korotus; if(!(p>0)||!isFinite(k)) return null; var u=p*(1+k/100);
return [["Uusi kuukausipalkka",f.e2(u),1],["Korotus kuukaudessa",f.e2(u-p)],["Korotus vuodessa",f.e(12*(u-p))]];""",
  """<p>Palkankorotus ilmoitetaan usein prosentteina. Laskuri muuttaa sen euroiksi kuukautta ja vuotta kohden.</p>
<p>Esimerkki: 3 prosentin korotus 3 000 euron palkkaan tekee 90 euroa kuukaudessa ja 1 080 euroa vuodessa ennen veroja.</p>
<p>Huomaa, että korotus on bruttona. Käteen jäävä osuus on pienempi, koska korotukseen sovelletaan marginaaliveroprosenttia, joka on yleensä suurempi kuin keskimääräinen veroprosenttisi.</p>""",
  [("Paljonko korotuksesta jää käteen?", "Se riippuu marginaaliverostasi. Keskituloisella korotuksesta jää käteen tyypillisesti noin 55–65 %."),
   ("Mikä on yleiskorotus?", "Yleiskorotus on työehtosopimuksessa sovittu korotus, joka koskee kaikkia sopimuksen piirissä olevia.")]),

L("tyoaikalaskuri", "Työaikalaskuri", TYO,
  "Työaikalaskuri – laske työtunnit kellonajoista",
  "Laske työpäivän pituus aloitus- ja lopetusajasta tauot vähentäen. Työaikalaskuri tuntikirjanpitoon ja palkan tarkistukseen.",
  "Laske, montako tuntia työpäiväsi kesti.",
  [K("alku", "Aloitus", "08:00", "", tyyppi="aika"), K("loppu", "Lopetus", "16:00", "", tyyppi="aika"), K("tauko", "Palkattomat tauot", 30, "min"), K("tunti", "Tuntipalkka (valinnainen)", "", "€/h")],
  """function m(s){var x=String(s||"").split(":");return x.length<2?NaN:(+x[0])*60+(+x[1]);}
var a=m(v.alku),b=m(v.loppu); if(!isFinite(a)||!isFinite(b)) return null; if(b<=a) b+=1440; var t=b-a-(v.tauko||0); if(t<=0) return null;
var r=[["Työaika",Math.floor(t/60)+" h "+(t%60)+" min",1],["Desimaalitunteina",f.n(t/60,2)+" h"]]; if(v.tunti>0) r.push(["Palkka (brutto)",f.e2(t/60*v.tunti)]); return r;""",
  """<p>Työaikalaskuri laskee työpäivän pituuden aloitus- ja lopetusajasta ja vähentää palkattomat tauot. Laskuri toimii myös yövuoroissa, jotka jatkuvat yli puolenyön.</p>
<p>Tunnit näytetään sekä tunteina ja minuutteina että desimaalitunteina. Desimaalitunteja tarvitaan, kun palkka lasketaan tuntipalkasta: esimerkiksi 7 h 30 min on 7,5 tuntia.</p>
<p>Työehtosopimukset määräävät, mitkä tauot ovat palkallisia. Kahvitauot ovat yleensä palkallisia, ruokatauko usein ei.</p>""",
  [("Miten minuutit muutetaan desimaaleiksi?", "Jaa minuutit kuudellakymmenellä. Esimerkiksi 45 minuuttia on 0,75 tuntia."),
   ("Lasketaanko yövuoro oikein?", "Kyllä. Jos lopetusaika on aikaisempi kuin aloitus, laskuri olettaa vuoron jatkuvan seuraavaan päivään.")]),
]
