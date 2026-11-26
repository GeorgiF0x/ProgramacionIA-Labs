"""Apartado 2: limpieza y preparación de los datos.

Criterio general:
- Valor fuera del rango físico del sensor -> error de medición -> se marca como ausente.
- Valor atípico dentro del rango -> posible anomalía real -> se conserva y se informa.
- Valores ausentes -> se dejan como np.nan; se imputan en src/preparacion.py (apartado 4)
  con la mediana del ENTRENAMIENTO, para que el conjunto de prueba no influya.
"""

from typing import NamedTuple

import numpy as np

from src.carga import ConjuntoDatos

# Una fila por variable (temperatura, vibracion, consumo, presion): [mínimo, máximo].
RANGOS_ADMISIBLES = np.array([[0.0, 150.0], [0.0, 15.0], [0.0, 65.0], [0.0, 12.0]])

# Con 2 o más huecos de 4, la fila sería mitad inventada: se descarta en lugar de imputarla.
MAX_VALORES_IMPUTABLES = 1

FACTOR_IQR = 1.5


class ResultadoLimpieza(NamedTuple):
    """Datos conservados y máscaras (n, 4) que explican cada decisión sobre los originales."""

    datos: ConjuntoDatos            # registros conservados; np.nan = valor que se imputará
    ausentes: np.ndarray            # (n, 4) bool: vacío en el CSV
    fuera_de_rango: np.ndarray      # (n, 4) bool: error de medición
    atipicos_globales: np.ndarray   # (n, 4) bool: IQR sobre todo el conjunto
    atipicos_por_clase: np.ndarray  # (n, 4) bool: IQR dentro de cada estado
    descartados: np.ndarray         # (n,) bool: fila eliminada


def detectar_fuera_de_rango(mediciones: np.ndarray, rangos: np.ndarray = RANGOS_ADMISIBLES) -> np.ndarray:  # [enunciado] A2
    # Broadcasting: (n, 4) se compara con (4,), cada columna con su propio límite.
    # Cualquier comparación con np.nan es False, así que un ausente no cuenta como error.
    return (mediciones < rangos[:, 0]) | (mediciones > rangos[:, 1])


def limites_iqr(mediciones: np.ndarray, factor: float = FACTOR_IQR) -> tuple:
    """Límites de Tukey por columna: [Q1 - factor·IQR, Q3 + factor·IQR], ignorando np.nan."""
    q1, q3 = np.nanpercentile(mediciones, [25, 75], axis=0)
    iqr = q3 - q1
    return q1 - factor * iqr, q3 + factor * iqr


def detectar_atipicos(mediciones: np.ndarray) -> np.ndarray:  # [enunciado] A2: identificar atípicos (Tukey)
    inferior, superior = limites_iqr(mediciones)
    return (mediciones < inferior) | (mediciones > superior)


def detectar_atipicos_por_clase(mediciones: np.ndarray, estados: np.ndarray) -> np.ndarray:
    """IQR calculado dentro de cada estado.

    Un sobrecalentamiento tiene temperaturas altas por definición: compararlo con
    las máquinas normales lo marcaría como atípico justo por ser lo que es.
    """
    atipicos = np.zeros(mediciones.shape, dtype=bool)
    for estado in np.unique(estados):  # 3 iteraciones (clases), no una por registro
        filas = estados == estado
        atipicos[filas] = detectar_atipicos(mediciones[filas])
    return atipicos


def limpiar(datos: ConjuntoDatos) -> ResultadoLimpieza:  # [enunciado] A2: separar válidos, corregidos y descartados
    mediciones = datos.mediciones
    ausentes = np.isnan(mediciones)
    fuera_de_rango = detectar_fuera_de_rango(mediciones)

    # Los errores pasan a ser ausentes: se conserva el resto de sensores de la fila.
    # np.where crea un array nuevo; los datos originales no se modifican.
    corregidas = np.where(fuera_de_rango, np.nan, mediciones)

    # Los atípicos se buscan SIN los errores: un 245 °C desplazaría los cuartiles.
    atipicos_globales = detectar_atipicos(corregidas)
    atipicos_por_clase = detectar_atipicos_por_clase(corregidas, datos.estados)

    descartados = np.isnan(corregidas).sum(axis=1) > MAX_VALORES_IMPUTABLES
    conservados = ~descartados
    datos_limpios = ConjuntoDatos(
        datos.ids[conservados], corregidas[conservados], datos.estados[conservados], datos.variables
    )
    return ResultadoLimpieza(
        datos_limpios, ausentes, fuera_de_rango, atipicos_globales, atipicos_por_clase, descartados
    )


def mostrar_resumen_limpieza(original: ConjuntoDatos, resultado: ResultadoLimpieza) -> None:
    variables = original.variables
    n = len(original.ids)

    print(f"Valores ausentes en el CSV: {resultado.ausentes.sum()} celdas "
          f"en {resultado.ausentes.any(axis=1).sum()} registros")

    filas, columnas = np.nonzero(resultado.fuera_de_rango)
    print(f"\nErrores de medición (fuera de rango físico): {filas.size} -> se marcan como ausentes")
    for fila, columna in zip(filas, columnas):
        minimo, maximo = RANGOS_ADMISIBLES[columna]
        print(f"  {original.ids[fila]}  {variables[columna]:<12} {original.mediciones[fila, columna]:>8.2f}"
              f"   admisible [{minimo:g}, {maximo:g}]")

    a_imputar = np.isnan(resultado.datos.mediciones).any(axis=1).sum()
    descartados = np.flatnonzero(resultado.descartados)
    print("\nDecisión por registro:")
    print(f"  Válidos sin cambios:             {n - a_imputar - descartados.size:>4}")
    print(f"  A corregir (1 valor a imputar):  {a_imputar:>4}")
    print(f"  Descartados (2+ valores):        {descartados.size:>4}  {original.ids[descartados].tolist()}")
    print(f"  Conservados:                     {len(resultado.datos.ids):>4}")

    print("\nAtípicos estadísticos (IQR x1.5) dentro del rango físico -> se CONSERVAN:")
    print(f"  {'variable':<12}{'global':>8}{'por clase':>11}")
    for j, variable in enumerate(variables):
        print(f"  {variable:<12}{resultado.atipicos_globales[:, j].sum():>8}"
              f"{resultado.atipicos_por_clase[:, j].sum():>11}")
    for nombre, mascara in (("global", resultado.atipicos_globales),
                            ("por clase", resultado.atipicos_por_clase)):
        por_estado = [int(mascara[original.estados == e].any(axis=1).sum()) for e in (0, 1, 2)]
        print(f"  Registros con algún atípico ({nombre}) por estado 0/1/2: {por_estado}")

    estados, recuento = np.unique(resultado.datos.estados, return_counts=True)
    print("\nRegistros por estado tras la limpieza:",
          ", ".join(f"{e}={r}" for e, r in zip(estados.tolist(), recuento.tolist())))
