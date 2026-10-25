# Quality & Value Radar — Manual operativo de producción

**Versión:** 2026-10-26. **Estado técnico:** operativo cuando `data/production_status.json` tenga `state: operational`; puede pasar automáticamente a `degraded` si fallan datos o las cotizaciones se vuelven antiguas. El estado **no** equivale a certificación de inversión.

## Abrir e instalar
Web: https://caligula2270-ctrl.github.io/ciip-investment-platform/quality-value-radar/
En iPhone: abrir en Safari fuera del visor de ChatGPT → Compartir → Añadir a pantalla de inicio. En ordenador: navegador habitual. La app es estática y guarda tus notas y cambios personales **en cada navegador**, no sincronizados entre dispositivos; exporta JSON si deseas traspasarlos.

## Procesos automatizados
1. Cotizaciones: `.github/workflows/update-quality-radar.yml`, producción `data/quotes.json`, datos fechados, 45 símbolos en la base actual.
2. Investigación económica: `.github/workflows/qvr-intrinsic.yml`, semanal los miércoles a las 09:15 UTC y ejecutable manualmente. Analiza fuentes SEC para hasta 16 valores estadounidenses, cálculos internacionales para 3 y seis modelos económicos de investigación.
3. En la tarea semanal, la última fase `scripts/build_production_snapshot.py` construye `data/production_status.json` con fuentes, coberturas, fechas de precio, bloqueos y escenarios. Un valor con datos faltantes no genera ninguna instrucción de compra.
4. Publicación de GitHub Pages: `.github/workflows/pages.yml` publica al cambiar `main` después de comprobar código. La tarea fundamental **ya no intenta publicar por su cuenta**, evitando ejecuciones simultáneas.
5. `sw.js`: documentos y JSON financieros con red prioritaria, archivos estáticos offline cuando ya están cacheados; jamás se debe considerar un precio de caché vigente sin fecha verificable.

## Significado de estados
- `operational`: conjunto completo de los feeds de investigación y cotizaciones con menos de siete días de antigüedad. Es un **estado de infraestructura**, NO calidad de valoración.
- `degraded`: cotizaciones incompletas, obsoletas o insuficientes.
- `conditional_research`: escenario de Adobe/Intuit utilizable únicamente como hipótesis, **no precio de compra defendible**.
- `incomplete_claims`: faltan deuda, caja, arrendamientos, estructura de capital o retornos por adquisiciones. Se oculta el umbral de compra hasta la reconciliación.
- `buyApproved: false`: invariable hasta completar auditoría de fuentes, acciones diluidas actuales, cash flows, escenarios y consenso independiente.
- `investmentGradeValue: null`: ningún precio certificado. No se fabrican partidas no publicadas.

## Definiciones y controles
- FCFE de software: mediana de CFO - CAPEX PPE - SBC sobre **ingresos del mismo ejercicio**; acciones y recompras requieren chequeo de posible doble cómputo.
- FCFF industrial: EBIT después de impuestos + depreciación/amortización - CAPEX - aumento de capital circulante; coherencia IFRS 16 obligatoria.
- No mezclar FCFE y FCFF, ni sumar caja a un flujo ya del accionista sin depurar activos no operativos y financiación.
- Copart / ACV: compra pagada una sola vez; saldo antes del cierre no equivale al balance pro forma posterior; flujo incrementado no probado.
- Constellation: FCFA2S antes de futuras compras debe financiar adquisiciones y descontar los flujos de caja de las cohortes; rentabilidades reales pendientes.
- ASML: último 6-K solo permite comprobar ciertos saldos, no el net cash sin deuda corriente y arrendamientos.
- Dino Polska: depreciación reincorporada al FCFF, pero puente lease-cash/debt todavía pendiente.

## Resolución de incidencias
- Acción verde pero cotizaciones antiguas: comprobar la fecha exacta de `data/quotes.json` y el resultado de `update-quality-radar.yml`, **no** borrar manualmente los avisos.
- Investigación fallida: revisar el paso que falla en `qvr-intrinsic.yml`. No sobrescribir valores anteriores sin distinguirlos por fecha.
- Web no refleja cambios: abrir Safari directamente, actualizar la página; el Service Worker está actualizado para usar red prioritaria.
- Publicación fallida: revisar `pages.yml`, en especial pruebas de JS/Python y permisos.
- Avisos: los umbrales de investigación se muestran en la interfaz. NO existe entrega por push, correo, Telegram, WhatsApp ni ejecución de operaciones.

## Criterio de cierre
La plataforma está **operativamente preparada** para consultar, investigar, seguir y comparar empresas y guardar escenarios. Las seis valoraciones finales **no están aprobadas** hasta existir evidencia suficiente de adquisición, deuda/arrendamientos, capital de mantenimiento y número actual de acciones totalmente diluidas. Una fuente oficial posterior debe contrastarse antes de retirar un bloqueo.
