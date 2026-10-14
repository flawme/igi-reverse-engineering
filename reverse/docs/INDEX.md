# IGI Reverse Engineering - Index

## Legend

| Marker | Meaning |
|--------|---------|
| ✅ | Confirmed by parsing the retail game data (parser run or hex dump) |
| ⚠️ | Partially known - structure documented but details unclear |
| ❌ | Unknown or not analyzed |

## Documentation Structure

```
reverse/docs/
├── 01-overview/          # Game info, structure
├── 02-executable/        # PE analysis, memory
├── 03-scripting/         # QVM bytecode
├── 04-rendering/         # Graphics pipeline
├── 05-ai-system/         # NPC behavior
├── 06-weapons/           # Weapon data
├── 07-terrain/           # Heightmap, tiles
├── 08-resources/         # ILFF format
├── 09-audio/             # Sound system
├── 10-menus/             # Menu system
├── 11-task-system/       # Task types
├── 12-level-system/      # Mission structure
├── 13-implementation/    # Implementation notes
├── 14-lod-system/        # LOD distances
├── 15-configuration/     # Config options
├── 16-verified-formats/  # Byte-level verified specs + evidence
├── STATUS.md             # What we know vs don't know
└── INDEX.md              # This file

reverse/tools/            # 15 tools; see the repo README for the full list
├── igi_formats.py        # ILFF / BIT / HMP / CTR / CMD / LMP / MEF parsers
├── verify_formats.py     # runs every parser over an extracted tree
└── verify_all.py         # end-to-end gate (4 checks)
```

## File Formats

| Format | Extension | Header | Payload | Confidence | Doc |
|--------|-----------|--------|---------|------------|-----|
| ILFF | .res | ✅ Verified | ✅ Verified (92/92 files) | HIGH | 08-resources |
| LOOP v8 | .qvm | ✅ Verified | ✅ Verified | HIGH | 03-scripting |
| LOOP v9 | .tex | ✅ Verified | ✅ Verified | HIGH | 07-terrain |
| LOOP v11 | .res | ✅ Verified | ✅ Verified | HIGH | 08-resources |
| MEF | .res | ✅ Verified | ✅ Vertex layout verified | HIGH | 04-rendering |
| Texture bitmaps | .bit | ✅ Verified | ✅ Verified (14/14) | HIGH | 07-terrain |
| Height maps | .hmp | ✅ Verified | ✅ Verified (6/6) | HIGH | 07-terrain |
| Tile tree | .ctr | ✅ Verified | ✅ Verified (32-byte records) | HIGH | 07-terrain |
| Tile Commands | .cmd | ✅ Verified | ✅ Verified (indices + packed vertices; flag/`A`/`B` semantics inferred) | HIGH | 07-terrain |
| Lightmap | .lmp | ✅ Verified | ✅ Verified (14/14) | HIGH | 07-terrain |
| Navigation | .dat | ✅ Verified | ✅ Verified (routing table `[destination][source] = {next_hop, distance}`) | HIGH | 05-ai-system |
| MTP | .mtp | ✅ Verified | ✅ Verified (`INST` = model_index + texture_count + gtt_index[]) | HIGH | 12-level-system |

## Game Systems

| System | Status | Confidence | Key Unknowns | Doc |
|--------|--------|------------|--------------|-----|
| Rendering | ✅ Model + texture formats verified | HIGH | Pipeline order | 04-rendering |
| AI | ⚠️ Partially documented | MEDIUM | Pathfinding algorithm, grid size | 05-ai-system |
| Weapons | ✅ Parameters + damage model verified | HIGH | Internal damage-path details | 06-weapons |
| Terrain | ✅ Formats verified | HIGH | `cmd_transform[0..7]` selection, terrain-grid coordinate space | 07-terrain |
| Resources | ✅ Container verified | HIGH | Sub-format 32 semantics | 08-resources |
| Scripting | ✅ Bytecode verified | HIGH | Unemitted opcodes, ALU semantics | 03-scripting |
| Audio | ✅ Container + encodings verified | HIGH | - | 09-audio |
| Menus | ⚠️ Partially documented | MEDIUM | Menu hierarchy reconstruction | 10-menus |
| Tasks | ⚠️ Partially documented | MEDIUM | Task descriptions inferred | 11-task-system |
| Levels | ⚠️ Partially documented | MEDIUM | Loading sequence inferred | 12-level-system |
| LOD | ⚠️ Partially documented | MEDIUM | Distance thresholds unverified | 14-lod-system |
| Configuration | ⚠️ Partially documented | HIGH | Runtime testing unverified | 15-configuration |

## Document Summaries

### 01-overview
- Game: Project IGI (1999)
- Developer: Innerloop Studios
- 14 missions + SHARED
- 1,955 files total
- Engine version: 0.0.124 (from string analysis)

### 02-executable
- PE32, MSVC 6.0 (from PE header)
- EntryPoint: 0x004A4F85 (from PE header)
- 4 sections: .text, .rdata, .data, .rsrc
- DirectX 7 (from DLL imports)

### 03-scripting
- QVM header: `"LOOP"` + version 8 + 5 interleaved (offset, size) pairs (997/997 files)
- Sections: symbol offsets, symbol names, string offsets, string constants, code
- 1-byte opcode + fixed-size operand; 49 names from `IGI.exe` @ 0x148394, numbering reversed
- 25 opcodes appear in retail data, all proven; 997/997 files disassemble clean
- 24 events confirmed; the "17 actions" claim is wrong (18 `AIAction_*` / 37 `AIFunction_*` defined, 12 / 30 used)
- ~997 script files (from filesystem)

