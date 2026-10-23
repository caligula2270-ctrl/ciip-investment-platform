#!/usr/bin/env python3
"""QVR v2: quarterly SEC 10-Q trailing twelve months and refined ROIC.

Requires existing build_intrinsic_radar.py to have produced intrinsic.json.
Does not overstate missing metrics. No third party requirements.
"""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
import math
import pathlib
import statistics
import sys
import time
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("qvr_build",pathlib.Path(__file__).with_name("build_intrinsic_radar.py"))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
TODAY=dt.datetime.now(dt.timezone.utc).date()
P=ROOT/"data"/"intrinsic.json"
TAX={"tax":["IncomeTaxExpenseBenefit"],"pretax":["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
"IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
"goodwill":["Goodwill"],"intangibles":["FiniteLivedIntangibleAssetsNet","IntangibleAssetsNetExcludingGoodwill"],
"lease":["OperatingLeaseLiabilityNoncurrent"],"currentlease":["OperatingLeaseLiabilityCurrent"]}
FLOW={"revenue","cfo","capex","ebit","net_income","tax","pretax"}
def fact_series(facts,key):
    tags=b.TAGS[key] if key in b.TAGS else TAX[key]
    unit=b.UNITS.get(key,"USD")
    return b.annual_series(facts,tags,unit,key not in FLOW and key!="diluted_shares")
def current_quarter_ytd(facts,key):
    tags=b.TAGS[key] if key in b.TAGS else TAX[key]
    units=b.UNITS.get(key,"USD")
    candidates=[]
    for rank,tag in enumerate(tags):
        for x in facts.get("us-gaap",{}).get(tag,{}).get("units",{}).get(units,[]):
            try:
                if x["form"] not in ("10-Q","10-Q/A"):continue
                filed=dt.date.fromisoformat(x["filed"])
                end=dt.date.fromisoformat(x["end"])
                start=dt.date.fromisoformat(x["start"])
                length=(end-start).days
                if filed>TODAY or end>TODAY or (TODAY-end).days>500 or not 75<=length<=320:continue
                if not math.isfinite(float(x["val"])):continue
                # 10-Q YTD may be 3, 6, or 9 months. Never combine the
                # 3 month standalone report with YTD.
                candidates.append({"value":float(x["val"]),"end":end,"start":start,
                    "filed":filed,"tag":tag,"rank":rank,"days":length,"accession":x.get("accn")})
            except (ValueError,TypeError,KeyError,OverflowError):continue
    # Prefer latest filing for same period; avoid mixing duplicate XBRL labels.
    candidates.sort(key=lambda v:(v["end"],v["days"],v["filed"],-v["rank"]),reverse=True)
    # For a given end, prefer longest valid YTD, then more recent filing.
    return candidates
def latest_ytd(facts, key, fy_end):
    fy=dt.date.fromisoformat(fy_end)
    choices=[x for x in current_quarter_ytd(facts,key) if x["end"]>fy
             and (x["start"]-fy).days in range(-12,15)]
    return choices[0] if choices else None
def comparative_ytd(facts, key, newer, year_ago):
    q=[x for x in current_quarter_ytd(facts,key)
       if abs((x["end"]-year_ago).days)<=12 and abs(x["days"]-newer["days"])<=12]
    return min(q,key=lambda x:(abs((x["end"]-year_ago).days),-x["filed"].toordinal())) if q else None
def ttm(facts,latest_fy):
    fy=dt.date.fromisoformat(latest_fy)
    first=latest_ytd(facts,"cfo",latest_fy)
    if not first:return {"status":"not_available","reason":"No hay 10-Q posterior al último 10-K para CFO"}
    # Prevent 53-week and uneven quarter mismatch
    earlier=dt.date(first["end"].year-1,first["end"].month,min(first["end"].day,28))
    values={}
    for key in ("revenue","cfo","capex","ebit","net_income"):
        now=[x for x in current_quarter_ytd(facts,key)
             if abs((x["end"]-first["end"]).days)<=8 and abs((x["start"]-first["start"]).days)<=8]
        prior=comparative_ytd(facts,key,first,earlier)
        annual=fact_series(facts,key).get(latest_fy)
        if annual and now and prior:
            values[key]=round(annual["value"]+now[0]["value"]-prior["value"],2)
    obj={"status":"available" if all(k in values for k in ("revenue","cfo","capex")) else "partial",
        "periodEnd":first["end"].isoformat(),"filedAt":first["filed"].isoformat(),
        "fiscalYearEnd":latest_fy,
        "method":"FY + YTD actual - YTD comparable (SEC 10-K/10-Q; filing dates verified)",
        "values":values,
        "sourceUrl":b.SOURCE_SEC,
        "tags":"Comparar CFO y CAPEX como flujos acumulados de exactamente el mismo periodo; ausencia = sin TTM"}
    if obj["status"]=="available":
        obj["fcf"]=round(values["cfo"]-values["capex"],2)
    return obj
def instant_value(facts, tagkey, year_end):
    series=fact_series(facts,tagkey)
    return b.asof_value(series,year_end,max_days=9)
# Cash and unused credit facilities: Copart 10-K 2024/2025/2026.
# Explicit allow-list only; absent generic XBRL borrowing tags never imply zero debt.
COPART_NO_REVOLVER_DATES = {"2023-07-31","2024-07-31","2025-07-31","2026-07-31"}
COPART_DEBT_SOURCES = [
 "https://www.sec.gov/Archives/edgar/data/900075/000090007524000024/cprt-20240731.htm",
 "https://www.sec.gov/Archives/edgar/data/900075/000162828025042946/cprt-20250731.htm",
 "https://www.sec.gov/Archives/edgar/data/900075/000119312526405731/cprt-20260731.htm"]
def balance(facts,end,revenues,ticker=""):
    equity=instant_value(facts,"equity",end)
    cash=instant_value(facts,"cash",end)
    debt_l=instant_value(facts,"debt_long",end)
    debt_c=instant_value(facts,"debt_current",end)
    # Copart reports no revolving facility borrowing for specifically documented fiscal years;
    # operating lease liabilities remain included separately. This is not a generic rule.
    inferred_zero=(ticker=="CPRT" and end in COPART_NO_REVOLVER_DATES
                   and debt_l is None and debt_c is None)
    if equity is None or cash is None:return None
    debt=(debt_l or 0)+(debt_c or 0)
    lease_l=instant_value(facts,"lease",end)
    lease_c=instant_value(facts,"currentlease",end)
    lease=(lease_l or 0)+(lease_c or 0)
    # 2% revenue left as operational cash when excess cash excluded.
    if revenues is None or revenues<=0:return None
    op_cash=min(cash,.02*revenues)
    excess_cash=max(0,cash-op_cash)
    invested=equity+debt+lease-excess_cash
    goodwill=instant_value(facts,"goodwill",end)
    intangibles=instant_value(facts,"intangibles",end)
    return {"end":end,"equity":equity,"cash":cash,"debt":debt,"leases":lease,
            "leasesDisclosed":lease_l is not None or lease_c is not None,
            "debtTagsDisclosed":debt_l is not None or debt_c is not None or inferred_zero,
            "debtZeroFromNotes":inferred_zero,
            "goodwill":goodwill,"intangibles":intangibles,"excessCash":excess_cash,
            "investedCapital":invested}
def adjusted_roic(facts,fy_end,ticker=""):
    annual={k:fact_series(facts,k) for k in ("revenue","ebit","tax","pretax")}
    ends=sorted(annual["ebit"])
    rows=[]
    for i in range(1,len(ends)):
        end=ends[i];previous=ends[i-1]
        if (dt.date.fromisoformat(end)-dt.date.fromisoformat(previous)).days>410:continue
        ebit=annual["ebit"][end]["value"]
        tax=annual["tax"].get(end,{}).get("value")
        pretax=annual["pretax"].get(end,{}).get("value")
        real_rate=tax/pretax if pretax and pretax>0 and tax is not None else None
        tax_rate=real_rate if real_rate is not None and .08<=real_rate<=.4 else .25
        if ebit<=0:continue
        revnow=annual["revenue"].get(end,{}).get("value")
        revprev=annual["revenue"].get(previous,{}).get("value")
        bn=balance(facts,end,revnow,ticker)
        bp=balance(facts,previous,revprev,ticker)
        if not bn or not bp:continue
        inv=(bn["investedCapital"]+bp["investedCapital"])/2
        if inv<=0:continue
        adj=100*ebit*(1-tax_rate)/inv
        if not -100<adj<200:continue
        # The key calculation includes acquired goodwill. The ex-goodwill
        # sensitivity is NOT used as a qualification gate.
        alt=None
        if bn["goodwill"] is not None and bp["goodwill"] is not None:
            inv_ex=inv-(bn["goodwill"]+bp["goodwill"])/2
            if inv_ex>0:alt=100*ebit*(1-tax_rate)/inv_ex
        rows.append({"fyEnd":end,"roicAdjustedPct":round(adj,2),"roicExGoodwillPct":round(alt,2) if alt is not None and -100<alt<250 else None,
             "nopat":round(ebit*(1-tax_rate),2),"averageInvestedCapital":round(inv,2),
             "effectiveTaxPct":round(tax_rate*100,2),"taxRateMethod":"reported" if tax_rate==real_rate else "fallback_25pct",
             "leaseIncluded":bn["leasesDisclosed"] and bp["leasesDisclosed"],
             "partialDebtTags":not (bn["debtTagsDisclosed"] and bp["debtTagsDisclosed"]),
             "debtZeroFromNotes":bool(bn.get("debtZeroFromNotes") or bp.get("debtZeroFromNotes"))})
    rows=rows[-5:]
    usable=[y["roicAdjustedPct"] for y in rows[-3:] if not y["partialDebtTags"]]
    med=round(statistics.median(usable),2) if len(usable)>=3 else None
    return {"status":"available" if med is not None else "insufficient",
            "median3yPct":med,"years":rows,
            "definition":"NOPAT EBIT×(1−tasa fiscal efectiva) / media de capital invertido apertura/cierre",
            "capitalDefinition":"Patrimonio + deuda financiera + arrendamientos revelados − caja excedentaria (caja operativa = 2% ventas)",
            "roicExGoodwill":"Solo sensibilidad; no usado en el filtro",
            "caveats":["SBC, adquisiciones y leasing pueden distorsionar el ratio",
                        "Tasa efectiva 8%-40% y fallback 25% cuando no hay tasa interpretable",
                        "No usar con entidades financieras; revisar estados contables para decisiones de compra"]}
def run():
    j=json.loads(P.read_text(encoding="utf-8"))
    if j.get("schema")!="qvr-auto-v1":raise SystemExit("Wrong upstream schema")
    if "@" not in b.AGENT:raise SystemExit("SEC_USER_AGENT required")
    mp=b.fetch_json("https://www.sec.gov/files/company_tickers.json")
    by_ticker={str(v["ticker"]).upper():str(v["cik_str"]).zfill(10) for v in mp.values()}
    updated=0
    for ticker,row in j.get("companies",{}).items():
        if row["status"] not in ("ready","insufficient","incomplete"):continue
        cik=by_ticker.get(ticker)
        if not cik:continue
        try:
            facts=b.fetch_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json").get("facts",{})
            fy=row.get("fiscalEnd")
            if not fy:continue
            t=ttm(facts,fy)
            r=adjusted_roic(facts,fy,ticker)
            row["recentFinancials"]=t
            row["adjustedRoic"]=r
            if ticker=="CPRT":
                row["debtReviewSources"]=COPART_DEBT_SOURCES
                row["debtZeroPolicy"]="Borrowings zero only for named filing years; lease liabilities and excess cash treated separately"
                # Subsequent purchase of ACV Auctions (Oct 2026) must be re-evaluated;
                # historical return is not a pro-forma balance sheet for acquisition.
                row.setdefault("warnings",[]).append("ROIC histórico no incorpora plenamente la adquisición posterior de ACV Auctions en octubre de 2026")
            # The old approximation is NOT an acceptable automated gate.
            row["roicProxyMedianPct"]=None
            good_r=r["status"]=="available" and r["median3yPct"]>=15
            gate=good_r and row.get("fcfPositiveYears",0)>=4 and (row.get("netDebtToFcf") is None or row["netDebtToFcf"]<=4)
            row["fundamentalQualityGate"]=bool(gate)
            qualifies=(row.get("status")=="ready" and gate and (row.get("historicalPfcfSamples") or 0)>=3
                and (row.get("marginOfSafetyPct") or -999)>=25 and row.get("quote")
                and (TODAY-dt.date.fromisoformat(row["quote"]["date"])).days<=7)
            row["classification"]="possible_discount" if qualifies else ("needs_review" if row["status"]=="ready" else "no_model")
            if t["status"]=="available":
                row.setdefault("warnings",[]).append("FCF TTM calculado; precio objetivo anterior aún basado en mediana anual. Revisar si difieren")
            updated+=1
        except Exception as exc:
            row["classification"]="needs_review" if row.get("status")=="ready" else "no_model"
            row["fundamentalQualityGate"]=False
            row.setdefault("warnings",[]).append("ROIC/TTM no validado: "+str(exc)[:125])
        time.sleep(.15)
    j["enhancement"]={"version":"2.0","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
        "period":"Anual SEC + último 10-Q compatible",
        "roic":"NOPAT / capital invertido medio con tasa efectiva y arrendamientos si reportados",
        "enriched":updated}
    P.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Trimestrales y ROIC reestimados para",updated,"empresas")
if __name__=="__main__":run()
