#!/usr/bin/env python3
"""CIIP fundamentals from SEC EDGAR companyfacts. No financial estimates."""
import datetime as dt, gzip, json, os, pathlib, sys, time, urllib.request, zlib
from ciip_quality_controls import quality_normalize, current_share_reconciliation
from ciip_sector_models import build_sector_valuation
from ciip_capital_filings import latest_equity_filings
ROOT=pathlib.Path(__file__).resolve().parents[1]
AGENT=os.environ.get("SEC_USER_AGENT","").strip()
if not AGENT or "@" not in AGENT:
    raise SystemExit("Set repository variable SEC_USER_AGENT to a descriptive name and valid contact email before running SEC ingestion.")
HEADERS={"User-Agent":AGENT,"Accept":"application/json","Accept-Encoding":"gzip, deflate"}
# Explicit mappings to SEC-listed US reporting issuers. ADRs and foreign issuers
# are excluded until IFRS taxonomy and depositary share conventions are validated.
TICKERS=["MSFT","GOOGL","AMZN","META","V","MA","SPGI","MCO","COST","CPRT","FICO","ROP","HEI","TDG","INTU","ADBE","TXN","LRCX","BKNG","MELI","AZO","ORLY","ODFL","VRSK","AON","DHR","MEDP","OXY","AAON","TRUP","TBBB","FRPH"]
TAGS={
"revenue":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet","RevenueFromContractWithCustomerIncludingAssessedTax"],
"net_income":["NetIncomeLoss"],
"operating_income":["OperatingIncomeLoss"],
"assets":["Assets"],
"liabilities":["Liabilities"],
"cash":["CashAndCashEquivalentsAtCarryingValue"],
"operating_cash_flow":["NetCashProvidedByUsedInOperatingActivities"],
"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],
"long_term_debt":["LongTermDebtNoncurrent","LongTermDebt"],
}
FLOW={"revenue","net_income","operating_income","operating_cash_flow","capex"}
def get(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=25) as resp:
        raw=resp.read()
        encoding=resp.headers.get("Content-Encoding","").lower()
    if encoding=="gzip" or raw[:2]==bytes([31,139]):
        raw=gzip.decompress(raw)
    elif encoding=="deflate":
        try:
            raw=zlib.decompress(raw)
        except zlib.error:
            raw=zlib.decompress(raw,-zlib.MAX_WBITS)
    return json.loads(raw.decode("utf-8-sig"))
def select(facts, metric, as_of):
    """Select comparable annual flows and recent balance sheet instants.

    Annual income/cash-flow observations MUST come from Form 10-K.
    Interim 10-Q cumulative observations must not be mislabelled as FY.
    Compare all accepted US-GAAP tags; do not stop at the first tag.
    """
    candidates=[]
    max_age=730 if metric in FLOW else 540
    for priority,tag in enumerate(TAGS[metric]):
        observations=facts.get("us-gaap",{}).get(tag,{}).get("units",{}).get("USD",[])
        for x in observations:
            try:
                form=x.get("form")
                if form not in ("10-K","10-Q"):continue
                if not x.get("accn") or not x.get("filed"):continue
                end=dt.date.fromisoformat(x["end"])
                filed=dt.date.fromisoformat(x["filed"])
                if end>as_of or filed>as_of or (as_of-end).days>max_age:continue
                start=dt.date.fromisoformat(x["start"]) if x.get("start") else None
                if metric in FLOW:
                    if form!="10-K" or start is None:continue
                    if not 330<=(end-start).days<=380:continue
                    period="FY"
                else:
                    if start is not None:continue
                    period="instant"
                value=x["val"]
                if isinstance(value,bool) or not isinstance(value,(int,float)):continue
                candidates.append({
                    "value":value,"end":str(end),"start":str(start) if start else None,
                    "filed":str(filed),"form":form,"accession":x["accn"],
                    "period":period,"tag":tag,"taxonomy":"us-gaap","unit":"USD",
                    "_priority":priority
                })
            except (ValueError,KeyError,TypeError,OverflowError):
                continue
    if not candidates:return None
    # Most recent period; latest correction for that period; only then tag preference.
    candidates.sort(key=lambda x:(x["end"],x["filed"],-x["_priority"]),reverse=True)
    item=candidates[0]
    item.pop("_priority")
    return item


