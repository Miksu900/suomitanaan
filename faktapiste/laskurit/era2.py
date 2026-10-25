"""Erä 2: suomalaiset vero- ja etuuslaskurit. Luvut tarkistettu Verohallinnon ja Veronmaksajien lähteistä (2026).

Lähteet ja voimassaolo:
- Perintövero 2026 (kuolinpäivä 1.1.2026 alkaen): I ja II veroluokan asteikot, verovapaa alle 30 000 €,
  puolisovähennys 90 000 €, alaikäisyysvähennys 60 000 € (vain I luokka). Lähde: Veronmaksajat / vero.fi.
- Lahjavero 2026 (lahja 1.1.2026 alkaen): verovapaa alle 7 500 €, saman antajan 3 v lahjat yhteen. Lähde: Veronmaksajat.
- Varainsiirtovero: asunto-osake 1,5 % (velattomasta hinnasta), kiinteistö 3 %, muut arvopaperit 1,5 %;
  ensiasunnon vapautus poistui 1.1.2024. Lähde: vero.fi / Veronmaksajat.
- ALV 2026: yleinen 25,5 %, alennettu 13,5 % (1.1.2026 alkaen), 10 % lehdet. Lähde: vero.fi.
- Kotitalousvähennys 2026: ostettu työ 40 %, palkkatyö 15 %, enimmäismäärä 2 100 €/hlö, omavastuu 150 €. Lähde: vero.fi.
- Kilometrikorvaus 2026: auto 55 snt/km, moottoripyörä 42, mopo 23; lisät perävaunu +9, matkustaja +4. Lähde: Verohallinnon päätös 2026.
"""
from ._yht import K, L

VERO = "Verot"
ETU = "Vähennykset ja korvaukset"

# Progressiivinen asteikko JS-muodossa: [alaraja, vakioero alarajalla, % ylittävästä]
PERINTO_I = "[[30000,100,7],[40000,800,10],[60000,2800,13],[200000,21000,16],[1000000,149000,19]]"
PERINTO_II = "[[30000,100,19],[40000,2000,25],[60000,7000,29],[200000,47600,31],[1000000,295600,33]]"
LAHJA_I = "[[7500,100,8],[25000,1500,10],[55000,4500,12],[200000,21900,15],[1000000,141900,17]]"
LAHJA_II = "[[7500,100,19],[25000,3425,25],[55000,10925,29],[200000,52975,31],[1000000,300975,33]]"

_ASTEIKKO = "function vero(x,a){var t=0;for(var i=0;i<a.length;i++){if(x>=a[i][0]) t=a[i][1]+(x-a[i][0])*a[i][2]/100;}return x<a[0][0]?0:t;}"

