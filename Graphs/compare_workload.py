#!/usr/bin/env python3

import os

import re

from itertools import combinations



# ─── CONFIG ────────────────────────────────────────────────────────────────────



BASE_DIR = "/home/mzako001"

# workloads to skip

EXCLUDE = {"Perlbench", "Bwaves", "Povray", "Exchange", "Imagick", "Leela"}



# detects lines like “A.txt vs B.txt : … (IDENTICAL)”

identical_rx = re.compile(r"^(.+?) vs (.+?) :.*\(IDENTICAL\)")



# The five features in each instruction class

FEATURES = [

    'DemotionClean',

    'DemotionDirty',

    'Insertion',

    'PromotionClean',

    'PromotionDirty',

]



# ─── HELPERS ────────────────────────────────────────────────────────────────────



def extract_L2_section(filepath):

    """Pull out everything under the “.L2:” label (skipping comments) until the next label."""

    in_L2 = False

    section = []

    with open(filepath) as f:

        for line in f:

            s = line.strip()

            if not in_L2 and ".L2:" in line:

                in_L2 = True

                continue

            if in_L2:

                # blank or leading-# before any real data: skip

                if not section and (s == "" or s.startswith("#")):

                    continue

                # next assembler label ends this section

                if s.startswith(".") and s.endswith(":"):

                    break

                if s.startswith("#"):

                    continue

                section.append(s)

    return section



def parse_values(lines):

    """From lines like “L_Insert %2” return [("L_Insert",2), …]."""

    out = []

    for ln in lines:

        if "%" in ln:

            try:

                name,val = ln.split("%")

                out.append((name.strip(), int(val.strip())))

            except ValueError:

                pass

    return out



def diff_stats(sec1, sec2):

    """

    Compare two L2 dumps, return

      total_distance,

      dict counts per e.g. “L_Insertion”, “W_DemotionDirty”, …

    """

    v1 = parse_values(sec1)

    v2 = parse_values(sec2)

    if len(v1) != len(v2):

        raise ValueError(f"mismatch {len(v1)} vs {len(v2)}")

    # suffix→human

    cat_map = {

        'DemClean':   'DemotionClean',

        'DemDirty':   'DemotionDirty',

        'Insert':     'Insertion',

        'SPromClean': 'PromotionClean',

        'SPromDirty': 'PromotionDirty',

    }

    # build empty buckets

    insts = set(n.split(suf)[0]

                for n,_ in v1

                for suf in cat_map

                if suf in n)

    counts = {

        f"{inst}_{feat}": 0

        for inst in insts

        for feat in cat_map.values()

    }

    total = 0



    for (n1,x1),(n2,x2) in zip(v1,v2):

        if n1!=n2:

            raise ValueError(f"name mismatch: {n1} vs {n2}")

        for suf,feat in cat_map.items():

            if suf in n1:

                inst = n1.split(suf)[0]

                key  = f"{inst}_{feat}"

                if suf.startswith("Dem"):

                    if x1!=x2:

                        counts[key] += 1

                        total     += 1

                else:

                    d = abs(x1-x2)

                    if d:

                        counts[key] += d

                        total     += d

                break



    return total, counts



# ─── MAIN ──────────────────────────────────────────────────────────────────────



def main():

    # find each workload folder

    workloads = []

    for d in os.listdir(BASE_DIR):

        p = os.path.join(BASE_DIR, d)

        if not os.path.isdir(p): continue

        if d=="Thesis":

            wl="Mcf"

        elif d.startswith("Thesis_"):

            wl=d[len("Thesis_"):]

        elif d in ("Roms","X264","Xz"):

            wl="x264" if d=="X264" else d

        else:

            continue

        if wl in EXCLUDE:

            print(f"⏭ Skipping {wl}")

            continue

        workloads.append((d,wl))



    for folder,wl in workloads:

        fdir = os.path.join(BASE_DIR, folder, "Fittest_Results_MiddleCrossover")

        if not os.path.isdir(fdir):

            print(f"⚠ {wl}: no MiddleCrossover dir")

            continue



        print(f"\n🔄 {wl}")



        # 1) repeatedly remove IDENTICAL pairs

        while True:

            txts = sorted(fn for fn in os.listdir(fdir)

                          if fn.endswith(".txt") and fn!="similarity.txt")

            if len(txts)<2:

                break



            sim = os.path.join(fdir, "similarity.txt")

            with open(sim,"w") as out:

                out.write(f"# {wl}\n\n")

                for a,b in combinations(txts,2):

                    p1,p2 = os.path.join(fdir,a), os.path.join(fdir,b)

                    try:

                        s1 = extract_L2_section(p1)

                        s2 = extract_L2_section(p2)

                        dist, cnts = diff_stats(s1,s2)

                        stats = ", ".join(f"{cnts[k]} {k}" for k in sorted(cnts))

                        tag   = " (IDENTICAL)" if all(v==0 for v in cnts.values()) else ""

                        out.write(f"{a} vs {b} : {dist} where {stats}{tag}\n")

                    except Exception as e:

                        out.write(f"{a} vs {b} : ERROR({e})\n")



            # delete the duplicates

            to_del = set()

            with open(sim) as f:

                for L in f:

                    m = identical_rx.match(L)

                    if m:

                        to_del.add(m.group(2))

            if not to_del:

                break

            for fn in to_del:

                os.remove(os.path.join(fdir,fn))

                print(f" 🗑 removed {fn}")



        # 2) scan similarity.txt, tally only the five FEATURES

        sim = os.path.join(fdir, "similarity.txt")

        raw = {}

        with open(sim) as f:

            for L in f:

                if " where " not in L:

                    continue

                for num,cat in re.findall(r"(\d+)\s+([A-Za-z0-9_]+)", L):

                    if any(cat.endswith(feat) for feat in FEATURES):

                        raw[cat] = raw.get(cat,0) + int(num)



        # group by feature type (drop the leading inst letter)

        grouped = {feat:0 for feat in FEATURES}

        for cat,cnt in raw.items():

            for feat in FEATURES:

                if cat.endswith(feat):

                    grouped[feat] += cnt

                    break



        total_feat = sum(grouped.values()) or 1



        # 3) append a clean 100% summary

        with open(sim,"a") as out:

            out.write("\nOverall difference distribution (percent):\n")

            for feat in FEATURES:

                pct = grouped[feat] / total_feat * 100

                out.write(f"  {feat}: {pct:5.1f}%\n")

            out.write("\n")



        print(" ✅ wrote 100% feature summary\n")



if __name__=="__main__":

    main()


