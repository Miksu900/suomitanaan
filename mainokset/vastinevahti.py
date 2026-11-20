"""Vastinevahti – Miikan oma työkalu vastinevideoita varten.
Etsii suomalaisesta mediasta (uutiset, Yle Areena, YouTube) uusia ja vanhoja kohtia, joissa islamia puolustetaan,
kaunistellaan tai kritiikkiä leimataan, ja tekee niistä valmiit pätkät Telegramiin:
  * uutiset  -> lainauskortti (PNG 1080x1920) + linkki
  * videot   -> pystyklippi (MP4 1080x1920, tekstitys, lähde ruudulla, -14 LUFS) + linkki
Arvioinnin tekee Claude Miikan näkökulmasta (islamkriittinen kommentaattori). Lainaukset tarkistetaan
sanatarkasti lähdetekstiä vasten, jotta mitään ei keksitä. Vain julkista mediasisältöä, ei yksityishenkilöitä.
Tila: vastinevahti.json (haara vastinevahti-tila). Artikkelit luetaan Uskontovahdin arkistosta (uskontovahti.json).
Ympäristö: AK (Anthropic), TG (Telegram), TILA = uudet | vanhat | molemmat, MAXV = videoita/ajo."""
import os, re, sys, json, html, glob, hashlib, subprocess, urllib.request, urllib.parse, datetime, textwrap

CHAT = "1893930799"
UA = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
AK = os.environ.get("AK", "").strip()
TG = os.environ.get("TG", "").strip()
TILA = os.environ.get("TILA", "molemmat") or "molemmat"
MAXV = int(os.environ.get("MAXV", "3") or 3)
MAXA_UUDET, MAXA_VANHAT = 80, 60          # artikkeleita/ajo arvioitavaksi
NYT = datetime.datetime.now(datetime.timezone.utc)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAKOKULMA = """Avustat Miika Koskelaa, joka tekee islamkriittisiä kommentti- ja vastinevideoita (TikTok, Facebook).
Tehtäväsi on löytää julkisesta mediasisällöstä kohtia, joihin Miika voi tehdä vastineen hänen näkökulmastaan. Olennaisia ovat esimerkiksi:
- islamia kuvataan rauhanuskonnoksi tai sen ongelmia kaunistellaan tai vähätellään (kunniaväkivalta, sharia, naisten asema, luopiot, radikalisoituminen, antisemitismi)
- islamin tai islamismin kritiikki leimataan islamofobiaksi, rasismiksi tai vihapuheeksi
- poliitikot, viranomaiset, kunnat, kirkko tai järjestöt edistävät tai puolustavat moskeijahankkeita, islamilaisia yhteisöjä, rukoustiloja, islamin opetusta tai niiden julkista rahoitusta
- muslimijärjestöjen tai -johtajien lausunnot, joissa vaaditaan erityiskohtelua tai torjutaan avoimuutta (esim. rahoituksen alkuperä)
- media jättää olennaisen taustan kertomatta tai esittää yksipuolisen myönteisen kuvan
Epäolennaisia: pelkät rikos- tai onnettomuusuutiset ilman islam-näkökulmaa, ulkomaiden sotauutiset ilman Suomi/Eurooppa-kytköstä, urheilu.
Arvioi rehellisesti: älä liioittele, älä keksi mitään, ja lainaa vain sanatarkasti sitä, mitä lähteessä oikeasti sanotaan."""


# ---------- apurit ----------
def hae(url, t=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t).read().decode("utf-8", "replace")

def claude(system, user, malli="claude-sonnet-4-5", tokens=2500):
    if not AK: return None
    for m in (malli, "claude-haiku-4-5"):
        d = json.dumps({"model": m, "max_tokens": tokens, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.anthropic.com/v1/messages", d,
                {"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"}), timeout=180).read())
            return r["content"][0]["text"]
        except Exception as e:
            print(f"CLAUDE-VIRHE ({m}):", str(e)[:200])
    return None

def json_osa(t, avaus="["):
    if not t: return None
    sulku = "]" if avaus == "[" else "}"
    try: return json.loads(t[t.index(avaus):t.rindex(sulku) + 1])
    except Exception: return None

