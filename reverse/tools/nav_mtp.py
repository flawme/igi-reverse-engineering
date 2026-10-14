#!/usr/bin/env python3
"""nav_mtp.py - decoder for two Project IGI (1999, Innerloop Studios) formats.

  1. Navigation graphs  missions/location0/level*/graphs/*.dat
  2. Level master tables missions/location0/level*/level*.mtp

Both decoders were derived from the retail data only (no executable analysis) and
are documented in FINDINGS.md next to this file.  Every claim below cites the
offset it was read from; see FINDINGS.md for the cross-file evidence counts.

Usage:
    python3 nav_mtp.py nav  <graph.dat> [...]
    python3 nav_mtp.py mtp  <level.mtp> [...]
    python3 nav_mtp.py all  <extracted/pc>          # every graph + every .mtp
    python3 nav_mtp.py selftest <extracted/pc>      # parse everything, print a summary

The module is importable: parse_nav(path) and parse_mtp(path) return dicts.
"""

from __future__ import annotations

import glob
import os
import struct
import sys

# ---------------------------------------------------------------------------
# Navigation graph (.dat)
# ---------------------------------------------------------------------------

NAV_MAGIC = 0xCCDDEEFF          # the four bytes cc dd ee ff, as written on disk
NAV_MAGIC_BYTES = b"\xcc\xdd\xee\xff"
NAV_HEADER_SIZE = 0x20          # grid starts here in the 0xCCDDEEFF format
NAV_CELL_SIZE = 8
NAV_SENTINEL = bytes.fromhex("ff ff 00 00 80 bf ff ff")   # (0xFFFF, -1.0f, 0xFFFF)
NAV_SENTINEL_LEGACY = bytes.fromhex("ff ff ff ff 00 00 80 bf")  # (0xFFFFFFFF, -1.0f)

# Tail token table for the 0xCCDDEEFF format:  <TT> <subtype> <value>
#   TT      payload bytes after the type byte (subtype byte + value)
#   0x35    3   subtype 0x07 + uint16 (record marker, first record only)
#   0x04    5   subtype + uint32 pointer-like field (constant per field)
#   0x05    5   subtype 0x05 + uint32
#   0x06    5   subtype 0x06 + float32
#   0x08    25  subtype 0x08 + 3 x float64 (node position)
#   0x09    variable: <subtype> <len> <len bytes>, null-terminated string
NAV_TAIL_FIXED = {0x35: 3, 0x04: 5, 0x05: 5, 0x06: 5, 0x08: 25}
NAV_TAIL_STRING = 0x09

# Token table for the legacy (level 8) format:  <TT> <value>, no subtype byte.
LEGACY_FIXED = {0x05: 4, 0x06: 4, 0x08: 24}
LEGACY_STRING = 0x09

# The record separator of the 0xCCDDEEFF tail: a 0x04 token whose 4-byte value is
# 0x00000735, immediately followed by the 4-byte record marker 35 07 00 00.
# Both are pointer-like constants, identical in every file.
NAV_RECORD_SEP_VALUE = 0x00000735
NAV_RECORD_MARKER = b"\x35\x07\x00\x00"


def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _f32(d, o):
    return struct.unpack_from("<f", d, o)[0]


def _f64(d, o):
    return struct.unpack_from("<d", d, o)[0]


