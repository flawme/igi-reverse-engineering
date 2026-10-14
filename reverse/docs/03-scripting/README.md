# 03 - Scripting System (QVM)

**Status: solved and verified.** The container, the section layout, the instruction
encoding and the opcode table were all extracted from the retail data and from
`IGI.exe`, and the disassembler runs clean on **all 997** `.qvm` files with zero
errors and zero desyncs. Byte-level tables are in
[16-verified-formats](../16-verified-formats/README.md).

## QVM File Format (LOOP v8)

Header, proven on 997/997 files:

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"LOOP"` |
| 0x04 | 4 | uint32 | version = 8 |
| 0x08 | 4 | uint32 | section count = 5 |
| 0x0C | 4 | uint32 | section 0 offset (always 0x3C) |
| 0x10 | 4 | uint32 | section 1 offset |
| 0x14 | 4 | uint32 | section 0 size |
| 0x18 | 4 | uint32 | section 1 size |
| 0x1C | 4 | uint32 | section 2 offset |
| 0x20 | 4 | uint32 | section 3 offset |
| 0x24 | 4 | uint32 | section 2 size |
| 0x28 | 4 | uint32 | section 3 size |
| 0x2C | 4 | uint32 | section 4 offset |
| 0x30 | 4 | uint32 | section 4 size |
| 0x34 | 8 | | two reserved words, 0 |

The five `(offset, size)` pairs are stored **interleaved**, not as a flat table.
Sections tile the file exactly: `off0 = 0x3C`, `off_i + size_i = off_{i+1}`,
`off4 + size4 = filesize`. Verified on all 997 files.

## Sections

| Index | Contents |
|-------|----------|
| 0 | `uint32[]` offsets into section 1 |
| 1 | **symbol table** - function, enum and event names |
| 2 | `uint32[]` offsets into section 3 |
| 3 | **string constants** |
| 4 | **code** |

Example (`config.qvm`): section 1 holds `GOStart, GOContentControlPW, GOPlayer, ...,
MoveLeft, KEY_LEFT, ...` (76 entries). Example (`weapon.qvm`): section 3 holds
`WEAPON_ID_AK47, AK47, <KALASHNIKOV>, ..., ak47_loop_e`.

## Instruction encoding

**1-byte opcode followed by a fixed-size operand.** The operand width is a property of
the opcode, not a length prefix.

Evidence: `IGI.exe` contains the string
`"Script: Internal Error: Unknown opcode: %02X."`, and its disassembler registers a
handler per opcode at VA `0x4c0f70`.

- `00` bytes are the real opcode **BRK**, not padding - proven by a `BF` target in
  `observer.qvm` landing on a `00` byte.
- Branches are relative to the **end** of the instruction; the exe's own disassembler
  prints `@(value+5)` for a 5-byte branch.
- `CALL` is followed by a `uint32` argument count and that many `uint32` offsets
  (relative to section 4) naming inline argument statements that a following `BRA`
  skips.

## Opcode table

The opcode **names** come from a 49-entry name table in `IGI.exe` at file offset
`0x148394`:

```
ILLEGAL BLK NOT INV MINUS PLUS ASSIGN GE GT LE LT NE EQ LOR LAND XOR OR AND SHR SHL
DIV MUL SUB ADD CALL JSR BT BF BRA RET POP PUSHM PUSH1 PUSH0 PUSHIIW PUSHIIB PUSHII
PUSHI PUSHSIW PUSHSIB PUSHSI PUSHS PUSHA PUSHF PUSHW PUSHB PUSH NOP BRK
```

The **numbering is the reverse of that list**: `vm_opcode = 48 - index_in_list`.

Three independent confirmations:

1. `IGI.exe` VA `0x4bec9e` is a switch returning the name for an opcode; its cases run
   `XOR, LAND, LOR, EQ, NE, LT, LE, GT, GE, ASSIGN, PLUS, MINUS, INV, NOT, BLK, ILLEGAL`
   - descending list order equals ascending opcode order.
2. `IGI.exe` VA `0x4c0f70` registers disassembler handlers per opcode: `2 -> PUSH`
   (4-byte), `3 -> PUSHB` (1), `4 -> PUSHW` (2), `5 -> PUSHF` (4, float),
   `8..14 -> PUSH*I*` family, `0x14/0x15/0x16 -> BRA/BF/BT` (4-byte relative),
   `0x18 -> CALL` (arg count + table); everything else uses a default handler that
   prints the opcode and advances 1 byte.
3. The bytecode's own semantics: opcode `0x18` is always followed by a count + offset
   table, `0x12` always terminates a statement, `0x14` always skips inline argument
   code, `0x0d` operands are always valid symbol indices, `0x09`/`0x0a` operands are
   always valid string indices, `0x05` operands are always sane floats.

| Op | Name | Operand | Confidence |
|----|------|---------|------------|
| 0x00 | BRK | 0 | PROVEN |
| 0x01 | NOP | 0 | INFERRED |
| 0x02 | PUSH | 4 (int32) | PROVEN |
| 0x03 | PUSHB | 1 (int8) | PROVEN |
| 0x04 | PUSHW | 2 (int16) | PROVEN |
| 0x05 | PUSHF | 4 (float32) | PROVEN |
| 0x06 | PUSHA | 4 (int32) | PROVEN |
| 0x07 | PUSHS | inline NUL-terminated string | PROVEN |
| 0x08 | PUSHSI | 4 | PROVEN |
| 0x09 | PUSHSIB | 1 | PROVEN |
| 0x0a | PUSHSIW | 2 | PROVEN |
| 0x0b | PUSHI | inline NUL-terminated string | PROVEN |
| 0x0c | PUSHII | 4 | PROVEN |
| 0x0d | PUSHIIB | 1 | PROVEN |
| 0x0e | PUSHIIW | 2 | PROVEN |
| 0x0f | PUSH0 | 0 | PROVEN |
| 0x10 | PUSH1 | 0 | PROVEN |
| 0x11 | PUSHM | 0 (pushes -1) | PROVEN |
| 0x12 | POP | 0 | PROVEN |
| 0x13 | RET | 0 (halt stub) | PROVEN |
| 0x14 | BRA | 4 (relative to end) | PROVEN |
| 0x15 | BF | 4 (relative to end) | PROVEN |
| 0x16 | BT | 4 (relative to end) | PROVEN |
| 0x17 | JSR | 0 (unimplemented stub) | PROVEN |
| 0x18 | CALL | 4 + argc*4 | PROVEN |
| 0x19 | ADD | 0 | INFERRED |
| 0x1a | SUB | 0 | INFERRED |
| 0x1b | MUL | 0 | INFERRED |
| 0x1c | DIV | 0 | INFERRED |
| 0x1d | SHL | 0 | INFERRED |
| 0x1e | SHR | 0 | INFERRED |
| 0x1f | AND | 0 | INFERRED |
| 0x20 | OR | 0 | INFERRED |
| 0x21 | XOR | 0 | INFERRED |
| 0x22 | LAND | 0 | INFERRED |
| 0x23 | LOR | 0 | INFERRED |
| 0x24 | EQ | 0 | INFERRED |
| 0x25 | NE | 0 | INFERRED |
| 0x26 | LT | 0 | INFERRED |
| 0x27 | LE | 0 | INFERRED |
| 0x28 | GT | 0 | INFERRED |
| 0x29 | GE | 0 | INFERRED |
| 0x2a | ASSIGN | 0 | INFERRED |
| 0x2b | PLUS | 0 | INFERRED |
| 0x2c | MINUS | 0 | INFERRED |
| 0x2d | INV | 0 | INFERRED |
| 0x2e | NOT | 0 | INFERRED |
| 0x2f | BLK | 0 | INFERRED |
| 0x30 | ILLEGAL | 0 | INFERRED |

25 opcodes actually appear in the retail data and all 25 are PROVEN. The rest are named
from the exe's table but never emitted by the retail compiler, so their operand widths
and semantics are inferred.

## Execution model

A **stack machine** with typed pushes: `PUSHB` (1 byte), `PUSHW` (2 bytes), `PUSHF`
(float32), `PUSHSIB`/`PUSHSIW` (string index), `PUSHIIB` (symbol index), `PUSH0`,
`PUSH1`.

Readable examples:

```c
// ammo/1000/ammo.qvm
DefineAmmoType(13, "AMMO_ID_1000", "<1000>", "<1000DESC>", 1000, 3.5, 250, 200,
               0, 255, 255, 0, 0, "115_01_1", "Sound0")

