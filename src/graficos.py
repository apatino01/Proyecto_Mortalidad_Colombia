"""
graficos.py
-----------
Fase 6: CONSTRUCCIÓN DE LAS VISUALIZACIONES con Plotly Express (px).

Cada función recibe una tabla YA AGREGADA (de analisis.py) y devuelve una
figura (go.Figure). Así los gráficos son livianos: al navegador viajan
decenas de filas, no cientos de miles.
"""

import json
import urllib.request
from functools import lru_cache

import plotly.express as px
import plotly.graph_objects as go

from src import config

# Formato común para todas las figuras: misma fuente, márgenes y plantilla
def _estilo(fig: go.Figure, titulo: str) -> go.Figure:
    fig.update_layout(
        title={"text": titulo, "x": 0.01, "font": {"size": 16}},
        template=config.PLANTILLA_GRAFICOS,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        font={"family": "Segoe UI, Roboto, Arial, sans-serif", "size": 12},
        separators=",.",          # formato colombiano: 1.234,5
        hoverlabel={"bgcolor": "white"},
    )
    return fig


def figura_vacia(mensaje: str = "No hay datos para este filtro") -> go.Figure:
    """Figura con un mensaje, para cuando un filtro deja la tabla vacía."""
    fig = go.Figure()
    fig.add_annotation(text=mensaje, showarrow=False, font={"size": 14})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _estilo(fig, "")


