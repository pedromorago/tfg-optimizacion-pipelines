"""
Construcción de la frontera de Pareto coste--tiempo mediante CBC.

Este script resuelve una familia de instancias del modelo MILP con número fijo
de contenedores N (Sección 3.5). Para cada valor de N se minimiza el tiempo de
validación de la pipeline

Cota inferior y calidad de la solución
--------------------------------------
Para cada N se reporta el intervalo [cota inferior, T_val], donde T_val es el
tiempo de validación de la mejor solución factible obtenida por el solver. La
cota inferior es la deducida en la Sección 3.5.1:

    T_val >= S + max{ max_j p_j , (sum_j p_j) / N },

Al tratarse de una cota inferior válida del óptimo entero, este queda
necesariamente contenido en el intervalo, y su amplitud

    gap = T_val - cota inferior

acota superiormente la distancia entre la solución obtenida y el óptimo. Si el
solver demuestra la optimalidad dentro del tiempo disponible (estado OPTIMAL),
T_val es el óptimo exacto y el gap reportado recoge únicamente la holgura de la
cota respecto a ese óptimo, no una suboptimalidad de la solución.

Como desigualdad redundante se añade T_val >= cota_discretizada, siendo
cota_discretizada la cota inferior redondeada hacia arriba a la precisión de los
datos (0,001). Es una desigualdad válida: tanto S como los tiempos p_j
son múltiplos de dicha precisión, por lo que el tiempo de validación óptimo
también lo es y no puede quedar por debajo de la cota redondeada. No elimina, por
tanto, ninguna solución óptima, y permite al solver detenerse de inmediato
cuando ese valor es alcanzable.

Los parámetros del solver y el criterio de parada siguen la Sección 5.2.4. El
estado de terminación se lee del registro (log) de CBC, ya que PuLP puede
informar 'Optimal' aun cuando el solver se haya detenido por límite de tiempo.
"""

import os
import math

import pulp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ============================================================
# PARÁMETROS DEL MODELO
# ============================================================

SETUP = 16.33            # tiempo de setup por contenedor (min), Sección 4.2.2
COSTE_UNITARIO = 0.04    # coste unitario de build (USD/min), Sección 4.3

# Barrido de la frontera: N de 3 a 14 contenedores (Sección 6.2).
MIN_CONTENEDORES = 3
MAX_CONTENEDORES = 14

TMAX = 60.0              # límite temporal por contenedor (min), Sección 4.3

# Parámetros del solver CBC (Sección 5.2.4). El límite de tiempo es un tope
# pragmático por instancia; la validez del resultado no descansa en él, sino en el
# intervalo [cota, T_val] (véase el encabezado del módulo), cuya amplitud acota la
# suboptimalidad de la solución que CBC devuelva en el momento de detenerse.
TIME_LIMIT = 120          # límite usado para generar los resultados de referencia (s)
GAP_REL = 0.0            # tolerancia de gap relativa (0: no se usa como parada)
GAP_ABS = 0.00095        # tolerancia de gap absoluta (min), por debajo de la precisión de los datos

# Precisión de los tiempos de entrada (tres decimales, registros de CI).
PRECISION_DATOS = 0.001

# Precisión a la que se redondean cota y tiempo de validación en el reporte.
NUM_DECIMALES_REPORTE = 2

ARCHIVO_TEXTO = "../Resultados/Frontera_Pareto_CBC.txt"
ARCHIVO_GRAFICA = "../Resultados/Frontera_Pareto_CBC.png"
CARPETA_LOGS = "../Resultados/logs_cbc"


# ============================================================
# DATOS DE ENTRADA
# ============================================================
# Tiempos medios observados por archivo spec en el Escenario Real (en minutos).

