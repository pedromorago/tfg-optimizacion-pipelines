"""
==========================================================================
ESCENARIO PPO DE PRIORIDAD TEMPORAL
==========================================================================

Implementación del Caso C del modelo de Programación por Objetivos
descrito en la Sección 3.6 del documento, con resultados analizados
en la Sección 6.3.3.

JUSTIFICACIÓN DE LAS METAS Y PESOS
----------------------------------
Las metas se eligen en una región infactible respecto a la frontera
de Pareto eficiente (Sección 6.2.2):

  - Meta temporal:   O_t = 28 min   (alcanzable solo con N >= 11)
  - Meta económica:  O_c = 26 USD   (alcanzable solo con N <= 8)

La incompatibilidad entre ambas metas obliga al modelo PPO a priorizar
el cumplimiento de uno de los criterios. La ponderación

  W_t = 8,  W_c = 1

asigna prioridad dominante a la reducción del tiempo de feedback, lo
que lleva al modelo a aceptar un coste superior al deseado a cambio
de minimizar el superávit temporal.

Este escenario complementa al de contención de coste (Caso B):
mientras que aquél reduce el coste a expensas del tiempo, éste acelera
la pipeline a expensas del coste. La comparación de ambos casos
ilustra cómo distintas prioridades operativas conducen a soluciones
diferentes a través del mismo modelo PPO.

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

# Meta temporal: alcanzable solo con N >= 11 (frontera de Pareto)
O_TIEMPO = 28.00               # horizonte temporal deseado (min)

# Meta económica: alcanzable solo con N <= 8 (frontera de Pareto)
O_COSTE = 10.40                # presupuesto deseado por ejecución (USD)

# Ponderaciones: prioridad dominante al cumplimiento de la meta temporal
W_T = 8.0                      # peso del superávit temporal
W_C = 1.0                      # peso del superávit económico

# ============================================================
# CONFIGURACIÓN DE SALIDA
# ============================================================

ARCHIVO_SALIDA = "../Resultados/Resultados_PPO_Caso_C.txt"
CABECERA = "CASO C - PPO CON PRIORIDAD TEMPORAL"


def main():
    """Resuelve el escenario C y exporta los resultados a fichero."""
    resultado = resolver_instancia_ppo(
        nombre_modelo="PPO_Caso_C_Prioridad_Temporal",
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
