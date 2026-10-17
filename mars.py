"""Mars as a spinning body: where on its surface an arriving trajectory hits.

Three things decide the impact point.

1. Which direction the spacecraft comes in from, set by the transfer orbit.
   Aim dead centre and you hit the point facing that direction.
2. How far off centre you aim. Mars's gravity bends the approach inwards, so
   aiming to one side walks the impact point around the globe, up to the
   grazing limit beyond which you miss the planet entirely.
3. Which way Mars is facing at that moment. Mars turns once on its axis in
   24 h 37 m 23 s, about 14.6 degrees an hour: arrive six hours late on the
   same approach and you land a quarter of the way round the planet. (A sol,
   noon to noon, is slightly longer at 24 h 39 m 35 s, because Mars has moved
   along its orbit meanwhile. What matters here is the spin.)

So the arrival time picks the longitude and the aim picks the rest.

The orientation model is the IAU/WGCCRE standard for Mars (Archinal et al.,
"Report of the IAU Working Group on Cartographic Coordinates and Rotational
Elements"). `tests/test_mars.py` checks it against JPL's own sub-Earth
longitudes: it agrees to 0.007 degrees, about 400 m on the ground.
"""
from __future__ import annotations

import numpy as np

RADIUS = 3396.19  # km, equatorial
MU = 4.282837e4  # km^3/s^2
J2000 = 2451545.0

# IAU/WGCCRE orientation of Mars. T is centuries and d is days from J2000 (TDB).
POLE_RA = (317.68143, -0.1061)  # degrees, and degrees per century
POLE_DEC = (52.88650, -0.0609)
PRIME_MERIDIAN = (176.630, 350.89198226)  # degrees, and degrees per day


def orientation(jd: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pole right ascension, pole declination and prime meridian angle, in degrees."""
    d = np.asarray(jd, float) - J2000
    t = d / 36525
    return (POLE_RA[0] + POLE_RA[1] * t,
            POLE_DEC[0] + POLE_DEC[1] * t,
            (PRIME_MERIDIAN[0] + PRIME_MERIDIAN[1] * d) % 360)


def _equatorial_to_ecliptic() -> np.ndarray:
    """Earth's equator of J2000 tilted into the ecliptic frame the ephemeris uses."""
    e = np.radians(23.43928)
    return np.array([[1, 0, 0], [0, np.cos(e), np.sin(e)], [0, -np.sin(e), np.cos(e)]])


def body_axes(jd: float) -> np.ndarray:
    """Mars's x, y, z body axes as rows, expressed in the ecliptic J2000 frame.

    z is the north pole; x pierces the surface at zero longitude at this instant.
    """
    ra, dec, w = (np.radians(v) for v in orientation(jd))
    z_eq = np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    node = np.array([-np.sin(ra), np.cos(ra), 0.0])  # ascending node on Earth's equator
    x_eq = node * np.cos(w) + np.cross(z_eq, node) * np.sin(w)
    m = _equatorial_to_ecliptic()
    return np.array([m @ x_eq, m @ np.cross(z_eq, x_eq), m @ z_eq])


def surface_point(jd: float, direction: np.ndarray) -> tuple[float, float]:
    """East longitude and latitude of the point where Mars's surface faces `direction`.

    `direction` points from Mars's centre outwards, in the ecliptic frame.
    Latitude is planetocentric, the convention MOLA maps use.
    """
    x, y, z = body_axes(jd) @ (np.asarray(direction, float) / np.linalg.norm(direction))
    return float(np.degrees(np.arctan2(y, x)) % 360), float(np.degrees(np.arcsin(np.clip(z, -1, 1))))


def grazing_aim_km(v_infinity_kms: float) -> float:
    """The widest you can aim and still hit Mars, in km off centre.

    Gravity focuses the approach, so this is wider than the planet's radius,
    and much wider for a slow arrival than a fast one.
    """
    return RADIUS * np.sqrt(1 + 2 * MU / (RADIUS * v_infinity_kms ** 2))


def aim_to_angle(v_infinity_kms: float, aim_km: float) -> float:
    """How far round the globe an off-centre aim moves the impact, in degrees.

    Aiming dead centre hits the point facing the incoming direction. Aiming at
    the grazing limit puts the impact on that point's horizon, a quarter of the
    way round the planet.
    """
    if aim_km <= 0:
        return 0.0
    e = np.sqrt(1 + (aim_km * v_infinity_kms ** 2 / MU) ** 2)
    p = (aim_km * v_infinity_kms) ** 2 / MU  # semi-latus rectum
    return float(np.degrees(np.arccos(-1 / e) - np.arccos(np.clip((p / RADIUS - 1) / e, -1, 1))))


def impact_point(jd_arrive: float, v_infinity: np.ndarray, aim_km: float = 0.0,
                 aim_azimuth_deg: float = 0.0) -> tuple[float, float]:
    """East longitude and latitude of the impact.

    `v_infinity` is the arrival velocity relative to Mars, in the ecliptic
    frame. `aim_km` steers off centre and `aim_azimuth_deg` chooses which way
    round, together moving the impact `aim_to_angle` degrees from the point
    facing the incoming direction.
    """
    v = np.asarray(v_infinity, float)
    speed = np.linalg.norm(v)
    facing = -v / speed  # where a dead-centre hit lands
    ref = np.array([0.0, 0.0, 1.0])
    if abs(facing @ ref) > 0.95:
        ref = np.array([1.0, 0.0, 0.0])
    side = np.cross(facing, ref)
    side /= np.linalg.norm(side)
    other = np.cross(facing, side)
    a = np.radians(aim_azimuth_deg)
    swing = np.radians(aim_to_angle(speed, aim_km))
    direction = facing * np.cos(swing) + (side * np.cos(a) + other * np.sin(a)) * np.sin(swing)
    return surface_point(jd_arrive, direction)


def entry_speed(v_infinity_kms: float) -> float:
    """Speed at the top of the atmosphere, km/s: approach speed plus the fall in."""
    return float(np.sqrt(v_infinity_kms ** 2 + 2 * MU / RADIUS))
