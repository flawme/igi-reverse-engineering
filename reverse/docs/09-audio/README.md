# 09 - Audio System

## Technology Stack

| Component | Technology | Confidence | Method |
|-----------|------------|------------|--------|
| Primary API | DirectSound | ✅ Verified | DLL import analysis |
| Mixing API | WINMM | ✅ Verified | DLL import analysis |
| Cutscene API | AVIFIL32.dll | ✅ Verified | DLL import analysis |
| Sample container | **ILSF** (custom) | ✅ Verified | 759/759 payloads + the loader in `IGI.exe` |

## Sample Format: ILSF ✅ VERIFIED

**Every audio file in the game is ILSF, not RIFF/WAVE.** Earlier revisions of this
document said "RIFF/WAV (PCM assumed)" - that is wrong. `python3 -c "import wave;
wave.open(f)"` fails with "file does not start with RIFF id" on all 413 loose `.wav`
files, and the first-4-bytes histogram over them is `{b'ILSF': 413}`.

The same container also holds the 346 `BODY` payloads of the two sound `.res`
archives, for **759 ILSF payloads total, 0 exceptions**.

### Header (20 bytes)

| Offset | Size | Type | Meaning | Evidence |
|--------|------|------|---------|----------|
| 0x00 | 4 | char[4] | `"ILSF"` | 759/759 |
| 0x04 | 2 | uint16 | version: 0/2 = loose `.wav`, 1/3 = inside a `.res` `BODY` | 759/759, perfect correlation with the container |
| 0x06 | 2 | uint16 | bits per sample - **always 16** | 759/759 |
| 0x08 | 2 | uint16 | channel count (1 or 2) | 759/759 |
| 0x0A | 2 | uint16 | flags: `0` for loose files, `0x1002` for `.res` members | 759/759, constant per version |
| 0x0C | 4 | uint32 | sample rate: 11025 / 22050 / 44100 | 759/759 |
| 0x10 | 4 | uint32 | frame count (samples **per channel**) | see below |
| 0x14 | | | sample data | |

### Versions and encodings

| Version | Count | Where | Encoding |
|---------|-------|-------|----------|
| 0 | 3 | loose `.wav` | 16-bit PCM |
| 1 | 338 | `.res` `BODY` | 16-bit PCM |
| 2 | 410 | loose `.wav` | 4-bit IMA ADPCM |
| 3 | 8 | `.res` `BODY` | 4-bit IMA ADPCM |

Loose files use 11025, 22050 and 44100 Hz; `.res` members use 22050 and 44100 Hz.
Channel counts are 1 or 2 in both.

### The decoder is in the executable

`"ILSF"` occurs exactly once in `IGI.exe`, at file offset `0x95E36` (VA `0x495E36`):

```
8b 06           mov  eax, [esi]
3d 49 4c 53 46  cmp  eax, 0x46534C49        ; "ILSF"
74 1b           je   0x495E58               ; -> the loader
```

The header layout above was read from that loader, not inferred.

### Decoding

`reverse/tools/misc.py` decodes ILSF to a playable WAV (stdlib `wave`). Verified
outputs include `game_music.wav` (12.8 MB), `menu_music.wav` (6.7 MB) and the full set
of footstep, weapon and UI samples.

## Loader evidence (IGI.exe)

The ILSF loader is `0x495e00`; the magic compare `cmp eax, 0x46534c49` ("ILSF")
is at `0x495e36`. Static disassembly settles the three open questions above.

### The `flags` field (`+0x0A`) controls nothing

✅ Verified: the loader copies the whole 20-byte header to `obj+0x10`
(`0x495ec7 rep movsd`) but never reads the flags word. The only header fields it
reads are:

| Field | Read at |
|-------|---------|
| `+0x14` version | `0x495ec9` |
| `+0x16` bits | `0x495fdf` |
| `+0x18` channels | `0x495fdb` |
| `+0x1c` rate | `0x495fc8` |
| `+0x20` frames | `0x495f3b` |

An exhaustive `.text` scan for every memory operand with displacement `0x1a`
found **11 hits, none in the sound module `0x495000`-`0x497000`**. The only
`0x1002` immediate in `.text` is `LOCALE_ILANGUAGE` for `GetLocaleInfoA` at
`0x48eea4`.

So the flags word is **authoring metadata** - written by the packing tool and
never consumed. Only the container correlation is provable: `0` for loose
`.wav`, `0x1002` for `.res` members.

### The version field is a bitfield

✅ Verified. The loader switches on the version word (`0x495ec9` /
`0x495ed9 jmp dword [eax*4 + 0x4960d0]`) and the table at `0x4960d0` is:

| Index | Target | Meaning |
|-------|--------|---------|
| 0 | `0x495ee0` | loose |
| 1 | `0x495f95` | archived |
| 2 | `0x495ee0` | loose |
| 3 | `0x495f30` | archived |

`v0 == v2` and `v1 != v3`, so the loader branches on **bit0 only**:
bit0 = "inside a `.res` archive". **bit1 = IMA ADPCM**, consumed in the
streaming path: `0x496a47 cmp word [ecx+0x14], 2` -> `0x496b70` (ADPCM) /
`0x496c10` (PCM).

### The trailing byte is zero pad, never read

✅ Verified. The nibble pump (`0x496193`-`0x4961bc`) reads one byte per two
samples, so it consumes exactly `ceil(frames*channels/2)` bytes and never reads
a trailing byte.

Over all 418 compressed payloads (410 loose v2 + 8 archived v3):

| payload - `ceil(frames*ch/2)` | count |
|---|---|
| 0 | 205 |
| +1 | 213 |
| anything else | 0 |

The extra byte is `0x00` in 209 of the 213 cases (`0x02` once, `0x53` once,
`0x94` twice) - a zero pad written by the encoder.

## Sound Archives

`.res` sound archives are ILFF containers whose `BODY` payloads are ILSF samples:

| Archive | Contents |
|---------|----------|
| `pc/common/sounds/sounds.res` | shared effects |
| `pc/missions/location0/level*/sounds/*.res` | per-level effects |
| `pc/menusystem/SOUND/*.res` | menu and music |

## Cutscenes

The five `.avi` files are standard RIFF/AVI. `AVIFIL32.dll` + `MSVFW32.dll` handle
playback.

## Still unknown

1. **ILSF `flags` (`+0x0A`)** - **Resolved**: the loader never reads it (see Loader
   evidence above), so it is authoring metadata. It is constant `0` for loose files and
   `0x1002` for `.res` members across all 759 payloads; only that container correlation
   is provable.
2. **ILSF version semantics** - **Resolved**: the version word is a bitfield
   (`bit0 = in archive`, `bit1 = compressed`), proven by the loader's switch table
   `0x4960d0` (v0 == v2, v1 != v3) and the ADPCM branch at `0x496a47`.
3. **The 0-or-1 trailing byte in compressed payloads** - **Resolved**: it is zero pad,
   never read. The nibble pump consumes exactly `ceil(frames*channels/2)`; 205/418 end
   exactly there and 213/418 have one extra byte, `0x00` in 209 of those.

## References

- Decoder: `reverse/tools/misc.py`
- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
