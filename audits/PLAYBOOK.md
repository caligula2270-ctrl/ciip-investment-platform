# CIIP — Procedimiento persistente de auditoría fundamental v1.4

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
- No generar órdenes, recomendaciones categóricas ni precios por acción desde datos provisionales.

## Ejecución reproducible
1. scripts/update_fundamentals.py genera fundamentals-auto.json.
2. scripts/build_ciip_audits.py lee audits/evidence.json y fundamentals-auto.json; genera audits/latest.json.
3. GitHub Actions ejecuta tests y estas fases con cron y publicación conjunta.
4. App CIIP consulta fichero reciente sin caché y expone pendientes y fuentes.
5. Cada auditoría futura reutiliza ESTE procedimiento del repositorio; ChatGPT Memory sola no sustituye esta persistencia.
