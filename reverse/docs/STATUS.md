# IGI Reverse Engineering - Status

## Legend

| Marker | Meaning |
|--------|---------|
| ✅ | Confirmed by parsing the retail game data (parser run or hex dump) |
| ⚠️ | Partially known - structure documented but details unclear |
| ❌ | Unknown or not analyzed |

**Verification harness:** `python3 reverse/tools/verify_formats.py /path/to/extracted/pc`
runs every parser over the whole extracted game tree and prints the pass counts quoted
below. Byte-level tables: [16-verified-formats](16-verified-formats/README.md).

## File Formats

| Format | Extension | Header | Payload | Confidence | Method |
|--------|-----------|--------|---------|------------|--------|
| ILFF | .res | ✅ Verified | ✅ Verified | HIGH | 92/92 files parse cleanly, 90,893 chunks |
| LOOP v8 | .qvm | ✅ Verified | ✅ Verified | HIGH | 997/997 files disassemble clean, 25 opcodes proven |
| LOOP v9 | .tex | ✅ Verified | ✅ Verified | HIGH | 8,232 textures decoded, 0 exceptions |
| LOOP v11 | .res | ✅ Verified | ✅ Verified | HIGH | 7,199/7,199 size invariants |
| MEF | .res | ✅ Verified | ✅ Vertex layout verified | HIGH | 6,795 models, 100% unit normals at the correct stride |
| Texture bitmaps | .bit | ✅ Verified | ✅ Verified | HIGH | 14/14 consume file exactly |
| Height maps | .hmp | ✅ Verified | ✅ Verified | HIGH | 6/6 consume file exactly |
| Tile tree | .ctr | ✅ Verified | ✅ Verified | HIGH | 32-byte records, 14/14 aligned |
| Tile commands | .cmd | ✅ Verified | ✅ Verified | HIGH | 13/14 levels 100% offset-valid; loader `fcn.004c60a0` |
| Lightmap | .lmp | ✅ Verified | ✅ Verified | HIGH | 14/14 consume file exactly |
| Navigation | .dat | ✅ Verified | ✅ Verified | HIGH | routing table `[destination][source] = {next_hop, distance}`; loader `fcn.004f9d30` |
| MTP | .mtp | ✅ Verified | ✅ Verified | HIGH | `INST` = model_index + texture_count + gtt_index[]; parser `fcn.004d1ee0` |
| ILSF | .wav, .res | ✅ Verified | ✅ Verified | HIGH | 759/759 payloads, loader `fcn.00495e00` |
| IFF | .iff | ✅ Verified | ✅ Verified | HIGH | 6/6 files; loader `fcn.004d65f0`; playback = SLERP sampler `fcn.004d4fd0` |
| FNT | .fnt | ✅ Verified | ✅ Verified | HIGH | 154/154 glyphs; `TRAN` char->glyph map verified code-side |

## Terrain

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| `.bit` layout | 256 x 12-byte descriptors + `size*size` bits per slot | ✅ | 14/14 exact |
| `.hmp` layout | 256 x 12-byte descriptors + `(size+1)^2` bytes per slot | ✅ | 6/6 exact |
| `.ctr` record | 32 bytes: `int16 children[8]; int8 transform[8]; uint8 mask; uint8 pad[3]; uint32 cmd_offset` | ✅ | 14/14 aligned |
| `.cmd` record | variable-length: 8-byte header + `triangle[n][4]` + `vertex[npv+ncv][4]` | ✅ | records tile every file exactly, no trailer |
| `.cmd` triangle | 3 x uint8 index + 1 flag byte | ✅ | 100% on all 13 levels; the packed 10:10:10 rival scores 0% |
| `.cmd` vertex | 4 bytes packed: `(Y<<27) | (X<<21) | (C<<15) | (B<<6) | A`; bits 3-5/10-14/20/26 always zero | ✅ | 840,866 entries, 0 violations; root tile exactly `{0,12,24}` |
| `.cmd` addressing | byte stream addressed by `.ctr` `cmd_offset`, **not** a linear array | ✅ | linear read fails on 61,036/63,587 windows; fixup loop `0x4c6437` |
| `.lmp` layout | `uint32 size` + `size*size` 8-bit greyscale texels | ✅ | 14/14 exact |
| Lightmap sizes | 16, 32, 64, 128 (powers of two) | ✅ | level 1 histogram |
| Level 14 `.ctr` | 44-byte records (`486,464 = 11,056 x 44`) | ✅ | constant 8-byte marker at +0x24, gaps all multiples of 44 |
| `.cmd` triangle flag bit | high nibble inferred to be a material index (14/15/4); winding/split/order rejected | ⚠️ | `CreateTerrainMaterial` `0x4c64d0` builds a 900-byte-stride table |
| `cmd_transform[8]` | `0xFF` = unused, `0..7` = transform index; what it selects unknown | ⚠️ | rule holds 149,243/149,256 records (13 exceptions = zero-filled roots) |
| World scale | **4096 units = 1 m** | ✅ | the `%.2fm` print multiplies by 1/4096 (`0x5334b0`); gravity 44.6009 at `0x53346c` = 9.8 x 4096 / 900 (30 ticks/s). A second handler (`fcn.004084b0`) uses 84.7417 at `0x5333f0` (18.62 m/s^2, undamped) - which state uses which is open |

