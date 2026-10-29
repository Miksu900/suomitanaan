"""Netvo – myynti- ja ehtosivu sekä mallisivujen galleria. Oma brändi, erillään Faktapisteesta.

Malli (29.10.2026): rakentaminen 0 € (jopa 1500 € arvosta), vain kuukausimaksu, ei sitoutumista, domain lunastettavissa 99 €.
"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from tietosuoja import seloste
from .malli import sivu as mallisivu
from .palvelusivu import sivu as palvelusivu, KUVAT, U as UK, SS as SSK
from .data import DEMOT

esc = html.escape
YHTEYS = "info@netvo.fi"
SEURANTA = "<script async src=\"https://www.googletagmanager.com/gtag/js?id=AW-18515756006\"></script>\n<script>(function(){window.dataLayer=window.dataLayer||[];window.gtag=window.gtag||function(){dataLayer.push(arguments)};\nvar K='nv_suostumus',c=null;try{c=localStorage.getItem(K)}catch(e){}var g=c==='ok'?'granted':'denied';\ngtag('consent','default',{ad_storage:g,ad_user_data:g,ad_personalization:g,analytics_storage:'denied',wait_for_update:500});\ngtag('js',new Date());gtag('config','AW-18515756006');\nvar L={soitto:'AW-18515756006/aUOJCILR-q0dEOaHgP1E',viesti:'AW-18515756006/7tTECIXR-q0dEOaHgP1E',rekisteroityminen:'AW-18515756006/o5SECIjR-q0dEOaHgP1E'},tehty={};\nwindow.nvKonversio=function(k){if(!L[k]||tehty[k])return;tehty[k]=1;gtag('event','conversion',{send_to:L[k]})};\ndocument.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href');if(/^tel:/.test(h))nvKonversio('soitto');else if(/^mailto:/.test(h))nvKonversio('viesti')},true);\n\nif(c)return;function nayta(){var d=document.createElement('div');d.id='nv-ev';d.setAttribute('role','dialog');d.setAttribute('aria-label','Evästeet');\nd.innerHTML='<p>Käytämme evästeitä mainonnan tehon mittaamiseen. Voit hyväksyä ne tai jatkaa ilman. <a href=\"https://netvo.fi/tietosuoja/\" style=\"color:#9fe3b5\">Lue lisää</a></p><div><button type=\"button\" data-v=\"ei\">Vain välttämättömät</button><button type=\"button\" data-v=\"ok\" class=\"ok\">Hyväksy</button></div>';\nvar s=document.createElement('style');s.textContent='#nv-ev{position:fixed;left:12px;right:12px;bottom:88px;z-index:2147483647;max-width:560px;margin:0 auto;background:#18211c;color:#fff;border-radius:18px;padding:16px 18px;box-shadow:0 20px 50px -15px rgba(0,0,0,.5);font:15px/1.45 Inter,system-ui,sans-serif;display:flex;gap:14px;align-items:center;flex-wrap:wrap}#nv-ev p{margin:0;flex:1 1 240px}#nv-ev div{display:flex;gap:8px}#nv-ev button{border:1.5px solid rgba(255,255,255,.5);background:transparent;color:#fff;border-radius:999px;padding:9px 14px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}#nv-ev button.ok{background:#fff;color:#18211c;border-color:#fff}';\ndocument.head.appendChild(s);document.body.appendChild(d);\nd.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var v=b.dataset.v;try{localStorage.setItem(K,v)}catch(x){}if(v==='ok')gtag('consent','update',{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted'});d.remove()})}\nif(document.body)nayta();else document.addEventListener('DOMContentLoaded',nayta)})();</script>\n"
PUHELIN = "044 777 7149"
PUHELIN_TEL = "+358447777149"

HINTA_KK = 99        # nettisivut €/kk (sis. alv)
KAUPPA_KK = 149      # verkkokauppa €/kk (sis. alv)
LUNASTUS = 99        # verkkotunnuksen lunastus €


KAUPPAKUVAT = {"kauppa-leipomo": "photo-1548228623-13e55dd16984", "kauppa-kasityo": "photo-1742386676097-a2a55fcdcc64"}
HERO = "photo-1783949247747-210d1403da8a"


def _demokortti(d):
    kauppa = d.get("tyyppi") == "kauppa"
    kuva = KAUPPAKUVAT.get(d["slug"]) or KUVAT.get(d["slug"], ("",))[0]
    merkki = "Räätälöity verkkokauppa" if kauppa else d["ala"]
    return f"""<a class="malli" href="/mallit/{d['slug']}/" target="_blank" rel="noopener">
