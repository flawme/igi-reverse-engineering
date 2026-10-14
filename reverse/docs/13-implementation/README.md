# 13 - Implementation Notes

## Status

This section contains notes on what would be required to implement an engine for
Project IGI.

**No plans to continue development.**

## What Would Be Required

### Core Components

| Component | Description | Confidence | Priority |
|-----------|-------------|------------|----------|
| QVM Interpreter | Bytecode VM for scripts | HIGH | Critical |
| ILFF Parser | Container format reader | HIGH | Critical |
| Texture Loader | LOOP format decoder | HIGH | High |
| Model Loader | MEF mesh parser | HIGH | High |
| Terrain Renderer | Heightmap + tile system | HIGH | High |
| AI System | Event-driven behavior trees | LOW | Medium |
| Physics | Collision detection | LOW | Medium |
| Sound | DirectSound integration | HIGH | Medium |
| Input | DirectInput mapping | HIGH | Low |

### Key Challenges

1. **`.cmd` triangle flag / vertex `A`/`B` fields** - the payload is decoded (indices +
   packed vertices); the flag high nibble (material index) and `A`/`B` semantics are
   inferred
2. **`DNER` / `OCEMHSEM` leftover fields** - `+0x7C`/`+0x7E`/DNER `+0x18` are consumed;
   the mesh `+0x0C`..`+0x1C` and render `+0x1A`/`+0x1E` consumers were not located
3. **`cmd_transform[0..7]`** - the unused/present rule is proven; what `0..7` selects is
   not
4. **Behavioral models** - AI, physics are inferred, not verified
5. **Gameplay numbers** - the damage formula and world scale are recovered; health,
   perception and other timing values are not in the files

## Format Confidence Levels

| Format | Confidence | Notes |
|--------|------------|-------|
| ILFF | HIGH | 92/92 archives parse cleanly, 90,893 chunks |
| LOOP v8 (.qvm) | HIGH | 997/997 files disassemble clean, 25 opcodes proven |
| LOOP v9 (.tex) | HIGH | 145/145 descriptor tables contiguous, pixel format proven |
| LOOP v11 | HIGH | 7,199/7,199 size invariants |
| Heightmap (.bit/.hmp) | HIGH | 14/14 and 6/6 consume the file exactly |
| Tile tree (.ctr) | HIGH | 32-byte records, 14/14 aligned |
| Tile commands (.cmd) | HIGH | 13/14 levels 100% offset-valid; indices + packed vertices proven |
| MEF | HIGH | 40-byte vertex proven by unit-length normals |
| Lightmap (.lmp) | HIGH | 14/14 consume the file exactly; 8-bit greyscale |
| QVM | HIGH | Header, sections, encoding and opcode table verified |

## Open Questions

1. **`DNER`/`OCEMHSEM` leftover fields:** mesh `+0x0C`..`+0x1C` and render `+0x1A`/`+0x1E` consumers
2. **`.cmd`:** the triangle flag high nibble and the vertex `A`/`B` semantics (packing proven, semantics inferred)
3. **`cmd_transform[0..7]`:** what the value selects
4. **`TAMC`/`PMTL`:** semantics (record shapes decoded, no consumer located)
5. **`.fnt`:** glyph `+0x24` semantic and the remaining `TRAN` bytes
6. **Animation format:** no `.anm` files ship in the retail tree
7. **Save format / network protocol:** no evidence in the retail tree
8. **NPC statistics:** health, damage, perception values
9. **Performance metrics:** actual measured values

## Implementation Roadmap

### Phase 1: Core Engine
1. QVM Interpreter (opcode table available, `reverse/tools/qvm.py`)
2. ILFF Parser (verified, `reverse/tools/igi_formats.py`)
3. Virtual Filesystem (path prefixes documented)
4. Memory Manager (details unknown)

### Phase 2: Rendering
1. Texture Loader (verified, `reverse/tools/loop.py`)
2. Model Loader (40-byte vertex verified)
3. Terrain Renderer (heightmap, tile tree and lightmaps verified)
4. Lightmap System (storage verified, blend mode unknown)
5. Sprite System (details unknown)
6. Font Renderer (details unknown)

### Phase 3: Game Systems
1. AI System (events/actions documented, behavior unknown)
2. Physics (details unknown)
3. Weapon System (24 weapons, 50 parameters extracted, damage formula recovered)
4. Sound System (DirectSound API documented)
5. Input System (DirectInput API documented)
6. Menu System (MenuManager API documented)

