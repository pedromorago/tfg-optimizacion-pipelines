# Logs de ejemplo sintéticos

Estos archivos `.log` son datos **sintéticos**, inventados para este repositorio.
No proceden de ninguna ejecución real ni contienen información de terceros.
Su único fin es permitir ejecutar y comprobar los scripts de extracción de datos
(`generar_datos_real.py`, `generar_datos_saneado.py`, `analisis_flakys.py`)
sin los logs originales de CI.

Reproducen el formato del reporter de lista de Playwright: una línea por intento de
test, con su estado (correcto, fallido u omitido), la ruta de la spec, la descripción
del caso y el tiempo entre paréntesis. El identificador de ciclo (run_id) se toma del
sufijo `-N.log` del nombre del fichero. Hay dos ciclos: `pipeline-regression-1.log` y
`pipeline-regression-2.log`.

Cubren a propósito los cuatro casos que manejan los scripts:

  1. Test que pasa siempre (login, perfil, listado, configuración/guarda).
     -> Aparece en ambos datasets (real y saneado); no sale en el reporte de deuda.

  2. Test flaky que falla y luego pasa en el reintento (exportación/exporta a CSV).
     -> En el reporte de deuda con tiempo saneado (el pase) y tiempo improductivo
        (el fallo). En el dataset real cuenta el fallo; en el saneado, no.

  3. Test que falla en todos los intentos, sin pasar nunca
     (configuración/sincroniza con servicio externo).
     -> En el reporte de deuda con tiempo saneado = N/A (nunca finalizó con éxito).
        Su tiempo cuenta como improductivo, y se descuenta de la carga saneada de su
        spec. El N/A es esto, NO un test omitido.

  4. Test omitido / skipped (configuración/exporta informe beta).
     -> No aparece en el reporte de deuda. No se confunde con el N/A del caso 3.

Para probarlos, sitúa estos ficheros en la ruta que lea cada script o ajusta temporalmente la constante de entrada correspondiente.

