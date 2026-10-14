#!/usr/bin/env python3
"""Project IGI (1999, Innerloop Studios) file format parsers.

Every parser in this module was written against the retail game data extracted
from the original CD image and validated by running it over the whole game tree.
The docstrings record the evidence for each field.

Formats covered
---------------
ILFF   .res containers (textures, models, lightmaps, sprites, sounds, menus)
BIT    terrain texture-modifier bitmaps (terrain.bit)
HMP    terrain height maps (terrain.hmp)
CTR    terrain tile tree (terrain.ctr)
CMD    terrain tile command records (terrain.cmd)
LMP    terrain lightmaps (terrain.lmp)
MEF    model files nested inside .res BODY chunks

Usage
-----
    python3 igi_formats.py <file> [file ...]
"""
from __future__ import annotations

import math
import struct
import sys

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def u16(d, off):
    return struct.unpack_from("<H", d, off)[0]


def u32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def i16(d, off):
    return struct.unpack_from("<h", d, off)[0]


def f32(d, off):
    return struct.unpack_from("<f", d, off)[0]


def align4(n):
    return (n + 3) & ~3


def is_ascii_tag(b):
    return len(b) == 4 and all(0x20 <= c < 0x7F for c in b)


# ---------------------------------------------------------------------------
# ILFF container
# ---------------------------------------------------------------------------

ILFF_MAGIC = b"ILFF"


class Chunk:
    """One ILFF chunk.

    Layout (verified byte-for-byte over all 92 .res files in the retail game):

        char[]   id      ASCII tag, null-padded to a 4-byte boundary (4 or 8 bytes)
        uint32   size    payload byte count
        uint32   type    sub-format id; 4 for most resources, 32 for textures
        uint32   total   align4(16 + size) when non-zero; frequently 0
        uint8    payload[size]
        pad to 4-byte alignment

    The next chunk starts at align4(offset + id_field + 12 + extra + size) where
    `extra` is 28 for type-32 (texture) chunks - those carry a 28-byte descriptor
    inside the payload ahead of the resource data.
    """

    __slots__ = ("id", "size", "type", "total", "offset", "payload_off", "id_field", "extra")

    def __init__(self, cid, size, ctype, total, offset, payload_off, id_field, extra=0):
        self.id = cid
        self.size = size
        self.type = ctype
        self.total = total
        self.offset = offset
        self.payload_off = payload_off
        self.id_field = id_field
        self.extra = extra

    @property
    def end(self):
        return align4(self.offset + self.id_field + 12 + self.extra + self.size)

    @property
    def end_total(self):
        return self.offset + self.total if self.total else None

    def payload(self, d):
        return d[self.payload_off:self.payload_off + self.size]

    def __repr__(self):
        return (f"<Chunk {self.id!r} @{self.offset} size={self.size} "
                f"type={self.type} total={self.total} id_field={self.id_field}>")


def _try_chunk(d, off, end):
    if off + 16 > end:
        return None
    id4 = d[off:off + 4]
    if not is_ascii_tag(id4):
        return None
    size = u32(d, off + 4)
    ctype = u32(d, off + 8)
    total = u32(d, off + 12)
    if off + 16 + size <= end and (total == 0 or (16 + size <= total <= end - off)):
        return (id4.decode(), size, ctype, total, 4)
    id8 = d[off:off + 8]
    if is_ascii_tag(id8[4:8]):
        size = u32(d, off + 8)
        ctype = u32(d, off + 12)
        total = u32(d, off + 16)
        if off + 20 + size <= end and (total == 0 or (16 + size <= total <= end - off)):
            return (id8.decode(), size, ctype, total, 8)
    return None


