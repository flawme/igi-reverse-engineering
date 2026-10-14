#!/usr/bin/env python3
"""Deep decoder for Project IGI (1999, Innerloop) terrain tile commands.

Parses a level's terrain.ctr + terrain.cmd and prints the tile tree with the
decoded commands.  Runs on all 14 retail levels.

What this decoder implements (see FINDINGS.md for the evidence):

  .ctr record, levels 1-13 (32 bytes):
      +0x00  int16  children[8]        child tile indices
      +0x10  int8   cmd_transform[8]   per-child transform selector, 0xFF = unused
      +0x18  uint8  children_mask      which of the 8 children are present
      +0x19  uint8  pad[3]             constant 0x40 0x43 0x00 (record 0: zeros)
      +0x1C  uint32 cmd_offset         byte offset into terrain.cmd

  .ctr record, level 14 (44 bytes):
      +0x00  int16  children[8]
      +0x10  int8   cmd_transform[8]
      +0x18  uint8  children_mask
      +0x19  ...    19 extra bytes (see FINDINGS.md; not a cmd_offset)

  .cmd record (all 14 levels), addressed by cmd_offset (levels 1-13) or
  walked linearly (level 14):
      +0x00  uint16 num_triangle
      +0x02  uint16 vertex_offset      == num_triangle * 4
      +0x04  uint16 num_parent_vertex
      +0x06  uint16 num_child_vertex
      +0x08  uint8  triangle[num_triangle][4]   3 x uint8 vertex index + 1 flag byte
      then   uint8  vertex[num_parent_vertex + num_child_vertex][4]
             (the parent vertices first, then the child vertices; the triangle
              indices are 0-based into this concatenated array)

Usage:
    python3 cmd_deep.py <level_dir> [--tree] [--limit N] [--all-levels]
    python3 cmd_deep.py --all-levels <extracted_pc_dir>
"""
from __future__ import annotations

import argparse
import os
import struct
import sys

CTR_RECORD_SIZE = 32          # levels 1-13
CTR_RECORD_SIZE_L14 = 44      # level 14
CMD_HEADER_SIZE = 8
TRI_SIZE = 4
VERTEX_SIZE = 4


# ---------------------------------------------------------------------------
# .ctr
# ---------------------------------------------------------------------------

def parse_ctr(d, stride=CTR_RECORD_SIZE):
    """Parse a terrain.ctr into a list of records.

    Returns (records, errors).  Each record is a dict with children,
    cmd_transform, children_mask, cmd_offset and (level 14) the extra tail.
    """
    errors = []
    if len(d) % stride:
        errors.append(f"ctr size {len(d)} is not a multiple of {stride}")
    n = len(d) // stride
    out = []
    for i in range(n):
        o = i * stride
        rec = {
            "index": i,
            "children": list(struct.unpack_from("<8h", d, o)),
            "cmd_transform": list(d[o + 16:o + 24]),
            "children_mask": d[o + 24],
            "pad": list(d[o + 25:o + 28]),
            "cmd_offset": struct.unpack_from("<I", d, o + 28)[0],
        }
        if stride == CTR_RECORD_SIZE_L14:
            rec["tail"] = d[o + 25:o + 44]
            rec["tail_u32_28"] = struct.unpack_from("<I", d, o + 28)[0]
            rec["tail_u16_30"] = struct.unpack_from("<H", d, o + 30)[0]
            rec["tail_u32_32"] = struct.unpack_from("<I", d, o + 32)[0]
            rec["tail_u32_36"] = struct.unpack_from("<I", d, o + 36)[0]
            rec["tail_u32_40"] = struct.unpack_from("<I", d, o + 40)[0]
        out.append(rec)
    return out, errors


def ctr_stride_for(path):
    """Level 14 ships a 44-byte .ctr record; every other level uses 32."""
    size = os.path.getsize(path)
    if size % CTR_RECORD_SIZE_L14 == 0 and "level14" in path.replace("\\", "/"):
        return CTR_RECORD_SIZE_L14
    return CTR_RECORD_SIZE


# ---------------------------------------------------------------------------
# .cmd
# ---------------------------------------------------------------------------

