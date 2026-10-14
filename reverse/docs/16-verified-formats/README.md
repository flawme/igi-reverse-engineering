# 16 - Verified Binary Formats

Every table in this section was produced by parsing the **retail game data** extracted
from the original CD image, not by static analysis of the executable. Each claim cites
the parser run that proves it.

Reproduce everything with:

```bash
python3 reverse/tools/verify_formats.py /path/to/extracted/pc
```

## Evidence summary

| Format | Files tested | Result |
|--------|--------------|--------|
| ILFF `.res` | 92 | 92/92 parse cleanly, 90,893 chunks, every parse consumes exactly the declared file size |
| `.bit` | 14 | 14/14: descriptor table + bit arrays consume exactly the file size |
| `.hmp` | 6 | 6/6: descriptor table + height arrays consume exactly the file size |
| `.lmp` | 14 | 14/14: the size-prefixed image walk consumes exactly the file size |
| `.ctr` | 14 | 14/14: file size is a multiple of 32 |
| `.cmd` | 14 | 13/14: 100% of the `.ctr` `cmd_offset` targets hold a record with `vertex_offset == num_triangle * 4` (level 14 is an outlier, see below) |
| MEF models | 6,795 | 6,795 models parsed, 1,468,324 vertices, 100.00% of normals are unit length at the correct stride (6,178 models stride 40, 617 stride 32, 0 ambiguous) |
| LOOP textures | 118 files | 8,232 textures decoded, 0 exceptions; 7,199/7,199 v11 size invariants, 145/145 v9 descriptor contiguity |

The MEF normal test is the load-bearing one: a wrong vertex stride cannot produce
unit-length normals. With a 40-byte stride 52/52 normals of the first level-1 model
are unit length; no other stride that divides the chunk size passes.

## Adversarial checks

`python3 reverse/tools/adversarial_checks.py /path/to/extracted/pc` runs the strongest
rival interpretation against each claim. Results:

| Claim | Rival | Outcome |
|-------|-------|---------|
| ILFF advance = `align4(offset + id_field + 12 + extra + size)` | advance = `total` when non-zero (same framing) | claim 92/92, rival **0/92** |
| ILFF advance (as above) | loader framing: 20-byte header, 4-byte tags from `0x14`, advance = `total` | claim 92/92, rival **91/92** (fails only on `common.res` - its zero-size `IRES` marker puts the next chunk at `0x20`) |
| `.bit`/`.hmp` descriptor table has 256 slots | 128 or 512 slots | 256 fits 14/14 and 6/6; 128 and 512 fit **0** |
| `.lmp` images are `size x size` | a `(width, height)` pair | the square walk consumes every file exactly; the pair reading produces absurd sizes |
| `.cmd` is addressed by `.ctr` offsets | `.cmd` is a linear 8-byte array | addressed 11,022/11,022 valid; linear **2,551/63,587** |
| MEF vertex stride 40, normal at 0x0C | any other (stride, normal offset) | 40/0x0C scores 84.6%, next best 44.7% (an alias of the same field at a wrong record boundary) |

---

## IGI.exe loader map

Every format below was anchored to the code that loads it. The loaders live in
`IGI.exe` (PE32, imagebase `0x400000`); the VAs are file-verified.

| Format | Loader | Notes |
|--------|--------|-------|
| ILFF container | `fcn.004b5e30` | magic compare `cmp eax, 0x46464c49` at `0x4b5e52`; outer `.res` carries an `IRES` marker at `+0x10` (`cmp eax,0x53455249` at `0x4b5e62`) |
| LOOP textures v7/v9 | `fcn.00517620` | called from the `.tex` path at `0x4c5dfd` |
| LOOP textures v2/v11 | `fcn.004b2370` | version compares at `0x4b23a0` (2) and `0x4b2407` (11) |
| LOOP textures (`.res`-embedded) | `fcn.004b6982`+ | v9 branch at `0x4b6a19`; reads the descriptor `+0x0E` field the `.tex` path skips |
| MEF models | `fcn.0049f9a0` | registered as method `LoadModel` of class `Direct3D` |
| QVM bytecode | `0x4bd0c6`-`0x4bd104` | size >= `0x3c`, magic, version 8, section count 5 |
| Nav graphs | `fcn.004f9d30` | caller at `0x4fab90` builds `"MISSION:graphs/graph%d.dat"` |
| `.mtp` manifests | `fcn.004d1ee0` | chunk finder `0x4d1900` byte-swaps big-endian IDs |
| Terrain `.ctr`/`.cmd` | `fcn.004c60a0` | `.cmd` -> `[terrain+8]` (`0x4c6319`), `.ctr` -> `[terrain+0xc]` (`0x4c637c`) |
| ILSF audio | `fcn.00495e00` | magic compare `cmp eax, 0x46534c49` at `0x495e36` |
| `.fnt` fonts | `fcn.004b65d0` | |
| `.iff` animation | `fcn.004d65f0` | reached from a `BANM` name list via `"%sanims/%s.iff"` (`0x4d27b6`) |

**The magic is compared byte-wise.** `LOOP` never appears as a 32-bit immediate in
`IGI.exe`; the loaders compare it one byte at a time (`cmp al, 0x4c` / `cmp byte
[esi+1], cl` / `[esi+2], cl` / `[esi+3], dl`, e.g. `0x517647`-`0x51766a`). Dword
searches for the magic therefore find nothing - this is why the earlier pass recorded
"no LOOP magic in any byte order".

### Shared infrastructure

- **ILFF node overlay.** The loader does not copy the container; it overlays a node
  struct on the raw bytes: `+0x00` tag, `+0x04` size, `+0x08` align (the raw `type`
  field), `+0x0c` next (the raw `total` field), payload at `node + align_up(16, align)`.
  Helpers: `0x4b7350` (first node), `0x4b7330` (next), `0x4b7390` (payload), `0x4b7450`
  (find by tag).
- **Renderer method registry.** `fcn.004b0d00` registers a name and returns an index
  (name table at `0xa951e0`, 8-byte entries); implementations live in the table at
  `0xa955e4`. The texture callbacks registered at `0x4b2030`-`0x4b20f1` are
  `AllocTexture` (index at `0x5476f8`), `DeAllocTexture`, `DownloadTexture`
  (`0x547700`), `BeginTextureList` (`0x5476f0`), `EndTextureList`, `GetTMUs`,
  `SetActiveTMU`, `GetActiveTMU`, `RefreshTexture`, `ReloadTexture`, `GetTextureSize`,
  `SetLOD`.
- **Texture constructor.** `fcn.004b2260` builds a 12-dword struct (out record, block,
  scale level, stride, 0, 0, width, height, format, arg8, global byte, pixels) and
  dispatches `AllocTexture` then `DownloadTexture`.

---

## ILFF container (`.res`)

Used by every resource archive: textures, models, lightmaps, sprites, sounds, menus.

### File header (16 bytes + a 4-byte format id)

