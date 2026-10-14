#!/usr/bin/env python3
"""misc.py -- decoders for the remaining Project IGI (1999, Innerloop Studios)
file types: ILSF sound archives, .iff animation containers, .fnt bitmap fonts
and the menu .res tag histogram.

Self-contained: standard library only (struct, wave, sys, os, collections).

Formats covered
---------------
ILSF   sound samples (loose .wav files AND the BODY payloads of sound .res
       archives).  Two encodings: 16-bit PCM (versions 0 and 1) and 4-bit
       IMA ADPCM (versions 2 and 3).
IFF    EA IFF 85 animation containers (common/anims/*.iff, FORM/BOBJ).
FNT    custom ILFF bitmap fonts (screens/intro/*.fnt, and font*.fnt inside
       computer.res / menusystem/*.res).
RES    ILFF archive chunk-tag histogram (menusystem/*.res, screens/**/*.res).

Evidence
--------
Every field below is backed by the retail data plus the decoder disassembled
from IGI.exe.  See FINDINGS.md for the byte-level tables and the file counts.

ILSF header (20 bytes, verified on 759/759 ILSF payloads in the tree):

    +0x00 char[4]  "ILSF"
    +0x04 uint16   version: 0/2 = loose .wav, 1/3 = inside a .res BODY
    +0x06 uint16   bits per sample (always 16)
    +0x08 uint16   channel count (1 or 2)
    +0x0A uint16   flags: 0 for loose files, 0x1002 for .res members
    +0x0C uint32   sample rate (11025 / 22050 / 44100)
    +0x10 uint32   frame count (samples PER CHANNEL)
    +0x14          sample data

    version 0/1: PCM,  frames*channels*2 bytes
    version 2/3: IMA ADPCM, frames*channels nibbles, high nibble first

The IGI.exe ILSF loader (file offset 0x95E36) compares the first dword with
"ILSF", copies the 20-byte header into a 48-byte struct at +0x10 and jumps
through a 4-entry table at VA 0x4960D0 indexed by the version word:

    version 0 -> 0x495EE0   data pointer stays NULL -> load the loose file
    version 1 -> 0x495F95   data pointer = buffer + 0x14   (PCM)
    version 2 -> 0x495EE0   same as version 0
    version 3 -> 0x495F30   malloc(channels*bits*frames/8), decode from
                            buffer + 0x14 via 0x496110

0x496110 is a textbook IMA ADPCM decoder: step table at VA 0x544088 (89
int16), index table at VA 0x544078 (16 bytes, the 8-entry IMA table
duplicated for the sign bit), predictor clamped to [-32768, 32767], step
index clamped to [0, 88].  The state is zeroed by 0x4962B0, so the first
step is step_table[0] = 7 and the first predictor is 0.

Usage
-----
    python3 misc.py wav   <file.wav|file.res> [outdir]   # ILSF -> .wav
    python3 misc.py iffs  <file.iff> [...]               # IFF chunk tree
    python3 misc.py fnt   <file.fnt> [...]               # font header+glyphs
    python3 misc.py res   <file.res> [...]               # chunk-tag histogram
    python3 misc.py scan  <tree-root>                    # run over the tree
"""
from __future__ import annotations

import os
import struct
import sys
import wave
from collections import Counter

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def u16(d, off):
    return struct.unpack_from("<H", d, off)[0]


def u32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def f32(d, off):
    return struct.unpack_from("<f", d, off)[0]


def align4(n):
    return (n + 3) & ~3


def is_ascii_tag(b):
    return len(b) == 4 and all(0x20 <= c < 0x7F for c in b)


# ---------------------------------------------------------------------------
# ILSF -- sound samples
# ---------------------------------------------------------------------------

ILSF_MAGIC = b"ILSF"
ILSF_HEADER_SIZE = 20

# IMA ADPCM tables, copied verbatim from IGI.exe:
#   step table  VA 0x544088, 89 int16
#   index table VA 0x544078, 16 int8 (the 8-entry IMA table duplicated)
IMA_STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41,
    45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190,
    209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724,
    796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272,
    2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132,
    7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500,
    20350, 22385, 24623, 27086, 29794, 32767,
]
IMA_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8,
                   -1, -1, -1, -1, 2, 4, 6, 8]


