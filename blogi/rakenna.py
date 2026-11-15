#!/usr/bin/env python3
"""Rakentaa Miika Koskelan blogin staattiset sivut kansioon blogi/public.

Kirjoitukset: blogi/kirjoitukset/*.md. Jokaisen tiedoston alussa otsake:
---
otsikko: Kirjoituksen otsikko
pvm: 2026-11-16
tiivistelma: Lyhyt kuvaus (näkyy listassa ja jaettaessa)
---
Tekstiä. Tyhjä rivi = uusi kappale. "## Väliotsikko". **lihavointi**, *kursiivi*, [linkki](https://...).
Kirjoitus julkaistaan vasta, kun pvm on tänään tai mennyt (Suomen aikaa).
"""
import datetime, html, os, re, shutil, json
from zoneinfo import ZoneInfo

JUURI = os.path.dirname(os.path.abspath(__file__))
ULOS = os.path.join(JUURI, "public")
NIMI = "Miika Koskela"
KUVAUS = "Kirjoituksia yhteiskunnasta, islamista, Euroopasta ja Suomen tulevaisuudesta."
OSOITE = os.environ.get("BLOGI_OSOITE", "").rstrip("/")
TANAAN = datetime.datetime.now(ZoneInfo("Europe/Helsinki")).date()
KK = ["tammikuuta", "helmikuuta", "maaliskuuta", "huhtikuuta", "toukokuuta", "kesäkuuta",
      "heinäkuuta", "elokuuta", "syyskuuta", "lokakuuta", "marraskuuta", "joulukuuta"]


def pvm_teksti(d):
    return f"{d.day}. {KK[d.month - 1]} {d.year}"