| Offset | Size | Type | Meaning | Evidence |
|--------|------|------|---------|----------|
| 0x00 | 4 | char[4] | `"ILFF"` | all 92 files; loader `cmp eax, 0x46464c49` at `0x4b5e52` |
| 0x04 | 4 | uint32 | total file size | equals the on-disk size in all 92 files |
| 0x08 | 4 | uint32 | sub-format id: `4` for most resources, `32` for `common/textures/common.res` | 91 files are 4, 1 file is 32 |
| 0x0C | 4 | uint32 | always 0 | all 92 files |
| 0x10 | 4 | char[4] | format id: `"IRES"` for resource archives, `"HSEM"` for models | loader `cmp eax, 0x53455249` at `0x4b5e62` |

The loader reads the first 20 bytes as one header struct (`fcn.004b5e30` requires
`[node+0] == "ILFF"` and `[node+0x10] == "IRES"`), and its chunk parser
(`fcn.004b5fa0`) starts at `+0x14` with a 4-byte tag - the first comparison is
`cmp eax, 0x454d414e` (`"NAME"`). The parser in `reverse/tools/igi_formats.py` reads
the same bytes as a 16-byte header plus an 8-byte first tag (`IRESNAME`); the two
framings produce identical chunk offsets on 91 of the 92 files. `common.res` is the
discriminator: its `IRES` marker is a zero-size chunk at `0x10`, so the next chunk
sits at `0x20`, not `0x14` - only the 8-byte-tag reading consumes it.

### Chunk

Chunks follow the header and repeat until EOF.

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 or 8 | char[] | ASCII tag, null-padded to a 4-byte boundary (the loader reads 4-byte tags) |
| +0 | 4 | uint32 | payload byte count |
| +4 | 4 | uint32 | type: mirrors the file sub-format (`4`, or `32` for texture resources) |
| +8 | 4 | uint32 | `total`: byte distance to the next chunk |
| +12 | `size` | uint8[] | payload |
| | 0-3 | | pad to a 4-byte boundary |

The next chunk starts at `align4(offset + id_field + 12 + extra + size)` where
`id_field` is 4 or 8 and `extra` is 28 for type-32 chunks.

**The `total` field.** It equals the advance for every 4-byte-tag chunk -
`next == offset + total` in **90,709/90,709** such chunks, including all 242 type-32
chunks. It is 0 in 93 chunks: the 92 last chunks of the files plus the zero-size
`IRES` marker of `common/textures/common.res`. The only disagreement is the 91 first
chunks: read as an 8-byte tag (`IRESNAME`) the real advance is `align4(20 + size)`
while `total` is `align4(16 + size)`, 4 short; read the way the loader does - format
id in the header, a 4-byte `NAME` tag at `0x14` - `total` is exact
(`common/sounds/sounds.res`: `NAME` at `0x14`, `size=36`, `total=52`, `BODY` at
`0x48 = 0x14 + 52`).

### Observed tags

| Tag | Payload |
|-----|---------|
| `IRESNAME` / `NAME` | resource path string, e.g. `LOCAL:models/210_01_1.mef` |
| `BODY` | the resource itself; for models this is a nested ILFF (MEF), for textures a LOOP file |
| `PATH` | `;`-separated path list (menus, sounds) |
| `CSTR` | localised string |
| `OCEMHSEM` | MEF model header |
| `IRES` | zero-length marker chunk at the start of `common/textures/common.res` |

### Type-32 (texture) resources

`common/textures/common.res` is the only file with sub-format 32. Its `BODY` payloads
pad the nested resource to a **32-byte boundary**: the `LOOP` magic sits at
`align32(payload_off)`. Observed padding lengths are 0, 16, 20, 24 and 28 bytes, always
zeros. Verified on all 243 `BODY` chunks of that file. Sub-format-4 archives have no
padding.

---

## Terrain: `.bit` and `.hmp`

Both files are a **256-slot descriptor table** followed by the arrays, in descriptor
order, for every slot with a non-zero size. The `contents` field is a runtime heap
pointer written to disk by the original tooling and is meaningless in the file.

### Descriptor (12 bytes)

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | uint32 | runtime pointer (garbage on disk) |
| 0x04 | 1 | uint8 | unknown, always 0 in the retail data |
| 0x05 | 3 | uint8[3] | padding |
| 0x08 | 4 | uint32 | `size` |

### `.bit` arrays

Each non-empty slot holds `size * size` **bits** (`size*size/8` bytes), one bit per
element. Level 1 has 52 non-empty slots with sizes 32, 64, 128 and 256; the computed
total is exactly 71,552 bytes.

### `.hmp` arrays

Each non-empty slot holds `(size + 1) * (size + 1)` **bytes** - a `(size+1) x (size+1)`
grid of 8-bit heights. Level 1 has 3 slots of size 128; the computed total is exactly
52,995 bytes. Only 6 of the 14 levels ship a `.hmp`.

---

## Terrain: `.ctr` (tile tree)

32 bytes per record in 13 of the 14 levels. Level 1: 352,704 / 32 = 11,022 records.

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 16 | int16[8] | child tile indices |
| 0x10 | 8 | int8[8] | per-child transform selector |
| 0x18 | 1 | uint8 | children mask |
| 0x19 | 3 | uint8[3] | padding |
| 0x1C | 4 | uint32 | byte offset into `terrain.cmd` |

The first record is all zeros (the tree root). Record 1 has children
`(1,1,1,1,2,3,4,5)` and mask `0xF0`.

### `cmd_transform[8]`

| Value | Level 1 count | Meaning |
|-------|--------------|---------|
| `0xFF` | 44,273 | slot unused (the corresponding mask bit is clear) |
| `0x00` | 26,978 | transform 0 |
| `0x07` | 6,440 | transform 7 |
| `0x06` | 4,484 | transform 6 |
| `0x01` | 1,916 | transform 1 |
| `0x03` | 1,832 | transform 3 |
| `0x04` | 1,288 | transform 4 |
| `0x02` | 630 | transform 2 |
| `0x05` | 335 | transform 5 |

**Proven:** `0xFF` marks unused slots (it appears only where the mask bit is clear) and
`0..7` are the only other values, in all 14 levels. Verified slot-by-slot over 1,194,048
slots: the rule "`0xFF` exactly when the mask bit is clear" holds in **149,243 of 149,256
records** across levels 1-13 (level 1: 11,021/11,022); the 13 exceptions are record 0 of
each level, which is entirely zero-filled (mask 0, transforms 0).

**Not proven:** what `0..7` selects. It is per (parent, child) rather than a property of
the child record - 4,305 of 11,020 child records receive more than one distinct value -
and it is mostly determined by the child's slot index (9,230 of 11,020). Eight values is
the size of the square's symmetry group (D4), which makes a rotation/reflection index
the natural reading, but the data does not confirm it.

**Loader evidence.** The terrain loader `fcn.004c60a0` reads `.cmd` into `[terrain+8]`
(`0x4c6319`) and `.ctr` into `[terrain+0xc]` (`0x4c637c`); the fixup loop
`0x4c6437`-`0x4c644d` converts the `.ctr` `+0x1C` byte offset into a pointer
(`mov edi,[edx+ecx+0x1c]; add edi,esi; mov [ecx],edi`), proving the addressing model at
code level.

### Level 14

Level 14 uses **44-byte records** (`486,464 = 11,056 x 44`), proven by the constant
8-byte sequence `ef ff ff ff 5f fe ff 07` at `+0x24` of every record: 2,658
occurrences, every gap a multiple of 44. The first 25 bytes are the same fields in the
same order as the other levels.

---

