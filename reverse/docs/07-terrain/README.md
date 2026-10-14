# 07 - Terrain System

**Status: the terrain file formats are now solved and verified against the retail
game data.** See [16-verified-formats](../16-verified-formats/README.md) for the
byte-level tables and the parser runs that prove them. This section keeps the
system-level description.

## File Types

| Extension | Purpose | Size (Level 1) | Confidence | Method |
|-----------|---------|----------------|------------|--------|
| .BIT | Texture-modifier bitmaps | 71,552 bytes | ✅ Verified | Parser consumes file exactly |
| .CMD | Tile command byte stream | 508,696 bytes | ✅ Verified | 11,022/11,022 `.ctr` offsets valid |
| .CTR | Tile tree | 352,704 bytes | ✅ Verified | 32-byte records, 11,022 of them |
| .LMP | Lightmaps | 461,360 bytes | ✅ Verified | Image walk consumes file exactly |
| .TEX | Terrain textures (LOOP v9) | 590,764 bytes | ✅ Verified | 18 textures decoded, all 128x128 ARGB1555 |
| .HMP | Height maps | 52,995 bytes | ✅ Verified | Parser consumes file exactly |
| .QVM | Terrain script | 12,733 bytes | ⚠️ Bytecode partial | See 03-scripting |

## Heightmap (.BIT)

**Not** a 16-byte float array. It is a 256-slot descriptor table followed by
bit-packed arrays:

```
256 x 12-byte descriptor { uint32 runtime_ptr; uint8 unk; uint8 pad[3]; uint32 size; }
then, in slot order, one array of size*size BITS per non-empty slot
```

Level 1: 52 non-empty slots (sizes 32, 64, 128, 256), total exactly 71,552 bytes.
All 14 levels verify.

The `runtime_ptr` field is a heap address written to disk by the original tooling; it
carries no file-relative meaning.

## Height maps (.HMP)

Same 256-slot descriptor table, but each array is `(size+1)^2` **bytes** - a
`(size+1) x (size+1)` grid of 8-bit heights. Level 1: 3 slots of size 128 = 52,995
bytes exactly. Only 6 of the 14 levels ship a `.hmp`.

## Tile tree (.CTR)

32 bytes per record:

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 16 | int16[8] | child tile indices |
| 0x10 | 8 | int8[8] | per-child transform selector |
| 0x18 | 1 | uint8 | children mask |
| 0x19 | 3 | uint8[3] | padding |
| 0x1C | 4 | uint32 | byte offset into `terrain.cmd` |

Level 1: 11,022 records. Record 0 is the all-zero root; record 1 has children
`(1,1,1,1,2,3,4,5)` with mask `0xF0`.

## Tile commands (.CMD)

**The `.cmd` file is a byte stream of variable-length records**, addressed by the
`cmd_offset` field of the `.ctr` tree. Reading it linearly produces garbage.

```
+0x00  uint16  num_triangle
+0x02  uint16  vertex_offset          == num_triangle * 4
+0x04  uint16  num_parent_vertex
+0x06  uint16  num_child_vertex
+0x08  uint8   triangle[num_triangle][4]
       uint8   vertex[num_parent_vertex + num_child_vertex][4]
```

Record length = `8 + 4 * (num_triangle + num_parent_vertex + num_child_vertex)`. The
records tile each file exactly - **no trailer** - which is why four levels' `.cmd`
sizes are not multiples of 8.

**Triangle descriptor:** three `uint8` vertex indices + one flag byte. The packed
10:10:10 rival scores 0% on all 13 levels against the 100% of the byte-wise reading.
The flag byte is `0xE0` or `0xF0` in levels 1-13 and `0x40` in level 14.

**Vertex entry:** 4 bytes, packed. Bits 21-25 and 27-31 are the vertex grid position -
for the level-1 root tile they are exactly `(12*x, 12*y)` with `(x,y)` in `{0,1,2}^2`.
Bits 3-5, 10-14, 20 and 26 are always zero.

**Validation:** for 13 of the 14 levels every single `cmd_offset` target satisfies
`vertex_offset == num_triangle * 4` - 11,022/11,022 for level 1, 11,024/11,024 for
level 2, through level 13.

**Level 14** uses 44-byte `.ctr` records (`486,464 = 11,056 x 44`) and a linear `.cmd`.
See [16-verified-formats](../16-verified-formats/README.md).

