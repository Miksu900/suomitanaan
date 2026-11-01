"""Kertaluonteinen kävijäerittely yhdelle sivustolle (Cloudflare Web Analytics)."""
import os, json, urllib.request, datetime
cf = os.environ["CF"].strip(); host = os.environ.get("HOST", "eduskuntaseuranta.fi")
h = {"Authorization": "Bearer " + cf, "Content-Type": "application/json"}
acc = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/accounts", headers=h)).read())["result"][0]["id"]
d1 = (datetime.date.today() - datetime.timedelta(days=7)).isoformat(); d2 = datetime.date.today().isoformat()
def q(dim):
    s = f"""query($a:String!,$d1:Date!,$d2:Date!,$h:String!){{viewer{{accounts(filter:{{accountTag:$a}}){{rumPageloadEventsAdaptiveGroups(limit:15,orderBy:[count_DESC],filter:{{date_geq:$d1,date_lt:$d2,requestHost:$h}}){{count sum{{visits}} dimensions{{{dim}}}}}}}}}}}"""
    r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", json.dumps({"query": s, "variables": {"a": acc, "d1": d1, "d2": d2, "h": host}}).encode(), h)).read())
    if r.get("errors"): return "VIRHE " + r["errors"][0]["message"][:200]
    return [(g["dimensions"][dim], g["count"], g["sum"]["visits"]) for g in r["data"]["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"]]
for dim in ("date", "refererHost", "requestPath", "countryName", "deviceType"):
    print(f"::notice title={dim}::" + json.dumps(q(dim), ensure_ascii=False)[:3000])
