"""CLI: python3 src/main.py <archivo.pl>"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from lexer import lexear
from tokens import TablaLexemas


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 src/main.py <archivo.pl>")
        return 2
    ruta = pathlib.Path(sys.argv[1])
    if not ruta.is_file():
        print(f"No existe: {ruta}")
        return 2
    texto = ruta.read_text(encoding="utf-8")
    tokens, errores = lexear(texto)
    for t in tokens:
        print(t)
    print("--- TABLA DE LEXEMAS ---")
    tabla = TablaLexemas()
    for t in tokens:
        tabla.agregar(t)
    for e in tabla.como_lista():
        print(f"{e['tipo']} '{e['lexema']}' atributo={e['atributo']!r} "
              f"x{e['apariciones']} primera={e['primera_pos']}")
    if errores:
        print("--- ERRORES ---")
        for e in errores:
            print(f"{e['mensaje']} :: {e['fragmento']!r}")
    else:
        print("--- SIN ERRORES ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
