"""Flujo de procesamiento: leer -> validar -> limpiar -> analizar -> comunicar."""

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from fuentes import crear_fuente
from modelos import EstadisticaPrecios, RegistroPrecio
from validacion import ErrorValidacion


@dataclass
class ResultadoPipeline:
    total_leidos: int
    registros: list
    rechazados: list = field(default_factory=list)
    duplicados: list = field(default_factory=list)
    resumen_provincias: list = field(default_factory=list)
    resumen_banderas: list = field(default_factory=list)
    brechas: list = field(default_factory=list)


# ---------- Validación y limpieza ----------

def validar_filas(filas):
    """Convierte filas crudas en RegistroPrecio.

    Devuelve (registros_validos, rechazados). Cada rechazo indica el número de
    registro (1 = primera fila de datos) y el motivo, para poder revisarlo.
    """
    registros, rechazados = [], []
    for numero, fila in enumerate(filas, start=1):
        try:
            registros.append(RegistroPrecio.desde_fila(fila))
        except ErrorValidacion as error:
            rechazados.append({"registro": numero, "motivo": str(error)})
    return registros, rechazados


def eliminar_duplicados(registros):
    """Conserva la primera aparición de cada clave; devuelve (únicos, duplicados)."""
    vistos, unicos, duplicados = set(), [], []
    for registro in registros:
        if registro.clave() in vistos:
            duplicados.append(registro)
        else:
            vistos.add(registro.clave())
            unicos.append(registro)
    return unicos, duplicados


# ---------- Análisis ----------

def agrupar_precios(registros, *campos):
    """Agrupa los precios por los atributos indicados: {(valor1, valor2, ...): [precios]}."""
    grupos = defaultdict(list)
    for registro in registros:
        grupos[tuple(getattr(registro, c) for c in campos)].append(registro.precio)
    return dict(grupos)


def resumir(registros, *campos):
    """Tabla de estadísticas por grupo, ordenada por los campos de agrupación."""
    filas = []
    for clave, precios in sorted(agrupar_precios(registros, *campos).items()):
        est = EstadisticaPrecios.desde_precios(precios)
        fila = dict(zip(campos, clave))
        fila.update(
            cantidad=est.cantidad,
            promedio=round(est.promedio, 2),
            mediana=round(est.mediana, 2),
            minimo=est.minimo,
            maximo=est.maximo,
        )
        filas.append(fila)
    return filas


def brecha_por_producto(resumen_provincias):
    """Para cada producto: provincia con el promedio más bajo, más alto y la diferencia %."""
    por_producto = defaultdict(list)
    for fila in resumen_provincias:
        por_producto[fila["producto"]].append(fila)
    brechas = []
    for producto, filas in sorted(por_producto.items()):
        barata = min(filas, key=lambda f: f["promedio"])
        cara = max(filas, key=lambda f: f["promedio"])
        brechas.append({
            "producto": producto,
            "provincia_mas_barata": barata["provincia"],
            "promedio_mas_bajo": barata["promedio"],
            "provincia_mas_cara": cara["provincia"],
            "promedio_mas_alto": cara["promedio"],
            "diferencia_pct": round((cara["promedio"] - barata["promedio"]) / barata["promedio"] * 100, 1),
        })
    return brechas


# ---------- Salida ----------

def escribir_csv(filas, ruta):
    """Guarda una lista de diccionarios como CSV (UTF-8, apto para Excel)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not filas:
        ruta.write_text("", encoding="utf-8-sig")
        return
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def ejecutar_pipeline(ruta_entrada, carpeta_salida=None):
    """Ejecuta el flujo completo. Si se indica carpeta_salida, guarda los CSV."""
    filas = crear_fuente(ruta_entrada).cargar()
    validos, rechazados = validar_filas(filas)
    registros, duplicados = eliminar_duplicados(validos)
    if not registros:
        raise ValueError("Ningún registro superó la validación; no hay nada que analizar.")

    resumen_provincias = resumir(registros, "producto", "provincia")
    resultado = ResultadoPipeline(
        total_leidos=len(filas),
        registros=registros,
        rechazados=rechazados,
        duplicados=duplicados,
        resumen_provincias=resumen_provincias,
        resumen_banderas=resumir(registros, "producto", "bandera"),
        brechas=brecha_por_producto(resumen_provincias),
    )

    if carpeta_salida is not None:
        carpeta = Path(carpeta_salida)
        escribir_csv(resultado.resumen_provincias, carpeta / "resumen_por_provincia.csv")
        escribir_csv(resultado.resumen_banderas, carpeta / "resumen_por_bandera.csv")
        escribir_csv(resultado.brechas, carpeta / "brecha_por_producto.csv")
        escribir_csv(resultado.rechazados, carpeta / "rechazados.csv")
    return resultado
