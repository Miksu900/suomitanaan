"""Räätälöidyt mallikaupat (Netvo – räätälöity verkkokauppa). Näytetään netvo.fi/mallit/<slug>/.

Tarkoitus: näyttää, mitä räätälöity kauppa tarjoaa enemmän kuin itse tehtävä Netvo Kauppa:
oma ilme ja kuvitus, pikakatselu, värit ja koot kuvineen, kokotaulukko, lahjapaketointi, kori ja kolmivaiheinen kassa,
leipomolle noutoaikojen valinta, toimitusalueen tarkistus postinumerolla, kakkukonfiguraattori ja viikkotilaus.
Kaikki toimii selaimessa ilman taustapalvelua – tilauksia ei tehdä (mallisivu).
"""
import html, json, pathlib
from . import premium_kuvat as K

esc = html.escape


def _svg(folder, name, svg):
    (folder / f'{name}.svg').write_text(svg, encoding='utf-8')
    return f'kuvat/{name}.svg'


# ---------------------------------------------------------------- sisältö
def villa(folder):
    k = lambda n, s: _svg(folder, n, s)
    P = [
        {"id": 1, "name": "Villasukat Tunturi", "cat": "Sukat", "price": 2400, "badge": "Suosituin", "rating": 4.9, "nrev": 128,
         "colors": [{"n": "Puolukka", "hex": "#9b2335", "img": k("sukka-puolukka", K.sukka("#9b2335"))},
                    {"n": "Metsä", "hex": "#2f4f3a", "img": k("sukka-metsa", K.sukka("#2f4f3a"))},
                    {"n": "Kaura", "hex": "#c9a86a", "img": k("sukka-kaura", K.sukka("#c9a86a"))}],
         "sizes": ["36–38", "39–41", "42–44", "45–47"], "soldout": {"45–47|Kaura": 1},
         "desc": "Paksut, pehmeät villasukat perinteisellä tunturikuviolla. Neulottu käsin 7 veljeksen villasekoitteesta, kestävä vahvistettu kantapää.",
         "details": [["Materiaali", "75 % villa, 25 % polyamidi"], ["Hoito", "Villapesu 30 °C, kuivaus tasossa"], ["Tekijä", "Neulottu Ylivieskassa, noin 9 h / pari"]]},
        {"id": 2, "name": "Lapaset Revontuli", "cat": "Lapaset", "price": 2900, "rating": 4.8, "nrev": 64,
         "colors": [{"n": "Yö", "hex": "#1f2a44", "img": k("lapaset-yo", K.lapaset("#1f2a44"))}, {"n": "Kanerva", "hex": "#8a5a8f", "img": k("lapaset-kanerva", K.lapaset("#8a5a8f"))}],
         "sizes": ["S", "M", "L"], "desc": "Kirjoneulotut lapaset kahdella langalla – kaksinkertainen lämpö. Pitkä resori pitää tuulen poissa.",
         "details": [["Materiaali", "100 % suomalainen lampaanvilla"], ["Hoito", "Käsinpesu, kuivaus tasossa"]]},
        {"id": 3, "name": "Merinopipo Huurre", "cat": "Pipot", "price": 3200, "badge": "Uutuus", "rating": 5.0, "nrev": 21,
         "colors": [{"n": "Kaura", "hex": "#d9c7a7", "img": k("pipo-kaura", K.pipo("#d9c7a7"))}, {"n": "Puolukka", "hex": "#9b2335", "img": k("pipo-puolukka", K.pipo("#9b2335"))}, {"n": "Harmaa", "hex": "#8e9197", "img": k("pipo-harmaa", K.pipo("#8e9197"))}],
         "sizes": ["Aikuinen", "Lapsi"], "desc": "Kutittamaton merinovilla ja irrotettava tupsu. Joustava resori, sopii useimmille.",
         "details": [["Materiaali", "100 % merinovilla"], ["Tupsu", "Irrotettava, nepparikiinnitys"]]},
        {"id": 4, "name": "Kaulahuivi Kaisla", "cat": "Huivit", "price": 4500, "rating": 4.7, "nrev": 33,
         "colors": [{"n": "Sammal", "hex": "#5f6b3a", "img": k("huivi-sammal", K.huivi("#5f6b3a", "#d9c7a7"))}, {"n": "Savi", "hex": "#a8624a", "img": k("huivi-savi", K.huivi("#a8624a", "#efe2cf"))}],
         "sizes": [], "desc": "Pitkä, ilmava palmikkohuivi hapsuilla. 180 × 30 cm.", "details": [["Materiaali", "70 % villa, 30 % alpakka"], ["Koko", "180 × 30 cm"]]},
        {"id": 5, "name": "Lasten villasukat", "cat": "Sukat", "price": 1800, "rating": 4.9, "nrev": 47,
         "colors": [{"n": "Mustikka", "hex": "#3e4a8a", "img": k("lsukka-mustikka", K.sukka("#3e4a8a", "raita"))}, {"n": "Puolukka", "hex": "#9b2335", "img": k("lsukka-puolukka", K.sukka("#9b2335", "raita"))}],
         "sizes": ["22–25", "26–29", "30–33"], "desc": "Raidalliset lastensukat, joissa liukueste pohjassa.", "details": [["Materiaali", "80 % villa, 20 % polyamidi"]]},
        {"id": 6, "name": "Lahjapaketti Lämmin talvi", "cat": "Lahjat", "price": 4900, "compare": 5300, "badge": "Säästä 4 €", "rating": 5.0, "nrev": 19,
         "colors": [{"n": "Puolukka", "hex": "#9b2335", "img": k("lahja", K.lahja("#9b2335", "#c9a86a"))}], "sizes": ["36–38", "39–41", "42–44"],
         "desc": "Villasukat Tunturi ja lapaset kauniissa lahjarasiassa, mukana käsin kirjoitettu kortti.", "details": [["Sisältö", "Sukat + lapaset + kortti"]]},
        {"id": 7, "name": "Kotimainen villalanka", "cat": "Langat", "price": 990, "rating": 4.8, "nrev": 88,
         "colors": [{"n": n, "hex": c, "img": k(f"kera-{i}", K.kera(c))} for i, (n, c) in enumerate([("Puolukka", "#9b2335"), ("Metsä", "#2f4f3a"), ("Kaura", "#c9a86a"), ("Yö", "#1f2a44"), ("Kanerva", "#8a5a8f")])],
         "sizes": [], "desc": "Neulo itse! 100 g kerä, n. 200 m. Riittää yksiin aikuisten sukkiin.", "details": [["Menekki", "Sukat 1 kerä, lapaset 1 kerä"], ["Puikot", "3–3,5 mm"]]},
        {"id": 8, "name": "Villasukat Kuura", "cat": "Sukat", "price": 1900, "compare": 2400, "badge": "−20 %", "rating": 4.6, "nrev": 52,
         "colors": [{"n": "Kuura", "hex": "#cfd6de", "img": k("sukka-kuura", K.sukka("#9fb0c2", "kuura"))}], "sizes": ["36–38", "39–41", "42–44"],
         "desc": "Kevyemmät arkisukat lumikidekuviolla. Rajoitettu erä.", "details": [["Materiaali", "75 % villa, 25 % polyamidi"]]},
    ]
    return {
        "slug": "kauppa-kasityo", "name": "Villa & Lanka", "tagline": "Käsin neulottua lämpöä pohjoisesta",
        "title": "Villa & Lanka – käsin neulotut villasukat, lapaset ja pipot",
        "meta": "Käsin neulotut villasukat, lapaset ja merinopipot kotimaisesta villasta. Lahjapaketointi, toimitus koko Suomeen.",
        "css": {"bg": "#f7f2ec", "card": "#fffdfa", "soft": "#efe6dc", "line": "#e6dbcf", "text": "#2a1a22", "muted": "#7a6b70", "acc": "#7a2a43", "acc2": "#c9a86a", "ink": "#fff",
                "fh": '"Iowan Old Style","Palatino Linotype","Book Antiqua",Palatino,Georgia,serif', "fb": 'ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif', "r": "4px"},
        "cover": _svg(folder, "kansi", K.kansi_villa()),
        "photos": {"hero": "photo-1742386676097-a2a55fcdcc64", "story": "photo-1597736091383-2976f665d932", "nl": "photo-1584992236310-6edddc08acff",
                   "band": ["photo-1614587431569-caafde7537d3", "Talvi on pitkä. Villa on lämmin.", "Neulomme tuotteet pohjoisen talveen: tiivistä, kestävää ja lämmintä vielä märkänäkin."],
                   "tiles": {"Sukat": "photo-1730448111621-c0524e75b0e8", "Lapaset": "photo-1730098016553-2844f370607d", "Pipot": "photo-1544967919-44c1ef2f9e7a",
                             "Huivit": "photo-1491245257527-395e9c480145", "Lahjat": "photo-1707944145479-12755f0434d8", "Langat": "photo-1598871956222-26b66d6559fe"}},
        "nav": ["Sukat", "Lapaset", "Pipot", "Huivit", "Lahjat", "Langat"],
        "free": 6000, "products": P, "gift": 400, "sizeguide": True,
        "ship": [["Posti – pakettiautomaatti", 590, "1–3 arkipäivää"], ["Matkahuolto – lähellä-paketti", 590, "1–3 arkipäivää"], ["Posti – kotiinkuljetus", 990, "2–4 arkipäivää"]],
        "hero": {"kicker": "Syksyn mallisto 2026", "h": "Käsin neulottua lämpöä pohjoisesta", "p": "Jokainen pari neulotaan Ylivieskassa kotimaisesta villasta. Ei kahta täysin samanlaista.", "cta": "Tutustu mallistoon"},
        "usp": [["Käsin neulottu", "Noin 9 tuntia / pari"], ["Kotimainen villa", "Jäljitettävä alkuperä"], ["Lahjapaketointi", "Kortti ja rasia +4 €"], ["Ilmainen toimitus", "Yli 60 € tilauksiin"]],
        "story": {"h": "Tehty käsin, tehty kestämään", "p": ["Villa & Lanka on kahden neulojan pieni paja Pohjanmaalla. Neulomme jokaisen tuotteen itse – yhdellä parilla menee noin yhdeksän tuntia.",
                                                             "Käytämme suomalaista lampaanvillaa ja merinoa, joiden alkuperän tiedämme. Tuotteet kestävät vuosia, ja korjaamme ne tarvittaessa."],
                  "stats": [["9 h", "neulontaa / pari"], ["2 400+", "tyytyväistä asiakasta"], ["4,9 / 5", "arvosana"]]},
        "reviews": [["Eeva", 5, "Lämpimimmät sukat ikinä. Tilasin heti lisää lahjaksi koko perheelle.", "Villasukat Tunturi"],
                    ["Sanna", 5, "Lahjarasia oli niin kaunis, että sitä melkein sääli avata. Nopea toimitus.", "Lahjapaketti Lämmin talvi"],
                    ["Mikko", 4, "Hyvä istuvuus ja laatu. Koko 42–44 sopi täydellisesti.", "Villasukat Tunturi"]],
        "faq": [["Miten valitsen sukkien koon?", "Valitse kenkäkokosi mukaan. Jos olet kokojen välissä, valitse isompi – villa painuu käytössä."],
                ["Kuinka nopeasti tilaus lähtee?", "Varastossa olevat tuotteet lähtevät 1–2 arkipäivässä."],
                ["Voinko palauttaa?", "Kyllä, 14 päivän palautusoikeus käyttämättömille tuotteille."]],
        "contact": ["myynti@villajalanka.fi", "050 444 5566"],
    }


