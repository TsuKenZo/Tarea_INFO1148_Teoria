"""Analizador léxico de Prolog (subconjunto INFO1148).

Estrategia (§5 informe): cada ER equivale a su AFD minimizado.
Aquí se implementa con máxima coincidencia + prioridad por orden:
se prueba primero la alternativa más larga en cada posición.

Reglas de contexto (§6):
 - '-' es parte de NUMERO solo si el token previo NO es
   NUMERO/ATOMO/VARIABLE/CADENA/ATOMO_COMILLA ni ')' ']' '}'.
 - '.' es parte de NUMERO solo si está pegado entre dos dígitos.
"""
import re
from typing import List, Optional, Tuple

# Nota: main.py y run_tests.py agregan src/ a sys.path,
# por eso el import directo funciona en ambos casos.
from tokens import (
    ATOMO, ATOMO_COMILLA, CADENA, DELIM, NUMERO, OP_ARIT,
    OP_CLAUSULA, OP_CONTROL, OP_UNIF_COMP, VARIABLE,
    Token, atributo_para,
)


RE_VARIABLE = re.compile(r"[A-Z_][a-zA-Z0-9_]*")
RE_ATOMO = re.compile(r"[a-z][a-zA-Z0-9_]*")
RE_ENTERO = re.compile(r"[0-9]+")
RE_NUM_MAL_PUNTO_DOBLE = re.compile(r"[0-9]+\.\.[0-9]+")
RE_PUNTO_NUM_MAL = re.compile(r"\.[0-9]+")

# Previos que bloquean el '-' de NUMERO (informe §6).
TIPOS_BLOQUEAN_MENOS = {NUMERO, ATOMO, ATOMO_COMILLA, VARIABLE, CADENA}
CIERRES_BLOQUEAN_MENOS = {")", "]", "}"}


class ErrorLexico(Exception):
    pass


