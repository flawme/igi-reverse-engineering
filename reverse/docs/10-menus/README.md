# 10 - Menu System

## Menu Resources ✅ VERIFIED

`pc/menusystem/*.res` and `pc/screens/**/*.res` are ILFF archives. Their contents are:

| Content | Container |
|---------|-----------|
| Sprites (cursors, buttons, HUD) | **LOOP textures** inside the `.res` |
| Fonts | nested ILFF `.fnt` payloads |
| Strings | `language/<lang>/menusystem.res` (262 strings) |

**`.spr` / `.pic` are extension labels, not formats.** The archives hold **158 `.spr`**
entries (`computer/computer.res` 49, `screens/game/status/status.res` 47,
`menusystem/menusystem.res` 24, `common/sprites/sprites.res` 16,
`menusystem/missionsprites.res` 14, `menusystem/ingamemenu.res` 8) and **5 `.pic`**
entries (`mainmenu.pic`, `logo.pic`, `logo_us.pic` in `menusystem.res`; `loading.pic`,
`loading_us.pic` in `loadingscreen.res`). Every one of those payloads starts with
`LOOP` + version 9 - they are LOOP textures (sprites, HUD elements, the main-menu and
loading pictures), not a separate binary format. A menu sprite decodes to a coherent
PNG with `reverse/tools/loop.py`.

The menu labels themselves are in the game's string table - dump them with
`reverse/tools/langdump.py`. The shipped English labels include `Main Menu`,
`Play Project IGI`, `Multi Player`, `Configuration`, `Quit`, `Update IGI`,
`Visit Website`, `Read Me`, `Credits`, `Start New Game`, `Load Game`,
`Select Mission`, `Sound Configuration`, `FX Volume`, `Music Volume`,
`Graphics Configuration`, `Resolution`, `Render Device`, `Gamma`,
`Advanced Options`, `Graphics Detail`.

## .fnt loader evidence (IGI.exe)

The `.fnt` payloads are loaded by `fcn.004b65d0` (`0x4b65d0`): `cmp eax,0x46464C49`
(ILFF) at `0x4B65FC`, `cmp eax,0x544E4F46` (FONT) at `0x4B6610`; chunk lookups
`push 0x48544E46` (FNTH) at `0x4B663A`, `push 0x4E415254` (TRAN) at `0x4B6645`,
`push 0x464D4E41` (ANMF) at `0x4B6652`. Both shipped fonts are ILFF containers with the
same chunk order
(`FONTFNTH`, `ANMF`, `TRAN`, `TEXH`, `BODY`):

| File | FONTFNTH | ANMF | TRAN | TEXH | BODY |
|---|---|---|---|---|---|
| `screens/intro/font3.fnt` | 24 B | 6160 B = 154x40 | 512 B | 24 B | 131072 B = 256x128x4 |
| `screens/intro/font4.fnt` | 24 B | 6160 B = 154x40 | 512 B | 24 B | 65536 B = 128x128x4 |

### TRAN - the character-to-glyph map ✅ VERIFIED

`TRAN` is a **256-entry `uint16` array indexed by Latin-1 character code**, holding the
glyph index. The loader allocates 256 bytes (`push 0x100` at `0x4B6740`,
`call 0x4B74F0` at `0x4B6745`), stores the pointer at `font+0x0C`
(`mov [edi+0xc],eax` at `0x4B674D`) and fills it entry by entry:

```
0x4B6752 mov al, byte [ebx]      ; low byte of TRAN[i]
0x4B6754 mov ecx, [edi+0xc]      ; the table
0x4B675C call 0x4B75B0           ; table[i] = value
0x4B6764 inc esi
0x4B6765 add ebx, 2              ; 2 bytes per entry
0x4B6768 cmp esi, 0x100
```

Data verification (both fonts, byte-identical tables): 154 non-zero entries, values
exactly the set {1..154} - a permutation, so every glyph 1..154 is reachable and glyph
0 is unused. `0x41`-`0x5A` (`A`..`Z`) map to 30..55, `0x61`-`0x7A` (`a`..`z`) to 62..87;
the Latin-1 tail (`0xA0`-`0xFF`) is identical in both fonts (e.g. `0xF7` -> 154, the
sentinel entry). Characters absent from the table (space, `!`-`$`, `0x83`-`0xA0`) have
no glyph and must be handled by the renderer.

### FONTFNTH ✅ VERIFIED

