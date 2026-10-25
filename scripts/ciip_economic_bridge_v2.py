#!/usr/bin/env python3
"""Independent economic bridges; diagnostic only, existing DCF untouched."""
import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIVE = ("ADBE", "MSFT", "V", "MA", "TXN")

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def approx(a, b, tolerance=0.01):
    return abs(a-b) <= tolerance

def build(evidence, assumptions, legacy, date):
    if set(evidence["companies"]) != set(FIVE) or set(assumptions["companies"]) != set(FIVE):
        raise ValueError("Scope change is forbidden")
    result = {
        "schema": "ciip-economic-bridges-v2",
        "as_of": date.isoformat(),
        "existing_dcf_immutable": True,
        "overall_status": "ECONOMIC_BRIDGES_PARTIAL_FORECAST_NOT_SIGNED",
        "companies": {}
    }
    for ticker in FIVE:
        x = evidence["companies"][ticker]
        old = legacy["companies"][ticker]
        scenario = assumptions["companies"][ticker]["scenarios"]["base"]
        base = old["scenario_values"]["base"]["equity_per_share_usd"]
        out = {
            "legacy_base_per_share_unchanged_usd": base,
            "valuation_approved": False,
            "portfolio_action_allowed": False,
            "hard_data_checks": [],
            "forward_economic_gaps": [],
            "no_double_count_controls": [],
            "source_urls": [str(v) for k,v in x.items() if k.endswith("source") and isinstance(v,str)],
        }
        def check(name, actual, expected):
            ok = approx(actual, expected)
            out["hard_data_checks"].append({"check":name, "pass":ok, "actual_musd":actual, "expected_musd":expected})
            if not ok:
                raise ValueError(f"{ticker}: {name} does not tie ({actual} vs {expected})")
        def gap(name, why):
            out["forward_economic_gaps"].append({"issue":name,"blocking_reason":why})
        def control(note):
            out["no_double_count_controls"].append(note)
        if ticker == "ADBE":
            fy = x["fy2025"]; interim = x["nine_months_2026"]; prior=x["nine_months_2025"]
            check("FY25 CFO-PPE CAPEX-SBC",fy["cfo"]-fy["capex_ppe"]-fy["sbc_non_cash"],7910)
            check("9M26 CFO-PPE CAPEX-SBC",interim["cfo"]-interim["capex_ppe"]-interim["sbc_non_cash"],5884)
            out["organic_vs_acquired_cash_diagnostic"]={
                "FY2025_owner_proxy_m":7910,
                "9m_2026_owner_proxy_m":5884,
                "9m_2025_owner_proxy_m":prior["cfo"]-prior["capex_ppe"]-prior["sbc_non_cash"],
                "unexplained_yoy_change_m":5884-(prior["cfo"]-prior["capex_ppe"]-prior["sbc_non_cash"]),
                "FY2026_acquisition_cash_9m_m":interim["acquisition_cash_net"],
                "baseline_gross_owner_cash_m":scenario["owner_cf1_m"],
                "assumed_annual_ma_reserve_m":scenario["annual_acquisition_reinvestment_m"],
                "original_model_net_cash_m":scenario["owner_cf1_m"]-scenario["annual_acquisition_reinvestment_m"]
            }
            control("Semrush historical purchase is spent, do not subtract again from FY2025 cash anchor.")
            control("The legacy model grows net initial cash; a fixed annual M&A reserve would instead be a separate annual deduction, not algebraically identical.")
            gap("M&A recurrence and organic growth","No disclosed annual recurring acquisition programme substantiates $350m/yr.")
            gap("Topaz conditional completion","As-of filing disclosed $340m pending; do not assume close or future contribution.")
            gap("Economic SBC compensation","SBC-as-cash proxy and diluted share awards jointly require checks for double charge.")
        if ticker == "MSFT":
            fy = x["fy2026"]; payments=x["reported_undiscounted_finance_lease_payments"]
            check("FY26 full historical owner proxy",fy["cfo"]-fy["capex_cash"]-fy["sbc_non_cash"]-fy["finance_lease_principal_cash"],51481)
            check("Finance lease payment face vs liabilities plus undiscounted interest",sum(payments.values()),x["reported_finance_lease_liability"]+x["finance_lease_imputed_interest_total"])
            out["lease_commitment_economics"]={"finance_lease_cash_principal_fy2026_m":fy["finance_lease_principal_cash"],"new_non_cash_finance_rou_fy2026_m":fy["noncash_new_finance_lease_ro_assets"],"finance_lease_future_undiscounted_payments_m":payments,"not_commenced_future_undiscounted_leases_m":x["finance_lease_not_yet_commenced"],"uncommenced_are_not_current_borrowings":True}
            control("Exclude finance lease interest from additional FCFE subtraction if already inside CFO.")
            control("Never deduct 24,608m ROU noncash additions as if current-period cash CAPEX.")
            control("Uncommenced leases are not the same as $329.1bn currently drawn debt.")
            gap("Lease commencement calendar","No exact years, financing type and incremental margin for $329.1bn uncommenced arrangements.")
            gap("AI/data center reinvestment economics","13% 5Y annual growth of lease-adjusted owner cash requires segment profitability and server renewal forecasts.")
        if ticker == "V":
            x26=x["nine_months_2026"]; x25=x["nine_months_2025"]
            check("9M26 PPE cash FCF proxy",x26["cfo"]-x26["capex_ppe_technology"],15164)
            check("9M26 incentives accrual/cash movement",x26["client_incentive_non_cash"]+x26["client_incentive_cash_change"],73)
            check("9M25 incentives accrual/cash movement",x25["client_incentive_non_cash"]+x25["client_incentive_cash_change"],250)
            out["period_specific_reconciliation"]={"2026_9m_net_client_incentive_bridge_m":73,"2025_9m_net_client_incentive_bridge_m":250,"2026_9m_settlement_receivables_change_m":x26["settlement_receivable_cash_change"],"2026_9m_settlement_payables_change_m":x26["settlement_payable_cash_change"],"2026_9m_accrued_litigation_cash_change_m":x26["accrued_litigation_cash_change"],"restricted_litigation_cash_20260630_m":x["restricted_litigation_cash_20260630"]}
            control("Litigation accrual movements already embedded in reported CFO must not be independently deducted twice.")
            control("Do not include restricted cash in shareholder distributable cash.")
            gap("5Y incentive timing","Only two comparable nine-month observations here; five full audited annual schedules not reconstructed.")
            gap("Current fully diluted Class A equivalents","Date-mixed September conversion and Q2 weighted shares remain a diagnostic denominator.")
        if ticker == "MA":
            fy=x["fy2025"]; h=x["six_months_2026"]; h25=x["six_months_2025"]
            fcf=fy["cfo"]-fy["capex_ppe"]-fy["capitalized_software"]
            check("FY25 PPE+capitalized software FCF",fcf,16433)
            check("H1 2026 PPE+capitalized software FCF",h["cfo"]-h["capex_ppe"]-h["capitalized_software"],5959)
            check("H1 2025 PPE+capitalized software FCF",h25["cfo"]-h25["capex_ppe"]-h25["capitalized_software"],6417)
            out["reported_2025_comparability"]={"legacy_omitting_software_capex_m":fy["cfo"]-fy["capex_ppe"],"reconciled_2025_investing_FCF_m":fcf,"cash_difference_m":fy["capitalized_software"],"legacy_base_cash_assumption_m":scenario["owner_cf1_m"],"base_vs_corrected_reported_fcf_m":scenario["owner_cf1_m"]-fcf}
            out["bvnk"]={"closed_date":x["bvnk"]["deal_complete_date"],"initial_contract_price_m":x["bvnk"]["contract_initial_price"],"contingent_cap_m":x["bvnk"]["contingent_consideration_cap"],"actual_cash_paid_m":None,"incremental_earnings_m":None}
            control("Capitalized software is an investing cash expense, do not report PPE-only as all-in FCF.")
            control("BVNK $1.5bn contractual price is not evidence for $1.5bn actual closing cash outflow.")
            gap("Customer incentives/settlement normalization","Prepaid incentives and settlement liability cash schedules need 5Y annual tie-outs.")
            gap("BVNK deal and return on capital","Closed acquisition, but exact post-close cash paid, funding and cash contribution are not established.")
            gap("Sector income cap discrepancy","Sector model uses 12,230m vs per-share 16,000m initial owner cash, requiring explicit common methodology.")
        if ticker == "TXN":
            ltm=x["ltm_20260930"]
            gaap=ltm["cfo"]-ltm["capex_cash"]
            check("GAAP LTM CFO-CAPEX",gaap,7318)
            check("Company adjusted FCF bridge direct government cash",gaap+ltm["direct_chips_investing_receipts"],ltm["reported_adjusted_fcf"])
            check("Legacy analyst reserve reconciliation",gaap-assumptions["companies"]["TXN"]["cash_anchor"]["cycle_reserve_model_m"],scenario["owner_cf1_m"])
            out["cycle_cash"]={"reported_GAAP_FCF_m":gaap,"direct_grants_in_investing_m":ltm["direct_chips_investing_receipts"],"investment_tax_credits_already_in_CFO_m":ltm["ips_chips_tax_credit_in_cfo"],"analyst_cycle_reserve_not_maintenance_capex_m":assumptions["companies"]["TXN"]["cash_anchor"]["cycle_reserve_model_m"],"legacy_model_owner_cash_m":scenario["owner_cf1_m"],"guidance_CAPEX_2026_low_m":x["capex_2026_guidance_low"],"guidance_CAPEX_2026_high_m":x["capex_2026_guidance_high"]}
            out["silicon_labs"]={"pending_enterprise_value_approx_m":x["silicon_labs"]["ev_approx"],"committed_term_loan_capacity_m":x["silicon_labs"]["term_loan_facility_capacity"],"loan_drawn_at_disclosure_m":0,"purchase_equity_cash_check_m":None}
            control("GAAP CFO includes $469m credit benefit; do not add it to historical cash a second time.")
            control("$1,104m direct grant investing cash appears only in adjusted measure, not GAAP CFO minus gross CAPEX.")
            control("An undrawn $5bn credit facility does not represent debt until borrowed.")
            gap("Fab capacity and sustaining CAPEX","No facility-level replacement CAPEX, utilization cycle or 2030 demand schedule validating $1.818bn reserve.")
            gap("Silicon Labs pending acquisition","No approved post-close transaction sources/uses, financing expense or acquired operating cash forecast.")
        out["hard_data_pass"] = all(q["pass"] for q in out["hard_data_checks"])
        out["economic_issues_open"] = len(out["forward_economic_gaps"])
        result["companies"][ticker]=out
    return result