## Rendering

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| API | Direct3D 7 | ✅ | DLL import analysis |
| Model vertex | 40 bytes (pos/normal/uv/lightmap_uv) for 6,178 models; 32 bytes (no lightmap uv) for 617 | ✅ | 100% unit normals at the correct stride, 0 ambiguous |
| Box vertex | 16 bytes: pos(12) + 0 | ✅ | 16 vertices form a box |
| Box faces (`ECFC`) | 8 bytes: `uint16 i0, i1, i2, material` into `XTVC` | ✅ | indices verified in range |
| Render triangles (`DNER`) | batch header + `uint16` list into `XTRV` | ✅ | indices verified in range |
| MEF chunk tags | byte-reversed 4CC (`XTRV`→`VRTX`, `ECFC`→`CFCE`, ...) | ✅ | 6,795 models |
| Texture pixel format | code 2 = ARGB1555, code 3 = A8R8G8B8, code 67 = A8R8G8B8 + mips | ✅ | 8,232 textures decoded, 0 exceptions |
| Texture mips | only in v11 format 67, level 0 first, halving | ✅ | mip chains exact |
| `DNER`/`OCEMHSEM` leftover fields | `+0x7C` = XTVM count, `+0x7E` = ATTA count, DNER `+0x18` = deferred-render flag; mesh `+0x0C`..`+0x1C` and render `+0x1A`/`+0x1E` consumers not located | ⚠️ | getters `fcn.004cf9b0`/`fcn.004cf9a0`; `0x49e578` |
| Terrain vertex format | generated at runtime, nothing on disk | ❌ | - |
| Pipeline order | not verified | ❌ | - |
| Triangle count / draw calls | not measured | ❌ | - |

## Resources

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| ILFF header | 16 bytes (`"ILFF"`, size, sub-format, 0) + a 4-byte format id at `+0x10` (`"IRES"`/`"HSEM"`); the loader reads the 20 bytes as one struct | ✅ | 92/92 files; loader `fcn.004b5e30` |
| Chunk header | tag (4 or 8 bytes, 4-aligned) + size + type + total | ✅ | 90,893 chunks |
| Chunk advance | `align4(offset + id_field + 12 + extra + size)` | ✅ | every parse consumes the declared size |
| `total` field | the advance for every 4-byte-tag chunk (90,709/90,709, incl. type-32); 0 in 93 chunks (92 last + the zero-size `IRES` marker); 4 short only for the 91 eight-byte-tag first chunks | ✅ | full-tree measurement |
| Sub-format 32 | nested resource padded to a 32-byte boundary | ✅ | 243/243 chunks of `common.res` |
| Nested archives | `BODY` payload is a nested ILFF (models) or LOOP (textures) | ✅ | 6,795 models parsed |
| Compression/checksums | none observed | ✅ | 92 files |

