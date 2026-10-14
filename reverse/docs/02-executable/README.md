# 02 - Executable Analysis

## PE Header

| Field | Value | Confidence | Method |
|-------|-------|------------|--------|
| Format | PE32 (GUI) Intel 80386 | ✅ Verified | PE header |
| Timestamp | 975522650 = 2000-11-29 18:30:50 UTC | ✅ Verified | PE header (COFF TimeDateStamp) |
| Linker | MSVC 6.0 (MajorLinkerVersion=6, MinorLinkerVersion=0) | ✅ Verified | PE header |
| ImageBase | 0x00400000 | ✅ Verified | PE header |
| EntryPoint | 0x004A4F85 (.text section) | ✅ Verified | PE header |
| SizeOfImage | 0x835000 (8,605,696 bytes) | ✅ Verified | PE header |
| Subsystem | 2 (Windows GUI) | ✅ Verified | PE header |
| DllCharacteristics | 0x0000 | ✅ Verified | PE header |

## Sections

| Section | Raw offset | VA | Virtual size | Raw size | Permissions | Confidence |
|---------|-----------|-----|--------------|----------|-------------|------------|
| .text | 0x1000 | 0x00401000 | 0x131570 | 0x132000 | R-X (code) | ✅ Verified |
| .rdata | 0x133000 | 0x00533000 | 0x0028E6 | 0x003000 | R-- (read-only) | ✅ Verified |
| .data | 0x136000 | 0x00536000 | 0x6FCCB8 | 0x01B000 | RW- (initialized) | ✅ Verified |
| .rsrc | 0x151000 | 0x00C33000 | 0x001E40 | 0x002000 | R-- (resources) | ✅ Verified |

Note the `.data` section is unusual: its virtual size (0x6FCCB8, ~7.3 MB) is far larger
than its raw size (0x1B000, 108 KB). The engine reserves a large BSS-like region there
for its runtime heap and asset tables, which is why `SizeOfImage` is 8.6 MB for a
1.39 MB executable.

## DLL Imports

| DLL | Key Functions | Purpose | Confidence |
|-----|--------------|---------|------------|
| KERNEL32.dll | CreateFileA, ReadFile, WriteFile, VirtualAlloc, LoadLibraryA, GetProcAddress | OS/file/memory management | ✅ Verified |
| USER32.dll | CreateWindowExA, PeekMessageA, TranslateMessage, DispatchMessageA | Window management | ✅ Verified |
| GDI32.dll | GetDeviceCaps, CreateICA, DeleteDC | GDI fallback | ✅ Verified |
| DDRAW.dll | DirectDrawCreateEx, DirectDrawEnumerateExA | DirectDraw initialization | ✅ Verified |
| DINPUT.dll | DirectInputCreateA, DirectInputCreateEx | Input devices | ✅ Verified |
| DSOUND.dll | (ordinal 1) | DirectSound | ✅ Verified |
| WINMM.dll | mixer*, mciSendCommandA | Audio mixing | ✅ Verified |
| AVIFIL32.dll | AVIFileInit, AVIFileOpenA, AVIStreamRead | Video playback | ✅ Verified |
| MSVFW32.dll | ICLocate, ICDecompress | Video codec | ✅ Verified |
| ole32.dll | CoInitialize, CoCreateInstance | COM (DirectX init) | ✅ Verified |

## Entry Point Analysis

The entry point at 0x004A4F85 performs:
1. SEH frame setup (fs:[0] chain)
2. `GetVersion()` - OS version detection
3. Version parsing into globals (0x9367C0-0x9367C8)
4. `fcn.004a6617` - Likely `__startup` or CRT init
5. `GetCommandLineA()` → stored at 0xC32CB4
6. `fcn.004a61c5` - Module handle init
7. `fcn.004a5f78` - Heap initialization
8. `fcn.004a5ebf` - Lowio initialization
9. `fcn.004a5295` - Stdio initialization
10. `GetStartupInfoA()` - Read startup config
11. Main game initialization loop

**Confidence:** MEDIUM - Reconstructed from disassembly, may have errors.

## Loader architecture

The resource loaders share one infrastructure: an overlay of the on-disk ILFF chunk
header, a renderer method registry, and a texture constructor. All VAs are image VAs in
`IGI.exe` (PE32, imagebase `0x400000`); every row below is ✅ Verified by the cited
instruction. Byte-level container tables: [16-verified-formats](../16-verified-formats/README.md).

### ILFF node overlay

The loader does not copy the container; it overlays a node struct on the raw bytes:

| Node offset | Meaning | On-disk field | Evidence |
|-------------|---------|---------------|----------|
| +0x00 | tag (4CC) | tag | `cmp dword [eax], esi` at `0x4b745d` |
| +0x04 | size | size | `mov edx, [esi+4]` at `0x4b7359` |
| +0x08 | align | the raw `type` field (4, or 32 for texture resources) | `mov eax, [esi+8]` at `0x4b7360` |
| +0x0c | next | the raw `total` field | `mov eax, [ecx+0xc]` at `0x4b7338` |
| +0x10 | payload (for 4-byte tags) | | `0x4b7390` |

Helpers:

| VA | Role | Evidence |
|----|------|----------|
| `0x4b7350` | first node = `base + align_up(20, align)` | `add eax, 0x13; and eax, ecx; add eax, esi` |
| `0x4b7330` | next node = `node + [node+0xc]` | `mov eax, [ecx+0xc]; add eax, ecx` |
| `0x4b7390` | payload = `base + align_up((node-base)+16, align)` | `lea eax, [ecx+eax+0xf]; and eax, ~(align-1); add eax, edx` |
| `0x4b7450` | find node by tag | walks the list via `0x4b7330`, `cmp dword [eax], esi` at `0x4b745d` |

