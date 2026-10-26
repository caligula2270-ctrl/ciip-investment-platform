# CIIP — Procedimiento persistente de auditoría fundamental v1.5

## Alcance
Investigación de inversiones de MSFT, ADBE, V, MA y TXN. Nunca declarar que existe auditoría contable independiente ni que los precios objetivo están verificados.

## Evidencia oficial
1. SEC EDGAR: 10-K, 10-Q, notas, enmiendas, CIK, accessionNumber, fecha de filing, ejercicio y URL.
2. Notas: EPS, acciones, clases, recompra, dilución, stock compensation, opciones, convertibles, litigios, CAPEX, leasing, adquisiciones y capital circulante.
3. Relaciones con inversores: reconciliar GAAP/no-GAAP e identificar diferencias, sin sustituir SEC.
4. Precios: fuente, moneda, fecha y splits.

Clasificar HECHO / CÁLCULO / HIPÓTESIS / INFERENCIA / NO VERIFICADO. Conservar citas verificables, página o epígrafe, fecha y limitación.

## Cinco ejercicios
- Separar datos anuales 10-K de acumulados trimestrales 10-Q, no mezclar.
- Registrar ingresos, márgenes, beneficio, CFO, CAPEX, FCF, SBC, deuda, acciones, circulante y adquisiciones.
- CAPEX de mantenimiento NO equivale a depreciación. Retener CAPEX total y estrés industrial.
- AR + inventario - proveedores es circulante PARCIAL. Cambios materiales bloquean la valoración.
- Software: sensibilidad a SBC, dilución, IA y recompras (evitar doble conteo).
- Pagos: clases, conversiones, customer incentives, settlement, escrow, litigios; sin per-share automático.
- Industrial: incluir pico CAPEX, ciclo, subvenciones CHIPS y reconciliación GAAP/no-GAAP.

## Capital social
- Los recuentos básicos SEC y media ponderada diluida NO certifican acciones plenamente diluidas actuales.
- Verificar clases de capital, RSU, opciones, warrants, exchangeable shares, splits, buybacks y emisiones posteriores.
- Si no se han leído y conciliado notas: notes_reviewed=false, verified_current_fully_diluted_shares=null, value_per_share=null.
- Detectar nuevos 10-Q/10-K y bloquear firmas anteriores. Las actualizaciones automatizadas NO simulan revisión manual de notas.

## Valoración y decisión
- Modelos independientes de software, pagos e intensivo; escenarios claramente marcados como HIPÓTESIS.
- Normalizar FCF y explicar descuento y valor terminal. Reconciliar deuda/caja y evitar doble contabilización.
- READY solo tras calidad, reconciliación de capital, comparabilidad, análisis de riesgos, precio vigente y revisión humana.
- Se permiten VALORACIONES POR ACCIÓN CONDICIONADAS si el denominador es una fórmula explícita con fuentes y fecha, bandas de dilución y scenario assumptions. NO son precios objetivo aprobados ni fully diluted shares certificados. No generar órdenes ni recomendaciones categóricas.

## Ejecución reproducible
1. scripts/update_fundamentals.py genera fundamentals-auto.json.
2. scripts/build_ciip_audits.py lee audits/evidence.json y fundamentals-auto.json; genera audits/latest.json.
3. GitHub Actions ejecuta tests y estas fases con cron y publicación conjunta.
4. App CIIP consulta fichero reciente sin caché y expone pendientes y fuentes.
5. Cada auditoría futura reutiliza ESTE procedimiento del repositorio; ChatGPT Memory sola no sustituye esta persistencia.

