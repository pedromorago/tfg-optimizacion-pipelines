# Datos derivados
 
Conjunto de datos del estudio en forma de ficheros independientes:
tiempos agregados por archivo spec, en minutos. Cada fichero figura
también embebido como diccionario en los scripts que lo consumen.
 
- `datos_pipeline_real.txt`: tiempo total observado por spec, con los
  reintentos incluidos (Escenario Real). Alimenta los modelos de
  optimización; en forma de tabla, es el Anexo D de la memoria.
- `datos_pipeline_saneado.txt`: tiempo de las ejecuciones exitosas por
  spec, descartados los intentos fallidos (Escenario Saneado). Alimenta
  la comparación de escenarios; también en el Anexo D.
- `datos_pipeline_real_optimizado.txt`: tiempos por spec medidos en las
  ejecuciones de validación, tras desplegar la configuración optimizada.
  Alimenta la extracción empírica de la configuración optimizada, cuyos
  agregados recoge la Tabla 6.6 de la memoria.
Estos ficheros se generaron con los scripts de `codigo/` a partir de los
logs del pipeline, que se publican anonimizados en `logs_anonimizados/`
y `logs_anonimizados_optimizados/`. De esos logs se conservan el
estado y el tiempo de cada test (los nombres se han generalizado), así que
regenerarlos produce ficheros idénticos a los aquí incluidos. Al ejecutar los scripts
de preprocesado sobre los logs sintéticos de `ejemplo_logs/` se obtienen
ficheros con idéntico nombre y formato, pero con los datos del ejemplo.