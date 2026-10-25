# CIIP | Auditoría y validación de cinco DCF

**Veredicto global: Not ready.** No utilizar estos modelos para órdenes de inversión hasta resolver P0, revisar denominadores, sensibilidad y caja.

| Compañía | Veredicto | P0 | P1 | DCF base USD |
|---|---|---:|---:|---:|
| ADBE | Ready with caveats | 0 | 3 | 265.78 |
| MSFT | Ready with caveats | 0 | 4 | 167.99 |
| V | Ready with caveats | 0 | 4 | 210.64 |
| MA | Ready with caveats | 0 | 3 | 383.66 |
| TXN | Ready with caveats | 0 | 3 | 97.4 |

## Adobe
Dictamen: Ready with caveats

### Hallazgos y medidas
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).
- **P1 Unsupported assumption**: Adobe recurring future M&A reserve 350m is an analyst stress, not proved recurring. Impacto: Revenue growth and acquisition cadence must be connected. Acción: Build explicit business acquisition dependence scenarios and reconcile organic growth. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).
- **P1 Unsupported assumption**: Adobe base cash 6500m vs FY2025 CFO-CAPEX-SBC 7910m. Impacto: Forecast SBC, AI economics and M&A not connected to operating schedules. Acción: Forecast revenue/margins/SBC/acquisition reinvestment separately. [Fuente](https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm).

### Sensibilidad independiente (solo diagnóstico)
- cash_80pct_usd: 212.62 USD/acción
- cash_120pct_usd: 318.94 USD/acción
- cost_of_equity_plus_2pp_usd: 210.12 USD/acción
- cost_of_equity_minus_2pp_usd: 359.01 USD/acción
- cost_of_equity_12pct_usd: 221.81 USD/acción
- cost_of_equity_15pct_usd: 165.86 USD/acción

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Adobe FY2025 CFO and CAPEX tie-out
- PASS: Adobe acquisition separate strategic reinvestment bridge
- PASS: Adobe source CFO-CAPEX-SBC bridge

## Microsoft
Dictamen: Ready with caveats

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 67.26%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).
- **P1 Unsupported assumption**: Microsoft first-stage 13% growth applied to a lease-adjusted $51.481bn base is not justified by a five-year datacenter segment forecast. Impacto: Uncertain server replacement economics and growth spending. Acción: Build asset replacement, cloud margin and AI return-on-capital forecasts. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).
- **P1 Not comparable without bridge**: New finance-lease datacenter assets and future server renewal not captured as current cash CAPEX. Impacto: Long-run owner cash still uncertain. Acción: Model lease principal beyond FY2026 and noncash server investment commitments. [Fuente](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).

### Sensibilidad independiente (solo diagnóstico)
- cash_80pct_usd: 134.39 USD/acción
- cash_120pct_usd: 201.59 USD/acción
- cost_of_equity_plus_2pp_usd: 129.09 USD/acción
- cost_of_equity_minus_2pp_usd: 235.95 USD/acción
- cost_of_equity_12pct_usd: 129.09 USD/acción
- cost_of_equity_15pct_usd: 94.62 USD/acción

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Microsoft reported FY2026 CFO CAPEX
- PASS: Microsoft FY2026 CFO less CAPEX SBC and lease principal owner-cash bridge

## Visa
Dictamen: Ready with caveats

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 65.35%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm).
- **P1 Not comparable without bridge**: Visa 1,898m weighted diluted Q2 EPS less 1.104m Sep conversion reduction is not shares currently outstanding. Impacto: Open-market repurchases and awards between June and October remain unverified. Acción: Update subsequent event/share-repurchase rollforward before approving price per share. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316126000121/v-20260918.htm).
- **P1 Unsupported assumption**: Visa CFO depends on client incentives, litigation and escrow. Impacto: Recurring cash can depart from operating CFO-CAPEX. Acción: Bridge 5Y incentive payments, litigation cash and restricted funds. [Fuente](https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm).

