import re
from collections import defaultdict
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

DIRECTORIO_DATOS = "../logs_anonimizados/"
ARCHIVO_SALIDA = "../Resultados/Reporte_Inestabilidad.txt"
NUM_CICLOS_REFERENCIA = 4

PATRON_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
PATRON_RUN_ID = re.compile(r'-(\d+)\.log$')

# Importante: ms antes que m
PATRON_TIEMPO = re.compile(r'\(([\d\.]+)(ms|s|m)\)')

# Captura:
# 1) estado: ✓ / ✘ / -
# 2) ruta spec completa
# 3) módulo extraído de la ruta
# 4) resto de línea
PATRON_TEST = re.compile(
    r'([✓✘\-])\s+\d+\s+\[.*?\]\s+›\s+(src/tests/([^/]+)/.*?\.spec\.ts)(.*)'
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def extraer_run_id(nombre_archivo: str):
    coincidencia = PATRON_RUN_ID.search(nombre_archivo)
    return int(coincidencia.group(1)) if coincidencia else None


def extraer_origen_log(nombre_archivo: str) -> str:
    """
    Elimina solo el sufijo '-<run_id>.log' para distinguir, dentro del mismo run,
    entre logs distintos (por ejemplo sanity y regression).
    """
    return re.sub(r'-(\d+)\.log$', '', nombre_archivo)


def extraer_modulo(nombre_archivo: str) -> str:
    """
    Obtiene el nombre del módulo a partir del nombre del log.
    """
    return nombre_archivo.split("-regression")[0].split("-sanity")[0]


def limpiar_nombre_test(resto_linea: str) -> str:
    """
    Normaliza el identificador del test eliminando:
    - referencias :linea:columna
    - tiempos
    - etiquetas @...
    - marcas de retry
    - espacios duplicados
    - variaciones simples de comillas
    """
    nombre_limpio = re.sub(r'^:\d+:\d+\s+›\s+', '', resto_linea)
    nombre_limpio = re.sub(r'\s*\([\d\.]+(?:ms|s|m)\)', '', nombre_limpio)
    nombre_limpio = re.sub(r'\s+@\w+', '', nombre_limpio)
    nombre_limpio = re.sub(r'\s+\(retry #\d+\)', '', nombre_limpio)

    nombre_limpio = (
        nombre_limpio
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio).strip()
    return nombre_limpio


def convertir_a_minutos(valor: float, unidad: str) -> float:
    if unidad == "m":
        return valor
    if unidad == "s":
        return valor / 60.0
    if unidad == "ms":
        return valor / 60000.0
    return valor


# ============================================================
# FASE 1: LECTURA Y EXTRACCIÓN
# ============================================================

def leer_intentos_desde_logs(directorio_datos: str):
    """
    Construye una estructura con los intentos observados para cada test.

    Estructura:
        intentos[(spec, test)][(run_id, origen_log)] = [
            {"status": "✘", "time": 0.52},
            {"status": "✓", "time": 0.18},
            ...
        ]

    También guarda un módulo representativo para cada (spec, test), solo con
    fines de reporte.
    """
    intentos = defaultdict(lambda: defaultdict(list))
    modulos_por_test = defaultdict(set)

    ruta_datos = Path(directorio_datos)

    for archivo in ruta_datos.glob("*.log"):
        run_id = extraer_run_id(archivo.name)
        if run_id is None:
            continue

        modulo = extraer_modulo(archivo.name)
        origen_log = extraer_origen_log(archivo.name)
        clave_ejecucion = (run_id, origen_log)

        try:
            with archivo.open("r", encoding="utf-8", errors="ignore") as f:
                for linea in f:
                    linea_limpia = PATRON_ANSI.sub("", linea)

                    if not any(m in linea_limpia for m in ["✓", "✘", "-"]):
                        continue

                    coincidencia_test = PATRON_TEST.search(linea_limpia)
                    if not coincidencia_test:
                        continue

                    estado = coincidencia_test.group(1)
                    spec = coincidencia_test.group(2).strip()
                    resto_linea = coincidencia_test.group(4)

                    coincidencia_tiempo = PATRON_TIEMPO.search(resto_linea)
                    if not coincidencia_tiempo:
                        continue

                    valor = float(coincidencia_tiempo.group(1))
                    unidad = coincidencia_tiempo.group(2)
                    tiempo_minutos = convertir_a_minutos(valor, unidad)

                    test_limpio = limpiar_nombre_test(resto_linea)

                    clave_test = (spec, test_limpio)

                    intentos[clave_test][clave_ejecucion].append(
                        {
                            "status": estado,
                            "time": tiempo_minutos,
                        }
                    )
                    modulos_por_test[clave_test].add(modulo)

        except Exception as e:
            print(f"Aviso: no se pudo procesar el archivo '{archivo.name}': {e}")

    return intentos, modulos_por_test


# ============================================================
# FASE 2: ANÁLISIS MATEMÁTICO
# ============================================================

def analizar_intentos(intentos, modulos_por_test):
    """
    Detecta el tiempo improductivo (deuda técnica) a nivel de test individual.

    Criterio:
    - Todo intento que termine en '✘' se contabiliza como tiempo improductivo,
      independientemente de si el test se reintenta después o no.
    - Los intentos exitosos ('✓') se utilizan para calcular el tiempo medio
      saneado del test cuando exista al menos una ejecución correcta.
    """
    filas_flakys = []
    tiempo_improductivo_global = 0.0

    for (spec, test), ejecuciones in intentos.items():
        tiene_fallos = False
        tiempo_improductivo_test = 0.0
        tiempos_exito = []

        for _, lista_eventos in ejecuciones.items():
            if not lista_eventos:
                continue

            for evento in lista_eventos:
                if evento["status"] == "✘":
                    tiene_fallos = True
                    tiempo_improductivo_test += evento["time"]
                    tiempo_improductivo_global += evento["time"]
                elif evento["status"] == "✓":
                    tiempos_exito.append(evento["time"])

        if tiene_fallos:
            media_exito = sum(tiempos_exito) / len(tiempos_exito) if tiempos_exito else None
            modulo = sorted(modulos_por_test[(spec, test)])[0] if modulos_por_test[(spec, test)] else "desconocido"

            filas_flakys.append(
                {
                    "Módulo": modulo,
                    "Spec": spec,
                    "Test": test,
                    "Tiempo_Saneado": media_exito,
                    "Tiempo_Improductivo": tiempo_improductivo_test,
                }
            )

    filas_flakys.sort(key=lambda x: (-x["Tiempo_Improductivo"], x["Spec"], x["Test"]))  # desempate determinista
    return filas_flakys, tiempo_improductivo_global


# ============================================================
# FASE 3: EXPORTACIÓN
# ============================================================

def exportar_reporte(
    filas_flakys,
    tiempo_improductivo_global: float,
    archivo_salida: str,
    num_ciclos_referencia: int = NUM_CICLOS_REFERENCIA,
) -> None:
    ruta_salida = Path(archivo_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with ruta_salida.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE DEUDA TÉCNICA OPERATIVA (FALLOS Y REINTENTOS)\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Tests con fallos detectados: {len(filas_flakys)}\n")
        f.write(f"Tiempo total improductivo (global): {tiempo_improductivo_global:.2f} minutos\n")
        f.write(
            "Media de tiempo improductivo por ciclo de CI/CD: "
            f"{tiempo_improductivo_global / num_ciclos_referencia:.2f} minutos\n\n"
        )

        f.write("-" * 80 + "\n")
        f.write("DETALLE DE TESTS CON DEUDA (ORDENADOS POR MAYOR IMPACTO)\n")
        f.write("-" * 80 + "\n\n")

        for fila in filas_flakys:
            t_saneado = fila['Tiempo_Saneado']
            str_saneado = f"{t_saneado:.4f} min" if t_saneado is not None else "N/A (Nunca finalizó con éxito)"

            f.write(f"Módulo: {fila['Módulo']}\n")
            f.write(f"Spec:   {fila['Spec']}\n")
            f.write(f"Test:   {fila['Test']}\n")
            f.write(f"        - Tiempo medio saneado (éxito):  {str_saneado}\n")
            f.write(f"        - Tiempo improductivo (total ✘): {fila['Tiempo_Improductivo']:.4f} min\n\n")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def analizar_flakys_txt(
    directorio_datos: str,
    archivo_salida: str,
    num_ciclos_referencia: int = NUM_CICLOS_REFERENCIA,
) -> None:
    print("Inicio del análisis de deuda técnica y tests inestables.")

    intentos, modulos_por_test = leer_intentos_desde_logs(directorio_datos)
    filas_flakys, tiempo_improductivo_global = analizar_intentos(intentos, modulos_por_test)

    exportar_reporte(
        filas_flakys=filas_flakys,
        tiempo_improductivo_global=tiempo_improductivo_global,
        archivo_salida=archivo_salida,
        num_ciclos_referencia=num_ciclos_referencia,
    )

    print(f"Proceso completado correctamente. Archivo generado: {Path(archivo_salida).resolve()}")
    print(f"Tests afectados detectados: {len(filas_flakys)}")
    print(f"Tiempo total improductivo: {tiempo_improductivo_global:.2f} minutos")
    print(
        "Media de tiempo improductivo por ejecución: "
        f"{tiempo_improductivo_global / num_ciclos_referencia:.2f} minutos"
    )


if __name__ == "__main__":
    analizar_flakys_txt(DIRECTORIO_DATOS, ARCHIVO_SALIDA)
