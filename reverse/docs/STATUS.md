# IGI Reverse Engineering - Status

## Legend

| Marker | Meaning |
|--------|---------|
| ✅ | Confirmed via hex dump or parser testing |
| ⚠️ | Partially known - structure documented but details unclear |
| ❌ | Unknown or not analyzed |

## File Formats

| Format | Extension | Header | Payload | Confidence | Method |
|--------|-----------|--------|---------|------------|--------|
| ILFF | .res | ✅ Verified | ⚠️ Nested archives edge cases unknown | HIGH | Hex dump + parser testing |
| LOOP v8 | .qvm | ✅ Verified | ⚠️ Bytecode internals partially mapped | HIGH | Hex dump + string analysis |
| LOOP v9 | .tex | ✅ Verified | ⚠️ Texture pixel data format unclear | HIGH | Hex dump + parser testing |
| LOOP v11 | .res | ✅ Verified | ⚠️ Similar to v9, less tested | MEDIUM | Hex dump |
| MEF | .res | ⚠️ Nested ILFF structure known | ❌ Vertex layout unknown | LOW | Hex dump only |
| Heightmap | .bit | ✅ Verified (16 bytes/entry) | ⚠️ Flag meanings inferred | HIGH | Hex dump + file size analysis |
| Tile Centers | .ctr | ⚠️ 52 bytes/entry structure | ⚠️ Flag meanings inferred | MEDIUM | Hex dump |
| Tile Commands | .cmd | ❌ Binary encoding unknown | ❌ Command types guessed | LOW | File size only |
| Lightmap | .lmp | ❌ Pixel format unknown | ❌ UV mapping unknown | LOW | File size only |
| Navigation | .dat | ✅ Magic 0xFFEEDDCC verified | ⚠️ Edge list format partially known | MEDIUM | Hex dump |

### MEF Chunk Types (Partial)

| Chunk ID | Likely Meaning | Confidence | Method |
|----------|---------------|------------|--------|
| OCEMHSEM | Mesh header? | LOW | String analysis (reversed) |
| XTVM | Vertex mapping? (MTVX reversed) | LOW | String analysis |
| TROP | Triangle properties? (PORT reversed) | LOW | String analysis |
| XVTP | Vertex positions? | LOW | String analysis |
| CFTP | Face/texture pairs? | LOW | String analysis |
| D3DR8 | Direct3D render state | HIGH | Known D3D7 constant |
| DNER | Normal data? (REND reversed) | LOW | String analysis |

**Open questions:** Vertex stride, attribute offsets, index format, vertex count per model.

## Game Structure

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Missions | 14 + SHARED | HIGH | Filesystem listing |
| Total files | ~1,972 | HIGH | Filesystem listing |
| QVM scripts | ~997 | HIGH | Filesystem listing |
| RES archives | ~92 | HIGH | Filesystem listing |
| TEX packages | ~26 | HIGH | Filesystem listing |
| Engine version | 0.0.124 | MEDIUM | String analysis in binary |

## Executable Analysis

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Format | PE32 (i386) | ✅ Verified | PE header parsing |
| Compiler | MSVC 6.0 | ✅ Verified | PE header parsing |
| EntryPoint | 0x004A4F85 | ✅ Verified | PE header parsing |
| Sections | 4 (.text, .rdata, .data, .rsrc) | ✅ Verified | PE header parsing |
| DirectX version | 7 | HIGH | DLL import analysis |
| Timestamp | Thu Nov 30 00:00:50 2000 | MEDIUM | PE header (can be spoofed) |

## AI System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Events | 22 | MEDIUM | String/symbol analysis |
| Actions | 17 | MEDIUM | String/symbol analysis |
| NPC types | 4+ documented | MEDIUM | QVM script analysis |
| Difficulty levels | 3 (Easy, Normal, Hard) | HIGH | Configuration analysis |
| Pathfinding algorithm | Unknown (A* assumed) | LOW | Standard game convention |
| Grid size | Unknown (512x512 assumed) | LOW | Standard game convention |

## Weapons

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Weapon count | 21 | MEDIUM | QVM script analysis |
| Categories | 8 | MEDIUM | QVM script analysis |
| Ammo types | 5 | MEDIUM | QVM script analysis |
| Specific damage values | Unknown | LOW | Not verified at runtime |
| Reload times | Unknown | LOW | Not verified at runtime |
| Spread values | Unknown | LOW | Not verified at runtime |