def render(r):
    lines=["# CIIP Economic Bridge Review v2","",f"Date: {r['as_of']}. Status: **{r['overall_status']}**.",
           "Legacy DCF assumptions and share-count estimates are NOT overwritten.","",
           "| Ticker | Legacy base DCF $/share | Reported arithmetic | Unresolved economic dependencies | Portfolio use |",
           "|---|---:|---|---:|---|"]
    for t,x in r["companies"].items():
        lines.append(f"| {t} | {x['legacy_base_per_share_unchanged_usd']:.2f} | {'PASS' if x['hard_data_pass'] else 'FAIL'} | {x['economic_issues_open']} | BLOCKED |")
    for t,x in r["companies"].items():
        lines += ["",f"## {t}","", "**Reconciled reported / historical quantities**"]
        for c in x["hard_data_checks"]:
            lines.append(f"- {'PASS' if c['pass'] else 'FAIL'} {c['check']}: {c['actual_musd']:,.3f} vs {c['expected_musd']:,.3f} USD m")
        lines += ["","**Double-counting rules**"] + ["- "+n for n in x["no_double_count_controls"]]
        lines += ["","**Economic model remains blocked on**"] + [f"- {z['issue']}: {z['blocking_reason']}" for z in x["forward_economic_gaps"]]
        if x["source_urls"]:
            lines+=["","Source URLs:"] + ["- "+u for u in x["source_urls"]]
    lines+=["","## Decision controls","- PASS means arithmetic tied to explicitly logged evidence, NOT an independent financial statement audit.","- Reported facts, derived historical numbers, and analyst estimates are never interchanged.","- No issuer can be READY while forward economic schedules or current share capital remain unverified.","- No change to old scenario parameters, reported legacy per-share values, or signoff.",""]
    return "\n".join(lines)

def main():
    date=dt.date.today()
    r=build(load("audits/economic_evidence_v2.json"),load("audits/per_share_inputs.json"),load("audits/per_share_latest.json"),date)
    (ROOT/"audits/economic_bridge_latest.json").write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (ROOT/"audits/ECONOMIC_BRIDGE_REPORT.md").write_text(render(r),encoding="utf-8")
    print(r["overall_status"], sum(x["economic_issues_open"] for x in r["companies"].values()))
if __name__=="__main__":
    main()
