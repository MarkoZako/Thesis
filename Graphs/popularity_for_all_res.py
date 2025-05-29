#!/usr/bin/env python3

import os



def extract_L2_section(filepath):

    """

    Extract lines under the .L2: label until the next label.

    """

    in_L2 = False

    section = []

    with open(filepath) as f:

        for line in f:

            stripped = line.strip()

            if not in_L2 and ".L2:" in line:

                in_L2 = True

                continue

            if in_L2:

                # skip leading blanks/comments

                if not section and (stripped == "" or stripped.startswith("#")):

                    continue

                # stop at next label like ".XYZ:"

                if stripped.startswith(".") and stripped.endswith(":"):

                    break

                if stripped.startswith("#"):

                    continue

                section.append(stripped)

    return section



def parse_values(policy_lines):

    """

    Parse lines of form NAME%VALUE into (NAME, int(VALUE)).

    """

    parsed = []

    for line in policy_lines:

        if "%" in line:

            try:

                name, val = line.split("%")

                parsed.append((name.strip(), int(val.strip())))

            except ValueError:

                continue

    return parsed



# --- Main popularity script ---



BASE_DIR = "/home/mzako001"



# detect all applicable folders

folders = [

    d for d in os.listdir(BASE_DIR)

    if os.path.isdir(os.path.join(BASE_DIR, d))

    and (d == "Thesis" or d.startswith("Thesis_") or d in ("Roms", "X264", "Xz"))

]



# gather all policy files (excluding similarity.txt)

policy_paths = []

for folder in folders:

    f_dir = os.path.join(BASE_DIR, folder, "Results")

    if not os.path.isdir(f_dir):

        continue

    for fname in os.listdir(f_dir):

        if fname.endswith(".txt") and fname != "similarity.txt":

            rel_path = os.path.join(folder, "Results", fname)

            policy_paths.append(rel_path)



# compute signature for each policy

signatures = {}

for rel_path in policy_paths:

    full_path = os.path.join(BASE_DIR, rel_path)

    sec = extract_L2_section(full_path)

    vec = parse_values(sec)

    # signature is the tuple of values

    signature = tuple(val for (_, val) in vec)

    signatures[rel_path] = signature



# brute-force count appearances

popularity = {}

for p1 in policy_paths:

    sig1 = signatures[p1]

    count = sum(1 for p2 in policy_paths if signatures[p2] == sig1)

    popularity[p1] = count



# write results, only those with popularity > 1

with open("popularity_all_res.txt", "w") as out:

    out.write("Policy popularity by configuration:\n")

    out.write("===================================\n\n")

    for p, cnt in sorted(popularity.items(), key=lambda x: -x[1]):

        if cnt > 1:

            out.write(f"{p}: appears in {cnt} Fittest_Results directories\n")



print("Done. See popularity.txt for results.")


