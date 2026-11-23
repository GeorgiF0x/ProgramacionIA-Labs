"""Genera memoria.pdf (apartado 7) con ReportLab.

Uso (desde la raíz del proyecto, después de ejecutar main.py para tener los gráficos):
    .venv/bin/python memoria/generar_memoria.py

Para añadir el vídeo, rellenar ENLACE_VIDEO y volver a ejecutar.
Todas las cifras proceden de la salida de main.py con la semilla 42.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, XPreformatted)
from reportlab.platypus.tableofcontents import TableOfContents

RAIZ = Path(__file__).resolve().parent.parent
GRAFICOS = RAIZ / "resultados" / "graficos"
SALIDA = RAIZ / "memoria.pdf"

ALUMNO = "Georgi Borisov Aleksandrov"
ENLACE_VIDEO = ""  # pegar aquí la URL del vídeo cuando esté grabado
REPOSITORIO = "https://github.com/GeorgiF0x/ProgramacionIA-Labs"

TINTA = colors.HexColor("#0a0a0a")
GRIS = colors.HexColor("#595a5a")
LINEA = colors.HexColor("#d8d9d9")
FONDO = colors.HexColor("#f2f2f1")
ROJO = colors.HexColor("#d71921")

# ---------------------------------------------------------------- fuentes

FUENTES = Path("/System/Library/Fonts/Supplemental")
for nombre, fichero in {
    "Arial": "Arial.ttf", "Arial-Bold": "Arial Bold.ttf",
    "Arial-Italic": "Arial Italic.ttf", "Arial-BoldItalic": "Arial Bold Italic.ttf",
}.items():
    pdfmetrics.registerFont(TTFont(nombre, str(FUENTES / fichero)))
# Charter: serif con números alineados, más legible que Georgia en un texto lleno de cifras.
for indice, nombre in enumerate(("Charter", "Charter-Italic", "Charter-BoldItalic", "Charter-Bold")):
    pdfmetrics.registerFont(TTFont(nombre, str(FUENTES / "Charter.ttc"), subfontIndex=indice))
pdfmetrics.registerFont(TTFont("Menlo", "/System/Library/Fonts/Menlo.ttc", subfontIndex=0))
pdfmetrics.registerFontFamily("Charter", normal="Charter", bold="Charter-Bold",
                              italic="Charter-Italic", boldItalic="Charter-BoldItalic")
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                              italic="Arial-Italic", boldItalic="Arial-BoldItalic")

# ---------------------------------------------------------------- estilos

CUERPO = ParagraphStyle("cuerpo", fontName="Charter", fontSize=10.3, leading=15.2, textColor=TINTA,
                        spaceAfter=7, alignment=TA_LEFT)
LISTA = ParagraphStyle("lista", parent=CUERPO, spaceAfter=3)
H1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=16, leading=20, textColor=TINTA,
                    spaceBefore=4, spaceAfter=10)
H2 = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=11.5, leading=15, textColor=TINTA,
                    spaceBefore=10, spaceAfter=5)
CELDA = ParagraphStyle("celda", fontName="Arial", fontSize=8.8, leading=11.5, textColor=TINTA)
CELDA_CAB = ParagraphStyle("celda_cab", parent=CELDA, fontName="Arial-Bold", textColor=GRIS)
PIE = ParagraphStyle("pie", fontName="Arial-Italic", fontSize=8.5, leading=11, textColor=GRIS, spaceAfter=10)
CODIGO = ParagraphStyle("codigo", fontName="Menlo", fontSize=8.2, leading=11.2, textColor=TINTA,
                        backColor=FONDO, borderPadding=(7, 8, 7, 8), spaceBefore=4, spaceAfter=10)
NOTA = ParagraphStyle("nota", parent=CUERPO, fontSize=9.6, leading=14, textColor=TINTA,
                      backColor=FONDO, borderPadding=(8, 10, 8, 10), spaceBefore=4, spaceAfter=12)


class Memoria(BaseDocTemplate):
    """Plantilla con portada sin pie y páginas con pie; registra los títulos para el índice."""

    def __init__(self, ruta):
        super().__init__(str(ruta), pagesize=A4, leftMargin=2.3 * cm, rightMargin=2.3 * cm,
                         topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                         title="Sistema inteligente de monitorización y diagnóstico industrial",
                         author="" if ALUMNO.startswith("[") else ALUMNO,
                         subject="Memoria de la práctica de Programación de Inteligencia Artificial")
        marco = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate("portada", [marco]),
                               PageTemplate("normal", [marco], onPage=self._pie)])

    def _pie(self, lienzo, doc):
        lienzo.saveState()
        lienzo.setStrokeColor(LINEA)
        lienzo.line(doc.leftMargin, 1.45 * cm, A4[0] - doc.rightMargin, 1.45 * cm)
        lienzo.setFont("Arial", 8)
        lienzo.setFillColor(GRIS)
        lienzo.drawString(doc.leftMargin, 1.0 * cm, "Sistema de monitorización y diagnóstico industrial · Memoria")
        lienzo.drawRightString(A4[0] - doc.rightMargin, 1.0 * cm, str(doc.page))
        lienzo.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h1":
            texto = flowable.getPlainText()
            clave = f"sec-{self.seq.nextf('sec')}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=0)
            self.notify("TOCEntry", (0, texto, self.page, clave))


# ---------------------------------------------------------------- ayudas

historia = []
contador = {"h1": 0, "fig": 0, "tab": 0}


def p(texto, estilo=CUERPO):
    historia.append(Paragraph(texto, estilo))


def h1(texto):
    contador["h1"] += 1
    historia.append(Paragraph(f'<font color="#d71921">{contador["h1"]}.</font>  {texto}', H1))


def h2(texto):
    historia.append(Paragraph(texto, H2))


def lista(items, numerada=False):
    historia.append(ListFlowable(
        [ListItem(Paragraph(t, LISTA), leftIndent=14) for t in items],
        bulletType="1" if numerada else "bullet", start="1" if numerada else None,
        bulletFontName="Arial-Bold" if numerada else "Arial", bulletFontSize=9.5 if numerada else 8,
        bulletColor=ROJO, leftIndent=14, spaceAfter=8))


def tabla(filas, anchos, titulo=None, numericas=()):
    """filas[0] es la cabecera. numericas: índices de columnas alineadas a la derecha."""
    datos = []
    for i, fila in enumerate(filas):
        estilo = CELDA_CAB if i == 0 else CELDA
        datos.append([Paragraph(str(c), ParagraphStyle(f"c{i}{j}", parent=estilo,
                                                       alignment=2 if j in numericas else 0))
                      for j, c in enumerate(fila)])
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    bloque = [t]
    if titulo:
        contador["tab"] += 1
        bloque.append(Spacer(1, 4))
        bloque.append(Paragraph(f"Tabla {contador['tab']}. {titulo}", PIE))
    else:
        bloque.append(Spacer(1, 10))
    historia.append(KeepTogether(bloque))


def figura(fichero, pie, ancho_cm=15.6):
    ruta = GRAFICOS / fichero
    ancho, alto = ImageReader(str(ruta)).getSize()
    img = Image(str(ruta), width=ancho_cm * cm, height=ancho_cm * cm * alto / ancho)
    contador["fig"] += 1
    historia.append(KeepTogether([img, Spacer(1, 4), Paragraph(f"Figura {contador['fig']}. {pie}", PIE)]))


def codigo(texto):
    historia.append(XPreformatted(texto.strip("\n"), CODIGO))


def nota(texto):
    p(texto, NOTA)


# ================================================================ PORTADA

historia.append(Spacer(1, 3.2 * cm))
p('<font color="#d71921">PRÁCTICA EVALUABLE</font> · PROGRAMACIÓN DE INTELIGENCIA ARTIFICIAL',
  ParagraphStyle("eyebrow", fontName="Arial-Bold", fontSize=9, leading=12, textColor=GRIS, spaceAfter=18))
p("Sistema inteligente de monitorización y diagnóstico industrial",
  ParagraphStyle("titulo", fontName="Charter", fontSize=30, leading=35, textColor=TINTA, spaceAfter=14))
p("Memoria técnica: decisiones, resultados y conclusiones",
  ParagraphStyle("subtitulo", fontName="Charter-Italic", fontSize=15, leading=20, textColor=GRIS, spaceAfter=40))

video = (f'<a href="{ENLACE_VIDEO}" color="#d71921">{ENLACE_VIDEO}</a>' if ENLACE_VIDEO
         else '<font color="#d71921">Pendiente de grabación. El enlace se añadirá antes de la entrega.</font>')
portada = [
    ["Alumno", ALUMNO],
    ["Curso", "Curso de Especialización de Inteligencia Artificial y Big Data"],
    ["Profesor", "Raúl Rubio Vázquez"],
    ["Fecha", "Noviembre de 2026"],
    ["Vídeo explicativo", video],
    ["Repositorio", f'<a href="{REPOSITORIO}" color="#d71921">{REPOSITORIO}</a>'],
]
t = Table([[Paragraph(a, CELDA_CAB), Paragraph(b, ParagraphStyle("pv", parent=CELDA, fontSize=10, leading=13))]
           for a, b in portada], colWidths=[3.6 * cm, 12.5 * cm], hAlign="LEFT")
t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, TINTA), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINEA),
                       ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                       ("LEFTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
historia.append(t)
historia.append(NextPageTemplate("normal"))
historia.append(PageBreak())

# ================================================================ ÍNDICE

p("Índice", H2)
indice = TableOfContents()
indice.levelStyles = [ParagraphStyle("toc0", fontName="Arial", fontSize=10.5, leading=17, textColor=TINTA,
                                     leftIndent=0, firstLineIndent=0)]
historia.append(indice)
historia.append(PageBreak())

# ================================================================ 1. INTRODUCCIÓN

h1("Introducción y objetivos")
p("Una empresa industrial quiere supervisar sus máquinas a partir de cuatro sensores (temperatura, vibración, "
  "consumo eléctrico y presión) y estimar qué incidencia puede estar ocurriendo: funcionamiento normal, "
  "desgaste mecánico o sobrecalentamiento.")
p("Se ha desarrollado una aplicación en Python que carga y limpia los datos, los analiza estadísticamente, "
  "entrena un clasificador de <b>centroide más cercano programado desde cero</b> y evalúa su rendimiento. "
  "Todo el procesamiento se hace con arrays de NumPy y operaciones vectorizadas, sin Pandas ni bibliotecas "
  "de aprendizaje automático. Matplotlib se usa solo para los gráficos.")
tabla([
    ["Objetivo del enunciado", "Apartado", "Dónde está"],
    ["Cargar y gestionar los datos con arrays de NumPy", "1", "src/carga.py"],
    ["Identificar y tratar valores ausentes, incorrectos y anómalos", "2", "src/limpieza.py"],
    ["Análisis estadístico de las variables", "3", "src/analisis.py, src/graficos.py"],
    ["Transformar y normalizar con operaciones vectorizadas", "4", "src/preparacion.py"],
    ["Clasificador sin bibliotecas de aprendizaje automático", "5", "src/clasificador.py"],
    ["Evaluar el rendimiento con varias métricas", "6", "src/evaluacion.py"],
    ["Presentar los resultados de forma estructurada", "7", "main.py y esta memoria"],
], [9.2, 1.8, 5.4], "Objetivos y módulo que los resuelve.")
p("Todas las cifras de esta memoria son las que imprime <font name='Menlo' size='9'>main.py</font> con la "
  "semilla 42, por lo que son reproducibles.")

# ================================================================ 2. DATOS

h1("Descripción del conjunto de datos")
p("El fichero <font name='Menlo' size='9'>datos/sensores.csv</font> contiene <b>750 mediciones</b>, cada una de "
  "una máquina, con seis columnas:")
tabla([
    ["Columna", "Descripción", "Tipo", "Rango admisible"],
    ["id", "Identificador del registro (S0001…S0750)", "texto", "—"],
    ["temperatura", "Temperatura del motor", "decimal, °C", "0 – 150"],
    ["vibracion", "Intensidad de la vibración", "decimal, mm/s", "0 – 15"],
    ["consumo", "Potencia consumida", "decimal, kW", "0 – 65"],
    ["presion", "Presión del circuito hidráulico", "decimal, bar", "0 – 12"],
    ["estado", "Diagnóstico real: 0 normal, 1 desgaste, 2 sobrecalentamiento", "entero", "0, 1, 2"],
], [2.6, 7.4, 3.0, 3.4], "Columnas del conjunto de datos y rangos físicos dados por el enunciado.")
p("Las tres clases están <b>perfectamente equilibradas</b>: 250 registros de cada una. Gracias a eso el "
  "<i>accuracy</i> es una métrica fiable, y un clasificador que respondiera siempre lo mismo solo acertaría el 33 %.")
p("El conjunto incluye problemas de calidad introducidos a propósito:")
lista([
    "<b>75 celdas vacías</b> repartidas en 73 registros (9,7 %): 15 en temperatura, 18 en vibración, 19 en consumo "
    "y 23 en presión. Dos registros tienen dos huecos.",
    "<b>11 valores fuera del rango físico</b>, imposibles en una máquina real (por ejemplo, −35 °C o 38 mm/s).",
    "<b>Valores extremos dentro del rango</b>, que pueden ser anomalías reales de funcionamiento.",
])

# ================================================================ 3. ESTRUCTURA

h1("Estructura de la solución")
p("El código sigue la estructura del entregable. <font name='Menlo' size='9'>main.py</font> no calcula nada: "
  "llama a cada módulo en orden y pasa a cada uno lo que devolvió el anterior. Cada módulo tiene una única "
  "responsabilidad.")
tabla([
    ["Fichero", "Responsabilidad", "Devuelve"],
    ["main.py", "Ejecuta los apartados 1 a 6 en orden y gestiona los errores de carga", "código de salida 0 o 1"],
    ["src/carga.py", "Lee el CSV, valida su estructura y resume los datos", "ConjuntoDatos (750, 4)"],
    ["src/limpieza.py", "Detecta errores y atípicos; decide qué conservar", "datos limpios (748, 4)"],
    ["src/analisis.py", "Estadísticas globales y por clase, F y d de Cohen", "tablas de estadísticas"],
    ["src/graficos.py", "Dibuja y guarda los gráficos", "6 PNG en resultados/graficos"],
    ["src/preparacion.py", "División, imputación y normalización sin fuga", "matrices (598, 4) y (150, 4)"],
    ["src/clasificador.py", "Centroides, distancias y predicciones", "150 predicciones y su CSV"],
    ["src/evaluacion.py", "Matriz de confusión, métricas y validación cruzada", "métricas y respuestas"],
], [3.6, 7.8, 5.0], "Módulos del proyecto.")
p("<font name='Menlo' size='9'>preparacion.py</font> y <font name='Menlo' size='9'>graficos.py</font> no aparecen "
  "en la estructura del enunciado. Se han añadido porque preparar los datos y dibujar son responsabilidades "
  "distintas de limpiar y calcular, y mezclarlas haría los módulos más difíciles de mantener.")
p("Para ejecutar la práctica:")
codigo("""
pip install -r requirements.txt     # numpy y matplotlib
python main.py                      # ejecuta los apartados 1 a 6
""")
p("Si el CSV no existe o no tiene la forma esperada, el programa muestra un mensaje claro y termina con código 1 "
  "en lugar de un error de Python. Además, el cuaderno <font name='Menlo' size='9'>practica_sensores.ipynb</font> "
  "recorre los mismos pasos con explicaciones; importa las funciones de <font name='Menlo' size='9'>src/</font>, "
  "así que el código no se repite.")

# ================================================================ 4. CARGA

h1("Carga y exploración de los datos")
p("El CSV se lee con <font name='Menlo' size='9'>np.genfromtxt</font>, que convierte cada celda vacía en "
  "<font name='Menlo' size='9'>nan</font>. Así los ausentes quedan marcados dentro del array y se cuentan sin bucles. "
  "<font name='Menlo' size='9'>np.loadtxt</font> no sirve: falla con una celda vacía.")
p("Los datos se separan en tres arrays según su papel, porque un array de NumPy solo admite un tipo: "
  "<font name='Menlo' size='9'>ids</font> (texto), <font name='Menlo' size='9'>mediciones</font> (matriz decimal "
  "de 750 × 4, las variables predictoras) y <font name='Menlo' size='9'>estados</font> (enteros, la variable "
  "objetivo). Se agrupan en un <font name='Menlo' size='9'>NamedTuple</font> para acceder a ellos por su nombre.")
codigo("""
ids        = np.genfromtxt(ruta, usecols=0,           dtype=str,   ndmin=1, ...)
mediciones = np.genfromtxt(ruta, usecols=range(1, 5), dtype=float, ndmin=2, ...)
estados    = np.genfromtxt(ruta, usecols=5,           dtype=float, ndmin=1, ...)
""")
p("Dos detalles evitan errores silenciosos. El estado se lee como decimal y no como entero, porque con "
  "<font name='Menlo' size='9'>dtype=int</font> una celda vacía se convertiría en −1 sin avisar. Y "
  "<font name='Menlo' size='9'>ndmin</font> garantiza la forma (n, 4) aunque el fichero tuviera una sola fila.")
p("Antes de continuar se comprueba que el fichero existe, que la cabecera es exactamente la esperada, que hay "
  "al menos una fila y que todos los estados valen 0, 1 o 2. Un sensor vacío se puede tratar después, pero una "
  "fila sin diagnóstico no sirve ni para entrenar ni para evaluar.")

# ================================================================ 5. LIMPIEZA

h1("Limpieza: problemas encontrados y decisiones")
p("El criterio general ha sido distinguir entre lo <b>imposible</b>, que es un error de medición, y lo "
  "<b>raro pero posible</b>, que puede ser una anomalía real y es justo lo que un sistema de monitorización "
  "debe detectar.")
h2("Problemas encontrados")
tabla([
    ["Id", "Sensor", "Valor", "Rango", "Id", "Sensor", "Valor", "Rango"],
    ["S0003", "Temperatura", "−35,00", "0–150", "S0414", "Consumo", "−1,50", "0–65"],
    ["S0149", "Temperatura", "245,00", "0–150", "S0590", "Consumo", "−4,00", "0–65"],
    ["S0396", "Temperatura", "−18,00", "0–150", "S0037", "Presión", "−3,00", "0–12"],
    ["S0130", "Vibración", "−2,50", "0–15", "S0724", "Presión", "28,00", "0–12"],
    ["S0168", "Vibración", "−0,80", "0–15", "S0728", "Presión", "−1,20", "0–12"],
    ["S0171", "Vibración", "38,00", "0–15", "", "", "", ""],
], [1.4, 2.2, 1.6, 1.4, 1.4, 2.2, 1.6, 1.4], "Los 11 valores fuera del rango físico.", numericas=(2, 6))
h2("Decisiones adoptadas")
tabla([
    ["Situación", "Cuántos", "Tratamiento", "Justificación"],
    ["Valor fuera del rango físico", "11 celdas", "Se convierte en nan",
     "Es un error seguro, pero solo falla un sensor de la fila; borrarla perdería tres valores válidos."],
    ["Atípico estadístico dentro del rango", "45 celdas", "Se conserva y se informa",
     "Puede ser una anomalía real. Eliminarlo dejaría al clasificador sin los casos límite."],
    ["Registro con 2 o más huecos", "2 registros", "Se descarta",
     "S0236 y S0641 no tienen temperatura ni vibración: la mitad del registro sería inventada."],
    ["Celda vacía en un registro válido", "82 celdas", "Se imputa en el apartado 4",
     "Con la mediana del entrenamiento, después de dividir, para no usar información de la prueba."],
], [3.6, 2.0, 3.3, 7.5], "Tratamiento de cada problema.")
p("Los atípicos se detectan con el criterio de Tukey: un valor es atípico si queda fuera de "
  "[Q1 − 1,5·IQR, Q3 + 1,5·IQR]. Se prefirió al <i>z-score</i> porque los cuartiles no se ven afectados por los "
  "propios valores extremos, mientras que la media y la desviación sí.")
p("Los cuartiles se calculan <b>dentro de cada clase</b>. Calculados sobre todo el conjunto, marcaban 18 "
  "vibraciones como atípicas, y 14 de ellas eran de máquinas con desgaste: una vibración alta es precisamente la "
  "señal del desgaste. Además, los atípicos se buscan después de convertir los errores en "
  "<font name='Menlo' size='9'>nan</font>, porque un valor de 245 °C desplazaría los cuartiles.")
p("El resultado son <b>748 registros</b> (249 normales, 250 con desgaste y 249 con sobrecalentamiento), con 82 "
  "huecos pendientes de imputar. Los datos originales no se modifican: <font name='Menlo' size='9'>np.where</font> "
  "crea un array nuevo y cada decisión queda registrada en una máscara (750 × 4).")
h2("Cómo afecta la limpieza a las fases posteriores")
lista([
    "<b>Análisis (apartado 3).</b> Las estadísticas se calculan con funciones que ignoran los nan, solo sobre valores "
    "realmente medidos. Como los atípicos se conservan, la mediana y el IQR describen los datos mejor que la media.",
    "<b>Preparación (apartado 4).</b> La imputación tiene que hacerse después de dividir y con las medianas del "
    "entrenamiento.",
    "<b>Clasificador (apartado 5).</b> Un centroide es una media, así que los atípicos conservados lo desplazan "
    "ligeramente. Con unos 200 registros por clase el efecto es pequeño.",
    "<b>Evaluación (apartado 6).</b> La prueba incluye casos raros, lo que hace las métricas más realistas.",
])

# ================================================================ 6. ANÁLISIS

h1("Principales resultados del análisis estadístico")
p("Se han calculado media, mediana, desviación estándar, mínimo, máximo, cuartiles e IQR de cada variable, de forma "
  "global y por clase, sobre los datos limpios sin imputar. La desviación es <b>muestral</b> "
  "(<font name='Menlo' size='9'>ddof=1</font>), porque los registros son una muestra del comportamiento de las máquinas.")
p("Las estadísticas globales resultan engañosas. La temperatura global tiene una media de 83,0 °C y una mediana de "
  "78,5 °C: la diferencia no se debe a valores erróneos, sino a que el grupo de sobrecalentamiento, alrededor de "
  "105 °C, arrastra la media. Por eso el análisis útil es el comparativo por clase.")
tabla([
    ["Variable", "Normal", "Desgaste", "Sobrecalentamiento", "F (ANOVA)"],
    ["Temperatura (°C)", "67,82 ± 10,24", "76,98 ± 12,27", "104,33 ± 13,22", "615,9"],
    ["Vibración (mm/s)", "2,07 ± 0,68", "5,08 ± 1,47", "3,14 ± 1,27", "400,2"],
    ["Consumo (kW)", "17,89 ± 4,72", "22,05 ± 4,86", "27,62 ± 5,30", "233,3"],
    ["Presión (bar)", "6,42 ± 0,95", "5,83 ± 1,01", "5,92 ± 1,25", "20,9"],
], [3.6, 3.1, 3.1, 3.6, 2.6], "Media ± desviación estándar por clase y estadístico F de cada variable.",
    numericas=(1, 2, 3, 4))
p("Para medir qué variable distingue los estados con números, y no a ojo, se usaron dos medidas. El "
  "<b>estadístico F</b> de un ANOVA divide la varianza entre clases por la varianza dentro de ellas: cuanto mayor, "
  "más separados están los centros de las clases respecto a su dispersión. La <b>d de Cohen</b> mide la distancia "
  "entre dos clases en desviaciones estándar; por encima de 0,8 la separación se considera grande.")
tabla([
    ["Variable", "Normal vs desgaste", "Normal vs sobrecalentamiento", "Desgaste vs sobrecalentamiento"],
    ["Temperatura", "0,81", "<b>3,09</b>", "<b>2,14</b>"],
    ["Vibración", "<b>2,63</b>", "1,05", "1,41"],
    ["Consumo", "0,87", "1,94", "1,10"],
    ["Presión", "0,60", "0,45", "0,07"],
], [3.4, 4.0, 4.6, 4.4], "d de Cohen de cada pareja de estados.", numericas=(1, 2, 3))
figura("01_boxplots_por_estado.png", "Distribución de cada variable por estado. Los puntos sueltos son los atípicos "
       "de cada clase, con el mismo criterio que en la limpieza.")
p("Conclusiones del análisis:")
lista([
    "La <b>temperatura</b> separa el sobrecalentamiento de las otras dos clases (d = 3,09 y 2,14).",
    "La <b>vibración</b> separa el desgaste de las máquinas normales (d = 2,63).",
    "El <b>consumo</b> aporta una separación moderada entre todas las clases.",
    "La <b>presión</b> apenas distingue nada (F = 20,9; entre desgaste y sobrecalentamiento, d = 0,07).",
    "La pareja <b>normal–desgaste</b> será la más difícil: solo la vibración la separa con claridad.",
])
figura("02_dispersion_temperatura_vibracion.png", "Temperatura frente a vibración. Las tres nubes se mezclan "
       "hacia los 75–90 °C y 2,5–4 mm/s, donde se esperan los errores del clasificador.", ancho_cm=13.5)

# ================================================================ 7. PREPARACIÓN

h1("Transformación y normalización")
p("Las variables predictoras ya estaban separadas de la variable objetivo desde la carga. Los 748 registros se "
  "dividen en <b>598 de entrenamiento y 150 de prueba</b>. La división es <b>estratificada</b>: cada clase se "
  "baraja y se corta al 80 % por separado, de modo que la prueba tiene exactamente 50 registros de cada clase. "
  "La semilla fija (<font name='Menlo' size='9'>np.random.default_rng(42)</font>) hace que el reparto sea el mismo "
  "en cada ejecución.")
p("La regla de todo el apartado es que <b>los parámetros se aprenden solo del entrenamiento</b>. La prueba simula "
  "mediciones futuras; si su media o su mediana influyeran en la transformación, habría fuga de datos y las "
  "métricas saldrían optimistas. La función que aprende los parámetros solo recibe el entrenamiento, así que la "
  "fuga es imposible por diseño.")
lista([
    "Se calcula la <b>mediana</b> de cada variable en el entrenamiento y se rellenan los huecos de las dos partes "
    "(68 en entrenamiento y 14 en prueba). Se usa la mediana porque no la desplazan los atípicos conservados.",
    "Con el entrenamiento ya completo, se calculan la <b>media</b> y la <b>desviación</b> de cada variable.",
    "Las dos partes se normalizan con <b>z = (x − media) / desviación</b>, usando esos mismos parámetros.",
], numerada=True)
tabla([
    ["Parámetro", "Temperatura", "Vibración", "Consumo", "Presión"],
    ["Mediana (imputación)", "78,770", "3,070", "21,679", "6,091"],
    ["Media", "82,953", "3,438", "22,512", "6,065"],
    ["Desviación (ddof = 1)", "19,375", "1,733", "6,408", "1,091"],
], [4.4, 3.0, 3.0, 3.0, 3.0], "Los 12 parámetros aprendidos del entrenamiento.", numericas=(1, 2, 3, 4))
p("La mediana de temperatura del entrenamiento es 78,77, mientras que con todos los datos sería 78,50: la diferencia "
  "confirma que no se ha usado la prueba. Normalizar es imprescindible porque el clasificador mide distancias: antes "
  "de normalizar, la temperatura tenía un rango de 102 °C y la vibración de 10 mm/s, y la primera habría dominado la "
  "distancia solo por su escala.")
p("Tras normalizar, el entrenamiento queda con media 0 y desviación 1 exactas. La prueba queda cerca, con medias "
  "entre −0,069 y 0,013 y desviaciones entre 0,895 y 1,011. Que no sean exactas es lo esperado: se ha normalizado "
  "con los parámetros del entrenamiento, no con los suyos.")

# ================================================================ 8. CLASIFICADOR

h1("Funcionamiento del clasificador")
p("El clasificador de <b>centroide más cercano</b> resume cada estado en un punto: la media de sus registros de "
  "entrenamiento normalizados. Para diagnosticar una medición nueva, calcula su distancia euclídea a los tres "
  "centroides y le asigna el estado del más cercano.")
codigo("""
# Entrenar: matriz de pertenencia P (598 x 3) y media por clase
pertenencia = (y[:, np.newaxis] == clases[np.newaxis, :]).astype(float)
centroides  = (pertenencia.T @ X) / pertenencia.sum(axis=0)[:, np.newaxis]

