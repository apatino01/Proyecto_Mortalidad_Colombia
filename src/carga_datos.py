"""
carga_datos.py
--------------
Fases 3 y 4 del proyecto: CARGA, LIMPIEZA e INTEGRACIÓN de los tres archivos.

Flujo:
    NoFetal2019.xlsx  ─┐
    Divipola.xlsx     ─┼─► limpiar ─► unir (merge) ─► columnas derivadas ─► DataFrame final
    CodigosDeMuerte   ─┘

Cada función hace UNA sola cosa (principio de responsabilidad única):
así es más fácil probarlas y encontrar errores.
"""

import re
import unicodedata

import pandas as pd

from src import config


# ---------------------------------------------------------------------------
# Utilidades de limpieza
# ---------------------------------------------------------------------------
def normalizar_texto(texto) -> str:
    """Convierte 'Código de la CIE-10 (4 caract.)' en 'CODIGO_DE_LA_CIE_10_4_CARACT'.

    - Quita tildes y la ñ (AÑO -> ANO) con unicodedata.
    - Pasa a mayúsculas.
    - Reemplaza todo lo que no sea letra o número por '_'.
    Esto evita errores por espacios invisibles o tildes en los encabezados.
    """
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto.upper())
    return texto.strip("_")


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalizar_texto a todos los nombres de columna."""
    df = df.copy()
    df.columns = [normalizar_texto(c) for c in df.columns]
    return df


def codigo_con_ceros(serie: pd.Series, largo: int) -> pd.Series:
    """Devuelve códigos como texto de 'largo' dígitos: 5001 -> '05001'.

    Excel suele guardar los códigos DANE como números y se pierde el cero
    inicial (Antioquia es '05', no '5'). Sin este paso, los cruces fallan.
    """
    numeros = pd.to_numeric(serie, errors="coerce").astype("Int64")
    return numeros.astype("string").str.zfill(largo)


def limpiar_codigo_cie10(serie: pd.Series) -> pd.Series:
    """'i21.9 ' -> 'I219'. Mayúsculas, sin puntos, guiones ni espacios."""
    return (
        serie.astype("string")
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .str.strip()
    )


def nombre_bonito(serie: pd.Series) -> pd.Series:
    """'VALLE DEL CAUCA' -> 'Valle del Cauca' (solo para mostrar en pantalla)."""
    s = serie.astype("string").str.strip().str.title()
    for palabra in [" De ", " Del ", " La ", " Las ", " Los ", " Y "]:
        s = s.str.replace(palabra, palabra.lower(), regex=False)
    return s


def buscar_columna(df: pd.DataFrame, *opciones: str, obligatoria: bool = True):
    """Busca la primera columna cuyo nombre contiene TODAS las palabras de
    alguna de las opciones. Ej.: buscar_columna(df, "CODIGO CUATRO", "CODIGO 4").
    """
    for opcion in opciones:
        palabras = opcion.split()
        for col in df.columns:
            if all(p in col for p in palabras):
                return col
    if obligatoria:
        raise KeyError(
            f"No encontré una columna parecida a {opciones}. "
            f"Columnas disponibles: {list(df.columns)}"
        )
    return None


def leer_excel_detectando_encabezado(ruta, palabra_clave: str, max_filas: int = 30):
    """Algunos Excel del DANE traen filas de título antes de la tabla.

    1. Lee las primeras filas SIN encabezado.
    2. Busca la primera fila que contiene 'palabra_clave'.
    3. Vuelve a leer el archivo usando esa fila como encabezado.
    """
    muestra = pd.read_excel(ruta, header=None, nrows=max_filas)
    for i, fila in muestra.iterrows():
        textos = [normalizar_texto(v) for v in fila.dropna()]
        if any(palabra_clave in t for t in textos):
            return pd.read_excel(ruta, header=i)
    return pd.read_excel(ruta)  # si no la encuentra, asume fila 0


# ---------------------------------------------------------------------------
# Carga de cada fuente
# ---------------------------------------------------------------------------
def cargar_mortalidad(ruta=config.ARCHIVO_MORTALIDAD) -> pd.DataFrame:
    """Lee NoFetal2019.xlsx: una fila = una defunción."""
    df = leer_excel_detectando_encabezado(ruta, "GRUPO_EDAD1")
    df = normalizar_columnas(df)

    # Código de departamento (2 dígitos) y código DANE del municipio (5 dígitos)
    df["COD_DEPARTAMENTO"] = codigo_con_ceros(df["COD_DEPARTAMENTO"], 2)
    if "COD_DANE" in df.columns:
        df["COD_DANE"] = codigo_con_ceros(df["COD_DANE"], 5)
    else:  # si no viene, se construye: depto (2) + municipio (3)
        df["COD_DANE"] = df["COD_DEPARTAMENTO"] + codigo_con_ceros(df["COD_MUNICIPIO"], 3)

    # Variables numéricas: to_numeric con errors="coerce" convierte lo inválido en NaN
    for col in ["MES", "SEXO", "GRUPO_EDAD1"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Algunos códigos vienen con 3 caracteres (ej. "F03"). En el catálogo del DANE
    # esas categorías sin subdivisión llevan una "X" al final ("F03X").
    df["COD_MUERTE"] = limpiar_codigo_cie10(df["COD_MUERTE"])
    tres = df["COD_MUERTE"].str.len() == 3
    df.loc[tres, "COD_MUERTE"] = df.loc[tres, "COD_MUERTE"] + "X"

    # Manera de muerte (Natural, Homicidio, Accidente...) sin espacios sobrantes
    if "MANERA_MUERTE" in df.columns:
        df["MANERA_MUERTE"] = df["MANERA_MUERTE"].astype("string").str.strip()
    return df


def cargar_divipola(ruta=config.ARCHIVO_DIVIPOLA) -> pd.DataFrame:
    """Lee Divipola.xlsx: catálogo de departamentos y municipios."""
    df = leer_excel_detectando_encabezado(ruta, "MUNICIPIO")
    df = normalizar_columnas(df)

    col_depto = buscar_columna(df, "COD_DEPARTAMENTO", "COD_DPTO", "CODIGO_DEPARTAMENTO")
    col_nom_depto = next(c for c in df.columns if "DEPARTAMENTO" in c and "COD" not in c)
    col_nom_mpio = next(c for c in df.columns if "MUNICIPIO" in c and "COD" not in c)

    salida = pd.DataFrame({
        "COD_DEPARTAMENTO": codigo_con_ceros(df[col_depto], 2),
        "DEPARTAMENTO": nombre_bonito(df[col_nom_depto]),
        "MUNICIPIO": nombre_bonito(df[col_nom_mpio]),
    })
    if "COD_DANE" in df.columns:
        salida["COD_DANE"] = codigo_con_ceros(df["COD_DANE"], 5)
    else:
        col_mpio = buscar_columna(df, "COD_MUNICIPIO", "COD_MPIO")
        salida["COD_DANE"] = salida["COD_DEPARTAMENTO"] + codigo_con_ceros(df[col_mpio], 3)

    # Nombre corto para San Andrés (el oficial es muy largo para los ejes)
    salida.loc[salida["DEPARTAMENTO"].str.contains("San Andr", na=False), "DEPARTAMENTO"] = "San Andrés y Providencia"

    # Un municipio debe aparecer una sola vez; si no, el merge duplicaría muertes
    return salida.dropna(subset=["COD_DANE"]).drop_duplicates("COD_DANE")


def cargar_codigos_muerte(ruta=config.ARCHIVO_CODIGOS) -> pd.DataFrame:
    """Lee CodigosDeMuerte.xlsx (CIE-10) y deja: COD_MUERTE -> CAUSA."""
    df = leer_excel_detectando_encabezado(ruta, "CUATRO")
    df = normalizar_columnas(df)

    col_cod4 = buscar_columna(df, "CODIGO CUATRO", "CODIGO 4")
    col_des4 = buscar_columna(df, "DESCRIPCION CUATRO", "DESCRIPCION 4")
    col_cod3 = buscar_columna(df, "CODIGO TRES", "CODIGO 3", obligatoria=False)
    col_des3 = buscar_columna(df, "DESCRIPCION TRES", "DESCRIPCION 3", obligatoria=False)

    causas = pd.DataFrame({
        "COD_MUERTE": limpiar_codigo_cie10(df[col_cod4]),
        "CAUSA": df[col_des4].astype("string").str.strip(),
    })
    if col_cod3 and col_des3:
        causas["COD_3"] = limpiar_codigo_cie10(df[col_cod3])
        causas["CAUSA_3"] = df[col_des3].astype("string").str.strip()
    return causas.dropna(subset=["COD_MUERTE"]).drop_duplicates("COD_MUERTE")


# ---------------------------------------------------------------------------
# Variables derivadas
# ---------------------------------------------------------------------------
def clasificar_grupo_edad(codigo) -> str:
    """Traduce un código GRUPO_EDAD1 (0-29) a su categoría del ciclo de vida."""
    if pd.isna(codigo):
        return "Edad desconocida"
    for minimo, maximo, categoria, _rango in config.GRUPOS_EDAD:
        if minimo <= int(codigo) <= maximo:
            return categoria
    return "Edad desconocida"  # códigos fuera de 0-29 se tratan como desconocidos


def integrar_datos(mortalidad, divipola, causas) -> pd.DataFrame:
    """Une las tres fuentes y crea las columnas que necesitan los gráficos."""
    # 1) Nombres de municipio y departamento (LEFT join: no se pierde ninguna muerte)
    df = mortalidad.merge(
        divipola[["COD_DANE", "MUNICIPIO"]], on="COD_DANE", how="left", validate="m:1"
    )
    deptos = divipola.drop_duplicates("COD_DEPARTAMENTO")[["COD_DEPARTAMENTO", "DEPARTAMENTO"]]
    df = df.merge(deptos, on="COD_DEPARTAMENTO", how="left", validate="m:1")

    # 2) Descripción de la causa de muerte (código de 4 caracteres)
    df = df.merge(causas[["COD_MUERTE", "CAUSA"]], on="COD_MUERTE", how="left", validate="m:1")
    if "COD_3" in causas.columns:  # respaldo: si no hay match de 4, usar el de 3
        tres = causas.drop_duplicates("COD_3").set_index("COD_3")["CAUSA_3"]
        faltan = df["CAUSA"].isna()
        df.loc[faltan, "CAUSA"] = df.loc[faltan, "COD_MUERTE"].str[:3].map(tres)
    df["CAUSA"] = df["CAUSA"].fillna("Código sin descripción")

    # 3) Etiquetas legibles
    df["SEXO_TXT"] = df["SEXO"].map(config.SEXO).fillna("Indeterminado")
    df["GRUPO_EDAD"] = df["GRUPO_EDAD1"].map(clasificar_grupo_edad)
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].fillna("Sin información")
    df["MUNICIPIO"] = df["MUNICIPIO"].fillna("Sin información")

    # 4) Bandera de homicidio según la CIE-10 (X85-Y09 por defecto)
    df["ES_HOMICIDIO"] = df["COD_MUERTE"].str[:3].isin(config.PREFIJOS_HOMICIDIO).fillna(False)

    columnas = [
        "COD_DANE", "COD_DEPARTAMENTO", "DEPARTAMENTO", "MUNICIPIO", "MES",
        "SEXO", "SEXO_TXT", "GRUPO_EDAD1", "GRUPO_EDAD", "COD_MUERTE", "CAUSA",
        "ES_HOMICIDIO",
    ]
    return df[columnas]


# ---------------------------------------------------------------------------
# Punto de entrada usado por la aplicación
# ---------------------------------------------------------------------------
def cargar_datos() -> pd.DataFrame:
    """Devuelve el DataFrame integrado.

    Si existe el archivo procesado (data/procesado/defunciones_2019.csv.gz)
    lo usa, porque carga en segundos. Si no, procesa los Excel originales.
    """
    if config.ARCHIVO_PROCESADO.exists():
        df = pd.read_csv(
            config.ARCHIVO_PROCESADO,
            dtype={"COD_DANE": "string", "COD_DEPARTAMENTO": "string", "COD_MUERTE": "string"},
        )
    else:
        df = integrar_datos(cargar_mortalidad(), cargar_divipola(), cargar_codigos_muerte())

    # Tipo "category" = menos memoria (importante en planes gratuitos de 512 MB)
    for col in ["DEPARTAMENTO", "MUNICIPIO", "SEXO_TXT", "GRUPO_EDAD", "CAUSA"]:
        df[col] = df[col].astype("category")
    return df