# Quality & Value Radar — Política permanente de inversión v5

## Ejecución obligatoria
La tarea semanal «QVR Valoración Fundamental Semanal» ejecuta en este orden: descarga 10-K y precios, 10-Q TTM, ROIC, revisión de CFO−CAPEX−SBC y adquisiciones, DCF internacional, y finalmente **reliability_v5.py**. Cada resultado conserva versión, procedencia, fecha y razón de bloqueo en JSON. La política `data/reliability_policy.json` es la especificación persistente; cualquier nueva versión debe actualizarla y probarse antes de sustituirla.

## Retorno sobre capital invertido en adquisiciones
- Registro por operación con entidad adquirida, anuncio, cierre, contraprestación, deuda y caja asumidas, costes de integración e inversión posterior cuando estén publicados.
- Retorno realizado = incremento atribuible de NOPAT normalizado (o FCF del propietario incremental, indicando la definición) / capital all-in invertido. Requiere estados comparables posteriores, idealmente dos periodos, eliminación de crecimiento orgánico, sinergias y efecto divisa.
- Sin desglose de la adquirida o serie pro forma, reportar **retorno no verificable**, nunca ROIC cero ni una rentabilidad inventada.
- Para Copart/ACV 1.900 MUSD de contraprestación anunciada × 12 % = **228 MUSD/año** como referencia de caja incremental requerida, NO como resultado realizado. El denominador final puede cambiar por deuda, caja, contraprestación y costes.
- Para Constellation, no confundir FCFA2S (antes de adquisiciones) con caja libre después de compras. Pedir información de cohortes y rentabilidad por adquisición antes de extrapolar el crecimiento inorgánico.

## CAPEX
- CFO−CAPEX reportado sigue siendo la base de caja verificable.
- Solo clasificar CAPEX de mantenimiento/crecimiento como datos reales si la dirección lo separa expresamente, con página/periodo y conciliación al CAPEX total. No utilizar D&A como mantenimiento «real».
- En ausencia de desglose, mostrar **no verificable** y, cuando se desarrollen escenarios por aproximaciones, etiquetarlos estimaciones y documentar fórmula, rango y margen. El CAPEX de Dino requiere separar aperturas de tiendas, logística, remodelaciones y necesidades recurrentes.

## Previsiones
- Distinguir cuatro clases: (1) guías oficiales de la compañía, (2) estimaciones de consenso independiente con licencia/fuente y fecha, (3) proyecciones *model-derived* basadas en márgenes históricos, (4) crecimiento *reverse DCF* implícito en precios.
- La guía de ingresos × margen FCF histórico es un **escenario del sistema**, nunca una previsión corporativa de caja libre.
- Bloquear señales si no se valida un flujo futuro por acción teniendo en cuenta SBC, adquisiciones, inversiones, deuda y crecimiento.
- Adobe FY2026, Intuit FY2027 y ASML FY2026 tienen guías de ingresos fechadas registradas en `data/reliability_policy.json`; requieren revalidación después de cada nueva publicación.

## Seguridad financiera y técnica
Cada corrida escribe `data/reliability_v5.json` y mantiene `signalsAllowed=false` hasta superar todos los requisitos. El motor preserva campos de origen y ausencia de datos. GitHub Actions ejecuta comprobaciones de integridad. Un workflow verde indica que el proceso terminó, **no** que se haya conseguido verificar un ROI ni que haya oportunidades de compra.

## Mantenimiento futuro
La fuente de persistencia es este repositorio, no la memoria informal de una conversación. Especificaciones y código: `data/reliability_policy.json`, `scripts/reliability_v5.py`, `.github/workflows/qvr-intrinsic.yml`. Cada nueva regla debe añadirse como criterio versionado al JSON y validarse con pruebas automáticas.
