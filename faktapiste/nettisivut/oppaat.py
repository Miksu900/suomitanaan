"""Netvo Oppaat -kauppa netvo.fi:ssä: /oppaat/, /oppaat/kiitos/ ja /toimitusehdot/. Maksut Visma Payn kautta (worker: src/kauppa.js)."""
import html, pathlib

esc = html.escape
OPPAAT = [
    ("01", "Nettisivut", "Tee yrityksellesi toimivat nettisivut tekoälyn avulla – ilman koodaamista.", 19),
    ("02", "Verkkokauppa", "Perusta oma verkkokauppa: tuotteet, maksutavat, toimitukset ja ehdot kuntoon.", 19),
    ("03", "Puhelinsovellus", "Rakenna oma puhelinsovellus tekoälyn kanssa ja julkaise se.", 24),
    ("04", "Domain ja sähköposti", "Oma verkko-osoite ja yrityksen sähköposti käyttöön vaihe vaiheelta.", 19),
    ("05", "Digituotteiden myynti", "Myy oppaita, pohjia ja muita digituotteita verkossa.", 19),
    ("06", "Itsestään päivittyvä sivusto", "Sivusto, joka hakee ja päivittää tietonsa automaattisesti.", 19),
    ("07", "Tekoälyvideot", "Tee lyhyitä videoita tekoälyäänellä ja tekstityksillä someen.", 19),
    ("08", "Somemarkkinointi", "Saa näkyvyyttä TikTokissa, Facebookissa ja X:ssä ilman isoa budjettia.", 19),
]
YRITYS = "Taksiliikenne Koskela Oy (Y-tunnus 3425681-3), palvelun nimi Netvo"
OSOITE = "Riihikatu 3 B 20, 84100 Ylivieska"

TYYLI = """<style>
.tuotteet{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.tuote{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:22px;display:flex;flex-direction:column;gap:8px}
.tuote h3{font-size:1.3rem;margin:0}.tuote p{color:var(--mute);margin:0;flex:1;font-size:.96rem}.tuote .hinta{font-family:Fraunces,Georgia,serif;font-size:1.8rem}
.tuote.paketti{background:var(--ink);color:#fff;border:0}.tuote.paketti p{color:#c9ccd3}.tuote.paketti .nappi{background:#fff;color:var(--ink)}
.tuote .nappi{justify-content:center;cursor:pointer;font:inherit;font-weight:600}
dialog{border:0;border-radius:22px;padding:26px;max-width:440px;width:calc(100% - 32px)}dialog::backdrop{background:rgba(0,0,0,.5)}
dialog label{display:block;font-weight:600;margin:14px 0 6px}dialog input[type=email]{width:100%;font:inherit;padding:12px 14px;border:1px solid var(--line);border-radius:12px}
.ehto{display:flex;gap:10px;align-items:flex-start;font-weight:400!important;font-size:.92rem;color:var(--mute)}.ehto input{margin-top:4px}
.virhe{color:#b91c1c;font-size:.95rem;min-height:1.2em}
.maksutavat{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center;margin-top:12px}.maksutavat img{height:30px;width:auto;background:#fff;border-radius:6px;padding:3px;border:1px solid var(--line)}
.lataus{display:flex;justify-content:space-between;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 18px;margin:10px 0}
</style>"""

MAKSUTAVAT_JS = """<script>
fetch('/api/kauppa/maksutavat').then(function(r){return r.json()}).then(function(d){var m=document.getElementById('maksutavat');if(!m||!d.tavat||!d.tavat.length)return;m.textContent='';d.tavat.forEach(function(t){if(!t.kuva)return;var i=document.createElement('img');i.src=t.kuva;i.alt=t.nimi;i.title=t.nimi;i.loading='lazy';m.appendChild(i)})}).catch(function(){});
</script>"""