# Five-year SEC 10-K data only. Annual weighted-average diluted shares are a
# proxy for shares outstanding, NOT certified point-in-time diluted share count.
HISTORY_METRICS={
    "revenue":TAGS["revenue"],
    "net_income":TAGS["net_income"],
    "operating_income":TAGS["operating_income"],
    "operating_cash_flow":TAGS["operating_cash_flow"],
    "capex":TAGS["capex"],
    "diluted_shares":["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "equity":["StockholdersEquity"],
    "cash":TAGS["cash"],
    "long_term_debt":["LongTermDebtNoncurrent","LongTermDebt"],
    "current_long_term_debt":["LongTermDebtCurrent"],
}
HISTORY_INSTANT={"equity","cash","long_term_debt","current_long_term_debt"}
def annual_history(facts, as_of, count=5):
    """Use same-year 10-K facts; keep unavailable values null, never zero-fill."""
    from statistics import median
    grouped={}
    for metric,tags in HISTORY_METRICS.items():
        series={}
        unit="shares" if metric=="diluted_shares" else "USD"
        for priority,tag in enumerate(tags):
            for item in facts.get("us-gaap",{}).get(tag,{}).get("units",{}).get(unit,[]):
                try:
                    if item.get("form") not in ("10-K","10-K/A"):continue
                    if not item.get("accn") or not item.get("filed"):continue
                    end=dt.date.fromisoformat(item["end"])
                    filed=dt.date.fromisoformat(item["filed"])
                    if end>as_of or filed>as_of or (as_of-end).days>2400:continue
                    start=dt.date.fromisoformat(item["start"]) if item.get("start") else None
                    if metric in HISTORY_INSTANT:
                        if start is not None:continue
                        period="instant"
                    else:
                        if start is None or not 330<=(end-start).days<=390:continue
                        period="FY"
                    val=item.get("val")
                    if isinstance(val,bool) or not isinstance(val,(int,float)):continue
                    if not (-1e16<float(val)<1e16):continue
                    datum={
                        "value":val,"end":end.isoformat(),"start":start.isoformat() if start else None,
                        "filed":filed.isoformat(),"form":item["form"],"accession":item["accn"],
                        "tag":tag,"unit":unit,"period":period,"taxonomy":"us-gaap"}
                    score=(filed.toordinal(),-priority)
                    key=end.isoformat()
                    if key not in series or score>series[key][0]:series[key]=(score,datum)
                except (ValueError,TypeError,KeyError,OverflowError):continue
        for year,(_score,datum) in series.items():
            grouped.setdefault(year,{})[metric]=datum
    ends=sorted((end for end,items in grouped.items() if
                 any(items.get(n) for n in ("revenue","operating_cash_flow","net_income"))),reverse=True)
    # Discard isolated partial 10-K periods that do not sit in an annual series.
    filtered=[]
    for end in ends:
        if not filtered or 280<=(dt.date.fromisoformat(filtered[-1])-dt.date.fromisoformat(end)).days<=455:
            filtered.append(end)
        if len(filtered)>=count:break
    rows=[]
    for end in reversed(filtered):
        facts_for_year=grouped[end]
        def num(k):
            x=facts_for_year.get(k)
            return x["value"] if x else None
        cfo=num("operating_cash_flow");capex=num("capex")
        fcf=cfo-capex if cfo is not None and capex is not None and capex>=0 else None
        rev=num("revenue");op=num("operating_income");net=num("net_income")
        shares=num("diluted_shares")
        rows.append({
            "fy_end":end,"metrics":facts_for_year,
            "fcf_usd":fcf,
            "fcf_per_diluted_share":fcf/shares if fcf is not None and shares and shares>0 else None,
            "operating_margin_pct":100*op/rev if rev and op is not None else None,
            "net_margin_pct":100*net/rev if rev and net is not None else None,
            "cash_conversion":cfo/net if net and cfo is not None and net>0 else None,
        })
    complete_fcf=[r for r in rows if r["fcf_usd"] is not None]
    recent=rows[-3:]
    normalized=median(r["fcf_usd"] for r in recent) if len(recent)==3 and all(
        r["fcf_usd"] is not None and r["fcf_usd"]>0 for r in recent) else None
    latest=rows[-1] if rows else None
    age=(as_of-dt.date.fromisoformat(latest["fy_end"])).days if latest else None
    # Raw SEC diluted weighted-average shares can be class-limited or split
    # inconsistent; label source and require deliberate confirmation in UI.
    shares=[r["metrics"]["diluted_shares"]["value"] for r in recent
            if r["metrics"].get("diluted_shares") and r["metrics"]["diluted_shares"]["value"]>0]
    share_variation=(max(shares)/min(shares)) if len(shares)==3 and min(shares)>0 else None
    shares_acceptable=bool(len(shares)==3 and share_variation is not None and
                           share_variation<=1.35 and 1e6<=shares[-1]<=1e11)
    revenue_cagr=None
    rev_rows=[r for r in rows if r["metrics"].get("revenue") and r["metrics"]["revenue"]["value"]>0]
    if len(rev_rows)>=4:
        start,end=rev_rows[0],rev_rows[-1]
        years=(dt.date.fromisoformat(end["fy_end"])-dt.date.fromisoformat(start["fy_end"])).days/365.25
        if years>=2.7:
            revenue_cagr=100*((end["metrics"]["revenue"]["value"]/start["metrics"]["revenue"]["value"])**(1/years)-1)
    notes=[]
    if len(rows)<3:notes.append("Menos de tres ejercicios anuales SEC identificados")
    if normalized is None:notes.append("Faltan tres años consecutivos con CFO-CAPEX positivo y comparable")
    if age is None or age>520:notes.append("Último 10-K demasiado antiguo para valoración")
    if not shares_acceptable:notes.append("Acciones diluidas anuales no verificadas o variación entre años superior al 35 %")
    if len(rows)>=5 and revenue_cagr is None:notes.append("CAGR de ingresos no calculable")
    return rows,{
        "latest_fy_end":latest["fy_end"] if latest else None,
        "latest_fy_age_days":age,"available_years":len(rows),
        "positive_fcf_years":sum(r["fcf_usd"] is not None and r["fcf_usd"]>0 for r in rows),
        "complete_fcf_years":len(complete_fcf),
        "normalized_fcf_3y_usd":normalized if normalized is not None and age is not None and age<=520 else None,
        "revenue_cagr_pct":revenue_cagr,
        "latest_diluted_shares":shares[-1] if shares_acceptable else None,
        "diluted_shares_3y_ratio":share_variation,
        "diluted_shares_proxy_available":shares_acceptable,
        "source_notes":notes,
        "status":"historical_ready" if normalized is not None and age is not None and age<=520 else "insufficient",
    }

def main():
    mapping=get("https://www.sec.gov/files/company_tickers.json")
    cikmap={v["ticker"].upper():str(v["cik_str"]).zfill(10) for v in mapping.values()}
    result={"schema":"ciip-fundamentals-v1","source":"SEC EDGAR companyfacts (US GAAP)","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"companies":{},"unavailable":{},"caveat":"Annual flows: latest matching 10-K fiscal year, Form 10-Q year-to-date excluded. Balance sheet values can be later quarterly instants. Capex is a positive cash outflow. Reported long-term debt excludes current portion when tagged LongTermDebtNoncurrent. Annual 5-year history is shown as supplied by 10-K; three-year median CFO-CAPEX is a provisional normalization. Diluted shares are weighted-average and must be verified. CAPEX normalized conservatively; working capital movements only partial. Share reconciliation is provisional and blocks multi-class situations. Sector-specific gates govern DCF. No audited ROIC or investment advice."}
    for ticker in TICKERS:
        cik=cikmap.get(ticker)
        if not cik:
            result["unavailable"][ticker]="Ticker not found in SEC mapping"
            continue
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            obj=get(url)
            facts=obj.get("facts",{})
            as_of=dt.datetime.now(dt.timezone.utc).date()
            metrics={k:select(facts,k,as_of) for k in TAGS}
            history,history_quality=annual_history(facts,as_of)
            sector=quality_normalize(facts,history,history_quality,ticker,as_of)
            shares=current_share_reconciliation(facts,ticker,history_quality,as_of)
            sector_valuation=build_sector_valuation(ticker,history,history_quality,shares)
            try:
                submissions=get(f"https://data.sec.gov/submissions/CIK{cik}.json")
                capital_filings=latest_equity_filings(submissions,cik,as_of)
            except Exception as filing_exc:
                capital_filings={"status":"filings_unavailable","filings":[],
                    "review_topics":[],"reviewed_notes":[],
                    "verified_current_fully_diluted_shares":None,
                    "warning":str(filing_exc)[:150]}
            annual_ends=[m["end"] for name,m in metrics.items() if name in FLOW and m]
            annual_end=max(annual_ends) if annual_ends else None
            # Drop older annual metrics rather than mixing fiscal years in one row.
            excluded=[]
            for name in FLOW:
                if metrics.get(name) and metrics[name]["end"]!=annual_end:
                    excluded.append({"metric":name,"latest_available_end":metrics[name]["end"],"reason":"different_fiscal_year"})
                    metrics[name]=None
            result["companies"][ticker]={"cik":cik,"entity_name":obj.get("entityName"),"url":url,"annual_reference_end":annual_end,"excluded_annual_metrics":excluded,"metrics":metrics,"history":history,"history_quality":history_quality,"sector_control":sector,"share_reconciliation":shares,"sector_valuation":sector_valuation,"capital_filings":capital_filings}
        except Exception as exc:
            result["unavailable"][ticker]=str(exc)[:180]
        time.sleep(0.25)
    out=ROOT/"fundamentals-auto.json"
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    available=sum(any(x for x in c["metrics"].values()) for c in result["companies"].values())
    print(f"SEC fundamentals: {available} entities with facts / {len(TICKERS)} targets; failures={len(result['unavailable'])}")
    if available<5:
        print("ERROR: insufficient SEC fundamentals coverage",file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":main()
