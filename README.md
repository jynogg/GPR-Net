# HotSpot dataset generator for GPR-Net

This folder reproduces the **dataset-generation protocol described in the final GPR-Net manuscript**.
It generates 40 geometric layouts, 100 power configurations per layout, runs HotSpot steady-state analysis, and extracts the 64x64 chiplet-layer temperature field used as the supervised target.

## 1. Physical model

Nominal three-layer stack:

| HotSpot grid layer | Description | Material / region | Thickness | Thermal conductivity | Nominal lateral size |
|---|---|---|---:|---:|---:|
| Layer 0 | Chiplet plane | chiplet: silicon; filler: effective material | 0.15 mm | chiplet 130 W/(m K); filler 10 W/(m K) | 10 x 10 mm |
| Layer 1 | Heat spreader | copper | 1.00 mm | 400 W/(m K) | 10 x 10 mm |
| Layer 2 | Heat sink | copper | 6.00 mm | 400 W/(m K) | 10 x 10 mm |

Boundary settings: ambient temperature 318.15 K and convection resistance 0.1 K/W.
Each grid layer contains 64x64 cells; the target is Layer 0 only.

### Important HotSpot implementation detail

HotSpot's grid model automatically appends its heat-spreader and heat-sink package layers when an LCF is supplied. Therefore `chiplet_layer.lcf` intentionally declares **only Layer 0**. The configured HotSpot spreader and sink then become Layer 1 and Layer 2, so `*.grid.steady` contains exactly three 64x64 layers.

Do **not** add the spreader and sink again to the LCF. Doing so would create five grid layers.

The chiplet and passive filler regions are in the same Layer 0. HotSpot's `detailed_3D` heterogeneous-RC feature is used: every floorplan block carries a volumetric heat capacity and thermal resistivity. Thus chiplets use `rho_th=1/130` while filler uses `rho_th=1/10` without introducing another layer.

The manuscript reports all three nominal lateral dimensions as 10x10 mm. In HotSpot's package equations, exact equality of die/spreader/sink side lengths produces zero-width peripheral package terms. The release therefore uses a nanometre-scale numerical regularization for the HotSpot side parameters (10.000001 mm spreader and 10.000002 mm sink). The 64x64 modeled plane remains exactly 10x10 mm, and the nominal dimensions remain 10.00 mm at the precision reported in the paper.

## 2. Dataset protocol

- Package plane: 10 x 10 mm
- 4 non-overlapping chiplets per original layout
- Chiplet size: 2 x 2 mm
- 40 layouts
- 100 independently sampled power configurations per layout
- Each chiplet power: uniform random value in [1, 10] W
- Total: 4,000 samples
- Layout-disjoint split: 32 train / 4 validation / 4 test layouts = 3200 / 400 / 400 samples

The manuscript does not specify the dataset random seed, placement lattice, or power-value rounding. This release fixes those implementation details for reproducibility: layout seed 2026, power seed 2027, 1-mm placement lattice, and one-decimal power values. They are configurable in the scripts.

## 3. Scripts

- `00_make_thermal_config.py` — writes HotSpot materials/config/LCF.
- `01_generate_layouts.py` — generates 40 unique non-overlapping layouts and exact filler tilings.
- `02_generate_power.py` — generates 100 single-case `.ptrace` files for every layout and `manifest.csv`.
- `03_run_hotspot.py` — runs HotSpot, verifies that every output has exactly Layers 0/1/2, and records runtime.
- `04_extract_dataset.py` — saves Layer-0 temperature, aligned power map, and global power as NumPy arrays.
- `05_verify_dataset.py` — checks sample counts, split counts, material resistivities, power ranges, shapes, and power conservation.
- `run_all.sh` — complete pipeline.

## 4. Usage

Install Python dependency:

```bash
pip install -r requirements.txt
```

Prepare and verify inputs only:

```bash
python 00_make_thermal_config.py --root generated_dataset
python 01_generate_layouts.py --root generated_dataset
python 02_generate_power.py --root generated_dataset
python 05_verify_dataset.py --root generated_dataset --inputs-only
```

Smoke-test one HotSpot case:

```bash
python 03_run_hotspot.py \
  --root generated_dataset \
  --hotspot /path/to/hotspot \
  --limit 1
```

Run the full dataset and extract NumPy arrays:

```bash
python 03_run_hotspot.py --root generated_dataset --hotspot /path/to/hotspot --resume
python 04_extract_dataset.py --root generated_dataset
python 05_verify_dataset.py --root generated_dataset
```

Or run everything:

```bash
bash run_all.sh /path/to/hotspot generated_dataset
```

## 5. Output layout

```text
generated_dataset/
├── thermal/
│   ├── chiplet.config
│   ├── chiplet.materials
│   ├── chiplet_layer.lcf
│   └── thermal_stack.json
├── layouts/
│   └── layout_000/
│       ├── chiplets.flp
│       └── layout.json
├── powers/
│   └── layout_000/
│       ├── sample_000.ptrace
│       └── ...
├── raw_results/
│   └── layout_000/
│       ├── sample_000.grid.steady
│       ├── sample_000.steady
│       └── sample_000.log
├── processed/
│   └── layout_000/sample_000/
│       ├── temperature_layer0.npy
│       ├── power_map.npy
│       ├── global_power.npy
│       └── meta.json
├── manifest.csv
├── layouts.json
├── splits.json
└── hotspot_runtime.csv
```

`temperature_layer0.npy` and `power_map.npy` are stored in raw HotSpot grid orientation: row 0 corresponds to the top of the floorplan.
