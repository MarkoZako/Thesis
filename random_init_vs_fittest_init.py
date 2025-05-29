#!/usr/bin/env python3

import os

import re

from datetime import datetime



# ─── CONFIG ────────────────────────────────────────────────────────────────────



RESULTS_DIR = "/home/mzako001/Thesis_All/Results"



# threshold: May 18, 2025 @ 14:30 local time

THRESHOLD = datetime(2025, 5, 18, 14, 30)

threshold_ts = THRESHOLD.timestamp()



# regex to pull the “1DOT020880” → “1.020880”

speedup_rx = re.compile(r"(\d+)DOT(\d+)")



# ─── SCAN & COLLECT ─────────────────────────────────────────────────────────────



max_before = ("", -float("inf"))

max_after  = ("", -float("inf"))



for fname in os.listdir(RESULTS_DIR):

    if not fname.endswith(".txt"):

        continue



    m = speedup_rx.search(fname)

    if not m:

        # skip anything that doesn't match

        continue



    # build a float from "1DOT020880" → "1.020880"

    speedup = float(f"{m.group(1)}.{m.group(2)}")



    fullpath = os.path.join(RESULTS_DIR, fname)

    mtime    = os.path.getmtime(fullpath)



    if mtime < threshold_ts:

        if speedup > max_before[1]:

            max_before = (fname, speedup)

    else:

        if speedup > max_after[1]:

            max_after = (fname, speedup)



# ─── OUTPUT ────────────────────────────────────────────────────────────────────



if max_before[0]:

    print(f"Max before {THRESHOLD:%Y-%m-%d %H:%M}: {max_before[1]:.6f}  ← {max_before[0]}")

else:

    print(f"No files found before {THRESHOLD:%Y-%m-%d %H:%M}")



if max_after[0]:

    print(f"Max after  {THRESHOLD:%Y-%m-%d %H:%M}: {max_after[1]:.6f}  ← {max_after[0]}")

else:

    print(f"No files found after  {THRESHOLD:%Y-%m-%d %H:%M}")