## Loader evidence (IGI.exe)

Static disassembly of `IGI.exe` (PE32, imagebase `0x400000`) settles the loader
questions above. Each claim cites the VA of the instruction that proves it;
claims that fit the code and the data but are not settled by an instruction are
marked ⚠️ Inferred.

### The `.ctr`/`.cmd` loader (`0x4c60a0`)

| Load | Instruction | VA |
|------|-------------|-----|
| `.cmd` image -> `terrain+0x08` | `mov [ebp+8], eax` | `0x4c6319` |
| `.ctr` image -> `terrain+0x0c` | `mov [ebp+0xc], eax` | `0x4c637c` |

The fix-up loop at `0x4c6437`-`0x4c644d` proves what the `.ctr` record `+0x1c`
field is: a **byte offset into `terrain.cmd`**, converted at load time into an
absolute pointer by adding the `.cmd` image base.

```
0x4c6437  mov ecx, [ebp + 0xc]         ; .ctr base
0x4c643a  mov esi, [ebp + 8]           ; .cmd base
0x4c643d  mov edi, [edx + ecx + 0x1c]  ; record[+0x1c] = file offset
0x4c6445  add edi, esi                 ; + .cmd base
0x4c6447  add edx, 0x20                ; stride 32
0x4c644b  mov [ecx], edi               ; store the pointer
0x4c644d  jne 0x4c6437
```

✅ Verified - the runtime consumer reads `[ctr + i*32 + 0x1c]` as a pointer, not
as an offset.

### `cmd_transform[0..7]`

✅ Verified by data over all 13 levels (level 1: 11,021/11,022 records):

**`cmd_transform[k] == 0xFF` exactly when mask bit `k` is clear, and
`cmd_transform[k] ∈ {0..7}` exactly when mask bit `k` is set.** The mask at
`+0x18` and the transform array at `+0x10` are redundant encodings of the same
8-slot occupancy; `0xFF` is the "no child" sentinel.

The only exceptions are **record 0 of each level** - 13 records out of 149,256 in
levels 1-13 - which is entirely zero-filled: mask `0` and all eight
transforms `0`.

⚠️ **Inferred:** the 8 values are the 8 symmetries of a square (the dihedral
group D4: 4 rotations x 2 reflections). The `.ctr` is a **DAG, not a tree** -
children are shared (level 1: records 2-5 all reference tile 9) - and every
tile's vertex coordinates are **local** (`0..24` at every depth), so a child's
placement must come from the parent link. Reusing one tile in several
orientations is exactly what a D4 index is for. No instruction that reads the
transform array was found.

### Triangle flag byte

✅ Verified by data: only `0xE0` and `0xF0` in levels 1-13, only `0x40` in
level 14. The low nibble is always 0.

Tested and **rejected** (level 1, 115,305 triangles): winding / signed-area
sign, the parent/child vertex split, and index ordering - both flags occur in
all cases.

⚠️ **Inferred:** the high nibble is a **material index** (`0xE0 >> 4 = 14`,
`0xF0 >> 4 = 15`, `0x40 >> 4 = 4`), consistent with `CreateTerrainMaterial`
(`0x4c64d0`) building a **900-byte-stride** material table at `0xc29740` from
script arguments. No instruction that reads the flag byte was found.

### `.cmd` vertex entry packing

✅ Verified over **840,866 vertex entries** (levels 1-13, distinct `.cmd`
records, 0 violations):

```
dword = (Y << 27) | (X << 21) | (C << 15) | (B << 6) | A
```

| Field | Bits | Range | Meaning | Confidence |
|-------|------|-------|---------|------------|
| `A` | 0-2 | 0..7 | subdivision / refinement index | ⚠️ Inferred |
| `B` | 6-9 | 0..10 | two 2-bit sub-fields, each `<= 2` | ⚠️ Inferred |
| `C` | 15-19 | 0..24 | height | ⚠️ Inferred |
| `X` | 21-25 | 0..24 | local grid X | ✅ Verified |
| `Y` | 27-31 | 0..24 | local grid Y | ✅ Verified |

Bits 3-5, 10-14, 20 and 26 are always zero. The root tile is exactly
`{0, 12, 24}` in both axes. `C` is constant per tile at depths 0-4 and monotone
in `X+Y` deeper - likely a height sampled from the `.hmp`.

### `.mtp` parser (`0x4d1ee0`)

