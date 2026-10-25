#!/usr/bin/env python3
"""Five-issuer CIIP model audit: source tie-out, math and assumptions."""
import datetime as dt, json, pathlib, math
from build_ciip_per_share import dcf, net_owner_cash
from ciip_official_filing_bridges import OFFICIAL_ANNUAL
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
 "inputs":"audits/per_share_inputs.json",
 "notes":"audits/validation_evidence.json",
 "sec":"fundamentals-auto.json",
 "audits":"audits/latest.json",
 "models":"audits/per_share_latest.json"
}
FIVE=("ADBE","MSFT","V","MA","TXN")
ORIGINAL_P0_CONTROLS={
 "ADBE":[("ADBE-MA","Adobe acquisition separate strategic reinvestment bridge")],
 "MSFT":[("MSFT-CASH","Microsoft FY2026 CFO less CAPEX SBC and lease principal owner-cash bridge")],
 "V":[("V-CAPEX","Visa 5Y issuer-filed CAPEX reconciled to source separate from SEC taxonomy"),
      ("V-SHARES","Visa June Class A diluted EPS denominator less September documented B conversion reduction")],
 "MA":[("MA-EARNINGS","Mastercard 5Y reported GAAP net income cash-to-earnings source bridge")],
 "TXN":[("TXN-CYCLE","TI LTM 2026 GAAP CFO-CAPEX less through-cycle analyst reserve")]
}

def load():
 return {k:json.loads((ROOT/path).read_text(encoding="utf-8")) for k,path in SOURCES.items()}
def issue(t,severity,kind,detail,impact,fix,source=None):
 return dict(ticker=t,severity=severity,kind=kind,detail=detail,
             impact=impact,required_fix=fix,source=source)
def passed(a,b,tol=.006):
 return a is not None and b is not None and abs(a-b)<=max(abs(b),1)*tol
