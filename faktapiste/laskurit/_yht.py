"""Apufunktiot laskurien määrittelyyn."""


def K(nimi, otsikko, oletus="", yks="", valinnat=None, tyyppi="n", askel="any"):
    """Kenttä. tyyppi: n = luku, pvm = päivämäärä, aika = kellonaika, valinta = alasvetovalikko (valinnat = [(arvo, teksti)])."""
    if valinnat:
        tyyppi = "valinta"
    return {"nimi": nimi, "otsikko": otsikko, "oletus": oletus, "yks": yks, "valinnat": valinnat, "tyyppi": tyyppi, "askel": askel}


def L(slug, nimi, ryhma, otsikko, kuvaus, johdanto, kentat, js, teksti, ukk):
    """Laskurin määrittely."""
    return {"slug": slug, "nimi": nimi, "ryhma": ryhma, "otsikko": otsikko, "kuvaus": kuvaus,
            "johdanto": johdanto, "kentat": kentat, "js": js, "teksti": teksti, "ukk": ukk}
