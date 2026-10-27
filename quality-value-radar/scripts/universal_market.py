#!/usr/bin/env python3
"""QVR universal equities research engine (market-first, evidence gated).

Scope: any listed ticker supported by the market-data source; fundamentals from
official SEC XBRL US-GAAP when available. Other jurisdictions: quote-only until
filing-normalized international adapters exist. No invented FCF, ROIC or FX.
This script never executes orders or classifies a purchase as approved.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
REGISTRY=DATA/"universal_registry.json"
RESULT=DATA/"universal_results.json"
NOW=dt.datetime.now(dt.timezone.utc)
VALID=re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,19}$")
AGENT=os.environ.get("SEC_USER_AGENT","").strip()
HORIZON=5
FINANCIAL_SIC=((6000,6999),)

def ticker_clean(t):
    s=(t or "").strip().upper()
    if not VALID.fullmatch(s):raise ValueError("Ticker no válido. Usa símbolo de Yahoo Finance, por ejemplo MSFT, SAP.DE, 7203.T, BRK-B.")
    return s

def request_json(url,sec=False):
    ua=AGENT if sec and "@" in AGENT else "Mozilla/5.0 QualityValueRadarResearch/1.0"
    if sec and "@" not in AGENT:
        raise ValueError("SEC_USER_AGENT no configurado; no se pueden consultar documentos SEC")
    req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"application/json","Accept-Encoding":"identity"})
    with urllib.request.urlopen(req,timeout=22) as fp:
        return json.load(fp)

def chart(ticker):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(ticker,safe="")+"?range=10d&interval=1d"
    o=request_json(url)["chart"]["result"]
    if not o:raise ValueError("Ticker no reconocido por el proveedor de cotizaciones")
    z=o[0];m=z.get("meta",{})
    instrument=m.get("instrumentType") or m.get("quoteType") or "unknown"
    c=m.get("currency")
    ts=z.get("timestamp",[])
    closes=z.get("indicators",{}).get("quote",[{}])[0].get("close",[])
    data=[(dt.datetime.fromtimestamp(t,dt.timezone.utc).date().isoformat(),round(float(v),6))
          for t,v in zip(ts,closes) if isinstance(v,(int,float)) and v>0 and math.isfinite(v)]
    if not data or not c:raise ValueError("Precio/currency ausentes: no se inventa cotización")
    return {"price":data[-1][1],"date":data[-1][0],"currency":c,
       "name":m.get("longName") or m.get("shortName") or ticker,
       "instrumentType":instrument,
       "exchangeName":m.get("exchangeName") or m.get("fullExchangeName"),
       "sourceUrl":"https://finance.yahoo.com/quote/"+urllib.parse.quote(ticker,safe="")+"/history/",
       "provider":"Yahoo chart, cotización no garantizada / cierre fechado"}

def sec_directory():
    if "@" not in AGENT:return {}
    obj=request_json("https://www.sec.gov/files/company_tickers.json",True)
    return {v["ticker"].upper():{"cik":str(v["cik_str"]).zfill(10),"name":v.get("title")}
            for v in obj.values()}

def latest_annual(facts,tags,unit="USD"):
    found={}
    for priority,tag in enumerate(tags):
        for row in facts.get("us-gaap",{}).get(tag,{}).get("units",{}).get(unit,[]):
            try:
                if row.get("form") not in ("10-K","10-K/A") or not row.get("filed"):continue
                st=dt.date.fromisoformat(row["start"]);en=dt.date.fromisoformat(row["end"])
                filed=dt.date.fromisoformat(row["filed"])
                if not 330<=(en-st).days<=390 or filed>NOW.date() or (NOW.date()-en).days>2300:continue
                num=float(row["val"])
                if not math.isfinite(num):continue
                key=en.isoformat()
                cmp=(filed.toordinal(),-priority)
                if key not in found or cmp>found[key][0]:
                    found[key]=(cmp,{"amount":num,"filed":str(filed),"tag":tag})
            except (ValueError,TypeError,KeyError,OverflowError):pass
    return {k:v[1] for k,v in found.items()}

def annual_from_sec(ticker,cik):
    obj=request_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",True)
    fact=obj.get("facts",{})
    fields={
     "cashOperations":["NetCashProvidedByUsedInOperatingActivities"],
     "capitalExpenditure":["PaymentsToAcquirePropertyPlantAndEquipment"],
     "revenue":["RevenueFromContractWithCustomerExcludingAssessedTax","RevenueFromContractWithCustomerIncludingAssessedTax","Revenues","SalesRevenueNet"],
     "sbc":["ShareBasedCompensation"],
    }
    raw={name:latest_annual(fact,tags) for name,tags in fields.items()}
    # For split-adjusted shares, use current snapshot only if SEC reports its own
    # fiscal period diluted shares; do not compare to unadjusted historical shares.
    shares=latest_annual(fact,["WeightedAverageNumberOfDilutedSharesOutstanding"],"shares")
    rows=[]
    for end in sorted(set(raw["cashOperations"]) & set(raw["capitalExpenditure"])):
        cfo=raw["cashOperations"][end]["amount"]
        capex=raw["capitalExpenditure"][end]["amount"]
        if capex<0:continue
        rev=raw["revenue"].get(end,{}).get("amount")
        sbc=raw["sbc"].get(end,{}).get("amount")
        dil=shares.get(end,{}).get("amount")
        rows.append({"fyEnd":end,"revenueUSD":rev,"cfoUSD":cfo,"capexUSD":capex,
           "sbcUSD":sbc,"sbcMissing":sbc is None,
           "ownerFcfUSD":cfo-capex-sbc if sbc is not None else None,
           "dilutedShares":dil,"filingDate":raw["cashOperations"][end]["filed"],
           "cashFlowTags":{"cfo":raw["cashOperations"][end]["tag"],
                           "capex":raw["capitalExpenditure"][end]["tag"],
                           "sbc":raw["sbc"].get(end,{}).get("tag")}})
    return rows[-6:],f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

def sector_for_sic(sic):
    if sic is None:return "unknown"
    if 6000<=sic<=6999:return "financial_or_real_estate"
    if 7370<=sic<=7379:return "software"
    if 4900<=sic<=4999:return "utilities"
    if 3500<=sic<=3999:return "industrials"
    if 2800<=sic<=2899:return "chemicals"
    if 5300<=sic<=5999:return "retail"
    return "general_nonfinancial"

def sec_sector(cik):
    obj=request_json(f"https://data.sec.gov/submissions/CIK{cik}.json",True)
    sic=obj.get("sic")
    try:sic=int(sic)
    except (ValueError,TypeError):sic=None
    return sector_for_sic(sic),sic,obj.get("name")

def project(cash_per_share,g,discount,terminal_multiple):
    if cash_per_share<=0 or discount<=0 or terminal_multiple<=0:return None
    series=[cash_per_share*(1+g)**t for t in range(1,6)]
    v=sum(x/(1+discount)**t for t,x in enumerate(series,1))
    v+=series[-1]*terminal_multiple/(1+discount)**5
    return round(v,2)

def scenario_sec(rows,quote,sector):
    if sector=="financial_or_real_estate":
        return {"status":"sector_requires_other_model","reason":"Bancos, aseguradoras y REIT no se valoran con CFO−CAPEX industrial"}
    if quote["currency"]!="USD":
        return {"status":"currency_mismatch","reason":"SEC en USD y cotización en otra divisa: falta conversión verificada"}
    r=[x for x in rows if x.get("ownerFcfUSD") is not None and x["ownerFcfUSD"]>0 and
        isinstance(x.get("dilutedShares"),(int,float)) and x["dilutedShares"]>0 and
        isinstance(x.get("revenueUSD"),(int,float)) and x["revenueUSD"]>0]
    if len(r)<3:return {"status":"insufficient_cash_data","reason":"Se requieren tres ejercicios SEC con CFO, CAPEX, SBC, ingresos y acciones diluidas"}
    y=r[-3:]
    # Per-share ratios from FY are not split-adjusted. Normalizing cash/revenue
    # avoids false historic per-share comparisons after splits.
    margins=[x["ownerFcfUSD"]/x["revenueUSD"] for x in y]
    normalized_margin=statistics.median(margins)
    latest=y[-1]
    latest_rev=latest["revenueUSD"]
    latest_diluted=latest["dilutedShares"]
    fiscal=dt.date.fromisoformat(latest["fyEnd"])
    if (NOW.date()-fiscal).days>570:
        return {"status":"financials_stale","reason":"Último cierre anual supera 570 días"}
    grows=[]
    for x,yrow in zip(y,y[1:]):
        if x["revenueUSD"]>0:grows.append(yrow["revenueUSD"]/x["revenueUSD"]-1)
    growth=max(-.03,min(.10,statistics.median(grows))) if grows else 0
    # 5-year equity owner-FCF scenario. Forecast shares flat because current
    # outstanding & future SBC net dilution is not reconciled.
    fcf_per_share=latest_rev*normalized_margin/latest_diluted
    if fcf_per_share<=0:return {"status":"negative_owner_cash","reason":"FCF normalizado no positivo"}
    bear=project(fcf_per_share,max(-.08,growth-.06),11,.14)
    base=project(fcf_per_share,growth,18,.12)
    bull=project(fcf_per_share,min(.16,growth+.05),25,.11)
    if not (bear<=base<=bull):
        return {"status":"scenario_inconsistent","reason":"Orden de escenarios no coherente"}
    return {"status":"indicative_research_only","bearUSD":bear,"baseUSD":base,"bullUSD":bull,
       "observedMedianOwnerCashMarginPct":round(normalized_margin*100,2),
       "assumedAnnualRevenueGrowthPct":round(growth*100,2),
       "latestFy":latest["fyEnd"],"currentDilutedSharesUnverified":True,
       "capexMaintenanceGrowthSplitUnverified":True,"acquisitionReturnUnverified":True,
       "stockSplitReconciliationNeeded":True,
       "fcfDefinition":"CFO menos inversiones PPE menos SBC, margen sobre ingresos del mismo FY",
       "model":"5Y owner FCF × assumed terminal P/FCF 11/18/25, discount 14/12/11%",
       "warning":"No es un valor intrínseco certificado. Acciones actuales, inversiones, adquisiciones y deuda requieren auditoría"}

def research(ticker,secmap):
    q=chart(ticker)
    record={"ticker":ticker,"name":q["name"],"currency":q["currency"],"exchangeName":q["exchangeName"],
      "instrumentType":q["instrumentType"],"quote":q,"updatedAt":NOW.isoformat(),
      "researchStatus":"quote_only","fundamentalSource":None,"sourceType":None,
      "financials":[],"valuation":None,"purchaseApproved":False,
      "issues":[]}
    if q["instrumentType"] not in ("EQUITY","unknown"):
        record["researchStatus"]="not_an_equity"
        record["issues"].append("Instrumento no identificado como acción ordinaria")
        return record
    sec=secmap.get(ticker) if isinstance(secmap,dict) else None
    # Legal SEC ticker can be dash while Yahoo class-share notation uses dot.
    if not sec and "." in ticker:sec=secmap.get(ticker.replace(".","-"))
    if not sec:
        record["sourceType"]="market_quote_only"
        record["issues"].append("No hay datos XBRL US-GAAP conciliados; IFRS/regulador local pendiente")
        return record
    record["secCik"]=sec["cik"]
    try:
        sector,sic,official_name=sec_sector(sec["cik"])
        record["sectorClass"]=sector;record["sic"]=sic
        record["officialIssuerName"]=official_name
        financials,uri=annual_from_sec(ticker,sec["cik"])
        record["financials"]=financials
        record["fundamentalSource"]=uri
        record["sourceType"]="SEC US-GAAP reported 10-K"
        v=scenario_sec(financials,q,sector)
        record["valuation"]=v
        record["researchStatus"]=v["status"]
        if v["status"]!="indicative_research_only":record["issues"].append(v.get("reason","Model not available"))
    except Exception as exc:
        record["researchStatus"]="sec_temporarily_unavailable"
        record["issues"].append("SEC sin respuesta / no comparable: "+str(exc)[:155])
    return record

def load_json(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:return default

def resolve_input(args):
    if args.ticker:
        return ticker_clean(args.ticker)
    if args.from_event:
        path=os.environ.get("GITHUB_EVENT_PATH")
        if not path:raise ValueError("Falta evento GitHub")
        obj=json.loads(Path(path).read_text())
        body=obj.get("issue",{}).get("body","")
        match=re.search(r"###\s+Ticker\s+de\s+Yahoo\s+Finance\s*\r?\n+\s*([A-Za-z0-9.\-]{1,20})",body,re.IGNORECASE)
        if not match:raise ValueError("La solicitud no contiene un ticker válido en el formulario")
        return ticker_clean(match.group(1))
    return None

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--ticker",default=None)
    pa.add_argument("--from-event",action="store_true")
    pa.add_argument("--refresh",action="store_true")
    args=pa.parse_args()
    new=resolve_input(args)
    registry=load_json(REGISTRY,{"schema":"qvr-universal-registry-v1","companies":{}})
    output=load_json(RESULT,{"schema":"qvr-universal-results-v1","companies":{}})
    if registry.get("schema")!="qvr-universal-registry-v1":raise ValueError("Unsupported registry")
    if output.get("schema")!="qvr-universal-results-v1":raise ValueError("Unsupported results")
    names=list(registry.get("companies",{}))
    if new and new not in names:names.append(new)
    if not names:
        print("Registry empty. No new tickers.");return
    # One SEC directory fetch per batch. Failed access does not fabricate data.
    try:secmap=sec_directory()
    except Exception as exc:
        secmap={}
        print("WARN SEC index unavailable:",str(exc)[:140],file=sys.stderr)
    updated=[]
    for symbol in names:
        try:
            rec=research(symbol,secmap)
            output["companies"][symbol]=rec
            registry["companies"][symbol]={"name":rec["name"],"currency":rec["currency"],
                "firstAddedAt":registry.get("companies",{}).get(symbol,{}).get("firstAddedAt",NOW.isoformat()),
                "instrumentType":rec["instrumentType"],"exchangeName":rec["exchangeName"]}
            updated.append(symbol)
            print(symbol,rec["researchStatus"])
        except Exception as exc:
            print("WARN",symbol,str(exc)[:160],file=sys.stderr)
            if symbol==new:raise
            if symbol in output["companies"]:
                output["companies"][symbol]["refreshFailure"]={"at":NOW.isoformat(),"reason":str(exc)[:140]}
        time.sleep(.16)
    registry["updatedAt"]=NOW.isoformat()
    output["generatedAt"]=NOW.isoformat()
    output["count"]=len(output["companies"])
    output["methodology"]="Official SEC US-GAAP when provided; global equities with no standardized official filings remain quote-only"
    output["purchasesEnabled"]=False
    # Atomic replace in Actions workspace
    REGISTRY.write_text(json.dumps(registry,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    RESULT.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Updated",len(updated),"registry",len(registry["companies"]))

if __name__=="__main__":main()
