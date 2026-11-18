"""Apartado 6: evaluación del clasificador.

Todas las métricas se calculan a mano con NumPy, sin bibliotecas de aprendizaje automático.
Convención de la matriz de confusión: filas = estado real, columnas = estado predicho.
"""

import warnings
from typing import NamedTuple

import numpy as np

from src import clasificador, preparacion
from src.carga import ESTADOS


class Metricas(NamedTuple):
    clases: np.ndarray     # (k,) etiquetas en el orden de filas y columnas
    matriz: np.ndarray     # (k, k) matriz de confusión
    accuracy: float
    precision: np.ndarray  # (k,) por clase
    recall: np.ndarray     # (k,) por clase
    f1: np.ndarray         # (k,) por clase


def matriz_confusion(y_real: np.ndarray, y_predicho: np.ndarray, clases: np.ndarray) -> np.ndarray:
    """Cuenta cada pareja (real, predicho) sin bucles.

    Cada pareja se convierte en un número de celda único: fila * k + columna.
    np.bincount cuenta cuántas veces aparece cada número y reshape lo coloca en la matriz (k, k).
    """
    clases = np.asarray(clases)
    if not (np.isin(y_real, clases).all() and np.isin(y_predicho, clases).all()):
        raise ValueError(f"Hay etiquetas que no están en las clases {clases.tolist()}")
    k = len(clases)
    filas = np.searchsorted(clases, y_real)        # etiqueta -> posición (clases está ordenado)
    columnas = np.searchsorted(clases, y_predicho)
    return np.bincount(filas * k + columnas, minlength=k * k).reshape(k, k)


def _dividir(numerador: np.ndarray, denominador: np.ndarray, metrica: str) -> np.ndarray:
    """División que devuelve 0 donde el denominador es 0 (métrica indefinida) y lo avisa."""
    if (denominador == 0).any():
        warnings.warn(f"{metrica} indefinida en alguna clase (división entre 0): se toma 0.")
    return np.divide(numerador, denominador, out=np.zeros(np.shape(numerador)), where=denominador != 0)


def calcular_metricas(y_real: np.ndarray, y_predicho: np.ndarray, clases=None) -> Metricas:
    clases = np.unique(np.concatenate([y_real, y_predicho])) if clases is None else np.asarray(clases)
    matriz = matriz_confusion(y_real, y_predicho, clases)
    verdaderos_positivos = np.diag(matriz)

    # Precision de c: de lo que se PREDIJO como c, cuánto lo era (columna c).
    precision = _dividir(verdaderos_positivos, matriz.sum(axis=0), "Precision")
    # Recall de c: de lo que REALMENTE era c, cuánto se detectó (fila c).
    recall = _dividir(verdaderos_positivos, matriz.sum(axis=1), "Recall")
    # F1: media armónica; castiga que una de las dos sea baja.
    f1 = _dividir(2 * precision * recall, precision + recall, "F1")
    accuracy = verdaderos_positivos.sum() / matriz.sum()
    return Metricas(clases, matriz, float(accuracy), precision, recall, f1)


def confusiones_por_pareja(matriz: np.ndarray) -> list:
    """Errores entre cada pareja de clases, sumando las dos direcciones, de más a menos."""
    simetrica = matriz + matriz.T
    i, j = np.triu_indices(len(matriz), k=1)
    orden = np.argsort(simetrica[i, j])[::-1]
    return [(int(i[o]), int(j[o]), int(simetrica[i[o], j[o]])) for o in orden]


def validacion_cruzada(X: np.ndarray, y: np.ndarray, n_pliegues: int = 5, columnas=None,
                       semilla: int = preparacion.SEMILLA) -> np.ndarray:
    """Accuracy de cada pliegue con validación cruzada estratificada.

    Se usa SOLO sobre el entrenamiento. En cada pliegue se repite el proceso completo:
    la imputación, la normalización y los centroides se aprenden con los otros pliegues,
    así el pliegue evaluado nunca participa en su propia transformación.
    """
    columnas = slice(None) if columnas is None else list(columnas)
    generador = np.random.default_rng(semilla)
    pliegue = np.empty(len(y), dtype=int)
    for estado in np.unique(y):  # reparto estratificado: cada clase se reparte entre los pliegues
        indices = generador.permutation(np.flatnonzero(y == estado))
        pliegue[indices] = np.arange(indices.size) % n_pliegues

    resultados = np.empty(n_pliegues)
    for k in range(n_pliegues):  # 5 iteraciones, una por pliegue
        entrena, evalua = pliegue != k, pliegue == k
        transformacion = preparacion.ajustar_transformacion(X[entrena])
        X_entrena = preparacion.transformar(X[entrena], transformacion)[:, columnas]
        X_evalua = preparacion.transformar(X[evalua], transformacion)[:, columnas]
        modelo = clasificador.entrenar(X_entrena, y[entrena])
        predicciones, _ = clasificador.predecir(modelo, X_evalua)
        resultados[k] = (predicciones == y[evalua]).mean()
    return resultados


