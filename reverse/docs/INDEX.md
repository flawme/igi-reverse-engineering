# IGI Reverse Engineering - Index

## Legend

| Marker | Meaning |
|--------|---------|
| ✅ | Confirmed via hex dump or parser testing |
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
├── STATUS.md             # What we know vs don't know
└── INDEX.md              # This file
```

## File Formats

| Format | Extension | Header | Payload | Confidence | Doc |
|--------|-----------|--------|---------|------------|-----|
| ILFF | .res | ✅ Verified | ⚠️ Edge cases unknown | HIGH | 08-resources |
| LOOP v8 | .qvm | ✅ Verified | ⚠️ Bytecode partially mapped | HIGH | 03-scripting |
| LOOP v9 | .tex | ✅ Verified | ⚠️ Pixel format unclear | HIGH | 07-terrain |
| LOOP v11 | .res | ✅ Verified | ⚠️ Less tested | MEDIUM | 08-resources |
| MEF | .res | ⚠️ Nested structure | ❌ Vertex layout unknown | LOW | 08-resources |
| Heightmap | .bit | ✅ Verified | ⚠️ Flags inferred | HIGH | 07-terrain |
| Tile Centers | .ctr | ⚠️ Structure known | ⚠️ Flags inferred | MEDIUM | 07-terrain |
| Tile Commands | .cmd | ❌ Unknown | ❌ Unknown | LOW | 07-terrain |
| Lightmap | .lmp | ❌ Unknown | ❌ Unknown | LOW | 07-terrain |
| Navigation | .dat | ✅ Magic verified | ⚠️ Edge format partial | MEDIUM | 05-ai-system |
| QVM | .qvm | ✅ Verified | ⚠️ Opcodes partial | HIGH | 03-scripting |

## Game Systems

| System | Status | Confidence | Key Unknowns | Doc |
|--------|--------|------------|--------------|-----|
| Rendering | ⚠️ Partially documented | MEDIUM | Vertex format, pipeline order | 04-rendering |
| AI | ⚠️ Partially documented | MEDIUM | Pathfinding algorithm, grid size | 05-ai-system |
| Weapons | ⚠️ Partially documented | LOW | Damage values, reload times | 06-weapons |
| Terrain | ⚠️ Partially documented | MEDIUM | Flag meanings, command encoding | 07-terrain |
| Resources | ⚠️ Partially documented | HIGH | Nested archive edge cases | 08-resources |
| Scripting | ⚠️ Partially documented | MEDIUM | Opcode table incomplete | 03-scripting |
| Audio | ⚠️ Partially documented | MEDIUM | Sample rate, bit depth | 09-audio |
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
- ~1,972 files total
- Engine version: 0.0.124 (from string analysis)

### 02-executable
- PE32, MSVC 6.0 (from PE header)
- EntryPoint: 0x004A4F85 (from PE header)
- 4 sections: .text, .rdata, .data, .rsrc
- DirectX 7 (from DLL imports)

### 03-scripting
- QVM bytecode VM (structure verified, opcodes partial)
- 22 events, 17 actions (from string analysis)
- Event-driven architecture (inferred)
- ~997 script files (from filesystem)

### 04-rendering
- DirectX 7 (from DLL imports)
- Terrain + models + particles + HUD (inferred from file types)
- Pipeline order reconstructed, not verified
- Triangle count unknown (estimated ~150K)

### 05-ai-system
- Behavior tree architecture (inferred, not verified)
- A* pathfinding (assumed, not confirmed)
- 20-50 NPCs per level (estimated)
- 3 difficulty levels (from configuration)

### 06-weapons
- 21 weapons (from QVM analysis)
- 8 categories (from QVM analysis)
- 5 ammo types (from QVM analysis)
- Damage values, reload times unverified

### 07-terrain
- Heightmap: 16 bytes/entry (verified via hex dump)
- Tile centers: 52 bytes/entry (partially verified)
- Tile commands: binary encoding unknown
- Lightmap: pixel format unknown

### 08-resources
- ILFF container format (header verified)
- IRESNAME + BODY pairs (structure known)
- Nested archives for models (edge cases untested)
- No compression/checksums (verified)

### 09-audio
- DirectSound primary (from imports)
- WINMM mixer (from imports)
- RIFF/WAV format (standard assumption)
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
- Hit multipliers unverified

### 12-level-system
- 9 missions documented (from filesystem)
- Loading sequence reconstructed
- Navigation graph structure partial
- Terrain grid 64x64 (from file size)

### 13-implementation
- Format confidence levels assessed
- Implementation roadmap provided
- Open questions listed
- See STATUS.md for unknowns

### 14-lod-system
- ~400 models (from LOD.QVM)
- 5 LOD levels + cutoff
- Category ranges inferred
- Distance thresholds unverified

### 15-configuration
- Graphics/sound/input settings (from symbols)
- Key bindings documented (from config)
- Player profiles (from symbols)
- Difficulty levels (from config)

## Known Issues

1. **MEF vertex format** - Chunk IDs known, vertex layout completely unknown
2. **Texture UV mapping** - No UV coordinates documented
3. **Lightmap format** - Pixel format, UV mapping, blending all unknown
4. **QVM opcodes** - Only partially mapped, many opcodes unidentified
5. **Weapon parameters** - Damage, timing, spread values are estimates
6. **NPC statistics** - Health, damage, perception values are guesses

## Legal

- No game assets included
- Static analysis only (no runtime verification)
- For educational purposes
- Users must own original game

## Status

Static analysis done, runtime unknowns remain. No plans to continue engine development.

## References

- Original game: Project IGI (1999)
- Developer: Innerloop Studios
- Publisher: Eidos Interactive
- Analysis tools: Hex dump, symbol analysis, string analysis
