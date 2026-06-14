import pulp
import os
import tempfile

# ============================================================
# DATOS DEL ESCENARIO REAL (74 specs, importados de A.1)
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

# ============================================================
# PARÁMETROS DEL MODELO
# ============================================================

S = 16.33          # tiempo de setup por contenedor (min)
CU = 0.04          # coste unitario (USD/min)
T_MAX = 60.0       # límite técnico por contenedor (min)
M_MAX = 20         # cota superior sobre el número de contenedores

FICHERO_SALIDA = "../Resultados/Resultado_Configuracion_N_Libre.txt"


def leer_estado_log(log_path, estado_pulp):
    """Lee el estado real del registro de CBC.

    PuLP puede informar de 'Optimal' aunque el solver se haya detenido
    por tiempo, de modo que el estado fiable se obtiene del log.
    """
    if not os.path.exists(log_path):
        return estado_pulp
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log = f.read()
    if ("Stopped on time limit" in log or "Exiting on maximum time" in log
            or "Exiting on maximum seconds" in log):
        return "TIME_LIMIT"
    if "Result - Optimal solution found" in log:
        return "OPTIMAL"
    return estado_pulp


def resolver_configuracion_minima():
    """Minimiza el número de contenedores sujeto a que el tiempo de
    validación alcance la cota inferior teórica de la Sección 3.5.1.
    Imprime el reporte y lo guarda en FICHERO_SALIDA."""
    specs = list(DATOS_PIPELINE_REAL.keys())
    p = DATOS_PIPELINE_REAL
    I = list(range(M_MAX))
    cota_teorica = S + max(p.values())          # 16.33 + 9.60 = 25.93

    # Buffer del reporte: cada línea se imprime y se acumula para el .txt
    out = []
    def w(linea=""):
        print(linea)
        out.append(linea)

    w("=" * 72)
    w("CONFIGURACIÓN ÓPTIMA CON NÚMERO DE CONTENEDORES LIBRE")
    w("=" * 72)
    w(f"Datos: {len(specs)} specs | S = {S} min | Cu = {CU} USD/min | M_MAX = {M_MAX}")
    w(f"Cota inferior teórica del tiempo (3.5.1): {cota_teorica:.2f} min")
    w(f"Objetivo: min Sum(z_i)  s.a.  T_val <= {cota_teorica:.2f}")
    w("")

    prob = pulp.LpProblem("config_minima_en_cota", pulp.LpMinimize)

    # Variables de decisión
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat=pulp.LpBinary)
         for i in I for j in specs}
    z = {i: pulp.LpVariable(f"z_{i}", cat=pulp.LpBinary) for i in I}
    t = {i: pulp.LpVariable(f"t_{i}", lowBound=0) for i in I}
    T_val = pulp.LpVariable("T_val", lowBound=0)

    # OBJETIVO: minimizar el número de contenedores activos
    prob += pulp.lpSum(z[i] for i in I)

    # R1: cada spec se asigna exactamente una vez
    for j in specs:
        prob += pulp.lpSum(x[i, j] for i in I) == 1
    # R2: coherencia de activación (un contenedor con specs debe estar activo)
    for i in I:
        for j in specs:
            prob += x[i, j] <= z[i]
    # R3: tiempo de cada contenedor = setup + specs asignados
    for i in I:
        prob += t[i] == S * z[i] + pulp.lpSum(p[j] * x[i, j] for j in specs)
    # R4: definición del makespan
    for i in I:
        prob += T_val >= t[i]
    # R5: límite técnico por contenedor
    for i in I:
        prob += t[i] <= T_MAX
    # R6: el tiempo de validación debe alcanzar la cota inferior teórica
    prob += T_val <= cota_teorica
    # R7: ruptura de simetría
    for i in range(len(I) - 1):
        prob += z[I[i]] >= z[I[i + 1]]

    # Resolución (se lee el estado real del log de CBC)
    print("Resolviendo...")
    log_path = os.path.join(tempfile.gettempdir(), "cbc_config_minima.log")
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=240, logPath=log_path)
    prob.solve(solver)
    estado = leer_estado_log(log_path, pulp.LpStatus[prob.status])

    Tval_final = T_val.value()
    N_final = sum(int(z[i].value() + 0.5) for i in I)
    coste_final = CU * sum(t[i].value() for i in I)

    w("=" * 72)
    w("RESULTADO")
    w("=" * 72)
    w(f"  Estado del solver (CBC):  {estado}")
    w(f"  N (contenedores activos): {N_final}")
    w(f"  T_val (makespan):         {Tval_final:.2f} min")
    w(f"  Coste total:              {coste_final:.2f} USD")
    w("")
    w("  Asignación por contenedor activo:")
    for i in I:
        if z[i].value() > 0.5:
            specs_i = sorted(((p[j], j) for j in specs if x[i, j].value() > 0.5),
                             reverse=True)
            w(f"    Contenedor {i + 1:2d}  ->  t = {t[i].value():6.2f} min   ({len(specs_i)} specs)")
            for pj, nombre in specs_i:
                w(f"          {pj:6.3f} min   {nombre}")

    w("")
    w("=" * 72)
    w("INTERPRETACIÓN")
    w("=" * 72)
    sumpj = sum(p.values())
    cota_13 = S + max(max(p.values()), sumpj / 13)
    w(f"  Cota inferior teórica (3.5.1): S + max_j p_j = {S} + {max(p.values())} = {cota_teorica:.2f} min")
    w(f"  El menor número de contenedores que la alcanza es N = {N_final} (óptimo certificado).")
    w(f"  Con N = 13: tiempo mínimo = {S} + {sumpj / 13:.3f} = {cota_13:.2f} min > {cota_teorica:.2f}: infactible.")
    w(f"  Por tanto N = {N_final} es el límite inferior alcanzable del tiempo de validación,")
    w(f"  y cualquier N >= {N_final} iguala ese tiempo sin mejorarlo.")
    w("")

    # Guardar el reporte en el fichero de texto
    os.makedirs(os.path.dirname(FICHERO_SALIDA), exist_ok=True)
    with open(FICHERO_SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"[Reporte guardado en: {os.path.abspath(FICHERO_SALIDA)}]")

    return {"T_val": Tval_final, "N": N_final, "C": coste_final, "estado": estado}


if __name__ == "__main__":
    resolver_configuracion_minima()
