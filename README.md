# Precios de combustibles en Argentina: ¿dónde es más barato cargar?

**Autor:** Valentino Grassini
**Materia:** Programación Orientada a Datos – Licenciatura en Ciencia de Datos – UCA, 2026
**Trabajo Práctico 2**

## 1. Problema, usuario y pregunta

Elegí este tema porque el precio de la nafta y el gasoil no es el mismo en todo
el país: cambia según la provincia y según la bandera de la estación (YPF, Shell,
Axion, etc.). El gobierno publica estos precios, pero el archivo tiene miles de
filas y mirándolo así nomás no se puede sacar ninguna conclusión.

**¿A quién le puede servir?** A alguien que viaja seguido entre provincias, a una
empresa con camiones que quiere saber dónde le conviene cargar, o a cualquiera que
tenga curiosidad por las diferencias de precios entre regiones.

**Pregunta que quiero responder:**
> Para cada tipo de combustible, ¿en qué provincia es más barato y en cuál es más
> caro el precio promedio por litro, y qué diferencia porcentual hay entre las dos?

**Qué hace el programa:** muestra un resumen en la consola y guarda cuatro archivos
CSV en la carpeta `outputs/`:

- `brecha_por_producto.csv`: la respuesta a la pregunta (provincia más barata, más
  cara y la diferencia en %).
- `resumen_por_provincia.csv`: cantidad, promedio, mediana, mínimo y máximo por
  combustible y provincia.
- `resumen_por_bandera.csv`: lo mismo, pero por bandera.
- `rechazados.csv`: las filas que el programa descartó y por qué.

**Hasta dónde llega esta versión:** compara precios de un período corto por
provincia y por bandera. **No hace:** ver cómo cambian los precios en el tiempo,
ajustar por inflación, mapas ni predicciones.

## 2. Datos

- **Fuente:** *Precios en surtidor – Resolución 314/2016*, de la Secretaría de
  Energía, publicado en datos.gob.ar.
- **Licencia:** CC BY 4.0 (se pueden usar citando la fuente).
- **Qué es cada fila:** el precio de un combustible en una estación de servicio, en
  un horario (diurno o nocturno), desde una fecha.

Como el archivo oficial es muy grande, en el repositorio dejé una **muestra de 59
filas sintética, generada con IA**, con las mismas columnas que el original, para
poder probar el programa. No son datos reales. Le agregué errores a propósito para ver que la validación los
detecte. Todo el detalle de las columnas y las limitaciones está en
[`data/README.md`](data/README.md).

## 3. Instalación

Hace falta **Python 3.10 o más nuevo**. No hay que instalar ninguna librería,
porque usé solamente lo que trae Python (`csv`, `json`, `re`, `unittest`, etc.).

```bash
  git clone https://github.com/TU_USUARIO/Programaci-n-Orientada-a-Datos-Trabajo-Pr-ctico-2-Individual-Valentino-Grassini.git
  cd Programaci-n-Orientada-a-Datos-Trabajo-Pr-ctico-2-Individual-Valentino-Grassini
```

## 4. Cómo ejecutarlo

Parado en la carpeta del proyecto:

```bash
python src/main.py
```

Para usar otro archivo (CSV o JSON) o guardar los resultados en otra carpeta:

```bash
python src/main.py --entrada data/muestra_precios.json --salida outputs
```

## 5. Pruebas

```bash
python -m unittest discover -s tests -v
```

Hice 17 pruebas, separadas en tres grupos:

- **Casos normales:** que una fila correcta se lea bien y que el programa completo
  funcione con la muestra.
- **Entradas inválidas y casos límite:**
  - CUIT mal escrito o con el dígito verificador mal;
  - una fecha que no existe (por ejemplo, 30 de febrero);
  - precios vacíos, negativos, que no son números o fuera de rango (y los
    valores justo en el límite);
  - un archivo que no existe;
  - un JSON roto o al que le faltan columnas.
- **Propiedades del resultado:**
  - leer el CSV y el JSON da exactamente los mismos registros;
  - no se pierde ninguna fila: leídos = analizados + rechazados + duplicados;
  - cada promedio queda entre el mínimo y el máximo de su grupo;
  - si corro el programa dos veces, da lo mismo.

## 6. Cómo está organizado el código

```
tp2-grassini/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py         # arranca el programa y muestra el reporte
│   ├── fuentes.py      # FuenteDatos, FuenteCSV y FuenteJSON (lectura de archivos)
│   ├── validacion.py   # expresiones regulares y reglas para validar cada campo
│   ├── modelos.py      # clases RegistroPrecio y EstadisticaPrecios
│   └── pipeline.py     # validar -> limpiar -> agrupar -> resumir -> guardar
├── tests/
│   └── test_tp2.py
├── data/
│   ├── README.md
│   ├── muestra_precios.csv
│   └── muestra_precios.json
└── outputs/            # se crea al ejecutar (no se sube a GitHub)
```

**Por qué lo armé así:**

