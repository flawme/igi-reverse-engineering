# 12 - Level/Mission System

## Level Structure

```
PC/MISSIONS/LOCATI~1/LEVEL{n}/
├── AI/           - AI script files (*.qvm)
├── ANIMS/        - Animation files
├── GRAPHS/       - Navigation graphs (graph*.dat)
├── LIGHTMAPS/    - Lightmap resources (*.res)
├── MODELS/       - 3D model resources (*.res)
├── SOUNDS/       - Level-specific audio (*.wav)
├── TERRAIN/      - Terrain data files
└── TEXTURES/     - Texture resources (*.res)
```

**Confidence:** HIGH - From filesystem listing.

## Level IDs (Observed)

| Level | Name | Theme | Confidence | Method |
|-------|------|-------|------------|--------|
| 1 | Training | Basic training mission | MEDIUM | Filename analysis |
| 2 | Traintown | Train station infiltration | MEDIUM | Filename analysis |
| 3 | River | River crossing | MEDIUM | Filename analysis |
| 4 | Sam Base | SAM base assault | MEDIUM | Filename analysis |
| 5 | Radar | Radar facility | MEDIUM | Filename analysis |
| 6 | Church | Church/castle infiltration | MEDIUM | Filename analysis |
| 7 | Airbase | Airbase assault | MEDIUM | Filename analysis |
| 8 | Chemical | Chemical plant | MEDIUM | Filename analysis |
| 9 | Nuclear | Nuclear facility | MEDIUM | Filename analysis |

**Note:** Level names and themes are inferred from filenames, not confirmed from game content.

## Level Resources (Observed)

### Per-Level Files

