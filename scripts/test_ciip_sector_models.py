#!/usr/bin/env python3
"""CIIP sector and capital-note safeguarding tests with synthetic SEC values."""
import datetime as dt
import unittest
from ciip_sector_models import build_sector_valuation
from ciip_capital_filings import latest_equity_filings


def rows(years=5, cfo=100, capex=20, sbc=10, net=90):
    records=[]
    for i in range(years):
        records.append({
            "fy_end":f"{2021+i}-12-31", "fcf_usd":cfo-capex,
            "metrics":{
                "operating_cash_flow":{"value":cfo},
                "capex":{"value":capex},
                "stock_compensation":{"value":sbc},
                "net_income":{"value":net},
            }})
    return records


def quality(**overrides):
    o={"latest_fy_age_days":150,"normalized_fcf_3y_usd":80,
       "normalized_fcf_status":"ready_with_caveats",
       "revenue_cagr_pct":7.}
    o.update(overrides)
    return o


class TestSectorModels(unittest.TestCase):
    def test_software_sbc_deducted_once(self):
        x=build_sector_valuation("ADBE",rows(),quality())
        self.assertEqual(x["model"],"software_owner_cash_sbc_stress")
        self.assertEqual(x["normalized_cash_usd"],70)
        self.assertEqual(x["status"],"review_required")
        self.assertIn("base",x["scenarios"])

    def test_software_without_sbc_not_valorable(self):
        r=rows()
        for y in r:y["metrics"].pop("stock_compensation")
        x=build_sector_valuation("ADBE",r,quality())
        self.assertEqual(x["status"],"insufficient")

    def test_payments_earnings_cap_and_no_share_targets(self):
        x=build_sector_valuation("V",rows(net=60),
             quality(normalized_fcf_3y_usd=None,normalized_fcf_status="sector_blocked"))
        self.assertEqual(x["status"],"aggregate_research_only")
        self.assertEqual(x["normalized_cash_usd"],57)
        self.assertNotIn("fair_value_per_share",x)

    def test_payments_working_capital_blocks(self):
        x=build_sector_valuation("MA",rows(),
               quality(normalized_fcf_3y_usd=None,normalized_fcf_status="working_capital_review"))
        self.assertEqual(x["status"],"insufficient")

    def test_capital_peak_capex_stress(self):
        r=rows(cfo=160,capex=30)
        r[-1]["metrics"]["capex"]["value"]=110
        r[-1]["fcf_usd"]=50
        x=build_sector_valuation("ODFL",r,quality(normalized_fcf_3y_usd=130))
        self.assertEqual(x["model"],"capital_heavy_peak_capex_stress")
        self.assertEqual(x["normalized_cash_usd"],50)
        self.assertEqual(x["status"],"review_required")

    def test_capital_five_years_required(self):
        x=build_sector_valuation("TXN",rows(years=3),quality())
        self.assertEqual(x["status"],"insufficient")

    def test_filings_metadata_never_equates_to_note_review(self):
        filings={"filings":{"recent":{
           "form":["10-Q","8-K"],
           "accessionNumber":["0000123456-26-000001","0000123456-26-000002"],
           "primaryDocument":["form10q.htm","event.htm"],
           "filingDate":["2026-10-20","2026-10-21"],
           "reportDate":["2026-09-30","2026-10-21"]}}}
        out=latest_equity_filings(filings,"0000123456",dt.date(2026,10,24))
        self.assertEqual(len(out["filings"]),1)
        self.assertIsNone(out["verified_current_fully_diluted_shares"])
        self.assertEqual(out["reviewed_notes"],[])
        self.assertIn("sec.gov/Archives/edgar/data/",out["filings"][0]["document_url"])

if __name__=="__main__":
    unittest.main()