def rivi(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
    return t


def md(teksti):
    osat = []
    for kpl in re.split(r"\n\s*\n", teksti.strip()):
        kpl = kpl.strip()
        if not kpl:
            continue
        if kpl.startswith("## "):
            osat.append(f"<h2>{rivi(kpl[3:].strip())}</h2>")
        elif kpl.startswith("> "):
            osat.append("<blockquote><p>" + rivi(" ".join(l.lstrip("> ") for l in kpl.splitlines())) + "</p></blockquote>")
        elif all(l.strip().startswith(("- ", "* ")) for l in kpl.splitlines()):
            osat.append("<ul>" + "".join(f"<li>{rivi(l.strip()[2:])}</li>" for l in kpl.splitlines()) + "</ul>")
        else:
            osat.append("<p>" + "<br>".join(rivi(l) for l in kpl.splitlines()) + "</p>")
    return "\n".join(osat)


def lue():
    kansio = os.path.join(JUURI, "kirjoitukset")
    kaikki = []
    for f in sorted(os.listdir(kansio)):
        if not f.endswith(".md"):
            continue
        raaka = open(os.path.join(kansio, f), encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---\n(.*)", raaka, re.S)
        if not m:
            continue
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
        d = datetime.date.fromisoformat(meta["pvm"].strip())
        if d > TANAAN:
            print("odottaa julkaisua:", f, d)
            continue
        polku = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f[:-3])
        sanat = len(m.group(2).split())
        kaikki.append({"otsikko": meta["otsikko"].strip(), "pvm": d, "tiiv": meta.get("tiivistelma", "").strip(),
                       "polku": polku, "html": md(m.group(2)), "min": max(1, round(sanat / 200))})
    return sorted(kaikki, key=lambda k: k["pvm"], reverse=True)


CSS = """
:root{--bg:#f7f4ee;--paper:#fffdf9;--fg:#1d1b18;--muted:#6f6a62;--line:#e6e0d4;--accent:#8c1d18;--accent-soft:#f3e4e1;--chip:#f1ece3}
@media (prefers-color-scheme:dark){:root{--bg:#121110;--paper:#191816;--fg:#ece8e1;--muted:#a39e95;--line:#2d2b27;--accent:#e2766b;--accent-soft:#2a1b19;--chip:#24221f}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:19px/1.75 'Source Serif 4',Georgia,serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-underline-offset:3px}
.ui{font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif}
.wrap{max-width:700px;margin:0 auto;padding:0 20px}
header.top{padding:44px 0 30px;text-align:center;border-bottom:1px solid var(--line);background:var(--paper)}
header.top .merkki{display:inline-grid;place-items:center;width:54px;height:54px;border-radius:50%;background:var(--accent);color:#fff;font:600 22px/1 Fraunces,Georgia,serif;letter-spacing:.02em;margin-bottom:14px}
header.top a.nimi{font:600 34px/1.15 Fraunces,Georgia,serif;color:var(--fg);text-decoration:none;letter-spacing:-.015em}
header.top p{margin:8px auto 0;max-width:460px;color:var(--muted);font:15px/1.55 Inter,system-ui,sans-serif}
main{padding:34px 0 70px}
.lista article{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:26px 26px 22px;margin:0 0 18px;transition:transform .15s,border-color .15s}
.lista article:hover{transform:translateY(-2px);border-color:var(--accent)}
.lista h2{margin:6px 0 8px;font:600 26px/1.25 Fraunces,Georgia,serif;letter-spacing:-.01em}
.lista h2 a{color:var(--fg);text-decoration:none}
.lista p{margin:0 0 12px;color:var(--fg)}
.meta{color:var(--muted);font:13.5px/1.5 Inter,system-ui,sans-serif;letter-spacing:.01em}
.lue{font:600 14px/1 Inter,system-ui,sans-serif;text-decoration:none}
article.kirjoitus{background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:38px 34px}
article.kirjoitus h1{font:600 40px/1.15 Fraunces,Georgia,serif;letter-spacing:-.02em;margin:10px 0 14px}
article.kirjoitus .sisalto{margin-top:30px}
article.kirjoitus .sisalto p:first-child::first-letter{float:left;font:600 64px/.85 Fraunces,Georgia,serif;margin:8px 10px 0 0;color:var(--accent)}
article.kirjoitus h2{font:600 25px/1.3 Fraunces,Georgia,serif;margin:38px 0 8px}
blockquote{margin:26px 0;padding:6px 0 6px 20px;border-left:3px solid var(--accent);font-style:italic;color:var(--muted)}
.jaa{margin-top:44px;padding-top:24px;border-top:1px solid var(--line)}
.otsake{font:600 13px/1 Inter,system-ui,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 14px}
.napit{display:flex;flex-wrap:wrap;gap:8px}
.napit button{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border:1px solid var(--line);border-radius:999px;background:var(--chip);color:var(--fg);font:500 14.5px/1 Inter,system-ui,sans-serif;cursor:pointer}
.napit button:hover{border-color:var(--accent);color:var(--accent)}
.napit .n{font-weight:700;color:var(--muted);min-width:1ch}
.kirjoittaja{display:flex;gap:16px;align-items:center;margin-top:34px;padding:20px;border-radius:16px;background:var(--accent-soft)}
.kirjoittaja .merkki{flex:none;display:grid;place-items:center;width:52px;height:52px;border-radius:50%;background:var(--accent);color:#fff;font:600 20px/1 Fraunces,Georgia,serif}
.kirjoittaja p{margin:0;font:15px/1.55 Inter,system-ui,sans-serif}
.kommentit{margin-top:30px;background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:30px 34px}
.kommentit h2{font:600 24px/1.3 Fraunces,Georgia,serif;margin:0 0 6px}
.kommentti{padding:16px 0;border-bottom:1px solid var(--line)}
.kommentti b{font:600 15px/1.4 Inter,system-ui,sans-serif}
.kommentti p{margin:6px 0 0;font-size:17px;white-space:pre-wrap;overflow-wrap:anywhere}
form.kirjoita{margin-top:22px;display:grid;gap:10px}
form.kirjoita input,form.kirjoita textarea{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--fg);font:16px/1.5 Inter,system-ui,sans-serif}
form.kirjoita textarea{min-height:120px;resize:vertical}
form.kirjoita input:focus,form.kirjoita textarea:focus{outline:2px solid var(--accent);border-color:transparent}
form.kirjoita button{justify-self:start;padding:12px 22px;border:0;border-radius:12px;background:var(--accent);color:#fff;font:600 15px/1 Inter,system-ui,sans-serif;cursor:pointer}
.ansa{position:absolute;left:-9999px}
.huom{font:13px/1.5 Inter,system-ui,sans-serif;color:var(--muted)}
footer{padding:30px 0 50px;color:var(--muted);font:13.5px/1.6 Inter,system-ui,sans-serif;text-align:center}
.laskuri{display:inline-block;margin-bottom:8px;padding:6px 14px;border-radius:999px;background:var(--chip);border:1px solid var(--line);font-weight:600;color:var(--fg)}
@media (max-width:560px){body{font-size:18px}article.kirjoitus,.kommentit{padding:26px 20px;border-radius:18px}article.kirjoitus h1{font-size:31px}.lista article{padding:22px 20px}.lista h2{font-size:23px}header.top a.nimi{font-size:29px}}
"""

JS = """
const P=location.pathname;const $=s=>document.querySelector(s);
const pvm=t=>{const d=new Date(t);return d.toLocaleDateString('fi-FI')+' klo '+d.toLocaleTimeString('fi-FI',{hour:'2-digit',minute:'2-digit'})};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function nayta(t){if(!t)return;const k=$('#kavijat');if(k)k.textContent=t.kavijat.toLocaleString('fi-FI');
 if(t.jaot)for(const [kan,n] of Object.entries(t.jaot)){const e=document.querySelector('[data-kanava="'+kan+'"] .n');if(e)e.textContent=n}
 if(t.lukijat!=null&&$('#lukijat'))$('#lukijat').textContent=t.lukijat+' lukijaa';
 if(t.lukijat_kirjoituksittain)document.querySelectorAll('[data-polku]').forEach(e=>{const l=t.lukijat_kirjoituksittain[e.dataset.polku]||0,c=(t.kommentit_kirjoituksittain||{})[e.dataset.polku]||0;e.textContent=l+' lukijaa · '+c+' kommenttia'})}
fetch('/api/tilastot?polku='+encodeURIComponent(P)).then(r=>r.json()).then(nayta).catch(()=>{});
(function(){let id='';try{id=localStorage.getItem('bk_id')||'';if(!id){id=(crypto.randomUUID?crypto.randomUUID():String(Math.random()).slice(2)+Date.now());localStorage.setItem('bk_id',id)}}catch(e){}
 let aika=0,toimi=false,lahti=false;const tarkista=()=>{if(!lahti&&aika>=5&&toimi){lahti=true;fetch('/api/kaynti?polku='+encodeURIComponent(P)+'&id='+encodeURIComponent(id),{method:'POST'}).then(r=>r.json()).then(nayta).catch(()=>{})}};
 setInterval(()=>{if(document.visibilityState==='visible'){aika++;tarkista()}},1000);
 ['scroll','touchstart','pointerdown','keydown','wheel'].forEach(e=>addEventListener(e,()=>{toimi=true;tarkista()},{passive:true,once:true}));})();
const U=location.origin+P,T=document.title;
const osoitteet={facebook:'https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(U),x:'https://x.com/intent/post?url='+encodeURIComponent(U)+'&text='+encodeURIComponent(T),whatsapp:'https://wa.me/?text='+encodeURIComponent(T+' '+U),telegram:'https://t.me/share/url?url='+encodeURIComponent(U)+'&text='+encodeURIComponent(T)};
document.querySelectorAll('[data-kanava]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.kanava;
 if(k==='linkki'){navigator.clipboard&&navigator.clipboard.writeText(U);b.querySelector('.t').textContent='Kopioitu!'}else window.open(osoitteet[k],'_blank','noopener');
 fetch('/api/jaa?kanava='+k+'&polku='+encodeURIComponent(P),{method:'POST'}).then(r=>r.json()).then(nayta).catch(()=>{})}));
const lista=$('#kommenttilista');
function piirra(k){return '<div class="kommentti"><b>'+esc(k.nimi)+'</b> <span class="meta">· '+pvm(k.aika)+'</span><p>'+esc(k.teksti)+'</p></div>'}
if(lista){fetch('/api/kommentit?polku='+encodeURIComponent(P)).then(r=>r.json()).then(d=>{lista.innerHTML=d.kommentit.length?d.kommentit.map(piirra).join(''):'<p class="huom">Ei vielä kommentteja. Ole ensimmäinen!</p>';$('#kommlkm').textContent=d.kommentit.length});
 $('form.kirjoita').addEventListener('submit',async e=>{e.preventDefault();const f=e.target,b=f.querySelector('button'),v=$('#viesti');b.disabled=true;v.textContent='';
  try{const r=await fetch('/api/kommentit?polku='+encodeURIComponent(P),{method:'POST',body:JSON.stringify({nimi:f.nimi.value,teksti:f.teksti.value,kotisivu:f.kotisivu.value})});const d=await r.json();
   if(d.kommentti){if(lista.querySelector('.huom'))lista.innerHTML='';lista.insertAdjacentHTML('beforeend',piirra(d.kommentti));f.teksti.value='';$('#kommlkm').textContent=+$('#kommlkm').textContent+1;v.textContent='Kiitos kommentistasi!'}else v.textContent=d.virhe||'Kommentointi ei onnistunut.'}catch{v.textContent='Kommentointi ei onnistunut.'}b.disabled=false})}
"""


def sivu(otsikko, kuvaus, runko, polku="/", tyyppi="website"):
    url = (OSOITE + polku) if OSOITE else polku
    t = html.escape(otsikko)
    k = html.escape(kuvaus)
    return f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title><meta name="description" content="{k}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{k}">
<meta property="og:type" content="{tyyppi}"><meta property="og:url" content="{url}"><meta property="og:locale" content="fi_FI">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{html.escape(NIMI)}" href="/rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><div class="merkki">MK</div><br><a class="nimi" href="/">{html.escape(NIMI)}</a><p>{html.escape(KUVAUS)}</p></div></header>
<main><div class="wrap">{runko}</div></main>
<footer><div class="wrap"><span class="laskuri">👁 <span id="kavijat">–</span> kävijää</span><br>© {TANAAN.year} {html.escape(NIMI)} · Kirjoitukset ovat kirjoittajan omia näkemyksiä · <a href="/rss.xml">RSS</a></div></footer>
<script>{JS}</script>
</body></html>"""


def kirjoita(polku, sisalto):
    p = os.path.join(ULOS, polku.strip("/"), "index.html") if not polku.endswith(".xml") else os.path.join(ULOS, polku.strip("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(sisalto)


def main():
    if os.path.exists(ULOS):
        shutil.rmtree(ULOS)
    os.makedirs(ULOS)
    kk = lue()
    lista = "".join(
        f'<article><div class="meta">{pvm_teksti(k["pvm"])} · {k["min"]} min lukuaika</div><h2><a href="/{k["polku"]}/">{html.escape(k["otsikko"])}</a></h2>'
        + (f'<p>{html.escape(k["tiiv"])}</p>' if k["tiiv"] else "")
        + f'<div class="meta"><a class="lue" href="/{k["polku"]}/">Lue kirjoitus →</a> &nbsp; <span data-polku="/{k["polku"]}/"></span></div></article>' for k in kk)
    kirjoita("/", sivu(NIMI, KUVAUS, f'<section class="lista">{lista or "<p>Ensimmäinen kirjoitus tulossa pian.</p>"}</section>'))
    for k in kk:
        p = f'/{k["polku"]}/'
        napit = "".join(f'<button type="button" data-kanava="{k}"><span class="t">{t}</span> <span class="n">0</span></button>' for k, t in
                        [("facebook", "Facebook"), ("x", "X"), ("whatsapp", "WhatsApp"), ("telegram", "Telegram"), ("linkki", "Kopioi linkki")])
        jaa = f'<div class="jaa"><p class="otsake ui">Jaa kirjoitus</p><div class="napit">{napit}</div></div>'
        tekija = ('<div class="kirjoittaja"><div class="merkki">MK</div><p><b>Miika Koskela</b><br>'
                  'Kirjoittaa yhteiskunnasta, islamista, Euroopasta ja Suomen tulevaisuudesta.</p></div>')
        kommentit = ('<section class="kommentit"><h2>Kommentit (<span id="kommlkm">0</span>)</h2>'
                     '<p class="huom">Kommentoi ilman kirjautumista. Asiattomat ja lainvastaiset kommentit poistetaan.</p>'
                     '<div id="kommenttilista"><p class="huom">Ladataan…</p></div>'
                     '<form class="kirjoita"><input name="nimi" maxlength="40" placeholder="Nimi tai nimimerkki (vapaaehtoinen)">'
                     '<textarea name="teksti" maxlength="2000" required placeholder="Kirjoita kommenttisi…"></textarea>'
                     '<input class="ansa" name="kotisivu" tabindex="-1" autocomplete="off">'
                     '<button type="submit">Lähetä kommentti</button><div id="viesti" class="huom" aria-live="polite"></div></form></section>')
        runko = (f'<article class="kirjoitus"><div class="meta">{pvm_teksti(k["pvm"])} · {k["min"]} min lukuaika · <span id="lukijat"></span></div>'
                 f'<h1>{html.escape(k["otsikko"])}</h1><div class="meta">Kirjoittanut {html.escape(NIMI)}</div>'
                 f'<div class="sisalto">{k["html"]}</div>{jaa}{tekija}</article>{kommentit}'
                 f'<p class="meta" style="margin-top:26px;text-align:center"><a href="/">← Kaikki kirjoitukset</a></p>')
        kirjoita(p, sivu(f'{k["otsikko"]} – {NIMI}', k["tiiv"] or KUVAUS, runko, p, "article"))
    items = "".join(
        f"<item><title>{html.escape(k['otsikko'])}</title><link>{OSOITE}/{k['polku']}/</link>"
        f"<guid>{OSOITE}/{k['polku']}/</guid><pubDate>{k['pvm'].strftime('%a, %d %b %Y')} 06:00:00 +0200</pubDate>"
        f"<description>{html.escape(k['tiiv'])}</description></item>" for k in kk)
    kirjoita("/rss.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{html.escape(NIMI)}</title>'
             f'<link>{OSOITE}/</link><description>{html.escape(KUVAUS)}</description><language>fi</language>{items}</channel></rss>')
    kirjoita("/404", sivu(f"Sivua ei löytynyt – {NIMI}", KUVAUS, '<h1>Sivua ei löytynyt</h1><p><a href="/">Etusivulle</a></p>'))
    shutil.move(os.path.join(ULOS, "404", "index.html"), os.path.join(ULOS, "404.html"))
    os.rmdir(os.path.join(ULOS, "404"))
    print("julkaistu", len(kk), "kirjoitusta:", [k["polku"] for k in kk])


if __name__ == "__main__":
    main()