| Type | Pattern | Example | Confidence | Method |
|------|---------|---------|------------|--------|
| Terrain | terrain/*.{bit,cmd,ctr,lmp,tex,qvm} | terrain1.bit | HIGH | File listing |
| Textures | textures/LEVEL{n}.RES | level1_tex.res | HIGH | File listing |
| Models | models/LEVEL{n}.RES | level1_models.res | HIGH | File listing |
| Lightmaps | lightmaps/LIGHTM~1.RES | lightmap1.res | HIGH | File listing |
| AI Scripts | AI/*.QVM | guard.qvm, patrol.qvm | HIGH | File listing |
| Navigation | graphs/graph*.DAT | graph1.dat | HIGH | File listing |
| Sounds | sounds/*.WAV | M1_AMB~1.WAV | HIGH | File listing |

### Shared Resources (Observed)

```
PC/COMMON/
├── AI/           - Common AI scripts
├── ANIMS/        - Common animations
├── SOUNDS/       - Common sounds
├── SPRITES/      - Common sprites
├── TEXTURES/     - Common textures
├── COMMON.DAT    - Material definitions
└── COMMON.MTP    - Material properties
```

**Confidence:** HIGH - From filesystem listing.

## Path Prefixes (From strings)

| Prefix | Purpose | Example | Confidence | Method |
|--------|---------|---------|------------|--------|
| LOCAL: | Game install dir | LOCAL:textures/000_01_1.tex | HIGH | String analysis |
| MISSION: | Mission-specific | MISSION:sounds/ | HIGH | String analysis |
| LANGUAGE: | Localized text | LANGUAGE:messages.res | HIGH | String analysis |
| COMPUTER: | HUD sprites | COMPUTER:h_camera.spr | HIGH | String analysis |
| STATUSSCREEN: | Status screen | STATUSSCREEN:weapon.spr | HIGH | String analysis |

## Flow Events (From strings)

| Event | Description | Confidence | Method |
|-------|-------------|------------|--------|
| FLOW_EVENT_RESTART_GAME | Restart | MEDIUM | String analysis |
| FLOW_EVENT_GAME | Game | MEDIUM | String analysis |
| FLOW_EVENT_MAINMENU | Main menu | MEDIUM | String analysis |
| FLOW_EVENT_INTRO | Intro | MEDIUM | String analysis |
| FLOW_EVENT_QUIT | Quit | MEDIUM | String analysis |

## Level Loading Sequence (Reconstructed)

**Confidence:** LOW - This sequence is inferred from file structure, not verified from source code.

1. Load mission.qsc → compile to mission.qvm
2. Load terrain files (BIT, CMD, CTR, LMP, TEX)
3. Load textures (LEVEL{n}.RES)
4. Load models (LEVEL{n}.RES)
5. Load lightmaps (LIGHTM~1.RES)
6. Load AI scripts (AI/*.QVM)
7. Load navigation graph (graph*.DAT)
8. Load sounds (sounds/*.WAV)
9. Initialize tasks and entities
10. Start level flow

## Navigation Graph (Partially verified)

### Header Format

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Magic: 0xFFEEDDCC | HIGH | Hex dump |
| 0x04 | 4 | Unknown parameter | LOW | Hex dump |
| 0x08 | 4 | Grid dimensions (e.g., 0x0505 = 5x5 sectors) | MEDIUM | Hex dump |
| 0x0C | 4 | Node count | MEDIUM | Hex dump |

### Node Format (Partially verified)

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 12 | Position (3x float32, -1.0 = unpopulated) | MEDIUM | Hex dump |
| 0x0C | var | Edge list (uint16 pairs: target_node, cost) | MEDIUM | Hex dump |

### Known Graph Files (Observed)

| File | Level | Size | Confidence | Method |
|------|-------|------|------------|--------|
| graph1.dat | Level 1 | 80,120 bytes | HIGH | File listing |
| graph2.dat | Level 2 | ~80 KB | HIGH | File listing |
| graph3.dat | Level 3 | ~80 KB | HIGH | File listing |
| ... | ... | ... | ... | ... |
| graph34.dat | Level 7 | ~81 KB | HIGH | File listing |

## Cutscene System (Observed)

AVI playback per level:
- Intro cutscene
- Level start/end cutscenes
- Triggered events

Uses AVIFIL32.dll for video decode.

**Confidence:** MEDIUM - From DLL imports and file listing.

## Level Script System (Observed)

### QSC Source Files

| File | Purpose | Confidence | Method |
|------|---------|------------|--------|
| mission.qsc | Per-mission configuration | MEDIUM | Filename analysis |
| sounds.qsc | Sound definitions | MEDIUM | Filename analysis |
| level*.qsc | Level-specific scripts | MEDIUM | Filename analysis |

### Compiled QVM

| File | Purpose | Confidence | Method |
|------|---------|------------|--------|
| terrain1.qvm | Terrain material/tilemap creation | MEDIUM | Filename analysis |
| AI/*.qvm | AI behavior scripts | MEDIUM | Filename analysis |

## Terrain Parameters (Estimated)

| Parameter | Value | Confidence | Method |
|-----------|-------|------------|--------|
| Grid | 64x64 tile grid per level | MEDIUM | File size analysis |
| Height format | IEEE float32 | HIGH | Hex dump |
| Texture format | LOOP v9 texture package | HIGH | Hex dump |
| Lightmaps | Unknown resolution | ❌ | Not extracted |
| Tile definitions | Material indices (12-bit?) | LOW | Guess |

## Level Editor Functions

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Level_Load | Load level | HIGH | Symbol analysis |
| LevelFlow_IsCountryUSA | Check if USA version | HIGH | Symbol analysis |
| LevelFlow_LevelFailed | Level failed | HIGH | Symbol analysis |
| LevelFlow_GetBreakCutSceneKey | Get cutscene key | HIGH | Symbol analysis |

## Known Issues

1. **Loading sequence unverified** - Reconstructed from file structure
2. **Navigation graph edge format partially known** - Edge list structure unclear
3. **Level themes inferred** - From filenames, not game content
4. **Terrain parameters estimated** - From file sizes, not verified

## References

- Level data: PC/MISSIONS/LOCATI~1/
- Common assets: PC/COMMON/
- Navigation: graph*.dat
- Terrain: terrain/*.{bit,cmd,ctr,lmp,tex}
