#!/usr/bin/env python3
"""QVR v6: sector-aware, source-labeled valuation + point-in-time research backtest.

Never issues an execution instruction. Prices are dated closes, not live quotes.
SEC history uses only filings already filed on the historical analysis date.
Revenue guides are MANAGEMENT inputs; cash-growth is a MODEL scenario, not consensus.
"""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"data"/"opportunity_v6.json"
AUDIT=ROOT/"data"/"backtest_v6.json"
FOCUS=("ADBE","INTU","CPRT","CSU.TO","ASML","DNP.WA")
NAME={"ADBE":"Adobe","INTU":"Intuit","CPRT":"Copart",
      "CSU.TO":"Constellation Software","ASML":"ASML","DNP.WA":"Dino Polska"}
SECTOR={"ADBE":"software","INTU":"software","CPRT":"marketplace",
        "CSU.TO":"acquisition_led_software","ASML":"capital_equipment","DNP.WA":"store_expansion"}
PARAMS={
 "software":{"discount":.115,"bearMultiple":12,"baseMaxMultiple":26,"bullMultiple":32,"terminal":.025,"gmax":.12},
 "marketplace":{"discount":.115,"bearMultiple":12,"baseMaxMultiple":24,"bullMultiple":30,"terminal":.02,"gmax":.10},
 "acquisition_led_software":{"discount":.135,"bearMultiple":10,"baseMaxMultiple":22,"bullMultiple":30,"terminal":.02,"gmax":.09},
 "capital_equipment":{"discount":.125,"bearMultiple":10,"baseMaxMultiple":21,"bullMultiple":27,"terminal":.025,"gmax":.12},
 "store_expansion":{"discount":.125,"bearMultiple":11,"baseMaxMultiple":23,"bullMultiple":29,"terminal":.025,"gmax":.12},
}
PDATE=dt.datetime.now(dt.timezone.utc)
TODAY=PDATE.date()

