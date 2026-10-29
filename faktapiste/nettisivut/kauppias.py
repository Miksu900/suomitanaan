"""Netvo "Puhuva kauppias": tekoälyavustaja, joka vastaa kauppiaan äänellä ja ottaa tilauksen vastaan puhumalla.
Käyttö: premium.page() lisää tämän, jos kaupan datassa on "kauppias"-avain. Taustapalvelu: faktapiste/src/index.js /api/kauppias."""
import json
from html import escape as esc

CSS = r"""
.kp-intro{padding:28px 0 6px}.kp-intro .box{display:grid;grid-template-columns:auto 1fr auto;gap:20px;align-items:center;background:linear-gradient(135deg,var(--card),var(--soft));border:1px solid var(--line);border-radius:calc(var(--r) + 6px);padding:22px 26px;box-shadow:0 18px 50px -30px rgba(0,0,0,.35)}
.kp-intro .av{width:74px;height:74px;font-size:40px}.kp-intro h2{margin:0 0 4px;font-size:clamp(1.3rem,3vw,1.75rem)}.kp-intro p{margin:0;color:var(--muted)}
.kp-intro .new{display:inline-block;background:var(--acc);color:var(--ink);font:700 .7rem/1 var(--fb);letter-spacing:.08em;text-transform:uppercase;padding:5px 9px;border-radius:99px;margin-bottom:8px}
@media(max-width:720px){.kp-intro .box{grid-template-columns:auto 1fr;padding:18px}.kp-intro .box .btn{grid-column:1/-1;width:100%;justify-content:center}.kp-intro .av{width:58px;height:58px;font-size:30px}}
.av{display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,var(--soft));border:2px solid var(--acc2);position:relative;flex:none}
.av.live::after{content:"";position:absolute;inset:-6px;border-radius:50%;border:2px solid var(--acc2);animation:kpring 1.8s ease-out infinite}
@keyframes kpring{from{transform:scale(.9);opacity:.9}to{transform:scale(1.35);opacity:0}}
.kp-fab{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:60;display:flex;align-items:center;gap:10px;background:var(--text);color:#fff;border:0;border-radius:99px;padding:8px 18px 8px 8px;font:600 .95rem var(--fb);box-shadow:0 14px 40px -12px rgba(0,0,0,.5);cursor:pointer}
.kp-fab .av{width:42px;height:42px;font-size:22px}.kp-fab small{display:block;font-weight:400;opacity:.75;font-size:.72rem;text-align:left}
.kp-fab.hide{display:none}
.kp{position:fixed;z-index:70;right:16px;bottom:16px;width:min(410px,calc(100% - 32px));height:min(640px,calc(100dvh - 32px));background:var(--card);border:1px solid var(--line);border-radius:calc(var(--r) + 6px);box-shadow:0 30px 80px -20px rgba(0,0,0,.45);display:flex;flex-direction:column;overflow:hidden;transform:translateY(20px) scale(.98);opacity:0;pointer-events:none;transition:.25s}
.kp.open{transform:none;opacity:1;pointer-events:auto}
@media(max-width:600px){.kp{right:0;bottom:0;width:100%;height:88dvh;border-radius:22px 22px 0 0}}
.kp-h{display:flex;gap:12px;align-items:center;padding:14px 16px;border-bottom:1px solid var(--line);background:var(--bg)}
.kp-h .av{width:46px;height:46px;font-size:24px}.kp-h b{font-family:var(--fh);font-size:1.1rem;display:block}.kp-h span{font-size:.78rem;color:var(--muted)}
.kp-h button{margin-left:auto;background:none;border:0;font-size:26px;line-height:1;color:var(--muted);cursor:pointer;padding:6px}
.kp-log{flex:1;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth}
.kp-m{max-width:86%;padding:10px 14px;border-radius:18px;line-height:1.45;font-size:.97rem;animation:kpin .25s ease}
@keyframes kpin{from{opacity:0;transform:translateY(6px)}}
.kp-m.a{align-self:flex-end;background:var(--acc);color:var(--ink);border-bottom-right-radius:6px}
.kp-m.k{align-self:flex-start;background:var(--soft);border-bottom-left-radius:6px}
.kp-m .play{background:none;border:0;cursor:pointer;font-size:.8rem;color:var(--acc);font-weight:700;padding:4px 0 0;display:block}
.kp-dots{align-self:flex-start;background:var(--soft);border-radius:18px;padding:12px 16px}.kp-dots i{display:inline-block;width:7px;height:7px;margin:0 2px;border-radius:50%;background:var(--muted);animation:kpd 1s infinite}.kp-dots i:nth-child(2){animation-delay:.15s}.kp-dots i:nth-child(3){animation-delay:.3s}
@keyframes kpd{50%{transform:translateY(-5px);opacity:.4}}
.kp-ps{display:flex;gap:8px;overflow-x:auto;align-self:stretch;padding-bottom:2px}
.kp-p{flex:none;width:132px;background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:8px;font-size:.82rem}
.kp-p img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px;background:var(--soft)}.kp-p b{display:block;margin:6px 0 2px;line-height:1.25}
.kp-p button{width:100%;margin-top:6px;border:0;border-radius:99px;background:var(--text);color:#fff;padding:7px;font:600 .8rem var(--fb);cursor:pointer}
.kp-ok{align-self:stretch;background:#e8f4ea;border:1px solid #b9dcc0;color:#1e5b2b;border-radius:14px;padding:10px 12px;font-size:.9rem}
.kp-ok div{display:flex;gap:8px;margin-top:8px}.kp-ok button{flex:1;border-radius:99px;padding:8px;font:600 .85rem var(--fb);cursor:pointer;border:1px solid #1e5b2b;background:#fff;color:#1e5b2b}.kp-ok button.go{background:#1e5b2b;color:#fff}
.kp-chips{display:flex;gap:8px;overflow-x:auto;padding:0 16px 10px}
.kp-chips button{flex:none;border:1px solid var(--line);background:var(--bg);border-radius:99px;padding:8px 12px;font:500 .84rem var(--fb);color:var(--text);cursor:pointer}
.kp-f{border-top:1px solid var(--line);padding:12px 14px calc(12px + env(safe-area-inset-bottom));display:flex;gap:10px;align-items:center;background:var(--bg)}
.kp-mic{flex:none;width:58px;height:58px;border-radius:50%;border:0;background:var(--acc);color:var(--ink);cursor:pointer;display:grid;place-items:center;box-shadow:0 8px 20px -8px var(--acc);transition:.2s}
.kp-mic svg{width:26px;height:26px}.kp-mic.on{background:#d33;box-shadow:0 0 0 0 rgba(221,51,51,.5);animation:kpmic 1.2s infinite}
@keyframes kpmic{70%{box-shadow:0 0 0 16px rgba(221,51,51,0)}}
.kp-f form{flex:1;display:flex;gap:6px;min-width:0}.kp-f input{flex:1;min-width:0;border:1px solid var(--line);border-radius:99px;padding:12px 14px;font:1rem var(--fb);background:var(--card);color:var(--text)}
.kp-f form button{border:0;background:none;font-size:1.3rem;cursor:pointer;color:var(--acc);padding:0 6px}
.kp-note{font-size:.72rem;color:var(--muted);text-align:center;padding:0 16px 8px}
"""