## Terrain: `.cmd` (tile commands)

**The `.cmd` file is not a linear array.** It is a byte stream of **variable-length
records** addressed by the `cmd_offset` field of the `.ctr` tree. Reading it linearly
produces garbage: only 2,551 of level 1's 63,587 8-byte windows satisfy the record
invariant.

### Record layout

```
+0x00  uint16  num_triangle
+0x02  uint16  vertex_offset          == num_triangle * 4
+0x04  uint16  num_parent_vertex
+0x06  uint16  num_child_vertex
+0x08  uint8   triangle[num_triangle][4]
       uint8   vertex[num_parent_vertex + num_child_vertex][4]
```

Record length = `8 + 4 * (num_triangle + num_parent_vertex + num_child_vertex)`. The
records tile each `.cmd` file exactly - **there is no trailer**, which is why four
levels' `.cmd` sizes are not multiples of 8 (level 2: 508,596; level 9: 539,100;
level 12: 511,108; level 14: 469,644).

### Triangle descriptor - 3 x uint8 index + 1 flag byte

Each 4-byte triangle descriptor is **three `uint8` vertex indices followed by one flag
byte**, not a packed 10:10:10.

| Candidate | Test: `max(index) == num_parent_vertex + num_child_vertex - 1` | Result |
|-----------|----------------------------------------------------------------|--------|
| 3 x uint8 + flag | | **100%** on all 13 levels (level 1: 5,005/5,005) |
| packed 10:10:10:2 | | **0%** on all 13 levels (level 1: 0/5,005) |

The flag byte takes exactly two values in levels 1-13: `0xE0` and `0xF0` - a 1-bit
flag in bit 4 with bits 7-5 = `111`. Level 14 uses `0x40` for every triangle
(53,157/53,157). Winding, parent/child split and index ordering were all tested and
rejected as readings. **Inferred:** the high nibble is a material index (14/15/4),
consistent with `CreateTerrainMaterial` (`0x4c64d0`) building a 900-byte-stride table at
`0xc29740`.

### Vertex entry - 4 bytes, packed

Bit usage over all 61,940 vertex entries of level 1:

| Bits | Width | Values seen |
|------|-------|-------------|
| 0-2 | 3 | 0-7 |
| 3-5 | 3 | always zero |
| 6-7 | 2 | 0-3 |
| 8-9 | 2 | 0-3 |
| 10-14 | 5 | always zero |
| 15 | 1 | 0-1 |
| 16-19 | 4 | 0-12 |
| 20 | 1 | always zero |
| 21-25 | 5 | 0-24 |
| 26 | 1 | always zero |
| 27-31 | 5 | 0-24 |

**Bits 21-25 and 27-31 are the vertex grid position.** For the level-1 root tile - a
2x2 grid with 4 corners, 4 edge midpoints and a centre - the fields are exactly
`(12*x, 12*y)` with `(x,y)` in `{0,1,2}^2`. The vertex array is
`parent[num_parent_vertex] ++ child[num_child_vertex]`.

**Full packing, proven over 840,866 vertex entries (levels 1-13, 0 violations):**

```
dword = (Y << 27) | (X << 21) | (C << 15) | (B << 6) | A
```

with bits 3-5, 10-14, 20 and 26 always zero; `X,Y <= 24` (the root tile is exactly
`{0,12,24}`), `C <= 24`, `B <= 10`, `A <= 7`. `C` is constant per tile at depths 0-4 and
monotone in `X+Y` deeper (likely a height); the `A`/`B` semantics remain inferred.

### Validation

For 13 of the 14 levels, **every** `cmd_offset` in the `.ctr` tree points at a window
satisfying `vertex_offset == num_triangle * 4` - 11,022/11,022 for level 1,
11,024/11,024 for level 2, through level 13. Offsets are 4-byte aligned.

### Level 14 is different

Level 14's `.ctr` is `486,464 = 11,056 x 44` bytes - **44-byte records, not 32**. The
44-byte stride is proven by the constant 8-byte sequence `ef ff ff ff 5f fe ff 07` at
`+0x24` of every record: it occurs 2,658 times and every gap between occurrences is a
multiple of 44.

The first 25 bytes are the same fields in the same order as levels 1-13 (children,
transforms, mask). Reading level 14 at 32-byte stride puts the "cmd_offset" at `+0x1C`,
which actually holds `0x0C000000 | (v << 16)` with `v` in 0..42 - **not an offset at
all**, which is why the earlier pass saw 10,174 out-of-bounds values. Level 14's `.cmd`
is a linear array.

---

## Terrain: `.lmp` (lightmaps)

A flat sequence of size-prefixed 8-bit greyscale images:

```
repeat until EOF:
    uint32 size
    uint8  pixels[size * size]     # row-major, greyscale
```

Level 1 holds 268 images with sizes 16 (x138), 32 (x79), 64 (x40) and 128 (x11). The
walk consumes the file exactly. Lightmaps are **8-bit greyscale, not RGB** - the
renderer expands each texel to RGBA with `alpha = texel ? 255 : 0`.

---

## MEF models

A MEF file is the nested ILFF inside a `BODY` chunk of a `models/*.res` archive. Level
1's `models/level1.res` holds 830 chunks = 415 models.

### Chunk tags

Tags are stored **byte-reversed** on disk (a 4CC written as a little-endian uint32).
The logical names are the reversed strings:

| On disk | Logical | Payload |
|---------|---------|---------|
| `OCEMHSEM` | `MESHMECO` | model header: 6 exact counts/byte-totals, two bounding spheres at 0x30/0x40, a format flag at 0x20 |
| `ATTA` | `ATTA` | zero-length marker |
| `XTVM` | `MVTX` | zero-length marker |
| `TROP` | `PORT` | zero-length marker |
| `XVTP` | `PTVX` | zero-length marker |
| `CFTP` | `PTFC` | zero-length marker |
| `D3DR` | `RD3D` | 48- and 56-byte variants carrying triangle/batch/vertex counts |
| `DNER` | `REND` | render triangle batches; header is 28 or 32 bytes |
| `XTRV` | `VRTX` | render vertices (40 or 32 bytes each) |
| `PMTL` | `LTMP` | 8-byte records, `u32@4` always 0 |
| `HSMC` | `CMSH` | two 32-byte collision-group descriptors. **Corrected**: the on-disk form is `{4 counts, 4 zero slots}`; the loader overwrites the slots with pointers (`0x49fc97`-`0x49fcd4`, 32-byte stride), so the earlier `{ecfc, xtvc, tamc, hpsc, pad[4]}` reading described the runtime struct, not the file. 169/169 64-byte HSMC chunks have descriptor 1 = group-1 counts and descriptor 2 = group-2 counts |
| `XTVC` | `CVTX` | box vertices |
| `ECFC` | `CFCE` | box faces |
| `TAMC` | `CMAT` | 12-byte material records |
| `HPSC` | `CSPH` | 24-byte records (the "collision sphere" reading is **falsified** - 477/83,432) |

### Model names

The trailing `_N` in a model name (`210_01_1`) is a **1-based LOD level**, contiguous
within a `.res` - verified on 100/100 groups in level 1.

### `OCEMHSEM`

