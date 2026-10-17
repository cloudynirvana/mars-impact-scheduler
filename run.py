"""When to launch for Mars, and where on Mars you land when you get there.

Two questions, answered from real JPL ephemerides and real MOLA terrain.

1. **When can you go?** Earth and Mars line up for a cheap transfer for a few
   weeks every 26 months. This searches every departure date and flight time
   over the next decade, solves Lambert's problem for each, and finds those
   windows and what they cost.

2. **Where do you land?** For the best trajectory in each window, the arrival
   direction is fixed by orbital mechanics, but Mars turns 14.6 degrees an
   hour underneath it. So the arrival time chooses the longitude. This solves
   for the arrival time and aim that put the payload on a chosen target.

The payload assumed here is a soil-conditioning package aimed at the
perchlorates in Martian soil, which are toxic to people and have to be dealt
with before anyone farms there. Delivering living organisms to Mars is barred
under the Outer Space Treaty and the COSPAR planetary protection rules, and
this project does not plan for it.

    python3 run.py

Takes a few minutes, mostly fetching ephemerides the first time.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import horizons
import lambert
import mars
import terrain

START, STOP = "2028-01-01", "2037-06-01"
DEPART_STEP_DAYS = 2
FLIGHT_DAYS = np.arange(120, 401, 5)
MAX_C3 = 25.0  # km^2/s^2 of departure energy; a heavy-lift rocket's reach
OUT = Path(__file__).parent / "results"

# Candidate delivery regions. Low, flat, equatorial ground is the easiest to
# reach and the likeliest to matter for a future crew.
TARGETS = {
    "Hellas Planitia": (-42.4, 70.5),
    "Utopia Planitia": (46.7, 117.5),
    "Isidis Planitia": (12.9, 87.0),
    "Chryse Planitia": (27.0, 320.0),
    "Amazonis Planitia": (24.8, 196.0),
    "Arcadia Planitia": (46.0, 175.0),
    "Meridiani Planum": (-1.9, 354.5),
    "Elysium Planitia": (4.5, 135.9),
}


def jd_to_date(jd: float) -> str:
    """Calendar date of a Julian day number."""
    return str(np.datetime64("1858-11-17") + np.timedelta64(int(round((jd - 2400000.5) * 86400)), "s"))[:10]


def search(jd_e, r_e, v_e, jd_m, r_m, v_m) -> pd.DataFrame:
    """Every workable Earth-to-Mars transfer in the search span."""
    rows = []
    for i in range(0, len(jd_e) - int(FLIGHT_DAYS.max()) - 1, DEPART_STEP_DAYS):
        for tof in FLIGHT_DAYS:
            j = i + int(tof)
            out = lambert.solve(r_e[i], r_m[j], tof * 86400)
            if out is None:
                continue
            v1, v2 = out
            c3 = float(np.sum((v1 - v_e[i]) ** 2))
            if c3 > MAX_C3:
                continue
            rows.append((jd_e[i], tof, jd_m[j], c3, *(v2 - v_m[j])))
    df = pd.DataFrame(rows, columns=["depart_jd", "flight_days", "arrive_jd", "c3",
                                     "vinf_x", "vinf_y", "vinf_z"])
    df["arrival_speed_kms"] = np.linalg.norm(df[["vinf_x", "vinf_y", "vinf_z"]], axis=1)
    return df


def windows(df: pd.DataFrame, gap_days: float = 180) -> pd.DataFrame:
    """Split the solutions into launch windows and take the cheapest of each."""
    df = df.sort_values("depart_jd")
    group = (df.depart_jd.diff().fillna(0) > gap_days).cumsum()
    best = df.loc[df.groupby(group).c3.idxmin()].copy()
    best["departs"] = [jd_to_date(j) for j in best.depart_jd]
    best["arrives"] = [jd_to_date(j) for j in best.arrive_jd]
    best["entry_speed_kms"] = [mars.entry_speed(v) for v in best.arrival_speed_kms]
    best["reach_deg"] = [mars.aim_to_angle(v, mars.grazing_aim_km(v)) for v in best.arrival_speed_kms]
    return best.reset_index(drop=True)


def _unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Unit vector from Mars's centre to a point on its surface, in the body frame."""
    la, lo = np.radians(lat_deg), np.radians(lon_deg)
    return np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