def html(k):
    n = esc(k["nimi"]); r = esc(k["rooli"]); a = k.get("avatar", "👨‍🍳")
    mic = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>'
    intro = f"""<section class="kp-intro"><div class="w"><div class="box"><span class="av live">{a}</span><div><span class="new">Uutta</span><h2>Tilaa puhumalla – {r.lower()} {n} vastaa</h2><p>Kysy suosituksia tai sano vain, mitä haluat. {n} laittaa tuotteet koriin puolestasi ja vastaa omalla äänellään.</p></div><button class="btn" data-kp>🎙️ Puhu {n}lle</button></div></div></section>"""
    pane = f"""<button class="kp-fab" data-kp aria-label="Tilaa puhumalla"><span class="av live">{a}</span><span>Tilaa puhumalla<small>{r} {n} vastaa</small></span></button>
<div class="kp" id="kp" role="dialog" aria-label="Puhu {r.lower()}lle"><div class="kp-h"><span class="av">{a}</span><div><b>{r} {n}</b><span>🤖 Tekoälyavustaja · vastaa ääneen</span></div><button data-kpx aria-label="Sulje">×</button></div>
<div class="kp-log" id="kplog" aria-live="polite"></div>
<div class="kp-chips" id="kpchips">{''.join(f'<button>{esc(c)}</button>' for c in k["vinkit"])}</div>
<div class="kp-note">Esimerkkikaupassa kuuluu valmis tekoälyääni. Omassa kaupassasi avustaja puhuu <b>sinun omalla äänelläsi</b>.</div>
<div class="kp-f"><button class="kp-mic" id="kpmic" aria-label="Puhu">{mic}</button><form id="kpform"><input id="kpin" placeholder="Puhu tai kirjoita…" autocomplete="off" maxlength="300"><button aria-label="Lähetä">➤</button></form></div></div>"""
    return intro, pane

