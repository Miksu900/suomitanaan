"""Räätälöityjen mallikauppojen kuvitus (SVG). Yhtenäinen, pehmeä kuvitustyyli: värikäs tausta, varjo, kuviot."""


def _wrap(bg1, bg2, body, w=800, h=1000):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient>
<radialGradient id="sh" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".28"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<pattern id="knit" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M0 0l11 11L22 0M0 11l11 11 11-11" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="3"/></pattern>
<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="13" cy="13" r="1.6" fill="#000" fill-opacity=".05"/></pattern>
<linearGradient id="gl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".45" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<rect width="{w}" height="{h}" fill="url(#bg)"/><rect width="{w}" height="{h}" fill="url(#dots)"/>{body}</svg>'''


def _shade(hexc, k):
    h = hexc.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = (lambda c: int(c + (255 - c) * k)) if k > 0 else (lambda c: int(c * (1 + k)))
    return '#%02x%02x%02x' % tuple(max(0, min(255, f(c))) for c in (r, g, b))


# ---------- Villa & Lanka ----------
def sukka(c, kuvio='tunturi', bg=('#f3ece3', '#e6dacb')):
    d, l = _shade(c, -.25), _shade(c, .55)
    leg = 'M300 170 h200 v330 c0 40 10 70 40 100 l90 90 c50 50 40 140-40 160 c-50 12-100-5-140-45 L310 600 c-25-25-10-60-10-100 Z'
    pattern = {
        'tunturi': f'<path d="M300 300 l33 -33 33 33 34 -33 33 33 34 -33 33 33" fill="none" stroke="{l}" stroke-width="16" stroke-linejoin="round"/><path d="M300 360 l33 -33 33 33 34 -33 33 33 34 -33 33 33" fill="none" stroke="{l}" stroke-width="16" stroke-linejoin="round"/>',
        'kuura': ''.join(f'<path d="M{x} {y}l10 -18 10 18 -10 18z" fill="{l}"/>' for x in range(320, 500, 44) for y in (300, 360, 420)),
        'raita': ''.join(f'<rect x="300" y="{y}" width="200" height="22" fill="{l}"/>' for y in (250, 300, 350, 400)),
    }[kuvio]
    body = f'''<ellipse cx="420" cy="880" rx="250" ry="34" fill="url(#sh)"/>
<g transform="rotate(-8 420 520)"><path d="{leg}" fill="{c}"/><path d="{leg}" fill="url(#knit)"/>
<rect x="296" y="150" width="208" height="70" rx="14" fill="{d}"/>{''.join(f'<rect x="{x}" y="156" width="10" height="58" rx="5" fill="#000" fill-opacity=".1"/>' for x in range(312, 500, 22))}
{pattern}<path d="M560 680 c50 50 40 140-40 160 c-30 7-60 3-88-10 c40-20 70-70 128-150Z" fill="{d}"/><path d="M320 520 c0 40 10 70 40 100" fill="none" stroke="{d}" stroke-width="10" opacity=".5"/>
<rect x="290" y="150" width="60" height="700" fill="url(#gl)" opacity=".7"/></g>'''
    return _wrap(*bg, body)


def lapaset(c, bg=('#ece7f1', '#ddd3e6')):
    d, l = _shade(c, -.25), _shade(c, .6)
    def one(x, rot):
        return f'''<g transform="translate({x} 0) rotate({rot} 0 520)"><path d="M-110 380 c0-120 40-190 110-190 s110 70 110 190 v170 h-220Z" fill="{c}"/><path d="M-110 380 c0-120 40-190 110-190 s110 70 110 190 v170 h-220Z" fill="url(#knit)"/>
<path d="M-110 420 c-60 -10 -90 -70 -60 -120 c20-30 60-20 60 20Z" fill="{c}"/><rect x="-118" y="540" width="236" height="110" rx="16" fill="{d}"/>
{''.join(f'<rect x="{xx}" y="548" width="10" height="94" rx="5" fill="#000" fill-opacity=".1"/>' for xx in range(-104, 110, 22))}
<path d="M-70 330 l35-35 35 35 35-35 35 35" fill="none" stroke="{l}" stroke-width="14"/><circle cx="0" cy="430" r="26" fill="{l}"/><circle cx="-60" cy="470" r="12" fill="{l}"/><circle cx="60" cy="470" r="12" fill="{l}"/></g>'''
    body = f'<ellipse cx="400" cy="860" rx="300" ry="36" fill="url(#sh)"/>{one(290, -10)}{one(520, 9)}'
    return _wrap(*bg, body)


def pipo(c, bg=('#f1ede4', '#e3dccd')):
    d, l = _shade(c, -.22), _shade(c, .55)
    body = f'''<ellipse cx="400" cy="840" rx="270" ry="34" fill="url(#sh)"/>
<circle cx="400" cy="250" r="95" fill="{l}"/>{''.join(f'<circle cx="{400 + dx}" cy="{250 + dy}" r="16" fill="#fff" fill-opacity=".25"/>' for dx, dy in [(-40, -30), (30, -50), (50, 20), (-20, 40), (-55, 15)])}
<path d="M170 700 c0-260 90-380 230-380 s230 120 230 380Z" fill="{c}"/><path d="M170 700 c0-260 90-380 230-380 s230 120 230 380Z" fill="url(#knit)"/>
{''.join(f'<path d="M{x} 360 C{x - 8} 500 {x - 5} 620 {x} 700" fill="none" stroke="#000" stroke-opacity=".08" stroke-width="10"/>' for x in range(230, 590, 45))}
<rect x="150" y="660" width="500" height="130" rx="40" fill="{d}"/>{''.join(f'<rect x="{x}" y="672" width="12" height="106" rx="6" fill="#000" fill-opacity=".12"/>' for x in range(175, 640, 26))}
<rect x="350" y="690" width="100" height="70" rx="10" fill="#f7f2ea"/><text x="400" y="735" font-family="Georgia,serif" font-size="26" text-anchor="middle" fill="{d}">V&amp;L</text>'''
    return _wrap(*bg, body)


def huivi(c, c2, bg=('#efe9e2', '#ded3c6')):
    d = _shade(c, -.22)
    body = f'''<ellipse cx="400" cy="870" rx="300" ry="34" fill="url(#sh)"/>
<path d="M210 200 c120 -60 260 -60 380 0 c40 120 30 230 -20 330 l-60 330 h-110 l20 -320 c-60 -10 -150 -30 -190 -80 c-50 -80 -60 -180 -20 -260Z" fill="{c}"/>
<path d="M210 200 c120 -60 260 -60 380 0 c40 120 30 230 -20 330 l-60 330 h-110 l20 -320 c-60 -10 -150 -30 -190 -80 c-50 -80 -60 -180 -20 -260Z" fill="url(#knit)"/>
{''.join(f'<rect x="420" y="{y}" width="150" height="26" fill="{c2}" transform="rotate(8 495 {y})"/>' for y in (560, 640, 720))}
{''.join(f'<rect x="{x}" y="860" width="10" height="70" rx="5" fill="{d}"/>' for x in range(422, 535, 18))}
<path d="M260 230 c80 40 200 40 290 0" fill="none" stroke="{d}" stroke-width="14" opacity=".6"/>'''
    return _wrap(*bg, body)


def kera(c, bg=('#f3ede5', '#e5dbcf')):
    d, l = _shade(c, -.25), _shade(c, .3)
    body = f'''<ellipse cx="400" cy="800" rx="230" ry="32" fill="url(#sh)"/><circle cx="400" cy="560" r="230" fill="{c}"/>
{''.join(f'<path d="M{170 + i * 6} {420 + i * 14} C 330 {360 + i * 22} 470 {760 - i * 18} {630 - i * 6} {690 - i * 10}" fill="none" stroke="{d if i % 2 else l}" stroke-width="9" opacity=".9"/>' for i in range(12))}
<path d="M560 720 c80 60 140 90 210 70" fill="none" stroke="{c}" stroke-width="10"/><circle cx="400" cy="560" r="230" fill="url(#gl)" opacity=".6"/>
<rect x="250" y="200" width="300" height="70" rx="12" fill="#fbf7f1"/><text x="400" y="246" font-family="Georgia,serif" font-size="30" text-anchor="middle" fill="{d}">100 g · 100 % villa</text>'''
    return _wrap(*bg, body)


def lahja(c1, c2, bg=('#f4e9e6', '#e7d4cf')):
    body = f'''<ellipse cx="400" cy="860" rx="300" ry="34" fill="url(#sh)"/>
<rect x="150" y="430" width="500" height="400" rx="20" fill="#efe4d6"/><rect x="130" y="370" width="540" height="110" rx="20" fill="#e6d8c6"/>
<rect x="370" y="370" width="60" height="460" fill="{c1}"/><rect x="130" y="400" width="540" height="40" fill="{c1}" opacity=".0"/>
<path d="M400 370 c-90 -120 -190 -60 -120 0Z" fill="{c1}"/><path d="M400 370 c90 -120 190 -60 120 0Z" fill="{c1}"/>
<g transform="translate(200 470) rotate(-12) scale(.32)"><path d="M300 170 h200 v330 c0 40 10 70 40 100 l90 90 c50 50 40 140-40 160 c-50 12-100-5-140-45 L310 600 c-25-25-10-60-10-100 Z" fill="{c2}"/></g>
<g transform="translate(430 500) rotate(10) scale(.3)"><path d="M300 170 h200 v330 c0 40 10 70 40 100 l90 90 c50 50 40 140-40 160 c-50 12-100-5-140-45 L310 600 c-25-25-10-60-10-100 Z" fill="{c2}"/></g>
<rect x="250" y="680" width="300" height="80" rx="10" fill="#fbf7f1"/><text x="400" y="732" font-family="Georgia,serif" font-size="34" text-anchor="middle" fill="#5b2a3d">Lämmin talvi</text>'''
    return _wrap(*bg, body)


def kansi_villa():
    body = f'''<rect width="1600" height="900" fill="#3c1f2f"/><circle cx="1250" cy="300" r="420" fill="#5b2a3d"/><circle cx="1350" cy="760" r="260" fill="#6e3a4f"/>
<rect width="1600" height="900" fill="url(#knit)" opacity=".5"/>
<g transform="translate(820 40) scale(.85)">{sukka("#c9a86a", "tunturi", ("#00000000", "#00000000")).split("</defs>")[1].replace("</svg>", "").replace('<rect width="800" height="1000" fill="url(#bg)"/><rect width="800" height="1000" fill="url(#dots)"/>', "")}</g>
<g transform="translate(1080 140) scale(.7)">{sukka("#e9e1d3", "kuura", ("#00000000", "#00000000")).split("</defs>")[1].replace("</svg>", "").replace('<rect width="800" height="1000" fill="url(#bg)"/><rect width="800" height="1000" fill="url(#dots)"/>', "")}</g>'''
    return _wrap('#3c1f2f', '#2a1420', body, 1600, 900)


# ---------- Kotileipomo Ruis ----------
def ruisleipa(bg=('#efe6d8', '#e0d0b8')):
    body = '''<ellipse cx="400" cy="800" rx="290" ry="40" fill="url(#sh)"/>
<ellipse cx="400" cy="600" rx="290" ry="190" fill="#5a3a24"/><ellipse cx="400" cy="570" rx="280" ry="170" fill="#6e4a2f"/>
<circle cx="400" cy="570" r="34" fill="#4a2f1c"/>''' + ''.join(f'<circle cx="{400 + dx}" cy="{570 + dy}" r="5" fill="#d8c3a0" opacity=".8"/>' for dx, dy in [(-200, -40), (-120, 60), (150, -60), (210, 40), (60, 100), (-40, -110), (90, -120), (-170, 90)]) + \
        '<path d="M180 500 c80 -60 160 -80 220 -80" fill="none" stroke="#8d6644" stroke-width="10" stroke-linecap="round" opacity=".7"/>'
    return _wrap(*bg, body)


def saaristolais(bg=('#f0e7d6', '#e2d3b9')):
    body = '''<ellipse cx="400" cy="800" rx="300" ry="36" fill="url(#sh)"/><rect x="140" y="430" width="520" height="330" rx="70" fill="#3b2416"/><rect x="150" y="410" width="500" height="300" rx="70" fill="#4d301c"/>
''' + ''.join(f'<ellipse cx="{x}" cy="{y}" rx="12" ry="7" fill="#c9a46b" transform="rotate(30 {x} {y})"/>' for x, y in [(230, 470), (320, 520), (430, 470), (540, 520), (280, 600), (480, 610), (370, 640), (580, 450)]) + \
        '<path d="M180 440 c120 -40 300 -40 440 0" fill="none" stroke="#6b4428" stroke-width="12" opacity=".7"/>'
    return _wrap(*bg, body)


def korvapuusti(bg=('#f6ead8', '#ead6b8')):
    def bun(x, y, s):
        return f'''<g transform="translate({x} {y}) scale({s})"><ellipse cx="0" cy="40" rx="150" ry="30" fill="url(#sh)"/><path d="M-130 0 c0-90 260-90 260 0 c0 60-60 70-130 70 s-130-10-130-70Z" fill="#c98a45"/>
<path d="M-90 -10 c30-40 90-40 120 0 c20 30-10 60-60 50 c-40-8-40-40-10-50" fill="none" stroke="#8a5227" stroke-width="16" stroke-linecap="round"/>''' + ''.join(f'<rect x="{dx}" y="{dy}" width="14" height="9" rx="3" fill="#fff" opacity=".92"/>' for dx, dy in [(-60, -30), (-10, -45), (40, -20), (10, 10), (-40, 15), (70, 5)]) + '</g>'
    body = '<rect x="120" y="640" width="560" height="40" rx="20" fill="#e2cfb0"/>' + bun(280, 560, 1.05) + bun(520, 580, .95) + bun(400, 420, 1.1)
    return _wrap(*bg, body)


def piirakka(bg=('#f4ead9', '#e6d6bb')):
    def one(x, y, r):
        return f'''<g transform="translate({x} {y}) rotate({r})"><ellipse cx="0" cy="0" rx="150" ry="80" fill="#caa46a"/><ellipse cx="0" cy="0" rx="110" ry="50" fill="#f4e4b8"/>
''' + ''.join(f'<path d="M{dx} -58 l12 18 12 -18" fill="none" stroke="#a87c43" stroke-width="7"/>' for dx in range(-110, 110, 26)) + \
            ''.join(f'<path d="M{dx} 58 l12 -18 12 18" fill="none" stroke="#a87c43" stroke-width="7"/>' for dx in range(-110, 110, 26)) + '<ellipse cx="-20" cy="-8" rx="40" ry="14" fill="#fff6d6" opacity=".9"/></g>'
    body = '<ellipse cx="400" cy="820" rx="300" ry="34" fill="url(#sh)"/>' + one(290, 620, -10) + one(520, 650, 12) + one(400, 450, -4)
    return _wrap(*bg, body)


def kakku(c='#e6879a', bg=('#f7ebec', '#ecd7da')):
    body = f'''<ellipse cx="400" cy="860" rx="300" ry="34" fill="url(#sh)"/><ellipse cx="400" cy="820" rx="290" ry="40" fill="#e9e2dc"/>
<rect x="160" y="480" width="480" height="320" rx="30" fill="#fbf6ef"/><rect x="160" y="600" width="480" height="40" fill="{c}" opacity=".85"/>
<path d="M160 510 q30 50 60 0 q30 50 60 0 q30 50 60 0 q30 50 60 0 q30 50 60 0 q30 50 60 0 q30 50 60 0 q30 50 60 0 v-30 h-480Z" fill="#fff"/>
<ellipse cx="400" cy="480" rx="240" ry="50" fill="#fffaf3"/>''' + ''.join(f'<circle cx="{x}" cy="{y}" r="22" fill="{c}"/><path d="M{x - 6} {y - 22} q6 -16 14 -6" stroke="#3d7a3a" stroke-width="5" fill="none"/>' for x, y in [(300, 470), (360, 455), (430, 458), (495, 472), (400, 495)]) + \
        '<text x="400" y="720" font-family="Georgia,serif" font-size="40" text-anchor="middle" fill="#a55a6a" font-style="italic">Onnea!</text>'
    return _wrap(*bg, body)


def sampyla(bg=('#efe9d9', '#e0d6bd')):
    def one(x, y):
        return f'<g transform="translate({x} {y})"><ellipse cx="0" cy="30" rx="120" ry="26" fill="url(#sh)"/><ellipse cx="0" cy="0" rx="110" ry="80" fill="#d9b27a"/><path d="M-60 -20 q60 -40 120 0" stroke="#b08550" stroke-width="10" fill="none"/>' + \
            ''.join(f'<ellipse cx="{dx}" cy="{dy}" rx="9" ry="5" fill="#f3e6c8"/>' for dx, dy in [(-40, -30), (0, -45), (40, -30), (-20, 10), (30, 5)]) + '</g>'
    body = one(270, 520) + one(520, 540) + one(400, 380) + one(390, 680) + \
        '<rect x="300" y="160" width="200" height="70" rx="35" fill="#fbf7ec"/><text x="400" y="207" font-family="Georgia,serif" font-size="32" text-anchor="middle" fill="#6a7a35">G · gluteeniton</text>'
    return _wrap(*bg, body)


def mustikkapiirakka(bg=('#ece9f2', '#dcd6e6')):
    body = '''<ellipse cx="400" cy="820" rx="300" ry="36" fill="url(#sh)"/><ellipse cx="400" cy="600" rx="290" ry="170" fill="#d7aa6a"/><ellipse cx="400" cy="585" rx="250" ry="140" fill="#3e3a6e"/>
''' + ''.join(f'<circle cx="{400 + dx}" cy="{585 + dy}" r="14" fill="#5a5596"/>' for dx, dy in [(-150, -40), (-90, 30), (-30, -60), (40, 20), (110, -40), (160, 30), (0, 80), (-120, 80), (90, 90), (30, -100)]) + \
        ''.join(f'<rect x="{x}" y="470" width="22" height="240" rx="10" fill="#e8c287" transform="rotate(35 {x} 590)"/>' for x in (220, 330, 440, 550))
    return _wrap(*bg, body)


def lihapiirakka(bg=('#f2e6d6', '#e2cfb4')):
    body = '''<ellipse cx="400" cy="800" rx="260" ry="34" fill="url(#sh)"/><path d="M150 620 c0 -180 500 -180 500 0 c0 90 -500 90 -500 0Z" fill="#c78b4a"/>
<path d="M170 600 c40 -120 420 -120 460 0" fill="none" stroke="#e2b072" stroke-width="18" stroke-linecap="round" opacity=".7"/><circle cx="330" cy="560" r="8" fill="#f4ddb0"/><circle cx="460" cy="550" r="8" fill="#f4ddb0"/>'''
    return _wrap(*bg, body)


def kansi_leipomo():
    body = '''<rect width="1600" height="900" fill="#2b1d14"/><circle cx="1240" cy="420" r="460" fill="#3b2819"/><circle cx="1240" cy="420" r="330" fill="#4a3220"/>
<g transform="translate(780 60) scale(.95)"><ellipse cx="400" cy="600" rx="290" ry="190" fill="#5a3a24"/><ellipse cx="400" cy="570" rx="280" ry="170" fill="#7a5233"/><circle cx="400" cy="570" r="34" fill="#4a2f1c"/>
<path d="M180 500 c80 -60 160 -80 220 -80" fill="none" stroke="#9b7450" stroke-width="12" stroke-linecap="round"/></g>
<g transform="translate(1180 470) scale(.6)"><path d="M-130 0 c0-90 260-90 260 0 c0 60-60 70-130 70 s-130-10-130-70Z" fill="#c98a45"/><path d="M-90 -10 c30-40 90-40 120 0 c20 30-10 60-60 50 c-40-8-40-40-10-50" fill="none" stroke="#8a5227" stroke-width="16" stroke-linecap="round"/></g>
''' + ''.join(f'<path d="M{x} {y} q20 -40 0 -80" fill="none" stroke="#fff" stroke-opacity=".15" stroke-width="10" stroke-linecap="round"/>' for x, y in [(1100, 300), (1180, 280), (1260, 300)])
    return _wrap('#2b1d14', '#1d130d', body, 1600, 900)