# ---------------------------------------------------------------------------
# 1. Mapa de muertes por departamento
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)          # se descarga/lee una sola vez y queda en memoria
def cargar_geojson():
    """Devuelve el GeoJSON de departamentos o None si no está disponible."""
    if config.ARCHIVO_GEOJSON.exists():
        with open(config.ARCHIVO_GEOJSON, encoding="utf-8") as f:
            return json.load(f)
    try:
        with urllib.request.urlopen(config.URL_GEOJSON, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:          # sin internet o URL caída -> mapa de burbujas
        return None


def mapa_departamentos(tabla) -> go.Figure:
    if tabla.empty:
        return figura_vacia()
    geojson = cargar_geojson()
    if geojson is not None:
        # Coropleta: cada departamento se colorea según su número de muertes.
        # featureidkey indica DÓNDE está el código dentro del GeoJSON.
        fig = px.choropleth(
            tabla,
            geojson=geojson,
            locations="COD_DEPARTAMENTO",
            featureidkey=f"properties.{config.PROPIEDAD_CODIGO_GEOJSON}",
            color="TOTAL",
            color_continuous_scale="Reds",
            hover_name="DEPARTAMENTO",
            hover_data={"COD_DEPARTAMENTO": False, "TOTAL": ":,"},
            labels={"TOTAL": "Muertes"},
        )
        # Encuadre fijo sobre Colombia continental + San Andrés, proyección Mercator
        fig.update_geos(visible=False, projection_type="mercator",
                        lonaxis_range=[-82, -66.5], lataxis_range=[-4.5, 13.5])
    else:
        # Respaldo: una burbuja por departamento, ubicada en su capital
        tabla = tabla.copy()
        tabla["LAT"] = tabla["COD_DEPARTAMENTO"].map(lambda c: config.COORDENADAS_DEPARTAMENTOS.get(c, (None, None))[0])
        tabla["LON"] = tabla["COD_DEPARTAMENTO"].map(lambda c: config.COORDENADAS_DEPARTAMENTOS.get(c, (None, None))[1])
        fig = px.scatter_geo(
            tabla.dropna(subset=["LAT"]), lat="LAT", lon="LON", size="TOTAL",
            color="TOTAL", color_continuous_scale="Reds", hover_name="DEPARTAMENTO",
            hover_data={"LAT": False, "LON": False, "TOTAL": ":,"}, size_max=45,
            labels={"TOTAL": "Muertes"},
        )
        fig.update_geos(fitbounds="locations", showcountries=True, showland=True, landcolor="#f2f2f2")
    fig = _estilo(fig, "Muertes por departamento")
    fig.update_layout(height=520)
    return fig


# ---------------------------------------------------------------------------
# 2. Línea de mortalidad mensual
# ---------------------------------------------------------------------------
def linea_mensual(tabla) -> go.Figure:
    if tabla["TOTAL"].sum() == 0:
        return figura_vacia()
    fig = px.line(
        tabla, x="MES_TXT", y="TOTAL", markers=True,
        labels={"MES_TXT": "Mes", "TOTAL": "Muertes"},
        color_discrete_sequence=[config.COLOR_PRINCIPAL],
    )
    fig.update_traces(hovertemplate="%{x}: %{y:,} muertes<extra></extra>")
    fig.update_yaxes(rangemode="tozero")   # el eje Y empieza en 0: no exagera cambios
    return _estilo(fig, "Muertes por mes, 2019")


# ---------------------------------------------------------------------------
# 3. Barras: 5 ciudades con más homicidios
# ---------------------------------------------------------------------------
def barras_homicidios(tabla) -> go.Figure:
    if tabla.empty:
        return figura_vacia("No hay homicidios para este filtro")
    fig = px.bar(
        tabla.sort_values("TOTAL"),           # orden ascendente: la mayor queda arriba
        x="TOTAL", y="CIUDAD", orientation="h", text="TOTAL",
        labels={"TOTAL": "Homicidios", "CIUDAD": ""},
        color_discrete_sequence=[config.COLOR_SECUNDARIO],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}: %{x:,} homicidios<extra></extra>")
    # 15 % de espacio extra a la derecha para que la etiqueta no se corte
    fig.update_xaxes(range=[0, tabla["TOTAL"].max() * 1.15])
    return _estilo(fig, "5 ciudades con más homicidios (CIE-10 X85–Y09)")


# ---------------------------------------------------------------------------
# 4. Circular: 10 ciudades con menor mortalidad
# ---------------------------------------------------------------------------
def circular_menor_mortalidad(tabla) -> go.Figure:
    if tabla.empty:
        return figura_vacia()
    fig = px.pie(
        tabla, names="CIUDAD", values="TOTAL", hole=0.35,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_traces(textinfo="value", hovertemplate="%{label}: %{value:,} muertes<extra></extra>")
    titulo = "10 ciudades con menor mortalidad"
    empatados = tabla.attrs.get("empatados", 0)
    if empatados > (tabla["TOTAL"] == tabla["TOTAL"].iloc[-1]).sum():
        # Hay más municipios con el mismo valor que puestos disponibles: se avisa
        titulo += (f"<br><sup>{empatados} municipios empatan con {tabla['TOTAL'].iloc[-1]} "
                   f"muerte(s); se muestran los 10 primeros en orden alfabético</sup>")
    fig = _estilo(fig, titulo)
    # Leyenda debajo del círculo: así el gráfico conserva su tamaño
    fig.update_layout(height=480, legend={"font": {"size": 10}, "orientation": "h", "y": -0.05})
    return fig


# ---------------------------------------------------------------------------
# 6. Barras apiladas por sexo y departamento
# ---------------------------------------------------------------------------
def barras_apiladas_sexo(tabla) -> go.Figure:
    if tabla.empty:
        return figura_vacia()
    fig = px.bar(
        tabla, x="DEPARTAMENTO", y="TOTAL", color="SEXO_TXT",
        barmode="stack",                       # apiladas: la altura total = muertes del depto
        color_discrete_map=config.COLORES_SEXO,
        category_orders={"SEXO_TXT": ["Hombre", "Mujer", "Indeterminado"]},
        labels={"DEPARTAMENTO": "", "TOTAL": "Muertes", "SEXO_TXT": "Sexo"},
    )
    fig.update_traces(hovertemplate="%{x}<br>%{y:,} muertes<extra></extra>")
    fig.update_xaxes(tickangle=-45)
    fig = _estilo(fig, "Muertes por sexo en cada departamento")
    fig.update_layout(height=520, legend={"orientation": "h", "y": 1.08, "x": 0.6})
    return fig


# ---------------------------------------------------------------------------
# 7. Histograma por grupo de edad (ciclo de vida)
# ---------------------------------------------------------------------------
def histograma_edad(tabla) -> go.Figure:
    if tabla["TOTAL"].sum() == 0:
        return figura_vacia()
    # px.histogram con histfunc="sum" suma la columna TOTAL dentro de cada
    # categoría. Como la tabla ya trae un renglón por categoría, el
    # resultado es la frecuencia de muertes por grupo de edad.
    fig = px.histogram(
        tabla, x="GRUPO_EDAD", y="TOTAL", histfunc="sum",
        category_orders={"GRUPO_EDAD": config.ORDEN_GRUPOS_EDAD},
        labels={"GRUPO_EDAD": "Grupo de edad", "TOTAL": "Muertes"},
        color_discrete_sequence=[config.COLOR_PRINCIPAL],
    )
    fig.update_traces(hovertemplate="%{x}<br>%{y:,} muertes<extra></extra>")
    fig.update_layout(bargap=0.05, yaxis_title="Muertes")
    fig.update_xaxes(tickangle=-30)
    return _estilo(fig, "Distribución de muertes por grupo de edad")