class IlsfHeader:
    """The 20-byte ILSF header."""

    __slots__ = ("version", "bits", "channels", "flags", "rate", "frames")

    def __init__(self, version, bits, channels, flags, rate, frames):
        self.version = version
        self.bits = bits
        self.channels = channels
        self.flags = flags
        self.rate = rate
        self.frames = frames

    @property
    def compressed(self):
        """Versions 2 and 3 are IMA ADPCM; 0 and 1 are 16-bit PCM."""
        return self.version in (2, 3)

    @property
    def in_archive(self):
        """Versions 1 and 3 live inside a .res BODY; 0 and 2 are loose files."""
        return self.version in (1, 3)

    @property
    def encoding(self):
        return "ima-adpcm" if self.compressed else "pcm-s16le"

    def __repr__(self):
        return (f"<ILSF v{self.version} {self.encoding} {self.rate}Hz "
                f"{self.channels}ch {self.bits}bit frames={self.frames}>")


def parse_ilsf(d, off=0):
    """Parse an ILSF header at `off`.  Returns (header, data_offset) or None."""
    if d[off:off + 4] != ILSF_MAGIC:
        return None
    version, bits, channels, flags, rate, frames = struct.unpack_from(
        "<HHHHII", d, off + 4)
    return IlsfHeader(version, bits, channels, flags, rate, frames), off + ILSF_HEADER_SIZE


def ima_adpcm_decode(data, channels, frames):
    """Decode `frames` interleaved frames of 4-bit IMA ADPCM.

    Mirrors IGI.exe 0x496110 exactly:
      * nibbles are consumed high-first from each byte
      * one nibble per channel per frame, channels interleaved
      * step = step_table[step_index]; diff = step>>3, plus step for bit 2,
        step>>1 for bit 1, step>>2 for bit 0
      * bit 3 is the sign; the predictor is clamped to [-32768, 32767]
      * step_index += index_table[nibble], clamped to [0, 88]
    """
    out = []
    append = out.append
    pos = 0
    byte = 0
    high = True
    pred = [0] * channels
    idx = [0] * channels
    n = len(data)
    for _ in range(frames):
        for ch in range(channels):
            if high:
                if pos >= n:
                    byte = 0
                else:
                    byte = data[pos]
                    pos += 1
                nib = byte >> 4
                high = False
            else:
                nib = byte & 0x0F
                high = True
            step = IMA_STEP_TABLE[idx[ch]]
            diff = step >> 3
            if nib & 4:
                diff += step
            if nib & 2:
                diff += step >> 1
            if nib & 1:
                diff += step >> 2
            if nib & 8:
                p = pred[ch] - diff
            else:
                p = pred[ch] + diff
            if p > 32767:
                p = 32767
            elif p < -32768:
                p = -32768
            pred[ch] = p
            i = idx[ch] + IMA_INDEX_TABLE[nib]
            if i < 0:
                i = 0
            elif i > 88:
                i = 88
            idx[ch] = i
            append(p)
    return out


def ilsf_decode(d, off=0):
    """Decode one ILSF payload to a list of interleaved int16 samples.

    Returns (header, samples, consumed_bytes) or None when the magic is wrong.
    """
    parsed = parse_ilsf(d, off)
    if parsed is None:
        return None
    hdr, data_off = parsed
    if hdr.compressed:
        # frames*channels nibbles, packed 2 per byte, high nibble first
        need = (hdr.frames * hdr.channels + 1) // 2
        raw = d[data_off:data_off + need]
        samples = ima_adpcm_decode(raw, hdr.channels, hdr.frames)
        return hdr, samples, ILSF_HEADER_SIZE + need
    # PCM: frames*channels 16-bit little-endian samples
    need = hdr.frames * hdr.channels * 2
    raw = d[data_off:data_off + need]
    n = len(raw) // 2
    samples = list(struct.unpack_from("<%dh" % n, raw, 0))
    return hdr, samples, ILSF_HEADER_SIZE + need


def write_wav(path, hdr, samples):
    """Write `samples` (interleaved int16) as a RIFF/WAVE file."""
    with wave.open(path, "wb") as w:
        w.setnchannels(hdr.channels)
        w.setsampwidth(2)
        w.setframerate(hdr.rate)
        w.writeframes(struct.pack("<%dh" % len(samples), *samples))


# ---------------------------------------------------------------------------
# ILFF container (shared by .res archives and .fnt fonts)
# ---------------------------------------------------------------------------

ILFF_MAGIC = b"ILFF"


