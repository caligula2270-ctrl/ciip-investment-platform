import datetime as dt
import unittest
from discover_opportunities import normalize_listing,prepare,evaluate,rank

FIX={"fields":["cik","name","ticker","exchange"],"data":[[10,"Great Test Inc","GREAT","Nasdaq"],[11,"Other Test Inc","OTHER","NYSE"],[12,"Index ETF","ETF1","Nasdaq"],[10,"Great Test Inc Class B","GREAT.B","Nasdaq"]]}
class DiscoveryChecks(unittest.TestCase):
 def test_unique_issuer_and_fund_filter(self):
  names=normalize_listing(FIX)
  self.assertEqual([x["ticker"] for x in names],["GREAT","OTHER"])
 def test_rotating_discovery_with_no_prior_manual_addition(self):
  q,state=prepare(dt.date(2026,10,26),FIX,{}, {},limit=2)
  self.assertEqual(len(q["candidates"]),2)
  self.assertEqual(q["listed_issuer_count"],2)
  self.assertNotEqual(q["candidates"][0]["cik"],q["candidates"][1]["cik"])
 def test_missing_fundamentals_never_recommends(self):
  q,_=prepare(dt.date(2026,10,26),FIX,{}, {},limit=2)
  radar,seen=rank(q,{"companies":{}},{},dt.date(2026,10,26))
  self.assertEqual(seen,[])
  self.assertTrue(all(x["status"]=="INSUFFICIENT_DATA" and not x["decision_ready"] and x["price_target_usd"] is None for x in radar["companies"]))
 def test_historical_13f_not_current_position(self):
  master={"03_HOLDINGS":[{"Ticker":"OTHER","Guru_ID":"G1","Fecha_corte":"2026-03-31","Tipo_aparición":"OF-13F","Fuente_URL":"https://example.com/filing"}]}
  q,_=prepare(dt.date(2026,10,26),FIX,master,{},limit=1)
  self.assertEqual(q["candidates"][0]["ticker"],"OTHER")
  self.assertIn("historical",q["candidates"][0]["historical_13f"]["status"])
if __name__=="__main__":unittest.main()
