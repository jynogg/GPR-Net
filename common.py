from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from settings import GRID_COLS, GRID_ROWS, PACKAGE_SIZE_M


@dataclass(frozen=True)
class Rect:
    name: str
    w: float
    h: float
    x: float
    y: float
    specific_heat: float | None = None
    resistivity: float | None = None

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y + self.h


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_flp(path: Path) -> list[Rect]:
    rects: list[Rect] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) not in (5, 7):
            raise ValueError(f"Unexpected FLP format in {path}: {raw}")
        name, w, h, x, y = parts[:5]
        sh = float(parts[5]) if len(parts) == 7 else None
        rho = float(parts[6]) if len(parts) == 7 else None
        rects.append(Rect(name, float(w), float(h), float(x), float(y), sh, rho))
    return rects


def parse_grid_steady(path: Path) -> dict[int, np.ndarray]:
    """Read HotSpot *.grid.steady into {layer_index: (rows, cols) array}."""
    layers: dict[int, list[float]] = {}
    current: int | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Layer ") and line.endswith(":"):
            current = int(line[len("Layer "):-1])
            if current in layers:
                raise ValueError(f"Duplicate Layer {current} in {path}")
            layers[current] = []
            continue
        if current is None:
            continue
        parts = line.split()
        if len(parts) >= 2:
            layers[current].append(float(parts[1]))

    out: dict[int, np.ndarray] = {}
    expected = GRID_ROWS * GRID_COLS
    for layer, vals in layers.items():
        if len(vals) != expected:
            raise ValueError(
                f"{path}: Layer {layer} has {len(vals)} cells, expected {expected}"
            )
        out[layer] = np.asarray(vals, dtype=np.float32).reshape(GRID_ROWS, GRID_COLS)
    return out


def build_power_map_hotspot_order(flp_path: Path, chiplet_powers: dict[str, float]) -> np.ndarray:
    """Build a 64x64 node-power map in HotSpot grid-row order.

    HotSpot row i=0 corresponds to the top of the floorplan. A chiplet's total
    power is divided uniformly among grid cells whose centers fall inside it.
    This matches the grid-cell/node power convention used by the graph input.
    """
    rects = [r for r in read_flp(flp_path) if r.name.startswith("chiplet")]
    arr = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.float32)
    cw = PACKAGE_SIZE_M / GRID_COLS
    ch = PACKAGE_SIZE_M / GRID_ROWS

    for rect in rects:
        hits: list[tuple[int, int]] = []
        for i in range(GRID_ROWS):
            y = PACKAGE_SIZE_M - (i + 0.5) * ch
            if not (rect.y <= y < rect.top):
                continue
            for j in range(GRID_COLS):
                x = (j + 0.5) * cw
                if rect.x <= x < rect.right:
                    hits.append((i, j))
        if not hits:
            raise RuntimeError(f"No grid cells hit {rect.name} in {flp_path}")
        p_cell = float(chiplet_powers[rect.name]) / len(hits)
        for i, j in hits:
            arr[i, j] += p_cell
    return arr


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
