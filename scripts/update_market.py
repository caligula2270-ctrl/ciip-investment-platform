#!/usr/bin/env python3
"""CIIP public daily closing-price collector. No credentials or trading."""
import csv, datetime as dt, io, json, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Explicit, auditable Stooq symbols; do not infer foreign exchange symbols.
SYMBOLS={
"MSFT":"msft.us","GOOGL":"googl.us","AMZN":"amzn.us","META":"meta.us",
"V":"v.us","MA":"ma.us","SPGI":"spgi.us","MCO":"mco.us",
"COST":"cost.us","CPRT":"cprt.us","FICO":"fico.us","ROP":"rop.us",
"HEI":"hei.us","TDG":"tdg.us","NVO":"nvo.us","RELX":"relx.us",
"INTU":"intu.us","ADBE":"adbe.us","TXN":"txn.us","LRCX":"lrcx.us",
"TSM":"tsm.us","BKNG":"bkng.us","MELI":"meli.us","AZO":"azo.us",
"ORLY":"orly.us","ODFL":"odfl.us","VRSK":"vrsk.us","AON":"aon.us",
"DHR":"dhr.us","MEDP":"medp.us","NTDOY":"ntdoy.us","OXY":"oxy.us",
"AAON":"aaon.us","TRUP":"trup.us","TBBB":"tbbb.us","FRPH":"frph.us"
}
today=dt.datetime.now(dt.timezone.utc)
result={"schema":"ciip-market-v1","provider":"Stooq (daily historical CSV)","generated_at":today.isoformat(),"frequency":"weekdays","prices":{},"unavailable":{},"notes":"Precios de cierre no ajustados en su divisa de cotizacion. No son cotizaciones en tiempo real ni datos fundamentales. Fuentes no garantizadas; confirmar con el mercado primario."}
def fetch_yahoo(ticker):
    """Yahoo Finance chart endpoint: daily exchange timestamps and closes."""
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(ticker)+"?range=10d&interval=1d"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; CIIP/0.4)","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=14) as response:
        data=json.load(response)
    node=data["chart"]["result"][0]
    currency=node["meta"].get("currency")
    if currency!="USD":raise ValueError("Divisa inesperada: "+str(currency))
    times=node.get("timestamp",[])
    closes=node["indicators"]["quote"][0]["close"]
    valid=[]
    for stamp,close in zip(times,closes):
        if close is None:continue
        date=dt.datetime.fromtimestamp(stamp,dt.timezone.utc).date()
        if 0<float(close)<1e7 and date<=today.date() and (today.date()-date).days<=15:valid.append((date,float(close)))
    if not valid:raise ValueError("Sin cierre reciente en Yahoo")
    date,price=max(valid)
    return {"price":price,"currency":"USD","date":date.isoformat(),"source":"Yahoo Finance (chart)","symbol":ticker,"url":url,"kind":"daily_close","verified":False}

def fetch_stooq(ticker,symbol):
    url="https://stooq.com/q/d/l/?"+urllib.parse.urlencode({"s":symbol,"i":"d","d1":(today-dt.timedelta(days=15)).strftime("%Y%m%d"),"d2":today.strftime("%Y%m%d")})
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; CIIP/0.4)","Accept":"text/csv"})
    with urllib.request.urlopen(req,timeout=14) as response:
        body=response.read(250000).decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(body)))
    valid=[]
    for row in rows:
        try:
            date=dt.date.fromisoformat(row["Date"])
            close=float(row["Close"])
            if 0<close<1e7 and date<=today.date() and (today.date()-date).days<=15:valid.append((date,close))
        except (KeyError,ValueError,TypeError):pass
    if not valid:raise ValueError("Sin cierre diario válido reciente; respuesta="+repr(body[:100]))
    date,price=max(valid)
    return {"price":price,"currency":"USD","date":date.isoformat(),"source":"Stooq","symbol":symbol,"url":url,"kind":"daily_close","verified":False}

result["provider"]="Yahoo Finance chart / Stooq fallback"
for ticker,symbol in SYMBOLS.items():
    errors=[]
    for name,fetch in [("Yahoo",lambda:fetch_yahoo(ticker)),("Stooq",lambda:fetch_stooq(ticker,symbol))]:
        try:
            result["prices"][ticker]=fetch()
            break
        except (urllib.error.URLError,TimeoutError,ValueError,OSError,KeyError,IndexError,TypeError,json.JSONDecodeError) as exc:
            errors.append(name+": "+str(exc)[:130])
    if ticker not in result["prices"]:
        result["unavailable"][ticker]=" | ".join(errors)[:350]
        print("Unavailable",ticker,result["unavailable"][ticker])
    time.sleep(0.25)
# Preserve previous successful observations if an upstream outage occurs, explicitly marking them stale.
dest=ROOT/"market-auto.json"
if dest.exists():
    try:
        old=json.loads(dest.read_text(encoding="utf-8"))
        for ticker,p in old.get("prices",{}).items():
            if ticker not in result["prices"] and ticker in SYMBOLS and p.get("date") and p.get("source") in ("Stooq","Yahoo Finance (chart)"):
                result["prices"][ticker]=p
    except (ValueError,OSError):pass
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(f"CIIP market: {len(result['prices'])} observations, {len(result['unavailable'])} unavailable")
if not result["prices"]:
    print("ERROR: Ninguna cotización válida. Comprobar proveedor, disponibilidad y formato.", file=sys.stderr)
    sys.exit(1)
if len(result["prices"]) < 10:
    print("ERROR: Cobertura insuficiente ("+str(len(result["prices"]))+"/"+str(len(SYMBOLS))+").", file=sys.stderr)
    sys.exit(1)
