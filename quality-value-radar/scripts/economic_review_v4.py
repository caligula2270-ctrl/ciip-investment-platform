#!/usr/bin/env python3
"""Conservative secondary analysis of SEC financial metrics."""
import json, pathlib, statistics, datetime as dt, importlib.util
P=pathlib.Path(__file__).resolve().parents[1]/"data"/"intrinsic.json"
spec=importlib.util.spec_from_file_location("base",pathlib.Path(__file__).with_name("build_intrinsic_radar.py"))
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
def company_cash(facts, history):
    sbc=base.annual_series(facts,["ShareBasedCompensation"])
    mna=base.annual_series(facts,["PaymentsToAcquireBusinessesNetOfCashAcquired","PaymentsToAcquireBusinessesGross"])
    rows=[]
    for y in history[-3:]:
        end=y["fyEnd"]
        stock=sbc.get(end,{}).get("value")
        acquisitions=mna.get(end,{}).get("value")
        cash=y["fcf"]-stock if stock is not None else None
        rows.append({"year":end,"sbc":stock,"acquisitionOutlay":acquisitions,
                     "ownerFcf":cash,"ownerFcfPerShare":cash/y["shares"] if cash is not None and y.get("shares") else None})
    valid=len(rows)==3 and all(r["ownerFcfPerShare"] is not None and r["ownerFcfPerShare"]>0 for r in rows)
    return {"status":"computed" if valid else "insufficient","observations":rows,
      "normalizedOwnerFcfPerShare":statistics.median(r["ownerFcfPerShare"] for r in rows) if valid else None,
      "acquisitionHistoryComplete":len(rows)==3 and all(r["acquisitionOutlay"] is not None for r in rows)}
def check():
    data=json.loads(P.read_text())
    reviewed=0
    directory=base.fetch_json("https://www.sec.gov/files/company_tickers.json")
    ciks={v["ticker"].upper():str(v["cik_str"]).zfill(10) for v in directory.values()}
    for ticker, row in data.get("companies",{}).items():
        row["legacyFairValue"]=row.get("fairValue")
        row["legacyMarginPct"]=row.get("marginOfSafetyPct")
        history=row.get("years",[])
        multiples=[y.get("historicalPfcf") for y in history if y.get("historicalPfcf") is not None]
        years=[y for y in history[-3:] if y.get("fcfPerShare") is not None]
        median=statistics.median(multiples) if len(multiples)>=3 else None
        cagr=row.get("revenueCagrPct")
        acquisitions=row.get("modelProFormaStatus")=="not_adjusted"
        growth=None if cagr is None else min(10,max(0,cagr))
        roic=row.get("adjustedRoic",{}).get("median3yPct")
        model=row.get("dcfBase")
        relative=row.get("valueFromHistoricalMultiple")
        divergence=abs(model-relative)/min(model,relative)*100 if model and relative else None
        blocking=[]
        try:
            cik=ciks[ticker]
            facts=base.fetch_json("https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json")["facts"]
            owner=company_cash(facts,history)
        except Exception as err:
            owner={"status":"unavailable","reason":str(err)[:150]}
        if owner.get("status")!="computed":blocking.append("Owner FCF cannot be normalized from disclosed SBC")
        if not owner.get("acquisitionHistoryComplete"):blocking.append("Acquisition cash-flow series not fully disclosed")
        if len(years)!=3:blocking.append("Historical FCF coverage insufficient")
        if median is None: blocking.append("No comparable historical P/FCF median")
        if roic is None: blocking.append("ROIC unverified")
        if acquisitions:blocking.append("Material acquisition needs pro-forma reconciliation")
        if divergence is None or divergence>65:blocking.append("DCF and historical multiple insufficiently aligned")
        blocking.append("Stock-based compensation and acquisition cash flow have not been independently reconciled")
        row["economicReview"]={"status":"requires_reconciliation","reportedFcfPerShare3y":[y.get("fcfPerShare") for y in years],
             "historicalPfcfMedian":median,"historicalRevenueCagrPct":cagr,
             "forecastGrowthCeilingPct":growth,"dcfVsMultipleDifferencePct":round(divergence,1) if divergence is not None else None,
             "roicAdjustedPct":roic,"ownerCashFlow":owner,"blocks":blocking,
             "cashFlowDefinition":"CFO minus reported capex; SBC and acquisition spending reconciliation pending"}
        row["classification"]="needs_review" if row.get("status")=="ready" else "no_model"
        row["fundamentalQualityGate"]=False
        row["fairValue"]=None
        row["marginOfSafetyPct"]=None
        reviewed+=1
    data["economicUpgrade"]={"version":"4.0-precheck","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
         "reviewed":reviewed,"status":"No automatic discounts until owner FCF and M&A are reconciled"}
    P.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("Conservative financial checks:",reviewed)
if __name__=="__main__":check()
