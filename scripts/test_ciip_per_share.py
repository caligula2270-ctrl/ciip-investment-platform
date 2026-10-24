#!/usr/bin/env python3
"""Regression tests for conservative per-share value screening."""
import datetime as dt
import unittest
from build_ciip_per_share import build, dcf

def fixtures():
    names=["MSFT","ADBE","V","MA","TXN"]
    company={"denominator":{"central_m":100,"low_m":90,"high_m":110,
           "confidence":"modelled_not_certified", "formula":"synthetic"},
          "name":"Mock","cash_anchor":{"forward_base_justification":"synthetic"},
          "scenarios":{
            "conservador":{"owner_cf1_m":100,"g1_pct":0,"g2_pct":0,"ke_pct":12,"t_pct":2},
            "base":{"owner_cf1_m":100,"g1_pct":5,"g2_pct":2,"ke_pct":10,"t_pct":2},
            "optimista":{"owner_cf1_m":120,"g1_pct":7,"g2_pct":4,"ke_pct":9,"t_pct":3}}}
    inputs={"companies":{n:company for n in names}}
    audit={"companies":{n:{"filing_status":"latest_filing_metadata_matches"} for n in names}}
    market={"prices":{n:{"price":5,"date":"2026-10-23","currency":"USD","source":"Test"} for n in names}}
    return inputs,audit,market

class TestPerShare(unittest.TestCase):
    def test_cash_scale_homogeneity(self):
        a=dcf(100,.05,.02,.10,.02)
        b=dcf(200,.05,.02,.10,.02)
        self.assertAlmostEqual(a["equity_value_musd"]*2,b["equity_value_musd"],delta=.02)
    def test_discount_rate_is_above_terminal(self):
        with self.assertRaises(ValueError):dcf(100,.05,.02,.04,.045)
    def test_denominator_sensitivity(self):
        c,a,m=fixtures()
        d=build(c,a,m,dt.date(2026,10,25))
        x=d["companies"]["MSFT"]["scenario_values"]["base"]
        self.assertGreater(x["share_count_sensitivity"]["low_dilution_value_usd"],
                           x["share_count_sensitivity"]["high_dilution_value_usd"])
        self.assertFalse(d["companies"]["MSFT"]["value_per_share_approved"])
    def test_invalid_share_interval_blocks(self):
        c,a,m=fixtures()
        c["companies"]["V"]["denominator"]["central_m"]=120
        with self.assertRaises(ValueError):build(c,a,m,dt.date(2026,10,25))
    def test_old_quote_not_comparable(self):
        c,a,m=fixtures()
        m["prices"]["TXN"]["date"]="2026-09-01"
        d=build(c,a,m,dt.date(2026,10,25))
        self.assertIsNone(d["companies"]["TXN"]["quote"])
        self.assertIsNone(d["companies"]["TXN"]["base_cash_required_to_match_last_price_musd"])

if __name__=="__main__":
    unittest.main()