def tg(metodi, kentat, tiedosto=None):
    if os.environ.get("EI_TG") == "1": return   # esim. Yle-pikaajo: Claude tarkistaa pätkät ennen Miikalle lähettämistä
    if not TG: print("TG puuttuu:", kentat.get("caption", kentat.get("text", ""))[:200]); return
    k = ["curl", "-sS", "--max-time", "120", f"https://api.telegram.org/bot{TG}/{metodi}"]
    for a, b in kentat.items(): k += ["--form-string", f"{a}={b}"]
    if tiedosto: k += ["-F", f"{tiedosto[0]}=@{tiedosto[1]}"]
    r = subprocess.run(k, capture_output=True, text=True)
    if '"ok":true' not in r.stdout: print("TG-VIRHE", r.stdout[:300], r.stderr[:200])

def puhdas(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    return re.sub(r"\s+", " ", t).strip()

def normi(t):
    return re.sub(r"[^0-9a-zåäö]+", " ", (t or "").lower()).strip()

def loytyy(lainaus, teksti):
    """Lainaus hyväksytään vain, jos se löytyy lähteestä (normalisoituna) sellaisenaan."""
    l, t = normi(lainaus), normi(teksti)
    if len(l) <= 15: return False
    if l in t: return True
    import difflib   # sallitaan pienet erot (välimerkit, puhujan johdanto); pisimmän yhtenäisen osan oltava >= 80 %
    m = difflib.SequenceMatcher(None, t, l, autojunk=False).find_longest_match(0, len(t), 0, len(l))
    return m.size >= 0.8 * len(l)


# ---------- artikkelit ----------
def artikkelin_teksti(url):
    if "news.google.com" in url: return ""
    try: s = hae(url)
    except Exception: return ""
    kpl = [puhdas(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", s, re.S | re.I)]
    kpl = [p for p in kpl if len(p) > 40 and not re.search(r"evästeet|cookie|tilaa |kirjaudu|copyright", p, re.I)]
    return "\n".join(kpl)[:12000]

def esiarvio(jutut):
    """Nopea otsikkoseulonta (Haiku): kuka 0-3 kiinnostava vastineen kannalta."""
    tulos = {}
    for i in range(0, len(jutut), 50):
        osa = jutut[i:i + 50]
        rivit = [{"i": n, "o": x["o"], "k": (x.get("k") or "")[:200], "l": x.get("l", "")} for n, x in enumerate(osa)]
        t = claude(NAKOKULMA + "\n\nPisteytä jokainen uutinen otsikon ja kuvauksen perusteella 0–3 sen mukaan, kuinka todennäköisesti siinä on vastineen arvoinen kohta (3 = erittäin todennäköisesti). Vastaa pelkkänä JSON-listana: [{\"i\":0,\"p\":2}, ...]",
                   json.dumps(rivit, ensure_ascii=False), "claude-haiku-4-5", 3000)
        for r in json_osa(t) or []:
            try: tulos[osa[int(r["i"])]["u"]] = int(r["p"])
            except Exception: pass
    return tulos

def arvioi_artikkeli(x, teksti):
    sisalto = f"OTSIKKO: {x['o']}\nLÄHDE: {x.get('l','')}\nPVM: {x['t'][:10]}\nKUVAUS: {x.get('k','')}\n\nTEKSTI:\n{teksti or '(ei saatavilla – arvioi otsikon ja kuvauksen perusteella, lainaus tyhjäksi)'}"
    t = claude(NAKOKULMA + """

Arvioi tämä juttu. Vastaa pelkkänä JSON-objektina:
{"sopii": true/false, "arvo": 1-3, "aihe": "lyhyt aihe", "lainaus": "sanatarkka lainaus tekstistä (max 45 sanaa) tai tyhjä",
 "puhuja": "kuka lainauksen sanoi (nimi ja asema) tai tyhjä", "miksi": "1-2 lausetta: miksi tähän kannattaa tehdä vastine",
 "vastine": "ehdotus Miikan vastinevideon ydinlauseeksi (1-2 lausetta, hänen äänellään, asiallinen ja faktapohjainen)"}""", sisalto)
    return json_osa(t, "{")

def kortti(polku, otsikko, lainaus, puhuja, lahde, pvm):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), (18, 20, 26)); d = ImageDraw.Draw(im)
    f = lambda s, b=False: ImageFont.truetype(FONTB if b else FONT, s)
    d.rectangle([0, 0, W, 14], fill=(200, 30, 30))
    d.text((70, 120), "MEDIASSA SANOTTUA", font=f(40, True), fill=(220, 60, 60))
    y = 210
    for r in textwrap.wrap(otsikko, 30)[:4]:
        d.text((70, y), r, font=f(56, True), fill=(255, 255, 255)); y += 72
    y += 60
    if lainaus:
        d.text((60, y - 20), "”", font=f(160, True), fill=(200, 30, 30)); y += 110
        for r in textwrap.wrap(lainaus, 28)[:10]:
            d.text((90, y), r, font=f(54), fill=(240, 236, 220)); y += 70
        if puhuja:
            y += 30
            for r in textwrap.wrap("– " + puhuja, 34)[:2]:
                d.text((90, y), r, font=f(40, True), fill=(200, 200, 200)); y += 52
    d.text((70, H - 200), "Lähde:", font=f(34, True), fill=(160, 160, 160))
    for n, r in enumerate(textwrap.wrap(f"{lahde}, {pvm}", 44)[:2]):
        d.text((70, H - 150 + n * 46), r, font=f(36), fill=(200, 200, 200))
    im.save(polku)


# ---------- videot ----------
YT_HAUT = ["islam rauhanuskonto", "islam on rauhan uskonto", "islamofobia", "islamofobia Suomi", "muslimivastaisuus",
           "muslimit Suomessa", "islam Suomessa keskustelu", "moskeija Suomi", "Yle islam", "A-studio islam",
           "muslimi rasismi Suomi", "imaami Suomi", "islamilainen yhdyskunta", "kunniaväkivalta Suomi", "moskeijahanke"]
AREENA = "https://areena.api.yle.fi/v1/ui/search?app_id=areena-web-items&app_key=wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN&language=fi&v=10&client=yle-areena-web&offset=0&limit=40&service=tv&query="
AREENA_HAUT = ["islam", "muslimit", "moskeija", "islamofobia", "imaami", "ramadan"]
# Yle-kokoelma (paljastusvideo): laajemmat aiheet, joissa vinouma näkyy
YLE_HAUT = ["islam", "muslimit", "muslimi", "moskeija", "islamofobia", "maahanmuutto", "maahanmuuttajat", "turvapaikanhakijat",
            "rasismi", "äärioikeisto", "perussuomalaiset", "monikulttuurisuus", "vihapuhe", "pakolaiset", "kotoutuminen", "ramadan",
            "huivi", "Gaza", "Palestiina", "somali", "syrjintä", "A-studio maahanmuutto", "MOT maahanmuutto", "Ykkösaamu maahanmuutto",
            "Spotlight islam", "rasismi Suomessa", "ennakkoluulot", "monikulttuurinen Suomi", "uskonnonvapaus", "Israel",
            "A-studio", "A-talk", "Ykkösaamu", "Pressiklubi", "MOT", "Spotlight", "Perjantai", "Yle Uutiset", "Silminnäkijä",
            "hallitus leikkaukset", "Purra", "Riikka Purra", "Orpon hallitus", "turvapaikka", "perheenyhdistäminen", "kansalaisuus"]
YLE_NAKOKULMA = """Avustat Miika Koskelaa, joka tekee paljastusvideon Ylen journalismin vasemmistovinoumasta ja islam- ja maahanmuuttomyönteisyydestä.
Etsi Ylen ohjelmista lyhyitä kohtia (8–25 s), joissa VINOUMA NÄKYY YLEN OMASSA TOIMINNASSA niin selvästi, että tavallinen katsoja huomaa sen ilman selitystä:
- Ylen toimittaja, juontaja tai selostusääni käyttää leimaavia tai arvottavia sanoja vain yhteen suuntaan (esim. "äärioikeisto", "populisti", "vihapuhe", "rasistinen" kriitikoista – vastaavia ei käytetä vasemmistosta tai islamisteista)
- toimittaja ottaa itse kantaa, esittää johdattelevan kysymyksen tai selittää ongelman pois (esim. maahanmuuton kustannukset, rikollisuus, työttömyys, kunniaväkivalta)
- kriitikko tai perussuomalainen esitetään naurettavana, pelottavana tai epäluotettavana, tai häntä keskeytetään/painostetaan selvästi tiukemmin kuin muita
- islam tai islamilainen toimija esitetään kritiikittömästi tavalla, jossa toimittaja itse kaunistelee tai ohittaa ilmeisen ongelman
EI kelpaa: pelkkä myönteinen henkilötarina, haastateltavan oma mielipide ilman toimittajan kannanottoa, neutraali uutisointi, juhlapyhäjutut.
Ole tiukka: jos vinouma ei näy itse pätkästä, älä valitse mitään (palauta tyhjä lista). Mieluummin ei yhtään kuin heikko pätkä."""

def yt_haku(q, uusi):
    lkm = 25
    k = ["yt-dlp", "--flat-playlist", "-J", "--no-warnings", (f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}&sp=CAI%253D" if uusi else f"ytsearch{lkm}:{q}")]
    try:
        r = subprocess.run(k, capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout or "null") or {}
        if not d: print("YT-HAKU TYHJÄ", q, r.stderr[-200:])
    except Exception as e:
        print("YT-HAKUVIRHE", q, e); return []
    out = []
    for e in d.get("entries") or []:
        if not e or not e.get("id"): continue
        dur = e.get("duration") or 0
        if dur and (dur < 30 or dur > 60 * 60): continue
        out.append({"id": "yt:" + e["id"], "url": f"https://www.youtube.com/watch?v={e['id']}", "o": e.get("title") or "",
                    "kanava": e.get("channel") or e.get("uploader") or "YouTube", "kesto": dur, "k": (e.get("description") or "")[:300]})
    return out

def areena_haku(q, sivuja=1):
    data = []
    for sv in range(sivuja):
        try: d = json.loads(hae(AREENA.replace("offset=0", f"offset={sv * 40}") + urllib.parse.quote(q)))
        except Exception as e:
            print("AREENA-HAKUVIRHE", q, str(e)[:120]); break
        data += d.get("data") or []
        if len(d.get("data") or []) < 40: break
    out = []
    for e in data:
        uri = json.dumps(e)
        m = re.search(r"(1-\d{5,})", uri)
        if not m: continue
        o = e.get("title") or ""
        if isinstance(o, dict): o = o.get("fi") or next(iter(o.values()), "")
        kuv = e.get("description") or ""
        if isinstance(kuv, dict): kuv = kuv.get("fi") or ""
        out.append({"id": "areena:" + m.group(1), "url": f"https://areena.yle.fi/{m.group(1)}", "o": str(o), "kanava": "Yle Areena",
                    "kesto": 0, "k": str(kuv)[:300]})
    return out

def lataa(v, kansio):
    os.makedirs(kansio, exist_ok=True)
    mv = int(os.environ.get("MINVUOSI", "0") or 0)
    if mv:
        try:
            u = subprocess.run(["yt-dlp", "--no-warnings", "--skip-download", "--print", "%(upload_date)s", v["url"]], capture_output=True, text=True, timeout=120).stdout.strip()[:4]
            if u.isdigit() and int(u) < mv: print("Liian vanha (metatieto), ohitetaan:", u, v["url"]); return None, None, {}
        except Exception: pass
    k = ["yt-dlp", "--no-warnings", "-q", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
         "--write-subs", "--write-auto-subs", "--sub-langs", "fi.*,fin.*,fi", "--convert-subs", "srt",
         "--max-filesize", "1500M", "-o", f"{kansio}/v.%(ext)s", "--print-to-file", "%(upload_date)s|%(title)s|%(channel)s", f"{kansio}/meta.txt", v["url"]]
    r = subprocess.run(k, capture_output=True, text=True, timeout=1800)
    vids = [p for p in glob.glob(f"{kansio}/v.*") if p.endswith((".mp4", ".mkv", ".webm"))]
    if not vids: print("LATAUS EPÄONNISTUI", v["url"], r.stderr[-300:]); return None, None, {}
    subs = [p for p in glob.glob(f"{kansio}/v*.srt")]
    meta = {}
    try:
        u, o, c = open(f"{kansio}/meta.txt").read().strip().split("\n")[0].split("|", 2)
        meta = {"pvm": f"{u[6:8]}.{u[4:6]}.{u[:4]}" if len(u) == 8 else "", "o": o, "kanava": c}
    except Exception: pass
    return vids[0], (subs[0] if subs else None), meta

def srt_luku(p):
    out = []
    for blokki in re.split(r"\n\s*\n", open(p, encoding="utf-8", errors="replace").read()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\n(.*)", blokki, re.S)
        if not m: continue
        g = list(map(int, m.groups()[:8]))
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        t = puhdas(m.group(9))
        if t and (not out or out[-1][2] != t): out.append((a, b, t))
    return out

def litteroi(video):
    from faster_whisper import WhisperModel
    global _MALLI
    if "_MALLI" not in globals(): _MALLI = WhisperModel(os.environ.get("WHISPER", "small"), compute_type="int8")
    import numpy as np   # ääni puretaan ffmpegillä (PyAV-versioriippuvuus ohitetaan)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    segs, _ = _MALLI.transcribe(np.frombuffer(raw, np.float32), language="fi", vad_filter=True, beam_size=int(os.environ.get("BEAM", "5")))
    return [(s.start, s.end, s.text.strip()) for s in segs]

def valitse_kohdat(v, segs, yle=False):
    rivit = "\n".join(f"[{a:.1f}-{b:.1f}] {t}" for a, b, t in segs)[:60000]
    t = claude((YLE_NAKOKULMA if yle else NAKOKULMA) + """

Saat videon litteroinnin aikaleimoineen. Valitse enintään 2 parasta kohtaa. Jokainen kohta """ + ("8–25" if yle else "12–55") + """ sekuntia,
alkaa ja päättyy lauseen rajalla, ja sisältää itse väitteen niin, että se ymmärtää ilman muuta kontekstia.
Jos videossa ei ole vastineen arvoista kohtaa, palauta tyhjä lista. Vastaa pelkkänä JSON-listana:
[{"alku": 123.4, "loppu": 160.2, "lainaus": "ydinlause sanatarkasti litteroinnista", "puhuja": "kuka puhuu (jos tiedossa)",
  "miksi": "miksi tähän kannattaa vastata", "vastine": "ehdotus Miikan vastinelauseeksi\"""" + (""",
  "osa": 1 (1 = islammyönteisyys, 2 = maahanmuutto ja kotoutuminen, 3 = toimittajien sanavalinnat ja haastateltavat)""" if yle else "") + "}]",
               f"VIDEO: {v['o']}\nKANAVA: {v.get('kanava','')}\nKUVAUS: {v.get('k','')}\n\nLITTEROINTI:\n{rivit}", tokens=2000)
    return json_osa(t) or []

def ass_aika(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

def leikkaa(video, segs, a, b, lahde, ulos):
    a = max(0.0, a - 0.3); b = b + 0.4; kesto = b - a
    cues = [(max(s, a) - a, min(e, b) - a, t) for s, e, t in segs if e > a and s < b]
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: S,DejaVu Sans,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,1,2,60,60,380,1",
           "Style: H,DejaVu Sans,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,3,10,0,8,50,50,120,1",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ass.append(f"Dialogue: 0,{ass_aika(0)},{ass_aika(kesto)},H,,0,0,0,,{lahde.replace(',', '‚')}")
    for s, e, t in cues:
        rivit = "\\N".join(textwrap.wrap(t, 30)[:3])
        ass.append(f"Dialogue: 0,{ass_aika(s)},{ass_aika(e)},S,,0,0,0,,{rivit}")
    open("/tmp/klippi.ass", "w").write("\n".join(ass) + "\n")
    # äänitaso -14 LUFS (yksinkertainen vahvistus + rajoitin)
    r = subprocess.run(["ffmpeg", "-ss", str(a), "-t", str(kesto), "-i", video, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    try: g = -14 - float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0])
    except Exception: g = 0
    vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:2,eq=brightness=-0.15[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles=/tmp/klippi.ass[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-t", str(kesto), "-i", video, "-filter_complex", vf,
                    "-map", "[v]", "-map", "0:a?", "-af", f"volume={g:.1f}dB,alimiter=limit=0.89:level=false", "-r", "30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", ulos], check=True)

def kokoelmaan(polku, nimi):
    """Tallentaa Yle-kokoelman pätkän GitHub-releaseen 'yle-kokoelma' (paljastusvideota varten)."""
    tok, repo = os.environ.get("GH_TOKEN", ""), os.environ.get("GITHUB_REPOSITORY", "")
    if not tok or not repo: return ""
    h = ["-H", f"authorization: Bearer {tok}", "-H", "accept: application/vnd.github+json"]
    r = subprocess.run(["curl", "-sS", *h, f"https://api.github.com/repos/{repo}/releases/tags/yle-kokoelma"], capture_output=True, text=True).stdout
    rid = (json.loads(r or "{}") or {}).get("id")
    if not rid:
        r = subprocess.run(["curl", "-sS", *h, "-X", "POST", f"https://api.github.com/repos/{repo}/releases", "-d",
                            json.dumps({"tag_name": "yle-kokoelma", "name": "Yle-kokoelma (paljastusvideo)", "body": "Vastinevahdin keräämät Yle-pätkät"})],
                           capture_output=True, text=True).stdout
        rid = (json.loads(r or "{}") or {}).get("id")
    if not rid: print("RELEASE-VIRHE", r[:200]); return ""
    r = subprocess.run(["curl", "-sS", *h, "-H", "content-type: video/mp4", "--data-binary", f"@{polku}",
                        f"https://uploads.github.com/repos/{repo}/releases/{rid}/assets?name={urllib.parse.quote(nimi)}"], capture_output=True, text=True).stdout
    return (json.loads(r or "{}") or {}).get("browser_download_url", "")

def mmss(s):
    s = int(s); return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


# ---------- pääohjelma ----------
def tallenna():
    if os.environ.get("EI_TILAA") == "1": return
    json.dump({"kasitellyt": sorted(kas)[-60000:], "loydot": loydot[-3000:]}, open("vastinevahti.json", "w"), ensure_ascii=False)

if __name__ == "__main__":
    import atexit
    try: tila = json.load(open("vastinevahti.json"))
    except Exception: tila = {}
    kas = set(tila.get("kasitellyt", [])); loydot = tila.get("loydot", [])
    atexit.register(tallenna)
    VAIN = os.environ.get("VAIN", "")   # "videot" = ohita uutiset, "uutiset" = ohita videot
    try: arkisto = json.load(open("uskontovahti.json")).get("arkisto", [])
    except Exception: arkisto = []
    fi = [x for x in arkisto if x.get("a") != "eu" and x.get("u") and x["u"] not in kas]
    raja = (NYT - datetime.timedelta(days=4)).isoformat()[:16]
    ehdokkaat = []
    if TILA in ("uudet", "molemmat"): ehdokkaat += sorted([x for x in fi if x["t"] >= raja], key=lambda x: x["t"], reverse=True)[:MAXA_UUDET]
    if TILA in ("vanhat", "molemmat"): ehdokkaat += sorted([x for x in fi if x["t"] < raja], key=lambda x: x["t"], reverse=True)[:MAXA_VANHAT]
    print(f"Artikkeleita arvioitavaksi: {len(ehdokkaat)} (arkistossa {len(arkisto)}, Suomi käsittelemättä {len(fi)})")
    if VAIN in ("videot", "yle"): ehdokkaat = []
    pisteet = esiarvio(ehdokkaat) if ehdokkaat else {}
    lahetetty = 0
    for x in ehdokkaat:
        kas.add(x["u"])
        if pisteet.get(x["u"], 0) < 2: continue
        teksti = artikkelin_teksti(x["u"])
        a = arvioi_artikkeli(x, teksti)
        if not a or not a.get("sopii") or int(a.get("arvo", 0) or 0) < 2: continue
        lainaus = a.get("lainaus") or ""
        if lainaus and not loytyy(lainaus, teksti): print("Lainaus ei löytynyt lähteestä, jätetään pois:", lainaus[:80]); lainaus = ""
        pvm = x["t"][:10]; pvm = f"{int(pvm[8:10])}.{int(pvm[5:7])}.{pvm[:4]}"
        p = f"/tmp/kortti_{hashlib.md5(x['u'].encode()).hexdigest()[:8]}.png"
        kortti(p, x["o"], lainaus, a.get("puhuja", ""), x.get("l", ""), pvm)
        cap = (f"📰 <b>{html.escape(x['o'])}</b>\n{html.escape(x.get('l',''))}, {pvm}\n\n"
               + (f"„{html.escape(lainaus)}” – {html.escape(a.get('puhuja',''))}\n\n" if lainaus else "")
               + f"🎯 {html.escape(a.get('miksi',''))}\n💬 Vastine-idea: {html.escape(a.get('vastine',''))}\n\n{x['u']}")[:1020]
        tg("sendPhoto", {"chat_id": CHAT, "caption": cap, "parse_mode": "HTML"}, ("photo", p)); lahetetty += 1
        loydot.append({"tyyppi": "uutinen", "u": x["u"], "o": x["o"], "l": x.get("l", ""), "t": x["t"], **{k: a.get(k, "") for k in ("aihe", "puhuja", "miksi", "vastine")}, "lainaus": lainaus})

    # Videot. YouTube estää lataukset GitHubin palvelimilta, joten YouTubesta tulee vain linkki-ilmoitus;
    # Yle Areenasta tehdään valmiit pätkät. VAIN=yle -> Yle-kokoelma (paljastusvideo).
    YLE = VAIN == "yle"
    videot = []
    if VAIN not in ("uutiset", "yle"):
        for q in YT_HAUT:
            if TILA in ("uudet", "molemmat"): videot += yt_haku(q, True)
            if TILA in ("vanhat", "molemmat"): videot += yt_haku(q, False)
    if VAIN != "uutiset":
        for q in (YLE_HAUT if YLE else AREENA_HAUT): videot += areena_haku(q, 5 if YLE else 1)
    etu = "yle:" if YLE else ""
    nahty = set(); videot = [v for v in videot if etu + v["id"] not in kas and not (v["id"] in nahty or nahty.add(v["id"]))]
    ohita = set(x.strip() for x in os.environ.get("OHITA", "").split(",") if x.strip())
    if ohita: videot = [v for v in videot if v["id"].split(":")[-1] not in ohita]
    SH, SHS = int(os.environ.get("SHARD", "0") or 0), int(os.environ.get("SHARDS", "1") or 1)
    if SHS > 1: videot = [v for v in videot if int(hashlib.md5(v["id"].encode()).hexdigest(), 16) % SHS == SH]
    print(f"Videoehdokkaita: {len(videot)} (Areena {sum(v['id'].startswith('areena') for v in videot)})")
    vp = {}
    ohje = (YLE_NAKOKULMA + "\n\nPisteytä Ylen ohjelmat otsikon ja kuvauksen perusteella 0–3: kuinka todennäköisesti ohjelmassa on lyhyt kohta, joka näyttää vinouman selvästi."
            if YLE else NAKOKULMA + "\n\nPisteytä videot otsikon, kanavan ja kuvauksen perusteella 0–3: kuinka todennäköisesti videossa on suomenkielinen kohta, johon Miika voi tehdä vastineen. Ei-suomenkieliset = 0.")
    for i in range(0, len(videot), 50):
        osa = videot[i:i + 50]
        t = claude(ohje + " Vastaa pelkkänä JSON-listana: [{\"i\":0,\"p\":2}]",
                   json.dumps([{"i": n, "o": v["o"], "c": v["kanava"], "k": v["k"][:200]} for n, v in enumerate(osa)], ensure_ascii=False), "claude-haiku-4-5", 3000)
        for r in json_osa(t) or []:
            try: vp[osa[int(r["i"])]["id"]] = int(r["p"])
            except Exception: pass
    for v in videot:
        if vp.get(v["id"], 0) < 2: kas.add(etu + v["id"])
    yt = [v for v in videot if v["id"].startswith("yt:") and vp.get(v["id"], 0) >= 3][:6]
    if yt:
        tg("sendMessage", {"chat_id": CHAT, "parse_mode": "HTML", "disable_web_page_preview": "true", "text":
            "▶️ <b>YouTube: mahdollisia vastinevideoita</b>\n(YouTube estää automaattisen leikkauksen – lähetä video minulle, niin teen pätkän)\n\n"
            + "\n\n".join(f"• {html.escape(v['o'])} <i>({html.escape(v['kanava'])})</i>\n{v['url']}" for v in yt)})
        kas.update(v["id"] for v in yt)
    OFFSET, SHARD, SHARDS = int(os.environ.get("OFFSET", "0") or 0), int(os.environ.get("SHARD", "0") or 0), int(os.environ.get("SHARDS", "1") or 1)
    raja_p = int(os.environ.get("RAJA", "2") or 2)
    valitut = sorted([v for v in videot if v["id"].startswith("areena") and vp.get(v["id"], 0) >= raja_p], key=lambda v: -vp[v["id"]])[OFFSET:OFFSET + MAXV]
    print(f"Ladataan {len(valitut)} Areena-ohjelmaa")
    for n, v in enumerate(valitut):
        kas.add(etu + v["id"])
        kansio = f"/tmp/v{n}"
        try:
            video, srt, meta = lataa(v, kansio)
            if not video: continue
            mv = int(os.environ.get("MINVUOSI", "0") or 0)
            if mv and meta.get("pvm") and int(meta["pvm"][-4:]) < mv:
                print("Liian vanha, ohitetaan:", meta.get("pvm"), v["url"]); continue
            segs = srt_luku(srt) if srt else []
            print("Tekstitys:", "Ylen oma" if len(segs) >= 5 else "litteroidaan", v["url"])
            if len(segs) < 5: segs = litteroi(video)
            kohdat = valitse_kohdat({**v, **{k: meta[k] for k in ("o",) if meta.get(k)}}, segs, YLE)
            pvm = meta.get("pvm", "")
            for j, k in enumerate(kohdat[:1 if YLE else 2]):   # Yle-kokoelmaan yksi pätkä per ohjelma
                a, b = float(k["alku"]), float(k["loppu"])
                if b - a < 4 or b - a > 75: continue
                lainaus = k.get("lainaus", "")
                if lainaus and not loytyy(lainaus, " ".join(t for s, e, t in segs)): lainaus = ""
                nimi = (meta.get("o") or v["o"])[:60]
                lahde = f"Lähde: Yle – {nimi}" + (f", {pvm}" if pvm else "")
                ulos = f"{kansio}/klippi{j}.mp4"
                leikkaa(video, segs, a, b, lahde, ulos)
                nro, linkki = "", ""
                if YLE:
                    nro = os.environ.get("NROETU", "") + str(sum(1 for x in loydot if x.get("tyyppi") == "yle") + 1)
                    linkki = kokoelmaan(ulos, f"yle{nro}_{v['id'].split(':')[1]}_{int(a)}.mp4")
                OSAT = {1: "Osa 1: Islammyönteisyys", 2: "Osa 2: Maahanmuutto", 3: "Osa 3: Sanavalinnat ja haastateltavat"}
                try: osa = int(k.get("osa") or 0)
                except Exception: osa = 0
                cap = ((f"🔴 <b>YLEN PALJASTUSVIDEO – pätkä #{nro}</b>\n{OSAT.get(osa, '')}\n\n" if YLE else "🎬 ")
                       + f"<b>{html.escape(meta.get('o') or v['o'])}</b>\nYle{', ' + pvm if pvm else ''} · kohta {mmss(a)}–{mmss(b)}\n\n"
                       + (f"„{html.escape(lainaus)}” – {html.escape(k.get('puhuja',''))}\n\n" if lainaus else "")
                       + f"🎯 {html.escape(k.get('miksi',''))}\n💬 {'Kommentti-idea' if YLE else 'Vastine-idea'}: {html.escape(k.get('vastine',''))}\n\n{v['url']}")[:1020]
                tg("sendVideo", {"chat_id": CHAT, "caption": cap, "parse_mode": "HTML", "supports_streaming": "true"}, ("video", ulos)); lahetetty += 1
                loydot.append({"tyyppi": "yle" if YLE else "video", "nro": nro, "u": v["url"], "o": meta.get("o") or v["o"], "t": pvm,
                               "alku": a, "loppu": b, "lainaus": lainaus, "tiedosto": linkki, "osa": k.get("osa", ""), **{x: k.get(x, "") for x in ("puhuja", "miksi", "vastine")}})
                tallenna()
        except Exception as e:
            print("VIDEOVIRHE", v["url"], str(e)[:300])
        subprocess.run(["rm", "-rf", kansio])
    print(f"::notice title=Vastinevahti::{lahetetty} pätkää Telegramiin; löytöjä yhteensä {len(loydot)}")
    if lahetetty == 0 and os.environ.get("TAPAHTUMA") == "workflow_dispatch":
        tg("sendMessage", {"chat_id": CHAT, "text": "Vastinevahti: tällä ajolla ei löytynyt uusia vastineen arvoisia kohtia."})
