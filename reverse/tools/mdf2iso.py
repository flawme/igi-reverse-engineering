#!/usr/bin/env python3
"""Convert a raw 2352-byte/sector Mode 1 CD image (.mdf) to a plain 2048-byte/sector ISO.

Project IGI ships on a mixed-mode CD: the data track is raw 2352-byte Mode 1 sectors
(12 sync + 4 header + 2048 data + 288 EDC/ECC), and the image carries trailing padding
and audio-track sectors after the ISO9660 volume. This reads the PVD at LBA 16 first to
learn the volume space size, then converts exactly that many sectors.

    python3 mdf2iso.py "Project IGI.mdf" project_igi.iso
    ../../tools/../..  # then: 7z x project_igi.iso -oextracted 'pc/*'
"""
from __future__ import annotations

import sys

SECTOR_RAW = 2352
SECTOR_DATA = 2048
DATA_OFF = 16  # Mode 1: 12 sync + 4 header


def read_sector_data(f, lba):
    f.seek(lba * SECTOR_RAW)
    sec = f.read(SECTOR_RAW)
    mode = sec[15]
    if mode == 1:
        return sec[DATA_OFF:DATA_OFF + SECTOR_DATA]
    if mode == 2:
        return sec[24:24 + SECTOR_DATA]
    raise SystemExit(f"unexpected sector mode {mode} at sector {lba}")


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    with open(src, "rb") as fin:
        pvd = read_sector_data(fin, 16)
        if pvd[1:6] != b"CD001":
            raise SystemExit("no ISO9660 PVD at LBA 16")
        vol = int.from_bytes(pvd[80:84], "little")
        print(f"volume space size = {vol} sectors ({vol * SECTOR_DATA} bytes)")
        with open(dst, "wb") as fout:
            for lba in range(vol):
                fin.seek(lba * SECTOR_RAW)
                sec = fin.read(SECTOR_RAW)
                if len(sec) < SECTOR_RAW:
                    raise SystemExit(f"short read at sector {lba}")
                mode = sec[15]
                if mode == 1:
                    fout.write(sec[DATA_OFF:DATA_OFF + SECTOR_DATA])
                elif mode == 2:
                    fout.write(sec[24:24 + SECTOR_DATA])
                elif mode == 0:
                    fout.write(b"\x00" * SECTOR_DATA)
                else:
                    raise SystemExit(f"unexpected sector mode {mode} at sector {lba}")
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
