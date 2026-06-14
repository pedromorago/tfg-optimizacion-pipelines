from typing import Dict, List, Any
from pathlib import Path


def spec_pertenece_a_contenedor(spec: str, prefijos: List[str]) -> bool:
    """
    Comprueba si una spec pertenece a un contenedor según una lista de prefijos.
    """
    return any(spec.startswith(prefijo) for prefijo in prefijos)


def calcular_metricas_empiricas(
    datos_pipeline_real: Dict[str, float],
    asignacion_contenedores: Dict[str, List[str]],
    tiempos_totales_observados: Dict[str, float],
    coste_unitario: float = 0.04,
) -> Dict[str, Any]:
    """
    Calcula la carga neta por contenedor, el setup deducido, el makespan,
    el coste total observado y el setup medio deducido.

    Parámetros
    ----------
    datos_pipeline_real : dict
        Diccionario {spec: tiempo_neto_en_minutos}.
    asignacion_contenedores : dict
        Diccionario {nombre_contenedor: [prefijos_asociados]}.
    tiempos_totales_observados : dict
        Diccionario {nombre_contenedor: tiempo_total_observado_en_minutos}.
    coste_unitario : float
        Coste por minuto de build.

    Devuelve
    --------
    dict
        Métricas calculadas.
    """
    filas = []

    for nombre_contenedor, prefijos in asignacion_contenedores.items():
        carga_neta = sum(
            tiempo
            for spec, tiempo in datos_pipeline_real.items()
            if spec_pertenece_a_contenedor(spec, prefijos)
        )

        tiempo_total_observado = tiempos_totales_observados[nombre_contenedor]
        setup_deducido = tiempo_total_observado - carga_neta

        filas.append(
            {
                "nombre": nombre_contenedor,
                "carga_neta": round(carga_neta, 2),
                "tiempo_total_observado": round(tiempo_total_observado, 2),
                "setup_deducido": round(setup_deducido, 2),
            }
        )

    makespan_observado = round(
        max(fila["tiempo_total_observado"] for fila in filas), 2
    )
    coste_total_observado = round(
        sum(fila["tiempo_total_observado"] for fila in filas) * coste_unitario, 2
    )
    setup_medio_deducido = round(
        sum(fila["setup_deducido"] for fila in filas) / len(filas), 2
    )

    return {
        "filas": filas,
        "makespan_observado": makespan_observado,
        "coste_total_observado": coste_total_observado,
        "setup_medio_deducido": setup_medio_deducido,
    }


def imprimir_metricas(titulo: str, metricas: Dict[str, Any]) -> None:
    """
    Imprime por consola las métricas calculadas.
    """
    print("\n" + "=" * 90)
    print(titulo)
    print("=" * 90)

    for fila in metricas["filas"]:
        print(
            f'{fila["nombre"]}: '
            f'carga neta = {fila["carga_neta"]:.2f} min | '
            f'tiempo total observado = {fila["tiempo_total_observado"]:.2f} min | '
            f'setup deducido = {fila["setup_deducido"]:.2f} min'
        )

    print("-" * 90)
    print(f'MAKESPAN OBSERVADO: {metricas["makespan_observado"]:.2f} min')
    print(f'COSTE TOTAL OBSERVADO: {metricas["coste_total_observado"]:.2f} USD')
    print(f'SETUP MEDIO DEDUCIDO: {metricas["setup_medio_deducido"]:.2f} min')


def guardar_metricas_txt(titulo: str, metricas: Dict[str, Any], ruta_salida: str) -> None:
    """
    Guarda en un archivo .txt las métricas calculadas.
    """
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with ruta.open("w", encoding="utf-8", newline="\n") as f:
        f.write("=" * 90 + "\n")
        f.write(f"{titulo}\n")
        f.write("=" * 90 + "\n")

        for fila in metricas["filas"]:
            f.write(
                f'{fila["nombre"]}: '
                f'carga neta = {fila["carga_neta"]:.2f} min | '
                f'tiempo total observado = {fila["tiempo_total_observado"]:.2f} min | '
                f'setup deducido = {fila["setup_deducido"]:.2f} min\n'
            )

        f.write("-" * 90 + "\n")
        f.write(f'MAKESPAN OBSERVADO: {metricas["makespan_observado"]:.2f} min\n')
        f.write(f'COSTE TOTAL OBSERVADO: {metricas["coste_total_observado"]:.2f} USD\n')
        f.write(f'SETUP MEDIO DEDUCIDO: {metricas["setup_medio_deducido"]:.2f} min\n')
