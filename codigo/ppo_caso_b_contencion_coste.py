"""
==========================================================================
ESCENARIO PPO DE CONTENCIÓN DE COSTE
==========================================================================

Implementación del Caso B del modelo de Programación por Objetivos
descrito en la Sección 3.6 del documento, con resultados analizados
en la Sección 6.3.2.

JUSTIFICACIÓN DE LAS METAS Y PESOS
----------------------------------
Las metas se eligen deliberadamente en una región infactible respecto
a la frontera de Pareto eficiente (Sección 6.2.2):

  - Meta temporal:   O_t = 33 min  (alcanzable solo con N >= 8)
  - Meta económica:  O_c = 19 USD  (alcanzable solo con N <= 4)

Como las dos metas no pueden cumplirse simultáneamente (ningún punto
de la frontera satisface ambas a la vez), el modelo PPO debe priorizar
el incumplimiento de uno de los criterios. La ponderación

  W_t = 1,  W_c = 8

asigna prioridad dominante a la contención del coste, lo que conduce
al modelo a sacrificar el cumplimiento de la meta temporal a cambio
de minimizar el superávit económico.

Esta configuración ilustra el comportamiento característico de la PPO
ante metas competitivas: las desviaciones positivas no son nulas y
las ponderaciones determinan la solución elegida.

PARÁMETROS DEL ENTORNO
----------------------
  S         : tiempo de setup por contenedor (16,33 min)
  C_u       : coste unitario (0,04 USD/min)
  m_max     : cota superior sobre el número de contenedores (20)
  T_max     : tiempo máximo permitido por contenedor (60 min)
"""

from ppo_base import resolver_instancia_ppo, exportar_resultados, imprimir_resumen

# ============================================================
# PARÁMETROS DEL ENTORNO OPERATIVO
# ============================================================

SETUP = 16.33                  # tiempo de setup por contenedor (min)
COSTE_UNITARIO = 0.04          # coste unitario (USD/min)
M_MAX = 20                     # cota superior sobre el número de contenedores
T_MAX = 60                     # tiempo máximo permitido por contenedor (min)

# ============================================================
# METAS Y PONDERACIONES PPO
# ============================================================

# Meta temporal: alcanzable solo con N >= 8 (frontera de Pareto)
O_TIEMPO = 33.00               # horizonte temporal deseado (min)

# Meta económica: alcanzable solo con N <= 4 (frontera de Pareto)
O_COSTE = 7.60                 # presupuesto deseado por ejecución (USD)

# Ponderaciones: prioridad dominante al cumplimiento de la meta económica
W_T = 1.0                      # peso del superávit temporal
W_C = 8.0                      # peso del superávit económico

# ============================================================
# CONFIGURACIÓN DE SALIDA
# ============================================================

ARCHIVO_SALIDA = "../Resultados/Resultados_PPO_Caso_B.txt"
CABECERA = "CASO B - PPO CON CONTENCION DE COSTE"


def main():
    """Resuelve el escenario B y exporta los resultados a fichero."""
    resultado = resolver_instancia_ppo(
        nombre_modelo="PPO_Caso_B_Contencion_Coste",
        setup=SETUP,
        coste_unitario=COSTE_UNITARIO,
        m_max=M_MAX,
        t_max=T_MAX,
        o_tiempo=O_TIEMPO,
        o_coste=O_COSTE,
        w_t=W_T,
        w_c=W_C,
    )

    exportar_resultados(resultado, ARCHIVO_SALIDA, CABECERA)
    imprimir_resumen(resultado, CABECERA, ARCHIVO_SALIDA)


if __name__ == "__main__":
    main()
