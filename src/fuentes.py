"""Fuentes de datos: una interfaz común para leer registros desde CSV o JSON.

La clase base FuenteDatos define el contrato `cargar()`: devolver una lista de
diccionarios (una fila por estación/producto) con, al menos, las columnas
requeridas. Cada subclase sólo resuelve cómo se lee su formato; la validación
del esquema es común y vive en la clase base.
"""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path

COLUMNAS_REQUERIDAS = (
    "cuit",
    "empresa",
    "empresabandera",
    "provincia",
    "localidad",
    "producto",
    "tipohorario",
    "precio",
    "fecha_vigencia",
)


class ErrorFuente(Exception):
    """Error al leer una fuente de datos o al comprobar su estructura."""


class FuenteDatos(ABC):
    """Fuente de datos tabular. Las subclases implementan `_leer()`."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)

    def cargar(self):
        """Lee el archivo y devuelve una lista de diccionarios con esquema válido."""
        if not self.ruta.is_file():
            raise ErrorFuente(f"No se encontró el archivo de datos: {self.ruta}")
        filas = self._leer()
        self._validar_esquema(filas)
        return filas

    @abstractmethod
    def _leer(self):
        """Devuelve las filas del archivo como lista de diccionarios."""

    def _validar_esquema(self, filas):
        if not filas:
            raise ErrorFuente(f"El archivo {self.ruta.name} no contiene registros.")
        for numero, fila in enumerate(filas, start=1):
            faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in fila]
            if faltantes:
                raise ErrorFuente(
                    f"{self.ruta.name}, registro {numero}: faltan las columnas "
                    f"{', '.join(faltantes)}."
                )

    def __repr__(self):
        return f"{type(self).__name__}('{self.ruta}')"


class FuenteCSV(FuenteDatos):
    """Lee un CSV con encabezado. Las celdas vacías se convierten en None."""

    def _leer(self):
        with open(self.ruta, encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [
                {clave: (valor if valor != "" else None) for clave, valor in fila.items()}
                for fila in lector
            ]


class FuenteJSON(FuenteDatos):
    """Lee un JSON cuya raíz es una lista de objetos (uno por registro)."""

    def _leer(self):
        try:
            with open(self.ruta, encoding="utf-8-sig") as archivo:
                datos = json.load(archivo)
        except json.JSONDecodeError as error:
            raise ErrorFuente(
                f"{self.ruta.name} no es un JSON válido (línea {error.lineno}): {error.msg}"
            ) from error
        if not isinstance(datos, list) or not all(isinstance(d, dict) for d in datos):
            raise ErrorFuente(
                f"{self.ruta.name}: se esperaba una lista de objetos JSON."
            )
        return datos


def crear_fuente(ruta):
    """Elige la implementación de FuenteDatos según la extensión del archivo."""
    tipos = {".csv": FuenteCSV, ".json": FuenteJSON}
    extension = Path(ruta).suffix.lower()
    if extension not in tipos:
        raise ErrorFuente(
            f"Formato no soportado: '{extension}'. Use un archivo .csv o .json."
        )
    return tipos[extension](ruta)
