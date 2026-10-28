"""
app.py
------
Punto de entrada de la aplicación Dash.

Ejecutar en tu computador:
    python app.py           -> abre http://127.0.0.1:8050

En Render / Railway se ejecuta con gunicorn:
    gunicorn app:server     -> "app" es este archivo, "server" la variable de abajo
"""

import os

from dash import Dash, Input, Output

from src import analisis, graficos
from src.carga_datos import cargar_datos
from src.layout import crear_layout

# ---------------------------------------------------------------------------
# 1. Cargar los datos UNA sola vez, al iniciar el servidor
# ---------------------------------------------------------------------------
# Si se cargaran dentro del callback, se leerían en cada clic: lentísimo.
DF = cargar_datos()
DEPARTAMENTOS = sorted(d for d in DF["DEPARTAMENTO"].astype(str).unique() if d != "Sin información")

# ---------------------------------------------------------------------------
# 2. Crear la aplicación
# ---------------------------------------------------------------------------
app = Dash(__name__, title="Mortalidad Colombia 2019")
server = app.server            # objeto Flask que usa gunicorn en el despliegue
app.layout = crear_layout(DEPARTAMENTOS)


# ---------------------------------------------------------------------------
# 3. Callback: cuando cambia un filtro, se recalculan gráficos e indicadores
# ---------------------------------------------------------------------------
# Input  = propiedad que, al cambiar, dispara la función (el valor del filtro)
# Output = propiedad que la función actualiza (la figura de cada gráfico)
# El orden de los valores retornados debe coincidir con el orden de los Output.
@app.callback(
    Output("grafico-mapa", "figure"),
    Output("grafico-mensual", "figure"),
    Output("grafico-homicidios", "figure"),
    Output("grafico-menor", "figure"),
    Output("tabla-causas", "data"),
    Output("grafico-sexo", "figure"),
    Output("grafico-edad", "figure"),
    Output("kpi-total", "children"),
    Output("kpi-homicidios", "children"),
    Output("kpi-mes", "children"),
    Output("kpi-causa", "children"),
    Input("filtro-departamento", "value"),
    Input("filtro-sexo", "value"),
)
def actualizar(departamento, sexo):
    # a) Filtro por sexo: afecta a TODOS los gráficos
    datos = DF if sexo == "TODOS" else DF[DF["SEXO_TXT"] == sexo]
    # b) Filtro por departamento: no se aplica al mapa ni a las barras por
    #    departamento, porque esos gráficos comparan departamentos entre sí.
    datos_depto = datos if departamento == "TODOS" else datos[datos["DEPARTAMENTO"] == departamento]

    mensual = analisis.muertes_por_mes(datos_depto)
    causas = analisis.top_causas(datos_depto, 10)

    # Indicadores (KPI). f"{n:,}" pone separador de miles: 1,234 -> lo
    # cambiamos a punto (formato colombiano) con replace.
    total = f"{len(datos_depto):,}".replace(",", ".")
    homicidios = f"{int(datos_depto['ES_HOMICIDIO'].sum()):,}".replace(",", ".")
    mes_max = mensual.loc[mensual["TOTAL"].idxmax(), "MES_TXT"] if len(datos_depto) else "–"
    causa_max = causas.iloc[0]["CAUSA"] if not causas.empty else "–"

    return (
        graficos.mapa_departamentos(analisis.muertes_por_departamento(datos)),
        graficos.linea_mensual(mensual),
        graficos.barras_homicidios(analisis.top_ciudades_homicidios(datos_depto, 5)),
        graficos.circular_menor_mortalidad(analisis.ciudades_menor_mortalidad(datos_depto, 10)),
        causas.to_dict("records"),
        graficos.barras_apiladas_sexo(analisis.muertes_sexo_departamento(datos)),
        graficos.histograma_edad(analisis.distribucion_grupo_edad(datos_depto)),
        total, homicidios, mes_max, causa_max,
    )


# ---------------------------------------------------------------------------
# 4. Ejecutar en modo local
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Solo se usa en tu computador. En Render/Railway arranca gunicorn (Procfile)
    # y este bloque no se ejecuta. 127.0.0.1 = "este mismo computador".
    puerto = int(os.environ.get("PORT", 8050))
    app.run(debug=True, host="127.0.0.1", port=puerto)