JS = r"""(function(){var K=window.KAUPPIAS,NV=window.NV;if(!K||!NV)return;
function $(s){return document.querySelector(s)}function esc(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
var kp=$('#kp'),log=$('#kplog'),inp=$('#kpin'),mic=$('#kpmic'),hist=[],busy=false,au=new Audio(),greeted=false;
function scroll(){log.scrollTop=log.scrollHeight}
function msg(r,t,a){var d=document.createElement('div');d.className='kp-m '+r;d.textContent=t;if(a){var b=document.createElement('button');b.className='play';b.textContent='🔊 Kuuntele uudelleen';b.onclick=function(){au.src=a;au.play()};d.appendChild(b)}log.appendChild(d);scroll();return d}
function open(){kp.classList.add('open');$('.kp-fab').classList.add('hide');if(!greeted){greeted=true;msg('k',K.tervehdys)}setTimeout(function(){if(!SR)inp.focus()},250)}
function close(){kp.classList.remove('open');$('.kp-fab').classList.remove('hide');try{au.pause()}catch(e){}stopRec()}
document.addEventListener('click',function(e){if(e.target.closest('[data-kp]')){e.preventDefault();open()}if(e.target.closest('[data-kpx]'))close()});
function pcard(id){var p=NV.P.find(function(x){return x.id===id});if(!p)return '';return '<div class="kp-p"><img src="'+NV.img(p)+'" alt=""><b>'+esc(p.name)+'</b>'+(p.cake?'alk. ':'')+NV.eur(p.price)+'<button data-kpadd="'+p.id+'">'+(p.cake?'Valitse kakku':'+ Lisää koriin')+'</button></div>'}
log.addEventListener('click',function(e){var b=e.target.closest('[data-kpadd]');if(b){var id=+b.dataset.kpadd,p=NV.P.find(function(x){return x.id===id});if(p.cake){close();NV.avaa(id);return}NV.lisaa(id,1);b.textContent='✓ Lisätty';b.disabled=true}
if(e.target.closest('[data-kpcart]')){close();NV.kori()}if(e.target.closest('[data-kpco]')){close();NV.kassa()}});
function send(t){t=(t||'').trim();if(!t||busy)return;busy=true;inp.value='';msg('a',t);try{au.pause()}catch(e){}
var dots=document.createElement('div');dots.className='kp-dots';dots.innerHTML='<i></i><i></i><i></i>';log.appendChild(dots);scroll();
fetch(K.api,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({kauppa:K.kauppa,viesti:t,historia:hist,kori:NV.cart().map(function(l){return{id:l.id,q:l.q}})})})
.then(function(r){return r.json()}).then(function(o){dots.remove();var v=o.vastaus||'Anteeks, nyt ei onnistunut. Kokeile uudestaan.';msg('k',v,o.aani);hist.push({r:'a',t:t},{r:'k',t:v});hist=hist.slice(-6);
if(o.aani){au.src=o.aani;var pr=au.play();if(pr&&pr.catch)pr.catch(function(){})}
if(o.lisaa&&o.lisaa.length){var names=o.lisaa.map(function(x){var p=NV.P.find(function(y){return y.id===x.id});NV.lisaa(x.id,x.q);return x.q+' × '+p.name});
var d=document.createElement('div');d.className='kp-ok';d.innerHTML='✓ Lisätty koriin: <b>'+esc(names.join(', '))+'</b><div><button data-kpcart>Näytä kori</button><button class="go" data-kpco>Kassalle →</button></div>';log.appendChild(d)}
var ids=(o.nayta||[]).filter(function(i){return !(o.lisaa||[]).some(function(x){return x.id===i})});if(o.avaa&&ids.indexOf(o.avaa)<0)ids.unshift(o.avaa);
if(ids.length){var c=document.createElement('div');c.className='kp-ps';c.innerHTML=ids.map(pcard).join('');log.appendChild(c)}
if(o.kassalle&&NV.cart().length){setTimeout(function(){close();NV.kassa()},1800)}scroll()})
.catch(function(){dots.remove();msg('k','Yhteys katkesi hetkeksi. Kokeile uudestaan.')}).then(function(){busy=false})}
$('#kpform').addEventListener('submit',function(e){e.preventDefault();send(inp.value)});
$('#kpchips').addEventListener('click',function(e){var b=e.target.closest('button');if(b)send(b.textContent)});
var SR=window.SpeechRecognition||window.webkitSpeechRecognition,rec=null,heard='';
function stopRec(){if(rec){try{rec.stop()}catch(e){}}}
if(!SR){mic.style.display='none'}else{mic.addEventListener('click',function(){if(rec){stopRec();return}try{au.pause()}catch(e){}
rec=new SR();rec.lang='fi-FI';rec.interimResults=true;rec.continuous=false;heard='';mic.classList.add('on');inp.placeholder='Kuuntelen… puhu nyt';
rec.onresult=function(e){var t='';for(var i=0;i<e.results.length;i++)t+=e.results[i][0].transcript;heard=t;inp.value=t};
rec.onerror=function(e){if(e.error==='not-allowed')msg('k','Salli mikrofoni selaimen asetuksista, niin voit puhua. Voit myös kirjoittaa.')};
rec.onend=function(){mic.classList.remove('on');inp.placeholder='Puhu tai kirjoita…';rec=null;if(heard.trim())send(heard)};
try{rec.start()}catch(e){mic.classList.remove('on');rec=null}})}
})();"""

def lisaa(k, kauppa):
    """Palauttaa (css, intro_html, pane_html, script_html)."""
    intro, pane = html(k)
    cfg = {"api": k.get("api", "/api/kauppias"), "kauppa": kauppa, "tervehdys": k["tervehdys"]}
    script = f"<script>window.KAUPPIAS={json.dumps(cfg, ensure_ascii=False)};</script><script>{JS}</script>"
    return CSS, intro, pane, script
