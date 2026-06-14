from extraccion_empirica_base import (
    calcular_metricas_empiricas,
    imprimir_metricas,
    guardar_metricas_txt,
)

# ======================================================================
# DATOS DEL ESCENARIO REAL (CONFIGURACIÓN OPTIMIZADA OBSERVADA)
# ======================================================================

datos_pipeline_real = {
    'rules/rules.spec.ts': 9.790,
    'catalog/reports-generation.spec.ts': 8.178,
    'projects-1/user.spec.ts': 7.238,
    'editor/custom-fields-managements.spec.ts': 7.133,
    'reporting/automations.spec.ts': 6.420,
    'projects-2/project-ownership.spec.ts': 5.673,
    'reporting/zone-block.spec.ts': 4.465,
    'admin/business-unit-permissions-bulk.spec.ts': 4.353,
    'projects-2/issue-trackers-profiles.spec.ts': 3.888,
    'rules/score-calculations.spec.ts': 3.698,
    'reporting/component.spec.ts': 3.133,
    'projects-2/custom-fields.spec.ts': 3.035,
    'projects-1/business-unit.spec.ts': 2.948,
    'editor/finding.spec.ts': 2.735,
    'projects-1/tag-patterns.spec.ts': 2.733,
    'projects-1/scenario.spec.ts': 2.712,
    'catalog/floating-modals.spec.ts': 2.665,
    'editor/library.spec.ts': 2.637,
    'editor/workflow-state.spec.ts': 2.613,
    'catalog/projects.spec.ts': 2.580,
    'projects-2/zone.spec.ts': 2.535,
    'admin/user-profile.spec.ts': 2.452,
    'reporting/dashboard.spec.ts': 2.035,
    'admin/versions.spec.ts': 1.945,
    'admin/login.spec.ts': 1.878,
    'projects-1/record-classification.spec.ts': 1.785,
    'rules/standard.spec.ts': 1.707,
    'rules/asset.spec.ts': 1.675,
    'catalog/issue-tracker-profiles.spec.ts': 1.463,
    'editor/project-import.spec.ts': 1.375,
    'catalog/findings.spec.ts': 1.330,
    'admin/record.spec.ts': 1.328,
    'catalog/reports-workflows.spec.ts': 1.278,
    'projects-2/block-inspector.spec.ts': 1.262,
    'projects-2/automations.spec.ts': 1.253,
    'admin/records.spec.ts': 1.158,
    'admin/redirection.spec.ts': 1.125,
    'reporting/templates.spec.ts': 0.917,
    'admin/content-hub.spec.ts': 0.792,
    'editor/templates-dashboard.spec.ts': 0.688,
    'projects-1/custom-views.spec.ts': 0.688,
    'admin/category.spec.ts': 0.602,
    'editor/questionnaire.spec.ts': 0.570,
    'admin/dashboard-empty.spec.ts': 0.518,
    'admin/block-with-user.spec.ts': 0.502,
    'rules/project-list.spec.ts': 0.480,
    'admin/audit-log.spec.ts': 0.477,
    'rules/project-dashboard.spec.ts': 0.410,
    'editor/role.spec.ts': 0.410,
    'reporting/workflow-state-change.spec.ts': 0.348,
    'reporting/restore-previous-board.spec.ts': 0.345,
    'projects-2/artifact.spec.ts': 0.302,
    'projects-2/workflow-rule.spec.ts': 0.167,
    'catalog/navigation.spec.ts': 0.158,
    'catalog/support.spec.ts': 0.067,
    'catalog/user-interface.spec.ts': 0.065,
    'rules/license.spec.ts': 0.065,
    'reporting/analytics-settings.spec.ts': 0.065,
    'reporting/api.spec.ts': 0.065,
    'reporting/features.spec.ts': 0.065,
    'projects-2/email.spec.ts': 0.063,
    'admin/header.spec.ts': 0.052,
    'reporting/archive-projects/archive-projects-without-archived-license.spec.ts': 0.010,
    'editor/issue-trackers-profiles-empty.spec.ts': 0.010,
    'catalog/questionnaire.spec.ts': 0.010,
    'projects-1/archive-projects/archive-projects-with-archived-license.spec.ts': 0.010,
    'catalog/configuration.spec.ts': 0.010,
    'projects-1/data-import.spec.ts': 0.010,
    'projects-1/unassigned-block.spec.ts': 0.010,
    'projects-1/restore-default-zone.spec.ts': 0.010,
    'projects-1/version-dashboard.spec.ts': 0.010,
    'rules/dashboard-cross-domain.spec.ts': 0.010,
    'reporting/form-template.spec.ts': 0.010,
    'admin/archive-projects/archive-projects-restore-and-delete.spec.ts': 0.010
}

# ======================================================================
# CONVERSIÓN AL ESQUEMA DE 7 CONTENEDORES
# ======================================================================
# Se mantiene esta lógica:
# Contenedor 1 -> admin
# Contenedor 2 -> catalog
# Contenedor 3 -> reporting
# Contenedor 4 -> projects-1
# Contenedor 5 -> editor
# Contenedor 6 -> rules
# Contenedor 7 -> projects-2

asignacion_contenedores = {
    "Contenedor 1 (Split 1)": ["admin/"],
    "Contenedor 2 (Split 2)": ["catalog/"],
    "Contenedor 3 (Split 3)": ["reporting/"],
    "Contenedor 4 (Split 4)": ["projects-1/"],
    "Contenedor 5 (Split 5)": ["editor/"],
    "Contenedor 6 (Split 6)": ["rules/"],
    "Contenedor 7 (Split 7)": ["projects-2/"],
}

# ======================================================================
# TIEMPOS TOTALES OBSERVADOS
# ======================================================================

tiempos_totales_observados = {
    "Contenedor 1 (Split 1)": 33.64,
    "Contenedor 2 (Split 2)": 34.03,
    "Contenedor 3 (Split 3)": 34.31,
    "Contenedor 4 (Split 4)": 34.13,
    "Contenedor 5 (Split 5)": 34.59,
    "Contenedor 6 (Split 6)": 34.57,
    "Contenedor 7 (Split 7)": 34.81,
}

# ======================================================================
# EJECUCIÓN
# ======================================================================

ARCHIVO_SALIDA_TXT = "../Resultados/salida_extraccion_optimizada.txt"

def main():
    metricas = calcular_metricas_empiricas(
        datos_pipeline_real=datos_pipeline_real,
        asignacion_contenedores=asignacion_contenedores,
        tiempos_totales_observados=tiempos_totales_observados,
        coste_unitario=0.04,
    )

    imprimir_metricas("EXTRACCIÓN EMPÍRICA - CONFIGURACIÓN OPTIMIZADA", metricas)
    guardar_metricas_txt(
        "EXTRACCIÓN EMPÍRICA - CONFIGURACIÓN OPTIMIZADA",
        metricas,
        ARCHIVO_SALIDA_TXT,
    )


if __name__ == "__main__":
    main()
