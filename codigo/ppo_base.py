import os
import math
import tempfile
import pulp

# ============================================================
# DATOS COMUNES DEL ESCENARIO REAL
# ============================================================

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

# Precisión de los tiempos de entrada (tres decimales, registros de CI).
PRECISION_DATOS = 0.001

# Tolerancia de gap absoluto del solver (min), por debajo de la precisión de los
# datos. Mismos parámetros que en la generación de la frontera de Pareto.
GAP_ABS = 0.00095


# ============================================================
# COTA INFERIOR DEL TIEMPO DE VALIDACIÓN (Sección 3.5.1)
# ============================================================

def redondear_hacia_arriba(valor, precision):
    # Redondea hacia arriba a la malla definida por la precisión de los datos.
    return math.ceil((valor - 1e-12) / precision) * precision


def calcular_cota_teorica(datos, setup, num_contenedores):
    # T_val >= S + max{ max_j p_j , (sum_j p_j) / N }.
    suma_tiempos = sum(datos.values())
    spec_mas_larga = max(datos.values())
    return setup + max(spec_mas_larga, suma_tiempos / num_contenedores)


def calcular_cota_discretizada(datos, setup, num_contenedores):
    # Cota teórica redondeada hacia arriba a la precisión de los datos. Desigualdad
    # redundante válida que acelera la minimización del tiempo de validación.
    cota = calcular_cota_teorica(datos, setup, num_contenedores)
    return redondear_hacia_arriba(cota, PRECISION_DATOS)


# ============================================================
# ESTADO DE TERMINACIÓN DEL SOLVER (a partir del log de CBC)
# ============================================================

def leer_estado_log(log_path, estado_pulp):
    # PuLP puede devolver 'Optimal' aunque CBC se haya detenido por límite de
    # tiempo; por ello el estado se lee directamente del registro (log) de CBC.
    # Si el log no está disponible, se devuelve el estado de PuLP.
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
# CONSTRUCCIÓN DEL MODELO PPO
# ============================================================

def construir_modelo_ppo(
    nombre_modelo,
    datos,
    setup,
    coste_unitario,
    m_max,
    t_max,
    o_tiempo,
    o_coste,
    w_t,
    w_c,
):
    tareas = list(datos.keys())
    contenedores = list(range(1, m_max + 1))

    modelo = pulp.LpProblem(nombre_modelo, pulp.LpMinimize)

    # Variables de decisión
    x = pulp.LpVariable.dicts("Asig", (contenedores, tareas), cat="Binary")
    z = pulp.LpVariable.dicts("Activo", contenedores, cat="Binary")
    t = pulp.LpVariable.dicts("Tiempo", contenedores, lowBound=0, cat="Continuous")

    cmax = pulp.LpVariable("Makespan", lowBound=0, cat="Continuous")
    coste_total = pulp.LpVariable("CosteTotal", lowBound=0, cat="Continuous")

    # Variables de desviación
    y_t_plus = pulp.LpVariable("Dev_T_Superavit", lowBound=0, cat="Continuous")
    y_t_minus = pulp.LpVariable("Dev_T_Deficit", lowBound=0, cat="Continuous")
    y_c_plus = pulp.LpVariable("Dev_C_Superavit", lowBound=0, cat="Continuous")
    y_c_minus = pulp.LpVariable("Dev_C_Deficit", lowBound=0, cat="Continuous")

    # Función objetivo: variante ponderada de la PPO con desviaciones normalizadas.
    modelo += (
        w_t * (y_t_plus / o_tiempo)
        + w_c * (y_c_plus / o_coste)
    ), "Z_Penalizacion_Global"

    # Restricciones de asignación única
    for j in tareas:
        modelo += pulp.lpSum(x[i][j] for i in contenedores) == 1

    # Restricciones de activación, tiempo y ruptura de simetría
    for i in contenedores:
        for j in tareas:
            modelo += x[i][j] <= z[i]

        # Activación no vacía: un contenedor activo recibe al menos una spec.
        modelo += z[i] <= pulp.lpSum(x[i][j] for j in tareas)

        modelo += t[i] == setup * z[i] + pulp.lpSum(datos[j] * x[i][j] for j in tareas)
        modelo += t[i] <= cmax
        modelo += t[i] <= t_max

        if i < m_max:
            modelo += z[i] >= z[i + 1]

    # Ecuación de coste total
    modelo += coste_total == coste_unitario * pulp.lpSum(t[i] for i in contenedores)

    # Metas de PPO
    modelo += cmax + y_t_minus - y_t_plus == o_tiempo
    modelo += coste_total + y_c_minus - y_c_plus == o_coste

    return modelo, x, z, t, cmax, coste_total, y_t_plus, y_c_plus


