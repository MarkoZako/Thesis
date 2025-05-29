#!/usr/bin/env python3

import os

import re

from collections import defaultdict



# ─── CONFIG ────────────────────────────────────────────────────────────────────



BASE_DIR = "/home/mzako001"

EXCLUDE = {"Bwaves", "Exchange", "Imagick", "Leela", "Perlbench", "Povray"}



WORKLOADS = [

    "Blender", "CactuBSSN", "Cam4", "Fotonik3d", "Gcc", "Lbm",

    "Mcf", "Omnetpp", "Parest", "Roms", "Wrf",

    "Xalancbmk", "x264", "Xz"

]



FEATURES = [

    f"{p}_{t}"

    for p in ("L","R","W","P")

    for t in ("DemotionClean","DemotionDirty","Insertion","PromotionClean","PromotionDirty")

]



NAME_MAP = {

    # L

    "L_DemClean":   "L_DemotionClean",

    "L_DemDirty":   "L_DemotionDirty",

    "L_Insert":     "L_Insertion",

    "L_SPromClean": "L_PromotionClean",

    "L_SPromDirty": "L_PromotionDirty",

    # R

    "R_DemClean":   "R_DemotionClean",

    "R_DemDirty":   "R_DemotionDirty",

    "R_Insert":     "R_Insertion",

    "R_SPromClean": "R_PromotionClean",

    "R_SPromDirty": "R_PromotionDirty",

    # P

    "P_DemClean":   "P_DemotionClean",

    "P_DemDirty":   "P_DemotionDirty",

    "P_Insert":     "P_Insertion",

    "P_SPromClean": "P_PromotionClean",

    "P_SPromDirty": "P_PromotionDirty",

    # W

    "W_DemClean":   "W_DemotionClean",

    "W_DemDirty":   "W_DemotionDirty",

    "W_Insert":     "W_Insertion",

    "W_SPromClean": "W_PromotionClean",

    "W_SPromDirty": "W_PromotionDirty",

}



LINE_RX = re.compile(r"^(?P<short>[LRWP]_[A-Za-z]+)\s*%\s*(?P<val>\d+)\s*$")



# ─── HELPERS ───────────────────────────────────────────────────────────────────



def find_workload_dirs(base):

    mapping = {}

    for d in os.listdir(base):

        if d in EXCLUDE:

            continue

        full = os.path.join(base, d)

        if not os.path.isdir(full):

            continue



        if d == "Thesis":

            wl = "Mcf"

        elif d.startswith("Thesis_"):

            wl = d[len("Thesis_"):]

        elif d in ("Roms","X264","Xz"):

            wl = d if d!="X264" else "x264"

        else:

            continue



        if wl in WORKLOADS:

            mapping[wl] = full



    print("🔍 Workloads found and their paths:")

    for wl, path in mapping.items():

        print(f"   {wl:<10} → {path}")

    return mapping



def parse_policy_file(path):

    found = {}

    with open(path) as f:

        for ln, line in enumerate(f,1):

            m = LINE_RX.match(line.strip())

            if not m:

                continue

            short = m.group("short")

            val   = int(m.group("val"))

            if short not in NAME_MAP:

                print(f"   ⚠️  [{os.path.basename(path)}:{ln}] unknown key '{short}'")

                continue

            canon = NAME_MAP[short]

            found[canon] = val

    if not found:

        print(f"   ⚠️   no valid lines in {os.path.basename(path)}")

    return found



# ─── MAIN ──────────────────────────────────────────────────────────────────────



def main():

    wdirs = find_workload_dirs(BASE_DIR)



    # collect per-workload

    workload_vals = {wl: defaultdict(set) for wl in WORKLOADS}

    for wl, d in wdirs.items():

        fdir = os.path.join(d, "Fittest_Results_MiddleCrossover")

        if not os.path.isdir(fdir):

            print(f"⚠️  Missing Fittest_Results for {wl}")

            continue



        files = [f for f in os.listdir(fdir) if f.endswith(".txt")]

        print(f"\n📁 [{wl}] files: {files}")



        for fn in files:

            if fn == "comparison_with_Thesis_All.txt":

                continue

            path = os.path.join(fdir, fn)

            parsed = parse_policy_file(path)

            print(f"   → parsed {fn}: {parsed}")

            for feat, val in parsed.items():

                workload_vals[wl][feat].add(val)



    # invert to get, for each feature, which workloads saw which values

    pop = {feat: defaultdict(set) for feat in FEATURES}

    for wl, fv in workload_vals.items():

        print(f"\n🔧 [{wl}] feature counts:")

        for feat, vals in fv.items():

            print(f"    {feat}: {sorted(vals)}")

            for v in vals:

                pop[feat][v].add(wl)



    # now cover and record selected values

    out = []

    for feat in FEATURES:

        out.append(f"=== {feat} ===")

        if not pop[feat]:

            out.append("   ⚠️  no values seen at all!\n")

            continue



        # show all value → workloads

        for v, wset in sorted(pop[feat].items(), key=lambda x: -len(x[1])):

            mask = "".join("1" if wl in wset else "0" for wl in WORKLOADS)

            out.append(f"   val={v:<2} pop={len(wset):>2} wls={sorted(wset)} mask={mask}")



        # greedy cover (and remember which values we picked)

        uncovered = set(range(len(WORKLOADS)))

        avail     = dict(pop[feat])

        cover     = []

        while uncovered and avail:

            best_v, best_set = max(

                ((v, pop[feat][v] & {WORKLOADS[i] for i in uncovered})

                 for v in avail),

                key=lambda x: len(x[1]), default=(None,set())

            )

            if not best_set:

                break

            cover.append(best_v)

            for wl in best_set:

                uncovered.remove(WORKLOADS.index(wl))

            del avail[best_v]



        if not uncovered:

            vals = ", ".join(str(v) for v in cover)

            out.append(f"--> min policies to cover all 14: {len(cover)} (values: {vals})\n")

        else:

            out.append(f"--> could not cover all workloads, picked {len(cover)} values: {cover}\n")



    fn = "popularityFittest_debug_middle.txt"

    with open(fn, "w") as f:

        f.write("\n".join(out))

    print(f"\n✅ Wrote debug output to {fn}")



if __name__=="__main__":

    main()