def oppaat_sivu(_sivu):
    kortit = "".join(f"""<div class="tuote"><span class="eb" style="margin:0">Opas {i}</span><h3>{esc(n)}</h3><p>{esc(k)}</p>
<div class="hinta">{h} €</div><button class="nappi osta" data-t="{i}" data-n="{esc(n)}" data-h="{h}">Osta {h} €</button></div>""" for i, n, k, h in OPPAAT)
    kortit += """<div class="tuote paketti"><span class="eb" style="margin:0;color:var(--kulta)">Paras hinta</span><h3>Kaikki 8 opasta</h3>
<p>Koko sarja yhdellä kertaa – säästät yli 100 €.</p><div class="hinta">49 €</div><button class="nappi osta" data-t="kaikki" data-n="Kaikki 8 opasta" data-h="49">Osta 49 €</button></div>"""
    runko = f"""{TYYLI}<section class="osio"><div class="w">
<div class="ots"><span class="eb">Netvo Oppaat</span><h1 style="font-size:clamp(2.2rem,5vw,3.4rem)">Selkeät oppaat ilman koodaamista</h1>
<p>Suomenkieliset PDF-oppaat yrittäjälle, joka haluaa tehdä itse. Oppaat perustuvat omaan kokemukseeni nettisivujen, kauppojen ja sovellusten rakentamisesta tekoälyn kanssa. Saat oppaan heti maksun jälkeen ladattavaksi ja sähköpostiisi.</p>
<p id="peruttu" class="virhe" hidden>Maksu peruttiin tai se ei onnistunut. Voit yrittää uudelleen.</p></div>
<div class="tuotteet">{kortit}</div>
<div style="text-align:center;margin-top:40px"><p style="color:var(--mute);margin:0">Turvallinen maksu Visma Payn kautta: verkkopankit, MobilePay ja maksukortit. Hinnat sisältävät alv 25,5 %.</p>
<div class="maksutavat" id="maksutavat" aria-label="Hyväksytyt maksutavat"></div>
<p style="margin-top:14px"><a href="/toimitusehdot/">Toimitus- ja maksuehdot</a> · <a href="/tietosuoja/">Tietosuoja</a></p></div>
</div></section>
<dialog id="ostoikkuna"><form method="dialog" id="ostolomake">
<h2 style="font-size:1.6rem" id="o-nimi">Opas</h2><p style="margin:0;color:var(--mute)">Hinta <b id="o-hinta"></b> (sis. alv 25,5 %)</p>
<label for="o-email">Sähköpostiosoite</label><input type="email" id="o-email" required autocomplete="email" placeholder="nimi@esimerkki.fi">
<p style="font-size:.88rem;color:var(--mute);margin:6px 0 0">Lähetämme latauslinkin ja kuitin tähän osoitteeseen.</p>
<label class="ehto"><input type="checkbox" id="o-ehto" required> <span>Hyväksyn <a href="/toimitusehdot/" target="_blank">toimitusehdot</a> ja pyydän oppaan toimittamista heti. Ymmärrän, että menetän peruuttamisoikeuteni, kun lataus on avattu.</span></label>
<p class="virhe" id="o-virhe"></p>
<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:10px"><button type="button" class="nappi toissij" id="o-peru">Peruuta</button><button type="submit" class="nappi sin" id="o-maksa">Siirry maksamaan</button></div>
</form></dialog>
<script>(function(){{
var d=document.getElementById('ostoikkuna'),f=document.getElementById('ostolomake'),tuote='';
if(location.search.indexOf('maksu=peruttu')>-1)document.getElementById('peruttu').hidden=false;
document.querySelectorAll('.osta').forEach(function(b){{b.onclick=function(){{tuote=b.dataset.t;document.getElementById('o-nimi').textContent=b.dataset.n;document.getElementById('o-hinta').textContent=b.dataset.h+' €';document.getElementById('o-virhe').textContent='';d.showModal()}}}});
document.getElementById('o-peru').onclick=function(){{d.close()}};
f.onsubmit=function(e){{e.preventDefault();var v=document.getElementById('o-virhe'),m=document.getElementById('o-maksa');v.textContent='';m.disabled=true;m.textContent='Avataan maksua…';
fetch('/api/kauppa/osto',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify({{tuote:tuote,email:document.getElementById('o-email').value,hyvaksy:document.getElementById('o-ehto').checked}})}})
.then(function(r){{return r.json()}}).then(function(x){{if(x.url){{location.href=x.url}}else{{v.textContent=x.virhe||'Jokin meni vikaan.';m.disabled=false;m.textContent='Siirry maksamaan'}}}})
.catch(function(){{v.textContent='Yhteysvirhe. Yritä uudelleen.';m.disabled=false;m.textContent='Siirry maksamaan'}})}};
}})();</script>{MAKSUTAVAT_JS}"""
    return _sivu("Netvo Oppaat – selkeät PDF-oppaat yrittäjälle", "Suomenkieliset PDF-oppaat nettisivuista, verkkokaupasta, sovelluksista, somesta ja tekoälystä. Toimitus heti maksun jälkeen.", runko, "/oppaat/")


