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
 (1999, 442, "Laki holhoustoimesta", "edunvalvonta, edunvalvontavaltuutus, alaikäisen omaisuus"),
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


LISTA = "https://opendata.finlex.fi/finlex/avoindata/v1/akn/fi/act/statute-consolidated/list?format=json&limit=10&page={p}&titleContains={t}"


def _get(url, acc=None, aika=150):
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile() as f:
        r = subprocess.run(["curl", "-sS", "--compressed", "--max-time", str(aika), "-o", f.name, "-w", "%{http_code}",
                            "-H", "User-Agent: " + UA["User-Agent"]] + (["-H", "accept: " + acc] if acc else []) + [url], capture_output=True, text=True)
        if r.stdout.strip() == "429":
            time.sleep(20)
            return _get(url, acc, aika)
        if r.stdout.strip() != "200":
            raise RuntimeError(f"HTTP {r.stdout.strip()} {r.stderr.strip()[:60]}")
        return open(f.name, "rb").read()


def versiot(v, n, nimi):
    """Lain ajantasaiset versiot (fin@VVVVNNNN). Haetaan nimellä ja suodatetaan vuoden ja numeron mukaan."""
    import urllib.parse
    loydetyt = set()
    for hakusana in (nimi, nimi.split()[0] if nimi.startswith(("Laki", "laki")) is False else nimi.split(" ", 1)[1]):
        for p in range(1, 31):
            try:
                d = json.loads(_get(LISTA.format(p=p, t=urllib.parse.quote(hakusana)), aika=60))
            except Exception:
                break
            for x in d:
                u = x.get("akn_uri", "")
                if re.search(rf"/statute-consolidated/{v}/{n}(-\d+)?/fin@", u):
                    loydetyt.add(u)
            if len(d) < 10:
                break
            time.sleep(0.3)
        if loydetyt:
            break
    return sorted(loydetyt, key=lambda u: u.rsplit("@", 1)[1] or "0", reverse=True)


def hae(v, n, nimi):
    """Uusin voimassa oleva versio: versioista suurin, jonka voimassaolopäivä (ELI-alias) ei ole tulevaisuudessa."""
    tanaan = time.strftime("%Y-%m-%d")
    ehdokkaat = versiot(v, n, nimi) or [API.format(v=v, n=n).rsplit("/main.akn", 1)[0]]
    viimeisin_virhe = None
    for u in ehdokkaat[:4]:
        try:
            z = zipfile.ZipFile(io.BytesIO(_get(u + "/main.akn", "application/zip")))
            root = ET.fromstring(z.read("main.xml"))
        except Exception as e:
            viimeisin_virhe = e; continue
        alias = next((a.get("value", "") for a in root.iter(NS + "FRBRalias") if "/ajantasa/" in a.get("value", "") and a.get("value", "").endswith("/fin")), "")
        m = re.search(r"/ajantasa/(\d{4}-\d{2}-\d{2})/", alias)
        if m and m.group(1) > tanaan:
            continue   # muutos ei ole vielä voimassa
        return root, (m.group(1) if m else "")
    raise RuntimeError(f"ei saatu ({viimeisin_virhe})")


def main():
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(os.path.join(OUT, "laki"), exist_ok=True)
    luettelo, virheet = [], []
    alku = time.time()

    def yksi(rivi):
        v, n, nimi, aihe = rivi
        t0 = time.time()
        try:
            root, pv = hae(v, n, nimi)
        except Exception as e:
            return rivi, None, str(e), time.time() - t0
        return rivi, (pykalat(root), pv), None, time.time() - t0

    with ThreadPoolExecutor(max_workers=2) as ex:
        for (v, n, nimi, aihe), tulos, err, kesto in ex.map(yksi, LAIT):
            if err:
                virheet.append(f"{nimi} {n}/{v}: {err}"); print(f"VIRHE {nimi}: {err}", flush=True); continue
            p, pv = tulos
            voimassa = [x for x in p if not re.match(r"^(\d+ ?§ ?)?(on )?kumottu", x["t"], re.I)]
            lid = f"{v}-{n}"
            json.dump({"id": lid, "nimi": nimi, "vuosi": v, "nro": n, "url": f"https://www.finlex.fi/fi/lainsaadanto/{v}/{n}", "versio": pv,
                       "p": voimassa}, open(os.path.join(OUT, "laki", lid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
            luettelo.append({"id": lid, "nimi": nimi, "aihe": aihe, "kpl": len(voimassa), "lyh": f"{n}/{v}", "versio": pv})
            print(f"{nimi} {n}/{v}: {len(voimassa)} pykälää, versio {pv} ({kesto:.0f} s)", flush=True)
    json.dump({"haettu": time.strftime("%Y-%m-%d"), "lait": luettelo}, open(os.path.join(OUT, "lait.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"::notice title=Lait::{len(luettelo)}/{len(LAIT)} lakia, {sum(l['kpl'] for l in luettelo)} pykälää, {time.time()-alku:.0f} s" + (" | puuttuu: " + "; ".join(virheet) if virheet else ""))
    if len(luettelo) < len(LAIT) * 0.8:
        sys.exit("Liian moni laki jäi hakematta")


if __name__ == "__main__":
    main()
