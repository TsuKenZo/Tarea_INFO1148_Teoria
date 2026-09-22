"""Runner minimo: lexea los 2 archivos completos y resume."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from lexer import lexear

BASE = pathlib.Path(__file__).resolve().parent


def chequear(nombre: str, espera_errores: bool) -> int:
    texto = (BASE / nombre).read_text(encoding="utf-8")
    toks, errs = lexear(texto)
    tipos = {t.tipo for t in toks}
    print(f"== {nombre}: {len(toks)} tokens, {len(errs)} errores, tipos={sorted(tipos)}")
    for e in errs:
        print(f"   {e['mensaje']} :: {e['fragmento']!r}")
    if espera_errores and not errs:
        print(f"   FALLO: se esperaban errores en {nombre}")
        return 1
    if not espera_errores and errs:
        print(f"   FALLO: no se esperaban errores en {nombre}")
        return 1
    return 0


if __name__ == "__main__":
    rc = 0
    rc |= chequear("prog_limpio.pl", False)
    rc |= chequear("prog_errores.pl", True)
    print("OK" if rc == 0 else "FALLOS")
    raise SystemExit(rc)
