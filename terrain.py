"""Mars's elevation map, from MOLA.

The Mars Orbiter Laser Altimeter flew on Mars Global Surveyor and measured the
whole planet's shape. We use the coarse 4-pixels-per-degree grid (2 MB), which
is plenty for choosing a delivery region: it resolves about 15 km on the ground.

Elevation matters here for one practical reason. Mars's atmosphere is thin
everywhere, but it is twice as thick over Hellas Basin as over the Tharsis
volcanoes, because Hellas is 16 km lower down. Anything arriving from space
has to shed its speed in that air, so low ground is a far easier target.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

URL = ("https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/"
       "mgsl_300x/meg004/megt90n000cb.img")
DATA = Path(__file__).parent / "data"
IMG = DATA / "megt90n000cb.img"
ROWS, COLS = 720, 1440  # 4 pixels per degree, 90N..90S and 0..360 east
SCALE_HEIGHT_KM = 11.1  # Mars's atmospheric scale height


def load() -> np.ndarray:
    """Elevation in metres above the Mars datum, as a 720 x 1440 grid."""
    return np.fromfile(IMG, dtype=">i2").reshape(ROWS, COLS).astype(np.float32)


def at(grid: np.ndarray, lat_deg, lon_east_deg):
    """Elevation at a latitude and east longitude, in metres."""
    row = np.clip(((90 - np.asarray(lat_deg)) * 4).astype(int), 0, ROWS - 1)
    col = (np.asarray(lon_east_deg) * 4).astype(int) % COLS
    return grid[row, col]


def relative_air_density(elevation_m) -> np.ndarray:
    """Air density at the surface relative to the datum: exp(-height / scale height).

    Low ground has more air above it, so an arriving vehicle has more to brake
    against. Hellas Basin, 7 km below datum, has nearly twice the surface
    density of the datum, while Olympus Mons has about an eighth.
    """
    return np.exp(-np.asarray(elevation_m) / 1000 / SCALE_HEIGHT_KM)