<span class="mk"><img src="{UK(kuva, 700, 520)}" srcset="{SSK(kuva, (400, 700, 1000), .74)}" sizes="(max-width:700px) 90vw, 33vw" alt="" loading="lazy"><em>{esc(merkki)}</em></span>
<span class="mt"><b>{esc(d['nimi'])}</b><span>{esc(d.get('slogan',''))}</span><i>Avaa malli →</i></span></a>"""


def _sivu(otsikko, kuvaus, runko):
    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(otsikko)}</title><meta name="description" content="{esc(kuvaus)}">
<meta property="og:title" content="{esc(otsikko)}"><meta property="og:description" content="{esc(kuvaus)}"><meta property="og:image" content="{UK(HERO, 1200, 630)}">
<meta name="theme-color" content="#14213d">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--p:#1d4ed8;--p2:#1e3a8a;--ink:#16181d;--mute:#5f6168;--line:#e7e2d9;--bg:#faf7f2;--card:#fff;--soft:#f1ece3;--vihrea:#15803d;--kulta:#d8a23c}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;font:16.5px/1.65 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased}}
img{{display:block;max-width:100%}}a{{color:var(--p)}}
h1,h2,h3{{font-family:Fraunces,Georgia,serif;font-weight:500;line-height:1.1;letter-spacing:-.018em;margin:0 0 .45em}}
.w{{max-width:1160px;margin:0 auto;padding:0 22px}}
header.top{{position:sticky;top:0;z-index:20;background:rgba(250,247,242,.88);backdrop-filter:saturate(1.4) blur(12px);-webkit-backdrop-filter:saturate(1.4) blur(12px);border-bottom:1px solid rgba(0,0,0,.06)}}
.top .w{{display:flex;align-items:center;justify-content:space-between;height:70px}}
.logo{{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1.6rem;color:var(--ink);text-decoration:none;letter-spacing:-.02em}}.logo span{{color:var(--vihrea)}}
.ylaoik{{display:flex;align-items:center;gap:14px}}.puh{{background:var(--ink);color:#fff;text-decoration:none;white-space:nowrap;font-weight:600;padding:10px 18px;border-radius:999px}}
.nappi{{display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:#fff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:999px;border:0;transition:transform .15s,background .15s}}
.nappi:hover{{transform:translateY(-1px);background:#000}}.nappi.iso{{padding:16px 28px;font-size:1.05rem}}
.nappi.sin{{background:var(--p)}}.nappi.sin:hover{{background:var(--p2)}}
.nappi.toissij{{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1.5px rgba(0,0,0,.25)}}
@media(max-width:620px){{.ylaoik .nappi{{display:none}}.puh{{background:var(--ink);color:#fff;padding:9px 14px;border-radius:999px;font-size:.92rem}}}}
.hero{{position:relative;overflow:hidden;padding:90px 0 96px;color:#fff;background:#1d1a16}}.hero .tausta{{position:absolute;inset:0;z-index:0}}.hero .tausta img{{width:100%;height:100%;object-fit:cover;animation:kb 22s ease-out both}}@keyframes kb{{from{{transform:scale(1.12)}}to{{transform:scale(1)}}}}.hero .tausta::after{{content:'';position:absolute;inset:0;background:linear-gradient(100deg,rgba(18,15,12,.86) 0%,rgba(18,15,12,.62) 48%,rgba(18,15,12,.2) 100%),linear-gradient(0deg,rgba(18,15,12,.55),transparent 40%)}}@media(max-width:900px){{.hero{{padding:64px 0 70px;min-height:86svh;display:flex;align-items:flex-end}}.hero .tausta::after{{background:linear-gradient(0deg,rgba(18,15,12,.92) 0%,rgba(18,15,12,.7) 55%,rgba(18,15,12,.35) 100%)}}.kollaasi{{display:none}}}}@media(prefers-reduced-motion:reduce){{.hero .tausta img{{animation:none}}}}.hero .w{{position:relative;z-index:1}}
.hero .w{{max-width:1180px}}.hero .w>div{{max-width:640px}}
@media(max-width:900px){{.hero .w{{grid-template-columns:1fr;gap:34px}}}}
.kick{{display:inline-flex;gap:8px;align-items:center;font-size:.85rem;font-weight:600;background:#fff;color:var(--ink);border:1px solid var(--line);padding:6px 12px;border-radius:999px}}.hero .kick{{background:rgba(255,255,255,.14);color:#fff;border-color:rgba(255,255,255,.28);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}}
.kick i{{width:8px;height:8px;border-radius:50%;background:var(--vihrea);display:inline-block}}
.hero h1{{font-size:clamp(2.6rem,6.4vw,4.6rem);margin:18px 0 18px}}.hero h1 em{{font-style:italic;color:#9fe3b5}}.hero h1{{color:#fff;text-shadow:0 2px 24px rgba(0,0,0,.25)}}
.hero p.l{{font-size:1.2rem;color:rgba(255,255,255,.88);max-width:44ch;margin:0 0 28px}}.hero .nappi.toissij{{color:#fff;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.6)}}.hero .luvut span{{color:rgba(255,255,255,.75)}}
.toim{{display:flex;gap:12px;flex-wrap:wrap}}
.luvut{{display:flex;gap:30px;margin-top:30px;flex-wrap:wrap}}.luvut b{{display:block;font-family:Fraunces,Georgia,serif;font-size:2rem;font-weight:500;line-height:1}}.luvut span{{color:var(--mute);font-size:.88rem}}
.kollaasi{{position:relative;height:540px}}
@media(max-width:900px){{.kollaasi{{height:430px}}}}
.kollaasi .kuva{{display:none;position:absolute;inset:0 60px 40px 0;border-radius:28px;overflow:hidden;box-shadow:0 40px 80px -40px rgba(0,0,0,.45)}}
.kollaasi .kuva img{{width:100%;height:100%;object-fit:cover}}
.puhelin{{position:absolute;right:0;bottom:0;width:200px;aspect-ratio:9/18.5;border-radius:34px;background:#111;padding:8px;box-shadow:0 30px 60px -20px rgba(0,0,0,.5)}}
.puhelin .ruutu{{width:100%;height:100%;border-radius:27px;overflow:hidden;position:relative;background:#000}}
.puhelin img{{width:100%;height:100%;object-fit:cover;opacity:.88}}
.puhelin .yp{{position:absolute;left:0;right:0;top:0;padding:30px 14px 0;color:#fff}}.puhelin .yp b{{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.25rem;line-height:1.1;display:block;margin-top:120px}}
.puhelin .yp small{{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;opacity:.85}}
.puhelin .np{{position:absolute;left:14px;right:14px;bottom:16px;background:#fff;color:#111;text-align:center;font-size:.72rem;font-weight:700;padding:9px;border-radius:999px}}
.merkki{{position:absolute;left:-12px;bottom:70px;background:#fff;border-radius:16px;padding:12px 16px;box-shadow:0 20px 40px -20px rgba(0,0,0,.35);font-size:.9rem;font-weight:600}}.merkki b{{color:var(--vihrea)}}
.osio{{padding:88px 0}}.osio.alt{{background:var(--soft)}}
.eb{{display:block;font-size:.76rem;letter-spacing:.24em;text-transform:uppercase;color:var(--p);font-weight:700;margin-bottom:10px}}
.osio h2{{font-size:clamp(2rem,4.4vw,3.1rem)}}.ots{{max-width:640px;margin-bottom:34px}}.ots p{{color:var(--mute);font-size:1.08rem}}
.keski{{text-align:center;margin-left:auto;margin-right:auto}}
.galleria{{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}}
.malli{{text-decoration:none;color:inherit;background:var(--card);border-radius:22px;overflow:hidden;display:block;box-shadow:0 1px 0 rgba(0,0,0,.04),0 24px 44px -32px rgba(0,0,0,.35);transition:transform .2s,box-shadow .2s}}
.malli:hover{{transform:translateY(-4px);box-shadow:0 30px 60px -30px rgba(0,0,0,.45)}}
.mk{{position:relative;display:block;aspect-ratio:4/3;overflow:hidden}}.mk img{{width:100%;height:100%;object-fit:cover;transition:transform .6s}}.malli:hover .mk img{{transform:scale(1.05)}}
.mk em{{position:absolute;left:12px;top:12px;font-style:normal;font-size:.75rem;font-weight:600;background:rgba(255,255,255,.92);padding:5px 10px;border-radius:999px}}
.mt{{display:block;padding:18px 20px 20px}}.mt b{{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.35rem;display:block}}.mt span{{color:var(--mute);font-size:.94rem;display:block}}.mt i{{font-style:normal;color:var(--p);font-weight:600;font-size:.92rem;display:block;margin-top:10px}}
.askeleet{{display:grid;gap:22px;grid-template-columns:repeat(3,1fr)}}@media(max-width:820px){{.askeleet{{grid-template-columns:1fr}}}}
.askel{{background:var(--card);border-radius:22px;padding:30px}}.askel .num{{font-family:Fraunces,Georgia,serif;font-size:3rem;color:var(--p);line-height:1;margin-bottom:12px}}.askel p{{color:var(--mute);margin:0}}
.hinnat{{display:grid;gap:22px;grid-template-columns:repeat(2,1fr);align-items:stretch;max-width:880px;margin:0 auto}}@media(max-width:900px){{.hinnat{{grid-template-columns:1fr}}}}
.hk{{background:var(--card);border-radius:24px;padding:32px;display:flex;flex-direction:column;border:1px solid var(--line)}}
.hk.paras{{background:var(--ink);color:#fff;border:0;box-shadow:0 40px 70px -40px rgba(0,0,0,.6)}}.hk.paras .m{{color:#b9bcc4}}.hk.paras li::before{{color:#4ade80}}
.hk .tag{{align-self:flex-start;font-size:.75rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:var(--soft);color:var(--ink);padding:5px 10px;border-radius:999px;margin-bottom:14px}}
.hk.paras .tag{{background:var(--kulta);color:#1b1305}}
.hk h3{{font-size:1.5rem;margin-bottom:6px}}.hk .m{{color:var(--mute);margin:0 0 16px;font-size:.96rem}}
.hk .h{{font-family:Fraunces,Georgia,serif;font-size:2.8rem;line-height:1}}.hk .h small{{font-family:Inter,sans-serif;font-size:1rem;opacity:.7}}
.hk ul{{list-style:none;padding:0;margin:20px 0 26px;display:grid;gap:9px;font-size:.96rem;flex:1}}.hk li{{padding-left:26px;position:relative}}.hk li::before{{content:"✓";position:absolute;left:0;color:var(--vihrea);font-weight:800}}
.hk .nappi{{justify-content:center}}.hk.paras .nappi{{background:#fff;color:var(--ink)}}
.raat{{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}}@media(max-width:900px){{.raat{{grid-template-columns:1fr;gap:30px}}}}
.raat .kuva{{border-radius:28px;overflow:hidden;aspect-ratio:4/5;box-shadow:0 40px 80px -40px rgba(0,0,0,.45)}}.raat .kuva img{{width:100%;height:100%;object-fit:cover}}
.ominais{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:24px 0 28px}}@media(max-width:560px){{.ominais{{grid-template-columns:1fr}}}}
.ominais div{{background:var(--card);border-radius:16px;padding:16px 18px;font-size:.95rem;color:var(--mute)}}.ominais b{{display:block;color:var(--ink);font-size:1rem;margin-bottom:2px}}
.reilu{{background:var(--ink);color:#fff}}.reilu h2{{color:#fff}}.reilu .eb{{color:var(--kulta)}}
.reilu .ruudut{{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-top:10px}}
.reilu .r{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:26px}}.reilu .r h3{{color:#fff;font-size:1.25rem}}.reilu .r p{{color:#c9ccd3;margin:0}}
.tekija{{display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center;background:var(--card);border-radius:26px;padding:34px;max-width:860px;margin:0 auto}}
.tekija .av{{width:96px;height:96px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--vihrea));color:#fff;display:grid;place-items:center;font-family:Fraunces,Georgia,serif;font-size:2.4rem}}
@media(max-width:620px){{.tekija{{grid-template-columns:1fr;text-align:center}}.tekija .av{{margin:0 auto}}}}
.tekija p{{margin:0 0 10px;color:var(--mute);font-size:1.05rem}}.tekija p.q{{font-family:Fraunces,Georgia,serif;color:var(--ink);font-size:1.4rem;line-height:1.35}}
.ukk{{max-width:760px;margin:0 auto}}.ukk details{{border-bottom:1px solid var(--line);padding:6px 0}}
.ukk summary{{cursor:pointer;font-weight:600;padding:16px 0;list-style:none;font-size:1.08rem;display:flex;justify-content:space-between;gap:16px}}
.ukk summary::-webkit-details-marker{{display:none}}.ukk summary::after{{content:"+";color:var(--p);font-size:1.4rem;line-height:1}}.ukk details[open] summary::after{{content:"–"}}
.ukk p{{color:var(--mute);margin:0 0 16px}}
.cta{{background:linear-gradient(135deg,#1e3a8a,#1d4ed8);color:#fff;border-radius:30px;padding:56px 34px;text-align:center}}
.cta h2{{color:#fff}}.cta p{{color:#dbe4ff;max-width:46ch;margin:0 auto 24px;font-size:1.1rem}}.cta .nappi{{background:#fff;color:var(--ink)}}.cta .nappi.toissij{{background:transparent;color:#fff;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.6)}}
.teksti{{max-width:720px;margin:0 auto}}.teksti h2{{text-align:left;margin-top:1.4em;font-size:1.6rem}}
footer.jalka{{background:#0f1014;color:#9a9ca3;text-align:center;padding:40px 16px 100px;font-size:.9rem}}footer.jalka a{{color:#e5e7eb}}
.keskita{{text-align:center;margin-top:28px}}
.ilm{{opacity:0;transform:translateY(16px);transition:opacity .7s,transform .7s}}.ilm.nak{{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){{.ilm{{opacity:1;transform:none}}}}
</style></head>
<body>
<header class="top"><div class="w">
<a class="logo" href="/">Net<span>vo</span></a>
<span class="ylaoik"><a class="puh" href="tel:{PUHELIN_TEL}" aria-label="Soita {PUHELIN}">📞 {PUHELIN}</a></span>
</div></header>
{runko}
<footer class="jalka"><p style="font-family:Fraunces,Georgia,serif;font-size:1.5rem;color:#fff;margin:0 0 8px">Net<span style="color:#4ade80">vo</span></p>
<p>Nettisivut ja verkkokaupat suomalaisille pienyrityksille.</p>
<p style="font-size:1.05rem;color:#fff">{esc(YHTEYS)}</p>
<p><a href="/ehdot/">Sopimusehdot</a> · <a href="/tietosuoja/">Tietosuoja</a> · Kuvat: Unsplash · Netvo on osa Faktapisteen palveluita.</p></footer>
<script>(function(){{var o=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add('nak');o.unobserve(e.target)}}}})}},{{threshold:.1}});document.querySelectorAll('.ilm').forEach(function(x){{o.observe(x)}});setTimeout(function(){{document.querySelectorAll('.ilm').forEach(function(x){{x.classList.add('nak')}})}},2500)}})();</script>
<script src="https://kauppa.netvo.fi/tuki.js" defer></script>{SEURANTA}
</body></html>"""


