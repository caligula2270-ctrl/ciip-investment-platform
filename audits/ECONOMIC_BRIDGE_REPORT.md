# CIIP Economic Bridge Review v2

Date: 2026-10-27. Status: **ECONOMIC_BRIDGES_PARTIAL_FORECAST_NOT_SIGNED**.
Legacy DCF assumptions and share-count estimates are NOT overwritten.

| Ticker | Legacy base DCF $/share | Reported arithmetic | Unresolved economic dependencies | Portfolio use |
|---|---:|---|---:|---|
| ADBE | 265.78 | PASS | 3 | BLOCKED |
| MSFT | 167.99 | PASS | 2 | BLOCKED |
| V | 210.64 | PASS | 2 | BLOCKED |
| MA | 383.66 | PASS | 3 | BLOCKED |
| TXN | 97.40 | PASS | 2 | BLOCKED |

## ADBE

**Reconciled reported / historical quantities**
- PASS FY25 CFO-PPE CAPEX-SBC: 7,910.000 vs 7,910.000 USD m
- PASS 9M26 CFO-PPE CAPEX-SBC: 5,884.000 vs 5,884.000 USD m

**Double-counting rules**
- Semrush historical purchase is spent, do not subtract again from FY2025 cash anchor.
- The legacy model grows net initial cash; a fixed annual M&A reserve would instead be a separate annual deduction, not algebraically identical.

**Economic model remains blocked on**
- M&A recurrence and organic growth: No disclosed annual recurring acquisition programme substantiates $350m/yr.
- Topaz conditional completion: As-of filing disclosed $340m pending; do not assume close or future contribution.
- Economic SBC compensation: SBC-as-cash proxy and diluted share awards jointly require checks for double charge.

Source URLs:
- https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm

## MSFT

**Reconciled reported / historical quantities**
- PASS FY26 full historical owner proxy: 51,481.000 vs 51,481.000 USD m
- PASS Finance lease payment face vs liabilities plus undiscounted interest: 89,686.000 vs 89,686.000 USD m

**Double-counting rules**
- Exclude finance lease interest from additional FCFE subtraction if already inside CFO.
- Never deduct 24,608m ROU noncash additions as if current-period cash CAPEX.
- Uncommenced leases are not the same as $329.1bn currently drawn debt.

**Economic model remains blocked on**
- Lease commencement calendar: No exact years, financing type and incremental margin for $329.1bn uncommenced arrangements.
- AI/data center reinvestment economics: 13% 5Y annual growth of lease-adjusted owner cash requires segment profitability and server renewal forecasts.

Source URLs:
- https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm

## V

**Reconciled reported / historical quantities**
- PASS 9M26 PPE cash FCF proxy: 15,164.000 vs 15,164.000 USD m
- PASS 9M26 incentives accrual/cash movement: 73.000 vs 73.000 USD m
- PASS 9M25 incentives accrual/cash movement: 250.000 vs 250.000 USD m

**Double-counting rules**
- Litigation accrual movements already embedded in reported CFO must not be independently deducted twice.
- Do not include restricted cash in shareholder distributable cash.

**Economic model remains blocked on**
- 5Y incentive timing: Only two comparable nine-month observations here; five full audited annual schedules not reconstructed.
- Current fully diluted Class A equivalents: Date-mixed September conversion and Q2 weighted shares remain a diagnostic denominator.

Source URLs:
- https://www.sec.gov/Archives/edgar/data/1403161/000140316126000104/v-20260630.htm

## MA

**Reconciled reported / historical quantities**
- PASS FY25 PPE+capitalized software FCF: 16,433.000 vs 16,433.000 USD m
- PASS H1 2026 PPE+capitalized software FCF: 5,959.000 vs 5,959.000 USD m
- PASS H1 2025 PPE+capitalized software FCF: 6,417.000 vs 6,417.000 USD m

**Double-counting rules**
- Capitalized software is an investing cash expense, do not report PPE-only as all-in FCF.
- BVNK $1.5bn contractual price is not evidence for $1.5bn actual closing cash outflow.

**Economic model remains blocked on**
- Customer incentives/settlement normalization: Prepaid incentives and settlement liability cash schedules need 5Y annual tie-outs.
- BVNK deal and return on capital: Closed acquisition, but exact post-close cash paid, funding and cash contribution are not established.
- Sector income cap discrepancy: Sector model uses 12,230m vs per-share 16,000m initial owner cash, requiring explicit common methodology.

Source URLs:
- https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm
- https://www.sec.gov/Archives/edgar/data/1141391/000114139126000083/ma-20260630.htm
- https://investor.mastercard.com/investor-news/investor-news-details/2026/Mastercard-completes-acquisition-of-BVNK-to-advance-global-stablecoin-capabilities/default.aspx

## TXN

**Reconciled reported / historical quantities**
- PASS GAAP LTM CFO-CAPEX: 7,318.000 vs 7,318.000 USD m
- PASS Company adjusted FCF bridge direct government cash: 8,422.000 vs 8,422.000 USD m
- PASS Legacy analyst reserve reconciliation: 5,500.000 vs 5,500.000 USD m

**Double-counting rules**
- GAAP CFO includes $469m credit benefit; do not add it to historical cash a second time.
- $1,104m direct grant investing cash appears only in adjusted measure, not GAAP CFO minus gross CAPEX.
- An undrawn $5bn credit facility does not represent debt until borrowed.

**Economic model remains blocked on**
- Fab capacity and sustaining CAPEX: No facility-level replacement CAPEX, utilization cycle or 2030 demand schedule validating $1.818bn reserve.
- Silicon Labs pending acquisition: No approved post-close transaction sources/uses, financing expense or acquired operating cash forecast.

Source URLs:
- https://www.sec.gov/Archives/edgar/data/97476/000009747626000169/txn-20260930.htm
- https://investor.ti.com/news-releases/news-release-details/ti-reports-third-quarter-2026-financial-results-and-shareholder

## Decision controls
- PASS means arithmetic tied to explicitly logged evidence, NOT an independent financial statement audit.
- Reported facts, derived historical numbers, and analyst estimates are never interchanged.
- No issuer can be READY while forward economic schedules or current share capital remain unverified.
- No change to old scenario parameters, reported legacy per-share values, or signoff.
