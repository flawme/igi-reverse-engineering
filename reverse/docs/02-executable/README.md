# 02 - Executable Analysis

## PE Header

| Field | Value | Confidence | Method |
|-------|-------|------------|--------|
| Format | PE32 (GUI) Intel 80386 | ✅ Verified | PE-bear |
| Timestamp | Mon Jul 10 04:36:22 2000 | MEDIUM | PE header (can be spoofed) |
| Linker | MSVC 6.0 (MajorLinkerVersion=6) | ✅ Verified | PE header |
| ImageBase | 0x00400000 | ✅ Verified | PE header |
| EntryPoint | 0x004A4F85 (.text section) | ✅ Verified | PE header |
| SizeOfImage | 0x835000 (8,605,696 bytes) | ✅ Verified | PE header |
| Subsystem | Windows GUI | ✅ Verified | PE header |

## Sections

| Section | File Offset | VA | Size | Permissions | Confidence |
|---------|-------------|-----|------|-------------|------------|
| .text | 0x1000 | 0x00401000 | 0x132000 (1,253,376) | R-X (code) | ✅ Verified |
| .rdata | 0x133000 | 0x00533000 | 0x3000 (12,288) | R-- (read-only) | ✅ Verified |
| .data | 0x136000 | 0x00536000 | 0x1B000 (110,592) | RW- (initialized) | ✅ Verified |
| .rsrc | 0x151000 | 0x00C33000 | 0x2000 (8,192) | R-- (resources) | ✅ Verified |

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
