# Mars impact scheduler

Work out when to launch for Mars, and where on Mars the payload comes down.

Earth and Mars only line up for a cheap trip for a few weeks every 26 months.
Once you pick a trajectory, the direction you arrive from is settled by orbital
mechanics — but Mars keeps turning at 14.6 degrees an hour underneath it. So
the arrival time is the steering wheel: shift it by a few hours and the same
trajectory lands you on a different continent.

This project computes both halves from real data: launch windows from JPL's
ephemerides, landing points from the IAU rotation model, and the terrain under
them from MOLA.

See [RESULTS.md](RESULTS.md) for what it found.

## Running it

```bash
pip install numpy scipy matplotlib pandas
curl -O https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg004/megt90n000cb.img
mv megt90n000cb.img data/
python3 run.py     # a few minutes; ephemerides are cached after the first run
pytest             # 9 checks, one of which calls JPL
```

## What's in it

| | |
|---|---|
| `horizons.py` | Earth and Mars state vectors from NASA/JPL Horizons |
| `lambert.py` | Lambert's problem: two points and a flight time give you the orbit |
| `mars.py` | Mars's rotation and where an arriving trajectory meets the ground |
| `terrain.py` | MOLA elevation, and the air density that follows from it |
| `run.py` | searches the windows, picks the deliveries, draws the charts |

## Is it right?

The parts that can be checked against someone else's answer, are:

- **Mars's orientation** is compared against JPL Horizons' own sub-Earth
  longitudes over a month. It agrees to **0.007 degrees**, about 400 m on the
  ground. That is `test_our_mars_rotation_matches_jpl`.
- **The Lambert solver** reproduces the textbook Earth-to-Mars Hohmann
  transfer: 2.94 km/s of departure energy over 259 days.
- **The launch windows it finds** — late 2028, early 2031, spring 2033, mid
  2035 — are the real Mars windows, and it finds them from the ephemerides
  alone, with nothing about the 26-month cycle written into the code.
- **The elevation lookup** puts Olympus Mons at 20.0 km and Hellas at −6.2 km.

## About the payload

The delivery modelled here is a soil-conditioning package, aimed at the
perchlorates in Martian soil, which are toxic to people and would have to be
dealt with before anyone could farm there.

It is deliberately not a biological payload. Delivering living organisms to
Mars on purpose is prohibited under Article IX of the Outer Space Treaty and
the COSPAR planetary protection policy, which exist so that the search for life
native to Mars is not contaminated by life brought from here. The trajectory
mathematics is identical either way; the rules are about what you put on top
of it.

## Data

- **JPL Horizons** — planetary ephemerides, <https://ssd.jpl.nasa.gov/horizons/>
- **MOLA MEGDR** — Mars Orbiter Laser Altimeter topography, 4 pixels/degree,
  from the [Planetary Data System](https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg004/)

## What I would do differently

The missing piece is entry, descent and landing. This project stops at the top
of the atmosphere, and that is where the hard part of actually hitting a target
begins: the interplanetary leg can be aimed to within a few kilometres, but
what the atmosphere does over the last 100 km is what sets the real landing
ellipse. Adding even a simple drag model would turn "where does it arrive" into
"where does it land", which is the question that matters.
