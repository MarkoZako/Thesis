#!/usr/bin/env python3

import os, re

from collections import defaultdict



BASE = "/home/mzako001"

WORKLOADS = [

    "Blender","CactuBSSN","Cam4","Fotonik3d","Gcc","Lbm",

    "Mcf","Omnetpp","Parest","Roms","Wrf",

    "Xalancbmk","x264","Xz"

]

EXCLUDE = {"Bwaves","Exchange","Imagick","Leela","Perlbench","Povray"}



# same NAME_MAP and LINE_RX from your debug script

NAME_MAP = {}       # map L_DemClean→L_DemotionClean, etc.

LINE_RX  = re.compile(r"^(?P<short>[LRWP]_[A-Za-z]+)\s*%\s*(?P<val>\d+)\s*$")



def load_policies():

    # policy_map[frozenset of (feat, val)] → set of workloads

    policy_map = defaultdict(set)



    for wl in WORKLOADS:

        if wl in EXCLUDE: continue

        d = os.path.join(BASE, wl, "Fittest_Results")

        for fn in os.listdir(d):

            if not fn.endswith(".txt") or fn=="comparison_with_Thesis_All.txt":

                continue

            path = os.path.join(d, fn)

            featvals = {}

            with open(path) as f:

                for line in f:

                    m = LINE_RX.match(line.strip())

                    if not m: continue

                    short = m.group("short")

                    val   = int(m.group("val"))

                    if short in NAME_MAP:

                        featvals[NAME_MAP[short]] = val

            if len(featvals)==20:

                key = frozenset(featvals.items())

                policy_map[key].add(wl)

            else:

                print(f"⚠️  {wl}/{fn}: only {len(featvals)} features parsed")



    return policy_map



def greedy_cover(policy_map):

    uncovered = set(WORKLOADS)

    chosen    = []

    # build list of (policy, coverset)

    candidates = [(p, set(cov)) for p,cov in policy_map.items()]



    while uncovered:

        # pick policy covering most *new* workloads

        best, covers = max(

            candidates,

            key=lambda pc: len(pc[1] & uncovered)

        )

        hit = covers & uncovered

        if not hit:

            break

        chosen.append((best, hit))

        uncovered -= hit

        candidates = [(p,c) for (p,c) in candidates if p!=best]



    return chosen, uncovered



def main():

    policy_map = load_policies()

    chosen, left = greedy_cover(policy_map)



    print(f"\n🔎 Selected {len(chosen)} policies, missed: {left}")

    for i,(policy, cov) in enumerate(chosen,1):

        print(f"\n--- Policy #{i}, covers {sorted(cov)} ---")

        for feat,val in sorted(policy):

            print(f"   {feat:20s} = {val}")

    if left:

        print("\n⚠️  Could not cover workloads:", left)



if __name__=="__main__":

    main()


