# Mortalidad en Colombia, 2019 · Aplicación web con Dash y Plotly

**Autor:** <Alexander Patiño Castaño> · **Curso:** <2026-2_Aplicaciones I_G1> · **Universidad de La Salle** · <01/11/2026>

**Aplicación desplegada:** <https://proyecto-mortalidad-colombia-d3o4.onrender.com>
**Repositorio:** <https://github.com/apatino01/Proyecto_Mortalidad_Colombia/tree/main>

---

## 1. Introducción

La mortalidad es uno de los indicadores más importantes de la salud de una población. Esta actividad analiza las **defunciones no fetales registradas en Colombia durante 2019** (DANE, Estadísticas Vitales) y las presenta en una aplicación web interactiva construida con Python, Dash y Plotly.

## 2. Objetivo

Desarrollar una aplicación web interactiva que permita explorar la distribución de la mortalidad en
Colombia en 2019 por territorio, tiempo, causa, sexo y edad, y desplegarla en una plataforma PaaS
para que cualquier persona pueda consultarla desde un navegador.

## 3. Conjunto de datos

| Archivo | Contenido | Llave de unión |
|---|---|---|
| `NoFetal2019.xlsx` | Una fila por defunción: municipio, mes, sexo, grupo de edad, causa (CIE-10) | `COD_DANE`, `COD_DEPARTAMENTO`, `COD_MUERTE` |
| `CodigosDeMuerte.xlsx` | Catálogo CIE-10: código y descripción de cada causa | `COD_MUERTE` (4 caracteres) |
| `Divipola.xlsx` | División político-administrativa: departamentos y municipios | `COD_DANE`, `COD_DEPARTAMENTO` |

Total de registros analizados: **244.355** defunciones (100 % cruzan con DIVIPOLA y con el catálogo CIE-10).

## 4. Arquitectura del proyecto

```
Proyecto_Mortalidad_Colombia/
├── app.py                                # Punto de entrada: crea la app Dash y el callback
├── requirements.txt                      # Librerías y versiones
├── Procfile                              # Comando de arranque en el servidor (gunicorn)
├── runtime.txt                           # Versión de Python (formato antiguo)
├── .python-version                       # Versión de Python (Render / Railway)
├── .gitignore                            # Lo que Git no sube (.venv, cachés)
├── README.md
├── data/                                 # Excel originales, LEEME.md y procesado/
├── assets/style.css                      # Estilos de la interfaz (Dash los carga solo)
├── src/
│   ├── config.py                         # Rutas, diccionarios de códigos, colores
│   ├── carga_datos.py                    # Carga, limpieza e integración
│   ├── preparar_datos.py                 # Genera el archivo procesado
│   ├── analisis.py                       # Agregaciones para cada gráfico
│   ├── graficos.py                       # Figuras Plotly
│   ├── layout.py                         # Estructura visual de la página
│   ├── verificar_proyecto.py             # Prueba automática (47 pruebas)
│   └── empaquetar.py                     # Crea el .zip del proyecto
├── notebooks/01_exploracion_datos.ipynb  # Exploración y validación
└── docs/capturas/                        # Capturas de pantalla
```

Flujo: `Excel → limpieza e integración (pandas) → agregaciones → figuras (Plotly) → app (Dash) → Render/Railway`.

## 5. Tecnologías utilizadas

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.14 | Lenguaje |
| pandas | 3.0 | Manipulación de datos |
| openpyxl | 3.1 | Lectura de archivos Excel |
| Plotly | 5.24 | Gráficos interactivos |
| Dash | 3.4 | Aplicación web |
| Gunicorn | 23 | Servidor de producción |
| Render / Railway | — | Plataforma PaaS de despliegue |

## 6. Instalación

```bash
git clone https://github.com/<apatino01>/Proyecto_Mortalidad_Colombia.git
cd Proyecto_Mortalidad_Colombia
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## 7. Ejecución local

```bash
python -m src.preparar_datos     # solo la primera vez (crea data/procesado/)
python -m src.verificar_proyecto # debe terminar en "47 de 47 pruebas aprobadas"
python app.py                    # abrir http://127.0.0.1:8050
```

## 8. Despliegue

Desplegado en **<Render>**.

- Comando de construcción: `pip install -r requirements.txt`
- Comando de inicio: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
- Versión de Python: archivo `.python-version` (3.14)

## 9. Resultados obtenidos

| Visualización | Hallazgo principal |
|---|---|
| Mapa por departamento | Bogotá (38.760), Antioquia (34.473) y Valle del Cauca (28.443) concentran el 41,6 % de las muertes del país |
| Mortalidad mensual | Diciembre es el mes con más muertes (21.678) y febrero el de menos (17.974, pero tiene solo 28 días); por día, el promedio va de 641 (abril) a 699 (diciembre) |
| 5 ciudades con más homicidios | Cali (1.239), Bogotá (1.148), Medellín (637), Barranquilla (345) y Cúcuta (262): 27,8 % de los 13.043 homicidios del país |
| 10 ciudades con menor mortalidad | 13 municipios empatan con 1 sola muerte (ej. Alto Baudó, Nuquí, Mapiripana); son municipios pequeños y apartados |
| 10 principales causas | El infarto agudo del miocardio (I219) causa 35.088 muertes, 14,4 % del total; le siguen dos códigos de EPOC (J449 y J440) |
| Sexo por departamento | 55,1 % hombres y 44,9 % mujeres; la razón hombre/mujer va de 1,07 en Bogotá a 3,36 en Guaviare |
| Grupos de edad | El 70,2 % de las muertes ocurre después de los 60 años (Vejez 47,2 % y Longevidad 22,9 %) |

## 10. Capturas de pantalla

![Vista general](docs/capturas/vista_general.png)
![Filtro aplicado](docs/capturas/filtro_departamento.png)

## 11. Conclusiones

1. La mortalidad se concentra donde se concentra la población: tres territorios (Bogotá, Antioquia y Valle) suman 4 de cada 10 muertes.
2. Predominan las enfermedades crónicas en la vejez: 7 de cada 10 muertes ocurren después de los 60 años y el infarto es, de lejos, la primera causa.
3. La violencia tiene un peso propio: los homicidios (5,3 % del total) se concentran en grandes ciudades, con Cali por encima de Bogotá pese a tener menos población, y el 91,3 % de las víctimas son hombres, 69,8 % de ellos entre 20 y 44 años, lo que eleva la razón hombre/mujer en varios departamentos.
4. Limitaciones: se usan cifras absolutas, no tasas por población; "menor mortalidad" refleja municipios pequeños y posible subregistro; los grupos de edad tienen anchos distintos.

## Fuentes

- DANE, Estadísticas Vitales: defunciones no fetales 2019.
- Organización Mundial de la Salud, CIE-10.
- DANE, DIVIPOLA.
- Mapa de departamentos: santiblanko/colombia.geojson (GitHub).