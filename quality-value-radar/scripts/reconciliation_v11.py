#!/usr/bin/env python3
"""V11 strict financial corrections: matched FY cash ratios, no ACV double count, lease gates."""
import json,datetime as dt,pathlib,math
D=pathlib.Path(__file__).resolve().parents[1]/"data"
def run():
 e=json.loads((D/"economic_v9.json").read_text())
 f=json.loads((D/"financial_audit_v10.json").read_text())
 s=json.loads((D/"financial_bridge_sources_v10.json").read_text())
 results={}
 for t,m in e["models"].items():
  old=f["models"][t]
  checks={}
  unresolved=[]
  if t in ("ADBE","INTU"):
   p=m["keyDrivers"].get("pairedFiscalYearMargins",[])
   assert len(p)==3 and len({x["fyEnd"] for x in p})==3
   for x in p:
    expected=(x["reportedFcfMillions"]-x["sbcMillions"])/x["revenueMillions"]*100
    assert abs(expected-x["ownerCashToRevenuePct"])<.001
   checks={"cashMarginPolicy":"median of matched FY owner cash divided by same-year revenue",
           "matchedFy":[x["fyEnd"] for x in p],
           "medianOwnerCashMarginPct":m["keyDrivers"]["ownerCashMarginObservedPct"]}
   if t=="INTU":checks["capexFY2026"]=s["companies"][t]["capexDefinitions"]
   unresolved+=["Current-period balance and buybacks/stock-plan funding bridge incomplete",
                 "Forward SBC/diluted-share double-count control remains assumption"]
  if t=="CPRT":
   for v in m["scenarios"].values():
    assert v["acquisitionCostDeductedFromProjectedFCF"] is False
   checks={"acquisitionCostRemovedFromDCFStream":True,
      "postCloseBalanceSheetAvailable":False,
      "costMustBeReflectedInPostCloseLiquidityExactlyOnce":True}
   unresolved+=["Post-close liquidity, debt, assumed obligations and operating target cash unreported",
                "ACV post-close incremental FCF not available for return verification"]
  if t=="ASML":
   br=old["balanceBridge"]
   checks={"twoHistoricLeaseAlternativesCalculated":True,
       "balanceAsOf":old["balanceAsOf"],
       "leaseDeductedOnlyInExplicitAlternative":True,
       "nonOperatingInvestments":None,
       "updated2026Q3Bridge":None}
   unresolved+=["2026 Q3 equity bridge not reconciled item-by-item","FY2025 balance cannot be contemporaneous equity bridge"]
  if t=="DNP.WA":
   checks={"leaseAccountingPolicy":s["companies"][t]["leasePolicy"],
        "reportedIssuerNetDebtIncludesLeases":True,
        "approvedLeaseConsistentBridge":None}
   unresolved+=["Recast lease cash flows to match leasing liability treatment",
                 "FY2026 H1 financial net debt and growth capex not tied out"]
  if t=="CSU.TO":
   checks={"fcfa2sAlreadyAfterDebtService":True,
     "noDuplicateLeaseDebtDeduction":True}
   unresolved+=["No verified realized return on purchased cohorts"]
  results[t]={"status":"partially_corrected" if t in ("ADBE","INTU","CPRT") else "blocked_until_filing_reconciliation",
     "checks":checks,"outstanding":unresolved,
     "illustrativeBase":m["scenarios"]["base"]["valuePerShare"],
     "approvedTarget":None,"sourceURLs":m["sourceUrls"]}
 out={"schema":"qvr-reconciliation-v11","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
     "models":results,"verifiedPrices":0,"automatedBuySignals":False,
     "rule":"Correct numbers and accounting treatment, but never treat an absent audited document as resolved"}
 assert len(results)==6 and all(x["approvedTarget"] is None for x in results.values())
 (D/"reconciliation_v11.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
 print("V11 reconciliations", {k:v["status"] for k,v in results.items()})
if __name__=="__main__":run()
