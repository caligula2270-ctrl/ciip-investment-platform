#!/usr/bin/env python3
"""Universal coverage contract — all tests deterministic without network."""
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("univ",Path(__file__).with_name("universal_market.py"))
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
class UniversalTests(unittest.TestCase):
 def test_global_symbols(self):
  for t in ("MSFT","SAP.DE","SAN.MC","7203.T","BRK-B","0001.HK"):
   self.assertEqual(engine.ticker_clean(t.lower()),t)
 def test_reject_malicious_or_invalid_symbols(self):
  for t in ("","../../etc/passwd","MSFT;rm -rf","MSFT/US","TEST TEST"):
   with self.assertRaises(ValueError):engine.ticker_clean(t)
 def test_financial_sectors_not_generic_dcf(self):
  self.assertEqual(engine.sector_for_sic(6021),"financial_or_real_estate")
  self.assertEqual(engine.sector_for_sic(6331),"financial_or_real_estate")
  self.assertEqual(engine.sector_for_sic(7372),"software")
  self.assertEqual(engine.sector_for_sic(2834),"chemicals")
 def test_scenarios_monotone_positive(self):
  records=[
   {"fyEnd":"2023-12-31","revenueUSD":100,"ownerFcfUSD":20,"dilutedShares":10},
   {"fyEnd":"2024-12-31","revenueUSD":110,"ownerFcfUSD":21,"dilutedShares":10},
   {"fyEnd":"2025-12-31","revenueUSD":120,"ownerFcfUSD":24,"dilutedShares":10}]
  result=engine.scenario_sec(records,{"currency":"USD"},"software")
  self.assertEqual(result["status"],"indicative_research_only")
  self.assertLess(result["bearUSD"],result["baseUSD"])
  self.assertLess(result["baseUSD"],result["bullUSD"])
  self.assertTrue(result["currentDilutedSharesUnverified"])
 def test_non_us_currency_not_mixed(self):
  r=[{"fyEnd":"2025-12-31","revenueUSD":100,"ownerFcfUSD":20,"dilutedShares":10}]
  v=engine.scenario_sec(r,{"currency":"EUR"},"general_nonfinancial")
  self.assertEqual(v["status"],"currency_mismatch")
 def test_bank_no_valuation(self):
  self.assertEqual(engine.scenario_sec([],{"currency":"USD"},"financial_or_real_estate")["status"],"sector_requires_other_model")
if __name__=="__main__":unittest.main()