# ---------------------------------------------------------------- presentación

def mostrar_metricas(metricas: Metricas) -> None:
    nombres = [ESTADOS[c] for c in metricas.clases]
    ancho = max(len(n) for n in nombres) + 2
    print("Matriz de confusión (filas = real, columnas = predicho):")
    print(f"  {'':<{ancho}}" + "".join(f"{n:>{ancho}}" for n in nombres))
    for nombre, fila in zip(nombres, metricas.matriz):
        print(f"  {nombre:<{ancho}}" + "".join(f"{x:>{ancho}}" for x in fila))

    total = metricas.matriz.sum()
    print(f"\nAccuracy: {metricas.accuracy:.3f}  ({int(np.trace(metricas.matriz))} aciertos de {total})")
    print(f"\n  {'':<{ancho}}{'precision':>11}{'recall':>9}{'f1':>8}{'soporte':>9}")
    for nombre, p, r, f, s in zip(nombres, metricas.precision, metricas.recall, metricas.f1,
                                  metricas.matriz.sum(axis=1)):
        print(f"  {nombre:<{ancho}}{p:>11.3f}{r:>9.3f}{f:>8.3f}{s:>9}")
    print(f"  {'Media macro':<{ancho}}{metricas.precision.mean():>11.3f}{metricas.recall.mean():>9.3f}"
          f"{metricas.f1.mean():>8.3f}{total:>9}")


def mostrar_validacion_cruzada(resultados: dict, accuracy_prueba: float) -> None:
    print("Validación cruzada estratificada de 5 pliegues (solo sobre el entrenamiento):")
    for nombre, accs in resultados.items():
        print(f"  {nombre:<30} media {accs.mean():.3f} ± {accs.std(ddof=1):.3f}   pliegues {np.round(accs, 3)}")
    referencia = next(iter(resultados.values()))
    print(f"  Accuracy en la prueba: {accuracy_prueba:.3f}  ->  "
          f"{'dentro' if abs(accuracy_prueba - referencia.mean()) <= 2 * referencia.std(ddof=1) else 'fuera'}"
          " del rango habitual de la validación cruzada (media ± 2 desviaciones)")


def responder_preguntas(metricas: Metricas) -> None:
    """Respuestas del enunciado calculadas a partir de las métricas, no escritas a mano."""
    nombre = {c: ESTADOS[c] for c in metricas.clases}
    clases = metricas.clases
    mejor = int(np.argmax(metricas.f1))
    peor = int(np.argmin(metricas.recall))
    fuera_diagonal = metricas.matriz * (1 - np.eye(len(clases), dtype=int))
    real, predicho = np.unravel_index(np.argmax(fuera_diagonal), fuera_diagonal.shape)
    parejas = confusiones_por_pareja(metricas.matriz)

    print(f"1. Mejores resultados: {nombre[clases[mejor]]} (F1 = {metricas.f1[mejor]:.3f}, "
          f"precision {metricas.precision[mejor]:.3f}, recall {metricas.recall[mejor]:.3f}).")
    print(f"2. Confusión más frecuente: {nombre[clases[real]]} predicho como {nombre[clases[predicho]]} "
          f"({fuera_diagonal[real, predicho]} casos). Errores por pareja, en ambas direcciones: "
          + ", ".join(f"{nombre[clases[a]]}–{nombre[clases[b]]} {n}" for a, b, n in parejas) + ".")
    escapadas = int(metricas.matriz[peor].sum() - metricas.matriz[peor, peor])
    print(f"3. Clase con más dificultad: {nombre[clases[peor]]} (recall = {metricas.recall[peor]:.3f}): "
          f"se escapan {escapadas} de {int(metricas.matriz[peor].sum())}.")

    normal = int(np.flatnonzero(clases == 0)[0]) if 0 in clases else None
    if normal is not None:
        averias = metricas.matriz[:, normal].sum() - metricas.matriz[normal, normal]
        reales = metricas.matriz.sum() - metricas.matriz[normal].sum()
        detalle = "; ".join(f"{nombre[c]}: {metricas.matriz[i, normal]} de {metricas.matriz[i].sum()}"
                            for i, c in enumerate(clases) if i != normal)
        print(f"4. Solo como apoyo, no como sistema autónomo. {averias} de {reales} máquinas con avería "
              f"({averias / reales:.0%}) se diagnostican como normales ({detalle}) y nadie las revisaría: "
              "es el error más caro en mantenimiento. Además, el modelo no da un grado de confianza y se ha "
              "evaluado con clases equilibradas, cuando en una fábrica real casi todas las mediciones son normales. "
              "Sirve como alerta temprana que prioriza qué máquinas revisar, con la decisión final en manos de una persona.")
