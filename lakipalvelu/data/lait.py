#!/usr/bin/env python3
"""Hakee valitut lait Finlexin avoimesta datasta (ajantasainen lainsäädäntö) ja pilkkoo ne pykäliksi.
Tulos: public/data/lait.json (luettelo) ja public/data/laki/<vuosi>-<nro>.json (pykälät)."""
import io, json, os, re, sys, time, zipfile, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data")
UA = {"User-Agent": "Pykalavahti/1.0 (miika@eduskuntaseuranta.fi)", "accept": "application/zip"}
API = "https://opendata.finlex.fi/finlex/avoindata/v1/akn/fi/act/statute-consolidated/{v}/{n}/fin@/main.akn"
NS = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"

# (vuosi, numero, nimi, aihe) – kansalaisten yleisimmät lakiasiat
LAIT = [
 (1978, 38, "Kuluttajansuojalaki", "kuluttajan oikeudet, virhe tuotteessa, reklamaatio, etämyynti, peruutusoikeus, kuluttajaluotot"),
 (1987, 355, "Kauppalaki", "irtaimen tavaran kauppa yksityisten välillä, virhe, viivästys"),
 (1994, 843, "Asuntokauppalaki", "asunto-osakkeen kauppa, uuden asunnon kauppa, virhe asunnossa, hinnanalennus"),
 (1995, 540, "Maakaari", "kiinteistön kauppa, talon kauppa, salainen virhe, lainhuuto, kiinnitys"),
 (1995, 481, "Laki asuinhuoneiston vuokrauksesta", "vuokrasuhde, vuokranantaja, vuokralainen, irtisanominen, vakuus, vuokrankorotus"),
 (1995, 482, "Laki liikehuoneiston vuokrauksesta", "liiketilan vuokrasopimus"),
 (2009, 1599, "Asunto-osakeyhtiölaki", "taloyhtiö, osakkaan remontit, kunnossapitovastuu, yhtiökokous, hallitus"),
 (1920, 26, "Laki eräistä naapuruussuhteista", "naapurit, kohtuuton haitta, puut rajalla, ojat"),
 (2001, 55, "Työsopimuslaki", "työsuhde, koeaika, irtisanominen, lomautus, palkka, työnantajan velvollisuudet"),
 (2019, 872, "Työaikalaki", "työaika, ylityö, lepoajat"),
 (2005, 162, "Vuosilomalaki", "vuosiloma, lomakorvaus, lomaraha"),
 (2014, 1325, "Yhdenvertaisuuslaki", "syrjintä, yhdenvertaisuus"),
 (1986, 609, "Laki naisten ja miesten välisestä tasa-arvosta", "sukupuoleen perustuva syrjintä, tasa-arvo"),
 (1965, 40, "Perintökaari", "perintö, testamentti, lakiosa, perunkirjoitus, kuolinpesä, perinnönjako"),
 (1929, 234, "Avioliittolaki", "avioliitto, avioero, avioehto, ositus, puolisot"),
 (2011, 26, "Laki avopuolisoiden yhteistalouden purkamisesta", "avoero, avopuolisoiden omaisuus"),
 (1983, 361, "Laki lapsen huollosta ja tapaamisoikeudesta", "huoltajuus, tapaamisoikeus, lapsen asuminen"),
 (1975, 704, "Laki lapsen elatuksesta", "elatusapu, elatusvelvollisuus"),
 (1999, 442, "Holhoustoimilaki", "edunvalvonta, edunvalvontavaltuutus, alaikäisen omaisuus"),
 (1974, 412, "Vahingonkorvauslaki", "vahingonkorvaus, kipu ja särky, työnantajan vastuu"),
 (2003, 728, "Laki velan vanhentumisesta", "velan vanhentuminen, vanhentumisen katkaisu"),
 (1982, 633, "Korkolaki", "viivästyskorko, korko"),
 (1999, 513, "Laki saatavien perinnästä", "perintä, perintäkulut, maksumuistutus"),
 (2007, 705, "Ulosottokaari", "ulosotto, palkan ulosmittaus, suojaosuus"),
 (1993, 57, "Laki yksityishenkilön velkajärjestelystä", "velkajärjestely, maksuohjelma"),
 (1994, 543, "Vakuutussopimuslaki", "vakuutus, korvaus, vakuutusyhtiö"),
 (2016, 460, "Liikennevakuutuslaki", "liikennevahinko, liikennevakuutus"),
 (2018, 729, "Tieliikennelaki", "liikennesäännöt, ajokortti, nopeus, rikesakko"),
 (1889, 39, "Rikoslaki", "rikokset, rangaistukset, petos, varkaus, pahoinpitely, kunnianloukkaus, vanhentuminen"),
 (1734, 4, "Oikeudenkäymiskaari", "oikeudenkäynti, todistelu, oikeudenkäyntikulut, valitus"),
 (2002, 257, "Oikeusapulaki", "julkinen oikeusapu, oikeusavun saaminen"),
 (2006, 624, "Osakeyhtiölaki", "osakeyhtiö, osakkaat, hallitus, osingonjako"),
 (1989, 503, "Yhdistyslaki", "yhdistys, hallitus, jäsenet, kokous"),
 (2003, 434, "Hallintolaki", "viranomainen, hallintopäätös, kuuleminen, oikaisuvaatimus"),
 (1999, 621, "Laki viranomaisten toiminnan julkisuudesta", "julkisuus, tietopyyntö, asiakirjat, salassapito"),
 (2018, 1050, "Tietosuojalaki", "henkilötiedot, tietosuoja"),
 (1940, 378, "Perintö- ja lahjaverolaki", "perintövero, lahjavero"),
 (2019, 863, "Rahankeräyslaki", "rahankeräys, pienkeräys, keräyslupa"),
 (2003, 612, "Järjestyslaki", "yleinen järjestys, alkoholin nauttiminen julkisella paikalla"),
]