def parse_cmd_record(d, off):
    """Decode one .cmd record at `off`.

    Returns a dict, or None when the record header is not self-consistent
    (vertex_offset != num_triangle * 4) or the record runs past EOF.
    """
    if off + CMD_HEADER_SIZE > len(d):
        return None
    nt, vo, npv, ncv = struct.unpack_from("<HHHH", d, off)
    if vo != nt * TRI_SIZE:
        return None
    nv = npv + ncv
    end = off + CMD_HEADER_SIZE + nt * TRI_SIZE + nv * VERTEX_SIZE
    if end > len(d):
        return None
    tri_off = off + CMD_HEADER_SIZE
    triangles = []
    for t in range(nt):
        a, b, c, flag = d[tri_off + t * 4: tri_off + t * 4 + 4]
        triangles.append({"v": (a, b, c), "flag": flag})
    vtx_off = tri_off + nt * TRI_SIZE
    vertices = []
    for k in range(nv):
        raw = d[vtx_off + k * 4: vtx_off + k * 4 + 4]
        v = struct.unpack("<I", raw)[0]
        vertices.append({
            "raw": raw,
            "value": v,
            "role": "parent" if k < npv else "child",
            # field decomposition (see FINDINGS.md)
            "x": v & 0x7,                 # bits 0-2
            "b67": (v >> 6) & 0x3,        # bits 6-7
            "y": (v >> 8) & 0x3,          # bits 8-9
            "b15": (v >> 15) & 0x1,       # bit 15
            "c": (v >> 16) & 0xF,         # bits 16-19
            "d": (v >> 21) & 0x1F,        # bits 21-25
            "e": (v >> 27) & 0x1F,        # bits 27-31
        })
    return {
        "offset": off,
        "num_triangle": nt,
        "vertex_offset": vo,
        "num_parent_vertex": npv,
        "num_child_vertex": ncv,
        "num_vertex": nv,
        "length": end - off,
        "end": end,
        "triangles": triangles,
        "vertices": vertices,
    }


def walk_cmd_linear(d):
    """Walk the whole .cmd linearly with the record-length rule.

    Returns (records, consumed, errors).  For every level this consumes the
    file exactly, which is the proof that the record length is
    8 + 4*(num_triangle + num_parent_vertex + num_child_vertex) and that the
    file has no trailer.
    """
    records = []
    errors = []
    off = 0
    while off < len(d):
        rec = parse_cmd_record(d, off)
        if rec is None:
            errors.append(f"@{off}: record header invalid or truncated")
            break
        records.append(rec)
        off = rec["end"]
    return records, off, errors


def index_cmd_records(records):
    return {r["offset"]: r for r in records}


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def validate(ctr, cmd, stride, cmd_records):
    """Cross-check the .ctr against the .cmd.  Returns a stats dict."""
    stats = {
        "ctr_records": len(ctr),
        "cmd_records": len(cmd_records),
        "cmd_size": len(cmd),
        "cmd_consumed": cmd_records[-1]["end"] if cmd_records else 0,
        "offsets_in_bounds": 0,
        "offsets_aligned4": 0,
        "offsets_valid_header": 0,
        "unique_offsets": 0,
        "max_index_ok": 0,
        "max_index_bad": 0,
        "tri_flag_values": {},
        "vertex_role_counts": {"parent": 0, "child": 0},
        "children_in_range": 0,
        "children_out_of_range": 0,
        "transform_values": {},
        "mask_values": {},
        "l14_u40_ok": 0,
    }
    by_off = index_cmd_records(cmd_records)
    offs = []
    for rec in ctr:
        offs.append(rec["cmd_offset"])
        if "tail_u32_40" in rec and rec["index"] >= 1 and \
                rec["tail_u32_40"] == (rec["index"] - 1) * 16:
            stats["l14_u40_ok"] += 1
        for k in range(8):
            if rec["children_mask"] >> k & 1:
                c = rec["children"][k]
                if 0 <= c < len(ctr):
                    stats["children_in_range"] += 1
                else:
                    stats["children_out_of_range"] += 1
        for t in rec["cmd_transform"]:
            stats["transform_values"][t] = stats["transform_values"].get(t, 0) + 1
        stats["mask_values"][rec["children_mask"]] = \
            stats["mask_values"].get(rec["children_mask"], 0) + 1
    stats["unique_offsets"] = len(set(offs))
    for off in set(offs):
        if off + CMD_HEADER_SIZE <= len(cmd):
            stats["offsets_in_bounds"] += 1
        if off % 4 == 0:
            stats["offsets_aligned4"] += 1
        if off in by_off:
            stats["offsets_valid_header"] += 1
    for r in cmd_records:
        nv = r["num_vertex"]
        mx = -1
        for t in r["triangles"]:
            mx = max(mx, *t["v"])
            stats["tri_flag_values"][t["flag"]] = \
                stats["tri_flag_values"].get(t["flag"], 0) + 1
        if mx == nv - 1:
            stats["max_index_ok"] += 1
        else:
            stats["max_index_bad"] += 1
        for v in r["vertices"]:
            stats["vertex_role_counts"][v["role"]] += 1
    return stats


