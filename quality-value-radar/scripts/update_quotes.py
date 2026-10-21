#!/usr/bin/env python3
"""Actualiza precios diarios desde fuentes públicas cuando responden.
No requiere API key; no garantiza acceso, continuidad ni redistribución comercial.
Si un proveedor falla se conserva el último dato con su fecha. Nunca se fabrican precios.
"""
from __future__ import annotations
import csv
from datetime import date, datetime, timedelta
from io import StringIO
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'data' / 'quotes.json'
SEED = ROOT / 'data' / 'seed.js'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; QualityValueRadar/1.0; public quote refresh)', 'Accept':'application/json,text/csv,*/*'}
# Lista de símbolos explícita. También puede ampliarse manualmente.
SYMBOLS = {
'CPRT':'USD','AMZN':'USD','CSU.TO':'CAD','KNSL':'USD','DNP.WA':'PLN','ADBE':'USD','ASML':'USD',
'ATCO-A.ST':'SEK','AAON':'USD','DE':'USD','DGE.L':'GBp','DHR':'USD','FIVE':'USD','FOUR':'USD',
'FRPH':'USD','INTU':'USD','JDG.L':'GBp','KEYS':'USD','MEDP':'USD','7974.T':'JPY',
'RMD':'USD','STVN':'USD','TRUP':'USD','TXN':'USD','ZTS':'USD','COST':'USD',
'GLNG':'USD','0001.HK':'HKD','ATYM.L':'GBp','DAN.MI':'EUR','BWO.OL':'NOK',
'BWE.OL':'NOK','WIZZ.L':'GBp','BRAV3.SA':'BRL','TGS.OL':'NOK','DBG.PA':'EUR',
'MEL.MC':'EUR','SCYR.MC':'EUR','TRE.MC':'EUR','GRF.MC':'EUR','ALM.MC':'EUR',
'GEST.MC':'EUR','DOM.MC':'EUR','MCM.MC':'EUR','TUB.MC':'EUR'}


def download_json(url: str) -> dict:
    req = urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=12) as result:
        return json.load(result)


def fetch_yahoo(ticker: str, expected_currency: str):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(ticker,safe='')+'?range=10d&interval=1d'
    data=download_json(url)
    obj=data['chart']['result'][0]
    meta=obj.get('meta',{})
    actual_currency=meta.get('currency') or ''
    expected=expected_currency.upper()
    # Yahoo uses GBp or GBX for pounds pence in some listings; GBP may be pounds.
    if expected_currency == 'GBp':
        if actual_currency not in ('GBp','GBX'):
            raise ValueError('Expected GBp/GBX, got '+actual_currency)
        # If Yahoo returns GBP rather than GBp, do not silently multiply by 100.
    elif actual_currency.upper()!=expected:
        raise ValueError(f'Currency mismatch: {ticker}, {actual_currency} vs {expected}')
    timestamps=obj.get('timestamp',[])
    closes=obj.get('indicators',{}).get('quote',[{}])[0].get('close',[])
    if not timestamps or not closes: raise ValueError('No daily candles')
    time_zone=meta.get('exchangeTimezoneName') or 'UTC'
    tz=ZoneInfo(time_zone)
    for ts,close in reversed(list(zip(timestamps,closes))):
        if close is not None and 0 < float(close) < 10**9:
            d=datetime.fromtimestamp(ts,tz).date().isoformat()
            if d>date.today().isoformat():continue
            return {'price': round(float(close),4),'currency':expected_currency,'date':d,
                'source':'Yahoo Finance chart (sin garantía de disponibilidad)',
                'sourceUrl':'https://finance.yahoo.com/quote/'+urllib.parse.quote(ticker)+'/history/',
                'kind':'cierre'}
    raise ValueError('All daily candles invalid')


def fetch_stooq_us(ticker: str):
    # Only US symbols: country-specific suffix prevents accidental symbol collision.
    start=(date.today()-timedelta(days=14)).strftime('%Y%m%d')
    end=date.today().strftime('%Y%m%d')
    url=f'https://stooq.com/q/d/l/?s={ticker.lower()}.us&d1={start}&d2={end}&i=d'
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=12) as response:
        raw=response.read().decode('utf-8-sig','replace')
    rows=list(csv.DictReader(StringIO(raw)))
    if not rows:raise ValueError('Stooq no data')
    q=rows[-1]
    px=float(q['Close']);dt=q['Date']
    if not (px>0 and re.fullmatch(r'\d{4}-\d\d-\d\d',dt)):raise ValueError('Invalid Stooq data')
    return {'price':round(px,4),'currency':'USD','date':dt,'source':'Stooq diario',
            'sourceUrl':'https://stooq.com/q/?s='+ticker.lower()+'.us','kind':'cierre'}


def main():
    previous=json.loads(PATH.read_text('utf-8')) if PATH.exists() else {'quotes':{}}
    quotes=previous.get('quotes',{}).copy()
    successes=[];failures=[]
    for symbol,currency in SYMBOLS.items():
        try:
            new=fetch_yahoo(symbol,currency)
            old=quotes.get(symbol)
            if not old or old.get('date','')<=new['date']:
                quotes[symbol]=new
            successes.append(symbol)
        except Exception as e:
            if currency=='USD' and '.' not in symbol:
                try:
                    new=fetch_stooq_us(symbol)
                    old=quotes.get(symbol)
                    if not old or old.get('date','')<=new['date']:
                        quotes[symbol]=new
                    successes.append(symbol)
                except Exception as e2:
                    failures.append((symbol, str(e)[:75]+' / '+str(e2)[:75]))
            else:
                failures.append((symbol,str(e)[:150]))
        time.sleep(.16)
    # Always keep original publication timestamps for quotes when provider failed.
    generated=datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ')
    payload={'generatedAt':generated,'successfulSymbols':len(successes),'attemptedSymbols':len(SYMBOLS),'quotes':dict(sorted(quotes.items()))}
    PATH.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f'Updated {len(successes)}; failed {len(failures)}; retained {len(quotes)} total')
    for t,error in failures: print(f'WARN {t}: {error}',file=sys.stderr)
    # No failure exit when some prices unavailable: stale data are visibly flagged in UI.
    if not successes: print('WARNING: No provider succeeded. Historical prices retained.',file=sys.stderr)


if __name__=='__main__':main()
