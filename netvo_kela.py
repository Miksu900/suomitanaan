# -*- coding: utf-8 -*-
"""Tekee Netvo-kelan (9:16, ~21 s, ilman ääntä) brändätyistä tekstislaideista."""
import pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
F = "/home/claude/suomitanaan/videokone/fontit/"
OUT = pathlib.Path("/home/claude/suomitanaan/netvo-video")
TMP = OUT / "slaidit"
TMP.mkdir(parents=True, exist_ok=True)

SIN = (21, 87, 192)
SIN2 = (14, 58, 133)
VIHR = (31, 122, 77)
VALK = (255, 255, 255)
PEHMEA = (226, 235, 250)

def font(n, k):
    return ImageFont.truetype(F + n, k)

def tausta():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(SIN[i] + (SIN2[i] - SIN[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse([W - 420, -200, W + 240, 460], fill=(31, 122, 77, 60))
    od.ellipse([-260, H - 520, 360, H + 100], fill=(255, 255, 255, 14))
    return Image.alpha_composite(img.convert("RGBA"), ov)

def rivita(d, teksti, fnt, maxw):
    rivit, nyt = [], ""
    for s in teksti.split():
        koe = (nyt + " " + s).strip()
        if d.textbbox((0, 0), koe, font=fnt)[2] <= maxw:
            nyt = koe
        else:
            if nyt:
                rivit.append(nyt)
            nyt = s
    if nyt:
        rivit.append(nyt)
    return rivit

def slaidi(nimi, otsikko, ala, numero):
    img = tausta()
    d = ImageDraw.Draw(img)
    marg = 96
    maxw = W - 2 * marg

    # brändi ylhäällä
    fl = font("Mont900.ttf", 84)
    d.text((marg, 170), "Net", font=fl, fill=VALK)
    bw = d.textbbox((0, 0), "Net", font=fl)[2]
    d.text((marg + bw, 170), "vo", font=fl, fill=(170, 235, 200))

    # pääotsikko keskelle
    fh = font("Mont900.ttf", 150)
    rivit = rivita(d, otsikko, fh, maxw)
    while len(rivit) > 3 and fh.size > 90:
        fh = font("Mont900.ttf", fh.size - 10)
        rivit = rivita(d, otsikko, fh, maxw)
    lh = int(fh.size * 1.08)
    y = (H - lh * len(rivit)) // 2 - 120
    for rv in rivit:
        d.text((marg, y), rv, font=fh, fill=VALK)
        y += lh

    # alateksti
    fa = font("Mont600.ttf", 70)
    y += 30
    for rv in rivita(d, ala, fa, maxw):
        d.text((marg, y), rv, font=fa, fill=PEHMEA)
        y += int(fa.size * 1.25)

    # vihreä piste + slaidin numero
    d.ellipse([marg, H - 470, marg + 26, H - 444], fill=VIHR)
    fs = font("Mont800.ttf", 40)
    d.text((marg + 46, H - 478), f"{numero}/6", font=fs, fill=PEHMEA)

    # pilleri netvo.fi alhaalla
    pill = "netvo.fi"
    fp = font("Mont800.ttf", 60)
    pw = d.textbbox((0, 0), pill, font=fp)[2]
    py = H - 300
    d.rounded_rectangle([marg, py, marg + pw + 90, py + 110], radius=55, fill=VIHR)
    d.text((marg + 45, py + 22), pill, font=fp, fill=VALK)

    polku = TMP / f"{nimi}.png"
    img.convert("RGB").save(polku)
    return polku

SLAIDIT = [
    ("s1", "Tarvitsetko nettisivut?", "Netvo tekee ne yrityksellesi"),
    ("s2", "Pystytys 0 €", "Ei pystytysmaksua"),
    ("s3", "Oma verkkotunnus", "Domain on sinun nimissäsi"),
    ("s4", "19 € / kk", "Selkeä hinta"),
    ("s5", "Katso mallisivut", "Näet ne ennen päätöstä"),
    ("s6", "Nettisivut yrityksellesi", "Katso lisää netvo.fi"),
]

kuvat = [slaidi(n, o, a, i + 1) for i, (n, o, a) in enumerate(SLAIDIT)]

KESTO = 4.0
SIIRTYMA = 0.5
ajat = [KESTO * (i + 1) - SIIRTYMA * i for i in range(len(kuvat) - 1)]
# xfade-offsetit: kumulatiiviset
off = []
t = 0.0
for i in range(len(kuvat) - 1):
    t = KESTO * (i + 1) - SIIRTYMA * (i + 1)
    off.append(t)

cmd = ["ffmpeg", "-y"]
for k in kuvat:
    cmd += ["-loop", "1", "-t", str(KESTO), "-r", "30", "-i", str(k)]

fc = []
prev = "0:v"
for i in range(1, len(kuvat)):
    nxt = f"v{i}"
    fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={SIIRTYMA}:offset={off[i-1]:.2f}[{nxt}]")
    prev = nxt
fc.append(f"[{prev}]format=yuv420p[out]")

ulos = OUT / "netvo-kela-01.mp4"
cmd += ["-filter_complex", ";".join(fc), "-map", "[out]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart", str(ulos)]
subprocess.run(cmd, check=True)
print("Valmis:", ulos)
