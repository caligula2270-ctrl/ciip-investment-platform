# Quality & Value Radar — cierre documental v12 (25 octubre 2026)

## Resultado y clasificación
Esta fase resuelve la presentación de datos observados de deuda, caja, restricciones y flujos, **no** sustituye los estados que una compañía aún no ha divulgado. Cualquier carencia material se conserva como bloqueo. El usuario debe diferenciar revisión documental de precio de inversión validado.

## Adobe
- Q3 2026 disponible. Revisión de efectivo, inversiones y deuda, pendiente integración de Semrush y financiación de recompras en un flujo de propietario totalmente normalizado.
- Ya corregidos tres márgenes fiscales emparejados en v11; el resultado económico continúa siendo un escenario.

## Intuit
- Excluidos de la caja corporativa los fondos de clientes.
- Diferenciadas compras PPE FY2026 por 175 MUSD y CAPEX gerencial amplio por 221 MUSD; la diferencia de 46 MUSD no debe imputarse sin identificar la partida.
- Las recompras y acciones pendientes requieren puente de capital.

## Copart / ACV
- Balance antes del cierre a julio de 2026, con efectivo restringido e inversiones a vencimiento: no tratarlos como caja libre.
- Contraprestación por adquisición del control ~1.801,02 MUSD documentada en 8-K.
- **No** se puede calcular un balance proforma real simplemente restando el pago a la caja histórica. Falta saldo postcierre, financiación, deuda asumida, circulante y retorno adquirido.

## Constellation
- FCFA2S ya incluye determinados intereses, arrendamientos y minoritarios. Diferenciar flujo antes de compras frente al destinado a nuevas adquisiciones.
- El pipeline de compras tras Q2 2026 comunicado no es un ROI por cohortes.

## ASML
- Q3 2026: caja 8.030,9 MEUR, inversiones cortas 4.704,2 MEUR; deuda larga 1.963 MEUR.
- Sin desglose homogéneo de deuda corriente, leases y claims no se puede publicar net cash ni equity bridge completo; el cálculo previo de FY2025 no es contemporáneo.
- R&D ya resta en EBIT; nunca duplicar.

## Dino
- Deuda neta de H1 2026 según divulgación pública secundaria de dirección: +81,1 MPLN incluyendo leases, frente a −199,4 MPLN en FY2025.
- Dos marcos alternativos: pre-leases FCFF / lease debt; o post-leases FCFE / excluir deuda lease. El modelo no selecciona un puente aprobado hasta conciliar pagos.
- CAPEX anunciado 2026 ~2.500 MPLN, incluyendo inversión separada en máquinas de devolución: la asignación a tiendas nuevas es una hipótesis, no desglose publicado.

## Persistencia y auditoría
- Datos: `data/source_evidence_v12.json`.
- Motor: `scripts/closeout_v12.py`.
- Evidencia generada: `data/closeout_v12.json`.
- Workflow: `.github/workflows/qvr-intrinsic.yml`.
- El control mantiene `signalsAllowed=false`; **seis empresas revisadas no implican seis precios defendibles**.
- Las cifras de origen deben refrescarse contra cuentas nuevas; los scripts actualmente recalculan consistencia y diagnostican lagunas, pero no extraen automáticamente todos los campos específicos de cada informe.