def parse_nav_header(d):
    """32-byte header of the 0xCCDDEEFF navigation graph format.

    Offset  Size  Type    Meaning                          Evidence
    0x00    4     uint32  magic 0xCCDDEEFF                  293/293 files
    0x04    4     uint32  0x0D3AE604 (constant)            293/293
    0x08    4     uint32  0x05050000 (constant)            293/293
    0x0C    4     uint32  grid dimension (100/200/300/400)  293/293
    0x10    4     uint32  0x0FDE0D04 (constant)            293/293
    0x14    4     uint32  0x000A0000 (constant)            293/293
    0x18    2     uint16  0x050A (constant)                293/293
    0x1A    4     uint32  data block size = dim*dim*8       293/293
    0x1E    2     uint16  0xFFFF (constant)                293/293
    0x1C    2     uint16  1/4/10/19 for dim 100/200/300/400 293/293
    """
    return {
        "magic": _u32(d, 0x00),
        "unk04": _u32(d, 0x04),
        "unk08": _u32(d, 0x08),
        "dim": _u32(d, 0x0C),
        "unk10": _u32(d, 0x10),
        "unk14": _u32(d, 0x14),
        "unk18": _u16(d, 0x18),
        "size": _u32(d, 0x1A),
        "unk1C": _u16(d, 0x1C),
        "unk1E": _u16(d, 0x1E),
    }


def tokenize_nav_tail(t):
    """Tokenize the 0xCCDDEEFF tail.  Returns a list of (offset, type, payload)."""
    toks = []
    i = 0
    while i < len(t):
        tt = t[i]
        if tt == NAV_TAIL_STRING:
            if i + 3 > len(t):
                raise ValueError(f"truncated 0x09 token at {i}")
            ln = t[i + 2]
            if i + 3 + ln > len(t):
                raise ValueError(f"0x09 token overruns at {i}")
            toks.append((i, tt, t[i + 1:i + 3 + ln]))
            i += 3 + ln
        elif tt in NAV_TAIL_FIXED:
            n = NAV_TAIL_FIXED[tt]
            if i + 1 + n > len(t):
                raise ValueError(f"truncated 0x{tt:02x} token at {i}")
            toks.append((i, tt, t[i + 1:i + 1 + n]))
            i += 1 + n
        else:
            raise ValueError(f"unknown token type 0x{tt:02x} at {i}")
    return toks


def _tail_token_value(tt, pl):
    """Decode one tail token payload into a python value.

    `pl` is the payload after the type byte, i.e. <subtype> <value>.
    """
    if tt == 0x35:
        return _u16(pl, 1)
    if tt == 0x04:
        return _u32(pl, 1)          # pointer-like; subtype byte pl[0]
    if tt == 0x05:
        return _u32(pl, 1)
    if tt == 0x06:
        return _f32(pl, 1)
    if tt == 0x08:
        return (_f64(pl, 1), _f64(pl, 9), _f64(pl, 17))
    if tt == 0x09:
        ln = pl[1]
        return pl[2:2 + ln].rstrip(b"\x00").decode("latin-1")
    return None


def parse_nav_tail(t):
    """Split the tail into node records and an edge list.

    Layout (verified on all 293 0xCCDDEEFF files):
        [35 07 00 00] [record 1] [04 CE 35 07 00 00] [record 2] ... [edge list]
    A node record carries: 0x05 node id, 0x08 position (3 x float64),
    0x06 floats, 0x09 criteria string.  The trailing edge list is a run of
    (0x04 target, 0x05 cost) token pairs.
    """
    toks = tokenize_nav_tail(t)
    records = []
    cur = None
    for off, tt, pl in toks:
        starts_record = (tt == 0x35) or (tt == 0x04 and pl[1:5] == NAV_RECORD_MARKER)
        if starts_record:
            if cur is not None:
                records.append(cur)
            cur = {"off": off, "tokens": []}
            if tt == 0x35:
                continue
        if cur is None:
            continue
        cur["tokens"].append((tt, pl))
    if cur is not None:
        records.append(cur)

    nodes = []
    edges = []
    for r in records:
        toks_r = r["tokens"]
        # A node record ends at its 0x09 criteria string; anything after that
        # inside the same record is the trailing edge list.
        split = len(toks_r)
        for i, (tt, _) in enumerate(toks_r):
            if tt == 0x09:
                split = i + 1
                break
        node_toks, edge_toks = toks_r[:split], toks_r[split:]
        if any(tt == 0x08 for tt, _ in node_toks):
            node = {"off": r["off"], "id": None, "pos": None, "floats": [],
                    "criteria": None, "pointers": []}
            for tt, pl in node_toks:
                if tt == 0x05:
                    v = _u32(pl, 1)
                    if node["id"] is None:
                        node["id"] = v
                    else:
                        node["floats"].append(v)
                elif tt == 0x06:
                    node["floats"].append(_f32(pl, 1))
                elif tt == 0x08:
                    node["pos"] = (_f64(pl, 1), _f64(pl, 9), _f64(pl, 17))
                elif tt == 0x09:
                    ln = pl[1]
                    node["criteria"] = pl[2:2 + ln].rstrip(b"\x00").decode("latin-1")
                elif tt == 0x04:
                    node["pointers"].append((pl[0], _u32(pl, 1)))
            nodes.append(node)
        else:
            edge_toks = node_toks
        # edge list: consecutive (0x04 target, 0x05 cost) pairs
        pend = None
        for tt, pl in edge_toks:
            if tt == 0x04:
                pend = _u32(pl, 1)
            elif tt == 0x05 and pend is not None:
                edges.append((pend, _u32(pl, 1)))
                pend = None
    return nodes, edges


