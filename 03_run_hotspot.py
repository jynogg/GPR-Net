#!/usr/bin/env python3
"""Run HotSpot for all 4,000 cases and enforce the manuscript's 3-layer output.

Requirements:
  * HotSpot 6.x/7.x with grid mode and detailed_3D heterogeneous-RC support.
  * 00_make_thermal_config.py, 01_generate_layouts.py, 02_generate_power.py run first.
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import time
from pathlib import Path

from common import parse_grid_steady, read_manifest
from settings import AMBIENT_K, TARGET_LAYER


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    ap.add_argument("--hotspot", type=Path, required=True, help="Path to HotSpot executable")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="Run only first N cases (smoke test)")
    ap.add_argument("--no-temp-sanity", action="store_true", help="Disable 250--500 K sanity check")
    args = ap.parse_args()

    root = args.root.resolve()
    hotspot = args.hotspot.resolve()
    if not hotspot.exists():
        raise FileNotFoundError(hotspot)

    thermal = root / "thermal"
    config = thermal / "chiplet.config"
    materials = thermal / "chiplet.materials"
    lcf = thermal / "chiplet_layer.lcf"
    manifest = root / "manifest.csv"
    for p in (config, materials, lcf, manifest):
        if not p.exists():
            raise FileNotFoundError(p)

    records = read_manifest(manifest)
    if args.limit is not None:
        records = records[:args.limit]

    runtime_rows = []
    for idx, rec in enumerate(records, start=1):
        layout = rec["layout"]
        sample = rec["sample"]
        layout_dir = root / "layouts" / layout
        ptrace = root / rec["ptrace"]
        out_dir = root / "raw_results" / layout
        out_dir.mkdir(parents=True, exist_ok=True)
        steady = out_dir / f"{sample}.steady"
        grid = out_dir / f"{sample}.grid.steady"
        log = out_dir / f"{sample}.log"

        if args.resume and grid.exists():
            try:
                layers = parse_grid_steady(grid)
                if sorted(layers) == [0, 1, 2]:
                    continue
            except Exception:
                pass

        cmd = [
            str(hotspot),
            "-c", str(config),
            "-p", str(ptrace),
            "-materials_file", str(materials),
            "-grid_layer_file", str(lcf),
            "-model_type", "grid",
            "-detailed_3D", "on",
            "-steady_file", str(steady),
            "-grid_steady_file", str(grid),
        ]

        t0 = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=layout_dir,  # chiplet_layer.lcf refers to local chiplets.flp
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        elapsed = time.perf_counter() - t0
        log.write_text(proc.stdout, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"HotSpot failed for {layout}/{sample}. See {log}")

        layers = parse_grid_steady(grid)
        if sorted(layers) != [0, 1, 2]:
            raise RuntimeError(
                f"{grid}: expected exactly 3 HotSpot grid layers [0,1,2], got {sorted(layers)}. "
                "Do not add spreader/sink again to the LCF; HotSpot appends them automatically."
            )

        chip = layers[TARGET_LAYER]
        if not args.no_temp_sanity:
            if not (250.0 <= float(chip.min()) <= 500.0 and 250.0 <= float(chip.max()) <= 500.0):
                raise RuntimeError(
                    f"Unphysical temperature range in {grid}: {chip.min():.3f}..{chip.max():.3f} K. "
                    "Check the HotSpot build/libraries and package-size regularization."
                )
            if float(chip.max()) < AMBIENT_K - 1.0:
                raise RuntimeError(f"Temperature field is below ambient in {grid}")

        runtime_rows.append({
            "layout": layout,
            "sample": sample,
            "seconds": f"{elapsed:.9f}",
        })
        if idx == 1 or idx % 50 == 0 or idx == len(records):
            print(f"[{idx}/{len(records)}] {layout}/{sample}: {elapsed:.3f} s")

    rt_path = root / "hotspot_runtime.csv"
    if runtime_rows:
        write_header = not rt_path.exists() or not args.resume
        mode = "a" if args.resume and rt_path.exists() else "w"
        with rt_path.open(mode, newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["layout", "sample", "seconds"])
            if write_header:
                w.writeheader()
            w.writerows(runtime_rows)
    print("HotSpot run complete.")


if __name__ == "__main__":
    main()
