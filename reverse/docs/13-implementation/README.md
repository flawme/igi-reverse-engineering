# 13 - Implementation Notes

## Status

This section contains notes on what would be required to implement an engine for Project IGI.

**No plans to continue development.**

## What Would Be Required

### Core Components

| Component | Description | Confidence | Priority |
|-----------|-------------|------------|----------|
| QVM Interpreter | Bytecode VM for scripts | MEDIUM | Critical |
| ILFF Parser | Container format reader | HIGH | Critical |
| Texture Loader | LOOP format decoder | MEDIUM | High |
| Model Loader | MEF mesh parser | LOW | High |
| Terrain Renderer | Heightmap + tile system | MEDIUM | High |
| AI System | Event-driven behavior trees | LOW | Medium |
| Physics | Collision detection | LOW | Medium |
| Sound | DirectSound integration | HIGH | Medium |
| Input | DirectInput mapping | HIGH | Low |

### Key Challenges

1. **MEF vertex format** - Chunk IDs known, vertex layout completely unknown
2. **Texture UV mapping** - No UV coordinates documented
3. **Lightmap format** - Pixel format, UV mapping unknown
4. **QVM opcodes** - Only partially mapped, many opcodes unidentified
5. **Behavioral models** - AI, physics are inferred, not verified

## Format Confidence Levels

| Format | Confidence | Notes |
|--------|------------|-------|
| ILFF | HIGH | Header and chunk structure verified |
| LOOP v8 | HIGH | Header verified, bytecode partially mapped |
| LOOP v9 | HIGH | Header verified, pixel format unknown |
| LOOP v11 | MEDIUM | Similar to v9, less tested |
| Heightmap | HIGH | Entry structure verified, flag meanings unknown |
| MEF | LOW | Nested ILFF structure known, vertex layout unknown |
| Lightmap | LOW | Format completely unknown |
| QVM | MEDIUM | Header verified, opcodes partially mapped |

## Open Questions

1. **QVM opcodes:** Full opcode table needed (only ~20 identified)
2. **Texture formats:** Actual D3D format mapping needed
3. **Model chunks:** OCEMHSEM/DNER structure unknown
4. **Physics:** Vehicle implementation details unknown
5. **Save format:** Game state serialization format unknown
6. **Weapon parameters:** Actual damage, timing, spread values unknown
7. **NPC statistics:** Health, damage, perception values unknown
8. **Performance metrics:** Actual measured values needed

## Implementation Roadmap

### Phase 1: Core Engine
1. QVM Interpreter (partial opcode table available)
2. ILFF Parser (basic structure documented)
3. Virtual Filesystem (path prefixes documented)
4. Memory Manager (details unknown)

### Phase 2: Rendering
1. Texture Loader (LOOP v9 headers documented)
2. Model Loader (MEF vertex format unknown)
3. Terrain Renderer (heightmap documented, lightmap unknown)
4. Lightmap System (format unknown)
5. Sprite System (details unknown)
6. Font Renderer (details unknown)

### Phase 3: Game Systems
1. AI System (events/actions documented, behavior unknown)
2. Physics (details unknown)
3. Weapon System (21 weapons identified, parameters unknown)
4. Sound System (DirectSound API documented)
5. Input System (DirectInput API documented)
6. Menu System (MenuManager API documented)

### Phase 4: Content Pipeline
1. Asset Converter (format partially documented)
2. Level Loader (structure documented)
3. Mission System (flow events documented)
4. Save System (format unknown)
5. Cutscene Player (AVI playback documented)

## What Would Improve Documentation

### High Impact
1. Runtime analysis with debugger attached
2. MEF vertex format extraction
3. Lightmap pixel format identification
4. QVM opcode table completion
5. Weapon parameter extraction from gameplay

### Medium Impact
6. Sound format details (sample rate, bit depth)
7. Navigation graph edge format
8. Level loading order verification
9. NPC behavior verification

### Low Impact
10. Animation format documentation
11. Save system format
12. Performance profiling

## References

- See other doc sections for format specifications
- STATUS.md for complete unknowns list
- Analysis tools: Hex dump, symbol analysis, string analysis
