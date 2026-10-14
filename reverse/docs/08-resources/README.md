# 08 - Resource System (ILFF)

**Status: solved and verified.** The container parses cleanly on all 92 `.res` archives
in the retail game (90,893 chunks), and every parse consumes exactly the declared file
size. Byte-level tables are in [16-verified-formats](../16-verified-formats/README.md).

## ILFF Header (16 bytes)

| Offset | Size | Type | Meaning | Evidence |
|--------|------|------|---------|----------|
| 0x00 | 4 | char[4] | `"ILFF"` | all 92 files |
| 0x04 | 4 | uint32 | total file size | equals on-disk size in all 92 files |
| 0x08 | 4 | uint32 | sub-format: `4` (91 files) or `32` (1 file) | histogram over the tree |
| 0x0C | 4 | uint32 | always 0 | all 92 files |

## Chunk Structure

```
char[]   id      ASCII tag, null-padded to a 4-byte boundary (4 or 8 bytes)
uint32   size    payload byte count
uint32   type    mirrors the file sub-format
uint32   total   align4(16 + size) when non-zero; frequently 0
uint8    payload[size]
         pad to 4-byte alignment
```

Next chunk = `align4(offset + id_field + 12 + extra + size)`, `extra = 28` for type-32
chunks.

**The `total` field is not the advance.** It ignores the extra 4 bytes of an 8-byte tag
and is often 0. Two proofs: `NAME` at 0x14 of `common/sounds/sounds.res` has `size=36`,
`total=52`, but the next `BODY` is at 0x48; and `BODY` at 0x54 of
`common/textures/common.res` has `size=32800`, `total=32844`, with the next `NAME` at
0x80A0.

## Chunk tags observed

| Tag | Payload |
|-----|---------|
| `IRESNAME`, `NAME` | resource path, e.g. `LOCAL:models/210_01_1.mef` |
| `BODY` | the resource; a nested ILFF for models, a LOOP file for textures |
| `PATH` | `;`-separated path list |
| `CSTR` | localised string |
| `IRES` | zero-length marker chunk |
| `OCEMHSEM` | MEF model header (inside a model's nested ILFF) |

## Resource Types

| Archive | Content | Count | Confidence | Method |
|---------|---------|-------|------------|--------|
| `models/levelN.res` | MEF models | 415 in level 1 | ✅ Verified | 830 chunks = 415 NAME/BODY pairs |
| `textures/levelN.res` | LOOP v11 textures | 393 BODY chunks in level 1 | ✅ Verified | chunk walk |
| `lightmaps/lightmaps.res` | lightmap resources | 1,308 BODY chunks | ✅ Verified | chunk walk |
| `common/textures/common.res` | LOOP v11 textures, sub-format 32 | 393 BODY chunks | ✅ Verified | chunk walk |
| `menusystem/*.res` | menu resources | - | ✅ Verified | chunk walk |
| `computer/computer.res` | HUD sprites | - | ✅ Verified | chunk walk |

## Nested archives

`BODY` payloads are themselves ILFF files for models and LOOP files for textures. The
nested ILFF repeats the same 16-byte header (`"ILFF"`, size, sub-format, 0) and then
chunks. Recursion is safe: the nested file's declared size always equals the enclosing
`BODY` `size` field.

## Type-32 texture resources

`common/textures/common.res` is the only sub-format-32 file. Its `BODY` payloads pad the
nested resource to a **32-byte boundary**: the `LOOP` magic sits at
`align32(payload_off)`, not at `payload_off`. Observed padding lengths are 0, 16, 20, 24
and 28 bytes, always zeros. Verified on all 243 `BODY` chunks of `common.res`:
`LOOP_offset == align32(payload_off)` in **243/243** cases. Sub-format-4 archives have
no padding (`LOOP_offset == payload_off`).

## Resource Path Prefixes

| Prefix | Purpose | Example | Confidence | Method |
|--------|---------|---------|------------|--------|
| LOCAL: | game installation directory | `LOCAL:textures/207_01_1.tex` | ✅ Verified | chunk payloads |
| MISSION: | mission-specific files | `MISSION:sounds/` | ✅ Verified | chunk payloads |
| LANGUAGE: | localised text resources | `LANGUAGE:messages.res` | ✅ Verified | chunk payloads |
| COMPUTER: | HUD/computer sprites | `COMPUTER:h_camera.spr` | ✅ Verified | chunk payloads |
| STATUSSCREEN: | status screen resources | `STATUSSCREEN:weapon.spr` | ✅ Verified | chunk payloads |

## Parsing

`reverse/tools/igi_formats.py` implements the container:

```python
import igi_formats as F
info, errors = F.parse_ilff(open("level1.res", "rb").read())
for c in info["chunks"]:
    print(c.id, c.size, c.type, c.total)
```

## Known Issues

1. **Level 14 `.ctr`** - unrelated to ILFF, see 07-terrain.
2. **Sub-format 32 semantics** - the 28-byte descriptor is all zeros in the retail data;
   its runtime meaning is unknown.
3. **Compression/checksums** - none observed in any of the 92 files.

## References

- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
- Parser: `reverse/tools/igi_formats.py`
