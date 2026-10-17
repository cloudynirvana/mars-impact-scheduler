"""Where Earth and Mars actually are, from NASA/JPL's Horizons service.

Horizons is the same ephemeris JPL uses to navigate real spacecraft. We ask it
for heliocentric state vectors (position and velocity about the Sun's centre)
and cache the answer, because the planets will not have moved since last time.
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

API = "https://ssd.jpl.nasa.gov/api/horizons.api"
BODY = {"earth": "399", "mars": "499"}
MU_SUN = 1.32712440018e11  # km^3/s^2
CACHE = Path(__file__).parent / "data"

_ROW = re.compile(
    r"^(\d+\.\d+) = .*?\n\s*X =\s*(\S+)\s*Y =\s*(\S+)\s*Z =\s*(\S+)\s*\n"
    r"\s*VX=\s*(\S+)\s*VY=\s*(\S+)\s*VZ=\s*(\S+)", re.M)


def _fetch(params: dict) -> str:
    url = API + "?" + urllib.parse.urlencode({k: f"'{v}'" if k != "format" else v
                                              for k, v in params.items()})
    with urllib.request.urlopen(url, timeout=180) as r:
        text = r.read().decode()
    if "$$SOE" not in text:
        raise RuntimeError(f"Horizons returned no ephemeris:\n{text[:600]}")
    return text


def states(body: str, start: str, stop: str, step: str = "1d") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Julian dates, positions (km) and velocities (km/s) about the Sun.

    Coordinates are the ecliptic of J2000, which is the natural frame for
    comparing two planets' orbits.
    """
    CACHE.mkdir(exist_ok=True)
    cache = CACHE / f"{body}_{start}_{stop}_{step}.npz".replace(" ", "")
    if cache.exists():
        d = np.load(cache)
        return d["jd"], d["r"], d["v"]
    text = _fetch({"format": "text", "COMMAND": BODY[body], "OBJ_DATA": "NO",
                   "MAKE_EPHEM": "YES", "EPHEM_TYPE": "VECTORS", "CENTER": "500@10",
                   "REF_PLANE": "ECLIPTIC", "START_TIME": start, "STOP_TIME": stop,
                   "STEP_SIZE": step, "VEC_TABLE": "2", "OUT_UNITS": "KM-S"})
    rows = _ROW.findall(text[text.index("$$SOE"):text.index("$$EOE")])
    if not rows:
        raise RuntimeError("could not parse the Horizons vector table")
    a = np.array([[float(x.replace("E", "e")) for x in row] for row in rows])
    jd, r, v = a[:, 0], a[:, 1:4], a[:, 4:7]
    np.savez_compressed(cache, jd=jd, r=r, v=v)
    return jd, r, v


def sub_earth_point(start: str, stop: str, step: str = "1d") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Which bit of Mars faces Earth: Julian date, east longitude, latitude.

    Only used to check our own Mars rotation model against JPL's.
    """
    text = _fetch({"format": "text", "COMMAND": BODY["mars"], "OBJ_DATA": "NO",
                   "MAKE_EPHEM": "YES", "EPHEM_TYPE": "OBSERVER", "CENTER": "500@399",
                   "START_TIME": start, "STOP_TIME": stop, "STEP_SIZE": step,
                   "QUANTITIES": "14", "CSV_FORMAT": "YES", "CAL_FORMAT": "JD"})
    jd, lon, lat = [], [], []
    for line in text[text.index("$$SOE"):text.index("$$EOE")].splitlines()[1:]:
        # columns: date, (blank), (blank), sub-observer east longitude, latitude
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5 or not parts[0]:
            continue
        jd.append(float(parts[0].split()[0]))
        lon.append(float(parts[3]))
        lat.append(float(parts[4]))
    return np.array(jd), np.array(lon), np.array(lat)
