#!/usr/bin/env python3
"""Verification harness for the Project IGI format parsers.

Runs every parser in igi_formats.py over the whole extracted game tree and
reports, per format, how many files were parsed and whether the parse consumed
exactly the declared size. This is the evidence behind the confidence markers in
reverse/docs/.

    python3 verify_formats.py /path/to/extracted/pc
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import igi_formats as F  # noqa: E402


def walk(root, ext):
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(ext):
                yield os.path.join(dirpath, fn)


def check_ilff(root):
    ok = bad = chunks = 0
    failures = []
    for path in sorted(walk(root, ".res")):
        d = open(path, "rb").read()
        info, errors = F.parse_ilff(d)
        if info and not errors and info["end"] == info["file_size"]:
            ok += 1
            chunks += len(info["chunks"])
        else:
            bad += 1
            failures.append((os.path.relpath(path, root), errors[:1]))
    return ok, bad, chunks, failures


def check_terrain(root, ext, parser, label):
    ok = bad = 0
    failures = []
    for path in sorted(walk(root, ext)):
        d = open(path, "rb").read()
        _items, end = parser(d)
        if end == len(d):
            ok += 1
        else:
            bad += 1
            failures.append((os.path.relpath(path, root), f"consumed {end} of {len(d)}"))
    return ok, bad, failures


def check_ctr_cmd(root):
    out = {}
    # .ctr: fixed-size records (32 bytes in levels 1-13, 44 in level 14);
    # a whole-file alignment check only.
    ok = bad = 0
    failures = []
    for path in sorted(walk(root, ".ctr")):
        d = open(path, "rb").read()
        if len(d) % F.CTR_ITEM_SIZE == 0:
            ok += 1
        else:
            bad += 1
            failures.append((os.path.relpath(path, root),
                             f"{len(d)} % {F.CTR_ITEM_SIZE} != 0"))
    out[".ctr"] = (ok, bad, failures)

    # .cmd: variable-length records 8 + 4*(nt + npv + ncv).  The walk must
    # consume the file exactly and every vertex_offset must equal nt * 4.
    # (A % 8 == 0 file-size check is not an invariant of this format.)
    ok = bad = 0
    failures = []
    for path in sorted(walk(root, ".cmd")):
        d = open(path, "rb").read()
        recs, end = F.parse_cmd(d)
        bad_vo = [r for r in recs if r["vertex_offset"] != r["num_triangle"] * 4]
        if end == len(d) and not bad_vo:
            ok += 1
        else:
            reason = f"walk ended at {end} of {len(d)}"
            if bad_vo:
                reason += f"; {len(bad_vo)} records with vertex_offset != num_triangle*4"
            failures.append((os.path.relpath(path, root), reason))
    out[".cmd"] = (ok, bad, failures)
    return out


def check_mef(root):
    """Parse every model in every models .res and validate the vertex layout."""
    models = 0
    verts = 0
    unit_normals = 0
    total_normals = 0
    strides = {}
    bad = []
    for path in sorted(walk(root, ".res")):
        if os.path.basename(os.path.dirname(path)) != "models":
            continue
        try:
            for name, mef in F.iter_mef_models(path):
                m = F.parse_mef(mef)
                if m is None:
                    bad.append((name, "not ILFF"))
                    continue
                models += 1
                if m["vertex_stride"]:
                    strides[m["vertex_stride"]] = strides.get(m["vertex_stride"], 0) + 1
                verts += len(m["vertices"])
                for v in m["vertices"]:
                    nx, ny, nz = v["normal"]
                    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
                    total_normals += 1
                    if 0.9 < ln < 1.1:
                        unit_normals += 1
        except Exception as exc:  # noqa: BLE001
            bad.append((os.path.relpath(path, root), repr(exc)))
    return models, verts, unit_normals, total_normals, strides, bad


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.normpath(os.path.join(here, "..", "extracted", "pc"))
    root = sys.argv[1] if len(sys.argv) > 1 else default_root
    if not os.path.isdir(root):
        sys.exit(f"game tree not found: {root}\n"
                 f"usage: python3 {os.path.basename(__file__)} /path/to/extracted/pc")
    print(f"root: {root}\n")

    ok, bad, chunks, failures = check_ilff(root)
    print(f"ILFF  .res : {ok} clean / {bad} bad   ({chunks} chunks parsed)")
    for f, e in failures[:5]:
        print(f"        FAIL {f}: {e}")

    for ext, parser, label in ((".bit", F.parse_bit, "BIT"),
                               (".hmp", F.parse_hmp, "HMP"),
                               (".lmp", F.parse_lmp, "LMP")):
        ok, bad, failures = check_terrain(root, ext, parser, label)
        print(f"{label:5s} {ext:5s}: {ok} exact / {bad} mismatch")
        for f, e in failures[:5]:
            print(f"        FAIL {f}: {e}")

    for ext, (ok, bad, failures) in check_ctr_cmd(root).items():
        if ext == ".cmd":
            print(f"CMD   .cmd : {ok} exact / {bad} mismatch "
                  f"(variable-length record walk)")
        else:
            print(f"{ext[1:].upper():5s} {ext:5s}: {ok} aligned / {bad} misaligned")
        for f, e in failures[:5]:
            print(f"        FAIL {f}: {e}")

    models, verts, unit, total, strides, bad = check_mef(root)
    pct = (100.0 * unit / total) if total else 0.0
    print(f"MEF   models: {models} parsed, {verts} vertices, "
          f"{unit}/{total} unit-length normals ({pct:.2f}%)")
    print(f"      vertex strides: {dict(sorted(strides.items()))}")
    for f, e in bad[:5]:
        print(f"        FAIL {f}: {e}")


if __name__ == "__main__":
    main()
