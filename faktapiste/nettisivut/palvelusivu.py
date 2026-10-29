"""Netvon valmiiden nettisivujen mallipohja (palvelualat), esteettinen versio:
iso tunnelmakuva, serif-otsikot, palvelulista hinnoin, kuvagalleria, arvostelut, "avoinna nyt" ja puhelimessa aina näkyvä soittonappi.
Kuvat: Unsplash (ilmainen Unsplash-lisenssi), tunnukset tarkistettu.
"""
import html, json

esc = html.escape
U = lambda i, w, h=None: f"https://images.unsplash.com/{i}?auto=format&fit=crop&w={w}{f'&h={h}' if h else ''}&q=72"
SS = lambda i, ws, ar=None: ", ".join(f"{U(i, w, int(w * ar) if ar else None)} {w}w" for w in ws)

KUVAT = {  # slug: (hero, [galleria x3])
    "parturi": ("photo-1585747860715-2ba37e788b70", ["photo-1647140655214-e4a2d914971f", "photo-1605497788044-5a32c7078486", "photo-1621605815971-fbc98d665033"]),
    "putki": ("photo-1749532125405-70950966b0e5", ["photo-1676210134188-4c05dd172f89", "photo-1542013936693-884638332954", "photo-1620653713380-7a34b773fef8"]),
    "siivous": ("photo-1758273238415-01ec03d9ef27", ["photo-1773579305267-8d75e0af5be4", "photo-1646980241033-cd7abda2ee88", "photo-1758272422155-d898efd14f81"]),
    "remontti": ("photo-1505798577917-a65157d3320a", ["photo-1618832515490-e181c4794a45", "photo-1656733911001-16912b79d2bf", "photo-1517581177682-a085bb7ffb15"]),
    "ravintola": ("photo-1578474846511-04ba529f0b88", ["photo-1466978913421-dad2ebd01d17", "photo-1555396273-367ea4eb4db5", "photo-1514933651103-005eec06c04b"]),
    "hyvinvointi": ("photo-1600334089648-b0d9d3028eb2", ["photo-1741522509438-a120c0bb5e88", "photo-1544161515-4ab6ce6db874", "photo-1598901986949-f593ff2a31a6"]),
    "autokorjaamo": ("photo-1615906655593-ad0386982a0f", ["photo-1727893119356-1702fe921cf9", "photo-1487754180451-c456f719a1fc", "photo-1675034743372-672c3c3f8377"]),
    "maalaus": ("photo-1742900280861-32bed068938b", ["photo-1525909002-1b05e0c869d8", "photo-1574359411659-15573a27fd0c", "photo-1599619585752-c3edb42a414c"]),
}

# teema -> (aksentti, aksentti tumma, tausta, pehmeä)
VARIT = {
    "musta": ("#b08a4e", "#8c6c38", "#f6f3ee", "#ece5da"),
    "sininen": ("#1f5fae", "#164784", "#f4f6f9", "#e3eaf4"),
    "petroli": ("#0f6f73", "#0a5255", "#f2f6f5", "#dfeceb"),
    "oranssi": ("#c25a1c", "#994513", "#f7f3ee", "#efe2d4"),
    "viininpunainen": ("#8e2a3d", "#6b1e2d", "#f8f3f0", "#efe1df"),
    "vihrea": ("#4f6e4a", "#3b5437", "#f5f4ef", "#e5e8dc"),
    "ruskea": ("#8a5a32", "#6b4426", "#f7f2ec", "#ece1d3"),
    "purppura": ("#5b3a9c", "#432b74", "#f6f4f9", "#e7e1f1"),
}

