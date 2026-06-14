# Resultados de referencia

Salidas de los scripts de optimización y de extracción empírica tal y como se obtuvieron para la memoria del trabajo, con Python 3.12, PuLP 3.3.2 y el solver CBC incluido en esa versión de PuLP. Sirven para consultar o comparar resultados sin necesidad de ejecutar nada.

Al reproducirlos, se espera que el coste y el tiempo de validación (*makespan*) coincidan con estos ficheros, salvo pequeñas diferencias de décimas de segundo acotadas por la cota inferior analítica utilizada en la memoria. La asignación concreta de specs a contenedores puede variar entre ejecuciones. Lo relevante para comparar una nueva ejecución con las salidas de referencia es revisar el coste, el tiempo de validación y la distancia respecto a la cota inferior. Las salidas de extracción empírica son deterministas y deben coincidir exactamente.

Esta carpeta contiene las salidas del estudio. Todas son regenerables desde el propio repositorio: los modelos y los scripts de extracción empírica llevan embebidos los datos que necesitan, y `Reporte_Inestabilidad.txt` es la salida directa de `analisis_flakys.py` sobre los logs anonimizados de `logs_anonimizados/`, sin ediciones manuales. Ejecutando ese script sobre los logs de `ejemplo_logs/` se obtiene un reporte con el mismo formato y datos de ejemplo. El conjunto de datos derivado de los logs está en `datos_derivados/`.

La carpeta `Resultados/` (ignorada por git) es el directorio de trabajo donde escriben los scripts al ejecutarse. Esta carpeta de referencia no se sobrescribe en ningún caso.
