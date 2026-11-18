"""Apartado 4: transformación y normalización.

Orden de las operaciones (todas las estadísticas salen SOLO del entrenamiento):
1. División estratificada 80/20.
2. Imputación de huecos con la mediana del entrenamiento.
3. Normalización z-score con la media y la desviación del entrenamiento.

El conjunto de prueba hace el papel de datos futuros: se le aplica la misma
transformación, pero nunca participa en calcularla (sin fuga de datos).
"""

from typing import NamedTuple

import numpy as np

from src.analisis import DDOF
from src.carga import ConjuntoDatos

PROPORCION_ENTRENAMIENTO = 0.8
SEMILLA = 42  # semilla fija: el mismo reparto en cada ejecución, resultados reproducibles


class Particion(NamedTuple):
    ids_entrenamiento: np.ndarray
    X_entrenamiento: np.ndarray
    y_entrenamiento: np.ndarray
    ids_prueba: np.ndarray
    X_prueba: np.ndarray
    y_prueba: np.ndarray


class Transformacion(NamedTuple):
    """Parámetros aprendidos del entrenamiento. Son los que se aplicarían a una medición nueva."""

    medianas: np.ndarray     # (4,) para rellenar huecos
    media: np.ndarray        # (4,) para centrar
    desviacion: np.ndarray   # (4,) para escalar


def dividir_estratificado(datos: ConjuntoDatos, proporcion: float = PROPORCION_ENTRENAMIENTO,
                          semilla: int = SEMILLA) -> Particion:
    """Reparte cada clase por separado para que ambas partes mantengan la proporción de clases."""
    generador = np.random.default_rng(semilla)
    entrenamiento, prueba = [], []
    for estado in np.unique(datos.estados):  # 3 iteraciones, una por clase
        indices = generador.permutation(np.flatnonzero(datos.estados == estado))
        corte = int(round(proporcion * indices.size))
        entrenamiento.append(indices[:corte])
        prueba.append(indices[corte:])

    # Se baraja también el orden final para que las clases no queden en bloques.
    i_ent = generador.permutation(np.concatenate(entrenamiento))
    i_pru = generador.permutation(np.concatenate(prueba))
    X, y, ids = datos.mediciones, datos.estados, datos.ids
    return Particion(ids[i_ent], X[i_ent], y[i_ent], ids[i_pru], X[i_pru], y[i_pru])


def calcular_medianas(mediciones_entrenamiento: np.ndarray) -> np.ndarray:
    """Mediana por variable. Se usa la mediana y no la media porque los atípicos no la desplazan."""
    return np.nanmedian(mediciones_entrenamiento, axis=0)


def imputar(mediciones: np.ndarray, medianas: np.ndarray) -> np.ndarray:
    """Sustituye cada np.nan por la mediana de su columna (broadcasting (n, 4) con (4,))."""
    return np.where(np.isnan(mediciones), medianas, mediciones)


def calcular_parametros_normalizacion(mediciones_entrenamiento: np.ndarray) -> tuple:
    media = mediciones_entrenamiento.mean(axis=0)
    desviacion = mediciones_entrenamiento.std(axis=0, ddof=DDOF)
    # Una variable constante tendría desviación 0 y dividir daría inf: se deja sin escalar.
    return media, np.where(desviacion == 0, 1.0, desviacion)


def normalizar(mediciones: np.ndarray, media: np.ndarray, desviacion: np.ndarray) -> np.ndarray:
    """z = (x - media) / desviación, vectorizado sobre todas las filas a la vez."""
    return (mediciones - media) / desviacion


def ajustar_transformacion(X_entrenamiento: np.ndarray) -> Transformacion:
    """Aprende los parámetros SOLO del entrenamiento.

    La media y la desviación se calculan después de imputar, porque la normalización
    se aplica a los datos ya imputados.
    """
    medianas = calcular_medianas(X_entrenamiento)
    media, desviacion = calcular_parametros_normalizacion(imputar(X_entrenamiento, medianas))
    return Transformacion(medianas, media, desviacion)


def transformar(mediciones: np.ndarray, transformacion: Transformacion) -> np.ndarray:
    """Aplica exactamente la misma transformación a cualquier conjunto (entrenamiento, prueba o nuevo)."""
    imputadas = imputar(mediciones, transformacion.medianas)
    return normalizar(imputadas, transformacion.media, transformacion.desviacion)


def mostrar_resumen_preparacion(particion: Particion, transformacion: Transformacion,
                                X_ent_norm: np.ndarray, X_pru_norm: np.ndarray, variables: tuple) -> None:
    n_ent, n_pru = len(particion.y_entrenamiento), len(particion.y_prueba)
    total = n_ent + n_pru
    print(f"Variables predictoras (X): {', '.join(variables)}  |  variable objetivo (y): estado")
    print(f"Entrenamiento: {n_ent} registros ({n_ent / total:.1%})   Prueba: {n_pru} registros ({n_pru / total:.1%})")

    print("\nDistribución de clases (estratificación):")
    for nombre, y in (("entrenamiento", particion.y_entrenamiento), ("prueba", particion.y_prueba)):
        estados, recuento = np.unique(y, return_counts=True)
        detalle = ", ".join(f"{e}={r} ({r / len(y):.1%})" for e, r in zip(estados.tolist(), recuento.tolist()))
        print(f"  {nombre:<14} {detalle}")

    solapados = np.intersect1d(particion.ids_entrenamiento, particion.ids_prueba).size
    print(f"  Registros presentes en ambas partes: {solapados}")

    print("\nHuecos imputados con la mediana del entrenamiento:")
    print(f"  entrenamiento: {int(np.isnan(particion.X_entrenamiento).sum())}   "
          f"prueba: {int(np.isnan(particion.X_prueba).sum())}")

    print("\nParámetros aprendidos del entrenamiento:")
    print(f"  {'':<12}" + "".join(f"{v:>13}" for v in variables))
    for nombre, valores in zip(("mediana", "media", "desviacion"), transformacion):
        print(f"  {nombre:<12}" + "".join(f"{x:>13.3f}" for x in valores))

    print("\nComprobación tras normalizar (media y desviación por variable):")
    for nombre, X in (("entrenamiento", X_ent_norm), ("prueba", X_pru_norm)):
        print(f"  {nombre:<14} media={np.round(X.mean(axis=0), 3)}  desviación={np.round(X.std(axis=0, ddof=DDOF), 3)}")
    print("  (el entrenamiento queda exactamente en 0 y 1; la prueba, cerca pero no exacta: es lo esperado)")