ERA2 = [
L("perintoverolaskuri", "Perintöverolaskuri", VERO,
  "Perintöverolaskuri 2026 – laske perintövero osuudestasi",
  "Laske perintövero vuoden 2026 asteikolla. Huomioi veroluokka, puolisovähennys ja alaikäisyysvähennys. Ilmainen perintöverolaskuri.",
  "Laske, paljonko perintöverosi on vuoden 2026 asteikon mukaan.",
  [K("osuus", "Perintöosuutesi arvo", 60000, "€"),
   K("luokka", "Suhde vainajaan", "1", "", valinnat=[("1", "Lapsi, puoliso, vanhempi tai lapsenlapsi (I luokka)"), ("2", "Sisarus tai muu sukulainen (II luokka)")]),
   K("puoliso", "Olen vainajan puoliso (−90 000 €)", False, ""),
   K("alaikainen", "Olen alle 18-v. lapsi (−60 000 €)", False, "")],
  _ASTEIKKO + """
var o=v.osuus; if(!(o>=0)) return null;
var I=""" + PERINTO_I + """,II=""" + PERINTO_II + """;
var vah=0; if(v.luokka==="1"){ if(v.puoliso) vah+=90000; if(v.alaikainen) vah+=60000; }
var pohja=Math.max(0,o-vah), t=v.luokka==="1"?vero(pohja,I):vero(pohja,II);
var r=[["Perintövero",f.e(t),1]];
if(vah>0) r.push(["Vähennykset",f.e(vah)],["Verotettava osuus",f.e(pohja)]);
r.push(["Veroluokka",v.luokka==="1"?"I luokka":"II luokka"]);
r.push(["Käteen jää",f.e(o-t)]);
if(pohja<30000&&pohja>0) r[0]=["Perintövero","0 € (alle 30 000 €:n verovapaa raja)",1];
return r;""",
  """<p>Perintövero lasketaan jokaisen perillisen oman perintöosuuden arvosta, ei koko kuolinpesän arvosta. Vuonna 2026 (kuolinpäivä 1.1.2026 tai myöhemmin) perintöosuus on verovapaa, jos se on <b>alle 30 000 euroa</b>.</p>
<p><b>Veroluokat:</b> I luokkaan kuuluvat lapset, puoliso, vanhemmat ja lapsenlapset. II luokkaan kuuluvat sisarukset ja muut sukulaiset, ja heillä vero on selvästi korkeampi.</p>
<p><b>Vähennykset:</b> vainajan puoliso saa 90 000 euron puolisovähennyksen ja alle 18-vuotias suoraan alenevassa polvessa oleva perillinen 60 000 euron alaikäisyysvähennyksen. Vähennys tehdään ennen veron laskemista.</p>
<p>Laskuri antaa suuntaa antavan arvion vuoden 2026 asteikolla. Se ei huomioi hallintaoikeusvähennystä, henkivakuutuskorvauksia eikä muita erityistilanteita. Verohallinto laskee lopullisen veron perukirjan perusteella.</p>""",
  [("Lasketaanko vero koko perinnöstä?", "Ei. Vero lasketaan kunkin perillisen omasta osuudesta erikseen. Siksi usealle jaettu perintö verotetaan kevyemmin kuin yhdelle jäävä."),
   ("Milloin perintö on verovapaa?", "Kun oma perintöosuus on alle 30 000 euroa. Puoliso- ja alaikäisyysvähennys voivat nostaa verovapaan määrän tätä suuremmaksi."),
   ("Mikä on I ja II veroluokan ero?", "I luokka koskee lähiomaisia ja on edullisempi. II luokka koskee kaukaisempia sukulaisia ja muita, ja siinä veroprosentit ovat noin kaksinkertaiset.")]),

L("lahjaverolaskuri", "Lahjaverolaskuri", VERO,
  "Lahjaverolaskuri 2026 – laske lahjavero",
  "Laske lahjavero vuoden 2026 asteikolla. Verovapaa raja 7 500 €, saman antajan lahjat lasketaan yhteen kolmen vuoden ajalta.",
  "Laske lahjavero vuoden 2026 asteikon mukaan.",
  [K("summa", "Lahjan arvo", 10000, "€"),
   K("luokka", "Suhde antajaan", "1", "", valinnat=[("1", "Lapsi, puoliso, vanhempi tai lapsenlapsi (I luokka)"), ("2", "Muu sukulainen tai ulkopuolinen (II luokka)")]),
   K("aiemmat", "Saman antajan lahjat viim. 3 v", 0, "€")],
  _ASTEIKKO + """
var s=v.summa+(v.aiemmat||0); if(!(v.summa>=0)) return null;
var I=""" + LAHJA_I + """,II=""" + LAHJA_II + """,a=v.luokka==="1"?I:II;
var koko=vero(s,a), aiempi=vero(v.aiemmat||0,a), t=Math.max(0,koko-aiempi);
var r=[["Lahjavero",f.e(t),1]];
if(v.aiemmat>0) r.push(["Yhteenlaskettu arvo",f.e(s)],["Aiemmista jo maksettu",f.e(aiempi)]);
r.push(["Veroluokka",v.luokka==="1"?"I luokka":"II luokka"]);
if(s<7500) r[0]=["Lahjavero","0 € (alle 7 500 €:n verovapaa raja)",1];
return r;""",
  """<p>Lahjavero maksetaan, kun samalta antajalta saatujen lahjojen arvo on <b>7 500 euroa tai enemmän kolmen vuoden aikana</b>. Raja nousi 5 000 eurosta vuoden 2026 alussa. Alle rajan jäävät lahjat ovat verovapaita.</p>
<p>Kolmen vuoden sääntö estää veron kiertämisen pilkkomalla lahja moneen osaan. Jos saat samalta henkilöltä useita lahjoja kolmen vuoden sisällä, ne lasketaan yhteen ja vero määräytyy yhteissummasta. Laskuri vähentää aiemmista lahjoista jo maksetun veron.</p>
<p>Puolisot katsotaan erillisiksi antajiksi, joten kummaltakin vanhemmalta voi saada erikseen alle 7 500 euroa verovapaasti. Laskuri antaa suuntaa antavan arvion vuoden 2026 asteikolla.</p>""",
  [("Paljonko voi lahjoittaa verovapaasti?", "Alle 7 500 euroa samalta antajalta kolmen vuoden aikana. Molemmilta vanhemmilta erikseen, joten pari voi antaa yhteensä lähes 15 000 euroa verovapaasti."),
   ("Lasketaanko lahjat yhteen?", "Kyllä. Saman antajan lahjat kolmen vuoden ajalta lasketaan yhteen, ja vero määräytyy yhteissummasta."),
   ("Kuka maksaa lahjaveron?", "Lahjan saaja. Saajan pitää tehdä lahjaveroilmoitus, jos raja ylittyy.")]),

L("varainsiirtoverolaskuri", "Varainsiirtoverolaskuri", VERO,
  "Varainsiirtoverolaskuri 2026 – asunto, kiinteistö ja osakkeet",
  "Laske varainsiirtovero asunnon, kiinteistön tai arvopaperien kaupasta. Asunto-osake 1,5 %, kiinteistö 3 %. Huomioi velaton hinta.",
  "Laske, paljonko varainsiirtoveroa maksat kaupasta.",
  [K("tyyppi", "Mitä ostat", "1.5", "", valinnat=[("1.5", "Asunto-osake (kerros- tai rivitalo)"), ("3", "Kiinteistö (omakotitalo, tontti, kesämökki)"), ("1.5o", "Muut arvopaperit")]),
   K("hinta", "Kauppahinta", 150000, "€"),
   K("velka", "Osuus taloyhtiön lainasta (vain asunto-osake)", 0, "€")],
  """var h=v.hinta; if(!(h>=0)) return null; var p=parseFloat(v.tyyppi), asunto=String(v.tyyppi).indexOf("1.5")===0&&v.tyyppi!=="3";
var pohja=v.tyyppi==="1.5"?h+(v.velka||0):h, t=pohja*p/100;
var r=[["Varainsiirtovero",f.e(t),1],["Veroprosentti",f.n(p,1)+" %"]];
if(v.tyyppi==="1.5"&&v.velka>0) r.push(["Velaton hinta (veron peruste)",f.e(pohja)]);
if(t<10) r.push(["Huom.","Alle 10 € veroa ei makseta, mutta ilmoitus on tehtävä"]);
return r;""",
  """<p>Varainsiirtovero maksetaan asunnon, kiinteistön tai arvopaperien ostosta. Prosentit ovat: <b>asunto-osake 1,5 %</b> (kerros- ja rivitaloasunnot asunto-osakeyhtiössä), <b>kiinteistö 3 %</b> (omakotitalo, tontti, kesämökki) ja muut arvopaperit 1,5 %.</p>
<p><b>Tärkeää asunto-osakkeissa:</b> vero lasketaan velattomasta hinnasta, eli kauppahintaan lisätään osuus taloyhtiön lainasta. Jos velkaosuus jää huomioimatta, vero arvioituu liian pieneksi.</p>
<p>Ensiasunnon ostajan verovapaus poistui 1.1.2024, joten myös ensiasunnosta maksetaan varainsiirtovero. Veron maksaa ostaja. Alle 10 euron veroa ei makseta, mutta varainsiirtoveroilmoitus pitää silti tehdä.</p>""",
  [("Lasketaanko vero velattomasta hinnasta?", "Asunto-osakkeissa kyllä: kauppahintaan lisätään osuus taloyhtiön lainasta. Kiinteistöissä vero lasketaan kauppahinnasta."),
   ("Onko ensiasunto verovapaa?", "Ei enää. Ensiasunnon ostajan vapautus poistui vuoden 2024 alussa."),
   ("Milloin vero pitää maksaa?", "Asunto-osakkeesta yleensä kahden kuukauden kuluessa kaupasta, kiinteistöstä ennen lainhuudon hakemista. Tarkista määräaika Verohallinnolta.")]),

L("alv-laskuri", "ALV-laskuri", VERO,
  "ALV-laskuri 2026 – lisää tai erota arvonlisävero",
  "Laske arvonlisävero hintaan tai erota ALV verollisesta hinnasta. Verokannat 2026: 25,5 %, 13,5 % ja 10 %. Ilmainen ALV-laskuri.",
  "Lisää ALV verottomaan hintaan tai erota se verollisesta.",
  [K("hinta", "Hinta", 100, "€"),
   K("suunta", "Hinta on", "veroton", "", valinnat=[("veroton", "Veroton (lisää ALV)"), ("verollinen", "Verollinen (erota ALV)")]),
   K("kanta", "Verokanta", "25.5", "", valinnat=[("25.5", "25,5 % – yleinen"), ("13.5", "13,5 % – ruoka, ravintola, kirjat, lääkkeet, kuljetus"), ("10", "10 % – lehdet")])],
  """var h=v.hinta,p=parseFloat(v.kanta)/100; if(!(h>=0)) return null;
var veroton,verollinen; if(v.suunta==="verollinen"){ verollinen=h; veroton=h/(1+p); } else { veroton=h; verollinen=h*(1+p); }
return [["Verollinen hinta",f.e2(verollinen),1],["Veroton hinta",f.e2(veroton)],["ALV:n osuus",f.e2(verollinen-veroton)],["Verokanta",f.n(p*100,1)+" %"]];""",
  """<p>Arvonlisävero lisätään useimpien tavaroiden ja palveluiden hintaan. Suomen verokannat vuonna 2026 ovat:</p>
<ul><li><b>25,5 %</b> – yleinen verokanta, useimmat tavarat ja palvelut</li>
<li><b>13,5 %</b> – elintarvikkeet, ravintolaruoka, kirjat, lääkkeet, henkilökuljetukset, liikunta ja majoitus (laski 14 %:sta 1.1.2026)</li>
<li><b>10 %</b> – sanoma- ja aikakauslehdet</li></ul>
<p>Veron lisääminen: verollinen hinta = veroton × (1 + verokanta). Veron erottaminen: veroton hinta = verollinen / (1 + verokanta). Yleinen virhe on vähentää verokanta suoraan verollisesta hinnasta, mikä antaa väärän tuloksen.</p>""",
  [("Mikä on yleinen ALV-kanta 2026?", "25,5 %. Se on ollut voimassa 1.9.2024 alkaen."),
   ("Miten ALV erotetaan hinnasta?", "Jaa verollinen hinta luvulla (1 + verokanta). Esimerkiksi 25,5 %:n kannassa jaetaan 1,255:llä."),
   ("Mihin sovelletaan 13,5 %:n kantaa?", "Muun muassa elintarvikkeisiin, ravintolaruokaan, kirjoihin, lääkkeisiin ja henkilökuljetuksiin. Kanta laski 14 %:sta 13,5 %:iin vuoden 2026 alussa.")]),

L("kotitalousvahennys", "Kotitalousvähennyslaskuri", ETU,
  "Kotitalousvähennyslaskuri 2026 – paljonko saat vähentää?",
  "Laske kotitalousvähennys vuonna 2026: remontti, siivous ja hoivatyö. Vähennys 40 % ostetusta työstä, enintään 2 100 € henkilöltä.",
  "Laske, paljonko kotitalousvähennystä saat työn hinnasta.",
  [K("tyyppi", "Työn teki", "yritys", "", valinnat=[("yritys", "Yritys (lasku) – 40 %"), ("palkka", "Palkattu työntekijä – 15 %")]),
   K("tyo", "Työn osuus laskusta (ei tarvikkeet)", 3000, "€"),
   K("sivukulut", "Palkan sivukulut (vain palkkatyö)", 0, "€"),
   K("henkiloita", "Montako henkilöä hakee (esim. puolisot)", 1, "hlö")],
  """var hlo=Math.max(1,Math.round(v.henkiloita||1));
var raaka=v.tyyppi==="yritys"?(v.tyo||0)*0.40:((v.tyo||0)+(v.sivukulut||0))*0.15;
var katto=2100*hlo, ennenOma=Math.min(raaka,katto), vah=Math.max(0,ennenOma-150*hlo);
if(!(v.tyo>=0)) return null;
return [["Vähennys pienentää veroa",f.e(vah),1],["Vähennys ennen omavastuuta",f.e(ennenOma)],["Omavastuu",f.e(150*hlo)],["Enimmäismäärä",f.e(katto)]];""",
  """<p>Kotitalousvähennys pienentää veroa, kun teetät kotona remonttia, siivousta tai hoivatyötä. Vuonna 2026 vähennys on <b>40 % yritykseltä ostetun työn osuudesta</b> tai 15 % palkatulle työntekijälle maksetusta palkasta ja sivukuluista. Vähennysprosentteja korotettiin vuosille 2026–2027.</p>
<p>Vähennetään vain <b>työn osuus</b>, ei tarvikkeita tai matkoja. Enimmäismäärä on 2 100 euroa henkilöä kohden, ja omavastuu 150 euroa vähennetään kerran vuodessa. Puolisot voivat hakea vähennystä erikseen, jolloin yhteinen enimmäismäärä on 4 200 euroa.</p>
<p>Vähennys tehdään verotuksessa, eli se pienentää maksettavia veroja suoraan. Laskuri antaa suuntaa antavan arvion; lopullisen vähennyksen vahvistaa Verohallinto.</p>""",
  [("Paljonko kotitalousvähennys on 2026?", "40 % yritykseltä ostetun työn osuudesta, enintään 2 100 euroa henkilöltä, omavastuu 150 euroa."),
   ("Voiko tarvikkeet vähentää?", "Ei. Vähennyksen saa vain työn osuudesta. Pyydä laskuun eroteltuna työ ja tarvikkeet."),
   ("Voivatko puolisot molemmat hakea?", "Kyllä. Silloin yhteinen enimmäismäärä on 4 200 euroa ja omavastuu 150 euroa kummallekin.")]),

L("kilometrikorvaus", "Kilometrikorvauslaskuri", ETU,
  "Kilometrikorvaus 2026 – laske verovapaa korvaus",
  "Laske verovapaa kilometrikorvaus 2026. Auto 55 snt/km, lisät perävaunusta ja matkustajista. Kilometrikorvauslaskuri työmatkoille.",
  "Laske verovapaa kilometrikorvaus työmatkasta.",
  [K("km", "Ajetut kilometrit", 100, "km"),
   K("neuvo", "Kulkuneuvo", "55", "", valinnat=[("55", "Auto – 55 snt/km"), ("42", "Moottoripyörä – 42 snt/km"), ("23", "Mopo – 23 snt/km"), ("13", "Muu kulkuneuvo – 13 snt/km")]),
   K("peravaunu", "Perävaunu autossa (+9 snt/km)", False, ""),
   K("matkustajat", "Työnantajan vastuulla olevia matkustajia (+4 snt/km/hlö)", 0, "hlö")],
  """var km=v.km; if(!(km>=0)) return null; var snt=parseFloat(v.neuvo);
if(v.neuvo==="55"){ if(v.peravaunu) snt+=9; snt+=4*Math.max(0,Math.round(v.matkustajat||0)); }
var e=km*snt/100;
return [["Verovapaa korvaus",f.e2(e),1],["Korvaus kilometriltä",f.n(snt,0)+" snt/km"],["Ajomatka",f.n(km,0)+" km"],["Meno-paluu (2 × matka)",f.e2(e*2)]];""",
  """<p>Työnantaja voi maksaa työmatkasta verovapaata kilometrikorvausta oman auton käytöstä. Vuonna 2026 enimmäismäärä omalla autolla on <b>55 senttiä kilometriltä</b>. Moottoripyörällä korvaus on 42, mopolla 23 ja muulla kulkuneuvolla 13 senttiä kilometriltä.</p>
<p>Autolla korvausta korotetaan tietyissä tilanteissa: perävaunu +9 snt/km ja jokainen työnantajan vastuulla kuljetettava matkustaja +4 snt/km. Lisäksi on erityiskorotuksia esimerkiksi raskaalle kuormalle ja metsäautotielle.</p>
<p>Korvaus on verovapaa vain todellisista työajoista, ei kodin ja työpaikan välisestä matkasta. Yli enimmäismäärän maksettu osa on veronalaista palkkaa. Työehtosopimus voi määrätä tätä pienemmän korvauksen.</p>""",
  [("Paljonko kilometrikorvaus on 2026?", "Omalla autolla enintään 55 senttiä kilometriltä verovapaana."),
   ("Saako työmatkasta kotoa töihin korvausta?", "Ei verovapaana. Kilometrikorvaus koskee työajoja, ei päivittäistä työmatkaa."),
   ("Mitä lisiä korvaukseen voi saada?", "Autolla esimerkiksi perävaunusta +9 snt/km ja matkustajista +4 snt/km kutakin kohden.")]),
]
