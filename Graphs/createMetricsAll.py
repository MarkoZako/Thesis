#!/usr/bin/env python3

import os
import re

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR   = "/home/mzako001"
OUTPUT_DIR = os.path.join(BASE_DIR, "outputFiles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# top‐level dirs to scan
benchmarks = [
    d for d in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, d))
    and (d == "Thesis" or d.startswith("Thesis_") or d in ("Roms","X264","Xz"))
]

# match filenames like:
#   28_1368_1DOT009560_1DOT009560_1302_1347.txt
pattern = re.compile(r"""
    ^
    (?P<gen>\d+)_           # generation
    (?P<id>\d+)_            # policy ID
    (?P<sp_int>\d+)DOT      # integer part of speedup
    (?P<sp_frac>\d+)        # fractional part of speedup
    _.*\.txt$               # rest of filename
""", re.VERBOSE)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

for bench in sorted(benchmarks):
    # look in .../<bench>/Results
    fdir = os.path.join(BASE_DIR, bench, "Results")
    if not os.path.isdir(fdir):
        continue

    out_path = os.path.join(OUTPUT_DIR, f"extracted_speedups_{bench}_middleCrossover.txt")
    with open(out_path, "w") as out:
        for fn in sorted(os.listdir(fdir)):
            if not fn.endswith(".txt") or fn == "similarity.txt":
                continue
            m = pattern.match(fn)
            if not m:
                continue

            gen      = int(m.group("gen"))
            pid      = int(m.group("id"))
            sp_int   = m.group("sp_int")
            sp_frac  = m.group("sp_frac")
            speedup  = float(f"{sp_int}.{sp_frac}")

            out.write(f"Generation: {gen}, ID: {pid}, Speedup: {speedup:.3f}\n")

    count = sum(1 for _ in open(out_path))
    print(f"→ Wrote {count} entries to {out_path}")

