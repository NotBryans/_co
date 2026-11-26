import os
import re
import sys

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static", "var",
    "int", "char", "boolean", "void", "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
}
SYMBOLS = set("{}()[].,;+-*/&|<>=~")
TOKEN_RE = re.compile(
    r'"[^"\n]*"|\d+|[A-Za-z_]\w*|[{}()\[\].,;+\-*/&|<>=~]'
)


class JackTokenizer:
    def __init__(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        # Strip block comments (/* ... */) and line comments (// ...)
        code = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
        code = re.sub(r"//.*", "", code)
        self.tokens = TOKEN_RE.findall(code)
        self.idx = 0

    def has_more(self):
        return self.idx < len(self.tokens)

    def peek(self, offset=0):
        pos = self.idx + offset
        return self.tokens[pos] if pos < len(self.tokens) else None

    def advance(self):
        tok = self.tokens[self.idx]
        self.idx += 1
        return tok

    def token_type(self, tok):
        if tok in KEYWORDS:
            return "KEYWORD"
        if tok in SYMBOLS:
            return "SYMBOL"
        if tok.startswith('"'):
            return "STRING_CONST"
        if tok.isdigit():
            return "INT_CONST"
        return "IDENTIFIER"


class SymbolTable:
    def __init__(self):
        self.class_table = {}
        self.sub_table = {}
        self.counts = {"STATIC": 0, "FIELD": 0, "ARG": 0, "VAR": 0}

    def start_subroutine(self):
        self.sub_table.clear()
        self.counts["ARG"] = 0
        self.counts["VAR"] = 0

    def define(self, name, typ, kind):
        idx = self.counts[kind]
        self.counts[kind] += 1
        target = self.class_table if kind in ("STATIC", "FIELD") else self.sub_table
        target[name] = (typ, kind, idx)

    def var_count(self, kind):
        return self.counts[kind]

    def _lookup(self, name):
        if name in self.sub_table:
            return self.sub_table[name]
        return self.class_table.get(name)

    def kind_of(self, name):
        entry = self._lookup(name)
        return entry[1] if entry else None

    def type_of(self, name):
        entry = self._lookup(name)
        return entry[0] if entry else None

    def index_of(self, name):
        entry = self._lookup(name)
        return entry[2] if entry else None


class VMWriter:
    KIND_TO_SEG = {"STATIC": "static", "FIELD": "this", "ARG": "argument", "VAR": "local"}

    def __init__(self, out_path):
        self.out = open(out_path, "w", encoding="utf-8")

    def write_push(self, segment, index):
        self.out.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        self.out.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, cmd):
        self.out.write(f"{cmd}\n")

    def write_label(self, label):
        self.out.write(f"label {label}\n")

    def write_goto(self, label):
        self.out.write(f"goto {label}\n")

    def write_if(self, label):
        self.out.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.out.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.out.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.out.write("return\n")

    def close(self):
        self.out.close()


