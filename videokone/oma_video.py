"""Netvo-video Hein omasta puheesta: kasvot + kuvitus (oma ääni taustalla) + loppuun mallikauppanäyte.

Syötteet työhakemistossa: a.mp4 ja b.mp4 (1080x1920, 30 fps), teksti.json (ElevenLabs scribe, a+b peräkkäin
alkuperäisessä järjestyksessä b ensin: puhe.mp3 = b + a) sekä kauppa-leipomo-koko.jpg ja kauppa-kasityo-koko.jpg.
Aja: python3 oma_video.py   (PV=1,5,9 tekee esikatselukuvat)
"""
import json, math, os, re, subprocess, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HERE = pathlib.Path(__file__).parent
W, H, FPS = 1080, 1920, 30
OUT = os.environ.get("ULOS", "video.mp4")
src = (HERE / "netvo_promo.py").read_text()
exec(src[src.index("def F(n, s)"):src.index("A = json.load")])
exec(src[src.index("# ---------- apurit"):src.index("# ---------- puhelinkehys")])
exec(src[src.index("yy = np.linspace"):src.index("TAG = logo")])

# ---------- leikkaus ----------
B_LEN = 23.5136                     # puhe.mp3:ssa b (194853) on ensin, a (194939) perässä
A_IN, A_OUT = 0.0, 12.9             # a: "Ei enää tuhansia euroja..." (koukku)
B_IN, B_OUT = 0.15, 23.35           # b: "Sano vaan..." -> netvo.fi
LA = A_OUT - A_IN; LB = B_OUT - B_IN
OUTRO = 4.0
DUR = LA + LB + OUTRO
N = int(DUR * FPS)

sana = [w for w in json.load(open("teksti.json"))["words"] if w["type"] == "word"]
words = []
for w in sana:
    if w["start"] >= B_LEN - 0.05: t0, t1 = w["start"] - B_LEN - A_IN, w["end"] - B_LEN - A_IN
    else: t0, t1 = w["start"] - B_IN + LA, w["end"] - B_IN + LA
    if 0 <= t0 < LA + LB: words.append((w["text"], t0, t1))
words.sort(key=lambda x: x[1])
def aika(s, n=1):  # n:nnen sanan alku, joka alkaa merkkijonolla s
    k = 0
    for w_, a_, b_ in words:
        if w_.lower().strip(".,").startswith(s):
            k += 1
            if k == n: return a_
    raise SystemExit("ei löydy " + s)
T_JOS = aika("jos") - 0.15
T_SILLA = aika("sillä") - 0.2
T_SANO = LA
T_EI2 = aika("ei", 2) - 0.25
T_JOTEN = aika("joten") - 0.25
T_SOITA = aika("soita")
T_NETVON = aika("netvon")
T_OUTRO = LA + LB
NUMERO = (aika("nolla"), aika("yhdeksän") + 0.45)
print("aikarajat", [round(x, 2) for x in (T_JOS, T_SILLA, T_SANO, T_EI2, T_JOTEN, T_SOITA, T_NETVON, T_OUTRO)], "kesto", round(DUR, 1))
SEG = [(0, T_JOS, "kasvo"), (T_JOS, T_SILLA, "haku"), (T_SILLA, T_SANO, "kauppa"), (T_SANO, T_EI2, "kasvo"),
       (T_EI2, T_JOTEN, "lista"), (T_JOTEN, T_OUTRO, "kasvo"), (T_OUTRO, DUR, "loppu")]

# ---------- kasvovideon kehykset ----------
class Lukija:
    def __init__(s, f, alku, kesto):
        s.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(alku), "-t", str(kesto + 0.5), "-i", f, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        s.i = -1; s.kuva = None
    def hae(s, i):
        while s.i < i:
            b = s.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            s.kuva = Image.frombuffer("RGB", (W, H), b).convert("RGBA"); s.i += 1
        return s.kuva
LA_ = LB_ = None
def kasvo(t):
    global LA_, LB_
    if t < LA:
        if LA_ is None: LA_ = Lukija("a.mp4", A_IN, LA)
        return LA_.hae(int(t * FPS))
    if LB_ is None: LB_ = Lukija("b.mp4", B_IN, LB)
    return LB_.hae(int((t - LA) * FPS))
