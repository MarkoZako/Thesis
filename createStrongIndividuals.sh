#!/usr/bin/env bash

set -euo pipefail

IFS=$'\n\t'



BASE_DIR=/home/mzako001

OUT_DIR=$BASE_DIR/Individuals



# workloads to skip entirely

EXCLUDE=(All Bwaves Exchange Imagick Leela Perlbench Povray)



mkdir -p "$OUT_DIR"



counter=1



for dir in "$BASE_DIR"/*/; do

  name=$(basename "$dir")



  # map folder → workload

  if [[ "$name" == "Thesis" ]]; then

    wl="Mcf"

  elif [[ "$name" == Thesis_* ]]; then

    wl="${name#Thesis_}"

  elif [[ "$name" =~ ^(Roms|X264|Xz)$ ]]; then

    wl="$name"

  else

    continue

  fi



  # skip excluded

  for ex in "${EXCLUDE[@]}"; do 

    [[ "$wl" == "$ex" ]] && continue 2

  done



  CAND_DIR="$dir/Fittest_Results_MiddleCrossover"

  [[ -d "$CAND_DIR" ]] || continue



  # gather all the .txt files except similarity.txt

  candidates=()

  for f in "$CAND_DIR"/*.txt; do

    [[ -f "$f" ]] || continue

    [[ $(basename "$f") == "similarity.txt" || $(basename "$f") == "comparison_with_Thesis_All.txt" ]] && continue

    candidates+=("$f")

  done



  # if none, skip

  (( ${#candidates[@]} )) || continue



  # pick up to 3 at random

  picks=3

  (( ${#candidates[@]} < picks )) && picks=${#candidates[@]}

  mapfile -t chosen < <(printf '%s\n' "${candidates[@]}" | shuf | head -n "$picks")



  for src in "${chosen[@]}"; do

    dst="$OUT_DIR/$counter.txt"

    cp "$src" "$dst"

    echo "Copied $src → $dst"

    ((counter++))

  done

done


