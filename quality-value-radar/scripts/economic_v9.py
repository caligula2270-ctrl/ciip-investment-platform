#!/usr/bin/env python3
"""v9 business-specific operating economics: separate issuer observations and model hypotheses.
Registered in the weekly SEC and international company research workflow.
No trading recommendations; values are exploratory cash-equity proxies, not audited DCF.
"""
import json, pathlib, datetime as dt, math, statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]; D=ROOT/"data"
def med(a):return statistics.median(a) if a else None
def dcf(cash,rate,multiple):
 if any(not math.isfinite(v) for v in cash+[rate,multiple]) or rate<=0 or multiple<=0:return None
 return sum(v/(1+rate)**i for i,v in enumerate(cash,1))+cash[-1]*multiple/(1+rate)**len(cash)
def record(values, cash,rate,multiple,shares,fx=1):
 enterprise=dcf(cash,rate,multiple)
 if not enterprise or shares<=0:return {"status":"insufficient"}
 return {"status":"illustrative_unreconciled_equity_proxy" if enterprise>0 else "funding_gap_negative_equity_proxy",
  "valuePerShare":round(max(0,enterprise/shares*fx),2),
  "rawDiscountedCashPerShare":round(enterprise/shares*fx,2),
  "fundingGapPerShare":round(abs(enterprise/shares*fx),2) if enterprise<0 else 0,
  "annualCashMillions":[round(v,2) for v in cash],"discountPct":rate*100,"terminalMultiple":multiple,
  "warnings":["DCF does not reconcile a fully verified net-debt bridge","Cash reinvestment and share denominator are assumptions, not issuer forecasts"]}
