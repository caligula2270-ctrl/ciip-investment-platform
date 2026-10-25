#!/usr/bin/env python3
"""QVR production snapshot: one conservative source of truth for public UI.

This is a read-only investing research product. It does not place trades.
An indicative DCF is NEVER promoted to a verified equity value.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=DATA/"production_status.json"
TODAY=dt.datetime.now(dt.timezone.utc)
FOCUS=("ADBE","INTU","CPRT","CSU.TO","ASML","DNP.WA")
CURRENCY={"ADBE":"USD","INTU":"USD","CPRT":"USD","CSU.TO":"CAD","ASML":"USD","DNP.WA":"PLN"}
LABEL={"ADBE":"Adobe","INTU":"Intuit","CPRT":"Copart","CSU.TO":"Constellation Software","ASML":"ASML","DNP.WA":"Dino Polska"}

def read(name, expected):
    obj=json.loads((DATA/name).read_text(encoding="utf-8"))
    if obj.get("schema")!=expected:
        raise RuntimeError(f"Missing or invalid source {name}: expected schema {expected}")
    return obj

def as_date(x):
    if not x:return None
    try:return dt.date.fromisoformat(str(x)[:10])
    except (ValueError,TypeError):return None

def day_age(x):
    d=as_date(x)
    return (TODAY.date()-d).days if d else None

def fmt_status(age,limit):
    if age is None or age<0:return "missing_or_future"
    return "current" if age<=limit else "stale"

def clean_numeric(x):
    return x if isinstance(x,(int,float)) and math.isfinite(x) and x>0 else None

def run():
    quote=read("quotes.json", None) # quotes uses no schema; explicit structural validation below
    if not isinstance(quote.get("quotes"),dict):
        raise RuntimeError("Quotes feed must have quotes map")
    # Recognized schemas for every value displayed in the production UI
    intrinsic=read("intrinsic.json","qvr-auto-v1")
    international=read("international.json","qvr-international-v1")
    econ=read("economic_v9.json","qvr-economic-model-v9")
    closeout=read("closeout_v12.json","qvr-closeout-v12")
    audit=read("evidence_audit_v13.json","qvr-evidence-audit-v13")
    trials=read("backtest_v6.json","qvr-pit-backtest-v6")
    policy=read("reliability_policy.json","qvr-reliability-policy-v5")
    companies={}
    price_ok=0
    for ticker in FOCUS:
        m=econ["models"][ticker]
        e=audit["models"][ticker]
        c=closeout["models"][ticker]
        q=quote["quotes"].get(ticker,{})
        v=m["scenarios"]
        unit=CURRENCY[ticker]
        quote_price=clean_numeric(q.get("price")) if q.get("currency")==unit else None
        quote_age=day_age(q.get("date"))
        qstatus=fmt_status(quote_age,7) if quote_price is not None else "wrong_currency_or_missing"
        if qstatus=="current":price_ok+=1
        scenarios={}
        for key in ("bear","base","bull"):
            x=v.get(key,{})
            scenarios[key]=clean_numeric(x.get("valuePerShare"))
            # A negative discounted FCFF never maps to a negative tradable price;
            # the funding-gap status is retained elsewhere in source data.
            if ticker=="DNP.WA" and x.get("status")=="funding_gap_negative_equity_proxy":
                scenarios[key]=0
        monotonic=all(isinstance(scenarios.get(k),(int,float)) for k in ("bear","base","bull"))
        if monotonic and not scenarios["bear"]<=scenarios["base"]<=scenarios["bull"]:
            raise RuntimeError(f"Non-monotonic scenario cashflows for {ticker}")
        open_items=list(dict.fromkeys(c.get("remaining",[])+e.get("missingSourceItems",[])))
        limited=ticker in ("CPRT","CSU.TO","ASML","DNP.WA")
        # Audit thresholds ONLY for US FCFE-style companies that have a
        # three-year historical, same-year cash/revenue reconciliation.
        threshold=None
        if ticker in ("ADBE","INTU") and monotonic and qstatus=="current":
            a=scenarios["bear"];b=scenarios["base"]
            if a>0 and b>0:threshold=round(min(.75*b,.90*a),2)
        review=(threshold is not None and quote_price is not None and quote_price<=threshold)
        as_of=c.get("balanceDate") or c.get("inputAsOf")
        source_age=day_age(as_of)
        companies[ticker]={
            "ticker":ticker,"name":LABEL[ticker],"currency":unit,
            "price":quote_price,"priceDate":q.get("date") if quote_price else None,
            "priceSource":q.get("sourceUrl") if quote_price else None,
            "quoteAgeDays":quote_age,"quoteStatus":qstatus,
            "balanceDate":as_of,"balanceAgeDays":source_age,
            "scenariosIllustrative":scenarios,
            "scenarioBasis":"operator cash model, non-audited equity price" if ticker not in ("ASML","DNP.WA") else "unbridged enterprise cash valuation; not equity fair value",
            "indicativeResearchThreshold":threshold,
            "watchForResearch":bool(review),
            "valuationStatus":"incomplete_claims" if limited else "conditional_research",
            "investmentGradeValue":None,"buyApproved":False,
            "openEvidenceCount":len(open_items),"openEvidence":open_items,
            "sourceUrls":e.get("sources",[]),
            "historicalBacktestStatus":trials["tickers"].get(ticker,{}).get("status","not_covered"),
            "quoteCanDriveAlerts":qstatus=="current",
        }
        if companies[ticker]["investmentGradeValue"] is not None:
            raise AssertionError("Production cannot approve a value with unverified equity bridge")
    all_quotes=quote["quotes"]
    good_prices=sum(1 for ticker,q in all_quotes.items()
        if clean_numeric(q.get("price")) and fmt_status(day_age(q.get("date")),7)=="current")
    report_age=day_age(quote.get("generatedAt"))
    status="operational" if good_prices>=35 and price_ok==len(FOCUS) else "degraded"
    result={
      "schema":"qvr-production-v1",
      "generatedAt":TODAY.isoformat(),"state":status,
      "message":"Radar de investigación operativo; ningún precio de compra está certificado.",
      "lastQuoteFeedGeneratedAt":quote.get("generatedAt"),"quoteFeedAgeDays":report_age,
      "automation":{"quotes":"scheduled GitHub market job", "fundamentals":"weekly Wednesday 09:15 UTC",
                     "alerts":"on-screen research only; no push/email/SMS","orderExecution":False},
      "coverage":{"universe":len(all_quotes),
                  "quotesCurrent7d":good_prices,
                  "USSECModelAttempted":len(intrinsic.get("companies",{})),
                  "internationalDCF":len(international.get("companies",{})),
                  "economicModels":len(companies),
                  "investmentGradePriceCount":0,
                  "researchWatchCount":sum(x["watchForResearch"] for x in companies.values())},
      "companies":companies,"focus":list(FOCUS),
      "systemAlerts":(
          [{"severity":"warning","message":"Algunas cotizaciones están desactualizadas o faltan; los avisos afectados se suspenden."}]
          if status=="degraded" else []),
      "provenance":{"inputs":["quotes.json","intrinsic.json","international.json",
                            "economic_v9.json","closeout_v12.json","evidence_audit_v13.json",
                            "backtest_v6.json","reliability_policy.json"],
                    "missingItemsNotZero":True},
      "disclaimer":"Precio de revisión NO es precio certificado ni recomendación; exige auditoría de deuda/caja, dilución, fuentes y riesgo.",
    }
    if len(result["companies"])!=6:raise AssertionError("Expected six research models")
    if any(x["buyApproved"] or x["investmentGradeValue"] is not None for x in companies.values()):
        raise AssertionError("Unverified valuation promoted to actionable")
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("QVR production",result["state"],result["coverage"])

if __name__=="__main__":run()
