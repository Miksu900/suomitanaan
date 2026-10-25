# -*- coding: utf-8 -*-
"""Rakentaa Netvon 4 viikon julkaisukalenterin HTML-sivuksi (kopioi-napeilla)."""
import html, pathlib
from netvo_sisalto import kalenteri

VIIKONPAIVA = {0: "Ma", 1: "Ti", 2: "Ke", 3: "To", 4: "Pe", 5: "La", 6: "Su"}
TEEMANIMI = {
 "sininen": "Perusviesti", "vihrea": "Reiluus", "oranssi": "Hyöty",
 "musta": "Tekniikka", "viininpunainen": "Ajankohta", "petroli": "Löydettävyys",
 "ruskea": "Mallisivu", "purppura": "Mallisivu",
}
esc = html.escape
rivit = kalenteri()

def kortti(r):
    vp = VIIKONPAIVA[r["pvm"].weekday()]
    pvm = r["pvm"].strftime("%d.%m.")
    koko = r["teksti"] + "\n\n" + r["tagit"]
    return f"""<article class="kortti" data-vari="{r['vari']}">
  <header class="kortti-yla">
    <div class="pvm"><span class="vp">{vp}</span><span class="pv">{pvm}</span></div>
    <div class="meta"><span class="aika">🕐 {r['aika']}</span><span class="teema">{esc(TEEMANIMI[r['vari']])}</span></div>
    <span class="nro">#{r['nro']:02d}</span>
  </header>
  <div class="teksti" data-copy="{esc(koko)}">{esc(r['teksti'])}</div>
  <div class="tagit">{esc(r['tagit'])}</div>
  <footer class="kortti-ala">
    <span class="kuva">🖼 {r['kuva']}</span>
    <button class="kopioi" type="button">Kopioi julkaisu</button>
  </footer>
</article>"""

viikot = ""
for vk in range(4):
    osa = rivit[vk*7:(vk+1)*7]
    alku = osa[0]["pvm"].strftime("%d.%m.")
    loppu = osa[-1]["pvm"].strftime("%d.%m.")
    kortit = "\n".join(kortti(r) for r in osa)
    viikot += f"""<section class="viikko">
  <h2>Viikko {vk+1} <span class="vali">{alku}–{loppu}</span></h2>
  <div class="ruudukko">{kortit}</div>
</section>"""

