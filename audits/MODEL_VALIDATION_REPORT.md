# CIIP | Auditoría y validación de cinco DCF

**Veredicto global: Not ready.** No utilizar estos modelos para órdenes de inversión hasta resolver P0, revisar denominadores, sensibilidad y caja.

| Compañía | Veredicto | P0 | P1 | DCF base USD |
|---|---|---:|---:|---:|
| ADBE | Not ready | 1 | 2 | 280.9 |
| MSFT | Not ready | 1 | 3 | 293.68 |
| V | Not ready | 2 | 3 | 211.27 |
| MA | Not ready | 1 | 3 | 383.66 |
| TXN | Not ready | 1 | 2 | 97.4 |

## Adobe
Dictamen: Not ready

### Hallazgos y medidas
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).
- **P0 Unsupported assumption**: Adobe 9M2026 acquisitions cash 1560m omitted from normalized owner cash. Impacto: If acquisitions sustain growth, cost of reinvestment understated. Acción: Model acquisitions separately from ordinary CAPEX, without assuming every acquisition repeats. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).
- **P1 Unsupported assumption**: Adobe base cash 6500m vs FY2025 CFO-CAPEX-SBC 7910m. Impacto: Forecast SBC, AI economics and M&A not connected to operating schedules. Acción: Forecast revenue/margins/SBC/acquisition reinvestment separately. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Adobe FY2025 CFO and CAPEX tie-out
- PASS: Adobe source CFO-CAPEX-SBC bridge

## Microsoft
Dictamen: Not ready

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 67.26%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).
- **P0 Unsupported assumption**: Base cash 90000m vs FY2026 CFO-CAPEX-SBC 54582m. Impacto: Large unverified increase before first forecast growth year. Acción: Build five-year AI capacity, renewal, finance lease principal and cloud margins bridge. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).
- **P1 Not comparable without bridge**: Finance lease principal/new financed datacenter assets omitted from simplistic cash CAPEX. Impacto: Reinvestment understates capital intensity. Acción: Bridge leases, depreciation, server capacity and cash/noncash investment. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Microsoft reported FY2026 CFO CAPEX

## Visa
Dictamen: Not ready

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 65.35%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm).
- **P0 Not comparable without bridge**: Visa lacks comparable annual CAPEX in generic SEC facts. Impacto: FCF series is missing, cash normalization is not reproducible. Acción: Implement issuer-specific XBRL/footnote mapping for property and technology spend. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm).
- **P0 Not comparable without bridge**: Visa B-class, preferred and participating-security denominator mixes different dates. Impacto: A-equivalent fully diluted share count unapproved. Acción: Reconcile September 2026 8-K class factors with same-date counts and litigation rights. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316126000121/v-20260918.htm).
- **P1 Unsupported assumption**: Visa CFO depends on client incentives, litigation and escrow. Impacto: Recurring cash can depart from operating CFO-CAPEX. Acción: Bridge 5Y incentive payments, litigation cash and restricted funds. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm).

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista

## Mastercard
Dictamen: Not ready

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 65.17%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm).
- **P0 Source contradiction**: Mastercard SEC normalized net income missing; audited FY2025 note cites 14968m. Impacto: Cash/earnings normalization and sector payment model blocked. Acción: Map issuer-specific net income US-GAAP concept with filing year matching. [Fuente](https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm).
- **P1 Not comparable without bridge**: Settlement and client incentive payments drive CFO. Impacto: Unadjusted FCF may not represent cash to shareholders. Acción: Reconcile 5Y payments incentives and accrued settlement. [Fuente](https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm).

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista

## Texas Instruments
Dictamen: Not ready

### Hallazgos y medidas
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/97476/000009747626000169/txn-20260930.htm).
- **P0 Unsupported assumption**: TI base cash 5500m vs FY2025 FCF 2603.0m. Impacto: High assumption for fab utilization and CAPEX reset. Acción: Construct through-cycle capacity utilization, CHIPS, depreciation and CAPEX plan. [Fuente](https://www.sec.gov/Archives/edgar/data/97476/000009747626000169/txn-20260930.htm).
- **P1 Not comparable without bridge**: CHIPS subsidy receipts are not necessarily recurring. Impacto: Cannot treat management adjusted FCF as perpetual owner cash. Acción: Keep GAAP CFO-CAPEX separate from government grant proceeds. [Fuente](https://www.ti.com/about-ti/newsroom/news-releases/2026/2026-10-21-ti-reports-third-quarter-2026-financial-results-and-shareholder-returns.html).

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: TI LTM adjusted FCF bridge

## Política de decisiones
Las hipótesis originales no se sustituyen silenciosamente. Los valores por acción actuales son referencias de un DCF de investigación, no precios aprobados.
Se requiere aprobación documental, puente financiero real y contraste independiente.
