import os
import re
from collections import defaultdict


# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_LOGS = "../logs_anonimizados/"
ARCHIVO_SALIDA = "../Resultados/datos_pipeline_saneado.txt"

# Expresiones regulares
PATRON_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
PATRON_TEST = re.compile(
    r'([✓✘\-])\s+\d+\s+\[.*?\]\s+›\s+(src/tests/([^/]+)/.*?\.spec\.ts)(.*)'
)
PATRON_TIEMPO = re.compile(r'\(([\d\.]+)\s*(ms|s|m)\)')
PATRON_RUN_ID = re.compile(r'-(\d+)\.log$')


def extraer_run_id(nombre_archivo: str) -> str:
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


def procesar_logs(ruta_logs: str):
    """
    Recorre los archivos log.
    Para evitar sobrescribir tests distintos que tengan el mismo nombre base,
    guardamos una LISTA de todos los intentos registrados para ese test.

    data[run_id][ruta_spec][test_id_limpio] = [t1, t2, t3...]
    """
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
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

                        # Solo nos interesan los tests que NO fallan (✓ o -)
                        # Si fallan (✘), ignoramos ese tiempo porque es deuda técnica.
                        estado = coincidencia_test.group(1)
                        if estado == '✘':
                            continue

                        ruta_spec = coincidencia_test.group(2).strip()
                        resto_linea = coincidencia_test.group(4)

                        tiempo_segundos = 0.0
                        coincidencia_tiempo = PATRON_TIEMPO.search(resto_linea)

                        if coincidencia_tiempo:
                            valor = float(coincidencia_tiempo.group(1))
                            unidad = coincidencia_tiempo.group(2)
                            tiempo_segundos = convertir_a_segundos(valor, unidad)

                        # Limpiamos el nombre para agrupar los reintentos
                        test_id = re.sub(r'^:\d+:\d+\s+›\s+', '', resto_linea)
                        test_id = re.sub(r'\s*\([\d\.]+\s*(?:ms|s|m)\)', '', test_id)
                        test_id = re.sub(r'\s+@\w+', '', test_id)
                        test_id = re.sub(r'\s+\(retry #\d+\)', '', test_id).strip()

                        # Almacenamos todos los tiempos exitosos para este test
                        data[run_id][ruta_spec][test_id].append(tiempo_segundos)

            except OSError as e:
                print(f"Aviso: no se pudo procesar el archivo '{ruta_completa}': {e}")

    return data, archivos_procesados


def calcular_tiempos_promedio(data: dict) -> dict:
    """
    Agrega los tiempos saneados (sin fallos) por archivo spec y calcula
    la media entre todos los ciclos de CI/CD.
    """
    spec_run_totals = defaultdict(lambda: defaultdict(float))

    for run_id, specs in data.items():
        for ruta_spec, tests in specs.items():
            tiempo_total_spec = 0.0
            for test_id, tiempos_exitosos in tests.items():
                # Si un test con el mismo nombre pasa varias veces (por ejemplo, tests parametrizados),
                # sumamos todos sus tiempos exitosos.
                tiempo_total_spec += sum(tiempos_exitosos)

            spec_run_totals[ruta_spec][run_id] = tiempo_total_spec

    resultados_finales = {}

    for ruta_spec, ciclos in spec_run_totals.items():
        if not ciclos:
            continue

        promedio_segundos = sum(ciclos.values()) / len(ciclos)
        promedio_minutos = promedio_segundos / 60.0

        if promedio_minutos == 0:
            promedio_minutos = 0.01

        nombre_limpio = ruta_spec.replace("src/tests/", "")
        resultados_finales[nombre_limpio] = promedio_minutos

    return resultados_finales


def guardar_diccionario_salida(resultados_finales: dict, archivo_salida: str, numero_ciclos: int) -> None:
    ordenado = sorted(resultados_finales.items(), key=lambda x: (-round(x[1], 3), x[0]))  # tiempo (a la precision impresa) desc; a igualdad, nombre asc

    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("# " + "=" * 75 + "\n")
        f.write("# DATOS DEL ESCENARIO SANEADO (SIN REINTENTOS, SANITY + REGRESSION AGREGADOS)\n")
        f.write("# " + "=" * 75 + "\n")
        f.write(f"# Ciclos de ejecución analizados: {numero_ciclos}\n")
        f.write(f"# Total de tareas indivisibles (specs): {len(ordenado)}\n\n")

        f.write("datos_pipeline_saneado = {\n")
        for i, (nombre, tiempo_min) in enumerate(ordenado):
            coma = "," if i < len(ordenado) - 1 else ""
            f.write(f"    '{nombre}': {tiempo_min:.3f}{coma}\n")
        f.write("}\n")


def main() -> None:
    print("Inicio del preprocesado de logs para la construcción del Escenario Saneado.")

    data, archivos_procesados = procesar_logs(RUTA_LOGS)
    resultados_finales = calcular_tiempos_promedio(data)
    guardar_diccionario_salida(resultados_finales, ARCHIVO_SALIDA, len(data))

    print(f"Proceso completado correctamente. Archivo generado: {ARCHIVO_SALIDA}")
    print(f"Número total de specs incluidos: {len(resultados_finales)}")


if __name__ == "__main__":
    main()