`FONTFNTH` is 24 bytes = 6 dwords:

| Field | font3 | font4 | Meaning | Evidence |
|---|---|---|---|---|
| 0 | 1 | 1 | font init arg8: `0x10000` if 0, else 0 | `0x4B66E7` neg/sbb, pushed at `0x4B66FB` |
| 1 | 154 | 154 | **glyph count** | `mov edx,[edi+4]` `0x4B66DE` -> font init arg10 -> `font+0x14` (`0x4B64B6`) |
| 2 | 32 | 32 | **no reader** | - |
| 3 | 6 | 4 | sentinel glyph `+0x10` | `0x4B6543` |
| 4 | 24 | 24 | sentinel glyph `+0x0C` | `0x4B6527` |
| 5 | 21 | 15 | **max glyph height + 1** (font3 20 -> 21, font4 14 -> 15); sentinel glyph `+0x0E` | `0x4B6534` |

Fields 3/4/5 are stored into the **sentinel glyph at index 154** (the font init writes
it at `0x4B6527`/`0x4B6534`/`0x4B6543`), i.e. a virtual glyph carrying the font-wide
metrics. Field 2 (32) has no reader at all.

### The glyph record (40 bytes) ✅ VERIFIED

`ANMF` is `glyph_count` records of 40 bytes. Layout (verified against both files):

| Offset | Type | Meaning | Evidence |
|---|---|---|---|
| +0x04 | float | u0 | `mov edx,[esi-8]` `0x4B6784` |
| +0x08 | float | v0 | `mov ecx,[esi-4]` `0x4B6780` |
| +0x0C | float | u1 | `mov eax,[esi]` `0x4B677E` |
| +0x10 | float | v1 | `mov edx,[esi+4]` `0x4B677B` |
| +0x16 | word | width | `movsx edx, word [esi+0xa]` `0x4B67A0` |
| +0x18 | word | height | `movsx ecx, word [esi+0xc]` `0x4B679C` |
| +0x1A | word | advance | `movsx ecx, word [esi+0xe]` `0x4B678C` |
| +0x24 | word | per-glyph vertical metric (see below) | `movsx edx, word [esi+0x18]` `0x4B6792` |

Data verification (both fonts, 154/154 glyphs): `(u1-u0)*atlas_width == width` and
`(v1-v0)*atlas_height == height` - 0 failures; every rect contains ink (coverage is the
4th byte of each 32bpp pixel).

⚠️ **`+0x24` is not settled.** It is a per-glyph 16-bit value (0..16) that the loader
copies into the internal 36-byte glyph at `+0x10` (`mov word [edx+eax+0x10], si` at
`0x4B643F`) - the same slot the sentinel uses for `FONTFNTH+0x0C`. Data-consistent
reading: `height + value` is 17 for most glyphs (font3: `A` 15+2, `y` 11+6) and 21 for
the tallest ones (`(` 20+1), i.e. it behaves like a vertical metric that, added to the
glyph height, lands on the font's line box (21 = `FONTFNTH+0x14`). It is not the ink
offset inside the glyph rect (`.` has h=6 with its ink in the bottom 2 rows and
`+0x24` = 14). The renderer that consumes the internal glyph record was not located,
so the exact semantic is open.

## Menu Hierarchy (Reconstructed)

**Confidence:** MEDIUM - Reconstructed from menu QVM files and UI observation. May be incomplete.

```
Main Menu
├── Single Player
│   ├── New Game
│   │   ├── Mission Selection
│   │   └── Difficulty (GD_1, GD_2, GD_3)
│   ├── Load Game
│   ├── Save Game
│   └── Player Profile (Create/Delete/Select)
├── Configuration
│   ├── Graphics
│   │   ├── Device Selection
│   │   ├── Resolution
│   │   ├── Performance Level
│   │   └── Advanced (Textures, Lightmaps, Geometry)
│   ├── Sound (Music/FX Volume)
│   ├── Controls (Mouse Sensitivity, Invert, Key Remapping)
│   ├── Language (EN/FR/DE/IT/ES)
│   └── Content Control (Password)
├── Credits
├── Readme
└── Quit

In-Game Menu (Pause)
├── Resume
├── Restart Mission
├── Sound Options
├── Controls
├── Graphics (subset)
├── Save/Load
└── Quit to Main Menu
```