## Scripting

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| QVM header | `"LOOP"` + version 8 + 5 interleaved (offset,size) pairs | ✅ | 997/997 files |
| QVM sections | 0 = symbol offsets, 1 = symbol names, 2 = string offsets, 3 = string constants, 4 = code | ✅ | 997/997 files |
| Instruction encoding | 1-byte opcode + fixed-size operand | ✅ | exe disassembler handlers at VA 0x4c0f70 |
| Opcode table | 49 names from `IGI.exe` @ 0x148394, numbering reversed | ✅ | 3 independent confirmations |
| Opcodes in retail data | 25, all proven | ✅ | 997 files disassembled clean |
| Unemitted opcodes | all 5 resolved: PUSHA 4 bytes, PUSHS/PUSHI inline strings, PUSHM 0, JSR 0 | ✅ | interpreter table at VA 0x4bd2c0 |
| ALU semantics | signed integer ops, x87 float, operand order `a OP b` proven | ✅ | handler at VA 0x4bdad0 |
| Reserved header words | 0x34 = value-stack size, 0x38 = type-stack size (defaults 0x800/0x100) | ✅ | loader at VA 0x4bd0b0 |
| Branch targets | 41,716 branches, 0 bad targets | ✅ | structural validation |
| CALL argument tables | 34,220 calls, 0 bad entries | ✅ | structural validation |
| Events | 24 distinct `AIEVENT_*` | ✅ | `IGI.exe` strings |
| Actions / functions | 18 `AIAction_*` / 37 `AIFunction_*` defined; 12 / 30 used by retail scripts | ✅ | `IGI.exe` strings + symbol tables |
| 4-byte PUSH*I* targets | resolved: the same string/symbol lookups at 4-byte width; unused in retail data | ✅ | `0x4be96b`/`0x4be921`/`0x4be946` |

## Audio

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Primary API | DirectSound | ✅ | DLL import analysis |
| Mixing API | WINMM | ✅ | DLL import analysis |
| Cutscene API | AVIFIL32.dll | ✅ | DLL import analysis |
| Sample container | **ILSF**, not RIFF/WAVE | ✅ | 759/759 payloads + loader at `IGI.exe` VA 0x495E36 |
| ILSF header | 20 bytes: magic, version, 16 bps, channels, flags, rate, frame count | ✅ | 759/759 |
| Encodings | 16-bit PCM (versions 0/1) and 4-bit IMA ADPCM (versions 2/3) | ✅ | 341 / 418 payloads |
| Sample rates | 11025 / 22050 / 44100 Hz | ✅ | 759/759 |
| Decoded output | playable WAVs incl. `game_music.wav` (12.8 MB) | ✅ | `reverse/tools/misc.py` |
| ILSF flags / version bitfield / trailing byte | flags never read (authoring metadata); version is a bitfield (bit 0 = in `.res`, bit 1 = ADPCM); trailing byte is zero pad | ✅ | loader `fcn.00495e00`, switch table `0x4960d0`, nibble pump `0x496193` |

## Weapons

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Weapon count | 24 directories in `pc/weapons/` | ✅ | filesystem |
| Ammo types | 14 directories in `pc/ammo/` | ✅ | filesystem |
| Parameter schema | 50 named parameters | ✅ | `weaponconfig.qvm` declaration |
| Parameter values | all 24 weapons, all 50 fields | ✅ | `reverse/data/weapon_table.tsv` |
| Damage model | `hitzone_multiplier[hitzone] * DamageFactor`, accumulated per hitzone; penetration gates continuation only (damage is applied first); the **player** path additionally scales by the profile difficulty (0.75 / 1.0 / 1.25) | ✅ | `fcn.0045fcd0` `0x45fd26`-`0x45fd32`; `0x47c195`; difficulty switch `0x412524`-`0x412552` |
| Hitzone multipliers | 17 x 16-byte entries; `0.5/0.75/1.0` triples, `100.0` at indices 15/16 (head) | ✅ | AI table `0x53f9d0`, player table `0x538a00` |

## Task System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Task type count | 64 | ⚠️ | string/symbol analysis |
| Vehicle / weapon / interactive / system task types | 15 / 15 / 13 / 15 | ⚠️ | string analysis |

## Level System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Missions | 14 levels + `common`, under `missions/location0/` | ✅ | filesystem |
| Level directory layout | `{ai,anims,graphs,lightmaps,models,sounds,terrain,textures}` + `levelN.dat`, `levelN.mtp`, `mission.qvm`, `objects.qvm` | ✅ | filesystem |
| Loading sequence | not verified | ❌ | - |
| Navigation graph nodes | decoded: name-hashed records (`nNodeID`, `tNodePosition`, `vNodeRadius`, ...); grid is a routing table `[destination][source] = {next_hop, distance}` | ✅ | loader `fcn.004f9d30`; 66,408 column-adjacent cells |

## LOD System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Model count | 462 | ✅ | `lod.qvm` decoded |
| LOD levels | 4 distances + cutoff, per model | ✅ | `lod.qvm` decoded |
| Full table | `reverse/data/lod_table.tsv` | ✅ | `qvmdec.py` |
| Category names | prefix groups are real, semantic labels are not proven | ⚠️ | - |
| LOD 4 semantics | billboard vs low-poly not established | ❌ | - |