## Valoración individual por acción: procedimiento reutilizable v1.5
1. Verificar 10-K, 10-Q y notas de capital (clases y conversiones, acciones básicas point-in-time, EPS trimestral diluido y antidilutivos, RSU/opciones, recompra y hechos posteriores).
2. Escribir un bloque nuevo en audits/per_share_inputs.json: recuentos, fórmula de conversión en acciones económicamente equivalentes, denominador central, límites mínimo/máximo, fecha exacta, fuentes y estado. No copiar sin verificar los factores de conversión anteriores.
3. Obtener flujo libre normalizado; diferenciar cifra SEC, ajuste propio y flujo forward. NO annualizar interinos automáticamente. Riesgo de doble contar SBC y dilución.
4. Presentar tres casos con crecimiento años 1-5 y 6-10, tasa exigida, tasa terminal, valor explícito y terminal. La caja inicial del modelo se incrementa en el año 1. Los escenarios son hipótesis, no previsiones de la empresa.
5. Dividir valor agregado del accionista entre acciones económicas equivalentes. No sumar caja/restar deuda si ya se descuentan flujos posteriores a intereses (FCFE proxy); si se usa FCFF, hacer puente EV-deuda-caja y excluir doble contabilización.
6. Mostrar banda de dilución y cierre de mercado con fecha, divisa y estado de verificación. Calcular flujo implícito inverso para explicar qué descuenta el mercado.
7. Aprobación: únicamente con conciliación independiente de capital, ajustes de caja/financiación, validación de los escenarios, sensibilidad y evidencia vigente. Estado intermedio SCREEN_GRADE_NOT_DECISION_READY y value_per_share_approved=false.
8. Ejecutar scripts/build_ciip_per_share.py tras scripts/build_ciip_audits.py o refresco diario de market-auto.json. Validar scripts/test_ciip_per_share.py. Publicar audits/per_share_latest.json y audits/PER_SHARE_REPORT.md.
9. Para ampliar el universo, añadir ticker al programa de adquisición SEC, expediente de evidencia con fuentes oficiales y parametrización por acción; ejecutar todos los tests y contrastar que no existan sustituciones silenciosas ni resultados READY automáticos.

## CIIP v1.6 — Auditoría independiente de supuestos y fuentes
- Antes de considerar cualquiera de las cinco valoraciones apta para invertir, reejecutar `scripts/audit_ciip_models.py` y sus pruebas en `scripts/test_ciip_model_validation.py`.
- Auditoría separada de (i) integridad matemática por escenario, (ii) puente contable SEC de CFO y CAPEX, (iii) adquisiciones, stock compensation y capital circulante, (iv) cambios en acciones y derechos económicos, (v) hipótesis forward y concentración de valor terminal.
- Generar `audits/model_validation_latest.json` y `audits/MODEL_VALIDATION_REPORT.md` con severidad P0/P1/P2, fuente, impacto, corrección exigida y veredicto.
- Los valores DCF publicados originalmente quedan inmutables hasta revisión justificada: la prueba de sensibilidad de `±20 %` en caja, `±2 puntos` en tasa exigida y tasas del 12 %/15 % es **Illustrative audit sensitivity**, no un nuevo precio objetivo.
- Si P0>0: `Not ready`, decisión de cartera bloqueada. Un P0 cerrado requiere sustitución explícita de fuente y código más un test nuevo, no cambio de etiqueta.
- Adobe: comprobar M&A recurrente versus extraordinario, dilución, SBC, riesgo de IA y reconcilación trimestral/anual.
- Microsoft: CAPEX de nube/IA, infraestructura financiada en leasing, caja inicial real, sustitución de activos y riesgo de extrapolación.
- Visa/Mastercard: taxonomía de inversiones, incentivos comerciales, litigios, cuentas de liquidación y clases convertibles con misma fecha de referencia.
- Texas Instruments: CAPEX y utilización fab a través del ciclo, puentes CHIPS y GAAP, duración de incentivos y obligaciones de inversión.
- **Ámbito cerrado:** exactamente ADBE, MSFT, V, MA, TXN durante este mandato; no añadir emisores aunque el motor pueda ampliarse en el futuro.