## MenuManager API

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| MenuManager_SetEnabled | Enable/disable menu | HIGH | Symbol analysis |
| MenuManager_DeactivatePopuScreen | Close popup | HIGH | Symbol analysis |
| MenuManager_ActivatePopupScreen | Open popup | HIGH | Symbol analysis |
| MenuManager_ForceUpdateWindow | Force refresh | HIGH | Symbol analysis |
| MenuManager_PopScreen | Pop screen stack | HIGH | Symbol analysis |
| MenuManager_PushScreen | Push screen stack | HIGH | Symbol analysis |
| MenuManager_SetLanguage | Set UI language | HIGH | Symbol analysis |
| MenuManager_LeaveMenus | Exit all menus | HIGH | Symbol analysis |
| MenuManager_RequestScreen | Request screen switch | HIGH | Symbol analysis |

## Menu QVM Files

| File | Size | Content | Confidence | Method |
|------|------|---------|------------|--------|
| mainmenu.qvm | 25,549 | Main menu definitions | MEDIUM | File listing |
| ingame~1.qvm | 11,308 | Pause menu | MEDIUM | File listing |

## Menu Resources (Observed)

| File | Content | Confidence | Method |
|------|---------|------------|--------|
| MAINMENU.QVM | Menu structure and logic | MEDIUM | File listing |
| MENUSY~1.RES | Menu textures | HIGH | File listing |
| INGAME~1.RES | In-game menu textures | HIGH | File listing |
| LOADIN~1.RES | Loading screen textures | HIGH | File listing |
| MISSIO~1.RES | Mission select textures | HIGH | File listing |
| ENGLISH.RES | Localized text | HIGH | File listing |
| MENUSY~1.DAT | Menu data | HIGH | File listing |
| MENUSY~1.MTP | Menu material properties | HIGH | File listing |

## Menu Screens (Observed)

| Screen | Purpose | Confidence | Method |
|--------|---------|------------|--------|
| Main Menu | Title screen | MEDIUM | UI observation |
| Mission Select | Level picker | MEDIUM | UI observation |
| Loading Screen | Level loading | MEDIUM | UI observation |
| In-Game Menu | Pause menu | MEDIUM | UI observation |
| Config Menu | Settings | MEDIUM | UI observation |
| Credits | End credits | MEDIUM | UI observation |

## Language Support (Observed)

| Language | Directory | Confidence | Method |
|----------|-----------|------------|--------|
| English | PC/LANGUAGE/ENGLISH/ | HIGH | File listing |
| French | PC/LANGUAGE/FRENCH/ | HIGH | File listing |
| German | PC/LANGUAGE/GERMAN/ | HIGH | File listing |
| Italian | PC/LANGUAGE/ITALIAN/ | HIGH | File listing |
| Spanish | PC/LANGUAGE/SPANISH/ | HIGH | File listing |
| USA English | PC/LANGUAGE/USA/ | HIGH | File listing |

## Content Control

Password-protected parental controls:
- Config_IsContentControlPasswordEnabled
- Config_VerifyContentControlPassword
- Config_GetContentControlPassword
- Config_SetContentControlPassword

**Confidence:** HIGH - From symbol analysis.

## Menu Flow Events (From strings)

| Event | Description | Confidence | Method |
|-------|-------------|------------|--------|
| FLOW_EVENT_RESTART_GAME | Restart | MEDIUM | String analysis |
| FLOW_EVENT_GAME | Game | MEDIUM | String analysis |
| FLOW_EVENT_MAINMENU | Main menu | MEDIUM | String analysis |
| FLOW_EVENT_INTRO | Intro | MEDIUM | String analysis |
| FLOW_EVENT_QUIT | Quit | MEDIUM | String analysis |

## Configuration Functions

### Graphics Settings

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_GraphicOptionsNumPerfLevels | Get number of performance levels | HIGH | Symbol analysis |
| Config_GraphicOptionsGetPerfLevelFromFlags | Get level from flags | HIGH | Symbol analysis |
| Config_GraphicOptionsGetPerfFlagsFromLevel | Get flags from level | HIGH | Symbol analysis |
| Config_GraphicOptionsGetPerformanceFlags | Get performance flags | HIGH | Symbol analysis |
| Config_GraphicOptionsGetGamma | Get gamma | HIGH | Symbol analysis |
| Config_GraphicOptionsGetDevice | Get device | HIGH | Symbol analysis |
| Config_GraphicOptionsGetTransparency | Get transparency | HIGH | Symbol analysis |
| Config_GraphicOptionsGetResolution | Get resolution | HIGH | Symbol analysis |
| Config_GraphicOptionsSetPerformanceFlags | Set performance flags | HIGH | Symbol analysis |
| Config_GraphicOptionsSetGamma | Set gamma | HIGH | Symbol analysis |
| Config_GraphicOptionsSetDevice | Set device | HIGH | Symbol analysis |
| Config_GraphicOptionsSetTransparency | Set transparency | HIGH | Symbol analysis |
| Config_GraphicOptionsSetResolution | Set resolution | HIGH | Symbol analysis |

