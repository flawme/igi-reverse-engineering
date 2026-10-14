#!/usr/bin/env python3
"""mef_deep.py - deep decoder for Project IGI (1999, Innerloop Studios) MEF models.

Decodes every chunk of a MEF model with the field layout established by
cross-model statistical analysis over all 6,795 models in the retail tree.
See FINDINGS.md in this directory for the evidence behind each field.

Usage
-----
    python3 mef_deep.py <file.res | file.mef> [...]      # decode every model
    python3 mef_deep.py --limit 20 <file.res>            # first 20 models
    python3 mef_deep.py --selftest <pc_root>             # decode all models, report

The MEF is the nested ILFF inside a models/*.res BODY chunk. Chunk tags are
stored byte-reversed on disk (a 4CC written as a little-endian uint32); the
logical names are the reversed strings.

Field confidence markers used in the output:
    [V]  verified  - holds on every model where it is testable (see FINDINGS.md)
    [S]  strong    - holds on >90% of models
    [U]  unknown   - no cross-model evidence; value printed raw
"""
from __future__ import annotations

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from igi_formats import parse_ilff, iter_mef_models, Chunk  # noqa: E402

# Default game tree: <repo>/reverse/extracted/pc (see the repo .gitignore).
DEFAULT_PC_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "extracted", "pc"))

u16 = lambda d, o: struct.unpack_from("<H", d, o)[0]
i16 = lambda d, o: struct.unpack_from("<h", d, o)[0]
u32 = lambda d, o: struct.unpack_from("<I", d, o)[0]
f32 = lambda d, o: struct.unpack_from("<f", d, o)[0]

# ---------------------------------------------------------------------------
# vertex formats
# ---------------------------------------------------------------------------

# Two render-vertex formats exist in the retail data. Which one a model uses is
# determined by XTRV_size / OCEMHSEM.vertex_count (0x64): 40 or 32 bytes.
#   40-byte: pos(0x00) normal(0x0C) uv(0x18) lightmap_uv(0x20)
#   32-byte: pos(0x00) normal(0x0C) uv(0x18)          <- no lightmap UV
VERTEX_STRIDES = (40, 32)


def vertex_stride(xtrv_size, vertex_count):
    """Return the vertex stride for an XTRV chunk, or None if undetermined."""
    if xtrv_size == 0:
        return None
    if vertex_count and xtrv_size % vertex_count == 0:
        s = xtrv_size // vertex_count
        if s in VERTEX_STRIDES:
            return s
    for s in VERTEX_STRIDES:
        if xtrv_size % s == 0:
            return s
    return None


def decode_vertex(p, off, stride):
    v = {
        "pos": (f32(p, off), f32(p, off + 4), f32(p, off + 8)),
        "normal": (f32(p, off + 12), f32(p, off + 16), f32(p, off + 20)),
        "uv": (f32(p, off + 24), f32(p, off + 28)),
    }
    if stride == 40:
        v["lightmap_uv"] = (f32(p, off + 32), f32(p, off + 36))
    return v


# ---------------------------------------------------------------------------
# chunk decoders
# ---------------------------------------------------------------------------

def decode_ocemhsem(p):
    """156-byte model header. Offsets and evidence in FINDINGS.md."""
    return {
        "0x00 float  [V] constant 0.1": f32(p, 0x00),
        "0x04 u32    [V] constant 2000": u32(p, 0x04),
        "0x08 u32    [V] constant 11": u32(p, 0x08),
        "0x0c u32    [U]": u32(p, 0x0C),
        "0x10 u32    [U]": u32(p, 0x10),
        "0x14 u32    [U]": u32(p, 0x14),
        "0x18 u32    [U]": u32(p, 0x18),
        "0x1c u32    [U]": u32(p, 0x1C),
        "0x20 u32    [S] format flag (0/1/3)": u32(p, 0x20),
        "0x24 u32    [V] zero": u32(p, 0x24),
        "0x28 u32    [V] zero": u32(p, 0x28),
        "0x2c u32    [V] zero": u32(p, 0x2C),
        "0x30 sphere[V] render bounding sphere (x,y,z,r)":
            (f32(p, 0x30), f32(p, 0x34), f32(p, 0x38), f32(p, 0x3C)),
        "0x40 sphere[V] collision bounding sphere (x,y,z,r)":
            (f32(p, 0x40), f32(p, 0x44), f32(p, 0x48), f32(p, 0x4C)),
        "0x50 sphere[V] duplicate of 0x40":
            (f32(p, 0x50), f32(p, 0x54), f32(p, 0x58), f32(p, 0x5C)),
        "0x60 u32    [V] DNER triangle count": u32(p, 0x60),
        "0x64 u32    [V] render vertex count": u32(p, 0x64),
        "0x68 u32    [V] render bytes = XTRV+DNER+D3DR": u32(p, 0x68),
        "0x6c u32    [V] ECFC record count": u32(p, 0x6C),
        "0x70 u32    [V] XTVC vertex count": u32(p, 0x70),
        "0x74 u32    [V] collision bytes = XTVC+ECFC+TAMC+HPSC+HSMC": u32(p, 0x74),
        "0x78 float  [V] radius from origin (upper bound)": f32(p, 0x78),
        "0x7c u32    [U]": u32(p, 0x7C),
        "0x80..0x9c  [S] zero padding": p[0x80:0x9C].hex(),
    }


