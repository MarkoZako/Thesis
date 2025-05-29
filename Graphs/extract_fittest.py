#!/usr/bin/env python3
import os, re, shutil

base_dir = "/home/mzako001"
folders = [
    "Thesis_All", "Thesis_Blender", "Thesis_Bwaves", "Thesis_Cam4", "Thesis_CactuBSSN",
    "Thesis_Exchange", "Thesis_Gcc", "Thesis_Lbm", "Thesis_Parest", "Thesis_Povray",
    "Thesis_Wrf", "Thesis_Xalancbmk", "Thesis_Fotonik3d", "Thesis_Imagick", "Thesis_Leela",
    "Thesis_Omnetpp", "Thesis_Perlbench", "Roms", "X264", "Xz", "Thesis"  # Thesis = Mcf
]

# Regex to find the first "<int>DOT<int>" in the filename
dot_pat = re.compile(r"(\d+DOT\d+)")

for folder in folders:
    results_dir = os.path.join(base_dir, folder, "Results")
    fittest_dir = os.path.join(base_dir, folder, "Fittest_Results_MiddleCrossover")

    if not os.path.isdir(results_dir):
        print(f"⚠️  Skipping missing folder: {results_dir}")
        continue

    # Make sure the output folder exists
    os.makedirs(fittest_dir, exist_ok=True)

    # --- 1) First pass: find max float value ---
    max_val = None
    for fname in os.listdir(results_dir):
        m = dot_pat.search(fname)
        if not m:
            continue
        # convert '123DOT456' -> 123.456
        val = float(m.group(1).replace("DOT", "."))
        if max_val is None or val > max_val:
            max_val = val

    if max_val is None:
        print(f"❌ No DOT‑pattern files found in {results_dir}")
        continue

    # --- 2) Second pass: copy all files matching max_val ---
    copied = 0
    for fname in os.listdir(results_dir):
        m = dot_pat.search(fname)
        if not m:
            continue
        if float(m.group(1).replace("DOT", ".")) == max_val:
            src = os.path.join(results_dir, fname)
            dst = os.path.join(fittest_dir, fname)
            shutil.copy2(src, dst)
            copied += 1

    print(f"✅ {folder}: max DOT‑value = {max_val} → copied {copied} file(s) into Fittest_Results")

