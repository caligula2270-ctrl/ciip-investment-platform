# Quality & Value Radar — auditoría permanente v10

## Objeto
Verificar la consistencia entre la arquitectura económica y las cifras contables antes de aceptar un precio objetivo. Fuentes con URL, moneda, fecha y tratamiento contable en `data/financial_bridge_sources_v10.json`; comprobaciones reproducibles en `scripts/financial_audit_v10.py`; resultados en `data/financial_audit_v10.json`. La ejecución de GitHub Actions semanal incorpora estos controles.

## Puentes financieros
- Adobe/Intuit/Copart: CFO-CAPEX-SBC es una aproximación a caja **para el accionista después de intereses**, no FCFF desapalancado. No restar deuda íntegra sin modificar la definición; analizar caja no operativa, inversiones, financiación de recompras, nuevos préstamos y adquisiciones. La caja de clientes de Intuit se excluye como caja libre del grupo.
- Constellation: FCFA2S ya se presenta después de pagos específicos a minoritarios, interés y arrendamientos bajo su definición de emisor. Comprobar notas y etiquetas antes de ajustes adicionales. Separar el coste de adquisiciones de flujos incrementales y evitar financiar el mismo gasto dos veces.
- ASML: NOPAT−reinversión como aproximación FCFF. Al valor operativo se suman caja e inversiones líquidas corporativas y se resta deuda; se muestra separado el caso con arrendamientos. Es un puente **histórico 2025**, incompatible con un precio objetivo vigente sin roll-forward hasta la fecha inicial del DCF. Inversiones no operativas, intereses minoritarios y claims sin valorar quedan abiertos.
- Dino: flujos operativos desapalancados y deuda neta reportada con leases. Si los arrendamientos forman parte de los costes operativos, descontarlos de nuevo puede duplicar el efecto. El valor ajustado es una prueba de coherencia, no una valoración definitiva.

## Reinversión
- Adobe/Intuit: construir margen de FCF/SBC sobre **parejas del mismo ejercicio**. Conciliar Semrush, financiación de recompras y nuevas acciones; no contar dos veces SBC.
- Copart: fecha de adquisición de ACV posterior al último balance auditado. Exige balance proforma; la consideración pagada no es todo el capital económico invertido.
- Constellation: retorno incremental de cohortes, precio pagado, intereses, earnouts, minoritarios y reinversión posterior.
- ASML: NOPAT, depreciación, CAPEX, inventarios, anticipos de clientes, R&D y reinversión; no descontar R&D dos veces.
- Dino: productividad por cohortes de tiendas, mantenimiento real, logística y capital circulante; el cociente CAPEX total/aperturas no equivale al coste de una tienda.

## Reglas
Los importes de liquidación y balance están fechados y nunca se deben presentar como «actuales» en el sentido bursátil. `signalsAllowed=false`, `verifiedEquityTargets=0` y `approvedEquityTarget=null` hasta conciliación satisfactoria. Las próximas ejecuciones volverán a calcular las pruebas, pero las cifras fijas del registro de fuentes requieren renovación al publicarse nuevos informes oficiales.