def parse_ilff(d):
    """Parse an ILFF container.

    Returns (info, errors). `info` is None when the magic is wrong.
    info = {file_size, sub_format, chunks, end, errors}
    """
    errors = []
    if d[:4] != ILFF_MAGIC:
        return None, ["not an ILFF file"]
    file_size = u32(d, 4)
    sub_format = u32(d, 8)
    end = min(len(d), file_size)
    off = 16
    chunks = []
    while off + 16 <= end:
        c = _try_chunk(d, off, end)
        if c is None:
            errors.append(f"@{off}: no valid chunk header {d[off:off + 16].hex(' ')}")
            break
        cid, size, ctype, total, id_field = c
        extra = 28 if ctype == 32 else 0
        ch = Chunk(cid, size, ctype, total, off, off + id_field + 12, id_field, extra)
        nxt = ch.end
        if nxt > end or (nxt < end and _try_chunk(d, nxt, end) is None and ch.end_total):
            if ch.end_total and ch.end_total <= end:
                nxt = ch.end_total
        if nxt > end:
            if ch.payload_off + size <= end:
                chunks.append(ch)
                off = ch.payload_off + size
                break
            errors.append(f"@{off}: chunk {cid!r} overruns ({nxt} > {end})")
            break
        chunks.append(ch)
        off = nxt
    return {
        "file_size": file_size,
        "sub_format": sub_format,
        "chunks": chunks,
        "end": off,
        "errors": errors,
    }, errors


# ---------------------------------------------------------------------------
# terrain: .bit / .hmp
# ---------------------------------------------------------------------------

TERRAIN_ITEM_SLOTS = 256  # MAX_TEX_MOD / MAX_HMP in the engine


def parse_bit(d):
    """terrain.bit - texture-modifier bitmaps.

    Layout (verified: computed size == file size for all 14 levels):
        256 x 12-byte descriptors
            uint32 contents   runtime pointer, meaningless on disk
            uint8  unk
            uint8  pad[3]
            uint32 size       bitmap is size x size *bits*
        then, in descriptor order, one bit array of size*size bits (size*size/8
        bytes) for every descriptor with size != 0.

    Returns a list of (size, bytes) with None for empty slots.
    """
    head = TERRAIN_ITEM_SLOTS * 12
    items = []
    off = head
    for i in range(TERRAIN_ITEM_SLOTS):
        size = u32(d, i * 12 + 8)
        if size:
            n = (size * size) // 8
            items.append((size, d[off:off + n]))
            off += n
        else:
            items.append(None)
    return items, off


def parse_hmp(d):
    """terrain.hmp - height maps.

    Layout (verified: computed size == file size for every level that ships one):
        256 x 12-byte descriptors (same shape as .bit)
        then, in descriptor order, one array of (size+1)^2 *bytes* per non-empty
        descriptor - the height map is a (size+1) x (size+1) grid of 8-bit
        heights.
    """
    head = TERRAIN_ITEM_SLOTS * 12
    items = []
    off = head
    for i in range(TERRAIN_ITEM_SLOTS):
        size = u32(d, i * 12 + 8)
        if size:
            n = (size + 1) * (size + 1)
            items.append((size, d[off:off + n]))
            off += n
        else:
            items.append(None)
    return items, off


# ---------------------------------------------------------------------------
# terrain: .ctr / .cmd / .lmp
# ---------------------------------------------------------------------------

CTR_ITEM_SIZE = 32
CMD_ITEM_SIZE = 8


def parse_ctr(d):
    """terrain.ctr - terrain tile tree.

    Layout (verified: 352704 / 32 == 11022 records for level 1):
        int16  children[8]       child tile indices
        int8   cmd_transform[8]  per-child transform selector
        uint8  children_mask     which of the 8 children are present
        uint8  pad[3]
        uint32 cmd_offset        byte offset into terrain.cmd
    """
    n = len(d) // CTR_ITEM_SIZE
    out = []
    for i in range(n):
        o = i * CTR_ITEM_SIZE
        out.append({
            "children": [i16(d, o + 2 * j) for j in range(8)],
            "cmd_transform": list(d[o + 16:o + 24]),
            "children_mask": d[o + 24],
            "cmd_offset": u32(d, o + 28),
        })
    return out


def parse_cmd(d):
    """terrain.cmd - terrain tile command records (variable length).

    Layout (verified: the walk consumes every retail file exactly; level 2 has
    5004 records, level 9 has 5334):
        uint16 num_triangle
        uint16 vertex_offset      == num_triangle * 4
        uint16 num_parent_vertex
        uint16 num_child_vertex
        uint8  triangle[num_triangle][4]   3 x uint8 index + 1 flag byte
        uint8  vertex[num_parent_vertex + num_child_vertex][4]

    Each record is 8 + 4*(num_triangle + num_parent_vertex + num_child_vertex)
    bytes and the file is a flat sequence of records.  A fixed-stride reading
    is wrong: it addresses only ~4% of level 1 records as valid (see
    adversarial_checks.py).  Returns (records, end) where end is the byte
    offset after the last complete record.
    """
    out = []
    off = 0
    while off + CMD_ITEM_SIZE <= len(d):
        nt = u16(d, off)
        npv = u16(d, off + 4)
        ncv = u16(d, off + 6)
        out.append({
            "num_triangle": nt,
            "vertex_offset": u16(d, off + 2),
            "num_parent_vertex": npv,
            "num_child_vertex": ncv,
        })
        off += CMD_ITEM_SIZE + 4 * (nt + npv + ncv)
    return out, off


