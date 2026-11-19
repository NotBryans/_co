import os
import sys


class Parser:
    ARITHMETIC = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

    def __init__(self, filepath):
        self.lines = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                clean = line.split("//")[0].strip()
                if clean:
                    self.lines.append(clean)
        self.index = -1
        self.current = ""

    def has_more_commands(self):
        return self.index + 1 < len(self.lines)

    def advance(self):
        self.index += 1
        self.current = self.lines[self.index]

    def command_type(self):
        cmd = self.current.split()[0]
        if cmd in self.ARITHMETIC:
            return "C_ARITHMETIC"
        return {
            "push": "C_PUSH",
            "pop": "C_POP",
            "label": "C_LABEL",
            "goto": "C_GOTO",
            "if-goto": "C_IF",
            "function": "C_FUNCTION",
            "return": "C_RETURN",
            "call": "C_CALL",
        }[cmd]

    def arg1(self):
        parts = self.current.split()
        return parts[0] if self.command_type() == "C_ARITHMETIC" else parts[1]

    def arg2(self):
        return int(self.current.split()[2])


class CodeWriter:
    SEGMENTS = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, output_path):
        self.out = open(output_path, "w", encoding="utf-8")
        self.filename = ""
        self.current_function = ""
        self.label_count = 0
        self.call_count = 0

    def set_file_name(self, filename):
        self.filename = os.path.splitext(os.path.basename(filename))[0]

    def write(self, lines):
        for line in lines:
            self.out.write(line + "\n")

    def write_init(self):
        self.write([
            "// Bootstrap code",
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ])
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, cmd):
        self.write([f"// {cmd}"])
        if cmd in {"add", "sub", "and", "or"}:
            op = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}[cmd]
            self.write([
                "@SP", "AM=M-1", "D=M", "A=A-1", f"M={op}",
            ])
        elif cmd in {"neg", "not"}:
            op = "-" if cmd == "neg" else "!"
            self.write([
                "@SP", "A=M-1", f"M={op}M",
            ])
        elif cmd in {"eq", "gt", "lt"}:
            jmp = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[cmd]
            lbl_true = f"TRUE_{self.label_count}"
            lbl_end = f"END_{self.label_count}"
            self.label_count += 1
            self.write([
                "@SP", "AM=M-1", "D=M", "A=A-1", "D=M-D",
                f"@{lbl_true}", f"D;{jmp}",
                "@SP", "A=M-1", "M=0",
                f"@{lbl_end}", "0;JMP",
                f"({lbl_true})",
                "@SP", "A=M-1", "M=-1",
                f"({lbl_end})",
            ])

    def _push_d(self):
        self.write(["@SP", "A=M", "M=D", "@SP", "M=M+1"])

    def write_push_pop(self, cmd_type, segment, index):
        self.write([f"// {cmd_type} {segment} {index}"])
        if cmd_type == "C_PUSH":
            if segment == "constant":
                self.write([f"@{index}", "D=A"])
            elif segment in self.SEGMENTS:
                self.write([f"@{self.SEGMENTS[segment]}", "D=M", f"@{index}", "A=D+A", "D=M"])
            elif segment == "temp":
                self.write([f"@{5 + index}", "D=M"])
            elif segment == "pointer":
                self.write([f"@{'THIS' if index == 0 else 'THAT'}", "D=M"])
            elif segment == "static":
                self.write([f"@{self.filename}.{index}", "D=M"])
            self._push_d()
        else:
            if segment in self.SEGMENTS:
                self.write([
                    f"@{self.SEGMENTS[segment]}", "D=M", f"@{index}", "D=D+A",
                    "@R13", "M=D",
                    "@SP", "AM=M-1", "D=M",
                    "@R13", "A=M", "M=D",
                ])
            elif segment == "temp":
                self.write(["@SP", "AM=M-1", "D=M", f"@{5 + index}", "M=D"])
            elif segment == "pointer":
                self.write(["@SP", "AM=M-1", "D=M", f"@{'THIS' if index == 0 else 'THAT'}", "M=D"])
            elif segment == "static":
                self.write(["@SP", "AM=M-1", "D=M", f"@{self.filename}.{index}", "M=D"])

    def _scoped_label(self, label):
        return f"{self.current_function}${label}" if self.current_function else label

    def write_label(self, label):
        self.write([f"({self._scoped_label(label)})"])

    def write_goto(self, label):
        self.write([f"@{self._scoped_label(label)}", "0;JMP"])

    def write_if(self, label):
        self.write(["@SP", "AM=M-1", "D=M", f"@{self._scoped_label(label)}", "D;JNE"])

    def write_function(self, func_name, num_locals):
        self.current_function = func_name
        self.write([f"// function {func_name} {num_locals}", f"({func_name})"])
        for _ in range(num_locals):
            self.write(["@0", "D=A"])
            self._push_d()

    def write_call(self, func_name, num_args):
        ret_label = f"{func_name}$ret.{self.call_count}"
        self.call_count += 1
        self.write([f"// call {func_name} {num_args}"])
        self.write([f"@{ret_label}", "D=A"])
        self._push_d()
        for seg in ("LCL", "ARG", "THIS", "THAT"):
            self.write([f"@{seg}", "D=M"])
            self._push_d()
        self.write([
            "@SP", "D=M", "@5", "D=D-A", f"@{num_args}", "D=D-A", "@ARG", "M=D",
            "@SP", "D=M", "@LCL", "M=D",
            f"@{func_name}", "0;JMP",
            f"({ret_label})",
        ])

    def write_return(self):
        self.write([
            "// return",
            "@LCL", "D=M", "@R13", "M=D",
            "@5", "A=D-A", "D=M", "@R14", "M=D",
            "@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D",
            "@ARG", "D=M+1", "@SP", "M=D",
        ])
        for offset, seg in ((1, "THAT"), (2, "THIS"), (3, "ARG"), (4, "LCL")):
            self.write(["@R13", "D=M", f"@{offset}", "A=D-A", "D=M", f"@{seg}", "M=D"])
        self.write(["@R14", "A=M", "0;JMP"])

    def close(self):
        self.out.close()


