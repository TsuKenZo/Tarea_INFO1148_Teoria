# Análisis léxico del lenguaje Prolog — Teoría de la Computación (INFO1148)

Analizador léxico para un subconjunto acotado de Prolog.
Recorre archivos fuente de izquierda a derecha y produce tokens con
tipo, lexema, línea y columna, más tabla de lexemas y errores léxicos.

## Autores

* Vicente Álvarez
* Joaquin Cantero
* Juan Sepúlveda (jefe de grupo)

Profesor: Prof. M. Lévano — Entrega: 22/09/2026

## Requisitos

Solo Python 3 stdlib (`re`, `dataclasses`, `pathlib`). Sin dependencias.

## Estructura

```
Tarea/
  src/
    tokens.py   # Token + TablaLexemas
    lexer.py    # lexear(texto) -> tokens, errores
    main.py     # CLI
  tests/
    prog_limpio.pl    # entrada completa sin errores
    prog_errores.pl   # entrada con errores recuperables
    run_tests.py
```

## Ejecución

```bash
python3 src/main.py tests/prog_limpio.pl
python3 src/main.py tests/prog_errores.pl
python3 tests/run_tests.py
```

Salida por token:

```
<ATOMO, 'padre', 2, 1>
```

Tabla de lexemas: solo `ATOMO, ATOMO_COMILLA, VARIABLE, NUMERO, CADENA`
(clave `(tipo, lexema)`, sin duplicados, con conteo).

Errores: mensaje con línea, columna y fragmento, con recuperación
(descarta carácter / hasta fin de línea; bloque sin cierre termina).

## Base formal

Ver informe completo en PDF (`Tarea_JefeGrupo_Sepulveda.pdf`):
§4 especificación + ER, §5 autómatas Thompson/subconjuntos/minimización,
§6 prioridad y máxima coincidencia.

Convenciones: línea/columna desde 1, `\t` = 1 columna,
`-` de NUMERO por contexto, `.` float solo si `dígito.dígito` pegado.
