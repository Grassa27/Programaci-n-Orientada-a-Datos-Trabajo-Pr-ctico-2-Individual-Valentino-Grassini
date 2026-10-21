"""Pruebas del TP2. Ejecutar desde la raíz del proyecto:

    python -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from fuentes import ErrorFuente, FuenteCSV, FuenteJSON, crear_fuente  # noqa: E402
from modelos import EstadisticaPrecios, RegistroPrecio  # noqa: E402
from pipeline import eliminar_duplicados, ejecutar_pipeline, validar_filas  # noqa: E402
from validacion import ErrorValidacion, validar_cuit, validar_fecha, validar_precio  # noqa: E402

MUESTRA_CSV = RAIZ / "data" / "muestra_precios.csv"
MUESTRA_JSON = RAIZ / "data" / "muestra_precios.json"

FILA_VALIDA = {
    "cuit": "30-70137911-6",
    "empresa": "ESTACION PRUEBA",
    "empresabandera": "YPF",
    "provincia": "Cordoba",
    "localidad": "Villa Maria",
    "producto": "Gas Oil Grado 2",
    "tipohorario": "Diurno",
    "precio": "1500.50",
    "fecha_vigencia": "2026-09-10 12:00:00",
}


class TestCasoNormal(unittest.TestCase):
    def test_fila_valida_se_convierte_en_registro(self):
        registro = RegistroPrecio.desde_fila(FILA_VALIDA)
        self.assertEqual(registro.precio, 1500.50)
        self.assertEqual(registro.provincia, "CORDOBA")
        self.assertEqual(registro.tipo_combustible, "Gas Oil")
        self.assertEqual(registro.fecha.day, 10)

    def test_pipeline_sobre_la_muestra(self):
        resultado = ejecutar_pipeline(MUESTRA_CSV)
        self.assertEqual(resultado.total_leidos, 59)
        self.assertEqual(len(resultado.rechazados), 6)
        self.assertEqual(len(resultado.duplicados), 1)
        self.assertEqual(len(resultado.registros), 52)
        self.assertEqual(len(resultado.brechas), 4)  # un resultado por producto

    def test_estadisticas(self):
        est = EstadisticaPrecios.desde_precios([100, 200, 300, 400])
        self.assertEqual(est.promedio, 250)
        self.assertEqual(est.mediana, 250)
        self.assertEqual(est.rango_relativo, 300)


class TestEntradasInvalidas(unittest.TestCase):
    def test_cuit_con_formato_invalido(self):
        with self.assertRaises(ErrorValidacion):
            validar_cuit("3070137911")

    def test_cuit_con_digito_verificador_incorrecto(self):
        with self.assertRaises(ErrorValidacion):
            validar_cuit("30-70137911-5")

    def test_fecha_que_no_existe(self):
        # El formato es correcto (pasa el regex) pero el 30 de febrero no existe.
        with self.assertRaisesRegex(ErrorValidacion, "no existe"):
            validar_fecha("2026-02-30")

    def test_precio_faltante_negativo_y_no_numerico(self):
        for valor in (None, "", "-1500", "abc", "0"):
            with self.subTest(valor=valor), self.assertRaises(ErrorValidacion):
                validar_precio(valor)

    def test_limites_del_rango_de_precio(self):
        self.assertEqual(validar_precio("100"), 100.0)
        self.assertEqual(validar_precio(10000), 10000.0)
        with self.assertRaises(ErrorValidacion):
            validar_precio("10000.01")

    def test_archivo_inexistente(self):
        with self.assertRaisesRegex(ErrorFuente, "No se encontró"):
            FuenteCSV(RAIZ / "data" / "no_existe.csv").cargar()

    def test_extension_no_soportada(self):
        with self.assertRaises(ErrorFuente):
            crear_fuente("datos.xlsx")

    def test_json_sin_columnas_requeridas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "incompleto.json"
            ruta.write_text(json.dumps([{"cuit": "30-70137911-6"}]), encoding="utf-8")
            with self.assertRaisesRegex(ErrorFuente, "faltan las columnas"):
                FuenteJSON(ruta).cargar()

    def test_json_mal_formado(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "roto.json"
            ruta.write_text("[{", encoding="utf-8")
            with self.assertRaisesRegex(ErrorFuente, "no es un JSON válido"):
                FuenteJSON(ruta).cargar()


class TestPropiedades(unittest.TestCase):
    def test_csv_y_json_producen_los_mismos_registros(self):
        desde_csv, rech_csv = validar_filas(FuenteCSV(MUESTRA_CSV).cargar())
        desde_json, rech_json = validar_filas(FuenteJSON(MUESTRA_JSON).cargar())
        self.assertEqual(desde_csv, desde_json)
        self.assertEqual(rech_csv, rech_json)

    def test_conservacion_de_cantidades(self):
        # Cada fila leída termina en exactamente un grupo: analizada, rechazada o duplicada.
        r = ejecutar_pipeline(MUESTRA_CSV)
        self.assertEqual(
            r.total_leidos, len(r.registros) + len(r.rechazados) + len(r.duplicados)
        )
        self.assertEqual(sum(f["cantidad"] for f in r.resumen_provincias), len(r.registros))

    def test_promedios_dentro_del_rango_de_cada_grupo(self):
        for fila in ejecutar_pipeline(MUESTRA_CSV).resumen_provincias:
            self.assertLessEqual(fila["minimo"], fila["promedio"])
            self.assertLessEqual(fila["promedio"], fila["maximo"])

    def test_sin_duplicados_tras_la_limpieza(self):
        registro = RegistroPrecio.desde_fila(FILA_VALIDA)
        unicos, duplicados = eliminar_duplicados([registro, registro, registro])
        self.assertEqual(len(unicos), 1)
        self.assertEqual(len(duplicados), 2)

    def test_resultados_reproducibles(self):
        self.assertEqual(
            ejecutar_pipeline(MUESTRA_CSV).brechas, ejecutar_pipeline(MUESTRA_CSV).brechas
        )


if __name__ == "__main__":
    unittest.main()
