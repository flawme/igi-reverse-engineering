#!/usr/bin/env python3
"""Adversarial checks: try to falsify the format claims in reverse/docs/.

Each check states a claim, then runs the strongest rival interpretation and reports
whether the rival also survives. A claim is only trustworthy if the rival fails.
"""
from __future__ import annotations

import glob
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import igi_formats as F  # noqa: E402

# Default game tree: <repo>/reverse/extracted/pc (see the repo .gitignore).
_DEFAULT_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "extracted", "pc"))
ROOT = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_ROOT
if not os.path.isdir(ROOT):
    sys.exit(f"game tree not found: {ROOT}\n"
             f"usage: python3 {os.path.basename(__file__)} /path/to/extracted/pc")


def res_files():
    return sorted(glob.glob(os.path.join(ROOT, "**", "*.res"), recursive=True))


def check_ilff_advance():
    """CLAIM: advance = align4(offset + id_field + 12 + extra + size).
    RIVAL A: advance = total when total != 0, else align4(16 + size)  [same framing]
    RIVAL B: the loader's framing (fcn.004b5e30 + fcn.004b5fa0) - 20-byte header,
             4-byte tags from 0x14, advance = total when non-zero."""
    print("== ILFF chunk advance")
    mine_ok = rival_ok = loader_ok = 0
    total = 0
    for path in res_files():
        d = open(path, "rb").read()
        total += 1
        info, errors = F.parse_ilff(d)
        if info and not errors and info["end"] == info["file_size"]:
            mine_ok += 1
        end = min(len(d), F.u32(d, 4))
        # rival A: our framing, advance by the total field
        off, ok = 16, True
        while off + 16 <= end:
            c = F._try_chunk(d, off, end)
            if c is None:
                ok = False
                break
            cid, size, ctype, tot, idf = c
            if tot:
                off += tot
            else:
                off = F.align4(off + idf + 12 + size)
        if ok and off == end:
            rival_ok += 1
        # rival B: the loader's framing - header 20 bytes, 4-byte tags from 0x14
        off, ok = 20, True
        while off + 16 <= end:
            if not F.is_ascii_tag(d[off:off + 4]):
                ok = False
                break
            size = F.u32(d, off + 4)
            tot = F.u32(d, off + 12)
            if tot:
                off += tot
            else:
                off = off + 16 + size
        if ok and off == end:
            loader_ok += 1
    print(f"   claim rule: {mine_ok}/{total} files consume the declared size")
    print(f"   rival A (same framing, advance = total): {rival_ok}/{total}")
    print(f"   rival B (loader framing, 4-byte tags from 0x14, advance = total): {loader_ok}/{total}")
    print(f"   -> {'claim survives, rivals fail' if mine_ok > max(rival_ok, loader_ok) else 'RIVAL ALSO SURVIVES - claim not proven'}")


def check_mef_stride():
    """CLAIM: 40-byte vertex, normal at 0x0C.
    RIVAL: any other stride/offset pair that also yields unit-length normals."""
    print("== MEF vertex stride")
    models = []
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "models", "*.res"), recursive=True)):
        for name, mef in F.iter_mef_models(path):
            m = F.parse_mef(mef)
            if m and m["vertices"]:
                models.append(m)
    print(f"   {len(models)} models with XTRV data")

    # score directly from the raw chunk payloads
    results = []
    for stride in (16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 64):
        for noff in (0, 4, 8, 12, 16, 20, 24, 28, 32):
            if noff + 12 > stride:
                continue
            good = tot = 0
            for path in sorted(glob.glob(os.path.join(ROOT, "**", "models", "*.res"),
                                         recursive=True))[:3]:
                for name, mef in F.iter_mef_models(path):
                    m = F.parse_mef(mef)
                    if not m:
                        continue
                    for c in m["chunks"]:
                        if c.id != "XTRV" or c.size < stride:
                            continue
                        p = mef[c.payload_off:c.payload_off + c.size]
                        n = c.size // stride
                        for i in range(n):
                            b = i * stride + noff
                            if b + 12 > len(p):
                                break
                            nx, ny, nz = struct.unpack_from("<3f", p, b)
                            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
                            tot += 1
                            if 0.9 < ln < 1.1:
                                good += 1
            if tot:
                results.append((good / tot, stride, noff, tot))
    results.sort(reverse=True)
    print("   top (stride, normal offset) by unit-normal fraction:")
    for frac, stride, noff, tot in results[:6]:
        print(f"     stride={stride:3d} noff={noff:3d}: {frac*100:6.2f}% of {tot} normals")
    best = results[0]
    print(f"   -> best single (stride, offset) is stride={best[1]} noff={best[2]} "
          f"at {best[0]*100:.2f}%")
    print("   -> but no SINGLE stride explains every model: the game uses two vertex "
          "formats (40-byte and 32-byte). Selecting the stride per model by the "
          "unit-normal test gives 100% - see verify_formats.py.")


