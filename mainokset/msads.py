"""Microsoft Advertising (Bing) -rajapinnan apuri GitHub Actionsiin. Ei tulosta avaimia."""
import os, sys, json, urllib.request, urllib.parse
from gads import holvi, ilmoita

CID, AID = "255103446", "188491572"  # asiakas- ja tilitunnus
CLIENT = "a5c26010-4549-400f-806a-4db7204ab906"
SCOPE = "https://ads.microsoft.com/msads.manage offline_access"
CM = "https://campaign.api.bingads.microsoft.com/CampaignManagement/v13"
CUS = "https://clientcenter.api.bingads.microsoft.com/CustomerManagement/v13"

def token():
    rt = holvi("msads_refresh")["arvo"]
    if not rt: sys.exit("::error::Microsoft-lupa puuttuu – avaa https://faktapiste.fi/api/oauth/microsoft/alku")
    d = urllib.parse.urlencode({"client_id": CLIENT, "client_secret": os.environ["MSSEC"].strip(), "grant_type": "refresh_token", "refresh_token": rt, "scope": SCOPE}).encode()
    try: v = json.loads(urllib.request.urlopen("https://login.microsoftonline.com/common/oauth2/v2.0/token", d).read())
    except urllib.error.HTTPError as e: sys.exit("::error::Tokenivirhe " + json.loads(e.read()).get("error", "?"))
    if v.get("refresh_token") and v["refresh_token"] != rt: holvi("msads_refresh", v["refresh_token"])
    return v["access_token"]

_t = None
def kutsu(url, runko, tili=True, tapa="POST"):
    global _t
    _t = _t or token()
    h = {"Authorization": "Bearer " + _t, "DeveloperToken": os.environ["MSDEV"].strip(), "content-type": "application/json"}
    if tili: h.update(CustomerId=CID, CustomerAccountId=AID)
    r = urllib.request.Request(url, json.dumps(runko).encode(), h, method=tapa)
    try: return json.loads(urllib.request.urlopen(r).read() or b"{}")
    except urllib.error.HTTPError as e: return {"virhe": e.code, "vastaus": e.read().decode()[:2000]}

if __name__ == "__main__":
    t = sys.argv[1]
    if t == "kampanjat":
        v = kutsu(CM + "/Campaigns/QueryByAccountId", {"AccountId": AID, "CampaignType": "Search,Audience"})
        ilmoita("Kampanjat", json.dumps([{k: c.get(k) for k in ("Id", "Name", "Status", "DailyBudget", "BudgetType", "CampaignType")} for c in v.get("Campaigns", [])] if "Campaigns" in v else v, ensure_ascii=False))
    elif t == "pysayta":
        # Pysäyttää kaikki aktiiviset kampanjat (Paused, ei poistoa).
        v = kutsu(CM + "/Campaigns/QueryByAccountId", {"AccountId": AID, "CampaignType": "Search,Audience"})
        kamp = [c for c in v.get("Campaigns", []) if c.get("Status") not in ("Paused", "Deleted")]
        ilmoita("Käynnissä ennen", json.dumps([(c["Name"], c.get("Status")) for c in kamp], ensure_ascii=False) if "Campaigns" in v else json.dumps(v))
        if kamp:
            ilmoita("Pysäytys", json.dumps(kutsu(CM + "/Campaigns", {"AccountId": AID, "Campaigns": [{"Id": c["Id"], "Status": "Paused"} for c in kamp]}, tapa="PATCH"), ensure_ascii=False)[:2000])
        v = kutsu(CM + "/Campaigns/QueryByAccountId", {"AccountId": AID, "CampaignType": "Search,Audience"})
        ilmoita("Tila nyt", json.dumps([(c["Name"], c.get("Status")) for c in v.get("Campaigns", [])], ensure_ascii=False))
    elif t == "kutsu":
        # KYSELY = JSON-lista [[polku CM:n alla, runko], ...]
        for i, (polku, runko) in enumerate(json.loads(os.environ["KYSELY"])):
            ilmoita(f"Kutsu {i+1}", json.dumps(kutsu(CM + "/" + polku, runko), ensure_ascii=False, separators=(",", ":")))
