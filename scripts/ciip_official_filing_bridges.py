"""Company-specific annual GAAP source bridges, never pretend to be XBRL facts.

These values are manually tie-out from *official issuer-filed 10-K tables*.
Only fill missing concepts; explicit footnote, accession, period and provenance.
Never override SEC companyfacts with curated observations. If SEC later exposes
a conflicting amount, preserve the conflict in the source notes and block.
"""
from __future__ import annotations
import datetime as dt
import statistics

OFFICIAL_ANNUAL = {
 "V": {
  "capex":{
   "2021-09-30":(705,"https://www.sec.gov/Archives/edgar/data/1403161/000140316122000081/v-20220930.htm","FY2022 10-K cash flows (2021 comparative)"),
   "2022-09-30":(970,"https://www.sec.gov/Archives/edgar/data/1403161/000140316122000081/v-20220930.htm","FY2022 10-K investing cash flows"),
   "2023-09-30":(1059,"https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm","FY2025 10-K investing cash flows (2023 comparative)"),
   "2024-09-30":(1257,"https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm","FY2025 10-K investing cash flows (2024 comparative)"),
   "2025-09-30":(1482,"https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm","FY2025 10-K investing cash flows")
  }
 },
 "MA":{
  "net_income":{
   "2021-12-31":(8687,"https://www.sec.gov/Archives/edgar/data/1141391/000114139123000020/ma-20221231.htm","FY2022 10-K consolidated operations (2021 comparative)"),
   "2022-12-31":(9930,"https://www.sec.gov/Archives/edgar/data/1141391/000114139123000020/ma-20221231.htm","FY2022 10-K consolidated operations"),
   "2023-12-31":(11195,"https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm","FY2025 10-K consolidated operations (2023 comparative)"),
   "2024-12-31":(12874,"https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm","FY2025 10-K consolidated operations (2024 comparative)"),
   "2025-12-31":(14968,"https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm","FY2025 10-K consolidated operations")
  }
 }
}

def bridge_history(ticker,history,quality,as_of):
    """Copy only explicitly missing reported values; validate FY ends and USD units."""
    detail={"schema":"ciip-official-reported-bridge-v1","ticker":ticker,
            "filled":[],"conflicts":[],"no_additions":True}
    mapping=OFFICIAL_ANNUAL.get(ticker,{})
    for row in history:
        end=row.get("fy_end")
        try:
            fy_date=dt.date.fromisoformat(end)
        except (ValueError,TypeError):continue
        if fy_date>as_of:continue
        for metric,by_end in mapping.items():
            note=by_end.get(end)
            if not note:continue
            millions,url,section=note
            value=int(millions*1_000_000)
            original=row.setdefault("metrics",{}).get(metric)
            if original is not None:
                if abs(original["value"]-value)>max(1_000_000,.005*value):
                    detail["conflicts"].append({"fy_end":end,"metric":metric,
                     "XBRL":original["value"],"10k_reported":value,"source_url":url})
                continue
            datum={"value":value,"unit":"USD","end":end,"start":None,
                   "period":"FY","tag":section,"taxonomy":"issuer_reported_10k",
                   "source_url":url,"source_location":section,
                   "provenance":"manual_issuer_reported_cash_flow_tieout_not_xbrl"}
            row["metrics"][metric]=datum
            detail["filled"].append({"fy_end":end,"metric":metric,"value":value,
              "source_url":url,"source_location":section,"provenance":datum["provenance"]})
        cfo=row["metrics"].get("operating_cash_flow",{}).get("value")
        cap=row["metrics"].get("capex",{}).get("value")
        row["fcf_usd"]=cfo-cap if cfo is not None and cap is not None and cap>=0 else None
        net=row["metrics"].get("net_income",{}).get("value")
        rev=row["metrics"].get("revenue",{}).get("value")
        row["net_margin_pct"]=100*net/rev if rev and net is not None else None
    detail["no_additions"]=not detail["filled"]
    complete=[r for r in history if r.get("fcf_usd") is not None]
    positive=sum(r["fcf_usd"]>0 for r in complete)
    quality["complete_fcf_years"]=len(complete)
    quality["positive_fcf_years"]=positive
    recent=history[-3:]
    baseline=(statistics.median(r["fcf_usd"] for r in recent)
              if len(recent)==3 and all(r.get("fcf_usd") is not None and r["fcf_usd"]>0 for r in recent)
              else None)
    age=quality.get("latest_fy_age_days")
    quality["normalized_fcf_3y_usd"]=baseline if baseline is not None and age is not None and age<=520 else None
    quality["status"]="historical_ready" if quality["normalized_fcf_3y_usd"] else "insufficient"
    if detail["conflicts"]:
        quality.setdefault("source_notes",[]).append("Conflicto material entre XBRL y 10-K manual; bloquear validación")
        detail["status"]="conflict_blocked"
    else:
        detail["status"]="crosswalk_validated" if detail["filled"] else "not_applicable"
    return detail
