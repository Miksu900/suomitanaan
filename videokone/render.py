"""Videokone: renderöi pystyvideon (1080x1920) tiedostoista aihe.json, aani.mp3 ja ajoitus.json.

Kohtaukset seuraavat käsikirjoituksen viittä lausetta. Tyypit: korjaus, huijaus, eduskunta.
Aja: python3 videokone/render.py  (PV=1,5,9 tekee esikatselukuvat videon sijaan)
"""
import json, math, os, re, subprocess, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HERE = pathlib.Path(__file__).parent
W, H, FPS = 1080, 1920, 30
TEMPO = float(os.environ.get("TEMPO", "1.05"))
OUT = os.environ.get("ULOS", "video.mp4")
def F(n, s): return ImageFont.truetype(str(HERE / "fontit" / n), s)
ANTON = lambda s: F("Anton.ttf", s); M9 = lambda s: F("Mont900.ttf", s); M8 = lambda s: F("Mont800.ttf", s); M6 = lambda s: F("Mont600.ttf", s)
WHITE = (255, 255, 255); YEL = (255, 210, 70); GOLD = (245, 197, 66); NAVY = (11, 31, 69); GREY = (170, 182, 205)
RED = (225, 60, 75); GREEN = (40, 185, 110)

A = json.load(open("aihe.json"))
TYYPPI, D = A["tyyppi"], A["data"]
al = json.load(open("ajoitus.json"))
ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
txt = "".join(ch)
words = [(m.group(), st[m.start()] / TEMPO, en[m.end() - 1] / TEMPO) for m in re.finditer(r"\S+", txt)]
# lauseiden alut käsikirjoituksen lauseista (merkkipaikat), varalla välimerkkijako
sent_starts, pos = [], 0
for s in A["lauseet"]:
    i = txt.find(s[:12], pos)
    if i < 0: break
    sent_starts.append(st[i] / TEMPO); pos = i + len(s) - 2
if len(sent_starts) != 5:
    sent_starts = [0.0] + [st[m.end()] / TEMPO for m in re.finditer(r"[.?!]\s", txt)][:4]
    while len(sent_starts) < 5: sent_starts.append(sent_starts[-1] + 2)
sent_starts[0] = 0.0
DUR = en[-1] / TEMPO + 1.8
N = int(DUR * FPS)
SC = sent_starts + [DUR]
print("lauseet", [round(x, 1) for x in sent_starts], "kesto", round(DUR, 1))

# ---------- apurit ----------
def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def back(t): t = max(0, min(1, t)); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def text_img(s, font, color=WHITE, stroke=0, sc=(0, 0, 0), shadow=True):
    b = font.getbbox(s, stroke_width=stroke); w, h = b[2] - b[0] + 40, b[3] - b[1] + 40
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((20 - b[0] + 4, 20 - b[1] + 6), s, font=font, fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((20 - b[0], 20 - b[1]), s, font=font, fill=color, stroke_width=stroke, stroke_fill=sc)
    return im
def pill(s, font, fg, bg, px=28, py=14):
    b = font.getbbox(s); w, h = b[2] - b[0] + 2 * px, b[3] - b[1] + 2 * py
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg); d.text((px - b[0], py - b[1]), s, font=font, fill=fg)
    return im
def wrap(s, font, maxw):
    out, line = [], ""
    for w_ in s.split():
        t = (line + " " + w_).strip()
        if font.getlength(t) <= maxw: line = t
        else:
            if line: out.append(line)
            line = w_
    out.append(line); return out