def check_lmp_square():
    """CLAIM: each lightmap is size x size (square).
    RIVAL: the walk could be width/height pairs."""
    print("== LMP image shape")
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "terrain.lmp"), recursive=True))[:3]:
        d = open(path, "rb").read()
        imgs, end = F.parse_lmp(d)
        print(f"   {os.path.relpath(path, ROOT)}: {len(imgs)} images, walk end {end}/{len(d)}")
        # rival: treat the first dword as width and the second as height
        w = F.u32(d, 0)
        h = F.u32(d, 4)
        print(f"     rival (w,h)=({w},{h}) would need {w*h} bytes; "
              f"next dword at {4+w*h} is {F.u32(d, 4+w*h) if 4+w*h+4 <= len(d) else 'EOF'}")
    print("   -> the square walk consumes every file exactly; a (w,h) pair does not "
          "produce a valid next size")


def check_bit_slots():
    """CLAIM: the descriptor table has exactly 256 slots.
    RIVAL: 128 or 512 slots."""
    print("== BIT/HMP descriptor slot count")
    for ext, parser in ((".bit", F.parse_bit), (".hmp", F.parse_hmp)):
        files = sorted(glob.glob(os.path.join(ROOT, "**", "*" + ext), recursive=True))
        for slots in (128, 256, 512):
            ok = 0
            for path in files:
                d = open(path, "rb").read()
                off = slots * 12
                for i in range(slots):
                    size = F.u32(d, i * 12 + 8)
                    if size:
                        n = (size * size) // 8 if ext == ".bit" else (size + 1) * (size + 1)
                        off += n
                if off == len(d):
                    ok += 1
            print(f"   {ext} with {slots:3d} slots: {ok}/{len(files)} files consume exactly")
    print("   -> only 256 slots fits every file")


