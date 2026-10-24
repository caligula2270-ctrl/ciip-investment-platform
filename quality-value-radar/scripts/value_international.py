#!/usr/bin/env python3
"""International QVR DCF, official issuer historical FCF snapshots, no fabricated FX.
Returns preliminary ranges, NOT buy signals. Units: millions of reporting currency.
"""
import datetime as dt,json,pathlib,statistics,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/"data"/"international.json"
QUOTES=ROOT/"data"/"quotes.json"
SERIES={
"CSU.TO":{"currency":"USD","stockCurrency":"CAD","sharesM":21.19153,"fcfM":[1160,1472,1683],"years":[2023,2024,2025],"metric":"FCFA2S Non-IFRS, excludes acquisitions","growth":.07,"discount":.125,"terminal":.025,"fx":"CAD=X","fxInterpretation":"CAD por USD","primary":["https://www.csisoftware.com/constellation-software-inc-announces-results-for-the-fourth-quarter-and-year-ended-december-31-2025-and-declares-quarterly-dividend/","https://www.csisoftware.com/constellation-software-inc-announces-results-for-the-fourth-quarter-and-year-ended-december-31-2024-and-declares-quarterly-dividend/"],"warning":"Adquisiciones consumen caja y crean crecimiento; FCFA2S no equivale a caja repartible después de adquisiciones."},
"ASML":{"currency":"EUR","stockCurrency":"USD","sharesM":385.417665,"fcfM":[3247.2,9083.1,11027.3],"years":[2023,2024,2025],"metric":"FCF no-GAAP, CFO - capex + intangibles","growth":.07,"discount":.115,"terminal":.025,"fx":"EURUSD=X","fxInterpretation":"USD por EUR","primary":["https://www.sec.gov/Archives/edgar/data/937966/000162828026011378/asml-20251231.htm","https://www.sec.gov/Archives/edgar/data/937966/000093796625000009/asml-20241231.htm"],"warning":"ASML cotiza en Nasdaq en USD; modelo parte de EUR. FCF sensible a anticipos de clientes y ciclo de semiconductores."},
"DNP.WA":{"currency":"PLN","stockCurrency":"PLN","sharesM":980.4,"fcfM":[599,995,610],"years":[2023,2024,2025],"metric":"CFO - capex reportados","growth":.095,"discount":.12,"terminal":.025,"fx":None,"primary":["https://grupadino.pl/wp-content/uploads/2026/03/Dino-Polska-2025-results-presentation.pdf","https://grupadino.pl/en/selected-financial-data/","https://grupadino.pl/raport-biezacy-nr-10-2025-oswiadczenie-kdpw-w-sprawie-wyznaczenia-dnia-podzialu-splitu-akcji-dino-polska-s-a/"],"warning":"Capex de expansión de tiendas elevado; FCF actual no mide plenamente valor de futuras aperturas. Split de 10:1 incorporado."}}
def fx_latest(pair):
  url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(pair,safe="")+"?range=5d&interval=1d"
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 QVR-Research"})
  with urllib.request.urlopen(req,timeout=15) as h:obj=json.load(h)["chart"]["result"][0]
  t=obj["timestamp"];p=obj["indicators"]["quote"][0]["close"]
  for timestamp,price in reversed(list(zip(t,p))):
    if price and price>0:
      return {"rate":round(price,6),"date":dt.datetime.fromtimestamp(timestamp,dt.timezone.utc).date().isoformat(),"source":url}
  raise ValueError("Missing FX data")
def value(fcf,g,r,term):
  if fcf<=0 or r<=term: return None
  return sum(fcf*(1+g)**t/(1+r)**t for t in range(1,6))+fcf*(1+g)**5*(1+term)/(r-term)/(1+r)**5
def run():
  dat=json.loads(PATH.read_text()); quotes=json.loads(QUOTES.read_text())["quotes"]
  dat["generatedAt"]=dt.datetime.now(dt.timezone.utc).isoformat()
  for ticker,s in SERIES.items():
    entry=dat["companies"][ticker]
    annual=[{"year":y,"fcfMillions":f} for y,f in zip(s["years"],s["fcfM"])]
    try:
      fx=fx_latest(s["fx"]) if s["fx"] else {"rate":1,"date":quotes.get(ticker,{}).get("date"),"source":"same currency"}
      q=quotes.get(ticker)
      if not q or q.get("currency")!=s["stockCurrency"]:raise ValueError("Stock quote or currency missing")
      # Rates must be independently dated. Never silently assume exchange rate.
      if not fx["date"] or abs((dt.date.fromisoformat(fx["date"])-dt.date.fromisoformat(q["date"])).days)>5:
        raise ValueError("FX and quote as-of dates inconsistent")
      norm=statistics.median(s["fcfM"])/s["sharesM"]
      low=value(norm,max(-.025,s["growth"]-.04),s["discount"]+.02,.02)
      mid=value(norm,s["growth"],s["discount"],s["terminal"])
      high=value(norm,min(.18,s["growth"]+.04),max(.095,s["discount"]-.01),.03)
      if not all(v and v>0 for v in (low,mid,high)):raise ValueError("Invalid model")
      vals=[round(x*fx["rate"],2) for x in (low,mid,high)]
      # Reverse DCF: revenue/FCF growth needed to support observed price.
      target=q["price"]/fx["rate"]
      lo,hi=-.20,.40
      for _ in range(65):
        guess=(lo+hi)/2
        if value(norm,guess,s["discount"],s["terminal"])<target:lo=guess
        else:hi=guess
      market_implied=(lo+hi)/2
      entry["valuation"]={"marketImpliedFiveYearFcfGrowthPct":round(market_implied*100,2),
        "growthReference":"Reverse DCF uses flat per-share terminal share count; NOT management guidance",
        "historicalPfcfCrossCheck":"unavailable: comparable split-and-FX-adjusted fiscal prices not independently normalized",
        "reinvestmentAdjustment":"Not separately modeled: acquisitions / development CAPEX must be reviewed","status":"preliminary","model":"5Y DCF median 3Y historical issuer FCF","annualFcf":annual,
         "normalizedFcfPerShare":round(norm,4),"reportingCurrency":s["currency"],"tradingCurrency":s["stockCurrency"],
         "sharesMillions":s["sharesM"],"fx":fx,"bear":vals[0],"base":vals[1],"bull":vals[2],
         "quotePrice":q["price"],"quoteDate":q["date"],"indicativeMarginPct":round(100*(1-q["price"]/vals[1]),1),
         "assumptions":{"baseGrowthPct":s["growth"]*100,"discountPct":s["discount"]*100,"terminalGrowthPct":s["terminal"]*100},
         "metric":s["metric"],"primarySources":s["primary"],"warning":s["warning"],
         "investmentSignal":"human_review_required","historicalMultipleAvailable":False}
      entry["status"]="preliminary_valuation"
      print(ticker,"preliminary",vals[1],s["stockCurrency"])
    except Exception as exc:
      entry["status"]="fx_or_quote_unavailable"
      entry["valuation"]={"status":"unavailable","reason":str(exc)[:180],"primarySources":s["primary"],
          "annualFcf":annual,"investmentSignal":"none"}
      print("WARN",ticker,str(exc))
  PATH.write_text(json.dumps(dat,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":run()
