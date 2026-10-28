"""Netvon TikTok-video "Maksoitko nettisivuista 3000 €?" (1080x1920).

Syötteet työhakemistossa: promo.json (lauseet), aani.mp3 ja ajoitus.json (ElevenLabs with-timestamps).
Aja: python3 videokone/netvo_promo.py   (PV=1,5,9 tekee esikatselukuvat videon sijaan)
Kohtaukset: 0 koukku 3000 € -lasku, 1 hidas sivu puhelimessa, 2 muutoslaskut, 3 vertailu Netvo, 4 loppu.
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
WHITE = (255, 255, 255); SIN = (21, 87, 192); SIN2 = (14, 58, 133); VIHR = (31, 122, 77); LIME = (80, 220, 140)
YEL = (255, 214, 80); RED = (225, 60, 75); INK = (20, 24, 34); MUTE = (110, 118, 135); PAPER = (250, 251, 253); PALE = (200, 215, 240)

A = json.load(open(os.environ.get("JSON", "promo.json")))
LAUSEET = A["lauseet"]
al = json.load(open("ajoitus.json"))
ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
txt = "".join(ch)
words = [(m.group(), st[m.start()] / TEMPO, en[m.end() - 1] / TEMPO) for m in re.finditer(r"\S+", txt)]
sent_starts, pos = [], 0
for s in LAUSEET:
    i = txt.find(s[:12], pos)
    if i < 0: break
    sent_starts.append(st[i] / TEMPO); pos = i + len(s) - 2
if len(sent_starts) != len(LAUSEET):
    sent_starts = [0.0] + [st[m.end()] / TEMPO for m in re.finditer(r"[.?!]\s", txt)][:len(LAUSEET) - 1]
    while len(sent_starts) < len(LAUSEET): sent_starts.append(sent_starts[-1] + 2)
sent_starts[0] = 0.0
DUR = en[-1] / TEMPO + 2.2
N = int(DUR * FPS)
NS = len(LAUSEET)
SC = sent_starts + [DUR]
print("lauseet", [round(x, 1) for x in sent_starts], "kesto", round(DUR, 1))

# ---------- apurit ----------
def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def back(t): t = max(0, min(1, t)); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def text_img(s, font, color=WHITE, shadow=True):
    b = font.getbbox(s); w, h = b[2] - b[0] + 40, b[3] - b[1] + 40
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((20 - b[0] + 4, 20 - b[1] + 6), s, font=font, fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((20 - b[0], 20 - b[1]), s, font=font, fill=color)
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
def iso_teksti(s, maxw=960, koko=150, vari=WHITE, vari2=YEL):
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
def logo(koko):
    a, b = text_img("Net", M9(koko), WHITE), text_img("vo", M9(koko), LIME)
    c = Image.new("RGBA", (a.width + b.width - 40, max(a.height, b.height)), (0, 0, 0, 0))
    c.alpha_composite(a, (0, 0)); c.alpha_composite(b, (a.width - 40, 0)); return c
def ruksi(d, x, y, s, col):  # vihreä pallo + väkänen
    d.ellipse((x, y, x + s, y + s), fill=col)
    d.line([(x + s * 0.26, y + s * 0.52), (x + s * 0.43, y + s * 0.69), (x + s * 0.75, y + s * 0.33)], fill=WHITE, width=max(4, s // 8), joint="curve")

# ---------- tausta ----------
yy = np.linspace(0, 1, H)[:, None]
bg = np.zeros((H, W, 3), np.float32)
bg[..., 0] = 8 + 6 * (1 - yy); bg[..., 1] = 22 + 30 * (1 - yy); bg[..., 2] = 52 + 70 * (1 - yy)  # tumma Netvo-sininen
BG = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
def glow(r, col, a):
    g = Image.new("RGBA", (r * 2, r * 2), col + (0,)); q = int(r * 0.45)
    ImageDraw.Draw(g).ellipse((q, q, r * 2 - q, r * 2 - q), fill=col + (a,))
    return g.filter(ImageFilter.GaussianBlur(r // 4))
G1, G2, G3 = glow(420, SIN, 90), glow(360, VIHR, 60), glow(300, (60, 110, 220), 40)
rng = np.random.default_rng(3); grain = [Image.fromarray(rng.integers(0, 16, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)).convert("L") for _ in range(4)]
TAG = logo(70)
LAHDE = pill("netvo.fi", M8(30), (225, 232, 245), (0, 0, 0, 120), 24, 12)

# ---------- tekstitys ----------
SUBF = M9(62)
NAYTA = {"KOLMETUHATTA": "3000", "NOLLA": "0", "KAKSIKYMMENTÄVIISI": "25", "EUROA": "€"}
def tok(w_): t = w_.strip(".,:;!?\"”“").upper(); return NAYTA.get(t, t)
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
    for k in range(len(toks) - 2, 0, -1):  # "NETVO PISTE FI" -> "NETVO.FI"
        if toks[k][0] == "PISTE" and toks[k + 1][0] == "FI" and toks[k - 1][0] == "NETVO":
            toks[k - 1:k + 2] = [("NETVO.FI", toks[k - 1][1] or toks[k][1] or toks[k + 1][1])]
    line = " ".join(x for x, _ in toks); f = SUBF
    while f.getlength(line) > W - 100: f = M9(f.size - 4)
    x = (W - f.getlength(line)) / 2; d = ImageDraw.Draw(base)
    for s_, on in toks:
        d.text((x, 1600), s_, font=f, fill=YEL if on else WHITE, stroke_width=8, stroke_fill=(0, 0, 0)); x += f.getlength(s_ + " ")


# ---------- kortit ----------
def lasku(lt, rivi="Nettisivuprojekti", summa="3 000 €", leveys=860):
    c = Image.new("RGBA", (leveys, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, leveys - 1, 399), radius=30, fill=PAPER + (255,))
    d.text((50, 40), "LASKU", font=M9(44), fill=MUTE); d.text((leveys - 50, 46), "Eräpäivä 14 pv", font=M6(32), fill=MUTE, anchor="ra")
    d.line([(50, 110), (leveys - 50, 110)], fill=(225, 228, 235), width=3)
    d.text((50, 150), rivi, font=M8(46), fill=INK)
    d.text((50, 260), "Yhteensä", font=M6(40), fill=MUTE)
    n = int(3000 * ease(lt * 1.5)) if summa == "3 000 €" else None
    d.text((leveys - 50, 240), (f"{n:,}".replace(",", " ") + " €") if n is not None else summa, font=M9(84), fill=RED, anchor="ra")
    return c
def hidas_sivu(lt):
    PW, PH = 560, 1000
    c = Image.new("RGBA", (PW + 44, PH + 44), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, PW + 43, PH + 43), radius=70, fill=(12, 14, 20, 255))
    r = Image.new("RGBA", (PW, PH), (238, 238, 238, 255)); dr = ImageDraw.Draw(r)
    dr.rectangle((0, 0, PW, 90), fill=(200, 200, 205)); dr.text((24, 30), "www.yritys-sivu.fi", font=M6(28), fill=MUTE)
    # liian leveä vanha sivu: pieni teksti ja kuva yli reunan
    dr.rectangle((20, 120, PW + 200, 380), fill=(205, 210, 220)); dr.text((40, 140), "TERVETULOA KOTISIVUILLEMME", font=M8(40), fill=(150, 150, 160))
    for k in range(10): dr.rectangle((20, 420 + k * 34, PW + 120 - (k % 3) * 90, 434 + k * 34), fill=(205, 205, 212))
    # latausrinkula
    cx, cy = PW // 2, 620; a = gt_global[0] * 360
    dr.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=(255, 255, 255, 230))
    dr.arc((cx - 46, cy - 46, cx + 46, cy + 46), a, a + 270, fill=SIN, width=12)
    sek = min(9.9, 1 + lt * 2.2); dr.text((cx, cy + 120), f"Ladataan... {sek:.1f} s", font=M8(36), fill=INK, anchor="mm")
    m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=50, fill=255)
    c.paste(r, (22, 22), m); return c
gt_global = [0.0]
def risti(s, col=RED):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.ellipse((0, 0, s - 1, s - 1), fill=col)
    q = s * 0.3; d.line([(q, q), (s - q, s - q)], fill=WHITE, width=s // 8); d.line([(s - q, q), (q, s - q)], fill=WHITE, width=s // 8); return im
def merkinta(teksti, col=RED, fg=WHITE):
    p_ = pill(teksti, M9(48), fg, col + (255,), 34, 20); return p_

# ---------- kohtaukset ----------
MUUTOKSET = [("Aukioloajan vaihto", "+ 90 €"), ("Uusi kuva etusivulle", "+ 120 €"), ("Hinnaston päivitys", "+ 150 €")]
def kohtaus(base, si, lt, gt):
    gt_global[0] = gt; dur = SC[si + 1] - SC[si]
    if si == 0:
        paste_c(base, iso_teksti("Maksoitko nettisivuista", koko=130, vari=WHITE, vari2=WHITE), W / 2, 330, back(lt * 3))
        paste_c(base, iso_teksti("3000 €?", koko=280, vari=YEL, vari2=YEL), W / 2, 620, back(lt * 3 - 0.15) * (1 + 0.02 * math.sin(gt * 7)))
        paste_c(base, lasku(lt).rotate(-4, expand=True, resample=Image.BICUBIC), W / 2, 1100, back(lt * 3 - 0.35))
        return
    if si == 1:
        paste_c(base, iso_teksti("Katso mitä sait", koko=120, vari=WHITE, vari2=WHITE), W / 2, 220, back(lt * 3))
        paste_c(base, hidas_sivu(lt), W / 2 - 120, 900, back(lt * 3 - 0.2) * 0.95)
        for k, s_ in enumerate(["HIDAS", "EI TOIMI PUHELIMELLA", "NUMERO HUKASSA"]):
            q = lt - dur * (0.25 + k * 0.2)
            if q > 0: paste_c(base, merkinta(s_), W / 2 + 220 - (60 if k == 1 else 0), 620 + k * 230, back(q * 4))
        return
    if si == 2:
        paste_c(base, iso_teksti("Ja jokaisesta muutoksesta", koko=110, vari=WHITE, vari2=WHITE), W / 2, 300, back(lt * 3))
        paste_c(base, text_img("uusi lasku.", ANTON(140), RED), W / 2, 470, back(lt * 3 - 0.2))
        for k, (r_, e_) in enumerate(MUUTOKSET):
            q = lt - 0.35 - k * dur * 0.18
            if q > 0:
                kortti = lasku(1, r_, e_, 820).rotate((-1) ** k * 3, expand=True, resample=Image.BICUBIC)
                paste_c(base, kortti, W / 2 + (-1) ** k * 30, 800 + k * 290, back(q * 4) * 0.8)
        return
    if si == 3:
        paste_c(base, logo(130), W / 2, 220, back(lt * 3))
        vas = Image.new("RGBA", (460, 640), (0, 0, 0, 0)); dv = ImageDraw.Draw(vas)
        dv.rounded_rectangle((0, 0, 459, 639), radius=34, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=3)
        dv.text((230, 70), "Projekti", font=M8(46), fill=PALE, anchor="mm")
        dv.text((230, 220), "3000 €", font=ANTON(120), fill=(200, 200, 210), anchor="mm")
        if lt > 0.5: dv.line([(50, 230), (410, 210)], fill=RED, width=14)
        dv.text((230, 380), "+ muutokset", font=M8(46), fill=(200, 200, 210), anchor="mm"); dv.text((230, 450), "erikseen", font=M8(46), fill=(200, 200, 210), anchor="mm")
        oik = Image.new("RGBA", (460, 640), (0, 0, 0, 0)); do = ImageDraw.Draw(oik)
        do.rounded_rectangle((0, 0, 459, 639), radius=34, fill=VIHR + (255,))
        do.text((230, 70), "Netvo", font=M9(50), fill=WHITE, anchor="mm")
        do.text((230, 200), "0 €", font=ANTON(130), fill=WHITE, anchor="mm"); do.text((230, 290), "pystytys", font=M8(40), fill=WHITE, anchor="mm")
        do.text((230, 410), "25 €/kk", font=ANTON(100), fill=YEL, anchor="mm"); do.text((230, 500), "sis. alv", font=M8(36), fill=WHITE, anchor="mm")
        do.text((230, 570), "pienet muutokset mukana", font=M8(30), fill=WHITE, anchor="mm")
        paste_c(base, vas, W / 2 - 250, 850, back(lt * 3 - 0.1))
        paste_c(base, oik, W / 2 + 250, 850, back(lt * 3 - 0.4) * (1 + 0.015 * math.sin(gt * 5)))
        if lt > dur * 0.55: paste_c(base, pill("EI LOUKKUA · OMA VERKKOTUNNUS", M9(44), INK, LIME + (255,), 34, 20), W / 2, 1300, back((lt - dur * 0.55) * 4))
        return
    paste_c(base, logo(220), W / 2, 450, back(lt * 3))
    paste_c(base, text_img("NETTISIVUT ILMAN TUHANSIEN LASKUA", M9(46), WHITE), W / 2, 640, back(lt * 3 - 0.25))
    paste_c(base, pill("netvo.fi", M9(96), WHITE, SIN + (255,), 66, 34), W / 2, 860, back(lt * 3 - 0.45) * (1 + 0.035 * math.sin(gt * 5)))
    paste_c(base, text_img("Katso mallisivut", M8(62), WHITE), W / 2, 1060, back(lt * 3 - 0.7))
    paste_c(base, pill("Pystytys 0 € · 25 €/kk · p. 044 777 7149", M9(40), INK, (255, 255, 255, 255), 30, 16), W / 2, 1190, back(lt * 3 - 0.95))

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
    si = max(i for i in range(NS) if SC[i] <= t) if t < SC[-1] else NS - 1
    lt = t - SC[si]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kohtaus(layer, si, lt, t)
    out = min(1, max(0, (SC[si + 1] - t) / 0.18)) if si < NS - 1 else 1
    if out < 1:
        a = layer.getchannel("A").point(lambda v: int(v * out)); layer.putalpha(a)
    fr.alpha_composite(layer)
    if si not in (3, NS - 1): fr.alpha_composite(TAG, (50, 60))
    fr.alpha_composite(LAHDE, (60, 1790))
    subtitle(fr, t)
    g = grain[f % 4]; fr = Image.composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), fr, g.point(lambda v: v // 3))
    if PV: fr.convert("RGB").resize((540, 960)).save(f"pv_{t:.1f}.jpg"); continue
    p.stdin.write(fr.convert("RGB").tobytes())
if not PV: p.stdin.close(); p.wait(); print("valmis", OUT, N, "kuvaa")
