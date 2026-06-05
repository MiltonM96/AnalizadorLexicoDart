# Analizador Léxico — Dart

Trabajo Práctico de **Teoría de Computabilidad**. Analizador léxico para el lenguaje **Dart**, implementado mediante un **Autómata Finito Determinista (AFD) manual** en Python, sin uso de expresiones regulares ni generadores de lexers.

La interfaz es una aplicación web construida con Flask que permite ingresar código Dart y visualizar la tabla de tokens resultante en tiempo real.

---

## Características

- Reconoce más de 25 tipos de tokens: palabras reservadas, tipos primitivos, constantes numéricas (enteras, reales, hexadecimales), cadenas (simples, dobles, triple-quote, raw), operadores aritméticos, lógicos, de comparación, bitwise, null-aware, spread, cascade, flecha, ternario y de tipo, delimitadores y comentarios (línea y bloque anidado).
- Lookahead de hasta 3 caracteres para resolver ambigüedades (`??=`, `...?`, `>>>=`, etc.).
- Recuperación de errores: ante un token malformado no detiene el análisis, emite un token `ERROR` con mensaje descriptivo y continúa.
- Cada token registra línea y columna exactas.
- Interfaz web con tabla de tokens, estadísticas y ejemplos precargados.

---

## Requisitos

- Python 3.10 o superior
- Flask 3.0 o superior

---

## Instalación y uso

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd analizadorLexicoTp

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar el servidor
python app.py
```

Abrir el navegador en `http://localhost:5000`.

---

## Estructura del proyecto

```
analizadorLexicoTp/
├── app.py              # Servidor Flask (API REST)
├── lexer.py            # Módulo léxico — AFD manual
├── requirements.txt
└── templates/
    └── index.html      # Interfaz web
```

---

## Tipos de tokens reconocidos

| Token | Descripción | Ejemplo |
|---|---|---|
| `KEYWORD` | Palabras reservadas | `if`, `return`, `class` |
| `TYPE` | Tipos primitivos | `int`, `String`, `bool` |
| `LIT_INT` | Constante entera | `42`, `0xFF` |
| `LIT_DOUBLE` | Constante real | `3.14`, `1e10` |
| `LIT_STRING_SQ` | Cadena comilla simple | `'hola'` |
| `LIT_STRING_DQ` | Cadena comilla doble | `"hola"` |
| `LIT_BOOL` | Literal booleano | `true`, `false` |
| `LIT_NULL` | Literal null | `null` |
| `IDENTIFIER` | Identificador | `miVariable` |
| `OP_ARITH` | Operador aritmético | `+`, `-`, `~/` |
| `OP_ASSIGN` | Operador de asignación | `=`, `+=`, `??=` |
| `OP_COMPARE` | Operador de comparación | `==`, `!=`, `<=` |
| `OP_LOGIC` | Operador lógico | `&&`, `\|\|`, `!` |
| `OP_BITWISE` | Operador bit a bit | `&`, `\|`, `>>>` |
| `OP_TERNARY` | Operador ternario | `?`, `:` |
| `OP_NULL` | Operador null-aware | `??`, `?.` |
| `OP_SPREAD` | Operador spread | `...`, `...?` |
| `OP_CASCADE` | Operador cascada | `..` |
| `OP_ARROW` | Operador flecha | `=>`, `->` |
| `OP_TYPE` | Operador de tipo | `is`, `as` |
| `DELIMITER` | Delimitador | `(`, `{`, `;` |
| `COMMENT_LINE` | Comentario de línea | `// ...` |
| `COMMENT_BLOCK` | Comentario de bloque | `/* ... */` |
| `WHITESPACE` | Espacio / tabulación | ` `, `\t` |
| `NEWLINE` | Salto de línea | `\n` |
| `ERROR` | Error léxico | `@`, cadena sin cerrar |

---

## API

### `POST /analyze`

**Body (JSON):**
```json
{
  "source": "void main() { print('Hola'); }",
  "include_whitespace": false
}
```

**Respuesta (JSON):**
```json
{
  "tokens": [
    { "type": "Palabra reservada", "type_key": "KEYWORD", "lexeme": "void", "line": 1, "col": 1, "error_msg": "" },
    ...
  ],
  "total": 12,
  "visible": 10,
  "errors": 0,
  "lines": 1,
  "counts": { "Palabra reservada": 2, "Identificador": 1, ... }
}
```
