// Pykälävahti – selainpuoli
(function () {
  var $ = function (i) { return document.getElementById(i); };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  // kevyt muotoilu: ## otsikot, - luettelot, **lihavointi**, [n] viitteet
  function muotoile(t, n) {
    var rivit = esc(t).split("\n"), out = [], lista = false;
    function inline(s) {
      return s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[(\d+(?:\s*[,–-]\s*\d+)*)\]/g, function (m, g) {
        return g.split(/\s*,\s*/).map(function (x) { var k = parseInt(x, 10); return k >= 1 && k <= n ? '<a class="viite" href="#l' + k + '">' + x + "</a>" : "[" + x + "]"; }).join("");
      });
    }
    rivit.forEach(function (r) {
      var s = r.trim();
      if (/^#{1,3}\s/.test(s)) { if (lista) { out.push("</ul>"); lista = false; } out.push("<h2>" + inline(s.replace(/^#+\s*/, "")) + "</h2>"); }
      else if (/^[-*•]\s/.test(s) || /^\d+\.\s/.test(s)) { if (!lista) { out.push("<ul>"); lista = true; } out.push("<li>" + inline(s.replace(/^([-*•]|\d+\.)\s*/, "")) + "</li>"); }
      else if (s) { if (lista) { out.push("</ul>"); lista = false; } out.push("<p>" + inline(s) + "</p>"); }
    });
    if (lista) out.push("</ul>");
    // Lyhyt vastaus ja toimintaohjeet näkyvät heti, perustelut avautuvat napista (sivu pysyy simppelinä)
    var html = out.join(""), osat = html.split(/(?=<h2>)/);
    return osat.map(function (o, i) {
      if (i === 0 || !/^<h2>/.test(o)) return o;
      var ots = o.match(/^<h2>(.*?)<\/h2>/)[1], auki = /voit tehdä|juristi|Tiivistelmä/i.test(ots);
      return '<details class="osio"' + (auki ? " open" : "") + "><summary>" + ots + "</summary>" + o.replace(/^<h2>.*?<\/h2>/, "") + "</details>";
    }).join("");
  }
  function lahteet(l) {
    if (!l || !l.length) return "";
    return '<div class="lahteet"><h2>Lähteet: ajantasainen lainsäädäntö</h2>' + l.map(function (x) {
      return '<details class="lahde" id="l' + x.n + '"><summary>[' + x.n + "] " + esc(x.laki) + " " + esc(x.lyh) + " · " + esc((x.luku ? x.luku.replace(/^(\d+\s*[a-z]?\s*luku).*/i, "$1") + " " : "") + x.num + " " + x.ots) +
        "</summary><p>" + esc(x.ote) + (x.ote.length >= 600 ? "…" : "") + '</p><p><a href="' + esc(x.url) + '" target="_blank" rel="noopener">Avaa laki Finlexissä →</a></p></details>';
    }).join("") + "</div>";
  }
  function etaisyys(a, c) { if (!a || !c) return null; var r = Math.PI / 180, dl = (c[0] - a[0]) * r, dn = (c[1] - a[1]) * r;
    var x = Math.sin(dl / 2) * Math.sin(dl / 2) + Math.cos(a[0] * r) * Math.cos(c[0] * r) * Math.sin(dn / 2) * Math.sin(dn / 2); return 12742 * Math.asin(Math.sqrt(x)); }
  var TOIM = null;
  function toimistot() { return TOIM || (TOIM = fetch("/data/toimistot.json").then(function (r) { return r.json(); }).then(function (d) { return d.t; })); }
  function korttiHTML(t) {
    return '<div class="toimisto"><b>' + esc(t.n) + '</b><span class="m"><span class="laji">' + esc(t.l) + "</span>" + esc([t.o, (t.pn + " " + t.k).trim()].filter(Boolean).join(", ")) +
      (t._e != null ? " · noin " + Math.round(t._e) + " km" : "") + "</span>" + (t.w ? '<span class="m"><a href="' + esc(t.w) + '" target="_blank" rel="noopener nofollow">' + esc(t.w.replace(/^https?:\/\//, "")) + "</a></span>" : "") + "</div>";
  }
  function lahimmat(el) {
    el.innerHTML = '<div class="lahin"><h2>Lähimmät asianajotoimistot</h2><div class="haku"><input type="search" id="lk" placeholder="Paikkakuntasi, esim. Ylivieska"><button type="button" class="btn" id="lsij">Käytä sijaintiani</button></div><div id="ll" class="lista"></div></div>';
    function nayta(piste, nimi) {
      toimistot().then(function (L) {
        var r = L.filter(function (t) { return t.l === "Asianajotoimisto" && t.c; });
        if (!piste) { var k = L.find(function (t) { return t.k.toLowerCase() === nimi.toLowerCase() && t.c; }); piste = k && k.c; }
        if (!piste) { $("ll").innerHTML = '<p class="mute small">Paikkakuntaa ei löytynyt. Kokeile lähintä kaupunkia tai <a href="/toimistot/">hae kaikista toimistoista</a>.</p>'; return; }
        r.forEach(function (t) { t._e = etaisyys(piste, t.c); }); r.sort(function (a, b) { return a._e - b._e; });
        $("ll").innerHTML = r.slice(0, 5).map(korttiHTML).join("") + '<p class="small"><a href="/toimistot/?laji=Asianajotoimisto&q=' + encodeURIComponent(nimi || "") + '">Näytä lisää toimistoja →</a></p>';
      });
    }
    var tm; $("lk").addEventListener("input", function () { clearTimeout(tm); var v = this.value.trim(); if (v.length >= 3) tm = setTimeout(function () { nayta(null, v); }, 350); });
    $("lsij").onclick = function () { if (!navigator.geolocation) return; $("ll").innerHTML = '<p class="lataa">Haetaan sijaintia…</p>';
      navigator.geolocation.getCurrentPosition(function (p) { nayta([p.coords.latitude, p.coords.longitude], ""); }, function () { $("ll").innerHTML = '<p class="mute small">Sijaintia ei saatu. Kirjoita paikkakuntasi.</p>'; }); };
    try { var muisti = localStorage.getItem("pv_kunta"); if (muisti) { $("lk").value = muisti; nayta(null, muisti); } } catch (e) {}
    $("lk").addEventListener("change", function () { try { localStorage.setItem("pv_kunta", this.value.trim()); } catch (e) {} });
  }
  var VASTUU = '<p class="vastuu">Tämä on yleistä tietoa laista, ei oikeudellista neuvontaa. Tekoäly voi erehtyä: tarkista pykälät ja käänny juristin puoleen, jos asialla on sinulle merkitystä.</p>';
  function laheta(polku, data, nappi, teksti, jalkeen) {
    var T = $("tulos"); T.hidden = false; nappi.disabled = true;
    T.innerHTML = '<p class="lataa">' + teksti + "</p>";
    fetch(polku, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        nappi.disabled = false;
        if (d.virhe) { T.innerHTML = '<p class="virhe">' + esc(d.virhe) + "</p>"; return; }
        var n = (d.lahteet || []).length;
        T.innerHTML = muotoile(d.vastaus, n) + VASTUU + (jalkeen || "") + '<div id="lahinLaatikko"></div>' + lahteet(d.lahteet);
        lahimmat($("lahinLaatikko"));
        T.scrollIntoView({ behavior: "smooth", block: "start" });
        T.dataset.teksti = d.vastaus + "\n\nLähteet:\n" + (d.lahteet || []).map(function (x) { return "[" + x.n + "] " + x.laki + " " + x.lyh + " " + x.num + " " + x.ots + " – " + x.url; }).join("\n");
      })
      .catch(function () { nappi.disabled = false; T.innerHTML = '<p class="virhe">Yhteys palveluun ei onnistunut. Yritä uudelleen.</p>'; });
  }
  function kopioi(b) {
    var t = $("tulos").dataset.teksti || "";
    var ok = function () { b.textContent = "Kopioitu"; setTimeout(function () { b.textContent = "Kopioi teksti"; }, 1600); };
    if (navigator.clipboard) navigator.clipboard.writeText(t).then(ok); else { var a = document.createElement("textarea"); a.value = t; document.body.appendChild(a); a.select(); document.execCommand("copy"); a.remove(); ok(); }
  }
  window.Pv = {
    kysy: function () {
      var q = $("kysymys"), b = $("kysyNappi"), m = $("merkit");
      q.addEventListener("input", function () { m.textContent = q.value.length + " / 1500"; });
      document.querySelectorAll(".esim").forEach(function (e) { e.onclick = function () { q.value = e.dataset.q; q.dispatchEvent(new Event("input")); laheta1(); }; });
      function laheta1() {
        if (q.value.trim().length < 10) { q.focus(); return; }
        laheta("/api/kysy", { kysymys: q.value, hp: $("hp").value }, b, "Etsitään pykäliä ja muotoillaan vastausta… (noin 15–30 s)",
          '<div class="napit"><a class="btn" href="/pohjaesitys/">Tee pohjaesitys juristille</a><a class="btn toissij" href="/toimistot/">Löydä lakitoimisto</a></div>');
      }
      $("kysyLomake").onsubmit = function (e) { e.preventDefault(); laheta1(); };
    },
    esitys: function () {
      var b = $("esitysNappi"), tila = { maksullinen: false, hinta: 29 }, kentat = ["kuvaus", "tavoite", "ajat"];
      var JALKI = '<div class="napit"><button type="button" class="btn" onclick="print()">Tulosta tai tallenna PDF</button><button type="button" class="btn toissij" id="kop">Kopioi teksti</button><a class="btn toissij" href="/toimistot/">Löydä juristi</a></div>';
      function kytkeKopio() { var t = setInterval(function () { var k = $("kop"); if (k) { k.onclick = function () { kopioi(k); }; clearInterval(t); } }, 300); }
      function laadi(maksu) {
        laheta("/api/esitys", { kuvaus: $("kuvaus").value, tavoite: $("tavoite").value, ajat: $("ajat").value, hp: $("hp").value, maksu: maksu || "" }, b,
          "Laaditaan pohjaesitystä… (noin 30–60 s)", JALKI);
        kytkeKopio();
      }
      var q = new URLSearchParams(location.search), maksu = q.get("maksu");
      try { var tall = JSON.parse(sessionStorage.getItem("pv_esitys") || "null"); if (tall) kentat.forEach(function (k) { $(k).value = tall[k] || ""; }); } catch (e) {}
      fetch("/api/tila").then(function (r) { return r.json(); }).then(function (d) {
        tila = d;
        $("hinta").innerHTML = d.maksullinen ? "<b>Hinta " + String(d.hinta).replace(".", ",") + " €</b> (sis. alv). Maksu kortilla tai mobiilimaksulla. Pohjaesitys toimitetaan heti maksun jälkeen." : "<b>Avajaistarjous: pohjaesitys on nyt maksuton.</b>";
        $("ehdotRivi").hidden = !d.maksullinen;
        b.textContent = d.maksullinen ? "Siirry maksamaan (" + String(d.hinta).replace(".", ",") + " €)" : "Laadi pohjaesitys";
        if (maksu && $("kuvaus").value.trim()) { history.replaceState(null, "", "/pohjaesitys/"); laadi(maksu); }
        else if (maksu) { $("tulos").hidden = false; $("tulos").innerHTML = '<p class="virhe">Maksu on vastaanotettu, mutta kuvauksesi ei säilynyt selaimessa. Kirjoita kuvaus uudelleen ja paina nappia: maksua ei veloiteta uudestaan.</p>'; b.textContent = "Laadi pohjaesitys"; b.dataset.maksu = maksu; }
        if (q.get("peruttu")) { $("tulos").hidden = false; $("tulos").innerHTML = '<p class="virhe">Maksu peruttiin. Mitään ei veloitettu.</p>'; }
      }).catch(function () {});
      $("esitysLomake").onsubmit = function (e) {
        e.preventDefault();
        if ($("kuvaus").value.trim().length < 40) { $("kuvaus").focus(); return; }
        if (b.dataset.maksu) { laadi(b.dataset.maksu); return; }
        if (!tila.maksullinen) { laadi(""); return; }
        if (!$("ehdot").checked) { $("ehdot").focus(); $("tulos").hidden = false; $("tulos").innerHTML = '<p class="virhe">Hyväksy ehdot ennen maksamista.</p>'; return; }
        var t = {}; kentat.forEach(function (k) { t[k] = $(k).value; });
        try { sessionStorage.setItem("pv_esitys", JSON.stringify(t)); } catch (x) {}
        b.disabled = true; b.textContent = "Siirrytään maksamaan…";
        fetch("/api/maksu", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ehdot: true }) })
          .then(function (r) { return r.json(); }).then(function (d) { if (d.url) location.href = d.url; else { b.disabled = false; $("tulos").hidden = false; $("tulos").innerHTML = '<p class="virhe">' + esc(d.virhe || "Maksun aloitus epäonnistui.") + "</p>"; } })
          .catch(function () { b.disabled = false; });
      };
      // onnistuneen esityksen jälkeen kuvaus poistetaan selaimesta
      new MutationObserver(function () { if ($("kop")) { try { sessionStorage.removeItem("pv_esitys"); } catch (x) {} } }).observe($("tulos"), { childList: true });
    },
    toimistot: function () {
      var L = [], sij = null, h = $("th"), out = $("toimistot"), tl = $("tl");
      function fold(s) { return (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, ""); }
      function etais(c) { if (!sij || !c) return null; var R = 6371, r = Math.PI / 180, dl = (c[0] - sij[0]) * r, dn = (c[1] - sij[1]) * r;
        var a = Math.sin(dl / 2) * Math.sin(dl / 2) + Math.cos(sij[0] * r) * Math.cos(c[0] * r) * Math.sin(dn / 2) * Math.sin(dn / 2); return 2 * R * Math.asin(Math.sqrt(a)); }
      function piirra() {
        var q = fold(h.value.trim()), laji = (document.querySelector("input[name=laji]:checked") || {}).value || "";
        var r = L.filter(function (t) { return (!laji || t.l === laji) && (!q || t._s.indexOf(q) > -1); });
        if (sij) r.forEach(function (t) { t._e = etais(t.c); }), r.sort(function (a, b) { return (a._e == null ? 1e9 : a._e) - (b._e == null ? 1e9 : b._e); });
        if (!q && !sij) { tl.textContent = L.length.toLocaleString("fi-FI") + " toimistoa. Hae paikkakunnalla tai nimellä, tai näytä lähimmät."; out.innerHTML = ""; return; }
        tl.textContent = r.length.toLocaleString("fi-FI") + (r.length === 1 ? " toimisto" : " toimistoa") + (sij ? ", lähimmät ensin" : "");
        out.innerHTML = r.slice(0, 60).map(function (t) {
          return '<div class="toimisto"><b>' + esc(t.n) + '</b><span class="m"><span class="laji">' + esc(t.l) + "</span>" + esc([t.o, (t.pn + " " + t.k).trim()].filter(Boolean).join(", ")) +
            (t._e != null ? " · noin " + Math.round(t._e) + " km" : "") + "</span>" + (t.w ? '<span class="m"><a href="' + esc(t.w) + '" target="_blank" rel="noopener nofollow">' + esc(t.w.replace(/^https?:\/\//, "")) + "</a></span>" : "") +
            '<span class="m">Y-tunnus ' + esc(t.y) + "</span></div>";
        }).join("") + (r.length > 60 ? '<p class="mute">Näytetään 60 ensimmäistä. Tarkenna hakua.</p>' : "");
      }
      var tm; h.addEventListener("input", function () { clearTimeout(tm); tm = setTimeout(piirra, 120); });
      document.querySelectorAll("input[name=laji]").forEach(function (r) { r.onchange = piirra; });
      $("lahin").onclick = function () {
        if (!navigator.geolocation) { tl.textContent = "Selaimesi ei tue sijaintia. Hae paikkakunnalla."; return; }
        tl.textContent = "Haetaan sijaintia…";
        navigator.geolocation.getCurrentPosition(function (p) { sij = [p.coords.latitude, p.coords.longitude]; piirra(); },
          function () { tl.textContent = "Sijaintia ei saatu. Hae paikkakunnalla."; }, { timeout: 10000, maximumAge: 600000 });
      };
      fetch("/data/toimistot.json").then(function (r) { return r.json(); }).then(function (d) {
        L = d.t; L.forEach(function (t) { t._s = fold(t.n + " " + t.k + " " + t.pn); });
        var qs = new URLSearchParams(location.search), u = qs.get("q"), lj = qs.get("laji"); if (u) h.value = u;
        if (lj) document.querySelectorAll("input[name=laji]").forEach(function (r) { r.checked = r.value === lj; }); piirra();
      }).catch(function () { tl.textContent = "Toimistojen lataus epäonnistui."; });
    },
  };
})();
