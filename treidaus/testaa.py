"""Testaa historiadatalla, voiko Bitcoinin ja kullan (PAXG) hintasuuntaa ennustaa
30 s, 1 min, 10 min ja 30 min päähän. Data: Binancen julkinen arkisto (data.binance.vision).
Malli koulutetaan vanhemmalla datalla ja testataan uudemmalla (ei kurkistusta tulevaan)."""
import io, zipfile, json, datetime as dt, requests, numpy as np, pandas as pd, lightgbm as lgb

BASE = "https://data.binance.vision/data/spot/monthly/klines"
COLS = ["t","o","h","l","c","v","ct","qv","n","tbv","tbqv","x"]

def kuukaudet(n):
    d = dt.date.today().replace(day=1)
    out = []
    for _ in range(n + 1):
        d = (d - dt.timedelta(days=1)).replace(day=1)
        out.append(d.strftime("%Y-%m"))
    return sorted(out[:n])

def lataa(sym, iv, kk):
    osat = []
    for m in kk:
        r = requests.get(f"{BASE}/{sym}/{iv}/{sym}-{iv}-{m}.zip", timeout=120)
        if r.status_code != 200:
            print("puuttuu", sym, iv, m); continue
        z = zipfile.ZipFile(io.BytesIO(r.content))
        df = pd.read_csv(z.open(z.namelist()[0]), header=None, names=COLS)
        osat.append(df)
    df = pd.concat(osat).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    for c in ["o","h","l","c","v","tbv","n"]: df[c] = df[c].astype(float)
    return df

def piirteet(df):
    f = pd.DataFrame(index=df.index)
    lr = np.log(df.c).diff()
    for k in [1, 3, 5, 10, 30, 60]:
        f[f"tuotto_{k}"] = np.log(df.c).diff(k)
    for k in [10, 30, 60]:
        f[f"vola_{k}"] = lr.rolling(k).std()
        f[f"vol_z_{k}"] = (df.v - df.v.rolling(k).mean()) / (df.v.rolling(k).std() + 1e-12)
    f["ostopaine"] = df.tbv / (df.v + 1e-12)
    f["ostopaine_10"] = f.ostopaine.rolling(10).mean()
    f["kauppoja_z"] = (df.n - df.n.rolling(60).mean()) / (df.n.rolling(60).std() + 1e-12)
    f["vaihteluvali"] = (df.h - df.l) / df.c
    up = lr.clip(lower=0).rolling(14).mean(); dn = (-lr.clip(upper=0)).rolling(14).mean()
    f["rsi"] = up / (up + dn + 1e-12)
    f["etais_ka60"] = np.log(df.c) - np.log(df.c.rolling(60).mean())
    return f

def testaa(df, h, kulut, nimi):
    X = piirteet(df)
    tuleva = np.log(df.c.shift(-h)) - np.log(df.c)
    d = X.assign(y=tuleva).dropna()
    d = d.iloc[::max(1, h // 2)]  # vähennetään päällekkäisiä havaintoja
    n = len(d); raja = int(n * 0.7)
    tr, te = d.iloc[:raja], d.iloc[raja:]
    malli = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=31,
                               min_child_samples=200, subsample=0.8, subsample_freq=1,
                               colsample_bytree=0.8, verbose=-1)
    malli.fit(tr.drop(columns="y"), (tr.y > 0).astype(int))
    p = malli.predict_proba(te.drop(columns="y"))[:, 1]
    oikea = (te.y > 0).values
    osuma = float(((p > 0.5) == oikea).mean())
    pohja = float(max(oikea.mean(), 1 - oikea.mean()))
    tulos = {}
    for kynnys in [0.5, 0.55, 0.6]:
        valinta = (p > kynnys) | (p < 1 - kynnys)
        suunta = np.where(p > 0.5, 1, -1)
        bruttotuotot = suunta[valinta] * te.y.values[valinta]
        kpl = int(valinta.sum())
        tulos[str(kynnys)] = {
            "kauppoja": kpl,
            "osuma": float((np.sign(bruttotuotot) > 0).mean()) if kpl else None,
            "brutto_%_per_kauppa": float(bruttotuotot.mean() * 100) if kpl else None,
            "netto_%_per_kauppa": float((bruttotuotot - kulut).mean() * 100) if kpl else None,
            "netto_%_yhteensa": float((bruttotuotot - kulut).sum() * 100) if kpl else None,
        }
    return {"kohde": nimi, "osuma_kaikki": osuma, "arvaus_pohjataso": pohja,
            "testijakso": f"{pd.to_datetime(df.t.iloc[te.index[0]], unit='ms').date()} – {pd.to_datetime(df.t.iloc[te.index[-1]], unit='ms').date()}",
            "testihavaintoja": len(te), "kynnykset": tulos}

KULUT = 0.002   # meno-paluu: 0,1 % kumpaankin suuntaan (Binancen perustaso)
tulokset = []
kk6 = kuukaudet(6); kk1 = kuukaudet(1)
for sym, nimi in [("BTCUSDT", "Bitcoin"), ("PAXGUSDT", "Kulta (PAXG)")]:
    m1 = lataa(sym, "1m", kk6)
    for h, lab in [(1, "1 min"), (10, "10 min"), (30, "30 min")]:
        r = testaa(m1, h, KULUT, nimi); r["aikavali"] = lab; tulokset.append(r); print(r)
    s1 = lataa(sym, "1s", kk1)
    if len(s1):
        r = testaa(s1, 30, KULUT, nimi); r["aikavali"] = "30 s"; tulokset.append(r); print(r)

json.dump(tulokset, open("treidaus/tulokset.json", "w"), ensure_ascii=False, indent=1)
L = ["# Treidausennusteen testitulokset", "",
     f"Ajettu {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC. Malli koulutettu 70 %:lla datasta, testattu uusimmalla 30 %:lla.",
     f"Kaupankäyntikulut: {KULUT*100:.1f} % per kauppa (osto + myynti).", "",
     "| Kohde | Aikaväli | Osuma-% | Arvaus-% | Kauppoja (≥60 %) | Osuma (≥60 %) | Netto/kauppa (≥60 %) |",
     "|---|---|---|---|---|---|---|"]
for r in tulokset:
    k = r["kynnykset"]["0.6"]
    f = lambda x, d=2: "–" if x is None else f"{x:.{d}f}"
    L.append(f"| {r['kohde']} | {r['aikavali']} | {r['osuma_kaikki']*100:.1f} | {r['arvaus_pohjataso']*100:.1f} | {k['kauppoja']} | "
             f"{f(k['osuma'] and k['osuma']*100,1)} | {f(k['netto_%_per_kauppa'],3)} % |")
open("treidaus/tulokset.md", "w").write("\n".join(L) + "\n")