# Predecir: todas las distancias a la vez por broadcasting (150 x 3 x 4 -> 150 x 3)
diferencias  = X[:, np.newaxis, :] - centroides[np.newaxis, :, :]
distancias   = np.sqrt((diferencias ** 2).sum(axis=2))
prediccion   = clases[np.argmin(distancias, axis=1)]
""")
p("La implementación no recorre los registros con bucles. Los centroides se obtienen con un producto de matrices: "
  "cada fila de la matriz de pertenencia selecciona los registros de una clase, y <font name='Menlo' size='9'>P.T @ X</font> "
  "los suma. Las 450 distancias (150 registros por 3 centroides) se calculan en una sola operación mediante "
  "<i>broadcasting</i> en tres dimensiones. Se comprobó que ambas versiones dan exactamente los mismos resultados que "
  "unos bucles escritos a mano.")
tabla([
    ["Centroide", "Temperatura (°C)", "Vibración (mm/s)", "Consumo (kW)", "Presión (bar)"],
    ["Normal", "67,92", "2,08", "18,03", "6,41"],
    ["Desgaste mecánico", "77,00", "5,06", "22,12", "5,92"],
    ["Sobrecalentamiento", "103,97", "3,16", "27,39", "5,87"],
], [4.0, 3.2, 3.2, 3.0, 3.0], "Centroides aprendidos, devueltos a unidades reales para interpretarlos.",
    numericas=(1, 2, 3, 4))
figura("05_centroides.png", "Centroides sobre los puntos de entrenamiento. Solo se muestran dos de las cuatro "
       "variables, en unidades reales; el modelo decide en cuatro dimensiones normalizadas.", ancho_cm=13.5)
p("Se usan las cuatro variables. La presión era la más débil, así que se probó a quitarla con una validación cruzada "
  "de 5 pliegues <b>solo sobre el entrenamiento</b>: con las cuatro variables se obtiene 0,888 ± 0,027 y sin la presión "
  "0,893 ± 0,018. La diferencia es menor que la variación entre pliegues, por lo que no justifica cambiar el modelo. "
  "Usar solo temperatura y vibración empeora el resultado (0,870 ± 0,041). La decisión no se tomó mirando la prueba, "
  "porque eso supondría ajustar el modelo al examen.")
p("Las 150 predicciones se guardan en <font name='Menlo' size='9'>resultados/predicciones.csv</font> junto con la "
  "distancia a cada centroide, lo que permite revisar cada fallo.")

# ================================================================ 9. EVALUACIÓN

h1("Resultados de la evaluación")
p("Todas las métricas se han implementado a mano con NumPy. La matriz de confusión se construye sin bucles: cada "
  "pareja (real, predicho) se convierte en un número de celda, <font name='Menlo' size='9'>real × 3 + predicho</font>, "
  "y <font name='Menlo' size='9'>np.bincount</font> los cuenta.")
tabla([
    ["Real \\ Predicho", "Normal", "Desgaste", "Sobrecalentamiento"],
    ["Normal", "<b>48</b>", "1", "1"],
    ["Desgaste mecánico", "7", "<b>40</b>", "3"],
    ["Sobrecalentamiento", "0", "4", "<b>46</b>"],
], [4.6, 3.2, 3.2, 3.8], "Matriz de confusión sobre los 150 registros de prueba.", numericas=(1, 2, 3))
tabla([
    ["Clase", "Precision", "Recall", "F1", "Soporte"],
    ["Normal", "0,873", "0,960", "0,914", "50"],
    ["Desgaste mecánico", "0,889", "0,800", "0,842", "50"],
    ["Sobrecalentamiento", "0,920", "0,920", "0,920", "50"],
    ["Media macro", "0,894", "0,893", "0,892", "150"],
], [4.6, 2.8, 2.8, 2.8, 2.8], "Métricas por clase. Accuracy global: 0,893 (134 aciertos de 150).",
    numericas=(1, 2, 3, 4))
p("La <b>precision</b> de una clase indica qué parte de lo que se predijo como esa clase lo era realmente; el "
  "<b>recall</b>, qué parte de lo que era esa clase se detectó. El F1 es su media armónica. Para comprobar que el "
  "reparto de la semilla 42 no era especialmente favorable, se repitió la validación cruzada sobre el entrenamiento: "
  "0,888 ± 0,027. El 0,893 de la prueba está dentro de ese rango.")
figura("06_matriz_confusion.png", "Matriz de confusión. El porcentaje de la diagonal es el recall de cada clase.",
       ancho_cm=11.5)
h2("Respuestas a las preguntas del enunciado")
lista([
    "<b>¿Qué categoría presenta mejores resultados?</b> El sobrecalentamiento (F1 = 0,920; precision y recall de "
    "0,920). La temperatura lo separa claramente de las otras dos clases.",
    "<b>¿Qué incidencias se confunden con mayor frecuencia?</b> El desgaste mecánico diagnosticado como normal "
    "(7 casos). Contando las dos direcciones, normal–desgaste suma 8 errores y desgaste–sobrecalentamiento 7, "
    "mientras que normal–sobrecalentamiento solo 1.",
    "<b>¿Hay alguna categoría difícil de identificar?</b> El desgaste mecánico: su recall es 0,800, es decir, se "
    "escapan 10 de 50, y es la única clase que se confunde con las otras dos.",
    "<b>¿Sería adecuado en un entorno industrial real?</b> Solo como herramienta de apoyo, no como sistema autónomo. "
    "7 de las 100 máquinas con avería de la prueba se diagnostican como normales, todas ellas con desgaste: un 14 % de "
    "los desgastes no se revisaría, y es el error más caro en mantenimiento. El sistema sí es útil como alerta "
    "temprana que prioriza qué máquinas revisar, con la decisión final en manos de una persona.",
], numerada=True)
p("El análisis del apartado 3 anticipó bien que la pareja normal–desgaste sería la más difícil y que el "
  "sobrecalentamiento sería la clase más fácil. No anticipó que la pareja desgaste–sobrecalentamiento acumularía "
  "casi tantos errores: en presión son prácticamente idénticas (d = 0,07) y en la franja de 80–90 °C se mezclan.")

# ================================================================ 10. LIMITACIONES

h1("Limitaciones del sistema")
lista([
    "<b>No tiene en cuenta la dispersión de cada clase.</b> La distancia euclídea trata igual todas las direcciones, "
    "pero el desgaste es mucho más disperso en vibración (desviación 1,47 mm/s) que las máquinas normales "
    "(0,68 mm/s). Un desgaste leve queda más cerca del centroide normal aunque pertenezca a una clase más ancha: es la "
    "causa de los 7 desgastes diagnosticados como normales.",
    "<b>Fronteras simples.</b> El modelo separa las clases con fronteras lineales a medio camino entre centroides. No "
    "puede representar clases con formas irregulares o con varios grupos.",
    "<b>Todas las variables pesan igual.</b> Tras normalizar, la presión pesa lo mismo que la temperatura. En estos "
    "datos el efecto medido es pequeño, pero en otros podría introducir ruido.",
    "<b>No da un grado de confianza.</b> Siempre emite un diagnóstico, aunque la medición esté casi a la misma "
    "distancia de dos centroides.",
    "<b>Coste de los errores simétrico.</b> Confundir un desgaste con una máquina normal cuesta mucho más que una "
    "falsa alarma, pero el modelo no distingue entre ambos errores.",
    "<b>Datos equilibrados y pocos.</b> En una fábrica real casi todas las mediciones son normales, así que la "
    "precision de las clases de avería bajaría. Además, con 50 registros por clase en la prueba, un solo error mueve "
    "el recall dos puntos.",
    "<b>Mediciones aisladas.</b> Cada registro se diagnostica por separado, sin la historia de la máquina, aunque "
    "el desgaste suele ser un proceso gradual.",
    "<b>Imputación con la mediana global.</b> Una máquina normal sin dato de vibración recibe 3,07 mm/s, cuando las "
    "normales rondan los 2,1 mm/s: la imputación acerca esos registros al centro de todos los datos.",
])

# ================================================================ 11. MEJORAS

h1("Posibles mejoras")
lista([
    "<b>Marcar los casos dudosos para revisión.</b> Los 16 fallos tienen una diferencia mediana de 0,235 entre las "
    "distancias a los dos centroides más cercanos, frente a 1,106 en los aciertos. En este conjunto, marcar como "
    "\"revisar\" las predicciones con una diferencia menor de 0,3 señala 22 registros (15 %) que contienen 10 de los "
    "16 errores, y el resto de predicciones acierta el 95,3 %. El umbral debería fijarse con validación cruzada "
    "sobre el entrenamiento, no con la prueba.",
    "<b>Usar la dispersión de cada clase</b>, por ejemplo con la distancia de Mahalanobis o normalizando la distancia "
    "por la desviación de cada clase. Ataca directamente la principal causa de error.",
    "<b>Penalizar los errores caros</b>, desplazando la decisión para que una máquina dudosa entre normal y desgaste "
    "se envíe a revisión antes que darla por buena.",
    "<b>Comparar con otros modelos</b> sencillos e interpretables, como k vecinos más cercanos o una regresión "
    "logística, siempre con validación cruzada sobre el entrenamiento.",
    "<b>Mejores datos</b>: más mediciones, con la proporción real de cada estado y con la evolución temporal de cada "
    "máquina.",
    "<b>Imputación más informada</b>, estimando el valor ausente a partir de registros similares en lugar de usar la "
    "mediana global.",
])

# ================================================================ 12. CONCLUSIONES

h1("Conclusiones")
p("El sistema cumple los objetivos planteados. Carga y valida los datos con NumPy, separa los errores de medición de "
  "las anomalías reales, identifica con números qué sensor distingue cada estado, prepara los datos sin fuga de "
  "información y clasifica con un algoritmo programado desde cero y vectorizado. En la prueba acierta el "
  "<b>89,3 %</b> de las mediciones, un resultado coherente con la validación cruzada (0,888 ± 0,027).")
p("El análisis previo explica bien el comportamiento del modelo: la temperatura delata el sobrecalentamiento, la "
  "vibración delata el desgaste, y la clase con más fallos es la que el análisis señalaba como más difícil de separar.")
p("Antes de usarlo en un entorno real habría que resolver su principal debilidad: 7 de los 50 desgastes de la prueba "
  "se diagnostican como máquinas normales. Las mejoras prioritarias serían tener en cuenta la dispersión de cada "
  "clase, marcar las predicciones dudosas para revisión humana y entrenar con datos que reflejen la proporción real "
  "de averías. Con esas condiciones, el sistema sería útil como herramienta de apoyo que prioriza qué máquinas "
  "revisar, no como sustituto del diagnóstico de un técnico.")

nota("<b>Vídeo explicativo.</b> " + (f'<a href="{ENLACE_VIDEO}" color="#d71921">{ENLACE_VIDEO}</a>' if ENLACE_VIDEO
     else "Pendiente de grabación. El enlace se añadirá en la portada y aquí antes de la entrega.")
     + f'<br/><b>Repositorio con el código.</b> <a href="{REPOSITORIO}" color="#d71921">{REPOSITORIO}</a>')

Memoria(SALIDA).multiBuild(historia)
print(f"Memoria generada: {SALIDA.relative_to(RAIZ)}")
