"""Reglas de validación de campos individuales.

Cada función recibe un valor crudo (texto o número) y devuelve el valor ya
convertido, o lanza ErrorValidacion con un mensaje comprensible.
"""

import re
from datetime import datetime

# CUIT: dos dígitos de tipo, ocho del número y uno verificador, separados por guiones.
# El regex sólo comprueba la forma; el dígito verificador se calcula aparte.
PATRON_CUIT = re.compile(r"^(20|23|24|27|30|33|34)-(\d{8})-(\d)$")
PESOS_CUIT = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

# Fecha AAAA-MM-DD con hora HH:MM:SS opcional. El regex no sabe si el día
# existe (por ejemplo 2026-02-30), por eso luego se construye un datetime.
PATRON_FECHA = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2})(?::(\d{2}))?)?$"
)

# Rango razonable de precios por litro en pesos. Valores fuera de él se
# consideran errores de carga (por ejemplo, un precio cargado en centavos).
PRECIO_MINIMO = 100.0
PRECIO_MAXIMO = 10_000.0


class ErrorValidacion(ValueError):
    """Un valor no cumple una regla necesaria para el análisis."""


def digito_verificador_cuit(base):
    """Calcula el dígito verificador de los 10 primeros dígitos de un CUIT."""
    suma = sum(int(d) * p for d, p in zip(base, PESOS_CUIT))
    resto = 11 - suma % 11
    if resto == 11:
        return 0
    if resto == 10:
        return None  # combinación que AFIP no asigna
    return resto


def validar_cuit(valor):
    """Devuelve el CUIT normalizado o lanza ErrorValidacion."""
    texto = texto_obligatorio(valor, "cuit")
    coincidencia = PATRON_CUIT.match(texto)
    if not coincidencia:
        raise ErrorValidacion(f"CUIT con formato inválido: '{texto}' (se espera NN-NNNNNNNN-N)")
    tipo, numero, verificador = coincidencia.groups()
    esperado = digito_verificador_cuit(tipo + numero)
    if esperado is None or esperado != int(verificador):
        raise ErrorValidacion(f"CUIT con dígito verificador incorrecto: '{texto}'")
    return texto


def validar_fecha(valor):
    """Convierte 'AAAA-MM-DD[ HH:MM[:SS]]' a datetime, comprobando que exista."""
    texto = texto_obligatorio(valor, "fecha_vigencia")
    coincidencia = PATRON_FECHA.match(texto)
    if not coincidencia:
        raise ErrorValidacion(f"Fecha con formato inválido: '{texto}' (se espera AAAA-MM-DD)")
    partes = [int(p) if p else 0 for p in coincidencia.groups()]
    try:
        return datetime(*partes)
    except ValueError:
        raise ErrorValidacion(f"La fecha no existe en el calendario: '{texto}'") from None


def validar_precio(valor):
    """Convierte el precio a float y comprueba que esté en un rango plausible."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ErrorValidacion("Precio faltante")
    try:
        precio = float(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion(f"Precio no numérico: '{valor}'") from None
    if not PRECIO_MINIMO <= precio <= PRECIO_MAXIMO:
        raise ErrorValidacion(
            f"Precio fuera de rango: {precio} (válido entre {PRECIO_MINIMO:.0f} y {PRECIO_MAXIMO:.0f})"
        )
    return precio


def texto_obligatorio(valor, campo):
    """Devuelve el texto sin espacios extremos; falla si está vacío."""
    if valor is None or not str(valor).strip():
        raise ErrorValidacion(f"Campo obligatorio vacío: {campo}")
    return str(valor).strip()
