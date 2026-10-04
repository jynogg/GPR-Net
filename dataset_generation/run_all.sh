#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash run_all.sh /path/to/hotspot [dataset_root]
HOTSPOT=${1:?"Please provide path to HotSpot executable"}
ROOT=${2:-generated_dataset}

python 00_make_thermal_config.py --root "$ROOT"
python 01_generate_layouts.py --root "$ROOT"
python 02_generate_power.py --root "$ROOT"
python 05_verify_dataset.py --root "$ROOT" --inputs-only
python 03_run_hotspot.py --root "$ROOT" --hotspot "$HOTSPOT" --resume
python 04_extract_dataset.py --root "$ROOT"
python 05_verify_dataset.py --root "$ROOT"
