"""Punto de entrada: python src/main.py [--entrada ARCHIVO] [--salida CARPETA]"""

import argparse
import sys
from pathlib import Path

from fuentes import ErrorFuente
from pipeline import ejecutar_pipeline

RAIZ = Path(__file__).resolve().parent.parent


def leer_argumentos():
    parser = argparse.ArgumentParser(
        description="Compara precios de combustibles en Argentina por provincia y bandera."
    )
    parser.add_argument(
        "--entrada",
        default=RAIZ / "data" / "muestra_precios.csv",
        help="Archivo .csv o .json con los precios (por defecto, la muestra en data/).",
    )
    parser.add_argument(
        "--salida",
        default=RAIZ / "outputs",
        help="Carpeta donde se guardan los CSV de resultados (por defecto, outputs/).",
    )
    return parser.parse_args()


def imprimir_reporte(resultado):
    print("=" * 70)
    print("PRECIOS DE COMBUSTIBLES EN ARGENTINA - brecha entre provincias")
    print("=" * 70)
    print(f"Registros leídos:     {resultado.total_leidos}")
    print(f"Rechazados:           {len(resultado.rechazados)}")
    print(f"Duplicados quitados:  {len(resultado.duplicados)}")
    print(f"Registros analizados: {len(resultado.registros)}")

    if resultado.rechazados:
        print("\nFilas rechazadas:")
        for rechazo in resultado.rechazados:
            print(f"  - registro {rechazo['registro']}: {rechazo['motivo']}")

    print("\nBrecha de precio promedio entre provincias, por producto:")
    for b in resultado.brechas:
        print(f"\n  {b['producto']}")
        print(f"    más barata: {b['provincia_mas_barata']:<14} $ {b['promedio_mas_bajo']:>9,.2f}")
        print(f"    más cara:   {b['provincia_mas_cara']:<14} $ {b['promedio_mas_alto']:>9,.2f}")
        print(f"    diferencia: {b['diferencia_pct']} %")


def main():
    args = leer_argumentos()
    try:
        resultado = ejecutar_pipeline(args.entrada, args.salida)
    except (ErrorFuente, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    imprimir_reporte(resultado)
    print(f"\nResultados guardados en: {Path(args.salida).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
