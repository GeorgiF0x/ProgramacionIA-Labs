"""Apartado 5: clasificador de centroide más cercano, implementado desde cero con NumPy.

Entrenar = calcular el punto medio (centroide) de cada clase.
Predecir = asignar cada observación a la clase del centroide más cercano (distancia euclídea).
"""

from pathlib import Path
from typing import NamedTuple

import numpy as np

from src.carga import ESTADOS


class ModeloCentroides(NamedTuple):
    clases: np.ndarray      # (k,) etiquetas, en el mismo orden que las filas de `centroides`
    centroides: np.ndarray  # (k, n_variables) un punto medio por clase


def entrenar(X: np.ndarray, y: np.ndarray) -> ModeloCentroides:
    """Centroide de cada clase = media de sus observaciones de entrenamiento.

    Se calcula sin bucles con una matriz de pertenencia (one-hot):
    pertenencia[i, c] = 1 si la observación i es de la clase c.
    pertenencia.T @ X suma las observaciones de cada clase, y al dividir
    entre el número de observaciones de cada clase se obtiene la media.
    """
    clases = np.unique(y)
    pertenencia = (y[:, np.newaxis] == clases[np.newaxis, :]).astype(float)  # (n, k)
    sumas = pertenencia.T @ X                                                # (k, n_variables)
    tamanos = pertenencia.sum(axis=0)[:, np.newaxis]                         # (k, 1)
    return ModeloCentroides(clases, sumas / tamanos)


def calcular_distancias(X: np.ndarray, centroides: np.ndarray) -> np.ndarray:
    """Distancia euclídea de cada observación a cada centroide: matriz (n, k).

    Broadcasting en 3D: (n, 1, v) - (1, k, v) -> (n, k, v) contiene todas las
    diferencias a la vez; se elevan al cuadrado, se suman por variable y se
    saca la raíz.
    """
    diferencias = X[:, np.newaxis, :] - centroides[np.newaxis, :, :]
    return np.sqrt((diferencias ** 2).sum(axis=2))


def predecir(modelo: ModeloCentroides, X: np.ndarray) -> tuple:
    """Devuelve (predicciones (n,), distancias (n, k)).

    argmin da la POSICIÓN del centroide más cercano; modelo.clases la traduce
    a su etiqueta. En caso de empate exacto gana la primera clase.
    """
    distancias = calcular_distancias(X, modelo.centroides)
    return modelo.clases[np.argmin(distancias, axis=1)], distancias


def guardar_predicciones(ruta: Path, ids, y_real, y_predicho, distancias, clases) -> Path:
    """Almacena las predicciones en CSV: id, estado real, estado predicho y distancia a cada centroide."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cabecera = ["id", "estado_real", "estado_predicho"] + [f"distancia_estado_{c}" for c in clases]
    filas = np.column_stack([ids, y_real, y_predicho, np.char.mod("%.4f", distancias)])
    np.savetxt(ruta, filas, fmt="%s", delimiter=",", header=",".join(cabecera), comments="")
    return ruta


def mostrar_modelo(modelo: ModeloCentroides, variables: tuple, media: np.ndarray, desviacion: np.ndarray) -> None:
    print("Centroides en unidades normalizadas (z):")
    print(f"  {'':<20}" + "".join(f"{v:>13}" for v in variables))
    for clase, centroide in zip(modelo.clases, modelo.centroides):
        print(f"  {ESTADOS[clase]:<20}" + "".join(f"{x:>13.3f}" for x in centroide))

    # Deshacer el z-score (x = z * desviación + media) para leerlos en unidades reales.
    print("\nCentroides en unidades originales:")
    print(f"  {'':<20}" + "".join(f"{v:>13}" for v in variables))
    for clase, centroide in zip(modelo.clases, modelo.centroides * desviacion + media):
        print(f"  {ESTADOS[clase]:<20}" + "".join(f"{x:>13.2f}" for x in centroide))


def mostrar_predicciones(ids, y_real, y_predicho, distancias, clases, n: int = 8) -> None:
    estados, recuento = np.unique(y_predicho, return_counts=True)
    print(f"Predicciones generadas: {len(y_predicho)}  ->  "
          + ", ".join(f"{ESTADOS[e]}={r}" for e, r in zip(estados.tolist(), recuento.tolist())))
    print(f"\nPrimeras {n} predicciones (distancia a cada centroide; gana la menor):")
    print(f"  {'id':<7}" + "".join(f"{'d_' + str(c):>8}" for c in clases) + f"{'predicho':>22}{'real':>22}")
    for i in range(min(n, len(ids))):
        marca = "" if y_real[i] == y_predicho[i] else "   <- fallo"
        print(f"  {ids[i]:<7}" + "".join(f"{x:>8.3f}" for x in distancias[i])
              + f"{ESTADOS[y_predicho[i]]:>22}{ESTADOS[y_real[i]]:>22}{marca}")
