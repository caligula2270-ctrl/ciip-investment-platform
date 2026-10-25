#!/usr/bin/env python3
"""CIIP reusable per-share equity DCF based on explicit reviewed-source anchors.

Economic inputs are analyst assumptions, not SEC facts. Share counts are
point-in-time basic plus contemporaneous incremental diluted EPS estimates;
all intermediate conventions and uncertainty preserved. This is screen-grade.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
INPUT=ROOT/"audits/per_share_inputs.json"
AUDIT=ROOT/"audits/latest.json"
MARKET=ROOT/"market-auto.json"
OUTPUT=ROOT/"audits/per_share_latest.json"
TEXT=ROOT/"audits/PER_SHARE_REPORT.md"

def dcf(cash_m, g1, g2, r, t):
    params=(cash_m,g1,g2,r,t)
    if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in params):
        raise ValueError("DCFs require finite numerical assumptions")
    if cash_m<=0 or not -.3<=g1<=.4 or not -.3<=g2<=.4 or not .04<r<.4 or not -.05<=t<=.05 or r-t<=.005:
        raise ValueError("Invalid DCF scenario assumptions")
    pv=0.; f=float(cash_m)
    flows=[]
    for y in range(1,11):
        f*=1+(g1 if y<=5 else g2)
        pv+=f/(1+r)**y
        flows.append(round(f,3))
    terminal=f*(1+t)/(r-t)/(1+r)**10
    v=pv+terminal
    return {"equity_value_musd":round(v,2),
            "pv_explicit_musd":round(pv,2),
            "pv_terminal_musd":round(terminal,2),
            "terminal_weight_pct":round(terminal/v*100,2),
            "projected_annual_cash_musd":flows}

def net_owner_cash(case):
    """Deduct an explicit analyst recurring acquisition reinvestment reserve.

    The cash already paid for past acquisitions is sunk. An analyst-selected
    forward reserve is a future growth-maintenance stress, distinct from
    historical CAPEX; do not expense the same cash twice.
    """
    gross=case["owner_cf1_m"]
    reserve=case.get("annual_acquisition_reinvestment_m",0)
    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (gross,reserve)):
        raise ValueError("Nonfinite owner cash/reinvestment assumptions")
    if reserve<0 or reserve>=gross:raise ValueError("Recurring acquisition reserve must be >=0 and less than cash")
    return gross-reserve

def audit_model(ticker,inputs,audit,market,as_of):
    rec=audit["companies"][ticker]
    info=inputs["companies"][ticker]
    eq=info["denominator"]
    low,mid,high=[eq[k] for k in ("low_m","central_m","high_m")]
    if not 0<low<=mid<=high:
        raise ValueError("Invalid dilution uncertainty interval: "+ticker)
    if eq.get("confidence")=="verified":
        raise ValueError("A model-based share-count must not be presented as certified")
    quote=market.get("prices",{}).get(ticker,{})
    spot=quote.get("price")
    date=quote.get("date")
    fresh=False
    if spot is not None and date:
        age=(as_of-dt.date.fromisoformat(date)).days
        fresh=bool(0<=age<=10 and quote.get("currency")=="USD" and spot>0)
    # explicit date/period mismatch => model not 'decision-ready'
    sec_latest=rec.get("latest_official_filing") or {}
    newly_filed=(rec.get("filing_status")!="latest_filing_metadata_matches")
    vals={}
    for name,sc in info["scenarios"].items():
        owner_net=net_owner_cash(sc)
        base=dcf(owner_net,sc["g1_pct"]/100,sc["g2_pct"]/100,
                 sc["ke_pct"]/100,sc["t_pct"]/100)
        ev=base["equity_value_musd"]
        # Different denominator alternatives are not free cash changes.
        equity_per_share=ev/mid
        vals[name]={
            "analyst_assumptions":sc,"owner_cash_after_recurring_reinvestment_m":owner_net,"equity_aggregate_musd":ev,
            "equity_per_share_usd":round(equity_per_share,2),
            "share_count_sensitivity":{"low_dilution_value_usd":round(ev/low,2),
                                       "high_dilution_value_usd":round(ev/high,2)},
            "terminal_weight_pct":base["terminal_weight_pct"],
            "implied_price_to_value_pct":round(100*spot/equity_per_share,1) if fresh else None,
            "margin_price_to_value_pct":round((1-spot/equity_per_share)*100,1) if fresh else None,
            "cashflows":base["projected_annual_cash_musd"]}
    base=vals.get("base")
    if not base:raise ValueError("No base case for "+ticker)
    # Solve for year-1 cash needed to justify market value with fixed base-case
    # growth, discount and terminal parameters. Model is homogeneous in cash.
    cf_required=(net_owner_cash(info["scenarios"]["base"])*
                 spot/base["equity_per_share_usd"]+
                 info["scenarios"]["base"].get("annual_acquisition_reinvestment_m",0)) if fresh else None
    return {
        "ticker":ticker,"company":info["name"],
        "as_of":as_of.isoformat(),"quote":quote if fresh else None,
        "data_price_status":"provider_unverified_close" if fresh else "stale_or_unavailable",
        "filing_source_status":rec["filing_status"],
        "source_newer_than_assessed":newly_filed,
        "denominator":eq,
        "cash_anchor":info["cash_anchor"],
        "forward_convention":"owner_cf1_m is gross pre-projection annual cash; deduct analyst recurring acquisition reserve before applying g1; this is not subtracting prior spent acquisition cash twice",
        "scenario_values":vals,
        "base_cash_required_to_match_last_price_musd":round(cf_required,1) if cf_required else None,
        "additional_issues":info.get("red_flags",[]),
        "next_required_checks":["Current fully diluted share count has not been certified",
             "Equity compensation and future buyback/issuance path",
             "Prospective FCF reinvestment and working capital",
             "Stock close sourced from provider but not independently verified",
             "Economic bridge from cash proxy to common shareholder claims"],
        "status":"SCREEN_GRADE_NOT_DECISION_READY",
        "value_per_share_approved":False,
        "investment_recommendation":None
    }

def build(config,audit,market,as_of):
    configured=set(config["companies"])
    audited=set(audit["companies"])
    if not configured.issubset(audited):
        raise ValueError("A valuation model cannot exist without an audited SEC company dossier")
    return {"schema":"ciip-per-share-valuation-v1",
            "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "as_of":as_of.isoformat(),
            "source_review_as_of":audit.get("source_review_as_of"),
            "evidence_urls":{"inputs":"audits/per_share_inputs.json","audit":"audits/latest.json","market":"market-auto.json"},
            "readiness":"SCREEN_GRADE_NOT_DECISION_READY",
            "not_yet_modelled":sorted(audited-configured),
            "methodology":"Discount future hypothetical owner cash after stated strategic acquisition reinvestment reserve, at cost of equity; do not double subtract past acquisition cash, SBC, cash or debt. No guaranteed FCFE or official issuer forecast.",
            "companies":{t:audit_model(t,config,audit,market,as_of) for t in config["companies"]}}

def report(d):
    lines=["# CIIP | Valoración por acción condicionada","",
           "Informe reproducible, no certificación de capital actual ni auditoría de cuentas.",
           "Datos reportados, recuentos estimados, precios del proveedor e hipótesis DCF se muestran por separado.","",
           "| Ticker | Precio 23/10 USD | Conservador | Base | Optimista | Dilución central, millones | Estado |",
           "|---|---:|---:|---:|---:|---:|---|"]
    for ticker,x in d["companies"].items():
        spot=x.get("quote",{}).get("price") if x.get("quote") else None
        sc=x["scenario_values"]
        def fmt(n):
            return f"{n:,.2f}" if isinstance(n,(int,float)) else "—"
        lines.append(f"| {ticker} | {fmt(spot)} | {fmt(sc['conservador']['equity_per_share_usd'])} | {fmt(sc['base']['equity_per_share_usd'])} | {fmt(sc['optimista']['equity_per_share_usd'])} | {fmt(x['denominator']['central_m'])} | SCREEN-GRADE |")
    for ticker,x in d["companies"].items():
        lines+=["",f"## {ticker} — {x['company']}",
           f"Acciones: {x['denominator']['formula']}. Banda {x['denominator']['low_m']:,.3f} – {x['denominator']['high_m']:,.3f} millones.",
           f"Fuentes: {x['denominator'].get('anchor_source') or x['denominator'].get('source')}.",
           f"Comparación con cierre de mercado: {x['data_price_status']}.",
           f"Flujo base: {x['cash_anchor'].get('forward_base_justification', 'Supuesto sin validar')}.",
           "", "| Escenario | FCF neto después de reserva M USD | Crec. 1-5 | Crec. 6-10 | Ke | Terminal | Valor USD | Banda dilución USD | Terminal % |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for key,val in x["scenario_values"].items():
            a=val["analyst_assumptions"];band=val["share_count_sensitivity"]
            lines.append(f"| {key} | {val['owner_cash_after_recurring_reinvestment_m']:,.0f} | {a['g1_pct']:.1f}% | {a['g2_pct']:.1f}% | {a['ke_pct']:.1f}% | {a['t_pct']:.1f}% | {val['equity_per_share_usd']:,.2f} | {band['high_dilution_value_usd']:,.2f}–{band['low_dilution_value_usd']:,.2f} | {val['terminal_weight_pct']:.1f}% |")
        required=x["base_cash_required_to_match_last_price_musd"]
        if required is not None:lines.append(f"Flujo anual de partida requerido para justificar el precio con hipótesis base: {required:,.1f} M USD (valor implícito inverso, no previsión).")
        lines.extend(["","Pendientes:"]+["- "+z for z in x["next_required_checks"]])
    lines+=["","## Condiciones de uso","- No sumar cash y deuda al valor de un flujo que ya representa caja del accionista.",
            "- La cifra de acciones es un estimador entre fechas, no un capital actual completamente diluido validado.",
            "- Las bandas muestran SOLO incertidumbre de acciones. El rango completo depende más de flujos, tasas y reinversión.",
            "- Ningún output supera SCREEN-GRADE hasta análisis independiente y aprobación.", ""]
    return "\n".join(lines)

def main():
    config=json.loads(INPUT.read_text(encoding="utf-8"))
    audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    market=json.loads(MARKET.read_text(encoding="utf-8"))
    as_of=dt.date.today()
    result=build(config,audit,market,as_of)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    TEXT.write_text(report(result)+"\n",encoding="utf-8")
    print("Per-share screen valuations generated:",len(result["companies"]),"companies; no signoff")
if __name__=="__main__":
    main()
