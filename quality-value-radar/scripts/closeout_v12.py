#!/usr/bin/env python3
"""V12 closeout: source-locked balance tie-outs, consistent equity-cash classification.
No FY2026 Q3/H1 partial balance may be presented as a verified complete EV/equity bridge.
"""
import json,datetime as dt,pathlib,math
D=pathlib.Path(__file__).resolve().parents[1]/"data"
def main():
 source=json.loads((D/"source_evidence_v12.json").read_text())
 econ=json.loads((D/"economic_v9.json").read_text())
 prior=json.loads((D/"reconciliation_v11.json").read_text())
 models={}
 for t,s in source["companies"].items():
  m=econ["models"][t];old=prior["models"][t]
  result={"company":t,"balanceDate":s["balanceDate"],"sourceUrls":[x["url"] for x in s["sources"]],
     "validatedValuation":None,"buySignal":False,"remaining":list(s.get("needs",[])),
     "previousResearchBase":m["scenarios"]["base"]["valuePerShare"],
     "status":"documentary_closed_conditional" if t in ("ADBE","INTU") else "material_claims_missing"}
  if t=="ADBE":
   result["liquidity"]={"cashPlusShortInvestmentsUSDMillions":s["cash"]+s["shortTermInvestments"],
     "financialDebtUSDMillions":s["currentDebt"]+s["longTermDebt"],
     "arithmeticNetLiquidityUSDMillions":s["cash"]+s["shortTermInvestments"]-s["currentDebt"]-s["longTermDebt"],
     "notAnAdditiveFCFEValuationBridge":True}
   result["marginReconciledPct"]=m["keyDrivers"]["ownerCashMarginObservedPct"]
   result["checks"]={"yearMatchedMargins":True,"SBCAlreadyDeducted":True,"SemrushROI":False}
  elif t=="INTU":
   result["liquidity"]={"corporateLiquidUSDMillions":s["cash"]+s["shortTermInvestments"]+s["longTermInvestments"],
     "customerFundsExcludedUSDMillions":s["custodialCustomerFunds"],
     "financialDebtUSDMillions":s["currentDebt"]+s["longTermDebt"],
     "arithmeticNetLiquidityUSDMillions":s["cash"]+s["shortTermInvestments"]+s["longTermInvestments"]-s["currentDebt"]-s["longTermDebt"],
     "leasesUSDMillions":s["operatingLeaseLiabilities"],"notAnAdditiveFCFEValuationBridge":True}
   result["capexReconciliation"]={"ppeUSDMillions":s["capexPropertyPurchases"],
      "managementBroadUSDMillions":s["managementCapexBroader"],"unreconciledDifferenceUSDMillions":s["managementCapexBroader"]-s["capexPropertyPurchases"]}
  elif t=="CPRT":
   result["preCloseLiquidAssets"]={"cashIncludesRestrictedUSDMillions":s["preCloseCashRestrictedIncluded"],
      "heldToMaturityUSDMillions":s["preCloseHeldToMaturityInvestments"],
      "sumNotEquivalentToAvailableCashUSDMillions":s["preCloseCashRestrictedIncluded"]+s["preCloseHeldToMaturityInvestments"]}
   result["transaction"]={"pricePaidControlUSDMillions":s["purchasePricePaidControl"],
      "postCloseCashAndDebt":None,"costAlreadyRemovedFromProjectedCashFlows":True,
      "historicalBalanceMustNotBeAddedToPostCloseValue":True}
  elif t=="CSU.TO":
   result["acquisitionCommitments"]={"cashConsiderationUSDMillions":s["acquisitionCommittedSinceQuarterCashAtClosing"],
      "deferredConsiderationUSDMillions":s["acquisitionCommittedDeferredConsideration"],
      "totalConsiderationUSDMillions":s["totalCommittedConsideration"],
      "acquisitionRealizedCashYield":None,
      "balanceClaimsNotDuplicated":True}
   assert abs(s["acquisitionCommittedSinceQuarterCashAtClosing"]+s["acquisitionCommittedDeferredConsideration"]-s["totalCommittedConsideration"])<.01
  elif t=="ASML":
   cash=s["cash"]+s["shortTermInvestments"]
   result["interimBalancePartial"]={"liquidAssetsEURMillions":round(cash,1),
      "verifiedLongTermDebtEURMillions":s["longTermFinancialDebt"],
      "cashMinusLongTermDebtEURMillions_NOT_NET_CASH":round(cash-s["longTermFinancialDebt"],1),
      "currentDebt":None,"leaseLiabilities":None,
      "verifiedCompleteEquityBridge":False}
   assert s["currentFinancialDebt"] is None and s["leaseLiabilitiesCurrent"] is None
  elif t=="DNP.WA":
   result["leaseInclusiveNetDebt"]={"h1FY2026PLNMillions":s["netDebtIncludingLeases"],
      "FY2025PLNMillions":s["netDebt2025IncludingLeases"],
      "changePLNMillions":round(s["netDebtIncludingLeases"]-s["netDebt2025IncludingLeases"],1),
      "leaseCashRecastAvailable":False,"cannotDeductDebtFromAfterLeaseFCFE":True}
   result["investment"]={"H1NetInvestingOutflowPLNMillions":abs(s["h1NetInvestingCashFlow"]),
      "FY2026ManagementCapexGuidanceApproxPLNMillions":s["managementFY2026CapexApprox"],
      "FY2026BottleMachinesCapexRangePLNMillions":s["managementFY2026BottleCollectionCapexRange"],
      "storeOnlyCapexNotSeparatelyVerified":True}
  models[t]=result
 out={"schema":"qvr-closeout-v12","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
      "models":models,"total":len(models),"documentaryImprovements":6,
      "investmentGradePrices":0,"signalsAllowed":False,
      "policy":"Never automatically approve a price until after-close balance, financing, and cash conversion are consistent"}
 assert len(models)==6 and all(v["validatedValuation"] is None for v in models.values())
 assert out["signalsAllowed"] is False
 (D/"closeout_v12.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
 print("V12 closeout", {t:x["status"] for t,x in models.items()})
if __name__=="__main__":main()
