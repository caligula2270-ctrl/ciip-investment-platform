# Quality & Value Radar — Protocolo operativo v6

Este proceso queda persistido en el repositorio y se reejecuta mediante `.github/workflows/qvr-intrinsic.yml`. No depende de recordar las decisiones del chat.

## 1. Priorización
Primera cobertura: Adobe, Intuit y Copart. Segundo bloque: Constellation Software, ASML y Dino Polska. Mantener las empresas no modeladas en backlog, sin falsa clasificación de barata/cara. La evidencia procede de los artefactos de las fases v4 y v5.

## 2. Valoración específica y escenarios
- Software (ADBE, INTU): flujo económico por acción después de SBC, crecimiento de ingresos oficial cuando sea comparable, múltiplo de salida limitado. Distorsión potencial por IA e intangibles.
- Copart: red de subastas y adquisiciones. La compra de ACV sin estados proforma impide elevar el modelo a recomendación aunque produzca una estimación.
- Constellation: FCFA2S anterior a adquisiciones, por tanto no equivale a caja disponible después de financiar nuevas adquisiciones. Solo escenario exploratorio.
- ASML: ciclos de semiconductores, anticipos de clientes, múltiplos normalizados, cambio EUR/USD.
- Dino: CAPEX de expansión de red frente a mantenimiento, moneda PLN y split de acciones. No inventar ROI por tienda.
- Mostrar valores descontados por acción, entradas como `mínimo(75 % DCF base, 90 % DCF prudente)`, IRR 5 y 10 años cuando existan cash flows por acción fiables, niveles de confianza (alta/estimada/insuficiente) y motivos de bloqueo.
- Cualquier IRR asume flujo distribuible anual, múltiplo terminal y número constante de acciones; no representa retorno prometido ni retorno total observado.
- Clasificación `watch_price_for_due_diligence` es invitación a investigar, **nunca recomendación ejecutable**.

## 3. Ranking
Priorizar calidad observable (cinco ejercicios FCF, ROIC ajustado, crecimiento de ingresos y balance), documentación y nivel de confianza. No mejorar puntaje por ausencia de datos. Separar empresas de gran calidad de las que están a precio de entrada.

## 4. Prueba retrospectiva
- Cortes históricos fechados, SEC forms **presentados antes del corte**; precios históricos comparables por split; prohibición de usar información futura para la señal.
- Indicar universo actual seleccionado retrospectivamente, sesgo de supervivencia y de selección; sin comisiones, fiscalidad y dividendos: el resultado no es una prueba de rentabilidad real.
- Si Yahoo u otra fuente no permite comprobar 2021, resultado = `insufficient_price_history`, no rellenar con precios inventados.
- El rendimiento anual de precio únicamente se calcula con datos verificables. Nunca llamar «backtest completo» a tres acciones escogidas hoy.

## 5. Alertas y controles
- Registrar alertas en `data/opportunity_alerts_v6.json`, actualizar después de cada valoración y mostrar las fechas de precios. No hay avisos por email/push todavía.
- Sólo investigación cuando una cotización verificablemente reciente sea inferior al umbral de entrada, con confianza suficiente. Sin compra automática.
- Artefactos: `data/opportunity_v6.json`, `data/backtest_v6.json`, `data/opportunity_alerts_v6.json`.
- Las reglas de control v5 siguen bloqueando falsos positivos. No atribuir consenso donde sólo exista guía de ingresos o hipótesis propias.

## 6. Siguiente auditoría
Conciliar las acciones corrientes con notas SEC, proforma ACV, mantenimiento/growth CAPEX y adquisiciones de CSU; contrastar precios de cierre por al menos 10 años y ajustar cálculo de acciones para cada split, incluyendo los anteriores a la fecha del backtest.