class Chunk:
    __slots__ = ("id", "size", "type", "total", "offset", "payload_off",
                 "id_field", "extra")

    def __init__(self, cid, size, ctype, total, offset, payload_off, id_field,
                 extra=0):
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
    """Parse an ILFF container.  Returns (info, errors); info is None on bad magic."""
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
        if nxt > end or (nxt < end and _try_chunk(d, nxt, end) is None and ch.total):
            if ch.total and ch.offset + ch.total <= end:
                nxt = ch.offset + ch.total
        if nxt > end:
            if ch.payload_off + size <= end:
                chunks.append(ch)
                off = ch.payload_off + size
                break
            errors.append(f"@{off}: chunk {cid!r} overruns ({nxt} > {end})")
            break
        chunks.append(ch)
        off = nxt
    return {"file_size": file_size, "sub_format": sub_format, "chunks": chunks,
            "end": off, "errors": errors}, errors


def iter_res_bodies(path):
    """Yield (name, payload_bytes, chunk) for every BODY in an ILFF archive."""
    d = open(path, "rb").read()
    info, _ = parse_ilff(d)
    if info is None:
        return
    name = None
    for c in info["chunks"]:
        if c.id in ("NAME", "IRESNAME"):
            name = c.payload(d).split(b"\x00")[0].decode("latin-1")
        elif c.id == "BODY":
            yield name, c.payload(d), c


def res_tag_histogram(path):
    """Chunk-tag histogram for an ILFF archive, plus the BODY magic histogram."""
    d = open(path, "rb").read()
    info, errors = parse_ilff(d)
    if info is None:
        return None
    tags = Counter(c.id for c in info["chunks"])
    body_magic = Counter()
    for c in info["chunks"]:
        if c.id == "BODY":
            body_magic[c.payload(d)[:4]] += 1
    return {"path": path, "size": len(d), "sub_format": info["sub_format"],
            "chunks": len(info["chunks"]), "tags": tags,
            "body_magic": body_magic, "errors": errors}


# ---------------------------------------------------------------------------
# IFF -- EA IFF 85 animation containers
# ---------------------------------------------------------------------------


def parse_iff(d, start=0, end=None, depth=0, out=None):
    """Walk an EA IFF 85 chunk tree.  Returns a list of dicts.

    Layout: "FORM" + uint32 BE size + 4-char form type, then chunks of
    "id" + uint32 BE size + payload, each padded to an even length.
    """
    if out is None:
        out = []
    if end is None:
        end = len(d)
    off = start
    while off + 8 <= end:
        cid = d[off:off + 4]
        if not all(0x20 <= c < 0x7F for c in cid):
            out.append({"id": None, "offset": off, "size": 0, "depth": depth,
                        "raw": d[off:off + 8]})
            break
        size = struct.unpack_from(">I", d, off + 4)[0]
        rec = {"id": cid.decode("latin-1"), "offset": off, "size": size,
               "depth": depth}
        if cid == b"FORM":
            rec["form_type"] = d[off + 8:off + 12].decode("latin-1")
            out.append(rec)
            parse_iff(d, off + 12, min(off + 8 + size, end), depth + 1, out)
        else:
            out.append(rec)
        off += 8 + size + (size & 1)
    return out


def iff_summary(d):
    """Tag histogram + form types for an IFF file."""
    chunks = parse_iff(d)
    return {"chunks": chunks,
            "tags": Counter(c["id"] for c in chunks if c["id"]),
            "forms": Counter(c.get("form_type") for c in chunks
                             if c["id"] == "FORM")}


# ---------------------------------------------------------------------------
# FNT -- custom ILFF bitmap fonts
# ---------------------------------------------------------------------------

FNT_GLYPH_SIZE = 40


