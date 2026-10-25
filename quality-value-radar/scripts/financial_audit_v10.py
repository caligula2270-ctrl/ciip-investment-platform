#!/usr/bin/env python3
"""v10 financial audit: prevent FCFF/FCFE confusion, reconcile sourced balance claims,
Runs in the recurring CIIP quality valuation pipeline, with permanent scenario-blocks.
maintenance-capex proxy and scenario re-investment. This is NOT certified target price.
"""
import json,math,datetime as dt,pathlib,statistics
D=pathlib.Path(__file__).resolve().parents[1]/"data"
def num(x):return isinstance(x,(int,float)) and math.isfinite(x)
def main():
    src=json.loads((D/"financial_bridge_sources_v10.json").read_text())
    econ=json.loads((D/"economic_v9.json").read_text())
    drv=json.loads((D/"economic_drivers_v9.json").read_text())
    out={"schema":"qvr-financial-bridge-v10","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
      "signalsAllowed":False,"verifiedEquityTargets":0,"models":{}}
    for ticker,c in src["companies"].items():
        old=econ["models"][ticker];model=drv["companies"][ticker]
        item={"ticker":ticker,"basis":c["basis"],"balanceAsOf":c["fiscalEnd"],
          "sourceUrl":c["sourceUrl"],"dataConfidence":"filing_snapshot_with_open_items",
          "unresolvedItems":list(c["fiscalSnapshotOutdatedReasons"]),
          "purchaseReady":False,"approvedTarget":None,"scenarioBridge":{},
          "reinvestmentCheck":{},"sourceObservations":c.get("factRefs",[])}
        if c["basis"]=="fcff":
            if ticker=="ASML":
                cash=c["cashMillions"]+c["shortInvestmentsMillions"]
                debt=c["currentDebtMillions"]+c["longDebtMillions"]
                leases=c["leasesMillions"]
                bridge_no_lease=cash-debt
                bridge_with_lease=bridge_no_lease-leases
                item["balanceBridge"]={"cashAndLiquidInvestmentsEURMillions":cash,
                  "financialDebtEURMillions":debt,"leaseLiabilitiesEURMillions":leases,
                  "equityAdjustmentExcludingLeasesEURMillions":round(bridge_no_lease,2),
                  "equityAdjustmentIncludingLeasesEURMillions":round(bridge_with_lease,2),
                  "leasePolicy":"unresolved; show both alternatives; do not approve either",
                  "nonOperatingInvestmentValue":None}
                shares=old["keyDrivers"]["sharesMillions"]
                fx=old["keyDrivers"]["fx"]
                for scen,v in old["scenarios"].items():
                    ev=v["rawDiscountedCashPerShare"]
                    ex=round(ev+bridge_no_lease/shares*fx,2)
                    inc=round(ev+bridge_with_lease/shares*fx,2)
                    item["scenarioBridge"][scen]={"operatingEnterpriseValuePerShare":ev,
                         "equityProxyExcludingLeasesPerShare":ex,
                         "equityProxyIncludingLeasesPerShare":inc,
                         "approvedEquityTarget":None,"status":"illustrative_mismatched_filing_dates"}
                    a=model["scenarios"][scen]
                    item["reinvestmentCheck"][scen]={"reportedOrAssumed":"model_assumption",
                         "allInReinvestmentPercentRevenue":a["netReinvestmentAsPctRevenue"],
                         "ebitMarginPct":a["ebitMarginPct"],
                         "taxPct":a["taxPct"],
                         "workingCapitalCycleNormalized":False}
                item["unresolvedItems"].append("Financing bridge is FY2025 while DCF uses FY2026 onward: roll-forward required")
            else:
                nd=c["reportedNetDebtMillions"]
                shares=old["keyDrivers"]["splitAdjustedSharesMillions"]
                for scen,v in old["scenarios"].items():
                    enterprise=v.get("rawDiscountedCashPerShare")
                    item["scenarioBridge"][scen]={"operatingEnterpriseProxyPerShare":enterprise,
                      "leaseInclusiveNetDebtPerShare":round(nd/shares,4),
                      "equityProxyNaivePerShare":round(enterprise-nd/shares,2),
                      "approvedEquityTarget":None,"status":"unapproved_lease_inconsistency"}
                    a=model["scenarios"][scen]
                    perStore=a["expansionCostPerNewStoreMillions"]
                    openings=a["newStoresPerYear"]
                    item["reinvestmentCheck"][scen]={"annualOpeningsAssumed":openings,
                       "assumedCapexPerNewStorePLNMillions":perStore,
                       "annualStoreExpansionCapexPLNMillions":round(perStore*openings,2),
                       "additionalLogisticsCapexPLNMillions":a["logisticsCapexMillions"],
                       "maintenanceCapexPctSalesHypothesis":a["maintenanceCapexToRevenuePct"],
                       "FY2025TotalCapexPLNMillions":c["fy2025CapexMillions"],
                       "totalCapexPerNewStoreUpperBoundMillions":round(c["fy2025CapexMillions"]/c["fy2025OpenedStores"],3),
                       "historicalDepreciationProxyPLNMillions":c["fy2025DepreciationProxyMillions"],
                       "note":"CAPEX / opened stores is an aggregate arithmetic UPPER-BOUND proxy, not per-store cost; D&A not necessarily maintenance"}
                item["unresolvedItems"].append("Finance leases already in issuer reported net debt: naive subtraction risks duplicate deduction")
        elif ticker=="CSU.TO":
            r=c["reconciliationFY2025"]
            # Note: signed line item basis must be checked against issuer definition
            item["cashDefinition"]={"metric":"FCFA2S","valueUSDMillions":r["fcfa2s"],
             "alreadyInterestDebtAndLeaseAdjusted":True,"alreadyNoncontrollingAdjusted":True,
             "leaseOrDebtReDeductionForbidden":True,
             "manualCashFlowSourceTieoutRequired":True,
             "reportedComponents":r}
            for scen,a in model["scenarios"].items():
                item["reinvestmentCheck"][scen]={"retentionForFutureAcquisitionsPct":a["acquisitionReinvestmentPct"],
                   "assumedIncrementalAcquisitionCashYieldPct":a["incrementalCashYieldOnPurchasePct"],
                   "incrementalRealizedYieldCertified":False,
                   "operatingGrossFCFA2SAlreadyAfterDebtService":True}
                item["scenarioBridge"][scen]={"FCFEProxyPerShare":old["scenarios"][scen]["valuePerShare"],
                   "approvedEquityTarget":None,"status":"acquisition_cohort_yields_unvalidated"}
        else:
            item["cashDefinition"]={"metric":"CFO - CAPEX - SBC","basis":"FCFE-like owner cash proxy",
              "netDebtSubtractedAgain":False,"needsSbcShareCountReconciliation":True}
            for scen,v in old["scenarios"].items():
                item["scenarioBridge"][scen]={"FCFEProxyPerShare":v["valuePerShare"],
                    "approvedEquityTarget":None,"status":"cash_and_operating_assets_not_reconciled"}
                if ticker=="CPRT":
                    item["reinvestmentCheck"][scen]={"postAcquisitionBalanceAvailable":False,
                      "acquiredIncrementalOwnerCashUSDMillionsFirstYearAssumed":
                           model["scenarios"][scen]["acquiredOwnerFcfFirstFullYearMillions"],
                      "reportedRealizedAcquisitionROI":None,"leaseAndWorkingCapitalReconciled":False}
                else:
                    item["reinvestmentCheck"][scen]={"forecastOwnerCashMarginShiftPpt":
                        model["scenarios"][scen]["ownerCashMarginShiftPpt"],
                        "sbcAndBuybackCostsDoubleCountRisk":True,"CAPEXMaintenanceSplitVerified":False}
            item["unresolvedItems"].append("FCFE-like metric requires excess cash/enterprise assets and funding of buybacks/acquisitions tie-out")
        out["models"][ticker]=item
    assert set(out["models"])==set(econ["models"])
    assert all(all(x["approvedEquityTarget"] is None for x in e["scenarioBridge"].values()) for e in out["models"].values())
    (D/"financial_audit_v10.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("V10 financial bridges",len(out["models"]),"validated target prices",out["verifiedEquityTargets"])
if __name__=="__main__":main()
