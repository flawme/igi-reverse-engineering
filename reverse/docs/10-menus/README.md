# 10 - Menu System

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
