/* Faktapisteen laskurit: lukee lomakkeen kentät, laskee sivun oman LASKE-funktion avulla ja näyttää tuloksen.
   Lisäksi kertoo palvelimelle anonyymisti sivun näytön ja ensimmäisen käytön (ei evästeitä, ei henkilötietoja). */
(function () {
  var F = document.querySelector("form.laskuri"); if (!F || typeof window.LASKE !== "function") return;
  var S = F.getAttribute("data-s"), T = F.querySelector(".tulos"), kaytetty = false;
  function ilmoita(t) { try { fetch("/api/laskuri", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ s: S, t: t }), keepalive: true }); } catch (e) {} }
  function luku(x) { var n = parseFloat(String(x).replace(/\s/g, "").replace(",", ".")); return isFinite(n) ? n : NaN; }
  function muoto(n, d) { return isFinite(n) ? n.toLocaleString("fi-FI", { minimumFractionDigits: d, maximumFractionDigits: d }) : "–"; }
  var f = {
    e: function (n) { return muoto(n, Math.abs(n) >= 1000 ? 0 : 2) + " €"; },
    e2: function (n) { return muoto(n, 2) + " €"; },
    n: function (n, d) { return muoto(n, d == null ? 2 : d); },
    p: function (n, d) { return muoto(n, d == null ? 1 : d) + " %"; }
  };
  function laske(kayttaja) {
    var v = {};
    Array.prototype.forEach.call(F.elements, function (el) {
      if (!el.name) return;
      v[el.name] = el.type === "checkbox" ? el.checked : (el.tagName === "SELECT" || el.dataset.teksti !== undefined ? el.value : luku(el.value));
    });
    var r; try { r = window.LASKE(v, f); } catch (e) { r = null; }
    if (!r || !r.length) { T.innerHTML = '<p class="mute">Täytä kentät, niin tulos näkyy tässä.</p>'; return; }
    T.innerHTML = r.map(function (x) {
      return '<div class="tr' + (x[2] ? " paa" : "") + '"><span>' + x[0] + "</span><b>" + x[1] + "</b></div>";
    }).join("");
    if (kayttaja && !kaytetty) { kaytetty = true; ilmoita("k"); }
  }
  F.addEventListener("input", function () { laske(true); });
  F.addEventListener("change", function () { laske(true); });
  F.addEventListener("submit", function (e) { e.preventDefault(); laske(true); });
  laske(false);
  ilmoita("n");
})();
