"""
analisis.py
-----------
Fase 5: ANÁLISIS EXPLORATORIO. Cada función recibe el DataFrame integrado
(o una parte filtrada) y devuelve una tabla pequeña y agregada, lista para
graficar.

Separar "calcular" (este archivo) de "dibujar" (graficos.py) permite
verificar los números en un notebook sin tener que abrir la aplicación.

Nota: observed=True en groupby evita que pandas cree filas vacías para
categorías que no aparecen en el filtro actual.
"""

import pandas as pd

from src import config


def _etiqueta_ciudad(tabla: pd.DataFrame) -> pd.Series:
    """'Barbosa (Antioquia)': hay municipios con el mismo nombre en
    departamentos distintos, así que se agrega el departamento."""
    return tabla["MUNICIPIO"].astype(str) + " (" + tabla["DEPARTAMENTO"].astype(str) + ")"


def muertes_por_departamento(df: pd.DataFrame) -> pd.DataFrame:
    """Total de muertes por departamento (para el mapa)."""
    return (
        df.groupby(["COD_DEPARTAMENTO", "DEPARTAMENTO"], observed=True)
        .size()                                  # cuenta filas = muertes
        .reset_index(name="TOTAL")
        .sort_values("TOTAL", ascending=False)
    )


def muertes_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Total de muertes por mes, con los 12 meses aunque alguno tenga 0."""
    conteo = df.groupby("MES").size()
    conteo = conteo.reindex(range(1, 13), fill_value=0)   # garantiza ene..dic
    tabla = conteo.rename_axis("MES").reset_index(name="TOTAL")
    tabla["MES_TXT"] = tabla["MES"].map(config.MESES)
    return tabla


def top_ciudades_homicidios(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Las n ciudades (municipios) con más homicidios."""
    homicidios = df[df["ES_HOMICIDIO"]]
    tabla = (
        homicidios.groupby(["COD_DANE", "MUNICIPIO", "DEPARTAMENTO"], observed=True)
        .size()
        .reset_index(name="TOTAL")
        .nlargest(n, "TOTAL")
    )
    tabla["CIUDAD"] = _etiqueta_ciudad(tabla)
    return tabla


def ciudades_menor_mortalidad(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Las n ciudades con MENOS muertes registradas (mínimo 1).

    Hay muchos empates (varios municipios con 1 muerte); para que el
    resultado sea reproducible se desempata por nombre alfabético.
    """
    todas = (
        df[df["MUNICIPIO"] != "Sin información"]
        .groupby(["COD_DANE", "MUNICIPIO", "DEPARTAMENTO"], observed=True)
        .size()
        .reset_index(name="TOTAL")
        .sort_values(["TOTAL", "MUNICIPIO"], ascending=[True, True])
    )
    tabla = todas.head(n).copy()
    tabla["CIUDAD"] = _etiqueta_ciudad(tabla)
    # Cuántos municipios comparten el valor del último puesto (para avisarlo en el gráfico).
    # Con los datos de 2019: 13 municipios tienen 1 sola muerte, así que el top 10 es un empate.
    if not tabla.empty:
        tabla.attrs["empatados"] = int((todas["TOTAL"] == tabla["TOTAL"].iloc[-1]).sum())
    return tabla


def top_causas(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Las n causas de muerte más frecuentes (código CIE-10 de 4 caracteres)."""
    tabla = (
        df.groupby(["COD_MUERTE", "CAUSA"], observed=True)
        .size()
        .reset_index(name="TOTAL")
        .nlargest(n, "TOTAL")
    )
    tabla["PORCENTAJE"] = (tabla["TOTAL"] / len(df) * 100).round(2)
    tabla.insert(0, "POSICION", range(1, len(tabla) + 1))
    return tabla


def muertes_sexo_departamento(df: pd.DataFrame) -> pd.DataFrame:
    """Muertes por departamento y sexo (formato largo, para barras apiladas)."""
    tabla = (
        df.groupby(["DEPARTAMENTO", "SEXO_TXT"], observed=True)
        .size()
        .reset_index(name="TOTAL")
    )
    # Ordenar departamentos por su total, para que el gráfico se lea de mayor a menor
    orden = tabla.groupby("DEPARTAMENTO", observed=True)["TOTAL"].sum().sort_values(ascending=False)
    tabla["DEPARTAMENTO"] = pd.Categorical(tabla["DEPARTAMENTO"].astype(str), categories=orden.index.astype(str))
    return tabla.sort_values("DEPARTAMENTO")


def distribucion_grupo_edad(df: pd.DataFrame) -> pd.DataFrame:
    """Muertes por categoría del ciclo de vida, en el orden de la tabla oficial."""
    conteo = df.groupby("GRUPO_EDAD", observed=True).size()
    conteo = conteo.reindex(config.ORDEN_GRUPOS_EDAD, fill_value=0)
    tabla = conteo.rename_axis("GRUPO_EDAD").reset_index(name="TOTAL")
    rangos = {g[2]: g[3] for g in config.GRUPOS_EDAD}
    codigos = {g[2]: f"{g[0]}–{g[1]}" if g[0] != g[1] else str(g[0]) for g in config.GRUPOS_EDAD}
    tabla["RANGO"] = tabla["GRUPO_EDAD"].map(rangos)
    tabla["CODIGOS"] = tabla["GRUPO_EDAD"].map(codigos)
    tabla["PORCENTAJE"] = (tabla["TOTAL"] / max(tabla["TOTAL"].sum(), 1) * 100).round(2)
    return tabla