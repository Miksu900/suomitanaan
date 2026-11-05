"""Netvo Kotivara: /kotivara/ – Kevyt-paketti (toimittaja Turvakauppa, suoratoimitus asiakkaalle).
Tilaukset ovat kiinni, kunnes Visma Pay on hyväksynyt kaupan ja jälleenmyyntihinnat on sovittu (AVOINNA = False)."""
import html, pathlib

esc = html.escape
AVOINNA = False
HINTA = 89
SISALTO = [
    ("SPR:n ensiapulaukku yleiskäyttöön", "Punaisen Ristin kattava ensiapulaukku kotiin, mökille tai autoon."),
    ("Punaisen Ristin hätäensiapuopas", "Selkeät ohjeet yleisimpiin ensiaputilanteisiin."),
    ("Lämpöpeite", "Pitää lämmön, kun sähköt ovat poikki tai sattuu onnettomuus."),
    ("Käsivalaisin ja 4 AA-paristoa", "Valo sähkökatkon varalle, paristot valmiina mukana."),
    ("Suojakäsineet", "Kestävät neopreenikäsineet siivoukseen ja raivaukseen."),
]


def kotivara_sivu(_sivu):
    rivit = "".join(f'<li><b>{esc(n)}</b><br><span style="color:var(--mute)">{esc(k)}</span></li>' for n, k in SISALTO)
    nappi = (f'<a class="nappi" href="/oppaat/">Tilaa {HINTA} €</a>' if AVOINNA else
             '<button class="nappi" disabled style="opacity:.6;cursor:default">Tilaukset avautuvat pian</button>'
             '<p style="color:var(--mute);font-size:.95rem;margin:10px 0 0">Haluatko tiedon, kun tilaukset avautuvat? Laita viesti: <a href="mailto:info@netvo.fi?subject=Kotivara%20Kevyt">info@netvo.fi</a></p>')
    runko = f"""<section class="osio"><div class="w teksti">
<span class="eb">Netvo Kotivara</span>
<h1 style="font-size:clamp(2.2rem,5vw,3.2rem)">Kevyt-paketti: ensiapu ja valo kotiin</h1>
<p>Valmis paketti häiriötilanteisiin: ensiapu, lämpö ja valo samassa toimituksessa. Kaikki tuotteet tulevat suomalaiselta varautumistuotteiden toimittajalta yhtenä pakettina suoraan kotiisi.</p>
<div style="background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px;margin:24px 0">
<div style="font-family:Fraunces,Georgia,serif;font-size:2.4rem">{HINTA} €</div>
<p style="color:var(--mute);margin:0 0 16px">Sisältää toimituksen ja arvonlisäveron. Toimitusaika 5–7 arkipäivää.</p>{nappi}</div>
<h2>Paketin sisältö</h2><ul style="display:grid;gap:12px;padding-left:1.2em">{rivit}</ul>
<h2>Miksi varautua?</h2>
<p>Viranomaiset suosittelevat, että jokainen kotitalous pärjää omillaan vähintään 72 tuntia esimerkiksi pitkän sähkökatkon tai myrskyn aikana. Ensiapuvälineet ja valo ovat varautumisen perusta. Lisää ohjeita löydät osoitteesta <a href="https://72tuntia.fi" target="_blank" rel="noopener">72tuntia.fi</a>.</p>
<h2>Toimitus ja palautus</h2>
<p>Paketti lähtee postitse 5–7 arkipäivän kuluessa tilauksesta. Kuluttajana sinulla on 14 päivän peruuttamisoikeus tuotteen vastaanottamisesta. Kysyttävää? <a href="mailto:info@netvo.fi">info@netvo.fi</a></p>
<p style="color:var(--mute);font-size:.9rem;margin-top:28px">Myyjä: Taksiliikenne Koskela Oy (Y-tunnus 3425681-3), palvelun nimi Netvo · <a href="/toimitusehdot/">Toimitus- ja maksuehdot</a> · <a href="/tietosuoja/">Tietosuoja</a></p>
</div></section>"""
    return _sivu("Kotivara Kevyt – ensiapu ja valo kotiin | Netvo", "Valmis kotivarapaketti: SPR:n ensiapulaukku, hätäensiapuopas, lämpöpeite, valaisin ja paristot. 89 € toimituksineen.", runko, "/kotivara/")


def rakenna(root, _sivu):
    p = pathlib.Path(root) / "netvo" / "kotivara"
    p.mkdir(parents=True, exist_ok=True)
    (p / "index.html").write_text(kotivara_sivu(_sivu), encoding="utf-8")