def parse_nav(path):
    """Parse a navigation graph .dat.  Returns a dict.

    Two on-disk variants exist:
      * 0xCCDDEEFF  - header + grid + tail token stream (293 files)
      * legacy      - tail token stream + grid, no magic (7 files, all level 8)
    """
    d = open(path, "rb").read()
    out = {"path": path, "size": len(d), "format": None}

    if len(d) >= 4 and d[:4] == NAV_MAGIC_BYTES:
        out["format"] = "magic"
        hdr = parse_nav_header(d)
        out["header"] = hdr
        dim, size = hdr["dim"], hdr["size"]
        grid = d[NAV_HEADER_SIZE:NAV_HEADER_SIZE + size]
        tail = d[NAV_HEADER_SIZE + size:]
        if len(grid) != dim * dim * NAV_CELL_SIZE:
            raise ValueError(f"{path}: grid size {len(grid)} != dim*dim*8")
        out["grid_off"] = NAV_HEADER_SIZE
        out["tail_off"] = NAV_HEADER_SIZE + size
        out["grid"] = grid
        out["tail"] = tail
        out["dim"] = dim
        records, edges = parse_nav_tail(tail)
        out["nodes"] = records
        out["edges"] = edges
        out["sentinel"] = NAV_SENTINEL
        out["dist_off"] = 2
    else:
        # legacy: token stream first, then a dim*dim*8 grid at the end
        out["format"] = "legacy"
        if len(d) < 80000:
            raise ValueError(f"{path}: too short for the legacy layout")
        grid = d[len(d) - 80000:]
        stream = d[:len(d) - 80000]
        out["dim"] = 100
        out["grid_off"] = len(d) - 80000
        out["tail_off"] = 0
        out["grid"] = grid
        out["tail"] = stream
        out["sentinel"] = NAV_SENTINEL_LEGACY
        out["dist_off"] = 4
        out["nodes"], out["edges"] = _parse_legacy_stream(stream)
    out["grid_stats"] = grid_stats(out["grid"], out["dim"], out["sentinel"], out["dist_off"])
    return out


def _tokenize_legacy(t):
    toks = []
    i = 0
    while i < len(t):
        tt = t[i]
        if tt == LEGACY_STRING:
            if i + 2 > len(t):
                raise ValueError(f"truncated 0x09 token at {i}")
            ln = t[i + 1]
            if i + 2 + ln > len(t):
                raise ValueError(f"0x09 token overruns at {i}")
            toks.append((i, tt, t[i + 1:i + 2 + ln]))
            i += 2 + ln
        elif tt in LEGACY_FIXED:
            n = LEGACY_FIXED[tt]
            if i + 1 + n > len(t):
                raise ValueError(f"truncated 0x{tt:02x} token at {i}")
            toks.append((i, tt, t[i + 1:i + 1 + n]))
            i += 1 + n
        else:
            raise ValueError(f"unknown legacy token type 0x{tt:02x} at {i}")
    return toks


