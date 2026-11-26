"""Apartado 1: carga y exploración del conjunto de datos de sensores."""

from pathlib import Path
from typing import NamedTuple

import numpy as np

COLUMNAS_ESPERADAS = ("id", "temperatura", "vibracion", "consumo", "presion", "estado")
VARIABLES = COLUMNAS_ESPERADAS[1:5]
NOMBRES_LEGIBLES = ("Temperatura", "Vibración", "Consumo", "Presión")  # para gráficos e informes
UNIDADES = ("°C", "mm/s", "kW", "bar")
ESTADOS = {0: "Normal", 1: "Desgaste mecánico", 2: "Sobrecalentamiento"}


class ConjuntoDatos(NamedTuple):
    """Datos separados por papel: identificadores, mediciones y diagnóstico."""

    ids: np.ndarray        # (n,) str   -> no es una medida, no entra en cálculos
    mediciones: np.ndarray  # (n, 4) float -> np.nan marca un valor ausente
    estados: np.ndarray    # (n,) int   -> variable objetivo
    variables: tuple       # nombres de las columnas de `mediciones`


def _leer_cabecera(ruta: Path) -> tuple:
    """Devuelve la cabecera y si existe al menos una fila de datos tras ella."""
    with ruta.open(encoding="utf-8") as fichero:
        cabecera = fichero.readline().strip().split(",")
        hay_registros = any(linea.strip() for linea in fichero)
    return cabecera, hay_registros


def cargar_datos(ruta) -> ConjuntoDatos:  # [enunciado] A1: cargar el CSV con NumPy y comprobar que se ha cargado bien
    """Carga el CSV y valida su estructura antes de devolver los arrays.

    Lanza FileNotFoundError si el fichero no existe y ValueError si su
    contenido no tiene la forma esperada.
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encuentra el fichero de datos: {ruta}")

    cabecera, hay_registros = _leer_cabecera(ruta)
    if tuple(cabecera) != COLUMNAS_ESPERADAS:
        raise ValueError(f"Columnas inesperadas: {cabecera}. Se esperaban: {list(COLUMNAS_ESPERADAS)}")
    if not hay_registros:
        raise ValueError("El fichero no contiene registros.")

    # genfromtxt convierte las celdas vacías en np.nan cuando el tipo es float,
    # así los ausentes quedan marcados sin tener que recorrer fila a fila.
    opciones = dict(delimiter=",", skip_header=1, encoding="utf-8")
    ids = np.genfromtxt(ruta, usecols=0, dtype=str, ndmin=1, **opciones)
    mediciones = np.genfromtxt(ruta, usecols=range(1, 5), dtype=float, ndmin=2, **opciones)
    estados_crudos = np.genfromtxt(ruta, usecols=5, dtype=float, ndmin=1, **opciones)

    # La variable objetivo no admite ausentes ni valores fuera de {0, 1, 2}:
    # sin etiqueta fiable no se puede entrenar ni evaluar.
    estados_validos = np.isin(estados_crudos, list(ESTADOS))
    if not estados_validos.all():
        filas = np.flatnonzero(~estados_validos) + 2  # +2: cabecera y base 1
        raise ValueError(f"Estado ausente o desconocido en las líneas {filas.tolist()}")

    return ConjuntoDatos(ids, mediciones, estados_crudos.astype(int), VARIABLES)


def resumen_exploratorio(datos: ConjuntoDatos) -> dict:  # [enunciado] A1: exploración de los datos
    """Calcula la información del apartado 1 sin imprimir nada."""
    ausentes = np.isnan(datos.mediciones)
    clases, recuento = np.unique(datos.estados, return_counts=True)
    return {
        "dimensiones": (datos.mediciones.shape[0], len(COLUMNAS_ESPERADAS)),
        "variables": datos.variables,
        "tipos": {"id": datos.ids.dtype, "mediciones": datos.mediciones.dtype,
                  "estado": datos.estados.dtype},
        "ausentes_por_variable": dict(zip(datos.variables, ausentes.sum(axis=0).tolist())),
        "registros_con_ausentes": int(ausentes.any(axis=1).sum()),
        "recuento_por_estado": dict(zip(clases.tolist(), recuento.tolist())),
    }


def mostrar_muestra(datos: ConjuntoDatos, n: int = 5) -> None:  # [enunciado] A1: mostrar una muestra de los registros
    print(f"{'id':<7}" + "".join(f"{v:>13}" for v in datos.variables) + f"{'estado':>9}")
    for i in range(min(n, len(datos.ids))):
        valores = "".join(f"{x:>13.3f}" for x in datos.mediciones[i])
        print(f"{datos.ids[i]:<7}{valores}{datos.estados[i]:>9}")


def mostrar_resumen(resumen: dict) -> None:
    filas, columnas = resumen["dimensiones"]
    print(f"Dimensiones: {filas} registros x {columnas} columnas")
    print(f"Variables predictoras: {', '.join(resumen['variables'])}")
    print("Tipos:", ", ".join(f"{k}={v}" for k, v in resumen["tipos"].items()))

    print("\nValores ausentes por variable:")
    for variable, total in resumen["ausentes_por_variable"].items():
        print(f"  {variable:<12} {total:>4} ({total / filas:.1%})")
    total = resumen["registros_con_ausentes"]
    print(f"  Registros con al menos un ausente: {total} ({total / filas:.1%})")

    print("\nRegistros por estado:")
    for estado, total in resumen["recuento_por_estado"].items():
        print(f"  {estado} - {ESTADOS[estado]:<20} {total:>4} ({total / filas:.1%})")
