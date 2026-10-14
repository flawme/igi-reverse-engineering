#!/usr/bin/env python3
"""
qvmdec.py - readable decompiler for Project IGI (1999) .qvm bytecode.

Turns the stack-machine instruction stream into call syntax:

    PUSHIIB <sym>            ->  the callee
    CALL n [block_0..block_{n-1}]
    BRA <after blocks>
    <block_0> ... BRK        ->  argument expressions

The VM model used here is taken from IGI.exe (see FINDINGS.md):
  * CALL pops the callee operand (a symbol index, type 1) off the stack,
    reads a u32 argument count at code[pos+1] and that many u32 offsets at
    code[pos+5], invokes the native function, then advances pos by 5+4*argc.
  * Each argument block is a self-contained statement terminated by BRK (0x00).
  * Binary ALU ops compute  first_pushed OP last_pushed  (see FINDINGS.md).

Usage:
    python3 qvmdec.py <file.qvm> [--raw] [--limit N]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qvm import QVM, OPCODES, OPERAND_SIZE  # noqa: E402

BINARY = {'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/', 'SHL': '<<', 'SHR': '>>',
          'AND': '&', 'OR': '|', 'XOR': '^', 'LAND': '&&', 'LOR': '||',
          'EQ': '==', 'NE': '!=', 'LT': '<', 'LE': '<=', 'GT': '>', 'GE': '>='}
UNARY = {'PLUS': '+', 'MINUS': '-', 'INV': '~', 'NOT': '!'}


class Val(object):
    """A value on the decompiler's simulated stack."""
    __slots__ = ('kind', 'value', 'text')

    def __init__(self, kind, value, text):
        self.kind = kind          # 'int' | 'float' | 'str' | 'sym' | 'expr'
        self.value = value        # python value when known
        self.text = text          # rendered source text

    def __repr__(self):
        return 'Val(%s,%r,%r)' % (self.kind, self.value, self.text)


def fmt_float(f):
    """Shortest decimal that round-trips to the same float32."""
    f32 = struct.unpack('<f', struct.pack('<f', f))[0]
    s = None
    for p in range(1, 10):
        cand = '%.*g' % (p, f32)
        if struct.unpack('<f', struct.pack('<f', float(cand)))[0] == f32:
            s = cand
            break
    if s is None:
        s = repr(f32)
    # prefer plain decimal notation for ordinary magnitudes
    if 'e' in s and 1e-4 <= abs(f32) < 1e7:
        plain = '%.*f' % (max(0, 6 - len(str(int(abs(f32))))), f32)
        plain = plain.rstrip('0').rstrip('.')
        if plain and struct.unpack('<f', struct.pack('<f', float(plain)))[0] == f32:
            s = plain
    if '.' not in s and 'e' not in s and 'n' not in s and 'i' not in s:
        s += '.0'
    return s


