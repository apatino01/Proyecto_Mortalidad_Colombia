"""
verificar_proyecto.py
---------------------
Prueba automática del proyecto completo. Revisa, en orden:
    1. Versión de Python y librerías instaladas.
    2. Que existan todos los archivos y carpetas.
    3. Que los datos carguen y crucen correctamente.
    4. Que las cifras clave coincidan con las esperadas para 2019.
    5. Que los 7 gráficos se construyan sin errores.
    6. Que la aplicación Dash arranque y el callback responda.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python -m src.verificar_proyecto

Al final muestra cuántas pruebas pasaron. Si alguna falla, el mensaje dice
qué revisar.
"""

import sys
from importlib import metadata

from src import config

resultados = []   # lista de (nombre de la prueba, ¿pasó?, detalle)


def prueba(nombre, condicion, detalle=""):
    """Registra una prueba y la imprime con un símbolo de OK o FALLA."""
    resultados.append((nombre, bool(condicion), detalle))
    simbolo = "OK   " if condicion else "FALLA"
    print(f"  [{simbolo}] {nombre}" + (f"  ->  {detalle}" if detalle else ""))


def main():
    # ------------------------------------------------------------------
    print("\n1. Entorno")
    version = sys.version_info
    prueba("Python 3.11 o superior", version >= (3, 11), f"Python {version.major}.{version.minor}.{version.micro}")
    for libreria in ["dash", "plotly", "pandas", "openpyxl"]:
        try:
            prueba(f"Librería {libreria} instalada", True, metadata.version(libreria))
        except metadata.PackageNotFoundError:
            prueba(f"Librería {libreria} instalada", False, "ejecute: pip install -r requirements.txt")

    # ------------------------------------------------------------------
    print("\n2. Estructura de archivos")
    obligatorios = [
        "app.py", "requirements.txt", "README.md", "Procfile", ".python-version", ".gitignore",
        "assets/style.css", "src/__init__.py", "src/config.py", "src/carga_datos.py",
        "src/preparar_datos.py", "src/analisis.py", "src/graficos.py", "src/layout.py",
        "notebooks", "docs",
    ]
    for ruta in obligatorios:
        prueba(f"Existe {ruta}", (config.RAIZ / ruta).exists())
    for archivo in [config.ARCHIVO_MORTALIDAD, config.ARCHIVO_CODIGOS, config.ARCHIVO_DIVIPOLA]:
        prueba(f"Existe data/{archivo.name}", archivo.exists(), "" if archivo.exists() else "copie el Excel a data/")
    prueba("Existe el archivo procesado", config.ARCHIVO_PROCESADO.exists(),
           "" if config.ARCHIVO_PROCESADO.exists() else "ejecute: python -m src.preparar_datos")
    if not config.ARCHIVO_PROCESADO.exists():
        return

    # ------------------------------------------------------------------
    print("\n3. Datos")
    from src import analisis
    from src.carga_datos import cargar_datos

    df = cargar_datos()
    total = len(df)
    prueba("Total de defunciones = 244.355", total == 244_355, f"{total:,}".replace(",", "."))
    prueba("Todas cruzan con un municipio", (df["MUNICIPIO"] == "Sin información").sum() == 0)
    prueba("Todas tienen descripción de causa", (df["CAUSA"] == "Código sin descripción").sum() == 0)
    prueba("Los 12 meses suman el total", analisis.muertes_por_mes(df)["TOTAL"].sum() == total)
    prueba("Los departamentos suman el total", analisis.muertes_por_departamento(df)["TOTAL"].sum() == total)
    prueba("Los grupos de edad suman el total", analisis.distribucion_grupo_edad(df)["TOTAL"].sum() == total)
    prueba("Sexo x departamento suma el total", analisis.muertes_sexo_departamento(df)["TOTAL"].sum() == total)

    # ------------------------------------------------------------------
    print("\n4. Cifras clave (datos DANE 2019)")
    homicidios = int(df["ES_HOMICIDIO"].sum())
    prueba("Homicidios X85-Y09 = 13.043", homicidios == 13_043, f"{homicidios:,}".replace(",", "."))
    causas = analisis.top_causas(df)
    prueba("Primera causa = I219 (35.088)",
           causas.iloc[0]["COD_MUERTE"] == "I219" and causas.iloc[0]["TOTAL"] == 35_088,
           f"{causas.iloc[0]['COD_MUERTE']} ({causas.iloc[0]['TOTAL']})")
    ciudades = analisis.top_ciudades_homicidios(df)
    prueba("Ciudad con más homicidios = Cali (1.239)",
           ciudades.iloc[0]["COD_DANE"] == "76001" and ciudades.iloc[0]["TOTAL"] == 1_239,
           f"{ciudades.iloc[0]['MUNICIPIO']} ({ciudades.iloc[0]['TOTAL']})")
    menores = analisis.ciudades_menor_mortalidad(df)
    prueba("10 ciudades de menor mortalidad, todas con 1 muerte",
           len(menores) == 10 and (menores["TOTAL"] == 1).all())
    mensual = analisis.muertes_por_mes(df)
    mes_max = mensual.loc[mensual["TOTAL"].idxmax(), "MES_TXT"]
    prueba("Mes con más muertes = Dic", mes_max == "Dic", mes_max)

    # ------------------------------------------------------------------
    print("\n5. Gráficos")
    from src import graficos

    figuras = {
        "Mapa por departamento": lambda: graficos.mapa_departamentos(analisis.muertes_por_departamento(df)),
        "Línea mensual": lambda: graficos.linea_mensual(mensual),
        "Barras de homicidios": lambda: graficos.barras_homicidios(ciudades),
        "Circular menor mortalidad": lambda: graficos.circular_menor_mortalidad(menores),
        "Barras apiladas por sexo": lambda: graficos.barras_apiladas_sexo(analisis.muertes_sexo_departamento(df)),
        "Histograma por edad": lambda: graficos.histograma_edad(analisis.distribucion_grupo_edad(df)),
    }
    for nombre, construir in figuras.items():
        try:
            figura = construir()
            prueba(f"Se construye: {nombre}", len(figura.data) > 0)
        except Exception as error:  # muestra el error sin detener las demás pruebas
            prueba(f"Se construye: {nombre}", False, repr(error))
    prueba("Tabla de 10 causas", len(causas) == 10)

    # ------------------------------------------------------------------
    print("\n6. Aplicación Dash")
    try:
        import app as aplicacion

        salida = aplicacion.actualizar("TODOS", "TODOS")
        prueba("El callback devuelve 11 salidas", len(salida) == 11)
        salida = aplicacion.actualizar("Antioquia", "Mujer")
        prueba("Filtro Antioquia + Mujer = 15.481 muertes", salida[7] == "15.481", salida[7])
        cliente = aplicacion.server.test_client()
        prueba("La página principal responde (HTTP 200)", cliente.get("/").status_code == 200)
    except Exception as error:
        prueba("La aplicación arranca", False, repr(error))


if __name__ == "__main__":
    print("Verificación del proyecto Mortalidad Colombia 2019")
    main()
    aprobadas = sum(1 for _, ok, _ in resultados if ok)
    print(f"\nResultado: {aprobadas} de {len(resultados)} pruebas aprobadas.")
    if aprobadas < len(resultados):
        print("Revise las líneas marcadas con FALLA.")
        sys.exit(1)
    print("El proyecto está completo y funciona correctamente.")