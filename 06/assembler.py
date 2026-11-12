import sys, os

COMP = {
    "0":"0101010", "1":"0111111", "-1":"0111010",
    "D":"0001100", "A":"0110000", "!D":"0001101", "!A":"0110001",
    "-D":"0001111", "-A":"0110011", "D+1":"0011111", "A+1":"0110111",
    "D-1":"0001110", "A-1":"0110010", "D+A":"0000010", "D-A":"0010011",
    "A-D":"0000111", "D&A":"0000000", "D|A":"0010101",
    "M":"1110000", "!M":"1110001", "-M":"1110011", "M+1":"1110111",
    "M-1":"1110010", "D+M":"1000010", "D-M":"1010011", "M-D":"1000111",
    "D&M":"1000000", "D|M":"1010101"
}
DEST = {"":"000", "M":"001", "D":"010", "MD":"011", "DM":"011", "A":"100", "AM":"101", "AD":"110", "AMD":"111"}
JUMP = {"":"000", "JGT":"001", "JEQ":"010", "JGE":"011", "JLT":"100", "JNE":"101", "JLE":"110", "JMP":"111"}

def assemble(asm_text):
    symbols = {f"R{i}": i for i in range(16)}
    symbols.update({"SP":0, "LCL":1, "ARG":2, "THIS":3, "THAT":4, "SCREEN":16384, "KBD":24576})

    lines = []
    rom_addr = 0
    for raw in asm_text.splitlines():
        line = raw.split("//")[0].strip()
        if not line: continue
        if line.startswith("(") and line.endswith(")"):
            symbols[line[1:-1]] = rom_addr
        else:
            lines.append(line)
            rom_addr += 1

    ram_addr = 16
    out = []
    for line in lines:
        if line.startswith("@"):
            token = line[1:]
            if token.isdigit():
                val = int(token)
            else:
                if token not in symbols:
                    symbols[token] = ram_addr
                    ram_addr += 1
                val = symbols[token]
            out.append(f"0{val:015b}")
        else:
            dest, rest = line.split("=", 1) if "=" in line else ("", line)
            comp, jump = rest.split(";", 1) if ";" in rest else (rest, "")
            out.append("111" + COMP[comp] + DEST[dest] + JUMP[jump])
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    targets = sys.argv[1:] or [f for f in os.listdir(".") if f.endswith(".asm")]
    for path in targets:
        with open(path, "r", encoding="utf-8") as f:
            hack = assemble(f.read())
        out_path = os.path.splitext(path)[0] + ".hack"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(hack)
        print(f"Assembled {path} -> {out_path}")
