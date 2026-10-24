"""Faktapisteen mainosvideo (TikTok, 1080x1920): kutsuu liittymään keskusteluun.

Syötteet: promo.json (lauseet), aani.mp3 ja ajoitus.json (ElevenLabs with-timestamps).
Aja: python3 videokone/promo.py   (PV=1,5,9 tekee esikatselukuvat videon sijaan)
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
WHITE = (255, 255, 255); YEL = (255, 210, 70); GOLD = (245, 197, 66); NAVY = (11, 31, 69); NAVY2 = (22, 42, 92); GREY = (170, 182, 205)
RED = (225, 60, 75); GREEN = (40, 185, 110); INK = (20, 22, 28); MUTE = (110, 118, 135); PAPER = (250, 250, 252)

A = json.load(open("promo.json"))
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
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((20 - b[0] + 4, 20 - b[1] + 6), s, font=font, fill=(0, 0, 0, 170))
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
def iso_teksti(s, maxw=960, koko=150, vari=WHITE, vari2=GOLD):
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
def silma(d, x, y, s, col):
    d.ellipse((x, y + s * 0.2, x + s * 1.5, y + s * 0.95), outline=col, width=max(3, s // 9))
    d.ellipse((x + s * 0.5, y + s * 0.33, x + s, y + s * 0.83), fill=col)

def sydanpiirto(d, x, y, s, col, tayte):
    r = s * 0.28
    pts = [(x + s * 0.5, y + s * 0.95), (x + s * 0.04, y + s * 0.42), (x + s * 0.96, y + s * 0.42)]
    if tayte:
        d.ellipse((x, y + s * 0.08, x + 2 * r, y + s * 0.08 + 2 * r), fill=col); d.ellipse((x + s - 2 * r, y + s * 0.08, x + s, y + s * 0.08 + 2 * r), fill=col)
        d.polygon(pts, fill=col)
    else:
        d.arc((x, y + s * 0.08, x + 2 * r, y + s * 0.08 + 2 * r), 140, 360, fill=col, width=4); d.arc((x + s - 2 * r, y + s * 0.08, x + s, y + s * 0.08 + 2 * r), 180, 40, fill=col, width=4)
        d.line([pts[1], pts[0], pts[2]], fill=col, width=4)

# ---------- postauskortti (näyttää Faktapisteen syötteeltä) ----------
def postaus(nimi, teksti, nakymat, w=940, taattu=None, sydan=0):
    fs = 46; f = M8(fs); rivit = wrap(teksti, f, w - 190)
    lh = int(fs * 1.32); h = 150 + len(rivit) * lh + (90 if taattu is not None else 0) + 70
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=30, fill=PAPER + (255,))
    d.ellipse((34, 34, 124, 124), fill=NAVY2); paste_c(c, text_img(nimi[0], M9(44), WHITE, False), 79, 79)
    d.text((150, 44), nimi, font=M9(42), fill=INK); d.text((w - 120, 50), "nyt", font=M6(34), fill=MUTE)
    y = 112
    for r in rivit: d.text((150, y), r, font=f, fill=INK); y += lh
    if taattu is not None:
        y += 20; d.rounded_rectangle((150, y, w - 40, y + 22), radius=11, fill=(230, 232, 238))
        d.rounded_rectangle((150, y, 150 + (w - 190) * min(1, taattu / 30), y + 22), radius=11, fill=GOLD)
        d.text((150, y + 34), f"Nähty {min(30, int(taattu))}/30", font=M8(30), fill=MUTE); y += 70
    y += 20
    d.text((150, y), "Vastaa", font=M8(34), fill=MUTE); sydanpiirto(d, 330, y + 2, 34, RED if sydan else MUTE, bool(sydan))
    if sydan: d.text((376, y), str(sydan), font=M8(34), fill=RED)
    silma(d, w - 230, y - 4, 40, MUTE); d.text((w - 160, y), str(int(nakymat)), font=M9(36), fill=INK)
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
G1, G2, G3 = glow(420, (40, 80, 180), 100), glow(360, GOLD, 40), glow(300, (100, 140, 220), 45)
rng = np.random.default_rng(3); grain = [Image.fromarray(rng.integers(0, 22, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)).convert("L") for _ in range(4)]

def logo(koko):
    a, b = text_img("FAKTA", ANTON(koko), WHITE), text_img("PISTE.", ANTON(koko), GOLD)
    c = Image.new("RGBA", (a.width + b.width - 30, max(a.height, b.height)), (0, 0, 0, 0))
    c.alpha_composite(a, (0, 0)); c.alpha_composite(b, (a.width - 30 + int(koko * 0.12), 0)); return c
TAG = logo(64)
LAHDE = pill("faktapiste.fi", M8(30), (225, 232, 245), (0, 0, 0, 130), 24, 12)

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

# ---------- kohtaukset ----------
KOUKKU = iso_teksti(A.get("koukku") or LAUSEET[0], koko=140)
TYHJA = postaus("Sinä", "Tämä on minusta tärkeä asia, ja haluaisin kuulla muidenkin mielipiteen.", 0)
LUOKAT = ["Keskustelut", "Uutiset", "Otsikkomuutokset", "Huijausvaroitukset", "Päätökset"]
TASOT = [2, 1, 2, 0, 1]

def saato(base, lt):
    d = ImageDraw.Draw(base); x0, w = 70, 940
    for k, l in enumerate(LUOKAT):
        q = ease(lt * 3 - k * 0.2)
        if q <= 0: continue
        y = 520 + k * 130; a = int(255 * q)
        d.rounded_rectangle((x0, y, x0 + w, y + 104), radius=22, fill=(255, 255, 255, int(28 * q)))
        d.text((x0 + 30, y + 30), l, font=M8(40), fill=(255, 255, 255, a))
        # kolmiportainen valitsin: Pois / Normaali / Enemmän
        sx = x0 + 560
        for t_ in range(3):
            on = TASOT[k] == t_ if lt > 0.6 + k * 0.15 else t_ == 1
            d.rounded_rectangle((sx + t_ * 118, y + 26, sx + t_ * 118 + 108, y + 78), radius=26, fill=(GOLD if on else (60, 74, 110)) + (a,))
            d.text((sx + t_ * 118 + 54 - M8(26).getlength(["Pois", "Norm.", "Lisää"][t_]) / 2, y + 38), ["Pois", "Norm.", "Lisää"][t_], font=M8(26), fill=(NAVY if on else WHITE) + (a,))

def kohtaus(base, si, lt, gt):
    if si == 0:
        paste_c(base, KOUKKU, W / 2, 470, back(lt * 3) * (1 + 0.02 * math.sin(gt * 6)))
        paste_c(base, TYHJA, W / 2, 1050, back(lt * 3 - 0.5))
        if lt > 1.0: paste_c(base, pill("0 NÄKYMÄÄ", M9(48), WHITE, RED + (255,), 34, 18), W / 2 + 230, 860, back((lt - 1.0) * 4))
        return
    if si == 1:
        n = 30 * ease((lt - 0.4) / 3.2) + max(0, lt - 3.6) * 4
        paste_c(base, pill("0 SEURAAJAA", M9(46), NAVY, (255, 255, 255, 255), 34, 18), W / 2, 330, back(lt * 3))
        paste_c(base, postaus("Sinä", "Tämä on minusta tärkeä asia, ja haluaisin kuulla muidenkin mielipiteen.", n, taattu=n, sydan=int(n // 9)), W / 2, 780, back(lt * 3 - 0.2))
        paste_c(base, iso_teksti("VÄHINTÄÄN 30 LUKIJAA", koko=110, vari=GOLD, vari2=GOLD), W / 2, 1230, back(lt * 3 - 1.2))
        return
    if si == 2:
        paste_c(base, text_img("SINÄ PÄÄTÄT", ANTON(120), GOLD), W / 2, 360, back(lt * 3))
        dur = SC[3] - SC[2]
        if lt < dur * 0.62: saato(base, lt)
        else:
            q = lt - dur * 0.62
            ok = Image.new("RGBA", (180, 180), (0, 0, 0, 0)); ImageDraw.Draw(ok).ellipse((0, 0, 179, 179), fill=GOLD)
            paste_c(ok, text_img("✓", M9(110), NAVY, False), 90, 92)
            paste_c(base, ok, W / 2, 720, back(q * 3))
            paste_c(base, iso_teksti("SYÖTE LOPPUU", koko=120, vari=WHITE, vari2=WHITE), W / 2, 960, back(q * 3 - 0.2))
            paste_c(base, text_img("Ei loputonta selaamista", M8(50), GREY), W / 2, 1110, back(q * 3 - 0.4))
        return
    if si == 3:
        paste_c(base, pill("KYSY FAKTA", M9(56), NAVY, GOLD + (255,), 44, 24), W / 2, 380, back(lt * 3) * (1 - 0.06 * max(0, math.sin(min(lt, 0.9) * 7)) * (lt < 0.9)))
        c = Image.new("RGBA", (940, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
        d.rounded_rectangle((0, 0, 939, 559), radius=30, fill=PAPER + (255,)); d.rounded_rectangle((0, 0, 18, 559), radius=9, fill=(40, 110, 255))
        d.text((50, 34), "EDUSKUNNAN ÄÄNESTYS", font=M9(34), fill=(40, 110, 255))
        d.text((50, 90), "Miten edustajat äänestivät?", font=M8(46), fill=INK)
        q = ease(lt * 1.4 - 0.7)
        for k, (lab, v, col) in enumerate([("JAA", 0.58, GREEN), ("EI", 0.42, RED)]):
            y = 200 + k * 150
            d.text((50, y), lab, font=ANTON(80), fill=INK)
            d.rounded_rectangle((220, y + 18, 220 + 560 * v * q, y + 86), radius=18, fill=col)
            d.text((240 + 560 * v * q, y + 14), f"{int(v * 100 * q)} %", font=ANTON(64), fill=INK)
        d.text((50, 490), "Lähde: eduskunnan avoin data", font=M6(30), fill=MUTE)
        paste_c(base, c, W / 2, 860, back(lt * 3 - 0.3))
        return
    # loppu: kehotus liittyä
    paste_c(base, logo(170), W / 2, 560, back(lt * 3))
    paste_c(base, pill("faktapiste.fi", M9(78), NAVY, GOLD + (255,), 54, 30), W / 2, 820, back(lt * 3 - 0.3) * (1 + 0.035 * math.sin(gt * 5)))
    paste_c(base, text_img("Liity ilmaiseksi", M8(60), WHITE), W / 2, 1010, back(lt * 3 - 0.6))
    paste_c(base, text_img("Ei salasanaa. Kirjaudut sähköpostilinkillä.", M6(40), GREY), W / 2, 1110, back(lt * 3 - 0.9))

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
    if si < NS - 1: fr.alpha_composite(TAG, (50, 90))
    fr.alpha_composite(LAHDE, (60, 1790))
    subtitle(fr, t)
    g = grain[f % 4]; fr = Image.composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), fr, g.point(lambda v: v // 3))
    if PV: fr.convert("RGB").resize((540, 960)).save(f"pv_{t:.1f}.jpg"); continue
    p.stdin.write(fr.convert("RGB").tobytes())
if not PV: p.stdin.close(); p.wait(); print("valmis", OUT, N, "kuvaa")
