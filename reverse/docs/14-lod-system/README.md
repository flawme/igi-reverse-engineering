# 14 - LOD System

**Status: solved.** `pc/lod.qvm` decodes to a complete per-model LOD table. The
structure guessed in earlier revisions of this document was correct in shape; the
values are now extracted rather than assumed.

## LOD Settings Format ✅ VERIFIED

`lod.qvm` is a QVM script that calls `DefineLODModel` once per model. Each call carries:

| Field | Type | Meaning |
|-------|------|---------|
| Model | String16 | model name, e.g. `300_01_1` |
| Distance to LOD 1 | Real32 | |
| Distance to LOD 2 | Real32 | |
| Distance to LOD 3 | Real32 | |
| Distance to LOD 4 | Real32 | |
| Distance to cutoff | Real32 | beyond this the model is not drawn |

**462 models**, not the ~400 previously estimated. The full table is at
`reverse/data/lod_table.tsv` (model, lod1, lod2, lod3, lod4, cutoff).

Sample rows:

| Model | LOD 1 | LOD 2 | LOD 3 | LOD 4 | Cutoff |
|-------|-------|-------|-------|-------|--------|
| 300_01_1 | 7.0 | 17.0 | 30.0 | 35.0 | 50.0 |
| 301_01_1 | 25.0 | 45.0 | 45.0 | 45.0 | 80.0 |
| 302_01_1 | 5.0 | 15.0 | 25.0 | 35.0 | 200.0 |
| 306_01_1 | 15.0 | 20.0 | 25.0 | 30.0 | 125.0 |
| 307_01_1 | 5.0 | 7.0 | 10.0 | 10.0 | 30.0 |
| 308_01_1 | 7.0 | 10.0 | 10.0 | 10.0 | 60.0 |

The distances are per-model, not global - a small prop cuts off at 30 units while a
large structure can stay visible to 200. The earlier "LOD 0 = 0-50m, LOD 1 = 50-100m,
..." table was invented and does not match the data.

## Model Categories

The model-ID prefix groups are real (they are the first component of the model name),
but the *category names* previously attached to them were guesses. The verified
grouping is simply the prefix distribution in the table:

| Prefix range | Count | Previously guessed as |
|--------------|-------|------------------------|
| 000-099 | 20 | (not listed) |
| 100-199 | ~30 | Player/items |
| 200-299 | ~40 | Buildings/architecture |
| 300-399 | ~60 | Vegetation/terrain details |
| 400-499 | ~60 | Vehicles |
| 500-599 | ~30 | Effects/explosions |
| 600-699 | ~40 | NPC characters |
| 700-799 | ~30 | Complex multi-part objects |
| 900-999 | ~10 | Special models |

To attach a real name to a prefix, cross-reference the model name against the level
manifests (`levelN.dat`) and the `.mtp` `MODS` list, which name the same models.

## Known Issues

1. **Category names** - the prefix groups are real, the semantic labels are not proven.
2. **LOD 4 semantics** - whether LOD 4 is a billboard, a sprite or a low-poly mesh is
   not established by the data.

## References

- LOD data: `pc/lod.qvm`
- Full table: `reverse/data/lod_table.tsv`
- Decoder: `reverse/tools/qvmdec.py`
