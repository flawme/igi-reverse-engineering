# 04 - Rendering System

## Technology Stack

| Component | Technology | Confidence | Method |
|-----------|------------|------------|--------|
| Primary API | Direct3D 7 | HIGH | DLL import analysis |
| Backend | DirectDraw 7 | HIGH | DLL import analysis |
| Fallback | GDI (CreateICA) | HIGH | DLL import analysis |
| Texture Management | Custom allocator | MEDIUM | Inferred from function names |

## Rendering Pipeline (Reconstructed)

**Confidence:** LOW - Pipeline order is inferred from standard practices, not verified from source.

1. DirectDraw object creation (`DirectDrawCreateEx`)
2. Cooperative level setup
3. Device enumeration (`DirectDrawEnumerateExA`)
4. D3D device creation
5. Texture allocation and download
6. Render state configuration
7. Scene begin/end
8. Sort rendering (transparency, BSP)
9. Terrain mesh rendering
10. Model rendering (rigid, bone, sprite)
11. Lightmap compositing
12. Fog application

## Vertex Formats (Reconstructed)

**Warning:** These vertex formats are guesses based on standard D3D7 patterns. They have NOT been verified from the actual game files.

### TerrainVertex (Guessed)

```c
struct TerrainVertex {
    float x, y, z;     // Position (offset 0)
    float u, v;         // Texture coordinates (offset 12)
    float nx, ny, nz;   // Normal (offset 20)
};
// Total: 32 bytes per vertex
```

**Confidence:** LOW - This is a reconstruction, not extracted from source.

### ModelVertex (Guessed)

```c
struct ModelVertex {
    float x, y, z;     // Position (offset 0)
    float nx, ny, nz;   // Normal (offset 12)
    float u, v;         // Texture coordinates (offset 24)
};
// Total: 32 bytes per vertex
```

**Confidence:** LOW - This is a reconstruction, not extracted from source.

## Index Format

**Status:** UNKNOWN

The index format (u16 or u16) is not confirmed. The document previously stated "16-bit indices (u16)" but this is unverified.

## Texture Formats

| Format | D3D Constant | Description | Confidence |
|--------|--------------|-------------|------------|
| RGBA8888 | D3DFMT_A8R8G8B8 | 32-bit with alpha | LOW - Common format guess |
| RGB888 | D3DFMT_X8R8G8B8 | 32-bit no alpha | LOW - Common format guess |
| RGB565 | D3DFMT_R5G6B5 | 16-bit no alpha | LOW - Common format guess |
| RGBA4444 | D3DFMT_A4R4G4B4 | 16-bit with alpha | LOW - Common format guess |

**Note:** These are standard D3D7 texture formats. The actual formats used by the game are unknown.

## Lighting (Reconstructed)

### Light Types

| Type | Count | Confidence | Method |
|------|-------|------------|--------|
| Ambient | 1 | LOW | Standard game convention |
| Directional | 1 | LOW | Standard game convention |
| Point | 0-8 | LOW | Standard game convention |
| Spot | 0 | LOW | Standard game convention |

### Lightmap System

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Resolution | Unknown (256x256 or 512x512 assumed) | LOW | Standard game convention |
| Pixel format | Unknown (RGB565? RGB888?) | ❌ | Not extracted |
| UV mapping | Unknown | ❌ | Not extracted |
| Blending | Unknown (multiply? add?) | ❌ | Not extracted |

**Note:** The lightmap system is largely unknown. Previous documentation stated specific resolutions and formats, but these are unverified guesses.

## Camera (Guessed)

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| FOV | ~75 degrees | LOW | Standard FPS convention |
| Near clip | 0.1 | LOW | Standard game convention |
| Far clip | 10000 | LOW | Standard game convention |

## Fog (Guessed)

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Type | Linear distance fog | LOW | Standard game convention |
| Start | Unknown | ❌ | Not extracted |
| End | Unknown | ❌ | Not extracted |
| Color | Unknown | ❌ | Not extracted |

## Skybox (Guessed)

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Type | 6-face cube map | LOW | Standard game convention |
| Rendering | Rendered at infinity | LOW | Standard game convention |
| Dynamic | No | LOW | Standard game convention |

## Performance Estimates

**Warning:** These are rough estimates, not measured values.

| Metric | Estimate | Confidence | Method |
|--------|----------|------------|--------|
| Fill rate | Unknown | LOW | Not measured |
| Triangle count | ~150K per frame | LOW | Estimate from terrain size |
| Draw calls | ~100-200 per frame | LOW | Estimate from file structure |

## Render States (From D3D7 documentation)

These are standard Direct3D 7 render states. The actual states used by the game are unknown.

### Common Render States

| State | Value | Purpose |
|-------|-------|---------|
| D3DRS_ALPHABLENDENABLE | TRUE | Enable alpha blending |
| D3DRS_SRCBLEND | D3DBLEND_SRCALPHA | Source blend factor |
| D3DRS_DESTBLEND | D3DBLEND_INVSRCALPHA | Destination blend factor |
| D3DRS_ZENABLE | TRUE | Enable Z-buffer |
| D3DRS_ZWRITEENABLE | TRUE | Enable Z-writing |
| D3DRS_CULLMODE | D3DCULL_CCW | Counter-clockwise culling |

### Common Texture States

| State | Value | Purpose |
|-------|-------|---------|
| D3DTSS_COLOROP | D3DTOP_MODULATE | Color operation |
| D3DTSS_COLORARG1 | D3DTA_TEXTURE | Color argument 1 |
| D3DTSS_COLORARG2 | D3DTA_DIFFUSE | Color argument 2 |
| D3DTSS_ALPHAOP | D3DTOP_MODULATE | Alpha operation |
| D3DTSS_MINFILTER | D3DTFN_LINEAR | Minification filter |
| D3DTSS_MAGFILTER | D3DTFN_LINEAR | Magnification filter |

**Note:** These are standard D3D7 configurations, not necessarily what this game uses.

## Texture Management Functions

| Function | Purpose | Confidence | Method |
|----------|---------|------------|--------|
| AllocTexture | Allocate texture memory | HIGH | Symbol analysis |
| DeAllocTexture | Free texture memory | HIGH | Symbol analysis |
| DownloadTexture | Upload to VRAM | HIGH | Symbol analysis |
| ReloadTexture | Reload from disk | HIGH | Symbol analysis |
| RefreshTexture | Update texture data | HIGH | Symbol analysis |
| GetTextureSize | Get memory usage | HIGH | Symbol analysis |

## Render Mode System

```
RenderMode: Failed to create new rendermode '%s'
RenderMode: Failed to create new method '%s'
```

**Method:** Error string extraction from binary.

## Known Issues

1. **Vertex formats unknown** - No vertex layout has been extracted
2. **Pipeline order unverified** - Reconstructed from standard practices
3. **Lightmap format unknown** - Pixel format, UV mapping unclear
4. **Texture formats unverified** - Assumed D3D7 formats, not confirmed
5. **Performance metrics unestimated** - No runtime profiling performed

## References

- Direct3D 7 SDK documentation
- D3D7 render state reference
- Symbol analysis of executable