### Sound Settings

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_SoundOptionsGetReverseStereo | Get reverse stereo | HIGH | Symbol analysis |
| Config_SoundOptionsGetSpeechVolume | Get speech volume | HIGH | Symbol analysis |
| Config_SoundOptionsGetSpeech | Get speech enabled | HIGH | Symbol analysis |
| Config_SoundOptionsGetMusicVolume | Get music volume | HIGH | Symbol analysis |
| Config_SoundOptionsGetMusic | Get music enabled | HIGH | Symbol analysis |
| Config_SoundOptionsGetSoundsEffectsVolume | Get effects volume | HIGH | Symbol analysis |
| Config_SoundOptionsGetSoundsEffects | Get effects enabled | HIGH | Symbol analysis |
| Config_SoundOptionsSetReverseStereo | Set reverse stereo | HIGH | Symbol analysis |
| Config_SoundOptionsSetSpeechVolume | Set speech volume | HIGH | Symbol analysis |
| Config_SoundOptionsSetSpeech | Set speech enabled | HIGH | Symbol analysis |
| Config_SoundOptionsSetMusicVolume | Set music volume | HIGH | Symbol analysis |
| Config_SoundOptionsSetMusic | Set music enabled | HIGH | Symbol analysis |
| Config_SoundOptionsSetSoundsEffectsVolume | Set effects volume | HIGH | Symbol analysis |
| Config_SoundOptionsSetSoundsEffects | Set effects enabled | HIGH | Symbol analysis |

### Input Settings

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_GameOptionsInputSetBloodEnabled | Set blood enabled | HIGH | Symbol analysis |
| Config_GameOptionsInputSetMouseSensitivity | Set mouse sensitivity | HIGH | Symbol analysis |
| Config_GameOptionsInputSetInvertMouse | Set invert mouse | HIGH | Symbol analysis |
| Config_GameOptionsInputGetBloodEnabled | Get blood enabled | HIGH | Symbol analysis |
| Config_GameOptionsInputGetMouseSensitivity | Get mouse sensitivity | HIGH | Symbol analysis |
| Config_GameOptionsInputGetInvertMouse | Get invert mouse | HIGH | Symbol analysis |

### UI Helpers

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_FillRenderDeviceListBox | Fill device list | HIGH | Symbol analysis |
| Config_FillScreenResolutionListBox | Fill resolution list | HIGH | Symbol analysis |
| Config_FillMissionTextBox | Fill mission text | HIGH | Symbol analysis |
| Config_FillMissionPictureBox | Fill mission picture | HIGH | Symbol analysis |
| Config_FillMissionSelectionBox | Fill mission selection | HIGH | Symbol analysis |
| Config_GetNumberOfPlayerProfiles | Get profile count | HIGH | Symbol analysis |
| Config_PlayerGetActiveMission | Get active mission | HIGH | Symbol analysis |
| Config_DeletePlayerProfile | Delete profile | HIGH | Symbol analysis |
| Config_CreateNewPlayerProfile | Create profile | HIGH | Symbol analysis |
| Config_SetActivePlayerProfileIndex | Set active profile | HIGH | Symbol analysis |
| Config_GetActivePlayerProfileIndex | Get active profile | HIGH | Symbol analysis |
| Config_FillPlayerProfileListBox | Fill profile list | HIGH | Symbol analysis |

## Known Issues

1. **Menu hierarchy may be incomplete** - Reconstructed from observation
2. **Screen flow unclear** - How screens transition is not documented
3. **Widget system unknown** - UI element types and properties unknown
4. **Menu textures unverified** - Actual menu appearance unknown

## References

- Menu scripts: mainmenu.qvm, ingame~1.qvm
- Menu textures: MENUSY~1.RES, INGAME~1.RES
- Localization: PC/LANGUAGE/
