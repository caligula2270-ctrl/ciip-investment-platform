# Quality & Value Radar

Aplicación web en español, **estática** (sin instaladores ni cuentas), para estudiar compañías referenciadas por Galician Investor, Best Anchor Stocks, François Rochon, Nick Sleep, Rob Vinall y Cobas, y distinguir empresas de calidad de oportunidades razonablemente valoradas.

## Abrir

- **Rápido:** abre `index.html` en el navegador. Funciona también como archivo local usando la base de cotizaciones de referencia; no necesita servidor para filtrar, guardar fichas ni valorar.
- **Servidor local (recomendado):** desde esta carpeta, ejecuta `python -m http.server 8000` y abre http://localhost:8000/.
- **GitHub Pages:** copia todos los archivos a la **raíz** de un repositorio público. En GitHub, Settings → Pages → Build and deployment → Deploy from a branch → `main` → `/ (root)` → Save. La URL será `https://USUARIO.github.io/REPOSITORIO/`. No requiere npm ni compilación.
- En móvil, abre la URL por HTTPS y añade a la pantalla de inicio mediante el menú del navegador.

## Funciones

- Resumen y radar con coincidencias entre gestores.
- Directorio de más de 40 compañías, filtros, búsqueda, favoritos, fichas y notas personales.
- Indicador cualitativo de calidad, **subjetivo e inicial**, que no suplanta métricas auditadas.
- Valorador de escenarios mediante EPS normalizado, tasa de crecimiento, PER de salida, periodo y rentabilidad exigida; valor manual alternativo; tabla de sensibilidad.
- Etiquetas de descuento solo si existe valor calculado e información de cotización reciente (≤7 días).
- Introducción manual de precios y carga por lotes (ticker, precio y fecha), exportación CSV (Excel) y copia de seguridad JSON.
- Instalación como PWA estática con service worker que prioriza red para precios.
- Actualización opcional de cierres mediante GitHub Actions cada día laborable (endpoint público de Yahoo Finance; fallback Stooq para ciertos tickers USA). No precisa claves. Limitaciones de proveedor y de uso de datos pueden provocar fallos; en tal caso mantiene el precio anterior **con su fecha**, y el sistema lo identifica como antiguo.

## Verificación de titularidad de carteras

El **universo inicial proviene del prompt del usuario** y no supone certificación independiente de posiciones actuales. En particular:

- Copart figura expresamente en Galician Investor y Best Anchor Stocks según el material facilitado.
- Amazon figura en Best Anchor Stocks y **históricamente** en Nick Sleep; no debe presentarse como coincidencia entre dos carteras actuales.
- Constellation Software solo figura de forma identificable en Best Anchor Stocks dentro de los datos facilitados. La atribución a Giverny Capital requiere evidencia adicional.
- Para Cobas, Atalaya Mining aparece en dos fondos pero cuenta como **una** gestora.
- Las compañías de Best Anchor Stocks figuran en una lista de compañías mantenidas **o cubiertas**; el sistema las clasifica como cobertura, no propiedad actual comprobada.

## Metodología

Separa: (1) calidad del negocio y moat, (2) capacidad de reinvertir, (3) balance y FCF, (4) valoración y margen de seguridad, (5) verificación de cartera. Para valoraciones **reales** deberían recalcularse ROIC, EBITDA normalizado, flujo libre, deuda neta, variación del número de acciones y sensibilidad sectorial con informes oficiales. El resultado simplificado basado en múltiplos no es un DCF completo y carece de análisis del terminal y riesgo de dilución.

## Datos y privacidad

Los favoritos, precios introducidos, escenarios, empresas nuevas y notas quedan en el `localStorage` del dispositivo. No hay cuentas de usuario, base de datos compartida ni sincronización entre móviles. Un backup JSON permite trasladar la información. Los precios cargados de GitHub afectan a todos cuando la página se actualiza, pero la valoración y watchlist son privadas de cada dispositivo.

Para sincronizar **carteras, listas y notas entre usuarios** sería necesario un backend (por ejemplo Supabase) con autenticación y permisos; no está incluido. No hay recomendaciones automáticas de compra sin precio actualizado y valoración documentada.

## Referencias iniciales de cotización

- [Copart — StockAnalysis](https://stockanalysis.com/stocks/cprt/history/): cierre USD 27,83 de 20/10/2026.
- [Amazon — ChartExchange](https://chartexchange.com/symbol/nasdaq-amzn/historical/): cierre USD 262,36 de 21/10/2026.
- [Constellation — YCharts](https://ycharts.com/companies/CSU.TO/price): cierre CAD 3.240,00 de 20/10/2026.

El usuario puede reemplazar cualquier cotización por otra referencia de su elección.

## Publicación en el repositorio CIIP

La aplicación vive en la carpeta `quality-value-radar/` del repositorio `caligula2270-ctrl/ciip-investment-platform`. Su dirección de GitHub Pages será `https://caligula2270-ctrl.github.io/ciip-investment-platform/quality-value-radar/` si GitHub Pages está habilitado. La página CIIP original de la raíz permanece intacta.

La publicación está configurada en `.github/workflows/pages.yml` (despliegue) y `.github/workflows/update-quality-radar.yml` (actualización programada de precios).

El workflow de precios es de **mejor esfuerzo**: Yahoo puede bloquear solicitudes; Stooq sirve de respaldo para símbolos estadounidenses. No hay acuerdo de suministro de datos ni cotización real-time.
