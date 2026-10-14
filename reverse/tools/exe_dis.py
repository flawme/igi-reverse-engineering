#!/usr/bin/env python3
"""IGI.exe static-disassembly helper (radare2 wrapper).

Every query is a one-shot radare2 invocation with clean, reproducible output.
This is the harness used by the IGI.exe analysis pass; see
reverse/docs/16-verified-formats/README.md for what it was used to prove.

Usage:
    python3 exe_dis.py sections
    python3 exe_dis.py strings <regex>            # strings in the whole file
    python3 exe_dis.py search <hexbytes>          # find a byte pattern
    python3 exe_dis.py dis <va> [count]           # disassemble at VA
    python3 exe_dis.py back <va> [count]          # disassemble backwards (find prologue)
    python3 exe_dis.py func <va>                  # define + print function at VA
    python3 exe_dis.py refs <va>                  # code refs to VA (/r, no analysis needed)
    python3 exe_dis.py hexdump <va> <len>
    python3 exe_dis.py imports [regex]
    python3 exe_dis.py exports [regex]

The default binary is <repo>/reverse/extracted/pc/IGI.exe; override with the
IGI_EXE environment variable or a second positional argument.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

_DEFAULT_EXE = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "extracted", "pc", "IGI.exe"))
EXE = os.environ.get("IGI_EXE", _DEFAULT_EXE)


def r2(*cmds: str) -> str:
    argv = ["r2", "-q", "-e", "scr.color=0", "-e", "scr.utf8=false"]
    for c in cmds:
        argv += ["-c", c]
    argv += ["-c", "q", EXE]
    proc = subprocess.run(argv, capture_output=True, text=True)
    return proc.stdout + proc.stderr


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "sections":
        print(r2("iS").strip())
    elif cmd == "strings":
        pat = args[0] if args else "."
        out = r2(f"izz~{pat}")
        print(out.strip())
    elif cmd == "search":
        pat = args[0]
        out = r2(f"/x {pat}")
        print(out.strip())
    elif cmd == "dis":
        va = args[0]
        n = args[1] if len(args) > 1 else "20"
        print(r2(f"pd {n} @ {va}").strip())
    elif cmd == "back":
        va = args[0]
        n = args[1] if len(args) > 1 else "40"
        print(r2(f"pd -{n} @ {va}").strip())
    elif cmd == "func":
        va = args[0]
        print(r2(f"af @ {va}", f"pdf @ {va}").strip())
    elif cmd == "refs":
        va = args[0]
        out = r2(f"/r {va}")
        print(out.strip())
    elif cmd == "hexdump":
        va, ln = args[0], args[1]
        print(r2(f"px {ln} @ {va}").strip())
    elif cmd == "imports":
        pat = args[0] if args else "."
        print(r2(f"ii~{pat}").strip())
    elif cmd == "exports":
        pat = args[0] if args else "."
        print(r2(f"iE~{pat}").strip())
    else:
        print(f"unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
