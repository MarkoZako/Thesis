#!/usr/bin/env python3
import os
import re
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR    = "/home/mzako001/Thesis_All"
POLICY_DIR  = os.path.join(BASE_DIR, "Results")
SADRRIP_DIR = os.path.join(BASE_DIR, "SADRRIP", "Results")
OUTPUT_DIR  = "/home/mzako001/outputFiles"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Baseline IPC per benchmark
baseline_ipc = {
    "Blender": 0.661,    "Bwaves": 1.016,   "Cam4": 0.725,       "cactuBSSN": 0.761,
    "Exchange": 1.127,   "Gcc": 0.353,      "Lbm": 0.652,        "Mcf": 0.400,
    "Parest": 0.935,     "Povray": 0.356,   "Wrf": 0.823,        "Xalancbmk": 0.395,
    "Fotonik3d": 0.621,  "Imagick": 2.193,  "Leela": 0.548,      "Omnetpp": 0.246,
    "Perlbench": 0.448,  "Roms": 1.079,     "x264": 1.372,       "Xz": 0.894
}

benchmarks = list(baseline_ipc.keys())

# stricter regex to match your gem5 line
ipc_rx = re.compile(r"Finished CPU 0 instructions:.*?cumulative IPC:\s*([0-9.]+)")

# prepare storage
bench_records = {b: [] for b in benchmarks}


# ─── WALK ALL POLICIES & PARSE .out ────────────────────────────────────────────
for fname in sorted(os.listdir(POLICY_DIR)):
    if not fname.endswith(".txt"):
        continue

    parts = fname.split("_", 2)
    if len(parts) < 2:
        print(f"⚠️  Skipping malformed name {fname}", file=sys.stderr)
        continue
    generation, policy_id = parts[0], parts[1]

    # find matching SADRRIP subdir
    suffix = f"-{generation}-{policy_id}"
    cands  = [d for d in os.listdir(SADRRIP_DIR) if d.endswith(suffix)]
    if not cands:
        print(f"⚠️  No SADRRIP dir *{suffix}* for {fname}", file=sys.stderr)
        continue
    out_dir = os.path.join(SADRRIP_DIR, cands[0])

    # parse each bench
    for bench in benchmarks:
        of = os.path.join(out_dir, bench + ".out")
        if not os.path.isfile(of):
            continue

        found = None
        with open(of) as f:
            for line in f:
                m = ipc_rx.search(line)
                if m:
                    found = float(m.group(1))
                    break
        if found is None:
            print(f"⚠️  no match in {of}", file=sys.stderr)
            continue

        speedup = found / baseline_ipc[bench]
        bench_records[bench].append((policy_id, speedup))


# ─── WRITE TXT PER BENCHMARK ─────────────────────────────────────────────────
for bench, recs in bench_records.items():
    if not recs:
        print(f"⚠️  no data for {bench}, skipping", file=sys.stderr)
        continue

    path = os.path.join(OUTPUT_DIR, f"{bench}_speedups.txt")
    with open(path, "w") as out:
        for pid, sp in sorted(recs, key=lambda x: int(x[0])):
            out.write(f"ID: {pid}, Speedup: {sp:.3f}\n")
    print(f"✏️  Wrote {len(recs)} entries to {path}")

print("✅ All done.")

