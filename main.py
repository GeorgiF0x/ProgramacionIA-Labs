"""Sistema inteligente de monitorización y diagnóstico industrial."""

import sys
from pathlib import Path

import matplotlib

# main.py solo guarda los gráficos en disco: backend sin ventanas. Se fija aquí y no en
# src/graficos.py para que el cuaderno pueda seguir mostrando gráficos en línea.
matplotlib.use("Agg")

from src import analisis, carga, graficos, limpieza, preparacion  # noqa: E402

RAIZ = Path(__file__).parent
RUTA_DATOS = RAIZ / "datos" / "sensores.csv"
RUTA_GRAFICOS = RAIZ / "resultados" / "graficos"


def titulo(texto: str) -> None:
    print(f"\n{'=' * 70}\n{texto}\n{'=' * 70}")


def main() -> int:
    titulo("APARTADO 1. Carga y exploración de los datos")
    try:
        datos = carga.cargar_datos(RUTA_DATOS)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error al cargar los datos: {error}", file=sys.stderr)
        return 1

    carga.mostrar_resumen(carga.resumen_exploratorio(datos))
    print("\nMuestra de registros:")
    carga.mostrar_muestra(datos)

    titulo("APARTADO 2. Limpieza y preparación de los datos")
    resultado_limpieza = limpieza.limpiar(datos)
    limpieza.mostrar_resumen_limpieza(datos, resultado_limpieza)

    titulo("APARTADO 3. Análisis estadístico")
    analizar(resultado_limpieza.datos)

    titulo("APARTADO 4. Transformación y normalización")
    preparar(resultado_limpieza.datos)
    return 0


def analizar(datos: carga.ConjuntoDatos) -> None:
    X, y, variables = datos.mediciones, datos.estados, datos.variables
    print("Estadísticos globales (valores medidos, sin imputar):")
    analisis.mostrar_estadisticos(analisis.calcular_estadisticos(X), variables)

    print("\nComparativa por estado:")
    analisis.mostrar_comparativa_por_clase(*analisis.estadisticos_por_clase(X, y), variables)

    print("\nCapacidad de cada variable para distinguir los estados:")
    parejas, d = analisis.d_cohen_por_pareja(X, y)
    analisis.mostrar_separabilidad(analisis.ratio_f(X, y), parejas, d, variables)

    rutas = [
        graficos.boxplots_por_clase(X, y, carga.NOMBRES_LEGIBLES, carga.UNIDADES, RUTA_GRAFICOS),
        graficos.dispersion(X, y, carga.NOMBRES_LEGIBLES, carga.UNIDADES, RUTA_GRAFICOS),
        graficos.histogramas_por_clase(X, y, carga.NOMBRES_LEGIBLES, carga.UNIDADES, RUTA_GRAFICOS),
        graficos.mapa_calor_cohen(d, parejas, carga.NOMBRES_LEGIBLES, RUTA_GRAFICOS),
    ]
    print("\nGráficos guardados:")
    for ruta in rutas:
        print(f"  {ruta.relative_to(RAIZ)}")


def preparar(datos: carga.ConjuntoDatos) -> tuple:
    particion = preparacion.dividir_estratificado(datos)
    transformacion = preparacion.ajustar_transformacion(particion.X_entrenamiento)
    X_entrenamiento = preparacion.transformar(particion.X_entrenamiento, transformacion)
    X_prueba = preparacion.transformar(particion.X_prueba, transformacion)
    preparacion.mostrar_resumen_preparacion(particion, transformacion, X_entrenamiento, X_prueba,
                                            datos.variables)
    return particion, X_entrenamiento, X_prueba


if __name__ == "__main__":
    sys.exit(main())