class Lexer:
    def __init__(self, texto: str):
        self.texto = texto
        self.n = len(texto)
        self.pos = 0
        self.linea = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.errores: List[dict] = []

    # ---- utilidades de posición ----
    def _peek(self, k: int = 0) -> str:
        i = self.pos + k
        return self.texto[i] if 0 <= i < self.n else ""

    def _avanzar(self, k: int = 1) -> None:
        for _ in range(k):
            if self.pos >= self.n:
                return
            c = self.texto[self.pos]
            self.pos += 1
            if c == "\n":
                self.linea += 1
                self.col = 1
            else:
                # '\t' cuenta como 1 columna (informe §7).
                self.col += 1

    def _emitir(self, tipo: str, lexema: str, linea: int, col: int,
                interior: str = "") -> None:
        atr = atributo_para(tipo, lexema, interior)
        self.tokens.append(Token(tipo, lexema, linea, col, atr))

    def _error(self, mensaje: str, linea: int, col: int, fragmento: str) -> None:
        self.errores.append({
            "mensaje": mensaje,
            "linea": linea,
            "columna": col,
            "fragmento": fragmento,
        })

    def _prev_token(self) -> Optional[Token]:
        return self.tokens[-1] if self.tokens else None

    def _menos_es_numero(self) -> bool:
        """¿El '-' en pos actual abre un NUMERO negativo? (§6).

        Regla informe: '-' es NUMERO salvo prev en
        NUMERO/ATOMO/VARIABLE/')'/']'. Excepción documentada:
        'X is -5' -> '-5' NUMERO, aunque 'is' sea ATOMO.
        'is'/'mod' son átomos-operadores, no operandos.
        """
        if self._peek() != "-" or not self._peek(1).isdigit():
            return False
        prev = self._prev_token()
        if prev is None:
            return True
        if prev.tipo == ATOMO and prev.lexema in ("is", "mod"):
            return True
        if prev.tipo in TIPOS_BLOQUEAN_MENOS:
            return False
        if prev.tipo == DELIM and prev.lexema in CIERRES_BLOQUEAN_MENOS:
            return False
        return True

    # ---- bucle principal ----
    def lexear(self) -> Tuple[List[Token], List[dict]]:
        while self.pos < self.n:
            c = self._peek()
            if c in (" ", "\t", "\r", "\n"):
                self._avanzar()
                continue
            if c == "%":
                self._lex_comentario_linea()
                continue
            if c == "/" and self._peek(1) == "*":
                if not self._lex_comentario_bloque():
                    break  # sin cierre: termina el análisis (§8).
                continue
            if c == "'":
                self._lex_comilla("'", ATOMO_COMILLA)
                continue
            if c == '"':
                self._lex_comilla('"', CADENA)
                continue
            if self._lex_numero_o_malformado():
                continue
            if c.isdigit() or (c == "-" and self._menos_es_numero()):
                # Fallback por seguridad (ya cubierto arriba).
                self._lex_numero_o_malformado()
                continue
            m = RE_VARIABLE.match(self.texto, self.pos)
            if m:
                lex = m.group(0)
                l, co = self.linea, self.col
                self._avanzar(len(lex))
                self._emitir(VARIABLE, lex, l, co)
                continue
            m = RE_ATOMO.match(self.texto, self.pos)
            if m:
                lex = m.group(0)
                l, co = self.linea, self.col
                self._avanzar(len(lex))
                # 'is' y 'mod' quedan como ATOMO (§3 alcance).
                self._emitir(ATOMO, lex, l, co)
                continue
            if self._lex_operador_o_delim():
                continue
            # Carácter no admitido (§8): se descarta 1 y se sigue.
            l, co = self.linea, self.col
            self._error(
                f"Error léxico: carácter no admitido '{c}' en línea {l}, columna {co}",
                l, co, c)
            self._avanzar()
        return self.tokens, self.errores

    # ---- comentarios ----
    def _lex_comentario_linea(self) -> None:
        # %[^\n]* : se descarta, no genera token.
        while self.pos < self.n and self._peek() != "\n":
            self._avanzar()

    def _lex_comentario_bloque(self) -> bool:
        # /\\* ... \\*/ : se descarta; sin cierre -> error y termina.
        l0, c0 = self.linea, self.col
        self._avanzar(2)  # consume /*
        while self.pos < self.n:
            if self._peek() == "*" and self._peek(1) == "/":
                self._avanzar(2)
                return True
            self._avanzar()
        self._error(
            f"Error léxico: comentario de bloque sin cerrar, "
            f"iniciado en línea {l0}, columna {c0}",
            l0, c0, "/*")
        return False

    # ---- comillas ----
    def _lex_comilla(self, delim: str, tipo: str) -> None:
        l0, c0 = self.linea, self.col
        self._avanzar()  # apertura
        interior: List[str] = []
        while self.pos < self.n:
            c = self._peek()
            if c == "\\" and self.pos + 1 < self.n:
                # backslash + CUALQUIER carácter (§4): se acepta.
                interior.append(c)
                interior.append(self._peek(1))
                self._avanzar(2)
                continue
            if c == delim:
                self._avanzar()  # cierre
                lexema = delim + "".join(interior) + delim
                self._emitir(tipo, lexema, l0, c0, "".join(interior))
                return
            if c == "\n":
                break  # sin cierre en la línea -> error.
            interior.append(c)
            self._avanzar()
        frag = delim + "".join(interior)
        nombre = "átomo" if tipo == ATOMO_COMILLA else "cadena"
        self._error(
            f"Error léxico: {nombre} sin cerrar, iniciado en línea {l0}, columna {c0}",
            l0, c0, frag)
        # Recuperación (§8): se descarta hasta fin de línea.
        while self.pos < self.n and self._peek() != "\n":
            self._avanzar()

    # ---- números ----
    def _lex_numero_o_malformado(self) -> bool:
        c = self._peek()
        # .14 : punto inicial sin dígito previo -> mal formado.
        m = RE_PUNTO_NUM_MAL.match(self.texto, self.pos)
        if m:
            lex = m.group(0)
            l, co = self.linea, self.col
            self._error(
                f"Error léxico: número mal formado '{lex}' en línea {l}, columna {co}",
                l, co, lex)
            self._avanzar(len(lex))
            return True
        # 3..14 : caso documentado informe §8.
        m = RE_NUM_MAL_PUNTO_DOBLE.match(self.texto, self.pos)
        if m and (c.isdigit() or (c == "-" and self._menos_es_numero())):
            lex = m.group(0)
            if lex.startswith("-") or c.isdigit():
                l, co = self.linea, self.col
                self._error(
                    f"Error léxico: número mal formado '{lex}' en línea {l}, columna {co}",
                    l, co, lex)
                self._avanzar(len(lex))
                return True
        # Inicio de número: dígito, o '-' negativo por contexto.
        es_neg = c == "-" and self._menos_es_numero()
        if not (c.isdigit() or es_neg):
            return False
        l0, c0 = self.linea, self.col
        pref = ""
        if es_neg:
            pref = "-"
            self._avanzar()  # consume '-'
        m = RE_ENTERO.match(self.texto, self.pos)
        if not m:
            # '-' no seguido de dígito (no debería pasar por _menos_es_numero).
            self.pos -= 0  # no-op defensivo
            # retrocede el '-' para que lo tome OP_ARIT.
            self.pos -= 1
            self.col -= 1
            return False
        entero = m.group(0)
        self._avanzar(len(entero))
        base = pref + entero
        # ¿ '.' pegado?
        if self._peek() == ".":
            nxt = self._peek(1)
            if nxt.isdigit():
                # 3.14 : float válido (punto entre dígitos, §6).
                self._avanzar()  # '.'
                dec = RE_ENTERO.match(self.texto, self.pos).group(0)  # type: ignore
                self._avanzar(len(dec))
                self._emitir(NUMERO, base + "." + dec, l0, c0)
                return True
            # Traza informe §5: '3.' aislado se rechaza.
            # Único caso válido dígitos+'.': fin de cláusula, o sea
            # '.' seguido de blanco/EOF/comentario (ej. 'mod 3.').
            # '3.)' con '.' pegado a ')' es mal formado.
            if nxt in (" ", "\t", "\r", "\n", "", "%"):
                # Fin de cláusula: entero válido, el '.' queda para DELIM.
                self._emitir(NUMERO, base, l0, c0)
                return True
            self._avanzar()  # consume '.'
            lex = base + "."
            self._error(
                f"Error léxico: número mal formado '{lex}' en línea {l0}, columna {c0}",
                l0, c0, lex)
            return True
        # ¿ dígitos seguidos de letra/_ pegado? 3abc -> mal formado.
        m2 = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.texto[self.pos:self.pos + 1])
        if m2 and self.pos < self.n and self.texto[self.pos].isalpha():
            # consume la cola alfanumérica completa.
            cola = re.match(r"[a-zA-Z0-9_]+", self.texto[self.pos:]).group(0)  # type: ignore
            lex = base + cola
            self._avanzar(len(cola))
            self._error(
                f"Error léxico: número mal formado '{lex}' en línea {l0}, columna {c0}",
                l0, c0, lex)
            return True
        # Entero válido.
        self._emitir(NUMERO, base, l0, c0)
        return True

    # ---- operadores y delimitadores (largo-primero = maximal munch) ----
    # Estrategia equivalente al AFD integrado (informe §7.1):
    # en cada posición se prueba la alternativa más larga primero.
    # Caso --> vs -: lookahead de 2 sin consumir; si tras '-' vienen
    # '-' y '>', se consumen los 3 como OP_CLAUSULA; si no, el '-'
    # se resuelve solo (OP_ARIT o signo NUMERO) y el siguiente char
    # se evalúa aparte. Así 'X --> Y' da 1 token y '5---3' da '-','-','-'.
    def _lex_operador_o_delim(self) -> bool:
        t = self.texto[self.pos:self.pos + 3]
        l, co = self.linea, self.col
        # 3 chars.
        if t.startswith("=.."):
            self._avanzar(3)
            self._emitir(OP_UNIF_COMP, "=..", l, co)
            return True
        if t.startswith("-->"):
            self._avanzar(3)
            self._emitir(OP_CLAUSULA, "-->", l, co)
            return True
        if t.startswith("\\=="):
            self._avanzar(3)
            self._emitir(OP_UNIF_COMP, "\\==", l, co)
            return True
        t2 = self.texto[self.pos:self.pos + 2]
        if t2 in (":-", "?-"):
            self._avanzar(2)
            self._emitir(OP_CLAUSULA, t2, l, co)
            return True
        if t2 in ("==", "\\=", "=<", ">=", "**", "//"):
            self._avanzar(2)
            tipo = OP_UNIF_COMP if t2 in ("==", "\\=", "=<", ">=") else OP_ARIT
            self._emitir(tipo, t2, l, co)
            return True
        if t2 == "\\+":
            self._avanzar(2)
            self._emitir(OP_CONTROL, "\\+", l, co)
            return True
        c = self._peek()
        if c in ("=", "<", ">"):
            self._avanzar()
            self._emitir(OP_UNIF_COMP, c, l, co)
            return True
        if c in ("+", "-", "*", "/"):
            self._avanzar()
            self._emitir(OP_ARIT, c, l, co)
            return True
        if c in ("!", ";", ","):
            self._avanzar()
            self._emitir(OP_CONTROL, c, l, co)
            return True
        if c in ("(", ")", "[", "]", "{", "}", "|", "."):
            self._avanzar()
            self._emitir(DELIM, c, l, co)
            return True
        if c == ":" or c == "?" or c == "\\":
            # ':'/'?' sueltos o '\' sin continuación -> no admitido.
            return False
        return False


def lexear(texto: str) -> Tuple[List[Token], List[dict]]:
    lx = Lexer(texto)
    return lx.lexear()