Six fields are exact counts or byte totals (6,795/6,795 models each). `0x30` and `0x40`
are bounding spheres that contain every render vertex (594/594); `0x50` duplicates
`0x40`; `0x20` is a format flag. `0x64` equals the render-vertex count once the correct
stride is used (6,686/6,686).

**Loader evidence.** The mesh object *is* the `OCEMHSEM` payload, and the loader
(`fcn.0049f9a0`) reads only `+0x20` from it. Data-proven field meanings: `+0x60` = DNER
triangle count, `+0x64` = XTRV vertex count, `+0x68` = D3DR+DNER+XTRV bytes, `+0x6C` =
total ECFC faces, `+0x70` = total XTVC verts, `+0x74` = total collision bytes (all
415/415). **Two more fields are consumed**: `+0x7C` = the XTVM record count (16-byte
records; getter `fcn.004cf9b0`, `movsx eax, word [edx+0x7c]` at `0x4cf9ba`; data proof
`+0x7C == XTVM_size/16` in 2,876/2,876 models) and `+0x7E` = the ATTA record count
(68-byte records; getter `fcn.004cf9a0`; loop bound at `0x4c47cf`; 2,876/2,876). The
`+0x0C`/`+0x10`/`+0x14`/`+0x18`/`+0x1C` fields still have no located consumer. The
spheres are tighter than the earlier reading: `+0x30` is a tight sphere of the render
vertices (386/411 exact) and `+0x40`/`+0x50` a tight sphere of render union collision
vertices (160/165 exact); the centre is a fitted point, not the origin, bbox centre or
centroid.

### `DNER`

The header is **28 or 32 bytes**, selected by `u32@+0x1C == 0x00010000`. A fixed
32-byte header explains only 5,641/6,795 chunks; the discriminator explains all 6,795,
and all 1,154 failures of the fixed rule carry `0x00010000` there. The index count,
byte count, texture index and vertex offset/count are pinned, and the indices are
**batch-relative**. The walk consumes the chunk exactly in 6,795/6,795 models.

**Loader evidence.** The size is selected by the mesh format flag (`[mesh+0x20]`): 28
bytes for flags 0/1, 32 bytes for flag 3 (344/344 non-empty models). `+0x0C` u16 index
count (`mov cx, word [esi+0xc]` at `0x49c509`, then `/3` via `imul 0x55555556`), `+0x0E`
u16 index byte count with `0xffff` = last batch (`0x49c61e`-`0x49c62d`), `+0x12`/`+0x14`
u16 vertex base, `+0x16` u16 vertex count, index list at `+0x1C` (28-byte) / `+0x20`
(32-byte) (`lea ebp,[esi+0x1c]` at `0x4a1af0` vs `lea ebp,[edi+0x20]` at `0x4a2053`).
**`+0x18` is consumed** (32-byte variant): a deferred/sorted-render flag
(`cmp word [ebp+0x18], 0` / `jne 0x49e620` at `0x49e578`; the non-zero path allocates a
0x68-byte item via `0x4b71a0` with callback `0x49f050`). The `u32@+0x1C == 0x00010000`
rule is a data heuristic - it is the first index pair `(0, 1)`. The `+0x1A`/`+0x1E`
fields have no located consumer.

### Render vertex - 40 or 32 bytes

Two formats exist. The 40-byte form carries a lightmap UV pair; the 32-byte form does
not.

| Offset | Size | Type | Meaning | 40-byte | 32-byte |
|--------|------|------|---------|---------|---------|
| 0x00 | 12 | float32[3] | position | yes | yes |
| 0x0C | 12 | float32[3] | normal | yes | yes |
| 0x18 | 8 | float32[2] | diffuse texture coordinates | yes | yes |
| 0x20 | 8 | float32[2] | lightmap coordinates | yes | - |

**Proof of the stride.** A stride is valid only if it divides the `XTRV` payload and
every vertex's normal at `+0x0C` is unit length. Exactly one of 40 / 32 satisfies that
per model, and the split is exact:

| Stride | Models | Vertices | Unit-length normals |
|--------|--------|----------|---------------------|
| 40 | 6,178 | 1,334,236 | 100.00% |
| 32 | 617 | 134,088 | 100.00% |
| ambiguous | **0** | | |

Across the whole game **1,468,324 of 1,468,324 normals (100.00%) are unit length** at
the correct stride. An earlier revision of this document reported 94.90% - that figure
came from forcing a single 40-byte stride on both formats, which mis-parses the 617
32-byte models.

The two UV pairs in the 40-byte form are distinguishable by range: the diffuse pair
spans `[0.0005, 0.9995]` (texel centres of a 1024-wide texture) while the lightmap pair
spans a small sub-rectangle of the lightmap atlas.

### Box vertex - 16 bytes

`XTVC` holds position-only vertices: `float32 x, y, z, 0`. Level 1's first model has
16 of them forming a box with `x in {1431.2, -1848.8}`, `y in {-8203.6, 8176.0}`,
`z in {-842.5, 487.4}`.

### Box faces - `ECFC`

8 bytes per record: `uint16 i0, i1, i2, material`. Indices are into `XTVC`. The first
model's 28 records index 0-15 (16 box vertices); the second model's 10 records index
0-7 (8 box vertices). The triangles pair up into quads, e.g. `(0,1,2)` + `(1,0,3)`.

### Render triangles - `DNER`

`DNER` holds one or more batches, each a header followed by a triangle list of
`uint16` indices into `XTRV`. The first level-1 model's `DNER` is 220 bytes: a 32-byte
header then 16 quads (`(0,1,2) (1,0,3) (4,5,6) (5,4,7) ...`, indices 0-31), followed by
a second batch header and 10 more triangles.

**Open:** the exact field meanings inside the `DNER` and `OCEMHSEM` headers are not
fully pinned down. `OCEMHSEM` contains a float `0.1`, the integers `2000, 11, 20, 23,
15, 19, 740, 3`, a bounding-box-like float block, and the counts `26, 52, 2356` and
`38, 24, 2576` - `52` matches the `XTRV` vertex count of that model, but the other
counts are unexplained.

---

## Level manifests: `.dat` and `.mtp`

### `levelN.dat` - plain text

Despite the `.dat` extension, `missions/location0/levelN/levelN.dat` is a plain-text,
machine-generated model/texture dependency list:

```
*** This file is machine generated
*** DO NOT EDIT!

415                  <- model count
210_01_1             <- model name
2                    <- texture count for that model
207_01_1             <- texture names
316_04_1
210_01_2
...
```

Level 1 is 2,985 lines. Texture names may carry an explicit format suffix; across all
14 manifests 411 of 6,668 texture references (6.2%) are `_argb8888`, the rest carry no
suffix. This is the game's own statement that a minority of textures are 32-bit ARGB
and the majority are something else.

### `levelN.mtp` - big-endian IFF container

`FORM` + **big-endian** size + `MTP `, then chunks with big-endian sizes but
**little-endian** payload integers:

| Chunk | Payload | Decoded |
|-------|---------|---------|
| `BANM` | 4 bytes, 0 | - |
| `SNDS` | 4 bytes, 0 | - |
| `SVOL` | 4 bytes, 0 | - |
| `MODS` | `uint32 count` + null-terminated model names (level 1: 415) | model list |
| `VNAM` | `uint32 count` + `uint32` offsets | offsets index `INST` in a **compacted** sense: `offsets[i] == 4*(record_start_dword_i - i)` (verified in all 17 files; 415/415 for level 1); its name blob is byte-identical to `MODS` |
| `INST` | instance data | `uint32 model_index; uint32 texture_count; uint32 gtt_index[texture_count]` |
| `TEXF` | `uint32 count` + null-terminated texture names (level 1: 393) | texture list |
| `PALF` | 4 bytes, 0 in every level | no palette |
| `GTT ` | `uint32 count` + `(i, 0xFFFFFFFF)` records | **not** a format table; an identity remap |

**`INST` semantics (parser `fcn.004d1ee0`).** `model_index` indexes the `MODS` model
list: `0x4d1fc3` (`mov eax,[ebp]` / `cmp eax,0x2000` / `jl`) selects
`list_nth(obj+0x10, A)` for `A < 0x2000` and `list_nth(common+0x10, A-0x2000)`
otherwise - i.e. `0x2000` selects `common.mtp`. The parser allocates `B*8+0x1c` bytes
and loops `B` times reading the `gtt_index` array (`0x4d207e`). The walk consumes `INST`
exactly (2,586/2,586 dwords, level 1; exact in all 17 files), and `max model_index ==
MODS_count-1` and `max gtt_index == GTT_count-1` in all 17. `GTT`'s field 0 feeds a
36-byte-stride array and field 1 a 12-byte-stride array with a `-1` sentinel
(`0x4d2088`/`0x4d20c2`); those arrays are filled later, not by the parser.

**Cross-check:** level 1's `TEXF` count is 393, exactly the number of `BODY` chunks in
`textures/level1.res`. The `TEXF[i]` name matches the `BODY[i]` resource name in
**6,665 of 6,667** cases across the tree, and `_argb8888` in the name corresponds to
LOOP format 67 in the archive. The 2 misses are the shipped typo `489_01_1argb8888`
(missing the underscore).

`GTT ` does **not** carry a format code - it is `count` + `(i, 0xFFFFFFFF)` records in
all 17 files. The texture format lives in the archive, not here.

`PALF` is 4 bytes of zero in every level, which argues against palettised textures.

---

## Navigation graphs (`graphs/*.dat`)

**The grid is a shortest-path distance matrix, not a spatial grid.** Three independent
proofs over the 300 nav files in the tree:

1. **Symmetry** - 1,096,112 of 1,096,112 cell pairs across 293 files are symmetric.
2. **Triangle inequality** - 0 violations in 3,666,142 sampled triples.
3. **Exact values** - the cells equal distances between the tail's node positions.
   `graph13` cell `(2,4)` = 35496.18 = `dist(2,3) + dist(3,4)` = 35496.19.

That third proof also explains why a naive straight-line test matches only 50,428 of
1,083,444 positive cells: the rest are multi-hop path distances.

### Header (30 bytes, not 120)

| Offset | Size | Type | Meaning | Evidence |
|--------|------|------|---------|----------|
| 0x00 | 4 | uint32 | magic `0xCCDDEEFF` | 293/293 files with a magic |
| 0x0C | 4 | uint32 | grid dimension: 100 in most files, 300 in `graph4019.dat` | header dump |
| 0x1A | 4 | uint32 | grid byte size = `dim * dim * 8` | 293/293 |
| 0x1E | `dim*dim*8` | | the routing matrix, 8 bytes per cell | loader `fcn.00509360` |
| tail | | | node records, then link records | |

An earlier revision said the header was 120 bytes, then 32. It is **30**: the loader
allocates `dim*dim*8` bytes and reads them as one blob (`fcn.00509360`, alloc at
`0x5093e7`), and the first cell `(0xFFFFFFFF, -1.0f)` starts at `0x1E` (sentinel fill at
`0x5093ed` with `ebp = 0xbf800000`). The "120" was the header plus the tail, which the
earlier pass did not recognise as data.

### The cell is a routing entry, not a cost

The `uint32` field of a cell is a **node ID: the next hop from the column node toward
the row node**; `0xFFFFFFFF` means no route. The accessor `fcn.00509740` returns NULL
when the field is `-1` (`0x509766`-`0x50976d`); the consumer at `0x425dec` feeds it to
`fcn.004f9460` (node-by-ID lookup) and steers toward that node's position (`0x425dfe`,
`0x425e17`). A scan of all 300 nav files: **66,408 cells have the `uint32` adjacent to
the column node, 0 adjacent to the row** (2,498 ambiguous 3-node paths). So the matrix
is a routing table indexed `[destination][source]` = `{next_hop, path_distance}` - not a
cost, hop count or predecessor index.

### The record stream

The header is followed by a stream of **name-hashed records**: each record is a 1-byte
type tag + payload (1/2/4-byte readers at `0x4fa520`/`0x4fa550`/`0x4fa590`/`0x4fa5d0`),
and the uint32 key is a **hash of the field name** (`fcn.004f9bb0`: `h += upper(c)*mul;
mul = (mul+0x13d) & 0xffff`). Verified: `hash("nMaxNodes") = 0x000D3AE6` = the first
record's key in `graph16.dat`. The 11 registered fields (hash / type / handler):
`nMaxNodes` `0xd3ae6`/5/`0x4fac20`, `nNodeID` `0x735ce`/5/`0x4fac90`, `tNodePosition`
`0x1d4295`/8/`0x4facc0`, `vNodeGamma` `0xf7e9c`/6/`0x4face0`, `vNodeRadius`
`0x143023`/6/`0x4fad00`, `nNodeMaterial` `0x1bb629`/5/`0x4fad20`, `nNodeCriteria`
`0x1bd3e5`/9/`0x4fad70`, `nLinkID1` `0x9104a`/5/`0x4fadc0`, `nLinkID2` `0x918f6`/5/`0x4fadf0`,
`eLinkType` `0xda923`/5/`0x4fae10`, `RouteTable` `0xfde0d`/10/`0x509320`.

### A second layout

The 7 `level8/graphs/*.dat` files carry **no magic**: `fcn.004f9ea0` parses a tag-only
token stream (node count, dim, link count, then per-node `id/pos/gamma/radius/...` and
per-link `a/b/type`). It never reads a RouteTable - yet the level8 files carry one at
`0xd11` (`00 0a 05 <u32 80000>` + 80,000 bytes ending exactly at EOF), left unread.

---

## LOOP textures (`.tex` and texture `.res`)

LOOP is a little-endian texture container. Five versions appear in the retail tree:
**2, 6, 7, 9, 11**. Versions 2/7/9/11 carry pixels; version 6 is a lighting
sub-resource appended after the pixels of a v9 file.

### Pixel formats

Two pixel formats exist, selected by a **format code** in the header:

| Code | Format | Count (v11) |
|------|--------|-------------|
| 2 | 16-bit `ARGB1555` (bit15 = A, 14-10 = R, 9-5 = G, 4-0 = B) | 6,767 |
| 3 | 32-bit `A8R8G8B8` (D3DFMT_A8R8G8B8; in memory the bytes are **B, G, R, A**) | 4 |
| 67 (`0x43`) | 32-bit `A8R8G8B8` + a full mip chain | 428 |

The game's own level manifests name the 32-bit textures with an `_argb8888` suffix;
those are exactly the code-3/code-67 textures. The majority (93.8%) are 16-bit and
carry no suffix.

