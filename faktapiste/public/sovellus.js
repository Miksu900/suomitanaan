// Faktapiste-keskustelu: syöte, kirjoittaminen, Kysy fakta, ketjut.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var LAHTEET = {
    suomitanaan: { nimi: "Suomi Tänään", lyh: "ST", vari: "#b4232c", url: "https://suomitanaan.fi", palvelu: "Lue lisää uutisia Suomi Tänään -sivulta" },
    korjausvahti: { nimi: "Korjausvahti", lyh: "KV", vari: "#7a4cc2", url: "https://nytpuhutaan.fi/muutokset/", palvelu: "Katso kaikki otsikkomuutokset Korjausvahdista" },
    eduskunta: { nimi: "Eduskunta", lyh: "§", vari: "#1d5fd1", url: "https://eduskuntaseuranta.fi" },
    faktapiste: { nimi: "Faktapiste", lyh: "F", vari: "#0f2a4a", url: "/palvelut/", palvelu: "Avaa Yksityisyysvahti" },
    keraysvahti: { nimi: "Keräysvahti", lyh: "!", vari: "#c26a00", url: "https://keraysvahti.fi", palvelu: "Tarkista keräys tai epäilyttävä viesti Keräysvahdista" }
  };
  var IK = {
    vastaa: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H9l-5 4V5z"/></svg>',
    tykkaa: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>',
    jaa: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 14v6h14v-6"/></svg>'
  };
  var tila = { mina: null, kirjautuminen: true, tab: "sinulle", sivu: 0, fakta: null, ladataan: false, saato: [1, 1, 1, 1, 1], kunta: "", lukija: "", syyt: {} };
  function lue(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function tallenna(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  tila.tab = ["sinulle", "seuratut", "uusimmat", "lahella"].indexOf(lue("fp_tab")) >= 0 ? lue("fp_tab") : "sinulle";
  tila.kunta = lue("fp_kunta") || "";
  (function () { var v = (lue("fp_saato") || "").split(",").map(Number); if (v.length === 5 && v.every(function (x) { return x >= 0 && x <= 2; })) tila.saato = v; })();
  // Lukijatunniste: satunnainen, vain lukukertojen laskemiseen (taattu yleisö ja syötteen loppuminen).
  tila.lukija = lue("fp_lukija") || "";
  if (!/^[a-f0-9]{32}$/.test(tila.lukija)) { var b = new Uint8Array(16); crypto.getRandomValues(b); tila.lukija = Array.prototype.map.call(b, function (x) { return ("0" + x.toString(16)).slice(-2); }).join(""); tallenna("fp_lukija", tila.lukija); }
  var LUOKAT = [["Keskustelut", "Ihmisten omat postaukset"], ["Uutiset", "Suomi Tänään"], ["Otsikkomuutokset", "Korjausvahti"], ["Huijausvaroitukset", "Keräysvahti"], ["Päätökset", "Eduskunnan äänestykset"]];

  function api(polku, data) {
    var o = data ? { method: "POST", headers: { "content-type": "application/json", "x-lukija": tila.lukija }, body: JSON.stringify(data), credentials: "same-origin", keepalive: polku === "nahty" } : { credentials: "same-origin", headers: { "x-lukija": tila.lukija } };
    return fetch("/api/" + polku, o).then(function (r) { return r.json().catch(function () { return { virhe: "Palvelin ei vastannut." }; }); });
  }
  function aika(ms) {
    var s = (Date.now() - ms) / 1000;
    if (s < 60) return "nyt";
    if (s < 3600) return Math.floor(s / 60) + " min";
    if (s < 86400) return Math.floor(s / 3600) + " t";
    if (s < 7 * 86400) return Math.floor(s / 86400) + " pv";
    return new Date(ms).toLocaleDateString("fi-FI");
  }
  function linkit(t) {
    t = String(t == null ? "" : t).replace(/\r/g, "").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
    return esc(t).replace(/https?:\/\/[^\s<]+/g, function (u) { return '<a href="' + u + '" rel="nofollow noopener ugc">' + u.replace(/^https?:\/\//, "").slice(0, 40) + (u.length > 48 ? "…" : "") + "</a>"; }).replace(/\n/g, "<br>");
  }
  function ilmoitus(t, virhe) {
    var el = $("#fp-toast"); el.textContent = t; el.className = "toast nakyy" + (virhe ? " virhe" : "");
    clearTimeout(el._t); el._t = setTimeout(function () { el.className = "toast"; }, 3800);
  }
  function pvm(s) { var d = s.split("-"); return d.length === 3 ? (+d[2]) + "." + (+d[1]) + "." + d[0] : s; }

  // ---------- kortit ----------
  function palkit(k) {
    var yht = Math.max(1, (k.jaa || 0) + (k.ei || 0) + (k.tyhja || 0) + (k.poissa || 0));
    var r = function (n, v, c) { return '<div class="pr"><span>' + n + '</span><span class="pb"><i class="' + c + '" style="width:' + (100 * v / yht).toFixed(1) + '%"></i></span><b>' + v + "</b></div>"; };
    return '<div class="palkit">' + r("Jaa", k.jaa || 0, "j") + r("Ei", k.ei || 0, "e") + r("Tyhjää", k.tyhja || 0, "t") + r("Poissa", k.poissa || 0, "p") + "</div>";
  }
  function ryhmat(k) {
    if (!k.ryhmat || !k.ryhmat.length) return "";
    return '<details class="ryhmat"><summary>Puolueittain</summary><table><thead><tr><th>Ryhmä</th><th>Jaa</th><th>Ei</th><th>Tyhjää</th><th>Poissa</th></tr></thead><tbody>' +
      k.ryhmat.map(function (g) { return "<tr><td>" + esc(g.r) + "</td><td>" + g.jaa + "</td><td>" + g.ei + "</td><td>" + g.tyhja + "</td><td>" + g.poissa + "</td></tr>"; }).join("") + "</tbody></table></details>";
  }
  function kortti(k) {
    if (!k) return "";
    if (k.tyyppi === "uutinen") return '<a class="kortti uutinen" href="' + esc(k.url) + '" rel="noopener"><span class="kl">' + esc(k.lahde) + "</span><strong>" + esc(k.otsikko) + "</strong>" + (k.kuvaus ? "<span>" + esc(k.kuvaus) + "</span>" : "") + "</a>";
    if (k.tyyppi === "muutos") return '<a class="kortti muutos" href="' + esc(k.url) + '" rel="noopener"><span class="kl">Otsikko muuttui · ' + esc(k.media) + mm(k) + '</span><span class="ennen"><em>Ennen</em>' + esc(k.ennen) + '</span><span class="nyt"><em>Nyt</em>' + esc(k.nyt) + "</span></a>";
    if (k.tyyppi === "varoitus") return '<a class="kortti varoitus" href="' + esc(k.url) + '" rel="noopener"><span class="kl">Huijausvaroitus · ' + esc(k.media) + mm(k) + "</span><strong>" + esc(k.otsikko) + "</strong></a>";
    if (k.tyyppi === "aanestys") return '<div class="kortti aanestys"><span class="kl">Eduskunnan äänestys' + (k.pv ? " · " + pvm(k.pv) : "") + "</span><strong>" + esc(k.otsikko) + "</strong>" +
      (k.lisaotsikko ? '<span class="lisa">' + esc(k.lisaotsikko) + "</span>" : "") + (k.tulos ? '<span class="tulos ' + (/Hyväks|Jaa/.test(k.tulos) ? "ok" : "no") + '">' + esc(k.tulos) + "</span>" : "") +
      palkit(k) + ryhmat(k) + '<a class="lue" href="' + esc(k.url) + '" rel="noopener">Katso edustajien äänet Eduskuntaseurannasta →</a></div>';
    if (k.tyyppi === "fakta") return '<div class="kortti fakta"><span class="kl">Fakta · Eduskuntaseuranta</span><span class="kys">' + esc(k.kysymys) + '</span><p>' + esc(k.vastaus) + "</p>" +
      (k.aanestys ? '<div class="fa"><strong>' + esc(k.aanestys.otsikko) + "</strong>" + palkit(k.aanestys) + ryhmat(k.aanestys) + "</div>" : "") +
      (k.lahteet && k.lahteet.length ? '<div class="lahteet">' + k.lahteet.slice(0, 3).map(function (s) { return '<a href="' + esc(s.url) + '" rel="noopener">' + esc(s.otsikko) + "</a>"; }).join("") + "</div>" : "") +
      '<small>Tekoälyn kokoama vastaus avoimesta datasta. Tarkista tärkeät asiat lähteestä.</small></div>';
    return "";
  }

  function mm(k) { return k.maksumuuri === true ? ' <span class="mmuuri" title="Uutinen on maksumuurin takana">🔒 Tilaajille</span>' : ""; }
  // ---------- kuvat ----------
  function kuvaGalleria(kuvat) {
    if (!kuvat || !kuvat.length) return "";
    return '<div class="kuvat n' + kuvat.length + '">' + kuvat.map(function (k) {
      return '<button type="button" class="kuva" data-kuva="' + k.id + '" aria-label="Avaa kuva"><img src="/api/kuva/' + k.id + '" alt="" loading="lazy"' + (k.w && k.h ? ' width="' + k.w + '" height="' + k.h + '"' : "") + "></button>"; }).join("") + "</div>";
  }
  function kuvaValitsin(kuvat) {
    return '<div class="kuvaesikatselu">' + (kuvat || []).map(esikatselu).join("") + "</div>";
  }
  function esikatselu(k) {
    return '<span class="ek' + (k.lataa ? " lataa" : "") + '" data-ek="' + k.avain + '"><img src="' + (k.url || "/api/kuva/" + k.id) + '" alt="">' + (k.lataa ? "<i></i>" : "") + '<button type="button" data-poistakuva="' + k.avain + '" aria-label="Poista kuva">×</button></span>';
  }
  // Pienentää kuvan selaimessa (pisin sivu 1600 px) ja tallentaa JPEG:ksi: sijaintitiedot ja muut metatiedot jäävät pois.
  function pienenna(tiedosto) {
    return new Promise(function (ok, ei) {
      var url = URL.createObjectURL(tiedosto), im = new Image();
      im.onload = function () {
        var max = 1600, s = Math.min(1, max / Math.max(im.naturalWidth, im.naturalHeight));
        var w = Math.max(1, Math.round(im.naturalWidth * s)), h = Math.max(1, Math.round(im.naturalHeight * s));
        var c = document.createElement("canvas"); c.width = w; c.height = h;
        var g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, w, h); g.drawImage(im, 0, 0, w, h);
        URL.revokeObjectURL(url);
        var laatu = 0.85;
        (function tee() { c.toBlob(function (b) { if (!b) return ei(new Error("Kuvaa ei voitu käsitellä.")); if (b.size > 1700000 && laatu > 0.5) { laatu -= 0.15; return tee(); } ok({ blob: b, w: w, h: h }); }, "image/jpeg", laatu); })();
      };
      im.onerror = function () { URL.revokeObjectURL(url); ei(new Error("Tätä kuvatiedostoa ei voi avata.")); };
      im.src = url;
    });
  }
  var kuvaLaskuri = 0;
  function lisaaKuvat(f, tiedostot) {
    f._kuvat = f._kuvat || [];
    var vapaa = 4 - f._kuvat.length;
    if (vapaa <= 0) return ilmoitus("Voit liittää enintään 4 kuvaa.", 1);
    Array.prototype.slice.call(tiedostot, 0, vapaa).forEach(function (t) {
      if (!/^image\//.test(t.type) && !/\.(jpe?g|png|webp|heic|heif|gif)$/i.test(t.name)) return ilmoitus("Valitse kuvatiedosto.", 1);
      var k = { avain: "k" + (++kuvaLaskuri), lataa: true, url: URL.createObjectURL(t) };
      f._kuvat.push(k); $(".kuvaesikatselu", f).insertAdjacentHTML("beforeend", esikatselu(k));
      pienenna(t).then(function (r) {
        return fetch("/api/kuva", { method: "POST", credentials: "same-origin", headers: { "content-type": "image/jpeg", "x-leveys": r.w, "x-korkeus": r.h }, body: r.blob }).then(function (x) { return x.json(); });
      }).then(function (j) {
        if (j.virhe) throw new Error(j.virhe);
        k.id = j.id; k.lataa = false; var el = $('[data-ek="' + k.avain + '"]', f); if (el) { el.classList.remove("lataa"); var i = $("i", el); if (i) i.remove(); }
      }).catch(function (e) {
        f._kuvat = f._kuvat.filter(function (x) { return x !== k; }); var el = $('[data-ek="' + k.avain + '"]', f); if (el) el.remove();
        ilmoitus(e.message || "Kuvan lataus epäonnistui.", 1);
      });
    });
  }
  function kuvatValmiit(f) { return !(f._kuvat || []).some(function (k) { return k.lataa; }); }
  function kuvaIdt(f) { return (f._kuvat || []).filter(function (k) { return k.id; }).map(function (k) { return k.id; }); }
  // ---------- videot ----------
  var VIDEONAPPI = '<label class="kuva-nappi" title="Lisää video"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3z"/></svg><span>Video</span><input type="file" name="videotiedosto" accept="video/mp4,video/quicktime,video/webm,video/*" hidden></label>';
  function videoSoitin(v) {
    if (!v) return "";
    return '<div class="video"><video controls playsinline preload="' + (v.kansi ? "none" : "metadata") + '" src="/api/video/' + v.id + '"' + (v.kansi ? ' poster="/api/video/' + v.id + '/kansi"' : "") +
      (v.w && v.h ? ' width="' + v.w + '" height="' + v.h + '"' : "") + "></video></div>";
  }
  // Lukee videon mitat ja keston sekä ottaa kansikuvan (JPEG) selaimessa. Ei koskaan jää jumiin:
  // jos puhelin ei suostu purkamaan videota, palautetaan se mitä saatiin (lataus ei odota tätä).
  function videoTiedot(t) {
    return new Promise(function (ok) {
      var url = URL.createObjectURL(t), v = document.createElement("video"), valmis = false, m = { w: 0, h: 0, kesto: 0, kansi: null };
      var lopeta = function () { if (valmis) return; valmis = true; try { v.removeAttribute("src"); v.load(); } catch (x) {} if (v.parentNode) v.remove(); URL.revokeObjectURL(url); ok(m); };
      v.muted = true; v.playsInline = true; v.preload = "auto"; v.setAttribute("playsinline", "");
      v.style.cssText = "position:fixed;left:-9999px;width:2px;height:2px;opacity:0"; document.body.appendChild(v);
      setTimeout(lopeta, 8000);
      v.onerror = lopeta;
      v.onloadedmetadata = function () { m.w = v.videoWidth; m.h = v.videoHeight; m.kesto = v.duration || 0; try { v.currentTime = Math.min(1, (v.duration || 2) / 3); } catch (x) { lopeta(); } };
      v.onseeked = function () {
        try {
          var s = Math.min(1, 1280 / Math.max(m.w, m.h, 1)), c = document.createElement("canvas");
          c.width = Math.round(m.w * s) || 320; c.height = Math.round(m.h * s) || 180;
          c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
          c.toBlob(function (kansi) { m.kansi = kansi; lopeta(); }, "image/jpeg", 0.82);
        } catch (x) { lopeta(); }
      };
      v.src = url;
    });
  }
  function lisaaVideo(f, t) {
    if (!tila.video) return ilmoitus("Videoiden lataus avautuu pian.", 1);
    if (f._video) return ilmoitus("Voit liittää yhden videon postausta kohden.", 1);
    if (t.size > 100 * 1024 * 1024) return ilmoitus("Video on liian suuri (enintään 100 Mt). Lyhennä videota tai tallenna se pienemmällä laadulla.", 1);
    var tyyppi = /^video\/(mp4|webm|quicktime)$/.test(t.type) ? t.type : /\.mov$/i.test(t.name) ? "video/quicktime" : /\.webm$/i.test(t.name) ? "video/webm" : "video/mp4";
    var vid = { lataa: true }; f._video = vid;
    $(".kuvaesikatselu", f).insertAdjacentHTML("beforeend", '<span class="ek video-ek lataa" data-ek="video"><span class="edistys">Ladataan video… 0 %</span><button type="button" data-poistavideo aria-label="Poista video">×</button></span>');
    var el = $('[data-ek="video"]', f), pros = $(".edistys", el), mb = (t.size / 1048576).toFixed(0);
    var poista = function (viesti) { if (vid.xhr && vid.lataa) try { vid.xhr.abort(); } catch (x) {} if (f._video === vid) f._video = null; if (el) el.remove(); if (viesti) ilmoitus(viesti, 1); };
    // Lataus alkaa heti; kansikuva ja mitat haetaan samaan aikaan.
    var x = new XMLHttpRequest(); vid.xhr = x;
    x.open("POST", "/api/video"); x.withCredentials = true; x.timeout = 15 * 60 * 1000;
    x.setRequestHeader("content-type", tyyppi);
    x.upload.onprogress = function (e) { if (e.lengthComputable && pros && vid.lataa) pros.textContent = "Ladataan video (" + mb + " Mt)… " + Math.round(100 * e.loaded / e.total) + " %"; };
    x.onerror = function () { poista("Videon lataus katkesi. Tarkista verkkoyhteys ja yritä uudelleen."); };
    x.ontimeout = function () { poista("Videon lataus kesti liian kauan. Kokeile lyhyempää videota tai parempaa yhteyttä."); };
    var tiedot = videoTiedot(t), kansiLahetetty = false;
    var lahetaKansi = function () {
      if (kansiLahetetty || !vid.id) return; tiedot.then(function (m) {
        if (kansiLahetetty || !m.kansi) return; kansiLahetetty = true;
        fetch("/api/video/kansi?id=" + vid.id, { method: "POST", credentials: "same-origin", headers: { "content-type": "image/jpeg" }, body: m.kansi });
      });
    };
    x.onload = function () {
      var j = {}; try { j = JSON.parse(x.responseText); } catch (er) {}
      if (j.virhe || !j.id) return poista(j.virhe || "Videon lataus epäonnistui (" + x.status + ").");
      vid.id = j.id; vid.lataa = false; el.classList.remove("lataa"); if (pros) pros.textContent = "✓ Video valmis";
      lahetaKansi();
    };
    tiedot.then(function (m) {
      if (f._video !== vid) return;
      if (m.kesto > 181) return poista("Video on liian pitkä (enintään 3 minuuttia).");
      if (m.kansi) el.insertAdjacentHTML("afterbegin", '<img src="' + URL.createObjectURL(m.kansi) + '" alt="">');
      lahetaKansi();
    });
    x.setRequestHeader("x-kesto", "0");
    x.send(t);
  }
  var KUVANAPPI = '<label class="kuva-nappi" title="Lisää kuva"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M21 16l-5-5-8 8"/></svg><span>Kuva</span><input type="file" name="kuvatiedosto" accept="image/*" multiple hidden></label>';

  // ---------- postaus ----------
  function pitka(t) { t = String(t || "").replace(/\n{3,}/g, "\n\n").trim(); return t.length > 420 || t.split("\n").length > 8; }
  function posti(p, iso) {
    var l = LAHTEET[p.lahde];
    var nimi = l ? l.nimi : p.nimi || "Käyttäjä";
    var av = l ? '<a class="av" href="' + l.url + '" rel="noopener" title="Avaa ' + esc(l.nimi) + '" style="background:' + l.vari + '">' + l.lyh + "</a>" : '<span class="av k">' + esc((p.nimi || "?").charAt(0).toUpperCase()) + "</span>";
    if (p.syy) tila.syyt[p.id] = p.syy;
    tila.tekstit = tila.tekstit || {}; tila.tekstit[p.id] = p.teksti;
    tila.postiKuvat = tila.postiKuvat || {}; tila.postiKuvat[p.id] = p.kuvat || [];
    var nak = p.nakymat || 0;
    var taattu = p.oma && !p.vanhempi && nak < (p.taattu || 30) ? '<div class="taattu"><span class="tpb"><i style="width:' + Math.min(100, 100 * nak / (p.taattu || 30)).toFixed(0) + '%"></i></span>Nähty ' + nak + "/" + (p.taattu || 30) + " · näytämme postauksesi vielä " + ((p.taattu || 30) - nak) + " ihmiselle</div>" : "";
    if (p.piilotettu) return '<article class="posti piilo" data-id="' + p.id + '"><p class="mute">Tämä postaus on poistettu tai piilotettu.</p></article>';
    return '<article class="posti' + (iso ? " iso" : "") + '" data-id="' + p.id + '">' + av + '<div class="pm"><header>' + (l ? '<a class="lahdelinkki" href="' + l.url + '" rel="noopener">' + esc(nimi) + " ↗</a>" : "<b>" + esc(nimi) + "</b>") + (l ? '<span class="auto">automaattinen</span>' : "") +
      (!l && p.kirjoittaja && !p.oma ? '<button type="button" class="seuraa' + (p.seuraan ? " on" : "") + '" data-seuraa="' + p.kirjoittaja + '" aria-pressed="' + !!p.seuraan + '">' + (p.seuraan ? "Seuraat" : "Seuraa") + "</button>" : "") + (p.kunta ? '<span class="paikka">📍 ' + esc(p.kunta) + "</span>" : "") +
      '<a class="aika" href="/?p=' + p.id + '" data-avaa="' + p.id + '">' + aika(p.luotu) + "</a>" + (p.muokattu ? '<span class="muokattu">muokattu</span>' : "") + "</header>" +
      (p.teksti ? '<div class="pt' + (!iso && pitka(p.teksti) ? " tiivis" : "") + '">' + linkit(p.teksti) + "</div>" + (!iso && pitka(p.teksti) ? '<button type="button" class="avaa-teksti" data-avaateksti>Näytä kokonaan</button>' : "") : "") + kuvaGalleria(p.kuvat) + videoSoitin(p.video) + kortti(p.kortti) + (l && l.palvelu ? '<a class="palvelulinkki" href="' + l.url + '" rel="noopener">' + esc(l.palvelu) + " →</a>" : "") + taattu +
      '<footer><button type="button" data-vastaa="' + p.id + '" aria-label="Vastaa">' + IK.vastaa + "<span>" + (p.vastaukset || "Vastaa") + '</span></button>' +
      '<button type="button" data-tykkaa="' + p.id + '" class="' + (p.tykkasin ? "on" : "") + '" aria-label="Tykkää">' + IK.tykkaa + "<span>" + (p.tykkaykset || "") + "</span></button>" +
      '<button type="button" data-jaa="' + p.id + '" aria-label="Jaa">' + IK.jaa + "<span>Jaa</span></button>" +
      '<span class="luettu" title="Näin moni on nähnyt postauksen">👁 ' + nak + "</span>" +
      '<button type="button" data-lisaa="' + p.id + '" aria-label="Lisää toimintoja" data-oma="' + (p.oma ? 1 : 0) + '">⋯</button></footer></div></article>';
  }

  // ---------- kirjoituslaatikko ----------
  function kirjoitus(vanhempi) {
    var id = vanhempi ? "v" : "u";
    if (!tila.mina) {
      if (!tila.kirjautuminen) return '<div class="kirjoita lukko"><b>Keskustelu on beta-testissä.</b><span>Kirjoittaminen avautuu kaikille pian. Voit jo lukea syötettä.</span></div>';
      return '<div class="kirjoita lukko"><b>' + (vanhempi ? "Kirjaudu vastataksesi." : "Mitä mieltä olet? Kirjaudu ja kirjoita.") + '</b><span>Kirjautuminen sähköpostilinkillä, ei salasanaa.</span><button type="button" class="nappi" data-kirjaudu>Kirjaudu</button></div>';
    }
    if (!tila.mina.nimiOk) return '<form class="kirjoita" id="nimilomake"><b>Kirjoita oma nimesi</b><span>Faktapisteessä keskustellaan omalla nimellä. Etu- ja sukunimesi näkyvät postaustesi yhteydessä. Sähköpostiosoitetta ei näytetä kenellekään.' + (tila.mina.nimi ? " Nimimerkit on vaihdettu oikeisiin nimiin." : "") + '</span><div class="rivi"><input name="nimi" maxlength="60" placeholder="Etunimi Sukunimi" autocomplete="name" required><button class="nappi">Tallenna</button></div></form>';
    return '<form class="kirjoita" data-lomake="' + id + '"' + (vanhempi ? ' data-vanhempi="' + vanhempi + '"' : "") + '>' +
      '<textarea name="teksti" rows="' + (vanhempi ? 2 : 3) + '" placeholder="' + (vanhempi ? "Kirjoita vastaus" : "Mitä mielessä? Jokainen postaus näytetään vähintään 30 ihmiselle.") + '"></textarea>' +
      kuvaValitsin() +
      '<div class="faktapaneeli" hidden><div class="rivi"><input name="kysymys" maxlength="300" placeholder="Kysy vapaasti, esim. miten perussuomalaiset äänesti kotihoidontuesta?"><button type="button" class="nappi toissijainen" data-hae>Hae</button></div><div class="faktatulos"></div></div>' +
      '<div class="toiminnot">' + KUVANAPPI + (tila.video && !vanhempi ? VIDEONAPPI : "") + '<button type="button" class="fakta-nappi" data-fakta>🔎 Kysy fakta</button>' + (tila.kunta && !vanhempi ? '<label class="paikkavalinta"><input type="checkbox" name="kunta" checked> 📍 ' + esc(tila.kunta) + "</label>" : "") + '<span class="laskuri"></span><button class="nappi">' + (vanhempi ? "Vastaa" : "Julkaise") + "</button></div></form>";
  }

  // ---------- näkymät ----------
  var SYOTE = $("#fp-syote"), KIRJ = $("#fp-kirjoita"), TABIT = $("#fp-tabit");
  function piirraArvonta() {
    var A = $("#fp-arvonta"); if (!A) return;
    api("arvonta").then(function (j) {
      if (!j || !j.kaynnissa) { A.innerHTML = ""; return; }
      var kk = j.arvonnat.filter(function (a) { return !a.tasot; })[0], iso = j.arvonnat.filter(function (a) { return a.tasot; })[0];
      var omat = j.arvonnat[0].omat, oma = j.yllapitaja ? "Ylläpitäjänä et osallistu." : omat === null ? "Kirjaudu ja kirjoita, niin olet mukana." : "Sinulla on nyt <b>" + omat + " " + (omat === 1 ? "arpa" : "arpaa") + "</b>.";
      var h = '<div class="arvonta"><span class="arv-ik" aria-hidden="true">🎁</span><div>';
      if (kk) h += "<b>Arvomme 100 € rahana tai lahjakorttina " + esc(kk.arvontaPv.replace(/\.20\d\d$/, ".")) + "</b>";
      h += "<p>Jokainen kirjoitus ja kommentti on arpa, ja kaverin kutsusta saat " + (j.kutsuArvat || 10) + " lisäarpaa. " + oma + "</p>";
      if (iso) {
        var max = iso.seuraava ? iso.seuraava.min : iso.tasot[iso.tasot.length - 1].min, pros = Math.min(100, 100 * iso.kayttajia / max);
        h += '<div class="iso-arv"><b>Iso arvonta ' + esc(iso.arvontaPv.replace(/\.20\d\d$/, ".")) + ": nyt " + iso.nyt + " €</b>" +
          '<span class="mittari" role="img" aria-label="' + iso.kayttajia + " / " + max + ' käyttäjää"><i style="width:' + pros.toFixed(1) + '%"></i></span>' +
          "<small>Meitä on " + iso.kayttajia + " / " + max + "." + (iso.seuraava ? " Kun meitä on " + iso.seuraava.min + ", palkinto nousee " + iso.seuraava.summa + " euroon." : "") + " Kutsu kaverit mukaan!</small></div>";
      }
      A.innerHTML = h + '<div class="kutsu-arv" id="fp-kutsuarv"></div><a class="arv-saannot" href="/arvonta/">Lue säännöt →</a></div></div>';
      if (tila.mina && tila.mina.nimiOk && !j.yllapitaja) api("kutsulinkki").then(function (k) {
        var K = $("#fp-kutsuarv"); if (!K || !k || !k.url) return;
        K.innerHTML = "<b>Kutsu kaverit: +" + k.arvatPerKaveri + " arpaa jokaisesta</b><small>Saat lisäarvat, kun kaveri liittyy linkilläsi ja kirjoittaa kahtena eri päivänä. Kavereiden määrää ei ole rajoitettu. " +
          (k.kutsutut ? "Olet kutsunut " + k.kutsutut + ", joista " + k.kirjoittaneet + " on jo tuonut sinulle arvat." : "") + "</small>" +
          '<div class="rivi"><input readonly value="' + esc(k.url) + '" aria-label="Oma kutsulinkki"><button type="button" class="nappi" data-kutsujako="' + esc(k.url) + '">Jaa</button></div>';
      });
    });
  }
  function piirraTabit() {
    TABIT.innerHTML = [["sinulle", "Sinulle"], ["seuratut", "Seuratut"], ["uusimmat", "Uusimmat"], ["lahella", tila.kunta ? "📍 " + tila.kunta : "📍 Lähellä"]].map(function (t) {
      return '<button type="button" role="tab" aria-selected="' + (tila.tab === t[0]) + '" data-tab="' + t[0] + '">' + esc(t[1]) + "</button>"; }).join("") +
      '<button type="button" class="saato-nappi" data-avaasaato aria-label="Säädä syötettä" title="Säädä syötettä">⚙</button>';
  }
  function lataaSyote(lisaa) {
    if (tila.ladataan) return; tila.ladataan = true;
    if (!lisaa) { tila.sivu = 0; SYOTE.innerHTML = '<p class="lataa">Ladataan…</p>'; }
    api("syote?tab=" + tila.tab + "&sivu=" + tila.sivu + "&s=" + tila.saato.join(",") + "&kunta=" + encodeURIComponent(tila.kunta)).then(function (j) {
      tila.ladataan = false;
      var vanha = $(".lisaa-nappi", SYOTE); if (vanha) vanha.remove();
      if (!lisaa) SYOTE.innerHTML = "";
      if (j.virhe) { SYOTE.innerHTML = '<p class="lataa">' + esc(j.virhe) + "</p>"; return; }
      if (j.kuntaPuuttuu) { SYOTE.innerHTML = kuntaValitsin("Valitse paikkakuntasi, niin näet sen keskustelut ja uutiset."); return; }
      if (!j.postit.length && !lisaa && !j.loppu) SYOTE.innerHTML = '<p class="lataa">' + (tila.tab === "lahella" ? "Paikkakunnaltasi ei ole vielä postauksia. Aloita sinä!" : tila.tab === "seuratut" ? (j.kirjauduSeuraa ? "Kirjaudu, niin voit seurata muita kirjoittajia." : j.seurattuja ? "Seuraamasi kirjoittajat eivät ole vielä kirjoittaneet." : "Et seuraa vielä ketään. Paina Seuraa-nappia kirjoittajan nimen vieressä.") : "Syöte täyttyy pian.") + "</p>";
      SYOTE.insertAdjacentHTML("beforeend", j.postit.map(function (p) { return posti(p); }).join(""));
      if (j.loppu) SYOTE.insertAdjacentHTML("beforeend", '<div class="loppu"><span class="ok">✓</span><b>Olet nähnyt kaiken tärkeän.</b><p>' + (j.tanaan ? "Luit tänään " + j.tanaan + " postausta. " : "") + "Syöte ei jatku loputtomiin. Tule myöhemmin takaisin, niin täällä on taas uutta.</p><button type=\"button\" class=\"nappi toissijainen\" data-uusimmat>Selaa silti uusimpia</button></div>");
      havainnoi();
      if (j.lisaa) SYOTE.insertAdjacentHTML("beforeend", '<button type="button" class="nappi toissijainen lisaa-nappi" data-lisaasivu>Näytä lisää</button>');
    });
  }
  function avaaKetju(id, push) {
    if (push) history.pushState({ p: id }, "", "/?p=" + id);
    $("#fp-paa").hidden = true; var K = $("#fp-ketju"); K.hidden = false; K.innerHTML = '<p class="lataa">Ladataan…</p>';
    window.scrollTo(0, 0);
    api("posti/" + id).then(function (j) {
      if (j.virhe) { K.innerHTML = '<button type="button" class="takaisin" data-takaisin>← Takaisin</button><p class="lataa">' + esc(j.virhe) + "</p>"; return; }
      K.innerHTML = '<button type="button" class="takaisin" data-takaisin>← Takaisin syötteeseen</button>' + (j.vanhempi ? '<div class="vanhempi">' + posti(j.vanhempi) + "</div>" : "") + posti(j.posti, true) +
        '<div class="ketju-kirj">' + kirjoitus(j.posti.id) + '</div><h2 class="vast">Vastaukset (' + j.vastaukset.length + ")</h2>" +
        (j.vastaukset.length ? j.vastaukset.map(function (p) { return posti(p); }).join("") : '<p class="lataa">Ei vielä vastauksia.</p>');
      havainnoi();
    });
  }
  function suljeKetju(push) {
    if (push) history.pushState({}, "", "/");
    $("#fp-ketju").hidden = true; $("#fp-paa").hidden = false;
  }
  function piirraKirjoitus() { KIRJ.innerHTML = kirjoitus(null); }
  function mina() {
    return api("mina").then(function (j) {
      tila.mina = j.kayttaja; tila.video = j.video === true; tila.tilasto = j.tilasto || null; tila.kirjautuminen = j.kirjautuminen === true;
      // Testivaihe: kirjautumisnappi näkyy vain osoitteella /?testi=1 avattuna (muistetaan selaimessa).
      var kq = (location.search.match(/[?&]kutsu=([a-f0-9]{6,20})/) || [])[1]; if (kq) tallenna("fp_kutsu", kq);
      var sq = (location.search.match(/[?&]k=([a-z0-9]{6})/) || [])[1]; if (sq && !lue("fp_suos")) tallenna("fp_suos", sq);
      if (j.testi && lue("fp_kutsu")) tila.kirjautuminen = true;
      if (j.testi) { var t = /[?&]testi=1/.test(location.search); try { if (t) localStorage.setItem("fp_testi", "1"); t = t || localStorage.getItem("fp_testi") === "1"; } catch (x) {} if (t) tila.kirjautuminen = true; }
      var a = $("#fp-tili");
      if (a) a.innerHTML = tila.mina ? '<button type="button" class="tili" data-tilivalikko aria-haspopup="true" aria-expanded="false">' + esc((tila.mina.nimi || "Oma tili").split(" ")[0]) + ' <span aria-hidden="true">▾</span></button>' : tila.kirjautuminen ? '<button type="button" class="tili" data-kirjaudu>Kirjaudu</button>' : "";
      piirraKirjoitus();
    });
  }

  // ---------- säätimet ja paikkakunta ----------
  var kunnat = null;
  function kuntaValitsin(teksti) {
    if (!kunnat) fetch("/kunnat.json").then(function (r) { return r.json(); }).then(function (k) { kunnat = k; var dl = $("#kunnat"); if (dl) dl.innerHTML = k.map(function (x) { return '<option value="' + esc(x) + '">'; }).join(""); });
    return '<div class="kuntavalinta"><b>' + esc(teksti) + '</b><div class="rivi"><input id="kunta-input" list="kunnat" placeholder="esim. Ylivieska" value="' + esc(tila.kunta) + '" autocomplete="off"><button type="button" class="nappi" data-kuntavalinta>Valitse</button></div><datalist id="kunnat">' + (kunnat || []).map(function (x) { return '<option value="' + esc(x) + '">'; }).join("") + "</datalist></div>";
  }
  function asetaKunta(v) {
    v = String(v || "").trim();
    var ok = function (lista) { var m = lista.filter(function (x) { return x.toLowerCase() === v.toLowerCase(); })[0]; if (!m && v) return ilmoitus("Valitse paikkakunta listasta.", 1); tila.kunta = m || ""; tallenna("fp_kunta", tila.kunta); piirraTabit(); piirraKirjoitus(); if (tila.tab === "lahella") lataaSyote(); avaaSaato(true); ilmoitus(m ? "Paikkakunta: " + m : "Paikkakunta poistettu."); };
    if (kunnat) ok(kunnat); else fetch("/kunnat.json").then(function (r) { return r.json(); }).then(function (k) { kunnat = k; ok(k); });
  }
  function avaaSaato(paivita) {
    var S = $("#fp-saato"); if (paivita && S.hidden) return; S.hidden = false;
    S.innerHTML = '<div class="saato-otsikko"><b>Sinä päätät, mitä näet</b><button type="button" class="linkki" data-suljesaato>Sulje</button></div>' +
      LUOKAT.map(function (l, i) { return '<div class="saato-rivi"><span><b>' + l[0] + "</b><small>" + l[1] + '</small></span><span class="seg">' +
        ["Pois", "Normaali", "Enemmän"].map(function (n, t) { return '<button type="button" data-luokka="' + i + '" data-taso="' + t + '" aria-pressed="' + (tila.saato[i] === t) + '">' + n + "</button>"; }).join("") + "</span></div>"; }).join("") +
      kuntaValitsin("Paikkakuntasi (Lähellä-syöte ja postausten sijainti)") +
      '<p class="pieni mute">Asetukset tallentuvat vain tähän selaimeen. Sinulle-syöte näyttää vain sellaista, mitä et ole vielä nähnyt, ja loppuu, kun tärkeät on katsottu.</p>';
  }
  // Nähdyt postaukset: lasketaan, kun postaus on ollut ruudulla sekunnin.
  var jono = [], ajastimet = {}, laheta = null;
  var tarkkailija = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var id = e.target.getAttribute("data-id"); if (!id) return;
      if (e.isIntersecting) { if (!ajastimet[id]) ajastimet[id] = setTimeout(function () { jono.push(+id); tarkkailija.unobserve(e.target); clearTimeout(laheta); laheta = setTimeout(tyhjenna, 2500); }, 1000); }
      else { clearTimeout(ajastimet[id]); delete ajastimet[id]; }
    });
  }, { threshold: 0.5 }) : null;
  function havainnoi() { if (tarkkailija) document.querySelectorAll(".posti[data-id]:not([data-h])").forEach(function (a) { a.setAttribute("data-h", "1"); tarkkailija.observe(a); }); }
  function tyhjenna() { if (!jono.length) return; var idt = jono.splice(0); api("nahty", { idt: idt }); }
  document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") tyhjenna(); });

  // ---------- kirjautumisikkuna ----------
  var DLG = $("#fp-kirjaudu");
  function avaaKirjautuminen() {
    DLG.innerHTML = '<form method="dialog" class="dlg" id="kirjform"><h2>Kirjaudu Faktapisteeseen</h2><p>Saat sähköpostiisi kirjautumislinkin. Salasanaa ei tarvita, ja sama linkki luo tilin, jos sinulla ei vielä ole sitä.</p>' +
      '<label>Sähköposti<input type="email" name="email" required autocomplete="email"></label><p class="pieni">Kirjautumalla hyväksyt <a href="/tietoa/#keskustelu">keskustelun säännöt ja tietosuojan</a>.</p>' +
      '<p class="ehto">Kirjoitukset ja kommentit ovat mukana Faktapisteen arvonnoissa. Osallistumalla hyväksyt <a href="/arvonta/" target="_blank" rel="noopener">arvonnan säännöt</a>.</p>' +
      '<div class="rivi"><button type="button" class="nappi toissijainen" data-sulje>Peruuta</button><button class="nappi" value="laheta">Lähetä linkki</button></div></form>';
    DLG.showModal();
  }

  // ---------- tapahtumat ----------
  document.addEventListener("click", function (e) {
    var avoin = $(".tilivalikko"); if (avoin && !e.target.closest(".tilivalikko, [data-tilivalikko]")) { avoin.remove(); var tb = $("[data-tilivalikko]"); if (tb) tb.setAttribute("aria-expanded", "false"); }
    var b = e.target.closest("button, a[data-avaa]"); if (!b) {
      var art = e.target.closest(".posti"); if (art && !e.target.closest("a, details, form, label, .kuvat, .kortti.aanestys, .kortti.fakta") && !art.classList.contains("iso") && !art.classList.contains("piilo")) avaaKetju(art.getAttribute("data-id"), true);
      return;
    }
    var d = b.dataset;
    if (d.tab) { tila.tab = d.tab; tallenna("fp_tab", d.tab); piirraTabit(); lataaSyote(); }
    else if (d.avaasaato !== undefined) { var S = $("#fp-saato"); if (S.hidden) avaaSaato(); else S.hidden = true; }
    else if (d.avaa) { e.preventDefault(); avaaKetju(d.avaa, true); }
    else if (d.takaisin !== undefined) { if (history.state && history.state.p && history.length > 1) history.back(); else suljeKetju(true); }
    else if (d.lisaasivu !== undefined) { tila.sivu++; lataaSyote(true); }
    else if (d.kirjaudu !== undefined) avaaKirjautuminen();
    else if (d.sulje !== undefined) DLG.close();
    else if (d.tilivalikko !== undefined) {
      var tv = $(".tilivalikko"); if (tv) { tv.remove(); b.setAttribute("aria-expanded", "false"); return; }
      var ts = tila.tilasto;
      b.setAttribute("aria-expanded", "true");
      b.insertAdjacentHTML("afterend", '<div class="valikko tilivalikko" role="menu"><div class="tv-nimi">' + esc(tila.mina.nimi || "Oma tili") + "</div>" +
        (ts ? '<div class="tv-tilasto"><b>Ylläpito</b><span>Rekisteröityneitä <b>' + ts.kayttajat + "</b></span><span>Nimen antaneita <b>" + ts.nimelliset + "</b></span><span>Kirjoittaneita <b>" + ts.kirjoittajat + "</b></span><span>Lukijoita 7 pv <b>" + ts.lukijat7 + "</b></span></div>" : "") +
        '<button type="button" role="menuitem" data-ulos>Kirjaudu ulos</button></div>');
    }
    else if (d.avaateksti !== undefined) { var ptx = b.previousElementSibling; if (ptx) ptx.classList.remove("tiivis"); b.remove(); }
    else if (d.ulos !== undefined && confirmOk("Kirjaudutaanko ulos?")) api("ulos", {}).then(function () { location.href = "/"; });
    else if (d.vastaa) avaaKetju(d.vastaa, true);
    else if (d.seuraa) {
      if (!tila.mina || !tila.mina.nimiOk) { tila.kirjautuminen ? avaaKirjautuminen() : ilmoitus("Seuraaminen avautuu pian."); return; }
      api("seuraa", { kayttaja: +d.seuraa }).then(function (j) {
        if (j.virhe) return ilmoitus(j.virhe, 1);
        document.querySelectorAll('[data-seuraa="' + d.seuraa + '"]').forEach(function (x) { x.classList.toggle("on", j.seuraan); x.setAttribute("aria-pressed", j.seuraan); x.textContent = j.seuraan ? "Seuraat" : "Seuraa"; });
        ilmoitus(j.seuraan ? "Seuraat nyt. Kirjoitukset näkyvät Seuratut-välilehdellä ja nousevat syötteessäsi." : "Seuraaminen lopetettu.");
      });
    }
    else if (d.tykkaa) {
      if (!tila.mina || !tila.mina.nimiOk) { tila.kirjautuminen ? avaaKirjautuminen() : ilmoitus("Tykkääminen avautuu pian."); return; }
      api("tykkaa", { id: +d.tykkaa }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); var on = !b.classList.contains("on"); b.classList.toggle("on", on); b.innerHTML = IK.tykkaa + "<span>" + (j.tykkaykset || "") + "</span>"; });
    }
    else if (d.jaa) {
      var vj = $(".valikko"); if (vj) { vj.remove(); if (vj.dataset.jaa === d.jaa) return; }
      var url = "https://faktapiste.fi/p/" + d.jaa, tx = String((tila.tekstit || {})[d.jaa] || "").replace(/\s+/g, " ").trim();
      if (tx.length > 180) tx = tx.slice(0, 177).replace(/\s+\S*$/, "") + "…";
      var e = encodeURIComponent;
      b.insertAdjacentHTML("afterend", '<div class="valikko jaavalikko" data-jaa="' + d.jaa + '">' +
        '<a href="https://x.com/intent/post?text=' + e(tx ? tx + " " : "") + "&url=" + e(url) + '" target="_blank" rel="noopener">Jaa X:ään</a>' +
        '<a href="https://www.facebook.com/sharer/sharer.php?u=' + e(url) + '" target="_blank" rel="noopener">Jaa Facebookiin</a>' +
        '<a href="https://wa.me/?text=' + e((tx ? tx + " " : "") + url) + '" target="_blank" rel="noopener">Lähetä WhatsAppilla</a>' +
        '<button type="button" data-kopioilinkki="' + url + '">Kopioi linkki</button>' +
        (navigator.share ? '<button type="button" data-muujako="' + url + '">Muu sovellus…</button>' : "") + "</div>");
    }
    else if (d.kutsujako) {
      var ku = d.kutsujako, kt = "Liity Faktapisteeseen! Siellä jokainen kirjoitus näytetään vähintään 30 ihmiselle, ja jokainen kirjoitus on arpa: 100 € joka kuukausi rahana tai lahjakorttina.";
      if (navigator.share) navigator.share({ text: kt, url: ku }).catch(function () {});
      else if (navigator.clipboard) navigator.clipboard.writeText(kt + " " + ku).then(function () { ilmoitus("Kutsu kopioitu. Liitä se viestiin."); });
      else prompt("Kopioi kutsu:", kt + " " + ku);
    }
    else if (d.kopioilinkki) { var cl = d.kopioilinkki; ($(".valikko") || { remove: function () {} }).remove();
      if (navigator.clipboard) navigator.clipboard.writeText(cl).then(function () { ilmoitus("Linkki kopioitu."); }, function () { prompt("Kopioi linkki:", cl); }); else prompt("Kopioi linkki:", cl); }
    else if (d.muujako) { var mu = d.muujako; ($(".valikko") || { remove: function () {} }).remove(); navigator.share({ url: mu, title: "Faktapiste" }).catch(function () {}); }
    else if (d.lisaa) {
      var vanha = $(".valikko"); if (vanha) { vanha.remove(); if (vanha.dataset.id === d.lisaa) return; }
      var oma = d.oma === "1" || (tila.mina && tila.mina.admin);
      b.insertAdjacentHTML("afterend", '<div class="valikko" data-id="' + d.lisaa + '">' + (tila.syyt[d.lisaa] ? '<button type="button" data-miksi="' + d.lisaa + '">Miksi näen tämän?</button>' : "") + (d.oma === "1" ? '<button type="button" data-muokkaa="' + d.lisaa + '">Muokkaa</button>' : "") + (oma ? '<button type="button" data-poista="' + d.lisaa + '">Poista</button>' : "") + '<button type="button" data-ilmoita="' + d.lisaa + '">Ilmoita lainvastaisesta sisällöstä</button></div>');
    }
    else if (d.miksi) { var v0 = $(".valikko"); if (v0) v0.outerHTML = '<div class="valikko miksi"><b>Miksi näet tämän</b><p>' + esc(tila.syyt[d.miksi]) + '</p><button type="button" data-saada>Säädä syötettä</button></div>'; }
    else if (d.saada !== undefined) { var v1 = $(".valikko"); if (v1) v1.remove(); avaaSaato(); }
    else if (d.taso) { var i = +d.luokka; tila.saato[i] = +d.taso; tallenna("fp_saato", tila.saato.join(",")); avaaSaato(true); if (tila.tab === "sinulle") lataaSyote(); }
    else if (d.suljesaato !== undefined) { $("#fp-saato").hidden = true; }
    else if (d.kuntavalinta !== undefined) { var inp = $("#kunta-input"); asetaKunta(inp ? inp.value : ""); }
    else if (d.uusimmat !== undefined) { tila.tab = "uusimmat"; tallenna("fp_tab", "uusimmat"); piirraTabit(); lataaSyote(); window.scrollTo(0, 0); }
    else if (d.muokkaa) {
      var art = b.closest(".posti");
      var v2 = $(".valikko"); if (v2) v2.remove();
      if (!art) return;
      if ($(".muokkaus", art)) return;
      var at = $(".avaa-teksti", art); if (at) at.remove();
      var nyk = (tila.postiKuvat[d.muokkaa] || []).map(function (k) { return { avain: "k" + (++kuvaLaskuri), id: k.id }; });
      var lomake = '<form class="muokkaus" data-muokkaus="' + d.muokkaa + '"><textarea name="teksti" rows="4"></textarea>' + kuvaValitsin(nyk) + '<div class="rivi">' + KUVANAPPI + '<span class="vali"></span><button type="button" class="nappi toissijainen" data-peru>Peruuta</button><button class="nappi">Tallenna</button></div></form>';
      var pt = $(".pt", art), gal = $(".kuvat", art);
      if (gal) gal.remove();
      if (pt) pt.outerHTML = lomake; else $("header", art).insertAdjacentHTML("afterend", lomake);
      var fm0 = $(".muokkaus", art); fm0._kuvat = nyk;
      var ta = $("textarea", fm0); ta.value = tila.tekstit[d.muokkaa] || ""; ta.style.height = Math.min(ta.scrollHeight + 4, 600) + "px"; ta.focus();
    }
    else if (d.peru !== undefined) { var fm = b.closest("form"); var id0 = fm.getAttribute("data-muokkaus"); fm.outerHTML = (tila.tekstit[id0] ? '<div class="pt">' + linkit(tila.tekstit[id0]) + "</div>" : "") + kuvaGalleria(tila.postiKuvat[id0]); }
    else if (d.poistavideo !== undefined) { var fvv = b.closest("form"); if (fvv && fvv._video && fvv._video.xhr && fvv._video.lataa) fvv._video.xhr.abort(); if (fvv) fvv._video = null; var ve = b.closest(".ek"); if (ve) ve.remove(); }
    else if (d.poistakuva) { var fk = b.closest("form"); fk._kuvat = (fk._kuvat || []).filter(function (k) { return k.avain !== d.poistakuva; }); var ek = b.closest(".ek"); if (ek) ek.remove(); }
    else if (d.kuva) { DLG.innerHTML = '<div class="dlg kuvaikkuna"><img src="/api/kuva/' + (+d.kuva) + '" alt=""><div class="rivi"><a class="nappi toissijainen" href="/api/kuva/' + (+d.kuva) + '" target="_blank" rel="noopener">Avaa koko koossa</a><button type="button" class="nappi" data-sulje>Sulje</button></div></div>'; DLG.showModal(); }
    else if (d.poista) {
      if (!confirmOk("Poistetaanko postaus?")) return;
      api("poista", { id: +d.poista }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); ilmoitus("Poistettu."); document.querySelectorAll('.posti[data-id="' + d.poista + '"]').forEach(function (a) { a.outerHTML = '<article class="posti piilo"><p class="mute">Postaus poistettu.</p></article>'; }); });
    }
    else if (d.ilmoita) {
      if (!tila.mina || !tila.mina.nimiOk) { ilmoitus("Ilmoita kirjautuneena tai sähköpostilla: miika@eduskuntaseuranta.fi"); return; }
      var syy = prompt("Miksi sisältö on mielestäsi lainvastaista? (esim. uhkaus, henkilötiedot, kiihottaminen kansanryhmää vastaan)");
      if (syy === null) return;
      api("ilmoita", { id: +d.ilmoita, syy: syy }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); ilmoitus("Kiitos, ilmoitus vastaanotettu."); var v = $(".valikko"); if (v) v.remove(); });
    }
    else if (d.fakta !== undefined) {
      var f = b.closest("form"), pan = $(".faktapaneeli", f); pan.hidden = !pan.hidden; if (!pan.hidden) $("input[name=kysymys]", f).focus();
    }
    else if (d.hae !== undefined) haeFakta(b.closest("form"));
    else if (d.poistafakta !== undefined) { var f2 = b.closest("form"); f2._fakta = null; $(".faktatulos", f2).innerHTML = ""; }
  });
  function confirmOk(t) { try { return window.confirm(t); } catch (e) { return true; } }
  function haeFakta(f) {
    var q = $("input[name=kysymys]", f).value.trim(), T = $(".faktatulos", f), B = $("[data-hae]", f);
    if (q.length < 3) { T.innerHTML = '<p class="mute">Kirjoita kysymys.</p>'; return; }
    B.disabled = true; T.innerHTML = '<p class="mute">Haetaan eduskunnan tiedoista… (noin 10 s)</p>';
    api("fakta", { kysymys: q }).then(function (j) {
      B.disabled = false;
      if (j.virhe) { T.innerHTML = '<p class="mute">' + esc(j.virhe) + "</p>"; return; }
      f._fakta = { tyyppi: "fakta", avain: j.avain };
      T.innerHTML = kortti(j.kortti) + '<p class="liitetty">✓ Liitetään postaukseen. <button type="button" class="linkki" data-poistafakta>Poista</button></p>';
      var ta = $("textarea", f); if (!ta.value.trim()) ta.placeholder = "Kirjoita oma näkemyksesi faktan rinnalle";
    });
  }
  document.addEventListener("change", function (e) {
    if (e.target.name === "videotiedosto") { var fv = e.target.closest("form"); if (fv && e.target.files && e.target.files[0]) lisaaVideo(fv, e.target.files[0]); e.target.value = ""; return; }
    if (e.target.name !== "kuvatiedosto") return;
    var f = e.target.closest("form"); if (f && e.target.files && e.target.files.length) lisaaKuvat(f, e.target.files); e.target.value = "";
  });
  document.addEventListener("input", function (e) {
    if (e.target.name === "teksti") { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight + 4, 600) + "px"; }
  });
  document.addEventListener("keydown", function (e) {
    if (e.target.name === "kysymys" && e.key === "Enter") { e.preventDefault(); haeFakta(e.target.form); }
  });
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.id === "kirjform") {
      e.preventDefault(); var em = f.email.value.trim(); var nb = $("button[value=laheta]", f); nb.disabled = true;
      api("kirjaudu", { email: em, kutsu: lue("fp_kutsu") || "" }).then(function (j) {
        nb.disabled = false;
        if (j.virhe) return ilmoitus(j.virhe, 1);
        f.innerHTML = "<h2>Tarkista sähköpostisi</h2><p>Lähetimme kirjautumislinkin osoitteeseen <b>" + esc(em) + "</b>. Linkki on voimassa 30 minuuttia. Katso tarvittaessa myös roskapostikansio.</p><div class=\"rivi\"><button type=\"button\" class=\"nappi\" data-sulje>Selvä</button></div>";
      }); return;
    }
    if (f.id === "nimilomake") {
      e.preventDefault();
      api("nimi", { nimi: f.nimi.value, suosittelija: lue("fp_suos") || "" }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); ilmoitus("Tervetuloa, " + j.nimi + "!"); mina(); }); return;
    }
    if (f.dataset.muokkaus) {
      e.preventDefault(); var mid = f.dataset.muokkaus, uusi = f.teksti.value.trim();
      if (!kuvatValmiit(f)) return ilmoitus("Odota hetki, kuvaa ladataan.", 1);
      if (uusi.length < 2 && !kuvaIdt(f).length) return ilmoitus("Kirjoita jotain tai lisää kuva.", 1);
      var tb = $(".nappi:not(.toissijainen)", f); if (tb) tb.disabled = true;
      api("muokkaa", { id: +mid, teksti: uusi, kuvat: kuvaIdt(f) }).then(function (j) {
        if (tb) tb.disabled = false;
        if (j.virhe) return ilmoitus(j.virhe, 1);
        tila.tekstit[mid] = uusi; tila.postiKuvat[mid] = j.kuvat || []; var art = f.closest(".posti");
        f.outerHTML = (uusi ? '<div class="pt">' + linkit(uusi) + "</div>" : "") + kuvaGalleria(j.kuvat);
        if (art && !$(".muokattu", art)) $("header", art).insertAdjacentHTML("beforeend", '<span class="muokattu">muokattu</span>');
        ilmoitus("Muutokset tallennettu.");
      }, function () { if (tb) tb.disabled = false; ilmoitus("Tallennus epäonnistui. Tarkista verkkoyhteys ja yritä uudelleen.", 1); }); return;
    }
    if (f.dataset.lomake) {
      e.preventDefault();
      var teksti = f.teksti.value.trim();
      if (!kuvatValmiit(f)) return ilmoitus("Odota hetki, kuvaa ladataan.", 1);
      if (f._video && f._video.lataa) return ilmoitus("Odota hetki, videota ladataan.", 1);
      var videoId = f._video && f._video.id ? f._video.id : null;
      if (teksti.length < 2 && !kuvaIdt(f).length && !videoId) return ilmoitus("Kirjoita jotain tai lisää kuva tai video.", 1);
      var nappi = $(".toiminnot .nappi", f); nappi.disabled = true;
      api("posti", { teksti: teksti, vanhempi: f.dataset.vanhempi ? +f.dataset.vanhempi : null, kortti: f._fakta || null, kuvat: kuvaIdt(f), video: videoId, kunta: f.kunta && f.kunta.checked ? tila.kunta : null }).then(function (j) {
        nappi.disabled = false;
        if (j.virhe) return ilmoitus(j.virhe, 1);
        piirraArvonta();
        if (f.dataset.vanhempi) { avaaKetju(f.dataset.vanhempi, false); ilmoitus("Vastaus julkaistu."); }
        else { f.reset(); f._fakta = null; f._kuvat = []; f._video = null; tila.tab = "uusimmat"; piirraTabit(); lataaSyote(); piirraKirjoitus(); ilmoitus("Julkaistu. Näytämme postauksesi vähintään 30 ihmiselle."); }
      });
    }
  });
  window.addEventListener("popstate", function () {
    var p = new URLSearchParams(location.search).get("p");
    if (p) avaaKetju(p, false); else suljeKetju(false);
  });

  // ---------- vapaaehtoinen opastus ----------
  var OPAS = [
    ["👀", "Täällä sinut nähdään", "Jokainen postaus näytetään vähintään 30 ihmiselle, vaikka sinulla ei olisi yhtään seuraajaa. Postauksen alla näet, kuinka moni sen on lukenut."],
    ["✓", "Syöte loppuu", "Sinulle-syöte näyttää vain sellaista, mitä et ole vielä nähnyt. Kun tärkeimmät on katsottu, se loppuu. Ei loputonta selaamista."],
    ["⚙", "Sinä päätät, mitä näet", "Säädä-napista valitset, paljonko näet keskusteluja, uutisia ja muuta. Jokaisen postauksen ⋯-valikosta näet, miksi se näkyy sinulle."],
    ["📍", "Oma paikkakunta ja faktat", "Lähellä-välilehti näyttää paikkakuntasi keskustelut. Kysy fakta -napilla saat tarkistetun tiedon suoraan postaukseesi."]
  ];
  function opastus(vaihe) {
    var O = $("#fp-opastus"); if (!O) return;
    if (vaihe < 0 || vaihe >= OPAS.length) { O.innerHTML = ""; tallenna("fp_opastus", "1"); return; }
    var o = OPAS[vaihe];
    O.innerHTML = '<div class="opas" role="region" aria-label="Opastus"><span class="opas-ik">' + o[0] + '</span><div><span class="opas-n">' + (vaihe + 1) + " / " + OPAS.length + "</span><b>" + o[1] + "</b><p>" + o[2] + '</p><div class="rivi"><button type="button" class="nappi" data-opas="' + (vaihe + 1) + '">' + (vaihe + 1 < OPAS.length ? "Seuraava" : "Valmis") + '</button><button type="button" class="linkki" data-opas="-1">Ohita opastus</button></div></div></div>';
  }
  function tarjoaOpastus() {
    var O = $("#fp-opastus"); if (!O || lue("fp_opastus") === "1") return;
    O.innerHTML = '<div class="opas"><span class="opas-ik">👋</span><div><b>Tervetuloa Faktapisteeseen!</b><p>Haluatko nähdä lyhyesti, miten täällä toimitaan? Vie alle minuutin.</p><div class="rivi"><button type="button" class="nappi" data-opas="0">Näytä miten toimii</button><button type="button" class="linkki" data-opas="-1">Ei kiitos</button></div></div></div>';
  }
  document.addEventListener("click", function (e) { var b = e.target.closest("[data-opas]"); if (b) opastus(+b.getAttribute("data-opas")); });

  // ---------- asennus puhelimeen (PWA) ----------
  var asennus = null;
  var sovelluksena = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone;
  var ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(function () {});
  function asennusNappi() {
    var A = $("#fp-asenna"); if (!A) return;
    A.innerHTML = sovelluksena || (!asennus && !ios) ? "" : '<button type="button" class="asenna" data-asenna>📲 Lataa sovellus</button>';
  }
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); asennus = e; asennusNappi(); });
  window.addEventListener("appinstalled", function () { asennus = null; asennusNappi(); ilmoitus("Faktapiste lisätty puhelimeesi!"); });
  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-asenna]")) return;
    if (asennus) { asennus.prompt(); asennus.userChoice.finally(function () { asennus = null; asennusNappi(); }); return; }
    DLG.innerHTML = '<div class="dlg"><h2>Lataa Faktapiste puhelimeesi</h2><p>iPhonessa (Safari):</p><ol class="ohje"><li>Paina alareunan <b>Jaa</b>-painiketta (neliö ja nuoli ylös).</li><li>Valitse <b>Lisää Koti-valikkoon</b>.</li><li>Paina <b>Lisää</b>. Faktapiste ilmestyy kotinäytölle omana sovelluksenaan.</li></ol><div class="rivi"><button type="button" class="nappi" data-sulje>Selvä</button></div></div>';
    DLG.showModal();
  });
  asennusNappi();

  // ---------- käynnistys ----------
  var qs = new URLSearchParams(location.search);
  if (qs.get("kirjautuminen") === "vanhentunut") setTimeout(function () { ilmoitus("Kirjautumislinkki on vanhentunut tai jo käytetty. Pyydä uusi.", 1); }, 300);
  if (qs.get("tervetuloa")) { history.replaceState({}, "", "/"); setTimeout(function () { ilmoitus("Olet kirjautunut sisään."); }, 300); }
  piirraTabit();
  tarjoaOpastus();
  mina().then(function () { piirraArvonta(); if (qs.get("p")) avaaKetju(qs.get("p"), false); });
  lataaSyote();
})();
