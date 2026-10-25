import datetime as dt
import json
import unittest
from ciip_economic_bridge_v2 import build, ROOT

def read(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

class TestEconomicBridgeV2(unittest.TestCase):
    def test_five_sources_reconcile_and_no_approval(self):
        e=read("audits/economic_evidence_v2.json")
        a=read("audits/per_share_inputs.json")
        m=read("audits/per_share_latest.json")
        result=build(e,a,m,dt.date(2026,10,25))
        self.assertEqual(set(result["companies"]),{"ADBE","MSFT","V","MA","TXN"})
        for t,row in result["companies"].items():
            self.assertTrue(row["hard_data_pass"],t)
            self.assertFalse(row["valuation_approved"])
            self.assertEqual(row["legacy_base_per_share_unchanged_usd"],m["companies"][t]["scenario_values"]["base"]["equity_per_share_usd"])
        self.assertEqual(result["companies"]["MA"]["reported_2025_comparability"]["reconciled_2025_investing_FCF_m"],16433)
        self.assertEqual(result["companies"]["TXN"]["cycle_cash"]["reported_GAAP_FCF_m"],7318)
    def test_modified_reported_figure_blocks(self):
        e=read("audits/economic_evidence_v2.json")
        a=read("audits/per_share_inputs.json")
        m=read("audits/per_share_latest.json")
        e["companies"]["MA"]["fy2025"]["capitalized_software"]+=30
        with self.assertRaises(ValueError):
            build(e,a,m,dt.date(2026,10,25))

if __name__=="__main__":unittest.main()
