# IGI Reverse Engineering

Reverse engineering documentation for **Project IGI** (1999) by Innerloop Studios.

## What's Here

### Documentation (15 sections)
- File format specifications with byte-level details
- Game structure analysis
- Executable reverse engineering
- AI, weapons, terrain, and rendering docs

**Note:** This is static analysis only. Runtime unknowns remain. See STATUS.md for details.

## Documentation

| Section | Topic | Confidence | Key Unknowns |
|---------|-------|------------|--------------|
| 01-overview | Game info, structure | MEDIUM | Difficulty ratings inferred |
| 02-executable | PE analysis, memory | HIGH | Memory layout inferred |
| 03-scripting | QVM bytecode | MEDIUM | Opcodes partially mapped |
| 04-rendering | Graphics pipeline | LOW | Vertex format unknown |
| 05-ai-system | NPC behavior | LOW | Architecture inferred |
| 06-weapons | Weapon data | LOW | All statistics unverified |
| 07-terrain | Heightmap, tiles | MEDIUM | Lightmap format unknown |
| 08-resources | ILFF format | HIGH | Nested archives edge cases |
| 09-audio | Sound system | MEDIUM | Sample rate/bit depth unknown |
| 10-menus | Menu system | MEDIUM | Hierarchy reconstructed |
| 11-task-system | Task types | MEDIUM | Descriptions inferred |
| 12-level-system | Mission structure | MEDIUM | Loading sequence inferred |
| 13-implementation | Implementation notes | - | See STATUS.md |
| 14-lod-system | LOD distances | LOW | Distance thresholds unknown |
| 15-configuration | Config options | HIGH | Runtime values unverified |

**See [INDEX.md](reverse/docs/INDEX.md) for complete reference.**

## Status

| Component | Status |
|-----------|--------|
| File formats | ⚠️ Partially documented |
| Game structure | ⚠️ Partially mapped |
| Executable analysis | ✅ Verified (PE header) |
| AI system | ⚠️ Partially documented |
| Weapons | ⚠️ Partially documented |
| Terrain | ⚠️ Partially documented |
| Resources | ⚠️ Partially documented |
| Audio | ⚠️ Partially documented |
| Menus | ⚠️ Partially documented |
| Tasks | ⚠️ Partially documented |
| Levels | ⚠️ Partially documented |
| LOD | ⚠️ Partially documented |
| Configuration | ⚠️ Partially documented |

## Quick Start

### View Documentation
```bash
ls reverse/docs/
```

## File Formats

| Format | Status | Notes |
|--------|--------|-------|
| ILFF | ⚠️ Header verified | Container format |
| LOOP | ⚠️ Header verified | Texture archive |
| MEF | ❌ Vertex format unknown | Model format |
| BIT | ✅ Entry structure verified | Heightmap |
| CTR | ⚠️ Structure partially known | Tile centers |
| CMD | ❌ Binary encoding unknown | Tile commands |
| LMP | ❌ Pixel format unknown | Lightmaps |
| DAT | ✅ Magic verified | Navigation |
| QVM | ⚠️ Opcodes partially mapped | Bytecode |

## Structure

```
igi/
└── reverse/
    ├── docs/              # Documentation (15 sections)
    │   ├── INDEX.md       # Complete reference
    │   ├── STATUS.md      # What we know vs don't know
    │   └── ...
    └── extracted/         # (gitignored) game files
```

## Legal

- **No game assets included**
- Static analysis only (no runtime verification)
- For educational purposes
- Users must own original game
- See [LICENSE](LICENSE) for details

## Status

Static analysis done, runtime unknowns remain. No plans to continue engine development.

## Credits

Original game: **Project IGI** (1999) by Innerloop Studios

Independent research project for game preservation.