def aim_for_angle(v_inf_kms: float, want_deg: float) -> float:
    """How far off centre to aim to move the impact `want_deg` round the globe."""
    lo, hi = 0.0, mars.grazing_aim_km(v_inf_kms)
    for _ in range(60):
        mid = (lo + hi) / 2
        if mars.aim_to_angle(v_inf_kms, mid) < want_deg:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def aim_at(target_lat, target_lon, jd_nominal, v_inf, hours=13.0, step_min=1.0):
    """The arrival time that lines a target up best with the incoming trajectory.

    The approach direction is fixed by orbital mechanics, so a dead-centre hit
    lands on whichever point happens to be facing it. Mars turns a full circle
    in 24 h 37 m, so sweeping the arrival over one rotation sweeps that point
    round the planet. The best arrival is the one that brings the target
    closest to dead centre; any remainder is made up by aiming off centre,
    which the trajectory can do up to its grazing limit.
    """
    speed = float(np.linalg.norm(v_inf))
    facing = -np.asarray(v_inf, float) / speed
    target = _unit(target_lat, target_lon)
    reach = mars.aim_to_angle(speed, mars.grazing_aim_km(speed) * 0.999)
    best = None
    for dt in np.arange(-hours / 24, hours / 24, step_min / 1440):
        jd = jd_nominal + dt
        towards = mars.body_axes(jd).T @ target  # the target, seen in the sky frame
        off = float(np.degrees(np.arccos(np.clip(facing @ towards, -1, 1))))
        if best is None or off < best[0]:
            best = (off, jd)
    off, jd = best
    miss = max(0.0, off - reach)
    aim = aim_for_angle(speed, min(off, reach))
    return miss, jd, aim, off


def porkchop(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    s = ax.scatter((df.depart_jd - 2451545) / 365.25 + 2000, df.flight_days,
                   c=df.c3, s=4, cmap="viridis_r", vmin=8, vmax=MAX_C3)
    ax.set_xlabel("departure date")
    ax.set_ylabel("flight time (days)")
    ax.set_title("Every workable Earth-to-Mars transfer, 2028 to 2037\n"
                 "each dot is one departure date and flight time", fontsize=11)
    fig.colorbar(s, ax=ax, label="departure energy C3 (km$^2$/s$^2$), lower is cheaper")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def impact_map(grid, hits: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.imshow(grid / 1000, extent=[0, 360, -90, 90], cmap="gist_earth", aspect="auto")
    for name, (lat, lon) in TARGETS.items():
        ax.plot(lon, lat, "o", mfc="none", mec="#ff3b30", ms=7, mew=1.5)
        ax.annotate(name, (lon, lat), (6, 4), textcoords="offset points",
                    color="#ff3b30", fontsize=8)
    for h in hits.itertuples():
        ax.plot(h.impact_lon, h.impact_lat, "x", color="#ffd60a", ms=9, mew=2)
    ax.set_xlabel("east longitude")
    ax.set_ylabel("latitude")
    ax.set_title("Mars (MOLA elevation) with the candidate delivery regions and\n"
                 "where each launch window's payload would actually land", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 220)
    print("fetching Earth and Mars from JPL Horizons...", flush=True)
    jd_e, r_e, v_e = horizons.states("earth", START, STOP)
    jd_m, r_m, v_m = horizons.states("mars", START, STOP)

    print("solving Lambert for every departure and flight time...", flush=True)
    df = search(jd_e, r_e, v_e, jd_m, r_m, v_m)
    best = windows(df)
    print(f"\n{len(df):,} workable transfers under C3 {MAX_C3:.0f}, in {len(best)} launch windows\n")
    print(best[["departs", "flight_days", "arrives", "c3", "arrival_speed_kms",
                "entry_speed_kms", "reach_deg"]].round(2).to_string(index=False))

    grid = terrain.load()
    print("\nwhere each window's payload can be put down:", flush=True)
    hits = []
    for w in best.itertuples():
        v_inf = np.array([w.vinf_x, w.vinf_y, w.vinf_z])
        # Pick the target this trajectory reaches most cheaply: the one it can
        # put closest to dead centre, which is the most accurate delivery.
        options = [(aim_at(lat, lon, w.arrive_jd, v_inf), name)
                   for name, (lat, lon) in TARGETS.items()]
        (miss, jd, aim, off), name = min(options, key=lambda o: (o[0][0], o[0][3]))
        lat, lon = TARGETS[name]
        elev = float(terrain.at(grid, lat, lon))
        hits.append({"departs": w.departs, "arrives": jd_to_date(jd),
                     "target": name, "miss_deg": round(miss, 2),
                     "impact_lon": lon, "impact_lat": lat,
                     "swing_needed_deg": round(off, 1), "aim_offset_km": round(aim),
                     "elevation_m": round(elev),
                     "air_vs_datum": round(float(terrain.relative_air_density(elev)), 2),
                     "entry_speed_kms": round(w.entry_speed_kms, 2),
                     "arrival_shift_hours": round((jd - w.arrive_jd) * 24, 2)})
    hits = pd.DataFrame(hits)
    hits.to_csv(OUT / "deliveries.csv", index=False)
    best.drop(columns=["vinf_x", "vinf_y", "vinf_z"]).to_csv(OUT / "launch_windows.csv", index=False)
    print(hits.to_string(index=False))

    porkchop(df, OUT / "launch_windows.png")
    impact_map(grid, hits, OUT / "impact_sites.png")
    print(f"\nwritten to {OUT}")
