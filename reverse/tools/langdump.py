#!/usr/bin/env python3
"""Dump the Project IGI localisation resources.

`pc/language/<lang>/*.res` are ILFF archives of NAME/CSTR pairs: a string key and its
translated text. The keys are what the QVM scripts and the engine look up, so this is
the game's own string table - mission names, objectives, menu labels, weapon names,
building tooltips, cutscene subtitles.

    python3 langdump.py /path/to/extracted/pc/language/english
    python3 langdump.py /path/to/extracted/pc/language/english missions
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import igi_formats as F  # noqa: E402

LANGS = ("english", "french", "german", "italian", "spanish", "USA")


def load_pairs(path):
    """Return [(key, text)] for one language .res file."""
    d = open(path, "rb").read()
    info, errors = F.parse_ilff(d)
    if info is None:
        raise ValueError(f"{path}: not ILFF")
    pairs = []
    key = None
    for c in info["chunks"]:
        if c.id in ("NAME", "IRESNAME"):
            key = c.payload(d).split(b"\x00")[0].decode("latin-1")
        elif c.id == "CSTR":
            pairs.append((key, c.payload(d).split(b"\x00")[0].decode("latin-1")))
    return pairs, errors


def dump_dir(lang_dir, only=None):
    for fn in sorted(os.listdir(lang_dir)):
        if not fn.endswith(".res"):
            continue
        stem = fn[:-4]
        if only and stem not in only:
            continue
        pairs, errors = load_pairs(os.path.join(lang_dir, fn))
        print(f"=== {fn}: {len(pairs)} strings"
              + (f"  ({len(errors)} parse errors)" if errors else ""))
        for k, v in pairs:
            print(f"   {k!r:46s} = {v!r}")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    dump_dir(argv[1], set(argv[2:]) or None)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
