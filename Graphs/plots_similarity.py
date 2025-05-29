#!/usr/bin/env python3

import os

import re

import matplotlib.pyplot as plt

import numpy as np

from collections import OrderedDict



# --- Configuration ---

BASE_DIR = "/home/mzako001"



# Detect only the real folders:

#  - "Thesis" for Mcf

#  - "Thesis_All" for overall

#  - "Thesis_<benchmark>" for the others (but not Thesis_Mcf)

#  - "Roms", "X264", "Xz"

folders = []

for d in os.listdir(BASE_DIR):

    full = os.path.join(BASE_DIR, d)

    if not os.path.isdir(full):

        continue

    if d in ("Thesis", "Thesis_All"):

        folders.append(d)

    elif d.startswith("Thesis_") and d != "Thesis_Mcf":

        folders.append(d)

    elif d in ("Roms", "X264", "Xz"):

        folders.append(d)

folders = sorted(folders)



# Instruction‐difference categories (in the same order they appear in similarity.txt)

categories = ["DemotionClean", "DemotionDirty", "Insertion", "PromotionClean", "PromotionDirty"]



# Regex helpers

pct_rx     = re.compile(r"\s*(\w+):.*\(([\d.]+)%\)")

sim_hdr_rx = re.compile(r"Overall difference distribution:")

dotval_rx  = re.compile(r"(\d+)DOT(\d+)")



# Container for per-benchmark stats

results = OrderedDict()  # bench_name -> {"pct":{...}, "count":N, "speedup":S}



# Gather stats

for folder in folders:

    # Map folder → label

    if folder == "Thesis_All":

        bench = "All"

    elif folder == "Thesis":

        bench = "Mcf"

    else:

        bench = folder.replace("Thesis_", "")



    fdir = os.path.join(BASE_DIR, folder, "Fittest_Results")

    simf = os.path.join(fdir, "similarity.txt")



    # 1) parse percentages from similarity.txt

    pct = {c: 0.0 for c in categories}

    if os.path.isfile(simf):

        lines = open(simf).read().splitlines()

        try:

            idx = next(i for i, l in enumerate(lines) if sim_hdr_rx.search(l))

            for i, c in enumerate(categories):

                m = pct_rx.match(lines[idx + 1 + i])

                pct[c] = float(m.group(2))

        except StopIteration:

            pass



    # 2) count number of .txt files (excluding similarity.txt)

    files = [f for f in os.listdir(fdir) if f.endswith(".txt") and f != "similarity.txt"]

    count = len(files)



    # 3) extract fittest speedup from first filename

    speedup = 0.0

    if files:

        m = dotval_rx.search(files[0])

        if m:

            speedup = float(f"{m.group(1)}.{m.group(2)}")



    results[bench] = {"pct": pct, "count": count, "speedup": speedup}



# --- Plot 1: Instruction‐type distribution + Speedup overlay ---



labels = list(results.keys())

x = np.arange(len(labels))

width = 0.6



# build matrix of percentages

pct_mat = np.array([[results[b]["pct"][c] for b in labels] for c in categories])

speeds  = [results[b]["speedup"] for b in labels]



fig1, ax_pct = plt.subplots(figsize=(12, 6))



# stacked‐bar for the %‐distribution

bottom = np.zeros(len(labels))

for i, cat in enumerate(categories):

    ax_pct.bar(x, pct_mat[i], width, bottom=bottom, label=cat)

    bottom += pct_mat[i]



ax_pct.set_xticks(x)

ax_pct.set_xticklabels(labels, rotation=45, ha="right")

ax_pct.set_ylabel("Percentage of Differences (%)")

ax_pct.set_title("Instruction‐Difference Distribution with Fittest Speedup Overlay")



# secondary axis for speedup

ax_spd = ax_pct.twinx()

ax_spd.plot(x, speeds, marker='o', linestyle='-', linewidth=2, label="Speedup", color='k')

ax_spd.axhline(1.0, color='gray', linestyle='--', label='Speedup = 1')

ax_spd.set_ylabel("Fittest Speedup")



# combine legends

h1, l1 = ax_pct.get_legend_handles_labels()

h2, l2 = ax_spd.get_legend_handles_labels()

ax_pct.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2)



fig1.tight_layout()

fig1.savefig("instruction_distribution_with_speedup.png")



# --- Plot 2: Number of Fittest_Results entries per benchmark ---



counts = [results[b]["count"] for b in labels]



fig2, ax2 = plt.subplots(figsize=(12, 4))

ax2.bar(labels, counts)

ax2.set_xticklabels(labels, rotation=45, ha="right")

ax2.set_ylabel("Number of Unique Fittest Policies")

ax2.set_title("Fittest_Results Entries per Benchmark")

fig2.tight_layout()

fig2.savefig("fittest_counts.png")



# --- Plot 3: Fittest Speedup per benchmark ---



fig3, ax3 = plt.subplots(figsize=(12, 4))

ax3.plot(labels, speeds, marker='o', linestyle='-')

ax3.axhline(1.0, color='gray', linestyle='--', label='Speedup = 1')

ax3.set_xticklabels(labels, rotation=45, ha="right")

ax3.set_ylabel("Fittest Speedup")

ax3.set_title("Fittest Speedup by Benchmark")

ax3.legend()

fig3.tight_layout()

fig3.savefig("fittest_speedup.png")



print("Saved plots as:")

print("  instruction_distribution_with_speedup.png")

print("  fittest_counts.png")

print("  fittest_speedup.png")


