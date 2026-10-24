#!/usr/bin/env python3
"""Build five-company investor due-diligence dossiers from CIIP SEC data and
a dated official-filing evidence ledger. Fail closed on source drift.

This is a structured *research audit*, NOT an independent external audit.
An older human-reviewed filing is marked superseded if SEC submissions exposes
a newer 10-K/10-Q. Manual notes are NOT automatically verified.
"""
import datetime as dt
import json
import math
import pathlib
import statistics

ROOT=pathlib.Path(__file__).resolve().parents[1]
AUDITS=ROOT/"audits"
MANIFEST=AUDITS/"evidence.json"
FACTS=ROOT/"fundamentals-auto.json"
OUTPUT=AUDITS/"latest.json"
TICKERS=["MSFT","ADBE","V","MA","TXN"]

def safe_ratio(n,d,multiplier=1):
    if not isinstance(n,(int,float)) or not isinstance(d,(int,float)) or d==0:return None
    result=multiplier*n/d
    return round(result,3) if math.isfinite(result) else None

def metrics_from_history(row):
    m=row.get("metrics",{})
    get=lambda k:(m[k].get("value") if isinstance(m.get(k),dict) else None)
    rev=get("revenue");op=get("operating_income");net=get("net_income")
    cfo=get("operating_cash_flow");cap=get("capex");sbc=get("stock_compensation")
    return {"fy_end":row.get("fy_end"),"revenue_musd":safe_ratio(rev,1e6),
        "operating_margin_pct":safe_ratio(op,rev,100),
        "net_margin_pct":safe_ratio(net,rev,100),
        "cfo_musd":safe_ratio(cfo,1e6),"capex_musd":safe_ratio(cap,1e6),
        "sbc_musd":safe_ratio(sbc,1e6),
        "reported_fcf_musd":safe_ratio(row.get("fcf_usd"),1e6),
        "capex_to_cfo_pct":safe_ratio(cap,cfo,100),
        "sbc_to_cfo_pct":safe_ratio(sbc,cfo,100)}