def etusivu():
    palvelut = [d for d in DEMOT if d.get("tyyppi") != "kauppa"]
    kaupat = [d for d in DEMOT if d.get("tyyppi") == "kauppa"]
    leip = KAUPPAKUVAT["kauppa-leipomo"]
    runko = f"""
<section class="hero"><div class="tausta"><img src="{UK(HERO, 1600)}" srcset="{SSK(HERO, (700, 1100, 1600, 2200))}" sizes="100vw" alt="Tunnelmallinen kahvila" fetchpriority="high"></div><div class="w">
<div><span class="kick"><i></i>Ei aloitusmaksua · ei sitoutumista</span>
<h1>Saat jopa <em>1500 €</em> edestä työtä ilmaiseksi.</h1>
<p class="l">Räätälöin yrityksesi nettisivut tai verkkokaupan alusta loppuun juuri sinun tarpeisiisi – maksutta. Ei valmispohjia. Maksat vain kuukausimaksun, ja voit lopettaa milloin tahansa.</p>
<div class="toim"><a class="nappi iso sin" href="#yhteys">Ota yhteyttä</a><a class="nappi iso toissij" href="#mallit">Katso esimerkkejä</a></div></div>
</div></section>

<section class="osio alt" id="mallit"><div class="w"><div class="ots ilm"><span class="eb">Esimerkkejä</span><h2>Jokainen sivu tehdään juuri sinulle</h2><p>Ei valmispohjia: suunnittelen jokaisen sivun ja kaupan yrityksesi tarpeiden mukaan. Avaa esimerkki ja katso, millaista laatua saat – omilla kuvillasi, teksteilläsi ja väreilläsi.</p></div>
<div class="galleria">{''.join(_demokortti(d) for d in palvelut + kaupat)}</div></div></section>

<section class="osio" id="ilmaiseksi"><div class="w"><div class="ots keski ilm" style="text-align:center"><span class="eb">Mitä saat ilmaiseksi</span><h2>Työ, josta muualla maksaisit 1000–1500 €</h2><p>Vastaavan sivuston teettäminen maksaa tyypillisesti yli 1000 €, verkkokauppa usein enemmän. Netvossa rakentaminen on aina 0 €. Ja koska muutoksista ei peritä erillistä hintaa, hyöty voi vuosien mittaan kasvaa jopa tuhansiin euroihin.</p></div>
<div class="ominais ilm" style="max-width:880px;margin:30px auto 0"><div><b>Räätälöity suunnittelu</b>Ei valmispohjia – ulkoasu ja toiminnot tehdään sinun tarpeisiisi.</div><div><b>Tekstit puolestasi</b>Sinun ei tarvitse kirjoittaa riviäkään.</div><div><b>Kuvat ja puhelinversio</b>Kauniit kuvat, toimii jokaisella laitteella.</div><div><b>Verkko-osoite ja julkaisu</b>Esim. yrityksesi.fi, valmiina nettiin.</div><div><b>Google-näkyvyyden perusta</b>Hakukoneystävälliset sivut alusta asti.</div><div><b>Verkkokauppaan tuotteet ja kassa</b>Lisään tuotteet ja kytken maksutavat.</div></div></div></section>

<section class="osio alt"><div class="w"><div class="ots keski ilm" style="text-align:center"><span class="eb">Näin se toimii</span><h2>Valmista kolmessa askeleessa</h2></div><div class="askeleet">
<div class="askel ilm"><div class="num">1</div><h3>Kerro yrityksestäsi</h3><p>Soitto tai viesti riittää: palvelut, yhteystiedot ja muutama kuva. Teksteistä ei tarvitse huolehtia.</p></div>
<div class="askel ilm"><div class="num">2</div><h3>Minä räätälöin sivut</h3><p>Suunnittelen ja rakennan sivut tai kaupan juuri sinun tarpeisiisi ja kirjoitan tekstit. Näet vedoksen ja saat muutokset mukaan.</p></div>
<div class="askel ilm"><div class="num">3</div><h3>Sivut julkaistaan</h3><p>Sivut tulevat nettiin omalla verkko-osoitteellasi. Pidän ne pystyssä ja ajan tasalla.</p></div>
</div></div></section>

<section class="osio" id="hinnat"><div class="w"><div class="ots keski ilm" style="text-align:center"><span class="eb">Hinnat</span><h2>Kaksi selkeää hintaa</h2><p>Rakentaminen 0 € ja kaikki muutokset hintaan sisältyen. Ei sitoutumista, ei lisämaksuja. Hinnat sisältävät alv:n.</p></div>
<div class="hinnat">
<div class="hk paras ilm"><span class="tag">Nettisivut</span><h3>Nettisivut</h3><p class="m">Rakentaminen 0 € – yli 1000 €:n arvosta.</p><div class="h">{HINTA_KK} €<small> / kk</small></div>
<ul><li>Räätälöity suunnittelu, ei valmispohjia</li><li>Tekstit kirjoitettuna puolestasi</li><li>Verkko-osoite, hosting ja tietoturva</li><li>Varmuuskopiot ja päivitykset</li><li>Kaikki muutokset hintaan sisältyen</li><li>Soitto- ja yhteydenottonapit</li><li>Lopeta milloin tahansa</li></ul><a class="nappi" href="#yhteys">Pyydä sivut</a></div>
<div class="hk ilm"><span class="tag">Verkkokauppa</span><h3>Verkkokauppa</h3><p class="m">Rakentaminen 0 € – jopa 1500 €:n arvosta.</p><div class="h">{KAUPPA_KK} €<small> / kk</small></div>
<ul><li>Räätälöity kauppa, ei valmispohjia</li><li>Tuotteet, ostoskori ja kassa</li><li>Suomalaiset maksutavat, rahat suoraan sinulle</li><li>Toimitustavat ja tilausten hallinta</li><li>Kaikki muutokset hintaan sisältyen</li><li>Tuki arkisin 9–21</li><li>Lopeta milloin tahansa</li></ul><a class="nappi toissij" href="#yhteys">Pyydä kauppa</a></div>
</div><p class="ilm" style="text-align:center;color:var(--mute);font-size:.9rem;margin-top:18px">Verkkokaupassa maksupalvelu (esim. Paytrail tai MobilePay) veloittaa omat kulunsa suoraan.</p></div></section>

<section class="osio alt" id="raataloity"><div class="w raat"><div class="kuva ilm"><img src="{UK(leip, 900, 1125)}" srcset="{SSK(leip, (500, 900, 1300), 1.25)}" sizes="(max-width:900px) 100vw, 48vw" alt="Tuoreita leipiä" loading="lazy"></div>
<div class="ilm"><span class="eb">Räätälöity verkkokauppa</span><h2>Kauppa, joka myy tunnelmalla</h2><p class="lead" style="color:var(--mute);font-size:1.08rem">Jokainen kauppa rakennetaan alusta asti juuri sinun yrityksesi tarpeisiin. Kauppaan voi lisätä esimerkiksi:</p>
<div class="ominais"><div><b>Nouto- ja toimitusajat</b>Asiakas valitsee ajan, esim. "huomenna 7–9".</div><div><b>Kotiinkuljetus alueittain</b>Postinumeroalueet ja omat hinnat.</div><div><b>Tuotteen räätälöinti</b>Kakkutoiveet, kaiverrukset, koot ja värit.</div><div><b>Lahjakortit ja koodit</b>Myy lahjakortteja ja tee kampanjoita.</div><div><b>Kanta-asiakasedut</b>Pisteet tai joka 10. ostos edullisemmin.</div><div style="grid-column:1/-1;background:var(--ink,#2b1d14);color:#fff"><b style="color:#ffd27a">🎙️ Uutuus: Puhuva kauppias</b>Asiakas tilaa puhumalla, ja tekoäly vastaa <u>sinun omalla äänelläsi</u>. <a href="/mallit/kauppa-leipomo/" style="color:#ffd27a;font-weight:700"> Kokeile leipomon esimerkkikaupassa →</a></div></div>
<a class="nappi sin" href="/mallit/kauppa-leipomo/" target="_blank" rel="noopener">Katso esimerkkikauppa →</a></div></div></section>

<section class="osio reilu"><div class="w"><div class="ots ilm"><span class="eb">Reilut ehdot</span><h2>Ei sitoutumista. Ei pientä pränttiä.</h2><p style="color:#c9ccd3">Riski on minun, ei sinun. Jos et ole tyytyväinen, voit lopettaa milloin vain.</p></div>
<div class="ruudut">
<div class="r ilm"><h3>Rakentaminen 0 €</h3><p>Et maksa sivujen tai kaupan tekemisestä mitään.</p></div>
<div class="r ilm"><h3>Lopeta milloin tahansa</h3><p>Ei sitoutumisaikaa eikä irtisanomismaksua. Kuukausi kerrallaan.</p></div>
<div class="r ilm"><h3>Osoite lunastettavissa</h3><p>Verkko-osoitteen voi lunastaa itselleen milloin vain {LUNASTUS} €:lla.</p></div>
<div class="r ilm"><h3>Muutokset sisältyvät</h3><p>Haluatko muuttaa sivustoa? Muutokset kuuluvat hintaan. Muualla jokainen muutos laskutetaan – Netvossa säästö voi olla tuhansia euroja.</p></div>
</div><p style="margin-top:26px"><a href="/ehdot/" style="color:var(--kulta);font-weight:600">Lue tarkat sopimusehdot →</a></p></div></section>

<section class="osio"><div class="w"><div class="tekija ilm"><div class="av">M</div><div><p class="q">”Hoidan jokaisen asiakkaan sivut alusta loppuun ja vastaan puhelimeen itse. Kun soitat, puhut sen kanssa, joka sivustasi oikeasti vastaa.”</p><p><b style="color:var(--ink)">Miika Koskela</b>, Netvo · Ylivieska</p></div></div></div></section>

<section class="osio alt" id="ukk"><div class="w"><div class="ots keski ilm" style="text-align:center"><span class="eb">Kysyttyä</span><h2>Usein kysyttyä</h2></div><div class="ukk">
<details><summary>Onko rakentaminen oikeasti ilmainen?</summary><p>Kyllä. Et maksa sivujen tai kaupan tekemisestä mitään. Maksat vain kuukausimaksun: nettisivut {HINTA_KK} €/kk tai verkkokauppa {KAUPPA_KK} €/kk.</p></details>
<details><summary>Onko sitoutumisaikaa?</summary><p>Ei. Voit lopettaa milloin tahansa, eikä lopettamisesta peritä maksua. Palvelu päättyy maksetun kuukauden lopussa.</p></details>
<details><summary>Kenen nimissä verkko-osoite on?</summary><p>Verkko-osoite rekisteröidään Netvon nimiin. Voit lunastaa sen itsellesi milloin tahansa {LUNASTUS} €:lla, ja siirrän sen sinulle viikon sisällä maksusta.</p></details>
<details><summary>Maksavatko muutokset erikseen?</summary><p>Eivät. Kaikki muutokset sisältyvät kuukausihintaan – oli kyse teksteistä, kuvista, tuotteista, uudesta sivusta tai ulkoasusta. Lähetät vain viestin. Koska muutoksista ei laskuteta erikseen, hyöty voi vuosien mittaan olla jopa tuhansia euroja.</p></details>
<details><summary>Milloin maksan ensimmäisen kerran?</summary><p>Ensimmäinen kuukausi maksetaan, kun olet hyväksynyt vedoksen ja ennen kuin sivut julkaistaan. Sen jälkeen lasku tulee kuukausittain.</p></details>
<details><summary>Käytätkö valmispohjia?</summary><p>En. Jokainen nettisivu ja verkkokauppa räätälöidään asiakkaan tarpeen mukaan: ulkoasu, rakenne ja toiminnot suunnitellaan juuri sinun yrityksellesi.</p></details>
<details><summary>Voinko käyttää omia kuvia?</summary><p>Totta kai, ja se on suositeltavaa: omat kuvat tekevät sivuista aidon näköiset. Jos kuvia ei ole, valitaan yhdessä laadukkaat kuvapankkikuvat.</p></details>
<details><summary>Kauanko tekeminen kestää?</summary><p>Yleensä muutaman päivän siitä, kun olet toimittanut tietosi. Näet vedoksen ennen julkaisua.</p></details>
</div></div></section>

<section class="osio" id="yhteys"><div class="w"><div class="cta ilm"><h2>Hanki sivut tai kauppa ilmaiseksi</h2><p>Soita yläkulman numeroon tai lähetä viesti. Rakentaminen on 0 €, eikä mitään tarvitse päättää heti.</p>
<div class="toim" style="justify-content:center"><a class="nappi iso" href="mailto:{esc(YHTEYS)}?subject=Netvo%20-%20nettisivut%20yritykselleni">Lähetä sähköposti</a></div>
<p style="margin:20px auto 0;font-size:.95rem">Arkisin 9–21 · {esc(YHTEYS)} · voit kysyä myös chatissa</p></div></div></section>
"""
    return _sivu("Netvo – nettisivut ja verkkokauppa ilmaiseksi rakennettuna, ei sitoutumista",
                 f"Saat jopa 1500 € edestä työtä ilmaiseksi: Netvo räätälöi yrityksesi nettisivut tai verkkokaupan maksutta, ilman valmispohjia. Nettisivut {HINTA_KK} €/kk, verkkokauppa {KAUPPA_KK} €/kk, ei sitoutumista.", runko)


