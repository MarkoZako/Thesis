#!/usr/bin/env python3

import os

import sys



BASE_DIR = "/home/mzako001"



# benchmarks to ignore entirely

EXCLUDE = {"Bwaves", "Leela", "Perlbench", "Povray", "Imagick", "Exchange"}



def discover_workloads(base):

    """

    Map directory names under `base` to our 14 workloads.

    - "Thesis"         → "Mcf"

    - "Thesis_<bench>" → "<bench>"

    - "Roms", "X264"   → "Roms", "x264"

    - "Xz"             → "Xz"

    """

    mapping = {}

    for d in os.listdir(base):

        full = os.path.join(base, d)

        if not os.path.isdir(full):

            continue



        if d == "Thesis":

            bench = "Mcf"

        elif d.startswith("Thesis_"):

            bench = d[len("Thesis_"):]

        elif d in ("Roms", "X264", "Xz"):

            bench = "x264" if d == "X264" else d

        else:

            continue



        if bench in EXCLUDE:

            continue



        mapping[bench] = d



    return mapping



def list_txt_files(dirpath):

    """Return all '*.txt' names (without .txt) in a directory, excluding 'similarity.txt'."""

    if not os.path.isdir(dirpath):

        return []

    out = []

    for fn in os.listdir(dirpath):

        if fn.endswith(".txt") and fn != "similarity.txt":

            out.append(fn[:-4])

    return sorted(out)



def extract_speed(name):

    """

    Given a filename base like '20_993_1.001490_1.001490_915_919'

    or '1DOT12131', return just the speedup (third field).

    """

    s = name.replace("DOT", ".")

    parts = s.split("_")

    if len(parts) >= 3:

        return parts[2]

    return s



def main():

    workloads = discover_workloads(BASE_DIR)

    if not workloads:

        print("⚠️  No workloads found under", BASE_DIR, file=sys.stderr)

        sys.exit(1)



    for bench in sorted(workloads):

        d = workloads[bench]



        base_dir = os.path.join(BASE_DIR, d, "Fittest_Results")

        mid_dir  = os.path.join(BASE_DIR, d, "Fittest_Results_MiddleCrossover")



        base_files = list_txt_files(base_dir)

        mid_files  = list_txt_files(mid_dir)



        # extract just the speedup numbers

        base_speeds = {extract_speed(fn) for fn in base_files}

        mid_speeds  = {extract_speed(fn) for fn in mid_files}



        # pick one (if there's more than one, they'll all be shown comma‐separated)

        base_out = ", ".join(sorted(base_speeds)) if base_speeds else "(none)"

        mid_out  = ", ".join(sorted(mid_speeds))  if mid_speeds  else "(none)"



        print(f"{bench}:")

        print(f"  baseline        → {base_out}")

        print(f"  MiddleCrossover → {mid_out}")

        print()



if __name__ == "__main__":

    main()


