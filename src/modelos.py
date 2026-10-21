"""Clases del dominio: un precio informado por una estación y un resumen estadístico."""

import statistics
from dataclasses import dataclass
from datetime import datetime

from validacion import texto_obligatorio, validar_cuit, validar_fecha, validar_precio


@dataclass(frozen=True)
class RegistroPrecio:
    """Precio de un producto en una estación de servicio, en una fecha de vigencia."""

    cuit: str
    empresa: str
    bandera: str
    provincia: str
    localidad: str
    producto: str
    horario: str
    precio: float
    fecha: datetime

    @classmethod
    def desde_fila(cls, fila):
        """Construye un registro validando cada campo; lanza ErrorValidacion si falla."""
        return cls(
            cuit=validar_cuit(fila.get("cuit")),
            empresa=texto_obligatorio(fila.get("empresa"), "empresa"),
            bandera=texto_obligatorio(fila.get("empresabandera"), "empresabandera"),
            provincia=texto_obligatorio(fila.get("provincia"), "provincia").upper(),
            localidad=texto_obligatorio(fila.get("localidad"), "localidad").upper(),
            producto=texto_obligatorio(fila.get("producto"), "producto"),
            horario=texto_obligatorio(fila.get("tipohorario"), "tipohorario"),
            precio=validar_precio(fila.get("precio")),
            fecha=validar_fecha(fila.get("fecha_vigencia")),
        )

    @property
    def tipo_combustible(self):
        """Agrupa los productos en 'Nafta', 'Gas Oil' u 'Otro'."""
        nombre = self.producto.lower()
        if nombre.startswith("nafta"):
            return "Nafta"
        if nombre.startswith("gas oil") or nombre.startswith("gasoil"):
            return "Gas Oil"
        return "Otro"

    def clave(self):
        """Identifica un precio: misma estación, producto, horario y fecha."""
        return (self.cuit, self.localidad, self.producto, self.horario, self.fecha)


@dataclass(frozen=True)
class EstadisticaPrecios:
    """Resumen de un conjunto de precios."""

    cantidad: int
    minimo: float
    maximo: float
    promedio: float
    mediana: float

    @classmethod
    def desde_precios(cls, precios):
        precios = list(precios)
        if not precios:
            raise ValueError("No se puede resumir una lista de precios vacía.")
        return cls(
            cantidad=len(precios),
            minimo=min(precios),
            maximo=max(precios),
            promedio=statistics.mean(precios),
            mediana=statistics.median(precios),
        )

    @property
    def rango_relativo(self):
        """Diferencia entre el máximo y el mínimo, como porcentaje del mínimo."""
        return (self.maximo - self.minimo) / self.minimo * 100
