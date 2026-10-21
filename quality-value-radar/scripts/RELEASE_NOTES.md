# Quality & Value Radar — actualización de precios

- Los precios provienen de fuentes públicas con **mejor esfuerzo**, sin garantía de continuidad o de retardo máximo.
- Cotizaciones son cierres diarios, con `date`, `currency`, `source`, `sourceUrl` y `kind` por símbolo. Un símbolo sin actualización conserva su última fecha.
- `data/quotes.json` solo debe considerarse actualizado para una empresa si su campo `date` corresponde a un día de negociación reciente.
- El flujo `Actualizar cotizaciones Quality & Value Radar` se ejecuta a las 06:20 UTC de lunes a viernes, admite ejecución manual y registra fallos del proveedor.
- Cambios locales de un dispositivo no se comparten automáticamente con otros dispositivos.