def audit_ticker(t,c,notes,sec,record,model):
 findings=[];checks=[]
 def flag(level,kind,detail,impact,fix,source=None):
  findings.append(issue(t,level,kind,detail,impact,fix,source))
 den=c["denominator"];scenarios=c["scenarios"]
 primary=notes["primary"]
 shares_ok=0<den["low_m"]<=den["central_m"]<=den["high_m"]
 checks.append({"name":"Shares bound correctly","pass":shares_ok})
 if not shares_ok:flag("P0","Formula/control defect","Invalid denominator range",
                         "Values per share unreliable","Reconcile share classes and awards",primary)
 for case,assumptions in scenarios.items():
  v=dcf(net_owner_cash(assumptions),assumptions["g1_pct"]/100,
        assumptions["g2_pct"]/100,assumptions["ke_pct"]/100,
        assumptions["t_pct"]/100)["equity_value_musd"]/den["central_m"]
  pub=model["scenario_values"][case]["equity_per_share_usd"]
  ok=abs(v-pub)<.025
  checks.append({"name":"DCF arithmetic "+case,"pass":ok,"computed":round(v,4),"published":pub})
  if not ok:flag("P0","Formula/control defect","DCF does not reproduce "+case,
                 "Scenario amount inaccurate","Regenerate model and examine discount math")
  weight=model["scenario_values"][case]["terminal_weight_pct"]
  if weight>=65:
   flag("P1","Unsupported assumption",case+" terminal weight "+str(weight)+"%",
        "High sensitivity to long-run economics","Stress terminal spread and exit economics")
 latest=sec["history"][-1]
 cfo=latest["metrics"].get("operating_cash_flow",{}).get("value")
 capex=latest["metrics"].get("capex",{}).get("value")
 cfo_m=cfo/1e6 if cfo is not None else None
 capex_m=capex/1e6 if capex is not None else None
 if record["filing_status"]!="latest_filing_metadata_matches":
  flag("P0","Missing forecast refresh","SEC filing changed since manual notes",
       "Capital or operating base may be stale","Refresh original 10-Q/10-K notes",primary)
 flag("P1","Not comparable without bridge",
      "Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution",
      "Forward share count can depart from observed EPS weighted average",
      "Reconcile outstanding classes, options, RSUs, convertibles and subsequent events",primary)
 if t=="ADBE":
  vals=notes["observations"]
  fy=vals["annual_fy2025_m"];nine=vals["cashflow_9m_2026_m"]
  ok=passed(cfo_m,fy["cfo"]) and passed(capex_m,fy["capex"])
  checks.append({"name":"Adobe FY2025 CFO and CAPEX tie-out","pass":ok})
  if not ok:flag("P0","Source contradiction","Adobe FY annual CFO or CAPEX does not tie",
                 "Historical owner cash unreliable","Reconcile filing table and SEC companyfacts",primary)
  reserve=scenarios["base"].get("annual_acquisition_reinvestment_m")
  acq_source=c["cash_anchor"].get("acquisition_source")
  reinvest_policy=c["cash_anchor"].get("acquisition_reinvestment_policy")
  acquisition_control=bool(nine.get("acquisitions_net",0)>0 and acq_source==primary
      and reinvest_policy and isinstance(reserve,(int,float)) and 0<reserve<scenarios["base"]["owner_cf1_m"]
      and model["scenario_values"]["base"].get("owner_cash_after_recurring_reinvestment_m")==scenarios["base"]["owner_cf1_m"]-reserve)
  checks.append({"name":"Adobe acquisition separate strategic reinvestment bridge","pass":acquisition_control,
    "historical_acquisition_cash_m":nine["acquisitions_net"],"forward_analyst_reserve_m":reserve})
  if not acquisition_control:
   flag("P0","Unsupported assumption",
        "Adobe historical acquired-business investment excluded without a future reinvestment policy",
        "M&A-driven growth may overstate owner cash","Document source and a distinct forecast reinvestment policy",primary)
  else:
   flag("P1","Unsupported assumption",
        "Adobe recurring future M&A reserve "+str(reserve)+"m is an analyst stress, not proved recurring",
        "Revenue growth and acquisition cadence must be connected",
        "Build explicit business acquisition dependence scenarios and reconcile organic growth",primary)
  anchor=fy["cfo"]-fy["capex"]-fy["sbc"]
  base=scenarios["base"]["owner_cf1_m"]
  checks.append({"name":"Adobe source CFO-CAPEX-SBC bridge","pass":passed(anchor,7910),
                 "owner_cash_m":anchor,"base_assumed_m":base})
  flag("P1","Unsupported assumption",
       "Adobe base cash "+str(base)+"m vs FY2025 CFO-CAPEX-SBC "+str(anchor)+"m",
       "Forecast SBC, AI economics and M&A not connected to operating schedules",
       "Forecast revenue/margins/SBC/acquisition reinvestment separately",primary)
  pending=vals.get("pending_topaz_acquisition_m",{})
  if pending.get("expected_cash"):
   flag("P1","Not comparable without bridge",
        "Adobe has a pending "+str(pending["expected_cash"])+"m Topaz Labs acquisition, separate from spent 9M Semrush",
        "Cash timing and incremental earnings are contingent on closing",
        "Scenario-model closing quarter, payment, acquisition contribution and effect on recurring reserve",pending.get("source",primary))
 elif t=="MSFT":
  a=notes["observations"]["fy2026_m"]
  ok=passed(cfo_m,a["cfo"]) and passed(capex_m,a["capex"])
  checks.append({"name":"Microsoft reported FY2026 CFO CAPEX","pass":ok})
  owner=a["cfo"]-a["capex"]-a["sbc"]
  lease_principal=a["finance_lease_principal_cash"]
  owner_after_lease=owner-lease_principal
  base=scenarios["base"]["owner_cf1_m"]
  lease_ok=(c["cash_anchor"].get("finance_lease_principal_2026_m")==lease_principal
    and passed(base,owner_after_lease,.001))
  checks.append({"name":"Microsoft FY2026 CFO less CAPEX SBC and lease principal owner-cash bridge",
    "pass":lease_ok,"source_cash_m":owner_after_lease,"base_owner_cash_m":base})
  if not lease_ok:
   flag("P0","Unsupported assumption",
      "Microsoft base cash does not tie to reported cash less CAPEX, SBC and finance leases",
      "Excess cash inflates value before forecasting",
      "Use documented FY2026 full reinvestment bridge",primary)
  else:
   flag("P1","Unsupported assumption",
      "Microsoft first-stage 13% growth applied to a lease-adjusted $51.481bn base is not justified by a five-year datacenter segment forecast",
      "Uncertain server replacement economics and growth spending",
      "Build asset replacement, cloud margin and AI return-on-capital forecasts",primary)
  flag("P1","Not comparable without bridge",
       "New finance-lease datacenter assets and future server renewal not captured as current cash CAPEX",
       "Long-run owner cash still uncertain","Model lease principal beyond FY2026 and noncash server investment commitments",primary)
 elif t=="V":
  official=sec.get("official_filing_bridge",{})
  reported_capex=notes["observations"]["fy2025_m"]["capex"]
  five_years=sec.get("history",[])
  by_end=OFFICIAL_ANNUAL["V"]["capex"]
  all_five=all(v.get("metrics",{}).get("capex",{}).get("value") is not None
    and v["fy_end"] in by_end
    and passed(v["metrics"]["capex"]["value"]/1e6,by_end[v["fy_end"]][0],.001)
    and (v["metrics"]["capex"].get("taxonomy")=="us-gaap" and v["metrics"]["capex"].get("accession")
       or v["metrics"]["capex"].get("taxonomy")=="issuer_reported_10k" and v["metrics"]["capex"].get("source_url"))
    for v in five_years)
  capex_ok=bool(len(five_years)==5 and all_five
    and official.get("status") in ("crosswalk_validated","not_applicable")
    and not official.get("conflicts") and passed(capex_m,reported_capex,.001))
  checks.append({"name":"Visa 5Y issuer-filed CAPEX reconciled to source separate from SEC taxonomy",
    "pass":capex_ok,"five_years":all_five,"FY2025_capex_m":capex_m,
    "bridge_status":official.get("status"),"filled_count":len(official.get("filled",[])),
    "conflicts":official.get("conflicts"),"filled":official.get("filled")})
  if not capex_ok:
   flag("P0","Not comparable without bridge",
        "Visa FY2021–2025 reported investments not reconciled across original 10-K cash flow tables",
        "Normalized FCF remains unreliable","Validate 10-K capex crosswalk and all five annual periods",primary)
  sep=den.get("sept_Bdrop_total_m")
  bchanges=[den.get(x) for x in ("september_B1_drop_m","september_B2_drop_m","september_B3_drop_m")]
  conversion_ok=bool(den.get("june_diluted_Aeq_weighted_m")==1898
     and isinstance(sep,(int,float)) and all(isinstance(x,(int,float)) for x in bchanges)
     and passed(sum(bchanges),sep,.00001)
     and passed(den["central_m"],1898-sep,.00001)
     and den.get("date_common_equivalent")=="2026-06-30"
     and den.get("date_conversion_adjustment")=="2026-09-18"
     and den.get("status")=="single_quarter_eps_diluted_with_september_class_B_event_adjustment")
  checks.append({"name":"Visa June Class A diluted EPS denominator less September documented B conversion reduction",
     "pass":conversion_ok,"june_weighted_diluted_Aeq_m":1898,"sept_loss_Aeq_m":sep,
     "provisional_denominator_m":den["central_m"]})
  if not conversion_ok:
   flag("P0","Not comparable without bridge",
        "Visa economic diluted class A denominator still mixes dates and double counts participating securities",
        "Model count not credible","Use Note12 EPS diluted shares as one basis, apply 8-K delta once",notes["rate_update"])
  else:
   flag("P1","Not comparable without bridge",
        "Visa 1,898m weighted diluted Q2 EPS less 1.104m Sep conversion reduction is not shares currently outstanding",
        "Open-market repurchases and awards between June and October remain unverified",
        "Update subsequent event/share-repurchase rollforward before approving price per share",notes["rate_update"])
  flag("P1","Unsupported assumption","Visa CFO depends on client incentives, litigation and escrow",
       "Recurring cash can depart from operating CFO-CAPEX",
       "Bridge 5Y incentive payments, litigation cash and restricted funds",primary)
 elif t=="MA":
  fy=notes["observations"]["fy2025_m"]
  bridge=sec.get("official_filing_bridge",{})
  incomes=[row.get("metrics",{}).get("net_income",{}).get("value") for row in sec["history"]]
  expected=OFFICIAL_ANNUAL["MA"]["net_income"]
  all_earnings=all(row["fy_end"] in expected
     and row.get("metrics",{}).get("net_income",{}).get("value") is not None
     and passed(row["metrics"]["net_income"]["value"]/1e6,expected[row["fy_end"]][0],.001)
     and (row["metrics"]["net_income"].get("taxonomy")=="us-gaap" and row["metrics"]["net_income"].get("accession")
       or row["metrics"]["net_income"].get("taxonomy")=="issuer_reported_10k" and row["metrics"]["net_income"].get("source_url"))
      for row in sec["history"])
  net_ok=bool(len(incomes)==5 and all_earnings
      and passed(incomes[-1]/1e6,fy["net_income"],.001)
      and bridge.get("status") in ("crosswalk_validated","not_applicable")
      and not bridge.get("conflicts"))
  checks.append({"name":"Mastercard 5Y reported GAAP net income cash-to-earnings source bridge",
    "pass":net_ok,"five_year_net_income_m":[v/1e6 if v else None for v in incomes]})
  if not net_ok:
   flag("P0","Source contradiction",
        "Mastercard FY2021–2025 annual net income remains missing or inconsistent with 10-K",
        "Earnings cross-check and payment model are unsupported",
        "Map the issuer-specific income concept and compare all five fiscal ends",primary)
  flag("P1","Not comparable without bridge","Settlement and client incentive payments drive CFO",
       "Unadjusted FCF may not represent cash to shareholders",
       "Reconcile 5Y payments incentives and accrued settlement",primary)
  screened=record.get("sector_valuation",{}).get("normalized_cash_musd")
  model_start=scenarios["base"]["owner_cf1_m"]
  if screened and model_start>screened*1.2:
   flag("P1","Not comparable without bridge",
        "Mastercard per-share base cash "+str(model_start)+"m exceeds payment sector cash/earnings cap "+str(round(screened))+"m",
        "Two CIIP methods yield materially different starting values",
        "Reconcile historical income cap versus prospectively distributable cash and choose one sourced method",primary)
 elif t=="TXN":
  ltm=notes["observations"]["ltm_20260930_m"]
  gaap=ltm["gaap_cfo"]-ltm["capex"]
  adjusted=gaap+ltm["CHIPS_direct_incentive_cash"]
  checks.append({"name":"TI LTM adjusted FCF bridge","pass":passed(adjusted,ltm["issuer_adjusted_fcf"],.001),
                 "gaap_proxy_m":gaap,"subsidy_m":ltm["CHIPS_direct_incentive_cash"],"adjusted_m":adjusted})
  if not passed(adjusted,ltm["issuer_adjusted_fcf"],.001):
   flag("P0","Source contradiction","TI adjusted non-GAAP FCF does not tie to source",
        "Reinvestment bridge inconsistent","Reconcile disclosures and subsidy line",notes["ir"])
  fyfcf=latest["fcf_usd"]/1e6 if latest.get("fcf_usd") is not None else None
  cash_anchor=c["cash_anchor"]
  ltm_gaap=gaap
  reserve=cash_anchor.get("cycle_reserve_model_m")
  bcase=scenarios["base"]["owner_cf1_m"]
  cycle_ok=bool(reserve is not None and reserve>=0
    and passed(ltm_gaap-reserve,bcase,.001)
    and cash_anchor.get("ltm_fcf_gaap_proxy_m")==ltm_gaap
    and cash_anchor.get("ltm_incentive_cash_nonrecurring_m")==ltm["CHIPS_direct_incentive_cash"])
  checks.append({"name":"TI LTM 2026 GAAP CFO-CAPEX less through-cycle analyst reserve",
    "pass":cycle_ok,"ltm_gaap_cash_m":ltm_gaap,"illustrative_cycle_reserve_m":reserve,
    "model_base_cash_m":bcase})
  if not cycle_ok:
   flag("P0","Unsupported assumption",
       "TI baseline cash does not reconcile to latest LTM GAAP CFO less gross CAPEX and a separately tagged cycle reserve",
       "Current FCF jump unsupported by reported data","Bridge LTM and operating cycle without adding CHIPS subsidy twice",primary)
  else:
   flag("P1","Unsupported assumption",
        "TXN analyst cycle reserve $1.818bn used to adjust 2026 LTM GAAP FCF is not equivalent to audited maintenance CAPEX",
        "Longer-run fab utilization and capital replacement schedule not demonstrated",
        "Reconcile utilization, inventory and facility CAPEX commitments through 2030",primary)
  flag("P1","Not comparable without bridge","CHIPS subsidy receipts are not necessarily recurring",
       "Cannot treat management adjusted FCF as perpetual owner cash",
       "Keep GAAP CFO-CAPEX separate from government grant proceeds",notes["ir"])
  pending=notes["observations"].get("pending_silicon_labs_acquisition_m",{})
  if pending.get("enterprise_value_approx"):
   flag("P1","Not comparable without bridge",
        "Texas Instruments pending Silicon Labs enterprise value ~"+str(pending["enterprise_value_approx"])+"m and potential financing of "+str(pending.get("financing_term_loan_committed"))+"m",
        "Forecast future debt service, acquisition payment and acquired cash are not in FY2025/LTM starting FCFE",
        "Add deal/no-deal and funded closing scenarios, acquisition purchase price and forward debt bridge",pending.get("source",primary))
 # Independent audit sensitivities are diagnostics, NOT revised forecasts.
 base_assumptions=scenarios["base"]
 def stress(cash_factor,required_return_shift):
  cash=net_owner_cash(base_assumptions)*cash_factor
  r=base_assumptions["ke_pct"]/100+required_return_shift
  return round(dcf(cash,base_assumptions["g1_pct"]/100,base_assumptions["g2_pct"]/100,
                   r,base_assumptions["t_pct"]/100)["equity_value_musd"]/den["central_m"],2)
 sensitivity={
  "status":"illustrative_audit_sensitivity_not_forecast",
  "cash_80pct_usd":stress(.8,0),
  "cash_120pct_usd":stress(1.2,0),
  "cost_of_equity_plus_2pp_usd":stress(1,.02),
  "cost_of_equity_minus_2pp_usd":stress(1,-.02),
  "cost_of_equity_12pct_usd":stress(1,.12-base_assumptions["ke_pct"]/100),
  "cost_of_equity_15pct_usd":stress(1,.15-base_assumptions["ke_pct"]/100),
  "caveat":"No changes to source scenario; sensitivity of the original cash baseline only. Does not incorporate operating-stage or accounting bridge changes."
 }
 remediation_checks=[]
 for rem_id,rem_control in ORIGINAL_P0_CONTROLS[t]:
  control=next((x for x in checks if x["name"]==rem_control),None)
  remediation_checks.append({"id":rem_id,"name":rem_control,
      "resolved":bool(control is not None and control["pass"]),"check":control})
 priority=sum(x["severity"]=="P0" for x in findings)
 return {"ticker":t,"name":c["name"],"verdict":"Not ready" if findings else "Ready with caveats",
        "portfolio_use":False,"valuation_approved":False,
        "source":primary,"source_date":dt.date.today().isoformat(),
        "checks":checks,"findings":findings,"sensitivity":sensitivity,
        "original_P0_remediations":remediation_checks,
        "P0":priority,"P1":sum(x["severity"]=="P1" for x in findings),
        "base_model_value_usd":model["scenario_values"]["base"]["equity_per_share_usd"]}