def _parse_legacy_stream(stream):
    """Legacy stream: header record, node records, then one edge record.

    A record ends at a 0x09 (string) token.  A record with no 0x08 (position)
    token is the edge list: a flat uint32 run of (a, b, cost) triples.
    The stream ends with a 7-byte grid trailer `00 0A 05 <uint32 size>`
    (all 7 legacy files: size = 80000).
    """
    trailer = b"\x00\x0a\x05"
    if stream[-7:-4] == trailer:
        stream = stream[:-7]
    toks = _tokenize_legacy(stream)
    recs = []
    cur = []
    for off, tt, pl in toks:
        if tt == 0x05:
            cur.append(("u32", _u32(pl, 0)))
        elif tt == 0x06:
            cur.append(("f32", _f32(pl, 0)))
        elif tt == 0x08:
            cur.append(("pos", (_f64(pl, 0), _f64(pl, 8), _f64(pl, 16))))
        elif tt == 0x09:
            cur.append(("str", pl[1:1 + pl[0]].rstrip(b"\x00").decode("latin-1")))
            recs.append(cur)
            cur = []
    if cur:
        recs.append(cur)
    nodes = []
    edges = []
    for r in recs:
        if any(k == "pos" for k, _ in r):
            pos = next(v for k, v in r if k == "pos")
            # the node id is the last uint32 before the position token
            pre = []
            for k, v in r:
                if k == "pos":
                    break
                if k == "u32":
                    pre.append(v)
            nodes.append({"id": pre[-1] if pre else None, "pos": pos,
                          "floats": pre[:-1],
                          "criteria": next((v for k, v in r if k == "str"), None)})
        else:
            flat = [v for k, v in r if k == "u32"]
            # The edge record starts with a short header (4 values in
            # level8/graph1.dat, 5 in the other six legacy files) followed by
            # (a, b, cost) triples whose cost is always 1.  Pick the header
            # length that makes the triples line up and every cost equal 1.
            edges = []
            for n in range(0, 9):
                if (len(flat) - n) % 3:
                    continue
                tri = [(flat[i], flat[i + 1], flat[i + 2])
                       for i in range(n, len(flat), 3)]
                if all(c == 1 for _, _, c in tri):
                    edges = tri
                    break
    return nodes, edges


def grid_stats(grid, dim, sentinel, dist_off=2):
    """Summarise the distance matrix: populated cells, symmetry, value range.

    dist_off is the byte offset of the float32 distance inside a cell:
    2 for the 0xCCDDEEFF layout (uint16, float32, uint16) and 4 for the legacy
    layout (uint32 cost, float32 distance).
    """
    cells = [grid[i * NAV_CELL_SIZE:(i + 1) * NAV_CELL_SIZE] for i in range(dim * dim)]
    populated = {}
    for i, c in enumerate(cells):
        if c != sentinel:
            populated[i] = c
    sym = pairs = 0
    for i, c in populated.items():
        x, y = i % dim, i // dim
        if x == y:
            continue
        j = y * dim + x
        if j in populated:
            pairs += 1
            if c[dist_off:dist_off + 4] == populated[j][dist_off:dist_off + 4]:
                sym += 1
    dists = []
    costs = []
    for i, c in populated.items():
        v = _f32(c, dist_off)
        if v >= 0:
            dists.append(v)
        costs.append(_u32(c, 0) if dist_off == 4 else _u16(c, 6))
    return {
        "cells": dim * dim,
        "populated": len(populated),
        "symmetric_pairs": f"{sym}/{pairs}",
        "dist_min": min(dists) if dists else None,
        "dist_max": max(dists) if dists else None,
        "no_path_cells": sum(1 for i, c in populated.items() if _f32(c, dist_off) < 0),
        "last_cell": cells[-1].hex(" ") if cells else None,
    }