def ehtosivu():
    runko = f"""<section class="osio"><div class="w teksti">
<h1>Sopimusehdot</h1>
<p style="color:var(--mute)">Nämä ehdot kuvaavat Netvo-palvelun sisällön ja hinnoittelun selkeästi ja reilusti. Ehdot ovat voimassa 29.10.2026 alkaen.</p>
<h2>1. Palvelut</h2>
<p>Netvolla on kaksi palvelua: <b>Nettisivut</b> ja <b>Verkkokauppa</b>. Netvo rakentaa sivut tai kaupan asiakkaan puolesta ja ylläpitää niitä. Kuukausimaksuun sisältyvät verkko-osoite, hosting, varmuuskopiot, tietoturva, päivitykset sekä kaikki asiakkaan pyytämät muutokset sivustoon (esimerkiksi tekstit, kuvat, tuotteet, uudet sivut ja ulkoasu). Muutoksista ei peritä erillistä maksua.</p>
<h2>2. Hinta</h2>
<p>Sivujen ja kaupan rakentaminen on maksutonta. Kuukausihinnat (sis. alv): Nettisivut {HINTA_KK} € ja Verkkokauppa {KAUPPA_KK} €. Verkkokaupassa asiakas tekee sopimuksen haluamansa maksupalvelun kanssa suoraan; maksupalvelu veloittaa omat kulunsa, ja myyntitulot menevät suoraan asiakkaalle. Muita kuluja tai lisämaksuja ei ole. Laskutus kuukausittain laskulla; palvelun tuottaa ja laskuttaa Taksiliikenne Koskela Oy, palvelun nimi Netvo.</p>
<h2>3. Laskutus ja julkaisu</h2>
<p>Asiakas näkee vedoksen ennen julkaisua. Ensimmäinen kuukausi maksetaan, kun asiakas on hyväksynyt vedoksen, ja sivut julkaistaan maksun jälkeen. Sen jälkeen palvelu laskutetaan kuukausi kerrallaan etukäteen.</p>
<h2>4. Ei sitoutumista</h2>
<p>Sopimus on voimassa toistaiseksi ilman sitoutumisaikaa. Asiakas voi lopettaa palvelun milloin tahansa ilmoittamalla siitä sähköpostilla tai puhelimella. Palvelu päättyy maksetun kuukauden lopussa. Lopettamisesta ei peritä maksua.</p>
<h2>5. Verkko-osoite</h2>
<p>Verkko-osoite (domain) rekisteröidään Netvon nimiin, ja Netvo maksaa sen vuosimaksut palvelun ajan. Asiakas voi lunastaa verkko-osoitteen itselleen milloin tahansa {LUNASTUS} €:lla (sis. alv). Netvo tekee haltijanvaihdon viikon sisällä maksusta. Jos asiakas lopettaa palvelun eikä lunasta osoitetta, osoite jää Netvolle.</p>
<h2>6. Sivujen sisältö ja vastuu</h2>
<p>Asiakas vastaa toimittamiensa tietojen, tuotetietojen ja kuvien oikeellisuudesta ja siitä, että niillä on oikeus julkaista ne. Verkkokaupassa asiakas vastaa myymistään tuotteista ja kuluttajansuojan velvoitteista. Netvo vastaa sivujen teknisestä toiminnasta ja ylläpidosta.</p>
<h2>7. Sopimuksen päättyminen</h2>
<p>Sopimuksen päättyessä sivut poistetaan verkosta. Asiakas voi halutessaan pyytää sivujen tekstit ja kuvat itselleen. Verkko-osoite siirtyy asiakkaalle, jos hän on lunastanut sen.</p>
<p style="color:var(--mute);margin-top:30px">Kysymyksiä ehdoista? Ota yhteyttä: {esc(YHTEYS)}</p>
<p class="keskita"><a class="nappi" href="/">← Takaisin etusivulle</a></p>
</div></section>"""
    return _sivu("Sopimusehdot – Netvo", "Netvo-palvelun selkeät ja reilut sopimusehdot: rakentaminen 0 €, kuukausihinta, ei sitoutumista.", runko)


