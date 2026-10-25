#!/usr/bin/env python3
import datetime as dt, unittest
from audit_ciip_models import build
class TestModelAudit(unittest.TestCase):
    def fixture(self):
        from audit_ciip_models import load
        return load()
    def test_real_five_models_have_arithmetic_control(self):
        r=build(self.fixture(),dt.date(2026,10,25))
        self.assertEqual(set(r["issuers"]),{"ADBE","MSFT","V","MA","TXN"})
        for t,x in r["issuers"].items():
            checks=[v for v in x["checks"] if v["name"].startswith("DCF arithmetic")]
            self.assertEqual(len(checks),3)
            self.assertTrue(all(v["pass"] for v in checks),t)
            self.assertFalse(x["valuation_approved"])
    def test_adobe_acquisition_blocker(self):
        r=build(self.fixture(),dt.date(2026,10,25))
        self.assertTrue(any(x["severity"]=="P0" and "acquisitions" in x["detail"].lower() for x in r["issuers"]["ADBE"]["findings"]))
    def test_source_cash_reconciliation(self):
        r=build(self.fixture(),dt.date(2026,10,25))
        self.assertTrue(any(v["name"]=="Adobe FY2025 CFO and CAPEX tie-out" and v["pass"] for v in r["issuers"]["ADBE"]["checks"]))
        self.assertTrue(any(v["name"]=="Microsoft reported FY2026 CFO CAPEX" and v["pass"] for v in r["issuers"]["MSFT"]["checks"]))
    def test_scope_locked(self):
        d=self.fixture()
        d["inputs"]["companies"]["NEW"]={}
        with self.assertRaises(ValueError):build(d,dt.date(2026,10,25))
if __name__=="__main__":unittest.main()