# Jokainen esimerkki omalla ilmeellään (fontit, hero-asettelu, kulmat, tumma/vaalea) – ei yhtä pohjaa.
TYYLIT = {  # slug: (otsikkofontti, leipäfontti, google-fonts-perhe, otsikon paino, kirjainväli, text-transform, kulmat, hero, tumma)
    "parturi":      ("'Playfair Display',Georgia,serif", "Inter,system-ui,sans-serif", "Playfair+Display:ital,wght@0,500;0,700;1,500&family=Inter:wght@400;500;600", 500, "-.01em", "none", "4px", "keski", True),
    "putki":        ("Manrope,system-ui,sans-serif", "Manrope,system-ui,sans-serif", "Manrope:wght@400;500;600;800", 800, "-.03em", "none", "16px", "jaettu", False),
    "siivous":      ("'DM Serif Display',Georgia,serif", "'DM Sans',system-ui,sans-serif", "DM+Serif+Display&family=DM+Sans:wght@400;500;600", 400, "-.01em", "none", "28px", "kaari", False),
    "remontti":     ("'Archivo Black',Impact,sans-serif", "Archivo,system-ui,sans-serif", "Archivo+Black&family=Archivo:wght@400;500;600", 400, "-.01em", "uppercase", "0px", "full", False),
    "ravintola":    ("'Cormorant Garamond',Georgia,serif", "Karla,system-ui,sans-serif", "Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Karla:wght@400;500;600", 600, "0", "none", "6px", "keski", True),
    "hyvinvointi":  ("'Cormorant Garamond',Georgia,serif", "Jost,system-ui,sans-serif", "Cormorant+Garamond:ital,wght@0,500;1,500&family=Jost:wght@400;500", 500, "0", "none", "32px", "kaari", False),
    "autokorjaamo": ("'Space Grotesk',system-ui,sans-serif", "'Space Grotesk',system-ui,sans-serif", "Space+Grotesk:wght@400;500;700", 700, "-.03em", "none", "8px", "full", True),
    "maalaus":      ("Fraunces,Georgia,serif", "Inter,system-ui,sans-serif", "Fraunces:ital,opsz,wght@0,9..144,500;1,9..144,500&family=Inter:wght@400;500;600", 500, "-.015em", "none", "22px", "jaettu", False),
}

IK = {
    "puh": '<path d="M4 4h4l2 5-3 2a12 12 0 006 6l2-3 5 2v4a2 2 0 01-2 2A16 16 0 014 6a2 2 0 010-2z"/>',
    "posti": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "paikka": '<path d="M12 21s-7-6-7-11a7 7 0 1114 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "kello": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "ok": '<path d="M5 12l4 4 10-10"/>',
}
def ik(n): return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{IK[n]}</svg>'

