# 04 - Rendering System

## Technology Stack

| Component | Technology | Confidence | Method |
|-----------|------------|------------|--------|
| Primary API | Direct3D 7 | ✅ Verified | DLL import analysis |
| Backend | DirectDraw 7 | ✅ Verified | DLL import analysis |
| Fallback | GDI (CreateICA) | ✅ Verified | DLL import analysis |
| Texture Management | Custom allocator | ⚠️ Inferred | Function names |

## Vertex Formats

### ModelVertex - 40 or 32 bytes ✅ VERIFIED

Extracted from the retail model files, not reconstructed. See
[16-verified-formats](../16-verified-formats/README.md) for the full proof.

```c
struct ModelVertex {          // 40 bytes - 6,178 models
    float x, y, z;            // 0x00  position
    float nx, ny, nz;         // 0x0C  normal
    float u, v;               // 0x18  diffuse texture coordinates
    float lu, lv;             // 0x20  lightmap coordinates
};

struct ModelVertexNoLM {      // 32 bytes - 617 models
    float x, y, z;            // 0x00  position
    float nx, ny, nz;         // 0x0C  normal
    float u, v;               // 0x18  diffuse texture coordinates
};
```

**Two formats exist and the split is exact.** Across all 6,795 models: 6,178 use the
40-byte vertex, 617 use the 32-byte one, and **0 are ambiguous** - a stride is valid
only if it divides the `XTRV` payload and every vertex's normal at `+0x0C` is unit
length, and exactly one stride satisfies that per model.

**Proof.** At the correct stride **100% of the 1,468,324 normals in the game are unit
length**. Forcing a single 40-byte stride on both formats is what produced the earlier
94.90% figure - the 32-byte models were being mis-parsed.

The two UV pairs in the 40-byte form are distinguishable by range: the diffuse pair
spans `[0.0005, 0.9995]` (texel centres of a 1024-wide texture), the lightmap pair
spans a small sub-rectangle of the lightmap atlas.

### BoxVertex - 16 bytes ✅ VERIFIED

`XTVC` chunks hold position-only vertices: `float32 x, y, z, 0`. Level 1's first model
has 16 of them forming a box with `x in {1431.2, -1848.8}`, `y in {-8203.6, 8176.0}`,
`z in {-842.5, 487.4}`.

### TerrainVertex - ❌ NOT EXTRACTED (runtime format)

The terrain mesh is generated at runtime from `.bit`/`.hmp`/`.cmd`; no terrain vertex
buffer is stored on disk, so there is nothing to extract. The on-disk `.cmd` payload is
decoded (see 07-terrain): triangle descriptors (3 x `uint8` index + flag byte) and the
packed 4-byte vertex entries, proven over 840,866 entries.

## Index Format ✅ VERIFIED (models)

| Chunk | Record | Indices into |
|-------|--------|--------------|
| `ECFC` | 8 bytes: `uint16 i0, i1, i2, material` | `XTVC` (box vertices) |
| `DNER` | batch header + `uint16` triangle list | `XTRV` (render vertices) |

`ECFC` indices are verified in range: the first level-1 model's 28 records index 0-15
(16 box vertices), the second model's 10 records index 0-7 (8 box vertices). The
triangles pair into quads, e.g. `(0,1,2)` + `(1,0,3)`.

`DNER` holds one or more batches. The first level-1 model's `DNER` is 220 bytes: a
32-byte header then 16 quads (`(0,1,2) (1,0,3) (4,5,6) (5,4,7) ...`, indices 0-31),
followed by a second batch header and 10 more triangles.

## MEF model chunk tree ✅ VERIFIED

Tags are stored byte-reversed on disk. The logical names are the reversed strings:

| On disk | Logical | Payload |
|---------|---------|---------|
| `OCEMHSEM` | `MESHMECO` | model header (floats, counts, bounding data) |
| `ATTA` `XTVM` `TROP` `XVTP` `CFTP` | - | zero-length markers |
| `D3DR` | `RD3D` | D3D render state: `4, 1, 26, 2, 52, 0...` |
| `DNER` | `REND` | render triangle batches |
| `XTRV` | `VRTX` | render vertices (40 bytes each) |
| `PMTL` | `LTMP` | 8 bytes: `0x10040, 0` |
| `HSMC` | `CMSH` | mesh info: `28, 16, 3, 55, 0, 0, 0, 0, 10, 8, 1, 19, ...` |
| `XTVC` | `CVTX` | box vertices (16 bytes each) |
| `ECFC` | `CFCE` | box faces |
| `TAMC` | `CMAT` | material |
| `HPSC` | `CSPH` | collision spheres |