def mod(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def clamp(x,lo,hi):return min(hi,max(lo,x))
def med(xs):
    good=[float(x) for x in xs if isinstance(x,(int,float)) and math.isfinite(x)]
    return statistics.median(good) if good else None

def irr(cashflows,initial):
    """Single-investment money-weighted IRR, annual period flows + terminal."""
    if not initial or initial<=0 or not cashflows:return None
    def npv(r):return -initial+sum(v/(1+r)**(i+1) for i,v in enumerate(cashflows))
    lo,hi=-.80,2.0
    if npv(lo)<0 or npv(hi)>0:return None
    for _ in range(90):
        mid=(lo+hi)/2
        if npv(mid)>0:lo=mid
        else:hi=mid
    return round((lo+hi)*50,2)

def scenario(fcf, growth, terminal_multiple, rate, years=5, fade=False):
    if fcf is None or fcf<=0 or rate<=0 or terminal_multiple<=0:return None
    vals=[];cash=fcf
    for t in range(1,years+1):
        g=growth*(.5 if fade and t>5 else 1)
        cash*=1+g
        vals.append(cash)
    terminal=cash*terminal_multiple
    pv=sum(v/(1+rate)**i for i,v in enumerate(vals,1))+terminal/(1+rate)**years
    return {"value":round(pv,2),"terminalPrice":round(terminal,2),
            "yearlyOwnerFcf":[round(v,3) for v in vals]}

def as_int(x):
    try:return int(x)
    except(TypeError,ValueError):return None

def forecast_growth(guidance,latest_revenue,last_end,historical_pct,sector):
    base=clamp((historical_pct or 0)/100,0,PARAMS[sector]["gmax"])
    if not guidance or not latest_revenue or not last_end:
        return base,{"kind":"historical_growth_proxy","source":None,"note":"CAGR revenue, NOT consensus"}
    mid=(guidance["revenueLow"]+guidance["revenueHigh"])/2*1e6
    try:
        fiscal=dt.date.fromisoformat(last_end)
        future=dt.date.fromisoformat(guidance["periodEnd"])
        gap=(future-fiscal).days/365.25
        if not .65<=gap<=2.2:return base,{"kind":"historical_growth_proxy","note":"Guidance period not comparable"}
        guided=max(-.3,(mid/latest_revenue)**(1/gap)-1)
        used=clamp(.6*guided+.4*base,-.03,PARAMS[sector]["gmax"])
        return used,{"kind":"model_derived_from_management_revenue_guidance",
                     "officialRevenueGuideMillions":[guidance["revenueLow"],guidance["revenueHigh"]],
                     "fiscalYear":guidance["fiscalYear"],"sourceUrl":guidance["sourceUrl"],
                     "guidedRevenueAnnualCagrPct":round(guided*100,2),
                     "historicalRevenueCagrPct":round(base*100,2),
                     "note":"Forecast FCF growth is an assumption. Official guidance concerns REVENUE, not FCF."}
    except (ValueError,ZeroDivisionError,KeyError):
        return base,{"kind":"historical_growth_proxy","note":"Insufficient comparable revenue guidance"}

def confidence(has3,quote,guide,roic,split,costknown,forecasts,foreign=False,major=False):
    parts={"cashSeries":25 if has3 else 0,"freshPrice":10 if quote else 0,
        "managementOutlook":12 if guide else 0,"roicComparable":15 if roic else 0,
        "capexVerified":10 if split else 0,"acquisitionEvidence":10 if costknown else 0,
        "independentForwardFcf":13 if forecasts else 0,"issuerComparability":5 if not foreign else 2}
    score=sum(parts.values())
    # Not all companies need material acquisitions; there is no invented
    # realized ROI requirement for an issuer with no material acquisitions.
    if major:score=min(score,49)
    if foreign and not has3:score=min(score,35)
    tier="high" if score>=85 and has3 and quote and split and forecasts and (not major) else (
         "medium" if score>=50 and has3 and quote and not major else "low")
    return score,tier,parts

def score_business(annual,roic,cagr,leverage):
    years=annual[-5:]
    samples=len(years)
    positive=sum(1 for y in years if (y.get("fcf") or 0)>0)
    quality=(round(30*positive/samples) if samples else 0)
    quality+=20 if roic is not None and roic>=20 else (12 if roic is not None and roic>=12 else 0)
    quality+=min(20,round(max(0,cagr or 0)*1.25))
    quality+=15 if leverage is not None and leverage<=2 else (8 if leverage is not None and leverage<=4 else 0)
    quality+=10 if samples>=5 else (5 if samples>=3 else 0)
    return min(100,quality)

def model_us(ticker,row,evidence,policy,quotes):
    sector=SECTOR[ticker];p=PARAMS[sector];owner=(row.get("economicReview") or {}).get("ownerCashFlow") or {}
    quote=quotes.get(ticker);quote_is_fresh=False
    try:
        quote_is_fresh=bool(quote and quote.get("currency")=="USD" and 0<=(TODAY-dt.date.fromisoformat(quote["date"])).days<=7)
    except ValueError:pass
    fy=row.get("years",[]);annual=fy[-3:]
    normalized=owner.get("normalizedOwnerFcfPerShare")
    if not isinstance(normalized,(float,int)) or normalized<=0:normalized=None
    hist=owner.get("historicalOwnerPfcfMedian")
    if not isinstance(hist,(float,int)) or not 0<hist<250:hist=None
    v5=evidence.get("companies",{}).get(ticker,{})
    capex=v5.get("maintenanceGrowthCapex") or []
    verified_capex=bool(capex) and all(c.get("separationStatus")=="issuer_disclosed" for c in capex)
    cohorts=v5.get("acquisitionCohorts") or []
    # A reported acquisition cost alone is NOT proof of ROI, but not
    # automatically a material company-changing event.
    major=ticker=="CPRT" and bool(row.get("modelProFormaStatus")=="not_adjusted" or row.get("materialEvent"))
    roic=(row.get("adjustedRoic") or {}).get("median3yPct")
    y=fy[-1] if fy else {}
    guide=policy.get("officialGuidance",{}).get(ticker)
    growth,basis=forecast_growth(guide,y.get("revenue"),y.get("fyEnd"),row.get("revenueCagrPct"),sector)
    costknown=not major and bool(owner.get("acquisitionHistoryComplete"))
    s,tier,confidenceParts=confidence(
       normalized is not None and len(annual)==3,quote_is_fresh,guide is not None,
       roic is not None,verified_capex,costknown,False,False,major)
    q=round(score_business(fy,roic,row.get("revenueCagrPct"),row.get("netDebtToFcf")),0)
    reasons=[]
    if normalized is None:reasons.append("Owner FCF after SBC unavailable or invalid")
    if hist is None:reasons.append("Historical P/owner-FCF insufficient")
    if not verified_capex:reasons.append("Maintenance/growth CAPEX split not issuer-verified")
    if major:reasons.append("ACV acquisition requires pro-forma cash/debt and target ROI")
    if not guide:reasons.append("No independent company growth guidance in policy")
    if not quote_is_fresh:reasons.append("Last dated quote stale or missing")
    if not (v5.get("forwardCashDerived")):reasons.append("Forward owner FCF not independently verified")
    data={"ticker":ticker,"name":NAME[ticker],"sector":sector,"currency":"USD",
      "confidence":{"tier":tier,"score":s,"components":confidenceParts},
      "qualityScore":q,"price":quote.get("price") if quote else None,
      "quoteDate":quote.get("date") if quote else None,
      "fy":y.get("fyEnd"),"normalizedOwnerFcfPerShare":normalized,
      "historicalPownerFcf":hist,"adjustedRoicPct":roic,
      "growthBasis":basis,"growthAssumptionPct":round(growth*100,2),
      "sourceUrl":row.get("sourceUrl"),"blockers":reasons,
      "valuationLevel":"indicative" if normalized and hist else "insufficient",
      "investmentAction":"research_only","acquisitionMaterialEvent":major}
    if normalized is None or hist is None:return data
    vals={}
    for label,g,mult,rate in [
        ("bear",max(-.05,growth-.055),p["bearMultiple"],p["discount"]+.02),
        ("base",growth,clamp(hist,12,p["baseMaxMultiple"]),p["discount"]),
        ("bull",min(.20,growth+.05),p["bullMultiple"],p["discount"]-.012)]:
        vals[label]=scenario(normalized,g,mult,rate,5)
        if vals[label]:vals[label].update({"growthPct":round(g*100,2),"exitMultiple":round(mult,1),"discountPct":round(rate*100,2)})
    if not all(vals.values()):return data
    base=vals["base"]["value"];bear=vals["bear"]["value"]
    entry=round(min(.75*base,.90*bear),2)
    current=data["price"] if quote_is_fresh else None
    gap=round(100*(entry/current-1),1) if current and current>0 else None
    margin=round(100*(1-current/base),1) if current and current>0 else None
    ten=scenario(normalized,growth,clamp(hist,12,p["baseMaxMultiple"]),p["discount"],10,True)
    irr5=irr(vals["base"]["yearlyOwnerFcf"][:-1]+[
        vals["base"]["yearlyOwnerFcf"][-1]+vals["base"]["terminalPrice"]],current) if current else None
    irr10=irr(ten["yearlyOwnerFcf"][:-1]+[ten["yearlyOwnerFcf"][-1]+ten["terminalPrice"]],current) if current and ten else None
    data.update({"scenarios":vals,"valueRange":[vals["bear"]["value"],vals["bull"]["value"]],
      "baseValue":base,"entryPrice":entry,"priceToEntryGapPct":gap,
      "marginVsBasePct":margin,"tenYearIndicativePv":ten["value"] if ten else None,
      "projectedIrrPct":{"fiveYear":irr5,"tenYear":irr10},
      "valuationLevel":"indicative","valuationMethod":"Equity owner-FCF per share; DCF + historically capped P/owner-FCF exit; no balance-sheet EV bridge",
      "warnings":["Historic FCF and SBC may not reflect future acquisition returns, working capital or AI competition",
                  "Exit P/FCF is an assumption, NOT the price to which a historical multiple must revert",
                  "Projections keep diluted share basis constant; future dilution must be audited"]})
    # A medium-tier valuation can flag RESEARCH only, NEVER buy approval.
    data["investmentAction"]="watch_price_for_due_diligence" if tier in ("high","medium") and current is not None and current<=entry else "research_only"
    if major:data["investmentAction"]="research_only"
    return data

def model_intl(ticker,entry,evidence,quotes):
    sector=SECTOR[ticker];v=entry.get("valuation") or {};q=quotes.get(ticker)
    price=q.get("price") if q else None
    fresh=False
    try:fresh=bool(q and q.get("currency")==v.get("tradingCurrency") and 0<=(TODAY-dt.date.fromisoformat(q["date"])).days<=7)
    except ValueError:pass
    fcf=v.get("normalizedFcfPerShare")
    if not isinstance(fcf,(int,float)) or fcf<=0:fcf=None
    # International FCFA2S is explicitly before acquisitive reinvestment.
    scores,tier,parts=confidence(bool(fcf),fresh,False,False,False,False,False,True,ticker=="CSU.TO")
    data={"ticker":ticker,"name":NAME[ticker],"sector":sector,"currency":v.get("tradingCurrency") or "",
       "confidence":{"score":scores,"tier":tier,"components":parts},
       "qualityScore":None,"quoteDate":q.get("date") if q else None,"price":price,
       "valuationLevel":"preliminary","investmentAction":"research_only",
       "sourceUrl":entry.get("sourceUrl"),"blockers":[
           "Historical P/owner-FCF comparison not split/currency reconciled",
           "Maintenance vs growth CAPEX not independently audited",
           "Cash return on acquisition/growth CAPEX not separately established",
           "Management and independent forward owner FCF not reconciled"],
       "growthBasis":{"kind":"issuer_historical_scenario_not_consensus"}}
    if v.get("status")!="preliminary":data["valuationLevel"]="insufficient";return data
    data["scenarios"]={x:{"value":v[x]} for x in ("bear","base","bull") if v.get(x)}
    base=v.get("base");bear=v.get("bear")
    if base and bear:
        data["baseValue"]=base
        data["entryPrice"]=round(min(.75*base,.90*bear),2)
        data["marginVsBasePct"]=round(100*(1-price/base),1) if price and fresh else None
        data["priceToEntryGapPct"]=round(100*(data["entryPrice"]/price-1),1) if price and fresh else None
        data["warnings"]=[v.get("warning",""),"Entry threshold illustrative, not a recommendation",
         "5Y/10Y IRRs withheld: acquisition economics, owner FCF and share bases not yet reconciled"]
    return data

def build():
    fundamentals=json.loads((ROOT/"data"/"intrinsic.json").read_text())
    evidence=json.loads((ROOT/"data"/"reliability_v5.json").read_text())
    intl=json.loads((ROOT/"data"/"international.json").read_text())
    quotes=json.loads((ROOT/"data"/"quotes.json").read_text()).get("quotes",{})
    policy=json.loads((ROOT/"data"/"reliability_policy.json").read_text())
    models={}
    for t in ("ADBE","INTU","CPRT"):
        models[t]=model_us(t,fundamentals["companies"].get(t,{}),evidence,policy,quotes)
    for t in ("CSU.TO","ASML","DNP.WA"):
        models[t]=model_intl(t,intl["companies"].get(t,{}),evidence,quotes)
    # Other names are research backlog, not ranked as cheap without models.
    pending={t:{"ticker":t,"valuationLevel":"not_modeled","reason":"Await sector-appropriate owner's cash flow model"}
             for t in fundamentals.get("companies",{}) if t not in models}
    ranking=sorted(models,key=lambda t:(models[t]["confidence"]["score"],
              models[t].get("qualityScore") or 0,models[t].get("marginVsBasePct") or -100),reverse=True)
    result={"schema":"qvr-v6","generatedAt":PDATE.isoformat(),"asOf":str(TODAY),"focus":list(FOCUS),
         "models":models,"coverageBacklog":pending,"researchRank":ranking,
         "researchOnly":True,"transactionSignals":False,
         "methodology":{"horizonYears":[5,10],"cash":"CFO - PPE capex - reported SBC, median three FY",
             "growth":"Verified issuer revenue guidance used only as one growth input, never consensus FCF",
             "entry":"MIN(75% base PV, 90% downside PV) using explicit cash and exit-multiple scenarios",
             "irr":"Modeled annual owner cash payouts plus estimated terminal exit; not guaranteed return",
             "confidence":"Evidence tier, not analyst conviction or probability of correctness",
             "history":"Point-in-time historical filings only; excludes future facts and forward guidance",
             "caveats":"No independent forward FCF consensus, maintenance CAPEX split or acquisition ROIC proven."}}
    PATH.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    return result

def backtest_one(ticker, asof, base):
    """Historical research replay: only 10-K facts FILED no later than asof."""
    cik=base.get("cik")
    if not cik:return {"ticker":ticker,"status":"unavailable","reason":"SEC CIK missing"}
    impl=mod("qvr_base","build_intrinsic_radar.py")
    if "@" not in impl.AGENT:return {"ticker":ticker,"status":"unavailable","reason":"SEC identity missing"}
    try:
        fact=impl.fetch_json("https://data.sec.gov/api/xbrl/companyfacts/CIK"+str(cik)+".json")["facts"]
        # 10-year daily closes, avoiding the rolling five-year window truncation.
        link="https://query1.finance.yahoo.com/v8/finance/chart/"+ticker+"?range=10y&interval=1d&events=splits"
        obj=impl.fetch_json(link,"Mozilla/5.0 QVR-Historical/1.0",25)["chart"]["result"][0]
        daily={}
        for unix,px in zip(obj.get("timestamp",[]),obj.get("indicators",{}).get("quote",[{}])[0].get("close",[])):
            if px is not None and px>0:
                daily[dt.datetime.fromtimestamp(unix,dt.timezone.utc).date()]=float(px)
        splits=[]
        for x in obj.get("events",{}).get("splits",{}).values():
            try:
                ratio=float(x["numerator"])/float(x["denominator"])
                if .01<ratio<100:splits.append((dt.datetime.fromtimestamp(x["date"],dt.timezone.utc).date(),ratio))
            except (KeyError,TypeError,ValueError):pass
    except Exception as exc:
        return {"ticker":ticker,"status":"unavailable","reason":"Historical source failure: "+str(exc)[:130]}
    # Need a FULL historical sample including as-of date before calculating a backtest.
    if min(daily,default=TODAY)>asof-dt.timedelta(days=25):
        return {"ticker":ticker,"status":"insufficient_price_history",
                "reason":"Historical quote series does not reach the 2021 cutoff; no return calculated",
                "neededAsOf":str(asof),"sourceUrl":link}
    # Full point-in-time companyfacts remains fetched but if prices unavailable,
    # historical annual numbers are not used in any future-looking result.
    cutoff=str(asof)
    names={"cfo":["NetCashProvidedByUsedInOperatingActivities"],
      "capex":["PaymentsToAcquirePropertyPlantAndEquipment"],
      "sbc":["ShareBasedCompensation"],
      "shares":["WeightedAverageNumberOfDilutedSharesOutstanding"]}
    years={}
    for key,tags in names.items():
        rows=[]
        for tag in tags:
            u="shares" if key=="shares" else "USD"
            for o in fact.get("us-gaap",{}).get(tag,{}).get("units",{}).get(u,[]):
                try:
                    if o.get("form") not in ("10-K","10-K/A") or o["filed"]>cutoff:continue
                    end=dt.date.fromisoformat(o["end"]);start=dt.date.fromisoformat(o["start"])
                    if end>asof or not 330<=(end-start).days<=390:continue
                    rows.append((str(end),o["filed"],float(o["val"])))
                except (ValueError,TypeError,KeyError):continue
        d={}
        for end,filed,v in sorted(rows,key=lambda y:y[1]):
            d[end]=(filed,v)
        years[key]=d
    common=sorted(set.intersection(*(set(v) for v in years.values())))
    points=[]
    for end in common:
        v={k:years[k][end][1] for k in names}
        if v["shares"]<=0 or v["capex"]<0:continue
        cash=v["cfo"]-v["capex"]-v["sbc"]
        if cash<=0:continue
        day=dt.date.fromisoformat(end)
        factor=impl.split_factor(day,splits)
        if factor<=0:continue
        fcfps=cash/(v["shares"]*factor)
        px=impl.closing_near({day:p for day,p in daily.items() if day<=asof},end)
        multiple=px[1]/fcfps if px and fcfps>0 else None
        points.append({"fy":end,"filingDate":max(years[k][end][0] for k in names),
                       "ownerFcfPerShare":fcfps,"histPowner":multiple,
                       "historicalQuote":str(px[0]) if px else None})
    points=points[-3:]
    start_trade=max(((d,p) for d,p in daily.items() if d<=asof),default=None)
    if len(points)<3 or not start_trade:
        return {"ticker":ticker,"status":"insufficient_asof_data","asOf":cutoff,"availableFY":len(points)}
    norm=med([x["ownerFcfPerShare"] for x in points])
    mult=med([x["histPowner"] for x in points])
    if not norm or not mult:
        return {"ticker":ticker,"status":"insufficient_historical_multiples","asOf":cutoff,
                "source":"Only filings dated before historical cutoff considered"}
    params=PARAMS[SECTOR[ticker]]
    baseVal=scenario(norm,.06,clamp(mult,12,params["baseMaxMultiple"]),params["discount"])
    bearVal=scenario(norm,.005,params["bearMultiple"],params["discount"]+.02)
    entry=round(min(.75*baseVal["value"],.9*bearVal["value"]),2)
    current=base.get("quote",{}).get("price")
    end_date=base.get("quote",{}).get("date")
    if not current or not end_date:return {"ticker":ticker,"status":"no_exit_quote"}
    elapsed=(dt.date.fromisoformat(end_date)-start_trade[0]).days/365.25
    if elapsed<=0:return {"ticker":ticker,"status":"invalid_horizon"}
    actual=(current/start_trade[1])**(1/elapsed)-1
    return {"ticker":ticker,"status":"measured","asOf":cutoff,"startQuoteDate":str(start_trade[0]),
       "startPriceSplitAdjusted":round(start_trade[1],2),"historicalFairValue":baseVal["value"],
       "historicalEntryPrice":entry,"wouldFlagForResearch":start_trade[1]<=entry,
       "exitQuoteDate":end_date,"exitPriceSplitAdjusted":current,
       "priceOnlyAnnualReturnPct":round(actual*100,2),"years":round(elapsed,2),
       "financialFY":[x["fy"] for x in points],
       "filingsAtOrBeforeAsOf":all(x["filingDate"]<=cutoff for x in points),
       "lookaheadChecked":True,
       "warnings":["Not a randomized universe: retrospective selection/survivorship bias",
          "Split-adjusted closing prices; does not include dividends or trading frictions",
          "No retrospective guidance is used; historical model uses constant 6% forward growth"]}

def backtest(models, fundamentals):
    # A deliberately narrow exact historical test, not a false claim of
    # multi-year strategy performance.
    asof=dt.date(2021,10,25)
    entries={}
    if os.getenv("QVR_RUN_BACKTEST","1")=="0":
        for ticker in ("ADBE","INTU","CPRT"):
            entries[ticker]={"ticker":ticker,"status":"not_run","reason":"Backtest disabled"}
    else:
        for ticker in ("ADBE","INTU","CPRT"):
            entries[ticker]=backtest_one(ticker,asof,fundamentals.get("companies",{}).get(ticker,{}))
    measured=[v for v in entries.values() if v["status"]=="measured"]
    obj={"schema":"qvr-pit-backtest-v6","generatedAt":PDATE.isoformat(),
        "historicalResearchAsOf":str(asof),"tickers":entries,
        "measuredCount":len(measured),"requestedCount":3,"strategyPerformanceClaim":False,
        "dataIntegrity":"No point-in-time price/SEC filings = NO backtest rather than a fabricated result",
        "limitations":["Three preselected present-day companies are not a valid representative backtest",
            "No historical portfolio weights, fees, tax, dividends, survivorship or benchmark",
            "Lookahead only checked for form filing dates and historical prices, not all accounting revisions"]}
    AUDIT.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    return obj

def main():
    result=build()
    fundamentals=json.loads((ROOT/"data"/"intrinsic.json").read_text())
    history=backtest(result,fundamentals)
    print("QVR6:",len(result["models"]),"models, tiers:",
         {k:sum(x["confidence"]["tier"]==k for x in result["models"].values()) for k in ("high","medium","low")},
         "backtest measured:",history["measuredCount"])
    # Assertions: a pricing candidate cannot be an investment order;
    # category names make low-credibility estimates unambiguous.
    assert all(x["investmentAction"] in ("research_only","watch_price_for_due_diligence")
               for x in result["models"].values())
    assert not result["transactionSignals"]

if __name__=="__main__":
    main()