### 04-rendering
- DirectX 7 (from DLL imports)
- Model vertex: 40 bytes (pos, normal, uv, lightmap uv) for 6,178 models; 32 bytes (no lightmap uv) for 617 - verified by unit-length normals
- Box vertex: 16 bytes; box faces: 8-byte records indexing them
- MEF chunk tags are byte-reversed 4CCs
- Texture texel encoding verified: ARGB1555 (code 2), A8R8G8B8 (code 3), A8R8G8B8 + mips (code 67)

### 05-ai-system
- Behavior tree architecture (inferred, not verified)
- Navigation: precomputed routing table, next hop per `[destination][source]` - verified
- 20-50 NPCs per level (estimated)
- 3 difficulty levels (from configuration)

### 06-weapons
- 24 weapons (directory listing of `pc/weapons/`; the earlier 21-weapon list was guessed and wrong)
- 14 ammo types (directory listing of `pc/ammo/`)
- 50-parameter schema; all values extracted to `reverse/data/weapon_table.tsv`
- Damage formula recovered: `hitzone_multiplier[hitzone] * DamageFactor`; penetration gates continuation

### 07-terrain
- `.bit`: 256-slot descriptor table + `size*size` bits per slot (14/14 exact)
- `.hmp`: 256-slot descriptor table + `(size+1)^2` bytes per slot (6/6 exact)
- `.ctr`: 32-byte tile-tree records with a `cmd_offset` into `.cmd`
- `.cmd`: byte stream addressed by `.ctr` offsets; triangle descriptors and packed vertex entries verified
- `.lmp`: size-prefixed 8-bit greyscale images (14/14 exact)
- `.tex`: LOOP v9, 18 textures in level 1, all 128x128 ARGB1555

### 08-resources
- ILFF container fully verified: 92/92 archives, 90,893 chunks
- Chunk advance is `align4(offset + id_field + 12 + extra + size)`, not the `total` field
- `BODY` payloads are nested ILFF (models) or LOOP (textures)
- Sub-format 32 (one file) pads the nested LOOP to a 32-byte boundary (243/243 verified)
- No compression or checksums in any of the 92 files
- LOOP textures: 8,232 decoded from 118 files, 0 exceptions

### 09-audio
- DirectSound primary (from imports)
- WINMM mixer (from imports)
- ILSF container (custom), not RIFF/WAVE; 16-bit PCM and IMA ADPCM
- AVI cutscene playback (from imports)

### 10-menus
- Screen stack system (reconstructed)
- MenuManager API (from symbols)
- 5 languages (from filesystem)
- Content control (from symbols)

### 11-task-system
- 64 task types (from string analysis)
- Descriptions inferred from names
- Vehicle hierarchy assumed
- Hitzone multipliers verified (17 x 16-byte entries; head 100.0)

### 12-level-system
- 14 levels + `common` documented (from filesystem)
- Loading sequence reconstructed
- Navigation graph decoded: name-hashed records + routing table
- Terrain grid 64x64 (from file size)

### 13-implementation
- Format confidence levels assessed
- Implementation roadmap provided
- Open questions listed
- See STATUS.md for unknowns

### 14-lod-system
- 462 models (from `lod.qvm`)
- 5 LOD levels + cutoff
- Category ranges inferred
- Distance thresholds unverified

### 15-configuration
- Graphics/sound/input settings (from symbols)
- Key bindings documented (from config)
- Player profiles (from symbols)
- Difficulty levels (from config)

## Known Issues

1. **`.cmd` triangle flag / vertex `A`/`B` fields** - packing proven; the flag high nibble (material index) and `A`/`B` semantics are inferred
2. **`DNER` / `OCEMHSEM` leftover fields** - `+0x7C`/`+0x7E`/DNER `+0x18` consumed; mesh `+0x0C`..`+0x1C` and render `+0x1A`/`+0x1E` consumers not located
3. **`cmd_transform[0..7]`** - the unused/present rule is proven; what `0..7` selects is not
4. **QVM leftovers** - unemitted opcodes resolved; the reversed numbering and the `PUSHA` intent remain open
5. **Weapon parameters** - all 24 x 50 values extracted and the damage formula recovered; some internal damage-path details remain
6. **NPC statistics** - health, damage, perception values are guesses
7. **Terrain-grid / level-script coordinate space** - not in the 1/4096 m unit; its scale is not determined

## Legal

- No game assets included
- Format analysis performed against a legally owned retail copy
- For educational purposes
- Users must own original game

## Status

Container, terrain, model, texture, bytecode, audio, font, navigation, manifest and
animation formats verified against the retail data, every format anchored to its loader
in `IGI.exe`, the weapon damage formula recovered, and the world scale proven
(4096 units = 1 m). The remaining open items are listed above. No plans to continue
engine development.

## References

- Original game: Project IGI (1999)
- Developer: Innerloop Studios
- Publisher: Eidos Interactive
- Analysis tools: `reverse/tools/` (`igi_formats.py`, `loop.py`, `qvm.py`,
  `verify_formats.py`, `verify_all.py`, `adversarial_checks.py`, `exe_dis.py`)
- Byte-level evidence: [16-verified-formats](16-verified-formats/README.md)
