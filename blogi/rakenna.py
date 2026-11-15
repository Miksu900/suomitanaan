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
:root{--bg:#fbfaf7;--fg:#1c1b19;--muted:#6b6862;--line:#e4e0d8;--accent:#9b1c1c;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe7;--muted:#a19e97;--line:#2c2b29;--accent:#e06666;--card:#1c1c1a}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:18px/1.7 Georgia,'Iowan Old Style','Times New Roman',serif}
a{color:var(--accent)}a:hover{text-decoration-thickness:2px}
.wrap{max-width:680px;margin:0 auto;padding:0 18px}
header.top{border-bottom:1px solid var(--line);padding:26px 0 18px}
header.top a.nimi{font:700 26px/1.2 system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--fg);text-decoration:none;letter-spacing:-.01em}
header.top p{margin:4px 0 0;color:var(--muted);font:15px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}
main{padding:28px 0 60px}
.lista article{padding:22px 0;border-bottom:1px solid var(--line)}
.lista h2{margin:0 0 6px;font:700 24px/1.3 system-ui,-apple-system,'Segoe UI',sans-serif;letter-spacing:-.01em}
.lista h2 a{color:var(--fg);text-decoration:none}.lista h2 a:hover{color:var(--accent)}
.meta{color:var(--muted);font:14px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}
.lista p{margin:8px 0 0}
article.kirjoitus h1{font:800 34px/1.2 system-ui,-apple-system,'Segoe UI',sans-serif;letter-spacing:-.02em;margin:0 0 10px}
article.kirjoitus .sisalto{margin-top:26px}
article.kirjoitus h2{font:700 22px/1.3 system-ui,-apple-system,'Segoe UI',sans-serif;margin:34px 0 8px}
blockquote{margin:22px 0;padding:4px 0 4px 18px;border-left:3px solid var(--accent);color:var(--muted)}
.jaa{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);font:15px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}
.jaa a,.jaa button{display:inline-block;margin:6px 8px 0 0;padding:8px 14px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--fg);text-decoration:none;font:inherit;cursor:pointer}
.jaa a:hover,.jaa button:hover{border-color:var(--accent)}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--muted);font:14px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}
@media (max-width:520px){body{font-size:17px}article.kirjoitus h1{font-size:28px}.lista h2{font-size:21px}}
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
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><a class="nimi" href="/">{html.escape(NIMI)}</a><p>{html.escape(KUVAUS)}</p></div></header>
<main><div class="wrap">{runko}</div></main>
<footer><div class="wrap">© {TANAAN.year} {html.escape(NIMI)} · Kirjoitukset ovat kirjoittajan omia näkemyksiä · <a href="/rss.xml">RSS</a></div></footer>
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
        f'<article><h2><a href="/{k["polku"]}/">{html.escape(k["otsikko"])}</a></h2>'
        f'<div class="meta">{pvm_teksti(k["pvm"])} · {k["min"]} min lukuaika</div>'
        + (f'<p>{html.escape(k["tiiv"])}</p>' if k["tiiv"] else "") + "</article>" for k in kk)
    kirjoita("/", sivu(NIMI, KUVAUS, f'<section class="lista">{lista or "<p>Ensimmäinen kirjoitus tulossa pian.</p>"}</section>'))
    for k in kk:
        p = f'/{k["polku"]}/'
        url = (OSOITE + p) if OSOITE else ""
        jaa = (f'<div class="jaa">Jaa kirjoitus:<br>'
               f'<a href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener">Facebook</a>'
               f'<a href="https://x.com/intent/post?url={url}" target="_blank" rel="noopener">X</a>'
               f'<a href="https://wa.me/?text={url}" target="_blank" rel="noopener">WhatsApp</a>'
               f'<button onclick="navigator.clipboard.writeText(location.href);this.textContent=\'Linkki kopioitu\'">Kopioi linkki</button></div>')
        runko = (f'<article class="kirjoitus"><h1>{html.escape(k["otsikko"])}</h1>'
                 f'<div class="meta">{html.escape(NIMI)} · {pvm_teksti(k["pvm"])} · {k["min"]} min lukuaika</div>'
                 f'<div class="sisalto">{k["html"]}</div>{jaa}'
                 f'<p class="meta" style="margin-top:30px"><a href="/">← Kaikki kirjoitukset</a></p></article>')
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
