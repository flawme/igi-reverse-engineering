# 08 - Resource System (ILFF)

## Overview

ILFF (InterLeaf File Format?) is a container format used for game resources. The exact origin of the format name is unknown - "InterLeaf" is a guess based on the filename.

**Confidence:** HIGH for container structure, MEDIUM for nested archives.

## ILFF Header

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Magic: "ILFF" (0x494C4646) | HIGH | Hex dump |
| 0x04 | 4 | Total file size | HIGH | Hex dump |
| 0x08 | 4 | Sub-format ID (typically 0x04) | MEDIUM | Hex dump |

**Note:** The magic bytes are "ILFF" in ASCII, which is 0x494C4646 in little-endian.

## Chunk Structure

### IRESNAME Entry

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Chunk ID: "IRESNAME" | HIGH | Hex dump |
| 0x04 | 4 | Chunk size | HIGH | Hex dump |
| 0x08 | var | "NAME" sub-chunk with path string | HIGH | Hex dump |

### NAME Entry

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Chunk ID: "NAME" | HIGH | Hex dump |
| 0x04 | 4 | Chunk size | HIGH | Hex dump |
| 0x08 | var | Null-terminated path string | HIGH | Hex dump |

### BODY Entry

| Offset | Size | Description | Confidence | Method |
|--------|------|-------------|------------|--------|
| 0x00 | 4 | Chunk ID: "BODY" | HIGH | Hex dump |
| 0x04 | 4 | Chunk size | HIGH | Hex dump |
| 0x08 | var | Raw resource data | HIGH | Hex dump |

## Resource Types

| Archive | Content | Count | Confidence | Method |
|---------|---------|-------|------------|--------|
| level1_tex.res | Texture definitions (.tex references) | ~100+ | MEDIUM | File analysis |
| level1_models.res | 3D models (.mef references) | ~50+ | MEDIUM | File analysis |
| lightmap1.res | Lightmap textures (.olm references) | ~100+ | MEDIUM | File analysis |
| menusystem.res | Menu textures and sprites | Unknown | LOW | Filename only |
| computer.res | HUD/computer sprites | Unknown | LOW | Filename only |
| status.res | Status screen resources | Unknown | LOW | Filename only |

## Parsing Algorithm

**Warning:** The following Rust code is a proposed parser, not extracted from the engine. It may work for simple cases but could fail on edge cases.

```rust
fn parse_ilff(data: &[u8]) -> Result<Vec<Chunk>> {
    let mut chunks = Vec::new();
    let mut offset = 0;

    // Read header
    let magic = read_u32(data, offset)?;
    if magic != 0x494C4646 {
        return Err("Invalid ILFF magic");
    }
    offset += 4;

    let file_size = read_u32(data, offset)?;
    offset += 4;

    let sub_format = read_u32(data, offset)?;
    offset += 4;

    // Read chunks
    while offset < file_size as usize {
        let chunk_id = read_u32(data, offset)?;
        offset += 4;

        let chunk_size = read_u32(data, offset)?;
        offset += 4;

        let chunk_data = &data[offset..offset + chunk_size as usize];
        offset += chunk_size as usize;

        chunks.push(Chunk {
            id: chunk_id,
            size: chunk_size,
            data: chunk_data.to_vec(),
        });
    }

    Ok(chunks)
}
```

**Confidence:** MEDIUM - This parser handles basic cases but may fail on:
- Padding bytes between chunks
- Nested ILFF archives
- Edge cases in chunk alignment

## Resource Path Prefixes

| Prefix | Purpose | Example | Confidence | Method |
|--------|---------|---------|------------|--------|
| LOCAL: | Game installation directory | LOCAL:textures/000_01_1.tex | HIGH | String analysis |
| MISSION: | Mission-specific files | MISSION:sounds/ | HIGH | String analysis |
| LANGUAGE: | Localized text resources | LANGUAGE:messages.res | HIGH | String analysis |
| COMPUTER: | HUD/computer sprites | COMPUTER:h_camera.spr | HIGH | String analysis |
| STATUSSCREEN: | Status screen resources | STATUSSCREEN:weapon.spr | HIGH | String analysis |

## File Sizes (Observed)

| Archive | Size | Confidence | Method |
|---------|------|------------|--------|
| level1_tex.res | 6,662,688 bytes | HIGH | File listing |
| level1_models.res | 5,029,944 bytes | HIGH | File listing |
| lightmap1.res | 1,668,412 bytes | HIGH | File listing |

## Known Issues

1. **Nested ILFF handling unclear** - How BODY chunks containing nested ILFF archives are parsed is not fully documented
2. **Padding bytes unknown** - Alignment between chunks is not documented
3. **Sub-format ID meaning unknown** - The 0x04 value is observed but its purpose is unclear
4. **Compression/checksums** - No evidence of compression or checksums, but not confirmed

## References

- ILFF specification: Unknown (possibly InterLeaf documentation)
- Container format: 16-byte header + IRESNAME/BODY pairs
- Analysis tools: Hex dump, parser testing
