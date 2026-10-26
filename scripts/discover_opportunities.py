#!/usr/bin/env python3
"""Rotating US issuer discovery + source-gated research triage.

prepare: expand beyond any hard-coded ticker list using SEC listing/CIK data.
rank: evaluate the new names AFTER the ordinary SEC fundamentals ingestion.
No price target, no 13F current-position claim, no automated trading.
"""
from __future__ import annotations
import argparse
import datetime as dt
import gzip
import json
import math
import os
import pathlib
import re
import time
import urllib.request
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
DIR=ROOT/"discovery"
QUEUE=DIR/"queue.json"
STATE=DIR/"state.json"
RADAR=DIR/"radar.json"
TICKER_RE=re.compile(r"^[A-Z][A-Z0-9.\-]{0,11}$")
EXCHANGES={"Nasdaq","NYSE","NYSE American","NASDAQ","New York Stock Exchange"}
FUND_WORDS=(" ETF"," ETF "," EXCHANGE TRADED"," FUND"," TRUST"," ETN"," SPDR"," ISHARES"," PROSHARES"," ACQUISITION CORP"," ACQUISITION CO"," SPAC ")
STAGES={"RESEARCH_PRIORITY","WATCHLIST","SPECIALIST_REVIEW","INSUFFICIENT_DATA"}
MAX_PER_RUN=36
REVISIT_DAYS=120

def read(path,default):
    if not path.exists():return default
    return json.loads(path.read_text(encoding="utf-8"))

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def fetch_json(url,agent):
    if not agent or "@" not in agent:
        raise ValueError("SEC_USER_AGENT with genuine contact email required")
    req=urllib.request.Request(url,headers={"User-Agent":agent,"Accept":"application/json",
                                            "Accept-Encoding":"gzip, deflate"})
    with urllib.request.urlopen(req,timeout=35) as response:
        raw=response.read()
        encoding=response.headers.get("Content-Encoding","").lower()
    if raw[:2]==b"\x1f\x8b" or encoding=="gzip":raw=gzip.decompress(raw)
    elif encoding=="deflate":
        try:raw=zlib.decompress(raw)
        except zlib.error:raw=zlib.decompress(raw,-zlib.MAX_WBITS)
    return json.loads(raw.decode("utf-8-sig"))

def normalize_listing(data):
    """SEC exchange association file is a [fields, data] columnar table.
    Accept also SEC company_tickers.json in test fixtures.
    """
    if isinstance(data,dict) and isinstance(data.get("fields"),list) and isinstance(data.get("data"),list):
        rows=[dict(zip(data["fields"],values)) for values in data["data"]]
    elif isinstance(data,dict):
        rows=[v for v in data.values() if isinstance(v,dict)]
    else:raise ValueError("Unexpected SEC ticker mapping format")
    candidates=[]
    seen=set()
    for x in rows:
        ticker=str(x.get("ticker") or "").strip().upper()
        name=str(x.get("name") or x.get("title") or "").strip()
        exchange=str(x.get("exchange") or "unverified").strip()
        cik=x.get("cik") if "cik" in x else x.get("cik_str")
        try:cik=int(cik)
        except (ValueError,TypeError):continue
        if cik<=0 or not TICKER_RE.fullmatch(ticker):continue
        if exchange!="unverified" and exchange not in EXCHANGES:continue
        upper=" "+name.upper()+" "
        if any(term in upper for term in FUND_WORDS):continue
        if (ticker,cik) in seen:continue
        seen.add((ticker,cik))
        candidates.append({"ticker":ticker,"cik":str(cik).zfill(10),"name":name,
                           "exchange":exchange})
    # Different share classes of a single issuer should not waste scarce requests.
    # Prefer plain common tickers over dot- or hyphen-suffixed share classes.
    by_cik={}
    for x in sorted(candidates,key=lambda x:("." in x["ticker"] or "-" in x["ticker"],len(x["ticker"]),x["ticker"])):
        by_cik.setdefault(x["cik"],x)
    return sorted(by_cik.values(),key=lambda x:x["ticker"])

