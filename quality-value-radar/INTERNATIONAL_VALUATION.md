# Valoración internacional v3 (reproducible)

## Series primarias (millones en moneda reportada)
- **Constellation Software (CSU.TO)**: FCFA2S USD 2023 1.160, 2024 1.472, 2025 1.683. FCFA2S es **no IFRS** y **antes de adquisiciones**; la caja de adquisiciones es fundamental para el negocio. Acciones 21,19153 millones (verificar eventuales emisiones). [Resultados 2025](https://www.csisoftware.com/constellation-software-inc-announces-results-for-the-fourth-quarter-and-year-ended-december-31-2025-and-declares-quarterly-dividend/) y [2024](https://www.csisoftware.com/constellation-software-inc-announces-results-for-the-fourth-quarter-and-year-ended-december-31-2024-and-declares-quarterly-dividend/).
- **ASML (NASDAQ:ASML)**: FCF EUR 2023 3.247,2, 2024 9.083,1, 2025 11.027,3. 385.417665 millones de acciones en circulación al cierre 2025. Datos SEC [2025](https://www.sec.gov/Archives/edgar/data/937966/000162828026011378/asml-20251231.htm) y [2024](https://www.sec.gov/Archives/edgar/data/937966/000093796625000009/asml-20241231.htm). El FCF reportado por ASML es una métrica no GAAP.
- **Dino Polska (DNP.WA)**: CFO menos capex PLN: 2023 1.772−1.173=599; 2024 2.557−1.562=995; 2025 2.697−2.087=610. Tras el split 10:1 del 31/07/2025, 980,4 millones de acciones. [Presentación FY2025](https://grupadino.pl/wp-content/uploads/2026/03/Dino-Polska-2025-results-presentation.pdf), [Series oficiales](https://grupadino.pl/en/selected-financial-data/) y [Split](https://grupadino.pl/raport-biezacy-nr-10-2025-oswiadczenie-kdpw-w-sprawie-wyznaczenia-dnia-podzialu-splitu-akcji-dino-polska-s-a/).

## Modelo y estados
- `scripts/value_international.py`: mediana FCF/acción de los tres ejercicios y DCF a cinco años con crecimiento base, prudente y optimista. Los supuestos y flujos quedan en el JSON; **no** es valor intrínseco auditado.
- Constellation: tipo USD/CAD; ASML: EUR/USD; Dino: PLN/PLN (sin conversión). Se consulta Yahoo Finance para FX; la cotización y el tipo de cambio han de corresponder a fechas con una diferencia máxima de cinco días.
- Si no hay datos de cambio fiables, marca `fx_or_quote_unavailable`. No se guarda un valor convertido ficticio.
- `international.json` se actualiza al ejecutar `QVR Valoración Fundamental Semanal`; antes de la primera ejecución nueva solo aparecen fichas internacionales y no valores automáticos.
- **El sistema no etiqueta a ninguna de estas tres compañías como barata** por un DCF aislado. Falta contrastar ROI(C) normalizado, adquisiciones, FCF disponible después de crecimiento y múltiplos relativos independientes.
- Copart: `enrich_sec_metrics.py` ahora admite años fiscales concretos con deuda revolvente no dispuesta documentada en los 10-K, sin suponer deuda cero para otros valores. Se conservan los arrendamientos y el capital medio.
