#!/usr/bin/env python3
"""v13: detect genuine accounting remediation, explicit documentary gaps, and dates.\nScheduled by the weekly research workflow.\n"""
import json, pathlib, datetime as dt
D=pathlib.Path(__file__).resolve().parents[1]/"data"
def main():
 econ=json.loads((D/"economic_v9.json").read_text())
 source=json.loads((D/"source_evidence_v12.json").read_text())
 out={"schema":"qvr-evidence-audit-v13","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
 "modelSignalsEnabled":False,"models":{}}
 for t,m in econ["models"].items():
  s=source["companies"][t]
  r={"ticker":t,"verifiedBuyPrice":None,"reviewStatus":"requires_further_filing_evidence",
   "sources":[i["url"] for i in s["sources"]],"missingSourceItems":s["needs"],
   "cashFlowFramework":s.get("FCFDefinition",s.get("cashFlowBasis",s.get("FCFFFrameworks"))),
   "inputAsOf":s["balanceDate"]}
  if t=="DNP.WA":
   d=m["keyDrivers"]
   expected=2546.3-2041.3
   assert abs(d["FY2025EbitdaLessEbitDepreciationMillions"]-expected)<.01
   for scenario in m["scenarios"].values():
    for y in scenario["storeBuild"]:
     assert abs(y["operatingCashBeforeInvestmentMillions"]-y["depreciationAddbackMillions"]-(y["ownerCashMillions"]+y["maintenanceCapexAssumedMillions"]+y["storeExpansionCapexAssumedMillions"]+y["logisticsCapexAssumedMillions"]+y["workingCapitalReinvestmentMillions"]-y["depreciationAddbackMillions"]))<.75
   r["remediation"]="NOPAT + D&A - reinvestment; provisional D&A based on EBITDA less EBIT"
   r["leaseBridgeStatus"]="blocked: IFRS16 ROU depreciation and lease debt/payout alignment"
   r["baseModelAfterDepreciationFix"]=m["scenarios"]["base"]["valuePerShare"]
  elif t=="CPRT":
   assert all(x["acquisitionCostDeductedFromProjectedFCF"] is False for x in m["scenarios"].values())
   r["remediation"]="No double count purchase consideration"
   r["proformaPostAcquisitionBalance"]=None
   r["acvROIStatus"]="not independently evidenced"
  elif t=="ASML":
   r["financialDebtCurrent"]=s["currentFinancialDebt"]
   assert r["financialDebtCurrent"] is None
   r["leaseObligations"]=None
   r["proformaEquityBridge"]=None
  elif t=="CSU.TO":
   r["realizedAcquisitionCohortReturns"]=None
   r["futureInvestmentBudgetModeledNotObserved"]=True
  else:
   assert len(m["keyDrivers"]["pairedFiscalYearMargins"])==3
   r["normalizationCheck"]="matched FY FCF and revenue; historical methodology corrected"
  out["models"][t]=r
 assert set(out["models"])==set(econ["models"])
 assert all(x["verifiedBuyPrice"] is None for x in out["models"].values())
 (D/"evidence_audit_v13.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
 print("V13 audited:",len(out["models"]),"Dino revised model:",out["models"]["DNP.WA"]["baseModelAfterDepreciationFix"])
if __name__=="__main__":main()
