#!/usr/bin/env python3
"""CIIP fundamentals from SEC EDGAR companyfacts. No financial estimates."""
import datetime as dt, gzip, json, os, pathlib, sys, time, urllib.request, zlib
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

def main():
    mapping=get("https://www.sec.gov/files/company_tickers.json")
    cikmap={v["ticker"].upper():str(v["cik_str"]).zfill(10) for v in mapping.values()}
    result={"schema":"ciip-fundamentals-v1","source":"SEC EDGAR companyfacts (US GAAP)","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"companies":{},"unavailable":{},"caveat":"Annual flows: latest matching 10-K fiscal year, Form 10-Q year-to-date excluded. Balance sheet values can be later quarterly instants. Capex is a positive cash outflow. Reported long-term debt excludes current portion when tagged LongTermDebtNoncurrent. No automatic FCF, ROIC or valuation."}
    for ticker in TICKERS:
        cik=cikmap.get(ticker)
        if not cik:
            result["unavailable"][ticker]="Ticker not found in SEC mapping"
            continue
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            obj=get(url)
            facts=obj.get("facts",{})
            metrics={k:select(facts,k,dt.datetime.now(dt.timezone.utc).date()) for k in TAGS}
            annual_ends=[m["end"] for name,m in metrics.items() if name in FLOW and m]
            annual_end=max(annual_ends) if annual_ends else None
            # Drop older annual metrics rather than mixing fiscal years in one row.
            excluded=[]
            for name in FLOW:
                if metrics.get(name) and metrics[name]["end"]!=annual_end:
                    excluded.append({"metric":name,"latest_available_end":metrics[name]["end"],"reason":"different_fiscal_year"})
                    metrics[name]=None
            result["companies"][ticker]={"cik":cik,"entity_name":obj.get("entityName"),"url":url,"annual_reference_end":annual_end,"excluded_annual_metrics":excluded,"metrics":metrics}
        except Exception as exc:
            result["unavailable"][ticker]=str(exc)[:180]
        time.sleep(0.16)
    out=ROOT/"fundamentals-auto.json"
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    available=sum(any(x for x in c["metrics"].values()) for c in result["companies"].values())
    print(f"SEC fundamentals: {available} entities with facts / {len(TICKERS)} targets; failures={len(result['unavailable'])}")
    if available<5:
        print("ERROR: insufficient SEC fundamentals coverage",file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":main()