### Phase 4: Content Pipeline
1. Asset Converter (container, terrain, model and texture formats verified)
2. Level Loader (structure documented)
3. Mission System (flow events documented)
4. Save System (format unknown)
5. Cutscene Player (AVI playback documented)

## What Would Improve Documentation

### High Impact
1. Runtime analysis with debugger attached
2. `.cmd` triangle flag / vertex `A`/`B` semantics
3. `DNER` / `OCEMHSEM` leftover field identification (`+0x0C`..`+0x1C`, `+0x1A`/`+0x1E`)
4. `cmd_transform[0..7]` selection

### Medium Impact
5. Level loading order verification
6. NPC behavior verification
7. `TAMC` / `PMTL` semantics
8. `.fnt` glyph `+0x24` semantic and the remaining `TRAN` bytes

### Low Impact
9. Animation format (no `.anm` files ship in the retail tree)
10. Save system format
11. Network protocol
12. Performance profiling

## World scale

**4096 world units = 1 metre** (1 unit = 1/4096 m = 0.000244140625 m). The
entity/physics coordinate space (player, AI, bullets, collision) is a fixed-point
representation of metres with 12 fractional bits. Six independent conversions in
`IGI.exe` (PE32, imagebase `0x400000`) agree on 2^-12:

| # | Conversion | VA | Evidence |
|---|---|---|---|
| a | `"Distance to ground from feet: %.2fm"` debug print | `0x410e10` | `fmul qword [0x5334b0]`; `[0x5334b0]` = 0.000244140625 = 2^-12 |
| b | gravity | `0x40dc74` | `fsub dword [0x53346c]`; `[0x53346c]` = 44.600887 = 9.8 x 4096 / 900, i.e. 9.8 m/s^2 in (1/4096 m) per tick^2 at 30 ticks/s; per-tick damping x0.99 at `0x533470` |
| c | km/h script speeds | `0x4100e0`-`0x410123` | x 4096000 (`[0x5334a4]`) x 9.259259e-06 (`[0x5334a0]`) = 4096/108 = 4096/(3.6 x 30) |
| d | `"Speed Z (m/s)"` debug print | `0x410d3f`, `0x410d48` | x 2^-12 -> m/tick, then x 30.0 -> m/s |
| e | metre script distances | `0x41012e` | `fmul qword [0x533498]` = 4096.0 (0.85 m -> 3481.6) |
| f | weapon Effective Range -> bullet travel | `0x47b5bc`, `0x47b5c2` | `fld dword [ebp+0x650]` x 4096.0 -> `bullet+0x34` (per-tick raycast length) |

The game's own script-level units are metres (distances), km/h (velocities) and
seconds (times); the engine converts them to internal units with the factors above.

**A second gravity path.** The same velocity field (`entity+0x66C`) is also driven by
a second handler, `fcn.004084b0`, which subtracts `84.741692` (`[0x5333f0]` = 18.62
m/s^2 at 30 ticks/s) with **no** damping and then adds an air-control acceleration:
the four input fields at `entity+0x1b8`..`+0x1c4` (compared against 0.0), scaled by
`[0x56e944]` and rotated by the entity's 3x3 orientation matrix at `+0x78`..`+0x94`,
added to `+0x664`/`+0x668`/`+0x66c`. It is reached from the player update (`0x410a26`
-> the dispatch thunk `0x408460`, whose handler table at `0xa97240` is filled at
runtime) and from three direct call sites (`0x40bc29`, `0x40be97`, `0x40e678`). The
damped handler above (`0x40dc41`, site `0x40dc74`) has no direct caller in the binary
- it is reached through a runtime table as well. Both are real; which one runs in
which player state is not determined statically, and the 9.8 m/s^2 constant remains
the one that matches the script-level metre.

**Negative result - `MuzzleVelocity` is dead data.** The weapon table's
`MuzzleVelocity` (`weapon+0x660`) is written by the `DefineWeaponType` handler at
`0x414290` and never read (a byte search for the offset in every addressing form
finds only false positives; the global `0x56f008` is referenced only by the store
itself). It is not a scale anchor - the live bullet-speed field is Effective Range
(`weapon+0x650`).

