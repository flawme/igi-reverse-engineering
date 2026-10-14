#!/usr/bin/env python3
"""End-to-end verification: run every decoder in reverse/tools over the whole tree.

This is the single command that reproduces every pass count quoted in reverse/docs/.

    python3 reverse/tools/verify_all.py /path/to/extracted/pc
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Default game tree: <repo>/reverse/extracted/pc (see the repo .gitignore).
DEFAULT_ROOT = os.path.normpath(os.path.join(HERE, "..", "extracted", "pc"))
ROOT = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
if not os.path.isdir(ROOT):
    sys.exit(f"game tree not found: {ROOT}\n"
             f"usage: python3 {os.path.basename(__file__)} /path/to/extracted/pc")


def run(label, argv, expect_zero=True):
    proc = subprocess.run(argv, capture_output=True, text=True)
    ok = (proc.returncode == 0) if expect_zero else True
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    tail = (proc.stdout or proc.stderr).strip().splitlines()
    for line in tail[-4:]:
        print(f"        {line}")
    return ok


def main():
    results = []

    results.append(run("igi_formats / verify_formats over the whole tree",
                       [sys.executable, os.path.join(HERE, "verify_formats.py"), ROOT]))

    results.append(run("adversarial_checks (rival interpretations must fail)",
                       [sys.executable, os.path.join(HERE, "adversarial_checks.py"), ROOT]))

    # LOOP: decode every .tex and every .res, count textures
    sys.path.insert(0, HERE)
    import loop  # noqa: E402

    files = sorted(glob.glob(os.path.join(ROOT, "**", "*.tex"), recursive=True)) + \
        sorted(glob.glob(os.path.join(ROOT, "**", "*.res"), recursive=True))
    total = 0
    failures = []
    for path in files:
        try:
            total += len(loop.load(path))
        except Exception as exc:  # noqa: BLE001
            failures.append((os.path.relpath(path, ROOT), repr(exc)))
    ok = not failures
    print(f"[{'PASS' if ok else 'FAIL'}] LOOP decoder: {total} textures from {len(files)} files, "
          f"{len(failures)} failures")
    for f, e in failures[:5]:
        print(f"        FAIL {f}: {e}")
    results.append(ok)

    # QVM: disassemble every .qvm
    import qvm  # noqa: E402

    qfiles = sorted(glob.glob(os.path.join(ROOT, "**", "*.qvm"), recursive=True))
    qok = 0
    qins = 0
    qfail = []
    for path in qfiles:
        try:
            q = qvm.QVM(open(path, "rb").read(), path)
            qins += len(q.instructions)
            qok += 1
        except Exception as exc:  # noqa: BLE001
            qfail.append((os.path.relpath(path, ROOT), repr(exc)))
    ok = not qfail
    print(f"[{'PASS' if ok else 'FAIL'}] QVM disassembler: {qok}/{len(qfiles)} files clean, "
          f"{qins} instructions decoded, {len(qfail)} failures")
    for f, e in qfail[:5]:
        print(f"        FAIL {f}: {e}")
    results.append(ok)

    print()
    print(f"{sum(1 for r in results if r)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
