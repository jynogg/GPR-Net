#!/usr/bin/env python3
"""Create the HotSpot thermal configuration for the manuscript's 3-layer stack.

Important HotSpot detail
------------------------
With an LCF, HotSpot automatically appends its heat-spreader and heat-sink package
layers. Therefore the LCF below intentionally contains ONLY the chiplet/filler
plane. Combined with the configured HotSpot spreader and sink, the resulting grid
output contains exactly three layers: Layer 0, Layer 1, Layer 2.

Heterogeneous conductivity within Layer 0 is enabled with '-detailed_3D on'.
The per-block specific heat and thermal resistivity are written in chiplets.flp by
01_generate_layouts.py. Thus chiplet regions use k=130 W/(m K), while passive
filler regions use k=10 W/(m K), without creating an extra physical layer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import write_json
from settings import (
    AMBIENT_K,
    C_CONVEC_J_PER_K,
    CHIPLET_LAYER_THICKNESS_M,
    CV_CHIPLET,
    CV_COPPER,
    CV_FILLER,
    GRID_COLS,
    GRID_ROWS,
    K_CHIPLET,
    K_FILLER,
    K_SINK,
    K_SPREADER,
    R_CONVEC_K_PER_W,
    SINK_SIDE_M,
    SINK_THICKNESS_M,
    SPREADER_SIDE_M,
    SPREADER_THICKNESS_M,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("generated_dataset"))
    args = ap.parse_args()

    thermal = args.root / "thermal"
    thermal.mkdir(parents=True, exist_ok=True)

    materials = f"""# HotSpot material file for the GPR-Net dataset\n# name / type / thermal conductivity [W/(m K)] / volumetric heat capacity [J/(m^3 K)]\n# Heat capacity does not affect the steady-state solution.\n\nsilicon\nsolid\n{K_CHIPLET:.12g}\n{CV_CHIPLET:.12g}\n\nfiller\nsolid\n{K_FILLER:.12g}\n{CV_FILLER:.12g}\n\ncopper\nsolid\n{K_SPREADER:.12g}\n{CV_COPPER:.12g}\n"""
    (thermal / "chiplet.materials").write_text(materials, encoding="utf-8")

    # Only the first physical plane is listed here. HotSpot appends spreader/sink.
    lcf = f"""# Layer 0: chiplet regions + passive filler, same physical plane\n# HotSpot appends Layer 1 (spreader) and Layer 2 (sink) from chiplet.config.\n0\nY\nY\n{CV_CHIPLET:.12g}\n{1.0 / K_CHIPLET:.15g}\n{CHIPLET_LAYER_THICKNESS_M:.15g}\nchiplets.flp\n"""
    (thermal / "chiplet_layer.lcf").write_text(lcf, encoding="utf-8")

    config = f"""# HotSpot configuration for the manuscript's 3-layer steady-state model\n\n# Layer 0 default material (local FLP overrides distinguish chiplet/filler)\n-t_chip {CHIPLET_LAYER_THICKNESS_M:.15g}\n-material_chip silicon\n\n# Layer 1: copper heat spreader\n-material_spreader copper\n-s_spreader {SPREADER_SIDE_M:.15g}\n-t_spreader {SPREADER_THICKNESS_M:.15g}\n\n# Layer 2: copper heat sink\n-material_sink copper\n-s_sink {SINK_SIDE_M:.15g}\n-t_sink {SINK_THICKNESS_M:.15g}\n\n# Boundary condition\n-r_convec {R_CONVEC_K_PER_W:.15g}\n-c_convec {C_CONVEC_J_PER_K:.15g}\n-ambient {AMBIENT_K:.15g}\n-init_temp {AMBIENT_K:.15g}\n\n# No explicit lower secondary path in the simplified manuscript stack\n-model_secondary 0\n\n# Grid model\n-model_type grid\n-grid_rows {GRID_ROWS}\n-grid_cols {GRID_COLS}\n-grid_map_mode center\n\n# No transient/leakage/package-fan model is used\n-leakage_used 0\n-package_model_used 0\n-sampling_intvl 0.01\n-base_proc_freq 3e9\n"""
    (thermal / "chiplet.config").write_text(config, encoding="utf-8")

    write_json(
        thermal / "thermal_stack.json",
        {
            "nominal_stack": [
                {
                    "layer": 0,
                    "description": "chiplet regions + passive filler",
                    "thickness_mm": CHIPLET_LAYER_THICKNESS_M * 1e3,
                    "k_chiplet_W_mK": K_CHIPLET,
                    "k_filler_W_mK": K_FILLER,
                    "lateral_size_mm": [10.0, 10.0],
                },
                {
                    "layer": 1,
                    "description": "heat spreader",
                    "material": "copper",
                    "thickness_mm": SPREADER_THICKNESS_M * 1e3,
                    "k_W_mK": K_SPREADER,
                    "lateral_size_mm": [10.0, 10.0],
                },
                {
                    "layer": 2,
                    "description": "heat sink",
                    "material": "copper",
                    "thickness_mm": SINK_THICKNESS_M * 1e3,
                    "k_W_mK": K_SINK,
                    "lateral_size_mm": [10.0, 10.0],
                },
            ],
            "ambient_K": AMBIENT_K,
            "r_convec_K_per_W": R_CONVEC_K_PER_W,
            "grid": [GRID_ROWS, GRID_COLS],
            "note": (
                "HotSpot appends its spreader and sink to the single LCF layer. "
                "Nanometre-scale side-length regularization is used only to avoid "
                "zero-width package-periphery terms when nominal sizes are all 10 mm."
            ),
            "hotspot_side_parameters_mm": {
                "spreader": SPREADER_SIDE_M * 1e3,
                "sink": SINK_SIDE_M * 1e3,
            },
        },
    )
    print(f"Wrote thermal configuration to: {thermal}")


if __name__ == "__main__":
    main()