**Evidence for ARGB1555 over RGB565:** in a decoded sky gradient the green channel
swings 42 to 12 between adjacent pixels under RGB565 but is monotone under ARGB1555.
**Evidence for bit15 = alpha:** all 106,399 pixels with bit15 clear are exactly
`0x0000` - none carries colour.
**Evidence for the 32-bit byte order:** `hole_blood2` has mean bytes `[0, 0, 119, 57]`,
and red blood requires byte 2 to be R.
**Cross-format check:** 12 textures exist in both formats; `344_01_1` decodes to
R=227.8/B=35.2 as 16-bit and R=223.8/B=34.3 as 32-bit.

### Header layouts

**Version 2** (`common/textures/flare*.tex`, `shadow*.tex`)

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"LOOP"` |
| 0x04 | 4 | uint32 | version = 2 |
| 0x08 | 4 | uint32 | 0 |
| 0x0C | 4 | uint32 | 0 |
| 0x10 | 2 | uint16 | row stride in bytes |
| 0x12 | 2 | uint16 | width |
| 0x14 | 2 | uint16 | height |
| 0x16 | 2 | uint16 | bytes per pixel (2) |
| 0x18 | stride*h | | pixel data |

`flare00.tex` (8,216 bytes): stride 128, 64x64, bpp 2, `128*64 = 8192 = 8216 - 0x18`
exactly. All 10 v2 files validate.

**Version 7** (sprites, e.g. `computer/computer.res`)

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"LOOP"` |
| 0x04 | 4 | uint32 | version = 7 |
| 0x08 | 8 | | `0xABABABAB` fill |
| 0x10 | 12 | | 0 |
| 0x1C | 4 | uint32 | end offset of texture data |
| 0x20 | 4 | uint32 | texture count |
| 0x24 | 4 | uint32 | `0xABABABAB` fill |
| 0x28 | 4 | uint32 | width |
| 0x2C | 4 | uint32 | height |
| 0x30 | 4 | uint32 | format code |
| 0x34 | 40*count | | descriptors: `offset, stride, width, height, 6*uint32 0` |

All 18 v7 textures live in `computer.res`, all with `count = 1`, 46x29, format 3,
`stride = 184 = 46*4`, `data_offset = 92 = 0x34 + 40`.

**Version 9** (`terrain.tex`, `status.res`, `menusystem.res`, `sprites.res`)

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"LOOP"` |
| 0x04 | 4 | uint32 | version = 9 |
| 0x08 | 12 | | 0, 0, `0x00050000` (constant in all 145 files) |
| 0x1C | 4 | uint32 | end offset of texture data |
| 0x20 | 4 | uint32 | texture count |
| 0x28 | 4 | uint32 | width of the first texture |
| 0x2C | 4 | uint32 | height of the first texture |
| 0x34 | 32*count | | descriptors: `offset, fmt, stride\|width, height, ...` |

**Version 11** (textures inside `.res` archives)

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"LOOP"` |
| 0x04 | 4 | uint32 | version = 11 |
| 0x08 | 4 | uint32 | format code |
| 0x16 | 2 | uint16 | height |
| 0x18 | 2 | uint16 | width |
| 0x1E | 2 | uint16 | bytes per pixel |
| 0x20 | | | pixel data |

v9 and v11 differ in header layout and in how many textures a file holds, but share the
same two pixel formats.

### Mip chains

Mips exist **only** in v11 format 67: level 0 first, each level half-size, stopping once
a side reaches 1.

### Verification

| Check | Result |
|-------|--------|
| Whole tree (118 files) | **8,232 textures decoded, 0 exceptions** |
| v11 size/stride invariants | 7,199/7,199 |
| v9 descriptor contiguity | 145/145 |
| v2 size invariant | 10/10 |
| `level1.res` texture count | 393 - equals the `TEXF` count in `level1.mtp` |
| Noise scan over 88 sampled images | 0 flagged, median mean abs dR = 13.4 |

Decoded output is visually coherent game art (terrain, water, vehicle panels, cloud
layers, blood decals, ladder sprites, radial flares, walls), not noise.

### Resolved and still-open items

Seven items were open after the first pass. Corpus-wide scans over all 7,402 LOOP
containers in the tree (versions: 2 x10, 6 x14, 7 x18, 9 x159, 11 x7201) settled them:

| Item | Verdict | Evidence |
|------|---------|----------|
| v11 `0x14` | **PROVEN** - a scale level keyed to the `_scaleN` name suffix | the 9 non-default textures all live in `common/textures/common.res`, all carry `_scaleN`, and the field equals N in 9/9. Refuted as a mip bias (the default is 5, not 0, and all nine are format 2 with no mips) and as a precomputed LOD (box-downscaling `200_01_1.tex` to the 8x8 of `200_01_1_scale8.tex` leaves a mean absolute channel difference of 74.0) |
| format 67 = `0x43` | **PROVEN** - `3 \| 0x40` where `0x40` means "has mips" | the chain is always full, 428/428 |
| v6 "lighting" block | **PROVEN** - 0x18-byte header + `count` 16-byte records `[0,0,0,N]`, N = 1..count, size exactly `0x18 + 16*count` | 14/14 files. Its `+0x08` name field holds UTF-16 `"ting"` - the tail of the string `"lighting"`, whose first 8 bytes the LOOP header overwrote. The `+0x14 = 1` is a constant type tag |
| v7 descriptor stride | no counterexample - 40 bytes stays inferred | 18/18 v7 files have `count = 1` |
| v2 header field order | no counterexample - `[stride, width]` stands | 10/10 v2 files are 64x64; the `[width, height]` rival is refuted by size |
| v9 descriptor `+0x0E` | **PROVEN** - the per-glyph advance, consumed by the text-layout path | the `.res` loader reads it (`movsx eax, word [edi-0xe]` at `0x4b6ab9`) into a 36-byte per-texture record at `+0x10` (`0x4b643f`); the getter `fcn.004b6bd0` returns it and its three callers are text-layout functions - the clearest (`fcn.004b6f10`) measures a string's width by summing `record[glyph-1].+0x10` per character (glyph lookup `fcn.004b75d0`), falling back to the object-level value for unmapped characters. The `.tex` path (`fcn.00517620`) skips the field. The `{0: 493, 1: 12, 64: 498}` values are exporter defaults on non-font textures |
| v9 header `0x10 = 0x00050000` | **PROVEN** - two u16s: `[0x10] = 0`, `[0x12] = 5` = the scale level | the loader reads `movsx eax, word [esi+0x12]` at `0x5177e0` and passes it into the texture struct slot that v11 fills from its proven scale-level field at `+0x14` (`mov cx, word [esi+0x14]` at `0x4b241f`); both default to 5. The earlier "no LOOP magic in any byte order" claim was wrong - the magic is compared byte-wise (`0x517647`-`0x51766a`, `0x517749`-`0x517766`) |

---

## QVM bytecode (`.qvm`)

Header, proven on 997/997 files: `"LOOP"`, `uint32 version = 8`, `uint32 section
count = 5`, then five `(offset, size)` pairs stored **interleaved** at 0x0C..0x33, then
two reserved words. Sections tile the file exactly.