def kupla(img, d=300):
    c = img.crop((90, 260, 990, 1160)).resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 2, d * 2), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 2 - 1, d * 2 - 1), fill=255); m = m.resize((d, d), Image.LANCZOS)
    o = Image.new("RGBA", (d + 16, d + 16), (0, 0, 0, 0)); ImageDraw.Draw(o).ellipse((0, 0, d + 15, d + 15), fill=LIME + (255,))
    o.paste(c, (8, 8), m); return o

# ---------- kuvitukset ----------
PW, PH = 560, 1060
def lataa(n):
    im = Image.open(n).convert("RGBA"); return im.resize((PW, round(im.height * PW / im.width)), Image.LANCZOS)
LEIPOMO, VILLA = lataa("kauppa-leipomo-koko.jpg"), lataa("kauppa-kasityo-koko.jpg")
def puhelin(img, off):
    c = Image.new("RGBA", (PW + 44, PH + 44), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, PW + 43, PH + 43), radius=70, fill=(12, 14, 20, 255))
    ruutu = Image.new("RGBA", (PW, PH), PAPER + (255,)); off = int(max(0, min(off, img.height - PH)))
    ruutu.alpha_composite(img.crop((0, off, PW, off + PH)), (0, 0))
    m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=50, fill=255)
    c.paste(ruutu, (22, 22), m); d.rounded_rectangle((PW // 2 - 60 + 22, 34, PW // 2 + 60 + 22, 62), radius=14, fill=(12, 14, 20, 255))
    return c
TULOKSET = [("Nettisivuprojekti", "3 000 €"), ("Yrityksen kotisivut", "2 490 €"), ("Sivusto + ylläpito", "4 900 €")]
def hakukortti(lt):
    w = 940; c = Image.new("RGBA", (w, 860), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, 859), radius=34, fill=PAPER + (255,))
    d.rounded_rectangle((40, 40, w - 40, 140), radius=50, outline=(210, 214, 222), width=4)
    hs = "edulliset nettisivut"; n = int(len(hs) * ease(lt * 1.3))
    d.ellipse((76, 66, 120, 110), outline=MUTE, width=6); d.line([(114, 104), (132, 122)], fill=MUTE, width=7)
    d.text((160, 64), hs[:n], font=M8(44), fill=INK)
    for k, (nimi, hinta) in enumerate(TULOKSET):
        q = ease((lt - 0.7 - k * 0.3) * 3)
        if q <= 0: continue
        y = 200 + k * 210; a = int(255 * q)
        d.text((60, y), "Mainos · nettisivutoimisto", font=M6(30), fill=MUTE + (a,))
        d.text((60, y + 44), nimi, font=M9(48), fill=SIN + (a,))
        d.text((w - 60, y + 44), hinta, font=M9(52), fill=RED + (a,), anchor="ra")
        if k < 2: d.line([(60, y + 170), (w - 60, y + 170)], fill=(230, 232, 238, a), width=3)
    return c
def risti(d, x, y, s):
    d.ellipse((x, y, x + s, y + s), fill=RED); q = s * 0.3
    d.line([(x + q, y + q), (x + s - q, y + s - q)], fill=WHITE, width=s // 8); d.line([(x + s - q, y + q), (x + q, y + s - q)], fill=WHITE, width=s // 8)
LISTA = [("kalliita", True, "Ei kalliita investointeja"), ("ylläpitokulut", True, "Kohtuullinen ylläpito"), ("ylläpitokulut", True, "Räätälöity yrityksellesi")]
LISTA_T = [aika("kalliita") - 0.1, aika("ylläpitokulut") - 0.1, aika("kohtuulliset") + 0.2]

def kuvitus(base, laji, lt, t, dur):
    if laji == "haku":
        paste_c(base, iso_teksti("Etsitkö edullisia nettisivuja?", koko=110, vari=WHITE, vari2=YEL), W / 2, 330, back(lt * 3))
        paste_c(base, hakukortti(lt), W / 2, 960, back(lt * 3 - 0.15))
        if lt > dur * 0.68: paste_c(base, pill("LOPETA ETSIMINEN", M9(66), WHITE, RED + (255,), 44, 26).rotate(-5, expand=True, resample=Image.BICUBIC), W / 2, 1000, back((lt - dur * 0.68) * 4))
    elif laji == "kauppa":
        paste_c(base, logo(110), W / 2, 210, back(lt * 3))
        puoli = dur * 0.55
        if lt < puoli: kuva, off = LEIPOMO, ease(lt / puoli) * 2600
        else: kuva, off = VILLA, ease((lt - puoli) / (dur - puoli)) * 2200
        paste_c(base, puhelin(kuva, off), W / 2, 930, back(lt * 3 - 0.15) * 0.97)
        paste_c(base, pill("Räätälöity yrityksellesi", M9(46), WHITE, VIHR + (255,), 34, 20), W / 2, 1500, back(lt * 4 - 0.3))
    elif laji == "lista":
        paste_c(base, iso_teksti("Netvolla", koko=150, vari=WHITE, vari2=WHITE), W / 2, 330, back(lt * 3))
        lt_ = Image.new("RGBA", (900, 520), (0, 0, 0, 0)); dl = ImageDraw.Draw(lt_)
        dl.rounded_rectangle((0, 0, 899, 519), radius=34, fill=(255, 255, 255, 26), outline=(255, 255, 255, 70), width=3)
        for k, (_, ok, s_) in enumerate(LISTA):
            if t < LISTA_T[k]: continue
            y = 60 + k * 150
            if ok: ruksi(dl, 50, y, 84, VIHR)
            else: risti(dl, 50, y, 84)
            dl.text((170, y + 42), s_, font=M8(54), fill=WHITE if ok else (255, 190, 195), anchor="lm")
            if not ok and t > LISTA_T[k] + 0.5: dl.line([(165, y + 46), (165 + M8(54).getlength(s_), y + 46)], fill=RED, width=8)
        paste_c(base, lt_, W / 2, 860, back(lt * 3 - 0.15))
    elif laji == "loppu":
        paste_c(base, logo(150), W / 2, 210, back(lt * 3))
        paste_c(base, puhelin(LEIPOMO, ease(lt / dur) * 1800), W / 2, 900, back(lt * 3) * 0.9)
        paste_c(base, pill("Mallikauppa: Kotileipomo Ruis", M9(44), WHITE, VIHR + (255,), 34, 20), W / 2, 1450, back(lt * 4 - 0.2))
        paste_c(base, pill("netvo.fi · 044 777 7149", M9(60), WHITE, SIN + (255,), 44, 24), W / 2, 1620, back(lt * 4 - 0.5) * (1 + 0.03 * math.sin(t * 5)))

# ---------- tekstitys ----------
SUBF = M9(64)
def tok(w_): return w_.strip(".,:;!?\"”“").upper()
CHUNKS, cur = [], []
for idx, (w_, a_, b_) in enumerate(words):
    if NUMERO[0] - 0.05 <= a_ <= NUMERO[1]:
        if cur and words[cur[0]][1] < NUMERO[0] - 0.05: CHUNKS.append(cur); cur = []
        cur.append(idx); continue
    if cur and NUMERO[0] - 0.05 <= words[cur[-1]][1] <= NUMERO[1]: CHUNKS.append(cur); cur = []
    test = " ".join([tok(words[j][0]) for j in cur] + [tok(w_)])
    if cur and (SUBF.getlength(test) > 900 or len(cur) >= 4): CHUNKS.append(cur); cur = []
    cur.append(idx)
    if w_.endswith((".", ",", "?", "!")): CHUNKS.append(cur); cur = []
if cur: CHUNKS.append(cur)
def subtitle(base, t, y=1560):
    done = [i for i, w in enumerate(words) if w[1] <= t + 0.04]
    if not done: return
    i = done[-1]
    if t > words[i][2] + 0.5: return
    c = next((c for c in CHUNKS if i in c), None)
    if c is None: return
    if NUMERO[0] - 0.05 <= words[c[0]][1] <= NUMERO[1]: toks = [("044 777 7149", True)]
    else: toks = [(tok(words[j][0]), j == i) for j in c]
    line = " ".join(x for x, _ in toks); f = SUBF
    while f.getlength(line) > W - 100: f = M9(f.size - 4)
    x = (W - f.getlength(line)) / 2; d = ImageDraw.Draw(base)
    for s_, on in toks:
        d.text((x, y), s_, font=f, fill=YEL if on else WHITE, stroke_width=9, stroke_fill=(0, 0, 0)); x += f.getlength(s_ + " ")

TAG = logo(64)
# ---------- renderöinti ----------
PV = os.environ.get("PV")
AF = (f"[1:a]atrim={A_IN}:{A_OUT},asetpts=PTS-STARTPTS,afade=t=out:st={LA - 0.04}:d=0.04[x];"
      f"[2:a]atrim={B_IN}:{B_OUT},asetpts=PTS-STARTPTS,afade=t=in:d=0.03[y];"
      f"[x][y]concat=n=2:v=0:a=1,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-14:TP=-1.5:LRA=9,apad=pad_dur={OUTRO + 1}[a]")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", "a.mp4", "-i", "b.mp4", "-filter_complex", AF,
       "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", OUT]
if not PV: p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for f in ([int(float(x) * FPS) for x in PV.split(",")] if PV else range(N)):
    t = f / FPS
    a_, b_, laji = next(s for s in SEG if s[0] <= t < s[1]) if t < DUR else SEG[-1]
    lt = t - a_; dur = b_ - a_
    if laji == "kasvo":
        fr = kasvo(t).copy()
        if a_ >= LA:  # pieni zoomaus toiseen kasvo-osuuteen
            z = 1.0 + 0.06 * ease(lt / dur); cw, ch_ = int(W / z), int(H / z)
            fr = fr.crop(((W - cw) // 2, int((H - ch_) * 0.35), (W - cw) // 2 + cw, int((H - ch_) * 0.35) + ch_)).resize((W, H))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((0, 1380, W, H), fill=(0, 0, 0, 70)); fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(60)))
        fr.alpha_composite(TAG, (40, 60))
        if t < T_JOS: paste_c(fr, pill("NETTISIVUT YRITTÄJILLE", M9(44), INK, YEL + (255,), 32, 18), W / 2, 220, back(lt * 3))
        if T_SOITA - 0.2 <= t < T_OUTRO:
            q = t - T_SOITA + 0.2
            paste_c(fr, pill("044 777 7149", M9(88), WHITE, VIHR + (255,), 54, 30), W / 2, 1290, back(q * 4) * (1 + 0.02 * math.sin(t * 6)))
            if t >= T_NETVON: paste_c(fr, pill("netvo.fi", M9(80), WHITE, SIN + (255,), 54, 28), W / 2, 1120, back((t - T_NETVON) * 4))
    else:
        fr = BG.copy()
        fr.alpha_composite(G1, (int(-200 + 160 * math.sin(t * 0.4)), int(200 + 120 * math.cos(t * 0.3))))
        fr.alpha_composite(G2, (int(W - 500 + 120 * math.cos(t * 0.5)), int(1100 + 160 * math.sin(t * 0.35))))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); kuvitus(layer, laji, lt, t, dur); fr.alpha_composite(layer)
        if laji != "loppu":
            k = kasvo(t)
            if k is not None: fr.alpha_composite(kupla(k, 250), (W - 300, 60) if laji == "kauppa" else (W - 300, 1250))
        if laji not in ("kauppa", "loppu"): fr.alpha_composite(TAG, (40, 60))
    if laji == "kasvo" and lt < 0.12 and a_ > 0:  # nopea välähdys leikkauksessa
        fr = Image.blend(fr, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35 * (1 - lt / 0.12))
    if laji != "loppu" and not (NUMERO[0] - 0.05 <= t <= NUMERO[1] + 0.5): subtitle(fr, t)
    if PV: fr.convert("RGB").resize((540, 960)).save(f"pv_{t:.1f}.jpg"); continue
    p.stdin.write(fr.convert("RGB").tobytes())
if not PV: p.stdin.close(); p.wait(); print("valmis", OUT, N, "kuvaa")
