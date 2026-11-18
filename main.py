"""Sistema inteligente de monitorización y diagnóstico industrial."""

import sys
from pathlib import Path

import matplotlib

# main.py solo guarda los gráficos en disco: backend sin ventanas. Se fija aquí y no en
# src/graficos.py para que el cuaderno pueda seguir mostrando gráficos en línea.
matplotlib.use("Agg")

from src import analisis, carga, clasificador, evaluacion, graficos, limpieza, preparacion  # noqa: E402

RAIZ = Path(__file__).parent
RUTA_DATOS = RAIZ / "datos" / "sensores.csv"
RUTA_GRAFICOS = RAIZ / "resultados" / "graficos"
RUTA_PREDICCIONES = RAIZ / "resultados" / "predicciones.csv"


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
    particion, transformacion, X_entrenamiento, X_prueba = preparar(resultado_limpieza.datos)

    titulo("APARTADO 5. Clasificador de centroide más cercano")
    _, predicciones, _ = clasificar(particion, transformacion, X_entrenamiento, X_prueba,
                                    resultado_limpieza.datos.variables)

    titulo("APARTADO 6. Evaluación del clasificador")
    evaluar(particion, predicciones)
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
    return particion, transformacion, X_entrenamiento, X_prueba


def clasificar(particion, transformacion, X_entrenamiento, X_prueba, variables) -> tuple:
    modelo = clasificador.entrenar(X_entrenamiento, particion.y_entrenamiento)
    clasificador.mostrar_modelo(modelo, variables, transformacion.media, transformacion.desviacion)

    predicciones, distancias = clasificador.predecir(modelo, X_prueba)
    print()
    clasificador.mostrar_predicciones(particion.ids_prueba, particion.y_prueba, predicciones, distancias,
                                      modelo.clases)
    ruta = clasificador.guardar_predicciones(RUTA_PREDICCIONES, particion.ids_prueba, particion.y_prueba,
                                             predicciones, distancias, modelo.clases)
    ruta_grafico = graficos.centroides(particion.X_entrenamiento, particion.y_entrenamiento,
                                       modelo.centroides * transformacion.desviacion + transformacion.media,
                                       modelo.clases, carga.NOMBRES_LEGIBLES, carga.UNIDADES, RUTA_GRAFICOS)
    print(f"\nPredicciones guardadas en {ruta.relative_to(RAIZ)}")
    print(f"Gráfico guardado en {ruta_grafico.relative_to(RAIZ)}")
    return modelo, predicciones, distancias


def evaluar(particion, predicciones) -> evaluacion.Metricas:
    metricas = evaluacion.calcular_metricas(particion.y_prueba, predicciones)
    evaluacion.mostrar_metricas(metricas)

    print()
    cv = {
        "4 variables (modelo final)": evaluacion.validacion_cruzada(particion.X_entrenamiento,
                                                                    particion.y_entrenamiento),
        "sin presión": evaluacion.validacion_cruzada(particion.X_entrenamiento, particion.y_entrenamiento,
                                                     columnas=[0, 1, 2]),
        "solo temperatura y vibración": evaluacion.validacion_cruzada(particion.X_entrenamiento,
                                                                      particion.y_entrenamiento, columnas=[0, 1]),
    }
    evaluacion.mostrar_validacion_cruzada(cv, metricas.accuracy)

    print("\nRespuestas a las preguntas del enunciado:")
    evaluacion.responder_preguntas(metricas)

    ruta = graficos.matriz_confusion(metricas.matriz, metricas.clases, RUTA_GRAFICOS)
    print(f"\nGráfico guardado en {ruta.relative_to(RAIZ)}")
    return metricas


if __name__ == "__main__":
    sys.exit(main())