# ============================================================
# RESOLUCIÓN: SELECCIÓN + RESTAURACIÓN DE EFICIENCIA DE PARETO
# ============================================================
# La variante ponderada de la PPO selecciona la configuración (número de
# contenedores) que minimiza las desviaciones ponderadas respecto a las metas.
# Esa solución puede no ser Pareto-eficiente cuando una meta se cumple con
# holgura (Jones y Tamiz, 2010); para garantizar una solución eficiente se fija
# la configuración seleccionada y se minimiza el tiempo de validación. Igual que
# en la frontera de Pareto, el tiempo óptimo de cada configuración queda
# caracterizado por el intervalo [cota inferior, T_val] y el estado de
# terminación se lee del log de CBC, no del estado de PuLP.

def resolver_instancia_ppo(
    nombre_modelo,
    setup,
    coste_unitario,
    m_max,
    t_max,
    o_tiempo,
    o_coste,
    w_t,
    w_c,
    time_limit=120,
):
    contenedores = list(range(1, m_max + 1))
    tareas = list(DATOS_PIPELINE_REAL.keys())

    modelo, x, z, t, cmax, coste_total, y_t_plus, y_c_plus = construir_modelo_ppo(
        nombre_modelo=nombre_modelo,
        datos=DATOS_PIPELINE_REAL,
        setup=setup,
        coste_unitario=coste_unitario,
        m_max=m_max,
        t_max=t_max,
        o_tiempo=o_tiempo,
        o_coste=o_coste,
        w_t=w_t,
        w_c=w_c,
    )

    dir_logs = tempfile.gettempdir()

    # --- Selección de la configuración (PPO ponderada) ---
    log_sel = os.path.join(dir_logs, f"cbc_ppo_sel_{nombre_modelo}.log")
    solver_sel = pulp.PULP_CBC_CMD(
        msg=False, timeLimit=time_limit, gapRel=0.0, gapAbs=GAP_ABS, logPath=log_sel
    )
    modelo.solve(solver_sel)
    estado_seleccion = leer_estado_log(log_sel, pulp.LpStatus[modelo.status])
    num_activos = sum(int(round(z[i].varValue)) for i in contenedores)

    # --- Restauración de eficiencia: fijada la configuración, minimizar T_val ---
    modelo += pulp.lpSum(z[i] for i in contenedores) == num_activos, "Fijar_configuracion"
    cota_teorica = calcular_cota_teorica(DATOS_PIPELINE_REAL, setup, num_activos)
    cota_disc = calcular_cota_discretizada(DATOS_PIPELINE_REAL, setup, num_activos)
    modelo += cmax >= cota_disc, "Cota_inferior_discretizada"
    modelo.setObjective(cmax)

    log_rest = os.path.join(dir_logs, f"cbc_ppo_rest_{nombre_modelo}.log")
    solver_rest = pulp.PULP_CBC_CMD(
        msg=False, timeLimit=time_limit, gapRel=0.0, gapAbs=GAP_ABS, logPath=log_rest
    )
    modelo.solve(solver_rest)
    estado_restauracion = leer_estado_log(log_rest, pulp.LpStatus[modelo.status])

    resultado = {
        "estado_seleccion": estado_seleccion,
        "estado": estado_restauracion,
        "modelo": modelo,
        "x": x,
        "z": z,
        "t": t,
        "cmax": cmax,
        "coste_total": coste_total,
        "y_t_plus": y_t_plus,
        "y_c_plus": y_c_plus,
        "contenedores": contenedores,
        "tareas": tareas,
        "setup": setup,
        "o_tiempo": o_tiempo,
        "o_coste": o_coste,
        "w_t": w_t,
        "w_c": w_c,
    }

    if cmax.varValue is not None:
        gap = cmax.varValue - cota_teorica
        resultado["num_activos"] = sum(int(round(z[i].varValue)) for i in contenedores)
        resultado["makespan"] = cmax.varValue
        resultado["cota"] = cota_teorica
        resultado["gap"] = gap if gap > 0 else 0.0
        resultado["coste"] = coste_total.varValue
        resultado["dev_t"] = y_t_plus.varValue
        resultado["dev_c"] = y_c_plus.varValue

    return resultado