def kiitos_sivu(_sivu):
    runko = f"""{TYYLI}<section class="osio"><div class="w teksti">
<h1>Kiitos tilauksesta!</h1><p id="tila" style="color:var(--mute)">Haetaan tilauksen tietoja…</p><div id="lista"></div>
<p style="color:var(--mute);margin-top:24px">Lähetimme latauslinkin myös sähköpostiisi. Linkki on voimassa 60 päivää. Apua saat osoitteesta info@netvo.fi.</p>
<p class="keskita"><a class="nappi toissij" href="/oppaat/">← Takaisin oppaisiin</a></p></div></section>
<script>(function(){{var t=new URLSearchParams(location.search).get('t')||'',s=document.getElementById('tila'),l=document.getElementById('lista'),k=0;
function hae(){{fetch('/api/kauppa/tilaus?t='+encodeURIComponent(t)).then(function(r){{return r.json()}}).then(function(d){{
if(d.tiedostot){{s.textContent='Tilaus '+d.nro+': '+d.tuote;l.textContent='';d.tiedostot.forEach(function(f){{var r=document.createElement('div');r.className='lataus';var n=document.createElement('span');n.textContent=f.nimi;var a=document.createElement('a');a.className='nappi sin';a.href=f.url;a.textContent='Lataa PDF';r.append(n,a);l.append(r)}})}}
else if(d.tila==='odottaa'&&k++<20){{s.textContent='Odotetaan maksun vahvistusta…';setTimeout(hae,3000)}}else{{s.textContent=d.virhe||'Tilausta ei löytynyt.'}}}}).catch(function(){{s.textContent='Yhteysvirhe. Päivitä sivu.'}})}}hae()}})();</script>"""
    return _sivu("Kiitos tilauksesta – Netvo Oppaat", "Lataa tilaamasi Netvo-oppaat.", runko, "/oppaat/kiitos/")


