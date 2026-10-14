#!/usr/bin/env python3
"""loop2.py -- follow-up decoders for the Project IGI LOOP texture container.

Companion to reverse/tools/loop.py (read-only import).  Adds:

  * parse_v6()          -- the v6 "lighting" sub-resource appended after the
                           pixels of a v9 terrain.tex file (item 7).
  * v9_descriptor()     -- the 32-byte v9 descriptor with the +0x0E field named
                           (item 1).
  * v9_header()         -- the v9 header with the 0x10 word named (item 2).
  * v11_header()        -- the v11 header with the 0x14 scale field (item 3).
  * v2_header()         -- the v2 header (item 6).
  * v7_descriptor()     -- the 40-byte v7 descriptor (item 5).

Nothing here modifies the game tree or the repo; it is a read-only analysis
module.  Byte offsets are relative to the start of the LOOP container.

Findings and the scans that decided them: FINDINGS.md in this directory.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop as _loop  # noqa: E402  (the proven decoder; imported, not edited)

__all__ = [
    "parse_v6", "v9_header", "v9_descriptor", "v11_header",
    "v2_header", "v7_descriptor", "find_v6", "mip_chain_size",
]

FMT_ARGB1555 = 2
FMT_ARGB8888 = 3
FMT_ARGB8888_MIPPED = 67


def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def mip_chain_size(w, h, bpp):
    """Bytes of the full mip chain as the engine stores it (stop at side 1)."""
    total = 0
    while True:
        total += w * h * bpp
        if w == 1 or h == 1:
            break
        w = max(1, w // 2)
        h = max(1, h // 2)
    return total


# --------------------------------------------------------------------------
# version 2  (flare*.tex / shadow*.tex)                        -- item 6
# --------------------------------------------------------------------------

def v2_header(d, off):
    """v2 header.  Field order proven by the size invariant.

    +0x10 u16 row stride in bytes (128)
    +0x12 u16 width  (64)   -- order vs. height is unobservable: all 10 files
    +0x14 u16 height (64)      are 64x64, so both readings fit the data.
    +0x16 u16 bytes per pixel (2)
    +0x18      pixel data, stride * height bytes
    """
    return {
        "stride": _u16(d, off + 0x10),
        "width": _u16(d, off + 0x12),
        "height": _u16(d, off + 0x14),
        "bpp": _u16(d, off + 0x16),
        "data_offset": off + 0x18,
        "data_size": _u16(d, off + 0x10) * _u16(d, off + 0x14),
    }


# --------------------------------------------------------------------------
# version 7  (computer.res sprites)                            -- item 5
# --------------------------------------------------------------------------

def v7_descriptor(d, off, i):
    """40-byte v7 descriptor.  Stride inferred, never proven: every v7 file
    in the retail tree has count == 1, so a 32-byte descriptor plus 8 bytes of
    padding would fit the same bytes.  The data offset (92 = 0x34 + 40) and
    the 24-byte zero tail are consistent with 40.
    """
    p = off + 0x34 + i * 40
    return {
        "offset": _u32(d, p + 0x00),
        "stride": _u32(d, p + 0x04),
        "width": _u32(d, p + 0x08),
        "height": _u32(d, p + 0x0C),
        "tail": d[p + 0x10:p + 0x28],  # 24 zero bytes
    }


# --------------------------------------------------------------------------
# version 9  (terrain.tex, sprites.res, menusystem.res, ...)   -- items 1, 2
# --------------------------------------------------------------------------

def v9_header(d, off):
    """v9 header (0x34 bytes).

    +0x08 u32 0
    +0x0C u32 0
    +0x10 u32 0x00050000  -- constant in all 159 v9 containers (item 2).
                             As two u16s: 0x0000 at 0x10, 0x0005 at 0x12.
                             The 5 matches v11's default scale field (0x14=5).
                             Meaning not proven; it is not the version (0x04)
                             and not a per-file flag (it never varies).
    +0x14 u32 0
    +0x18 u32 0
    +0x1C u32 end offset of the texture data (the v6 block starts here)
    +0x20 u32 texture count
    +0x24 u32 0
    +0x28 u32 width of the first texture
    +0x2C u32 height of the first texture
    +0x30 u32 format code of the first texture
    +0x34      count * 32-byte descriptors
    """
    return {
        "word_0x10": _u32(d, off + 0x10),
        "end_offset": _u32(d, off + 0x1C),
        "count": _u32(d, off + 0x20),
        "width": _u32(d, off + 0x28),
        "height": _u32(d, off + 0x2C),
        "fmt": _u32(d, off + 0x30),
    }


def v9_descriptor(d, off, i):
    """32-byte v9 descriptor.

    +0x00 u32 data offset (relative to the LOOP start)
    +0x04 u32 format code (2 = ARGB1555, 3 = A8R8G8B8)
    +0x08 u16 row stride in bytes
    +0x0A u16 width
    +0x0C u16 height
    +0x0E u16 unknown (item 1).  Observed values: 0 (493 descriptors),
             1 (12), 64 (498).  Constant within a LOOP.  Non-zero only in
             sprites.res (blood1.spr, 7 frames, X=1), computer.res
             (h_scamera2.spr, 5 frames, X=1), menusystem.res (198, X=64)
             and loadingscreen.res (300, X=64).  Not the width (X=1 on 32px
             sprites), not a mip count, not "has alpha" (X=0 textures carry
             rich alpha).  Meaning not proven.
    +0x10 16 zero bytes
    """
    p = off + 0x34 + i * 32
    return {
        "offset": _u32(d, p + 0x00),
        "fmt": _u32(d, p + 0x04),
        "stride": _u16(d, p + 0x08),
        "width": _u16(d, p + 0x0A),
        "height": _u16(d, p + 0x0C),
        "unknown_0x0E": _u16(d, p + 0x0E),
        "reserved": d[p + 0x10:p + 0x20],
    }


# --------------------------------------------------------------------------
# version 11  (all .res model/level textures)                  -- items 3, 4
# --------------------------------------------------------------------------

def v11_header(d, off):
    """v11 header (0x20 bytes).

    +0x08 u32 format code: 2 = ARGB1555, 3 = A8R8G8B8, 67 = 0x43 =
             3 | 0x40 (A8R8G8B8 + full mip chain) (item 4)
    +0x0C u32 0
    +0x10 u32 0
    +0x14 u16 scale level (item 3).  5 in 7,192 of 7,201 textures; 6/7/8 in
             the nine textures whose names carry a _scaleN suffix, and N
             always equals this field.  Not a mip bias (default is 5, not 0,
             and the _scaleN textures are format 2, i.e. carry no mips); not
             a precomputed LOD (the _scaleN textures are different images,
             not downscales of the same-named base texture).
    +0x16 u16 height
    +0x18 u16 width
    +0x1A u16 height (duplicate of 0x16; equal in all 7,201 textures)
    +0x1C u16 width  (duplicate of 0x18; equal in all 7,201 textures)
    +0x1E u16 bytes per pixel (2 or 4)
    +0x20      pixel data (mip chain for format 67)
    """
    return {
        "fmt": _u32(d, off + 0x08),
        "scale": _u16(d, off + 0x14),
        "height": _u16(d, off + 0x16),
        "width": _u16(d, off + 0x18),
        "height2": _u16(d, off + 0x1A),
        "width2": _u16(d, off + 0x1C),
        "bpp": _u16(d, off + 0x1E),
        "data_offset": off + 0x20,
    }


# --------------------------------------------------------------------------
# version 6  (the "lighting" sub-resource)                     -- item 7
# --------------------------------------------------------------------------

def parse_v6(d, off):
    """Decode the v6 "lighting" sub-resource.

    Layout (proven on all 14 terrain.tex files):

      +0x00 char[4] "LOOP"
      +0x04 u32     version = 6
      +0x08 char[8] name field.  Uninitialised in the retail data: "ting"
                    (the tail of the UTF-16 string "lighting", whose first
                    8 bytes the LOOP header overwrote) in 9 files, all-zero
                    in 4, 0xCCCCCCCC (MSVC debug fill) in 1.
      +0x10 u32     count -- always equal to the v9 texture count of the
                    same file (18 or 12)
      +0x14 u32     1 in all 14 files.  Meaning not proven; it is constant,
                    so it is a type/version tag rather than a per-file value.
      +0x18         count * 16-byte records, each [0, 0, 0, N] with
                    N = 1..count.  The block is exactly 0x18 + 16*count
                    bytes, so the last record is complete (no truncation).

    The block starts exactly at the v9 header's +0x1C end offset and runs to
    the end of the file.
    """
    if d[off:off + 4] != b"LOOP" or _u32(d, off + 4) != 6:
        return None
    count = _u32(d, off + 0x10)
    flag = _u32(d, off + 0x14)
    records = []
    for i in range(count):
        p = off + 0x18 + i * 16
        if p + 16 > len(d):
            break
        records.append(struct.unpack_from("<4I", d, p))
    return {
        "offset": off,
        "name_bytes": d[off + 0x08:off + 0x10],
        "count": count,
        "flag_0x14": flag,
        "records": records,
        "size": 0x18 + count * 16,
    }


def find_v6(d):
    """Locate the v6 block in a buffer (it sits at the v9 end offset)."""
    if d[:4] == b"LOOP" and _u32(d, 4) == 9:
        end = _u32(d, 0x1C)
        if d[end:end + 8] == b"LOOP\x06\x00\x00\x00":
            return parse_v6(d, end)
    return None


if __name__ == "__main__":
    import os
    for path in sys.argv[1:]:
        with open(path, "rb") as fh:
            data = fh.read()
        v6 = find_v6(data)
        if v6:
            print("%s: v6 block @0x%X count=%d flag=%d name=%r"
                  % (path, v6["offset"], v6["count"], v6["flag_0x14"],
                     v6["name_bytes"]))
