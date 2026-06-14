from extraccion_empirica_base import (
    calcular_metricas_empiricas,
    imprimir_metricas,
    guardar_metricas_txt,
)

# ======================================================================
# DATOS DEL ESCENARIO REAL (CONFIGURACIÓN ORIGINAL)
# ======================================================================

datos_pipeline_real = {
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
    'reporting/version-dashboard.spec.ts': 0.010
}

# ======================================================================
# ASIGNACIÓN ORIGINAL A CONTENEDORES
# ======================================================================

asignacion_contenedores = {
    "Contenedor 1 (Admin)": ["admin/"],
    "Contenedor 2 (Catalog)": ["catalog/"],
    "Contenedor 3 (Reporting)": ["reporting/"],
    "Contenedor 4 (Projects A)": ["projects-1/"],
    "Contenedor 5 (Editor)": ["editor/"],
    "Contenedor 6 (Rules)": ["rules/"],
    "Contenedor 7 (Projects B)": ["projects-2/"],
}

# ======================================================================
# TIEMPOS TOTALES OBSERVADOS
# ======================================================================

tiempos_totales_observados = {
    "Contenedor 1 (Admin)": 59.73,
    "Contenedor 2 (Catalog)": 46.48,
    "Contenedor 3 (Reporting)": 30.35,
    "Contenedor 4 (Projects A)": 27.71,
    "Contenedor 5 (Editor)": 26.87,
    "Contenedor 6 (Rules)": 25.95,
    "Contenedor 7 (Projects B)": 23.75,
}

# ======================================================================
# EJECUCIÓN
# ======================================================================

ARCHIVO_SALIDA_TXT = "../Resultados/salida_extraccion_original.txt"

def main():
    metricas = calcular_metricas_empiricas(
        datos_pipeline_real=datos_pipeline_real,
        asignacion_contenedores=asignacion_contenedores,
        tiempos_totales_observados=tiempos_totales_observados,
        coste_unitario=0.04,
    )

    imprimir_metricas("EXTRACCIÓN EMPÍRICA - CONFIGURACIÓN ORIGINAL", metricas)
    guardar_metricas_txt(
        "EXTRACCIÓN EMPÍRICA - CONFIGURACIÓN ORIGINAL",
        metricas,
        ARCHIVO_SALIDA_TXT,
    )


if __name__ == "__main__":
    main()
