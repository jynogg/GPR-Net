#!/usr/bin/env python3
"""Generate 100 independent 1--10 W chiplet-power cases per layout."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from common import read_flp
from settings import (
    DEFAULT_POWER_SEED,
    N_LAYOUTS,
    POWER_DECIMALS,
    POWER_MAX_W,
    POWER_MIN_W,
    SAMPLES_PER_LAYOUT,
    split_for_layout,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    ap.add_argument("--seed", type=int, default=DEFAULT_POWER_SEED)
    args = ap.parse_args()

    manifest_path = args.root / "manifest.csv"
    rows = []

    for lid in range(N_LAYOUTS):
        layout_name = f"layout_{lid:03d}"
        layout_dir = args.root / "layouts" / layout_name
        flp = layout_dir / "chiplets.flp"
        if not flp.exists():
            raise FileNotFoundError(f"Run 01_generate_layouts.py first: {flp}")
        units = [r.name for r in read_flp(flp)]
        chiplet_units = [u for u in units if u.startswith("chiplet")]
        if len(chiplet_units) != 4:
            raise RuntimeError(f"{flp}: expected 4 chiplets, got {len(chiplet_units)}")

        out_dir = args.root / "powers" / layout_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Per-layout deterministic stream: changing one layout does not shift all later layouts.
        rng = random.Random(args.seed + lid)
        for sid in range(SAMPLES_PER_LAYOUT):
            p_chip = {
                u: round(rng.uniform(POWER_MIN_W, POWER_MAX_W), POWER_DECIMALS)
                for u in chiplet_units
            }
            ptrace = out_dir / f"sample_{sid:03d}.ptrace"
            values = [p_chip.get(u, 0.0) for u in units]
            ptrace.write_text(
                " ".join(units) + "\n" +
                " ".join(f"{v:.{POWER_DECIMALS}f}" for v in values) + "\n",
                encoding="utf-8",
            )
            total = sum(p_chip.values())
            rows.append({
                "layout_id": lid,
                "layout": layout_name,
                "sample_id": sid,
                "sample": f"sample_{sid:03d}",
                "split": split_for_layout(lid),
                "p_chiplet1_W": p_chip["chiplet1"],
                "p_chiplet2_W": p_chip["chiplet2"],
                "p_chiplet3_W": p_chip["chiplet3"],
                "p_chiplet4_W": p_chip["chiplet4"],
                "global_power_W": total,
                "ptrace": str(ptrace.relative_to(args.root)),
            })

    fieldnames = list(rows[0].keys())
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Generated {len(rows)} power cases and wrote {manifest_path}")


if __name__ == "__main__":
    main()