def leipomo(folder):
    k = lambda n, s: _svg(folder, n, s)
    P = [
        {"id": 1, "name": "Juurileipä (ruis)", "cat": "Leivät", "price": 450, "badge": "Uunista tänään", "rating": 4.9, "nrev": 211, "tags": ["V", "L", "M"], "sub": True,
         "img": k("ruisleipa", K.ruisleipa()), "desc": "Hapanjuureen leivottu perinteinen ruisleipä, 48 tunnin taikinanteko. 600 g.", "details": [["Ainekset", "Ruisjauho, vesi, suola, juuri"], ["Säilyvyys", "5 vrk, pakastettavissa"]]},
        {"id": 2, "name": "Saaristolaisleipä", "cat": "Leivät", "price": 590, "rating": 4.8, "nrev": 96, "tags": ["L", "M"], "img": k("saaristo", K.saaristolais()),
         "desc": "Mehevä, makeahko maltaileipä rusinoilla. 500 g.", "details": [["Ainekset", "Ruis, ohra, mallas, piimä, siirappi, rusinat"]]},
        {"id": 3, "name": "Korvapuustit 6 kpl", "cat": "Pullat", "price": 790, "badge": "Suosituin", "rating": 5.0, "nrev": 154, "tags": [], "img": k("korvapuusti", K.korvapuusti()),
         "desc": "Mehevät kanelikorvapuustit oikealla voilla ja raesokerilla.", "details": [["Allergeenit", "Vehnä, maito, kananmuna"]]},
        {"id": 4, "name": "Karjalanpiirakat 10 kpl", "cat": "Suolaiset", "price": 850, "rating": 4.9, "nrev": 132, "tags": ["L"], "img": k("piirakka", K.piirakka()),
         "desc": "Ohut ruiskuori ja kermainen riisipuuro. Lämmitä uunissa ja nauti munavoin kanssa.", "details": [["Allergeenit", "Ruis, maito (laktoositon)"]]},
        {"id": 5, "name": "Täytekakku tilauksesta", "cat": "Kakut", "price": 3500, "rating": 5.0, "nrev": 78, "tags": [], "img": k("kakku", K.kakku()), "cake": True,
         "desc": "Juhlakakku toiveidesi mukaan. Valitse koko, täyte ja teksti – nouto aikaisintaan 3 päivän päästä.", "details": [["Tilaus", "Vähintään 3 vrk ennen"], ["Erikoisruokavaliot", "Gluteeniton ja laktoositon onnistuvat"]]},
        {"id": 6, "name": "Gluteenittomat kaurasämpylät 6 kpl", "cat": "Gluteenittomat", "price": 690, "rating": 4.7, "nrev": 41, "tags": ["G", "L", "V"], "img": k("sampyla", K.sampyla()),
         "desc": "Pehmeät kaurasämpylät puhtaasta gluteenittomasta kaurasta. Leivotaan erillisellä linjalla.", "details": [["Ainekset", "Gluteeniton kaura, psyllium, öljy, hiiva"]]},
        {"id": 7, "name": "Mustikkapiirakka", "cat": "Pullat", "price": 1290, "badge": "Sesonki", "rating": 4.9, "nrev": 67, "tags": [], "img": k("mustikka", K.mustikkapiirakka()),
         "desc": "Rapea murotaikina ja kotimaiset metsämustikat. 8 palaa.", "details": [["Allergeenit", "Vehnä, maito, kananmuna"]]},
        {"id": 8, "name": "Lihapiirakka", "cat": "Suolaiset", "price": 320, "rating": 4.6, "nrev": 58, "tags": [], "img": k("lihapiirakka", K.lihapiirakka()),
         "desc": "Klassinen munkkitaikinainen lihapiirakka. Lämpimänä parhaimmillaan.", "details": [["Allergeenit", "Vehnä, kananmuna"]]},
    ]
    return {
        "slug": "kauppa-leipomo", "name": "Kotileipomo Ruis", "tagline": "Tuoretta leipää, joka aamu",
        "title": "Kotileipomo Ruis – tuore leipä ja leivonnaiset verkosta, nouto tai kotiinkuljetus",
        "meta": "Hapanjuurileivät, korvapuustit, karjalanpiirakat ja tilauskakut. Valitse noutoaika tai kotiinkuljetus Ylivieskan alueelle.",
        "css": {"bg": "#faf5ec", "card": "#fffdf8", "soft": "#f1e7d6", "line": "#e9dcc6", "text": "#2b1d14", "muted": "#7d6c5c", "acc": "#8a4b22", "acc2": "#d8a23c", "ink": "#fff",
                "fh": 'Georgia,"Iowan Old Style","Palatino Linotype",serif', "fb": 'ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif', "r": "18px"},
        "cover": _svg(folder, "kansi", K.kansi_leipomo()),
        "photos": {"hero": "photo-1548228623-13e55dd16984", "story": "photo-1652283319196-9288add2d60c", "nl": "photo-1762754104628-cb53c14d79b7",
                   "band": ["photo-1787648065226-67c905836b4f", "Jauhot Pohjanmaan pelloilta", "Ruis ja vehnä jauhetaan lähimyllyssä. Lyhyt matka pellolta uuniin maistuu leivässä."],
                   "tiles": {"Leivät": "photo-1509440159596-0249088772ff", "Pullat": "photo-1609126979532-0f514232d1a8", "Suolaiset": "photo-1741768785646-956b38de4903",
                             "Kakut": "photo-1650419424455-d0513aaf0dd6", "Gluteenittomat": "photo-1635627363683-25f5adc35eb5"}},
        "nav": ["Leivät", "Pullat", "Suolaiset", "Kakut", "Gluteenittomat"],
        "free": 3500, "products": P, "bakery": True,
        "ship": [["Nouto leipomosta", 0, "Leipurinkuja 2, Ylivieska"], ["Kotiinkuljetus", 490, "Ylivieska, Alavieska, Sievi, Nivala · ma–la"]],
        "hero": {"kicker": "Avattu klo 7 · uunista tänään", "h": "Tuoretta leipää, joka aamu", "p": "Hapanjuurta, voita ja aikaa – ei lisäaineita. Tilaa illalla, nouda aamulla tuoreena tai tilaa kotiovelle.", "cta": "Tilaa aamuksi"},
        "usp": [["Leivottu tänään", "Joka aamu klo 4 alkaen"], ["Nouto tai kotiinkuljetus", "Valitse aika kassalla"], ["Gluteenittomat", "Oma tuotantolinja"], ["Viikkotilaus", "−10 % joka kerta"]],
        "story": {"h": "Kolmannen polven leipurit", "p": ["Kotileipomo Ruis aloitti isoäidin juurella vuonna 1962. Samaa juurta ruokitaan yhä joka päivä.",
                                                          "Jauhot tulevat Pohjanmaalta, voi ja maito lähimeijeristä. Leivomme pienissä erissä, jotta kaikki on tuoretta."],
                  "stats": [["1962", "sama juuri"], ["48 h", "taikinanteko"], ["4,9 / 5", "arvosana"]]},
        "reviews": [["Tuula", 5, "Parasta ruisleipää sitten mummon. Viikkotilaus on helppo – leipä odottaa perjantaina valmiina.", "Juurileipä (ruis)"],
                    ["Noora", 5, "Lastenjuhlien kakku oli upea ja maistui taivaalliselta. Teksti juuri kuten toivoin.", "Täytekakku tilauksesta"],
                    ["Jari", 5, "Karjalanpiirakat kuin itse tehdyt. Nouto aamulla kävi minuutissa.", "Karjalanpiirakat 10 kpl"]],
        "faq": [["Mihin asti voin tilata huomiseksi?", "Tilaa klo 20 mennessä, niin leivomme tuotteet aamuksi. Klo 20 jälkeen tehdyn tilauksen saat seuraavana päivänä klo 12 alkaen."],
                ["Mille alueelle kotiinkuljetus toimii?", "Ylivieskaan, Alavieskaan, Sieviin ja Nivalaan maanantaista lauantaihin. Kirjoita postinumerosi kassalla, niin näet heti, toimitammeko perille. Valitset itse toimitusajan, ja kuljettaja ilmoittaa, kun on matkalla."],
                ["Voiko kakun saada gluteenittomana?", "Kyllä, valitse kakun tilauksessa gluteeniton (+5 €)."]],
        "contact": ["tilaukset@kotileipomoruis.fi", "040 111 2233"],
        "hours": [["Ma–Pe", 7, 17], ["La", 8, 14], ["Su", None, None]],
        "cake": {"sizes": [["8 hlöä", 3500], ["12 hlöä", 4500], ["16 hlöä", 5900]], "fill": ["Mansikka-vanilja", "Suklaa-vadelma", "Kinuski-banaani", "Sitruuna-mustikka"], "gf": 500},
    }