def main():
 inputs=json.loads((D/"economic_drivers_v9.json").read_text())
 v8=json.loads((D/"audit_v8.json").read_text())
 v6=json.loads((D/"opportunity_v6.json").read_text())
 intrinsic=json.loads((D/"intrinsic.json").read_text())
 intl=json.loads((D/"international.json").read_text())
 results={}
 for ticker,c in inputs["companies"].items():
  mode=c["archetype"];out={"ticker":ticker,"archetype":mode,"sourceUrls":c["sources"],
  "verifiedReturnOnNewCapital":False,"actualMaintenanceCapexSplit":False,
  "approval":"research_only","missingEvidence":[],"scenarios":{}}
  if ticker in ("ADBE","INTU"):
   old=intrinsic["companies"][ticker]
   annual=old["years"][-3:]
   obs={x["year"]:x for x in old["economicReview"]["ownerCashFlow"]["observations"]}
   paired=[]
   for y in annual:
    o=obs.get(y["fyEnd"])
    if not o or not y.get("revenue") or o.get("sbc") is None or o.get("ownerFcf") is None:
     raise ValueError("Financial year cash/SBC/revenue mismatch: "+ticker+" "+y["fyEnd"])
    if abs(o["ownerFcf"]-(y["fcf"]-o["sbc"]))>1:
     raise ValueError("Owner cash does not reconcile to same year FCF less SBC")
    paired.append({"fyEnd":y["fyEnd"],"revenueMillions":y["revenue"]/1e6,
      "reportedFcfMillions":y["fcf"]/1e6,"sbcMillions":o["sbc"]/1e6,
      "ownerFcfMillions":o["ownerFcf"]/1e6,
      "ownerCashToRevenuePct":round(100*o["ownerFcf"]/y["revenue"],4)})
   if len(paired)!=3:raise ValueError("Require three paired FY cash flow margins")
   observed_fcf=med([y["reportedFcfMillions"] for y in paired])
   sbc=med([y["sbcMillions"] for y in paired])
   capex=med([y["capex"] for y in annual])/1e6
   fcf_margin=med([p["ownerCashToRevenuePct"] for p in paired])/100
   g=c["latestOfficialRevenueGuidance"]
   guide_mid=(g["revenueLowMillions"]+g["revenueHighMillions"])/2
   shares=(v8["companies"][ticker]["outstandingSharesSnapshotMillions"])
   for k,a in c["scenarios"].items():
    cashflow=[];rev=guide_mid
    for year in range(5):
     if year:rev*=1+a["salesGrowthAfterGuidancePct"]/100
     conversion=max(0,fcf_margin+a["ownerCashMarginShiftPpt"]/100)
     cashflow.append(rev*conversion)
    # SBC economically deducted and future shares adjusted, not counted twice.
    per=[f/(shares*(1+a["netShareGrowthPct"]/100)**(i+1)) for i,f in enumerate(cashflow)]
    val=dcf(per,a["discountPct"]/100,a["exitOwnerFcfMultiple"])
    out["scenarios"][k]={"status":"illustrative","valuePerShare":round(val,2),
      "operatingCashMarginPct":round(conversion*100,2),"futureRevenueMillions":round(rev,1),
      "annualOwnerCashPerShare":[round(x,2) for x in per],"source":"management revenue guidance × modeled owner cash conversion"}
   out.update({"keyDrivers":{"historicalMedianFcfMillions":round(observed_fcf,1),
    "historicalMedianSbcMillions":round(sbc,1),"historicalMedianCapexMillions":round(capex,1),
    "ownerCashMarginObservedPct":round(fcf_margin*100,2),"pairedFiscalYearMargins":paired,
    "normalizedMethod":"median of three matched FY (CFO−PPE CAPEX−SBC)/revenue ratios",
    "guideRevenueMidMillions":guide_mid,
    "spotShareBaseMillions":shares},
    "missingEvidence":["Reinvestment in software/product IP and Semrush integration ROI" if ticker=="ADBE" else "Separately validated consumer vs business owner cash conversion","Spot shares lack full future treasury and dilution bridge"]})
  elif ticker=="CPRT":
   old=intrinsic["companies"]["CPRT"];cash=old["economicReview"]["ownerCashFlow"]
   base=med([x["ownerFcf"] for x in cash["observations"]])/1e6
   rev=old["years"][-1]["revenue"]/1e6
   shares=v8["companies"]["CPRT"]["outstandingSharesSnapshotMillions"]
   acquired_cost=v8["companies"]["CPRT"]["acquisition"]["closingAggregateUSDMillions"]
   capex=med([y["capex"] for y in old["years"][-3:]])/1e6
   for k,a in c["scenarios"].items():
    total=[];acv=[];organic=[]
    for year in range(1,6):
     ops=base*(1+a["organicRevenueGrowthPct"]/100)**year
     diff=capex*a["capexAnnualVs3YMedianPct"]/100
     acquired=a["acquiredOwnerFcfFirstFullYearMillions"]*(1+a["acquiredOwnerCashGrowthPct"]/100)**(year-1)
     organic.append(ops-diff);acv.append(acquired);total.append(ops-diff+acquired)
    per=[x/(shares*(1+a["netShareGrowthPct"]/100)**i) for i,x in enumerate(total,1)]
    # Deal cost is deducted ONCE on valuation date. Acquisition flows are ADDED once.
    # Cash spent at close is already absent from a POST-CLOSE cash balance. This
    # stream-only valuation assumes the deal is included in opening capital;
    # any net cash / financing bridge is handled separately in the audit.
    value=dcf(per,a["discountPct"]/100,a["exitOwnerFcfMultiple"])
    out["scenarios"][k]={"status":"illustrative_post_deal_cash_before_balance_bridge","valuePerShare":round(value,2),
       "annualOrganicCashMillions":[round(x,2) for x in organic],"annualAcquiredCashMillions":[round(x,2) for x in acv],
       "acvUpfrontPerSpotShare":round(acquired_cost/shares,2),
       "acquisitionCostDeductedFromProjectedFCF":False,
       "warning":"Opening post-close cash/debt unverified: do NOT subtract consideration again or add pre-close liquid balances"}
   out.update({"keyDrivers":{"organicOwnerCashMedianMillions":round(base,1),"reportedCapex3yMedianMillions":round(capex,1),
    "latestRevenueMillions":rev,"historicalSpotSharesMillions":shares,"acvControlConsiderationMillions":acquired_cost},
    "missingEvidence":["ACV independent post-close owner cash and proforma working capital","Proforma cash/debt and acquisition related compensation","Yard maintenance and growth investment split"]})
  elif ticker=="CSU.TO":
   v=intl["companies"][ticker]["valuation"];shares=v["sharesMillions"];fx=v["fx"]["rate"]
   base=c["fy2025"]["fcfa2sMillions"]
   for k,a in c["scenarios"].items():
    existing=base;cohorts=[];flow=[];spends=[]
    for year in range(1,6):
     existing*=1+a["organicFcfGrowthPct"]/100
     acquired=sum(spend*a["incrementalCashYieldOnPurchasePct"]/100
                  for vintage,spend in cohorts if year-vintage>=a["cohortLagYears"])
     gross=existing+acquired
     cashout=gross*a["acquisitionReinvestmentPct"]/100
     flow.append(gross-cashout);spends.append(cashout);cohorts.append((year,cashout))
    gross_terminal=existing+sum(spend*a["incrementalCashYieldOnPurchasePct"]/100 for _,spend in cohorts)
    terminal_cash=gross_terminal*(1-a["acquisitionReinvestmentPct"]/100)
    pv=sum(x/(1+a["discountPct"]/100)**i for i,x in enumerate(flow,1))+terminal_cash*a["exitCashMultiple"]/(1+a["discountPct"]/100)**5
    out["scenarios"][k]={"status":"acquisition_cohort_hypothesis","valuePerShare":round(pv/shares*fx,2),
      "annualCashAfterNewAcquisitionsMillions":[round(x,1) for x in flow],
      "newAcquisitionSpendMillions":[round(x,1) for x in spends],"modeledIncrementalCashYieldPct":a["incrementalCashYieldOnPurchasePct"]}
   out.update({"keyDrivers":{"fcfa2s2025Millions":base,"acquisitions2025Millions":c["fy2025"]["acquisitionConsiderationMillions"],
      "h1OrganicRevenueGrowthPct":c["h12026"]["organicRevenueGrowthPct"],"reportingCurrency":"USD","tradingCurrency":"CAD","fxFromIssuerDataset":fx},
      "missingEvidence":["Actual historic cohort acquisition cash yields, earnouts, organic/FX effects","Gross vs net purchase consideration and terminal acquisition obligations","Minority capital and consolidated acquisition returns"]})
  elif ticker=="ASML":
   v=intl["companies"][ticker]["valuation"];shares=v["sharesMillions"];fx=v["fx"]["rate"]
   for k,a in c["scenarios"].items():
    revenue=(c["fy2026Guidance"]["revenueLowMillions"]+c["fy2026Guidance"]["revenueHighMillions"])/2
    flows=[]
    for year in range(1,6):
     if year>1:revenue*=1+a["salesGrowthAfterFY2026Pct"]/100
     nopat=revenue*a["ebitMarginPct"]/100*(1-a["taxPct"]/100)
     # Hypothetical all-in reinvestment including net CAPEX and delta NWC; not issuer certified.
     cash=nopat-revenue*a["netReinvestmentAsPctRevenue"]/100
     flows.append(cash)
    out["scenarios"][k]=record(c,flows,a["discountPct"]/100,a["exitCashMultiple"],shares,fx)
   out.update({"keyDrivers":{"FY2026GuidanceRevenueMillions":c["fy2026Guidance"],"sharesMillions":shares,
         "reportingCurrency":"EUR","quoteCurrency":"USD","fx":fx},
     "missingEvidence":["Quarterly working capital and installed-base margins normalized over full order cycle",
                        "FCFF to equity net debt and other obligations bridge",
                        "Reinvestment depreciation/capex and expansion funding tie-out"]})
  elif ticker=="DNP.WA":
   shares=intl["companies"][ticker]["valuation"]["sharesMillions"]
   begin_stores=c["fy2025"]["storesAtEnd"];per_store=c["fy2025"]["revenueMillions"]/((begin_stores+c["fy2025"]["storesAtBeginning"])/2)
   for k,a in c["scenarios"].items():
    stores=begin_stores;rev_per=per_store;old_revenue=c["fy2025"]["revenueMillions"];cash=[]
    rows=[]
    for year in range(1,6):
     average_stores=stores+a["newStoresPerYear"]/2
     rev_per*=1+a["lflGrowthPct"]/100
     rev=average_stores*rev_per
     nopat=rev*a["ebitMarginPct"]/100*(1-a["taxPct"]/100)
     upkeep=rev*a["maintenanceCapexToRevenuePct"]/100
     openings=a["newStoresPerYear"]*a["expansionCostPerNewStoreMillions"]
     logistics=a["logisticsCapexMillions"]
     working=(rev-old_revenue)*a["workingCapitalPerIncrementalRevenuePct"]/100
     owner=nopat-upkeep-openings-logistics-working
     cash.append(owner)
     rows.append({"year":year,"endStores":stores+a["newStoresPerYear"],"revenueMillions":round(rev,1),
       "maintenanceCapexAssumedMillions":round(upkeep,1),"storeExpansionCapexAssumedMillions":round(openings,1),
       "logisticsCapexAssumedMillions":round(logistics,1),"workingCapitalReinvestmentMillions":round(working,1),
       "ownerCashMillions":round(owner,1)})
     stores+=a["newStoresPerYear"];old_revenue=rev
    out["scenarios"][k]=record(c,cash,a["discountPct"]/100,a["exitCashMultiple"],shares)
    out["scenarios"][k]["storeBuild"]=rows
   out.update({"keyDrivers":{"FY2025Stores":begin_stores,"FY2025OpenedStores":c["fy2025"]["openedStores"],
     "FY2025RevenuePerAverageStoreMillions":round(per_store,2),"splitAdjustedSharesMillions":shares},
     "missingEvidence":["Store-age cohort productivity and actual spend per store not independently reconciled",
                        "Opening cadence, costs and working capital not management guidance",
                        "Lease liabilities and debt-to-equity bridge"]})
  out["currentQuote"]=v6["models"][ticker].get("price")
  out["currentQuoteDate"]=v6["models"][ticker].get("quoteDate")
  out["legacyModelBaseValue"]=v6["models"][ticker].get("baseValue")
  out["scenarioInputs"]=c["scenarios"]
  out["comparisonOnly"]=True
  out["verifiedBuyPrice"]=None
  vals={k:x.get("valuePerShare") for k,x in out["scenarios"].items()}
  if all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals.values()):
   out["range"]={"low":min(vals.values()),"high":max(vals.values())}
  else:out["missingEvidence"].append("Scenario cashflow unavailable or nonfinite")
  results[ticker]=out
 payload={"schema":"qvr-economic-model-v9","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
     "assumptionsAsOf":inputs["asOf"],"companyCount":len(results),"models":results,
     "signalsAllowed":False,"modelNature":"What-if sector economics with issuer-anchored FY snapshots, NOT audited enterprise-to-equity DCF",
     "safeguards":["No automatic buy recommendation","Do not interchange FCFF and equity owner cash without net-debt bridge",
       "Acquisitions counted as prospective purchase funding and acquired incremental cash, never as free growth",
       "Unverified inputs remain as assumptions with open evidence gaps"]}
 assert len(results)==6 and not payload["signalsAllowed"]
 assert all(m["verifiedBuyPrice"] is None for m in results.values())
 (D/"economic_v9.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
 print("v9 economic models",len(results),{t:{k:x.get("valuePerShare") for k,x in m["scenarios"].items()} for t,m in results.items()})
if __name__=="__main__":main()
