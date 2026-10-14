#!/usr/bin/env python3
"""
loop.py -- decoder for the LOOP texture container used by Project IGI
(Innerloop Studios, 1999 PC release).

Self-contained: standard library only (struct, zlib, sys, os).

Public API
----------
    images = load(path)                 # path = .tex file or .res archive
    for im in images:
        im.width, im.height, im.rgba    # rgba = bytes, w*h*4, R,G,B,A order
        im.name, im.version, im.fmt, im.bpp, im.mips

    write_png(path, im.width, im.height, im.rgba)

CLI
---
    python3 loop.py <file.tex|file.res> [outdir]
        decodes every texture and writes <outdir>/<index>_<name>.png

Container summary (see FINDINGS.md for the byte-level evidence)
--------------------------------------------------------------
LOOP file:
    +0x00 char[4]  "LOOP"
    +0x04 uint32   version (2, 6, 7, 9, 11 observed)

  version 2  (flare*/shadow* in common/textures)
    +0x08 uint32   0
    +0x0C uint32   0
    +0x10 uint16   row stride in bytes
    +0x12 uint16   width
    +0x14 uint16   height
    +0x16 uint16   bytes per pixel (2)
    +0x18          pixel data (stride * height bytes)

  version 7  (sprites, e.g. computer.res)
    +0x08 uint32   0xABABABAB fill
    +0x0C uint32   0xABABABAB fill
    +0x10 uint32   0
    +0x14 uint32   0
    +0x18 uint32   0
    +0x1C uint32   end offset of texture data (relative to LOOP start)
    +0x20 uint32   texture count
    +0x24 uint32   0xABABABAB fill
    +0x28 uint32   width
    +0x2C uint32   height
    +0x30 uint32   format code
    +0x34          40-byte descriptors (offset, stride, width, height, 0*6)

  version 9  (terrain.tex, status.res)
    +0x08 uint32   0
    +0x0C uint32   0
    +0x10 uint32   0x00050000 (constant)
    +0x14 uint32   0
    +0x18 uint32   0
    +0x1C uint32   end offset of texture data (relative to LOOP start)
    +0x20 uint32   texture count
    +0x24 uint32   0
    +0x28 uint32   width  (of first texture)
    +0x2C uint32   height (of first texture)
    +0x30 uint32   format code
    +0x34          count * 32-byte descriptors:
                     +0x00 uint32 data offset (relative to LOOP start)
                     +0x04 uint32 format code
                     +0x08 uint16 row stride in bytes
                     +0x0A uint16 width
                     +0x0C uint32 height
                     +0x10 16 bytes zero

  version 11 (all .res model textures, sky layers)
    +0x08 uint32   format code
    +0x0C uint32   0
    +0x10 uint32   0
    +0x14 uint16   scale / LOD level (5 default, 6/7/8 seen)
    +0x16 uint16   height
    +0x18 uint16   width
    +0x1A uint16   height
    +0x1C uint16   width
    +0x1E uint16   bytes per pixel (2 or 4)
    +0x20          pixel data (single texture per LOOP file)

  format codes: 2 = 16-bit ARGB1555, 3 = 32-bit A8R8G8B8 (no mips),
                67 = 0x43 = 32-bit A8R8G8B8 + full mip chain

Pixel formats
-------------
  16-bit: ARGB1555, little-endian uint16.
          bit15 = alpha (1 = opaque; every observed 0 bit belongs to an
          all-zero pixel), bits14-10 = R, bits9-5 = G, bits4-0 = B.
  32-bit: D3DFMT_A8R8G8B8, i.e. bytes in memory are B,G,R,A.
"""

import os
import struct
import sys
import zlib

__all__ = ["Image", "parse_loop", "parse_ilff", "load", "write_png", "mip_levels"]

FMT_ARGB1555 = 2
FMT_ARGB8888 = 3
FMT_ARGB8888_MIPPED = 67


def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _align32(n):
    return (n + 31) & ~31