def dner_header_size(p, off):
    """DNER batch headers are 28 or 32 bytes.

    Discriminator (perfect over all 6,795 models): the u32 at +0x1C is
    0x00010000 for the 28-byte form and something else for the 32-byte form.
    """
    return 28 if u32(p, off + 0x1C) == 0x00010000 else 32


def decode_dner(p):
    """Render batches: header + uint16 triangle list (indices into XTRV)."""
    batches = []
    off = 0
    while off < len(p):
        hdr = dner_header_size(p, off)
        if off + hdr > len(p):
            batches.append({"error": f"truncated header at 0x{off:x}"})
            break
        n_idx = u16(p, off + 0x0C)
        if n_idx == 0 or n_idx % 3:
            batches.append({"error": f"bad index count {n_idx} at 0x{off:x}"})
            break
        body = 2 * n_idx
        if off + hdr + body > len(p):
            batches.append({"error": f"body overruns at 0x{off:x}"})
            break
        idx = [u16(p, off + hdr + 2 * i) for i in range(n_idx)]
        # vertex offset / count live at +0x12/+0x14 (28-byte header)
        # or +0x14/+0x16 (32-byte header)
        vo_off = 0x12 if hdr == 28 else 0x14
        batches.append({
            "offset": off,
            "header_size": hdr,
            "sphere": (f32(p, off), f32(p, off + 4), f32(p, off + 8)),
            "index_count": n_idx,
            "triangles": n_idx // 3,
            "byte_count": u16(p, off + 0x0E),
            "batch_index": u16(p, off + 0x10),
            "vertex_offset": u16(p, off + vo_off),
            "vertex_count": u16(p, off + vo_off + 2),
            "unk_0x18": u16(p, off + 0x18),
            "unk_0x1a": u16(p, off + 0x1A),
            "unk_0x1c": u16(p, off + 0x1C),
            "unk_0x1e": u16(p, off + 0x1E),
            "indices": idx,
        })
        off += hdr + body
    return batches


def decode_hsmc(p):
    """64 bytes = two 32-byte collision-group descriptors.

    Each: uint32 ecfc_count, xtvc_count, tamc_count, hpsc_count, pad[4].
    """
    out = []
    for i in range(0, len(p) - 31, 32):
        out.append({
            "ecfc_count": u32(p, i),
            "xtvc_count": u32(p, i + 4),
            "tamc_count": u32(p, i + 8),
            "hpsc_count": u32(p, i + 12),
            "pad": [u32(p, i + 16 + 4 * k) for k in range(4)],
        })
    return out