class FntGlyph:
    """One 40-byte glyph record of the ANMF chunk.

    Verified on 154/154 glyphs of both fonts:

        +0x04 float32 u_start    x / atlas_width
        +0x0C float32 u_end      (x + width) / atlas_width
        +0x10 float32 v_bottom   y_bottom / 128   (the glyph BASELINE, not a height)
        +0x16 uint16  width      glyph width in pixels
        +0x18 uint16  height     glyph height in pixels
        +0x1A uint16  advance    width + 1 in 151/154 (font3) and 152/154 (font4)
        +0x1C uint16  height     repeated
        +0x24 uint16  unknown    0..16, meaning not determined

    The glyph occupies the atlas rectangle
    [u_start*W, v_bottom*128 - height] .. [u_end*W, v_bottom*128].
    That box contains ink for 154/154 glyphs of both fonts.
    """

    __slots__ = ("index", "u_start", "u_end", "v_bottom", "width", "height",
                 "advance", "height2", "unknown_24", "raw")

    def __init__(self, index, raw):
        self.index = index
        self.raw = raw
        self.u_start = f32(raw, 4)
        self.u_end = f32(raw, 12)
        self.v_bottom = f32(raw, 16)
        self.width = u16(raw, 22)
        self.height = u16(raw, 24)
        self.advance = u16(raw, 26)
        self.height2 = u16(raw, 28)
        self.unknown_24 = u16(raw, 36)

    def box(self, atlas_width):
        """Atlas rectangle (x, y, w, h) for this glyph."""
        x = round(self.u_start * atlas_width)
        y = round(self.v_bottom * 128) - self.height
        return x, y, self.width, self.height

    def __repr__(self):
        return (f"<Glyph {self.index} u={self.u_start:.6f}..{self.u_end:.6f} "
                f"v_bottom={self.v_bottom:.6f} w={self.width} h={self.height} "
                f"adv={self.advance}>")