```
INST record (one per VNAM entry):
    uint32 model_index;
    uint32 texture_count;
    uint32 gtt_index[texture_count];
```

✅ Verified by code and data:

- `model_index` indexes the MODS model list - `0x4d1fc3 cmp eax, 0x2000` / `jl`
  -> `list_nth(obj+0x10, A)`, else `list_nth(common+0x10, A - 0x2000)`.
- The sequential walk consumes `INST` exactly: 2,586/2,586 dwords for level 1,
  exact in all 17 `.mtp` files.
- `max(model_index) == MODS_count - 1` and `max(gtt_index) == GTT_count - 1`
  in all 17 files.

**Correction:** VNAM offsets are **not** direct `INST` offsets. They satisfy

```
offsets[i] == 4 * (record_start_dword_i - i)
```

a compacted index - the `model_index` dword removed from every record. Verified
in all 17 files (415/415 for level 1).

**GTT is an identity remap:** `GTT[i] == (i, 0xFFFFFFFF)` in all 17 files.

## Lightmaps (.LMP)

A flat sequence of size-prefixed **8-bit greyscale** square images:

```
repeat until EOF:  uint32 size;  uint8 pixels[size*size]
```

Level 1: 268 images, sizes 16 (x138), 32 (x79), 64 (x40), 128 (x11). The walk consumes
the file exactly. The renderer expands each texel to RGBA with `alpha = texel ? 255 : 0`.

## Terrain textures (.TEX)

LOOP version 9. **Solved.** `terrain.tex` holds 18 textures, all 128x128, all 16-bit
`ARGB1555`. The header is 0x34 bytes followed by 32-byte descriptors
(`offset, fmt, stride|width, height, ...`); the descriptor table is exactly contiguous
in all 145 v9 files in the tree.

The two LOOP pixel formats are:

| Code | Format |
|------|--------|
| 2 | 16-bit `ARGB1555` (bit15 = A, 14-10 = R, 9-5 = G, 4-0 = B) |
| 3 | 32-bit `A8R8G8B8` (bytes in memory: B, G, R, A) |
| 67 | 32-bit `A8R8G8B8` + a full mip chain |

The game's own level manifests mark the 32-bit textures with an `_argb8888` suffix;
those are exactly the code-3/code-67 textures. 93.8% of textures are 16-bit.

Decode with `reverse/tools/loop.py`:

```bash
python3 reverse/tools/loop.py /path/to/level1/terrain/terrain.tex out/
```

## World scale

The entity/physics coordinate space is **4096 units = 1 m** (1 unit = 2^-12 m), proven
by six independent conversions in `IGI.exe` - see
[13-implementation](../13-implementation/README.md).

The `.bit`/`.hmp` arrays are indexed by `TextureModifier` tasks in the level QVM, which
carry positions on the order of 1e7, while the model vertices in the same levels are on
the order of 1e3-1e4. The level-script/terrain-grid space is therefore **not** in the
1/4096 m unit, and its scale is not determined.

## Known Issues

1. **`.cmd` triangle flag byte** - `0xE0`/`0xF0` in levels 1-13, `0x40` in level 14.
   Winding, parent/child split and index ordering were rejected; the high nibble is
   **inferred** to be a material index (see Loader evidence).
2. **`.cmd` vertex entry fields** - the packing is proven
   (`(Y<<27)|(X<<21)|(C<<15)|(B<<6)|A`, 840,866 entries, 0 violations); the `A`/`B`
   semantics remain inferred.
3. **`cmd_transform[8]`** - `0xFF` = unused and `0..7` are the only values (rule holds
   149,243/149,256 records); what `0..7` selects is not proven (D4 symmetry index is the
   natural reading).
4. **Terrain-grid / level-script coordinate space** - not in the 1/4096 m unit; its
   scale is not determined (the entity/physics world scale is proven: 4096 units = 1 m).
5. **LOOP v9 header leftovers** - **Resolved**: `0x10 = 0x00050000` is the scale level
   (u16 at `+0x12`, default 5) and descriptor `+0x0E` is the per-glyph advance (see
   [16-verified-formats](../16-verified-formats/README.md)).

## References

- Terrain files: `PC/MISSIONS/LOCATION0/LEVEL{n}/TERRAIN/`
- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
- Parsers: `reverse/tools/igi_formats.py`, `reverse/tools/loop.py`
- Harness: `reverse/tools/verify_formats.py`
