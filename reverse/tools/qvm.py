#!/usr/bin/env python3
"""
qvm.py - Disassembler for Project IGI (Innerloop Studios, 1999) .qvm bytecode.

Format summary (all little-endian):

  Header (60 bytes):
    0x00  char[4]  magic "LOOP"
    0x04  u32      version (8 in retail)
    0x08  u32      section count (5)
    0x0C  u32      off0   0x10 u32 off1   0x14 u32 size0  0x18 u32 size1
    0x1C  u32      off2   0x20 u32 off3   0x24 u32 size2  0x28 u32 size3
    0x2C  u32      off4   0x30 u32 size4
    0x34  u32      0      0x38 u32 0
    Sections are contiguous: off0=0x3C, off_i+size_i = off_{i+1}, off4+size4 = filesize.

  Section 0: u32[] offsets into section 1
  Section 1: symbol table (NUL-terminated strings: function/enum/event names)
  Section 2: u32[] offsets into section 3
  Section 3: string constant table (NUL-terminated strings)
  Section 4: code

  Code: instruction stream.  Opcodes are 1 byte; operand size is fixed per opcode.
  CALL (0x18) is followed by a u32 argument count and then that many u32 offsets
  (relative to the start of section 4) naming the argument statements, which are
  emitted inline after the following BRA.

Opcode names come from IGI.exe (file offset 0x148394); the VM opcode numbering is
the reverse of that table: vm_op = 48 - index.
"""
import struct
import sys
import os

MAGIC = b'LOOP'

# index order as stored in IGI.exe at 0x148394
_NAME_TABLE = [
    "ILLEGAL", "BLK", "NOT", "INV", "MINUS", "PLUS", "ASSIGN", "GE", "GT", "LE",
    "LT", "NE", "EQ", "LOR", "LAND", "XOR", "OR", "AND", "SHR", "SHL", "DIV",
    "MUL", "SUB", "ADD", "CALL", "JSR", "BT", "BF", "BRA", "RET", "POP", "PUSHM",
    "PUSH1", "PUSH0", "PUSHIIW", "PUSHIIB", "PUSHII", "PUSHI", "PUSHSIW",
    "PUSHSIB", "PUSHSI", "PUSHS", "PUSHA", "PUSHF", "PUSHW", "PUSHB", "PUSH",
    "NOP", "BRK",
]
_N = len(_NAME_TABLE)  # 49

# operand size in bytes (after the opcode byte)
_OPERAND = {
    "PUSH": 4, "PUSHB": 1, "PUSHW": 2, "PUSHF": 4, "PUSHA": 4, "PUSHS": 4,
    "PUSHSI": 4, "PUSHSIB": 1, "PUSHSIW": 2, "PUSHI": 4, "PUSHII": 4,
    "PUSHIIB": 1, "PUSHIIW": 2, "PUSH0": 0, "PUSH1": 0, "PUSHM": 4,
    "POP": 0, "RET": 0, "BRA": 4, "BF": 4, "BT": 4, "JSR": 4, "CALL": 4,
    "BRK": 0, "NOP": 0,
}
for _nm in ("NOT", "INV", "MINUS", "PLUS", "ASSIGN", "GE", "GT", "LE", "LT",
            "NE", "EQ", "LOR", "LAND", "XOR", "OR", "AND", "SHR", "SHL", "DIV",
            "MUL", "SUB", "ADD", "ILLEGAL", "BLK"):
    _OPERAND[_nm] = 0

OPCODES = {}          # vm opcode -> mnemonic
OPERAND_SIZE = {}     # vm opcode -> operand size
for _i, _nm in enumerate(_NAME_TABLE):
    _op = (_N - 1) - _i
    OPCODES[_op] = _nm
    OPERAND_SIZE[_op] = _OPERAND[_nm]

PUSH_MNEMONICS = {"PUSH", "PUSHB", "PUSHW", "PUSHF", "PUSHA", "PUSHS", "PUSHSI",
                  "PUSHSIB", "PUSHSIW", "PUSHI", "PUSHII", "PUSHIIB", "PUSHIIW",
                  "PUSHM"}
BRANCH_MNEMONICS = {"BRA", "BF", "BT", "JSR"}


class QVMError(Exception):
    pass


