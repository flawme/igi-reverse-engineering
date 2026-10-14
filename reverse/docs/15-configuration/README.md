# 15 - Configuration System

## Overview

Game configuration stored in CONFIG.QVM. Handles graphics, sound, input, and game settings.

**Confidence:** HIGH - Configuration options extracted from QVM string analysis.

## Global Options ✅ VERIFIED

`config.qvm` decodes to 43 statements. The full list with values is at
`reverse/data/config_options.tsv`. The defaults the game ships with:

| Option | Default value | Meaning |
|--------|---------------|---------|
| `GOStart` | 0 | entry point |
| `GOContentControlPW` | (empty) | parental-control password |
| `GOPlayer` | `Joe` | player name |
| `GOActiveMission` | 1 | current mission |
| `GOInMouInv` | 1 | invert mouse |
| `GOInMouSens` | 0.4 | mouse sensitivity |
| `GOGfxDisp` | `640, 480, 32` | display mode |
| `GOGfxDevice` | `{00000000-0000-0000-0000-000000000000}` | D3D device GUID (all-zero = default) |
| `GOGfxGamma` | 1 | gamma |
| `GOGfxPerformance` | 0 | graphics detail level |
| `GOGameLang` | `USA` | language |
| `GOGameDiff` | `GD_2` | difficulty |
| `GOIsBlood` | `TRUE` | blood enabled |
| `GOSoundSpeech` | `1, 1` | speech on, volume |
| `GOSoundMusic` | `1, 1` | music on, volume |
| `GOSoundFX` | `1, 1` | effects on, volume |
| `GOInRemap` | 30 bindings | key/mouse remaps |

The 30 `GOInRemap` bindings are the shipped default controls, e.g.
`MoveLeft, INPUTPORT_DEVICE_KEYBOARD, KEY_LEFT`,
`Fire, INPUTPORT_DEVICE_MOUSE, MOUSE_BUTTON_1`,
`Crouch, INPUTPORT_DEVICE_KEYBOARD, KEY_RIGHT_CTRL`,
`WeaponCategory1..9, INPUTPORT_DEVICE_KEYBOARD, KEY_1..KEY_9`.

## Difficulty Levels

| ID | Name | Confidence | Method |
|----|------|------------|--------|
| GD_1 | Easy | ✅ Verified as a constant; behaviour not verified | config.qvm |
| GD_2 | Normal | ✅ Verified - this is the shipped default | config.qvm |
| GD_3 | Hard | ✅ Verified as a constant; behaviour not verified | config.qvm |

The three constants exist and `GD_2` is the default. What each level actually changes
(damage, accuracy, perception) is not in the config file.

## Default Key Bindings (From config)

| Action | Device | Key | Confidence | Method |
|--------|--------|-----|------------|--------|
| MoveLeft | KEYBOARD | KEY_LEFT | HIGH | Configuration analysis |
| MoveRight | KEYBOARD | KEY_RIGHT | HIGH | Configuration analysis |
| MoveUp | KEYBOARD | KEY_UP | HIGH | Configuration analysis |
| MoveDown | KEYBOARD | KEY_DOWN | HIGH | Configuration analysis |
| Fire | MOUSE | MOUSE_BUTTON_1 | HIGH | Configuration analysis |
| Reload | KEYBOARD | KEY_RETURN | HIGH | Configuration analysis |
| Activate | KEYBOARD | KEY_RIGHT_SHIFT | HIGH | Configuration analysis |
| Crouch | KEYBOARD | KEY_RIGHT_CTRL | HIGH | Configuration analysis |
| Jump | KEYBOARD | KEY_NUMPAD0 | HIGH | Configuration analysis |
| NextWeapon | MOUSE | MOUSE_BUTTON_2 | HIGH | Configuration analysis |
| PrevWeapon | KEYBOARD | KEY_O | HIGH | Configuration analysis |
| AlternateFire | KEYBOARD | KEY_BACKSPACE | HIGH | Configuration analysis |
| Peek | KEYBOARD | KEY_NUMPAD1 | HIGH | Configuration analysis |
| Binoculars | KEYBOARD | KEY_SPACE | HIGH | Configuration analysis |
| MapComputer | KEYBOARD | KEY_C | HIGH | Configuration analysis |
| ToggleWalkRun | KEYBOARD | KEY_W | HIGH | Configuration analysis |
| ZoomIn | KEYBOARD | KEY_PAGEUP | HIGH | Configuration analysis |
| ZoomOut | KEYBOARD | KEY_PAGEDOWN | HIGH | Configuration analysis |
| WeaponCategory1-9 | KEYBOARD | KEY_1-KEY_9 | HIGH | Configuration analysis |

## Configuration Functions

### Graphics

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_ResetGraphicOptions | Reset graphics | HIGH | Symbol analysis |
| Config_GraphicOptionsNumPerfLevels | Get performance levels | HIGH | Symbol analysis |
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

### Sound

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

### Input

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_GameOptionsInputSetBloodEnabled | Set blood enabled | HIGH | Symbol analysis |
| Config_GameOptionsInputSetMouseSensitivity | Set mouse sensitivity | HIGH | Symbol analysis |
| Config_GameOptionsInputSetInvertMouse | Set invert mouse | HIGH | Symbol analysis |
| Config_GameOptionsInputGetBloodEnabled | Get blood enabled | HIGH | Symbol analysis |
| Config_GameOptionsInputGetMouseSensitivity | Get mouse sensitivity | HIGH | Symbol analysis |
| Config_GameOptionsInputGetInvertMouse | Get invert mouse | HIGH | Symbol analysis |

### Player Profiles

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Config_GetNumberOfPlayerProfiles | Get profile count | HIGH | Symbol analysis |
| Config_PlayerGetActiveMission | Get active mission | HIGH | Symbol analysis |
| Config_DeletePlayerProfile | Delete profile | HIGH | Symbol analysis |
| Config_CreateNewPlayerProfile | Create profile | HIGH | Symbol analysis |
| Config_SetActivePlayerProfileIndex | Set active profile | HIGH | Symbol analysis |
| Config_GetActivePlayerProfileIndex | Get active profile | HIGH | Symbol analysis |
| Config_FillPlayerProfileListBox | Fill profile list | HIGH | Symbol analysis |

## Known Issues

1. **Configuration values unverified** - Actual runtime values unknown
2. **Default settings unverified** - Assumed from function names
3. **Profile format unknown** - Save/load format not documented
4. **Settings persistence unknown** - How settings are saved is unclear

## References

- Configuration: CONFIG.QVM
- Key bindings: config.qsc
- Symbol analysis of executable