def translate(target_path):
    if os.path.isdir(target_path):
        vm_files = [
            os.path.join(target_path, f)
            for f in sorted(os.listdir(target_path))
            if f.endswith(".vm")
        ]
        folder_name = os.path.basename(os.path.normpath(target_path))
        output_path = os.path.join(target_path, f"{folder_name}.asm")
        needs_bootstrap = any(os.path.basename(f) == "Sys.vm" for f in vm_files)
    else:
        vm_files = [target_path]
        output_path = os.path.splitext(target_path)[0] + ".asm"
        needs_bootstrap = False

    writer = CodeWriter(output_path)
    if needs_bootstrap:
        writer.write_init()

    for vm_file in vm_files:
        writer.set_file_name(vm_file)
        parser = Parser(vm_file)
        while parser.has_more_commands():
            parser.advance()
            ctype = parser.command_type()
            if ctype == "C_ARITHMETIC":
                writer.write_arithmetic(parser.arg1())
            elif ctype in ("C_PUSH", "C_POP"):
                writer.write_push_pop(ctype, parser.arg1(), parser.arg2())
            elif ctype == "C_LABEL":
                writer.write_label(parser.arg1())
            elif ctype == "C_GOTO":
                writer.write_goto(parser.arg1())
            elif ctype == "C_IF":
                writer.write_if(parser.arg1())
            elif ctype == "C_FUNCTION":
                writer.write_function(parser.arg1(), parser.arg2())
            elif ctype == "C_CALL":
                writer.write_call(parser.arg1(), parser.arg2())
            elif ctype == "C_RETURN":
                writer.write_return()

    writer.close()
    print(f"Translated -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python vm_translator.py <file.vm | directory>")
        sys.exit(1)
    translate(sys.argv[1])
