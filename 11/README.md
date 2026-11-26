# Week 12: Nand2Tetris Jack Compiler (Chapter 11)

A complete Python implementation of the Nand2Tetris Jack-to-VM compiler (`JackCompiler.py`).

## Components
- **JackTokenizer**: Strips comments and tokenizes Jack source code into keywords, symbols, integer constants, string constants, and identifiers.
- **SymbolTable**: Tracks class-level (`static`, `field`) and subroutine-level (`arg`, `var`) scopes.
- **VMWriter**: Emits Nand2Tetris VM commands (`push`, `pop`, arithmetic, branching, `function`, `call`, `return`).
- **CompilationEngine**: Recursive-descent parser and code generator supporting classes, constructors, methods, functions, expressions, arrays, strings, and control flow (`if`/`else`, `while`, `let`, `do`, `return`).

## Usage
1. Compile a single `.jack` file: `python JackCompiler.py path/to/Main.jack`
2. Compile a Chapter 11 project folder: `python JackCompiler.py path/to/ProjectFolder`