def teksti(el):
    """Elementin teksti siistittynä (lisäykset, kursiivit jne. mukana)."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def pykalat(root):
    out = []
    luku_num = luku_ots = ""
    def kay(el, luku):
        nonlocal out
        for c in el:
            tag = c.tag.replace(NS, "")
            if tag == "chapter":
                n = c.find(NS + "num"); h = c.find(NS + "heading")
                kay(c, ((teksti(n) if n is not None else ""), (teksti(h) if h is not None else "")))
            elif tag == "section":
                n = c.find(NS + "num"); h = c.find(NS + "heading")
                osat = []
                for sub in c:
                    st = sub.tag.replace(NS, "")
                    if st in ("num", "heading"):
                        continue
                    t = teksti(sub)
                    if t:
                        osat.append(t)
                tx = "\n".join(osat)
                out.append({"id": c.get("eId"), "luku": " ".join(x for x in luku if x), "num": teksti(n) if n is not None else "",
                            "ots": teksti(h) if h is not None else "", "t": tx[:6000]})
            elif tag in ("body", "part", "hcontainer", "title", "subtitle", "division", "book"):
                kay(c, luku)
    body = root.find(f".//{NS}body")
    if body is not None:
        kay(body, ("", ""))
    return out


def main():
    os.makedirs(os.path.join(OUT, "laki"), exist_ok=True)
    luettelo, virheet = [], []
    for v, n, nimi, aihe in LAIT:
        url = API.format(v=v, n=n)
        for yritys in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                    data = r.read()
                break
            except Exception as e:
                err = e
                time.sleep(5 * (yritys + 1))
        else:
            virheet.append(f"{nimi} {n}/{v}: {err}"); continue
        z = zipfile.ZipFile(io.BytesIO(data))
        root = ET.fromstring(z.read("main.xml"))
        p = pykalat(root)
        voimassa = [x for x in p if not re.match(r"^(\d+ ?§ ?)?(on )?kumottu", x["t"], re.I)]
        lid = f"{v}-{n}"
        json.dump({"id": lid, "nimi": nimi, "vuosi": v, "nro": n, "url": f"https://www.finlex.fi/fi/lainsaadanto/ajantasa/{v}/{n}",
                   "p": voimassa}, open(os.path.join(OUT, "laki", lid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        luettelo.append({"id": lid, "nimi": nimi, "aihe": aihe, "kpl": len(voimassa), "lyh": f"{n}/{v}"})
        print(f"{nimi} {n}/{v}: {len(voimassa)} pykälää")
        time.sleep(1.5)
    json.dump({"haettu": time.strftime("%Y-%m-%d"), "lait": luettelo}, open(os.path.join(OUT, "lait.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if virheet:
        print("::warning::Hakematta jäi: " + "; ".join(virheet))
    if len(luettelo) < len(LAIT) * 0.8:
        sys.exit("Liian moni laki jäi hakematta")


if __name__ == "__main__":
    main()