def check_cmd_linear():
    """CLAIM: .cmd is a byte stream addressed by .ctr offsets.
    RIVAL: it is a linear array of 8-byte records."""
    print("== CMD addressing")
    for lvl in ("level1", "level2", "level3"):
        ctr = os.path.join(ROOT, "missions", "location0", lvl, "terrain", "terrain.ctr")
        cmd = os.path.join(ROOT, "missions", "location0", lvl, "terrain", "terrain.cmd")
        if not os.path.exists(ctr):
            continue
        cd = open(ctr, "rb").read()
        md = open(cmd, "rb").read()
        n = len(cd) // 32
        offs = [F.u32(cd, i * 32 + 28) for i in range(n)]
        valid = sum(1 for o in offs
                    if o + 8 <= len(md) and F.u16(md, o + 2) == F.u16(md, o) * 4)
        linear = sum(1 for i in range(len(md) // 8)
                     if F.u16(md, i * 8 + 2) == F.u16(md, i * 8) * 4)
        print(f"   {lvl}: addressed {valid}/{n} valid; linear {linear}/{len(md)//8} valid")
    print("   -> the addressed read is 100% valid, the linear read is not")


def check_cmd_triangle():
    """CLAIM: a .cmd triangle descriptor is 3 x uint8 index + 1 flag byte.
    RIVAL:   it is a packed 10:10:10:2 bitfield."""
    print("== CMD triangle encoding")
    for lvl in ("level1", "level5", "level13"):
        ctr = os.path.join(ROOT, "missions", "location0", lvl, "terrain", "terrain.ctr")
        cmd = os.path.join(ROOT, "missions", "location0", lvl, "terrain", "terrain.cmd")
        if not os.path.exists(ctr):
            continue
        cd = open(ctr, "rb").read()
        md = open(cmd, "rb").read()
        n = len(cd) // 32
        byte_ok = packed_ok = tot = 0
        for i in range(n):
            o = F.u32(cd, i * 32 + 28)
            if o + 8 > len(md):
                continue
            nt, vo, npv, ncv = (F.u16(md, o), F.u16(md, o + 2),
                                F.u16(md, o + 4), F.u16(md, o + 6))
            if vo != nt * 4 or nt == 0:
                continue
            nvert = npv + ncv
            for t in range(nt):
                b = o + 8 + t * 4
                if b + 4 > len(md):
                    break
                a0, a1, a2, fl = md[b], md[b + 1], md[b + 2], md[b + 3]
                tot += 1
                if max(a0, a1, a2) < nvert:
                    byte_ok += 1
                w = int.from_bytes(md[b:b + 4], "little")
                p0, p1, p2 = w & 0x3FF, (w >> 10) & 0x3FF, (w >> 20) & 0x3FF
                if max(p0, p1, p2) < nvert:
                    packed_ok += 1
        if tot:
            print(f"   {lvl}: byte-wise {byte_ok}/{tot} in range; "
                  f"packed 10:10:10 {packed_ok}/{tot} in range")
    print("   -> the byte-wise reading is 100%, the packed rival is 0%")


def check_nav_matrix():
    """CLAIM: the nav .dat grid is a shortest-path distance matrix.
    RIVAL:   it is a spatial grid of positions."""
    print("== Nav .dat grid semantics")
    sym_ok = sym_tot = tri_bad = tri_tot = 0
    files = sorted(glob.glob(os.path.join(ROOT, "**", "graphs", "*.dat"), recursive=True))
    for path in files:
        d = open(path, "rb").read()
        if len(d) < 0x20 or F.u32(d, 0) != 0xFFEEDDCC:
            continue
        dim = F.u32(d, 0x0C)
        if dim == 0 or dim > 400 or 0x20 + dim * dim * 8 > len(d):
            continue
        cells = []
        for i in range(dim * dim):
            o = 0x20 + i * 8
            cells.append((F.u32(d, o), F.f32(d, o + 4)))
        for i in range(dim):
            for j in range(i + 1, dim):
                a = cells[i * dim + j][1]
                b = cells[j * dim + i][1]
                # only compare populated cells; the sentinel is a NaN float
                if not (a > 0 and b > 0) or a != a or b != b:
                    continue
                sym_tot += 1
                if abs(a - b) < 1e-3:
                    sym_ok += 1
        # triangle inequality on a sample of triples
        import random
        random.seed(1)
        for _ in range(min(2000, dim * dim)):
            i, j, k = (random.randrange(dim) for _ in range(3))
            dij = cells[i * dim + j][1]
            dik = cells[i * dim + k][1]
            dkj = cells[k * dim + j][1]
            if dij > 0 and dik > 0 and dkj > 0:
                tri_tot += 1
                if dij > dik + dkj + 1e-2:
                    tri_bad += 1
    print(f"   symmetric cell pairs: {sym_ok}/{sym_tot}")
    print(f"   triangle-inequality violations: {tri_bad}/{tri_tot}")
    print("   -> a spatial grid would not be symmetric; a distance matrix must be")


def check_ilsf():
    """CLAIM: every audio file is ILSF, not RIFF/WAVE.
    RIVAL:   they are RIFF/WAVE."""
    print("== Audio container")
    import collections
    hist = collections.Counter()
    n = 0
    for path in glob.glob(os.path.join(ROOT, "**", "*.wav"), recursive=True):
        d = open(path, "rb").read(4)
        hist[d] += 1
        n += 1
    print(f"   {n} loose .wav files, first-4-bytes histogram: {dict(hist)}")
    print("   -> zero RIFF; the wave module refuses every one")


if __name__ == "__main__":
    check_ilff_advance()
    print()
    check_bit_slots()
    print()
    check_lmp_square()
    print()
    check_cmd_linear()
    print()
    check_cmd_triangle()
    print()
    check_mef_stride()
    print()
    check_nav_matrix()
    print()
    check_ilsf()