## Texture Formats ✅ VERIFIED

LOOP textures use two pixel formats, selected by a format code in the header:

| Code | Format | Share |
|------|--------|-------|
| 2 | 16-bit `ARGB1555` (bit15 = A, 14-10 = R, 9-5 = G, 4-0 = B) | 93.8% |
| 3 | 32-bit `A8R8G8B8` (D3DFMT_A8R8G8B8; bytes in memory B, G, R, A) | 0.1% |
| 67 (`0x43`) | 32-bit `A8R8G8B8` + a full mip chain | 5.9% |

The game's own level manifests name the 32-bit textures with an `_argb8888` suffix, and
those are exactly the code-3/code-67 textures - an independent confirmation from the
game's data rather than from the pixels.

**Falsified hypotheses:** 8-bit palettised (the data size is exactly `w*h*2` and the
`PALF` chunk is 4 bytes of zero in every level); RGB565 (a sky gradient's green channel
swings 42 to 12 between adjacent pixels under RGB565 but is monotone under ARGB1555);
byte-plane split (mean abs dR rises from 39.24 to 57.97).

Mips exist only in format 67: level 0 first, each level half-size, stopping once a side
reaches 1.

Decode with `reverse/tools/loop.py`; the whole tree decodes 8,232 textures from 118
files with zero exceptions.

## Loader evidence (IGI.exe)

Static disassembly of `IGI.exe` (PE32, imagebase `0x400000`) located the model and
texture loaders and settled several of the open header questions. Markers: ✅ = an
instruction at the cited VA does exactly what is claimed, ⚠️ = consistent with
code+data but not directly witnessed, ❌ = tested and not settled.

### MEF model loader - fcn.0049f9a0 ✅ VERIFIED

The mesh loader `fcn.0049f9a0` (`0x49f9a0`) is registered as method `LoadModel` of class `Direct3D`
(`push str.LoadModel` at `0x4d1d60`, id assigned at `0x4d18e0`/`0x494f70`, registered
through `0x4b0d50`, invoked through the dispatcher `0x4b0e90`). It switches on the
format flag at `[mesh+0x20]`:

```
0x49f9a9  mov eax,[esi]        ; mesh object
0x49f9ab  mov eax,[eax+0x20]   ; format flag
0x49f9ae  sub eax,0 / je 0x49fb01    ; flag 0
0x49f9b7  dec eax / je 0x49fa80      ; flag 1
0x49f9be  sub eax,2 / je 0x49f9d2    ; flag 3
0x49f9c3  push "Mesh format not supported"
```

It looks up the chunks by tag - `D3DR` (`push 0x52443344` at `0x49f9d6`, `0x49fa84`,
`0x49fb05`), `XTRV` (`push 0x56525458` at `0x49fa01`, `0x49fab2`, `0x49fb30`), `DNER`,
`PMTL`, `HSMC` (`push 0x434d5348` at `0x49fbdb`), `XTVC`, `ECFC`, `TAMC`, `HPSC` - and
**the mesh object IS the `OCEMHSEM` payload**: the loader writes pointers into it
(`+0x24` = D3DR at `0x49f9f8`, `+0x2c` = HSMC at `0x49fc1a`) and the flush code reads
the same offsets.

| mesh field | flag 0 (`0x49fb01`) | flag 1 (`0x49fa80`) | flag 3 (`0x49f9d2`) |
|---|---|---|---|
| +0x20 | format flag (read) | read | read |
| +0x24 | D3DR payload (`0x49fb27`) | D3DR (`0x49faa6`) | D3DR (`0x49f9f8`) |
| +0x2c | HSMC payload (`0x49fc1a`) | HSMC | HSMC |
| D3DR+0x10 | XTRV (`0x49fb53`) | - | - |
| D3DR+0x14 | DNER (`0x49fb77`) | - | XTRV (`0x49fa24`) |
| D3DR+0x18 | - | XTRV (`0x49fad2`) | PMTL (`0x49fa6f`) |
| D3DR+0x1c | - | DNER (`0x49faf9`) | DNER (`0x49fa4b`) |
| count -> `0x49b2c0` | `[D3DR+0xc]` (`0x49fb7a`) | none | `[D3DR+0x10]` (`0x49fa72`) |