def review_one(ticker,evidence,company,generated_date):
    hist=company.get("history",[])
    quality=company.get("history_quality",{})
    sc=company.get("sector_control",{})
    model=company.get("sector_valuation",{})
    shares=company.get("share_reconciliation",{})
    filings=company.get("capital_filings",{})
    latest=filings.get("filings",[])
    latest_obj=latest[0] if latest else None
    reviewed_url=evidence.get("interim_source") or evidence.get("annual_source")
    current_source=latest_obj.get("document_url") if latest_obj else None
    official_source_updated=bool(current_source and
                                 current_source.rstrip("/") != reviewed_url.rstrip("/"))
    # SEC 'latest' could be an amendment 10-K/A and may supersede a reviewed 10-Q.
    date_current=latest_obj.get("filed") if latest_obj else None
    source_status=("newer_or_different_filing_needs_review" if official_source_updated
                   else "latest_filing_metadata_matches" if current_source
                   else "latest_filing_unavailable")
    problems=[]
    if official_source_updated:problems.append("Presentación SEC actual distinta de la nota examinada")
    if shares.get("status")!="provisional_reconciled":
        problems.append("Sin conciliación siquiera provisional de acciones")
    if filings.get("verified_current_fully_diluted_shares") is None:
        problems.append("Notas de capital no permiten confirmar acciones plenamente diluidas actuales")
    if not hist:problems.append("Sin histórico anual SEC")
    if sc.get("status")=="blocked":problems.append("DCF industrial bloqueado por sector")
    if quality.get("normalized_fcf_status") not in ("ready_with_caveats",):
        problems.append("CFO, CAPEX o capital circulante requieren normalización/revisión")
    if model.get("status") in ("insufficient","not_applicable"):
        problems.append("Modelo sectorial sin flujos comparables suficientes")
    if not evidence.get("evidence"):problems.append("Sin libro mayor de evidencias")
    relevant={
      "MSFT":["lease finance and datacenter replacement","full-year investment commitments","unvested stock awards and buybacks"],
      "ADBE":["contract ARR versus GAAP cash generation","SBC settlement and equity awards","Semrush acquisition and repurchases"],
      "V":["Class B conversion rights and litigation escrow","multi-class Class A equivalent economic shares","client incentives and restricted settlement cash"],
      "MA":["Class B exchangeability and EPS notes","customer settlement balances and cash conversion","incentives and equity awards"],
      "TXN":["CHIPS Act incentives receipt/conditions","gross fab CAPEX, depreciation, utilization","inventory cycle and split between GAAP and adjusted FCF"]
    }
    # FCF conservatism: two methods are retained separately and not blended.
    normalized=quality.get("normalized_fcf_3y_usd")
    aggregate_scenarios=model.get("scenarios",{}) if model.get("status") in ("review_required","aggregate_research_only") else {}
    return {
       "ticker":ticker,"company":evidence["company"],"sector":evidence["sector"],
       "scope":"source-backed investment research audit, not a statutory or financial statement audit",
       "generated_at":generated_date,
       "reviewed_as_of":evidence.get("review_as_of") or "2026-10-24",
       "latest_official_filing":latest_obj,
       "reference_filing":reviewed_url,
       "filing_status":source_status,
       "filing_date":date_current,
       "financials_five_years":[metrics_from_history(r) for r in hist[-5:]],
       "annual_account_end":evidence.get("annual"),
       "interim_account_end":evidence.get("interim"),
       "reported_period_snapshot":evidence.get("reported_snapshot",{}),
       "quality_summary":{
           "five_years":len(hist)>=5,
           "positive_fcf_years":quality.get("positive_fcf_years"),
           "normalized_fcf_musd":safe_ratio(normalized,1e6),
           "capital_intensity":quality.get("median_capex_3y_usd"),
           "revenue_cagr_pct":quality.get("revenue_cagr_pct"),
           "sector_gate":sc.get("status"),
           "normalization_status":quality.get("normalized_fcf_status"),
           "shares_reconciliation_status":shares.get("status")},
       "sector_valuation":{
           "model":model.get("model"),"status":model.get("status"),
           "normalized_cash_musd":safe_ratio(model.get("normalized_cash_usd"),1e6),
           "scenarios_aggregate":aggregate_scenarios,
           "warnings":model.get("warnings",[])},
       "share_capital":{
           "historical_diluted_shares":quality.get("latest_diluted_shares"),
           "sec_basic_latest":shares.get("latest_basic"),
           "sec_quarter_weighted_diluted":shares.get("latest_quarter_diluted"),
           "reported_share_footnote":evidence.get("equity_snapshot",{}),
           "notes_reviewed":False,
           "current_fully_diluted_verified":None,
           "value_per_share":None,
           "reason":"Current fully diluted shares cannot be certified from cover/XBRL alone; review options, RSU, convertibles, exchangeability and subsequent events"},
       "evidence_ledger":evidence.get("evidence",[]),
       "material_risks":evidence.get("key_risks",[]),
       "business_assessment":evidence.get("business_quality"),
       "manual_review_checklist":relevant.get(ticker,[]),
       "open_issues":problems,
       "signoff":{"accounting_reconciliation":False,
                  "capital_notes_reconciled":False,
                  "valuation_approved":False,
                  "trade_recommendation":None},
       "quality_stage":"RESEARCH_REVIEW_REQUIRED",
       "disclaimer":evidence.get("evidence_limit")}

def build(evidence,facts,now):
    required=set(TICKERS)
    if set(evidence["entities"]) != required:
        raise ValueError("Audit universe changed without explicit source ledger update")
    if not all(t in facts.get("companies",{}) for t in required):
        raise ValueError("Missing SEC companyfacts for mandatory five-company audit")
    generated=now.isoformat()
    records={t:review_one(t,evidence["entities"][t],facts["companies"][t],generated)
             for t in TICKERS}
    return {
      "schema":"ciip-issuer-research-audit-v1",
      "generated_at":generated,"sec_generated_at":facts.get("generated_at"),
      "source_review_as_of":evidence.get("review_as_of"),
      "methodology":"See audits/PLAYBOOK.md; investment research, not an independent or statutory audit",
      "companies":records,
      "audit_complete":False,
      "release_status":"provisional_research",
      "reason":"Manual notes and current diluted shares still require documentary reconciliation."}

def main():
    evidence=json.loads(MANIFEST.read_text(encoding="utf-8"))
    facts=json.loads(FACTS.read_text(encoding="utf-8"))
    payload=build(evidence,facts,dt.datetime.now(dt.timezone.utc))
    AUDITS.mkdir(exist_ok=True,parents=True)
    OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Audit research:",len(payload["companies"]),"companies.",
          sum(x["filing_status"]=="newer_or_different_filing_needs_review" for x in payload["companies"].values()),
          "filing source-change warnings; all five remain research-only.")
if __name__=="__main__":main()
