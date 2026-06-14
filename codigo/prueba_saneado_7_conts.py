import os
import pulp

# ============================================================
# PARÁMETROS DEL MODELO
# ============================================================

SETUP = 16.33
CU = 0.04          # coste unitario (USD/min)
NUM_CONTENEDORES = 7
ARCHIVO_SALIDA = "../Resultados/Asignacion_7_Contenedores_Saneado.txt"

# ============================================================
# DATOS DE ENTRADA
# ============================================================

DATOS_PIPELINE_SANEADO = {
    'rules/rules.spec.ts': 9.600,
    'reporting/reports-generation.spec.ts': 8.197,
    'admin/project-ownership.spec.ts': 5.645,
    'projects-1/automations.spec.ts': 4.741,
    'editor/zone-block.spec.ts': 4.558,
    'admin/business-unit-permissions-bulk.spec.ts': 4.348,
    'admin/user.spec.ts': 3.877,
    'catalog/component.spec.ts': 3.150,
    'admin/custom-fields.spec.ts': 2.990,
    'projects-2/projects.spec.ts': 2.643,
    'catalog/library.spec.ts': 2.583,
    'admin/workflow-state.spec.ts': 2.579,
    'catalog/zone.spec.ts': 2.511,
    'projects-1/floating-modals.spec.ts': 2.468,
    'reporting/dashboard.spec.ts': 2.359,
    'admin/issue-trackers-profiles.spec.ts': 2.065,
    'projects-2/templates.spec.ts': 1.931,
    'projects-2/versions.spec.ts': 1.913,
    'editor/block-inspector.spec.ts': 1.826,
    'catalog/record-classification.spec.ts': 1.757,
    'catalog/asset.spec.ts': 1.696,
    'catalog/standard.spec.ts': 1.689,
    'projects-1/issue-tracker-profiles.spec.ts': 1.431,
    'editor/project-import.spec.ts': 1.376,
    'catalog/record.spec.ts': 1.315,
    'projects-1/findings.spec.ts': 1.290,
    'reporting/reports-workflows.spec.ts': 1.255,
    'catalog/automations.spec.ts': 1.226,
    'admin/business-unit.spec.ts': 1.221,
    'projects-2/records.spec.ts': 1.213,
    'admin/redirection.spec.ts': 1.141,
    'catalog/finding.spec.ts': 1.011,
    'catalog/tag-patterns.spec.ts': 0.983,
    'catalog/scenario.spec.ts': 0.959,
    'catalog/content-hub.spec.ts': 0.759,
    'projects-1/custom-views.spec.ts': 0.725,
    'admin/user-profile.spec.ts': 0.704,
    'catalog/category.spec.ts': 0.682,
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
    'admin/custom-fields-managements.spec.ts': 0.327,
    'editor/artifact.spec.ts': 0.313,
    'catalog/score-calculations.spec.ts': 0.304,
    'admin/login.spec.ts': 0.175,
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
    'rules/questionnaire.spec.ts': 0.010,
    'catalog/form-template.spec.ts': 0.010,
    'editor/data-import.spec.ts': 0.010,
    'editor/unassigned-block.spec.ts': 0.010,
    'editor/restore-default-zone.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-with-archived-license.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-without-archived-license.spec.ts': 0.010,
    'reporting/archive-projects/archive-projects-restore-and-delete.spec.ts': 0.010,
    'reporting/version-dashboard.spec.ts': 0.010,
    'admin/issue-trackers-profiles-empty.spec.ts': 0.010
}

# ============================================================
# CONSTRUCCIÓN DEL MODELO
# ============================================================

def construir_modelo(datos_pipeline_saneado: dict, setup: float, num_contenedores: int):
    tareas = list(datos_pipeline_saneado.keys())
    contenedores = list(range(1, num_contenedores + 1))

    modelo = pulp.LpProblem("Asignacion_Saneada_7_Contenedores", pulp.LpMinimize)

    x = pulp.LpVariable.dicts("Asig", (contenedores, tareas), cat="Binary")
    cmax = pulp.LpVariable("Makespan", lowBound=0)

    modelo += cmax

    for tarea in tareas:
        modelo += pulp.lpSum(x[i][tarea] for i in contenedores) == 1

    for contenedor in contenedores:
        modelo += (
            setup
            + pulp.lpSum(datos_pipeline_saneado[tarea] * x[contenedor][tarea] for tarea in tareas)
            <= cmax
        )

    # A diferencia de generar_pareto.py, aquí no se imponen t_i <= T_max ni la
    # activación de al menos una spec por contenedor: con N=7 fijo y un makespan
    # muy por debajo del límite de 60 min, ambas son no vinculantes y no alteran
    # el óptimo. Solo importan al barrer configuraciones con pocos contenedores
    # (N pequeño), como hace la frontera de Pareto.

    return modelo, x, cmax, tareas, contenedores

# ============================================================
# RESOLUCIÓN DEL MODELO
# ============================================================

def resolver_modelo(modelo):
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=120, gapRel=0.0)
    modelo.solve(solver)

# ============================================================
# EXTRACCIÓN DE RESULTADOS
# ============================================================

def extraer_asignacion(x, tareas, contenedores, datos_pipeline_saneado: dict, setup: float):
    resultados = []
    for contenedor in contenedores:
        tareas_asignadas = [tarea for tarea in tareas if x[contenedor][tarea].varValue > 0.5]
        tiempo_neto = sum(datos_pipeline_saneado[tarea] for tarea in tareas_asignadas)
        tiempo_total = tiempo_neto + setup

        resultados.append({
            "contenedor": contenedor,
            "tareas_asignadas": tareas_asignadas,
            "tiempo_neto": tiempo_neto,
            "tiempo_total": tiempo_total,
        })
    return resultados

# ============================================================
# EXPORTACIÓN DE RESULTADOS
# ============================================================

def exportar_asignacion(resultados: list[dict], archivo_salida: str, makespan: float, setup: float) -> None:
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("=" * 75 + "\n")
        f.write("ASIGNACIÓN PARA SIETE CONTENEDORES (ESCENARIO SANEADO)\n")
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
    print("Inicio de la resolución del modelo saneado para siete contenedores.")

    modelo, x, cmax, tareas, contenedores = construir_modelo(
        datos_pipeline_saneado=DATOS_PIPELINE_SANEADO,
        setup=SETUP,
        num_contenedores=NUM_CONTENEDORES,
    )

    resolver_modelo(modelo)

    resultados = extraer_asignacion(
        x=x,
        tareas=tareas,
        contenedores=contenedores,
        datos_pipeline_saneado=DATOS_PIPELINE_SANEADO,
        setup=SETUP,
    )

    carga_neta_agregada = sum(DATOS_PIPELINE_SANEADO.values())
    coste_total = CU * ((SETUP * NUM_CONTENEDORES) + carga_neta_agregada)

    exportar_asignacion(
        resultados=resultados,
        archivo_salida=ARCHIVO_SALIDA,
        makespan=cmax.varValue,
        setup=SETUP,
    )

    print(f"Proceso completado correctamente. Archivo generado: {ARCHIVO_SALIDA}")
    print(f"Makespan esperado: {cmax.varValue:.2f} minutos")
    print(f"Carga neta agregada: {carga_neta_agregada:.2f} minutos")
    print(f"Coste total asociado: {coste_total:.2f} USD")

if __name__ == "__main__":
    main()