# ---------------------------------------------------------------------------
# printing
# ---------------------------------------------------------------------------

def print_record(rec, indent=0):
    pad = "  " * indent
    print(f"{pad}cmd@{rec['offset']:6d} len={rec['length']:4d} "
          f"nt={rec['num_triangle']:3d} npv={rec['num_parent_vertex']:2d} "
          f"ncv={rec['num_child_vertex']:2d} nv={rec['num_vertex']:2d}")
    for t in rec["triangles"]:
        print(f"{pad}    tri {t['v']} flag={t['flag']:#04x}")
    for k, v in enumerate(rec["vertices"]):
        print(f"{pad}    {v['role'][0].upper()}{k:2d} {v['raw'].hex(' ')}  "
              f"x={v['x']} y={v['y']} c={v['c']} d={v['d']} e={v['e']}")


def print_tree(ctr, cmd_records, limit=None, max_depth=None, stride=CTR_RECORD_SIZE):
    """Print the tile tree from record 1 (record 0 is the all-zero header).

    Levels 1-13: each tile's .cmd record is looked up by its cmd_offset.
    Level 14: the .ctr carries no cmd_offset (its +0x1C field is not one), so
    the .cmd records are attached in linear order as the tree is walked; the
    mapping is flagged as a hypothesis in the output.
    """
    by_off = index_cmd_records(cmd_records)
    linear = stride == CTR_RECORD_SIZE_L14
    root = 1 if len(ctr) > 1 else 0
    seen = set()
    stack = [(root, 0)]
    printed = 0
    cmd_cursor = 0
    while stack:
        idx, depth = stack.pop()
        if idx in seen or idx < 0 or idx >= len(ctr):
            continue
        seen.add(idx)
        if max_depth is not None and depth > max_depth:
            continue
        rec = ctr[idx]
        ch = [rec["children"][k] for k in range(8) if rec["children_mask"] >> k & 1]
        tr = [rec["cmd_transform"][k] for k in range(8) if rec["children_mask"] >> k & 1]
        if linear:
            print(f"{'  ' * depth}#{idx:5d} mask={rec['children_mask']:#04x} "
                  f"children={ch} transform={tr} "
                  f"tail_u16@30={rec['tail_u16_30']:#06x} "
                  f"tail_u32@32={rec['tail_u32_32']:#010x} "
                  f"tail_u32@40={rec['tail_u32_40']}")
        else:
            print(f"{'  ' * depth}#{idx:5d} mask={rec['children_mask']:#04x} "
                  f"children={ch} transform={tr} cmd_offset={rec['cmd_offset']}")
        if linear:
            if cmd_cursor < len(cmd_records):
                print(f"{'  ' * (depth + 1)}"
                      f"(level 14: .cmd record {cmd_cursor} attached in tree order - "
                      f"mapping is a hypothesis)")
                print_record(cmd_records[cmd_cursor], indent=depth + 1)
                cmd_cursor += 1
        else:
            cr = by_off.get(rec["cmd_offset"])
            if cr is not None:
                print_record(cr, indent=depth + 1)
            else:
                print(f"{'  ' * (depth + 1)}(no .cmd record at offset {rec['cmd_offset']})")
        printed += 1
        if limit is not None and printed >= limit:
            break
        for k in reversed(range(8)):
            if rec["children_mask"] >> k & 1:
                stack.append((rec["children"][k], depth + 1))
    print(f"# printed {printed} tile(s); tree reached {len(seen)} record(s) "
          f"of {len(ctr)}")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def analyse_level(level_dir, show_tree=False, limit=None, quiet=False):
    ctr_path = os.path.join(level_dir, "terrain.ctr")
    cmd_path = os.path.join(level_dir, "terrain.cmd")
    if not os.path.exists(ctr_path) or not os.path.exists(cmd_path):
        return None, [f"missing {ctr_path} or {cmd_path}"]
    ctr_bytes = open(ctr_path, "rb").read()
    cmd_bytes = open(cmd_path, "rb").read()
    stride = ctr_stride_for(ctr_path)
    ctr, ctr_errors = parse_ctr(ctr_bytes, stride)
    cmd_records, consumed, cmd_errors = walk_cmd_linear(cmd_bytes)
    stats = validate(ctr, cmd_bytes, stride, cmd_records)
    stats["ctr_stride"] = stride
    stats["ctr_size"] = len(ctr_bytes)
    stats["errors"] = ctr_errors + cmd_errors
    if not quiet:
        name = os.path.basename(os.path.dirname(level_dir))
        print(f"=== {name}  ctr={len(ctr_bytes)} ({stride}B records, {len(ctr)})  "
              f"cmd={len(cmd_bytes)} ({len(cmd_records)} records)")
        print(f"    cmd walk consumed {consumed}/{len(cmd_bytes)} "
              f"{'OK' if consumed == len(cmd_bytes) else 'MISMATCH'}")
        if stride == CTR_RECORD_SIZE_L14:
            print(f"    level 14: the .ctr +0x1C field is NOT a cmd_offset "
                  f"(it holds 0x0C000000|(v<<16)); the .cmd is a linear array.")
            print(f"    level 14: +0x28..+0x2B = {stats['l14_u40_ok']} records "
                  f"with tail_u32@40 == (index-1)*16")
        else:
            print(f"    ctr cmd_offsets: in-bounds {stats['offsets_in_bounds']}/"
                  f"{stats['unique_offsets']} unique, 4-aligned "
                  f"{stats['offsets_aligned4']}/{stats['unique_offsets']}, "
                  f"valid header {stats['offsets_valid_header']}/{stats['unique_offsets']}")
        print(f"    max triangle index == nv-1: {stats['max_index_ok']}/"
              f"{stats['max_index_ok'] + stats['max_index_bad']}")
        print(f"    triangle flag bytes: "
              f"{ {hex(k): v for k, v in sorted(stats['tri_flag_values'].items())} }")
        print(f"    children in range: {stats['children_in_range']} "
              f"(out of range {stats['children_out_of_range']})")
        print(f"    cmd_transform values: "
              f"{ {hex(k): v for k, v in sorted(stats['transform_values'].items())} }")
        for e in stats["errors"]:
            print(f"    ERROR {e}")
    if show_tree:
        print_tree(ctr, cmd_records, limit=limit, stride=stride)
    return stats, stats["errors"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="level dir (contains terrain.ctr/.cmd) or the "
                                 "extracted/pc dir with --all-levels")
    ap.add_argument("--all-levels", action="store_true",
                    help="treat path as the extracted/pc dir and run every level")
    ap.add_argument("--tree", action="store_true", help="print the tile tree")
    ap.add_argument("--limit", type=int, default=None,
                    help="max tiles to print with --tree")
    args = ap.parse_args(argv)

    if args.all_levels:
        base = os.path.join(args.path, "missions", "location0")
        if not os.path.isdir(base):
            base = args.path
        levels = sorted(
            (d for d in os.listdir(base) if d.startswith("level")),
            key=lambda s: int(s[5:]) if s[5:].isdigit() else 0)
        failures = 0
        for lv in levels:
            level_dir = os.path.join(base, lv, "terrain")
            stats, errors = analyse_level(level_dir, show_tree=args.tree,
                                          limit=args.limit)
            if stats is None:
                print(f"=== {lv}: {errors}")
                failures += 1
            elif errors:
                failures += 1
        print(f"\n# {len(levels)} levels processed, {failures} with errors")
        return 1 if failures else 0

    stats, errors = analyse_level(args.path, show_tree=args.tree, limit=args.limit)
    if stats is None:
        print("ERROR:", errors)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