def historical_13f_mentions(master):
    """User's dated historical holdings; NO claim that old 13F is current."""
    found={}
    for h in master.get("03_HOLDINGS",[]):
        ticker=str(h.get("Ticker") or "").strip().upper()
        if not TICKER_RE.fullmatch(ticker):continue
        date=str(h.get("Fecha_corte") or "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):continue
        if not str(h.get("Tipo_aparición") or "").upper().startswith("OF-13F"):continue
        g=str(h.get("Guru_ID") or "")
        row=found.setdefault(ticker,{"counted_managers":set(),"latest_quarter":date,
                                     "source_urls":set()})
        row["counted_managers"].add(g)
        row["latest_quarter"]=max(row["latest_quarter"],date)
        if str(h.get("Fuente_URL") or "").startswith("https://"):
            row["source_urls"].add(h["Fuente_URL"])
    return {t:{"manager_count_historical":len(v["counted_managers"]),
               "latest_reported_holdings_date":v["latest_quarter"],
               "reference_urls":sorted(v["source_urls"])[:4],
               "status":"historical_snapshot_not_current_13f"}
            for t,v in found.items()}

def choose_queue(listings,prior_mentions,prior_state,today,existing=(),limit=MAX_PER_RUN):
    """Bounded, repeatable rotating scanner with an explicit review budget."""
    if limit<1:raise ValueError("positive scan budget needed")
    tracked=prior_state.get("last_scanned",{})
    known=set(existing)
    eligible={p["ticker"]:p for p in listings if p["ticker"] not in known}
    stale_threshold=today-dt.timedelta(days=REVISIT_DAYS)
    def due(p):
        last=tracked.get(p["cik"])
        if not last:return True
        try:return dt.date.fromisoformat(last)<=stale_threshold
        except ValueError:return True
    selected=[]
    for ticker,_ in sorted(prior_mentions.items(),key=lambda item:(-item[1]["manager_count_historical"],item[0])):
        row=eligible.get(ticker)
        if row and due(row) and len(selected)<min(limit,12):
            selected.append(row)
    chosen={x["cik"] for x in selected}
    sorted_rows=sorted(listings,key=lambda x:x["ticker"])
    cursor=int(prior_state.get("cursor",0))%max(1,len(sorted_rows))
    traversed=0
    while len(selected)<limit and traversed<len(sorted_rows):
        p=sorted_rows[(cursor+traversed)%len(sorted_rows)]
        traversed+=1
        if p["cik"] in chosen or p["ticker"] in known or not due(p):continue
        selected.append(p)
        chosen.add(p["cik"])
    next_cursor=(cursor+traversed)%max(1,len(sorted_rows))
    return selected,next_cursor

def prepare(today,listing_doc,master,state,base_tickers=(),limit=MAX_PER_RUN):
    listings=normalize_listing(listing_doc)
    if not listings:raise ValueError("SEC mapping empty; preserving previous scan")
    mentions=historical_13f_mentions(master)
    selected,cursor=choose_queue(listings,mentions,state,today,base_tickers,limit)
    result={"schema":"ciip-discovery-queue-v1","generated_on":today.isoformat(),
            "source":"https://www.sec.gov/files/company_tickers_exchange.json",
            "listed_issuer_count":len(listings),"scan_budget":limit,
            "selection_method":"dated_13f_leads_then_rotating_sec_list",
            "no_universe_completeness_claim":True,
            "candidates":[dict(row,seed_reason="historical_13f" if row["ticker"] in mentions else "rotation",
                     historical_13f=mentions.get(row["ticker"])) for row in selected]}
    next_state={"schema":"ciip-discovery-state-v1","cursor":cursor,
                "last_scanned":dict(state.get("last_scanned",{})),
                "as_of":today.isoformat(),"listed_issuer_count":len(listings)}
    # Mark candidates after SEC extraction, not when only selected.
    return result,next_state

def metric(row,key):
    x=row.get("metrics",{}).get(key)
    v=x.get("value") if isinstance(x,dict) else None
    return float(v) if isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) else None