## Rendering

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| API | DirectX 7 | HIGH | DLL import analysis |
| Pipeline order | Unknown | LOW | Reconstructed from standard practices |
| Triangle count | Unknown (~150K estimated) | LOW | Estimate, not measured |
| Draw calls | Unknown (~100-200 estimated) | LOW | Estimate, not measured |
| Vertex format | Unknown | ❌ | Not extracted |
| Index format | Unknown (u16 or u32) | ❌ | Not extracted |

## Task System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Task type count | 64 | MEDIUM | String/symbol analysis |
| Vehicle task types | 15 | MEDIUM | String analysis |
| Weapon task types | 15 | MEDIUM | String analysis |
| Interactive task types | 13 | MEDIUM | String analysis |
| System task types | 15 | MEDIUM | String analysis |
| Hit damage multipliers | Unknown (2x head, 1x body assumed) | LOW | Standard FPS convention |

## Level System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Documented levels | 9 + shared | HIGH | Filesystem listing |
| Loading sequence | 10 steps (reconstructed) | LOW | Inferred from file structure |
| Navigation graph nodes | ~100 per level | LOW | Estimate from file size |
| Terrain grid | 64x64 tiles | MEDIUM | File size analysis |
| Lightmap resolution | Unknown | ❌ | Not extracted |

## LOD System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Model count | ~400 | MEDIUM | LOD.QVM analysis |
| LOD levels | 5 + cutoff | MEDIUM | LOD.QVM analysis |
| Category ranges | 8 categories | LOW | Inferred from ID patterns |
| Distance thresholds | Unknown per model | LOW | Not verified at runtime |

## Configuration

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Graphics settings | 14 functions | HIGH | Symbol analysis |
| Sound settings | 14 functions | HIGH | Symbol analysis |
| Input settings | 6 functions | HIGH | Symbol analysis |
| Key bindings | 20+ documented | HIGH | Configuration file analysis |
| Default difficulty | GD_2 (Normal) | HIGH | Configuration analysis |

## Audio System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Primary API | DirectSound | HIGH | DLL import analysis |
| Mixing API | WINMM | HIGH | DLL import analysis |
| Format | RIFF/WAV (PCM assumed) | MEDIUM | Standard Windows audio |
| Cutscene API | AVIFIL32.dll | HIGH | DLL import analysis |
| Sample rate | Unknown | ❌ | Not extracted |
| Bit depth | Unknown | ❌ | Not extracted |

## Menu System

| Item | Value | Confidence | Method |
|------|-------|------------|--------|
| Menu screens | 6+ documented | MEDIUM | QVM script analysis |
| Languages | 5 (EN, FR, DE, IT, ES) | HIGH | Filesystem listing |
| MenuManager API | 9 functions | HIGH | Symbol analysis |
| Menu hierarchy | Reconstructed | LOW | Inferred from QVM scripts |

## What Remains Unknown

### High Priority (would significantly improve documentation)
1. MEF vertex layout (stride, offsets, index format)
2. Texture UV mapping coordinates
3. Lightmap pixel format and UV mapping
4. QVM opcode table (only partially mapped)
5. Actual weapon damage values (not inferred)

### Medium Priority
6. Sound format details (sample rate, bit depth)
7. Navigation graph edge format
8. Tile command encoding
9. Level loading order (actual vs inferred)

### Low Priority
10. Animation format (.ANM files)
11. Network protocol (if any)
12. Save system format
13. Performance metrics (actual measured values)

## Methodology Notes

- **Hex dump analysis:** Used for file format reverse engineering (ILFF, LOOP, heightmap)
- **Symbol analysis:** Used for API function identification (MenuManager, Config, Game)
- **String analysis:** Used for event/action names, task types, error messages
- **Filesystem listing:** Used for file counts, directory structure
- **DLL import analysis:** Used for technology stack identification
- **Standard conventions:** Used for guessing where no direct evidence exists (not reliable)

## Limitations

- No runtime analysis was performed (no debugger attached)
- No source code is available
- Most numeric values (damage, timing, distances) are unverified estimates
- Behavioral models (AI, physics) are inferred from standard game patterns
- The documentation reflects static analysis only; runtime behavior may differ

## Last Updated

- Date: 2026-06-26
- Version: 5.0
- Status: Static analysis done, runtime unknowns remain.