**Caveat - other coordinate spaces.** The level-script object positions
(`HeightMap`/`TextureModifier` tasks, ~1e7-1e8) and the nav-graph node positions
(~1e4-1e5) are **not** in the 1/4096 m unit; their units were not determined. MEF
model space is consistent with the same unit (corroboration, not proof).

## Skeletal animation playback (.iff)

The `.iff` animation files are consumed by the module at `0x4d2xxx`-`0x4d7xxx`.
Every claim below cites the instruction that proves it.

### Bone objects

`fcn.004d2bc0` (`0x4d2bc0`) creates a bone object for a model slot: it allocates
`bone_count*0x84` bytes for the bone array (`0x4d2c29`) and stores
`0xa54d88 = &skeleton[slot]` (`0x4d2c52`) for the tree builder. `fcn.004d2d20`
(`0x4d2d20`) builds the tree recursively: `PLST[i]` is the parent index (`mov edx,
[ecx+edi*4]` `0x4d2d3f`) and `TLST[i]` is the rest translation (`add ecx, ebp`
`0x4d2d73` -> `bone+8`; the translation length -> `bone+0x14` at `0x4d2da5`).

### Per-frame update and pose sampling

| Function | Role | Evidence |
|---|---|---|
| `fcn.004d49b0` (`0x4d49b0`) | per-frame update: `time += speed` (`+0x28` -> `+0x2c`), wrap/loop, events | `fadd dword [esi+0x2c]` `0x4d49e8`; loop/ping-pong `0x4d4ab4`-`0x4d4ad6` |
| `fcn.004d4c10` (`0x4d4c10`) | event window: collects keys with time in `[tOld, tNew]` | `0x4d4d43 add edx, 0x18` |
| `fcn.004d4fd0` (`0x4d4fd0`) | pose sampler: key search + quaternion SLERP | `0x4d508c`, `0x4d515e`-`0x4d5180`, `0x4d525a`, `0x4d54bd`/`0x4d54ca` |
| `fcn.004d6b90` (`0x4d6b90`) | per-key weight precompute `{angle, sin(angle)}` | `0x4d6c15`, `0x4d6c2f`, `0x4d6c95` |
| `fcn.004d4690` (`0x4d4690`) | BOTD cubic spline -> object transform (40-byte stride) | `0x4d4702 add ebx, 0x28`; `3.0f` at `0x53352c` `0x4d47f9` |

The pose sampler `fcn.004d4fd0` walks 52-byte keys (key time at `+0x10`), stops at
the first key with `time >= t` (`0x4d508c`), computes the blend factor
`(t-t0)/(t1-t0)` (`0x4d515e`-`0x4d5180`) and blends the two quaternions with
`fsin`-weighted terms - a SLERP (`0x4d525a`, `0x4d54bd`/`0x4d54ca`). The output is
a 20-byte record `{quat x,y,z,w; 1-based key index}` (`0x4d5505`, `0x4d550f`).

### Chunk roles

| Chunk | Role | Evidence |
|---|---|---|
| `BOSH[0]` | model slot index (into the 64-slot tables) | `0x4d6672` |
| `BOSH[+4]` | bone count | `0x4d667b` |
| `PLST` | `bone_count` dwords of parent indices | `0x4d2d3f` |
| `TLST` | `bone_count` x 12 bytes of rest translations | `0x4d2d73`, `0x4d2da5` |
| `BALH[0]` | BOAN count | `0x4d6757` |
| `BALH[+4]` | animation slot count | `0x4d6763` |
| `BOAH[0]` | duration (float) | `0x4d67f7` |
| `BOAH[+8]` | animation slot index | `0x4d6806` |
| `BORH[0]` | key count (per bone) | `0x4d697c` |
| `BORD` | keys (52 bytes each) | `0x4d699d` |

Example: `000.iff` has `BOSH[0]=0`, 33 bones, `BALH=[122,247]`, first `BOAN` slot 2,
duration 13248.0.

### Selection and triggering

`entity+0x68` holds the bone object and `entity+0xcfc` the animation index;
`0x453e50` calls `fcn.004d6020` (`0x4d6020`, play) and logs `"Animation #%d not
found"` (`0x53ee28`) on failure. `fcn.004d6020` has 31 callers, split between the AI
layer and the player/weapon layer. `AIEVENT_ANIMATION` is enum value 3 (`0x44f2a6`).

## References

- Byte-level tables: [16-verified-formats](../16-verified-formats/README.md)
- STATUS.md for the complete unknowns list
- Tools: `reverse/tools/`