// level1/ai/1205.qvm
if (GetCurrentEventType() == AIEVENT_CREATE) { DefaultHandler(); }
```

## Events and actions

| Claim | Status |
|-------|--------|
| 24 events | ✅ Confirmed - exactly 24 distinct `AIEVENT_*` symbols (earlier revisions said 22) |
| 17 actions | ❌ **Not confirmed** - the data has 18 `AIAction_*` / 37 `AIFunction_*` defined, 12 / 30 used |

## Execution semantics

**ALU.** All 17 arithmetic/logic opcodes share one interpreter handler at
`IGI.exe` VA `0x4bdad0`. It pops two operands, coerces them to a common type, and
dispatches through `0x4be3e8` (integer) or `0x4be42c` (float).

- Integer ops are **signed**: `imul`, `idiv`, `sar`, and `setl`/`setle`/`setg`/`setge`.
- Comparisons push integer `0` or `1`.
- Float ops use x87 with an unordered-safe `test ah,0x41`.
- `SHL`/`SHR`/`AND`/`OR`/`XOR` on floats raise error 6.
- **Operand order is proven** from two independent code paths: `PUSH a; PUSH b; OP`
  computes `a OP b`.

**Reserved header words.** The loader at VA `0x4bd0b0` reads them at `0x4bd10e` and
`0x4bd119`:

| Offset | Meaning | Default when 0 |
|--------|---------|----------------|
| 0x34 | value-stack size, in entries | `0x800` |
| 0x38 | type-stack size, in entries | `0x100` |

They size the stacks that `push_int`/`push_float` index. All 997 retail files carry
`(0, 0)`, so the defaults apply.

## QVM interpreter internals (IGI.exe)

The interpreter loop, the handler table and the native call convention were located by
static disassembly of `IGI.exe` (PE32, imagebase `0x400000`). Every claim below cites
the instruction that proves it.

### The interpreter loop

`0x4bce60` is the fetch/dispatch loop:

```
0x004bce65  mov dword [esi+0x2c], 0        ; ctx->break = 0
0x004bce6c  mov eax, [esi+0x20]            ; ctx->halt
0x004bce71  jne 0x4bce99                   ; halted -> return
0x004bce73  mov eax, [esi+0x14]            ; ctx->pc
0x004bce76  mov ecx, [esi]                 ; ctx->code
0x004bce7c  mov dl, byte [eax+ecx]         ; opcode = code[pc]
0x004bce84  lea ecx, [eax+eax*2]           ; 3*opcode
0x004bce88  call dword [ecx*8 + 0xa96868]  ; table[opcode*6 + 0](ctx, 0, opcode, 0)
0x004bce8f  mov eax, [esi+0x2c]            ; ctx->break
0x004bce97  je 0x4bce6c                    ; loop while break == 0
```

- The handler table is `uint32[49][6]` at `0xa96868` (24-byte stride). The setter
  `0x4bd260` computes the slot: `lea eax,[eax+eax*2]` (3*opcode), `lea edx,[ecx+eax*2]`
  (mode + 6*opcode), `mov dword [edx*4 + 0xa96868], handler`. Only modes 0, 1, 3 are
  populated.
- Handler signature: `handler(ctx, arg2, opcode, mode)`. Mode 0 = execute, mode 1 =
  return the mnemonic (`0x4beb40`), mode 3 = the exe's own disassembler (`0x4c0f70`).
- The loop runs while `ctx->halt == 0 && ctx->break == 0`.
- `0x4bcf10` is the top-level run entry: it resets `pc = 0`, both stack pointers to
  capacity, `break`/`halt`/`errpc = 0`, calls `0x4bce60`, then decodes `ctx->halt` into
  one of 15 messages (table at `0x4bd06c`).

### The push family

| Op | Name | Operand | Pushes | Confidence | Evidence |
|----|------|---------|--------|------------|----------|
| 0x02 | PUSH | 4-byte int | type 1 | PROVEN | `0x4be7c3` -> `0x4bd890`; `mov dword [edx+ecx*4], 1` at `0x4bd8a5` |
| 0x06 | PUSHA | 4-byte int | type 5 | PROVEN | `0x4be7ae` -> `0x4be7e0`; `mov dword [edx+ecx*4], 5` at `0x4be7f5` |
| 0x07 | PUSHS | inline NUL-terminated string | type 3 (literal) | PROVEN | `0x4be86e` `cmp cl, 7` -> tag 3 |
| 0x0b | PUSHI | inline NUL-terminated string | type 4 (identifier) | PROVEN | `0x4be873` `cmp cl, 0xb` -> tag 4 |
| 0x08/0x09/0x0a | PUSHSI/B/W | u32 / u8 / u16 | string table (section 2/3) | PROVEN | `0x4be961` / `0x4be8e6` / `0x4be92d` |
| 0x0c/0x0d/0x0e | PUSHII/B/W | u32 / u8 / u16 | symbol table (section 0/1) | PROVEN | `0x4be96b` / `0x4be921` / `0x4be946` |
| 0x0f/0x10 | PUSH0/PUSH1 | none | 0 / 1 | PROVEN | `0x4be6c0` / `0x4be6a0` |
| 0x11 | PUSHM | none | -1 | PROVEN | `0x4be6e5` `push 0xffffffff` -> `0x4bd890` |
| 0x13 | RET | none | halt stub | PROVEN | registered to `0x4beb20` at `0x4bd3a9` |
| 0x17 | JSR | none | halt stub | PROVEN | registered to `0x4beb20` at `0x4bd3b6` |

- **`PUSH*I*` are the same lookups at different widths.** The string forms resolve
  through `0x4bead0(&ctx->0x30, index)` into section 3 (offsets in section 2); the symbol
  forms resolve the index through the record arrays at `ctx+0x60`/`ctx+0x64` (lazily
  resolved from the name descriptor at `ctx+0x48`, sections 0/1) and push the record with
  type 6 (`0x4beaa0`; `mov dword [edx+ecx*4], 6` at `0x4beab5`). The 4-byte forms are
  unused in retail data but fully implemented.
- **`PUSHS`/`PUSHI`** both take an inline NUL-terminated string and advance
  `pc += 1 + strlen + 1` (`lea ecx,[ecx+edx+2]` at `0x4be8b4`). The tag distinguishes
  them: type 3 is a literal, type 4 is an identifier resolved against the symbol table by
  `0x4bcc20` (`call 0x4baa30` at `0x4bcc69`; failure -> halt 7 "Undefined symbol" at
  `0x4bcc89`).
- **`PUSHA` (0x06) is vestigial.** It pushes a 4-byte immediate tagged type 5; no
  interpreter path consumes type 5 specially (the only comparison is the generic scalar
  pop `0x4bcb7c cmp ecx, 5`), the exe's own disassembler registers no handler for opcode
  6, and the opcode occurs **0 times** in all 997 retail `.qvm` files.
- **`JSR` and `RET` are halt stubs**: both are registered to `0x4beb20`, which sets
  `ctx->halt = 5` ("Illegal instruction"). Neither appears in retail data.

### BRK

`0x4beb10` sets the break flag:

```
0x004beb10  mov eax, [esp+4]         ; ctx
0x004beb14  mov dword [eax+0x2c], 1  ; ctx->break = 1
```

`BRK` is the statement/function terminator, required because the interpreter is
re-entrant: `0x4bc970` (the argument evaluator) sets `ctx->pc = argtable[i]`
(`mov [eax+0x14], ecx` at `0x4bc999`) and calls `0x4bce60` (`call 0x4bce60` at
`0x4bc9a0`) to run each inline argument fragment, which ends at its own `BRK`. It is the
most common opcode in the retail tree (374,365 occurrences).

### Native call convention

Native functions live in the **global symbol table** at `0xa445d8` (lookup `0x4baa30`,
intern `0x4baa60`) as 28-byte records created by `0x4ba970`:

| Off | Meaning | Evidence |
|-----|---------|----------|
| +0x00 | kind: 0 = variable, 1 = native function, 2 = constant | `mov [esi], edx` at `0x4ba9c8` |
| +0x04 | kind 1: return type (0 = int, 2 = float, 3 = string) | `mov [esi+4], eax` at `0x4ba9ca` |
| +0x08 | flags (0 for kind 1; for kind 0, nonzero = "resolved") | `0x4be990` |
| +0x0c | kind 0: storage width (1/2/4); kind 1: registration arg4 | `mov [esi+0x0c], ecx` at `0x4ba9be` |
| +0x10 | kind 1: native function pointer; kind 0/2: value getter | `mov [esi+0x10], edx` at `0x4ba9b0` |
| +0x14 | interned name | `mov [esi+0x14], eax` at `0x4ba9a9` |
| +0x18 | kind 0: data pointer; kind 1: registration arg3; kind 2: constant value | `mov [esi+0x18], eax` at `0x4ba9b7` |

`CALL` (0x18) at `0x4bd710`:

- Requires `kind == 1`: `cmp dword [ecx], 1` at `0x4bd739`; otherwise halt 9
  ("Identifier not a function", `mov dword [ebx+0x20], 9` at `0x4bd822`).
- Reads `argc = *(u32*)(code+pc+1)` (`mov edx, [eax+1]` at `0x4bd756`) and
  `argtable = code+pc+5` (`add eax, 5` at `0x4bd759`), then builds a callframe
  `{argc@+0x00, mode@+0x04 = 1, argarray@+0x08, ctx@+0x0c, argtable@+0x10}`.
- Calls the native function as `fn(&retbuf, record->0x18, &frame)`: `push eax` (&frame)
  at `0x4bd783`, `push edx` (record->0x18) at `0x4bd788`, `push eax` (&retbuf) at
  `0x4bd789`, `call dword [ecx+0x10]` at `0x4bd78e`.
- The return value is a 24-byte struct `{int@+0x00, double@+0x08, char*@+0x10}`, copied
  with `rep movsd` (6 dwords) at `0x4bd7a2` and pushed per `record->0x04` (string at
  `0x4bd7db`, float at `0x4bd7f4`, int at `0x4bd80b`).
- `pc += argc*4 + 5` (`lea edx, [ebp + ecx*4 + 5]` at `0x4bd7c0`).
- Arguments are pulled by the native side with `0x4b88d0` (int), `0x4b8900` (float) and
  `0x4b8930` (string), which run each inline argument statement through `0x4bc970`.

### VM context layout

Allocated as one block by the loader `0x4bd0b0` (`lea edi, [edx*4 + 0x46c]` at
`0x4bd147`):

| Off | Meaning | Evidence |
|-----|---------|----------|
| +0x00 | code base (section 4) | `mov [edx], eax` at `0x4bd16f` |
| +0x14 | pc (byte offset into section 4) | `mov eax, [esi+0x14]` at `0x4bce73` |
| +0x18 | value-stack pointer (index, grows down) | `0x4bd890` |
| +0x1c | type-stack pointer (index, grows down) | `0x4bd890` |
| +0x20 | halt code (0 = running) | `mov eax, [esi+0x20]` at `0x4bce6c` |
| +0x2c | break flag | `mov dword [esi+0x2c], 0` at `0x4bce65` |
| +0x30 | string-table descriptor `{count@+0x08, max@+0x0c, offsets@+0x10, base@+0x14}` | `0x4bead0` |
| +0x48 | symbol-table descriptor (same shape) | `lea ecx, [esi+0x48]` at `0x4be9e0` |

The value stack is a pair of parallel arrays (value + type) growing down from capacity.
Type tags: 1 = int, 2 = float, 3 = string literal, 4 = identifier string, 5 = address
(`PUSHA`), 6 = symbol record. `0x4bead0(desc, index)` is the shared bounds-checked
resolver: `cmp ecx, [eax+8]` (count), `mov edx, [eax+0x10]` (offsets), `mov ecx, [ecx]`
(offset), `cmp ecx, edx` (max), `add eax, ecx` (base + offset).

## Verification

| Check | Result |
|-------|--------|
| Header hypothesis | 997/997 files, 0 failures |
| Disassembler over the whole tree | 997 files processed, 0 errors, 0 desyncs |
| Branch targets | 41,716 branches, 0 bad targets |
| CALL argument tables | 34,220 calls, 0 bad table entries |
| String-index pushes | 0 out of range (max `PUSHSIW` operand 1,596) |
| Symbol-index pushes | 0 out of range |
| Reserved words | 997/997 files carry `(0, 0)` |

Disassemble with `reverse/tools/qvm.py`:

```bash
python3 reverse/tools/qvm.py /path/to/mission.qvm
python3 reverse/tools/qvm.py --findings
```

## Still unknown

Closed by the interpreter pass (see [QVM interpreter internals](#qvm-interpreter-internals-igiexe)):
the 4-byte `PUSH*I*` targets, `BRK` semantics, the type-3/type-4 string distinction, the
type-5 operand kind and the native call convention.

Still open:

1. Why the VM numbering is reversed relative to the compiler's name list.
2. Why six tiny AI files contain a bare instruction stream with no prologue.
3. What the compiler *meant* by `PUSHA` (0x06): the mechanism is proven (4-byte
   immediate, type tag 5, 0 occurrences in 997 files), but no interpreter path consumes
   type 5 and the `.qsc` sources are not shipped.
4. The producer of type 7: `0x4bcb50` has a branch for it and `0x4bcc20` sets halt 7 on
   the type-4 failure path, but no push helper writes type 7.
5. `record->0x08` for kind-0 symbols: the `PUSH*I*` path treats it as "resolved"
   (`0x4be990`), but where kind-0 records are created was not traced.
6. The `argc` overflow guard (halt 13, "Function argument overflow") was not located.
7. Mode 2 of the handler table is never registered; the dispatcher accepts modes 0..3.
8. The exe's own disassembler (mode 3) is incomplete for `PUSHA` (6) and `PUSHS` (7).

## QSC Source Files

`.qsc` files are the source format compiled to `.qvm`. The retail tree ships only
`.qvm`; `.qsc` names appear in `IGI.exe` strings and in the `TextureModifier` task
declarations quoted in [07-terrain](../07-terrain/README.md).

## References

- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
- Disassembler: `reverse/tools/qvm.py`
- Decoded LOD / config / weapon data: [14-lod-system](../14-lod-system/README.md),
  [15-configuration](../15-configuration/README.md),
  [06-weapons](../06-weapons/README.md)
