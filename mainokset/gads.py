"""Google Ads -rajapinnan apuri GitHub Actionsiin. Avaimet: GitHubin salaisuudet + Faktapisteen holvi.
Ei koskaan tulosta avaimia."""
import os, sys, json, urllib.request, urllib.parse

U = "https://faktapiste.fi/api/hallinta/holvi"
API = "https://googleads.googleapis.com/" + os.environ.get("GADS_VER", "v24") + ""

def holvi(nimi, arvo=None):
    d = {"nimi": nimi}
    if arvo is not None: d["arvo"] = arvo
    r = urllib.request.Request(U, json.dumps(d).encode(), {"x-avain": os.environ["HALLINTA"], "content-type": "application/json", "user-agent": "gads"})
    return json.loads(urllib.request.urlopen(r).read())

def oauth(data):
    data.update(client_id=os.environ["CID"].strip(), client_secret=os.environ["CSEC"].strip())
    try: return json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", urllib.parse.urlencode(data).encode()).read())
    except urllib.error.HTTPError as e: return json.loads(e.read())

def token():
    rt = holvi("gads_refresh")["arvo"]
    if not rt: sys.exit("::error::Kirjautumisavain puuttuu – tee ensin vaihda")
    return oauth({"grant_type": "refresh_token", "refresh_token": rt})["access_token"]

def kutsu(polku, data=None, tapa=None, login=None):
    h = {"Authorization": "Bearer " + token(), "content-type": "application/json"}
    if os.environ.get("DEVTOKEN"): h["developer-token"] = os.environ["DEVTOKEN"]
    if login: h["login-customer-id"] = login
    r = urllib.request.Request(API + polku, json.dumps(data).encode() if data is not None else None, h, method=tapa)
    try: return json.loads(urllib.request.urlopen(r).read() or b"{}")
    except urllib.error.HTTPError as e: return {"virhe": e.code, "vastaus": e.read().decode()[:1500]}

def ilmoita(otsikko, teksti):
    for rivi in str(teksti).splitlines() or [""]:
        [print(f"::notice title={otsikko}::{rivi[i:i+3500]}") for i in range(0, max(len(rivi),1), 3500)]

if __name__ == "__main__":
    t = sys.argv[1]
    if t == "vaihda":
        for koodi in os.environ["KOODI"].split():
            v = oauth({"grant_type": "authorization_code", "code": koodi, "redirect_uri": "http://localhost"})
            if "refresh_token" in v: break
        if "refresh_token" in v:
            holvi("gads_refresh", v["refresh_token"]); ilmoita("Kirjautuminen", "OK – avain tallennettu holviin")
        else: ilmoita("Kirjautuminen", "VIRHE " + str(v.get("error")) + " " + str(v.get("error_description")))
    elif t == "tilit":
        ilmoita("Tilit", json.dumps(kutsu("/customers:listAccessibleCustomers")))
    elif t == "muuta":
        # KYSELY = JSON-lista [[polku, runko], ...], esim. ["campaigns:mutate", {...}]
        asiakas = os.environ["ASIAKAS"].replace("-", "")
        for i, (polku, runko) in enumerate(json.loads(os.environ["KYSELY"])):
            ilmoita(f"Muutos {i+1}", json.dumps(kutsu(f"/customers/{asiakas}/{polku}", runko), ensure_ascii=False, separators=(",", ":")))
    elif t == "pysayta":
        # Pysäyttää kaikki käynnissä olevat kampanjat (tila PAUSED, ei poistoa – voi palauttaa myöhemmin).
        asiakas = os.environ["ASIAKAS"].replace("-", "")
        v = kutsu(f"/customers/{asiakas}/googleAds:search", {"query": "SELECT campaign.resource_name, campaign.name, campaign.status FROM campaign WHERE campaign.status = 'ENABLED'"})
        rivit = v.get("results", [])
        ilmoita("Käynnissä ennen", json.dumps([r["campaign"]["name"] for r in rivit], ensure_ascii=False) if "results" in v or "virhe" not in v else json.dumps(v))
        if rivit:
            ops = [{"update": {"resourceName": r["campaign"]["resourceName"], "status": "PAUSED"}, "updateMask": "status"} for r in rivit]
            ilmoita("Pysäytys", json.dumps(kutsu(f"/customers/{asiakas}/campaigns:mutate", {"operations": ops}), ensure_ascii=False)[:3000])
        v = kutsu(f"/customers/{asiakas}/googleAds:search", {"query": "SELECT campaign.name, campaign.status FROM campaign WHERE campaign.status != 'REMOVED'"})
        ilmoita("Tila nyt", json.dumps([(r["campaign"]["name"], r["campaign"]["status"]) for r in v.get("results", [])], ensure_ascii=False))
    elif t == "kysely":
        asiakas = os.environ["ASIAKAS"].replace("-", "")
        for i, q in enumerate(x for x in os.environ["KYSELY"].split(";;") if x.strip()):
            v = kutsu(f"/customers/{asiakas}/googleAds:search", {"query": q.strip()})
            v.pop("fieldMask", None)
            ilmoita(f"Kysely {i+1}", json.dumps(v, ensure_ascii=False, separators=(",", ":")))
