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

    suffix = f"-{gen}-{ind}"

    for d in os.listdir(SADR_DIR):

        full = os.path.join(SADR_DIR, d)

        if os.path.isdir(full) and d.endswith(suffix):

            return full

    return None



def parse_out_ipcs(folder):

    results = {}

    for fn in os.listdir(folder):

        if not fn.endswith(".out"):

            continue

        name = fn[:-4]

        if name in IGNORE:

            continue

        path = os.path.join(folder, fn)

        with open(path) as f:

            for line in f:

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

    best_ipc = {}

    best_id  = {}



    for fn in os.listdir(RES_TXT_DIR):

        m = TXT_RX.match(fn)

        if not m:

            continue

        txt_path = os.path.join(RES_TXT_DIR, fn)

        if os.path.getmtime(txt_path) >= cutoff_ts:

            continue

        gen, ind = m.group(1), m.group(2)



        sad_dir = find_sadrrip_folder(gen, ind)

        if not sad_dir:

            continue



        ipcs = parse_out_ipcs(sad_dir)

        for bm, ipc in ipcs.items():

            if bm not in best_ipc or ipc > best_ipc[bm]:

                best_ipc[bm] = ipc

                best_id[bm]  = (gen, ind)



    print("=== Highest-IPC individuals (before 2025-05-18 14:30) ===")

    for bm in sorted(best_ipc):

        gen, ind = best_id[bm]

        ipc = best_ipc[bm]

        print(f"{bm:12s} → gen {gen}, ind {ind}   ipc = {ipc:.6f}")



    target = "33_1645_1DOT026690_1DOT026690_1592_1558.txt"

    print("\n=== IPCs for individual from", target, "===")

    m = TXT_RX.match(target)

    if m:

        gen, ind = m.group(1), m.group(2)

        sad_dir = find_sadrrip_folder(gen, ind)

        if sad_dir:

            ipcs = parse_out_ipcs(sad_dir)

            for bm in sorted(ipcs):

                print(f"{bm:12s} → ipc = {ipcs[bm]:.6f}")

        else:

            print("❌ no matching SADRRIP folder for target")

    else:

        print("❌ target filename did not match pattern")



    # ── Print all IPC results for generation 1 ──────────────────────────────

    print("\n=== IPCs for all individuals from generation 1 ===")

    for fn in os.listdir(RES_TXT_DIR):

        m = TXT_RX.match(fn)

        if not m or m.group(1) != '1':

            continue

        gen, ind = m.group(1), m.group(2)

        sad_dir = find_sadrrip_folder(gen, ind)

        if not sad_dir:

            continue

        ipcs = parse_out_ipcs(sad_dir)

        print(f"\n→ Individual gen {gen}, ind {ind}")

        for bm in sorted(ipcs):

            print(f"  {bm:12s} → ipc = {ipcs[bm]:.6f}")



if __name__ == "__main__":

    main()


