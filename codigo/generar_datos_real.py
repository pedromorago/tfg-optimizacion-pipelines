import os
import re
from collections import defaultdict


# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_LOGS = "../logs_anonimizados/"
ARCHIVO_SALIDA = "../Resultados/datos_pipeline_real.txt"

# Expresiones regulares empleadas durante el preprocesado
PATRON_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
PATRON_TEST = re.compile(
    r'[✓✘\-]\s+\d+\s+\[.*?\]\s+›\s+(src/tests/([^/]+)/.*?\.spec\.ts)(.*)'
)
PATRON_TIEMPO = re.compile(r'\(([\d\.]+)\s*(ms|s|m)\)')
PATRON_RUN_ID = re.compile(r'-(\d+)\.log$')


def extraer_run_id(nombre_archivo: str) -> str:
    """
    Extrae el identificador del ciclo de ejecución (run_id) a partir del nombre
    del archivo log. Si no encuentra coincidencia, devuelve el propio nombre.
    """
    coincidencia = PATRON_RUN_ID.search(nombre_archivo)
    return coincidencia.group(1) if coincidencia else nombre_archivo


def convertir_a_segundos(valor: float, unidad: str) -> float:
    if unidad == "m":
        return valor * 60.0
    if unidad == "s":
        return valor
    if unidad == "ms":
        return valor / 1000.0

    raise ValueError(f"Unidad de tiempo no reconocida: {unidad}")


def procesar_logs(ruta_logs: str) -> tuple[dict, int]:
    """
    Recorre los archivos de log y construye una estructura de tiempos agregados
    por archivo spec y por ciclo de ejecución.

    Devuelve:
        - diccionario anidado de la forma:
          {ruta_spec: {run_id: tiempo_total_en_segundos}}
        - número total de archivos .log procesados
    """
    tiempos_spec_por_run = defaultdict(lambda: defaultdict(float))
    archivos_procesados = 0

    for raiz, _, archivos in os.walk(ruta_logs):
        for archivo in archivos:
            if not archivo.endswith(".log"):
                continue

            archivos_procesados += 1
            run_id = extraer_run_id(archivo)
            ruta_completa = os.path.join(raiz, archivo)

            try:
                with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as f:
                    for linea in f:
                        linea_limpia = PATRON_ANSI.sub("", linea)
                        coincidencia_test = PATRON_TEST.search(linea_limpia)

                        if not coincidencia_test:
                            continue

                        ruta_spec = coincidencia_test.group(1).strip()
                        resto_linea = coincidencia_test.group(3)

                        tiempo_segundos = 0.0
                        coincidencia_tiempo = PATRON_TIEMPO.search(resto_linea)

                        if coincidencia_tiempo:
                            valor = float(coincidencia_tiempo.group(1))
                            unidad = coincidencia_tiempo.group(2)
                            tiempo_segundos = convertir_a_segundos(valor, unidad)

                        # Si un mismo run_id aparece en logs de Sanity y Regression,
                        # ambos tiempos quedan agregados dentro del mismo ciclo.
                        tiempos_spec_por_run[ruta_spec][run_id] += tiempo_segundos

            except OSError as e:
                print(f"Aviso: no se pudo procesar el archivo '{ruta_completa}': {e}")

    return tiempos_spec_por_run, archivos_procesados


def calcular_tiempos_promedio(tiempos_spec_por_run: dict) -> dict:
    """
    Calcula el tiempo medio por archivo spec a partir de los tiempos agregados
    por ciclo de ejecución.

    El resultado se expresa en minutos y elimina el prefijo 'src/tests/' para
    obtener nombres más manejables en el modelo.
    """
    tiempos_promedio = {}

    for spec, runs in tiempos_spec_por_run.items():
        tiempos_totales_por_ciclo = list(runs.values())

        if not tiempos_totales_por_ciclo:
            continue

        promedio_segundos = sum(tiempos_totales_por_ciclo) / len(tiempos_totales_por_ciclo)
        promedio_minutos = promedio_segundos / 60.0

        nombre_corto = spec.replace("src/tests/", "")

        # Para evitar duraciones exactamente nulas en el modelo, se asigna
        # un valor mínimo positivo cuando no se ha registrado tiempo efectivo.
        if promedio_minutos == 0:
            promedio_minutos = 0.01

        tiempos_promedio[nombre_corto] = promedio_minutos

    return tiempos_promedio


def guardar_diccionario_salida(tiempos_promedio: dict, archivo_salida: str, archivos_procesados: int) -> None:
    """
    Guarda en disco el diccionario de tiempos medio del Escenario Real con
    formato Python, listo para ser utilizado como entrada del modelo MILP.
    """
    specs_ordenados = sorted(
        tiempos_promedio.items(),
        key=lambda x: (-round(x[1], 3), x[0]),  # tiempo (a la precision impresa) desc; a igualdad, nombre asc
    )

    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("# " + "=" * 70 + "\n")
        f.write("# DATOS DEL ESCENARIO REAL (SANITY + REGRESSION AGREGADOS)\n")
        f.write("# " + "=" * 70 + "\n")
        f.write(f"# Archivos log analizados: {archivos_procesados}\n")
        f.write(f"# Total de tareas indivisibles (specs): {len(specs_ordenados)}\n\n")

        f.write("datos_pipeline_real = {\n")
        for i, (spec, tiempo_min) in enumerate(specs_ordenados):
            coma = "," if i < len(specs_ordenados) - 1 else ""
            f.write(f"    '{spec}': {tiempo_min:.3f}{coma}\n")
        f.write("}\n")


def main() -> None:
    """
    Ejecuta el flujo completo de construcción del diccionario de tiempos del
    Escenario Real.
    """
    print("Inicio del preprocesado de logs para la construcción del Escenario Real.")

    tiempos_spec_por_run, archivos_procesados = procesar_logs(RUTA_LOGS)
    tiempos_promedio = calcular_tiempos_promedio(tiempos_spec_por_run)
    guardar_diccionario_salida(tiempos_promedio, ARCHIVO_SALIDA, archivos_procesados)

    print(f"Proceso completado correctamente. Archivo generado: {ARCHIVO_SALIDA}")
    print(f"Número total de specs incluidos: {len(tiempos_promedio)}")


if __name__ == "__main__":
    main()