def tietosuojasivu():
    ts = seloste(palvelu="Netvo (netvo.fi)", rekisterinpitaja="Taksiliikenne Koskela Oy (Y-tunnus 3425681-3), palvelun nimi Netvo", yhteys=YHTEYS,
        tiedot=[("Yhteydenotot", "kun soitat, lähetät sähköpostia tai viestin, käsittelemme nimesi, yhteystietosi ja viestisi sisällön."),
                ("Asiakkuus", "asiakkaista käsittelemme yrityksen ja yhteyshenkilön tiedot, laskutustiedot sekä sivujen sisällön, jonka asiakas toimittaa."),
                ("Chat", "Kysy meiltä -chattiin kirjoittamasi viesti välitetään tekoälypalvelulle vastauksen muodostamista varten. Keskusteluja ei tallenneta palvelimellemme; laskemme vain viestien määrän."),
                ("Mainonnan mittaus", "Google Ads -tagi kirjaa, jos mainoksen kautta tullut kävijä painaa puhelin- tai sähköpostilinkkiä tai lähettää chat-viestin. Evästeitä käytetään tähän vain, jos hyväksyt ne."),
                ("Esimerkkisivut", "esimerkkikauppojen ostoskori tallentuu vain selaimeesi. Puhuva kauppias -esimerkissä puheesi muutetaan tekstiksi selaimessa, ja kysymys välitetään tekoälypalveluille vastauksen ja puheen tuottamiseksi. Niitä ei tallenneta."),
                ("Tekniset lokitiedot", "palvelin käsittelee laitteesi IP-osoitteen ja selaimen tiedot sivuston toimittamiseksi ja tietoturvaa varten.")],
        tarkoitus="Tietoja käsitellään yhteydenottoihin vastaamiseen, asiakassuhteen hoitamiseen ja laskutukseen (sopimus ja sopimusta edeltävät toimet), kirjanpitolain velvoitteisiin (lakisääteinen velvoite), sivuston toimivuuteen ja tietoturvaan (oikeutettu etu) sekä mainonnan mittaamiseen (suostumus).",
        kasittelijat=[("Cloudflare, Inc.", "palvelimet ja tietoturva"), ("Anthropic PBC", "chatin ja Puhuvan kauppiaan tekoälyvastaukset"), ("ElevenLabs", "Puhuvan kauppiaan puhe"),
                      ("Google LLC", "Google Ads -mainonnan mittaus ja Google Fonts -kirjasimet"), ("Google Workspace / Gmail", "sähköpostiviestintä"), ("Kirjanpitäjä", "kirjanpito ja laskutusaineisto")],
        sailytys="Yhteydenotot säilytetään niin kauan kuin asian hoitaminen vaatii, enintään kaksi vuotta. Asiakkuuden tiedot säilytetään asiakkuuden ajan ja kirjanpitoaineisto kirjanpitolain mukaisen ajan (yleensä 6–10 vuotta). Mainonnan mittaustiedot säilyvät Googlen asetusten mukaisesti.",
        evasteet="Mainonnan mittauksen evästeet otetaan käyttöön vain, jos hyväksyt ne sivun alareunan ilmoituksesta. Valintasi tallentuu selaimeesi, ja voit muuttaa sitä tyhjentämällä sivuston tallennetut tiedot. Ilman hyväksyntää Google saa vain evästeettömän, yksilöimättömän tiedon käynnistä.")
    return _sivu("Tietosuojaseloste – Netvo", "Netvon tietosuojaseloste: mitä tietoja käsitellään ja miksi.", f'<section class="osio"><div class="w teksti">{ts}</div></section>')


def rakenna_nettikoti(root):
    """Kirjoittaa Netvo-sivut kansioon <root>/netvo/."""
    root = pathlib.Path(root)
    (root / "netvo").mkdir(parents=True, exist_ok=True)
    (root / "netvo" / "index.html").write_text(etusivu(), encoding="utf-8")
    (root / "netvo" / "ehdot").mkdir(exist_ok=True)
    (root / "netvo" / "ehdot" / "index.html").write_text(ehtosivu(), encoding="utf-8")
    (root / "netvo" / "tietosuoja").mkdir(exist_ok=True)
    (root / "netvo" / "tietosuoja" / "index.html").write_text(tietosuojasivu(), encoding="utf-8")
    for d in DEMOT:
        kansio = root / "netvo" / "mallit" / d["slug"]
        kansio.mkdir(parents=True, exist_ok=True)
        (kansio / "index.html").write_text(palvelusivu(d) if d.get("tyyppi") != "kauppa" else mallisivu(d), encoding="utf-8")
    # Verkkokauppamallit: räätälöidyt, täysin toimivat mallikaupat (korvaavat yksinkertaiset)
    from .premium import rakenna as rakenna_premium
    rakenna_premium(root)
    return len(DEMOT)
