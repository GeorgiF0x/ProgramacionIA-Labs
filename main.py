"""Sistema inteligente de monitorización y diagnóstico industrial."""

import sys
from pathlib import Path

from src import carga, limpieza

RUTA_DATOS = Path(__file__).parent / "datos" / "sensores.csv"


def titulo(texto: str) -> None:
    print(f"\n{'=' * 70}\n{texto}\n{'=' * 70}")


def main() -> int:
    titulo("APARTADO 1. Carga y exploración de los datos")
    try:
        datos = carga.cargar_datos(RUTA_DATOS)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error al cargar los datos: {error}", file=sys.stderr)
        return 1

    carga.mostrar_resumen(carga.resumen_exploratorio(datos))
    print("\nMuestra de registros:")
    carga.mostrar_muestra(datos)

    titulo("APARTADO 2. Limpieza y preparación de los datos")
    resultado_limpieza = limpieza.limpiar(datos)
    limpieza.mostrar_resumen_limpieza(datos, resultado_limpieza)
    return 0


if __name__ == "__main__":
    sys.exit(main())
