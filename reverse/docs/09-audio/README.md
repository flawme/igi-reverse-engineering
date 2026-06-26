# 09 - Audio System

## Technology

| Component | Technology | Confidence | Method |
|-----------|------------|------------|--------|
| Primary | DirectSound | HIGH | DLL import analysis |
| Mixing | WINMM mixer API | HIGH | DLL import analysis |
| Media Control | mciSendCommandA | HIGH | DLL import analysis |
| Cutscenes | AVIFIL32.dll + MSVFW32.dll | HIGH | DLL import analysis |

## Sound Classes (Reconstructed)

**Confidence:** MEDIUM - Class names extracted from string analysis, but hierarchy is reconstructed.

| Class | Description | Confidence | Method |
|-------|-------------|------------|--------|
| SoundManager | Master audio controller | MEDIUM | String analysis |
| SoundSysController | System-level audio | MEDIUM | String analysis |
| SoundSysDef | Sound definition | MEDIUM | String analysis |
| SoundSysDefParent | Parent sound definition | MEDIUM | String analysis |
| SoundSysMicrophone | 3D audio listener | MEDIUM | String analysis |
| SoundDefGraph | Graph-based sound | MEDIUM | String analysis |
| SoundDefGroup | Sound group | MEDIUM | String analysis |
| SoundDefSound | Individual sound | MEDIUM | String analysis |
| SoundDefTriggerOnce | One-shot trigger | MEDIUM | String analysis |

## Audio API Functions

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| Game_DisableMusic | Stop music playback | HIGH | Symbol analysis |
| Game_EnableMusic | Start music playback | HIGH | Symbol analysis |
| Game_SetMusicVolume | Set music volume (0-100) | HIGH | Symbol analysis |
| Game_SetSFXVolume | Set SFX volume | HIGH | Symbol analysis |
| Game_UpdateVolume | Refresh all volumes | HIGH | Symbol analysis |

## Audio File Format

Standard RIFF/WAV PCM format:
- Header: "RIFF" + size + "WAVE"
- Format chunk: "fmt " + format info
- Data chunk: "data" + PCM samples

**Confidence:** MEDIUM - Standard WAV format assumed. Actual compression (PCM vs ADPCM) is unknown.

## Sound Categories (Inferred)

| Category | Examples | Confidence | Method |
|----------|---------|------------|--------|
| Ambient | M*_AMB*.WAV, M*_WIND.WAV | MEDIUM | Filename analysis |
| Music | game_music, menu_music | MEDIUM | Filename analysis |
| Weapon | Fire, reload, impact sounds | MEDIUM | Filename analysis |
| Voice | Communication, radio | MEDIUM | Filename analysis |
| Effects | Explosion, footsteps | MEDIUM | Filename analysis |
| UI | Menu clicks, beeps | MEDIUM | Filename analysis |

## Per-Level Sounds

Each level has unique sounds in:
```
MISSION:sounds/
```

Examples (from filesystem):
- BIRD_01.WAV, BIRD_02.WAV, BIRD_03.WAV
- M5_BEEPS.WAV, M5_CAR.WAV
- _CUT05~1.WAV through _CUT05~5.WAV

**Confidence:** HIGH - Observed from extracted files.

## Sound Configuration

Defined in sounds.qsc per level:
```
LOCAL:common/sounds/
MISSION:sounds/
```

**Confidence:** HIGH - From QVM script analysis.

## Cutscene Audio

AVI files paired with WAV files:
- EIDOS.AVI + EIDOS.WAV
- INNERL~1.AVI + INNERL~1.WAV
- INTRO_US.AVI + INTRO_US.WAV
- OUTRO.AVI + OUTRO.WAV
- VP.AVI + VP.WAV

**Confidence:** HIGH - Observed from extracted files.

## Cutscene Playback (Reconstructed)

**Confidence:** MEDIUM - API call sequence reconstructed from function names.

1. AVIFileInit() - Initialize
2. AVIFileOpenA() - Open .avi file
3. AVIFileGetStream() - Get video stream
4. AVIStreamInfoA() - Stream properties
5. AVIStreamRead() - Read frames
6. ICDecompress() - Decode (via MSVFW32.dll)
7. AVIFileExit() - Cleanup

## Cutscene Files (Observed)

| File | Content | Confidence | Method |
|------|---------|------------|--------|
| EIDOS.AVI/WAV | Eidos logo | HIGH | File listing |
| INNERLOGIC.AVI/WAV | Developer logo | HIGH | File listing |
| INTRO_US.AVI/WAV | US intro | HIGH | File listing |
| OUTRO.AVI/WAV | Ending | HIGH | File listing |
| VP.AVI/WAV | Victory Pictures logo | HIGH | File listing |

## Known Issues

1. **Sample rate unknown** - Not extracted from WAV files
2. **Bit depth unknown** - Not extracted from WAV files
3. **Compression unknown** - PCM assumed, but ADPCM possible
4. **Sound class hierarchy unverified** - Reconstructed from strings
5. **3D audio implementation unknown** - SoundSysMicrophone suggests 3D audio, but details unclear

## References

- DirectSound: DSOUND.dll
- Video: AVIFIL32.dll, MSVFW32.dll
- Audio mixing: WINMM mixer API
- Sound scripts: sounds.qsc per level
