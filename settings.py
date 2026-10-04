"""Central settings for the HotSpot dataset described in the GPR-Net manuscript.

Only parameters explicitly reported in the manuscript are treated as physical/model
settings. A few dataset-generation details that the manuscript does not specify
(random seeds, 1-mm placement lattice, and one-decimal power rounding) are exposed
as reproducibility settings and can be changed from the command line where relevant.
"""
from pathlib import Path

# -----------------------------------------------------------------------------
# Dataset geometry (manuscript Sec. 2.3)
# -----------------------------------------------------------------------------
PACKAGE_SIZE_M = 10.0e-3
CHIPLET_W_M = 2.0e-3
CHIPLET_H_M = 2.0e-3
N_CHIPLETS = 4
N_LAYOUTS = 40
SAMPLES_PER_LAYOUT = 100

# Layout-disjoint split (manuscript Sec. 4.1)
N_TRAIN_LAYOUTS = 32
N_VAL_LAYOUTS = 4
N_TEST_LAYOUTS = 4

# Grid resolution
GRID_ROWS = 64
GRID_COLS = 64
TARGET_LAYER = 0

# -----------------------------------------------------------------------------
# Power settings (manuscript Sec. 2.3)
# -----------------------------------------------------------------------------
POWER_MIN_W = 1.0
POWER_MAX_W = 10.0

# The paper states 1--10 W but does not specify rounding. The original local
# ptrace convention used one decimal place, so the release keeps that convention.
POWER_DECIMALS = 1

# -----------------------------------------------------------------------------
# Three-layer thermal stack (manuscript Table 1)
# -----------------------------------------------------------------------------
# Layer 0: chiplet + passive filler, same physical plane and thickness
CHIPLET_LAYER_THICKNESS_M = 0.15e-3
K_CHIPLET = 130.0          # W/(m K), silicon region
K_FILLER = 10.0            # W/(m K), effective passive filler region

# Layer 1: copper heat spreader
SPREADER_THICKNESS_M = 1.0e-3
K_SPREADER = 400.0

# Layer 2: copper heat sink
SINK_THICKNESS_M = 6.0e-3
K_SINK = 400.0

# Nominal lateral size in the manuscript is 10 x 10 mm for all three layers.
# HotSpot's built-in package-layer equations contain zero-width peripheral terms
# when s_spreader == die_size or s_sink == s_spreader. We therefore use a
# nanometre-scale numerical regularization for the package *side parameters*.
# At the manuscript precision these are still 10.00 mm. The 64x64 grid itself
# remains exactly the 10 x 10 mm chiplet plane.
PACKAGE_SIDE_EPS_M = 1.0e-9
SPREADER_SIDE_M = PACKAGE_SIZE_M + PACKAGE_SIDE_EPS_M
SINK_SIDE_M = PACKAGE_SIZE_M + 2.0 * PACKAGE_SIDE_EPS_M

# Boundary conditions (manuscript Sec. 2.3)
AMBIENT_K = 318.15
R_CONVEC_K_PER_W = 0.1

# HotSpot needs volumetric heat capacities in its RC description even for a
# steady-state run. These values do NOT affect the steady-state solution.
CV_CHIPLET = 1.75e6        # J/(m^3 K)
CV_FILLER = 1.75e6         # J/(m^3 K)
CV_COPPER = 3.55e6         # J/(m^3 K)
C_CONVEC_J_PER_K = 140.4   # irrelevant to steady state, kept for completeness

# -----------------------------------------------------------------------------
# Reproducibility settings not uniquely specified in the manuscript
# -----------------------------------------------------------------------------
DEFAULT_LAYOUT_SEED = 2026
DEFAULT_POWER_SEED = 2027
DEFAULT_PLACEMENT_STEP_M = 1.0e-3

# Output root used by scripts unless overridden
DEFAULT_DATASET_ROOT = Path("generated_dataset")


def split_for_layout(layout_id: int) -> str:
    if 0 <= layout_id < N_TRAIN_LAYOUTS:
        return "train"
    if layout_id < N_TRAIN_LAYOUTS + N_VAL_LAYOUTS:
        return "val"
    if layout_id < N_LAYOUTS:
        return "test"
    raise ValueError(f"layout_id out of range: {layout_id}")