### Sensibilidad independiente (solo diagnóstico)
- cash_80pct_usd: 168.51 USD/acción
- cash_120pct_usd: 252.77 USD/acción
- cost_of_equity_plus_2pp_usd: 163.21 USD/acción
- cost_of_equity_minus_2pp_usd: 293.18 USD/acción
- cost_of_equity_12pct_usd: 163.21 USD/acción
- cost_of_equity_15pct_usd: 120.96 USD/acción

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Visa 5Y issuer-filed CAPEX reconciled to source separate from SEC taxonomy
- PASS: Visa June Class A diluted EPS denominator less September documented B conversion reduction

## Mastercard
Dictamen: Ready with caveats

### Hallazgos y medidas
- **P1 Unsupported assumption**: optimista terminal weight 65.17%. Impacto: High sensitivity to long-run economics. Acción: Stress terminal spread and exit economics.
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm).
- **P1 Not comparable without bridge**: Settlement and client incentive payments drive CFO. Impacto: Unadjusted FCF may not represent cash to shareholders. Acción: Reconcile 5Y payments incentives and accrued settlement. [Fuente](https://www.sec.gov/Archives/edgar/data/1141391/000114139126000013/ma-20251231.htm).

### Sensibilidad independiente (solo diagnóstico)
- cash_80pct_usd: 306.93 USD/acción
- cash_120pct_usd: 460.39 USD/acción
- cost_of_equity_plus_2pp_usd: 297.27 USD/acción
- cost_of_equity_minus_2pp_usd: 534.01 USD/acción
- cost_of_equity_12pct_usd: 297.27 USD/acción
- cost_of_equity_15pct_usd: 220.31 USD/acción

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: Mastercard 5Y reported GAAP net income cash-to-earnings source bridge

## Texas Instruments
Dictamen: Ready with caveats

### Hallazgos y medidas
- **P1 Not comparable without bridge**: Current diluted shares assembled from dated basic outstanding and weighted-average EPS dilution. Impacto: Forward share count can depart from observed EPS weighted average. Acción: Reconcile outstanding classes, options, RSUs, convertibles and subsequent events. [Fuente](https://www.sec.gov/Archives/edgar/data/97476/000009747626000169/txn-20260930.htm).
- **P1 Unsupported assumption**: TXN analyst cycle reserve $1.818bn used to adjust 2026 LTM GAAP FCF is not equivalent to audited maintenance CAPEX. Impacto: Longer-run fab utilization and capital replacement schedule not demonstrated. Acción: Reconcile utilization, inventory and facility CAPEX commitments through 2030. [Fuente](https://www.sec.gov/Archives/edgar/data/97476/000009747626000169/txn-20260930.htm).
- **P1 Not comparable without bridge**: CHIPS subsidy receipts are not necessarily recurring. Impacto: Cannot treat management adjusted FCF as perpetual owner cash. Acción: Keep GAAP CFO-CAPEX separate from government grant proceeds. [Fuente](https://www.ti.com/about-ti/newsroom/news-releases/2026/2026-10-21-ti-reports-third-quarter-2026-financial-results-and-shareholder-returns.html).

### Sensibilidad independiente (solo diagnóstico)
- cash_80pct_usd: 77.92 USD/acción
- cash_120pct_usd: 116.88 USD/acción
- cost_of_equity_plus_2pp_usd: 77.77 USD/acción
- cost_of_equity_minus_2pp_usd: 129.32 USD/acción
- cost_of_equity_12pct_usd: 81.93 USD/acción
- cost_of_equity_15pct_usd: 61.85 USD/acción

### Controles realizados
- PASS: Shares bound correctly
- PASS: DCF arithmetic conservador
- PASS: DCF arithmetic base
- PASS: DCF arithmetic optimista
- PASS: TI LTM adjusted FCF bridge
- PASS: TI LTM 2026 GAAP CFO-CAPEX less through-cycle analyst reserve

## Política de decisiones
Las hipótesis originales no se sustituyen silenciosamente. Los valores por acción actuales son referencias de un DCF de investigación, no precios aprobados.
Se requiere aprobación documental, puente financiero real y contraste independiente.
