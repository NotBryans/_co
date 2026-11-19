# Week 11: Nand2Tetris Virtual Machine Translator (Chapters 7 & 8)

A complete Python implementation of the Nand2Tetris VM-to-Hack Assembly translator (`vm_translator.py`).

## Supported VM Commands
- **Arithmetic & Logical (Ch. 7):** `add`, `sub`, `neg`, `eq`, `gt`, `lt`, `and`, `or`, `not`
- **Memory Access (Ch. 7):** `push` and `pop` across `constant`, `local`, `argument`, `this`, `that`, `temp`, `pointer`, and `static`
- **Program Flow (Ch. 8):** `label`, `goto`, `if-goto`
- **Function Calling (Ch. 8):** `function`, `call`, `return`, plus automatic bootstrap code (`SP=256`, `call Sys.init 0`) when translating a directory containing `Sys.vm`.

## Usage
- Translate a single `.vm` file: `python vm_translator.py path/to/Program.vm`
- Translate a directory of `.vm` files: `python vm_translator.py path/to/ProjectFolder`