class CompilationEngine:
    BIN_OPS = {
        "+": "add", "-": "sub", "&": "and", "|": "or",
        "<": "lt", ">": "gt", "=": "eq",
    }

    def __init__(self, tokenizer, vm):
        self.tk = tokenizer
        self.vm = vm
        self.sym = SymbolTable()
        self.class_name = ""
        self.label_id = 0

    def _next_label(self, prefix):
        lbl = f"{prefix}_{self.label_id}"
        self.label_id += 1
        return lbl

    def _eat(self, expected=None):
        tok = self.tk.advance()
        if expected and tok != expected:
            raise SyntaxError(f"Expected '{expected}', got '{tok}'")
        return tok

    def compile_class(self):
        self._eat("class")
        self.class_name = self._eat()
        self._eat("{")
        while self.tk.peek() in ("static", "field"):
            self.compile_class_var_dec()
        while self.tk.peek() in ("constructor", "function", "method"):
            self.compile_subroutine()
        self._eat("}")

    def compile_class_var_dec(self):
        kind = self._eat().upper()
        typ = self._eat()
        self.sym.define(self._eat(), typ, kind)
        while self.tk.peek() == ",":
            self._eat(",")
            self.sym.define(self._eat(), typ, kind)
        self._eat(";")

    def compile_subroutine(self):
        self.sym.start_subroutine()
        sub_kind = self._eat()
        self._eat()  # return type
        sub_name = self._eat()
        if sub_kind == "method":
            self.sym.define("this", self.class_name, "ARG")

        self._eat("(")
        self.compile_parameter_list()
        self._eat(")")

        self._eat("{")
        while self.tk.peek() == "var":
            self.compile_var_dec()

        n_locals = self.sym.var_count("VAR")
        self.vm.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_kind == "constructor":
            self.vm.write_push("constant", self.sym.var_count("FIELD"))
            self.vm.write_call("Memory.alloc", 1)
            self.vm.write_pop("pointer", 0)
        elif sub_kind == "method":
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)

        self.compile_statements()
        self._eat("}")

    def compile_parameter_list(self):
        if self.tk.peek() == ")":
            return
        typ = self._eat()
        self.sym.define(self._eat(), typ, "ARG")
        while self.tk.peek() == ",":
            self._eat(",")
            typ = self._eat()
            self.sym.define(self._eat(), typ, "ARG")

    def compile_var_dec(self):
        self._eat("var")
        typ = self._eat()
        self.sym.define(self._eat(), typ, "VAR")
        while self.tk.peek() == ",":
            self._eat(",")
            self.sym.define(self._eat(), typ, "VAR")
        self._eat(";")

    def compile_statements(self):
        while self.tk.peek() in ("let", "if", "while", "do", "return"):
            cmd = self.tk.peek()
            if cmd == "let":
                self.compile_let()
            elif cmd == "if":
                self.compile_if()
            elif cmd == "while":
                self.compile_while()
            elif cmd == "do":
                self.compile_do()
            elif cmd == "return":
                self.compile_return()

    def compile_let(self):
        self._eat("let")
        var_name = self._eat()
        seg = VMWriter.KIND_TO_SEG[self.sym.kind_of(var_name)]
        idx = self.sym.index_of(var_name)
        is_array = False

        if self.tk.peek() == "[":
            is_array = True
            self._eat("[")
            self.compile_expression()
            self._eat("]")
            self.vm.write_push(seg, idx)
            self.vm.write_arithmetic("add")

        self._eat("=")
        self.compile_expression()
        self._eat(";")

        if is_array:
            self.vm.write_pop("temp", 0)
            self.vm.write_pop("pointer", 1)
            self.vm.write_push("temp", 0)
            self.vm.write_pop("that", 0)
        else:
            self.vm.write_pop(seg, idx)

    def compile_if(self):
        lbl_else = self._next_label("IF_FALSE")
        lbl_end = self._next_label("IF_END")
        self._eat("if")
        self._eat("(")
        self.compile_expression()
        self._eat(")")
        self.vm.write_arithmetic("not")
        self.vm.write_if(lbl_else)
        self._eat("{")
        self.compile_statements()
        self._eat("}")
        if self.tk.peek() == "else":
            self.vm.write_goto(lbl_end)
            self.vm.write_label(lbl_else)
            self._eat("else")
            self._eat("{")
            self.compile_statements()
            self._eat("}")
            self.vm.write_label(lbl_end)
        else:
            self.vm.write_label(lbl_else)

    def compile_while(self):
        lbl_exp = self._next_label("WHILE_EXP")
        lbl_end = self._next_label("WHILE_END")
        self._eat("while")
        self.vm.write_label(lbl_exp)
        self._eat("(")
        self.compile_expression()
        self._eat(")")
        self.vm.write_arithmetic("not")
        self.vm.write_if(lbl_end)
        self._eat("{")
        self.compile_statements()
        self._eat("}")
        self.vm.write_goto(lbl_exp)
        self.vm.write_label(lbl_end)

    def compile_do(self):
        self._eat("do")
        self._compile_subroutine_call()
        self._eat(";")
        self.vm.write_pop("temp", 0)

    def compile_return(self):
        self._eat("return")
        if self.tk.peek() != ";":
            self.compile_expression()
        else:
            self.vm.write_push("constant", 0)
        self._eat(";")
        self.vm.write_return()

    def compile_expression(self):
        self.compile_term()
        while self.tk.peek() in ("+", "-", "*", "/", "&", "|", "<", ">", "="):
            op = self._eat()
            self.compile_term()
            if op == "*":
                self.vm.write_call("Math.multiply", 2)
            elif op == "/":
                self.vm.write_call("Math.divide", 2)
            else:
                self.vm.write_arithmetic(self.BIN_OPS[op])

    def compile_term(self):
        tok = self.tk.peek()
        ttype = self.tk.token_type(tok)

        if ttype == "INT_CONST":
            self.vm.write_push("constant", int(self._eat()))
        elif ttype == "STRING_CONST":
            s = self._eat()[1:-1]
            self.vm.write_push("constant", len(s))
            self.vm.write_call("String.new", 1)
            for ch in s:
                self.vm.write_push("constant", ord(ch))
                self.vm.write_call("String.appendChar", 2)
        elif tok in ("true", "false", "null", "this"):
            self._eat()
            if tok == "true":
                self.vm.write_push("constant", 0)
                self.vm.write_arithmetic("not")
            elif tok in ("false", "null"):
                self.vm.write_push("constant", 0)
            else:
                self.vm.write_push("pointer", 0)
        elif tok == "(":
            self._eat("(")
            self.compile_expression()
            self._eat(")")
        elif tok in ("-", "~"):
            op = self._eat()
            self.compile_term()
            self.vm.write_arithmetic("neg" if op == "-" else "not")
        elif self.tk.peek(1) in ("(", "."):
            self._compile_subroutine_call()
        elif self.tk.peek(1) == "[":
            var_name = self._eat()
            self._eat("[")
            self.compile_expression()
            self._eat("]")
            seg = VMWriter.KIND_TO_SEG[self.sym.kind_of(var_name)]
            self.vm.write_push(seg, self.sym.index_of(var_name))
            self.vm.write_arithmetic("add")
            self.vm.write_pop("pointer", 1)
            self.vm.write_push("that", 0)
        else:
            var_name = self._eat()
            seg = VMWriter.KIND_TO_SEG[self.sym.kind_of(var_name)]
            self.vm.write_push(seg, self.sym.index_of(var_name))

    def _compile_subroutine_call(self):
        name = self._eat()
        n_args = 0
        if self.tk.peek() == ".":
            self._eat(".")
            sub_name = self._eat()
            kind = self.sym.kind_of(name)
            if kind is not None:
                self.vm.write_push(VMWriter.KIND_TO_SEG[kind], self.sym.index_of(name))
                full_name = f"{self.sym.type_of(name)}.{sub_name}"
                n_args = 1
            else:
                full_name = f"{name}.{sub_name}"
        else:
            self.vm.write_push("pointer", 0)
            full_name = f"{self.class_name}.{name}"
            n_args = 1

        self._eat("(")
        n_args += self.compile_expression_list()
        self._eat(")")
        self.vm.write_call(full_name, n_args)

    def compile_expression_list(self):
        count = 0
        if self.tk.peek() == ")":
            return count
        self.compile_expression()
        count += 1
        while self.tk.peek() == ",":
            self._eat(",")
            self.compile_expression()
            count += 1
        return count


def compile_file(jack_path):
    vm_path = os.path.splitext(jack_path)[0] + ".vm"
    tk = JackTokenizer(jack_path)
    vm = VMWriter(vm_path)
    engine = CompilationEngine(tk, vm)
    engine.compile_class()
    vm.close()
    print(f"Compiled {jack_path} -> {vm_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)
    target = sys.argv[1]
    if os.path.isdir(target):
        for fname in sorted(os.listdir(target)):
            if fname.endswith(".jack"):
                compile_file(os.path.join(target, fname))
    else:
        compile_file(target)


if __name__ == "__main__":
    main()
