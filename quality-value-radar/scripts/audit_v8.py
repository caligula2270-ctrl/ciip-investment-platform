#!/usr/bin/env python3
"""QVR v8: SEC-linked share-base reconciliations and acquisition sensitivity.\nThis file is included in the scheduled research process.
No investment-ready targets; actual maintenance capex and ROI remain unverified.
"""
import datetime as dt
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
def main():
    ledger=json.loads((DATA/"source_ledger_v8.json").read_text())
    fundamental=json.loads((DATA/"intrinsic.json").read_text())
    sensit=json.loads((DATA/"sensitivity_v7.json").read_text())
    models={}
    for ticker,item in ledger["companies"].items():
        old=fundamental["companies"].get(ticker,{})
        history=old.get("years") or []
        share=history[-1].get("shares") if history else None
        reported=item["dilutedWeightedAverageSharesMillions"]*1e6
        delta=100*(share/reported-1) if share and reported else None
        spot=item.get("sharesOutstandingSnapshotMillions")
        avg=item["dilutedWeightedAverageSharesMillions"]
        signal="pass" if delta is not None and abs(delta)<1 else "review"
        base=sensit["models"].get(ticker,{})
        capex=base.get("capex",{}).get("reportedCapexStress",[])
        dil=base.get("netShares",{}).get("cases",[])
        matrix=[]
        # Combined stress is multiplicative on cash flow per share.
        # Not an independent benefit/cost estimate: SBC was already deducted.
        if capex and dil:
            for c in capex:
                for d in dil:
                    v=c["valuePerShare"]
                    dilution_ref=next((z["valuePerShare"] for z in dil if z["annualNetDilutedShareChangePct"]==0),None)
                    combined=round(v*d["valuePerShare"]/dilution_ref,2) if v is not None and dilution_ref else None
                    matrix.append({"totalCapexChangePct":c["changeInTotalCapexPct"],
                       "annualNetShareChangePct":d["annualNetDilutedShareChangePct"],
                       "indicativeValuePerShare":combined})
        models[ticker]={
          "status":"reconciliation_incomplete","sourceUrl":item["filingUrl"],
          "lastFY":item["fiscalYearEnd"],"annualWeightedDilutedSharesMillions":round(share/1e6,4) if share else None,
          "ledgerWeightedDilutedSharesMillions":avg,
          "ledgerTieOutDifferencePct":round(delta,4) if delta is not None else None,
          "ledgerTieOut":signal,"outstandingSharesSnapshotMillions":spot,
          "outstandingSnapshotDate":item["sharesOutstandingSnapshotDate"],
          "spotMinusWeightedAveragePct":round((spot/avg-1)*100,2),
          "spotIsNotWeightedDiluted":True,
          "repurchasedSharesMillions":item["repurchasedSharesFYMillions"],
          "repurchaseCashUSDMillions":item["repurchaseCashFYMillions"],
          "averageRepurchasePriceUSD":round(item["repurchaseCashFYMillions"]/item["repurchasedSharesFYMillions"],2),
          "capexSplit":"not_issuer_certified","acquisitionRealizedROIC":None,
          "jointStressMatrix":matrix,"stressIsNotInvestmentValuation":True,
          "warnings":[item["caveat"],"SBC was economically deducted from FCF; net share change may include SBC issuance and repurchases",
          "Average repurchase price excludes settlement timing and withholding complexities; not necessarily fill price"]}
    transaction=ledger["transactions"]["ACV"]
    cop=models["CPRT"]
    current_base=fundamental["companies"]["CPRT"]["years"][-1]["shares"]
    actual=transaction["aggregateConsiderationPaidForControlUSDMillions"]
    announced=transaction["announcedEquityValueUSDMillionsApprox"]
    cop["acquisition"]={
      "name":"ACV Auctions","announcedUSDMillionsApprox":announced,
      "closingAggregateUSDMillions":actual,"deltaAgainstAnnouncementUSDMillions":round(actual-announced,3),
      "closingCashCostPerHistoricalShareUSD":round(actual*1e6/current_base,4),
      "annualCashHurdle12PctUSDMillions":round(actual*.12,3),
      "cashReturnVerified":False,"totalInvestedCapitalReconciled":False,
      "sourceUrl":transaction["sourceUrl"],
      "note":"Announced 1.9bn and 8-K closing amount are not interchangeable. Full transaction EV, fees, debt and synergies not reconciled.",
      "capitalDeploymentScenarios":[{
         "incrementalCashUSDMillions":cash,
         "returnOnClosingConsiderationPct":round(cash/actual*100,2),
         "cashReturnRealized":False} for cash in (0,100,150,216.12252972,228,300,400)]
    }
    out={"schema":"qvr-v8-audit","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
         "signalsAllowed":False,"sourceLedgerDate":ledger["dataAsOf"],"companies":models,
         "verifiedBuyPrices":0,"verifiedAcquisitionReturns":0,"verifiedMaintenanceCapexSplits":0,
         "limitations":["Spot shares do not equal diluted annual weighted averages",
          "Joint stress is ceteris paribus, not predictive; growth/CAPEX covariance unknown",
          "No pro-forma ACV balance sheet or independently verified acquisition ROI",
          "No maintenance CAPEX allocation certified by issuer"]}
    assert all(m["ledgerTieOut"]=="pass" for m in models.values()),"Do not publish inconsistent share denominators"
    assert all(m["spotIsNotWeightedDiluted"] and m["capexSplit"]=="not_issuer_certified" for m in models.values())
    assert not out["signalsAllowed"]
    (DATA/"audit_v8.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("v8 share base: ",{t:m["ledgerTieOut"] for t,m in models.items()}, "copart cash hurdle:",cop["acquisition"]["annualCashHurdle12PctUSDMillions"])
if __name__=="__main__":main()
