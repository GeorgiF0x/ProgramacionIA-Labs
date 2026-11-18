"""Apartado 3: análisis estadístico de las variables numéricas.

Todas las funciones ignoran np.nan: se describen solo los valores realmente medidos
(los huecos se imputan más adelante, en el apartado 4).
"""

from itertools import combinations

import numpy as np

from src.carga import ESTADOS

ESTADISTICOS = ("media", "mediana", "desviacion", "minimo", "maximo", "q1", "q3", "iqr")

# Desviación muestral (divide entre n - 1): los registros son una muestra del
# comportamiento de las máquinas, no todas sus mediciones posibles.
DDOF = 1

# Umbral habitual de Cohen para considerar grande la separación entre dos grupos.
EFECTO_GRANDE = 0.8


def calcular_estadisticos(mediciones: np.ndarray) -> np.ndarray:
    """Matriz (8, n_variables): una fila por estadístico, en el orden de ESTADISTICOS."""
    q1, mediana, q3 = np.nanpercentile(mediciones, [25, 50, 75], axis=0)
    return np.vstack([
        np.nanmean(mediciones, axis=0),
        mediana,
        np.nanstd(mediciones, axis=0, ddof=DDOF),
        np.nanmin(mediciones, axis=0),
        np.nanmax(mediciones, axis=0),
        q1,
        q3,
        q3 - q1,
    ])


def estadisticos_por_clase(mediciones: np.ndarray, estados: np.ndarray) -> tuple:
    """Devuelve (clases, array (n_clases, 8, n_variables))."""
    clases = np.unique(estados)
    return clases, np.stack([calcular_estadisticos(mediciones[estados == c]) for c in clases])


def _momentos_por_clase(mediciones: np.ndarray, estados: np.ndarray) -> tuple:
    """Tamaño, media y varianza muestral de cada clase: arrays (n_clases, n_variables)."""
    clases = np.unique(estados)
    grupos = [mediciones[estados == c] for c in clases]
    n = np.array([(~np.isnan(g)).sum(axis=0) for g in grupos])
    medias = np.array([np.nanmean(g, axis=0) for g in grupos])
    varianzas = np.array([np.nanvar(g, axis=0, ddof=DDOF) for g in grupos])
    return clases, n, medias, varianzas


def ratio_f(mediciones: np.ndarray, estados: np.ndarray) -> np.ndarray:
    """Estadístico F (ANOVA de un factor) por variable.

    F = varianza ENTRE clases / varianza DENTRO de las clases.
    Cuanto mayor, más se alejan los centros de las clases en relación con su dispersión.
    """
    clases, n, medias, varianzas = _momentos_por_clase(mediciones, estados)
    k = len(clases)
    media_global = np.nanmean(mediciones, axis=0)
    entre = (n * (medias - media_global) ** 2).sum(axis=0) / (k - 1)
    dentro = ((n - 1) * varianzas).sum(axis=0) / (n.sum(axis=0) - k)
    return entre / dentro


def d_cohen_por_pareja(mediciones: np.ndarray, estados: np.ndarray) -> tuple:
    """d de Cohen de cada pareja de clases: |media_a - media_b| / desviación conjunta.

    Devuelve (lista de parejas, array (n_parejas, n_variables)).
    """
    clases, n, medias, varianzas = _momentos_por_clase(mediciones, estados)
    # Indexación avanzada: a y b son vectores de índices, se calculan todas las parejas a la vez.
    a, b = np.array(list(combinations(range(len(clases)), 2))).T
    varianza_conjunta = ((n[a] - 1) * varianzas[a] + (n[b] - 1) * varianzas[b]) / (n[a] + n[b] - 2)
    d = np.abs(medias[a] - medias[b]) / np.sqrt(varianza_conjunta)
    parejas = [(int(clases[i]), int(clases[j])) for i, j in zip(a, b)]
    return parejas, d


def _fila(nombre: str, valores, ancho: int = 12) -> str:
    return f"  {nombre:<12}" + "".join(f"{v:>{ancho}.2f}" for v in valores)


def mostrar_estadisticos(tabla: np.ndarray, variables: tuple) -> None:
    print(f"  {'':<12}" + "".join(f"{v:>12}" for v in variables))
    for nombre, fila in zip(ESTADISTICOS, tabla):
        print(_fila(nombre, fila))


def mostrar_comparativa_por_clase(clases: np.ndarray, tablas: np.ndarray, variables: tuple) -> None:
    """Una tabla por variable con las clases en columnas, para compararlas lado a lado."""
    for j, variable in enumerate(variables):
        print(f"\n  {variable.upper()}")
        print(f"  {'':<12}" + "".join(f"{ESTADOS[c]:>20}" for c in clases))
        for i, nombre in enumerate(ESTADISTICOS):
            print(_fila(nombre, tablas[:, i, j], ancho=20))


def mostrar_separabilidad(f: np.ndarray, parejas: list, d: np.ndarray, variables: tuple) -> None:
    print("  Estadístico F (ANOVA), de mayor a menor capacidad de separar las 3 clases:")
    for j in np.argsort(f)[::-1]:
        print(f"    {variables[j]:<12} {f[j]:>8.1f}")

    nombres = [f"{a} vs {b}" for a, b in parejas]
    print(f"\n  d de Cohen por pareja de estados (> {EFECTO_GRANDE} = separación grande):")
    print(f"  {'':<12}" + "".join(f"{p:>10}" for p in nombres))
    for j, variable in enumerate(variables):
        print(_fila(variable, d[:, j], ancho=10))

    print("\n  Conclusiones:")
    for fila, (a, b) in enumerate(parejas):
        mejor = np.argmax(d[fila])
        grandes = [variables[j] for j in np.flatnonzero(d[fila] > EFECTO_GRANDE)]
        print(f"    {ESTADOS[a]} vs {ESTADOS[b]}: la separa mejor '{variables[mejor]}' "
              f"(d={d[fila, mejor]:.2f}); variables con separación grande: {grandes or 'ninguna'}")
    debiles = [variables[j] for j in np.flatnonzero((d <= EFECTO_GRANDE).all(axis=0))]
    if debiles:
        print(f"    Sin separación grande en ninguna pareja: {debiles}")
