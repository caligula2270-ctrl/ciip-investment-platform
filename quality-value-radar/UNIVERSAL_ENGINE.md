# Quality & Value Radar — motor universal (v1)

## Qué significa «universal»
El universo **no está limitado a 45 tickers ni a seis modelos**: se pueden registrar nuevas acciones cotizadas que el proveedor de datos bursátiles reconozca (p. ej. `MSFT`, `SAP.DE`, `SAN.MC`, `7203.T`, `V`, `MA`).

La investigación **no garantiza una valoración fundamental** para todos los países: una acción puede quedar sólo con un precio real fechado, a la espera de normalización contable oficial. Nunca se inventa un balance o unas acciones diluidas para poder presentar un valor.

## Cómo se incorpora cualquier ticker

### Desde la propia web
Abrir `https://caligula2270-ctrl.github.io/ciip-investment-platform/quality-value-radar/` → «Radar de oportunidades» → «Analizador universal de empresas». Escribir el ticker bursátil exacto → pulsar «Registrar empresa en GitHub» → cumplimentar y **enviar** el formulario de GitHub. Requiere una cuenta de GitHub para enviar solicitudes al repositorio. Los datos quedan publicados después de finalizar GitHub Actions.

### Desde GitHub Actions
Acciones → `QVR Universal - altas y actualizacion` → «Run workflow» → introducir en la casilla opcional `ticker` el símbolo. Si se deja vacío, recalcula los registrados. El repositorio debe permitir al solicitante ejecutar Actions.

### Actualizaciones
El workflow `.github/workflows/qvr-universal.yml` realiza una actualización de los tickers registrados **de lunes a viernes a las 07:40 UTC**. Los resultados quedan en `data/universal_results.json`; el registro en `data/universal_registry.json`. GitHub Pages se publica al incorporarse los cambios. Ningún proceso exige modificar manualmente el código al incorporar un ticker compatible.

## Modelo económico automático según fuentes
1. **Global**: consulta Yahoo Finance Chart: nombre, tipo de instrumento, divisa, bolsa, fecha y cierre. No garantiza disponibilidad, continuidad ni uso comercial licenciado.
2. **SEC US-GAAP**: cuando la empresa está en el índice SEC y cuenta con 10-K comparables, analiza ingresos, CFO, inversiones en propiedad/equipo, SBC y acciones diluidas. Calcula el margen de flujo del propietario por año y tres escenarios históricos por acción (múltiplos terminales hipotéticos), marcados como `indicative_research_only`. Todas las cifras están referenciadas a SEC companyfacts por CIK.
3. **Bancos/aseguradoras/REIT**: nunca aplicar el CFO−CAPEX general. Muestran `sector_requires_other_model` si se identifica su SIC financiero. Requieren método basado en capital, ROE, reservas, rentas, etc.
4. **Otras empresas internacionales**: `quote_only` hasta disponer de fuente oficial IFRS/regulador, divisa, acciones diluidas y cash flows comparables; no hay traducción arbitraria SEC/IFRS.
5. **Incertidumbre**: cada registro informa motivo preciso de no valoración, fuente, fecha y si el historial es suficiente. Ningún valor tiene compra aprobada.

**No confundir** «escenario de flujo económico preliminar» con «valor intrínseco probado» o «precio objetivo». El DCF genérico estadounidense aún no verifica crecimiento orgánico, capital circulante, rentabilidad de adquisiciones, CAPEX de mantenimiento, caja no operativa y acciones plenamente diluidas posteventos.

## Piloto integrado
`MSFT`, `GOOGL`, `V`, `MA`, `SAP.DE`, `SAN.MC`, `7203.T`. Los tickers adicionales no sustituyen las 45 cotizaciones iniciales ni los seis expedientes de investigación profunda.

## Limitaciones para el siguiente salto
Para disponer de valoración **automática y comparable en cualquier jurisdicción** hace falta integrar al menos un proveedor normalizado de cuentas IFRS locales y sus condiciones de licencia, taxonomías sectoriales, series históricas, identificación global de emisores, divisas y ajustes de split, además de pruebas temporales de estados y conciliación EV/accionista. Sin esas fuentes sería engañoso calificar de universal la profundidad de las valoraciones.

## Seguridad y privacidad
El sitio es público. **No introduzcas información confidencial** en un issue público. GitHub Issues puede ser visible para todos. No hay órdenes de compra, recomendaciones automáticas, notificaciones externas ni claves en el navegador.
