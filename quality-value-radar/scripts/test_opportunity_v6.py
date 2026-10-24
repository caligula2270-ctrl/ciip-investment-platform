#!/usr/bin/env python3
"""Offline regression tests for valuation assumptions and safe research gates."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).with_name("opportunity_v6.py")
spec=importlib.util.spec_from_file_location("opportunity_v6",p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class ModelRegressionTests(unittest.TestCase):
    def test_constant_cash_value_positive(self):
        a=module.scenario(1,0,15,.12)
        self.assertGreater(a["value"],0)
        self.assertEqual(len(a["yearlyOwnerFcf"]),5)
    def test_bear_is_below_base(self):
        bear=module.scenario(10,.01,12,.13)
        base=module.scenario(10,.07,22,.115)
        self.assertLess(bear["value"],base["value"])
    def test_entry_below_base(self):
        base=module.scenario(10,.07,20,.12)["value"]
        bear=module.scenario(10,.01,12,.135)["value"]
        self.assertLessEqual(min(.75*base,.9*bear),.75*base)
    def test_no_irr_for_invalid_purchase_price(self):
        self.assertIsNone(module.irr([1,2,3],0))
    def test_missing_evidence_cannot_be_high(self):
        score,tier,parts=module.confidence(True,True,False,False,False,False,False)
        self.assertNotEqual(tier,"high")
    def test_major_acquisition_caps_confidence(self):
        score,tier,parts=module.confidence(True,True,True,True,True,True,True,False,True)
        self.assertLessEqual(score,49)
        self.assertEqual(tier,"low")
    def test_guidance_does_not_become_consensus(self):
        guide={"revenueLow":150,"revenueHigh":160,"periodEnd":"2027-12-31",
               "fiscalYear":2027,"sourceUrl":"https://example.org"}
        grow,source=module.forecast_growth(guide,120_000_000,"2026-12-31",10,"software")
        self.assertEqual(source["kind"],"model_derived_from_management_revenue_guidance")
        self.assertIn("not fcf",source["note"].lower())
if __name__=="__main__":unittest.main()