`0x49b2c0(slot, mesh, count)` accumulates meshes into one of three 4008-byte batch
slots (`0x720d10 + slot*0xfa8`, `0x49b2cb`-`0x49b2d7`) and flushes at 1000 meshes or
65535 vertices.

### OCEMHSEM ✅ VERIFIED (data-proven fields)

The loader reads only `+0x20` (format flag, `0x49f9ab`) and writes `+0x24`/`+0x2c`.
The remaining fields are per-model data; these are proven by correlating all 415
level-1 models (6,984 game-wide):

| Offset | Meaning | Evidence |
|---|---|---|
| +0x20 | format flag (3 = 344, 1 = 25, 0 = 46 in level 1) | read at `0x49f9ab` |
| +0x24 | D3DR pointer (0 on disk) | written at `0x49f9f8` |
| +0x2C | HSMC pointer (0 on disk) | written at `0x49fc1a` |
| +0x30 | tight sphere of the render vertices (x,y,z,r) | 386/411 exact |
| +0x40 | tight sphere of render ∪ collision vertices | 160/165 exact |
| +0x50 | duplicate of +0x40 | 415/415 identical |
| +0x60 | DNER triangle count | 415/415 == sum(index_count)/3 |
| +0x64 | XTRV vertex count | 415/415 == XTRV_size/stride |
| +0x68 | D3DR+DNER+XTRV byte total | 415/415 (e.g. 56+220+2080 = 2356) |
| +0x6C | total ECFC face count | 415/415 (28+10 = 38) |
| +0x70 | total XTVC vertex count | 415/415 (16+8 = 24) |
| +0x74 | total collision byte count (HSMC+XTVC+ECFC+TAMC+HPSC) | 415/415 (64+384+304+48+1776 = 2576) |

**Bounding spheres.** `+0x30` is a tight enclosing sphere of the render vertices
(`max distance(centre, XTRV) == radius` in 386/411 models, exact to 0.05 units);
`+0x40`/`+0x50` are identical and tight for the render ∪ XTVC collision vertices
(160/165 exact). The centre is not the model origin, the bbox centre or the vertex
centroid (median distance to the bbox centre 649 units for sphere 1, 768 for sphere 2)
- it is a fitted centre produced by the exporter.

❌ **Consumers not found:** `+0x0C`/`+0x10`/`+0x14`/`+0x18`/`+0x1C`. No
instruction reading those offsets off a mesh object was located; the values are
per-model data, so "exporter leftover" is the weaker reading. (`+0x7C` is now
resolved - see MEF field consumers below.)

### DNER ✅ VERIFIED (header sizes)

Two header sizes, selected by the mesh format flag, not by the data:

| Variant | Header size | Models |
|---|---|---|
| 28-byte | `0x1C` | flag 0 (46/46) and flag 1 (25/25) |
| 32-byte | `0x20` | flag 3 (344/344 with a non-empty DNER) |

Walk rule (`0x49ca47`-`0x49ca5a`, `0x49c61e`-`0x49c637`): `next = batch + [batch+0x0E] + 0x1C`
for the 28-byte variant; `[batch+0x0E] == 0xffff` marks the last batch. The 32-byte
variant advances by `0x20 + [batch+0x0E]`.

| Offset | Meaning | Evidence |
|---|---|---|
| +0x0C | u16 index count | `mov cx,word [esi+0xc]` `0x49c509`, `0x4a1aec`, `0x4a204f`; `/3` via `imul 0x55555556` `0x49c510` |
| +0x0E | u16 index byte count (0xffff = last batch) | `0x49c61e`-`0x49c62d`, `0x49ca47`-`0x49ca56` |
| +0x12 | u16 vertex base (28-byte variant) | `mov ax,word [esi+0x12]` `0x49c52d`, `0x4a1b10` |
| +0x14 | u16 vertex base (32-byte variant) | `mov ax,word [edi+0x14]` `0x4a2073` |
| +0x16 | u16 vertex count | `cmp word [ebx+0x16],0` `0x49c8ca` |
| +0x1C | index list (28-byte variant) | `lea ebp,[esi+0x1c]` `0x4a1af0` |
| +0x20 | index list (32-byte variant) | `lea ebp,[edi+0x20]` `0x4a2053` |

