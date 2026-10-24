#!/usr/bin/env python3
"""Quality Value Radar v5: persistent evidence and quality gates.
Never mistake forecasts derived from historical margins for independent consensus.
"""
import datetime as dt
import json
import pathlib
import statistics

ROOT=pathlib.Path(__file__).resolve().parents[1]
POLICY=ROOT/"data"/"reliability_policy.json"
INTRINSIC=ROOT/"data"/"intrinsic.json"
INTERNATIONAL=ROOT/"data"/"international.json"
OUT=ROOT/"data"/"reliability_v5.json"
def median(a):
    x=[v for v in a if isinstance(v,(float,int)) and v>=0]
    return statistics.median(x) if x else None
def analyze():
    p=json.loads(POLICY.read_text())
    u=json.loads(INTRINSIC.read_text())
    intl=json.loads(INTERNATIONAL.read_text())
    now=dt.datetime.now(dt.timezone.utc)
    result={"schema":"qvr-v5-evidence","generatedAt":now.isoformat(),
        "policyVersion":p["version"],"signalsAllowed":False,
        "companies":{},"counters":{},"warnings":[]}
    for ticker,row in u["companies"].items():
        eco=row.get("economicReview",{})
        cash=eco.get("ownerCashFlow",{})
        fy=row.get("years",[])
        capex=[{"fiscalYearEnd":y["fyEnd"],"reportedCapexUSD":y["capex"],
            "maintenanceActualUSD":None,"growthActualUSD":None,
            "separationStatus":"not_disclosed",
            "maintenanceProxyMinUSD":None,"maintenanceProxyMaxUSD":None}
            for y in fy[-3:]]
        acq=[]
        for x in p["acquisitions"].get(ticker,[]):
            cost=x.get("considerationUSDMillions")
            required=x.get("capitalRequiredRatePct")
            acq.append({**x,"minimumAnnualIncrementalOwnerCashMillions":round(cost*required/100,2)
                        if cost is not None and required is not None else None,
                        "realizedReturnPct":None,"returnStatus":"pending_post_close_evidence"})
        for ob in cash.get("observations",[]):
            if ob.get("acquisitionOutlay") is not None:
                acq.append({"period":ob["year"],"reportedAcquisitionCashUSD":ob["acquisitionOutlay"],
                  "realizedReturnPct":None,"returnStatus":"unallocatable_to_cohort"})
        guidance=p["officialGuidance"].get(ticker)
        fiscal=fy[-1] if fy else {}
        historical=[]
        for y in fy[-3:]:
            if y.get("revenue") and y.get("fcf"):
                historical.append(y["fcf"]/y["revenue"])
        margin=median(historical)
        derived=None
        if guidance and margin is not None:
            derived={"kind":"model_derived_not_consensus",
                "basis":"management revenue range × median historical FCF/revenue",
                "historicalFcfMarginPct":round(margin*100,2),
                "forwardReportedFcfLowMillions":round(guidance["revenueLow"]*margin,2),
                "forwardReportedFcfHighMillions":round(guidance["revenueHigh"]*margin,2),
                "forwardOwnerFcfLowMillions":None,
                "forwardOwnerFcfHighMillions":None,
                "warning":"Not management free-cash-flow guidance. SBC and acquisitions not forecast."}
        blockers=[]
        if not guidance:blockers.append("No dated primary management revenue/FCF guidance")
        if guidance and guidance.get("forecastCashFlowProvided") is not True:
            blockers.append("Forward owner FCF not independently guided or consensus-verified")
        if any(x["separationStatus"]!="issuer_disclosed" for x in capex):
            blockers.append("Maintenance/growth CAPEX split is not disclosed and validated")
        if acq and any(x.get("returnStatus")!="verified" for x in acq):
            blockers.append("Acquisition realized ROI unverified")
        if cash.get("status")!="computed":blockers.append("Owner FCF normalized from SBC is incomplete")
        if row.get("adjustedRoic",{}).get("status")!="available":
            blockers.append("ROIC lacks complete comparable capital history")
        result["companies"][ticker]={"company":ticker,"ownerFcf":cash,
            "maintenanceGrowthCapex":capex,"acquisitionCohorts":acq,
            "forwardCashDerived":derived,"guidance":guidance,
            "forecastLabels":{"management":bool(guidance),"consensusVerified":False,
              "modelDerived":bool(derived),"marketImplied":False},
            "historicalFcfMarginPct":round(margin*100,2) if margin is not None else None,
            "investmentReadiness":"needs_evidence" if blockers else "qualifies_for_manual_review",
            "blockers":blockers,"automaticBuySignal":False}
        row["classification"]="needs_review" if row.get("status")=="ready" else "no_model"
        row["fundamentalQualityGate"]=False
        row["fairValue"]=None
        row["marginOfSafetyPct"]=None
    for ticker,x in intl.get("companies",{}).items():
        guide=p["officialGuidance"].get(ticker)
        v=x.get("valuation") or {}
        result["companies"][ticker]={"company":ticker,"guidance":guide,
         "forwardCashDerived":None,"acquisitionCohorts":p["acquisitions"].get(ticker,[]),
         "maintenanceGrowthCapex":[],"reverseDcfImpliedGrowth":v.get("marketImpliedFiveYearFcfGrowthPct"),
         "investmentReadiness":"needs_evidence","automaticBuySignal":False,
         "blockers":["International FCF requires maintenance/growth CAPEX and acquisition cohort reconciliation",
                     "Comparable independent forward FCF consensus missing"]}
    result["counters"]={"companies":len(result["companies"]),
        "withGuidance":sum(bool(x.get("guidance")) for x in result["companies"].values()),
        "verifiedAcquisitionReturns":0,"verifiedCapexSplits":0,
        "automaticBuySignals":0}
    INTRINSIC.write_text(json.dumps(u,ensure_ascii=False,indent=2)+"\n")
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    assert not result["signalsAllowed"]
    assert all(not x["automaticBuySignal"] for x in result["companies"].values())
    assert result["counters"]["companies"]>=16
    print("v5 reliability run:",result["counters"])
if __name__=="__main__":analyze()