## Configuration

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| `config.qvm` statements | 43 | ✅ | `qvmdec.py` |
| `GOInRemap` bindings | 30 shipped defaults | ✅ | `reverse/data/config_options.tsv` |
| Display default | `GOGfxDisp(640, 480, 32)` | ✅ | `config.qvm` |
| Difficulty default | `GD_2` | ✅ | `config.qvm` |
| Difficulty semantics | what each level changes is not in the file | ❌ | - |

## Menu System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Menu screens | 6+ documented | ⚠️ | QVM script analysis |
| Languages | 5 (EN, FR, DE, IT, ES) | ✅ | filesystem |
| MenuManager API | 9 functions | ⚠️ | symbol analysis |
| Menu hierarchy | reconstructed | ❌ | - |

## What Remains Unknown

Resolved by the IGI.exe disassembly passes (2026-10-14): the nav `.dat` cell field
(next-hop node ID), `.mtp` `INST` semantics, ILSF flags/version/trailing byte, QVM
leftovers (PUSHA/BRK/native call convention), LOOP leftovers (v9 `0x10`, v9 descriptor
`+0x0E`), the `.fnt` `TRAN` map and `FONTFNTH` fields, the weapon damage formula and
the player difficulty scaling (0.75 / 1.0 / 1.25), `.iff` playback (bone objects,
per-frame update, SLERP sampler, selection path), and world scale (4096 units = 1 m).

### High Priority
1. `OCEMHSEM` / `DNER` leftover fields - `+0x7C` (XTVM count) and `+0x7E` (ATTA count)
   are now consumed and proven, and DNER `+0x18` is a deferred-render flag; the
   `+0x0C`/`+0x10`/`+0x14`/`+0x18`/`+0x1C` (mesh) and `+0x1A`/`+0x1E` (render) consumers
   were not located
2. `.cmd` triangle flag bit (high nibble inferred = material index) and the `A`/`B`
   fields of the vertex entry
3. `cmd_transform[0..7]` semantics (the unused/present rule is proven)

### Medium Priority
4. `TAMC` / `PMTL` semantics (record shapes decoded; HPSC is consumed as 24-byte
   records; no TAMC consumer and no flag-3 `D3DR+0x18` reader located)
5. `.fnt` glyph record `+0x24` semantic and the remaining `TRAN` bytes
6. Which gravity handler runs in which player state - two handlers drive the same
   velocity field (`+0x66C`): the damped one at `0x40dc41` (44.6009 = 9.8 m/s^2) and
   the undamped air-control one at `fcn.004084b0` (84.7417 = 18.62 m/s^2); both are
   reached through runtime-filled dispatch tables

### Low Priority
7. Animation format - no `.anm` files ship in the retail tree; the `anims/`
   directories are empty
8. Network protocol - no evidence found
9. Save format - no evidence found
10. Performance metrics - not measured

## Methodology Notes

- **Parser testing:** every format claim is backed by a parser that consumes the real
  file exactly, or by an invariant that a wrong interpretation cannot satisfy (the
  unit-length-normal test for the MEF vertex stride, the `vertex_offset ==
  num_triangle * 4` test for `.cmd`).
- **Hex dump analysis:** used for header layouts.
- **Symbol analysis:** used for API function identification.
- **String analysis:** used for event/action names, task types, error messages.
- **DLL import analysis:** used for the technology stack.

## Limitations

- No runtime analysis was performed (no debugger attached).
- No source code is available.
- Gameplay numbers: the damage formula, hitzone multipliers and the world scale (4096 units = 1 m) are recovered from `IGI.exe`; other timing and behavioural numbers remain estimates.
- Behavioural models (AI, physics) are inferred from standard game patterns.

## Last Updated

- Date: 2026-10-14
- Version: 7.3
- Status: container, terrain, model, texture, bytecode, audio, font, navigation,
  manifest and animation formats verified against the retail data, every format anchored
  to its loader in `IGI.exe`, the weapon damage formula recovered, and the world scale
  proven (4096 units = 1 m). Remaining open items are listed above.
- 7.2: reconciled stale rows with the disassembly pass (weapon damage and hitzones,
  ILSF flags/version, navigation nodes, `PUSH*I*`, `DNER`/`OCEMHSEM` leftovers).
- 7.3: cross-check against the `project-igi-research-data` claims - added the player
  difficulty scaling, corrected the ILFF header/`total`-field description, documented
  the second gravity handler.
