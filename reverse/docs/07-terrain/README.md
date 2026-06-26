# 07 - Terrain System

## File Types

| Extension | Purpose | Size (Level 1) | Confidence | Method |
|-----------|---------|----------------|------------|--------|
| .BIT | Heightmap vertex data | 71,552 bytes | HIGH | Hex dump |
| .CMD | Tile commands/materials | 508,696 bytes | MEDIUM | File size only |
| .CTR | Tile center coordinates | 352,704 bytes | MEDIUM | Hex dump |
| .LMP | Lightmap textures | 461,360 bytes | LOW | File size only |
| .TEX | Terrain texture package | 590,764 bytes | HIGH | Hex dump |
| .HMP | Heightmap (alternate) | Varies by level | LOW | Filename only |
| .QVM | Terrain script | 12,733 bytes | HIGH | Hex dump |

## Heightmap (.BIT)

### Entry Format (16 bytes)

| Offset | Size | Type | Description | Confidence | Method |
|--------|------|------|-------------|------------|--------|
| 0x00 | 4 | float32 | X coordinate | HIGH | Hex dump |
| 0x04 | 4 | float32 | Y coordinate (height) | HIGH | Hex dump |
| 0x08 | 4 | float32 | Z coordinate | HIGH | Hex dump |
| 0x0C | 4 | uint32 | Flags | MEDIUM | Hex dump |

**Note:** The flag meanings are inferred, not confirmed from source.

### Flag Bits (Inferred)

| Bit | Meaning | Confidence | Method |
|-----|---------|------------|--------|
| 0 | Solid? | LOW | Guess |
| 1 | Water? | LOW | Guess |
| 2 | Bridge? | LOW | Guess |
| 3 | Road? | LOW | Guess |
| 4-5 | Unknown | ❌ | Unknown |
| 6-31 | Reserved? | LOW | Assumption |

### Grid Dimensions (Estimated)

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Width | 256 or 512 | LOW | File size analysis |
| Height | 256 or 512 | LOW | File size analysis |
| Tile size | 64x64 | MEDIUM | File structure |

**Note:** Grid dimensions are inferred from file size, not confirmed.

### Coordinate System (Guessed)

| Axis | Direction | Confidence | Method |
|------|-----------|------------|--------|
| X | East | LOW | Standard convention |
| Y | Up | LOW | Standard convention |
| Z | South | LOW | Standard convention |

## Tile Centers (.CTR)

### Entry Format (52 bytes)

| Offset | Size | Type | Description | Confidence | Method |
|--------|------|------|-------------|------------|--------|
| 0x00 | 2 | uint16 | X coordinate | MEDIUM | Hex dump |
| 0x02 | 2 | uint16 | Y coordinate | MEDIUM | Hex dump |
| 0x04 | 2 | uint16 | Z coordinate | MEDIUM | Hex dump |
| 0x06 | 4 | uint32 | Flags | MEDIUM | Hex dump |
| 0x0A | 32 | float32[8] | Additional data | LOW | Hex dump |
| 0x2A | 4 | ? | Unknown | ❌ | Unknown |

### Flag Bits (Inferred)

| Bit | Meaning | Confidence | Method |
|-----|---------|------------|--------|
| 0 | Visible? | LOW | Guess |
| 1 | Collision? | LOW | Guess |
| 2 | Water? | LOW | Guess |
| 3-31 | Unknown | ❌ | Unknown |

## Tile Commands (.CMD)

**Status:** LARGELY UNKNOWN

The .CMD file contains tile command data, but the binary encoding is not documented. Previous documentation listed command types like "SET_HEIGHT", "SET_TEXTURE", etc., but these are guesses.

| Command | Description | Confidence |
|---------|-------------|------------|
| SET_HEIGHT | Set tile height | LOW - Guessed |
| SET_TEXTURE | Set tile texture | LOW - Guessed |
| SET_FLAGS | Set tile flags | LOW - Guessed |
| SET_LIGHTMAP | Set lightmap | LOW - Guessed |
| ? | Unknown commands | ❌ |

## Lightmap (.LMP)

**Status:** LARGELY UNKNOWN

| Property | Status | Confidence |
|----------|--------|------------|
| Pixel format | Unknown (RGB565? RGB888?) | ❌ |
| Resolution | Unknown (256x256? 512x512?) | ❌ |
| UV mapping | Unknown | ❌ |
| Blending mode | Unknown (multiply? add?) | ❌ |

