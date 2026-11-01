"""Päivittäinen mainosraportti Telegramiin (Google Ads + Bing). Ei tulosta avaimia."""
import os, json, urllib.request, datetime
import gads, msads, xads

G = "4566722878"
def eur(m): return f"{int(m or 0)/1e6:.2f} €".replace(".", ",")

def google():
    q = lambda s: gads.kutsu(f"/customers/{G}/googleAds:search", {"query": s})
    rivit = ["<b>Google Ads</b>"]
    eilen = {r["campaign"]["id"]: r.get("metrics", {}) for r in q("SELECT campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING YESTERDAY").get("results", [])}
    kk = q("SELECT metrics.cost_micros FROM customer WHERE segments.date DURING THIS_MONTH").get("results", [{}])
    v = q("SELECT campaign.id, campaign.name, campaign.status, campaign.primary_status, campaign_budget.amount_micros, campaign_budget.total_amount_micros, campaign.end_date_time FROM campaign WHERE campaign.status != 'REMOVED'")
    if "virhe" in v: return rivit + ["⚠️ Haku epäonnistui: " + str(v["virhe"])]
    for r in v.get("results", []):
        c, b = r["campaign"], r.get("campaignBudget", {}); m = eilen.get(c["id"], {})
        tila = {"ENABLED": "🟢", "PAUSED": "⏸"}.get(c["status"], c["status"])
        bud = (eur(b["amountMicros"]) + "/pv") if b.get("amountMicros") else (eur(b.get("totalAmountMicros")) + " yht.")
        loppu = f", päättyy {c['endDateTime'][:10]}" if c.get("endDateTime") else ""
        rivit.append(f"{tila} {c['name']} ({bud}{loppu})\n   eilen: {m.get('impressions','0')} näyttöä, {m.get('clicks','0')} klikkiä, {eur(m.get('costMicros'))}"
                     + ("" if c.get("primaryStatus") in ("ELIGIBLE", "PAUSED", None) else f"\n   ⚠️ {c['primaryStatus'].lower()}"))
    hyl = q("SELECT campaign.name FROM ad_group_ad WHERE ad_group_ad.policy_summary.approval_status = 'DISAPPROVED' AND campaign.status = 'ENABLED'").get("results", [])
    if hyl: rivit.append(f"⚠️ Hylättyjä mainoksia: {len(hyl)}")
    rivit.append(f"Kuukausi tähän mennessä: {eur((kk[0].get('metrics') or {}).get('costMicros'))}")
    return rivit

def bing():
    rivit = ["<b>Bing</b>"]
    v = msads.kutsu(msads.CM + "/Campaigns/QueryByAccountId", {"AccountId": msads.AID, "CampaignType": "Search"})
    if "virhe" in v: return rivit + ["⚠️ Haku epäonnistui: " + str(v.get("vastaus", ""))[:200]]
    for c in v.get("Campaigns", []):
        tila = {"Active": "🟢", "Paused": "⏸", "BudgetPaused": "⏸ budjetti", "Suspended": "⛔"}.get(c["Status"], c["Status"])
        rivit.append(f"{tila} {c['Name']} ({c.get('DailyBudget')} €/pv)")
    t = msads.kutsu(msads.CUS + "/AccountsInfo/Query", {"CustomerId": msads.CID, "OnlyParentAccounts": False}, tili=False)
    for a in t.get("AccountsInfo", []) or []:
        if a.get("AccountLifeCycleStatus") not in ("Active", None):
            rivit.append(f"⚠️ Tilin tila: {a['AccountLifeCycleStatus']} (esim. vahvistus tai kortti kesken)")
    return rivit

def ilmainen():
    """Ilmainen liikenne hakukoneista ja tekoälyistä Cloudflare Web Analyticsista (eilinen päivä)."""
    cf = os.environ.get("CF", "").strip()
    if not cf: return []
    h = {"Authorization": "Bearer " + cf, "Content-Type": "application/json"}
    acc = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/accounts", headers=h)).read())["result"][0]["id"]
    eilen = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    q = """query($a:String!,$d:Date!){viewer{accounts(filter:{accountTag:$a}){rumPageloadEventsAdaptiveGroups(limit:200,filter:{date:$d}){count dimensions{refererHost requestHost}}}}}"""
    r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", json.dumps({"query": q, "variables": {"a": acc, "d": eilen}}).encode(), h)).read())
    ryhmat = (((r.get("data") or {}).get("viewer") or {}).get("accounts") or [{}])[0].get("rumPageloadEventsAdaptiveGroups") or []
    if not ryhmat: return ["<b>Ilmainen liikenne</b>", "ei tietoa (" + str((r.get("errors") or [{}])[0].get("message", "tyhjä"))[:80] + ")"]
    haku, ai, yht = {}, {}, {}
    for g in ryhmat:
        ref, host, n = (g["dimensions"].get("refererHost") or ""), g["dimensions"].get("requestHost") or "?", g["count"]
        yht[host] = yht.get(host, 0) + n
        if any(x in ref for x in ("google.", "bing.", "duckduckgo.", "yahoo.", "ecosia.")): haku[host] = haku.get(host, 0) + n
        if any(x in ref for x in ("chatgpt.", "openai.", "perplexity.", "claude.ai", "copilot.", "gemini.")): ai[host] = ai.get(host, 0) + n
    rivit = ["<b>Ilmainen liikenne (eilen)</b>"]
    for host in sorted(yht, key=lambda k: -yht[k])[:6]:
        rivit.append(f"{host}: {yht[host]} sivulatausta, hakukoneista {haku.get(host, 0)}" + (f", tekoälyistä {ai[host]}" if ai.get(host) else ""))
    return rivit

def laheta(teksti):
    d = json.dumps({"chat_id": "1893930799", "text": teksti, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{os.environ['TG'].strip()}/sendMessage", d, {"content-type": "application/json"}))

if __name__ == "__main__":
    pv = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%-d.%-m.")
    osat = [f"📊 <b>Mainosraportti</b> (eilen {pv})", ""]
    for f in (google, bing, xads.raporttirivit, ilmainen):
        try: osat += f()
        except Exception as e: osat.append(f"⚠️ {getattr(f, '__name__', 'X')}: {type(e).__name__}")
        osat.append("")
    laheta("\n".join(osat))
    print("::notice title=Raportti::lähetetty")
    for r in osat[-10:]: print("::notice title=Rivi::" + r.replace("<b>", "").replace("</b>", "")[:300])
