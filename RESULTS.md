# When to launch for Mars, and where you land when you get there

Run on 16 October 2026 against live JPL Horizons ephemerides and the MOLA
elevation map. Rebuild with `python3 run.py`.

## The launch windows

Searching every departure date from 2028 to 2037 and every flight time from
120 to 400 days gives **6,770 workable transfers**, and they fall into exactly
**four windows**, about 26 months apart. That spacing is not a choice anyone
makes; it is how long Earth takes to lap Mars.

| Depart | Flight | Arrive | Departure energy C3 | Arrival speed | Entry speed |
|---|---|---|---|---|---|
| 2028-11-30 | 315 d | 2029-10-11 | 9.0 km²/s² | 3.17 km/s | 5.94 km/s |
| 2031-02-22 | 320 d | 2032-01-08 | 8.2 km²/s² | 5.51 km/s | 7.45 km/s |
| 2033-04-28 | 275 d | 2034-01-28 | 7.7 km²/s² | 4.38 km/s | 6.66 km/s |
| 2035-05-30 | 220 d | 2036-01-05 | 13.8 km²/s² | 2.92 km/s | 5.81 km/s |

*Chart: `results/launch_windows.png`* — the four columns are the windows. Miss
one and you wait two years.

**2033 is the cheapest to leave on** (C3 7.7) and gets there in 275 days.
**2035 is the gentlest to arrive on**: it costs nearly twice as much energy to
leave, but the payload hits the atmosphere at 5.81 km/s instead of 7.45, which
is a far easier entry to survive. That trade — cheap to leave versus cheap to
arrive — is the real decision, and it is not the same answer in every window.

## Where on Mars you can put it

Here is the part that makes the scheduling interesting. Once the trajectory is
fixed, the direction the payload comes in from is fixed too, and a dead-centre
arrival lands on whichever part of Mars happens to be facing that direction.
But **Mars turns 14.6 degrees an hour**. Shift the arrival by a few hours and
the same trajectory lands on a different continent.

So the longitude is free: pick the arrival time to the minute and you can have
any longitude you want. The latitude is the part you have to buy, by aiming off
centre and letting Mars's gravity bend the approach around.

Each window's cheapest delivery, out of eight candidate regions:

| Depart | Arrive | Target | Steering needed | Aim offset | Elevation | Air vs datum |
|---|---|---|---|---|---|---|
| 2028-11-30 | 2029-10-11 | Chryse Planitia | 4.8° | 412 km | −3,857 m | 1.42× |
| 2031-02-22 | 2032-01-08 | Chryse Planitia | 1.2° | 87 km | −3,857 m | 1.42× |
| 2033-04-28 | 2034-01-27 | Isidis Planitia | 3.5° | 259 km | −3,792 m | 1.41× |
| 2035-05-30 | 2036-01-04 | Elysium Planitia | 1.0° | 89 km | −2,650 m | 1.27× |

*Chart: `results/impact_sites.png`* — the eight candidate regions on the MOLA
map, with the landing point for each window marked.

**Every one of the eight regions is reachable in every window.** The arrival
geometry reaches 107 to 127 degrees from dead centre, which is more than a
hemisphere, so nothing on the sunward side is out of range. What changes is how
hard you have to steer:

| Region | Latitude | Steering needed, by window |
|---|---|---|
| Chryse Planitia | 27°N | 4.8° / 1.2° / 17.6° / 23.5° |
| Elysium Planitia | 4.5°N | 27.3° / 23.7° / 4.9° / 1.0° |
| Isidis Planitia | 12.9°N | 18.9° / 15.3° / 3.5° / 9.4° |
| Hellas Planitia | 42.4°S | 74.2° / 70.6° / 51.8° / 45.9° |

Hellas is the most expensive target in every single window, and the reason is
simple: it is far into the southern hemisphere, while every one of these
approaches comes in near Mars's equator. Latitude, not longitude, is what costs
you.

That is a slightly annoying result, because **Hellas is the best place to arrive
on other grounds.** It is the deepest basin on Mars, 6.2 km below datum, with
about 1.7 times the surface air density of the reference level and nearly 11
times that of the Tharsis summits. Anything arriving from interplanetary space
has to shed 6 km/s in that thin air, and Hellas offers the most air to do it
in. So the trajectory wants the equator and the entry physics wants Hellas, and
somebody has to decide which wins.

## How it works

1. **Ephemerides.** Earth and Mars positions and velocities straight from JPL
   Horizons, the same service used to navigate real spacecraft.
2. **Lambert's problem.** For each departure date and flight time, solve for the
   one Sun-centred orbit that connects Earth then to Mars later. The departure
   energy C3 is what the rocket must supply above escaping Earth.
3. **Arrival geometry.** The arrival velocity relative to Mars sets the approach
   direction. Aiming off centre swings the impact around the globe, up to the
   grazing limit; gravity bends the path in, so a slow arrival wraps further
   round than a fast one.
4. **Mars's rotation.** The IAU orientation model fixes which face is pointing
   where. Checked against JPL's own sub-Earth longitudes: **agrees to 0.007
   degrees**, about 400 m on the ground.
5. **Terrain.** MOLA elevation at the landing point, and the air density that
   follows from it.

## What this does not do

- **No atmospheric entry model.** Entry speed is computed; what the atmosphere
  then does to the vehicle is not. Real delivery accuracy is set by entry,
  descent and landing, not by the interplanetary leg.
- **No mid-course corrections.** The aim offset is treated as free. In reality
  it is a small burn weeks out, and a cheap one, but not nothing.
- **Patched conics.** The transfer is Sun-only and the arrival is Mars-only,
  stitched at the edge of Mars's gravitational reach. Good to a few hours of
  arrival time, which matters here because hours are degrees of longitude.
- **No launch-site or departure-declination constraint.** Some C3-cheap
  trajectories need a departure direction a given launch site cannot reach.
- **The payload is a soil-conditioning package**, not a biological one.
  Deliberately delivering living organisms to Mars is prohibited under Outer
  Space Treaty Article IX and the COSPAR planetary protection policy.