def provisional_sic_bucket(sic):
    """SEC SIC gives a cautious sector ROUTE, not a verified moat or DCF model."""
    try:n=int(sic)
    except (TypeError,ValueError):return "unclassified"
    if 6000 <= n < 6800:return "financial_specialist"
    if 6300 <= n < 6400:return "insurance_specialist"
    if 6500 <= n < 6600:return "real_estate_specialist"
    if 2830 <= n <= 2839:return "pharma_specialist"
    if 7370 <= n <= 7379:return "software_candidate"
    if 3500 <= n < 3700:return "manufacturing_specialist"
    if 4800 <= n < 4900:return "telecom_specialist"
    if 5000 <= n < 6000:return "distribution_specialist"
    if 7000 <= n < 7300:return "service_specialist"
    if 7300 <= n < 7400:return "service_specialist"
    if 2000 <= n < 4000:return "industrial_specialist"
    return "unclassified"

def evaluate(q,company,today):
    record={"ticker":q["ticker"],"cik":q["cik"],"name":q["name"],
            "exchange":q.get("exchange"),"detected_at":today.isoformat(),
            "origin":q["seed_reason"],"historical_13f":q.get("historical_13f"),
            "decision_ready":False,"price_target_usd":None,"investment_signal":None,
            "price_data_verified":False,"evidence":[],
            "quality_score_screen":None,"status":"INSUFFICIENT_DATA",
            "limitations":[],"metrics":{}}
    if not company:
        record["limitations"].append("SEC XBRL companyfacts not downloaded or unavailable")
        return record
    if company.get("cik")!=q["cik"]:
        record["limitations"].append("Ticker-CIK identity mismatch")
        return record
    quality=company.get("history_quality",{})
    history=company.get("history",[])
    latest=history[-1] if history else {}
    net=metric(latest,"net_income");rev=metric(latest,"revenue")
    op=metric(latest,"operating_income");cfo=metric(latest,"operating_cash_flow")
    fcf=latest.get("fcf_usd")
    cagr=quality.get("revenue_cagr_pct")
    positive=sum(1 for row in history if isinstance(row.get("fcf_usd"),(int,float)) and row["fcf_usd"]>0)
    record["evidence"].append(company.get("url"))
    record["metrics"]={"fiscal_year_end":latest.get("fy_end"),
                       "revenue_cagr_pct":round(cagr,2) if isinstance(cagr,(int,float)) else None,
                       "operating_margin_pct":round(100*op/rev,2) if rev and rev>0 and op is not None else None,
                       "net_margin_pct":round(100*net/rev,2) if rev and rev>0 and net is not None else None,
                       "fcf_positive_years":positive,"years_available":len(history),
                       "normalized_3y_fcf_usd":quality.get("normalized_fcf_3y_usd")}
    gate=company.get("sector_control",{})
    sector=gate.get("profile","unclassified")
    if sector=="unclassified":sector=provisional_sic_bucket(company.get("sic"))
    record["sector_profile"]=sector
    record["sic"]=company.get("sic")
    record["sic_description"]=company.get("sic_description")
    if gate.get("profile")=="unclassified" and sector!="unclassified":
        record["limitations"].append("SIC sector classification provisional; specialist model not audited")
    record["sector_model_status"]=company.get("sector_valuation",{}).get("status","not_applicable")
    if len(history)<3 or fcf is None or cagr is None or rev is None or net is None or op is None or cfo is None:
        record["limitations"].append("Incomparable/incomplete annual 10-K metrics")
        return record
    if quality.get("latest_fy_age_days") is None or quality["latest_fy_age_days"]>520:
        record["limitations"].append("Stale annual audited period")
        return record
    # All thresholds transparent heuristics for research PRIORITY, not expected returns.
    score=0
    score+=min(30,max(0,positive)*6)
    score+=20 if op/rev>=.20 else 14 if op/rev>=.10 else 7 if op/rev>0 else 0
    score+=15 if cfo>=net>0 else 7 if cfo>0 and net>0 else 0
    score+=15 if cagr>=10 else 10 if cagr>=5 else 5 if cagr>0 else 0
    score+=10 if fcf>0 and cfo>0 and fcf/cfo>=.50 else 5 if fcf>0 else 0
    score+=10 if quality.get("normalized_fcf_3y_usd") is not None else 0
    record["quality_score_screen"]=score
    if gate.get("status")=="blocked" and sector=="unclassified" or record["sector_profile"] in (
        "unclassified","insurer","real_estate","foreign_special","mixed_operations","payment_network","energy",
        "financial_specialist","insurance_specialist","real_estate_specialist","pharma_specialist") or sector.endswith("_specialist"):
        record["status"]="SPECIALIST_REVIEW"
        record["limitations"].append("Sector-specific accounting and valuation model not yet validated")
    elif score>=70:
        record["status"]="RESEARCH_PRIORITY"
        record["limitations"].append("Priority to research only; no sector DCF approved")
    else:
        record["status"]="WATCHLIST"
    if company.get("share_reconciliation",{}).get("status")!="provisional_reconciled":
        record["limitations"].append("Current diluted share capital not reconciled")
    record["limitations"].append("No checked live price, intrinsic value, debt/cash bridge or forecast")
    return record

