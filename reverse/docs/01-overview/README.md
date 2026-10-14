# 01 - Project Overview

## Game Info

- **Title:** Project IGI (I'm Going In)
- **Developer:** Innerloop Studios (Norway, dissolved 2003)
- **Publisher:** Eidos Interactive (now Square Enix)
- **Release:** December 15, 1999 (EU), March 2000 (US)
- **Genre:** First-person tactical shooter
- **Platform:** Windows (DirectX 7)
- **Engine Version:** 0.0.124 (from string analysis - may be inaccurate)

## System Requirements (Original)

- **OS:** Windows 95/98/ME
- **CPU:** Pentium II 300MHz
- **RAM:** 64MB
- **GPU:** 8MB DirectX 7 compatible
- **Storage:** 500MB

## Game Structure

### Missions (14 total)

Names verified from the game's own string table (`pc/language/english/missions.res`),
not inferred. See [12-level-system](../12-level-system/README.md) for the full table
with descriptions.

| ID | Directory | Mission name |
|----|-----------|--------------|
| 1 | LEVEL1 | Trainyard |
| 2 | LEVEL2 | SAM Base |
| 3 | LEVEL3 | Military Airbase |
| 4 | LEVEL4 | GOD |
| 5 | LEVEL5 | Radar Base |
| 6 | LEVEL6 | Get Priboi |
| 7 | LEVEL7 | Border Crossing |
| 8 | LEVEL8 | Re-supply |
| 9 | LEVEL9 | Missile Trainyard |
| 10 | LEVEL10 | Defend Priboi |
| 11 | LEVEL11 | Eagle's Nest I |
| 12 | LEVEL12 | Eagle's Nest II |
| 13 | LEVEL13 | Nuclear Infiltration |
| 14 | LEVEL14 | Finding the bomb |
| - | common | shared assets (not a mission) |

**Note:** the "SHARED" directory in earlier revisions of this document is
`missions/location0/common`; there is no `SHARED` directory in the retail tree.
Difficulty ratings are not present in the game data.

### Per-Mission Directory Structure

```
MISSIONS/LOCATI~1/{MISSION}/
├── TERRAIN/
│   ├── terrain{N}.bit      # Heightmap vertices
│   ├── terrain{N}.cmd      # Tile commands
│   ├── terrain{N}.ctr      # Tile centers
│   ├── terrain{N}.lmp      # Lightmap data
│   └── terrain{N}.tex      # Terrain texture atlas
├── AI/
│   └── {mission}.qvm       # AI scripts
├── TEXTURES/
│   └── level{N}_tex.res    # Texture archive (ILFF)
├── MODELS/
│   └── level{N}_models.res # Model archive (ILFF)
├── LIGHTMAPS/
│   └── lightmap{N}.res     # Lightmap archive (ILFF)
├── GRAPHS/
│   └── graph{N}.dat        # Navigation graph
├── SOUNDS/
│   └── *.wav               # Sound effects
└── ANIMS/
    └── *.anm               # Animations
```

**Method:** Filesystem listing of extracted game files.

### Shared Assets

```
PC/MISSIONS/LOCATI~1/SHARED/
├── COMMON/                 # Common textures, sprites
├── COMPUTER/               # Computer/hacking minigame
├── INGAME/                 # HUD elements
├── LOADING/                # Loading screens
├── MISSION/                # Mission select
├── SPRITES/                # UI sprites
├── TECHNICAL/              # Technical screens
├── AUDIO/                  # Music
├── QVM/                    # Core scripts
├── FONTS/                  # Font files
├── LANGUAGE/               # Localization
└── STATUSSCREEN/           # Status screens
```

## File Count

| Type | Count | Description | Confidence | Method |
|------|-------|-------------|------------|--------|
| QVM | 997 | Bytecode scripts | HIGH | Filesystem listing |
| WAV | 413 | ILSF sound samples | HIGH | Filesystem listing |
| DAT | 317 | Navigation graphs (300) + level manifests | HIGH | Filesystem listing |
| RES | 92 | ILFF archives | HIGH | Filesystem listing |
| TEX | 26 | Texture packages | HIGH | Filesystem listing |
| MTP | 17 | Level manifests | HIGH | Filesystem listing |
| LMP / CTR / CMD / BIT | 14 each | Terrain data | HIGH | Filesystem listing |
| Other | 37 | Fonts, cutscenes, config, etc. | HIGH | Filesystem listing |
| **Total** | **1,955** | | HIGH | Filesystem listing |

## AFP Archives (PC/AFPS/)

| Name | Content | Confidence | Method |
|------|---------|------------|--------|
| CONFIG.AFP | Game configuration | MEDIUM | Filename inference |
| ANYS.AFP | Unknown | LOW | Filename guess (analytics?) |
| DILJ.AFP | Unknown | LOW | No evidence |
| MPZM.AFP | Unknown | LOW | Filename guess (multiplayer?) |
| YMBE.AFP | Unknown | LOW | No evidence |

**Note:** MPZM.AFP may contain multiplayer data, but no multiplayer code was found in the executable. This is a contradiction that needs investigation.

## Engine Architecture

### Core Systems (Inferred from imports and strings)

| System | Technology | Confidence | Method |
|--------|------------|------------|--------|
| Rendering | DirectX 7 | HIGH | DLL import analysis |
| Scripting | QVM bytecode | HIGH | File format analysis |
| AI | Event-driven system | MEDIUM | String analysis |
| Physics | Unknown | LOW | No direct evidence |
| Audio | DirectSound | HIGH | DLL import analysis |
| Input | DirectInput | HIGH | DLL import analysis |

### Rendering Pipeline (Reconstructed, not verified)

1. Terrain (heightmap + textures)
2. Static models (opaque)
3. Transparent objects
4. Particles/effects
5. HUD/UI

**Confidence:** LOW - Pipeline order is inferred from standard practices, not verified from source.

### Scripting Architecture (Partially verified)

- QVM files contain bytecode (format verified)
- 5 sections per QVM (header verified)
- Event-driven: respond to game events (from string analysis)
- Actions: modify game state (from string analysis)

## Key Strings (from QVM)

```
GOStart
GOPlayer=Joe
GOGameDiff=GD_2
GOIsBlood=TRUE
GONoCloth=FALSE
GOWeapon=Desert_Eagle
```

**Method:** String extraction from QVM files.

## Technical Notes

- Engine version 0.0.124 (from string analysis - may be inaccurate)
- Uses MSVC 6.0 (1998 compiler) - confirmed via PE header
- DirectX 7 for rendering - confirmed via DLL imports
- DirectInput for input - confirmed via DLL imports
- DirectSound for audio - confirmed via DLL imports
- Custom memory allocator (inferred from heap patterns)
- No Lua/Python - all custom scripting (from imports)

## References

- Game executable: IGI.EXE (PE32, 1.5MB)
- Data files: PC/MISSIONS/, PC/SHARED/, PC/AFPS/
- No source code available
- No official documentation