The earlier discriminator `u32@+0x1C == 0x00010000` is a **data heuristic**: for
28-byte headers `+0x1C` holds the first two indices, which are (0,1) for the first
triangle, i.e. bytes `00 00 01 00`. The real selector is the mesh format flag.

⚠️ **Partly resolved:** `+0x18` in the 32-byte variant is the deferred/sorted-render
flag (see MEF field consumers below); `+0x1A`/`+0x1C`/`+0x1E` still have no located
consumer.

### HSMC - descriptor layout corrected ✅ VERIFIED

The earlier reading `{ecfc, xtvc, tamc, hpsc, pad[4]}` is **wrong**. The loader
overwrites `+0x10..+0x1F` and `+0x30..+0x3F` with pointers (`0x49fc97`-`0x49fcd4`), so
those are runtime pointer slots, not data. The on-disk layout is 2 x 32-byte
descriptors of {4 counts, 4 pointer slots}:

```
desc+0x00 u32 ECFC record count      desc+0x10 u32 ECFC payload pointer  (filled at load)
desc+0x04 u32 XTVC vertex count      desc+0x14 u32 XTVC payload pointer
desc+0x08 u32 TAMC record count      desc+0x18 u32 TAMC payload pointer
desc+0x0C u32 HPSC record count      desc+0x1C u32 HPSC payload pointer
```

Verified on model 1: descriptor 1 = {28, 16, 3, 55} with ECFC 224/8 = 28, XTVC
256/16 = 16, TAMC 36/12 = 3, HPSC 1320/24 = 55; descriptor 2 = {10, 8, 1, 19}.
**169/169** 64-byte HSMC chunks in level 1 have descriptor 1's counts equal to group
1's chunk sizes and descriptor 2's to group 2's, with all 8 pointer slots zero on disk.

### PMTL ✅ VERIFIED (bit pattern)

Across 5,628 PMTL chunks the first dword is always
`(0x10000|0x20000|0x40000|0x80000) | low` with `low` in {1, 2, 4, 8, 0x10, 0x20, 0x40,
0x100} (0x10001, 0x10002, 0x10004, 0x10008, 0x10010, 0x10020, 0x10040, 0x20020,
0x20040, 0x200100, 0x40040, 0x80040); the second dword is always 0. The loader stores
the PMTL pointer at `D3DR+0x18` **only for flag 3** (`0x49fa6f`); flag 0/1 models have
no PMTL chunk at all (46/46 and 25/25 in level 1).

⚠️ The bit pattern reads like a packed state/flag word, but no consumer instruction was
found, so the semantics remain unresolved.

### D3DR - the runtime struct ✅ VERIFIED

The on-disk chunk is the runtime struct, partially initialised; the flush at `0x49b340`
completes it. 48 bytes for flag 0, 56 bytes for flags 1 and 3:

| Offset | flag 0 (48 B) | flag 1 (56 B) | flag 3 (56 B) |
|---|---|---|---|
| +0x0C | **vertex count** (18) | 231 | 2 |
| +0x10 | XTRV ptr | 958 | **vertex count** (52) |
| +0x14 | DNER ptr | **vertex count** (1189) | XTRV ptr |
| +0x18 | 0 | XTRV ptr | PMTL ptr |
| +0x1C | 0 | DNER ptr | DNER ptr |
| +0x20 | 1 (flush) | - | 0 |
| +0x28 | batch ptr (flush) | - | 1 (flush) |
| +0x2C | XTRV ptr (flush) | - | u16 0 (flush) |
| +0x30 | - | - | batch ptr (flush) |
| +0x34 | - | - | XTRV ptr (flush) |

The flush confirms the layouts and the vertex strides: for flag 3 it reads
`word [D3DR+0x10]` as the vertex count and `[D3DR+0x14]` as the vertex array, copying
`count*40` bytes (`0x49b463`-`0x49b486`); for flag 0 it reads `word [D3DR+0xc]` and
`[D3DR+0x10]`, copying `count*32` bytes (`0x49b4b9`-`0x49b50c`).

### MEF field consumers ✅ VERIFIED (with documented negatives)

