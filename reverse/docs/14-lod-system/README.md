# 14 - LOD System

## Overview

Level of Detail (LOD) system for model rendering. Approximately 400 models defined in LOD.QVM.

**Confidence:** MEDIUM - Model count is estimated from file analysis.

## LOD Settings Format (Reconstructed)

**Confidence:** LOW - This structure is reconstructed from common game patterns, not extracted from source.

```
ModelLODSettings
  Model: String16 (model name)
  Distance to LOD 1: Real32
  Distance to LOD 2: Real32
  Distance to LOD 3: Real32
  Distance to LOD 4: Real32
  Distance to cutoff: Real32
```

## Model Categories (Inferred)

| Range | Category | Confidence | Method |
|-------|----------|------------|--------|
| 100-140 | Player/items | LOW | ID pattern guess |
| 200-245 | Buildings/architecture | LOW | ID pattern guess |
| 300-368 | Vegetation/terrain details | LOW | ID pattern guess |
| 400-472 | Vehicles | LOW | ID pattern guess |
| 500-506 | Effects/explosions | LOW | ID pattern guess |
| 600-622 | NPC characters | LOW | ID pattern guess |
| 700-716 | Complex multi-part objects | LOW | ID pattern guess |
| 900-905 | Special models | LOW | ID pattern guess |

**Note:** These category ranges are guesses based on ID patterns, not confirmed from game data.

## LOD Levels (Guessed)

| Level | Description | Typical Distance | Confidence | Method |
|-------|-------------|------------------|------------|--------|
| LOD 0 | Full detail | 0-50m | LOW | Standard game convention |
| LOD 1 | Medium detail | 50-100m | LOW | Standard game convention |
| LOD 2 | Low detail | 100-200m | LOW | Standard game convention |
| LOD 3 | Very low detail | 200-400m | LOW | Standard game convention |
| LOD 4 | Billboard/sprite | 400m+ | LOW | Standard game convention |
| Cutoff | Not rendered | 500m+ | LOW | Standard game convention |

**Note:** These distance thresholds are typical values for games of this era. The actual distances are unknown.

## Known Issues

1. **LOD format unverified** - Structure is reconstructed, not extracted
2. **Distance thresholds unknown** - Actual values not measured
3. **Category ranges unverified** - ID patterns are guesses
4. **Model count estimated** - Not confirmed

## References

- LOD data: LOD.QVM
- ~400 model definitions (estimated)