| Section | Contents |
|---------|----------|
| 0 | `uint32[]` offsets into section 1 |
| 1 | symbol table (function / enum / event names) |
| 2 | `uint32[]` offsets into section 3 |
| 3 | string constants |
| 4 | code |

Instructions are a **1-byte opcode plus a fixed-size operand**. The opcode names come
from a 49-entry table in `IGI.exe` at file offset `0x148394`, and the numbering is the
**reverse** of that list (`vm_opcode = 48 - index`). 25 opcodes appear in the retail
data and all 25 are proven; the rest are named from the exe but never emitted.

Verification: 997/997 files disassemble with 0 errors and 0 desyncs; 41,716 branches
with 0 bad targets; 34,220 CALL argument tables with 0 bad entries; 0 out-of-range
string or symbol indices.

**Interpreter internals (IGI.exe).** The loop is `fcn.004bce60`: `opcode = code[ctx->pc]`,
dispatch through the handler table `uint32[49][6]` at `0xa96868` (24-byte stride), looping
while `ctx->halt == 0 && ctx->break == 0`. Handlers take `(ctx, arg2, opcode, mode)`;
mode 0 = execute, 1 = name, 3 = disassembler. The push family: `PUSHSI/B/W` and
`PUSHII/B/W` are the same lookups at different widths (string table section 2/3, symbol
table section 0/1); `PUSHS`/`PUSHI` are inline NUL-terminated strings (tags 3/4);
`PUSHM` pushes -1; `JSR` and `RET` are halt stubs; `PUSHA` (`0x06`) pushes type 5 and is
**vestigial** - 0 occurrences in all 997 retail files. `BRK` (`0x4beb10`) sets the break
flag and is the statement/function terminator, required because the interpreter is
re-entrant (`0x4bc970` runs each inline argument fragment, which ends at its own BRK).
Native functions live in the global symbol table `0xa445d8` as 28-byte records (kind
`+0x00`, return type `+0x04`, width `+0x0c`, function pointer `+0x10`, name `+0x14`);
`CALL` (`0x4bd710`) requires `kind == 1`, calls `fn(&retbuf, record->0x18, &frame)`, and
the return is a 24-byte struct `{int@+0, double@+8, char*@+0x10}`; `pc += argc*4 + 5`.
The VM context: `+0x00` code, `+0x14` pc, `+0x18`/`+0x1c` stack pointers, `+0x20` halt
code, `+0x2c` break flag, `+0x30`/`+0x48` table descriptors.

Full tables and the readable decompiled examples are in
[03-scripting](../03-scripting/README.md). Disassemble with `reverse/tools/qvm.py`.

---

## Audio: ILSF sample container

**Every audio file in the game is ILSF, not RIFF/WAVE.** 413 loose `.wav` files plus
346 `.res` `BODY` payloads = 759 payloads, 0 exceptions.

| Offset | Size | Type | Meaning |
|--------|------|------|---------|
| 0x00 | 4 | char[4] | `"ILSF"` |
| 0x04 | 2 | uint16 | version **bitfield**: bit0 = inside a `.res` `BODY`, bit1 = IMA ADPCM |
| 0x06 | 2 | uint16 | bits per sample - always 16 |
| 0x08 | 2 | uint16 | channel count (1 or 2) |
| 0x0A | 2 | uint16 | flags: `0` loose, `0x1002` in `.res` - **authoring metadata, read by nothing** |
| 0x0C | 4 | uint32 | sample rate: 11025 / 22050 / 44100 |
| 0x10 | 4 | uint32 | frame count (samples per channel) |
| 0x14 | | | sample data |

Versions 0/1 are 16-bit PCM (341 payloads); versions 2/3 are 4-bit IMA ADPCM (418).
The loader is `fcn.00495e00` (magic compare `cmp eax, 0x46534C49` at `0x495e36`). It
copies the 20-byte header to `obj+0x10` (`0x495ec7`) but only ever reads `+0x14` version
(`0x495ec9`), `+0x16` bits (`0x495fdf`), `+0x18` channels (`0x495fdb`), `+0x1c` rate
(`0x495fc8`) and `+0x20` frames (`0x495f3b`) - an exhaustive `.text` scan for any operand
with displacement `0x1a` finds 11 hits, none in the sound module `0x495000`-`0x497000`.
The version switch table `0x4960d0` = `[0x495ee0, 0x495f95, 0x495ee0, 0x495f30]` proves
the bitfield (v0 == v2, v1 != v3); bit1 is consumed in the streaming path
(`0x496a47 cmp word [ecx+0x14], 2` -> `0x496b70` ADPCM / `0x496c10` PCM). The trailing
byte in compressed payloads is **zero pad, never read**: the nibble pump
(`0x496193`-`0x4961bc`) consumes exactly `ceil(frames*channels/2)`; over all 418
compressed payloads, 205 are exact and 213 are exactly +1 (the extra byte is `0x00` in
209 of 213).

---

## Fonts: `.fnt`

A **custom ILFF bitmap font**, not a Windows FNT. Two loose files plus five inside
archives. Both loose files share the same chunk layout:

| Chunk | Contents |
|-------|----------|
| `FONTFNTH` | header; field 1 = the glyph count (154 in both files) |
| `TRAN` | 131,072 bytes; the **character-to-glyph map** is the 256 `uint16` at `+0x08` |
| `TEXH` | atlas header (256x128 and 128x128) |
| `ANMF` | 154 glyph records x 40 bytes |
| `BODY` | a 32bpp atlas with coverage in the low byte |

**The float at glyph `+0x10` is the baseline, not a height.** Reading it as a baseline
makes `(x, v*128 - h, w, h)` contain ink for **154/154 glyphs of both fonts**; reading
it as a height gives 39/154. `(u_end - u_start) * atlas_width == width` holds 154/154.

**Loader evidence (`fcn.004b65d0`).** The `TRAN` map is 256 `uint16` at byte offset 8,
indexed by Latin-1 code, value = glyph index; it is a permutation of 1..154 with 102
zeros, byte-identical in both fonts (`!` -> 1, `A` -> 34, `C4` -> 146, `E9` -> 104,
`F7` -> 154). The loader reads it at stride 2 into a 256-byte table at `font+0x0C`
(alloc `0x4b674d`, loop `0x4b6752`-`0x4b676e`), so the Latin-1 tail mapping is now
verified code-side, not sampled. `FONTFNTH` is 6 dwords `[1, 154, 0x20, 6|4, 0x18,
0x15|0xf]`: field 1 = glyph count (`0x4b66de`), field 5 = **max glyph height + 1**
(font3 20 -> 21, font4 14 -> 15), fields 3/4/5 are stored into the sentinel glyph at
index 154 (`0x4b6527`/`0x4b6534`/`0x4b6543`), field 2 (32) has no reader. The glyph
record is 40 bytes: floats `u0/v0/u1/v1` at `+0x04`/`+0x08`/`+0x0C`/`+0x10`, words
width/height/advance at `+0x16`/`+0x18`/`+0x1A` - verified 154/154 in both fonts
(`(u1-u0)*W == width`, `(v1-v0)*H == height`, every rect contains ink). `+0x24` is a
per-glyph 16-bit vertical metric (0..16) copied into the internal 36-byte glyph at
`+0x10` (`0x4b643f`); its exact semantic is unsettled. The purpose of the remaining
`TRAN` bytes (65,280 `uint16` after the map) is not established.