def toimitusehdot_sivu(_sivu):
    runko = f"""{TYYLI}<section class="osio"><div class="w teksti">
<h1>Toimitus- ja maksuehdot</h1>
<p style="color:var(--mute)">Ehdot koskevat Netvon verkkokaupassa (netvo.fi/oppaat) myytäviä digitaalisia tuotteita. Voimassa 5.11.2026 alkaen.</p>
<h2>Myyjä</h2>
<p>{esc(YRITYS)}<br>{esc(OSOITE)}<br>Sähköposti: info@netvo.fi<br>Puhelin: 044 777 7149</p>
<h2>Tuotteet ja hinnat</h2>
<p>Myymme suomenkielisiä PDF-oppaita. Hinnat ovat euroina ja sisältävät arvonlisäveron 25,5 %. Toimituskuluja ei ole. Tilaus on sitova, kun maksu on hyväksytty.</p>
<h2>Toimitus</h2>
<p>Tuotteet toimitetaan sähköisesti heti maksun vahvistuttua: lataussivu avautuu maksun jälkeen, ja lähetämme latauslinkin sekä tilausvahvistuksen antamaasi sähköpostiosoitteeseen. Latauslinkki on voimassa 60 päivää. Jos et saa linkkiä, ota yhteyttä info@netvo.fi, niin toimitamme oppaan sähköpostilla.</p>
<h2>Peruuttamisoikeus</h2>
<p>Kuluttajansuojalain mukaan kuluttajalla ei ole peruuttamisoikeutta digitaaliseen sisältöön, jota ei toimiteta aineellisella tallenteella, kun toimittaminen on aloitettu kuluttajan nimenomaisella suostumuksella ja kuluttaja on hyväksynyt menettävänsä peruuttamisoikeutensa. Tilauksen yhteydessä pyydät oppaan toimittamista heti ja hyväksyt tämän. Jos tiedosto on viallinen tai ei avaudu, toimitamme uuden tai palautamme rahat.</p>
<h2>Maksupalveluntarjoaja</h2>
<p>Maksunvälityspalvelun toteuttajana ja maksupalveluntarjoajana toimii Visma Payments Oy (Y-tunnus 2486559-4), joka on rekisteröity Finanssivalvonnan ylläpitämään maksulaitosrekisteriin. Maksamiseen siirrytään Visma Pay -verkkopalvelun kautta, ja tiliotteella sekä laskulla maksun saajana näkyy Visma Pay tai Visma Payments Oy. Visma Payments Oy välittää maksut verkkokaupalle. Maksaminen on turvallista, sillä kaikki maksutapahtumaa koskevat tiedot välitetään salattua yhteyttä käyttäen niin, ettei kukaan ulkopuolinen taho näe maksutapahtuman tietoja.</p>
<p>Kauppa on Taksiliikenne Koskela Oy:n (palvelun nimi Netvo). Visma Payments Oy:n yhteystiedot: Laserkatu 6, 53850 Lappeenranta, helpdesk@vismapay.com.</p>
<h2>Maksutavat</h2>
<p>Visma Pay -palvelun kautta voit maksaa verkkopankkitunnuksilla, mobiilimaksulla (esim. MobilePay) ja maksukorteilla (Visa, Visa Electron, Mastercard). Käytettävissä olevat maksutavat näet maksusivulla. Maksutapahtuma näkyy pankin tiliotteella kauppiaan nimellä Netvo.</p>
<div class="maksutavat" id="maksutavat" aria-label="Hyväksytyt maksutavat"></div>
<h2>Reklamaatiot ja riidat</h2>
<p>Ota yhteyttä info@netvo.fi, jos tuotteessa on vikaa. Pyrimme ratkaisemaan asiat ensin keskenämme. Kuluttaja voi viedä riita-asian myös kuluttajariitalautakunnan käsiteltäväksi (kuluttajariita.fi); ennen sitä kannattaa olla yhteydessä kuluttajaneuvontaan (kkv.fi).</p>
<h2>Tietosuoja</h2>
<p>Tilauksen yhteydessä käsittelemme sähköpostiosoitteesi ja tilauksen tiedot tuotteen toimittamiseksi ja kirjanpitoa varten. Lue lisää <a href="/tietosuoja/">tietosuojaselosteesta</a>.</p>
<p class="keskita"><a class="nappi" href="/oppaat/">Oppaisiin →</a></p>
</div></section>{MAKSUTAVAT_JS}"""
    return _sivu("Toimitus- ja maksuehdot – Netvo", "Netvon verkkokaupan toimitus- ja maksuehdot: digitaaliset oppaat, Visma Pay -maksut, peruuttamisoikeus.", runko, "/toimitusehdot/")


def rakenna(root, _sivu):
    root = pathlib.Path(root) / "netvo"
    for polku, sivu in [("oppaat", oppaat_sivu), ("oppaat/kiitos", kiitos_sivu), ("toimitusehdot", toimitusehdot_sivu)]:
        (root / polku).mkdir(parents=True, exist_ok=True)
        (root / polku / "index.html").write_text(sivu(_sivu), encoding="utf-8")