# ---------------------------------------------------------------- sivu
CSS = r"""
[hidden]{display:none!important}*{box-sizing:border-box}html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 var(--fb);-webkit-font-smoothing:antialiased}
img{display:block;max-width:100%}a{color:inherit}button{font:inherit;color:inherit}
h1,h2,h3{font-family:var(--fh);font-weight:500;letter-spacing:-.01em;line-height:1.12;margin:0 0 .4em}
.w{max-width:1240px;margin:0 auto;padding:0 22px}.muted{color:var(--muted)}.small{font-size:.88rem}
.demo{background:#15171a;color:#e9e9ea;font-size:.84rem;text-align:center;padding:8px 14px}.demo a{color:#ffd24a;font-weight:700}
.annc{background:var(--acc);color:var(--ink);text-align:center;font-size:.84rem;letter-spacing:.04em;padding:9px 14px}
header.top{position:sticky;top:0;z-index:40;background:color-mix(in srgb,var(--bg) 90%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.bar{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;height:74px;gap:12px}
.brand{font-family:var(--fh);font-size:1.6rem;text-decoration:none;letter-spacing:.01em;text-align:center;white-space:nowrap}
.brand small{display:block;font-family:var(--fb);font-size:.62rem;letter-spacing:.32em;text-transform:uppercase;color:var(--muted);margin-top:-2px}
nav.main{display:flex;gap:4px}nav.main a{text-decoration:none;padding:8px 10px;font-size:.93rem;border-radius:999px}nav.main a:hover{background:var(--soft)}
.tools{display:flex;justify-content:flex-end;gap:2px}
.ic{position:relative;width:44px;height:44px;border-radius:999px;border:0;background:none;display:grid;place-items:center;cursor:pointer}.ic:hover{background:var(--soft)}
.ic svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.cnt{position:absolute;top:4px;right:2px;min-width:18px;height:18px;border-radius:9px;background:var(--acc);color:var(--ink);font-size:.66rem;font-weight:800;display:grid;place-items:center;padding:0 4px}
.burger{display:none}@media(max-width:620px){.bar{grid-template-columns:auto 1fr auto;gap:4px}.brand{font-size:1.25rem}.brand small{display:none}.tools .ic.hide-m{display:none}.ic{width:40px;height:40px}}
@media(max-width:980px){nav.main{display:none;position:absolute;left:0;right:0;top:74px;flex-direction:column;background:var(--bg);padding:12px 18px;border-bottom:1px solid var(--line)}nav.main.open{display:flex}.burger{display:grid}nav.main a{padding:13px 10px;font-size:1.05rem}}
/* hero */
.hero{position:relative;overflow:hidden;min-height:min(78vh,720px);display:flex;align-items:center;color:#fff;background:#222}
.hero>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.55),rgba(0,0,0,.1) 60%)}
.hero .in{position:relative;z-index:1;max-width:620px;padding:60px 0;animation:rise .9s cubic-bezier(.2,.8,.2,1) both}
.kick{display:inline-block;font-size:.76rem;letter-spacing:.24em;text-transform:uppercase;border:1px solid rgba(255,255,255,.5);padding:6px 12px;border-radius:999px;margin-bottom:18px}
.hero h1{font-size:clamp(2.4rem,6.4vw,4.6rem);color:#fff;text-wrap:balance}.hero p{font-size:1.15rem;opacity:.92;max-width:48ch;margin:0 0 28px}
@keyframes rise{from{opacity:0;transform:translateY(22px)}}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border:0;cursor:pointer;background:var(--acc);color:var(--ink);padding:15px 26px;border-radius:var(--r);font-weight:650;letter-spacing:.02em;text-decoration:none;transition:transform .15s,filter .15s}
.btn:hover{filter:brightness(1.08)}.btn:active{transform:scale(.98)}.btn.light{background:#fff;color:#141414}.btn.line{background:transparent;border:1.5px solid currentColor;color:inherit}.btn.block{width:100%}.btn[disabled]{opacity:.45;cursor:not-allowed}
.usp{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--line);background:var(--card)}.usp div{padding:20px 18px;text-align:center;border-right:1px solid var(--line)}.usp div:last-child{border:0}.usp b{display:block;font-family:var(--fh);font-weight:500;font-size:1.08rem}.usp span{font-size:.84rem;color:var(--muted)}
@media(max-width:760px){.usp{grid-template-columns:1fr 1fr}.usp div:nth-child(2){border-right:0}.usp div:nth-child(-n+2){border-bottom:1px solid var(--line)}}
section.s{padding:76px 0}.sh{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:26px}.sh h2{font-size:clamp(1.8rem,4vw,2.8rem);margin:0}
.eyebrow{font-size:.74rem;letter-spacing:.24em;text-transform:uppercase;color:var(--acc);font-weight:700;margin-bottom:10px;display:block}
/* category tiles */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}.tile{position:relative;aspect-ratio:4/5;border-radius:var(--r);overflow:hidden;text-decoration:none;color:#fff;background:var(--soft);cursor:pointer;border:0;padding:0}
.tile img{width:100%;height:100%;object-fit:cover;transition:transform .8s cubic-bezier(.2,.7,.2,1)}.tile:hover img{transform:scale(1.06)}.tile span{position:absolute;left:14px;bottom:12px;font-family:var(--fh);font-size:1.3rem;text-shadow:0 2px 12px rgba(0,0,0,.4)}
.tile:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(0,0,0,.45))}.tile span{z-index:1}
/* filters */
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:22px}.chip{border:1.5px solid var(--line);background:var(--card);border-radius:999px;padding:8px 16px;cursor:pointer;font-size:.92rem}.chip.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.filters select{margin-left:auto;font:inherit;padding:9px 14px;border-radius:999px;border:1.5px solid var(--line);background:var(--card)}
.tag{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 6px;border-radius:6px;background:var(--soft);font-size:.72rem;font-weight:800;color:var(--acc)}
/* grid */
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:34px 22px}@media(max-width:1000px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){.grid{grid-template-columns:1fr 1fr;gap:26px 12px}}
.card{position:relative;cursor:pointer}.card .ph{position:relative;aspect-ratio:4/5;border-radius:var(--r);overflow:hidden;background:var(--soft)}
.card .ph img{width:100%;height:100%;object-fit:cover;transition:transform .7s cubic-bezier(.2,.7,.2,1)}.card:hover .ph img{transform:scale(1.045)}
.card .bd{position:absolute;left:10px;top:10px;background:var(--card);color:var(--text);font-size:.72rem;font-weight:700;letter-spacing:.04em;padding:5px 9px;border-radius:999px}.card .bd.sale{background:var(--acc);color:var(--ink)}
.fav{position:absolute;right:10px;top:10px;width:38px;height:38px;border-radius:99px;border:0;background:color-mix(in srgb,var(--card) 90%,transparent);display:grid;place-items:center;cursor:pointer}.fav svg{width:18px;height:18px;fill:none;stroke:var(--text);stroke-width:1.8}.fav.on svg{fill:var(--acc);stroke:var(--acc)}
.qv{position:absolute;left:10px;right:10px;bottom:10px;border:0;background:color-mix(in srgb,var(--card) 94%,transparent);padding:11px;border-radius:var(--r);font-weight:650;cursor:pointer;opacity:0;transform:translateY(8px);transition:.25s}.card:hover .qv,.card:focus-within .qv{opacity:1;transform:none}@media(hover:none){.qv{display:none}}
.card h3{font-family:var(--fb);font-weight:600;font-size:1rem;margin:12px 0 2px;letter-spacing:0}.card .row{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.price{font-weight:700;font-variant-numeric:tabular-nums}.old{color:var(--muted);text-decoration:line-through;font-weight:400;font-size:.88em;margin-left:6px}
.sw{display:flex;gap:6px;margin-top:8px}.sw button{width:20px;height:20px;border-radius:99px;border:2px solid var(--card);box-shadow:0 0 0 1px var(--line);cursor:pointer;padding:0}.sw button.on{box-shadow:0 0 0 2px var(--text)}
.stars{color:#d9a221;letter-spacing:1px;font-size:.86rem}.rv{font-size:.8rem;color:var(--muted)}
/* story */
.story{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}@media(max-width:860px){.story{grid-template-columns:1fr;gap:30px}}
.story .pic{aspect-ratio:1;border-radius:var(--r);overflow:hidden;background:var(--soft)}.story .pic img{width:100%;height:100%;object-fit:cover}
.stats{display:flex;gap:34px;margin-top:26px;flex-wrap:wrap}.stats b{display:block;font-family:var(--fh);font-weight:500;font-size:2.2rem;color:var(--acc)}.stats span{font-size:.86rem;color:var(--muted)}
.revs{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}@media(max-width:860px){.revs{grid-template-columns:1fr}}.rev{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:26px}.rev p{font-family:var(--fh);font-size:1.18rem;line-height:1.45;margin:10px 0 16px}
.faqw{display:grid;grid-template-columns:1fr 1.4fr;gap:40px}@media(max-width:760px){.faqw{grid-template-columns:1fr;gap:10px}}.faq details{border-bottom:1px solid var(--line)}.faq summary{cursor:pointer;list-style:none;padding:18px 0;font-weight:600;display:flex;justify-content:space-between}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";font-size:1.4rem;font-weight:300}.faq details[open] summary:after{content:"–"}.faq details p{margin:0 0 18px;color:var(--muted)}
.nl{background:var(--acc);color:var(--ink);border-radius:var(--r);padding:clamp(30px,6vw,60px);display:grid;grid-template-columns:1.2fr 1fr;gap:30px;align-items:center}@media(max-width:860px){.nl{grid-template-columns:1fr}}
.band{position:relative;color:#fff;text-align:center;padding:clamp(90px,16vw,180px) 0;background:#222 var(--bimg) center/cover no-repeat;isolation:isolate}@media(min-width:900px) and (hover:hover){.band{background-attachment:fixed}}
.band:before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.32),rgba(0,0,0,.6));z-index:-1}.band h2{color:#fff;font-size:clamp(2rem,5vw,3.6rem);text-wrap:balance;margin:0 auto 14px;max-width:18ch}.band p{max-width:52ch;margin:0 auto 26px;font-size:1.12rem;opacity:.92}
.nl.ph{position:relative;isolation:isolate;overflow:hidden;background:var(--acc) var(--nimg) center/cover}.nl.ph:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,color-mix(in srgb,var(--acc) 92%,transparent),color-mix(in srgb,var(--acc) 55%,transparent));z-index:-1}
.hero>img{animation:kb 22s ease-out both}@keyframes kb{from{transform:scale(1.08)}to{transform:scale(1)}}@media(prefers-reduced-motion:reduce){.hero>img{animation:none}}
.nl>*{min-width:0}.nl form{display:flex;gap:8px;flex-wrap:wrap}.nl h2{overflow-wrap:anywhere}.nl input{flex:1;min-width:0;padding:15px 16px;border-radius:var(--r);border:0;font:inherit}.nl .btn{background:var(--text);color:var(--bg)}
footer{background:var(--text);color:color-mix(in srgb,var(--bg) 80%,transparent);padding:60px 0 30px;margin-top:80px;font-size:.92rem}footer h4{font-family:var(--fh);font-weight:500;font-size:1.1rem;color:var(--bg);margin:0 0 12px}
.fc{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}@media(max-width:860px){.fc{grid-template-columns:1fr 1fr}}footer a{text-decoration:none}footer ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.pays{display:flex;gap:6px;flex-wrap:wrap;margin-top:30px;padding-top:22px;border-top:1px solid rgba(255,255,255,.15)}.pays span{border:1px solid rgba(255,255,255,.25);border-radius:6px;padding:4px 9px;font-size:.74rem;font-weight:700}
/* overlays */
.ov{position:fixed;inset:0;z-index:60;visibility:hidden}.ov.open{visibility:visible}.ov .bg{position:absolute;inset:0;background:rgba(20,14,10,.5);opacity:0;transition:opacity .3s}.ov.open .bg{opacity:1}
.drawer{position:absolute;right:0;top:0;bottom:0;width:min(460px,100%);background:var(--bg);display:flex;flex-direction:column;transform:translateX(100%);transition:transform .35s cubic-bezier(.2,.8,.2,1)}.ov.open .drawer{transform:none}
.dh{display:flex;justify-content:space-between;align-items:center;padding:16px 16px 16px 24px;border-bottom:1px solid var(--line)}.dh h3{margin:0;font-size:1.5rem}
.db{flex:1;overflow:auto;padding:4px 24px}.df{border-top:1px solid var(--line);padding:18px 24px calc(18px + env(safe-area-inset-bottom));display:grid;gap:10px}
.li{display:grid;grid-template-columns:84px 1fr auto;gap:14px;padding:18px 0;border-bottom:1px solid var(--line)}.li img{width:84px;aspect-ratio:4/5;object-fit:cover;border-radius:calc(var(--r) * .8);background:var(--soft)}
.li .o{font-size:.84rem;color:var(--muted)}.qty{display:inline-flex;align-items:center;border:1.5px solid var(--line);border-radius:999px;margin-top:8px}.qty button{border:0;background:none;width:34px;height:34px;cursor:pointer;font-size:1.1rem}.qty span{min-width:22px;text-align:center;font-weight:650}
.rm{background:none;border:0;color:var(--muted);cursor:pointer;font-size:.82rem;text-decoration:underline;margin-left:10px}
.prog{font-size:.88rem}.prog i{display:block;height:6px;border-radius:9px;background:var(--soft);margin-top:7px;overflow:hidden}.prog i b{display:block;height:100%;background:var(--acc);transition:width .4s}
.tot{display:flex;justify-content:space-between;font-weight:700;font-size:1.1rem}
.upsell{display:flex;gap:10px;overflow:auto;padding:12px 0 6px}.upsell button{flex:none;width:120px;border:1px solid var(--line);background:var(--card);border-radius:var(--r);padding:8px;cursor:pointer;text-align:left;font-size:.8rem}.upsell img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:calc(var(--r) * .6);margin-bottom:6px}
.modal{position:absolute;inset:0;margin:auto;width:min(1040px,calc(100% - 28px));height:min(680px,calc(100% - 28px));background:var(--bg);border-radius:var(--r);overflow:hidden;display:grid;grid-template-columns:1.05fr 1fr;opacity:0;transform:translateY(16px) scale(.98);transition:.3s}.ov.open .modal{opacity:1;transform:none}
@media(max-width:820px){.modal{grid-template-columns:1fr;height:calc(100% - 20px);width:calc(100% - 20px);overflow:auto;display:block}}
.mg{background:var(--soft);position:relative}.mg img{width:100%;height:100%;object-fit:cover}@media(max-width:820px){.mg{aspect-ratio:4/5}}
.mi{padding:34px;overflow:auto}@media(max-width:820px){.mi{padding:22px}}.mi h2{font-size:2.1rem}.x{position:absolute;right:12px;top:12px;z-index:3;background:var(--card)}
.opt{margin:20px 0 8px;font-weight:650;font-size:.92rem;display:flex;justify-content:space-between}.opt a,.opt button{font-weight:500;color:var(--muted);background:none;border:0;cursor:pointer;text-decoration:underline;font-size:.86rem}
.sizes{display:flex;flex-wrap:wrap;gap:8px}.sizes button{min-width:64px;padding:11px 14px;border:1.5px solid var(--line);border-radius:var(--r);background:var(--card);cursor:pointer;font-weight:600}.sizes button.on{border-color:var(--text);background:var(--text);color:var(--bg)}.sizes button:disabled{opacity:.4;text-decoration:line-through;cursor:not-allowed}
.big-sw{display:flex;gap:10px}.big-sw button{width:38px;height:38px;border-radius:99px;border:3px solid var(--bg);box-shadow:0 0 0 1px var(--line);cursor:pointer}.big-sw button.on{box-shadow:0 0 0 2px var(--text)}
.check{display:flex;gap:10px;align-items:flex-start;margin:14px 0;padding:14px;border:1.5px solid var(--line);border-radius:var(--r);cursor:pointer;background:var(--card)}.check input{accent-color:var(--acc);margin-top:3px;transform:scale(1.2)}
.fld{display:grid;gap:5px;margin-bottom:12px}.fld label{font-weight:600;font-size:.88rem}.fld input,.fld select,.fld textarea{font:inherit;font-size:16px;padding:12px 14px;border:1.5px solid var(--line);border-radius:calc(var(--r) * .8);background:var(--card);width:100%}
.fld input:focus,.fld select:focus,.fld textarea:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 4px color-mix(in srgb,var(--acc) 15%,transparent)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:520px){.two{grid-template-columns:1fr}}
.acc details{border-top:1px solid var(--line)}.acc summary{padding:14px 0;cursor:pointer;font-weight:600}.acc table{width:100%;font-size:.9rem;border-collapse:collapse}.acc td{padding:6px 0;border-bottom:1px solid var(--line)}.acc td:first-child{color:var(--muted);width:40%}
.co{position:absolute;inset:0;margin:auto;width:min(980px,calc(100% - 20px));height:calc(100% - 20px);background:var(--bg);border-radius:var(--r);display:grid;grid-template-columns:1.3fr 1fr;overflow:hidden;opacity:0;transition:.3s}.ov.open .co{opacity:1}
@media(max-width:820px){.co{display:block;overflow:auto}}.co .l{padding:30px;overflow:auto}.co .r{background:var(--soft);padding:30px;overflow:auto}
.steps{display:flex;gap:8px;margin-bottom:24px;font-size:.84rem;color:var(--muted)}.steps span{display:flex;align-items:center;gap:6px}.steps i{font-style:normal;width:24px;height:24px;border-radius:99px;background:var(--soft);display:grid;place-items:center;font-weight:800}.steps .on{color:var(--text)}.steps .on i{background:var(--acc);color:var(--ink)}
.pm{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.pm button{padding:12px 6px;border:1.5px solid var(--line);border-radius:var(--r);background:var(--card);cursor:pointer;font-weight:700;font-size:.82rem}.pm button.on{border-color:var(--text);box-shadow:inset 0 0 0 1px var(--text)}
.slots{display:flex;gap:8px;overflow:auto;padding-bottom:4px}.slots button{flex:none;padding:10px 14px;border:1.5px solid var(--line);border-radius:var(--r);background:var(--card);cursor:pointer;text-align:center;font-size:.86rem}.slots button.on{border-color:var(--text);background:var(--text);color:var(--bg)}.slots button b{display:block;font-size:1rem}
.okmsg{color:#1f7a4d;font-weight:600}.errmsg{color:#b42318;font-weight:600}
.done{text-align:center;padding:40px 20px}.done .tick{width:72px;height:72px;border-radius:99px;background:#e3f4ec;color:#1f7a4d;display:grid;place-items:center;margin:0 auto 16px;font-size:2rem}
.toast{position:fixed;left:50%;bottom:24px;z-index:80;transform:translate(-50%,150%);visibility:hidden;background:var(--text);color:var(--bg);padding:12px 20px;border-radius:999px;font-weight:600;transition:.3s}.toast.show{transform:translate(-50%,0);visibility:visible}
.search{position:absolute;left:0;right:0;top:0;background:var(--bg);padding:24px 0 30px;transform:translateY(-100%);transition:.3s}.ov.open .search{transform:none}.search input{width:100%;font:inherit;font-size:1.6rem;font-family:var(--fh);border:0;border-bottom:2px solid var(--text);background:none;padding:10px 0;outline:none}
.sres{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px;margin-top:20px}.sres button{border:0;background:none;text-align:left;cursor:pointer;padding:0}.sres img{border-radius:var(--r);aspect-ratio:4/5;object-fit:cover;background:var(--soft)}
.open-now{display:inline-flex;gap:8px;align-items:center;font-weight:600}.open-now:before{content:"";width:9px;height:9px;border-radius:9px;background:#22a06b;box-shadow:0 0 0 4px #22a06b33}.open-now.closed:before{background:#c9372c;box-shadow:0 0 0 4px #c9372c33}
table.hrs{border-collapse:collapse}table.hrs td{padding:4px 16px 4px 0}
.sg td,.sg th{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
:focus-visible{outline:2.5px solid var(--acc);outline-offset:2px}
"""

