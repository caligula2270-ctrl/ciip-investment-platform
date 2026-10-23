# Radar automático de infravaloración (v1)

## Qué hace

- **Precios:** flujo diario previo `update-quality-radar.yml`, último cierre fechado para 45 símbolos, sujeto a disponibilidad del proveedor.
- **Fundamentales:** `qvr-intrinsic.yml` se ejecuta los miércoles a las 09:15 UTC o manualmente. Necesita la variable de repositorio `SEC_USER_AGENT` con nombre identificable y correo válido para consultar SEC EDGAR.
- **Cobertura fase 1:** 16 compañías estadounidenses no aseguradoras con declaraciones 10-K bajo US GAAP. Para el resto, el sistema muestra **sin cobertura**, no inventa cifras ni inferencias.

## Modelo y decisiones de elegibilidad

1. SEC `companyfacts`: CFO (flujo operativo), CAPEX (salidas de inmovilizado), ingresos, EBIT, capital y acciones medias diluidas de ejercicios completos publicados mediante 10-K. FCF = CFO - CAPEX. Se usan datos de hasta seis ejercicios.
2. FCF normalizado por acción: mediana de los tres últimos ejercicios con FCF positivo. Quedan excluidos modelos con datos insuficientes o sin tres FCF positivos recientes.
3. Crecimiento base: CAGR histórico de ingresos con tope al 12% y suelo al 0%. Esto es una **hipótesis heurística**, no una previsión de consenso.
4. DCF proxy de 5 años: tasa requerida base 11,5%, crecimiento terminal 2,5%. Escenario prudente 13% de descuento; optimista 10,5%.
5. Valoración relativa: mediana de 3+ múltiplos P/FCF en fecha cercana al cierre de ejercicio, usando cotizaciones históricas ajustadas por splits y las acciones diluidas del ejercicio.
6. Precio objetivo indicativo mixto: 60% DCF + 40% valor derivado de la mediana P/FCF. Se calcula únicamente cuando están disponibles **ambos** métodos.
7. Una empresa se considera **posible descuento** solo si el precio tiene ≤7 días, margen >=25%, proxy ROIC mediano >=15%, FCF positivo en 4+ de los últimos 5 ejercicios y deuda neta/FCF <=4 si calculable.

## Limitaciones que importan

- **NO ES UN DCF COMPLETO:** el CFO-CAPEX no ajusta automáticamente intereses/deuda neta, capital circulante normalizado, gastos de opciones/SBC, cambios fiscales, leasing, adquisición de negocios o acciones convertibles. No comparar valores por acción con distintas divisas. No usar ratios de compañías financieras como si fueran manufactureras.
- El **ROIC mostrado es un proxy**, EBIT × (1 - tasa fiscal supuesta del 24%) / (patrimonio + deuda - caja), con valores alineados al cierre fiscal. No es ROIC económico auditado, ni está depurado de adquisiciones/intangibles.
- El P/FCF histórico se calcula con precio cercano al fin del año fiscal y FCF/acción anual de ese mismo ejercicio: es una **comparación retrospectiva** (no estimación forward disponible en esa fecha). La mediana no es valor razonable por sí sola.
- No se reestima la situación de cartera real de los inversores ni se deduce que un gestor siga invertido. La puntuación cualitativa del catálogo es editorial.
- Datos bloqueados o faltantes se señalan como "insuficientes", "desactualizados" o "sin cobertura". No hay precios inventados, ni señal de compra, ni transacciones.

## Verificación

- GitHub → Actions → **QVR Valoración Fundamental Semanal** → Run workflow en `main`. Mira el paso de validación y el artefacto de publicación.
- Inspecciona [data/intrinsic.json](./data/intrinsic.json): `status`, `classification`, `warnings`, `years`, `assumptions`, `sourceUrl`.
- Comprueba el panel "Radar de oportunidades" de [Quality & Value Radar](https://caligula2270-ctrl.github.io/ciip-investment-platform/quality-value-radar/).
- Si SEC responde con error, configura en el repo **Settings → Secrets and variables → Actions → Variables** `SEC_USER_AGENT` con texto como `QualityValueRadar (investor-contact@example.com)` usando **tu contacto real**, no el ejemplo.

**Una ejecución verde confirma que el proceso técnico terminó; no certifica la exactitud financiera, la calidad de la fuente secundaria ni la conveniencia de invertir.**
