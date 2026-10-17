"""Checks on the orbital mechanics and on Mars's rotation.

The Lambert tests are self-contained. The rotation test calls JPL Horizons, so
it is skipped when there is no network.
"""
import numpy as np
import pytest

import lambert
import mars
from horizons import MU_SUN

AU = 1.495978707e8  # km
TDB_MINUS_UT = 69.184 / 86400  # days, as of 2028
LIGHT_KM_S = 299792.458


def circular(radius_km: float, angle_deg: float) -> tuple[np.ndarray, np.ndarray]:
    a = np.radians(angle_deg)
    r = radius_km * np.array([np.cos(a), np.sin(a), 0.0])
    v = np.sqrt(MU_SUN / radius_km) * np.array([-np.sin(a), np.cos(a), 0.0])
    return r, v


def test_half_an_orbit_comes_back_to_the_same_circle():
    """Launch across a circular orbit and the speed at both ends must match."""
    r1, _ = circular(AU, 0)
    r2, _ = circular(AU, 180)
    period = 2 * np.pi * np.sqrt(AU ** 3 / MU_SUN)
    v1, v2 = lambert.solve(r1, r2, period / 2)
    assert np.linalg.norm(v1) == pytest.approx(np.linalg.norm(v2), rel=1e-6)
    assert np.linalg.norm(v1) == pytest.approx(np.sqrt(MU_SUN / AU), rel=1e-6)


def test_a_hohmann_transfer_costs_what_the_textbook_says():
    """Earth to Mars the cheap way: 2.94 km/s of departure energy, 259 days."""
    r_earth, r_mars = 1.0 * AU, 1.524 * AU
    a = (r_earth + r_mars) / 2
    tof = np.pi * np.sqrt(a ** 3 / MU_SUN)
    r1, v_planet = circular(r_earth, 0)
    r2, _ = circular(r_mars, 180)
    v1, _ = lambert.solve(r1, r2, tof)
    assert tof / 86400 == pytest.approx(258.9, abs=1.0)
    assert np.linalg.norm(v1 - v_planet) == pytest.approx(2.94, abs=0.02)


def test_impossible_flight_times_give_no_answer():
    r1, _ = circular(AU, 0)
    r2, _ = circular(AU, 90)
    assert lambert.solve(r1, r2, 60.0) is None  # a minute to cross 150 million km


def test_mars_turns_once_every_sidereal_day():
    """Mars turns once on its axis in 24 h 37 m 23 s, a little short of a sol."""
    day = 360 / mars.PRIME_MERIDIAN[1]
    assert day * 24 == pytest.approx(24 + 37 / 60 + 22.7 / 3600, abs=0.002)
    _, _, w0 = mars.orientation(mars.J2000)
    _, _, w1 = mars.orientation(mars.J2000 + day)
    assert (w1 - w0 + 180) % 360 - 180 == pytest.approx(0, abs=1e-6)


def test_six_hours_of_rotation_moves_the_impact_a_quarter_way_round():
    """Arrive six hours later on the same approach and you hit a different continent.

    The longitude goes backwards: Mars turns east under a fixed arrival
    direction, so the ground that meets it has a smaller east longitude.
    """
    approach = np.array([1.0, 0.2, -0.3])
    lon0, lat0 = mars.impact_point(mars.J2000, approach)
    lon6, lat6 = mars.impact_point(mars.J2000 + 0.25, approach)
    assert lat6 == pytest.approx(lat0, abs=0.01)  # latitude is set by the approach
    assert (lon6 - lon0) % 360 == pytest.approx(-0.25 * mars.PRIME_MERIDIAN[1] % 360, abs=0.01)


def test_gravity_pulls_in_trajectories_that_would_otherwise_miss():
    """Mars catches anything aimed inside this radius; slower arrivals are caught wider."""
    slow, fast = mars.grazing_aim_km(2.0), mars.grazing_aim_km(6.0)
    assert slow > fast > mars.RADIUS
    assert mars.entry_speed(3.0) == pytest.approx(5.85, abs=0.05)  # km/s at the top of the air


def test_aiming_off_centre_walks_the_impact_round_the_globe():
    """Dead centre hits the point facing you; a wider aim reaches further round.

    With no gravity the widest aim would graze the horizon, 90 degrees away.
    A real arrival curves in, so a slow one wraps past 90 and can hit ground
    that was facing away when it arrived.
    """
    v = 3.0
    assert mars.aim_to_angle(v, 0) == 0
    assert mars.aim_to_angle(v, mars.grazing_aim_km(v)) > 120  # curved well round
    assert mars.aim_to_angle(50.0, mars.grazing_aim_km(50.0)) == pytest.approx(90, abs=1.0)
    steps = [mars.aim_to_angle(v, b) for b in np.linspace(0, mars.grazing_aim_km(v), 10)]
    assert np.all(np.diff(steps) > 0)  # aiming wider always reaches further round


def test_the_impact_moves_the_way_you_aim_it():
    v_inf = np.array([-4.0, 1.0, 0.5])
    straight = mars.impact_point(mars.J2000, v_inf)
    for azimuth in (0, 90, 180, 270):
        off = mars.impact_point(mars.J2000, v_inf, aim_km=4000, aim_azimuth_deg=azimuth)
        assert off != straight


@pytest.mark.network
def test_our_mars_rotation_matches_jpl():
    """The real check: which way is Mars facing, against JPL's own answer.

    Horizons reports the sub-Earth point in WEST longitude for Mars, and as a
    planetodetic latitude, so the latitude differs from our planetocentric one
    by the planet's flattening. Longitude should agree to a rounding error.
    """
    import horizons
    jd, r_mars, _ = horizons.states("mars", "2028-01-01", "2028-02-01")
    _, r_earth, _ = horizons.states("earth", "2028-01-01", "2028-02-01")
    _, lon_west, lat_jpl = horizons.sub_earth_point("2028-01-01", "2028-02-01")
    for i in range(0, len(jd), 7):
        towards_earth = r_earth[i] - r_mars[i]
        light_days = np.linalg.norm(towards_earth) / LIGHT_KM_S / 86400
        lon, lat = mars.surface_point(jd[i] - light_days + TDB_MINUS_UT, towards_earth)
        assert ((-lon) % 360 - lon_west[i] + 180) % 360 - 180 == pytest.approx(0, abs=0.05)
        assert lat == pytest.approx(lat_jpl[i], abs=0.25)
