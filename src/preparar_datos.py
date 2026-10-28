"""
preparar_datos.py
-----------------
Ejecuta UNA VEZ la limpieza e integración y guarda el resultado en
data/procesado/defunciones_2019.csv.gz.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python -m src.preparar_datos

¿Por qué? Leer tres Excel grandes tarda y consume mucha memoria. En el
servidor gratuito (Render/Railway) eso puede hacer que la app no arranque
a tiempo. Un CSV comprimido ya limpio carga en pocos segundos.
"""

from src import config
from src.carga_datos import (
    cargar_codigos_muerte,
    cargar_divipola,
    cargar_mortalidad,
    integrar_datos,
)


def main():
    print("1/4 Leyendo NoFetal2019.xlsx ...")
    mortalidad = cargar_mortalidad()
    print(f"    {len(mortalidad):,} defunciones, {mortalidad.shape[1]} columnas")

    print("2/4 Leyendo Divipola.xlsx y CodigosDeMuerte.xlsx ...")
    divipola = cargar_divipola()
    causas = cargar_codigos_muerte()
    print(f"    {len(divipola):,} municipios, {len(causas):,} códigos CIE-10")

    print("3/4 Integrando ...")
    df = integrar_datos(mortalidad, divipola, causas)
    assert len(df) == len(mortalidad), "El merge cambió el número de filas: revisa duplicados"

    # Reporte de calidad: cuántas filas no encontraron su par en cada catálogo
    sin_municipio = (df["MUNICIPIO"] == "Sin información").sum()
    sin_causa = (df["CAUSA"] == "Código sin descripción").sum()
    print(f"    Sin municipio en Divipola: {sin_municipio:,}")
    print(f"    Sin descripción de causa:  {sin_causa:,}")

    print("4/4 Guardando archivo procesado ...")
    config.CARPETA_PROCESADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.ARCHIVO_PROCESADO, index=False, compression="gzip")
    print(f"    Listo: {config.ARCHIVO_PROCESADO}")


if __name__ == "__main__":
    main()