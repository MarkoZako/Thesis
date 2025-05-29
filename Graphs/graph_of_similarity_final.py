import os

import re

import matplotlib.pyplot as plt



# ─── CONFIG ────────────────────────────────────────────────────────────────────



base_path = "/home/mzako001"



# Benchmarks to exclude

exclude = {"Bwaves", "Perlbench", "Povray", "Exchange", "Imagick", "Leela"}



# Features to include (not instruction types)

features = ['DemotionClean', 'DemotionDirty', 'Insertion', 'PromotionClean', 'PromotionDirty']

color_map = {

    'DemotionClean': '#1f77b4',

    'DemotionDirty': '#ff7f0e',

    'Insertion': '#2ca02c',

    'PromotionClean': '#d62728',

    'PromotionDirty': '#9467bd'

}



# ─── HELPER ────────────────────────────────────────────────────────────────────



def extract_feature_counts(filepath):

    counts = {f: 0 for f in features}

    total = 0

    in_section = False



    with open(filepath) as f:

        for line in f:

            if "Overall difference distribution" in line:

                in_section = True

                continue

            if in_section:

                if "where:" in line:

                    match = re.search(r"where:\s+(\d+)", line)

                    if match:

                        total = int(match.group(1)) * 2  # scale to 100%

                    break

                match = re.match(r"\s*[A-Z]__([A-Za-z]+):\s+(\d+)", line)

                if match:

                    feat, val = match.groups()

                    if feat in counts:

                        counts[feat] += int(val)

    return counts, total



# ─── MAIN ──────────────────────────────────────────────────────────────────────



data = {}

benchmarks = []



for dname in os.listdir(base_path):

    if dname in exclude:

        continue

    if not (dname.startswith("Thesis") or dname in {"Roms", "Xz", "X264"}):

        continue



    folder = os.path.join(base_path, dname, "Fittest_Results_MiddleCrossover")

    if not os.path.isdir(folder):

        continue



    sim_path = os.path.join(folder, "similarity.txt")

    if not os.path.isfile(sim_path):

        continue



    counts, total = extract_feature_counts(sim_path)

    if total == 0:

        continue



    name = dname.replace("Thesis_", "")

    data[name] = [counts[f] / total * 100 for f in features]

    benchmarks.append(name)



# ─── PLOT ──────────────────────────────────────────────────────────────────────



# Sort for consistent order

benchmarks.sort()

bar_data = [data[b] for b in benchmarks]



# Create stacked bar chart

fig, ax = plt.subplots(figsize=(12, 6))

bottoms = [0] * len(benchmarks)



for i, feat in enumerate(features):

    values = [entry[i] for entry in bar_data]

    ax.bar(benchmarks, values, bottom=bottoms, color=color_map[feat], label=feat)

    bottoms = [bottoms[j] + values[j] for j in range(len(values))]



# Final formatting

plt.xticks(rotation=45, ha="right")

plt.ylabel("Percentage of Differences (%)")

plt.title("Instruction-Difference Distribution by Benchmark")

plt.legend(title="Feature", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()

plt.savefig("final_percentage_feature_importance.png")

print("✅ Plot saved as instruction_diff_distribution.png")