A follow-up pass enumerated every `instance+0xc -> model+0xc -> mesh` double-deref
site in `.text` (the canonical `8b 48 0c 8b 51 0c` pattern, 8 sites) and scanned
each mesh register for reads at the leftover offsets. `+0x7C`, `+0x7E`, `DNER+0x18`
and `HPSC` are consumed; the rest are documented negatives.

| Field | Meaning | Evidence |
|---|---|---|
| `OCEMHSEM +0x7C` | XTVM record count (16-byte records) | getter `fcn.004cf9b0`: `movsx eax, word [edx+0x7c]` `0x4cf9ba` |
| `OCEMHSEM +0x7E` | ATTA record count (68-byte records) | getter `fcn.004cf9a0`: `movsx eax, word [edx+0x7e]` `0x4cf9aa` |
| `DNER +0x18` (32-byte variant) | deferred/sorted-render flag | `cmp word [ebp+0x18], 0` / `jne 0x49e620` `0x49e578` |
| `HPSC` | collision spheres, 24-byte records | `0x4e4e3d`, `0x4e4e70`, `0x4e4e92` |
| `D3DR +0x18` (flag 1) | XTRV pointer; read as the first vertex's lightmap UV | `fld dword [eax+0x20]` `0x49b653` |

**`+0x7C` - XTVM record count.** The getter walks the same chain as every other
consumer (`instance+0xc -> model+0xc -> mesh`):

```
0x4cf9b0  mov eax, [esp+4]        ; instance
0x4cf9b4  mov ecx, [eax+0xc]      ; model
0x4cf9b7  mov edx, [ecx+0xc]      ; mesh
0x4cf9ba  movsx eax, word [edx+0x7c]
```

Callers use it as a threshold (`cmp eax, ecx / jle` `0x414ed9`) and as a
skip-when-zero guard (`test esi, esi / je 0x44755a` `0x44736c`). Data proof:
`+0x7C == XTVM_size / 16` in **2,876/2,876** models across levels 1, 10, 11, 12,
13, 14 (415/415 in level 1) - so the XTVM records are 16 bytes.

**`+0x7E` - ATTA record count.** Getter `fcn.004cf9a0` (`movsx eax, word
[edx+0x7e]` `0x4cf9aa`); the caller at `0x4c47cf` uses it as the loop bound and
indexes `ATTA[i]` through `fcn.004cf980`, which computes `ATTA + index*68`
(`shl ecx,4` / `add ecx,eax` / `lea eax,[edx+ecx*4]` `0x4cf990`-`0x4cf99b`).
Data proof: `+0x7E == ATTA_size / 68` in **2,876/2,876** models.

**`+0x0C`/`+0x10`/`+0x14`/`+0x18`/`+0x1C` - no consumer located.** Every
instance->model->mesh double-deref site was enumerated; the only mesh reads found
are `+0x2c`, `+0x30`-`+0x38`, `+0x7c`, `+0x7e` and `+0x8c`. The five fields are
not chunk sizes and not counts of any known chunk, so the "exporter leftover /
source-model metadata" reading stands - a negative result, not a proof.

**`DNER +0x18` - deferred/sorted-render flag (32-byte variant).** The draw loop
tests it before the normal path:

```
0x49e578  cmp word [ebp+0x18], 0
0x49e57d  jne 0x49e620            ; non-zero -> deferred path
```

The deferred path allocates a 0x68-byte item via `0x4b71a0` with the callback
`0x49f050` and copies the renderable's transform, the D3DR pointer and the DNER
batch pointer into it. Data: flag 3 `+0x18` = 0 (313/340) or 1 (27/340) - bit 0 of
a wider bitfield. `+0x1A` and `+0x1E` have no located consumer (every 16-bit read
at those offsets is a texture-struct read).

**`HPSC` - consumed.** The collision-object builder `0x4e4e20` reads the count
(`mov esi, [eax+0xc]` `0x4e4e3d`; `mov eax, [edx+0xc]` `0x4e4e70`), allocates
`count*24` (`lea eax,[eax+eax*2]` / `shl eax,3` `0x4e4e76`-`0x4e4e79`, `call
0x4b0af0` `0x4e4e7d`) and copies the records from the pointer (`mov esi,
[edx+0x1c]` `0x4e4e92`). So HPSC records are **24 bytes**. `TAMC` has no located
consumer - the loader fills the count/pointer slots but no reader was found.

