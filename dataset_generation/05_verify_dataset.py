#!/usr/bin/env python3
"""Consistency checks for the released HotSpot dataset."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from common import read_flp, read_manifest
from settings import (
    GRID_COLS,
    GRID_ROWS,
    K_CHIPLET,
    K_FILLER,
    N_LAYOUTS,
    POWER_MAX_W,
    POWER_MIN_W,
    SAMPLES_PER_LAYOUT,
)


def close(a, b, tol=1e-10):
    return abs(a - b) <= tol


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    ap.add_argument("--inputs-only", action="store_true", help="Do not require HotSpot outputs")
    args = ap.parse_args()
    root = args.root.resolve()

    rows = read_manifest(root / "manifest.csv")
    assert len(rows) == N_LAYOUTS * SAMPLES_PER_LAYOUT == 4000
    counts = Counter(r["split"] for r in rows)
    assert counts == {"train": 3200, "val": 400, "test": 400}, counts

    for lid in range(N_LAYOUTS):
        layout = f"layout_{lid:03d}"
        rects = read_flp(root / "layouts" / layout / "chiplets.flp")
        chip = [r for r in rects if r.name.startswith("chiplet")]
        fill = [r for r in rects if r.name.startswith("filler")]
        assert len(chip) == 4
        for r in chip:
            assert close(r.resistivity, 1.0 / K_CHIPLET, 1e-9)
        for r in fill:
            assert close(r.resistivity, 1.0 / K_FILLER, 1e-9)

    for r in rows:
        for i in range(1, 5):
            p = float(r[f"p_chiplet{i}_W"])
            assert POWER_MIN_W <= p <= POWER_MAX_W

    if not args.inputs_only:
        for idx, r in enumerate(rows, 1):
            p = root / "processed" / r["layout"] / r["sample"]
            t = np.load(p / "temperature_layer0.npy")
            q = np.load(p / "power_map.npy")
            assert t.shape == (GRID_ROWS, GRID_COLS)
            assert q.shape == (GRID_ROWS, GRID_COLS)
            if not np.isfinite(t).all() or not np.isfinite(q).all():
                raise RuntimeError(f"Non-finite values in {p}")
            # Power map must preserve total power to numerical precision.
            if abs(float(q.sum()) - float(r["global_power_W"])) > 1e-4:
                raise RuntimeError(f"Power-map sum mismatch in {p}")
            if idx % 500 == 0:
                print(f"verified {idx}/4000 processed cases")

    print("Verification passed.")
    print(f"cases={len(rows)}, splits={dict(counts)}")


if __name__ == "__main__":
    main()
