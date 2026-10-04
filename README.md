# GPR-Net

Official code repository accompanying the manuscript **“Two-stage fast thermal analysis for 2.5D chiplets via graph-prior guidance and spatial refinement.”**

GPR-Net is a two-stage steady-state thermal-analysis framework for 2.5D chiplets. The structural stage uses an edge-aware GAT followed by GCN propagation to predict node-level temperatures, and the spatial stage uses U-Net refinement to recover hotspot morphology and local temperature gradients.

## Repository structure

```text
GPR-Net/
├── dataset_generation/
│   ├── 00_make_thermal_config.py
│   ├── 01_generate_layouts.py
│   ├── 02_generate_power.py
│   ├── 03_run_hotspot.py
│   ├── 04_extract_dataset.py
│   ├── 05_verify_dataset.py
│   ├── common.py
│   ├── settings.py
│   ├── run_all.sh
│   └── README.md
├── model/
│   └── README.md
├── requirements.txt
├── .gitignore
└── README.md
```

At present, this repository contains the HotSpot dataset-generation and verification pipeline together with the manuscript pseudocode for the GPR-Net forward-propagation procedure. The full model implementation will be released after paper acceptance.

## Dataset configuration

The released scripts reproduce the dataset protocol described in the manuscript:

- package plane: 10 × 10 mm²;
- 4 non-overlapping chiplets per original layout;
- chiplet size: 2 × 2 mm²;
- 40 layouts;
- 100 power configurations per layout;
- 4,000 samples in total;
- 64 × 64 grid per physical layer;
- layout-disjoint split: 32 train / 4 validation / 4 test layouts.

The three-layer thermal stack is:

| Layer | Region / material | Thickness | Thermal conductivity |
|---|---|---:|---:|
| Layer 0 | Silicon chiplet regions | 0.15 mm | 130 W/(m·K) |
| Layer 0 | Passive filler region | 0.15 mm | 10 W/(m·K) |
| Layer 1 | Copper heat spreader | 1.00 mm | 400 W/(m·K) |
| Layer 2 | Copper heat sink | 6.00 mm | 400 W/(m·K) |

The ambient temperature is 318.15 K and the convective thermal resistance is 0.1 K/W. Each chiplet is assigned an independently sampled power value in the range 1–10 W. The Layer-0 64 × 64 steady-state temperature field is used as the supervised ground-truth target.

## Quick start

Install the Python dependency:

```bash
pip install -r requirements.txt
```

Run the complete dataset-generation pipeline:

```bash
bash dataset_generation/run_all.sh /path/to/hotspot generated_dataset
```

For detailed information about HotSpot configuration, output files, and individual generation steps, see:

```text
dataset_generation/README.md
```

The model-level pseudocode reported as Algorithm 1 in the manuscript is available at:

```text
model/README.md
```

## Reproducibility note

The manuscript specifies the physical configuration, dataset size, grid resolution, power range, and layout-disjoint split. Random seeds, placement lattice, and power-value rounding are fixed in the released scripts to make regeneration deterministic.

## Requirements

- Python 3
- NumPy
- A compatible HotSpot executable with grid-mode support

HotSpot itself is not redistributed in this repository.

## Citation

If you use this repository, please cite the associated GPR-Net manuscript. The final bibliographic information can be added after publication.