def decode_tamc(p):
    """12-byte records: float + 4 x uint16 (semantics partly unknown)."""
    out = []
    for i in range(len(p) // 12):
        o = i * 12
        out.append({
            "float_0x00": f32(p, o),
            "u16_0x04": u16(p, o + 4),
            "u16_0x06": u16(p, o + 6),
            "u16_0x08": u16(p, o + 8),
            "u16_0x0a": u16(p, o + 10),
        })
    return out


def decode_hpsc(p):
    """24-byte records: 4 floats + 4 uint16 (semantics partly unknown)."""
    out = []
    for i in range(len(p) // 24):
        o = i * 24
        out.append({
            "f32_0x00": (f32(p, o), f32(p, o + 4), f32(p, o + 8), f32(p, o + 12)),
            "u16_0x10": u16(p, o + 0x10),
            "u16_0x12": u16(p, o + 0x12),
            "u16_0x14": u16(p, o + 0x14),
            "u16_0x16": u16(p, o + 0x16),
        })
    return out


def decode_d3dr(p):
    """D3D render state block. 48- and 56-byte variants exist.

    48-byte: u32 4, dner_triangles, batch_count, vertex_count, 0...
    56-byte: u32 4, <extra>, dner_triangles, batch_count, vertex_count, ...
    """
    vals = [u32(p, i) for i in range(0, len(p) - 3, 4)]
    out = {"size": len(p), "u32": vals}
    if len(p) == 48:
        out["fields"] = {"const_4": vals[0], "dner_triangles": vals[1],
                         "batch_count": vals[2], "vertex_count": vals[3]}
    elif len(p) == 56:
        out["fields"] = {"const_4": vals[0], "unk_0x04": vals[1],
                         "dner_triangles": vals[2], "batch_count": vals[3],
                         "vertex_count": vals[4], "unk_0x14": vals[5]}
    return out


def decode_pmtl(p):
    """8-byte records; u32@4 is always 0, u32@0 is a packed pair of u16."""
    out = []
    for i in range(len(p) // 8):
        o = i * 8
        out.append({"u32_0x00": u32(p, o), "u16_0x00": u16(p, o),
                    "u16_0x02": u16(p, o + 2), "u32_0x04": u32(p, o + 4)})
    return out


def decode_xtvm(p):
    """Marker chunk; non-empty in a minority of models. Layout unknown."""
    return {"size": len(p), "u32": [u32(p, i) for i in range(0, len(p) - 3, 4)]}


# ---------------------------------------------------------------------------
# model decoder
# ---------------------------------------------------------------------------

def decode_model(name, mef, verbose=True):
    """Decode one MEF model. Returns a dict; prints when verbose."""
    info, errors = parse_ilff(mef)
    if info is None:
        return None
    chunks = info["chunks"]
    oc = next((c for c in chunks if c.id == "OCEMHSEM"), None)
    if oc is None:
        return None
    ocp = oc.payload(mef)
    vertex_count = u32(ocp, 0x64)

    out = {"name": name, "size": len(mef), "chunks": [], "errors": errors}

    if verbose:
        print(f"\n=== {name}  ({len(mef)} bytes, {len(chunks)} chunks)")

    for c in chunks:
        p = c.payload(mef)
        entry = {"id": c.id, "size": c.size, "offset": c.offset}
        if verbose:
            print(f"  {c.id:<9} size={c.size:<7} @0x{c.offset:06x}")

        if c.id == "OCEMHSEM":
            entry["decoded"] = decode_ocemhsem(p)
            if verbose:
                for k, v in entry["decoded"].items():
                    print(f"      {k:<58} = {v}")
        elif c.id == "DNER":
            entry["decoded"] = decode_dner(p)
            if verbose:
                for b in entry["decoded"]:
                    if "error" in b:
                        print(f"      ERROR {b['error']}")
                        continue
                    print(f"      batch@{b['offset']} hdr={b['header_size']} "
                          f"tri={b['triangles']} idx={b['index_count']} "
                          f"bytes={b['byte_count']} batch#={b['batch_index']} "
                          f"vtx_off={b['vertex_offset']} vtx_cnt={b['vertex_count']} "
                          f"unk=({b['unk_0x18']},{b['unk_0x1a']},{b['unk_0x1c']},{b['unk_0x1e']})")
                    print(f"        sphere={tuple(round(x, 3) for x in b['sphere'])}")
                    print(f"        indices[:12]={b['indices'][:12]}")
        elif c.id == "XTRV":
            stride = vertex_stride(c.size, vertex_count)
            entry["stride"] = stride
            if stride:
                n = c.size // stride
                entry["vertices"] = [decode_vertex(p, i * stride, stride) for i in range(n)]
                if verbose:
                    print(f"      stride={stride} vertices={n}")
                    for v in entry["vertices"][:3]:
                        print(f"        pos={tuple(round(x,3) for x in v['pos'])} "
                              f"n={tuple(round(x,3) for x in v['normal'])} "
                              f"uv={tuple(round(x,4) for x in v['uv'])}"
                              + (f" lm={tuple(round(x,4) for x in v['lightmap_uv'])}"
                                 if stride == 40 else ""))
                    if n > 3:
                        print(f"        ... ({n - 3} more)")
        elif c.id == "XTVC":
            n = c.size // 16
            entry["vertices"] = [(f32(p, i * 16), f32(p, i * 16 + 4), f32(p, i * 16 + 8))
                                 for i in range(n)]
            if verbose:
                print(f"      box vertices={n}")
                for v in entry["vertices"][:3]:
                    print(f"        {tuple(round(x,3) for x in v)}")
        elif c.id == "ECFC":
            n = c.size // 8
            entry["faces"] = [(u16(p, i * 8), u16(p, i * 8 + 2), u16(p, i * 8 + 4),
                               u16(p, i * 8 + 6)) for i in range(n)]
            if verbose:
                print(f"      box faces={n} (i0,i1,i2,material)")
                for f in entry["faces"][:3]:
                    print(f"        {f}")
        elif c.id == "HSMC":
            entry["decoded"] = decode_hsmc(p)
            if verbose:
                for i, g in enumerate(entry["decoded"]):
                    print(f"      group{i}: ecfc={g['ecfc_count']} xtvc={g['xtvc_count']} "
                          f"tamc={g['tamc_count']} hpsc={g['hpsc_count']} pad={g['pad']}")
        elif c.id == "TAMC":
            entry["decoded"] = decode_tamc(p)
            if verbose:
                print(f"      records={len(entry['decoded'])}")
                for r in entry["decoded"][:3]:
                    print(f"        {r}")
        elif c.id == "HPSC":
            entry["decoded"] = decode_hpsc(p)
            if verbose:
                print(f"      records={len(entry['decoded'])}")
                for r in entry["decoded"][:3]:
                    print(f"        {r}")
        elif c.id == "D3DR":
            entry["decoded"] = decode_d3dr(p)
            if verbose:
                print(f"      {entry['decoded']}")
        elif c.id == "PMTL":
            entry["decoded"] = decode_pmtl(p)
            if verbose:
                for r in entry["decoded"]:
                    print(f"      {r}")
        elif c.id == "XTVM":
            entry["decoded"] = decode_xtvm(p)
            if verbose:
                print(f"      {entry['decoded']}")
        else:
            if verbose:
                print(f"      (marker / undecoded, {c.size} bytes)")
        out["chunks"].append(entry)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def iter_models(path):
    """Yield (name, mef_bytes) for a .res or a bare .mef file."""
    if path.lower().endswith(".mef"):
        yield os.path.basename(path), open(path, "rb").read()
    else:
        yield from iter_mef_models(path)


def selftest(root):
    """Decode every model under root; report counts and any exception."""
    n_models = n_ok = n_err = 0
    n_chunks = 0
    stride_counts = {}
    batch_hdr_counts = {}
    errors = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.lower().endswith(".res"):
                continue
            rp = os.path.join(dirpath, fn)
            try:
                for name, mef in iter_mef_models(rp):
                    n_models += 1
                    try:
                        r = decode_model(name, mef, verbose=False)
                        if r is None:
                            continue
                        n_ok += 1
                        n_chunks += len(r["chunks"])
                        for e in r["chunks"]:
                            if e["id"] == "XTRV" and e.get("stride"):
                                stride_counts[e["stride"]] = stride_counts.get(e["stride"], 0) + 1
                            if e["id"] == "DNER" and e.get("decoded"):
                                for b in e["decoded"]:
                                    if "header_size" in b:
                                        k = b["header_size"]
                                        batch_hdr_counts[k] = batch_hdr_counts.get(k, 0) + 1
                    except Exception as ex:
                        n_err += 1
                        if len(errors) < 10:
                            errors.append((rp, name, f"{type(ex).__name__}: {ex}"))
            except Exception as ex:
                n_err += 1
                if len(errors) < 10:
                    errors.append((rp, None, f"{type(ex).__name__}: {ex}"))
    print(f"selftest root={root}")
    print(f"  models seen      : {n_models}")
    print(f"  models decoded   : {n_ok}")
    print(f"  chunks decoded   : {n_chunks}")
    print(f"  errors           : {n_err}")
    print(f"  XTRV strides     : {stride_counts}")
    print(f"  DNER header sizes: {batch_hdr_counts}")
    for e in errors:
        print("  ERR", e)
    return n_err == 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--selftest":
        return 0 if selftest(argv[1] if len(argv) > 1 else
                             DEFAULT_PC_ROOT) else 1
    limit = None
    if argv[0] == "--limit":
        limit = int(argv[1])
        argv = argv[2:]
    total = 0
    for path in argv:
        for name, mef in iter_models(path):
            if limit is not None and total >= limit:
                break
            decode_model(name, mef, verbose=True)
            total += 1
    print(f"\n{total} models decoded")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