def build(d,as_of):
 if set(d["inputs"]["companies"])!=set(FIVE) or set(d["notes"]["companies"])!=set(FIVE):
  raise ValueError("Five company scope must remain unchanged")
 audits={}
 for ticker in FIVE:
  audits[ticker]=audit_ticker(ticker,d["inputs"]["companies"][ticker],
     d["notes"]["companies"][ticker],d["sec"]["companies"][ticker],
     d["audits"]["companies"][ticker],d["models"]["companies"][ticker])
 issues=sorted((f for a in audits.values() for f in a["findings"]),key=lambda x:({"P0":0,"P1":1,"P2":2}[x["severity"]],FIVE.index(x["ticker"])))
 corrected=sum(r["resolved"] for x in audits.values() for r in x["original_P0_remediations"])
 return {"schema":"ciip-model-audit-v1","as_of":as_of.isoformat(),"scope":list(FIVE),
 "overall_verdict":"Not ready for portfolio action","issuers":audits,"issue_log":issues,
 "original_P0_total":6,"original_P0_corrected":corrected,
 "new_material_issues":sum(x["severity"]=="P0" for x in issues),
 "method":"Independent recomputation and reported-cash check; does not approve forecast cash, future equity claims or stock prices"}
def markdown(d):
 lines=["# CIIP | Auditoría y validación de cinco DCF","","**Veredicto global: Not ready.** La corrección de los P0 originales se registra por control independiente. Aun si se corrigen todos, las reservas económicas y las notas de capital P1 pueden impedir decisiones de inversión.","",
 "| Compañía | Veredicto | P0 | P1 | DCF base USD |","|---|---|---:|---:|---:|"]
 lines += ["", "**P0 originales subsanados con prueba:** "+str(d["original_P0_corrected"])+"/"+str(d["original_P0_total"])+". **Cuestiones P0 nuevas:** "+str(d["new_material_issues"])+".",""]
 for t,a in d["issuers"].items():lines.append("| "+t+" | "+a["verdict"]+" | "+str(a["P0"])+" | "+str(a["P1"])+" | "+str(a["base_model_value_usd"])+" |")
 for t,a in d["issuers"].items():
  lines.extend(["","## "+a["name"],"Dictamen: "+a["verdict"],"","### Hallazgos y medidas"])
  for i in a["findings"]:
   lines.append("- **"+i["severity"]+" "+i["kind"]+"**: "+i["detail"]+". Impacto: "+i["impact"]+". Acción: "+i["required_fix"]+((". [Fuente]("+i["source"]+")") if i.get("source") else "")+".")
  lines.extend(["","### Sensibilidad independiente (solo diagnóstico)"])
  for key,val in a["sensitivity"].items():
   if isinstance(val,(int,float)):lines.append("- "+key+": "+str(val)+" USD/acción")
  lines.extend(["","### Controles realizados"])
  for c in a["checks"]:
   lines.append("- "+("PASS" if c["pass"] else "FLAG")+": "+c["name"])
 lines.extend(["","## Política de decisiones","Las hipótesis originales no se sustituyen silenciosamente. Los valores por acción actuales son referencias de un DCF de investigación, no precios aprobados.",
 "Se requiere aprobación documental, puente financiero real y contraste independiente.",""])
 return "\n".join(lines)
def main():
 d=load();x=build(d,dt.date.today())
 a=ROOT/"audits"
 (a/"model_validation_latest.json").write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 (a/"MODEL_VALIDATION_REPORT.md").write_text(markdown(x),encoding="utf-8")
 print("Validated arithmetic; audit verdict:",x["overall_verdict"],
       "P0:",sum(i["severity"]=="P0" for i in x["issue_log"]),
       "P1:",sum(i["severity"]=="P1" for i in x["issue_log"]))
if __name__=="__main__":main()
