# QVR v7 — Sensibilidades financieras, no señales de compra
Este procedimiento forma parte del workflow semanal `qvr-intrinsic.yml`. Código `scripts/sensitivity_v7.py` y resultados `data/sensitivity_v7.json`.

## 1. CAPEX
- Punto de partida: FCF del propietario por acción calculado desde SEC mediante CFO–CAPEX–SBC; último CAPEX anual normalizado por acción.
- Sensibilidades ceteris paribus de CAPEX total: −25%, 0%, +25%, +50%, manteniendo fijo crecimiento, tasa de descuento y múltiplo. No identifican mantenimiento ni crecimiento real.
- Contrafactual independiente: al diferir 30% o 60% del CAPEX, reducir simultáneamente crecimiento previsto (75% o 40% del crecimiento base). Estos coeficientes son **hipótesis** y pueden no reflejar una compañía concreta.
- No sumar automáticamente un ahorro de CAPEX a un DCF que ya presupone el crecimiento de inversiones financiadas por ese CAPEX. Los modelos internacionales aún carecen de desglose auditable: se muestran como insuficientes.

## 2. Dilución
- Cálculo neto de acciones diluidas por año: escenarios de reducción −1%, sin cambio, aumento +1%, +2,5% y +4% anual. Cada escenario vuelve a dividir el flujo económico agregado por las acciones esperadas.
- SBC se descuenta ya del CFO–CAPEX para aproximar coste económico. Un segundo descuento por emisión de acciones podría duplicar el efecto de SBC: las curvas son sensibilidades alternativas, no factores independientes acumulables sin conciliación de planes y recompras.
- Separar precio de recompras (consumo de caja de capital), emisión bruta por planes y evolución neta del número de acciones.
- Copart: registro S-8 de acciones de incentivos adquiridos no equivale a emisiones efectivas; no incorporarlas automáticamente como totalmente dilutivas.

## 3. Adquisiciones
- Copart / ACV: contrafactual de FCF adicional anual 0/100/150/228/300/400 MUSD; precio anunciado ~1.900 MUSD. Se calcula NPV por acción de flujos adicionales descontados menos desembolso de adquisición. Costes de integración, financiación, deuda asumida y sinergias **no reconciliados**. Por tanto este NPV **no se suma automáticamente al valor por acción**.
- El umbral de 228 MUSD (12% sobre 1.900 MUSD) es tasa mínima de caja hipotética, no retorno acreditado de la compra. Verificar la estructura de adquisición antes de cualquier opinión de inversión.
- Constellation: simulación independiente de cuánto cambia el efectivo repartible al dedicar una proporción de FCFA2S a adquisiciones. Mantener crecimiento constante mientras se reduce reinversión **no es un DCF coherente**; prueba de dependencia del modelo, no una valoración nueva.
- Para los demás emisores, no inventar retorno de cohortes no revelado.

## 4. Regla estricta
`automaticBuyDecisions=false` y `reliableBuyPrice=null` para las seis compañías mientras persistan ausencias documentales. Un cambio de flujo, CAPEX o dilución no constituye por sí mismo una oportunidad de inversión. Cada ejecución persiste el archivo, fecha, unidad, hipótesis y valor de referencia. Cualquier mejora posterior debe conservar pruebas de no doble cómputo y de cobertura.