CSS = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:#1c1a17;font:16.5px/1.65 var(--fb);-webkit-font-smoothing:antialiased}
img{display:block;max-width:100%}a{color:inherit}
h1,h2,h3{font-family:var(--fh);font-weight:var(--hw);letter-spacing:var(--ls);line-height:1.08;margin:0 0 .45em;text-transform:var(--tt)}
.w{max-width:1120px;margin:0 auto;padding:0 22px}
.demo{background:#15171a;color:#e9e9ea;font-size:.84rem;text-align:center;padding:8px 14px}.demo a{color:#ffd24a;font-weight:700}
header.top{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.86);backdrop-filter:saturate(1.4) blur(12px);-webkit-backdrop-filter:saturate(1.4) blur(12px);border-bottom:1px solid rgba(0,0,0,.06)}
.bar{display:flex;align-items:center;justify-content:space-between;height:68px}
.logo{font-family:var(--fh);font-size:1.45rem;text-decoration:none;letter-spacing:-.01em}
.logo small{display:block;font-family:var(--fb);font-size:.6rem;letter-spacing:.28em;text-transform:uppercase;color:#7a746b;margin-top:-3px}
nav.m{display:flex;gap:22px;align-items:center;font-size:.95rem}nav.m a{text-decoration:none;color:#3a362f}nav.m a:hover{color:var(--a)}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--a);color:#fff;text-decoration:none;font-weight:600;padding:13px 22px;border-radius:999px;border:0;cursor:pointer;font-size:1rem;transition:background .15s,transform .15s}
.btn:hover{background:var(--a2);transform:translateY(-1px)}.btn svg{width:18px;height:18px}
.btn.light{background:#fff;color:#1c1a17}.btn.ghost{background:transparent;color:#fff;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.75)}
@media(max-width:760px){nav.m a:not(.btn){display:none}}
.hero{position:relative;min-height:min(86vh,760px);display:flex;align-items:flex-end;color:#fff;overflow:hidden}
.hero img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:kb 18s ease-out both}
@keyframes kb{from{transform:scale(1.08)}to{transform:scale(1)}}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05) 0%,rgba(0,0,0,.25) 45%,rgba(0,0,0,.72) 100%)}
.hero .w{position:relative;z-index:1;padding-bottom:64px;padding-top:120px}
.kick{display:inline-block;font-size:.78rem;letter-spacing:.24em;text-transform:uppercase;opacity:.92;margin-bottom:14px}
.hero h1{font-size:clamp(2.5rem,7vw,4.8rem);max-width:15ch}
.hero p{font-size:clamp(1.05rem,2vw,1.25rem);max-width:46ch;opacity:.95;margin:0 0 26px}
.hero .toim{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.auki{display:inline-flex;align-items:center;gap:8px;font-size:.92rem;background:rgba(0,0,0,.35);padding:7px 13px;border-radius:999px;margin-top:18px}
.auki i{width:9px;height:9px;border-radius:50%;background:#ccc;display:inline-block}.auki.on i{background:#4ade80;box-shadow:0 0 0 4px rgba(74,222,128,.25)}
.trust{background:#fff;border-bottom:1px solid rgba(0,0,0,.06)}
.trust .w{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding-top:22px;padding-bottom:22px}
.trust div{display:flex;gap:10px;align-items:center;font-size:.95rem;font-weight:500}.trust svg{width:22px;height:22px;color:var(--a);flex:none}
@media(max-width:760px){.trust .w{grid-template-columns:1fr 1fr}}
.s{padding:84px 0}.s.alt{background:var(--soft)}
.eb{font-size:.76rem;letter-spacing:.24em;text-transform:uppercase;color:var(--a);font-weight:600;display:block;margin-bottom:10px}
.s h2{font-size:clamp(2rem,4.4vw,3rem)}
.lead{color:#5d574e;max-width:56ch;font-size:1.08rem}
.pal{display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:start;margin-top:30px}
@media(max-width:860px){.pal{grid-template-columns:1fr;gap:30px}}
.lista{border-top:1px solid rgba(0,0,0,.12)}
.rivi{display:grid;grid-template-columns:1fr auto;gap:4px 18px;padding:20px 0;border-bottom:1px solid rgba(0,0,0,.12)}
.rivi h3{font-size:1.3rem;margin:0}.rivi .h{font-family:var(--fh);font-size:1.25rem;color:var(--a);white-space:nowrap}
.rivi p{grid-column:1/-1;margin:0;color:#6a645a}
.pal .kuva{position:sticky;top:96px;border-radius:var(--r);overflow:hidden;aspect-ratio:4/5;box-shadow:0 30px 60px -30px rgba(0,0,0,.35)}
.pal .kuva img{width:100%;height:100%;object-fit:cover}
.gal{display:grid;grid-template-columns:2fr 1fr;grid-template-rows:1fr 1fr;gap:14px;height:min(70vw,560px);margin-top:34px}
.gal img{width:100%;height:100%;object-fit:cover;border-radius:calc(var(--r) * .85)}.gal img:first-child{grid-row:1/3}
@media(max-width:640px){.gal{height:auto;grid-template-columns:1fr 1fr;grid-template-rows:auto}.gal img{aspect-ratio:1}.gal img:first-child{grid-column:1/-1;grid-row:auto;aspect-ratio:4/3}}
.meista{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}
@media(max-width:860px){.meista{grid-template-columns:1fr;gap:28px}}
.edut{list-style:none;padding:0;margin:22px 0 0;display:grid;gap:12px}
.edut li{display:flex;gap:12px;align-items:center;font-weight:500}.edut span{width:30px;height:30px;border-radius:50%;background:var(--soft);color:var(--a);display:grid;place-items:center;flex:none}.edut svg{width:16px;height:16px}
.luku{display:flex;gap:34px;margin-top:28px}.luku b{display:block;font-family:var(--fh);font-size:2.4rem;font-weight:500;color:var(--a);line-height:1}.luku span{color:#6a645a;font-size:.9rem}
.arvot{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:30px}
.arvo{background:#fff;border-radius:var(--r);padding:30px;box-shadow:0 1px 0 rgba(0,0,0,.04),0 20px 40px -28px rgba(0,0,0,.25)}
.arvo .t{color:#e3a72f;letter-spacing:2px}.arvo p{font-family:var(--fh);font-size:1.22rem;line-height:1.45;margin:12px 0 16px}.arvo b{font-size:.92rem}
.yht{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:30px}
@media(max-width:860px){.yht{grid-template-columns:1fr}}
.kortti{background:#fff;border-radius:var(--r);padding:30px;box-shadow:0 20px 40px -30px rgba(0,0,0,.3)}
.yrivi{display:flex;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid rgba(0,0,0,.08);text-decoration:none;font-weight:500;font-size:1.05rem}
.yrivi svg{width:22px;height:22px;color:var(--a);flex:none}.yrivi:last-of-type{border:0}
.ajat{width:100%;border-collapse:collapse;margin-top:6px}.ajat td{padding:10px 0;border-bottom:1px solid rgba(0,0,0,.08)}.ajat td:last-child{text-align:right;font-weight:600}
.ajat tr.tanaan td{color:var(--a);font-weight:700}
form.lom{display:grid;gap:12px}
form.lom input,form.lom textarea{width:100%;font:inherit;padding:14px 16px;border-radius:calc(var(--r) * .6);border:1px solid rgba(0,0,0,.14);background:var(--bg)}
form.lom input:focus,form.lom textarea:focus{outline:2px solid var(--a);border-color:transparent}
.pieni{color:#8a8378;font-size:.82rem;margin:0}
footer{background:#141210;color:#a49d92;padding:46px 0 110px;font-size:.92rem}
footer .w{display:flex;flex-wrap:wrap;gap:20px;justify-content:space-between}footer b{color:#fff;font-family:var(--fh);font-weight:500;font-size:1.3rem}
footer a{color:#e8e2d6}
.ilm{opacity:0;transform:translateY(18px);transition:opacity .7s ease,transform .7s ease}.ilm.nak{opacity:1;transform:none}

/* --- hero-muunnelmat --- */
.hero.keski{align-items:center;text-align:center}.hero.keski .w{padding-bottom:90px;padding-top:110px}.hero.keski h1,.hero.keski p{margin-left:auto;margin-right:auto}.hero.keski h1{max-width:18ch;font-size:clamp(2.7rem,8vw,5.6rem)}.hero.keski .toim{justify-content:center}
.hero.keski::after{background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.55))}
.hj{padding:56px 0 70px}.hj .w{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center}
.hj h1{font-size:clamp(2.5rem,6.4vw,4.6rem);max-width:14ch}.hj p.l{font-size:1.15rem;color:var(--mu);max-width:44ch;margin:0 0 26px}
.hj .kick{color:var(--a);font-weight:600}.hj .toim{display:flex;gap:12px;flex-wrap:wrap}
.hj .btn.ghost{color:var(--tx);box-shadow:inset 0 0 0 1.5px var(--li2)}
.hj figure{margin:0;position:relative}.hj figure img{width:100%;aspect-ratio:4/5;object-fit:cover;border-radius:var(--r);box-shadow:0 40px 80px -40px rgba(0,0,0,.5)}
.hj.kaari figure img{border-radius:999px 999px var(--r) var(--r);aspect-ratio:3/4}
.hj .auki{background:var(--soft);color:var(--tx)}
@media(max-width:860px){.hj .w{grid-template-columns:1fr;gap:30px}.hj figure img{aspect-ratio:4/3}.hj.kaari figure img{aspect-ratio:4/5;max-height:70vh}}
/* --- tumma tyyli --- */
body.tumma{background:#121110;color:#ece6dc}
body.tumma header.top{background:rgba(18,17,16,.86);border-color:rgba(255,255,255,.08)}
body.tumma nav.m a{color:#d6cfc3}body.tumma .logo small{color:#9a9287}
body.tumma .trust{background:#171513;border-color:rgba(255,255,255,.07)}
body.tumma .s.alt{background:#191715}body.tumma .lead,body.tumma .rivi p,body.tumma .luku span{color:#a8a095}
body.tumma .lista,body.tumma .rivi{border-color:rgba(255,255,255,.12)}
body.tumma .arvo,body.tumma .kortti{background:#1e1c19;box-shadow:none;border:1px solid rgba(255,255,255,.07)}
body.tumma .edut span{background:#23201c}
body.tumma form.lom input,body.tumma form.lom textarea{background:#141210;color:#ece6dc;border-color:rgba(255,255,255,.14)}
body.tumma .yrivi,body.tumma .ajat td{border-color:rgba(255,255,255,.1)}
@media(prefers-reduced-motion:reduce){.hero img{animation:none}.ilm{opacity:1;transform:none}}
"""

JS = """
(function(){var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('nak');o.unobserve(e.target)}})},{threshold:.12});
document.querySelectorAll('.ilm').forEach(function(x){o.observe(x)});setTimeout(function(){document.querySelectorAll('.ilm').forEach(function(x){x.classList.add('nak')})},2500);
var A=window.AUKI||[];var d=new Date(),wd=(d.getDay()+6)%7,h=d.getHours()+d.getMinutes()/60;
var map={'ma':0,'ti':1,'ke':2,'to':3,'pe':4,'la':5,'su':6};function paivat(s){s=s.toLowerCase();var m=s.match(/^(ma|ti|ke|to|pe|la|su)(?:\\s*[–-]\\s*(ma|ti|ke|to|pe|la|su))?$/);if(!m)return null;var a=map[m[1]],b=m[2]?map[m[2]]:a,r=[];for(var i=a;i<=b;i++)r.push(i);return r}
var auki=false,tunn=false;A.forEach(function(r,ix){var p=paivat(r[0]||'');if(!p||p.indexOf(wd)<0)return;tunn=true;var row=document.querySelectorAll('.ajat tr')[ix];if(row)row.classList.add('tanaan');var t=(r[1]||'').match(/(\\d{1,2})(?:[.:](\\d\\d))?\\s*[–-]\\s*(\\d{1,2})(?:[.:](\\d\\d))?/);if(t){var a=+t[1]+(+t[2]||0)/60,b=+t[3]+(+t[4]||0)/60;if(h>=a&&h<b)auki=true}});
document.querySelectorAll('[data-auki]').forEach(function(el){if(!tunn&&!A.length){el.remove();return}el.classList.toggle('on',auki);el.querySelector('span').textContent=auki?'Avoinna nyt':'Suljettu nyt – jätä viesti'});})();
"""


def sivu(d, demo=True):
    a, a2, bg, soft = VARIT.get(d.get("teema", "sininen"), VARIT["sininen"])
    hero, gal = KUVAT.get(d["slug"], KUVAT["putki"])
    nimi = d["nimi"]
    fh, fb, gf, hw, ls, tt, r, hv, tumma = TYYLIT.get(d["slug"], TYYLIT["maalaus"])
    kaupunki = (d.get("osoite", "").split()[-1] if d.get("osoite") else "")
    tel = "tel:" + d.get("puhelin", "").replace(" ", "")
    edut = d.get("edut", [])[:4]
    palvelut = "".join(
        f'<div class="rivi"><h3>{esc(s["nimi"])}</h3>' + (f'<span class="h">{esc(s["hinta"])}</span>' if s.get("hinta") else '<span></span>')
        + f'<p>{esc(s["kuvaus"])}</p></div>' for s in d.get("palvelut", []))
    arvot = "".join(f'<figure class="arvo ilm" style="margin:0"><div class="t">★★★★★</div><p>”{esc(x["teksti"])}”</p><b>{esc(x["nimi"])}</b></figure>' for x in d.get("arvostelut", []))
    ajat_rivit = [(p, t) for p, t in d.get("aukiolo", []) if p]
    ajat = "".join(f"<tr><td>{esc(p)}</td><td>{esc(t)}</td></tr>" for p, t in ajat_rivit)
    kick = esc(d.get("ala", "")) + (" · " + esc(kaupunki) if kaupunki else "")
    toim = f'<div class="toim"><a class="btn" href="#yhteys">{esc(d.get("cta", "Ota yhteyttä"))} →</a><a class="btn ghost" href="{tel}">{ik("puh")}{esc(d.get("puhelin", ""))}</a></div><div class="auki" data-auki><i></i><span>Avoinna</span></div>'
    if hv in ("jaettu", "kaari"):
        hero_html = (f'<section class="hj {hv}"><div class="w"><div><span class="kick">{kick}</span><h1>{esc(d.get("slogan", nimi))}</h1><p class="l">{esc(d.get("lupaus", ""))}</p>{toim}</div>'
                     f'<figure><img src="{U(hero, 1100, 1375)}" srcset="{SS(hero, (600, 1100, 1500), 1.25)}" sizes="(max-width:860px) 100vw, 46vw" alt="" fetchpriority="high"></figure></div></section>')
    else:
        hero_html = (f'<section class="hero{" keski" if hv == "keski" else ""}"><img src="{U(hero, 1600)}" srcset="{SS(hero, (800, 1200, 1600, 2200))}" sizes="100vw" alt="" fetchpriority="high">'
                     f'<div class="w"><span class="kick">{kick}</span><h1>{esc(d.get("slogan", nimi))}</h1><p>{esc(d.get("lupaus", ""))}</p>{toim}</div></section>')
    demo_html = ('<div class="demo">Tämä on Netvon <b>esimerkkisivu</b>. Jokainen sivu räätälöidään asiakkaan tarpeen mukaan – ei valmispohjia. '
                 '<a href="/">Rakentaminen 0 € →</a></div>') if demo else ""
    return f"""<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(nimi)} – {esc(d.get("ala", ""))} {esc(kaupunki)}</title><meta name="description" content="{esc(d.get("meta", nimi))}"><meta name="robots" content="noindex"><meta name="theme-color" content="{a}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={gf}&display=swap" rel="stylesheet">
<link rel="preload" as="image" href="{U(hero, 1200)}">
<style>:root{{--a:{a};--a2:{a2};--bg:{bg};--soft:{soft};--fh:{fh};--fb:{fb};--hw:{hw};--ls:{ls};--tt:{tt};--r:{r};--tx:{"#ece6dc" if tumma else "#1c1a17"};--mu:{"#a8a095" if tumma else "#5d574e"};--li2:{"rgba(255,255,255,.35)" if tumma else "rgba(0,0,0,.25)"}}}{CSS}</style></head><body class="{"tumma" if tumma else ""}">
{demo_html}
<header class="top"><div class="w bar"><a class="logo" href="#">{esc(nimi)}<small>{esc(d.get("ala", ""))}</small></a>
<nav class="m"><a href="#palvelut">Palvelut</a><a href="#meista">Meistä</a><a href="#yhteys">Yhteys</a></nav></div></header>
{hero_html}
<div class="trust"><div class="w">{''.join(f'<div>{ik("ok")}{esc(e)}</div>' for e in edut)}</div></div>
<section class="s" id="palvelut"><div class="w"><span class="eb">{esc(d.get("palvelut_otsikko", "Palvelut"))}</span><h2 class="ilm">Mitä teemme</h2>
<div class="pal"><div class="lista ilm">{palvelut}</div><div class="kuva ilm"><img src="{U(gal[0], 900, 1125)}" srcset="{SS(gal[0], (500, 900, 1300), 1.25)}" sizes="(max-width:860px) 100vw, 45vw" alt="" loading="lazy"></div></div></div></section>
<section class="s alt" id="meista"><div class="w meista"><div class="ilm"><span class="eb">Meistä</span><h2>{esc(d.get("esittely_otsikko", "Meistä"))}</h2>
{''.join(f'<p class="lead">{esc(x)}</p>' for x in d.get("esittely", []))}
<ul class="edut">{''.join(f'<li><span>{ik("ok")}</span>{esc(e)}</li>' for e in d.get("edut", []))}</ul>
<div class="luku"><div><b>4,9</b><span>asiakkaiden arvio</span></div><div><b>{len(d.get("palvelut", []))}</b><span>palvelua</span></div><div><b>100 %</b><span>paikallinen</span></div></div></div>
<div class="gal ilm" style="margin:0"><img src="{U(gal[1], 900, 1100)}" alt="" loading="lazy"><img src="{U(gal[2], 600, 500)}" alt="" loading="lazy"><img src="{U(hero, 600, 500)}" alt="" loading="lazy"></div></div></section>
<section class="s"><div class="w"><span class="eb">Asiakkaat sanovat</span><h2 class="ilm">4,9 / 5 tähteä</h2><div class="arvot">{arvot}</div></div></section>
<section class="s alt" id="yhteys"><div class="w"><span class="eb">Yhteystiedot</span><h2 class="ilm">{esc(d.get("cta", "Ota yhteyttä"))}</h2>
<div class="yht"><div class="kortti ilm"><a class="yrivi" href="mailto:{esc(d.get("sposti", ""))}">{ik("posti")}{esc(d.get("sposti", ""))}</a>
<div class="yrivi">{ik("paikka")}{esc(d.get("osoite", ""))}</div>{('<h3 style="margin-top:22px;font-size:1.3rem">Aukioloajat</h3><table class="ajat">' + ajat + '</table>') if ajat else ''}</div>
<form class="lom kortti ilm" onsubmit="event.preventDefault();this.innerHTML='<h3>Kiitos viestistä!</h3><p class=&quot;pieni&quot;>Mallisivulla viestiä ei lähetetä. Oikealla sivulla se tulee suoraan sähköpostiisi.</p>'">
<h3 style="font-size:1.3rem">Lähetä viesti</h3><input placeholder="Nimesi" required><input placeholder="Puhelin tai sähköposti" required><textarea rows="4" placeholder="Mitä voimme tehdä puolestasi?"></textarea>
<button class="btn" type="submit">Lähetä →</button><p class="pieni">Vastaamme yleensä saman päivän aikana.</p></form></div></div></section>
<footer><div class="w"><div><b>{esc(nimi)}</b><br>{esc(d.get("osoite", ""))}<br>{esc(d.get("sposti", ""))}</div>
<div style="text-align:right">© {esc(nimi)}<br>Sivusto: <a href="https://netvo.fi/">Netvo</a> · Kuvat: Unsplash</div></div></footer>

<script>window.AUKI={json.dumps([[p, t] for p, t in ajat_rivit], ensure_ascii=False)};{JS}</script></body></html>"""