The outer `.res` carries a 4-byte `IRES` marker at +0x10 (`cmp eax, 0x53455249` at
`0x4b5e62`), so its first node is at +0x14 = `align_up(20, 4)`.

### Renderer method registry

`fcn.004b0d00` registers a name and returns its index: it scans the name table at
`0xa951e0` (8-byte entries: name pointer + used byte) for a free slot, stores the name
(`mov dword [eax*8 + 0xa951e0], ecx` at `0x4b0d30`) and marks it used
(`mov byte [eax*8 + 0xa951e4], 1` at `0x4b0d37`). Implementations live in the table at
`0xa955e4`, dispatched by index (`call dword [ecx*4 + 0xa955e4]`).

The texture callbacks registered at `0x4b2030`-`0x4b20f1`:

| Callback | Index global | Index stored at |
|----------|--------------|-----------------|
| `AllocTexture` | `0x5476f8` | `0x4b204e` |
| `DeAllocTexture` | `0x5476fc` | `0x4b205d` |
| `DownloadTexture` | `0x547700` | `0x4b206c` |
| `BeginTextureList` | `0x5476f0` | `0x4b207b` |
| `EndTextureList` | `0x5476f4` | `0x4b208a` |
| `GetTMUs` | `0x547704` | `0x4b2099` |
| `SetActiveTMU` | `0x547708` | `0x4b20a8` |
| `GetActiveTMU` | `0x54770c` | `0x4b20b7` |
| `RefreshTexture` | `0x5476ec` | `0x4b20c6` |
| `ReloadTexture` | `0x5476e8` | `0x4b20d5` |
| `GetTextureSize` | `0x5476e4` | `0x4b20e4` |
| `SetLOD` | `0x5476e0` | `0x4b20f1` |

Each row is `push str.<name>; call 0x4b0d00; mov [<index global>], eax`; the teardown at
`0x4b2100`-`0x4b2194` unregisters them through `0x4b0d40`.

### Texture constructor

`fcn.004b2260` builds a 12-dword struct and dispatches `AllocTexture` then
`DownloadTexture`:

| Struct offset | Field | Source |
|---------------|-------|--------|
| +0x00 | out record | arg1 (`mov [esp+4], edx` at `0x4b2294`) |
| +0x04 | block | arg2 (`mov [esp+8], eax` at `0x4b228c`) |
| +0x08 | scale level | arg7 (`mov [esp+0xc], edx` at `0x4b22d1`) |
| +0x0c | stride | arg3 (`mov [esp+0x10], eax` at `0x4b22a0`) |
| +0x10 | 0 | zeroed by `rep stosd` at `0x4b227a` |
| +0x14 | 0 | zeroed by `rep stosd` at `0x4b227a` |
| +0x18 | width | arg4 (`mov [esp+0x1c], ecx` at `0x4b2284`) |
| +0x1c | height | arg5 (`mov [esp+0x20], edx` at `0x4b22af`) |
| +0x20 | format | arg6 (`mov [esp+0x24], ecx` at `0x4b229c`) |
| +0x24 | arg8 | arg8 (`mov [esp+0x28], eax` at `0x4b22b7`) |
| +0x28 | global byte | `movsx ecx, byte [0x94428c]` at `0x4b22a4` |
| +0x2c | pixels | arg9 (`mov [esp+0x30], edx` at `0x4b22bb`) |

Dispatch: `mov ecx, [0x5476f8]` / `call dword [ecx*4 + 0xa955e4]` at `0x4b22d6`
(`AllocTexture`), then `mov eax, [0x547700]` / `call dword [eax*4 + 0xa955e4]` at
`0x4b22e7` (`DownloadTexture`, passed `&struct+4`).

## Memory Layout (Inferred from debugging)

| Area | Address | Size | Purpose | Confidence |
|------|---------|------|---------|------------|
| Code | 0x00401000 | 1.2MB | Executable code | ✅ Verified |
| Read-only data | 0x00533000 | 12KB | Constants | ✅ Verified |
| Initialized data | 0x00536000 | 110KB | Global variables | ✅ Verified |
| Heap area 1 | 0x1000000 | 16MB | Unknown | LOW - Inferred |
| Heap area 2 | 0x2000000 | 32MB | Unknown | LOW - Inferred |
| Heap area 3 | 0x4000000 | 64MB | Unknown | LOW - Inferred |

**Note:** Heap area addresses are inferred from memory patterns during debugging, not confirmed from source.

## Anti-Piracy

| Check | Status | Confidence | Method |
|-------|--------|------------|--------|
| CD check | Not found | LOW | Absence of evidence |
| Serial check | Not found | LOW | Absence of evidence |
| File checks | Simple file existence | LOW | Inferred from strings |

**Note:** "No CD check found" does not mean none exists - the search methodology was not comprehensive.

## String Analysis

### Error Messages Found

```
"This application requires DirectX version %d.%d or greater to run."
"No D3D drivers with hardware acceleration found."
"Could not create config file %s."
"Unable to create HumanAIConfig task"
"No configuration found for AIType: #%d, Difficulty: #%d"
"No active playerprofile found"
"The mission ID %d does not exist."
"Mission_Open(): Couldn't load script: %s"
"WeaponType_Open(): Couldn't load script: %s"
"HumanPlayer_LoadParameters: Couldn't load script '%s'"
"Couldn't create DirectDraw object"
"Couldn't create Direct3D device"
"Error occured during rendering"
"Bone model too large. Model %s has %d vertices."
```

**Method:** String extraction from .rdata section.

## References

- PE-bear: Header analysis
- Ghidra: Disassembly
- String extraction: .rdata section