## CIIP v2 — Puentes económicos prospectivos independientes (25-10-2026)
- Fuente de hechos económicos con fechas y partidas: `audits/economic_evidence_v2.json`.
- Motor separado y de solo lectura sobre las valoraciones existentes: `scripts/ciip_economic_bridge_v2.py`.
- Pruebas de conciliación, scope y bloqueo: `scripts/test_ciip_economic_bridge_v2.py`.
- Salidas de la ejecución semanal SEC: `audits/economic_bridge_latest.json` y `audits/ECONOMIC_BRIDGE_REPORT.md`. Una salida no generada o prueba fallida impide declarar resultado validado.
- La revisión v2 NO cambia las 15 hipótesis DCF anteriores ni los denominadores; deja audit trail del valor de base legado. Nunca transformar cambios en contingencias de inversión en un cambio silencioso de la valoración.
- Corregir en MA el FCF comparable FY2025 para incluir tanto `PP&E 489m` como `software capitalizado 726m`; `CFO 17648m - 489m - 726m = 16433m`. Mantener FCFE prospectivo base 16000m hasta elaboración de proyecciones.
- En MSFT el flujo inicial 51481m cuadra con FY2026 CFO-CAPEX-SBC-principal de arrendamientos; pagos futuros nominales de arrendamientos (incluyendo interés) no son deuda corriente y la nueva ROU no es salida de caja contemporánea. No restar doble interés ni ROU.
- En V conciliar incentivos contables y pagos, así como cuentas de settlement, litigios y escrow por ejercicios homogéneos. No deducir cambios incluidos en CFO por segunda vez.
- En ADBE separar Semrush cerrada, Topaz condicional y reserva anual M&A hipotética. Revisar el código DCF: restar una reserva una sola vez del efectivo inicial y después crecer el neto equivale a una reserva que crece con el negocio, no a una reserva plana anual. Documentar la política antes de activar cualquier DCF revisado.
- En TXN FCF GAAP LTM 7318m, subvención directa CHIPS en inversión 1104m y crédito fiscal dentro CFO 469m son tres conceptos diferentes; la reserva de ciclo 1818m no es CAPEX de mantenimiento probado. EV aproximado Silicon Labs y facility comprometida no equivalen a cash check o a deuda dispuesta.
- Los datos históricos conciliados cierran incidencias de procedencia y aritmética; la aprobación económica prospectiva requiere unidades de negocio, crecimiento, ciclos de CAPEX, litigios, financiación y eventos posteriores sustentados por notas.
- Política de resultado: nunca emitir `READY` ni una decisión de cartera hasta completar estos puentes, revisar nuevas presentaciones y reconciliar capital diluido actual.


## CIIP v3 — Descubrimiento sin lista fija (26-10-2026)
**El universo operativo NO son las cinco compañías de calibración ni los ~30 tickers originales.** El universo potencial se obtiene del fichero SEC company_tickers_exchange.json y se rastrea por lotes según presupuesto de consultas. La lista estática original funciona solo como cohort de regresión y cobertura permanente.

- `scripts/discover_opportunities.py prepare --limit 24` consulta universo SEC, descarta duplicados por CIK, fondos evidentes y SPAC por nombre, prioriza menciones históricas 13F del `data.json` y rota por el resto del catálogo; deja `discovery/queue.json`.
- `scripts/update_fundamentals.py` incorpora automáticamente a las candidatas de la cola a su descarga SEC e introduce sectorización SIC provisional.
- Tras validación histórica, `scripts/discover_opportunities.py rank` publica `discovery/radar.json` con estados RESEARCH_PRIORITY, WATCHLIST, SPECIALIST_REVIEW, INSUFFICIENT_DATA, y persiste cursor/fechas en `discovery/state.json`; las fallidas no se marcan como exitosas.
- El workflow SEC se ejecuta de lunes a viernes (cron UTC 07:45; GitHub Actions puede retrasar ejecuciones). La app muestra la cola en `discovery/index.html`, enlazada desde el panel principal.
- 13F almacenadas son instantáneas históricas, no novedades. Ampliación necesaria: ingestión 13F SEC trimestral con resolución de CUSIP↔emisor y pesos ajustados; nunca usar antigüedad como nueva entrada.
- **Separar los niveles:** (A) generación y priorización automática de ideas, (B) modelo sectorial retrospectivo + evidencia, (C) valoración individual proyectada y verificada. Un 0–100 del cribado NO es margen de seguridad ni valor intrínseco. Ninguna idea genera orden automática.
- SIC es clasificación aproximada y puede ser incompatible con el negocio mixto; jamás aprobar modelo simplemente por SIC. Emisores 20-F, ADR, IFRS, bancos, aseguradoras, REIT, SPAC, multiclase y negocios híbridos requieren conectores y valoraciones sectoriales específicas. SEC companyfacts US-GAAP no implica cobertura real de cualquier mercado global.
- Lista de cinco expedientes `audits/per_share_inputs.json` y `scripts/audit_ciip_models.py` permanece como REGRESIÓN de investigación profunda; ya no es el ámbito del descubrimiento.
- Cada alerta automatizada debe conservar fecha, fuente primaria, explicación de la oportunidad, factores de riesgo, calidad del dato y limitación de precio, en especial dividendos/corporate actions y dilución.
