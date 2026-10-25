#!/usr/bin/env python3
"""Netvo-brändikuvat: logo, profiilimerkki, kansikuva."""
from PIL import Image, ImageDraw, ImageFont
import pathlib

OUT = pathlib.Path("/home/claude/suomitanaan/netvo-brandi")
OUT.mkdir(exist_ok=True)
F = "/home/claude/suomitanaan/videokone/fontit/"

SIN = (21, 87, 192)      # #1557c0
SIN2 = (14, 58, 133)     # #0e3a85
VIHR = (31, 122, 77)     # #1f7a4d
VALK = (255, 255, 255)

def font(nimi, koko):
    return ImageFont.truetype(F + nimi, koko)

def keskita(d, teksti, fnt, cx, y, vari):
    b = d.textbbox((0, 0), teksti, font=fnt)
    w = b[2] - b[0]
    d.text((cx - w / 2 - b[0], y), teksti, font=fnt, fill=vari)
    return b[3] - b[1]

def pystygrad(koko, ylavari, alavari):
    w, h = koko
    base = Image.new("RGB", koko)
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px0 = tuple(int(ylavari[i] + (alavari[i] - ylavari[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = px0
    return base

# --- 1. Logo (wordmark, läpinäkyvä tausta) ---
def logo():
    W, H = 1600, 520
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font("Mont900.ttf", 300)
    # "Net" sininen + "vo" vihreä, keskitettynä yhtenä sanana
    s1, s2 = "Net", "vo"
    b1 = d.textbbox((0, 0), s1, font=f)
    b2 = d.textbbox((0, 0), s2, font=f)
    w1, w2 = b1[2] - b1[0], b2[2] - b2[0]
    kok = w1 + w2
    x0 = (W - kok) / 2
    y0 = (H - (b1[3] - b1[1])) / 2 - b1[1]
    d.text((x0 - b1[0], y0), s1, font=f, fill=SIN)
    d.text((x0 + w1 - b2[0], y0), s2, font=f, fill=VIHR)
    img.save(OUT / "netvo-logo.png")

# --- 2. Profiilimerkki (neliö, sininen tausta) ---
def profiili():
    S = 1024
    img = pystygrad((S, S), SIN, SIN2).convert("RGBA")
    d = ImageDraw.Draw(img)
    f = font("Mont900.ttf", 460)
    # iso valkoinen "N" + vihreä piste
    txt = "N"
    b = d.textbbox((0, 0), txt, font=f)
    w = b[2] - b[0]
    h = b[3] - b[1]
    x = (S - w) / 2 - b[0] - 18
    y = (S - h) / 2 - b[1]
    d.text((x, y), txt, font=f, fill=VALK)
    # vihreä piste oikeaan alakulmaan N:n viereen
    r = 58
    cx = x + w + b[0] + 46
    cy = y + h + b[1] - r
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=VIHR)
    img.convert("RGB").save(OUT / "netvo-profiili.png")

# --- 3. Kansikuva (1640x664) ---
def kansi():
    W, H = 1640, 664
    img = Image.new("RGB", (W, H))
    # vino gradientti: päällekkäin pysty + sivusiirto
    base = pystygrad((W, H), SIN, SIN2)
    img.paste(base)
    d = ImageDraw.Draw(img)
    # koristepallo (vihreä, läpikuultava) oikealle
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W - 420, -180, W + 180, 420], fill=(31, 122, 77, 70))
    od.ellipse([W - 260, H - 220, W + 260, H + 260], fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    # Teksti vasemmalle, turvallisella alueella (mobiili rajaa reunoja)
    x = 120
    fL = font("Mont900.ttf", 128)
    fM = font("Mont600.ttf", 44)
    fS = font("Mont800.ttf", 40)
    d.text((x, 150), "Net", font=fL, fill=VALK)
    b1 = d.textbbox((0, 0), "Net", font=fL)
    d.text((x + (b1[2] - b1[0]), 150), "vo", font=fL, fill=(150, 230, 190))
    d.text((x, 310), "Valmiit nettisivut yrityksellesi", font=fM, fill=(230, 238, 252))
    # alapalkki-korostus
    d.text((x, 372), "Pystytys 0 €  ·  Oma verkkotunnus  ·  Reilut ehdot", font=fM, fill=(200, 216, 245))
    # netvo.fi pilleri
    pill = "netvo.fi"
    bp = d.textbbox((0, 0), pill, font=fS)
    pw = bp[2] - bp[0]
    d.rounded_rectangle([x, 470, x + pw + 64, 470 + 78], radius=39, fill=VIHR)
    d.text((x + 32, 470 + 18), pill, font=fS, fill=VALK)
    img.save(OUT / "netvo-kansi.png")

logo()
profiili()
kansi()
print("Valmis:", [p.name for p in sorted(OUT.glob("*.png"))])
for p in sorted(OUT.glob("*.png")):
    im = Image.open(p)
    print(p.name, im.size)
