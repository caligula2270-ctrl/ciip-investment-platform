#!/usr/bin/env python3
"""Tests remediations independently from previously committed generated JSON."""
import copy
import datetime as dt
import json
import unittest
from audit_ciip_models import build,load,ROOT
from build_ciip_per_share import build as build_per_share
from ciip_official_filing_bridges import bridge_history

class TestModelAudit(unittest.TestCase):
    def fixture(self):
        d=copy.deepcopy(load())
        date=dt.date(2026,10,25)
        for ticker in ("V","MA"):
            c=d["sec"]["companies"][ticker]
            c["official_filing_bridge"]=bridge_history(ticker,c["history"],c["history_quality"],date)
        market=json.loads((ROOT/"market-auto.json").read_text(encoding="utf-8"))
        d["models"]=build_per_share(d["inputs"],d["audits"],market,date)
        return d
    def test_5_models_formula_recalculation_and_0_fixed_P0(self):
        r=build(self.fixture(),dt.date(2026,10,25))
        self.assertEqual(set(r["issuers"]),{"ADBE","MSFT","V","MA","TXN"})
        for ticker,x in r["issuers"].items():
            checks=[c for c in x["checks"] if c["name"].startswith("DCF arithmetic")]
            self.assertEqual(len(checks),3)
            self.assertTrue(all(c["pass"] for c in checks),ticker)
            self.assertFalse(x["valuation_approved"])
            self.assertEqual(x["P0"],0,ticker)
    def test_adobe_acquisition_reserve_is_enforced(self):
        d=self.fixture()
        d["inputs"]["companies"]["ADBE"]["scenarios"]["base"].pop("annual_acquisition_reinvestment_m")
        x=build(d,dt.date(2026,10,25))["issuers"]["ADBE"]
        self.assertGreater(x["P0"],0)
        self.assertTrue(any("acquisition" in c["name"].lower() and not c["pass"] for c in x["checks"]))
    def test_source_cash_reconciliation(self):
        r=build(self.fixture(),dt.date(2026,10,25))
        for ticker,text in (("ADBE","Adobe FY2025 CFO and CAPEX"),
                            ("MSFT","Microsoft reported FY2026 CFO"),
                            ("V","Visa 5Y issuer-filed CAPEX"),
                            ("MA","Mastercard 5Y reported GAAP"),
                            ("TXN","TI LTM 2026 GAAP")):
            self.assertTrue(any(text in x["name"] and x["pass"] for x in r["issuers"][ticker]["checks"]),ticker)
    def test_missing_visa_bridge_blocks(self):
        d=self.fixture()
        d["sec"]["companies"]["V"]["official_filing_bridge"]={"status":"not_applicable","filled":[],"conflicts":[]}
        r=build(d,dt.date(2026,10,25))
        self.assertGreater(r["issuers"]["V"]["P0"],0)
    def test_visa_share_delta_must_tie(self):
        d=self.fixture()
        d["inputs"]["companies"]["V"]["denominator"]["sept_Bdrop_total_m"]=.7
        r=build(d,dt.date(2026,10,25))
        self.assertGreater(r["issuers"]["V"]["P0"],0)
    def test_microsoft_unsupported_cash_uplift_blocks(self):
        d=self.fixture()
        d["inputs"]["companies"]["MSFT"]["scenarios"]["base"]["owner_cf1_m"]=90000
        r=build(d,dt.date(2026,10,25))
        self.assertGreater(r["issuers"]["MSFT"]["P0"],0)
    def test_scope_locked(self):
        d=self.fixture()
        d["inputs"]["companies"]["NEW"]={}
        with self.assertRaises(ValueError):build(d,dt.date(2026,10,25))

if __name__=="__main__":unittest.main()