# ============================================================
# EXPORTACIÓN DE RESULTADOS
# ============================================================

def exportar_resultados(resultado, archivo_salida, titulo):
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("=" * 78 + "\n")
        f.write(titulo + "\n")
        f.write("=" * 78 + "\n")

        if "makespan" not in resultado:
            f.write(f"Estado de la selección: {resultado['estado_seleccion']}\n")
            f.write(f"Estado de la restauración: {resultado['estado']}\n")
            return

        gap_segundos = resultado["gap"] * 60.0

        f.write(f"Estado de la selección de configuración: {resultado['estado_seleccion']}\n")
        f.write(f"Estado de la restauración de eficiencia: {resultado['estado']}\n")
        f.write(f"Contenedores activados: {resultado['num_activos']}\n")
        f.write(f"Tiempo de validación (T_val): {resultado['makespan']:.4f} min\n")
        f.write(f"Cota inferior (Sección 3.5.1): {resultado['cota']:.4f} min\n")
        f.write(f"Gap (T_val - cota): {resultado['gap']:.4f} min ({gap_segundos:.2f} s)\n")
        f.write(f"Coste total alcanzado: {resultado['coste']:.2f} USD\n")
        f.write(f"Desviación temporal (superávit): {resultado['dev_t']:.2f} min\n")
        f.write(f"Desviación económica (superávit): {resultado['dev_c']:.2f} USD\n")
        f.write("-" * 78 + "\n")
        f.write(f"Meta temporal: {resultado['o_tiempo']:.2f} min\n")
        f.write(f"Meta económica: {resultado['o_coste']:.2f} USD\n")
        f.write(f"Pesos (W_t, W_c): ({resultado['w_t']:.2f}, {resultado['w_c']:.2f})\n")
        f.write("=" * 78 + "\n")
        f.write(
            "Nota: el tiempo de validación óptimo de la configuración está contenido "
            "en [cota, T_val]. Con estado OPTIMAL, T_val es el óptimo demostrado y el "
            "gap recoge solo la holgura de la cota; con TIME_LIMIT, el gap acota la "
            "distancia de T_val al óptimo.\n"
        )
        f.write("=" * 78 + "\n\n")

        for i in resultado["contenedores"]:
            if resultado["z"][i].varValue > 0.5:
                tareas_asignadas = [
                    tarea
                    for tarea in resultado["tareas"]
                    if resultado["x"][i][tarea].varValue > 0.5
                ]

                tiempo_total = resultado["t"][i].varValue
                carga_neta = tiempo_total - resultado["setup"]

                f.write(
                    f"CONTENEDOR {i} "
                    f"(Tiempo total: {tiempo_total:.2f} min | "
                    f"Carga neta: {carga_neta:.2f} min)\n"
                )
                f.write("-" * 78 + "\n")
                f.write(" ".join(f"src/tests/{tarea}" for tarea in tareas_asignadas))
                f.write("\n\n")


# ============================================================
# IMPRESIÓN POR CONSOLA
# ============================================================

def imprimir_resumen(resultado, cabecera, archivo_salida):
    print("\n" + "=" * 78)
    print(cabecera)
    print("=" * 78)
    print(f"Estado de la selección de configuración: {resultado['estado_seleccion']}")
    print(f"Estado de la restauración de eficiencia: {resultado['estado']}")

    if "makespan" in resultado:
        gap_segundos = resultado["gap"] * 60.0
        print(f"Contenedores activados: {resultado['num_activos']}")
        print(f"Tiempo de validación (T_val): {resultado['makespan']:.4f} min")
        print(f"Cota inferior: {resultado['cota']:.4f} min")
        print(f"Gap (T_val - cota): {resultado['gap']:.4f} min ({gap_segundos:.2f} s)")
        print(f"Coste total alcanzado: {resultado['coste']:.2f} USD")
        print(f"Desviación temporal (superávit): {resultado['dev_t']:.2f} min")
        print(f"Desviación económica (superávit): {resultado['dev_c']:.2f} USD")

    print(f"Archivo exportado: {archivo_salida}")