SISALTO = f"""<meta name="claude:viewport-fit-sides" content="cover">
<title>Netvon julkaisukalenteri</title>
<style>
/* Layout: brändätty otsikko + viikoittain ryhmitellyt kopioitavat korttiruudukot */
:root {{
  --bg:#f4f6fb; --paper:#ffffff; --ink:#15181f; --mute:#5c6372; --line:#e4e8f0;
  --sin:#1557c0; --sin2:#0e3a85; --vihr:#1f7a4d; --pehmea:#eaf1fd;
  --varjo:0 1px 3px rgba(16,32,64,.06),0 6px 18px rgba(16,32,64,.05);
  --f-otsikko:'Poppins',system-ui,sans-serif; --f-leipa:'Inter',system-ui,sans-serif;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bg:#0d1016; --paper:#161b24; --ink:#eef1f6; --mute:#9aa3b3; --line:#283040;
  --sin:#5b93f0; --sin2:#3f78dd; --vihr:#4fb584; --pehmea:#1a2434;
  --varjo:0 1px 3px rgba(0,0,0,.4); color-scheme:dark;
}}}}
:root[data-theme="dark"]{{
  --bg:#0d1016; --paper:#161b24; --ink:#eef1f6; --mute:#9aa3b3; --line:#283040;
  --sin:#5b93f0; --sin2:#3f78dd; --vihr:#4fb584; --pehmea:#1a2434;
  --varjo:0 1px 3px rgba(0,0,0,.4); color-scheme:dark;
}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-leipa);line-height:1.5}}
.wrap{{max-width:1120px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0}}
h1,h2,h3{{font-family:var(--f-otsikko);line-height:1.15;text-wrap:balance;margin:0}}
a{{color:var(--sin)}}

.hero{{background:linear-gradient(135deg,var(--sin),var(--sin2));color:#fff;border-radius:0 0 22px 22px}}
.hero .wrap{{padding-block:34px 30px}}
.brand{{font-family:var(--f-otsikko);font-weight:800;font-size:1.6rem;letter-spacing:-.01em}}
.brand i{{font-style:normal;color:#9fe6c2}}
.hero h1{{font-size:clamp(1.5rem,4.5vw,2.3rem);margin:.5rem 0 .4rem;color:#fff}}
.hero p{{margin:0;max-width:60ch;color:#dce7fb;font-size:1.02rem}}
.ohje{{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px}}
.ohje span{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);padding:7px 13px;border-radius:999px;font-size:.84rem;font-weight:600}}

.viikko{{margin-top:30px}}
.viikko h2{{font-size:1.25rem;display:flex;align-items:baseline;gap:10px;margin-bottom:14px}}
.viikko h2 .vali{{font-family:var(--f-leipa);font-weight:600;color:var(--mute);font-size:.92rem}}
.ruudukko{{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}}

.kortti{{background:var(--paper);border:1px solid var(--line);border-radius:16px;box-shadow:var(--varjo);padding:16px;display:flex;flex-direction:column;gap:12px;border-top:4px solid var(--sin);min-width:0}}
.kortti[data-vari="vihrea"]{{border-top-color:var(--vihr)}}
.kortti[data-vari="oranssi"]{{border-top-color:#d9631a}}
.kortti[data-vari="musta"]{{border-top-color:#444}}
.kortti[data-vari="viininpunainen"]{{border-top-color:#9c2742}}
.kortti[data-vari="petroli"]{{border-top-color:#116b74}}
.kortti[data-vari="ruskea"]{{border-top-color:#7a5230}}
.kortti[data-vari="purppura"]{{border-top-color:#5b3a9c}}
.kortti-yla{{display:flex;align-items:center;gap:10px}}
.pvm{{display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--pehmea);color:var(--sin);border-radius:10px;width:50px;height:50px;flex:none}}
.pvm .vp{{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em}}
.pvm .pv{{font-size:.95rem;font-weight:800;font-variant-numeric:tabular-nums}}
.meta{{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1}}
.meta .aika{{font-size:.84rem;color:var(--mute);font-variant-numeric:tabular-nums}}
.meta .teema{{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--vihr)}}
.nro{{font-family:var(--f-otsikko);font-weight:800;color:var(--line);font-size:1.1rem;flex:none}}
.teksti{{white-space:pre-wrap;font-size:.95rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px;min-width:0;overflow-wrap:break-word}}
.tagit{{font-size:.82rem;color:var(--sin);font-weight:600;overflow-wrap:break-word}}
.kortti-ala{{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:auto}}
.kuva{{font-size:.82rem;color:var(--mute);font-variant-numeric:tabular-nums}}
.kopioi{{font-family:var(--f-leipa);font-weight:700;font-size:.88rem;background:var(--sin);color:#fff;border:none;border-radius:9px;padding:9px 16px;cursor:pointer;transition:background .15s}}
.kopioi:hover{{background:var(--sin2)}}
.kopioi.ok{{background:var(--vihr)}}
.kopioi:focus-visible{{outline:3px solid var(--sin);outline-offset:2px}}

footer.loppu{{margin:40px 0 10px;text-align:center;color:var(--mute);font-size:.85rem}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>

<div class="hero"><div class="wrap">
  <div class="brand">Net<i>vo</i></div>
  <h1>4 viikon julkaisukalenteri</h1>
  <p>Yksi julkaisu päivässä (28 kpl). Kopioi teksti, liitä kuva ja ajasta Meta Business Suitessa. Kuvat ovat erillisessä zip-paketissa samoilla numeroilla.</p>
  <div class="ohje"><span>1 · Kopioi julkaisu</span><span>2 · Liitä sama kuva (netvo-NN.png)</span><span>3 · Ajasta Business Suitessa</span></div>
</div></div>

<div class="wrap">
{viikot}
<footer class="loppu">Netvo · netvo.fi · Julkaisut saa vapaasti muokata omaan ääneesi sopivaksi.</footer>
</div>

<script>
document.querySelectorAll('.kopioi').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    var teksti = btn.closest('.kortti').querySelector('.teksti').getAttribute('data-copy');
    function ok(){{ var v=btn.textContent; btn.textContent='Kopioitu ✓'; btn.classList.add('ok');
      setTimeout(function(){{btn.textContent=v; btn.classList.remove('ok');}},1600); }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(teksti).then(ok).catch(function(){{ valitse(btn); }});
    }} else {{ valitse(btn); }}
  }});
}});
function valitse(btn){{
  var el = btn.closest('.kortti').querySelector('.teksti');
  var r = document.createRange(); r.selectNodeContents(el);
  var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
}}
</script>"""

out = pathlib.Path("/tmp/claude-0/-home-claude/b142e595-80d2-56b7-a839-92763a6d395f/scratchpad/netvo-kalenteri.html")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(SISALTO, encoding="utf-8")
print("Kirjoitettu:", out, len(SISALTO), "merkkiä")
