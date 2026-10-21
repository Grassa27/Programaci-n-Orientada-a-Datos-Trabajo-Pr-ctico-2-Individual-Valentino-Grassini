# Datos

## De dónde salen

- **Nombre del conjunto:** Precios en surtidor – Resolución 314/2016
- **Quién lo publica:** la Secretaría de Energía de la Nación (Ministerio de Economía)
- **Dónde encontrarlo:** en el portal de datos abiertos <https://datos.gob.ar>,
  buscando "Precios en surtidor" (también está en <http://datos.energia.gob.ar>)
- **Licencia:** Creative Commons Attribution 4.0 (CC BY 4.0), o sea que se puede
  usar libremente siempre que se cite la fuente
- **Fecha de consulta:** _completar con la fecha en que descargues el archivo_

Por ley, las estaciones de servicio tienen que informarle sus precios a la
Secretaría de Energía, y con eso se arma este conjunto. El archivo completo tiene
decenas de miles de filas, así que es muy pesado para subirlo al repositorio.

## Qué hay en esta carpeta

| Archivo | Qué tiene |
|---|---|
| `muestra_precios.csv` | Una muestra de 59 filas con las mismas columnas que el archivo oficial |
| `muestra_precios.json` | La misma muestra pero en JSON, para comprobar que leer los dos formatos da lo mismo |

> **Importante:** la muestra es **inventada** (sintética). Tiene las mismas
> columnas que el archivo oficial, pero las estaciones, los CUIT y los precios los
> generé para poder probar el programa. Por eso los nombres de las empresas dicen
> "(ficticia)".
>
> Además, le puse 7 filas con errores a propósito, para ver si el programa los
> detecta: una fila repetida, dos CUIT mal, un precio vacío, un precio negativo,
> una fecha que no existe y una fila sin provincia.
>
> Para hacer el análisis con datos reales, hay que bajar el CSV oficial, guardarlo
> en esta carpeta y correr:
> `python src/main.py --entrada data/precios-en-surtidor.csv`

## Qué representa cada fila

Cada fila es **el precio de un combustible en una estación de servicio, en un
horario (diurno o nocturno), desde una fecha determinada**.

## Columnas que uso

| Columna | Tipo | Qué significa |
|---|---|---|
| `cuit` | texto | CUIT de la empresa dueña de la estación (formato `NN-NNNNNNNN-N`) |
| `empresa` | texto | Nombre de la empresa |
| `empresabandera` | texto | Marca de la estación (YPF, Shell, Axion, Puma, blanca, etc.) |
| `provincia` | texto | Provincia donde está la estación |
| `localidad` | texto | Ciudad o localidad |
| `producto` | texto | Tipo de combustible (por ejemplo, "Gas Oil Grado 2") |
| `tipohorario` | texto | Si el precio es diurno o nocturno |
| `precio` | número | Precio por litro, en pesos |
| `fecha_vigencia` | fecha | Desde cuándo vale ese precio (`AAAA-MM-DD HH:MM:SS`) |

El archivo oficial trae más columnas (dirección, latitud, longitud, etc.), pero
para mi pregunta no las necesito, así que el programa no las usa.

## Limitaciones

- Los precios los **carga cada estación**, así que puede haber errores o precios
  viejos (por ejemplo, una estación que subió el precio y no lo actualizó).
- No todas las provincias tienen la misma cantidad de estaciones. En las que tienen
  pocas, el promedio es menos confiable.
- El promedio es **por estación**, no por litros vendidos, porque el conjunto no
  dice cuánto vende cada una.
- Los precios no están ajustados por inflación. Si comparo fechas muy distintas, no
  sé si la diferencia es por la provincia o porque pasó el tiempo. Por eso conviene
  analizar un período corto.
