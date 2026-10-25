#!/usr/bin/env python3
"""Offline operational contract regression tests for production research feed."""
import importlib.util,pathlib,unittest,json,tempfile
BASE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("qvr_production",BASE/"build_production_snapshot.py")
prod=importlib.util.module_from_spec(spec);spec.loader.exec_module(prod)
class ProductionTests(unittest.TestCase):
 def test_quote_asof(self):
  self.assertEqual(prod.fmt_status(0,7),"current")
  self.assertEqual(prod.fmt_status(8,7),"stale")
  self.assertEqual(prod.fmt_status(None,7),"missing_or_future")
  self.assertEqual(prod.fmt_status(-1,7),"missing_or_future")
 def test_no_value_in_unavailable_quote(self):
  self.assertIsNone(prod.clean_numeric(None))
  self.assertIsNone(prod.clean_numeric(-1))
  self.assertIsNone(prod.clean_numeric(float("nan")))
 def test_company_universe(self):
  self.assertEqual(len(prod.FOCUS),6)
  self.assertEqual(set(prod.CURRENCY),set(prod.FOCUS))
 def test_output_is_research_only(self):
  p=prod.OUT
  if p.exists():
   j=json.loads(p.read_text())
   self.assertFalse(any(x.get("buyApproved") for x in j.get("companies",{}).values()))
   self.assertFalse(any(x.get("investmentGradeValue") is not None for x in j.get("companies",{}).values()))
if __name__=="__main__":unittest.main()