def parse_fnt(d):
    """Parse a .fnt font.  Returns a dict or None when it is not ILFF."""
    info, errors = parse_ilff(d)
    if info is None:
        return None
    out = {"sub_format": info["sub_format"], "chunks": info["chunks"],
           "header": None, "glyphs": [], "texh": None, "body": None,
           "errors": errors}
    for c in info["chunks"]:
        p = c.payload(d)
        if c.id == "FONTFNTH":
            out["header"] = list(struct.unpack_from("<6I", p, 0))
        elif c.id == "ANMF":
            out["glyphs"] = [FntGlyph(i, p[i * FNT_GLYPH_SIZE:(i + 1) * FNT_GLYPH_SIZE])
                             for i in range(c.size // FNT_GLYPH_SIZE)]
        elif c.id == "TEXH":
            out["texh"] = list(struct.unpack_from("<6I", p, 0))
            out["texh_u16"] = list(struct.unpack_from("<12H", p, 0))
        elif c.id == "BODY":
            out["body"] = p
    return out


def fnt_atlas(fnt):
    """Return (width, height, coverage_bytes) for the font's glyph atlas.

    The atlas is a 32-bit-per-pixel bitmap; the low byte of each pixel is the
    glyph coverage (alpha).  Dimensions come from TEXH, which holds
    [3, 0, 0, 0, W, H, W, H, 32] as uint16 at +0x0C.
    """
    t = fnt.get("texh_u16")
    if not t:
        return None
    width, height = t[7], t[8]
    body = fnt["body"]
    if body is None or width * height * 4 > len(body):
        return None
    cov = bytes(body[i * 4 + 3] for i in range(width * height))
    return width, height, cov


def fnt_extract_glyph(fnt, index):
    """Return (w, h, coverage_bytes) for one glyph, cropped from the atlas."""
    atlas = fnt_atlas(fnt)
    if atlas is None or index >= len(fnt["glyphs"]):
        return None
    aw, ah, cov = atlas
    g = fnt["glyphs"][index]
    x, y, w, h = g.box(aw)
    out = bytearray(w * h)
    for yy in range(h):
        sy = y + yy
        if 0 <= sy < ah:
            row = cov[sy * aw + x:sy * aw + x + w]
            out[yy * w:yy * w + len(row)] = row
    return w, h, bytes(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_wav(args):
    outdir = args[1] if len(args) > 1 else "out"
    os.makedirs(outdir, exist_ok=True)
    n = 0
    for path in [args[0]]:
        d = open(path, "rb").read()
        if d[:4] == ILFF_MAGIC:
            for name, payload, ch in iter_res_bodies(path):
                if payload[:4] != ILSF_MAGIC:
                    continue
                hdr, samples, _ = ilsf_decode(payload)
                base = os.path.basename(name or "body").replace("/", "_")
                if not base.lower().endswith(".wav"):
                    base += ".wav"
                out = os.path.join(outdir, base)
                write_wav(out, hdr, samples)
                print(f"{path}::{ch.payload_off} -> {out}  {hdr}  "
                      f"{len(samples)} samples  {len(samples)/hdr.channels/hdr.rate:.3f}s")
                n += 1
        elif d[:4] == ILSF_MAGIC:
            hdr, samples, _ = ilsf_decode(d)
            out = os.path.join(outdir, os.path.basename(path))
            write_wav(out, hdr, samples)
            print(f"{path} -> {out}  {hdr}  {len(samples)} samples  "
                  f"{len(samples)/hdr.channels/hdr.rate:.3f}s")
            n += 1
        else:
            print(f"{path}: not ILSF and not ILFF")
    print(f"wrote {n} wav file(s)")


def _cmd_iffs(args):
    for path in args:
        d = open(path, "rb").read()
        s = iff_summary(d)
        print(f"=== {path} ({len(d)} bytes)")
        print(f"    tags: {dict(s['tags'])}")
        print(f"    forms: {dict(s['forms'])}")
        for c in s["chunks"]:
            ft = f" form={c['form_type']}" if "form_type" in c else ""
            print(f"      {'  ' * c['depth']}{c['id']} @{c['offset']} "
                  f"size={c['size']}{ft}")


def _cmd_fnt(args):
    for path in args:
        d = open(path, "rb").read()
        f = parse_fnt(d)
        if f is None:
            print(f"{path}: not an ILFF font")
            continue
        print(f"=== {path} ({len(d)} bytes)")
        print(f"    chunks: {[c.id for c in f['chunks']]}")
        print(f"    FONTFNTH: {f['header']}")
        print(f"    TEXH u32: {f['texh']}  u16: {f.get('texh_u16')}")
        print(f"    glyphs: {len(f['glyphs'])} x {FNT_GLYPH_SIZE} bytes")
        atlas = fnt_atlas(f)
        if atlas:
            w, h, cov = atlas
            print(f"    atlas: {w}x{h} 32bpp, coverage in the low byte, "
                  f"{sum(1 for x in cov if x)} non-zero texels")
        for g in f["glyphs"][:8]:
            box = g.box(atlas[0]) if atlas else None
            print(f"      {g}  box={box}")


def _cmd_res(args):
    for path in args:
        r = res_tag_histogram(path)
        if r is None:
            print(f"{path}: not an ILFF archive")
            continue
        print(f"=== {path} ({r['size']} bytes) sub_format={r['sub_format']} "
              f"chunks={r['chunks']} errors={len(r['errors'])}")
        print(f"    tags: {dict(r['tags'])}")
        print(f"    BODY magic: { {k.decode('latin-1', 'replace'): v for k, v in r['body_magic'].items()} }")


def _cmd_scan(root):
    counts = Counter()
    errors = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            p = os.path.join(dirpath, fn)
            low = fn.lower()
            try:
                if low.endswith(".wav"):
                    d = open(p, "rb").read()
                    if d[:4] != ILSF_MAGIC:
                        errors.append((p, "not ILSF"))
                        continue
                    hdr, samples, _ = ilsf_decode(d)
                    counts[("wav", hdr.encoding)] += 1
                elif low.endswith(".iff"):
                    d = open(p, "rb").read()
                    s = iff_summary(d)
                    counts[("iff", "ok")] += 1
                elif low.endswith(".fnt"):
                    d = open(p, "rb").read()
                    f = parse_fnt(d)
                    if f is None:
                        errors.append((p, "not ILFF"))
                        continue
                    counts[("fnt", "ok")] += 1
                elif low.endswith(".res"):
                    r = res_tag_histogram(p)
                    if r is None:
                        errors.append((p, "not ILFF"))
                        continue
                    counts[("res", "ok")] += 1
                    for name, payload, ch in iter_res_bodies(p):
                        if payload[:4] == ILSF_MAGIC:
                            hdr, samples, _ = ilsf_decode(payload)
                            counts[("res-ilsf", hdr.encoding)] += 1
            except Exception as e:  # noqa: BLE001
                errors.append((p, f"{type(e).__name__}: {e}"))
    print("scan complete")
    for k in sorted(counts):
        print(f"   {k[0]:10s} {k[1]:12s} {counts[k]}")
    print(f"errors: {len(errors)}")
    for p, e in errors[:20]:
        print(f"   {p}: {e}")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    mode = argv[1]
    args = argv[2:]
    if mode == "wav":
        _cmd_wav(args)
    elif mode == "iffs":
        _cmd_iffs(args)
    elif mode == "fnt":
        _cmd_fnt(args)
    elif mode == "res":
        _cmd_res(args)
    elif mode == "scan":
        _cmd_scan(args[0])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
