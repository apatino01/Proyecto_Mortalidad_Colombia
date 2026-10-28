"""
empaquetar.py
-------------
Crea el archivo Proyecto_Mortalidad_Colombia.zip con todo el proyecto,
listo para entregar o compartir.

Uso (desde la raíz del proyecto):
    python -m src.empaquetar

El .zip queda en la carpeta que CONTIENE al proyecto (un nivel arriba), para
que no se incluya a sí mismo. Deja por fuera lo que no se debe compartir:
el entorno virtual (.venv), las cachés de Python y la carpeta .git.
"""

import zipfile

from src import config

# Carpetas que nunca van en el .zip (se recrean en cada computador)
EXCLUIR_CARPETAS = {".venv", "venv", "__pycache__", ".ipynb_checkpoints", ".git", ".vscode"}
EXCLUIR_EXTENSIONES = {".pyc"}


def main():
    nombre = config.RAIZ.name                       # "Proyecto_Mortalidad_Colombia"
    destino = config.RAIZ.parent / f"{nombre}.zip"  # un nivel arriba del proyecto
    archivos = 0

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zip_salida:
        for ruta in sorted(config.RAIZ.rglob("*")):
            relativa = ruta.relative_to(config.RAIZ)
            # Se descarta si alguna carpeta de la ruta está en la lista de exclusión
            if any(parte in EXCLUIR_CARPETAS for parte in relativa.parts):
                continue
            if ruta.is_file() and ruta.suffix not in EXCLUIR_EXTENSIONES:
                # Dentro del .zip todo queda bajo la carpeta Proyecto_Mortalidad_Colombia/
                zip_salida.write(ruta, arcname=f"{nombre}/{relativa.as_posix()}")
                archivos += 1
            elif ruta.is_dir() and not any(ruta.iterdir()):
                # Carpeta vacía (ej. docs/capturas antes de tomar capturas):
                # se guarda igual para que la estructura quede completa
                zip_salida.write(ruta, arcname=f"{nombre}/{relativa.as_posix()}/")

    megas = destino.stat().st_size / 1_048_576
    print(f"Listo: {destino}")
    print(f"{archivos} archivos, {megas:.1f} MB")


if __name__ == "__main__":
    main()