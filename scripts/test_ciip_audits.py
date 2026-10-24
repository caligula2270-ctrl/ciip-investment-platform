#!/usr/bin/env python3
"""CIIP evidence-based audit compiler regression tests (offline)."""
import datetime as dt
import unittest
from build_ciip_audits import build,metrics_from_history,TICKERS

class TestAudit(unittest.TestCase):
    def test_missing_required_company_blocks(self):
        d={"entities":{t:{"company":t,"sector":"X","evidence":[]} for t in TICKERS}}
        with self.assertRaises(ValueError):
            build(d,{"companies":{}},dt.datetime(2026,10,24,tzinfo=dt.timezone.utc))
    def test_no_automatic_signoff_and_filing_change_flag(self):
        d={"review_as_of":"2026-10-24","entities":{
            t:{"company":t,"sector":"X","evidence":[{"topic":"a","source":"https://sec.gov","location":"Notes","fact":"x","impact":"y"}],
                "interim_source":"https://www.sec.gov/old.htm"}
            for t in TICKERS}}
        facts={"companies":{t:{"history":[],"history_quality":{},"sector_control":{},
             "sector_valuation":{},"share_reconciliation":{},"capital_filings":{"filings":[{
             "document_url":"https://www.sec.gov/new.htm","filed":"2026-10-23"}]}} for t in TICKERS}}
        out=build(d,facts,dt.datetime(2026,10,24,tzinfo=dt.timezone.utc))
        for v in out["companies"].values():
            self.assertFalse(v["signoff"]["capital_notes_reconciled"])
            self.assertIsNone(v["share_capital"]["value_per_share"])
            self.assertEqual(v["filing_status"],"newer_or_different_filing_needs_review")
    def test_missing_cash_not_zero(self):
        x=metrics_from_history({"fy_end":"2025-12-31","metrics":{}})
        self.assertIsNone(x["cfo_musd"])
        self.assertIsNone(x["reported_fcf_musd"])

if __name__=="__main__":unittest.main()
