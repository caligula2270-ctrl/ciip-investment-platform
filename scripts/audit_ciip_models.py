#!/usr/bin/env python3
"""Five-issuer CIIP model audit: source tie-out, math and assumptions."""
import datetime as dt, json, pathlib, math
from build_ciip_per_share import dcf
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
 "inputs":"audits/per_share_inputs.json",
 "notes":"audits/validation_evidence.json",
 "sec":"fundamentals-auto.json",
 "audits":"audits/latest.json",
 "models":"audits/per_share_latest.json"
}
FIVE=("ADBE","MSFT","V","MA","TXN")
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
  v=dcf(assumptions["owner_cf1_m"],assumptions["g1_pct"]/100,
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
  if nine["acquisitions_net"]>0:
   flag("P0","Unsupported assumption",
        "Adobe 9M2026 acquisitions cash "+str(nine["acquisitions_net"])+"m omitted from normalized owner cash",
        "If acquisitions sustain growth, cost of reinvestment understated",
        "Model acquisitions separately from ordinary CAPEX, without assuming every acquisition repeats",primary)
  anchor=fy["cfo"]-fy["capex"]-fy["sbc"]
  base=scenarios["base"]["owner_cf1_m"]
  checks.append({"name":"Adobe source CFO-CAPEX-SBC bridge","pass":passed(anchor,7910),
                 "owner_cash_m":anchor,"base_assumed_m":base})
  flag("P1","Unsupported assumption",
       "Adobe base cash "+str(base)+"m vs FY2025 CFO-CAPEX-SBC "+str(anchor)+"m",
       "Forecast SBC, AI economics and M&A not connected to operating schedules",
       "Forecast revenue/margins/SBC/acquisition reinvestment separately",primary)
 elif t=="MSFT":
  a=notes["observations"]["fy2026_m"]
  ok=passed(cfo_m,a["cfo"]) and passed(capex_m,a["capex"])
  checks.append({"name":"Microsoft reported FY2026 CFO CAPEX","pass":ok})
  owner=a["cfo"]-a["capex"]-a["sbc"];base=scenarios["base"]["owner_cf1_m"]
  if base>owner*1.2:
   flag("P0","Unsupported assumption",
      "Base cash "+str(base)+"m vs FY2026 CFO-CAPEX-SBC "+str(owner)+"m",
      "Large unverified increase before first forecast growth year",
      "Build five-year AI capacity, renewal, finance lease principal and cloud margins bridge",primary)
  flag("P1","Not comparable without bridge","Finance lease principal/new financed datacenter assets omitted from simplistic cash CAPEX",
       "Reinvestment understates capital intensity","Bridge leases, depreciation, server capacity and cash/noncash investment",primary)
 elif t=="V":
  if capex is None:
   flag("P0","Not comparable without bridge","Visa lacks comparable annual CAPEX in generic SEC facts",
        "FCF series is missing, cash normalization is not reproducible",
        "Implement issuer-specific XBRL/footnote mapping for property and technology spend",primary)
  flag("P0","Not comparable without bridge","Visa B-class, preferred and participating-security denominator mixes different dates",
       "A-equivalent fully diluted share count unapproved",
       "Reconcile September 2026 8-K class factors with same-date counts and litigation rights",
       notes["rate_update"])
  flag("P1","Unsupported assumption","Visa CFO depends on client incentives, litigation and escrow",
       "Recurring cash can depart from operating CFO-CAPEX",
       "Bridge 5Y incentive payments, litigation cash and restricted funds",primary)
 elif t=="MA":
  fy=notes["observations"]["fy2025_m"]
  if latest["metrics"].get("net_income") is None:
   flag("P0","Source contradiction",
        "Mastercard SEC normalized net income missing; audited FY2025 note cites "+str(fy["net_income"])+"m",
        "Cash/earnings normalization and sector payment model blocked",
        "Map issuer-specific net income US-GAAP concept with filing year matching",primary)
  flag("P1","Not comparable without bridge","Settlement and client incentive payments drive CFO",
       "Unadjusted FCF may not represent cash to shareholders",
       "Reconcile 5Y payments incentives and accrued settlement",primary)
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
  if fyfcf and scenarios["base"]["owner_cf1_m"]>fyfcf*1.5:
   flag("P0","Unsupported assumption",
        "TI base cash "+str(scenarios["base"]["owner_cf1_m"])+"m vs FY2025 FCF "+str(fyfcf)+"m",
        "High assumption for fab utilization and CAPEX reset",
        "Construct through-cycle capacity utilization, CHIPS, depreciation and CAPEX plan",primary)
  flag("P1","Not comparable without bridge","CHIPS subsidy receipts are not necessarily recurring",
       "Cannot treat management adjusted FCF as perpetual owner cash",
       "Keep GAAP CFO-CAPEX separate from government grant proceeds",notes["ir"])
 # Independent audit sensitivities are diagnostics, NOT revised forecasts.
 base_assumptions=scenarios["base"]
 def stress(cash_factor,required_return_shift):
  cash=base_assumptions["owner_cf1_m"]*cash_factor
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
 priority=sum(x["severity"]=="P0" for x in findings)
 return {"ticker":t,"name":c["name"],"verdict":"Not ready" if priority else "Ready with caveats",
        "portfolio_use":False,"valuation_approved":False,
        "source":primary,"source_date":dt.date.today().isoformat(),
        "checks":checks,"findings":findings,"sensitivity":sensitivity,
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
 return {"schema":"ciip-model-audit-v1","as_of":as_of.isoformat(),"scope":list(FIVE),
 "overall_verdict":"Not ready for portfolio action","issuers":audits,"issue_log":issues,
 "method":"Independent recomputation and reported-cash check; does not approve forecast cash, future equity claims or stock prices"}
def markdown(d):
 lines=["# CIIP | Auditoría y validación de cinco DCF","","**Veredicto global: Not ready.** No utilizar estos modelos para órdenes de inversión hasta resolver P0, revisar denominadores, sensibilidad y caja.","",
 "| Compañía | Veredicto | P0 | P1 | DCF base USD |","|---|---|---:|---:|---:|"]
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
