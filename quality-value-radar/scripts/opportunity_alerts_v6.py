#!/usr/bin/env python3
"""Write dated research alerts; never alert as if an unverified model were a buy."""
import datetime as dt,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]/"data"
m=json.loads((root/"opportunity_v6.json").read_text())
alerts=[]
for ticker,x in m.get("models",{}).items():
    if x.get("investmentAction")=="watch_price_for_due_diligence":
        alerts.append({"ticker":ticker,"severity":"review","asOf":m["generatedAt"],
            "price":x.get("price"),"quoteDate":x.get("quoteDate"),
            "illustrativeEntryPrice":x.get("entryPrice"),
            "confidence":x.get("confidence",{}).get("tier"),
            "message":"Research alert only; verify source documents, valuation, capital allocation and suitability"})
out={"schema":"qvr-alerts-v6","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
     "action":"research_only","alerts":alerts,"notificationsDelivered":False,
     "note":"No email, push or external alert service is enabled. Alerts are persisted in the app feed."}
(root/"opportunity_alerts_v6.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print("research alerts",len(alerts))
