#!/bin/sh
# Download the national CDL zip for each year given, two at a time, resuming
# partial files. Usage: pipeline/fetch_cdl.sh 2019 2020 ...
# CropScape was down on 14 Nov 2026, so this is the USDA NASS fallback.
BASE=https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets
mkdir -p data/raw/cdl && cd data/raw/cdl || exit 1
fetch() {
  y=$1
  want=$(curl -sSI "$BASE/${y}_30m_cdls.zip" | tr -d '\r' | awk 'tolower($1)=="content-length:"{print $2}')
  for try in 1 2 3 4 5 6 7 8; do
    have=$(stat -f %z "${y}_30m_cdls.zip" 2>/dev/null || stat -c %s "${y}_30m_cdls.zip" 2>/dev/null || echo 0)
    [ "$have" = "$want" ] && { echo "$y done $have bytes"; return 0; }
    curl -sS -C - -o "${y}_30m_cdls.zip" "$BASE/${y}_30m_cdls.zip" || sleep 5
  done
  echo "$y FAILED"; return 1
}
for y in "$@"; do
  fetch "$y" &
  # keep two downloads running at once
  while [ "$(jobs -r | wc -l)" -ge 2 ]; do sleep 2; done
done
wait
