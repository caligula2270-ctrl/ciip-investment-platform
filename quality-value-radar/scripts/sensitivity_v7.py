#!/usr/bin/env python3
"""QVR v7 sensitivity tests: CAPEX, share count, and acquisition capital.
Output is a CETERIS-PARIBUS stress test, never an investment-ready target.
Exhaustive non-live data dependency: v6, SEC XBRL-derived files, issuer filing notes.
"""
import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"sensitivity_v7.json"
FOCUS=("ADBE","INTU","CPRT","CSU.TO","ASML","DNP.WA")
TODAY=dt.datetime.now(dt.timezone.utc)

def med(values):
    arr=[float(x) for x in values if isinstance(x,(float,int)) and math.isfinite(x)]
    return median(arr) if arr else None

def pv_equity(owner_ps, g, discount, exit_multiple, years=5, dilution=0):
    """Forecast growing aggregate owner cash, divided by projected net shares.
    Base owner FCF already deducts SBC; dilution is an ADDITIONAL net-share stress,
    not automatically an independent loss. Uses year-indexed fractional shares.
    """
    if owner_ps is None or owner_ps<=0 or discount<=0 or exit_multiple<=0 or dilution<=-.99:
        return None
    values=[owner_ps*((1+g)/(1+dilution))**t for t in range(1,years+1)]
    terminal=values[-1]*exit_multiple
    return round(sum(f/(1+discount)**t for t,f in enumerate(values,1))
                 +terminal/(1+discount)**years,2)

def format_rows(cases):
    return [{"label":name,"valuePerShare":round(v,2) if v is not None else None}
            for name,v in cases]

