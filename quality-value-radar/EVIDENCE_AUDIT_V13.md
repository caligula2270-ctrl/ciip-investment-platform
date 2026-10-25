# Fase 13: cierre disciplinado de evidencias financieras

Ejecución técnica validada en la tarea semanal de GitHub Actions. `data/evidence_audit_v13.json` conserva por emisor la fuente y el motivo concreto que impide aprobar una valoración. `scripts/evidence_audit_v13.py` lo verifica en cada ejecución.

## Corrección financiera cuantificable
Dino Polska: el modelo de FCFF había omitido reincorporar depreciación y amortización al partir de EBIT después de impuestos. Con cifras declaradas 2025 EBITDA 2.546,3 MPLN y EBIT 2.041,3 MPLN, aproximación D&A=505 MPLN. FCF operativo modelado = NOPAT + D&A − CAPEX de mantenimiento supuesto − CAPEX de aperturas supuesto − logística supuesta − aumento de capital circulante. El modelo estima D&A futuro proporcional a ingresos; **esto es hipótesis**, no predicción publicada. El valor central ilustrativo cambia de 8,82 PLN a 22,15 PLN por acción. Escenario prudente 4,35 y optimista 48,81 PLN. No debe aprobarse hasta separar amortización IFRS 16 de derechos de uso y revisar obligaciones de arrendamiento y lease cash.

## Estado documental
- Copart/ACV: 8-K de cierre, pero no balance completo del grupo postadquisición ni ROIC por la unidad adquirida. No inventar saldos proforma.
- ASML: 6-K Q3 2026 proporciona caja, inversiones y cierta deuda, pero sin conciliación vigente de deuda corriente, arrendamientos y otros derechos. No inferir ausencia a partir de campo no divulgado.
- Constellation: adquisiciones comunicadas no prueban retornos incrementales por cohorte.
- Adobe/Intuit: reconstrucción anual de flujo normalizado corregida desde v11, pero financiación de recompra, SBC y ROIC de adquisiciones todavía requieren conciliación.

## Estructura
- Fuente `data/source_evidence_v12.json` (cada afirmación con origen identificado; no constituye prueba universal de cada cifra).
- Motor `scripts/economic_v9.py` corregido para amortización y marcado como no apto para compra.
- Auditoría `scripts/evidence_audit_v13.py` y resultado `data/evidence_audit_v13.json`.
- Workflow `.github/workflows/qvr-intrinsic.yml` cron miércoles; pruebas y rechazo de valores definitivos sin datos.
- UI `app.js` sección 'Auditoría de evidencia v13'.

La publicación verde verifica computación y actualización de datos, no la veracidad contable de cada campo. Ningún precio nuevo se ha aprobado para operar.
