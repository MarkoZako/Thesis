#!/usr/bin/env python3

import os

import re



# --- Configuration ---

BASE_DIR = "/home/mzako001/Thesis_All"

POLICY_RESULTS  = os.path.join(BASE_DIR, "Results")

SADRRIP_RESULTS = os.path.join(BASE_DIR, "SADRRIP", "Results")

OUTPUT_FILE     = "best_speedups.txt"



# Baseline IPC values

baseline_ipc = {

    "Blender": 0.661,    "Bwaves": 1.016,   "Cam4": 0.725,       "cactuBSSN": 0.761,

    "Exchange": 1.127,   "Gcc": 0.353,      "Lbm": 0.652,       "Mcf": 0.400,

    "Parest": 0.935,     "Povray": 0.356,   "Wrf": 0.823,       "Xalancbmk": 0.395,

    "Fotonik3d": 0.621,  "Imagick": 2.193,  "Leela": 0.548,     "Omnetpp": 0.246,

    "Perlbench": 0.448,  "Roms": 1.079,     "x264": 1.372,      "Xz": 0.894

}



# Ordered list of benchmarks

benchmarks = list(baseline_ipc.keys())



# Regex to extract IPC from the "Finished CPU 0 instructions" line

ipc_line_rx = re.compile(

    r"Finished CPU 0 instructions:.*cumulative IPC:\s*([0-9.]+)"

)



# Initialize best‐speedup records

best_speedups = {

    bench: {"speedup": 0.0, "policy": None}

    for bench in benchmarks

}



# Iterate through each policy file

for fname in sorted(os.listdir(POLICY_RESULTS)):

    if not fname.endswith(".txt"):

        continue



    # Expect filename format: <generation>_<policy_id>_*.txt

    parts = fname.split("_")

    if len(parts) < 2:

        continue

    generation, policy_id = parts[0], parts[1]



    # Find matching SADRRIP subdir ending in "-<generation>-<policy_id>"

    pattern = re.compile(rf"-{re.escape(generation)}-{re.escape(policy_id)}$")

    candidates = [

        d for d in os.listdir(SADRRIP_RESULTS)

        if pattern.search(d)

    ]

    if not candidates:

        continue

    # pick first if multiple

    subdir = candidates[0]

    out_dir = os.path.join(SADRRIP_RESULTS, subdir)



    # For each benchmark, open .out and parse the IPC

    for bench in benchmarks:

        out_path = os.path.join(out_dir, f"{bench}.out")

        if not os.path.isfile(out_path):

            continue

        found_ipc = None

        with open(out_path) as f:

            for line in f:

                m = ipc_line_rx.search(line)

                if m:

                    found_ipc = float(m.group(1))

                    break

        if found_ipc is None:

            continue

        speedup = found_ipc / baseline_ipc[bench]

        record = best_speedups[bench]

        if speedup > record["speedup"]:

            record["speedup"] = speedup

            record["policy"]  = fname



# Write out the results

with open(OUTPUT_FILE, "w") as out:

    out.write("Highest Fittest Speedup per Benchmark\n")

    out.write("=====================================\n\n")

    for bench in benchmarks:

        rec = best_speedups[bench]

        if rec["policy"] is not None:

            out.write(

                f"{bench}: {rec['speedup']:.6f}  achieved by policy {rec['policy']}\n"

            )

        else:

            out.write(f"{bench}: no data found\n")



print(f"Results written to {OUTPUT_FILE}")