DATOS_PIPELINE_REAL = {
    'rules/rules.spec.ts': 9.600,
    'reporting/reports-generation.spec.ts': 8.197,
    'admin/custom-fields-managements.spec.ts': 7.127,
    'admin/user.spec.ts': 6.852,
    'admin/project-ownership.spec.ts': 5.645,
    'projects-1/automations.spec.ts': 5.166,
    'editor/zone-block.spec.ts': 4.558,
    'admin/business-unit-permissions-bulk.spec.ts': 4.348,
    'catalog/score-calculations.spec.ts': 3.704,
    'admin/business-unit.spec.ts': 3.346,
    'catalog/component.spec.ts': 3.150,
    'admin/custom-fields.spec.ts': 3.008,
    'admin/issue-trackers-profiles.spec.ts': 2.915,
    'catalog/finding.spec.ts': 2.711,
    'catalog/tag-patterns.spec.ts': 2.683,
    'catalog/scenario.spec.ts': 2.659,
    'projects-2/projects.spec.ts': 2.643,
    'catalog/library.spec.ts': 2.599,
    'admin/workflow-state.spec.ts': 2.579,
    'catalog/zone.spec.ts': 2.511,
    'projects-1/floating-modals.spec.ts': 2.468,
    'admin/user-profile.spec.ts': 2.444,
    'reporting/dashboard.spec.ts': 2.359,
    'editor/block-inspector.spec.ts': 2.251,
    'projects-2/templates.spec.ts': 1.931,
    'projects-2/versions.spec.ts': 1.913,
    'admin/login.spec.ts': 1.875,
    'projects-1/findings.spec.ts': 1.770,
    'catalog/record-classification.spec.ts': 1.757,
    'catalog/asset.spec.ts': 1.696,
    'catalog/standard.spec.ts': 1.689,
    'catalog/category.spec.ts': 1.532,
    'projects-1/issue-tracker-profiles.spec.ts': 1.431,
    'editor/project-import.spec.ts': 1.376,
    'catalog/record.spec.ts': 1.315,
    'reporting/reports-workflows.spec.ts': 1.255,
    'catalog/automations.spec.ts': 1.226,
    'projects-2/records.spec.ts': 1.213,
    'admin/redirection.spec.ts': 1.141,
    'catalog/content-hub.spec.ts': 0.759,
    'projects-1/custom-views.spec.ts': 0.725,
    'reporting/templates-dashboard.spec.ts': 0.681,
    'editor/questionnaire.spec.ts': 0.578,
    'reporting/dashboard-empty.spec.ts': 0.513,
    'reporting/project-list.spec.ts': 0.496,
    'editor/block-with-user.spec.ts': 0.493,
    'admin/audit-log.spec.ts': 0.472,
    'reporting/dashboard-cross-domain.spec.ts': 0.470,
    'admin/role.spec.ts': 0.412,
    'reporting/project-dashboard.spec.ts': 0.356,
    'editor/restore-previous-board.spec.ts': 0.348,
    'admin/workflow-state-change.spec.ts': 0.340,
    'editor/artifact.spec.ts': 0.313,
    'reporting/navigation.spec.ts': 0.165,
    'rules/workflow-rule.spec.ts': 0.146,
    'admin/features.spec.ts': 0.067,
    'admin/analytics-settings.spec.ts': 0.067,
    'admin/api.spec.ts': 0.067,
    'admin/license.spec.ts': 0.065,
    'admin/support.spec.ts': 0.065,
    'admin/user-interface.spec.ts': 0.065,
    'admin/email.spec.ts': 0.064,
    'admin/header.spec.ts': 0.050,
    'projects-1/configuration.spec.ts': 0.010,
    'admin/issue-trackers-profiles-empty.spec.ts': 0.010,
    'rules/questionnaire.spec.ts': 0.010,
    'catalog/form-template.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-with-archived-license.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-without-archived-license.spec.ts': 0.010,
    'editor/data-import.spec.ts': 0.010,
    'editor/unassigned-block.spec.ts': 0.010,
    'editor/restore-default-zone.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-restore-and-delete.spec.ts': 0.010,
    'reporting/version-dashboard.spec.ts': 0.010,
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def redondear_hacia_arriba(valor: float, precision: float) -> float:
    """
    Redondea un valor hacia arriba a la malla definida por `precision`.

    Ejemplo: redondear_hacia_arriba(30.3889, 0.001) -> 30.3890.

    El término -1e-12 evita que un valor que ya está sobre la malla, pero que se
    representa por defecto en coma flotante, se redondee a la celda superior.
    """
    return math.ceil((valor - 1e-12) / precision) * precision


def calcular_cota_teorica(
    datos_pipeline: dict,
    setup: float,
    num_contenedores: int,
) -> float:
    """
    Cota inferior teórica del tiempo de validación para N contenedores
    (Sección 3.5.1):

        T_val >= S + max{ max_j p_j , (sum_j p_j) / N }.

    Combina la cota por la tarea más larga (alguna spec se asigna íntegramente a
    un contenedor) y la cota por carga media (algún contenedor soporta una carga
    no inferior a la media). Es una cota inferior válida del óptimo entero; no
    siempre es alcanzable, por la indivisibilidad de los archivos spec.
    """
    suma_tiempos = sum(datos_pipeline.values())
    spec_mas_larga = max(datos_pipeline.values())

    return setup + max(spec_mas_larga, suma_tiempos / num_contenedores)


def calcular_cota_discretizada(
    datos_pipeline: dict,
    setup: float,
    num_contenedores: int,
) -> float:
    """
    Cota inferior discretizada: la cota teórica redondeada hacia arriba a la
    precisión de los datos (PRECISION_DATOS).

    Se utiliza como desigualdad redundante válida: el tiempo de validación óptimo
    es múltiplo de esa precisión (S y los p_j lo son), por lo que no puede quedar
    por debajo de la cota redondeada.
    """
    cota = calcular_cota_teorica(
        datos_pipeline=datos_pipeline,
        setup=setup,
        num_contenedores=num_contenedores,
    )

    return redondear_hacia_arriba(cota, PRECISION_DATOS)


def calcular_coste(
    datos_pipeline: dict,
    setup: float,
    coste_unitario: float,
    num_contenedores: int,
) -> float:
    """
    Coste total de una configuración con N contenedores fijos:

        C(N) = C_u * (S * N + sum_j p_j).

    Con N fijo, el coste no depende de la asignación concreta de specs, sino solo
    del número de contenedores activos.
    """
    suma_tiempos = sum(datos_pipeline.values())

    return coste_unitario * (setup * num_contenedores + suma_tiempos)


def leer_estado_log(log_path: str, estado_pulp: str) -> str:
    """
    Determina el motivo de terminación a partir del registro (log) de CBC.

    PuLP puede devolver 'Optimal' aunque el solver se haya detenido por límite de
    tiempo; por ello el estado se lee directamente del log. Si el log no está
    disponible o no contiene un patrón reconocido, se devuelve el estado de PuLP.
    """
    if not os.path.exists(log_path):
        return estado_pulp

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            log = f.read()

        if (
            "Stopped on time limit" in log
            or "Exiting on maximum time" in log
            or "Exiting on maximum seconds" in log
        ):
            return "TIME_LIMIT"

        if "Result - Optimal solution found" in log:
            return "OPTIMAL"

        if "Problem is infeasible" in log or "Infeasible" in log:
            return "INFEASIBLE"

    except OSError:
        pass

    return estado_pulp


# ============================================================
# CONSTRUCCIÓN DEL MODELO
# ============================================================

def construir_modelo(
    datos_pipeline: dict,
    setup: float,
    num_contenedores: int,
):
    """
    Construye el modelo MILP para un número fijo de contenedores (Sección 3.5).

    Variables:
      * x[i][j] en {0, 1}: vale 1 si la spec j se asigna al contenedor i.
      * t_val >= 0 (continua): tiempo de validación de la pipeline (makespan).

    Al estar fijado N, los contenedores están activos por construcción, por lo
    que no se introducen variables de activación z_i. Devuelve el problema y la
    variable t_val para poder recuperar su valor tras la resolución.
    """
    tareas = list(datos_pipeline.keys())
    contenedores = list(range(1, num_contenedores + 1))

    modelo = pulp.LpProblem(
        f"Pareto_{num_contenedores}_contenedores",
        pulp.LpMinimize,
    )

    x = pulp.LpVariable.dicts(
        "Asig",
        (contenedores, tareas),
        cat="Binary",
    )

    t_val = pulp.LpVariable(
        "T_val",
        lowBound=0,
        cat="Continuous",
    )

    # Función objetivo: minimizar el tiempo de validación.
    modelo += t_val

    # Cada spec se asigna exactamente a un contenedor.
    for tarea in tareas:
        modelo += pulp.lpSum(x[i][tarea] for i in contenedores) == 1

    # Restricciones por contenedor.
    for i in contenedores:
        carga_i = pulp.lpSum(
            datos_pipeline[tarea] * x[i][tarea]
            for tarea in tareas
        )

        # Cada contenedor recibe al menos una spec, de modo que los N
        # contenedores quedan efectivamente activos, en coherencia con el coste
        # C(N) calculado para N contenedores.
        modelo += pulp.lpSum(x[i][tarea] for tarea in tareas) >= 1

        # Definición del tiempo de validación: el tiempo total de cada contenedor
        # (setup más carga asignada) no puede superar t_val.
        modelo += setup + carga_i <= t_val

        # Límite temporal por contenedor (Sección 4.3).
        modelo += setup + carga_i <= TMAX

    # Desigualdad redundante: cota inferior discretizada. Es válida (el tiempo de
    # validación óptimo es múltiplo de la precisión de los datos y no puede quedar
    # por debajo de la cota redondeada), no elimina ninguna solución óptima y
    # permite al solver detenerse en cuanto alcanza ese valor.
    cota_disc = calcular_cota_discretizada(
        datos_pipeline=datos_pipeline,
        setup=setup,
        num_contenedores=num_contenedores,
    )
    modelo += t_val >= cota_disc

    return modelo, t_val


# ============================================================
# RESOLUCIÓN DE UNA INSTANCIA
# ============================================================

def resolver_instancia(
    datos_pipeline: dict,
    setup: float,
    coste_unitario: float,
    num_contenedores: int,
) -> dict:
    """
    Resuelve la instancia para un número fijo de contenedores y devuelve las
    magnitudes necesarias para construir la frontera coste--tiempo: el intervalo
    [cota inferior, T_val], su amplitud (el gap, en minutos y segundos), el coste
    total y el estado de terminación reportado por CBC.
    """
    modelo, var_t_val = construir_modelo(
        datos_pipeline=datos_pipeline,
        setup=setup,
        num_contenedores=num_contenedores,
    )

    os.makedirs(CARPETA_LOGS, exist_ok=True)
    log_path = os.path.join(CARPETA_LOGS, f"cbc_N_{num_contenedores}.log")

    solver = pulp.PULP_CBC_CMD(
        msg=False,
        timeLimit=TIME_LIMIT,
        gapRel=GAP_REL,
        gapAbs=GAP_ABS,
        logPath=log_path,
    )

    modelo.solve(solver)

    estado_pulp = pulp.LpStatus[modelo.status]
    estado_log = leer_estado_log(log_path, estado_pulp)

    t_val = var_t_val.varValue

    cota_teorica = calcular_cota_teorica(
        datos_pipeline=datos_pipeline,
        setup=setup,
        num_contenedores=num_contenedores,
    )
    coste_total = calcular_coste(
        datos_pipeline=datos_pipeline,
        setup=setup,
        coste_unitario=coste_unitario,
        num_contenedores=num_contenedores,
    )

    if t_val is None:
        return {
            "num_contenedores": num_contenedores,
            "estado_pulp": estado_pulp,
            "estado_log": estado_log,
            "t_val": None,
            "t_val_2dec": None,
            "cota_teorica": cota_teorica,
            "cota_teorica_2dec": round(cota_teorica, NUM_DECIMALES_REPORTE),
            "gap": None,
            "gap_segundos": None,
            "coste_total": coste_total,
        }

    # Amplitud del intervalo [cota inferior, T_val].
    gap = t_val - cota_teorica
    if abs(gap) < 1e-7:
        gap = 0.0

    return {
        "num_contenedores": num_contenedores,
        "estado_pulp": estado_pulp,
        "estado_log": estado_log,
        "t_val": t_val,
        "t_val_2dec": round(t_val, NUM_DECIMALES_REPORTE),
        "cota_teorica": cota_teorica,
        "cota_teorica_2dec": round(cota_teorica, NUM_DECIMALES_REPORTE),
        "gap": gap,
        "gap_segundos": gap * 60.0,
        "coste_total": coste_total,
    }


# ============================================================
# EXPORTACIÓN DEL REPORTE
# ============================================================

def exportar_reporte(resultados: list, archivo_texto: str) -> None:
    """
    Exporta a texto el resumen numérico de la frontera coste--tiempo: para cada
    nivel de paralelismo N, el intervalo [cota inferior, tiempo de validación],
    el gap, el estado de CBC y el coste total.
    """
    os.makedirs(os.path.dirname(archivo_texto), exist_ok=True)

    with open(archivo_texto, "w", encoding="utf-8") as f:
        f.write("=" * 104 + "\n")
        f.write("FRONTERA DE PARETO COSTE-TIEMPO\n")
        f.write("Intervalo [cota inferior, tiempo de validación] por nivel de paralelismo (N)\n")
        f.write("=" * 104 + "\n")
        f.write(
            f"Solver: CBC  |  timeLimit = {TIME_LIMIT} s  |  gapRel = {GAP_REL}  |  "
            f"gapAbs = {GAP_ABS:.5f} min  |  precisión de los datos = {PRECISION_DATOS:.3f} min\n"
        )
        f.write(
            "El tiempo de validación óptimo está contenido en [cota inferior, T_val]; "
            "el gap = T_val - cota\nacota superiormente su distancia al óptimo.\n"
        )
        f.write("-" * 104 + "\n")
        f.write(
            f"{'N':>3} | {'Estado CBC':>11} | {'Cota inf. (min)':>15} | "
            f"{'T_val (min)':>13} | {'Gap (min)':>9} | {'Gap (s)':>7} | {'Coste (USD)':>11}\n"
        )
        f.write("-" * 104 + "\n")

        for r in resultados:
            if r["t_val"] is None:
                f.write(
                    f"{r['num_contenedores']:>3} | {r['estado_log']:>11} | "
                    f"{r['cota_teorica']:>15.4f} | {'sin solución':>13} | "
                    f"{'-':>9} | {'-':>7} | {r['coste_total']:>11.2f}\n"
                )
            else:
                f.write(
                    f"{r['num_contenedores']:>3} | {r['estado_log']:>11} | "
                    f"{r['cota_teorica']:>15.4f} | {r['t_val']:>13.4f} | "
                    f"{r['gap']:>9.4f} | {r['gap_segundos']:>7.2f} | {r['coste_total']:>11.2f}\n"
                )

        f.write("=" * 104 + "\n")
        f.write(
            "Nota: con estado OPTIMAL, T_val es el óptimo demostrado; un gap no nulo es\n"
            "entonces la holgura de la cota teórica respecto al óptimo, no suboptimalidad.\n"
        )


# ============================================================
# GENERACIÓN DE LA GRÁFICA
# ============================================================

def generar_grafica(resultados: list, archivo_grafica: str) -> None:
    """
    Representa la frontera de Pareto coste--tiempo: tiempo de validación frente a
    coste total por ejecución, con cada punto etiquetado por su número de
    contenedores N.
    """
    resultados_validos = [r for r in resultados if r["t_val"] is not None]

    costes = [r["coste_total"] for r in resultados_validos]
    tiempos_validacion = [r["t_val"] for r in resultados_validos]
    contenedores = [r["num_contenedores"] for r in resultados_validos]

    plt.figure(figsize=(10, 6))
    plt.plot(
        costes,
        tiempos_validacion,
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=8,
        color="black",
    )

    for i, n in enumerate(contenedores):
        plt.annotate(
            f"{n}",
            (costes[i], tiempos_validacion[i]),
            textcoords="offset points",
            xytext=(8, 5),
            ha="left",
            fontsize=9,
        )

    plt.title("Frontera de Pareto coste-tiempo")
    plt.xlabel("Coste total por ejecución (USD)")
    plt.ylabel("Tiempo de validación (min)")
    plt.grid(True, linestyle="--", linewidth=0.8, alpha=0.6, color="0.6")
    plt.tight_layout()

    os.makedirs(os.path.dirname(archivo_grafica), exist_ok=True)
    plt.savefig(archivo_grafica, dpi=300)
    plt.close()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main() -> None:
    """
    Resuelve el barrido de configuraciones de paralelismo (N de MIN_CONTENEDORES
    a MAX_CONTENEDORES), exporta el reporte numérico y genera la gráfica de la
    frontera coste--tiempo.
    """
    print("Inicio del cálculo de la frontera de Pareto con CBC.")
    print(f"Límite de tiempo por instancia: {TIME_LIMIT} s.")
    print(f"gapRel = {GAP_REL} | gapAbs = {GAP_ABS} min (< precisión {PRECISION_DATOS} min).")
    print("Para cada N se reporta el intervalo [cota inferior, tiempo de validación] y su amplitud (el gap).")

    resultados = []

    for num_contenedores in range(MIN_CONTENEDORES, MAX_CONTENEDORES + 1):
        resultado = resolver_instancia(
            datos_pipeline=DATOS_PIPELINE_REAL,
            setup=SETUP,
            coste_unitario=COSTE_UNITARIO,
            num_contenedores=num_contenedores,
        )

        resultados.append(resultado)

        if resultado["t_val"] is None:
            print(
                f"N = {num_contenedores:2d} | {resultado['estado_log']:>11} | "
                f"sin solución registrada"
            )
        else:
            print(
                f"N = {num_contenedores:2d} | {resultado['estado_log']:>11} | "
                f"cota = {resultado['cota_teorica']:.4f} | "
                f"T_val = {resultado['t_val']:.4f} | "
                f"gap = {resultado['gap']:.4f} min ({resultado['gap_segundos']:.2f} s) | "
                f"coste = {resultado['coste_total']:.2f} USD"
            )

    exportar_reporte(resultados, ARCHIVO_TEXTO)
    generar_grafica(resultados, ARCHIVO_GRAFICA)

    print(f"Reporte generado: {ARCHIVO_TEXTO}")
    print(f"Gráfica generada: {ARCHIVO_GRAFICA}")


if __name__ == "__main__":
    main()
