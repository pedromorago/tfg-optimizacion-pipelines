"""
==========================================================================
ESCENARIO PPO ADVERSO DE SETUP
==========================================================================

Implementación del Caso D del modelo de Programación por Objetivos
descrito en la Sección 3.6 del documento, con resultados analizados
en la Sección 6.3.4.

JUSTIFICACIÓN DEL ESCENARIO
---------------------------
Este escenario evalúa el comportamiento del modelo bajo condiciones
adversas de infraestructura, sustituyendo el valor medio del tiempo
de setup observado (S = 16,33 min) por el peor valor registrado en
los logs de ejecución:

  S_peor = 18,22 min

Este desplazamiento del parámetro de setup tiene un efecto directo
sobre la frontera de Pareto: cada makespan resulta más caro y cada
presupuesto da menos tiempo, lo que reduce el espacio de soluciones
factibles para cada nivel de paralelismo.

JUSTIFICACIÓN DE LAS METAS Y PESOS
----------------------------------
A diferencia de los Casos B y C, donde las metas son extremas y los
pesos asimétricos, este escenario combina:

  - Metas competitivas pero moderadas:
      O_t = 35 min,    O_c = 22 USD

  - Ponderaciones iguales:
      W_t = 1,    W_c = 1

En setup adverso, el cumplimiento simultáneo de ambas metas no es
posible. Al estar normalizadas las desviaciones respecto a sus propias
metas, unos pesos iguales representan un escenario sin prioridad
explícita entre el incumplimiento temporal y el económico: el modelo
no favorece a priori a ninguno de los dos criterios.

Esta configuración complementa los Casos B y C: aquéllos muestran
cómo la asimetría de pesos induce soluciones extremas (mínimo coste
o mínimo tiempo); éste muestra cómo, ante prioridades equilibradas,
la PPO produce una solución de compromiso bajo presión simultánea
sobre ambos criterios.

PARÁMETROS DEL ENTORNO
----------------------
  S_peor    : tiempo de setup por contenedor en condiciones adversas (18,22 min)
  C_u       : coste unitario (0,04 USD/min)
  m_max     : cota superior sobre el número de contenedores (20)
  T_max     : tiempo máximo permitido por contenedor (60 min)
"""

from ppo_base import resolver_instancia_ppo, exportar_resultados, imprimir_resumen

# ============================================================
# PARÁMETROS DEL ENTORNO OPERATIVO
# ============================================================

SETUP_ADVERSO = 18.22          # peor valor de setup observado (min)
COSTE_UNITARIO = 0.04          # coste unitario (USD/min)
M_MAX = 20                     # cota superior sobre el número de contenedores
T_MAX = 60                     # tiempo máximo permitido por contenedor (min)

# ============================================================
# METAS Y PONDERACIONES PPO
# ============================================================

# Metas competitivas en condiciones adversas: ambas son ambiciosas pero
# ninguna es por sí sola tan extrema como las de los Casos B y C
O_TIEMPO = 35.00               # horizonte temporal deseado (min)
O_COSTE = 8.80                 # presupuesto deseado por ejecución (USD)

# Ponderaciones iguales: ambos criterios reciben el mismo peso. Al estar
# normalizadas las desviaciones, no hay prioridad explícita de uno sobre otro
W_T = 1.0                      # peso del superávit temporal
W_C = 1.0                      # peso del superávit económico

# ============================================================
# CONFIGURACIÓN DE SALIDA
# ============================================================

ARCHIVO_SALIDA = "../Resultados/Resultados_PPO_Caso_D.txt"
CABECERA = "CASO D - PPO BAJO SETUP ADVERSO"


def main():
    """Resuelve el escenario D y exporta los resultados a fichero."""
    resultado = resolver_instancia_ppo(
        nombre_modelo="PPO_Caso_D_Setup_Adverso",
        setup=SETUP_ADVERSO,
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
