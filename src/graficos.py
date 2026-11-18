"""Gráficos de los resultados (Matplotlib), guardados como PNG.

Criterios de diseño:
- Cada estado tiene siempre el mismo color en todos los gráficos.
- Paleta comprobada para daltonismo (azul, naranja, aguamarina).
- El aguamarina tiene poco contraste sobre fondo claro, así que cada clase se nombra
  con texto visible (ejes, leyenda o etiquetas) y nunca depende solo del color.
- Ejes y rejilla en grises discretos para que destaquen los datos.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from src.carga import ESTADOS

COLORES_ESTADO = {0: "#2a78d6", 1: "#eb6834", 2: "#1baf7a"}
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
SUPERFICIE = "#fcfcfb"
ESCALA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

ESTILO = {
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": "#c3c2b7",
    "axes.labelcolor": TINTA_SECUNDARIA,
    "axes.titlecolor": TINTA,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#e1e0d9",
    "grid.linewidth": 0.8,
    "xtick.color": TINTA_SECUNDARIA,
    "ytick.color": TINTA_SECUNDARIA,
    "font.size": 10,
    "legend.frameon": False,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
}


def _guardar(figura, carpeta: Path, nombre: str) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    figura.savefig(ruta)
    plt.close(figura)  # libera memoria: cada figura abierta sigue ocupándola
    return ruta


def _por_clase(columna: np.ndarray, estados: np.ndarray, clases) -> list:
    """Valores no ausentes de una variable, separados por estado."""
    return [columna[(estados == c) & ~np.isnan(columna)] for c in clases]


@plt.rc_context(ESTILO)
def boxplots_por_clase(mediciones, estados, nombres, unidades, carpeta: Path) -> Path:
    clases = np.unique(estados)
    figura, ejes = plt.subplots(2, 2, figsize=(10, 7.5))
    for j, eje in enumerate(ejes.flat):
        # whis=1.5: mismo criterio de Tukey que los atípicos por clase del apartado 2.
        cajas = eje.boxplot(
            _por_clase(mediciones[:, j], estados, clases), whis=1.5, patch_artist=True, widths=0.55,
            medianprops=dict(color=TINTA, linewidth=1.6),
            whiskerprops=dict(color=TINTA_SECUNDARIA), capprops=dict(color=TINTA_SECUNDARIA),
            boxprops=dict(linewidth=0),
        )
        for caja, volantes, c in zip(cajas["boxes"], cajas["fliers"], clases):
            caja.set_facecolor(COLORES_ESTADO[c])
            volantes.set(marker="o", markersize=5, markerfacecolor=COLORES_ESTADO[c],
                         markeredgecolor=SUPERFICIE, markeredgewidth=0.8)
        # Nombres en dos líneas para que no se solapen bajo cada caja.
        eje.set_xticks(range(1, len(clases) + 1), [ESTADOS[c].replace(" ", "\n") for c in clases])
        eje.set_title(f"{nombres[j]} ({unidades[j]})", loc="left")
        eje.grid(axis="x", visible=False)
    figura.suptitle("Distribución de cada variable por estado de la máquina", x=0.01, ha="left",
                    fontsize=13, color=TINTA)
    figura.tight_layout()
    return _guardar(figura, carpeta, "01_boxplots_por_estado.png")


@plt.rc_context(ESTILO)
def dispersion(mediciones, estados, nombres, unidades, carpeta: Path, x: int = 0, y: int = 1) -> Path:
    clases = np.unique(estados)
    validos = ~np.isnan(mediciones[:, [x, y]]).any(axis=1)
    figura, eje = plt.subplots(figsize=(9, 6.5))
    for c in clases:
        filas = validos & (estados == c)
        eje.scatter(mediciones[filas, x], mediciones[filas, y], s=28, color=COLORES_ESTADO[c], alpha=0.8,
                    edgecolors=SUPERFICIE, linewidths=0.6, label=ESTADOS[c])
        # Etiqueta directa en la mediana del grupo: el nombre no depende solo del color.
        mx, my = np.median(mediciones[filas][:, [x, y]], axis=0)
        eje.annotate(ESTADOS[c], (mx, my), ha="center", va="center", fontsize=10, color=TINTA,
                     fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.3", facecolor=SUPERFICIE, edgecolor=COLORES_ESTADO[c]))
    eje.set_xlabel(f"{nombres[x]} ({unidades[x]})")
    eje.set_ylabel(f"{nombres[y]} ({unidades[y]})")
    eje.set_title(f"{nombres[x]} frente a {nombres[y].lower()}: las dos variables que más separan",
                  loc="left", fontsize=12)
    eje.legend(loc="upper left", markerscale=1.2)
    return _guardar(figura, carpeta, "02_dispersion_temperatura_vibracion.png")


@plt.rc_context(ESTILO)
def histogramas_por_clase(mediciones, estados, nombres, unidades, carpeta: Path, bins: int = 30) -> Path:
    clases = np.unique(estados)
    figura, ejes = plt.subplots(2, 2, figsize=(10, 7.5))
    for j, eje in enumerate(ejes.flat):
        columna = mediciones[:, j]
        # Mismos intervalos para las tres clases: si no, las barras no serían comparables.
        bordes = np.histogram_bin_edges(columna[~np.isnan(columna)], bins=bins)
        for valores, c in zip(_por_clase(columna, estados, clases), clases):
            eje.hist(valores, bins=bordes, histtype="step", linewidth=2, color=COLORES_ESTADO[c],
                     label=ESTADOS[c])
        eje.set_title(f"{nombres[j]} ({unidades[j]})", loc="left")
        eje.set_ylabel("Registros")
    manejadores, etiquetas = ejes.flat[0].get_legend_handles_labels()
    figura.legend(manejadores, etiquetas, loc="upper right", ncols=len(clases))
    figura.suptitle("Forma de la distribución por estado", x=0.01, ha="left", fontsize=13, color=TINTA)
    figura.tight_layout(rect=(0, 0, 1, 0.95))
    return _guardar(figura, carpeta, "03_histogramas_por_estado.png")


@plt.rc_context(ESTILO)
def mapa_calor_cohen(d: np.ndarray, parejas: list, nombres, carpeta: Path, umbral: float = 0.8) -> Path:
    mapa = LinearSegmentedColormap.from_list("azul", ESCALA_AZUL)
    figura, eje = plt.subplots(figsize=(7.5, 4.8))
    valores = d.T  # filas = variables, columnas = parejas
    imagen = eje.imshow(valores, cmap=mapa, vmin=0, vmax=np.ceil(d.max()), aspect="auto")
    eje.set_xticks(range(len(parejas)), [f"{ESTADOS[a]}\nvs {ESTADOS[b]}" for a, b in parejas])
    eje.set_yticks(range(len(nombres)), list(nombres))
    eje.grid(visible=False)
    eje.tick_params(length=0)
    for spine in eje.spines.values():
        spine.set_visible(False)
    for (i, j), valor in np.ndenumerate(valores):
        oscuro = valor > 0.55 * np.ceil(d.max())
        texto = f"{valor:.2f}" + ("" if valor > umbral else "  (débil)")
        eje.text(j, i, texto, ha="center", va="center", fontsize=10,
                 color="#ffffff" if oscuro else TINTA, fontweight="bold" if valor > umbral else "normal")
    barra = figura.colorbar(imagen, ax=eje, fraction=0.05, pad=0.03)
    barra.set_label("d de Cohen")
    barra.outline.set_visible(False)
    eje.set_title(f"Separación entre cada pareja de estados (d > {umbral} = grande)", loc="left", fontsize=12)
    return _guardar(figura, carpeta, "04_mapa_calor_cohen.png")


@plt.rc_context(ESTILO)
def centroides(X_entrenamiento, y_entrenamiento, centroides_originales, clases, nombres, unidades,
               carpeta: Path, x: int = 0, y: int = 1) -> Path:
    """Puntos de entrenamiento (atenuados) y el centroide de cada clase, en unidades originales.

    Solo se ven 2 de las 4 variables: el modelo decide en 4 dimensiones, así que algún
    punto puede parecer más cerca de otro centroide en este plano.
    """
    validos = ~np.isnan(X_entrenamiento[:, [x, y]]).any(axis=1)
    figura, eje = plt.subplots(figsize=(9, 6.5))
    for c in clases:
        filas = validos & (y_entrenamiento == c)
        eje.scatter(X_entrenamiento[filas, x], X_entrenamiento[filas, y], s=20, color=COLORES_ESTADO[c],
                    alpha=0.3, edgecolors="none", label=f"{ESTADOS[c]} (entrenamiento)")
    for c, centroide in zip(clases, centroides_originales):
        eje.scatter(centroide[x], centroide[y], s=260, marker="X", color=COLORES_ESTADO[c],
                    edgecolors=TINTA, linewidths=1.2, zorder=3)
        eje.annotate(f"Centroide\n{ESTADOS[c]}", (centroide[x], centroide[y]), xytext=(12, 10),
                     textcoords="offset points", fontsize=9, color=TINTA, fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.3", facecolor=SUPERFICIE, edgecolor=COLORES_ESTADO[c]))
    eje.set_xlabel(f"{nombres[x]} ({unidades[x]})")
    eje.set_ylabel(f"{nombres[y]} ({unidades[y]})")
    eje.set_title("Centroides aprendidos: cada punto nuevo se asigna al más cercano", loc="left", fontsize=12)
    eje.legend(loc="upper left", markerscale=1.2)
    return _guardar(figura, carpeta, "05_centroides.png")


@plt.rc_context(ESTILO)
def matriz_confusion(matriz: np.ndarray, clases, carpeta: Path) -> Path:
    """Matriz de confusión con una sola escala de azul (más oscuro = más casos) y el recuento en cada celda."""
    mapa = LinearSegmentedColormap.from_list("azul", ESCALA_AZUL)
    figura, eje = plt.subplots(figsize=(7.2, 5.6))
    imagen = eje.imshow(matriz, cmap=mapa, vmin=0, vmax=matriz.max())
    nombres = [ESTADOS[c].replace(" ", "\n") for c in clases]
    eje.set_xticks(range(len(clases)), nombres)
    eje.set_yticks(range(len(clases)), nombres)
    eje.set_xlabel("Estado predicho")
    eje.set_ylabel("Estado real")
    eje.grid(visible=False)
    eje.tick_params(length=0)
    for spine in eje.spines.values():
        spine.set_visible(False)
    totales = matriz.sum(axis=1)
    for (i, j), valor in np.ndenumerate(matriz):
        oscuro = valor > 0.55 * matriz.max()
        eje.text(j, i, f"{valor}\n{valor / totales[i]:.0%}", ha="center", va="center", fontsize=11,
                 color="#ffffff" if oscuro else TINTA, fontweight="bold" if i == j else "normal")
    barra = figura.colorbar(imagen, ax=eje, fraction=0.046, pad=0.04)
    barra.set_label("Registros de prueba")
    barra.outline.set_visible(False)
    eje.set_title("Matriz de confusión · 150 registros de prueba (% sobre cada fila)", loc="left", fontsize=12)
    return _guardar(figura, carpeta, "06_matriz_confusion.png")
