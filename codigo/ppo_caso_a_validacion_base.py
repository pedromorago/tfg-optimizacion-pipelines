from ppo_base import resolver_instancia_ppo, exportar_resultados, imprimir_resumen

# ============================================================
# PARÁMETROS DEL CASO A: VALIDACIÓN DE LA SOLUCIÓN BASE
# ============================================================

SETUP = 16.33
COSTE_UNITARIO = 0.04
M_MAX = 20
T_MAX = 60

# Metas PPO diseñadas para seleccionar una configuración coherente
# con la solución base implantada de 7 contenedores
O_TIEMPO = 35.05
O_COSTE = 9.64

# Pesos equilibrados
W_T = 1.0
W_C = 1.0

ARCHIVO_SALIDA = "../Resultados/Resultados_PPO_Caso_A.txt"
CABECERA = "CASO A - PPO DE VALIDACION DE LA SOLUCION BASE"


def main():
    resultado = resolver_instancia_ppo(
        nombre_modelo="PPO_Caso_A_Validacion_Solucion_Base",
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