def describe_nav(path, verbose=True):
    g = parse_nav(path)
    lines = []
    lines.append(f"== {path}  ({g['size']} bytes, format={g['format']})")
    if g["format"] == "magic":
        h = g["header"]
        lines.append(f"   header: magic=0x{h['magic']:08X} dim={h['dim']} size={h['size']} "
                     f"unk04=0x{h['unk04']:08X} unk08=0x{h['unk08']:08X} unk10=0x{h['unk10']:08X} "
                     f"unk14=0x{h['unk14']:08X} unk18=0x{h['unk18']:04X} unk1C={h['unk1C']} unk1E=0x{h['unk1E']:04X}")
        lines.append(f"   grid @0x{g['grid_off']:X}  {g['dim']}x{g['dim']} x 8 bytes   tail @0x{g['tail_off']:X} ({len(g['tail'])} bytes)")
    else:
        lines.append(f"   legacy layout: token stream {len(g['tail'])} bytes, grid @0x{g['grid_off']:X}")
    s = g["grid_stats"]
    lines.append(f"   grid: populated={s['populated']}/{s['cells']} no_path={s['no_path_cells']} "
                 f"symmetric={s['symmetric_pairs']} dist=[{s['dist_min']}, {s['dist_max']}] last_cell={s['last_cell']}")
    lines.append(f"   nodes: {len(g['nodes'])}")
    if verbose:
        for n in g["nodes"][:12]:
            pos = n["pos"]
            pos_s = "(" + ", ".join(f"{v:.2f}" for v in pos) + ")" if pos else "None"
            lines.append(f"     id={n['id']} pos={pos_s} floats={n['floats']} criteria={n['criteria']!r}")
        if len(g["nodes"]) > 12:
            lines.append(f"     ... {len(g['nodes']) - 12} more")
    lines.append(f"   edges: {len(g['edges'])}")
    if verbose and g["edges"]:
        lines.append(f"     first 8: {g['edges'][:8]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Level master table (.mtp)
# ---------------------------------------------------------------------------

MTP_FORM = b"MTP "


def parse_mtp(path):
    """Parse a .mtp: big-endian IFF container with little-endian payload ints.

    Chunks (all 17 retail files): BANM, SNDS, SVOL, MODS, VNAM, INST, TEXF,
    PALF, GTT .  See FINDINGS.md for the per-chunk layouts.
    """
    d = open(path, "rb").read()
    if d[:4] != b"FORM":
        raise ValueError(f"{path}: not a FORM container")
    declared = struct.unpack_from(">I", d, 4)[0]
    form = d[8:12]
    chunks = []
    off = 12
    while off + 8 <= len(d):
        tag = d[off:off + 4]
        csz = struct.unpack_from(">I", d, off + 4)[0]
        payload = d[off + 8:off + 8 + csz]
        if len(payload) != csz:
            raise ValueError(f"{path}: chunk {tag!r} overruns")
        chunks.append({"tag": tag, "size": csz, "off": off + 8, "payload": payload})
        off += 8 + csz
    out = {"path": path, "size": len(d), "declared": declared, "form": form,
           "chunks": chunks, "trailing": len(d) - off}
    by_tag = {c["tag"]: c for c in chunks}

    def names(tag):
        c = by_tag.get(tag)
        if c is None:
            return []
        cnt = _u32(c["payload"], 0)
        return [n.decode("latin-1") for n in c["payload"][4:].split(b"\x00")[:cnt]]

    out["models"] = names(b"MODS")
    out["textures"] = names(b"TEXF")

    v = by_tag.get(b"VNAM")
    if v is not None:
        cnt = _u32(v["payload"], 0)
        offs = struct.unpack_from("<%dI" % cnt, v["payload"], 4)
        blob = v["payload"][4 + 4 * cnt:]
        out["vnam"] = {
            "count": cnt,
            "offsets": list(offs),
            "names": [n.decode("latin-1") for n in blob.split(b"\x00")[:cnt]],
            "blob_size": len(blob),
            "monotonic": all(offs[i] <= offs[i + 1] for i in range(len(offs) - 1)),
        }
    ins = by_tag.get(b"INST")
    if ins is not None:
        p = ins["payload"]
        out["inst"] = {
            "size": len(p),
            "u32": list(struct.unpack_from("<%dI" % (len(p) // 4), p, 0)),
        }
    g = by_tag.get(b"GTT ")
    if g is not None:
        cnt = _u32(g["payload"], 0)
        recs = [struct.unpack_from("<II", g["payload"], 4 + 8 * i) for i in range(cnt)]
        out["gtt"] = {"count": cnt, "records": recs}
    for tag in (b"BANM", b"SNDS", b"SVOL", b"PALF"):
        c = by_tag.get(tag)
        if c is not None:
            out[tag.decode().strip()] = _u32(c["payload"], 0) if c["size"] >= 4 else None
    return out


def describe_mtp(path, verbose=True):
    m = parse_mtp(path)
    lines = [f"== {path}  ({m['size']} bytes, declared {m['declared']}, form {m['form']!r})"]
    for c in m["chunks"]:
        extra = ""
        if c["tag"] in (b"MODS", b"TEXF", b"VNAM", b"GTT "):
            extra = f" count={_u32(c['payload'], 0)}"
        elif c["size"] == 4:
            extra = f" value={_u32(c['payload'], 0)}"
        lines.append(f"   {c['tag'].decode('latin-1')} size={c['size']:6d} @0x{c['off']:06X}{extra}")
    lines.append(f"   MODS models={len(m['models'])}  TEXF textures={len(m['textures'])}")
    if "vnam" in m:
        v = m["vnam"]
        lines.append(f"   VNAM count={v['count']} blob={v['blob_size']} monotonic={v['monotonic']} "
                     f"max_offset={max(v['offsets']) if v['offsets'] else 0} "
                     f"names==MODS:{v['names'] == m['models']}")
    if "inst" in m:
        u = m["inst"]["u32"]
        lines.append(f"   INST size={m['inst']['size']} u32={len(u)} max={max(u) if u else 0}")
    if "gtt" in m:
        g = m["gtt"]
        vals = set(r[1] for r in g["records"])
        lines.append(f"   GTT count={g['count']} second_field_values={sorted(vals)} "
                     f"first_field_is_index={all(r[0] == i for i, r in enumerate(g['records']))}")
    if verbose:
        lines.append(f"   first models: {m['models'][:5]}")
        lines.append(f"   first textures: {m['textures'][:5]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _iter_tree(root):
    navs = sorted(glob.glob(os.path.join(root, "missions/location0/level*/graphs/*.dat")))
    mtps = sorted(glob.glob(os.path.join(root, "**/*.mtp"), recursive=True))
    return navs, mtps


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    mode = argv[1]
    if mode == "nav":
        for p in argv[2:]:
            print(describe_nav(p))
        return 0
    if mode == "mtp":
        for p in argv[2:]:
            print(describe_mtp(p))
        return 0
    if mode in ("all", "selftest"):
        root = argv[2] if len(argv) > 2 else "."
        navs, mtps = _iter_tree(root)
        ok = fail = 0
        for p in navs:
            try:
                g = parse_nav(p)
                if mode == "all":
                    print(describe_nav(p, verbose=False))
                ok += 1
            except Exception as e:                       # noqa: BLE001
                print(f"FAIL {p}: {e}")
                fail += 1
        for p in mtps:
            try:
                m = parse_mtp(p)
                if mode == "all":
                    print(describe_mtp(p, verbose=False))
                ok += 1
            except Exception as e:                       # noqa: BLE001
                print(f"FAIL {p}: {e}")
                fail += 1
        print(f"selftest: {ok} files parsed, {fail} failures "
              f"({len(navs)} nav graphs, {len(mtps)} .mtp)")
        return 0 if fail == 0 else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