def sensitivity_one(ticker, model, source, intl, evidence, policy):
    is_us=ticker in ("ADBE","INTU","CPRT")
    cur=model.get("currency") or ""
    baseline=model.get("baseValue")
    norm=model.get("normalizedOwnerFcfPerShare")
    base_scenario=(model.get("scenarios") or {}).get("base") or {}
    p={
      "ticker":ticker,"currency":cur,"sourcePrice":model.get("price"),
      "quoteDate":model.get("quoteDate"),"asOf":TODAY.date().isoformat(),
      "baselineIndicativeValue":baseline,"baselineLevel":model.get("valuationLevel","unverified"),
      "verifiedMaintenanceGrowthSplit":False,"verifiedAcquisitionReturn":False,
      "assumptions":[],"capex":{},"netShares":{},"acquisitions":{},
      "priceSignal":"no_automatic_buy","warnings":[]}
    if is_us:
        annual=source.get("years") or []
        recent=annual[-3:]
        capex_ps=med([y["capex"]*y["fcfPerShare"]/y["fcf"]
                      for y in recent if y.get("fcf") and y.get("fcfPerShare")
                      and y.get("capex") is not None])
        growth=(base_scenario.get("growthPct") or model.get("growthAssumptionPct") or 0)/100
        rate=(base_scenario.get("discountPct") or 11.5)/100
        mult=base_scenario.get("exitMultiple") or 22
        # Annual CAPEX +/- stress, constant growth. This is ONLY a numerical
        # sensitivity and does not establish the real maintenance fraction.
        if norm and capex_ps is not None and baseline:
            capex_stress=[]
            for shift in (-.25,0,.25,.50):
                owner=norm-shift*capex_ps
                v=pv_equity(owner,growth,rate,mult) if owner>0 else None
                capex_stress.append({"changeInTotalCapexPct":round(shift*100),
                    "ownerFcfPerShare":round(owner,4),
                    "valuePerShare":v,"differenceFromBasePct":round(100*(v/baseline-1),1) if v else None})
            p["capex"]={
              "status":"stress_only_unverified_split",
              "medianReportedCapexPerShare":round(capex_ps,4),
              "medianReportedCapexToOwnerFcfPct":round(100*capex_ps/norm,2),
              "reportedCapexStress":capex_stress,"sourceFyEnds":[y.get("fyEnd") for y in recent],
              "maintenancePct":None,"growthPct":None,
              "note":"Total reported CAPEX varied independently while all growth assumptions remain FIXED. This is not evidence of maintenance CAPEX."}
            # Illustrative 'defer growth CAPEX' counterfactual: less investment
            # paired with impaired growth; shows why addbacks are not free FCF.
            counterfactual=[]
            for retained,growth_retained in ((.4,.4),(.7,.75),(1.0,1.0)):
                cash=norm+(1-retained)*capex_ps
                counterfactual.append({"illustrativeCapexRetainedPct":int(retained*100),
                  "assumedGrowthRetainedPct":round(growth_retained*100),
                  "valuePerShare":pv_equity(cash,growth*growth_retained,rate,mult),
                  "label":"Counterfactual, not reported company maintenance/growth split"})
            p["capex"]["deferredGrowthTradeoff"]=counterfactual
        else:p["capex"]={"status":"insufficient","reason":"Missing historical CAPEX/owner FCF denominator"}
        if norm and mult and baseline:
            tested=[]
            for net_dilution in (-.01,0,.01,.025,.04):
                adjusted=pv_equity(norm,growth,rate,mult,dilution=net_dilution)
                tested.append({"annualNetDilutedShareChangePct":round(net_dilution*100,1),
                    "valuePerShare":adjusted,
                    "deltaPct":round(100*(adjusted/baseline-1),1) if adjusted else None})
            current=recent[-1].get("shares") if recent else None
            prev=recent[-2].get("shares") if len(recent)>=2 else None
            observed=round((current/prev-1)*100,2) if current and prev else None
            p["netShares"]={"status":"sensitivity_not_projection",
                "latestWeightedAvgDilutedShares":current,
                "priorWeightedAvgDilutedShares":prev,
                "lastYearChangePct":observed,
                "cases":tested,
                "stockCompAlreadyDeductedFromOwnerCash":True,
                "note":"Net diluted-share change includes issuance and buybacks. SBC expense is already deducted in owner FCF: positive net issuance can overlap the economic SBC charge, so these are stresses not cumulative verified effects."}
            if ticker=="CPRT":
                p["netShares"]["assumedAcquiredPlanShareRegistration"]={
                    "maximumRegisteredShares":4_500_000,
                    "incrementalToFYWeightedDilutedPct":round(4_500_000/current*100,3) if current else None,
                    "status":"registered_not_necessarily_issued",
                    "sourceUrl":"https://www.sec.gov/Archives/edgar/data/900075/000119312526426897/d123686ds8.htm"}
        else:p["netShares"]={"status":"insufficient"}
        if ticker=="CPRT":
            items=policy.get("acquisitions",{}).get("CPRT",[])
            event=next((a for a in items if a.get("target")=="ACV Auctions"),None)
            price_m=event.get("considerationUSDMillions") if event else None
            current_shares=recent[-1].get("shares") if recent else None
            if price_m and current_shares:
                # Acquisition ROI: incremental target owner cash NOT reported.
                # Show NPV of DEPLOYMENT only, not incremented current equity fair
                # value. This avoids double-counting purchase-price financing.
                cases=[]
                for fcf_m in (0,100,150,228,300,400):
                    fcf_per_share=fcf_m*1e6/current_shares
                    pv_before_cost=pv_equity(fcf_per_share,.02,.12,12) if fcf_m else 0
                    cost_ps=price_m*1e6/current_shares
                    npv_per_share=round(pv_before_cost-cost_ps,2)
                    cases.append({"incrementalOwnerCashAnnualUSDMillions":fcf_m,
                        "yearOneCashReturnOnEquityConsiderationPct":round(fcf_m/price_m*100,2),
                        "acquisitionNPVPerShare":npv_per_share,
                        "investmentValueBeforeConsiderationPerShare":pv_before_cost,
                        "yearOneCashReturnObserved":False})
                p["acquisitions"]={"status":"transaction_return_unverified",
                    "event":"ACV October 2026","announcedConsiderationUSDMillions":price_m,
                    "considerationType":"announced equity consideration; total economic invested capital not yet reconciled",
                    "FY2026HistoricalDilutedShares":current_shares,
                    "capitalOutlayPerShare":round(price_m*1e6/current_shares,3),
                    "minimumCashAnnualAt12PctUSDMillions":round(price_m*.12,1),
                    "scenarios":cases,"incrementalCashGrowthAssumptionPct":2,
                    "terminalMultipleForAcquiredCash":12,
                    "discountPct":12,
                    "integrationAndFinancingCosts":"not included",
                    "sourceUrl":event.get("sourceUrl"),
                    "notAddedToStandaloneFairValue":True,
                    "note":"NPV = PV incremental cash AND exit − cash consideration. It is NOT a consolidated post-deal price target; FY2026 balance is pre-deal."}
            else:p["acquisitions"]={"status":"insufficient"}
        else:
            observations=(source.get("economicReview") or {}).get("ownerCashFlow",{}).get("observations") or []
            recentobs=observations[-3:]
            p["acquisitions"]={"status":"cohort_returns_unverified",
                "cashConsiderationDisclosedByYear":[{"fyEnd":x.get("year"),
                    "cashOutflowUSD":x.get("acquisitionOutlay")} for x in recentobs],
                "demonstratedIncrementalCashOrNOPAT":None,"realizedROI":None,
                "note":"Acquisition cash spending is NOT a proof of return. No cohort-level incremental ROIC, synergies or integration bridge is available."}
    else:
        v=(intl.get("valuation") or {})
        p["capex"]={"status":"insufficient_issuer_split",
            "reason":"The imported historical FCF series does not have a filing-verified maintenance vs growth CAPEX reconciliation."}
        p["netShares"]={"status":"illustrative_only",
            "note":"Future net dilution ranges are hypothetical; foreign FX and non-GAAP flow definition not fully reconciled."}
        if v.get("status")=="preliminary" and v.get("base") and v.get("normalizedFcfPerShare"):
            p["netShares"]["valueCases"]=[{
                "fiveYearNetShareCagrPct":d,
                "approximateDCFBase":round(v["base"]/((1+d/100)**5),2),
                "method":"Approximation applying 5Y share denominator to entire DCF, NOT a recomputed cash stream"}
                for d in (-1,0,1,2.5)]
        if ticker=="CSU.TO" and v.get("base"):
            p["acquisitions"]={"status":"acquisitions_core_to_business_no_cohort_ROI",
                "fcfa2sBasis":"before investment in acquired businesses",
                "nonAdditiveCashSpendSensitivity":[
                    {"futureAcquisitionBudgetAsPctPreAcquisitionFcf":spend,
                     "staticCashDistributionValuePerShare":round(v["base"]*(1-spend/100),2),
                     "growthHeldFixed":True,"notValuation":True} for spend in (0,15,30,50,75)],
                "note":"Simply deducting future acquisition spend without modeling purchased cash flows is NOT an intrinsic value. These tests expose how sensitive naive FCFA2S valuations are."}
        else:
            p["acquisitions"]={"status":"no_incremental_acquisition_return_verified",
                "note":"No disclosed acquired-cohort NOPAT / total invested capital, so acquired return sensitivity cannot be investment-grade."}
    p["decision"]={
        "reliableBuyPrice":None,"buyDecision":"unavailable",
        "reason":"Sensitivity is exploratory; maintenance CAPEX and acquisition returns remain unverified."}
    return p

