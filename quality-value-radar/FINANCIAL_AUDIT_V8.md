# QVR v8: reconciliación financiera y controles permanentes

## Capital y dilución
El motor reconcilia media anual de acciones diluidas procedente de formularios SEC 10-K con el denominador utilizado en los DCF. Aparte, archiva el número puntual de acciones en circulación y las recompras del ejercicio. **La media diluida no es intercambiable con el saldo puntual**. Los ASR, planes de incentivos, recompras y acciones retenidas por impuestos requieren una conciliación independiente; nunca se supone que un registro S-8 ha generado todas las acciones.

## CAPEX
Se conserva íntegro el CAPEX reportado en CFO-CAPEX-SBC. La matriz conjunta varía CAPEX y número de acciones como **estreses independientes**; no permite certificar qué proporción es mantenimiento. Una reducción de CAPEX sin revisar la tasa de crecimiento no acredita ningún ahorro sostenible. Desagregar solo con datos oficiales y conciliar al flujo consolidado.

## Adquisición de ACV
Separar el valor aproximado de la operación anunciada (~1.900 MUSD), del valor agregado comunicado al cierre para adquisición del control (~1.801,021081 MUSD). Ninguna de estas cifras acredita automáticamente valor empresa, capital empleado final o coste de integración. La aproximación de caja incremental exigida al 12 % sobre el precio comunicado al cierre es **216,12 MUSD/año**, una exigencia hipotética, no un retorno realizado. Las obligaciones asumidas, el efectivo recibido, la financiación, la fecha del cierre y las participaciones no controladoras deben conciliarse antes de un DCF proforma combinado.

## Fuentes y QA
- Datos SEC y notas archivados en `data/source_ledger_v8.json` con URL y fecha.
- `scripts/audit_v8.py` ejecuta conciliaciones e hipótesis conjuntas de CAPEX/dilución y guarda `data/audit_v8.json`.
- `.github/workflows/qvr-intrinsic.yml` exige que los denominadores históricos concilien antes de publicar. Si faltan fuentes o no concilian, debe fallar el control.
- `signalsAllowed=false`, `verifiedBuyPrices=0` y no se produce recomendación de inversión.
- Las hipótesis se aplican automáticamente a siguientes ejecuciones, pero **no** sustituyen verificación de estados oficiales futuros o asesoramiento individual.

## Limitaciones abiertas
Seguimos sin reconciliación completa del CAPEX de mantenimiento, del flujo adquirido de ACV o del capital económico all-in, y sin una política uniforme de acciones corrientes totalmente diluidas en las tres compañías. Por ello no se puede aprobar precio objetivo definitivo ni compra.
