#!/usr/bin/env bash
# Fetch a Wetterzentrale single-model forecast feed (op_feed.php) and write
# the 2m temperature (TMP_2) as CSV: Date, Time, Temperature.
#
# - One row per forecast timestamp, in the location's local time. The
#   feed's dt values are already shifted to local time (its own chart
#   formats them as-UTC), so they must be formatted WITHOUT applying the
#   feed's `timezone` offset — adding it double-shifts the times.
# - The feed also carries dew point (DPT_2), cloud cover (TCDC_0), CAPE,
#   precipitation (APCP_0) and wind (ws/wd/wdn) per row if ever needed.
#
# Usage: fetch_wetterzentrale_csv.sh [-g geoid] [-m model] [-r run] [-d date] [-o outfile]
#   -g  geoid   location id            (default 140524, Berlin Friedrichshain)
#   -m  model   model id, e.g. ico     (default ico = ICON)
#   -r  run     model run, e.g. 00/12  (default 00)
#   -d  date    run date YYYY-MM-DD    (default today)
#   -o  outfile output CSV path        (default tmp/wetterzentrale-2m-temp.csv)
set -euo pipefail

geoid=140524
model=ico
run=00
date=$(date +%Y-%m-%d)
outfile=tmp/wetterzentrale-2m-temp.csv

while getopts "g:m:r:d:o:h" opt; do
  case $opt in
    g) geoid=$OPTARG ;;
    m) model=$OPTARG ;;
    r) run=$OPTARG ;;
    d) date=$OPTARG ;;
    o) outfile=$OPTARG ;;
    h) sed -n '2,17p' "$0"; exit 0 ;;
    *) exit 1 ;;
  esac
done

mkdir -p "$(dirname "$outfile")"

url="https://wetterzentrale.de/op_feed.php?geoid=${geoid}&var=4,5,10,83,82,86,87&run=${run}&date=${date}&model=${model}&member=OP&bw=1&tr=1"

curl -fsS "$url" \
  | jq -r '
      ["Date","Time","Temperature"],
        (.[0].forecast[]
          | [ (.dt/1000 | strftime("%Y-%m-%d")),
              (.dt/1000 | strftime("%H:%M")),
              .TMP_2 ])
      | @csv
    ' > "$outfile"

echo "Wrote $outfile ($(($(wc -l < "$outfile") - 1)) data rows)" >&2
