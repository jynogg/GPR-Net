#!/usr/bin/env python3
"""Generate 40 unique layouts, each with four non-overlapping 2x2 mm chiplets.

The non-chiplet area is exactly tiled by passive filler rectangles. Chiplet and
filler blocks are written into the SAME HotSpot floorplan layer with different
per-block thermal resistivities, using HotSpot's detailed_3D heterogeneous-layer
format:

  <name> <w> <h> <x> <y> <volumetric_heat_capacity> <thermal_resistivity>

Thermal resistivity is 1/k, so chiplet blocks use 1/130 and filler blocks 1/10.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from common import Rect, write_json
from settings import (
    CHIPLET_H_M,
    CHIPLET_W_M,
    CV_CHIPLET,
    CV_FILLER,
    DEFAULT_LAYOUT_SEED,
    DEFAULT_PLACEMENT_STEP_M,
    K_CHIPLET,
    K_FILLER,
    N_CHIPLETS,
    N_LAYOUTS,
    PACKAGE_SIZE_M,
    split_for_layout,
)


def conflict(a: Rect, b: Rect) -> bool:
    return not (a.right <= b.x or b.right <= a.x or a.top <= b.y or b.top <= a.y)


def generate_one(rng: random.Random, step: float) -> list[Rect]:
    max_x = PACKAGE_SIZE_M - CHIPLET_W_M
    max_y = PACKAGE_SIZE_M - CHIPLET_H_M
    nx = round(max_x / step)
    ny = round(max_y / step)
    candidates = [(ix * step, iy * step) for iy in range(ny + 1) for ix in range(nx + 1)]

    for _ in range(10000):
        rng.shuffle(candidates)
        placed: list[Rect] = []
        for x, y in candidates:
            r = Rect("", CHIPLET_W_M, CHIPLET_H_M, x, y)
            if all(not conflict(r, q) for q in placed):
                placed.append(r)
                if len(placed) == N_CHIPLETS:
                    placed.sort(key=lambda z: (z.y, z.x))
                    return [
                        Rect(f"chiplet{i+1}", z.w, z.h, z.x, z.y, CV_CHIPLET, 1.0 / K_CHIPLET)
                        for i, z in enumerate(placed)
                    ]
    raise RuntimeError("Could not generate a legal layout")


def layout_key(rects: list[Rect]) -> tuple:
    return tuple(sorted((round(r.x, 12), round(r.y, 12), r.w, r.h) for r in rects))


def decompose_filler(chiplets: list[Rect], step: float) -> list[Rect]:
    """Exact rectangular tiling of the remaining plane on the placement lattice."""
    n = round(PACKAGE_SIZE_M / step)
    occ = np.zeros((n, n), dtype=np.uint8)  # bottom-up lattice, used only for tiling
    for c in chiplets:
        x0, y0 = round(c.x / step), round(c.y / step)
        w, h = round(c.w / step), round(c.h / step)
        if np.any(occ[y0:y0+h, x0:x0+w]):
            raise RuntimeError("Unexpected chiplet overlap")
        occ[y0:y0+h, x0:x0+w] = 1

    used = occ.copy()
    fillers: list[Rect] = []
    fid = 1
    for y in range(n):
        for x in range(n):
            if used[y, x]:
                continue
            width = 0
            while x + width < n and used[y, x + width] == 0:
                width += 1
            height = 1
            while y + height < n and np.all(used[y + height, x:x+width] == 0):
                height += 1
            used[y:y+height, x:x+width] = 2
            fillers.append(
                Rect(
                    f"filler{fid}", width * step, height * step, x * step, y * step,
                    CV_FILLER, 1.0 / K_FILLER,
                )
            )
            fid += 1

    if not np.all(used):
        raise RuntimeError("Filler decomposition left uncovered area")
    return fillers


def write_flp(path: Path, blocks: list[Rect]) -> None:
    lines = [
        "# name width height left_x bottom_y volumetric_heat_capacity thermal_resistivity",
        "# dimensions: m; heat capacity: J/(m^3 K); resistivity: (m K)/W",
    ]
    for r in blocks:
        lines.append(
            f"{r.name}\t{r.w:.9g}\t{r.h:.9g}\t{r.x:.9g}\t{r.y:.9g}\t"
            f"{r.specific_heat:.9g}\t{r.resistivity:.12g}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    ap.add_argument("--seed", type=int, default=DEFAULT_LAYOUT_SEED)
    ap.add_argument("--placement-step-mm", type=float, default=DEFAULT_PLACEMENT_STEP_M * 1e3)
    args = ap.parse_args()

    step = args.placement_step_mm * 1e-3
    if step <= 0:
        raise ValueError("placement step must be positive")
    for v, label in [(PACKAGE_SIZE_M, "package"), (CHIPLET_W_M, "chiplet width"), (CHIPLET_H_M, "chiplet height")]:
        q = v / step
        if abs(q - round(q)) > 1e-9:
            raise ValueError(f"{label} is not divisible by placement step")

    layout_root = args.root / "layouts"
    layout_root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    seen: set[tuple] = set()
    records = []

    lid = 0
    while lid < N_LAYOUTS:
        chiplets = generate_one(rng, step)
        key = layout_key(chiplets)
        if key in seen:
            continue
        seen.add(key)
        fillers = decompose_filler(chiplets, step)

        d = layout_root / f"layout_{lid:03d}"
        d.mkdir(parents=True, exist_ok=True)
        write_flp(d / "chiplets.flp", chiplets + fillers)
        meta = {
            "layout_id": lid,
            "split": split_for_layout(lid),
            "package_mm": [10.0, 10.0],
            "chiplets": [
                {"name": c.name, "x_mm": c.x*1e3, "y_mm": c.y*1e3, "w_mm": c.w*1e3, "h_mm": c.h*1e3}
                for c in chiplets
            ],
            "n_fillers": len(fillers),
            "placement_step_mm": args.placement_step_mm,
            "layout_seed": args.seed,
        }
        write_json(d / "layout.json", meta)
        records.append(meta)
        lid += 1

    write_json(args.root / "layouts.json", records)
    write_json(
        args.root / "splits.json",
        {
            "train": [f"layout_{i:03d}" for i in range(0, 32)],
            "val": [f"layout_{i:03d}" for i in range(32, 36)],
            "test": [f"layout_{i:03d}" for i in range(36, 40)],
        },
    )
    print(f"Generated {N_LAYOUTS} unique layouts under {layout_root}")


if __name__ == "__main__":
    main()