**Note:** Previous documentation stated specific lightmap properties, but these are unverified guesses.

## Terrain Texture Package (.TEX)

### LOOP v9 Header

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Magic: "LOOP" (0x4C4F4F50) | HIGH | Hex dump |
| 0x04 | 4 | Version: 9 | HIGH | Hex dump |
| 0x08 | 4 | Texture count | HIGH | Hex dump |
| 0x0C | var | 32-byte headers per texture | MEDIUM | Hex dump |

### Texture Headers (32 bytes each)

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Width | MEDIUM | Hex dump |
| 0x04 | 4 | Height | MEDIUM | Hex dump |
| 0x08 | 4 | Flags | LOW | Hex dump |
| 0x0C | 4 | Offset to data | MEDIUM | Hex dump |
| 0x10 | 16 | Unknown | ❌ | Unknown |

### Texture Dimensions (Observed)

| Size | Frequency | Confidence | Method |
|------|-----------|------------|--------|
| 32x32 | Common | HIGH | File analysis |
| 64x64 | Common | HIGH | File analysis |
| 64x32 | Common | HIGH | File analysis |
| 128x128 | Common | HIGH | File analysis |
| 128x256 | Common | HIGH | File analysis |
| 256x256 | Common | HIGH | File analysis |
| 512x512 | Rare | HIGH | File analysis |

### Mip Levels

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Count | 2 (base + 1 mip) | MEDIUM | File analysis |

### Texture Format

**Status:** UNKNOWN

The actual texture pixel format is unknown. Previous documentation suggested D3D7 formats (D3DFMT_A8R8G8B8, D3DFMT_X1R5G5B5), but these are guesses.

## Terrain Parameters (Estimated)

| Parameter | Value | Confidence | Method |
|-----------|-------|------------|--------|
| Grid | 64x64 tile grid per level | MEDIUM | File size analysis |
| Height format | IEEE float32 | HIGH | Hex dump |
| Texture format | LOOP v9 | HIGH | Hex dump |
| Lightmaps | Unknown resolution | ❌ | Not extracted |
| Tile definitions | Material indices (12-bit?) | LOW | Guess |

## Terrain QVM Functions

| Function | Description | Confidence | Method |
|----------|-------------|------------|--------|
| CreateTerrainMaterial | Creates terrain surface materials | MEDIUM | String analysis |
| CreateTerrainTileMap | Generates tile grid from heightmap | MEDIUM | String analysis |

## Rendering (Reconstructed)

**Confidence:** LOW - This is pseudocode showing how one might implement terrain rendering, not how the engine actually does it.

### Mesh Generation (Pseudocode)

```
For each tile in grid:
    If tile is visible (frustum culling):
        Generate quad mesh from heightmap
        Apply texture from atlas
        Apply lightmap
        Render mesh
```

### Index Generation (Pseudocode)

```
For each quad:
    index0 = vertex0
    index1 = vertex1
    index2 = vertex2
    index3 = vertex3
    Add triangle (0, 1, 2)
    Add triangle (1, 2, 3)
```

### Normal Computation (Pseudocode)

```
For each vertex:
    normal = cross product of adjacent edges
    normalize(normal)
```

## World Scale (Estimated)

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Tile size | 10-50 meters | LOW | Guess |
| Max height | 100-500 meters | LOW | Guess |
| World size | 1-10 km | LOW | Guess |

## Rendering Features (Guessed)

| Feature | Status | Confidence | Method |
|---------|--------|------------|--------|
| Frustum culling | Per-tile | LOW | Standard game convention |
| Occlusion | Software-based | LOW | Standard game convention |
| LOD | Distance-based | LOW | Standard game convention |

## Known Issues

1. **Heightmap flags unknown** - Bit meanings are guesses
2. **Tile commands undocumented** - Binary encoding unclear
3. **Lightmap format unknown** - Pixel format, UV mapping unknown
4. **Texture mapping unknown** - UV coordinates not documented
5. **World scale unknown** - Actual dimensions unverified

## References

- Terrain files: MISSIONS/LOCATI~1/{MISSION}/TERRAIN/
- Texture format: LOOP v9 specification
- Heightmap format: 16 bytes per vertex