def mip_levels(w, h):
    """Mip chain as stored by the engine: emit, stop once a side is 1."""
    out = []
    while True:
        out.append((w, h))
        if w == 1 or h == 1:
            break
        w = max(1, w // 2)
        h = max(1, h // 2)
    return out


class Image(object):
    __slots__ = ("width", "height", "rgba", "name", "version", "fmt", "bpp",
                 "mips", "offset")

    def __init__(self, width, height, rgba, name=None, version=0, fmt=0,
                 bpp=0, mips=None, offset=0):
        self.width = width
        self.height = height
        self.rgba = rgba
        self.name = name
        self.version = version
        self.fmt = fmt
        self.bpp = bpp
        self.mips = mips or []
        self.offset = offset

    def __repr__(self):
        return ("<Image %s %dx%d fmt=%d bpp=%d mips=%d>"
                % (self.name or "?", self.width, self.height, self.fmt,
                   self.bpp, len(self.mips)))


# --------------------------------------------------------------------------
# pixel decoders
# --------------------------------------------------------------------------

def decode_argb1555(data, w, h, stride=None):
    """16-bit ARGB1555 -> RGBA bytes. stride = row pitch in bytes."""
    if stride is None:
        stride = w * 2
    out = bytearray(w * h * 4)
    o = 0
    for y in range(h):
        base = y * stride
        for x in range(w):
            i = base + x * 2
            v = data[i] | (data[i + 1] << 8)
            out[o] = ((v >> 10) & 31) * 255 // 31
            out[o + 1] = ((v >> 5) & 31) * 255 // 31
            out[o + 2] = (v & 31) * 255 // 31
            out[o + 3] = 255 if (v >> 15) & 1 else 0
            o += 4
    return bytes(out)


def decode_argb8888(data, w, h, stride=None):
    """32-bit D3DFMT_A8R8G8B8 (memory order B,G,R,A) -> RGBA bytes."""
    if stride is None:
        stride = w * 4
    out = bytearray(w * h * 4)
    o = 0
    for y in range(h):
        base = y * stride
        for x in range(w):
            i = base + x * 4
            out[o] = data[i + 2]
            out[o + 1] = data[i + 1]
            out[o + 2] = data[i]
            out[o + 3] = data[i + 3]
            o += 4
    return bytes(out)


def _decode(data, w, h, fmt, stride=None):
    if fmt == FMT_ARGB1555:
        return decode_argb1555(data, w, h, stride)
    if fmt in (FMT_ARGB8888, FMT_ARGB8888_MIPPED):
        return decode_argb8888(data, w, h, stride)
    raise ValueError("unknown format code %d" % fmt)


def _bpp_for_fmt(fmt):
    if fmt == FMT_ARGB1555:
        return 2
    if fmt in (FMT_ARGB8888, FMT_ARGB8888_MIPPED):
        return 4
    return 0


# --------------------------------------------------------------------------
# LOOP parsers
# --------------------------------------------------------------------------

def _parse_v2(d, off, name):
    """LOOP v2: 24-byte header, one texture."""
    stride = _u16(d, off + 0x10)
    w = _u16(d, off + 0x12)
    h = _u16(d, off + 0x14)
    bpp = _u16(d, off + 0x16)
    fmt = FMT_ARGB1555 if bpp == 2 else FMT_ARGB8888
    need = stride * h
    data = d[off + 0x18:off + 0x18 + need]
    if len(data) < need:
        return []
    return [Image(w, h, _decode(data, w, h, fmt, stride), name, 2, fmt, bpp,
                  offset=off)]


def _parse_v7(d, off, name):
    """LOOP v7: 0x34 header + count * 40-byte descriptors."""
    count = _u32(d, off + 0x20)
    if count == 0 or count > 4096:
        return []
    out = []
    for i in range(count):
        p = off + 0x34 + i * 40
        doff = _u32(d, p + 0x00)
        stride = _u32(d, p + 0x04)
        w = _u32(d, p + 0x08)
        h = _u32(d, p + 0x0C)
        if w == 0 or h == 0 or w > 8192 or h > 8192:
            continue
        fmt = FMT_ARGB1555 if stride == w * 2 else FMT_ARGB8888
        bpp = 2 if fmt == FMT_ARGB1555 else 4
        need = stride * h
        base = off + doff
        data = d[base:base + need]
        if len(data) < need:
            continue
        out.append(Image(w, h, _decode(data, w, h, fmt, stride), name, 7, fmt,
                         bpp, offset=base))
    return out


def _parse_v9(d, off, name):
    """LOOP v9: 0x34 header + count * 32-byte descriptors."""
    count = _u32(d, off + 0x20)
    if count == 0 or count > 65536:
        return []
    out = []
    for i in range(count):
        p = off + 0x34 + i * 32
        doff = _u32(d, p + 0x00)
        fmt = _u32(d, p + 0x04)
        stride = _u16(d, p + 0x08)
        w = _u16(d, p + 0x0A)
        h = _u16(d, p + 0x0C)
        # +0x0E is an unidentified u16 (0 in most files, 1 or the width in a
        # few); it is not needed to locate the pixels.
        if w == 0 or h == 0 or w > 8192 or h > 8192:
            continue
        bpp = _bpp_for_fmt(fmt)
        if bpp == 0:
            continue
        if stride == 0:
            stride = w * bpp
        need = stride * h
        base = off + doff
        data = d[base:base + need]
        if len(data) < need:
            continue
        out.append(Image(w, h, _decode(data, w, h, fmt, stride), name, 9, fmt,
                         bpp, offset=base))
    return out


def _parse_v11(d, off, name):
    """LOOP v11: 32-byte header, one texture (optionally mipmapped)."""
    fmt = _u32(d, off + 0x08)
    scale = _u16(d, off + 0x14)
    h = _u16(d, off + 0x16)
    w = _u16(d, off + 0x18)
    bpp = _u16(d, off + 0x1E)
    if w == 0 or h == 0 or w > 8192 or h > 8192:
        return []
    if bpp not in (2, 4):
        bpp = _bpp_for_fmt(fmt)
    if bpp == 0:
        return []
    base = off + 0x20
    if fmt == FMT_ARGB8888_MIPPED:
        levels = mip_levels(w, h)
        mips = []
        cur = base
        for (lw, lh) in levels:
            need = lw * lh * bpp
            chunk = d[cur:cur + need]
            if len(chunk) < need:
                break
            mips.append(Image(lw, lh, _decode(chunk, lw, lh, fmt), name, 11,
                              fmt, bpp, offset=cur))
            cur += need
        if not mips:
            return []
        top = mips[0]
        top.mips = mips[1:]
        return [top]
    need = w * h * bpp
    data = d[base:base + need]
    if len(data) < need:
        return []
    return [Image(w, h, _decode(data, w, h, fmt), name, 11, fmt, bpp,
                  offset=base)]


def parse_loop(d, off=0, name=None, limit=None):
    """Decode one LOOP file located at `off` inside buffer `d`.

    Returns a list of Image. Unknown versions yield an empty list.
    """
    if off + 8 > len(d) or d[off:off + 4] != b"LOOP":
        return []
    version = _u32(d, off + 4)
    if version == 2:
        return _parse_v2(d, off, name)
    if version == 7:
        return _parse_v7(d, off, name)
    if version == 9:
        return _parse_v9(d, off, name)
    if version == 11:
        return _parse_v11(d, off, name)
    return []


# --------------------------------------------------------------------------
# ILFF container walker (for .res archives)
# --------------------------------------------------------------------------

def _is_ascii_tag(b):
    return len(b) == 4 and all(0x20 <= c < 0x7F for c in b)


def _try_chunk(d, off, end):
    if off + 16 > end:
        return None
    if not _is_ascii_tag(d[off:off + 4]):
        return None
    size = _u32(d, off + 4)
    ctype = _u32(d, off + 8)
    total = _u32(d, off + 12)
    if off + 16 + size <= end and (total == 0 or (16 + size <= total <= end - off)):
        return (d[off:off + 4].decode(), size, ctype, total, 4)
    if _is_ascii_tag(d[off + 4:off + 8]):
        size = _u32(d, off + 8)
        ctype = _u32(d, off + 12)
        total = _u32(d, off + 16)
        if off + 20 + size <= end and (total == 0 or (16 + size <= total <= end - off)):
            return (d[off:off + 8].decode(), size, ctype, total, 8)
    return None


def _find_loop(d, payload_off, sub_format):
    """Locate the LOOP magic inside a BODY payload.

    sub_format 32 archives pad the payload to a 32-byte boundary before the
    nested resource; sub_format 4 archives do not.
    """
    if sub_format == 32:
        cand = _align32(payload_off)
        if d[cand:cand + 4] == b"LOOP":
            return cand
    if d[payload_off:payload_off + 4] == b"LOOP":
        return payload_off
    hit = d.find(b"LOOP", payload_off, payload_off + 64)
    return hit if hit >= 0 else None


def parse_ilff(d):
    """Walk an ILFF archive and decode every nested LOOP texture."""
    if d[:4] != b"ILFF":
        return []
    file_size = _u32(d, 4)
    sub_format = _u32(d, 8)
    end = min(len(d), file_size) if file_size else len(d)
    out = []
    name = None
    off = 16
    while off + 16 <= end:
        c = _try_chunk(d, off, end)
        if c is None:
            break
        cid, size, ctype, total, id_field = c
        payload_off = off + id_field + 12
        if cid == "NAME":
            raw = d[payload_off:payload_off + size]
            name = raw.split(b"\0")[0].decode("latin-1")
        elif cid == "BODY":
            lo = _find_loop(d, payload_off, sub_format)
            if lo is not None:
                out.extend(parse_loop(d, lo, name))
        # Two candidate advances. `total` is authoritative for sub-format 32
        # BODY chunks (it covers the 32-byte alignment padding), but it is
        # wrong for chunks whose id field is 8 bytes wide (it is computed as
        # if the id were 4 bytes). Pick whichever lands on a valid chunk.
        cand1 = (payload_off + size + 3) & ~3
        cand2 = (off + total) if total else 0
        ok1 = cand1 > off and _try_chunk(d, cand1, end) is not None
        ok2 = bool(cand2) and cand2 > off and _try_chunk(d, cand2, end) is not None
        if ok1:
            nxt = cand1
        elif ok2:
            nxt = cand2
        else:
            nxt = cand2 or cand1
        if nxt <= off:
            break
        off = nxt
    return out


def load(path):
    """Decode every texture in a .tex file or .res archive."""
    with open(path, "rb") as fh:
        d = fh.read()
    if d[:4] == b"ILFF":
        return parse_ilff(d)
    if d[:4] == b"LOOP":
        return parse_loop(d, 0, os.path.basename(path))
    return []


# --------------------------------------------------------------------------
# PNG writer (stdlib only)
# --------------------------------------------------------------------------

def write_png(path, w, h, rgba):
    """Write 8-bit RGBA PNG without any third-party dependency."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * w * 4:(y + 1) * w * 4]

    def chunk(tag, payload):
        body = tag + payload
        return (struct.pack(">I", len(payload)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)


def _safe(name):
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    base = os.path.basename(name or "texture")
    return "".join(c if c in keep else "_" for c in base)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    outdir = argv[2] if len(argv) > 2 else "out"
    os.makedirs(outdir, exist_ok=True)
    total = 0
    for path in argv[1:]:
        if path == outdir:
            continue
        imgs = load(path)
        print("%s: %d texture(s)" % (path, len(imgs)))
        for i, im in enumerate(imgs):
            fn = os.path.join(outdir, "%03d_%s.png" % (i, _safe(im.name)))
            write_png(fn, im.width, im.height, im.rgba)
            print("   [%3d] %-52s %4dx%-4d fmt=%-3d bpp=%d mips=%d -> %s"
                  % (i, (im.name or "?")[-52:], im.width, im.height, im.fmt,
                     im.bpp, len(im.mips), fn))
            total += 1
    print("wrote %d PNG(s) to %s" % (total, outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
