#!/usr/bin/env python3
"""CIIP fundamentals from SEC EDGAR companyfacts. No financial estimates."""
import datetime as dt, json, os, pathlib, sys, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
AGENT=os.environ.get("SEC_USER_AGENT","CIIP Research contact ciip-research@example.org")
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
"long_term_debt":["LongTermDebtCurrent","LongTermDebtNoncurrent","LongTermDebt"],
}
FLOW={"revenue","net_income","operating_income","operating_cash_flow","capex"}
def get(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=25) as resp:
        return json.load(resp)
def select(facts,metric):
    for tag in TAGS[metric]:
        node=facts.get("us-gaap",{}).get(tag,{})
        units=node.get("units",{}).get("USD",[])
        rows=[]
        for x in units:
            try:
                if x.get("form") not in ("10-K","10-Q"):continue
                if x.get("accn") is None or not x.get("filed"):continue
                end=dt.date.fromisoformat(x["end"])
                start=dt.date.fromisoformat(x["start"]) if x.get("start") else None
                duration=(end-start).days if start else None
                if metric in FLOW:
                    if duration is None or not (70<=duration<=110 or 330<=duration<=380):continue
                    period="FY" if duration>300 else "Q"
                else:
                    if start is not None:continue
                    period="instant"
                rows.append({"value":x["val"],"end":x["end"],"start":x.get("start"),"filed":x["filed"],"form":x["form"],"accession":x["accn"],"period":period,"tag":tag,"taxonomy":"us-gaap","unit":"USD"})
            except (ValueError,KeyError,TypeError):continue
        if rows:
            # Prefer latest fiscal period; prefer latest filing if restated.
            rows.sort(key=lambda x:(x["end"],x["filed"]),reverse=True)
            return rows[0]
    return None
def main():
    mapping=get("https://www.sec.gov/files/company_tickers.json")
    cikmap={v["ticker"].upper():str(v["cik_str"]).zfill(10) for v in mapping.values()}
    result={"schema":"ciip-fundamentals-v1","source":"SEC EDGAR companyfacts (US GAAP)","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"companies":{},"unavailable":{},"caveat":"Latest reported facts may represent different periods. Capex is cash outflow (positive). Debt components are NOT added because tags may overlap. No automatic FCF, ROIC or valuation."}
    for ticker in TICKERS:
        cik=cikmap.get(ticker)
        if not cik:
            result["unavailable"][ticker]="Ticker not found in SEC mapping"
            continue
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            obj=get(url)
            facts=obj.get("facts",{})
            metrics={k:select(facts,k) for k in TAGS}
            result["companies"][ticker]={"cik":cik,"entity_name":obj.get("entityName"),"url":url,"metrics":metrics}
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
