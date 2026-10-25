"""Faktapisteen laskurit: jokainen laskuri on oma hakukoneelle optimoitu sivu osoitteessa /laskurit/<slug>/.
Määrittelyt: ks. _yht.py (K = kenttä, L = laskuri)."""
from .era1a import ERA1A
from .era1b import ERA1B
from .era2 import ERA2

# Julkaistaan vain laskurit, joissa on oma kulma tai suomalainen erityistieto. Yleiset laskurit (BMI, prosentti,
# ikä, päivät, tavallinen lainalaskuri jne.) jätettiin pois, koska niissä kilpailu on liian kovaa uudelle sivulle.
JULKAISTUT = {"asuntolainalaskuri", "osamaksulaskuri", "katelaskuri", "neliohintalaskuri", "vuokratuottolaskuri",
              "sahkonkulutus", "sahkosopimusvertailu", "sahkoauton-lataus", "auton-kustannukset", "polttoainekulut"}
LASKURIT = [l for l in ERA1A + ERA1B if l["slug"] in JULKAISTUT] + ERA2
RYHMAT = []
for _l in LASKURIT:
    if _l["ryhma"] not in RYHMAT:
        RYHMAT.append(_l["ryhma"])