**`PMTL` / `D3DR+0x18`.** The PMTL pointer is stored at `D3DR+0x18` only for flag 3
(`0x49fa6f`); for flag 1 the same slot holds XTRV and **is** read at `0x49b653`
(`fld dword [eax+0x20]` = the first vertex's lightmap UV). For flag 3 no reader of
`D3DR+0x18` was found, so the PMTL pointer is write-only as far as located code is
concerned.

### LOOP texture loader map ✅ VERIFIED

Three loaders read LOOP textures, and **the magic is checked byte-wise**, never as a
32-bit immediate - which is why every dword search for `LOOP` missed it:

| Function | Versions | Called from | Magic check |
|---|---|---|---|
| `fcn.00517620` (`0x517620`) | v7, v9 | the `.tex` path at `0x4c5dfd` | `cmp al,0x4c` / `cmp byte [esi+1],cl` / `[esi+2],cl` / `[esi+3],dl` at `0x517647`-`0x51766a` (v7) and `0x517749`-`0x517766` (v9) |
| `fcn.004b2370` (`0x4b2370`) | v2, v11 | (not traced) | `0x4b2383`-`0x4b2405` |
| `fcn.004b6982+` (`0x4b6982`) | v7, v9, ... | `.res`-embedded payloads | `0x4b69f4`-`0x4b6a19` |

The v9 header word at `+0x10` (`0x00050000`) is two u16s: `u16[0x10] = 0`,
`u16[0x12] = 5`. The loader reads the u16 at `+0x12` as a signed int16
(`movsx eax, word [esi+0x12]` at `0x5177e0`) and passes it as the scale level - the
same struct slot the v11 loader fills from its `+0x14` (`mov cx, word [esi+0x14]` at
`0x4b241f`), the field already proven to be the `_scaleN` key.

The v9 descriptor (32 bytes, base = file+`0x34`, stride `0x20`):

| Offset | Type | Meaning | Evidence |
|---|---|---|---|
| +0x00 | dword | pixel data offset | read by the `.tex` path |
| +0x04 | dword | format code | read by the `.tex` path |
| +0x08 | u16 | stride | read by the `.tex` path |
| +0x0a | u16 | width | read by the `.tex` path |
| +0x0c | u16 | height | read by the `.tex` path |
| +0x0e | int16 | per-glyph advance | read by the `.res` path at `0x4b6ab9`, stored into a 36-byte record at `+0x10` (`0x4b643f`), consumed by the text-width function `0x4b6f10` |
| +0x10..+0x1f | - | tail (zero except 6 descriptors in `status.res` with `+0x1f` = 2 or 4) | data |

## Lighting

### Lightmap System ✅ VERIFIED (storage)

Lightmaps are stored in `terrain.lmp` as a flat sequence of size-prefixed **8-bit
greyscale** square images:

```
repeat until EOF:  uint32 size;  uint8 pixels[size*size]
```

Level 1: 268 images, sizes 16 (x138), 32 (x79), 64 (x40), 128 (x11). The walk consumes
the file exactly. The renderer expands each texel to RGBA with `alpha = texel ? 255 : 0`.

The lightmap UVs are carried per-vertex in the model vertex (offset 0x20). The blending
mode is not verified.

## Camera / Fog / Skybox

Not extracted. No verified FOV, clip distances, fog parameters or skybox layout.

## Performance

Not measured. No runtime profiling was performed.

## Known Issues

1. **`DNER` / `OCEMHSEM` header fields** - triangle and vertex data decoded; `+0x7C`
   (XTVM count), `+0x7E` (ATTA count) and DNER `+0x18` (deferred flag) are now
   consumed, the remaining header fields are not.
2. **`.cmd` triangle flag / vertex `A`/`B` fields** - the payload is decoded (indices +
   packed vertices); the flag high nibble (material index) and `A`/`B` semantics are
   inferred, not proven.
3. **Terrain vertex format** - generated at runtime, nothing on disk to extract.
4. **Lightmap blending** - storage verified, blend mode not.

## References

- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
- Parsers: `reverse/tools/igi_formats.py` (`parse_mef`, `parse_mef_vertex`),
  `reverse/tools/loop.py` (textures)
