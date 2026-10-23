# Motor fundamental QVR v2 — octubre 2026

## Mejoras integradas
1. **Trimestrales y TTM**: para emisores estadounidenses con 10-K/10-Q compatibles, calcula `FY último + YTD último - YTD comparable`. Conserva fecha de cierre, fecha de presentación, componentes y ausencia de datos cuando la reconciliación es incompleta. FCF TTM = CFO TTM menos CAPEX TTM. No extrapola trimestrales.
2. **ROIC ajustado**: NOPAT = EBIT reportado por (1−tasa fiscal efectiva entre 8% y 40%; fallback 25% documentado). Divide entre capital invertido medio de principio y final de ejercicio (patrimonio + deuda + pasivos de arrendamiento publicados − caja excedentaria, dejando 2% de ventas como caja operativa). Se exige una mediana de al menos 3 años comparables. El ROIC sin goodwill se muestra solo como sensibilidad, nunca para el filtro automático. Incongruencias o falta de deuda publicada bloquean el filtro.
3. **Cobertura internacional**: datos primarios con fecha y divisa en `data/international.json` para CSU (Q2/2026, USD/IFRS), ASML (Q3/2026, EUR) y Dino Polska (H1/2026, PLN/IFRS). Fichas accesibles en Radar; **no se les atribuye valor intrínseco automático** mientras falte serie de FCF, acciones diluidas, ajustes contables y conversión de divisa congruente.

## Integración
- `scripts/build_intrinsic_radar.py`: modelo anual base SEC.
- `scripts/enrich_sec_metrics.py`: reconciliación 10-Q TTM y ROIC ajustado.
- `.github/workflows/qvr-intrinsic.yml`: ejecuta ambos cada miércoles o mediante Run workflow y publica GitHub Pages.
- `app.js`: muestra el ROIC ajustado, el estado del TTM y fichas internacionales.
- `data/intrinsic.json`: resultados de producción, **solo se actualizará a v2 tras la primera ejecución del workflow nuevo**.

## Salvaguardas
- El precio objetivo mixto anual no se reemplaza automáticamente con FCF TTM: este último se muestra como contraste, porque requiere normalización y análisis de estacionalidad.
- No se consideran baratas las empresas sin ROIC ajustado con capital medio validado.
- El ROIC ajustado **no es auditado**: necesita comprobación de adquisiciones, caja operativa real, deuda, leasing, impuestos y compensación basada en acciones.
- Ni las fuentes internacionales ni un resultado técnico verde bastan para certificar infravaloración.
