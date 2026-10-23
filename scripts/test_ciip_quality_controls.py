#!/usr/bin/env python3
"""Offline regression tests for conservative CIIP finance/sector gates."""
import datetime as dt
import unittest
from ciip_quality_controls import (
    sector_control, quality_normalize, current_share_reconciliation,
)


def fact(value, end, tag, *, start=None, taxonomy="us-gaap", form="10-K"):
    return {"val": value, "end": end, "start": start,
            "filed": "2026-09-01", "form": form,
            "accn": "0000000000-26-000001"}


def sample():
    # Latest FY 2025; fiscal rows have three annual periods.
    years = ["2023-12-31", "2024-12-31", "2025-12-31"]
    cfo = [100, 200, 150]
    capex = [30, 80, 30]
    return [{
        "fy_end": year,
        "metrics": {
            "operating_cash_flow": {"value": a},
            "capex": {"value": b},
        },
        "fcf_usd": a-b,
    } for year, a, b in zip(years, cfo, capex)]


class NormalizationTests(unittest.TestCase):
    def test_medians_fail_closed_and_do_not_add_back_growth_capex(self):
        rows = sample()
        quality = {"latest_fy_age_days": 200}
        profile = quality_normalize({}, rows, quality, "CPRT", dt.date(2026, 10, 24))
        # yearly FCF [70,120,120]; median=120, but median(CFO)-median(CAPEX)=120.
        self.assertEqual(quality["normalized_fcf_3y_usd"], 120)
        self.assertEqual(profile["status"], "eligible")

    def test_block_insurers(self):
        quality = {"latest_fy_age_days": 200}
        quality_normalize({}, sample(), quality, "TRUP", dt.date(2026, 10, 24))
        self.assertIsNone(quality["normalized_fcf_3y_usd"])
        self.assertEqual(quality["normalized_fcf_status"], "sector_blocked")

    def test_missing_capex_blocks(self):
        rows = sample()
        rows[1]["metrics"].pop("capex")
        rows[1]["fcf_usd"] = None
        quality = {"latest_fy_age_days": 200}
        quality_normalize({}, rows, quality, "CPRT", dt.date(2026, 10, 24))
        self.assertIsNone(quality["normalized_fcf_3y_usd"])

    def test_wc_movement_blocks(self):
        rows = sample()
        facts = {"us-gaap": {
            "AccountsReceivableNetCurrent": {"units": {"USD": []}},
            "InventoryNet": {"units": {"USD": []}},
            "AccountsPayableCurrent": {"units": {"USD": []}},
        }}
        for i, row in enumerate(rows):
            end = row["fy_end"]
            for tag, val in (
                ("AccountsReceivableNetCurrent", [10, 120, 125][i]),
                ("InventoryNet", 10),
                ("AccountsPayableCurrent", 10),
            ):
                facts["us-gaap"][tag]["units"]["USD"].append(fact(val, end, tag))
        quality = {"latest_fy_age_days": 200}
        quality_normalize(facts, rows, quality, "CPRT", dt.date(2026, 10, 24))
        self.assertEqual(quality["normalized_fcf_status"], "working_capital_review")
        self.assertIsNone(quality["normalized_fcf_3y_usd"])

    def test_multiclass_manual_review(self):
        q = {"latest_diluted_shares": 500000000,
             "diluted_shares_proxy_available": True}
        rec = current_share_reconciliation({}, "GOOGL", q, dt.date(2026, 10, 24))
        self.assertEqual(rec["status"], "manual_review")
        self.assertTrue(rec["complex_multiclass"])

    def test_recent_cover_shares_and_quarter_dilution(self):
        facts = {
            "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [{
                "val": 500000000,"end": "2026-09-30","filed":"2026-10-15",
                "form":"10-Q","accn":"0000000000-26-000001",
            }]}}},
            "us-gaap": {"WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [{
                "val": 503000000,"start":"2026-07-01","end":"2026-09-30",
                "filed":"2026-10-15","form":"10-Q","accn":"0000000000-26-000001",
            }]}}},
        }
        q = {"latest_diluted_shares": 505000000,
             "diluted_shares_proxy_available": True}
        rec = current_share_reconciliation(facts, "CPRT", q, dt.date(2026,10,24))
        self.assertEqual(rec["status"], "provisional_reconciled")
        self.assertEqual(rec["provisional_diluted_shares"], 503000000)
        self.assertNotEqual(rec["latest_basic"]["value"], rec["latest_quarter_diluted"]["value"])


if __name__ == "__main__":
    unittest.main()
