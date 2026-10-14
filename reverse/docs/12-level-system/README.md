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

## Level IDs and Mission Names

**Verified from the game's own string table** - `pc/language/<lang>/missions.res` holds
the `Mission N Name` / `Mission N Desc` keys the engine looks up. Dump them with
`reverse/tools/langdump.py`.

| Level | Mission name | Description |
|-------|--------------|-------------|
| 1 | Trainyard | Small coastline trainyard |
| 2 | SAM Base | Small missile defence base |
| 3 | Military Airbase | Rescue Josef from the airbase |
| 4 | GOD | Defend the friendly troops |
| 5 | Radar Base | Disrupt Jach's communications network |
| 6 | Get Priboi | Kidnap Jach from his base |
| 7 | Border Crossing | Get Jones across the border |
| 8 | Re-supply | Get Jones' equipment back |
| 9 | Missile Trainyard | Get on the train |
| 10 | Defend Priboi | Take Jach to the FRV |
| 11 | Eagle's Nest I | The approach to Ekk's fortress |
| 12 | Eagle's Nest II | Ekk's hilltop fortress |
| 13 | Nuclear Infiltration | Infiltrate the nuclear base |
| 14 | Finding the bomb | Kill Ekk and find the bomb |

**Confidence:** HIGH - read directly from `language/english/missions.res`, not inferred.
Level 14's `mission.qvm` also carries the sentinel string
`MISSION_NEXT_MISSION_UNDEFINED`, marking it as the last mission.

The five other language directories (`french`, `german`, `italian`, `spanish`, `USA`)
each hold the same six `.res` files with translated text.

### Localisation resources

| File | Strings | Contents |
|------|---------|----------|
| `missions.res` | 28 | mission names and descriptions |
| `objectives.res` | 78 | objective complete/failed/incomplete messages |
| `movies.res` | 18 | intro and outro cutscene subtitles |
| `computer.res` | 6 | HUD computer labels (Map, Objectives, Log, INITIALIZING, ...) |
| `menusystem.res` | 262 | every menu label |
| `messages.res` | 514 | weapon names, building tooltips, in-game messages |

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
├── COMMON.DAT    - Model/texture dependency list (plain text)
└── COMMON.MTP    - Model/texture manifest (MODS/VNAM/INST/TEXF/GTT)
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

## Navigation Graph ✅ VERIFIED

### Header Format ✅ VERIFIED

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Magic: 0xFFEEDDCC | ✅ | 293/293 files |
| 0x0C | 4 | Grid dimension (100 in most files, 300 in `graph4019.dat`) | ✅ | header dump |
| 0x1A | 4 | Grid byte size = `dim * dim * 8` | ✅ | 293/293 |
| 0x1E | `dim*dim*8` | Routing matrix, 8 bytes per cell | ✅ | loader `fcn.00509360` |

### Cell Format ✅ VERIFIED

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Next-hop node ID (`0xFFFFFFFF` = no route) | ✅ | accessor `fcn.00509740`; 66,408 column-adjacent cells |
| 0x04 | 4 | Path distance (float) | ✅ | symmetry + triangle inequality |

The tail is a stream of name-hashed records (`nNodeID`, `tNodePosition`, `vNodeRadius`,
`nLinkID1`/`nLinkID2`, `eLinkType`, ...). See
[16-verified-formats](../16-verified-formats/README.md).

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
| Lightmaps | 16/32/64/128 (powers of two), 8-bit greyscale | ✅ | 14/14 files consume exactly |
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
2. **Navigation graph** - decoded (routing table + name-hashed records); the level8 tag-only layout is the exception
3. **Level themes inferred** - From filenames, not game content
4. **Terrain grid size estimated** - From file sizes; the other terrain formats are verified

## References

- Level data: PC/MISSIONS/LOCATI~1/
- Common assets: PC/COMMON/
- Navigation: graph*.dat
- Terrain: terrain/*.{bit,cmd,ctr,lmp,tex}
