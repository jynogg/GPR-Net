#!/usr/bin/env python3
"""Extract Layer-0 ground truth and the aligned 64x64 power map for each case."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from common import build_power_map_hotspot_order, parse_grid_steady, read_manifest, write_json
from settings import TARGET_LAYER


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    args = ap.parse_args()
    root = args.root.resolve()
    rows = read_manifest(root / "manifest.csv")

    for idx, rec in enumerate(rows, start=1):
        layout = rec["layout"]
        sample = rec["sample"]
        grid_file = root / "raw_results" / layout / f"{sample}.grid.steady"
        if not grid_file.exists():
            raise FileNotFoundError(f"Missing HotSpot output: {grid_file}")
        layers = parse_grid_steady(grid_file)
        if sorted(layers) != [0, 1, 2]:
            raise RuntimeError(f"Expected 3 layers in {grid_file}, got {sorted(layers)}")
        temp = layers[TARGET_LAYER]

        powers = {f"chiplet{i}": float(rec[f"p_chiplet{i}_W"]) for i in range(1, 5)}
        flp = root / "layouts" / layout / "chiplets.flp"
        pmap = build_power_map_hotspot_order(flp, powers)

        out = root / "processed" / layout / sample
        out.mkdir(parents=True, exist_ok=True)
        np.save(out / "temperature_layer0.npy", temp.astype(np.float32))
        np.save(out / "power_map.npy", pmap.astype(np.float32))
        np.save(out / "global_power.npy", np.asarray(float(rec["global_power_W"]), dtype=np.float32))
        write_json(
            out / "meta.json",
            {
                "layout": layout,
                "sample": sample,
                "split": rec["split"],
                "chiplet_powers_W": powers,
                "global_power_W": float(rec["global_power_W"]),
                "temperature_shape": list(temp.shape),
                "power_map_shape": list(pmap.shape),
                "orientation": "HotSpot grid order: row 0 is the top of the floorplan",
            },
        )
        if idx == 1 or idx % 500 == 0 or idx == len(rows):
            print(f"[{idx}/{len(rows)}] extracted {layout}/{sample}")

    print(f"Processed dataset written to {root / 'processed'}")


if __name__ == "__main__":
    main()