def rank(queue,sec,previous,today):
    entries={p["ticker"]:p for p in previous.get("companies",[])}
    candidates=queue.get("candidates",[])
    seen=[]
    for q in candidates:
        c=sec.get("companies",{}).get(q["ticker"])
        row=evaluate(q,c,today)
        entries[q["ticker"]]=row
        if c:seen.append(q["cik"])
    sorted_entries=sorted(entries.values(),key=lambda x:(
        {"RESEARCH_PRIORITY":0,"WATCHLIST":1,"SPECIALIST_REVIEW":2,"INSUFFICIENT_DATA":3}.get(x["status"],4),
        -(x.get("quality_score_screen") or 0),x["ticker"]))
    return {"schema":"ciip-automatic-discovery-radar-v1",
            "generated_on":today.isoformat(),
            "total_unique_candidates_seen":len(entries),
            "last_batch_size":len(candidates),
            "last_batch_sec_downloaded":len(seen),
            "readiness":"RESEARCH_SCREEN_ONLY_NOT_RECOMMENDATIONS",
            "scope":"SEC-listed US equity issuers, rotating incremental sampling",
            "13f_policy":"Dated user-provided historical holdings are only lead sources; not refreshed 13F evidence",
            "companies":sorted_entries},seen

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=["prepare","rank"])
    parser.add_argument("--limit",type=int,default=MAX_PER_RUN)
    args=parser.parse_args()
    today=dt.datetime.now(dt.timezone.utc).date()
    if args.stage=="prepare":
        from update_fundamentals import TICKERS
        source="https://www.sec.gov/files/company_tickers_exchange.json"
        doc=fetch_json(source,os.environ.get("SEC_USER_AGENT",""))
        master=read(ROOT/"data.json",{})
        state=read(STATE,{})
        queue,new_state=prepare(today,doc,master,state,TICKERS,args.limit)
        write(QUEUE,queue)
        # Do not update cursor until the ingestion job succeeds.
        write(DIR/"pending_state.json",new_state)
        print(f"Prepared {len(queue['candidates'])} out of {queue['listed_issuer_count']} SEC listing entries")
    else:
        q=read(QUEUE,None)
        sec=read(ROOT/"fundamentals-auto.json",None)
        if q is None or sec is None:raise SystemExit("Missing discovery queue or SEC ingestion")
        prior=read(RADAR,{})
        result,done=rank(q,sec,prior,today)
        state=read(DIR/"pending_state.json",read(STATE,{}))
        for cik in done:state.setdefault("last_scanned",{})[cik]=today.isoformat()
        state["as_of"]=today.isoformat()
        write(RADAR,result)
        write(STATE,state)
        if (DIR/"pending_state.json").exists():(DIR/"pending_state.json").unlink()
        print(f"Radar: {len(result['companies'])} names, batch {result['last_batch_sec_downloaded']}/{result['last_batch_size']} SEC-covered")
if __name__=="__main__":main()