- **`FuenteDatos`** es una clase base (abstracta) con el método `cargar()`. Ese
  método se fija que el archivo exista, lo lee y revisa que tenga las columnas
  necesarias. `FuenteCSV` y `FuenteJSON` heredan de ella y lo único que cambian es
  *cómo* se lee el archivo (el método `_leer()`). La ventaja es que el resto del
  programa no necesita saber si los datos vienen de un CSV o de un JSON. La función
  `crear_fuente()` elige cuál usar según la extensión del archivo.
- **`RegistroPrecio`** representa una fila que ya pasó la validación, con cada dato
  en su tipo correcto (el precio como `float` y la fecha como `datetime`). Tiene el
  método `desde_fila()`, que hace la validación, y `clave()`, que sirve para
  detectar filas repetidas.
- **`EstadisticaPrecios`** calcula el resumen (promedio, mediana, mínimo, máximo)
  de un grupo de precios.
- **Expresiones regulares** (en `validacion.py`):
  - `PATRON_CUIT` revisa que el CUIT tenga la forma `NN-NNNNNNNN-N`. Con una regex
    no se puede saber si el último dígito (el verificador) es correcto, así que lo
    complementé con la cuenta de módulo 11 que usa AFIP.
  - `PATRON_FECHA` revisa la forma `AAAA-MM-DD` (con hora opcional). La regex
    acepta cosas como `2026-02-30`, así que después intento crear un `datetime`:
    si la fecha no existe en el calendario, da error y la fila se rechaza.
- **Funciones:** traté de que cada una haga una sola cosa (`validar_filas`,
  `eliminar_duplicados`, `agrupar_precios`, `resumir`, `brecha_por_producto`,
  `escribir_csv`). Ninguna modifica lo que recibe, siempre devuelven datos nuevos.

## 7. Decisiones de limpieza

| Problema | Qué hace el programa |
|---|---|
| Faltan columnas obligatorias | Se frena y avisa qué columnas faltan |
| El archivo no existe o el JSON está roto | Se frena con un mensaje claro (no esconde el error) |
| CUIT mal escrito o con dígito verificador incorrecto | Descarta la fila |
| Fecha mal escrita o que no existe | Descarta la fila |
| Precio vacío, que no es número o fuera de 100 a 10.000 $/l | Descarta la fila |
| Un campo de texto obligatorio vacío | Descarta la fila |
| Fila repetida (misma estación, combustible, horario y fecha) | Se queda con la primera |
| Provincia o localidad escrita con mayúsculas distintas | Pasa todo a mayúsculas |

Cada fila descartada se muestra en la consola y se guarda en
`outputs/rechazados.csv`, con su número y el motivo.

## 8. Ejemplo de resultado

Esto es lo que sale al correr `python src/main.py` con la muestra:

```
======================================================================
PRECIOS DE COMBUSTIBLES EN ARGENTINA - brecha entre provincias
======================================================================
Registros leídos:     59
Rechazados:           6
Duplicados quitados:  1
Registros analizados: 52

Filas rechazadas:
  - registro 54: CUIT con dígito verificador incorrecto: '30-12345678-0'
  - registro 55: CUIT con formato inválido: '3071234567' (se espera NN-NNNNNNNN-N)
  - registro 56: Precio faltante
  - registro 57: Precio fuera de rango: -1500.0 (válido entre 100 y 10000)
  - registro 58: La fecha no existe en el calendario: '2026-02-30 10:00:00'
  - registro 59: Campo obligatorio vacío: provincia

Brecha de precio promedio entre provincias, por producto:

  Gas Oil Grado 2
    más barata: NEUQUEN        $  1,350.65
    más cara:   SALTA          $  1,548.45
    diferencia: 14.6 %

  Gas Oil Grado 3
    más barata: NEUQUEN        $  1,691.73
    más cara:   SALTA          $  1,899.64
    diferencia: 12.3 %

  Nafta (premium) de más de 95 Ron
    más barata: NEUQUEN        $  1,619.53
    más cara:   SALTA          $  1,850.57
    diferencia: 14.3 %

  Nafta (súper) entre 92 y 95 Ron
    más barata: NEUQUEN        $  1,319.49
    más cara:   SALTA          $  1,517.47
    diferencia: 15.0 %
```

Se ve que el programa detectó los 6 errores que puse a propósito y la fila
duplicada, y que las cuentas cierran: 52 + 6 + 1 = 59.

## 9. Interpretación y limitaciones

- La **diferencia %** indica cuánto más caro es el litro en la provincia más cara
  comparado con la más barata. Por ejemplo, un 15 % quiere decir que en una
  provincia se paga 15 % más que en la otra por el mismo combustible.
- **Ojo:** estos números salen de la muestra generada con IA, así que **no dicen nada
  de la realidad**. Solo sirven para mostrar que el programa funciona. Para sacar
  conclusiones de verdad hay que correrlo con el archivo oficial.
- El promedio es por estación, no por litros vendidos (esos datos no están). Si
  una provincia tiene pocas estaciones, su promedio es menos confiable; por eso
  conviene mirar la columna `cantidad`.
- Los precios no están ajustados por inflación. Si se mezclan fechas muy separadas,
  la comparación se distorsiona, así que lo mejor es usar un período corto.
- Los precios los carga cada estación y pueden tener errores. El programa atrapa
  los errores obvios, pero no un precio que parece normal y en realidad está mal
  cargado.