---

## Animation: `.iff`

Six files, **EA IFF 85** containers (`FORM`/`BOBJ`) holding skeletal animation.
Big-endian chunk sizes, little-endian payloads.

| Chunk | Size | Contents |
|-------|------|----------|
| `BOAH` | 12 | |
| `BOTH` | 4 | |
| `BOTD` | 40 | |
| `BORH` | 4 | |
| `BORD` | 52 | looks like a quaternion written three times plus one float |
| `BOEH` | 4 | |
| `BOED` | 4 | |
| `BOSH` | | `[file_index, bone_count]` (6/6) |
| `PLST` | | parent indices, `-1` at the root |
| `TLST` | | rest-pose translations |
| `BALH` | | `[0]` = the `BOAN` count (6/6) |

Framing, sizes and the bone tables are proven 6/6; the animation semantics are not
decoded.

**Loader evidence.** The files are live assets: `fcn.004d2770` looks up a `BANM` chunk
(animation name list) and, for each name, builds `"%sanims/%s.iff"` (`0x4d27b6` /
`0x4d27f8`, string at VA `0x548c54`) and calls `fcn.004d65f0`. That loader parses the IFF
container (`fcn.00517a80`), walks `BOBJ` -> `BOBH` -> `BOSH` (skeleton: `[0]` = model
slot, `[+4]` = bone count), copies `PLST` (parent indices) and `TLST` (rest
translations) into global tables at `0xa54a40` / `0xa54a44` / `0xa54a48`, then reaches
`BALO`/`BALH` (bone animation; `BALH[0]` = BOAN count, `BALH[+4]` = slot count).

**Playback (proven).** `fcn.004d2bc0` builds the bone objects (`bone_count * 0x84`
bytes) and `fcn.004d2d20` builds the hierarchy recursively from the `PLST` parent
indices (`0x4d2d3f`) and `TLST` rest translations (`0x4d2d73` -> `bone+8`, `0x4d2da5` ->
`bone+0x14`). `fcn.004d49b0` is the per-frame update (`time += speed` at `+0x28`,
`0x4d49e8`; wrap/loop at `0x4d4ab4`-`0x4d4ad6`). The pose sampler `fcn.004d4fd0` uses a
52-byte key stride with the key time at `+0x10`, finds the bracketing keys
(`0x4d508c`), computes `(t-t0)/(t1-t0)` (`0x4d515e`-`0x4d5180`) and blends the two
quaternions with `fsin` weights - a **SLERP** (`0x4d525a`, `0x4d54bd`/`0x4d54ca`) -
emitting 20 bytes `{quat, 1-based key index}` (`0x4d5505`, `0x4d550f`). `fcn.004d6b90`
precomputes the per-key `{angle, sin(angle)}` weights; `fcn.004d4690` handles the `BOTD`
cubic spline (40-byte stride, `3.0f` at `0x53352c`). Selection: `entity+0x68` is the
bone object and `entity+0xcfc` the animation index; `0x453e50` calls `fcn.004d6020`
(play), which has 31 callers across AI and player code, and a miss logs
`"Animation #%d not found"` (`0x53ee28`). `AIEVENT_ANIMATION` is enum value 3
(`0x44f2a6`).

---

## Cutscenes: `.avi`

Five standard RIFF/AVI files, 320x240, **Intel Indeo 5.0 (`IV50`)**, one video stream
each - the audio lives in the paired ILSF `.wav`. Durations 13.4 to 120.9 seconds.

---

## Menus and sprites

`pc/menusystem/*.res` and `pc/screens/**/*.res` are ILFF archives whose contents are
**LOOP textures**; the nested `ILFF` payloads inside them are `.fnt` fonts.

**`.spr` / `.pic` are extension labels, not formats.** The archives hold **158 `.spr`**
entries (`computer/computer.res` 49, `screens/game/status/status.res` 47,
`menusystem/menusystem.res` 24, `common/sprites/sprites.res` 16,
`menusystem/missionsprites.res` 14, `menusystem/ingamemenu.res` 8) and **5 `.pic`**
entries (`mainmenu.pic`, `logo.pic`, `logo_us.pic` in `menusystem.res`; `loading.pic`,
`loading_us.pic` in `loadingscreen.res`). Every one of those payloads starts with
`LOOP` + version 9 - they are LOOP textures (sprites, HUD elements, the main-menu and
loading pictures), not a separate binary format. A menu sprite decodes to a coherent
PNG with `reverse/tools/loop.py`.

---

## Text files

The 12 `.txt` / `.rtf` files are the plain-ASCII README (v1.0, 29 Nov 2000). Each
language's `.txt` and `.rtf` are **byte-identical**, so the `.rtf` extension is a
misnomer. The 5 `.url` files are Windows Internet Shortcuts.

---

## What is still unknown

The disassembly pass closed 8 of the 16 items outright and advanced the rest. What
remains:

1. **`OCEMHSEM` leftovers** - `+0x7C` (XTVM record count) and `+0x7E` (ATTA record
   count) are now consumed and proven; the fields at `+0x0C`/`+0x10`/`+0x14`/`+0x18`/
   `+0x1C` still have no located consumer.
2. **`DNER` leftovers** - `+0x18` is a deferred/sorted-render flag (32-byte variant);
   `+0x1A`/`+0x1E` have no located consumer.
3. **`TAMC` record fields** - the shape is data-inferred (`{float, 0xffff, a, b, 0}` with
   `(a,b)` = `(i, 15-i)`); no consumer was located. `HPSC` is consumed (24-byte records
   copied at `0x4e4e3d`).
4. **`PMTL` semantics** - the first dword is always
   `(0x10000|0x20000|0x40000|0x80000) | low` with `low` in
   `{1,2,4,8,0x10,0x20,0x40,0x100}`; stored at `D3DR+0x18` only for flag 3, where no
   reader was found (for flag 1 the same slot holds XTRV and is read at `0x49b653`).
5. **`.cmd` triangle flag bit** - the high nibble is inferred to be a material index
   (14/15/4); winding, parent/child split and index ordering were rejected. The `A`/`B`
   fields of the vertex entry remain inferred.
6. **`cmd_transform[0..7]`** - the unused/present rule is proven (149,243/149,256 records;
   the 13 exceptions are the zero-filled root records); what the 0..7 value selects is
   not (a D4 symmetry index is the natural reading, unconfirmed).
7. **`.fnt` leftovers** - the glyph record `+0x24` (a per-glyph 16-bit vertical metric,
   0..16) has an unsettled semantic, and the purpose of the remaining `TRAN` bytes
   (65,280 `uint16` after the map) is not established.
8. **Save format, network protocol** - no evidence found in the retail tree.

Resolved by the disassembly passes: the nav cell field (**next-hop node ID**), `.mtp`
`INST` semantics, ILSF flags/version/trailing byte, QVM leftovers (PUSHA/BRK/native call
convention), LOOP leftovers (v9 `+0x0E` and header `0x10`), the weapon damage formula,
the `.fnt` `TRAN` map and `FONTFNTH` fields, **`.iff` playback** (bone objects, per-frame
update, SLERP sampler, selection path), and **world scale** (4096 units = 1 m - see
[13-implementation](../13-implementation/README.md)).
