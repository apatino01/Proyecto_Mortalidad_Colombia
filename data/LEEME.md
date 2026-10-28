# Carpeta data/

Aca se copian los tres archivos fuente para realizar la actividad, con las siguientes denominaciones:

- `NoFetal2019.xlsx`
- `CodigosDeMuerte.xlsx`
- `Divipola.xlsx`

Ejecute desde la raíz del proyecto:

    python -m src.preparar_datos

Esto crea `data/procesado/defunciones_2019.csv.gz`, que es el archivo que
usa la aplicación en el servidor.

