// Toimituksen hyväksyntäjono: luonnokset luetaan, tarkistetaan lähteestä ja julkaistaan tai hylätään.
export function toimitusSivu(KATEGORIAT) {
  return String.raw`<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex">
<title>Toimitus | Suomi Tänään</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,600;6..72,700&family=Public+Sans:wght@400;500;600;700&display=swap">
<style>
/* Toimitus: kapea työpöytä puhelimelle. Kortti = yksi juttu, toiminnot kortin alareunassa. */
:root{--bg:#eef1f5;--paper:#fff;--ink:#121722;--mute:#5d6778;--line:#dfe4ec;--acc:#123f8c;--acc-soft:#e6edfa;--ok:#11734f;--ok-soft:#e3f4ec;--bad:#b42318;--warn-soft:#fff6e0;--warn:#8a5a00;
--serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,-apple-system,Segoe UI,sans-serif;--r:14px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0b0f16;--paper:#141b26;--ink:#e9edf4;--mute:#9ba6b9;--line:#253042;--acc:#8fb2ff;--acc-soft:#1a2740;--ok:#5fd3a2;--ok-soft:#14302a;--bad:#ff8a80;--warn-soft:#2e2614;--warn:#f0c46a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0b0f16;--paper:#141b26;--ink:#e9edf4;--mute:#9ba6b9;--line:#253042;--acc:#8fb2ff;--acc-soft:#1a2740;--ok:#5fd3a2;--ok-soft:#14302a;--bad:#ff8a80;--warn-soft:#2e2614;--warn:#f0c46a;color-scheme:dark}
[hidden]{display:none!important}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--sans)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--paper)}
.yla{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--paper);border-bottom:1px solid var(--line)}
.yla .s{max-width:720px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;padding-block:12px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.logo{font:700 21px/1 var(--serif);letter-spacing:-.01em}.logo b{color:var(--acc)}.logo small{font:600 12px var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--mute);margin-left:8px}
.ulos{font:600 13px var(--sans);color:var(--mute);background:none;border:0;cursor:pointer}
.s2{max-width:720px;margin:0 auto;padding-block:16px 80px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.vlehdet{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:4px;margin-bottom:16px}
.vlehdet button{font:600 13px var(--sans);border:0;border-radius:9px;padding:9px 4px;background:none;color:var(--mute);cursor:pointer;line-height:1.2}
.vlehdet button.on{background:var(--acc);color:var(--paper)}.vlehdet .n{display:block;font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}
.kortti{background:var(--paper);border:1px solid var(--line);border-radius:var(--r);margin-bottom:16px;overflow:hidden}
.kortti .sis{padding:16px;display:grid;gap:10px}
.chipit{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chip{font:700 11px var(--sans);letter-spacing:.08em;text-transform:uppercase;padding:4px 8px;border-radius:999px;background:var(--acc-soft);color:var(--acc)}
.chip.h{background:none;color:var(--mute);padding-inline:0;letter-spacing:.02em;text-transform:none;font-weight:500;font-size:13px}
.kortti h2{font:700 23px/1.2 var(--serif);margin:2px 0 0;text-wrap:balance}
.nayta{display:grid;gap:8px}.ingr{font-size:17px;color:var(--mute);margin:0}
.teksti{white-space:pre-wrap;font-size:16px;margin:0;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
.teksti.auki{display:block}
.linkki{font:600 14px var(--sans);color:var(--acc);background:none;border:0;padding:0;cursor:pointer;justify-self:start}
.lahde{display:flex;gap:10px;align-items:flex-start;background:var(--bg);border-radius:10px;padding:10px 12px;font-size:14px}
.lahde a{color:var(--acc);font-weight:600;text-decoration:none;overflow-wrap:anywhere}.lahde .i{font-weight:700;color:var(--mute);white-space:nowrap}
.tark{background:var(--warn-soft);border-radius:10px;padding:10px 12px}
.tark b{display:block;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--warn);margin-bottom:6px}
.tark label{display:flex;gap:8px;align-items:flex-start;font-size:14px;margin:4px 0;cursor:pointer}.tark input{margin-top:3px;accent-color:var(--ok);width:16px;height:16px;flex:0 0 auto}
.toim{display:grid;grid-template-columns:1fr auto auto;gap:8px;padding:12px 16px;border-top:1px solid var(--line);background:var(--paper)}
.nappi{font:700 15px var(--sans);padding:12px 16px;border-radius:10px;border:1px solid var(--line);background:var(--paper);color:var(--ink);cursor:pointer}
.nappi.p{background:var(--ok);border-color:var(--ok);color:#fff}.nappi.s{background:var(--acc);border-color:var(--acc);color:var(--paper)}.nappi.v{color:var(--bad);border-color:transparent;background:none}
.nappi:disabled{opacity:.5}
.lomake{display:grid;gap:10px}.lomake label{display:grid;gap:4px;font:700 12px var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
input,textarea,select{font:16px/1.5 var(--sans);padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);width:100%;text-transform:none;letter-spacing:0;font-weight:400}
textarea{min-height:100px;resize:vertical}textarea.pitka{min-height:300px}
.tt-koukku{font:700 20px/1.3 var(--serif);margin:0}.tt-teksti{white-space:pre-wrap;margin:0}
.tyhja{background:var(--paper);border:1px dashed var(--line);border-radius:var(--r);padding:32px 20px;text-align:center;color:var(--mute)}
.tyhja b{display:block;color:var(--ink);font:700 19px var(--serif);margin-bottom:6px}
.kirj{max-width:380px;margin:12vh auto 0;background:var(--paper);border:1px solid var(--line);border-radius:var(--r);padding:24px;display:grid;gap:14px}
.kirj h1{font:700 26px var(--serif);margin:0}.kirj p{margin:0;color:var(--mute);font-size:15px}
.ilmo{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:10px 18px;border-radius:999px;font-weight:600;z-index:20}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
</style></head><body>
<form class="kirj" id="kirj"><h1>Suomi Tänään</h1><p>Kirjaudu toimitukseen.</p><input id="pw" type="password" autocomplete="current-password" placeholder="Salasana"><button class="nappi s">Kirjaudu</button></form>
<div id="app" hidden>
<div class="yla"><div class="s"><div class="logo">Suomi <b>Tänään</b><small>Toimitus</small></div><button class="ulos" id="ulos">Kirjaudu ulos</button></div></div>
<div class="s2"><div class="vlehdet" role="tablist">
<button data-v="luonnokset" class="on"><span class="n" id="n-l">–</span>Luonnokset</button>
<button data-v="tiktok"><span class="n" id="n-t">–</span>TikTok</button>
<button data-v="julkaistut"><span class="n" id="n-j">–</span>Julkaistut</button>
<button data-v="paakirjoitus"><span class="n">+</span>Pääkirjoitus</button></div>
<div id="sisalto"></div></div></div>
<div class="ilmo" id="ilmo" hidden></div>
<script>
const KAT=${JSON.stringify(KATEGORIAT)};let PW="";try{PW=sessionStorage.getItem("pw")||""}catch(x){}
const $=s=>document.querySelector(s),e=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let LUONN=[],JULK=[],nakyma="luonnokset";
function ilmo(t){const i=$("#ilmo");i.textContent=t;i.hidden=false;clearTimeout(ilmo.t);ilmo.t=setTimeout(()=>i.hidden=true,2400)}
function sitten(iso){const m=Math.round((Date.now()-new Date(iso))/6e4);return m<60?m+" min sitten":m<1440?Math.round(m/60)+" h sitten":new Date(iso).toLocaleDateString("fi-FI")}
async function api(p,b){const r=await fetch(p,{method:b?"POST":"GET",headers:{authorization:"Bearer "+PW,"content-type":"application/json"},body:b?JSON.stringify(b):undefined});
 if(r.status==401){ulos();throw new Error("Väärä salasana")}return r.json()}
function ulos(){PW="";try{sessionStorage.removeItem("pw")}catch(x){}$("#app").hidden=true;$("#kirj").hidden=false}
$("#ulos").onclick=ulos;
$("#kirj").onsubmit=async ev=>{ev.preventDefault();PW=$("#pw").value;try{await lataa();try{sessionStorage.setItem("pw",PW)}catch(x){}alku()}catch(x){ilmo(x.message)}};
document.querySelectorAll(".vlehdet button").forEach(b=>b.onclick=()=>{nakyma=b.dataset.v;document.querySelectorAll(".vlehdet button").forEach(x=>x.classList.toggle("on",x==b));piirra()});
async function lataa(){[LUONN,JULK]=await Promise.all([api("/api/luonnokset"),api("/api/julkaistut")]);$("#n-l").textContent=LUONN.length;$("#n-t").textContent=LUONN.filter(x=>x.tiktok).length;$("#n-j").textContent=JULK.length}
function alku(){$("#kirj").hidden=true;$("#app").hidden=false;piirra()}
function kopioi(t){try{navigator.clipboard.writeText(t).then(()=>ilmo("Kopioitu"),()=>ilmo("Kopiointi ei onnistunut"))}catch(x){ilmo("Kopiointi ei onnistunut")}}
const lyhyt=t=>/äänestys/i.test(t||"")?"Äänestys":/tiedote/i.test(t||"")?"Tiedote":"Lähde";
function lahteet(x){return (x.lahteet||[]).map(a=>'<div class=lahde><span class=i>Lähde</span><a href="'+e(a.url)+'" target=_blank rel=noopener>'+e(a.nimi||a.url)+' ↗</a></div>').join("")}
function kortti(x){
 const tark=(x.tarkistettavat||[]).length?'<div class=tark><b>Tarkista lähteestä</b>'+x.tarkistettavat.map((t,i)=>'<label><input type=checkbox id="t'+e(x.id)+i+'"><span>'+e(t)+'</span></label>').join("")+'</div>':"";
 return '<article class=kortti data-id="'+e(x.id)+'"><div class=sis><div class=chipit><span class=chip>'+lyhyt(x.lahdetyyppi)+'</span><span class=chip>'+e(x.kategoria)+'</span><span class="chip h">'+sitten(x.luotu)+'</span></div>'+
 '<div class=nayta><h2>'+e(x.otsikko)+'</h2><p class=ingr>'+e(x.ingressi)+'</p><p class=teksti>'+e(x.teksti)+'</p><button class=linkki data-a=lue>Lue koko teksti</button></div>'+
 '<div class=lomake hidden><label>Otsikko<input name=otsikko value="'+e(x.otsikko)+'"></label><label>Ingressi<textarea name=ingressi>'+e(x.ingressi)+'</textarea></label><label>Teksti<textarea name=teksti class=pitka>'+e(x.teksti)+'</textarea></label><label>Osasto<select name=kategoria>'+KAT.map(k=>'<option'+(k==x.kategoria?" selected":"")+'>'+k+'</option>').join("")+'</select></label></div>'+
 lahteet(x)+tark+'</div><div class=toim><button class="nappi p" data-a=julkaise>Julkaise</button><button class=nappi data-a=muokkaa>Muokkaa</button><button class="nappi v" data-a=hylkaa>Hylkää</button></div></article>'}
async function piirra(){const s=$("#sisalto");
 if(nakyma=="paakirjoitus"){s.innerHTML='<article class=kortti><div class="sis lomake"><label>Otsikko<input id=po></label><label>Ingressi<textarea id=pi></textarea></label><label>Teksti (kappaleet tyhjällä rivillä erotettuina)<textarea id=pt class=pitka></textarea></label></div><div class=toim style="grid-template-columns:1fr"><button class="nappi p" id=pj>Julkaise pääkirjoitus</button></div></article>';
  $("#pj").onclick=async()=>{const d={tyyppi:"paakirjoitus",otsikko:$("#po").value.trim(),ingressi:$("#pi").value,teksti:$("#pt").value,kategoria:"Pääkirjoitus",lahteet:[]};if(!d.otsikko||!d.teksti.trim())return ilmo("Otsikko ja teksti tarvitaan");const r=await api("/api/julkaise",d);if(r.ok){ilmo("Julkaistu");location.href="/uutiset/"+r.slug+"/"}else ilmo("Julkaisu epäonnistui")};return}
 if(nakyma=="julkaistut"){s.innerHTML=JULK.length?JULK.map(x=>'<article class=kortti><div class=sis><div class=chipit><span class=chip>'+e(x.tyyppi=="paakirjoitus"?"Pääkirjoitus":x.kategoria)+'</span><span class="chip h">'+sitten(x.julkaistu)+'</span></div><h2><a href="/uutiset/'+e(x.slug)+'/" target=_blank style="color:inherit;text-decoration:none">'+e(x.otsikko)+' ↗</a></h2></div><div class=toim style="grid-template-columns:1fr"><button class="nappi v" data-p="'+e(x.slug)+'">Poista julkaisusta</button></div></article>').join(""):'<div class=tyhja><b>Ei vielä julkaistuja juttuja</b>Julkaistut jutut näkyvät tässä.</div>';
  s.querySelectorAll("[data-p]").forEach(b=>b.onclick=async()=>{if(b.dataset.ok!="1"){b.dataset.ok="1";b.textContent="Vahvista poisto";return}await api("/api/poista",{slug:b.dataset.p});ilmo("Poistettu julkaisusta");await lataa();piirra()});return}
 if(nakyma=="tiktok"){const t=LUONN.filter(x=>x.tiktok);s.innerHTML=t.length?t.map(x=>'<article class=kortti><div class=sis><div class=chipit><span class=chip>Ohjaa: '+e(x.tiktok.sivusto||"Suomi Tänään")+'</span></div><p class=tt-koukku>'+e(x.tiktok.koukku)+'</p><p class=tt-teksti>'+e(x.tiktok.teksti)+'</p><span class="chip h">Juttu: '+e(x.otsikko)+'</span></div><div class=toim style="grid-template-columns:1fr"><button class="nappi s" data-k="'+e(x.id)+'">Kopioi käsikirjoitus</button></div></article>').join(""):'<div class=tyhja><b>Ei käsikirjoituksia</b>Uudet tulevat luonnosten mukana joka päivä.</div>';
  s.querySelectorAll("[data-k]").forEach(b=>b.onclick=()=>{const x=LUONN.find(y=>y.id==b.dataset.k);kopioi(x.tiktok.koukku+"\n\n"+x.tiktok.teksti)});return}
 s.innerHTML=LUONN.length?LUONN.map(kortti).join(""):'<div class=tyhja><b>Jono on tyhjä</b>Uudet luonnokset tulevat joka päivä noin klo 12.20.</div>';
 s.querySelectorAll(".kortti").forEach(k=>k.querySelectorAll("[data-a]").forEach(b=>b.onclick=async()=>{const id=k.dataset.id,a=b.dataset.a,x=LUONN.find(y=>y.id==id);
  if(a=="lue"){const t=k.querySelector(".teksti");t.classList.toggle("auki");b.textContent=t.classList.contains("auki")?"Näytä vähemmän":"Lue koko teksti";return}
  if(a=="muokkaa"){const f=k.querySelector(".lomake"),n=k.querySelector(".nayta");f.hidden=!f.hidden;n.hidden=!f.hidden;b.textContent=f.hidden?"Muokkaa":"Esikatsele";return}
  if(a=="hylkaa"){if(b.dataset.ok!="1"){b.dataset.ok="1";b.textContent="Vahvista";return}await api("/api/hylkaa",{id});ilmo("Hylätty");await lataa();piirra();return}
  const v=n=>k.querySelector("[name="+n+"]").value;
  b.disabled=true;const r=await api("/api/julkaise",{id,tyyppi:"uutinen",otsikko:v("otsikko"),ingressi:v("ingressi"),teksti:v("teksti"),kategoria:v("kategoria"),lahteet:x.lahteet});
  if(r.ok){ilmo("Julkaistu");await lataa();piirra()}else{ilmo("Julkaisu epäonnistui");b.disabled=false}}))}
if(PW)lataa().then(alku,()=>{});
</script></body></html>`;
}
