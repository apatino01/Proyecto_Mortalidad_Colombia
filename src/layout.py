"""
layout.py
---------
Fase 7 (parte visual): ESTRUCTURA DE LA PÁGINA.

En Dash, el "layout" es un árbol de componentes:
    html.*  -> etiquetas HTML (Div, H1, P...)            -> estructura y texto
    dcc.*   -> componentes interactivos (Graph, Dropdown) -> gráficos y filtros
    dash_table.DataTable -> tablas
Los estilos (colores, tarjetas, cuadrícula) están en assets/style.css,
que Dash carga automáticamente.
"""

from dash import dash_table, dcc, html


def tarjeta_indicador(id_valor: str, titulo: str, clase_extra: str = "") -> html.Div:
    """Tarjeta pequeña con un número grande (KPI)."""
    return html.Div(
        className=f"kpi {clase_extra}",
        children=[html.P(titulo, className="kpi-titulo"), html.H3("–", id=id_valor, className="kpi-valor")],
    )


def tarjeta_grafico(id_grafico: str, descripcion: str, ancho: str = "mitad") -> html.Div:
    """Contenedor blanco con un gráfico y una frase que explica qué responde."""
    return html.Div(
        className=f"tarjeta {ancho}",
        children=[
            dcc.Loading(dcc.Graph(id=id_grafico, config={"displaylogo": False}), type="circle"),
            html.P(descripcion, className="nota"),
        ],
    )


def crear_layout(departamentos: list[str]) -> html.Div:
    opciones_depto = [{"label": "Todos los departamentos", "value": "TODOS"}] + [
        {"label": d, "value": d} for d in departamentos
    ]
    return html.Div(
        className="contenedor",
        children=[
            # ---------------- Encabezado ----------------
            html.Header(
                className="encabezado",
                children=[
                    html.H1("Mortalidad en Colombia, 2019"),
                    html.P(
                        "Análisis interactivo de las defunciones no fetales registradas por el DANE. "
                        "Use los filtros para explorar por departamento y sexo."
                    ),
                ],
            ),
            # ---------------- Filtros ----------------
            html.Section(
                className="filtros",
                children=[
                    html.Div([
                        html.Label("Departamento", htmlFor="filtro-departamento"),
                        dcc.Dropdown(id="filtro-departamento", options=opciones_depto,
                                     value="TODOS", clearable=False),
                    ], className="filtro"),
                    html.Div([
                        html.Label("Sexo"),
                        dcc.RadioItems(
                            id="filtro-sexo",
                            options=[{"label": " Todos", "value": "TODOS"},
                                     {"label": " Hombre", "value": "Hombre"},
                                     {"label": " Mujer", "value": "Mujer"}],
                            value="TODOS", inline=True, className="radio",
                        ),
                    ], className="filtro"),
                ],
            ),
            # ---------------- Indicadores ----------------
            html.Section(
                className="kpis",
                children=[
                    tarjeta_indicador("kpi-total", "Muertes registradas"),
                    tarjeta_indicador("kpi-homicidios", "Homicidios"),
                    tarjeta_indicador("kpi-mes", "Mes con más muertes"),
                    tarjeta_indicador("kpi-causa", "Causa más frecuente", "kpi-texto"),
                ],
            ),
            # ---------------- Gráficos ----------------
            html.Section(
                className="cuadricula",
                children=[
                    tarjeta_grafico("grafico-mapa",
                                    "¿Dónde se concentran las muertes? El mapa muestra el total por departamento "
                                    "(no depende del filtro de departamento).", "mitad"),
                    tarjeta_grafico("grafico-mensual",
                                    "¿Cómo varía la mortalidad durante el año? Total de muertes en cada mes.", "mitad"),
                    tarjeta_grafico("grafico-homicidios",
                                    "¿Qué ciudades concentran más homicidios? Agresiones CIE-10 X85–Y09.", "mitad"),
                    tarjeta_grafico("grafico-menor",
                                    "¿Qué ciudades registran menos muertes? Cifras absolutas, no tasas.", "mitad"),
                    html.Div(
                        className="tarjeta completo",
                        children=[
                            html.H4("10 principales causas de muerte"),
                            dash_table.DataTable(
                                id="tabla-causas",
                                columns=[
                                    {"name": "#", "id": "POSICION"},
                                    {"name": "Código CIE-10", "id": "COD_MUERTE"},
                                    {"name": "Causa", "id": "CAUSA"},
                                    {"name": "Muertes", "id": "TOTAL", "type": "numeric",
                                     "format": {"specifier": ",d", "locale": {"group": ".", "decimal": ","}}},
                                    {"name": "% del total", "id": "PORCENTAJE", "type": "numeric",
                                     "format": {"specifier": ".2f", "locale": {"group": ".", "decimal": ","}}},
                                ],
                                style_table={"overflowX": "auto"},
                                style_cell={"textAlign": "left", "padding": "8px",
                                            "fontFamily": "Segoe UI, Roboto, Arial, sans-serif", "whiteSpace": "normal"},
                                style_header={"backgroundColor": "#1f4e79", "color": "white",
                                              "fontWeight": "bold"},
                                style_data_conditional=[
                                    {"if": {"row_index": "odd"}, "backgroundColor": "#f5f8fb"}
                                ],
                                sort_action="native",
                            ),
                        ],
                    ),
                    tarjeta_grafico("grafico-sexo",
                                    "¿Cómo se reparten las muertes entre hombres y mujeres en cada departamento?",
                                    "completo"),
                    tarjeta_grafico("grafico-edad",
                                    "¿En qué etapa del ciclo de vida ocurren más muertes? GRUPO_EDAD1 agrupado "
                                    "según la tabla de referencia.", "completo"),
                ],
            ),
            html.Footer(
                "Fuente: DANE, Estadísticas Vitales 2019 (defunciones no fetales), "
                "Clasificación CIE-10 y DIVIPOLA.",
                className="pie",
            ),
        ],
    )