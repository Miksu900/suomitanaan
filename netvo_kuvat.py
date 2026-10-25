# -*- coding: utf-8 -*-
"""Luo 28 brändättyä julkaisukuvaa (1080x1080) Netvon postauksille."""
from PIL import Image, ImageDraw, ImageFont
import pathlib, zipfile
from netvo_sisalto import kalenteri

OUT = pathlib.Path("/home/claude/suomitanaan/netvo-kuvat")
OUT.mkdir(exist_ok=True)
F = "/home/claude/suomitanaan/videokone/fontit/"
VALK = (255, 255, 255)

TEEMAT = {
 "sininen": ((21, 87, 192), (14, 58, 133)),
 "vihrea": ((31, 122, 77), (20, 85, 53)),
 "oranssi": ((217, 99, 26), (168, 74, 17)),
 "musta": ((51, 51, 51), (0, 0, 0)),
 "viininpunainen": ((156, 39, 66), (111, 26, 47)),
 "petroli": ((17, 107, 116), (11, 74, 80)),
 "ruskea": ((122, 82, 48), (85, 56, 32)),
 "purppura": ((91, 58, 156), (63, 40, 110)),
}

def font(nimi, koko):
    return ImageFont.truetype(F + nimi, koko)

def grad(koko, yl, al):
    w, h = koko
    base = Image.new("RGB", koko)
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(yl[i] + (al[i] - yl[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return base

def rivita(d, teksti, fnt, maxw):
    sanat = teksti.split()
    rivit, nyt = [], ""
    for s in sanat:
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

def kuva(r):
    S = 1080
    yl, al = TEEMAT[r["vari"]]
    img = grad((S, S), yl, al).convert("RGBA")
    # koristepallot
    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse([S-360, -160, S+160, 340], fill=(255, 255, 255, 16))
    od.ellipse([-180, S-320, 260, S+220], fill=(255, 255, 255, 12))
    img = Image.alpha_composite(img, ov)
    d = ImageDraw.Draw(img)

    marg = 96
    maxw = S - 2 * marg

    # ylälogo "netvo"
    fl1 = font("Mont900.ttf", 64)
    d.text((marg, 86), "Net", font=fl1, fill=VALK)
    bw = d.textbbox((0, 0), "Net", font=fl1)[2]
    d.text((marg + bw, 86), "vo", font=fl1, fill=(170, 235, 200))

    # pääotsikko (keskelle, rivitettynä)
    fh = font("Mont900.ttf", 112)
    rivit = rivita(d, r["otsikko"], fh, maxw)
    # jos liian monta riviä, pienennä
    while len(rivit) > 3 and fh.size > 70:
        fh = font("Mont900.ttf", fh.size - 8)
        rivit = rivita(d, r["otsikko"], fh, maxw)
    lh = int(fh.size * 1.08)
    block_h = lh * len(rivit)
    y = (S - block_h) // 2 - 40
    for rv in rivit:
        d.text((marg, y), rv, font=fh, fill=VALK)
        y += lh

    # alaote
    fa = font("Mont600.ttf", 52)
    arivit = rivita(d, r["ala"], fa, maxw)
    y += 18
    for rv in arivit:
        d.text((marg, y), rv, font=fa, fill=(226, 235, 250))
        y += int(fa.size * 1.2)

    # alapilleri netvo.fi
    fs = font("Mont800.ttf", 46)
    pill = "netvo.fi"
    pw = d.textbbox((0, 0), pill, font=fs)[2]
    py = S - 150
    d.rounded_rectangle([marg, py, marg + pw + 72, py + 86], radius=43,
                        fill=(255, 255, 255, 235))
    d.text((marg + 36, py + 18), pill, font=fs, fill=al)

    img.convert("RGB").save(OUT / r["kuva"], quality=92)

rivit = kalenteri()
for r in rivit:
    kuva(r)

# zippaa kaikki
zp = pathlib.Path("/home/claude/suomitanaan/netvo-julkaisukuvat.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for r in rivit:
        z.write(OUT / r["kuva"], r["kuva"])
print("Kuvia:", len(rivit), "| zip:", zp)
