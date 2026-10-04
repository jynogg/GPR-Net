#!/usr/bin/env bash
set -euo pipefail

HOTSPOT=$1
ROOT=${2:-generated_dataset}
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

python "$SCRIPT_DIR/00_make_thermal_config.py" --root "$ROOT"
python "$SCRIPT_DIR/01_generate_layouts.py" --root "$ROOT"
python "$SCRIPT_DIR/02_generate_power.py" --root "$ROOT"
python "$SCRIPT_DIR/05_verify_dataset.py" --root "$ROOT" --inputs-only
python "$SCRIPT_DIR/03_run_hotspot.py" --root "$ROOT" --hotspot "$HOTSPOT" --resume
python "$SCRIPT_DIR/04_extract_dataset.py" --root "$ROOT"
python "$SCRIPT_DIR/05_verify_dataset.py" --root "$ROOT"
