#!/usr/bin/env python3
"""Conservative secondary analysis of SEC financial metrics."""
import json, pathlib, statistics, datetime as dt
P=pathlib.Path(__file__).resolve().parents[1]/"data"/"intrinsic.json"
def check():
    data=json.loads(P.read_text())
    reviewed=0
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
        if len(years)!=3:blocking.append("Historical FCF coverage insufficient")
        if median is None: blocking.append("No comparable historical P/FCF median")
        if roic is None: blocking.append("ROIC unverified")
        if acquisitions:blocking.append("Material acquisition needs pro-forma reconciliation")
        if divergence is None or divergence>65:blocking.append("DCF and historical multiple insufficiently aligned")
        blocking.append("Stock-based compensation and acquisition cash flow have not been independently reconciled")
        row["economicReview"]={"status":"requires_reconciliation","reportedFcfPerShare3y":[y.get("fcfPerShare") for y in years],
             "historicalPfcfMedian":median,"historicalRevenueCagrPct":cagr,
             "forecastGrowthCeilingPct":growth,"dcfVsMultipleDifferencePct":round(divergence,1) if divergence is not None else None,
             "roicAdjustedPct":roic,"blocks":blocking,
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
