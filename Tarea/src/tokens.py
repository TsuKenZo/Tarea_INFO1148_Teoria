"""Tipos de token y tabla de lexemas.

Base formal: informe §4 (tabla especificación léxica).
Los nombres de token son los del informe y deben coincidir
con lo documentado en Overleaf.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# Categorías del subconjunto (informe §4).
ATOMO = "ATOMO"
ATOMO_COMILLA = "ATOMO_COMILLA"
VARIABLE = "VARIABLE"
NUMERO = "NUMERO"
CADENA = "CADENA"
OP_CLAUSULA = "OP_CLAUSULA"
OP_UNIF_COMP = "OP_UNIF_COMP"
OP_ARIT = "OP_ARIT"
OP_CONTROL = "OP_CONTROL"
DELIM = "DELIM"

# Solo estas categorías van a la tabla (contenido variable).
CATEGORIAS_TABLA = {ATOMO, ATOMO_COMILLA, VARIABLE, NUMERO, CADENA}


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int
    atributo: Optional[Any] = None

    def __str__(self) -> str:
        return f"<{self.tipo}, '{self.lexema}', {self.linea}, {self.columna}>"


# Secuencias con significado especial (informe §4, tabla escapes).
_ESCAPES_ESPECIALES = {
    "n": "\n",
    "t": "\t",
    "'": "'",
    '"': '"',
    "\\": "\\",
}


def resolver_escapes(contenido: str) -> str:
    """Resuelve escapes de ATOMO_COMILLA / CADENA.

    ER informe: backslash + CUALQUIER carácter es léxicamente válido.
    Solo los 5 pares de la tabla tienen significado especial;
    en cualquier otro caso (ej. \\a, \\x) se ignora el backslash
    y se conserva el carácter siguiente, sin error.
    """
    out: List[str] = []
    i = 0
    while i < len(contenido):
        c = contenido[i]
        if c == "\\" and i + 1 < len(contenido):
            nxt = contenido[i + 1]
            out.append(_ESCAPES_ESPECIALES.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def atributo_para(tipo: str, lexema: str, contenido_interior: str = "") -> Optional[Any]:
    """Atributo conservado por token (informe §4, tabla atributos)."""
    if tipo in (ATOMO, VARIABLE):
        return lexema
    if tipo in (ATOMO_COMILLA, CADENA):
        return resolver_escapes(contenido_interior)
    if tipo == NUMERO:
        return float(lexema) if "." in lexema else int(lexema)
    return None


class TablaLexemas:
    """Diccionario (tipo, lexema) -> entrada, sin duplicados."""

    def __init__(self) -> None:
        self._t: Dict[Tuple[str, str], Dict] = {}

    def agregar(self, tok: Token) -> None:
        if tok.tipo not in CATEGORIAS_TABLA:
            return
        clave = (tok.tipo, tok.lexema)
        if clave in self._t:
            self._t[clave]["apariciones"] += 1
        else:
            self._t[clave] = {
                "tipo": tok.tipo,
                "lexema": tok.lexema,
                "atributo": tok.atributo,
                "apariciones": 1,
                "primera_pos": (tok.linea, tok.columna),
            }

    def como_lista(self) -> List[Dict]:
        return sorted(self._t.values(), key=lambda e: e["primera_pos"])
