# IGI Reverse Engineering

Reverse engineering documentation for **Project IGI** (1999) by Innerloop Studios.

**Updated revision.** A substantially deeper pass over the original write-up: every
format claim is now anchored to the loader code in `IGI.exe` (see the
[loader map](reverse/docs/16-verified-formats/README.md#igiexe-loader-map)), reproduced
by parsers that print the pass counts quoted in the docs
(`reverse/tools/verify_all.py`), and stress-tested against rival interpretations
(`reverse/tools/adversarial_checks.py`). The weapon damage formula and the world scale
(4096 units = 1 m) are recovered. [STATUS.md](reverse/docs/STATUS.md) tracks what is
proven, partial, and still open.

**Platform.** Developed and verified on **Linux (x86-64)**, which is the best-suited
platform for this kind of work (radare2, binutils and the usual RE tooling are happiest
there). The tooling is pure Python 3 (standard library only, no POSIX-specific calls),
so it is expected to run on Windows and macOS as-is - but **only Linux has been
tested**, so some scripts may need porting; reports are welcome. `reverse/tools/exe_dis.py`
additionally needs `radare2` on `PATH`. The shell examples below use bash and `7z`.

## What's Here

### Documentation (16 sections)
- File format specifications with byte-level details
- Game structure analysis
- Executable reverse engineering
- AI, weapons, terrain, and rendering docs

### Tooling
- `reverse/tools/igi_formats.py` - parsers for ILFF, `.bit`, `.hmp`, `.ctr`, `.cmd`,
  `.lmp` and MEF models
- `reverse/tools/cmd_deep.py` - deep `.ctr` + `.cmd` decoder (tile tree with commands)
- `reverse/tools/loop.py` - LOOP texture decoder (writes PNG, stdlib only)
- `reverse/tools/loop_headers.py` - LOOP container header dumper (versions, scale levels)
- `reverse/tools/mef_deep.py` - MEF vertex-layout probe (the 40/32-byte stride split)
- `reverse/tools/nav_mtp.py` - navigation graph and `.mtp` manifest decoders
- `reverse/tools/misc.py` - ILSF-to-WAV, `.iff`, `.fnt` and menu `.res` decoders
- `reverse/tools/qvm.py` - QVM bytecode disassembler
- `reverse/tools/qvmdec.py` - readable decompiler for QVM data scripts
- `reverse/tools/langdump.py` - dumps the localisation resources (mission names, menus)
- `reverse/tools/exe_dis.py` - IGI.exe static-disassembly harness (radare2 wrapper:
  disassemble, xrefs, byte search)
- `reverse/tools/verify_formats.py` - runs every parser over an extracted game tree and
  prints the pass counts quoted in the docs
- `reverse/tools/adversarial_checks.py` - runs the strongest rival interpretation
  against each format claim
- `reverse/tools/verify_all.py` - the single end-to-end gate: every decoder over the
  whole tree
- `reverse/tools/mdf2iso.py` - converts the retail `.mdf` CD image to a plain ISO so the
  game tree can be extracted

### Decoded data
- `reverse/data/lod_table.tsv` - 462 models with their LOD distances and cutoff
- `reverse/data/config_options.tsv` - the shipped `config.qvm` defaults
- `reverse/data/weapon_table.tsv` - all 24 weapons with their 50 parameters
- `reverse/data/weapon_parameters.tsv` - the weapon parameter declaration

The tools take the extracted game tree as an argument; the default is
`reverse/extracted/pc` (gitignored), so pass your own path if the tree lives elsewhere.

```bash
python3 reverse/tools/mdf2iso.py "Project IGI.mdf" project_igi.iso
7z x project_igi.iso -oextracted 'pc/*'
python3 reverse/tools/verify_all.py /path/to/extracted/pc
python3 reverse/tools/verify_formats.py /path/to/extracted/pc
python3 reverse/tools/adversarial_checks.py /path/to/extracted/pc
python3 reverse/tools/loop.py /path/to/terrain.tex out/
python3 reverse/tools/qvm.py /path/to/mission.qvm
python3 reverse/tools/langdump.py /path/to/extracted/pc/language/english
python3 reverse/tools/exe_dis.py func 0x4bce60   # QVM interpreter loop
```

## Documentation

| Section | Topic | Confidence | Key Unknowns |
|---------|-------|------------|--------------|
| 01-overview | Game info, structure | MEDIUM | Difficulty ratings inferred |
| 02-executable | PE analysis, memory | HIGH | Loader map verified; runtime memory layout inferred |
| 03-scripting | QVM bytecode | HIGH | Reversed numbering, `PUSHA` intent |
| 04-rendering | Graphics pipeline | HIGH | Model vertex + texture formats verified; pipeline order open |
| 05-ai-system | NPC behavior | MEDIUM | Behaviour architecture inferred; navigation verified |
| 06-weapons | Weapon data | HIGH | Internal damage-path details |
| 07-terrain | Heightmap, tiles | HIGH | All terrain formats verified |
| 08-resources | ILFF format | HIGH | Container fully verified |
| 09-audio | Sound system | HIGH | Container + encodings verified |
| 10-menus | Menu system | MEDIUM | Hierarchy reconstructed |
| 11-task-system | Task types | MEDIUM | Descriptions inferred |
| 12-level-system | Mission structure | MEDIUM | Loading sequence inferred |
| 13-implementation | Implementation notes | - | See STATUS.md |
| 14-lod-system | LOD distances | MEDIUM | LOD 4 semantics (billboard vs low-poly) |
| 15-configuration | Config options | HIGH | Runtime values unverified |
| 16-verified-formats | Byte-level verified specs | HIGH | Evidence for every claim |

**See [INDEX.md](reverse/docs/INDEX.md) for complete reference.**

## Status

| Component | Status |
|-----------|--------|
| File formats | ✅ Container, terrain, model, texture, bytecode, audio, font, navigation, manifest and animation formats verified |
| Game structure | ⚠️ Partially mapped |
| Executable analysis | ✅ Verified (PE header + loader map) |
| AI system | ⚠️ Partially documented |
| Weapons | ✅ Parameters + damage model verified |
| Terrain | ✅ Formats verified |
| Resources | ✅ Container verified |
| Scripting | ✅ Bytecode verified |
| Audio | ✅ Container + encodings verified |
| Menus | ⚠️ Partially documented |
| Tasks | ⚠️ Partially documented |
| Levels | ⚠️ Partially documented |
| LOD | ⚠️ Partially documented |
| Configuration | ⚠️ Partially documented |

## Quick Start

### View Documentation
```bash
ls reverse/docs/
```

### Verify the format claims
```bash
python3 reverse/tools/verify_formats.py /path/to/extracted/pc
```

## File Formats

| Format | Status | Notes |
|--------|--------|-------|
| ILFF | ✅ Verified | Container; 92/92 archives parse cleanly |
| LOOP | ✅ Verified | Texture archive; 8,232 textures decoded, 0 exceptions |
| MEF | ✅ Vertex layout verified | 40-byte vertex (6,178 models) / 32-byte (617), proven by unit-length normals |
| BIT | ✅ Verified | 256-slot descriptor table + bit-packed arrays |
| CTR | ✅ Verified | 32-byte tile-tree records |
| CMD | ✅ Verified | Byte stream addressed by `.ctr` offsets; indices + packed vertices proven |
| LMP | ✅ Verified | Size-prefixed 8-bit greyscale images |
| HMP | ✅ Verified | 256-slot descriptor table + `(size+1)^2` byte grids |
| DAT | ✅ Verified | Navigation routing table `[destination][source] = {next_hop, distance}` |
| MTP | ✅ Verified | Level manifest; `INST` = model_index + texture_count + gtt_index[] |
| ILSF | ✅ Verified | Audio container; 759/759 payloads |
| IFF | ✅ Verified | Skeletal animation; SLERP playback chain |
| FNT | ✅ Verified | 154/154 glyphs; `TRAN` map verified |
| QVM | ✅ Verified | Bytecode; 997/997 files disassemble clean |

## Structure

```
igi/
└── reverse/
    ├── docs/              # Documentation (16 sections)
    │   ├── INDEX.md       # Complete reference
    │   ├── STATUS.md      # What we know vs don't know
    │   ├── 16-verified-formats/   # Byte-level verified specs + evidence
    │   └── ...
    ├── tools/             # 15 tools; see Tooling above
    │   ├── igi_formats.py
    │   ├── loop.py
    │   ├── qvm.py
    │   ├── mdf2iso.py
    │   ├── verify_formats.py
    │   ├── adversarial_checks.py
    │   └── verify_all.py
    └── extracted/         # (gitignored) game files
```

## Related research

- **[heaven-hm/project-igi-research-data](https://github.com/heaven-hm/project-igi-research-data)** -
  please check it out. Runtime analysis (a Cheat Engine table with live pointer chains,
  a Ghidra database, the natives list), format documentation for IGI1 and IGI2, 010
  Editor templates and a tool index, plus a web portal at
  [project-igi-research.vercel.app](https://project-igi-research.vercel.app/). The
  cross-check against it added the player difficulty scaling (0.75 / 1.0 / 1.25) and
  the second gravity handler to this repo.

## Legal

- **No game assets included**
- Format analysis performed against a legally owned retail copy
- For educational purposes
- Users must own original game
- See [LICENSE](LICENSE) for details

## Credits

Original game: **Project IGI** (1999) by Innerloop Studios

Independent research project for game preservation.