def parse_lmp(d):
    """terrain.lmp - lightmaps.

    Layout (verified: the walk consumes the file exactly, 268 images in level 1):
        repeated: uint32 size, then size*size bytes of 8-bit greyscale.
        Observed sizes: 16, 32, 64, 128 (powers of two).
    """
    out = []
    off = 0
    while off + 4 <= len(d):
        size = u32(d, off)
        off += 4
        if size == 0:
            out.append((0, b""))
            continue
        n = size * size
        out.append((size, d[off:off + n]))
        off += n
    return out, off


# ---------------------------------------------------------------------------
# MEF models
# ---------------------------------------------------------------------------

MEF_VERTEX_SIZE = 40
MEF_VERTEX_SIZE_NOLM = 32
MEF_BOX_VERTEX_SIZE = 16

# chunk tags are stored byte-reversed on disk (a 4CC written as a little-endian
# uint32); the logical names are the reversed strings
MEF_TAGS = {
    "OCEMHSEM": "MESHMECO",
    "ATTA": "ATTA",
    "XTVM": "MVTX",
    "TROP": "PORT",
    "XVTP": "PTVX",
    "CFTP": "PTFC",
    "D3DR": "RD3D",
    "DNER": "REND",
    "XTRV": "VRTX",
    "PMTL": "LTMP",
    "HSMC": "CMSH",
    "XTVC": "CVTX",
    "ECFC": "CFCE",
    "TAMC": "CMAT",
    "HPSC": "CSPH",
}


