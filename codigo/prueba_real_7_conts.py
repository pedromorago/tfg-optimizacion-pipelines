"""
Resolución del modelo P||Cmax para la configuración base de siete contenedores
del Escenario Real (Anexo B.1).

Reparte los 74 ficheros spec entre siete contenedores minimizando el tiempo de
validación (makespan) mediante un modelo MILP resuelto con CBC, y exporta la
asignación resultante en un formato directamente incorporable a la configuración
declarativa del sistema de integración continua.
"""

import os
import pulp


# ============================================================
# PARÁMETROS DEL MODELO
# ============================================================

SETUP = 16.33
NUM_CONTENEDORES = 7
ARCHIVO_SALIDA = "../Resultados/Asignacion_7_Contenedores.txt"


# ============================================================
# DATOS DE ENTRADA
# ============================================================
# Tiempos medios observados por archivo spec en el Escenario Real.
# Las claves se almacenan sin el prefijo "src/tests/" para facilitar
# la manipulación interna. Dicho prefijo se reincorpora en la fase
# de exportación para producir una salida utilizable en el sistema CI.

DATOS_PIPELINE_REAL = {
    'rules/rules.spec.ts': 9.6,
    'reporting/reports-generation.spec.ts': 8.197,
    'admin/custom-fields-managements.spec.ts': 7.127,
    'admin/user.spec.ts': 6.852,
    'admin/project-ownership.spec.ts': 5.645,
    'projects-1/automations.spec.ts': 5.166,
    'editor/zone-block.spec.ts': 4.558,
    'admin/business-unit-permissions-bulk.spec.ts': 4.348,
    'catalog/score-calculations.spec.ts': 3.704,
    'admin/business-unit.spec.ts': 3.346,
    'catalog/component.spec.ts': 3.15,
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
    'projects-1/findings.spec.ts': 1.77,
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
    'reporting/dashboard-cross-domain.spec.ts': 0.47,
    'admin/role.spec.ts': 0.412,
    'reporting/project-dashboard.spec.ts': 0.356,
    'editor/restore-previous-board.spec.ts': 0.348,
    'admin/workflow-state-change.spec.ts': 0.34,
    'editor/artifact.spec.ts': 0.313,
    'reporting/navigation.spec.ts': 0.165,
    'rules/workflow-rule.spec.ts': 0.146,
    'admin/analytics-settings.spec.ts': 0.067,
    'admin/api.spec.ts': 0.067,
    'admin/features.spec.ts': 0.067,
    'admin/license.spec.ts': 0.065,
    'admin/support.spec.ts': 0.065,
    'admin/user-interface.spec.ts': 0.065,
    'admin/email.spec.ts': 0.064,
    'admin/header.spec.ts': 0.05,
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
# CONSTRUCCIÓN DEL MODELO
# Caso particular con N fijo: no se modelan variables de activación z_i
# porque los siete contenedores están activos por construcción.
# ============================================================

def construir_modelo(datos_pipeline: dict, setup: float, num_contenedores: int):
    """
    Construye el modelo MILP para la asignación de tareas a un número fijo de
    contenedores, minimizando el tiempo de validación (makespan).

    Parámetros
    ----------
    datos_pipeline : dict
        Diccionario {spec: tiempo_en_minutos}.
    setup : float
        Tiempo fijo de inicialización por contenedor.
    num_contenedores : int
        Número exacto de contenedores considerados.

    Devuelve
    --------
    tuple
        Modelo PuLP, variables binarias de asignación, variable de tiempo de
        validación, lista de tareas y lista de contenedores.
    """
    tareas = list(datos_pipeline.keys())
    contenedores = list(range(1, num_contenedores + 1))

    modelo = pulp.LpProblem(f"Asignacion_{num_contenedores}_contenedores", pulp.LpMinimize)

    x = pulp.LpVariable.dicts("Asig", (contenedores, tareas), cat="Binary")
    t_val = pulp.LpVariable("T_val", lowBound=0, cat="Continuous")

    # Función objetivo: minimizar el tiempo de validación.
    modelo += t_val

    # Cada tarea se asigna exactamente a un único contenedor.
    for tarea in tareas:
        modelo += pulp.lpSum(x[i][tarea] for i in contenedores) == 1

    # El tiempo total de cada contenedor (setup + carga asignada)
    # no puede superar el tiempo de validación.
    for i in contenedores:
        carga_i = pulp.lpSum(datos_pipeline[tarea] * x[i][tarea] for tarea in tareas)
        modelo += setup + carga_i <= t_val

    # A diferencia de generar_pareto.py, aquí no se imponen t_i <= T_max ni la
    # activación de al menos una spec por contenedor: con N=7 fijo y un makespan
    # muy por debajo del límite de 60 min, ambas son no vinculantes y no alteran
    # el óptimo. Solo importan al barrer configuraciones con pocos contenedores
    # (N pequeño), como hace la frontera de Pareto.

    return modelo, x, t_val, tareas, contenedores


# ============================================================
# RESOLUCIÓN DEL MODELO
# ============================================================

def resolver_modelo(modelo) -> None:
    """
    Resuelve el modelo mediante CBC con límite temporal y gap relativo nulo.
    """
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=120, gapRel=0.0)
    modelo.solve(solver)


