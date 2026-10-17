"""Lambert's problem: given two points and a flight time, find the orbit.

This is the heart of interplanetary mission planning. You know where Earth is
on the day you launch and where Mars will be when you want to arrive; Lambert's
problem gives you the one Sun-centred conic that connects them in exactly that
many days. The departure velocity it asks for, minus Earth's own velocity,
is the energy the rocket has to supply.

The solver is the universal-variable formulation (Bate, Mueller and White),
iterated with bisection on the universal anomaly z. It is slower than Izzo's
method but short enough to read and check.
"""
from __future__ import annotations

import numpy as np

from horizons import MU_SUN


def _stumpff(z: float) -> tuple[float, float]:
    """The C and S functions that make one formula cover ellipse, parabola and hyperbola."""
    if z > 1e-6:
        s = np.sqrt(z)
        return (1 - np.cos(s)) / z, (s - np.sin(s)) / s ** 3
    if z < -1e-6:
        s = np.sqrt(-z)
        return (np.cosh(s) - 1) / -z, (np.sinh(s) - s) / s ** 3
    return 0.5 - z / 24, 1 / 6 - z / 120  # series near zero


def solve(r1: np.ndarray, r2: np.ndarray, tof_s: float, mu: float = MU_SUN,
          prograde: bool = True, tol: float = 1e-8, max_iter: int = 200) -> tuple[np.ndarray, np.ndarray] | None:
    """Velocities at r1 and r2 (km/s) for a transfer taking tof_s seconds.

    Returns None where no solution converges, which happens for flight times
    that are physically impossible between those two points.
    """
    n1, n2 = np.linalg.norm(r1), np.linalg.norm(r2)
    cross_z = np.cross(r1, r2)[2]
    dnu = np.arccos(np.clip(r1 @ r2 / (n1 * n2), -1, 1))
    if (cross_z >= 0) != prograde:
        dnu = 2 * np.pi - dnu
    A = np.sin(dnu) * np.sqrt(n1 * n2 / (1 - np.cos(dnu)))
    if abs(A) < 1e-9:
        return None  # the two points and the Sun are in a straight line

    def time_of_flight(z: float) -> float:
        C, S = _stumpff(z)
        y = n1 + n2 + A * (z * S - 1) / np.sqrt(C)
        if y < 0:
            return np.inf
        x = np.sqrt(y / C)
        return (x ** 3 * S + A * np.sqrt(y)) / np.sqrt(mu)

    # Bracket the answer: time of flight rises monotonically with z.
    lo, hi = -4 * np.pi ** 2 + 1e-6, 4 * np.pi ** 2 - 1e-6
    if time_of_flight(lo) > tof_s or time_of_flight(hi) < tof_s:
        return None
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if time_of_flight(mid) < tof_s:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    z = (lo + hi) / 2
    C, S = _stumpff(z)
    y = n1 + n2 + A * (z * S - 1) / np.sqrt(C)
    if y < 0 or not np.isfinite(y):
        return None
    f = 1 - y / n1
    g = A * np.sqrt(y / mu)
    gdot = 1 - y / n2
    return (r2 - f * r1) / g, (gdot * r2 - r1) / g
