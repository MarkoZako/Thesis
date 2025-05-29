#!/usr/bin/env python3

import os

import re

import time

from datetime import datetime



# ─── CONFIG ────────────────────────────────────────────────────────────────



# cutoff timestamp: May 18 2025 14:30 local time

cutoff_dt = datetime(2025, 5, 18, 14, 30)

cutoff_ts = time.mktime(cutoff_dt.timetuple())



# paths

BASE = "/home/mzako001"

RES_TXT_DIR = os.path.join(BASE, "Thesis_All", "Results")

SADR_DIR    = os.path.join(BASE, "Thesis_All", "SADRRIP", "Results")



# benchmarks to ignore

IGNORE = {"Leela", "Bwaves", "Perlbench", "Exchange", "Imagick", "Povray"}



# regexps

TXT_RX = re.compile(r"^(\d+)_(\d+)_1DOT[0-9]+.*\.txt$")

IPC_RX = re.compile(r"cumulative IPC:\s*([0-9.]+)")



# ─── HELPERS ────────────────────────────────────────────────────────────────



def find_sadrrip_folder(gen, ind):

    """

    In SADRRIP/Results, find a subdir whose name ends with "-{gen}-{ind}".

    Return its full path or None.

    """

    suffix = f"-{gen}-{ind}"

    for d in os.listdir(SADR_DIR):

        full = os.path.join(SADR_DIR, d)

        if os.path.isdir(full) and d.endswith(suffix):

            return full

    return None



def parse_out_ipcs(folder):

    """

    In folder, look at all .out files except the ignored benchmarks.

    Parse each for the single line containing "Finished CPU 0 ... cumulative IPC: X.YZ ..."

    and return a dict {benchmark_name: ipc_value}.

    """

    results = {}

    for fn in os.listdir(folder):

        if not fn.endswith(".out"):

            continue

        name = fn[:-4]  # strip ".out"

        if name in IGNORE:

            continue

        path = os.path.join(folder, fn)

        with open(path) as f:

            for line in f:

                # only consider the line that begins with "Finished"

                if "Finished" not in line:

                    continue

                m = IPC_RX.search(line)

                if m:

                    ipc = float(m.group(1))

                    results[name] = ipc

                break

    return results



# ─── MAIN ──────────────────────────────────────────────────────────────────



def main():

    # track best per benchmark

    best_ipc = {}      # benchmark -> max ipc

    best_id  = {}      # benchmark -> (gen, ind)

    

    # scan all .txt in RES_TXT_DIR before cutoff

    for fn in os.listdir(RES_TXT_DIR):

        m = TXT_RX.match(fn)

        if not m:

            continue

        txt_path = os.path.join(RES_TXT_DIR, fn)

        if os.path.getmtime(txt_path) >= cutoff_ts:

            continue  # only before cutoff

        gen, ind = m.group(1), m.group(2)

        

        # find corresponding SADRRIP folder

        sad_dir = find_sadrrip_folder(gen, ind)

        if not sad_dir:

            print(f"⚠️  no SADRRIP folder for {fn}")

            continue

        

        # parse all IPCs in that folder

        ipcs = parse_out_ipcs(sad_dir)

        for bm, ipc in ipcs.items():

            if bm not in best_ipc or ipc > best_ipc[bm]:

                best_ipc[bm] = ipc

                best_id[bm]  = (gen, ind)

    

    # print summary of highest-IPC individuals

    print("=== Highest-IPC individuals (before 2025-05-18 14:30) ===")

    for bm in sorted(best_ipc):

        gen, ind = best_id[bm]

        ipc = best_ipc[bm]

        print(f"{bm:12s} → gen {gen}, ind {ind}   ipc = {ipc:.6f}")

    

    # ── Now do the same *only* for the specific file 28_1086_…txt ─────────────

    target = "28_1086_1DOT031160_1DOT031160_1055_1063.txt"

    print("\n=== IPCs for individual from", target, "===")

    m = TXT_RX.match(target)

    if not m:

        print("❌ target filename did not match pattern")

        return

    gen, ind = m.group(1), m.group(2)

    sad_dir = find_sadrrip_folder(gen, ind)

    if not sad_dir:

        print("❌ no matching SADRRIP folder for target")

        return

    ipcs = parse_out_ipcs(sad_dir)

    for bm in sorted(ipcs):

        print(f"{bm:12s} → ipc = {ipcs[bm]:.6f}")



if __name__ == "__main__":

    main()