class Decompiler(object):
    def __init__(self, q):
        self.q = q
        self.code = q.code
        self.by_off = {}
        for ins in q.instructions:
            self.by_off[ins.offset] = ins
        self.lines = []
        self.visited = set()

    # ------------------------------------------------------------ primitives
    def ins_at(self, off):
        return self.by_off.get(off)

    def operand_int(self, ins):
        return int.from_bytes(ins.operand, 'little')

    def operand_signed(self, ins):
        return int.from_bytes(ins.operand, 'little', signed=True)

    def operand_float(self, ins):
        return struct.unpack('<f', ins.operand)[0]

    # ------------------------------------------------------- block evaluation
    def eval_block(self, off, depth=0):
        """Interpret the statement starting at `off` until BRK. Returns a Val."""
        stack = []
        i = off
        guard = 0
        while True:
            guard += 1
            if guard > 4096:
                return Val('expr', None, '<runaway@%#x>' % off)
            ins = self.ins_at(i)
            if ins is None:
                return Val('expr', None, '<bad@%#x>' % i)
            m = ins.mnemonic
            if m == 'BRK':
                break
            if m == 'POP':
                if stack:
                    stack.pop()
                i = self.next_off(ins)
                continue
            if m in ('PUSH', 'PUSHB', 'PUSHW'):
                stack.append(Val('int', self.operand_signed(ins),
                                 str(self.operand_signed(ins))))
            elif m == 'PUSHF':
                f = self.operand_float(ins)
                stack.append(Val('float', f, fmt_float(f)))
            elif m == 'PUSH0':
                stack.append(Val('int', 0, '0'))
            elif m == 'PUSH1':
                stack.append(Val('int', 1, '1'))
            elif m == 'PUSHM':
                stack.append(Val('int', -1, '-1'))
            elif m in ('PUSHSIB', 'PUSHSIW', 'PUSHSI', 'PUSHS'):
                v = self.operand_int(ins)
                s = self.q.string(v)
                stack.append(Val('str', s, '"%s"' % (s if s is not None else '?')))
            elif m in ('PUSHIIB', 'PUSHIIW', 'PUSHII', 'PUSHI'):
                v = self.operand_int(ins)
                s = self.q.symbol(v)
                stack.append(Val('sym', s, s if s is not None else 'sym%d' % v))
            elif m == 'PUSHA':
                stack.append(Val('expr', None, '&%d' % self.operand_int(ins)))
            elif m in BINARY:
                b = stack.pop() if stack else Val('expr', None, '?')
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(self.binop(m, a, b))
            elif m in UNARY:
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(self.unop(m, a))
            elif m == 'ASSIGN':
                b = stack.pop() if stack else Val('expr', None, '?')
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(Val('expr', None, '%s = %s' % (a.text, b.text)))
            elif m == 'CALL':
                args = self.do_call(ins, depth + 1)
                callee = stack.pop() if stack else Val('expr', None, '?')
                stack.append(Val('expr', None, '%s(%s)' %
                                 (callee.text, ', '.join(a.text for a in args))))
                end = self.next_off(ins)
                nxt = self.ins_at(end)
                if nxt is not None and nxt.mnemonic == 'BRA' and nxt.target is not None:
                    i = nxt.target
                else:
                    i = end
                continue
            elif m in ('BRA', 'BF', 'BT'):
                # a nested branch inside an argument block: render as a marker
                stack.append(Val('expr', None, '<branch>'))
                i = ins.target if ins.target is not None else self.next_off(ins)
                continue
            else:
                stack.append(Val('expr', None, '<%s>' % m))
            i = self.next_off(ins)
        if not stack:
            return Val('expr', None, 'void')
        return stack[-1]

    def next_off(self, ins):
        end = ins.offset + 1 + len(ins.operand)
        if ins.mnemonic == 'CALL' and ins.table is not None:
            end += 4 * len(ins.table)
        return end

    def binop(self, m, a, b):
        op = BINARY[m]
        if a.kind in ('int', 'float') and b.kind in ('int', 'float'):
            try:
                v = self.const_binop(m, a.value, b.value)
                if v is not None:
                    kind = 'int' if isinstance(v, int) else 'float'
                    txt = str(v) if kind == 'int' else fmt_float(v)
                    return Val(kind, v, txt)
            except ZeroDivisionError:
                pass
        return Val('expr', None, '(%s %s %s)' % (a.text, op, b.text))

    @staticmethod
    def const_binop(m, x, y):
        if m == 'ADD':
            return x + y
        if m == 'SUB':
            return x - y
        if m == 'MUL':
            return x * y
        if m == 'DIV':
            if isinstance(x, int) and isinstance(y, int):
                if y == 0:
                    return None
                q = abs(x) // abs(y)
                return -q if (x < 0) != (y < 0) else q   # C truncating division
            return x / y
        if m == 'SHL':
            return x << (y & 31)
        if m == 'SHR':
            return x >> (y & 31)
        if m == 'AND':
            return x & y
        if m == 'OR':
            return x | y
        if m == 'XOR':
            return x ^ y
        if m == 'LAND':
            return 1 if (x != 0 and y != 0) else 0
        if m == 'LOR':
            return 0 if (x == 0 and y == 0) else 1
        if m == 'EQ':
            return 1 if x == y else 0
        if m == 'NE':
            return 1 if x != y else 0
        if m == 'LT':
            return 1 if x < y else 0
        if m == 'LE':
            return 1 if x <= y else 0
        if m == 'GT':
            return 1 if x > y else 0
        if m == 'GE':
            return 1 if x >= y else 0
        return None

    def unop(self, m, a):
        if a.kind in ('int', 'float'):
            if m == 'PLUS':
                return a
            if m == 'MINUS':
                v = -a.value
                return Val(a.kind, v, str(v) if a.kind == 'int' else fmt_float(v))
            if m == 'INV' and a.kind == 'int':
                return Val('int', ~a.value, str(~a.value))
            if m == 'NOT':
                return Val('int', 0 if a.value else 1, '0' if a.value else '1')
        return Val('expr', None, '%s%s' % (UNARY[m], a.text))

    # ------------------------------------------------------------------- calls
    def do_call(self, ins, depth=0):
        """Render CALL: callee is the top of the simulated stack (handled by
        the caller); here we only render the argument list."""
        args = []
        if ins.table:
            for off in ins.table:
                args.append(self.eval_block(off, depth + 1))
        return args

    # -------------------------------------------------------------- statements
    def decompile(self):
        """Walk the code linearly, rendering one line per top-level statement."""
        i = 0
        n = len(self.code)
        stack = []
        out = []
        while i < n:
            ins = self.ins_at(i)
            if ins is None:
                out.append('; <undecoded at code+%#x>' % i)
                break
            m = ins.mnemonic
            if m == 'CALL':
                args = self.do_call(ins)
                callee = stack.pop() if stack else Val('expr', None, '?')
                out.append('%s(%s)' % (callee.text, ', '.join(a.text for a in args)))
                stack = []
                # skip the BRA and the inline argument blocks
                end = self.next_off(ins)
                nxt = self.ins_at(end)
                if nxt is not None and nxt.mnemonic == 'BRA' and nxt.target is not None:
                    i = nxt.target
                else:
                    i = end
                continue
            if m == 'POP':
                stack = []
                i = self.next_off(ins)
                continue
            if m in ('PUSH', 'PUSHB', 'PUSHW'):
                stack.append(Val('int', self.operand_signed(ins), str(self.operand_signed(ins))))
            elif m == 'PUSHF':
                f = self.operand_float(ins)
                stack.append(Val('float', f, fmt_float(f)))
            elif m == 'PUSH0':
                stack.append(Val('int', 0, '0'))
            elif m == 'PUSH1':
                stack.append(Val('int', 1, '1'))
            elif m == 'PUSHM':
                stack.append(Val('int', -1, '-1'))
            elif m in ('PUSHSIB', 'PUSHSIW', 'PUSHSI', 'PUSHS'):
                v = self.operand_int(ins)
                s = self.q.string(v)
                stack.append(Val('str', s, '"%s"' % (s if s is not None else '?')))
            elif m in ('PUSHIIB', 'PUSHIIW', 'PUSHII', 'PUSHI'):
                v = self.operand_int(ins)
                s = self.q.symbol(v)
                stack.append(Val('sym', s, s if s is not None else 'sym%d' % v))
            elif m in BINARY:
                b = stack.pop() if stack else Val('expr', None, '?')
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(self.binop(m, a, b))
            elif m in UNARY:
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(self.unop(m, a))
            elif m == 'ASSIGN':
                b = stack.pop() if stack else Val('expr', None, '?')
                a = stack.pop() if stack else Val('expr', None, '?')
                stack.append(Val('expr', None, '%s = %s' % (a.text, b.text)))
            elif m == 'BRA':
                i = ins.target if ins.target is not None else self.next_off(ins)
                continue
            elif m in ('BF', 'BT'):
                cond = stack.pop() if stack else Val('expr', None, '?')
                out.append('if (%s%s) goto code+%#x;' %
                           ('' if m == 'BT' else '!', cond.text, ins.target))
                i = self.next_off(ins)
                continue
            elif m == 'BRK':
                out.append('; BRK')
            else:
                out.append('; %s %s' % (m, self.q.format_operand(ins)))
            i = self.next_off(ins)
        return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    q = QVM(open(path, 'rb').read(), path)
    d = Decompiler(q)
    for line in d.decompile():
        print(line)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