def mef_vertex_stride(p):
    """Return the render-vertex stride for an XTRV payload: 40 or 32.

    Two formats exist and the split is exact - 6,069 models use the 40-byte vertex
    and 617 use the 32-byte one, with 0 ambiguous. Both give unit-length normals
    for 100% of their vertices; forcing a single stride on both is what produced
    the earlier 94.90% figure.

    The test: a stride is valid when it divides the payload and every vertex's
    normal at +0x0C is unit length.
    """
    for stride in (MEF_VERTEX_SIZE, MEF_VERTEX_SIZE_NOLM):
        if len(p) == 0 or len(p) % stride:
            continue
        good = tot = 0
        for i in range(len(p) // stride):
            b = i * stride + 12
            if b + 12 > len(p):
                break
            nx, ny, nz = f32(p, b), f32(p, b + 4), f32(p, b + 8)
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            tot += 1
            if 0.9 < ln < 1.1:
                good += 1
        if tot and good == tot:
            return stride
    return MEF_VERTEX_SIZE


def parse_mef_vertex(d, off, stride=MEF_VERTEX_SIZE):
    """One render vertex - 40 bytes, or 32 bytes without the lightmap UV.

    Verified by unit-length normals: at the correct stride 100% of the normals in
    all 6,686 models with XTRV data are unit length (0.9 < |n| < 1.1).

        float32 x, y, z          position
        float32 nx, ny, nz       normal
        float32 u, v             diffuse texture coordinates
        float32 lu, lv           lightmap coordinates   (40-byte form only)
    """
    v = {
        "pos": (f32(d, off), f32(d, off + 4), f32(d, off + 8)),
        "normal": (f32(d, off + 12), f32(d, off + 16), f32(d, off + 20)),
        "uv": (f32(d, off + 24), f32(d, off + 28)),
        "lightmap_uv": None,
        "stride": stride,
    }
    if stride == MEF_VERTEX_SIZE:
        v["lightmap_uv"] = (f32(d, off + 32), f32(d, off + 36))
    return v


def parse_mef(d):
    """Parse a MEF model (the nested ILFF inside a .res BODY chunk).

    Returns {chunks, vertices, box_vertices, faces, box_faces, spheres, raw}.
    """
    info, errors = parse_ilff(d)
    if info is None:
        return None
    out = {
        "chunks": info["chunks"],
        "vertices": [],
        "box_vertices": [],
        "faces": [],
        "box_faces": [],
        "spheres": [],
        "raw": {},
        "errors": errors,
        "vertex_stride": None,
    }
    for c in info["chunks"]:
        p = c.payload(d)
        if c.id == "XTRV":
            stride = mef_vertex_stride(p)
            out["vertex_stride"] = stride
            out["vertices"] = [parse_mef_vertex(p, i * stride, stride)
                               for i in range(c.size // stride)]
        elif c.id == "XTVC":
            out["box_vertices"] = [
                (f32(p, i * 16), f32(p, i * 16 + 4), f32(p, i * 16 + 8))
                for i in range(c.size // MEF_BOX_VERTEX_SIZE)
            ]
        elif c.id == "ECFC":
            # 8-byte records: uint16 i0, i1, i2, material
            out["box_faces"] = [
                (u16(p, i * 8), u16(p, i * 8 + 2), u16(p, i * 8 + 4), u16(p, i * 8 + 6))
                for i in range(c.size // 8)
            ]
        elif c.id == "DNER":
            out["raw"]["DNER"] = p
        elif c.id == "HPSC":
            out["raw"]["HPSC"] = p
        elif c.id == "TAMC":
            out["raw"]["TAMC"] = p
        elif c.id == "HSMC":
            out["raw"]["HSMC"] = p
        elif c.id == "PMTL":
            out["raw"]["PMTL"] = p
        elif c.id == "D3DR":
            out["raw"]["D3DR"] = p
        elif c.id == "OCEMHSEM":
            out["raw"]["OCEMHSEM"] = p
    return out


def iter_mef_models(res_path):
    """Yield (name, mef_bytes) for every model inside a models .res archive."""
    d = open(res_path, "rb").read()
    info, _ = parse_ilff(d)
    if info is None:
        return
    name = None
    for c in info["chunks"]:
        if c.id in ("NAME", "IRESNAME"):
            name = c.payload(d).split(b"\x00")[0].decode("latin-1")
        elif c.id == "BODY":
            yield name, c.payload(d)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def describe(path):
    d = open(path, "rb").read()
    low = path.lower()
    print(f"=== {path} ({len(d)} bytes)")
    if d[:4] == ILFF_MAGIC:
        info, errors = parse_ilff(d)
        print(f"    ILFF file_size={info['file_size']} sub_format={info['sub_format']} "
              f"chunks={len(info['chunks'])} parsed_end={info['end']} errors={len(errors)}")
        for c in info["chunks"][:12]:
            print(f"      {c}")
        for e in errors[:5]:
            print("      ERR", e)
    elif low.endswith(".bit"):
        items, end = parse_bit(d)
        used = [i for i in items if i]
        print(f"    BIT slots={len(items)} used={len(used)} consumed={end}/{len(d)} "
              f"{'OK' if end == len(d) else 'MISMATCH'}")
        print(f"      sizes: {[s for s, _ in used]}")
    elif low.endswith(".hmp"):
        items, end = parse_hmp(d)
        used = [i for i in items if i]
        print(f"    HMP slots={len(items)} used={len(used)} consumed={end}/{len(d)} "
              f"{'OK' if end == len(d) else 'MISMATCH'}")
        print(f"      sizes: {[s for s, _ in used]}")
    elif low.endswith(".ctr"):
        rec = parse_ctr(d)
        print(f"    CTR records={len(rec)} (32 bytes each)")
        print(f"      first: {rec[0]}")
    elif low.endswith(".cmd"):
        rec, end = parse_cmd(d)
        print(f"    CMD records={len(rec)} consumed={end}/{len(d)} "
              f"{'OK' if end == len(d) else 'MISMATCH'}")
        print(f"      first: {rec[0]}")
    elif low.endswith(".lmp"):
        imgs, end = parse_lmp(d)
        print(f"    LMP images={len(imgs)} consumed={end}/{len(d)} "
              f"{'OK' if end == len(d) else 'MISMATCH'}")
        print(f"      sizes: {sorted(set(s for s, _ in imgs))}")
    else:
        print("    (no parser selected)")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        describe(p)
