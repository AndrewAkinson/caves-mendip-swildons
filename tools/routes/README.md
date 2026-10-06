# Route cards

An A3 sheet per route through the cave, made automatically from the
survey. Each has:

- **The route on the survey,** as a bold line with chevrons pointing the
  way. Where the route passes the same way twice it keeps to the right,
  so both directions show.
- **Numbered decisions:** every junction where there's a choice, found
  from the survey.
- **A close-up of each decision,** with an arrowhead on the way to go, a
  red cross on each way not to take (with where it leads), and the
  directions in words: "Turn left, down about 3 m, towards Boulder
  Chamber. Not the way on the right (to Zig Zags)."
- **Kit and tackle** from the route file, with the steep drops and
  climbs on the survey, so you can see what the tackle is for.
- **A height profile** along the route, with the decisions and the
  places passed.
- **The title and description, the numbers** (distance, depth, total
  up and down), and a locator showing where in the cave the route is.

The route definitions are in [`routes/`](../../routes) at the top of the
repository. To add a route, add a file there.

## A route

```toml
title = "The Dry Ways round trip"
subtitle = "Down the Long Dry Way to Old Grotto, back up the Short Dry Way"
description = """
A round trip of the dry upper series, ...
"""
# Stations to go through, in order. The route between them is the
# shortest way through the survey, so only add enough to pin it to the
# passages you mean.
waypoints = ["1.0@ZigZags", "2.33@LongDryWay", "2.59@LongDryWay",
             "4.0@ShortDryWay", "2.5@LongDryWay", "1.0@ZigZags"]

# Kit and tackle, shown in a box on the card. The card also lists the
# steep drops and climbs it finds on the survey (2 m or more), and says
# "not listed yet" for tackle when there are drops but no tackle list.
tackle = ["..."]
kit = ["..."]

# Optional:
avoid = ["11.13@WetWayOxbows"]   # stations the route must not use
visit = ["13.13@WaterChamber"]   # dead ends to go into and back out of
min_branch = 8                    # side passages shorter than this (m) aren't decisions (default 4)
way_out = true                    # also make a card for the route backwards
way_out_title = "The way out from Sump 1"
way_out_subtitle = "..."
way_out_description = """..."""

# Settings for single decisions, by the station they're at (shown on each
# close-up as "stn 2.33"). These tables go at the END of the file: in
# TOML everything after a [[decision]] line belongs to it.

[[decision]]
at = "1.21@ZigZags"
skip = true                       # obvious: leave it off the card

[[decision]]
at = "2.33@LongDryWay"
width = 40                        # metres across the close-up (default about 23)
title = "Boulder Chamber"         # instead of the nearest passage name
directions = "Go left over the boulders."   # instead of the worked-out words
text = "Low and wet in flood."    # an extra note under the directions
photo = "photos/boulder-chamber.jpg"        # relative to this file
caption = "Looking into Boulder Chamber from the Long Dry Way"

# At a station with no junction, a [[decision]] with text or a photo
# adds a point of interest to the card.
[[decision]]
at = "2.45@LongDryWay"
title = "The Pretty Way"
photo = "photos/pretty-way.jpg"

# [[way_out_decision]] does the same for the reversed card.
```

Station names are `station@survey`, as in the centreline sheet
(`Swildons-plan-centreline.pdf`). A bare station name works when only
one survey has it.

The directions are worked out from the plan geometry and the heights:

- **The turn** comes from the bearing of the passage arriving and
  leaving: straight on, bear, turn, or sharply back.
- **Up or down** comes from the height change over the next 6 m.
- **The ways not to take** are side passages that go on for at least
  4 m without rejoining the route. Each is named from the nearest
  passage name on the drawing, where there is one.

They describe the survey's geometry, which isn't always how the
passage feels, so treat them as a draft. Rewrite them with `[[note]]`
where they're wrong.

## Photos

Put them in `routes/photos/` and point a `[[decision]]` at them. They
are built into the card itself, so each card is one file that works
offline on a phone. Keep them small: about 1600 pixels across, a few
hundred kB (the build warns over 1.5 MB). A photo taken looking the way
to go helps most.

## Phone and print

Each card is one HTML file and a PDF.

- **Printed**, it is an A3 sheet. A4 also works, at a smaller scale.
- **On a phone**, the same HTML file stacks into one column with
  full-width maps. Tapping a number on the map jumps to its close-up.
  Copy the `.html` file to the phone before the trip. It needs no
  signal, apart from the web fonts, which fall back to the phone's own.

## Building them

After the main build (which writes `output/Swildons.sql`):

```bash
therion -l output/therion-routes.log tools/routes/routes.thconfig   # the background, output/routes-base.svg
python3 -m tools.routes                    # every route in routes/
python3 -m tools.routes routes/1-dry-ways.toml   # just one
```

This writes `output/routes/<name>.html` and, with Chromium or Chrome
installed (set `CHROMIUM` if it isn't found), `<name>.pdf`, plus an
index. CI builds them and the website links them. It needs only
Python 3.11+, no packages.

## How it works

| Module | What it does |
|---|---|
| `survey.py` | Builds the cave as a graph from Therion's database export, with equated stations merged and Stanton's replaced legs made dearer. Reads the passage names off the plan drawings. |
| `analyse.py` | Routes through the waypoints, finds the decisions, writes the directions, and makes the profile. |
| `basemap.py` | Lines the route up with Therion's drawing. The background render has three dots in an unusual colour, exactly on three stations (`reg.th2`). Finding them in the SVG gives the transform from survey coordinates, and the dots are then removed. |
| `render.py`, `__main__.py` | Lay out the sheet. Every map panel is a window onto the same embedded drawing. |
