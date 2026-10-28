"""
config.py
---------
Configuración central del proyecto: rutas de archivos y tablas de referencia.

¿Por qué un archivo de configuración?
    Si mañana cambias el nombre de un archivo o una categoría, solo editas
    este archivo y no tienes que buscar el valor repetido por todo el código.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Rutas
# ---------------------------------------------------------------------------
# Path(__file__) es la ruta de ESTE archivo (src/config.py).
# .resolve().parent.parent sube dos niveles: src/ -> raíz del proyecto.
# Así las rutas funcionan igual en tu PC, en Render o en Railway.
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "data"
CARPETA_PROCESADOS = CARPETA_DATOS / "procesado"

# Nombres de los archivos originales. Si los tuyos se llaman distinto
# (por ejemplo "Anexo1.NoFetal2019_CE_15-03-23.xlsx"), cámbialos aquí.
ARCHIVO_MORTALIDAD = CARPETA_DATOS / "NoFetal2019.xlsx"
ARCHIVO_CODIGOS = CARPETA_DATOS / "CodigosDeMuerte.xlsx"
ARCHIVO_DIVIPOLA = CARPETA_DATOS / "Divipola.xlsx"

# Archivo intermedio ya limpio (se crea con: python -m src.preparar_datos).
# Cargar un CSV comprimido es mucho más rápido que leer tres Excel.
ARCHIVO_PROCESADO = CARPETA_PROCESADOS / "defunciones_2019.csv.gz"

# Mapa de departamentos (GeoJSON). Primero se busca en data/; si no está,
# se intenta descargar de esta URL pública; si tampoco, se usa un mapa de
# burbujas con las coordenadas de las capitales (ver COORDENADAS_DEPARTAMENTOS).
ARCHIVO_GEOJSON = CARPETA_DATOS / "colombia_departamentos.geojson"
URL_GEOJSON = (
    "https://raw.githubusercontent.com/santiblanko/colombia.geojson/"
    "master/depto.json"
)
# Nombre de la propiedad del GeoJSON que trae el código DANE del departamento
PROPIEDAD_CODIGO_GEOJSON = "DPTO"

# ---------------------------------------------------------------------------
# 2. Tablas de referencia (diccionarios de códigos)
# ---------------------------------------------------------------------------
# SEXO según el diccionario de datos del DANE.
SEXO = {1: "Hombre", 2: "Mujer", 3: "Indeterminado"}

# Clasificación de GRUPO_EDAD1 exigida por la actividad.
# Cada tupla: (código mínimo, código máximo, categoría, rango aproximado)
GRUPOS_EDAD = [
    (0, 4, "Mortalidad neonatal", "Menor de 1 mes"),
    (5, 6, "Mortalidad infantil", "1 a 11 meses"),
    (7, 8, "Primera infancia", "1 a 4 años"),
    (9, 10, "Niñez", "5 a 14 años"),
    (11, 11, "Adolescencia", "15 a 19 años"),
    (12, 13, "Juventud", "20 a 29 años"),
    (14, 16, "Adultez temprana", "30 a 44 años"),
    (17, 19, "Adultez intermedia", "45 a 59 años"),
    (20, 24, "Vejez", "60 a 84 años"),
    (25, 28, "Longevidad / Centenarios", "85 a 100+ años"),
    (29, 29, "Edad desconocida", "Sin información"),
]
# Orden en que deben aparecer las categorías en el histograma (ciclo de vida)
ORDEN_GRUPOS_EDAD = [g[2] for g in GRUPOS_EDAD]

# Homicidios: en la CIE-10 las "agresiones" van de X85 a Y09.
# Verificado con los datos 2019: X85-Y09 = 13.043 muertes, y TODAS tienen
# MANERA_MUERTE = "Homicidio" (esa columna suma 13.077; la diferencia son 34
# casos con otros códigos). Solo armas de fuego (X95) serían 9.273.
# Si tu docente pide solo "agresión con disparo de arma de fuego", usa
# PREFIJOS_HOMICIDIO = ["X95"].
PREFIJOS_HOMICIDIO = [f"X{n}" for n in range(85, 100)] + [f"Y0{n}" for n in range(0, 10)]

MESES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}

# Coordenadas aproximadas de la capital de cada departamento (lat, lon).
# Solo se usan si no hay GeoJSON disponible (mapa de burbujas de respaldo).
COORDENADAS_DEPARTAMENTOS = {
    "05": (6.25, -75.56), "08": (10.96, -74.80), "11": (4.61, -74.08),
    "13": (10.39, -75.51), "15": (5.54, -73.36), "17": (5.07, -75.52),
    "18": (1.61, -75.61), "19": (2.44, -76.61), "20": (10.46, -73.25),
    "23": (8.75, -75.88), "25": (4.80, -74.10), "27": (5.69, -76.66),
    "41": (2.93, -75.28), "44": (11.54, -72.91), "47": (11.24, -74.20),
    "50": (4.14, -73.63), "52": (1.21, -77.28), "54": (7.89, -72.50),
    "63": (4.53, -75.68), "66": (4.81, -75.69), "68": (7.12, -73.12),
    "70": (9.30, -75.40), "73": (4.44, -75.23), "76": (3.45, -76.53),
    "81": (7.08, -70.76), "85": (5.34, -72.40), "86": (1.15, -76.65),
    "88": (12.58, -81.70), "91": (-4.21, -69.94), "94": (3.87, -67.92),
    "95": (2.57, -72.64), "97": (1.25, -70.23), "99": (6.19, -67.49),
}

# Paleta de colores de la interfaz (coherente en todos los gráficos)
COLOR_PRINCIPAL = "#1f4e79"
COLOR_SECUNDARIO = "#c0504d"
COLORES_SEXO = {"Hombre": "#1f77b4", "Mujer": "#e377c2", "Indeterminado": "#7f7f7f"}
PLANTILLA_GRAFICOS = "plotly_white"