JS = r"""(function(){var C=window.CFG,P=C.products,K='nv_'+C.slug,cart=load('c',[]),favs=load('f',[]),cat='Kaikki',sort='pop';
function load(k,d){try{return JSON.parse(localStorage.getItem(K+k))||d}catch(e){return d}}function save(){try{localStorage.setItem(K+'c',JSON.stringify(cart));localStorage.setItem(K+'f',JSON.stringify(favs))}catch(e){}}
function eur(c){return (c/100).toLocaleString('fi-FI',{style:'currency',currency:'EUR'})}function esc(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function $(s,r){return (r||document).querySelector(s)}function $$(s,r){return [].slice.call((r||document).querySelectorAll(s))}
function img(p,ci){return p.colors?p.colors[ci||0].img:p.img}
function stars(r){return '★★★★★'.slice(0,Math.round(r))+'☆☆☆☆☆'.slice(0,5-Math.round(r))}
function toast(t){var e=$('#toast');e.textContent=t;e.classList.add('show');clearTimeout(e._t);e._t=setTimeout(function(){e.classList.remove('show')},2300)}
var heart='<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z"/></svg>';
function card(p){var ci=0;return '<article class="card" data-id="'+p.id+'" tabindex="0" aria-label="'+esc(p.name)+'"><div class="ph"><img src="'+img(p)+'" alt="'+esc(p.name)+'" loading="lazy">'+(p.badge?'<span class="bd'+(p.compare?' sale':'')+'">'+esc(p.badge)+'</span>':'')+
'<button class="fav'+(favs.indexOf(p.id)>=0?' on':'')+'" data-fav="'+p.id+'" aria-label="Suosikki">'+heart+'</button><button class="qv" data-open="'+p.id+'">Pikakatselu</button></div>'+
'<h3>'+esc(p.name)+'</h3><div class="row"><span class="price">'+(p.cake?'alk. ':'')+eur(p.price)+(p.compare?'<span class="old">'+eur(p.compare)+'</span>':'')+'</span><span class="rv"><span class="stars">★</span> '+String(p.rating).replace('.',',')+' ('+p.nrev+')</span></div>'+
(p.colors&&p.colors.length>1?'<div class="sw">'+p.colors.map(function(c,i){return '<button data-sw="'+i+'" style="background:'+c.hex+'" class="'+(i?'':'on')+'" aria-label="'+esc(c.n)+'" title="'+esc(c.n)+'"></button>'}).join('')+'</div>':'')+
(p.tags&&p.tags.length?'<div class="sw">'+p.tags.map(function(t){return '<span class="tag" title="'+({G:'Gluteeniton',L:'Laktoositon',V:'Vegaaninen',M:'Maidoton'}[t])+'">'+t+'</span>'}).join('')+'</div>':'')+'</article>'}
function renderGrid(){var list=P.filter(function(p){return cat==='Kaikki'||p.cat===cat||(cat==='G'&&p.tags&&p.tags.indexOf('G')>=0)});
list.sort({pop:function(a,b){return b.nrev-a.nrev},low:function(a,b){return a.price-b.price},high:function(a,b){return b.price-a.price},rate:function(a,b){return b.rating-a.rating}}[sort]);
$('#grid').innerHTML=list.map(card).join('');$('#cnt').textContent=list.length+' tuotetta'}
function setCat(c){cat=c;$$('#chips .chip').forEach(function(b){b.classList.toggle('on',b.dataset.cat===c)});renderGrid()}
// ---- kori
function count(){var n=cart.reduce(function(a,l){return a+l.q},0);$$('[data-cc]').forEach(function(e){e.textContent=n;e.hidden=!n});var f=favs.length;$$('[data-fc]').forEach(function(e){e.textContent=f;e.hidden=!f})}
function lineKey(l){return [l.id,l.c,l.s,l.g,l.x||''].join('|')}
function add(l){var k=lineKey(l),r=cart.find(function(x){return lineKey(x)===k});if(r)r.q+=l.q;else cart.push(l);save();count();openCart()}
function sub(){return cart.reduce(function(a,l){return a+l.u*l.q},0)}
function openOv(id){var o=$(id);o.classList.add('open');document.body.style.overflow='hidden';var f=o.querySelector('[data-close]');setTimeout(function(){f&&f.focus()},60)}
function closeOv(){$$('.ov.open').forEach(function(o){o.classList.remove('open')});document.body.style.overflow=''}
function openCart(){closeOv();renderCart();openOv('#cartov')}
function renderCart(){var b=$('#cartb'),f=$('#cartf');if(!cart.length){b.innerHTML='<div class="done"><p style="font-family:var(--fh);font-size:1.4rem">Ostoskori on tyhjä</p><p class="muted">Löydä jotain ihanaa mallistostamme.</p></div>';f.innerHTML='<button class="btn block" data-close>Jatka ostoksia</button>';return}
b.innerHTML=cart.map(function(l,i){var p=P.find(function(x){return x.id===l.id});return '<div class="li"><img src="'+img(p,l.c)+'" alt=""><div><b>'+esc(p.name)+'</b><div class="o">'+[p.colors?p.colors[l.c].n:'',l.s,l.x,l.g?'Lahjapaketointi':''].filter(Boolean).map(esc).join(' · ')+'</div><span class="qty"><button data-q="-1" data-i="'+i+'" aria-label="Vähennä">−</button><span>'+l.q+'</span><button data-q="1" data-i="'+i+'" aria-label="Lisää">+</button></span><button class="rm" data-rm="'+i+'">Poista</button></div><b class="price">'+eur(l.u*l.q)+'</b></div>'}).join('')+
'<div class="upsell">'+P.filter(function(p){return !cart.some(function(l){return l.id===p.id})&&!p.cake}).slice(0,4).map(function(p){return '<button data-open="'+p.id+'"><img src="'+img(p)+'" alt=""><b>'+esc(p.name)+'</b><br>'+eur(p.price)+'</button>'}).join('')+'</div>';
var s=sub(),left=C.free-s;f.innerHTML='<div class="prog">'+(left<=0?'<b>Toimitus on ilmainen! 🎉</b>':'Vielä <b>'+eur(left)+'</b> ilmaiseen toimitukseen')+'<i><b style="width:'+Math.min(100,s/C.free*100)+'%"></b></i></div><div class="tot"><span>Välisumma</span><span>'+eur(s)+'</span></div><button class="btn block" id="tocheck">Kassalle →</button><p class="small muted" style="margin:0;text-align:center">Turvallinen maksu · 14 päivän palautusoikeus</p>'}
// ---- tuote
var cur=null,st={};
function openProduct(id){var p=P.find(function(x){return x.id===id});cur=p;st={c:0,s:null,q:1,g:false,cs:0,cf:0,gf:false,txt:''};renderProduct();openOv('#pov')}
function priceNow(){var p=cur,u=p.price;if(p.cake){u=C.cake.sizes[st.cs][1]+(st.gf?C.cake.gf:0)}if(st.g)u+=C.gift||0;return u}
function renderProduct(){var p=cur,col=p.colors?p.colors[st.c]:null;$('#pimg').src=img(p,st.c);$('#pimg').alt=p.name;
var h='<span class="eyebrow">'+esc(p.cat)+'</span><h2>'+esc(p.name)+'</h2><p><span class="stars">'+stars(p.rating)+'</span> <span class="rv">'+String(p.rating).replace('.',',')+' · '+p.nrev+' arvostelua</span></p>'+
'<p class="price" style="font-size:1.6rem;margin:10px 0" id="pp">'+eur(priceNow())+(p.compare?'<span class="old">'+eur(p.compare)+'</span>':'')+'</p><p class="muted">'+esc(p.desc)+'</p>';
if(p.colors&&p.colors.length>1)h+='<div class="opt"><span>Väri: <span class="muted">'+esc(col.n)+'</span></span></div><div class="big-sw">'+p.colors.map(function(c,i){return '<button data-pc="'+i+'" class="'+(i===st.c?'on':'')+'" style="background:'+c.hex+'" aria-label="'+esc(c.n)+'"></button>'}).join('')+'</div>';
if(p.sizes&&p.sizes.length)h+='<div class="opt"><span>Koko</span>'+(C.sizeguide?'<button type="button" data-sg>Kokotaulukko</button>':'')+'</div><div class="sizes">'+p.sizes.map(function(s){var out=p.soldout&&p.soldout[s+'|'+(col?col.n:'')];return '<button data-ps="'+esc(s)+'" class="'+(st.s===s?'on':'')+'" '+(out?'disabled title="Loppu"':'')+'>'+esc(s)+'</button>'}).join('')+'</div>';
if(p.cake){h+='<div class="opt">Koko</div><div class="sizes">'+C.cake.sizes.map(function(s,i){return '<button data-cs="'+i+'" class="'+(st.cs===i?'on':'')+'">'+esc(s[0])+'<br><span class="small">'+eur(s[1])+'</span></button>'}).join('')+'</div><div class="opt">Täyte</div><div class="sizes">'+C.cake.fill.map(function(f,i){return '<button data-cf="'+i+'" class="'+(st.cf===i?'on':'')+'">'+esc(f)+'</button>'}).join('')+'</div>'+
'<div class="fld" style="margin-top:14px"><label for="ctx">Teksti kakkuun (valinnainen)</label><input id="ctx" maxlength="30" placeholder="Onnea Aino 5 v!" value="'+esc(st.txt)+'"></div><label class="check"><input type="checkbox" id="cgf" '+(st.gf?'checked':'')+'><span><b>Gluteeniton</b> +'+eur(C.cake.gf)+'</span></label>'}
if(C.gift&&!p.cake)h+='<label class="check"><input type="checkbox" id="pg" '+(st.g?'checked':'')+'><span><b>Lahjapaketointi +'+eur(C.gift)+'</b><br><span class="small muted">Kaunis rasia, silkkipaperi ja käsin kirjoitettu kortti.</span></span></label>';
if(p.sub)h+='<label class="check"><input type="checkbox" id="psub"><span><b>Viikkotilaus −10 %</b><br><span class="small muted">Sama leipä joka perjantai. Voit tauottaa tai perua milloin vain.</span></span></label>';
h+='<div style="display:flex;gap:10px;margin:18px 0"><span class="qty" style="margin:0"><button data-pq="-1" aria-label="Vähennä">−</button><span>'+st.q+'</span><button data-pq="1" aria-label="Lisää">+</button></span><button class="btn" style="flex:1" id="padd">Lisää ostoskoriin · '+eur(priceNow()*st.q)+'</button></div><p class="errmsg small" id="perr"></p>'+
'<div class="acc">'+'<details open><summary>Tuotetiedot</summary><table>'+p.details.map(function(d){return '<tr><td>'+esc(d[0])+'</td><td>'+esc(d[1])+'</td></tr>'}).join('')+'</table></details><details><summary>Toimitus ja palautus</summary><p class="small muted">'+C.ship.map(function(s){return esc(s[0])+' '+(s[1]?eur(s[1]):'0 €')}).join(' · ')+'. Ilmainen toimitus yli '+eur(C.free)+'. 14 päivän palautusoikeus.</p></details></div>';
$('#pinfo').innerHTML=h}
function addCur(){var p=cur;if(p.sizes&&p.sizes.length&&!st.s){$('#perr').textContent='Valitse koko.';return}
var x=p.cake?[C.cake.sizes[st.cs][0],C.cake.fill[st.cf],st.gf?'gluteeniton':'',st.txt?'”'+st.txt+'”':''].filter(Boolean).join(', '):'';
var u=priceNow(),sb=$('#psub')&&$('#psub').checked;if(sb){u=Math.round(u*.9);x='Viikkotilaus perjantaisin'}
add({id:p.id,c:st.c,s:st.s,g:st.g,x:x,u:u,q:st.q,cake:!!p.cake})}
// ---- kassa
var co={step:1,ship:0,pay:'Verkkopankki',slot:null,zipOk:null,f:{}};
function slots(){var out=[],d=new Date();d.setHours(0,0,0,0);var late=new Date().getHours()>=20,minDays=cart.some(function(l){return l.cake})?3:1;for(var i=minDays;i<minDays+6;i++){var x=new Date(d);x.setDate(d.getDate()+i);var wd=x.getDay();if(wd===0)continue;
var times=wd===6?['8–10','10–12','12–14']:['7–9','9–12','12–15','15–17'];times.forEach(function(t){if(late&&i===1&&parseInt(t)<12)return;out.push({d:x,t:t})})}return out}
// Kotiinkuljetusalueet: postinumerovälit → paikkakunta
var ZONES=[[84100,84880,'Ylivieska'],[85200,85210,'Alavieska'],[85410,85410,'Sievi'],[85500,85580,'Nivala']];
function zone(z){if(!/^\d{5}$/.test(z))return null;var n=+z,r=ZONES.find(function(x){return n>=x[0]&&n<=x[1]});return r?r[2]:false}
function keep(){['cn','ce','cp','adr','zip','city','gn','dn'].forEach(function(k){var e=$('#'+k);if(e)co.f[k]=e.value})}
function fv(k){return esc(co.f[k]||'')}
var WD=['su','ma','ti','ke','to','pe','la'];
function shipCost(){var s=sub(),c=C.ship[co.ship][1];return s>=C.free?0:c}
function renderCo(){var L=$('#col'),R=$('#cor'),s=sub();
R.innerHTML='<h3>Tilauksesi</h3>'+cart.map(function(l){var p=P.find(function(x){return x.id===l.id});return '<div class="li" style="grid-template-columns:64px 1fr auto"><img src="'+img(p,l.c)+'" alt="" style="width:64px"><div><b>'+esc(p.name)+'</b><div class="o">'+[l.q+' kpl',p.colors?p.colors[l.c].n:'',l.s,l.x].filter(Boolean).map(esc).join(' · ')+'</div></div><b class="price">'+eur(l.u*l.q)+'</b></div>'}).join('')+
'<div style="display:grid;gap:6px;margin-top:16px"><div class="tot" style="font-weight:500;font-size:1rem"><span>Tuotteet</span><span>'+eur(s)+'</span></div><div class="tot" style="font-weight:500;font-size:1rem"><span>'+esc(C.ship[co.ship][0])+'</span><span>'+(shipCost()?eur(shipCost()):'0,00 €')+'</span></div><div class="tot" style="border-top:1px solid var(--line);padding-top:12px;margin-top:6px"><span>Yhteensä</span><span>'+eur(s+shipCost())+'</span></div><p class="small muted">Sis. ALV 14 %/25,5 %</p></div>';
var stp='<div class="steps">'+['Tiedot','Toimitus','Maksu'].map(function(t,i){return '<span class="'+(co.step===i+1?'on':'')+'"><i>'+(i+1)+'</i>'+t+'</span>'}).join('<span>—</span>')+'</div>';
if(co.step===1)L.innerHTML=stp+'<h2>Yhteystiedot</h2><div class="fld"><label for="cn">Nimi</label><input id="cn" autocomplete="name" value="'+fv('cn')+'"></div><div class="two"><div class="fld"><label for="ce">Sähköposti</label><input id="ce" type="email" autocomplete="email" value="'+fv('ce')+'"></div><div class="fld"><label for="cp">Puhelin</label><input id="cp" type="tel" autocomplete="tel" value="'+fv('cp')+'"></div></div><p class="errmsg small" id="cerr"></p><button class="btn block" data-next>Jatka toimitukseen →</button>';
if(co.step===2){var h=stp+'<h2>Toimitus</h2>'+C.ship.map(function(x,i){return '<label class="check"><input type="radio" name="sh" value="'+i+'" '+(co.ship===i?'checked':'')+'><span style="flex:1"><b>'+esc(x[0])+'</b><br><span class="small muted">'+esc(x[2])+'</span></span><b>'+(x[1]&&s<C.free?eur(x[1]):'0 €')+'</b></label>'}).join('');
if(C.bakery){h+='<div class="opt">'+(co.ship===0?'Noutoaika':'Toimitusaika')+(cart.some(function(l){return l.cake})?' <span class="muted small">(kakut aikaisintaan 3 päivän päästä)</span>':'')+'</div><div class="slots">'+slots().map(function(x,i){return '<button data-slot="'+i+'" class="'+(co.slot===i?'on':'')+'"><b>'+WD[x.d.getDay()]+' '+x.d.getDate()+'.'+(x.d.getMonth()+1)+'.</b>klo '+x.t+'</button>'}).join('')+'</div>';
if(co.ship===1){var zz=zone(co.f.zip||'');h+='<div class="fld" style="margin-top:14px"><label for="zip">Postinumero</label><input id="zip" inputmode="numeric" maxlength="5" placeholder="84100" autocomplete="postal-code" value="'+fv('zip')+'"><span id="zipmsg" class="small '+(zz?'okmsg':zz===false?'errmsg':'muted')+'">'+(zz?'✓ Toimitamme alueelle '+zz+'.':zz===false?'Emme vielä toimita tälle alueelle. Valitse nouto leipomosta.':'Toimitamme Ylivieskaan, Alavieskaan, Sieviin ja Nivalaan.')+'</span></div><div class="fld"><label for="adr">Katuosoite</label><input id="adr" autocomplete="street-address" placeholder="Esim. Kauppakatu 5 B 12" value="'+fv('adr')+'"></div><div class="fld"><label for="dn">Ohje kuljettajalle (valinnainen)</label><input id="dn" maxlength="140" placeholder="Ovikoodi, porraskäytävä tai jätä oven taakse" value="'+fv('dn')+'"></div>'}}
else h+='<div class="fld" style="margin-top:14px"><label for="adr">Katuosoite</label><input id="adr" autocomplete="street-address" value="'+fv('adr')+'"></div><div class="two"><div class="fld"><label for="zip">Postinumero</label><input id="zip" inputmode="numeric" maxlength="5" value="'+fv('zip')+'"></div><div class="fld"><label for="city">Postitoimipaikka</label><input id="city" value="'+fv('city')+'"></div></div><div class="fld"><label for="gn">Lahjaviesti korttiin (valinnainen)</label><textarea id="gn" rows="2" maxlength="200" placeholder="Lämpimät terveiset!">'+fv('gn')+'</textarea></div>';
L.innerHTML=h+'<p class="errmsg small" id="cerr"></p><div style="display:flex;gap:10px"><button class="btn line" data-back>← Takaisin</button><button class="btn" style="flex:1" data-next>Jatka maksuun →</button></div>'}
if(co.step===3)L.innerHTML=stp+'<h2>Maksutapa</h2><div class="pm">'+['Verkkopankki','MobilePay','Kortti','Apple Pay','Google Pay','Lasku'].map(function(m){return '<button data-pm="'+m+'" class="'+(co.pay===m?'on':'')+'">'+m+'</button>'}).join('')+'</div><p class="small muted" style="margin:12px 0">Maksut käsitellään suomalaisen maksupalvelun kautta. Rahat menevät suoraan kauppiaalle.</p><label class="check"><input type="checkbox" id="terms"><span>Hyväksyn toimitus- ja tilausehdot.</span></label><p class="errmsg small" id="cerr"></p><div style="display:flex;gap:10px"><button class="btn line" data-back>← Takaisin</button><button class="btn" style="flex:1" id="payb">Maksa '+eur(s+shipCost())+'</button></div>';
if(co.step===4){L.innerHTML='<div class="done"><div class="tick">✓</div><h2>Kiitos tilauksestasi!</h2><p>Tilausnumero <b>'+co.no+'</b>. '+(C.bakery&&co.slot!=null?(co.ship===1?'Tuomme tilauksesi osoitteeseen <b>'+fv('adr')+', '+esc(zone(co.f.zip)||'')+'</b> <b>'+co.when+'</b>. Kuljettaja soittaa tai tekstaa, kun on matkalla.':'Tilauksesi on noudettavissa leipomosta <b>'+co.when+'</b>.'):'Saat vahvistuksen ja seurantalinkin sähköpostiisi.')+'</p><p class="small muted" style="background:var(--soft);padding:12px;border-radius:var(--r)">Tämä on Netvon <b>mallisivu</b> – tilausta ei tehty eikä maksua veloitettu.</p><p><a class="btn" href="https://netvo.fi/#yhteys" target="_top">Haluan tällaisen kaupan</a></p></div>';R.innerHTML=''}}
function coNext(){var e=$('#cerr');keep();if(co.step===1){var n=$('#cn').value.trim(),m=$('#ce').value.trim();if(!n||!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(m)){e.textContent='Tarkista nimi ja sähköposti.';return}}
if(co.step===2){if(C.bakery&&co.slot==null){e.textContent='Valitse aika.';return}if(C.bakery&&co.ship===1){var zn=zone((co.f.zip||'').trim());if(!zn){e.textContent=zn===false?'Emme toimita tähän postinumeroon – valitse nouto leipomosta.':'Kirjoita postinumero.';$('#zip').focus();return}if((co.f.adr||'').trim().length<4){e.textContent='Kirjoita katuosoite, johon tilaus tuodaan.';$('#adr').focus();return}}if(C.bakery){var sl=slots()[co.slot];co.when=WD[sl.d.getDay()]+' '+sl.d.getDate()+'.'+(sl.d.getMonth()+1)+'. klo '+sl.t}if(!C.bakery&&(!$('#adr').value.trim()||!/^\d{5}$/.test($('#zip').value.trim()))){e.textContent='Tarkista osoite ja postinumero.';return}}
co.step++;renderCo();$('#col').scrollTop=0}
function openCo(){if(!cart.length)return;co={step:1,ship:0,pay:'Verkkopankki',slot:null,zipOk:null,f:{}};closeOv();renderCo();openOv('#coov')}
// ---- haku
function search(q){q=q.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');var r=P.filter(function(p){return (p.name+' '+p.cat+' '+p.desc).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').indexOf(q)>=0});
$('#sres').innerHTML=q?(r.length?r.map(function(p){return '<button data-open="'+p.id+'"><img src="'+img(p)+'" alt=""><b>'+esc(p.name)+'</b><br><span class="muted">'+eur(p.price)+'</span></button>'}).join(''):'<p class="muted">Ei tuloksia haulle.</p>'):''}
// ---- tapahtumat
document.addEventListener('click',function(e){var t=e.target,x;
if((x=t.closest('[data-fav]'))){e.stopPropagation();var id=+x.dataset.fav,i=favs.indexOf(id);if(i<0){favs.push(id);toast('Lisätty suosikkeihin')}else{favs.splice(i,1);toast('Poistettu suosikeista')}save();count();x.classList.toggle('on',i<0);return}
if((x=t.closest('.card [data-sw]'))){e.stopPropagation();var c=x.closest('.card'),p=P.find(function(y){return y.id===+c.dataset.id});c.querySelector('img').src=img(p,+x.dataset.sw);$$('[data-sw]',c).forEach(function(b){b.classList.toggle('on',b===x)});return}
if((x=t.closest('[data-open]'))){e.stopPropagation();closeOv();openProduct(+x.dataset.open);return}
if((x=t.closest('.card'))){openProduct(+x.dataset.id);return}
if((x=t.closest('[data-cat]'))){setCat(x.dataset.cat);if(x.classList.contains('tile')||x.closest('nav.main')){e.preventDefault();$('#tuotteet').scrollIntoView();$('nav.main').classList.remove('open')}return}
if(t.closest('[data-close]')||t.classList.contains('bg')){closeOv();return}
if(t.closest('[data-cart]')){openCart();return}if(t.closest('[data-search]')){openOv('#sov');setTimeout(function(){$('#sq').focus()},80);return}
if(t.closest('[data-menu]')){$('nav.main').classList.toggle('open');return}
if((x=t.closest('[data-pc]'))){st.c=+x.dataset.pc;st.s=null;renderProduct();return}if((x=t.closest('[data-ps]'))){st.s=x.dataset.ps;renderProduct();return}
if((x=t.closest('[data-cs]'))){st.cs=+x.dataset.cs;renderProduct();return}if((x=t.closest('[data-cf]'))){st.cf=+x.dataset.cf;renderProduct();return}
if((x=t.closest('[data-pq]'))){st.q=Math.max(1,Math.min(20,st.q+ +x.dataset.pq));renderProduct();return}
if(t.id==='padd'){addCur();return}if(t.closest('[data-sg]')){openOv('#sgov');return}
if((x=t.closest('[data-q]'))){var l=cart[+x.dataset.i];l.q+=+x.dataset.q;if(l.q<1)cart.splice(+x.dataset.i,1);save();count();renderCart();return}
if((x=t.closest('[data-rm]'))){cart.splice(+x.dataset.rm,1);save();count();renderCart();return}
if(t.id==='tocheck'){openCo();return}if(t.closest('[data-next]')){coNext();return}if(t.closest('[data-back]')){keep();co.step--;renderCo();return}
if((x=t.closest('[data-slot]'))){co.slot=+x.dataset.slot;$$('[data-slot]').forEach(function(b){b.classList.toggle('on',b===x)});return}
if((x=t.closest('[data-pm]'))){co.pay=x.dataset.pm;$$('[data-pm]').forEach(function(b){b.classList.toggle('on',b===x)});return}

if(t.id==='payb'){if(!$('#terms').checked){$('#cerr').textContent='Hyväksy ehdot.';return}t.disabled=true;t.textContent='Siirrytään maksamaan…';setTimeout(function(){co.no=new Date().toISOString().slice(0,10).replace(/-/g,'')+'-'+Math.random().toString(16).slice(2,8).toUpperCase();cart=[];save();count();co.step=4;renderCo()},900);return}});
document.addEventListener('change',function(e){var t=e.target;if(t.id==='pg'){st.g=t.checked;renderProduct()}if(t.id==='cgf'){st.gf=t.checked;renderProduct()}if(t.name==='sh'){keep();co.ship=+t.value;co.slot=null;renderCo()}if(t.id==='sort'){sort=t.value;renderGrid()}});
document.addEventListener('input',function(e){if(e.target.id==='zip'&&C.bakery&&co.ship===1){var z=e.target.value.replace(/\D/g,'');e.target.value=z;var zn=zone(z),m=$('#zipmsg');m.className='small '+(zn?'okmsg':zn===false?'errmsg':'muted');m.textContent=zn?'✓ Toimitamme alueelle '+zn+'.':zn===false?'Emme vielä toimita tälle alueelle. Valitse nouto leipomosta.':'Toimitamme Ylivieskaan, Alavieskaan, Sieviin ja Nivalaan.'}if(e.target.id==='sq')search(e.target.value);if(e.target.id==='ctx')st.txt=e.target.value});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeOv();if(e.key==='Enter'&&e.target.classList&&e.target.classList.contains('card'))openProduct(+e.target.dataset.id)});
if(C.hours){var n=new Date(),d=n.getDay(),hh=n.getHours(),row=C.hours[d===0?2:d===6?1:0],open=row[1]!=null&&hh>=row[1]&&hh<row[2];$$('[data-open-now]').forEach(function(e){e.className='open-now'+(open?'':' closed');e.textContent=open?'Auki nyt – suljemme klo '+row[2]:'Suljettu nyt – tilaa verkosta valmiiksi'})}
renderGrid();count()})();"""