class Section(object):
    def __init__(self, index, offset, size, data):
        self.index = index
        self.offset = offset
        self.size = size
        self.data = data


class Instruction(object):
    __slots__ = ("offset", "opcode", "mnemonic", "operand", "table", "target")

    def __init__(self, offset, opcode, mnemonic, operand, table=None, target=None):
        self.offset = offset
        self.opcode = opcode
        self.mnemonic = mnemonic
        self.operand = operand
        self.table = table
        self.target = target


class QVM(object):
    def __init__(self, data, path="<memory>"):
        self.data = data
        self.path = path
        self.parse_header()
        self.parse_sections()
        self.parse_tables()
        self.parse_code()

    # ---------------------------------------------------------------- header
    def parse_header(self):
        d = self.data
        if len(d) < 0x3C:
            raise QVMError("file too short (%d bytes)" % len(d))
        if d[:4] != MAGIC:
            raise QVMError("bad magic %r (expected 'LOOP')" % d[:4])
        self.magic = d[:4]
        self.version, self.section_count = struct.unpack_from('<II', d, 4)
        (self.off0, self.off1, self.size0, self.size1,
         self.off2, self.off3, self.size2, self.size3,
         self.off4, self.size4) = struct.unpack_from('<10I', d, 0x0C)
        self.reserved = struct.unpack_from('<2I', d, 0x34)
        self.sections = [
            (self.off0, self.size0), (self.off1, self.size1),
            (self.off2, self.size2), (self.off3, self.size3),
            (self.off4, self.size4),
        ]
        self.warnings = []
        if self.off0 != 0x3C:
            self.warnings.append("off0=%#x (expected 0x3c)" % self.off0)
        for i in range(4):
            if self.sections[i][0] + self.sections[i][1] != self.sections[i + 1][0]:
                self.warnings.append("section %d not contiguous" % i)
        if self.off4 + self.size4 != len(d):
            self.warnings.append("section 4 does not end at EOF")

    def parse_sections(self):
        self.sec = []
        for i, (off, size) in enumerate(self.sections):
            if off + size > len(self.data):
                raise QVMError("section %d out of range" % i)
            self.sec.append(Section(i, off, size, self.data[off:off + size]))

    # ------------------------------------------------------- symbol/strings
    def parse_tables(self):
        self.symbol_offsets = self._u32_table(self.sec[0])
        self.symbols = self._strings(self.sec[1], self.symbol_offsets)
        self.string_offsets = self._u32_table(self.sec[2])
        self.strings = self._strings(self.sec[3], self.string_offsets)

    @staticmethod
    def _u32_table(sec):
        n = sec.size // 4
        return list(struct.unpack_from('<%dI' % n, sec.data, 0)) if n else []

    @staticmethod
    def _strings(sec, offsets):
        out = []
        for o in offsets:
            if o >= sec.size:
                out.append(None)
                continue
            end = sec.data.find(b'\0', o)
            if end < 0:
                end = sec.size
            out.append(sec.data[o:end].decode('latin-1'))
        return out

    # ---------------------------------------------------------------- code
    def parse_code(self):
        code = self.sec[4].data
        self.code = code
        self.instructions = []
        self.code_error = None
        self.call_tables = []
        i = 0
        n = len(code)
        while i < n:
            op = code[i]
            mnemonic = OPCODES.get(op)
            if mnemonic is None:
                self.code_error = "unknown opcode %#04x at code+%#x" % (op, i)
                break
            size = _OPERAND[mnemonic]
            if i + 1 + size > n:
                self.code_error = "truncated %s at code+%#x" % (mnemonic, i)
                break
            operand = code[i + 1:i + 1 + size]
            table = None
            target = None
            end = i + 1 + size
            if mnemonic == "CALL":
                argc = struct.unpack('<I', operand)[0] if size == 4 else 0
                if end + 4 * argc > n:
                    self.code_error = "CALL table overflow at code+%#x" % i
                    break
                table = list(struct.unpack_from('<%dI' % argc, code, end)) if argc else []
                self.call_tables.append((i, argc, table))
                end += 4 * argc
            elif mnemonic in BRANCH_MNEMONICS and size == 4:
                rel = struct.unpack('<I', operand)[0]
                target = end + rel
            self.instructions.append(Instruction(i, op, mnemonic, operand, table, target))
            i = end

    # -------------------------------------------------------------- helpers
    def symbol(self, index):
        if 0 <= index < len(self.symbols):
            return self.symbols[index]
        return None

    def string(self, index):
        if 0 <= index < len(self.strings):
            return self.strings[index]
        return None

    def format_operand(self, ins):
        m = ins.mnemonic
        if m in PUSH_MNEMONICS and ins.operand:
            v = int.from_bytes(ins.operand, 'little')
            if m == "PUSHF":
                f = struct.unpack('<f', ins.operand)[0]
                return "%g (%#x)" % (f, v)
            if m in ("PUSHSIB", "PUSHSIW", "PUSHS", "PUSHSI"):
                s = self.string(v)
                if s is not None:
                    return "%d ; %r" % (v, s)
            if m in ("PUSHIIB", "PUSHIIW", "PUSHII", "PUSHI"):
                s = self.symbol(v)
                if s is not None:
                    return "%d ; %s" % (v, s)
            return "%d (%#x)" % (v, v)
        if m == "CALL":
            argc = int.from_bytes(ins.operand, 'little')
            return "%d args" % argc
        if m in BRANCH_MNEMONICS and ins.operand:
            rel = int.from_bytes(ins.operand, 'little')
            return "code+%#x (rel %d)" % (ins.target, rel)
        return ""

    # ----------------------------------------------------------------- dump
    def dump(self, out=sys.stdout, show_hex=False):
        w = out.write
        w("=" * 78 + "\n")
        w("QVM file: %s  (%d bytes)\n" % (self.path, len(self.data)))
        w("=" * 78 + "\n")
        w("Header\n")
        w("  magic          : %r\n" % self.magic)
        w("  version        : %d\n" % self.version)
        w("  section count  : %d\n" % self.section_count)
        w("  reserved       : %s\n" % (self.reserved,))
        w("  Section table (offset/size/type):\n")
        names = ["0 symbol-offset table", "1 symbol names (strings)",
                 "2 string-offset table", "3 string constants", "4 code"]
        for i, (off, size) in enumerate(self.sections):
            w("    [%d] off=%#08x size=%#08x end=%#08x  %s\n"
              % (i, off, size, off + size, names[i]))
        for warn in self.warnings:
            w("  WARNING: %s\n" % warn)

        w("\nSymbol table (section 0 -> section 1): %d entries\n" % len(self.symbols))
        for i, s in enumerate(self.symbols):
            w("    [%2d] @%#06x  %s\n" % (i, self.symbol_offsets[i], s))

        w("\nString table (section 2 -> section 3): %d entries\n" % len(self.strings))
        for i, s in enumerate(self.strings):
            w("    [%2d] @%#06x  %r\n" % (i, self.string_offsets[i], s))

        w("\nCode (section 4): %d bytes\n" % len(self.code))
        if self.code_error:
            w("  DISASSEMBLY ERROR: %s\n" % self.code_error)
        w("  %-8s %-8s %-10s %s\n" % ("offset", "opcode", "mnemonic", "operand"))
        for ins in self.instructions:
            hexb = ins.operand.hex() if show_hex else ""
            w("  %-8s %-8s %-10s %s %s\n"
              % ("+%#06x" % ins.offset, "%#04x" % ins.opcode, ins.mnemonic,
                 self.format_operand(ins), hexb))
            if ins.table is not None and ins.table:
                w("           arg table: %s\n"
                  % ", ".join("code+%#x" % t for t in ins.table))


def main(argv):
    if len(argv) >= 2 and argv[1] == '--findings':
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'FINDINGS.md')
        try:
            sys.stdout.write(open(path).read())
        except OSError as e:
            print("cannot read %s: %s" % (path, e))
            return 1
        return 0
    if len(argv) < 2:
        print("usage: qvm.py <file.qvm> [...]   |   qvm.py --findings")
        return 2
    rc = 0
    for path in argv[1:]:
        try:
            data = open(path, 'rb').read()
            q = QVM(data, path)
            q.dump()
            print()
        except (QVMError, OSError) as e:
            print("ERROR %s: %s" % (path, e))
            rc = 1
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv))