# ============================================================
# EXTRACCIÓN DE RESULTADOS
# ============================================================

def extraer_asignacion(x, tareas, contenedores, datos_pipeline: dict, setup: float) -> list[dict]:
    """
    Extrae la asignación de tareas por contenedor y calcula, para cada uno,
    la carga neta y el tiempo total incluyendo setup.

    Devuelve
    --------
    list[dict]
        Lista de diccionarios con la información de cada contenedor.
    """
    resultados = []

    for i in contenedores:
        tareas_asignadas = [tarea for tarea in tareas if x[i][tarea].varValue > 0.5]
        tiempo_neto = sum(datos_pipeline[tarea] for tarea in tareas_asignadas)
        tiempo_total = tiempo_neto + setup

        resultados.append(
            {
                "contenedor": i,
                "tareas_asignadas": tareas_asignadas,
                "tiempo_neto": tiempo_neto,
                "tiempo_total": tiempo_total,
            }
        )

    return resultados


# ============================================================
# EXPORTACIÓN DE RESULTADOS
# ============================================================

def exportar_asignacion(resultados: list[dict], archivo_salida: str, makespan: float, setup: float) -> None:
    """
    Exporta la asignación obtenida a un archivo de texto legible y utilizable
    para su posterior incorporación a la configuración declarativa del sistema CI.
    """
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("=" * 75 + "\n")
        f.write("ASIGNACIÓN PARA SIETE CONTENEDORES\n")
        f.write("=" * 75 + "\n")
        f.write(f"Makespan esperado: {makespan:.2f} minutos\n")
        f.write(f"Tiempo de setup por contenedor: {setup:.2f} minutos\n\n")

        for resultado in resultados:
            contenedor = resultado["contenedor"]
            tiempo_total = resultado["tiempo_total"]
            tiempo_neto = resultado["tiempo_neto"]
            tareas_asignadas = resultado["tareas_asignadas"]

            f.write(
                f"CONTENEDOR {contenedor} "
                f"(Tiempo total: {tiempo_total:.2f} min | "
                f"Carga neta: {tiempo_neto:.2f} min)\n"
            )
            f.write("-" * 75 + "\n")

            rutas_formateadas = " ".join(f"src/tests/{tarea}" for tarea in tareas_asignadas)
            f.write(f"{rutas_formateadas}\n\n")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main() -> None:
    """
    Ejecuta el flujo completo de resolución y exportación para el caso con
    siete contenedores.
    """
    print("Inicio de la resolución del modelo para siete contenedores.")

    modelo, x, t_val, tareas, contenedores = construir_modelo(
        datos_pipeline=DATOS_PIPELINE_REAL,
        setup=SETUP,
        num_contenedores=NUM_CONTENEDORES,
    )

    resolver_modelo(modelo)

    resultados = extraer_asignacion(
        x=x,
        tareas=tareas,
        contenedores=contenedores,
        datos_pipeline=DATOS_PIPELINE_REAL,
        setup=SETUP,
    )

    exportar_asignacion(
        resultados=resultados,
        archivo_salida=ARCHIVO_SALIDA,
        makespan=t_val.varValue,
        setup=SETUP,
    )

    print(f"Proceso completado correctamente. Archivo generado: {ARCHIVO_SALIDA}")
    print(f"Makespan esperado: {t_val.varValue:.2f} minutos")


if __name__ == "__main__":
    main()