def _icons():
    return {
        "search": '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>',
        "heart": '<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z"/></svg>',
        "bag": '<svg viewBox="0 0 24 24"><path d="M5 8h14l-1 13H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
        "menu": '<svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
        "x": '<svg viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    }


def page(c):
    I = _icons()
    css = c["css"]
    root = ";".join(f"--{k}:{v}" for k, v in css.items())
    P = c["products"]
    cats = c["nav"]
    tiles = [(name, next((p.get("img") or p["colors"][0]["img"]) for p in P if p["cat"] == name)) for name in cats if any(p["cat"] == name for p in P)]
    cfg = {k: c[k] for k in ("slug", "products", "free", "ship") if k in c}
    for k in ("gift", "sizeguide", "bakery", "cake", "hours"):
        if k in c: cfg[k] = c[k]
    st = c["story"]
    hero = c["hero"]
    story_img = next((p.get("img") or p["colors"][0]["img"]) for p in P)
    ph = c.get("photos") or {}
    U = lambda i, w, h=None: f"https://images.unsplash.com/{i}?auto=format&fit=crop&w={w}{f'&h={h}' if h else ''}&q=72"
    SS = lambda i, ws, ar=None: ", ".join(f"{U(i, w, int(w * ar) if ar else None)} {w}w" for w in ws)
    if ph.get("tiles"):
        tiles = [(n, U(ph["tiles"][n], 520, 650)) if n in ph["tiles"] else (n, im) for n, im in tiles]
    hero_img = (f'<img src="{U(ph["hero"], 1600)}" srcset="{SS(ph["hero"], (800, 1200, 1600, 2200))}" sizes="100vw" alt="" fetchpriority="high">' if ph.get("hero") else f'<img src="{c["cover"]}" alt="">')
    story_tag = (f'<img src="{U(ph["story"], 900, 900)}" srcset="{SS(ph["story"], (500, 900, 1300), 1)}" sizes="(max-width:860px) 100vw, 50vw" alt="" loading="lazy">' if ph.get("story") else f'<img src="{story_img}" alt="" loading="lazy">')
    band = ""
    if ph.get("band"):
        bi, bh, bp = ph["band"]
        band = f'<section class="band" style="--bimg:url({U(bi, 2000)})"><div class="w"><h2>{esc(bh)}</h2><p>{esc(bp)}</p><a class="btn light" href="#tuotteet">Tutustu tuotteisiin →</a></div></section>'
    nl_style = f' style="--nimg:url({U(ph["nl"], 1600)})"' if ph.get("nl") else ""
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(c['title'])}</title><meta name="description" content="{esc(c['meta'])}"><meta name="robots" content="noindex"><meta name="theme-color" content="{css['acc']}">
<style>:root{{{root}}}{CSS}</style></head><body>
<div class="demo">Tämä on Netvon <b>räätälöity verkkokauppa</b> -mallisivu. Kaikki toimii – tilauksia ei tehdä. <a href="https://netvo.fi/">Katso hinnat ja pyydä tarjous →</a></div>
<div class="annc">Ilmainen toimitus yli {c['free'] // 100} € tilauksiin{' · Tilaa klo 20 mennessä, leivomme aamuksi' if c.get('bakery') else ' · Lahjapaketointi saatavilla'}</div>
<header class="top"><div class="w bar"><div style="display:flex;align-items:center;gap:4px"><button class="ic burger" data-menu aria-label="Valikko">{I['menu']}</button>
<nav class="main" aria-label="Valikko">{''.join(f'<a href="#tuotteet" data-cat="{esc(n)}">{esc(n)}</a>' for n in cats)}<a href="#tarina">Meistä</a></nav></div>
<a class="brand" href="#">{esc(c['name'])}<small>{esc(c['tagline'])}</small></a>
<div class="tools"><button class="ic" data-search aria-label="Hae">{I['search']}</button><button class="ic hide-m" aria-label="Suosikit" onclick="document.getElementById('tuotteet').scrollIntoView()">{I['heart']}<b class="cnt" data-fc hidden>0</b></button><button class="ic" data-cart aria-label="Ostoskori">{I['bag']}<b class="cnt" data-cc hidden>0</b></button></div></div></header>
<section class="hero">{hero_img}<div class="w"><div class="in"><span class="kick">{esc(hero['kicker'])}</span><h1>{esc(hero['h'])}</h1><p>{esc(hero['p'])}</p>
<a class="btn light" href="#tuotteet">{esc(hero['cta'])} →</a>{' <span data-open-now style="margin-left:16px;color:#fff"></span>' if c.get('hours') else ''}</div></div></section>
<div class="usp">{''.join(f'<div><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in c['usp'])}</div>
<section class="s"><div class="w"><div class="sh"><div><span class="eyebrow">Kategoriat</span><h2>Löydä suosikkisi</h2></div></div>
<div class="tiles">{''.join(f'<button class="tile" data-cat="{esc(n)}"><img src="{im}" alt="" loading="lazy"><span>{esc(n)}</span></button>' for n, im in tiles)}</div></div></section>
<section class="s" id="tuotteet" style="padding-top:20px;scroll-margin-top:80px"><div class="w"><div class="sh"><div><span class="eyebrow">Mallisto</span><h2>Kaikki tuotteet</h2></div><span class="muted" id="cnt"></span></div>
<div class="filters" id="chips"><button class="chip on" data-cat="Kaikki">Kaikki</button>{''.join(f'<button class="chip" data-cat="{esc(n)}">{esc(n)}</button>' for n in cats)}
<label class="small muted" for="sort" style="margin-left:auto">Järjestä</label><select id="sort" style="margin-left:0"><option value="pop">Suosituimmat</option><option value="rate">Parhaiksi arvioidut</option><option value="low">Halvin ensin</option><option value="high">Kallein ensin</option></select></div>
<div class="grid" id="grid"></div></div></section>
<section class="s" id="tarina" style="background:var(--card);border-block:1px solid var(--line)"><div class="w story"><div class="pic">{story_tag}</div><div><span class="eyebrow">Tarinamme</span><h2 style="font-size:clamp(1.8rem,4vw,2.8rem)">{esc(st['h'])}</h2>{''.join(f'<p class="muted" style="font-size:1.08rem">{esc(x)}</p>' for x in st['p'])}
<div class="stats">{''.join(f'<div><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in st['stats'])}</div>{('<h3 style="margin-top:30px">Aukioloajat</h3><table class="hrs">' + ''.join(f'<tr><td>{esc(d)}</td><td>{f"{a}–{b}" if a else "suljettu"}</td></tr>' for d, a, b in c['hours']) + '</table><p data-open-now></p>') if c.get('hours') else ''}</div></div></section>
{band}<section class="s"><div class="w"><div class="sh"><div><span class="eyebrow">Asiakkaat sanovat</span><h2>4,9 / 5 tähteä</h2></div></div>
<div class="revs">{''.join(f'<div class="rev"><span class="stars">{"★" * r}</span><p>”{esc(t)}”</p><b>{esc(n)}</b><br><span class="small muted">Vahvistettu ostaja · {esc(pr)}</span></div>' for n, r, t, pr in c['reviews'])}</div></div></section>
<section class="s" style="padding-top:0"><div class="w faqw"><div><span class="eyebrow">Apua</span><h2>Usein kysyttyä</h2><p class="muted">Etkö löytänyt vastausta? {esc(c['contact'][0])} · {esc(c['contact'][1])}</p></div>
<div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in c['faq'])}</div></div></section>
<section class="s" style="padding-top:0"><div class="w"><div class="nl{' ph' if nl_style else ''}"{nl_style}><div><h2 style="color:var(--ink)">Liity kanta-asiakkaaksi – saat 10 %</h2><p style="opacity:.9;margin:0">Uutuudet ja tarjoukset ensimmäisenä. Ei roskapostia.</p></div>
<form onsubmit="event.preventDefault();this.innerHTML='<p style=&quot;margin:0;font-weight:700&quot;>Kiitos! Koodi TERVETULOA10 on matkalla sähköpostiisi.</p>'"><label class="sr" for="nle" style="position:absolute;left:-9999px">Sähköposti</label><input id="nle" type="email" required placeholder="sähköposti@esimerkki.fi"><button class="btn">Liity</button></form></div></div></section>
<footer><div class="w"><div class="fc"><div><h4>{esc(c['name'])}</h4><p>{esc(c['meta'])}</p></div><div><h4>Kauppa</h4><ul>{''.join(f'<li><a href="#tuotteet" data-cat="{esc(n)}">{esc(n)}</a></li>' for n in cats)}</ul></div>
<div><h4>Asiakaspalvelu</h4><ul><li>Toimitus ja palautus</li><li>Tilauksen seuranta</li><li>Usein kysytyt</li><li>Tietosuoja</li></ul></div><div><h4>Yhteys</h4><ul><li>{esc(c['contact'][0])}</li><li>{esc(c['contact'][1])}</li></ul></div></div>
<div class="pays"><span>Verkkopankit</span><span>MobilePay</span><span>Visa</span><span>Mastercard</span><span>Apple Pay</span><span>Google Pay</span><span>Lasku</span>{'<span style="border:0;opacity:.7">Kuvat: Unsplash</span>' if ph else ''}<span style="margin-left:auto;border:0;font-weight:500">Toteutus: <a href="https://netvo.fi/" style="color:#ffd24a">Netvo – räätälöity verkkokauppa</a></span></div></div></footer>
<div class="ov" id="cartov"><div class="bg"></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="Ostoskori"><div class="dh"><h3>Ostoskori</h3><button class="ic" data-close aria-label="Sulje">{I['x']}</button></div><div class="db" id="cartb"></div><div class="df" id="cartf"></div></aside></div>
<div class="ov" id="pov"><div class="bg"></div><div class="modal" role="dialog" aria-modal="true" aria-label="Tuote"><button class="ic x" data-close aria-label="Sulje">{I['x']}</button><div class="mg"><img id="pimg" alt=""></div><div class="mi" id="pinfo"></div></div></div>
<div class="ov" id="coov"><div class="bg"></div><div class="co" role="dialog" aria-modal="true" aria-label="Kassa"><button class="ic x" data-close aria-label="Sulje" style="position:absolute;right:12px;top:12px;z-index:3">{I['x']}</button><div class="l" id="col"></div><div class="r" id="cor"></div></div></div>
<div class="ov" id="sov"><div class="bg"></div><div class="search"><div class="w"><div style="display:flex;gap:10px;align-items:center"><label for="sq" style="position:absolute;left:-9999px">Hae</label><input id="sq" placeholder="Mitä etsit?" autocomplete="off"><button class="ic" data-close aria-label="Sulje">{I['x']}</button></div><div class="sres" id="sres"></div></div></div></div>
<div class="ov" id="sgov"><div class="bg"></div><div class="modal" style="display:block;height:auto;max-height:90%;width:min(560px,calc(100% - 28px));padding:30px;overflow:auto" role="dialog" aria-modal="true" aria-label="Kokotaulukko"><button class="ic x" data-close aria-label="Sulje">{I['x']}</button><h2>Kokotaulukko</h2>
<table class="sg" style="border-collapse:collapse;width:100%"><tr><th>Koko</th><th>Kenkäkoko</th><th>Jalan pituus</th></tr><tr><td>36–38</td><td>36–38</td><td>23–24,5 cm</td></tr><tr><td>39–41</td><td>39–41</td><td>25–26,5 cm</td></tr><tr><td>42–44</td><td>42–44</td><td>27–28,5 cm</td></tr><tr><td>45–47</td><td>45–47</td><td>29–30,5 cm</td></tr></table>
<p class="muted small">Lapaset: S = naisten pieni, M = naisten / miesten pieni, L = miesten. Kokojen välissä? Valitse isompi – villa painuu käytössä.</p></div></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>window.CFG={json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/')};</script><script>{JS}</script></body></html>"""


def rakenna(root):
    """Kirjoittaa räätälöidyt mallikaupat kansioon <root>/netvo/mallit/<slug>/ (index.html + kuvat/). Palauttaa slugit."""
    root = pathlib.Path(root)
    out = []
    for make in (villa, leipomo):
        tmp = root / 'netvo' / 'mallit'
        # slug selviää datasta; kansio luodaan ensin väliaikaisesti kuvia varten
        slug = {'villa': 'kauppa-kasityo', 'leipomo': 'kauppa-leipomo'}[make.__name__]
        folder = tmp / slug
        (folder / 'kuvat').mkdir(parents=True, exist_ok=True)
        c = make(folder / 'kuvat')
        c = {**c, 'cover': 'kuvat/kansi.svg'}
        for p in c['products']:
            for col in p.get('colors', []):
                col['img'] = col['img']
            if p.get('img'):
                p['img'] = p['img']
        (folder / 'index.html').write_text(page(c), encoding='utf-8')
        out.append(slug)
    return out
