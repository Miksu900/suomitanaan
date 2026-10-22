// Faktapiste-keskustelu: syöte, kirjoittaminen, Kysy fakta, ketjut.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var LAHTEET = {
    suomitanaan: { nimi: "Suomi Tänään", lyh: "ST", vari: "#b4232c" },
    korjausvahti: { nimi: "Korjausvahti", lyh: "KV", vari: "#7a4cc2" },
    eduskunta: { nimi: "Eduskunta", lyh: "§", vari: "#1d5fd1" },
    keraysvahti: { nimi: "Keräysvahti", lyh: "!", vari: "#c26a00" }
  };
  var tila = { mina: null, kirjautuminen: true, tab: "suositut", sivu: 0, fakta: null, ladataan: false };
  try { tila.tab = localStorage.getItem("fp_tab") || "suositut"; } catch (e) {}

  function api(polku, data) {
    var o = data ? { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(data), credentials: "same-origin" } : { credentials: "same-origin" };
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
    return esc(t).replace(/https?:\/\/[^\s<]+/g, function (u) { return '<a href="' + u + '" rel="nofollow noopener ugc" target="_blank">' + u.replace(/^https?:\/\//, "").slice(0, 40) + (u.length > 48 ? "…" : "") + "</a>"; }).replace(/\n/g, "<br>");
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
    if (k.tyyppi === "uutinen") return '<a class="kortti uutinen" href="' + esc(k.url) + '" target="_blank" rel="noopener"><span class="kl">' + esc(k.lahde) + "</span><strong>" + esc(k.otsikko) + "</strong>" + (k.kuvaus ? "<span>" + esc(k.kuvaus) + "</span>" : "") + "</a>";
    if (k.tyyppi === "muutos") return '<a class="kortti muutos" href="' + esc(k.url) + '" target="_blank" rel="noopener"><span class="kl">Otsikko muuttui · ' + esc(k.media) + '</span><span class="ennen"><em>Ennen</em>' + esc(k.ennen) + '</span><span class="nyt"><em>Nyt</em>' + esc(k.nyt) + "</span></a>";
    if (k.tyyppi === "varoitus") return '<a class="kortti varoitus" href="' + esc(k.url) + '" target="_blank" rel="noopener"><span class="kl">Huijausvaroitus · ' + esc(k.media) + "</span><strong>" + esc(k.otsikko) + "</strong></a>";
    if (k.tyyppi === "aanestys") return '<div class="kortti aanestys"><span class="kl">Eduskunnan äänestys' + (k.pv ? " · " + pvm(k.pv) : "") + "</span><strong>" + esc(k.otsikko) + "</strong>" +
      (k.lisaotsikko ? '<span class="lisa">' + esc(k.lisaotsikko) + "</span>" : "") + (k.tulos ? '<span class="tulos ' + (/Hyväks|Jaa/.test(k.tulos) ? "ok" : "no") + '">' + esc(k.tulos) + "</span>" : "") +
      palkit(k) + ryhmat(k) + '<a class="lue" href="' + esc(k.url) + '" target="_blank" rel="noopener">Katso edustajien äänet Eduskuntaseurannasta →</a></div>';
    if (k.tyyppi === "fakta") return '<div class="kortti fakta"><span class="kl">Fakta · Eduskuntaseuranta</span><span class="kys">' + esc(k.kysymys) + '</span><p>' + esc(k.vastaus) + "</p>" +
      (k.aanestys ? '<div class="fa"><strong>' + esc(k.aanestys.otsikko) + "</strong>" + palkit(k.aanestys) + ryhmat(k.aanestys) + "</div>" : "") +
      (k.lahteet && k.lahteet.length ? '<div class="lahteet">' + k.lahteet.slice(0, 3).map(function (s) { return '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.otsikko) + "</a>"; }).join("") + "</div>" : "") +
      '<small>Tekoälyn kokoama vastaus avoimesta datasta. Tarkista tärkeät asiat lähteestä.</small></div>';
    return "";
  }

  // ---------- postaus ----------
  function posti(p, iso) {
    var l = LAHTEET[p.lahde];
    var nimi = l ? l.nimi : p.nimi || "Käyttäjä";
    var av = l ? '<span class="av" style="background:' + l.vari + '">' + l.lyh + "</span>" : '<span class="av k">' + esc((p.nimi || "?").charAt(0).toUpperCase()) + "</span>";
    if (p.piilotettu) return '<article class="posti piilo" data-id="' + p.id + '"><p class="mute">Tämä postaus on poistettu tai piilotettu.</p></article>';
    return '<article class="posti' + (iso ? " iso" : "") + '" data-id="' + p.id + '">' + av + '<div class="pm"><header><b>' + esc(nimi) + "</b>" + (l ? '<span class="auto">automaattinen</span>' : "") +
      '<a class="aika" href="/?p=' + p.id + '" data-avaa="' + p.id + '">' + aika(p.luotu) + "</a></header>" +
      (p.teksti ? '<div class="pt">' + linkit(p.teksti) + "</div>" : "") + kortti(p.kortti) +
      '<footer><button type="button" data-vastaa="' + p.id + '" aria-label="Vastaa">💬 <span>' + (p.vastaukset || "") + '</span></button>' +
      '<button type="button" data-tykkaa="' + p.id + '" class="' + (p.tykkasin ? "on" : "") + '" aria-label="Tykkää">' + (p.tykkasin ? "♥" : "♡") + " <span>" + (p.tykkaykset || "") + "</span></button>" +
      '<button type="button" data-jaa="' + p.id + '" aria-label="Jaa">↗</button>' +
      '<button type="button" data-lisaa="' + p.id + '" aria-label="Lisää toimintoja" data-oma="' + (p.oma ? 1 : 0) + '">⋯</button></footer></div></article>';
  }

  // ---------- kirjoituslaatikko ----------
  function kirjoitus(vanhempi) {
    var id = vanhempi ? "v" : "u";
    if (!tila.mina) {
      if (!tila.kirjautuminen) return '<div class="kirjoita lukko"><b>Keskustelu on beta-testissä.</b><span>Kirjoittaminen avautuu kaikille pian. Voit jo lukea syötettä.</span></div>';
      return '<div class="kirjoita lukko"><b>' + (vanhempi ? "Kirjaudu vastataksesi." : "Mitä mieltä olet? Kirjaudu ja kirjoita.") + '</b><span>Kirjautuminen sähköpostilinkillä, ei salasanaa.</span><button type="button" class="nappi" data-kirjaudu>Kirjaudu</button></div>';
    }
    if (!tila.mina.nimi) return '<form class="kirjoita" id="nimilomake"><b>Valitse nimimerkki</b><span>Näkyy postaustesi yhteydessä. Sähköpostiosoitetta ei näytetä kenellekään.</span><div class="rivi"><input name="nimi" maxlength="24" placeholder="esim. Pohjanmaan Pekka" required><button class="nappi">Tallenna</button></div></form>';
    return '<form class="kirjoita" data-lomake="' + id + '"' + (vanhempi ? ' data-vanhempi="' + vanhempi + '"' : "") + '>' +
      '<textarea name="teksti" maxlength="500" rows="' + (vanhempi ? 2 : 3) + '" placeholder="' + (vanhempi ? "Kirjoita vastaus" : "Mitä mieltä olet? Kysy faktaa eduskunnan päätöksistä ja liitä se postaukseen.") + '"></textarea>' +
      '<div class="faktapaneeli" hidden><div class="rivi"><input name="kysymys" maxlength="300" placeholder="Kysy vapaasti, esim. miten perussuomalaiset äänesti kotihoidontuesta?"><button type="button" class="nappi toissijainen" data-hae>Hae</button></div><div class="faktatulos"></div></div>' +
      '<div class="toiminnot"><button type="button" class="fakta-nappi" data-fakta>🔎 Kysy fakta</button><span class="laskuri">500</span><button class="nappi">' + (vanhempi ? "Vastaa" : "Julkaise") + "</button></div></form>";
  }

  // ---------- näkymät ----------
  var SYOTE = $("#fp-syote"), KIRJ = $("#fp-kirjoita"), TABIT = $("#fp-tabit");
  function piirraTabit() {
    TABIT.innerHTML = [["suositut", "Suositut"], ["uusimmat", "Uusimmat"], ["keskustelut", "Vain keskustelut"]].map(function (t) {
      return '<button type="button" role="tab" aria-selected="' + (tila.tab === t[0]) + '" data-tab="' + t[0] + '">' + t[1] + "</button>"; }).join("");
  }
  function lataaSyote(lisaa) {
    if (tila.ladataan) return; tila.ladataan = true;
    if (!lisaa) { tila.sivu = 0; SYOTE.innerHTML = '<p class="lataa">Ladataan…</p>'; }
    api("syote?tab=" + tila.tab + "&sivu=" + tila.sivu).then(function (j) {
      tila.ladataan = false;
      var vanha = $(".lisaa-nappi", SYOTE); if (vanha) vanha.remove();
      if (!lisaa) SYOTE.innerHTML = "";
      if (j.virhe) { SYOTE.innerHTML = '<p class="lataa">' + esc(j.virhe) + "</p>"; return; }
      if (!j.postit.length && !lisaa) SYOTE.innerHTML = '<p class="lataa">' + (tila.tab === "keskustelut" ? "Ei vielä keskusteluja. Aloita sinä!" : "Syöte täyttyy pian.") + "</p>";
      SYOTE.insertAdjacentHTML("beforeend", j.postit.map(function (p) { return posti(p); }).join(""));
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
    });
  }
  function suljeKetju(push) {
    if (push) history.pushState({}, "", "/");
    $("#fp-ketju").hidden = true; $("#fp-paa").hidden = false;
  }
  function piirraKirjoitus() { KIRJ.innerHTML = kirjoitus(null); }
  function mina() {
    return api("mina").then(function (j) {
      tila.mina = j.kayttaja; tila.kirjautuminen = j.kirjautuminen === true;
      // Testivaihe: kirjautumisnappi näkyy vain osoitteella /?testi=1 avattuna (muistetaan selaimessa).
      if (j.testi) { var t = /[?&]testi=1/.test(location.search); try { if (t) localStorage.setItem("fp_testi", "1"); t = t || localStorage.getItem("fp_testi") === "1"; } catch (x) {} if (t) tila.kirjautuminen = true; }
      var a = $("#fp-tili");
      if (a) a.innerHTML = tila.mina ? '<button type="button" class="tili" data-ulos>' + esc(tila.mina.nimi || "Oma tili") + " · Kirjaudu ulos</button>" : tila.kirjautuminen ? '<button type="button" class="tili" data-kirjaudu>Kirjaudu</button>' : "";
      piirraKirjoitus();
    });
  }

  // ---------- kirjautumisikkuna ----------
  var DLG = $("#fp-kirjaudu");
  function avaaKirjautuminen() {
    DLG.innerHTML = '<form method="dialog" class="dlg" id="kirjform"><h2>Kirjaudu Faktapisteeseen</h2><p>Saat sähköpostiisi kirjautumislinkin. Salasanaa ei tarvita, ja sama linkki luo tilin, jos sinulla ei vielä ole sitä.</p>' +
      '<label>Sähköposti<input type="email" name="email" required autocomplete="email"></label><p class="pieni">Kirjautumalla hyväksyt <a href="/tietoa/#keskustelu">keskustelun säännöt ja tietosuojan</a>.</p>' +
      '<div class="rivi"><button type="button" class="nappi toissijainen" data-sulje>Peruuta</button><button class="nappi" value="laheta">Lähetä linkki</button></div></form>';
    DLG.showModal();
  }

  // ---------- tapahtumat ----------
  document.addEventListener("click", function (e) {
    var b = e.target.closest("button, a[data-avaa]"); if (!b) {
      var art = e.target.closest(".posti"); if (art && !e.target.closest("a, details, .kortti.aanestys, .kortti.fakta") && !art.classList.contains("iso") && !art.classList.contains("piilo")) avaaKetju(art.getAttribute("data-id"), true);
      return;
    }
    var d = b.dataset;
    if (d.tab) { tila.tab = d.tab; try { localStorage.setItem("fp_tab", d.tab); } catch (x) {} piirraTabit(); lataaSyote(); }
    else if (d.avaa) { e.preventDefault(); avaaKetju(d.avaa, true); }
    else if (d.takaisin !== undefined) { if (history.state && history.state.p && history.length > 1) history.back(); else suljeKetju(true); }
    else if (d.lisaasivu !== undefined) { tila.sivu++; lataaSyote(true); }
    else if (d.kirjaudu !== undefined) avaaKirjautuminen();
    else if (d.sulje !== undefined) DLG.close();
    else if (d.ulos !== undefined) api("ulos", {}).then(function () { location.href = "/"; });
    else if (d.vastaa) avaaKetju(d.vastaa, true);
    else if (d.tykkaa) {
      if (!tila.mina || !tila.mina.nimi) { tila.kirjautuminen ? avaaKirjautuminen() : ilmoitus("Tykkääminen avautuu pian."); return; }
      api("tykkaa", { id: +d.tykkaa }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); var on = !b.classList.contains("on"); b.classList.toggle("on", on); b.innerHTML = (on ? "♥" : "♡") + " <span>" + (j.tykkaykset || "") + "</span>"; });
    }
    else if (d.jaa) {
      var url = location.origin + "/?p=" + d.jaa;
      if (navigator.share) navigator.share({ url: url, title: "Faktapiste" }).catch(function () {});
      else if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { ilmoitus("Linkki kopioitu."); });
    }
    else if (d.lisaa) {
      var vanha = $(".valikko"); if (vanha) { vanha.remove(); if (vanha.dataset.id === d.lisaa) return; }
      var oma = d.oma === "1" || (tila.mina && tila.mina.admin);
      b.insertAdjacentHTML("afterend", '<div class="valikko" data-id="' + d.lisaa + '">' + (oma ? '<button type="button" data-poista="' + d.lisaa + '">Poista</button>' : "") + '<button type="button" data-ilmoita="' + d.lisaa + '">Ilmoita lainvastaisesta sisällöstä</button></div>');
    }
    else if (d.poista) {
      if (!confirmOk("Poistetaanko postaus?")) return;
      api("poista", { id: +d.poista }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); ilmoitus("Poistettu."); var a = document.querySelector('.posti[data-id="' + d.poista + '"]'); if (a) a.outerHTML = '<article class="posti piilo"><p class="mute">Postaus poistettu.</p></article>'; });
    }
    else if (d.ilmoita) {
      if (!tila.mina || !tila.mina.nimi) { ilmoitus("Ilmoita kirjautuneena tai sähköpostilla: miika@eduskuntaseuranta.fi"); return; }
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
  document.addEventListener("input", function (e) {
    if (e.target.name === "teksti") { var l = $(".laskuri", e.target.form); if (l) { var n = 500 - e.target.value.length; l.textContent = n; l.classList.toggle("vahan", n < 40); } }
  });
  document.addEventListener("keydown", function (e) {
    if (e.target.name === "kysymys" && e.key === "Enter") { e.preventDefault(); haeFakta(e.target.form); }
  });
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.id === "kirjform") {
      e.preventDefault(); var em = f.email.value.trim(); var nb = $("button[value=laheta]", f); nb.disabled = true;
      api("kirjaudu", { email: em }).then(function (j) {
        nb.disabled = false;
        if (j.virhe) return ilmoitus(j.virhe, 1);
        f.innerHTML = "<h2>Tarkista sähköpostisi</h2><p>Lähetimme kirjautumislinkin osoitteeseen <b>" + esc(em) + "</b>. Linkki on voimassa 30 minuuttia. Katso tarvittaessa myös roskapostikansio.</p><div class=\"rivi\"><button type=\"button\" class=\"nappi\" data-sulje>Selvä</button></div>";
      }); return;
    }
    if (f.id === "nimilomake") {
      e.preventDefault();
      api("nimi", { nimi: f.nimi.value }).then(function (j) { if (j.virhe) return ilmoitus(j.virhe, 1); ilmoitus("Tervetuloa, " + j.nimi + "!"); mina(); }); return;
    }
    if (f.dataset.lomake) {
      e.preventDefault();
      var teksti = f.teksti.value.trim(); if (teksti.length < 2) return ilmoitus("Kirjoita jotain.", 1);
      var nappi = $(".toiminnot .nappi", f); nappi.disabled = true;
      api("posti", { teksti: teksti, vanhempi: f.dataset.vanhempi ? +f.dataset.vanhempi : null, kortti: f._fakta || null }).then(function (j) {
        nappi.disabled = false;
        if (j.virhe) return ilmoitus(j.virhe, 1);
        if (f.dataset.vanhempi) { avaaKetju(f.dataset.vanhempi, false); ilmoitus("Vastaus julkaistu."); }
        else { f.reset(); f._fakta = null; tila.tab = "uusimmat"; piirraTabit(); lataaSyote(); piirraKirjoitus(); ilmoitus("Julkaistu."); }
      });
    }
  });
  window.addEventListener("popstate", function () {
    var p = new URLSearchParams(location.search).get("p");
    if (p) avaaKetju(p, false); else suljeKetju(false);
  });

  // ---------- käynnistys ----------
  var qs = new URLSearchParams(location.search);
  if (qs.get("kirjautuminen") === "vanhentunut") setTimeout(function () { ilmoitus("Kirjautumislinkki on vanhentunut tai jo käytetty. Pyydä uusi.", 1); }, 300);
  if (qs.get("tervetuloa")) { history.replaceState({}, "", "/"); setTimeout(function () { ilmoitus("Olet kirjautunut sisään."); }, 300); }
  piirraTabit();
  mina().then(function () { if (qs.get("p")) avaaKetju(qs.get("p"), false); });
  lataaSyote();
})();
