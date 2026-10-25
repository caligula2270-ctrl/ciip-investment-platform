# Conciliación de discrepancias v11 (25 octubre 2026)

## Correcciones ejecutadas
- **ADBE e INTU:** `economic_v9.py` calcula cada flujo del propietario (CFO menos inversión PPE menos SBC) y su margen sobre los **ingresos del mismo ejercicio fiscal**; valida la identidad `ownerCF = FCF − SBC`. Usa mediana de tres márgenes emparejados. Se prohíbe calcular una mediana de flujos de tres ejercicios dividida entre ingresos del año último.
- **INTU:** compras PPE FY2026 175 MUSD frente a CAPEX de definición gerencial más amplia 221 MUSD. Las definiciones se registran por separado; no se añade la diferencia al FCF sin identificar y reconciliar el activo intangible/otros usos.
- **CPRT:** `economic_v9.py` ya no descuenta 1.801,021081 MUSD al valor del flujo adquirido **y** a la liquidez postcierre simultáneamente. El coste de la adquisición solo debe quedar reflejado en el puente de caja/deuda postcierre, aún no publicado; no se calcula precio objetivo aprobado.
- **ASML:** se ha localizado su estado Q3 2026: 8.030,9 MEUR de caja, 4.704,2 MEUR de inversiones a corto plazo y 1.963 MEUR de deuda a largo plazo. No se calcula deuda neta definitiva sin deuda corriente, arrendamientos y derechos de terceros coherentes. El puente de FY2025 se conserva como comparación histórica.
- **DNP.WA:** dos políticas mutuamente excluyentes para arrendamientos: flujos después de pagos + deuda sin leases, o flujos antes de pagos + deuda incluyendo leases. El modelo FCFF existente no tiene conciliado este tratamiento; cualquier objetivo debe bloquearse.
- **CSU.TO:** FCFA2S ya incorpora ajustes a intereses, minoritarios y arrendamientos según la definición informada. No volver a restar partidas sin cambiar base de valoración; rentabilidad incremental de adquisiciones todavía sin observar.

## Pruebas automáticas
`scripts/reconciliation_v11.py` exige tres ejercicios emparejados y unicidad de cierres para Adobe e Intuit, no doble descuento del precio de ACV, y distingue el estado documental de seis empresas. Publica `data/reconciliation_v11.json` y se ejecuta en `.github/workflows/qvr-intrinsic.yml` tras la valoración sectorial. No habilita señales automáticas.

## Cuestiones abiertas con criterio de cierre
Adobe/Intuit: conciliar SBC, operaciones de capital, cuadro financiero actualizado y capacidad repartible del accionista.
Copart: balance proforma post ACV, caja pagada y obligaciones, plus FCF adquirido independiente.
ASML: puente a septiembre 2026 íntegro con deuda corriente, leases y terceros y valoración no operativa.
Dino: cuadro de arrendamientos y recalcular FCFF/FCFE con definición compatible; extraer datos oficiales H1 2026.
Constellation: ROIC por cohortes adquiridas y financiación de adquisiciones (earnouts, minoritarios).
No presentar los precios recalculados como compras hasta cerrar estas evidencias.