def main():
    base=json.loads((ROOT/"data"/"opportunity_v6.json").read_text())
    fundamental=json.loads((ROOT/"data"/"intrinsic.json").read_text())
    intl=json.loads((ROOT/"data"/"international.json").read_text())
    evidence=json.loads((ROOT/"data"/"reliability_v5.json").read_text())
    policy=json.loads((ROOT/"data"/"reliability_policy.json").read_text())
    models={}
    for ticker in FOCUS:
        m=base.get("models",{}).get(ticker,{})
        src=fundamental.get("companies",{}).get(ticker,{})
        international=intl.get("companies",{}).get(ticker,{})
        models[ticker]=sensitivity_one(ticker,m,src,international,evidence,policy)
    payload={"schema":"qvr-sensitivity-v7","generatedAt":TODAY.isoformat(),
      "sourceVersion":base.get("schema"),"automaticBuyDecisions":False,
      "allValuesIllustrative":True,"models":models,
      "majorWarning":"A business reinvestment reduction without revised growth is a ceteris-paribus stress, not a valid fundamental value.",
      "coverage":{"capexStressUS":sum(x["capex"].get("status")=="stress_only_unverified_split" for x in models.values()),
            "dilutionStressUS":sum(bool(x["netShares"].get("cases")) for x in models.values()),
            "fullyAuditedAcquisitionReturns":0,
            "verifiedMaintenanceCapexSplits":0}}
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print("Sensitivity v7:",payload["coverage"])
    assert not payload["automaticBuyDecisions"]
    assert all(x["decision"]["reliableBuyPrice"] is None for x in models.values())

if __name__=="__main__":main()
