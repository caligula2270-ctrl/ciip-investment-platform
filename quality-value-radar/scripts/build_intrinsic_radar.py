#!/usr/bin/env python3
"""Quality & Value Radar: SEC filing-based valuation research, not advice.

US GAAP Form 10-K, historical split-adjusted daily prices and documented
model assumptions. Never fabricate metrics when sources fail.
No third-party Python dependencies. Requires SEC_USER_AGENT (real contact).
"""
from __future__ import annotations
import csv
import datetime as dt
import gzip
import json
import math
import os
import pathlib
import statistics
import sys
import time
import urllib.parse
import urllib.request
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "intrinsic.json"
AGENT = os.environ.get("SEC_USER_AGENT", "").strip()
US = ["CPRT", "AMZN", "COST", "ADBE", "AAON", "DE", "DHR", "FIVE", "FOUR",
      "FRPH", "INTU", "KEYS", "MEDP", "RMD", "TXN", "ZTS"]
# Insurers, banks, financial services and foreign 20-F/IFRS issuers require a
# DIFFERENT financial model; explicitly exclude rather than mislead.
EXCLUDED = {
    "KNSL": "Aseguradora: evaluar combined ratio, reservas, float y ROE; DCF industrial no aplicable.",
    "TRUP": "Aseguradora: las primas y provisiones requieren valoración sectorial.",
    "ASML": "Emisor extranjero: pendiente normalización IFRS / 20-F.",
    "STVN": "Emisor extranjero: pendiente normalización IFRS / 20-F.",
    "GLNG": "Emisor extranjero: pendiente normalización IFRS / 20-F.",
}
TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "ebit": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "eps": ["EarningsPerShareDiluted"],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "equity": ["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "debt_long": ["LongTermDebtNoncurrent","LongTermDebt"],
    "debt_current": ["LongTermDebtCurrent","LongTermDebtAndCapitalLeaseObligationsCurrent"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
}
UNITS = {"eps":"USD/shares","diluted_shares":"shares"}
INSTANTS = {"equity","debt_long","debt_current","cash"}
SOURCE_SEC = "https://www.sec.gov"
SOURCE_STOOQ = "https://stooq.com/q/d/l/"
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date()

def fetch_json(url, agent=AGENT, timeout=30):
    req=urllib.request.Request(url,headers={
        "User-Agent":agent, "Accept":"application/json, */*",
        "Accept-Encoding":"gzip, deflate"})
    with urllib.request.urlopen(req,timeout=timeout) as res:
        body=res.read()
        encoding=res.headers.get("Content-Encoding","").lower()
    if body[:2] == b"\x1f\x8b" or encoding=="gzip": body=gzip.decompress(body)
    elif encoding=="deflate":
        try:body=zlib.decompress(body)
        except zlib.error:body=zlib.decompress(body,-zlib.MAX_WBITS)
    return json.loads(body.decode("utf-8-sig"))

def annual_series(facts, tag_names, units="USD", instant=False):
    """Comparable fiscal-year-end dates. Annual duration 330-390 days only."""
    result={}
    for priority,tag in enumerate(tag_names):
        entries=facts.get("us-gaap",{}).get(tag,{}).get("units",{}).get(units,[])
        for x in entries:
            try:
                if x.get("form") not in ("10-K","10-K/A") or not x.get("filed"):continue
                end=dt.date.fromisoformat(x["end"]);filed=dt.date.fromisoformat(x["filed"])
                if filed>TODAY or end>TODAY or (TODAY-end).days>2300:continue
                if instant:
                    if x.get("start"):continue
                else:
                    start=dt.date.fromisoformat(x["start"])
                    if not 330 <= (end-start).days <= 390:continue
                if not math.isfinite(float(x["val"])):continue
                score=(filed.toordinal(),-priority)
                k=end.isoformat()
                if k not in result or score>result[k][0]:
                    result[k]=(score,{"value":float(x["val"]),"end":k,"filed":str(filed),"tag":tag,
                                       "form":x["form"],"unit":units,
                                       "accession":x.get("accn")})
            except (KeyError,ValueError,TypeError,OverflowError):pass
    return {k:r[1] for k,r in result.items()}

def series(facts,key):
    return annual_series(facts,TAGS[key],UNITS.get(key,"USD"),key in INSTANTS)

def asof_value(series_by_end,end,max_days=110):
    """Balance sheet must be aligned to fiscal year end, never taken from future."""
    try:
        exact=series_by_end.get(end)
        if exact:return exact["value"]
        end_date=dt.date.fromisoformat(end)
        options=[(abs((dt.date.fromisoformat(k)-end_date).days),v["value"])
                 for k,v in series_by_end.items()
                 if abs((dt.date.fromisoformat(k)-end_date).days)<=max_days]
        return min(options)[1] if options else None
    except ValueError:return None

def fetch_prices(ticker):
    """Yahoo chart: historical daily unadjusted for dividends, adjusted for splits."""
    url=("https://query1.finance.yahoo.com/v8/finance/chart/"+
         urllib.parse.quote(ticker)+"?range=5y&interval=1d&events=splits")
    obj=fetch_json(url,"Mozilla/5.0 QualityValueRadar Research/1.0",25)["chart"]["result"][0]
    if obj.get("meta",{}).get("currency") != "USD":
        raise ValueError("Historical price currency not USD")
    rows=list(zip(obj.get("timestamp",[]),
                  obj.get("indicators",{}).get("quote",[{}])[0].get("close",[])))
    daily={}
    for unix,close in rows:
        if close is not None and float(close)>0:
            day=dt.datetime.fromtimestamp(unix,dt.timezone.utc).date()
            daily[day]=float(close)
    splits=[]
    for s in obj.get("events",{}).get("splits",{}).values():
        try:
            ratio=float(s["numerator"])/float(s["denominator"])
            if not 0.01<ratio<100:continue
            splits.append((dt.datetime.fromtimestamp(s["date"],dt.timezone.utc).date(),ratio))
        except (KeyError,ValueError,TypeError):continue
    return daily,splits,url

def split_factor(date,splits):
    f=1.0
    for day,ratio in splits:
        if day>date:f*=ratio
    return f

def closing_near(daily,financial_year_end):
    when=dt.date.fromisoformat(financial_year_end)
    options=[(abs((day-when).days),day,price) for day,price in daily.items()
             if abs((day-when).days)<=9 and day<=TODAY]
    if not options:return None
    _,day,price=min(options)
    return day,price

def clamp(x,low,high):return min(high,max(low,x))

def median(seq):
    vals=[v for v in seq if v is not None and math.isfinite(v)]
    return statistics.median(vals) if vals else None

def dcf(fcf_per_share,growth,discount=.115,terminal=.025,horizon=5):
    if fcf_per_share<=0 or growth<=-1 or discount<=terminal:return None
    stream=sum(fcf_per_share*(1+growth)**t/(1+discount)**t for t in range(1,horizon+1))
    terminal_cash=fcf_per_share*(1+growth)**horizon*(1+terminal)
    perpetuity=terminal_cash/(discount-terminal)/(1+discount)**horizon
    value=stream+perpetuity
    return round(value,2) if 0<value<1e8 else None

def compute(ticker, cik, facts, q, daily, splits, price_url):
    metrics={key:series(facts,key) for key in TAGS}
    ends=sorted(set(metrics["cfo"]) & set(metrics["capex"]) & set(metrics["diluted_shares"]))
    years=[]
    for end in ends:
        cfo=metrics["cfo"][end]["value"];capex=metrics["capex"][end]["value"]
        shares=metrics["diluted_shares"][end]["value"]
        if shares<=0 or cfo<-1e12 or capex<0:continue
        fcf=cfo-capex
        rev=metrics["revenue"].get(end,{}).get("value")
        ebit=metrics["ebit"].get(end,{}).get("value")
        equity=asof_value(metrics["equity"],end)
        debt=(asof_value(metrics["debt_long"],end) or 0)+(asof_value(metrics["debt_current"],end) or 0)
        cash=asof_value(metrics["cash"],end)
        roc=None
        # NO industrial ROIC without reported debt/cash/equity and EBIT;
        # EBIT after an *assumed* 24% effective tax is a ROIC proxy, not audited ROIC.
        if ebit is not None and equity is not None and cash is not None and (metrics["debt_long"] or metrics["debt_current"]):
            invested=equity+debt-cash
            if invested>0 and 0<ebit<1e12:
                roc=100*(ebit*.76)/invested
                if not -100<roc<250:roc=None
        close=closing_near(daily,end)
        multiple=None;sample_date=None
        if close and fcf>0:
            day,close_price=close
            normalized_shares=shares*split_factor(day,splits)
            per_share_at_year=fcf/normalized_shares
            multiple=close_price/per_share_at_year
            if not 0<multiple<200:multiple=None
            sample_date=day.isoformat()
        years.append({"fyEnd":end,"revenue":rev,"cfo":round(cfo,2),"capex":round(capex,2),
                      "fcf":round(fcf,2),"fcfPerShare":round(fcf/shares,4),
                      "shares":round(shares,2),"roicProxyPct":round(roc,2) if roc is not None else None,
                      "historicalPfcf":round(multiple,2) if multiple else None,
                      "historicalPriceDate":sample_date})
    years=years[-6:]
    recent=years[-3:];latest=years[-1] if years else None
    result={"ticker":ticker,"cik":cik,"status":"insufficient","currency":"USD",
            "model":"FCF-to-equity proxy: 5Y DCF + P/FCF historical",
            "source":"SEC XBRL US-GAAP / 10-K; Yahoo daily historical close",
            "sourceUrl":f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            "priceHistoryUrl":price_url,"years":years,
            "assumptions":{"horizonYears":5,"discountRatePct":11.5,"terminalGrowthPct":2.5,
                           "cashTaxAssumptionPct":24,"discountThresholdPct":25},
            "warnings":[]}
    if not latest or len(recent)<3:
        result["reason"]="No hay tres ejercicios comparables con CFO, CAPEX y acciones diluidas"
        return result
    if (TODAY-dt.date.fromisoformat(latest["fyEnd"])).days>520:
        result["reason"]="Último cierre fiscal demasiado antiguo (>520 días)"
        return result
    if len(recent)<3 or sum(1 for y in recent if y["fcf"]>0)<3:
        result["reason"]="FCF negativo o no positivo en alguno de los últimos 3 ejercicios"
        return result
    revs=[y["revenue"] for y in years if y["revenue"] is not None and y["revenue"]>0]
    if len(revs)<3:
        result["reason"]="Faltan ingresos comparables para calibrar crecimiento"
        return result
    rev_start=next(y for y in years if y["revenue"] is not None and y["revenue"]>0)
    rev_end=next(y for y in reversed(years) if y["revenue"] is not None and y["revenue"]>0)
    span=(dt.date.fromisoformat(rev_end["fyEnd"])-dt.date.fromisoformat(rev_start["fyEnd"])).days/365.25
    if span<1.8 or rev_end["revenue"]<=0:
        result["reason"]="No hay historial suficiente para CAGR de ingresos"
        return result
    revenue_cagr=(rev_end["revenue"]/rev_start["revenue"])**(1/span)-1
    fcf_median=median([y["fcfPerShare"] for y in recent])
    if fcf_median is None or fcf_median<=0:
        result["reason"]="FCF por acción normalizado no utilizable"
        return result
    if max(y["fcfPerShare"] for y in recent)>4*min(y["fcfPerShare"] for y in recent):
        result["warnings"].append("FCF muy volátil (>4×); precio objetivo menos fiable")
    normalized=round(fcf_median,4)
    g=clamp(revenue_cagr,0,.12)
    bear=dcf(normalized,max(-.02,g-.05),.13,.02)
    base=dcf(normalized,g,.115,.025)
    bull=dcf(normalized,min(.16,g+.04),.105,.03)
    mult=[y["historicalPfcf"] for y in years if y["historicalPfcf"] is not None]
    historical=round(median(mult),2) if len(mult)>=3 else None
    relative=round(historical*normalized,2) if historical is not None else None
    fair=round(.60*base+.40*relative,2) if (base and relative) else None
    roic=[y["roicProxyPct"] for y in years[-5:] if y["roicProxyPct"] is not None]
    roic_med=round(median(roic),1) if len(roic)>=3 else None
    fcf_positive=sum(1 for y in years[-5:] if y["fcf"]>0)
    latest_debt=(asof_value(metrics["debt_long"],latest["fyEnd"]) or 0)+(asof_value(metrics["debt_current"],latest["fyEnd"]) or 0)
    latest_cash=asof_value(metrics["cash"],latest["fyEnd"])
    latest_fcf=latest["fcf"]
    net_debt_fcf=round((latest_debt-latest_cash)/latest_fcf,2) if latest_cash is not None and latest_fcf>0 and (metrics["debt_long"] or metrics["debt_current"]) else None
    if net_debt_fcf is not None and net_debt_fcf>4:
        result["warnings"].append("Deuda neta / FCF >4×; valorar estructura financiera")
    if roic_med is None:result["warnings"].append("ROIC proxy no disponible; no equivale a ROIC auditado")
    if historical is None:result["warnings"].append("Faltan al menos 3 múltiplos P/FCF históricos comparables")
    if len(recent)<3:result["warnings"].append("Historial corto")
    price=q.get("price") if q and q.get("currency")=="USD" else None
    fresh=q and isinstance(q.get("date"),str) and (TODAY-dt.date.fromisoformat(q["date"])).days<=7
    mos=round(100*(1-price/fair),1) if fair and price is not None and price>0 else None
    # Conservative screen: valuation + quality check; classification is research-only.
    quality=roic_med is not None and roic_med>=15 and fcf_positive>=4 and (net_debt_fcf is None or net_debt_fcf<=4)
    qualifies=bool(fair and historical and quality and fresh and mos is not None and mos>=25)
    result.update({
        "status":"ready" if fair is not None else "incomplete",
        "fiscalEnd":latest["fyEnd"],"revenueCagrPct":round(revenue_cagr*100,2),
        "roicProxyMedianPct":roic_med,"fcfPositiveYears":fcf_positive,"netDebtToFcf":net_debt_fcf,
        "normalizedFcfPerShare":normalized,"historicalPfcfMedian":historical,
        "historicalPfcfSamples":len(mult),"historicalPfcfObservations":[
             {"fiscalEnd":y["fyEnd"],"priceDate":y["historicalPriceDate"],"pfcf":y["historicalPfcf"]}
             for y in years if y["historicalPfcf"] is not None],
        "dcfBear":bear,"dcfBase":base,"dcfBull":bull,
        "valueFromHistoricalMultiple":relative,"fairValue":fair,
        "quote":{"price":price,"currency":"USD","date":q.get("date"),"source":q.get("source")} if price else None,
        "marginOfSafetyPct":mos,"fundamentalQualityGate":quality,
        "classification":"possible_discount" if qualifies else ("needs_review" if fair else "no_model"),
        "assumptions":{**result["assumptions"],"revenueGrowthCapPct":12.0,
                       "baseGrowthPct":round(g*100,2),"bearDiscountPct":13.0,
                       "bullDiscountPct":10.5,"blendedWeightDcfPct":60,
                       "historicalWeightPct":40},
    })
    return result

def main():
    if "@" not in AGENT or len(AGENT)<10:
        raise SystemExit("Set SEC_USER_AGENT as a GitHub Actions repository variable with real contact email.")
    payload={"schema":"qvr-auto-v1","generatedAt":NOW.isoformat(),
             "source":"US SEC companyfacts; historical daily prices from Yahoo Finance",
             "methodology":"Conservative research screen, not a transaction recommendation.",
             "companies":{},"unavailable":{},
             "exclusions":EXCLUDED,
             "coverage":{"eligibleTickers":US,"nonUS":"No financial model without verified comparable IFRS source."}}
    prices_path=ROOT/"data"/"quotes.json"
    quotes=json.loads(prices_path.read_text(encoding="utf-8")).get("quotes",{}) if prices_path.exists() else {}
    mapping=fetch_json("https://www.sec.gov/files/company_tickers.json")
    ciks={str(z["ticker"]).upper():str(z["cik_str"]).zfill(10) for z in mapping.values()}
    complete=0
    previous=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for ticker in US:
        cik=ciks.get(ticker)
        if not cik:
            payload["unavailable"][ticker]="Ticker no localizado en SEC; no se estima su valor"
            continue
        try:
            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            obj=fetch_json(url)
            daily,splits,priceurl=fetch_prices(ticker)
            rec=compute(ticker,cik,obj.get("facts",{}),quotes.get(ticker),daily,splits,priceurl)
            payload["companies"][ticker]=rec
            if rec.get("status")=="ready":complete+=1
            print(ticker,rec.get("status"),rec.get("classification"),len(rec.get("years",[])))
        except Exception as exc:
            payload["unavailable"][ticker]=str(exc)[:180]
            # Never re-stamp stale results with a current date. Keep last
            # usable result individually and flag it as stale/unverified.
            old=previous.get("companies",{}).get(ticker)
            if old:
                old={**old,"status":"stale","classification":"no_model",
                     "reason":"No se pudo actualizar SEC/Yahoo; no usar para clasificar",
                     "marginOfSafetyPct":None}
                payload["companies"][ticker]=old
            print("WARN",ticker,str(exc)[:130],file=sys.stderr)
        time.sleep(.28)
    payload["completed"] = complete
    payload["attempted"] = len(US)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"SEC analysis: {complete}/{len(US)} full models")
    if complete==0:
        print("WARNING: no complete models; the UI must show insufficient coverage.",file=sys.stderr)

if __name__=="__main__":
    main()
