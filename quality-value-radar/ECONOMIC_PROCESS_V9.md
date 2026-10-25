# QVR v9 — Modelos económicos específicos por sector

Cada ejecución de `.github/workflows/qvr-intrinsic.yml` construye `data/economic_v9.json` leyendo `data/economic_drivers_v9.json` y los datos oficiales/conciliaciones disponibles de versiones v4–v8.

## Modelos
- **Adobe:** ingresos FY2026 guiados, escenarios de crecimiento posterior, conversión a owner FCF normalizada de CFO-CAPEX-SBC, posible margen de integración Semrush, emisiones/recompras netas por acción. Sin ROI post-adquisición observado y sin guía corporativa de FCF.
- **Intuit:** ingresos FY2027 guiados, hipótesis de margen y crecimiento posterior. El modelo no extrapola ciegamente el pico estacional fiscal ni certifica el flujo de Consumer frente al Business Segment.
- **Copart:** núcleo orgánico basado en owner FCF, CAPEX normalizado, flujo incremental comprado de ACV y capital desembolsado una sola vez. **El estado proforma y el FCF incremental de ACV no están auditados**.
- **Constellation:** FCFA2S en USD, flujo retenido para adquisiciones, cohortes compradas que empiezan a devolver caja tras un retraso, crecimiento orgánico y FX CAD/USD. Rendimiento incremental adquirido = hipótesis, no IRR histórico.
- **ASML:** previsión de ingresos, escenario de EBIT ajustado por impuestos y ratio de reinversión que incluye CAPEX/circulante. Representa una aproximación FCFF; no se puede presentar como valor del accionista sin puente EV-deuda-caja.
- **Dino Polska:** centros existentes + nuevas tiendas, venta media por tienda, crecimiento LFL, EBIT/tasa fiscal, CAPEX mantenimiento supuesto, coste por nueva apertura, logística y capital circulante. La maduración por cohortes y la financiación de arrendamientos no están conciliadas.

## Salvaguardas
- Todos los parámetros de escenarios son hipótesis observables/editables versionadas; los datos oficiales tienen URLs y periodos distintos.
- Usar una cifra en `officialKpis` exige comprobar su consistencia con el PDF/10-K antes de elevar su confianza; no equivale a validación independiente automática.
- Los resultados se publican como `illustrative` o `illustrative_unreconciled_equity_proxy`, NO precios objetivos, NO recomendaciones.
- `signalsAllowed=false` y `verifiedBuyPrice=null` obligatorios. Las diferencias entre v6 y v9 ayudan a diagnosticar errores de modelo, no acreditan infravaloración.
- El cash flow antes de adquisiciones no se puede distribuir y reinvertir simultáneamente.
- La SBC no puede descontarse dos veces junto a emisiones brutas de acciones.
- Para aprobar una valoración: revisar cifras fuente, ROIC/ROI incremental, capex recurrente, deuda, caja, acciones actuales efectivamente diluidas, impuestos, circulante y escenarios macro. 

## Futuras ejecuciones
Los cambios de parámetros y motores se versionan con SHA en GitHub; el workflow recalcula automáticamente los modelos sectoriales, publica datos y ejecuta sus controles. Esta documentación y el JSON constituyen memoria procedimental estable del radar.
