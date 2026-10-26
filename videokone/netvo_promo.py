"""Netvon mainosvideo (TikTok, 1080x1920): valmiit nettisivut yrityksille.

Syötteet työhakemistossa: promo.json (lauseet), aani.mp3 ja ajoitus.json (ElevenLabs with-timestamps).
Aja: python3 videokone/netvo_promo.py   (PV=1,5,9 tekee esikatselukuvat videon sijaan)
Kohtaukset lauseittain: 0 koukku (haku, kilpailija), 1 mallisivut puhelimessa + pystytys 0 €,
2 hinta 25 €/kk + mitä kuuluu, 3 oma verkkotunnus / reilut ehdot, 4 loppu netvo.fi.
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

# ---------- puhelinkehys mallisivuille ----------
MALLIT = [Image.open(HERE / "netvo-kuvat" / f"{m}.jpg").convert("RGBA") for m in ["parturi", "putki", "ravintola", "siivous", "kauppa-leipomo"]]
PW, PH = 560, 1100
def puhelin(lt, dur):
    c = Image.new("RGBA", (PW + 44, PH + 44), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, PW + 43, PH + 43), radius=70, fill=(12, 14, 20, 255))
    ruutu = Image.new("RGBA", (PW, PH), PAPER + (255,))
    jakso = max(0.9, dur / len(MALLIT)); k = int(lt / jakso) % len(MALLIT); q = (lt % jakso) / jakso
    nyk = MALLIT[k]; ruutu.alpha_composite(nyk.crop((0, 0, PW, min(PH, nyk.height))), (0, 0))
    if q > 0.8 and lt + jakso * 0.2 < dur:  # liuku seuraavaan malliin
        seur = MALLIT[(k + 1) % len(MALLIT)]; x = int(PW * (1 - ease((q - 0.8) / 0.2)))
        ruutu.alpha_composite(seur.crop((0, 0, PW - x, min(PH, seur.height))), (x, 0))
    m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=50, fill=255)
    c.paste(ruutu, (22, 22), m)
    d.rounded_rectangle((PW // 2 - 60 + 22, 34, PW // 2 + 60 + 22, 62), radius=14, fill=(12, 14, 20, 255))
    return c

# ---------- hakutulos-kortti (koukku) ----------
def haku(lt):
    w = 940; c = Image.new("RGBA", (w, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, 899), radius=34, fill=PAPER + (255,))
    d.rounded_rectangle((40, 40, w - 40, 140), radius=50, outline=(210, 214, 222), width=4)
    hakusana = "parturi lähelläni"; n = int(len(hakusana) * ease(lt * 1.4))
    d.ellipse((76, 66, 120, 110), outline=MUTE, width=6); d.line([(114, 104), (132, 122)], fill=MUTE, width=7)
    d.text((160, 64), hakusana[:n] + ("|" if lt < 0.9 and int(lt * 6) % 2 == 0 else ""), font=M8(44), fill=INK)
    rivit = [("Parturi Kilpailija", "kilpailija.fi", "4,8 · Varaa aika verkossa", True),
             ("Hiussalonki Nova", "salonkinova.fi", "4,6 · Avoinna tänään 9–18", True),
             ("Sinun yrityksesi", "ei nettisivuja", "Ei tietoja", False)]
    for k, (nimi, url, info, ok) in enumerate(rivit):
        q = ease((lt - 0.6 - k * 0.25) * 3)
        if q <= 0: continue
        y = 190 + k * 230; a = int(255 * q) if ok else int(150 * q)
        d.text((60, y), url, font=M6(32), fill=(VIHR if ok else MUTE) + (a,))
        d.text((60, y + 46), nimi, font=M9(50), fill=(SIN if ok else MUTE) + (a,))
        tx = 60
        if ok:  # tähti
            cx, cy, r = 78, y + 138, 18
            d.polygon([(cx + (r if j % 2 == 0 else r * 0.45) * math.sin(j * math.pi / 5), cy - (r if j % 2 == 0 else r * 0.45) * math.cos(j * math.pi / 5)) for j in range(10)], fill=(245, 180, 30, a)); tx = 108
        d.text((tx, y + 116), info, font=M6(36), fill=(INK if ok else MUTE) + (a,))
        if k < 2: d.line([(60, y + 190), (w - 60, y + 190)], fill=(230, 232, 238, a), width=3)
    return c

# ---------- verkkotunnuskortti ----------
def tunnus(lt):
    w = 900; c = Image.new("RGBA", (w, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, 419), radius=34, fill=PAPER + (255,))
    d.rounded_rectangle((40, 40, w - 40, 140), radius=24, fill=(236, 240, 248))
    d.text((80, 64), "https://", font=M8(46), fill=MUTE); d.text((80 + M8(46).getlength("https://"), 64), "yrityksesi.fi", font=M9(46), fill=SIN)
    d.text((60, 190), "Verkkotunnuksen omistaja", font=M6(38), fill=MUTE)
    if lt > 0.6:
        d.text((60, 250), "Sinun yrityksesi", font=M9(64), fill=INK)
        ruksi(d, w - 160, 236, 96, VIHR)
    else:
        d.text((60, 250), "...", font=M9(64), fill=MUTE)
    return c

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
NAYTA = {"NOLLA": "0", "KAKSIKYMMENTÄVIISI": "25", "EUROA": "€"}
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

# ---------- kohtaukset ----------
SISALTO = ["Ylläpito ja hosting", "Tuki arkisin 9–21", "Pienet muutokset", "Toimii puhelimella"]
def kohtaus(base, si, lt, gt):
    dur = SC[si + 1] - SC[si]
    if si == 0:
        paste_c(base, iso_teksti("Ei nettisivuja?", koko=150, vari=WHITE, vari2=WHITE), W / 2, 330, back(lt * 3) * (1 + 0.015 * math.sin(gt * 6)))
        paste_c(base, haku(lt), W / 2, 930, back(lt * 3 - 0.2))
        if lt > dur * 0.55: paste_c(base, pill("ASIAKAS MENEE KILPAILIJALLE", M9(46), WHITE, RED + (255,), 34, 20), W / 2, 1450, back((lt - dur * 0.55) * 4))
        return
    if si == 1:
        paste_c(base, logo(120), W / 2, 230, back(lt * 3))
        paste_c(base, puhelin(lt, dur), W / 2, 900, back(lt * 3 - 0.2) * 0.98)
        if lt > dur * 0.5: paste_c(base, pill("PYSTYTYS 0 €", M9(70), WHITE, VIHR + (255,), 46, 26), W / 2 + 200, 1380, back((lt - dur * 0.5) * 4) * (1 + 0.03 * math.sin(gt * 6)))
        return
    if si == 2:
        hehku = Image.new("RGBA", (900, 460), (0, 0, 0, 0)); ImageDraw.Draw(hehku).ellipse((60, 60, 840, 400), fill=LIME + (50,))
        paste_c(base, hehku.filter(ImageFilter.GaussianBlur(70)), W / 2, 430, back(lt * 3))
        paste_c(base, iso_teksti("25 € / kk", koko=230, vari=WHITE, vari2=WHITE), W / 2, 410, back(lt * 4) * (1 + 0.02 * math.sin(gt * 5)))
        paste_c(base, text_img("sis. alv · pystytys 0 €", M8(44), PALE), W / 2, 580, back(lt * 4 - 0.2))
        laatikko = Image.new("RGBA", (860, 560), (0, 0, 0, 0)); dl = ImageDraw.Draw(laatikko)
        dl.rounded_rectangle((0, 0, 859, 559), radius=34, fill=(255, 255, 255, 26), outline=(255, 255, 255, 70), width=3)
        dl.text((430, 60), "Hintaan kuuluu", font=M9(46), fill=LIME, anchor="mm")
        for k, s_ in enumerate(SISALTO):
            if lt < 0.5 + k * 0.35: continue
            y = 130 + k * 102; ruksi(dl, 60, y, 64, VIHR); dl.text((150, y + 32), s_, font=M8(48), fill=WHITE, anchor="lm")
        paste_c(base, laatikko, W / 2, 1000, back(lt * 3 - 0.3))
        return
    if si == 3:
        paste_c(base, iso_teksti("Reilut ehdot", koko=140, vari=WHITE, vari2=WHITE), W / 2, 300, back(lt * 3))
        paste_c(base, tunnus(lt), W / 2, 680, back(lt * 3 - 0.2))
        if lt > dur * 0.45: paste_c(base, pill("EI LOUKKUA", M9(60), INK, LIME + (255,), 40, 22), W / 2, 1000, back((lt - dur * 0.45) * 4))
        if lt > dur * 0.6:
            paste_c(base, text_img("Lopetus kesken sitoutumisen:", M8(44), WHITE), W / 2, 1160, back((lt - dur * 0.6) * 4))
            paste_c(base, text_img("vain 2 kk maksu", M9(56), YEL), W / 2, 1240, back((lt - dur * 0.6) * 4 - 0.15))
        return
    # loppu
    paste_c(base, logo(220), W / 2, 450, back(lt * 3))
    paste_c(base, text_img("VALMIIT NETTISIVUT YRITYKSELLESI", M9(50), WHITE), W / 2, 640, back(lt * 3 - 0.25))
    paste_c(base, pill("netvo.fi", M9(96), WHITE, SIN + (255,), 66, 34), W / 2, 860, back(lt * 3 - 0.45) * (1 + 0.035 * math.sin(gt * 5)))
    paste_c(base, text_img("Katso mallisivut ja tilaa", M8(62), WHITE), W / 2, 1060, back(lt * 3 - 0.7))
    paste_c(base, pill("Pystytys 0 € · 25 €/kk · oma verkkotunnus", M9(40), INK, (255, 255, 255, 255), 30, 16), W / 2, 1190, back(lt * 3 - 0.95))

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
    if si not in (1, NS - 1): fr.alpha_composite(TAG, (50, 80))
    fr.alpha_composite(LAHDE, (60, 1790))
    subtitle(fr, t)
    g = grain[f % 4]; fr = Image.composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), fr, g.point(lambda v: v // 3))
    if PV: fr.convert("RGB").resize((540, 960)).save(f"pv_{t:.1f}.jpg"); continue
    p.stdin.write(fr.convert("RGB").tobytes())
if not PV: p.stdin.close(); p.wait(); print("valmis", OUT, N, "kuvaa")