def paste_c(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def iso_teksti(s, maxw=960, koko=170, vari=WHITE, vari2=GOLD):
    """Iso otsikko 1–3 riville, viimeinen rivi korostevärillä."""
    k = koko
    while True:
        f = ANTON(k); r = wrap(s.upper(), f, maxw)
        if (len(r) <= 3 and all(f.getlength(x) <= maxw for x in r)) or k < 70: break
        k -= 10
    ims = [text_img(x, f, vari2 if i == len(r) - 1 and len(r) > 1 else vari) for i, x in enumerate(r)]
    h = sum(i.height - 30 for i in ims) + 30
    c = Image.new("RGBA", (max(i.width for i in ims), h), (0, 0, 0, 0)); y = 0
    for i in ims: c.alpha_composite(i, ((c.width - i.width) // 2, y)); y += i.height - 30
    return c
def kortti(otsake, teksti, vari, w=960, fs=50, yliviivaus=0.0, tausta=(250, 250, 252), hl=None):
    f = M8(fs); rivit = wrap(teksti, f, w - 90)
    if len(rivit) > 6:
        rivit = rivit[:6]; rivit[-1] = rivit[-1] + "…"
    lh = int(fs * 1.34); h = 110 + len(rivit) * lh + 30
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=28, fill=tausta + (255,))
    d.rounded_rectangle((0, 0, 18, h - 1), radius=9, fill=vari + (255,))
    d.text((46, 28), otsake, font=M9(34), fill=vari)
    y = 96
    for r in rivit:
        x = 46
        for wd in r.split():
            ww = f.getlength(wd)
            if hl and any(h_ and h_.lower() in wd.lower() for h_ in hl):
                d.rounded_rectangle((x - 6, y - 2, x + ww + 6, y + fs * 1.12), radius=8, fill=(255, 214, 90))
            d.text((x, y), wd, font=f, fill=(20, 22, 28)); x += ww + f.getlength(" ")
        if yliviivaus > 0:
            lw = f.getlength(r)
            d.rectangle((40, y + fs * 0.55, 40 + (lw + 12) * yliviivaus, y + fs * 0.55 + 7), fill=RED + (255,))
        y += lh
    return c

# ---------- tausta ----------
yy = np.linspace(0, 1, H)[:, None]
bg = np.zeros((H, W, 3), np.float32)
bg[..., 0] = 8 + 8 * yy; bg[..., 1] = 18 + 14 * yy; bg[..., 2] = 50 + 30 * (1 - yy)
BG = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
def glow(r, col, a):
    g = Image.new("RGBA", (r * 2, r * 2), col + (0,)); q = int(r * 0.45)
    ImageDraw.Draw(g).ellipse((q, q, r * 2 - q, r * 2 - q), fill=col + (a,))
    return g.filter(ImageFilter.GaussianBlur(r // 4))
KOROSTE = {"korjaus": (150, 90, 230), "huijaus": (230, 70, 70), "eduskunta": (40, 110, 255), "uutinen": (245, 197, 66)}[TYYPPI]
G1, G2, G3 = glow(420, (40, 80, 180), 100), glow(360, KOROSTE, 45), glow(300, (100, 140, 220), 45)
rng = np.random.default_rng(3); grain = [Image.fromarray(rng.integers(0, 22, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)).convert("L") for _ in range(4)]

BRAND = {"korjaus": ("KORJAUSVAHTI", "nytpuhutaan.fi/muutokset"), "huijaus": ("KERÄYSVAHTI", "keraysvahti.fi/huijaukset"), "eduskunta": ("EDUSKUNTASEURANTA", "eduskuntaseuranta.fi"), "uutinen": ("SUOMI TÄNÄÄN", "suomitanaan.fi")}[TYYPPI]
if A.get("osoite"): BRAND = (BRAND[0], A["osoite"])
TAG = pill(BRAND[0], M9(34), NAVY, GOLD + (255,))
LAHDE = pill("Faktapiste · " + BRAND[1], M6(26), (225, 232, 245), (0, 0, 0, 130), 22, 10)

# ---------- tekstitys ----------
SUBF = M9(62)
def tok(w_): return w_.strip(".,:;!?\"”“").upper()
CHUNKS, cur = [], []
for idx, (w_, a_, b_) in enumerate(words):
    tk = tok(w_)
    if tk:
        test = " ".join([tok(words[j][0]) for j in cur] + [tk])
        if cur and (SUBF.getlength(test) > 900 or len(cur) >= 4): CHUNKS.append(cur); cur = []
        cur.append(idx)
    if w_.endswith((".", ":", "?", ",", "!")) and cur: CHUNKS.append(cur); cur = []
if cur: CHUNKS.append(cur)
def subtitle(base, t):
    done = [i for i, w in enumerate(words) if w[1] <= t + 0.04]
    if not done: return
    i = done[-1]
    if t > words[i][2] + 0.5: return
    c = next((c for c in CHUNKS if i in c), None)
    if c is None: return
    toks = [(tok(words[j][0]), j == i) for j in c if tok(words[j][0])]
    line = " ".join(x for x, _ in toks); f = SUBF
    while f.getlength(line) > W - 100: f = M9(f.size - 4)
    x = (W - f.getlength(line)) / 2; d = ImageDraw.Draw(base)
    for s_, on in toks:
        d.text((x, 1560), s_, font=f, fill=YEL if on else WHITE, stroke_width=8, stroke_fill=(0, 0, 0)); x += f.getlength(s_ + " ")

# ---------- valmiit elementit ----------
KOUKKU = iso_teksti(A.get("koukku") or A["lauseet"][0])
if TYYPPI == "korjaus":
    MEDIA = pill(D.get("media", "").upper(), M9(52), NAVY, GOLD + (255,), 36, 20)
    NYTK = kortti("NYT", D["nyt"], GREEN, hl=D.get("lisattiin"))
    POIS = [pill(x[:30], M8(44), WHITE, RED + (255,), 26, 14) for x in D.get("poistettiin", [])[:3] if x]
    LIS = [pill(x[:30], M8(44), NAVY, (120, 225, 160, 255), 26, 14) for x in D.get("lisattiin", [])[:3] if x]
elif TYYPPI == "huijaus":
    # Valinnaiset kentät käsin tehtyihin videoihin (kasivideo.json): merkki, vinkkiotsikko, osoite.
    # Ilman niitä video on tavallinen huijausvaroitus.
    _NEUT = bool(A.get("merkki"))
    VAR = pill(A.get("merkki") or "HUIJAUSVAROITUS", M9(52), WHITE, ((40, 110, 255) if _NEUT else RED) + (255,), 36, 20)
    UUTINEN = kortti(("UUTINEN · " + D.get("media", "")).upper(), D["otsikko"], (40, 110, 255) if _NEUT else RED)
    VINKIT = [v for v in (A.get("vinkit") or []) if v][:2]
elif TYYPPI == "uutinen":
    UOTS = kortti("SUOMI TÄNÄÄN · UUTINEN", D["otsikko"], (180, 35, 44))
    UING = kortti("FAKTAT", D.get("ingressi") or " ".join(D.get("kappaleet", [])[:1]), (40, 110, 255), fs=46)
    NAKO = A.get("nakokulma_naytolle") or D.get("nakokulma", "")[:90]
else:
    OTS = kortti("EDUSKUNTA · " + ".".join(str(int(x)) for x in reversed(D["pv"].split("-"))), D["otsikko"], (40, 110, 255), fs=46)
    TULOS = pill("HYVÄKSYTTIIN" if D["hyvaksyttiin"] else "HYLÄTTIIN", M9(60), WHITE, (GREEN if D["hyvaksyttiin"] else RED) + (255,), 40, 22)
    RYHMAT = sorted(D.get("ryhmat", []), key=lambda g: -(g["jaa"] + g["ei"] + g["tyhja"] + g["poissa"]))[:8]

def palkit(base, t, y0):
    yht = max(1, D["jaa"] + D["ei"]); d = ImageDraw.Draw(base)
    for k, (lab, n, col) in enumerate([("JAA", D["jaa"], GREEN), ("EI", D["ei"], RED)]):
        q = ease(t * 1.5 - k * 0.2); y = y0 + k * 150
        d.text((90, y), lab, font=ANTON(90), fill=WHITE)
        d.rounded_rectangle((300, y + 20, 300 + 600 * n / yht * q, y + 90), radius=18, fill=col)
        d.text((310 + 600 * n / yht * q + 10, y + 8), str(int(n * q)), font=ANTON(80), fill=WHITE)

def ryhmataulu(base, t, y0):
    d = ImageDraw.Draw(base); f = M8(44)
    d.text((90, y0), "PUOLUE", font=M9(30), fill=GREY); d.text((700, y0), "JAA", font=M9(30), fill=GREY); d.text((860, y0), "EI", font=M9(30), fill=GREY)
    for k, g in enumerate(RYHMAT):
        q = ease(t * 3 - k * 0.25)
        if q <= 0: continue
        y = y0 + 56 + k * 74; a = int(255 * q)
        voitto = g["jaa"] > g["ei"]
        d.rounded_rectangle((70, y - 8, 1010, y + 58), radius=14, fill=(255, 255, 255, int(22 * q)))
        d.text((90, y), g["r"][:22], font=f, fill=(255, 255, 255, a))
        d.text((700, y), str(g["jaa"]), font=M9(44), fill=(GREEN if voitto else WHITE) + (a,))
        d.text((860, y), str(g["ei"]), font=M9(44), fill=(RED if not voitto and g["ei"] else WHITE) + (a,))

def kohtaus(base, si, lt, gt):
    t = SC[si] + lt
    if si == 0:
        paste_c(base, KOUKKU, W / 2, 640, back(lt * 3) * (1 + 0.02 * math.sin(gt * 6)))
        mer = MEDIA if TYYPPI == "korjaus" else VAR if TYYPPI == "huijaus" else pill("UUTINEN", M9(52), WHITE, (180, 35, 44, 255), 36, 20) if TYYPPI == "uutinen" else pill("ÄÄNESTYS", M9(52), WHITE, (40, 110, 255, 255), 36, 20)
        paste_c(base, mer, W / 2, min(380, 640 - KOUKKU.height / 2 - 60), back(lt * 3 - 0.4))
        return
    if si == 4:
        paste_c(base, text_img(BRAND[0], ANTON(130), GOLD), W / 2, 600, back(lt * 3))
        paste_c(base, pill(BRAND[1], M9(56), NAVY, GOLD + (255,), 40, 24), W / 2, 800, back(lt * 3 - 0.3) * (1 + 0.03 * math.sin(gt * 5)))
        paste_c(base, text_img("Osa Faktapistettä", M8(48), GREY), W / 2, 960, back(lt * 3 - 0.6))
        return
    if TYYPPI == "korjaus":
        if si == 1:
            paste_c(base, kortti("ENNEN · " + D.get("media", "").upper(), D["ennen"], RED, yliviivaus=ease(lt * 0.8 - 0.6), hl=D.get("poistettiin")), W / 2, 760, back(lt * 3))
        elif si == 2:
            paste_c(base, kortti("ENNEN", D["ennen"], RED, yliviivaus=1, fs=40), W / 2, 470, 0.9, 0.55)
            paste_c(base, NYTK, W / 2, 1050, back(lt * 3))
        else:
            paste_c(base, text_img("POISTETTIIN", ANTON(90), RED), W / 2, 330, back(lt * 3))
            for k, p_ in enumerate(POIS): paste_c(base, p_, W / 2, 470 + k * 110, back(lt * 3 - 0.2 - k * 0.15))
            if LIS:
                y = 470 + len(POIS) * 110 + 60
                paste_c(base, text_img("TILALLE", ANTON(90), (120, 225, 160)), W / 2, y, back(lt * 3 - 0.6))
                for k, p_ in enumerate(LIS): paste_c(base, p_, W / 2, y + 140 + k * 110, back(lt * 3 - 0.8 - k * 0.15))
    elif TYYPPI == "huijaus":
        if si == 1:
            paste_c(base, VAR, W / 2, 380, 1)
            paste_c(base, UUTINEN, W / 2, 780, back(lt * 3))
        else:
            paste_c(base, text_img(A.get("vinkkiotsikko") or "NÄIN SUOJAUDUT", ANTON(110 if len(A.get("vinkkiotsikko") or "") < 16 else 86), GOLD), W / 2, 380, back((t - SC[2]) * 3))
            for k, v in enumerate(VINKIT):
                if t >= SC[2 + k] - 0.1:
                    q = t - SC[2 + k]
                    paste_c(base, pill(("✓ " if False else "") + v, M9(56), NAVY, (255, 255, 255, 255), 40, 26), W / 2, 620 + k * 190, back(q * 3))
    elif TYYPPI == "uutinen":
        if si == 1:
            paste_c(base, UOTS, W / 2, 760, back(lt * 3))
        elif si == 2:
            paste_c(base, UOTS, W / 2, 470, 0.85, 0.5)
            paste_c(base, UING, W / 2, 1000, back(lt * 3))
        else:
            paste_c(base, pill("SUOMI TÄNÄÄN -NÄKÖKULMA", M9(48), NAVY, GOLD + (255,), 34, 20), W / 2, 380, back(lt * 3))
            paste_c(base, iso_teksti("”" + NAKO + "”", koko=96, vari=WHITE, vari2=WHITE), W / 2, 760, back(lt * 3 - 0.3))
            paste_c(base, text_img("Mielipide", M8(40), GREY), W / 2, 1100, back(lt * 3 - 0.6))
    else:
        if si == 1:
            paste_c(base, OTS, W / 2, 760, back(lt * 3))
        elif si == 2:
            paste_c(base, TULOS, W / 2, 420, back(lt * 3))
            palkit(base, lt, 620)
        else:
            paste_c(base, text_img("NÄIN RYHMÄT ÄÄNESTIVÄT", ANTON(80), GOLD), W / 2, 300, back(lt * 3))
            ryhmataulu(base, lt, 420)

# ---------- renderöinti ----------
PV = os.environ.get("PV")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", "aani.mp3", "-filter_complex", f"[1:a]atempo={TEMPO},loudnorm=I=-14:TP=-1.5:LRA=11,apad=pad_dur=3[a]", "-map", "0:v", "-map", "[a]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
if not PV: p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for f in ([int(float(x) * FPS) for x in PV.split(",")] if PV else range(N)):
    t = f / FPS
    fr = BG.copy()
    fr.alpha_composite(G1, (int(-200 + 160 * math.sin(t * 0.4)), int(200 + 120 * math.cos(t * 0.3))))
    fr.alpha_composite(G2, (int(W - 500 + 120 * math.cos(t * 0.5)), int(1100 + 160 * math.sin(t * 0.35))))
    fr.alpha_composite(G3, (int(300 + 200 * math.sin(t * 0.25)), int(1500 + 80 * math.cos(t * 0.6))))
    si = max(i for i in range(5) if SC[i] <= t) if t < SC[-1] else 4
    lt = t - SC[si]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kohtaus(layer, si, lt, t)
    out = min(1, max(0, (SC[si + 1] - t) / 0.18)) if si < 4 else 1
    if out < 1:
        a = layer.getchannel("A").point(lambda v: int(v * out)); layer.putalpha(a)
    fr.alpha_composite(layer)
    fr.alpha_composite(TAG, (60, 110)); fr.alpha_composite(LAHDE, (60, 1790))
    subtitle(fr, t)
    g = grain[f % 4]; fr = Image.composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), fr, g.point(lambda v: v // 3))
    if PV: fr.convert("RGB").resize((540, 960)).save(f"pv_{t:.1f}.jpg"); continue
    p.stdin.write(fr.convert("RGB").tobytes())
if not PV: p.stdin.close(); p.wait(); print("valmis", OUT, N, "kuvaa")
