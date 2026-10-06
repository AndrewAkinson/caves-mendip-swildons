---
name: therion-drawing
description: Conventions for drawing or editing Therion scraps (.th2) in this survey, and the checks to run afterwards. Use when converting sketches, editing walls, water, labels, cross-sections or other symbols, or reviewing a drawing.
---

# Drawing Therion scraps in this survey

These come from a Therion expert's review of the converted drawings
(Andrew Atkinson). `tools/sketch2therion` (convert, `tidy`, `roofs`,
`details`, `sections`) follows them; keep to them when editing by hand
too.

- The sheets print the licence from `map-comment` in `gb_layout.thc`.

## Walls and the outline

- Walls are `-outline out` by default; it doesn't need setting.
- Walls are the scrap's outline. Draw each `line wall` with the passage
  on its LEFT, or use `-reverse on` if the passage is on its right
  (Footleg's drawings do; `-reverse on` flips a line).
- Walls enclosing an internal pillar have `-outline in`.
- Do not close the gaps between walls: no invisible walls, and no
  closed invisible fill line with the walls set `-outline none`.
  Therion closes the outline itself, joining each wall's end to the
  nearest free end of another with a straight line
  (`thscrap::get_outline`). Converted sketches can be so broken up that
  this joining goes wrong (it jumps across the passage, or closes the
  outline early); only there does `tidy` keep a gap filled, with the
  wall carried on across a short one or a presumed wall across a longer
  one. `therion_chain` in `tools/sketch2therion/tidy.py` checks it.
- The outline must not cross itself, and no wall may loop back on
  itself. Otherwise Therion warns "invalid scrap outline" (no 3D model
  for the scrap) or MetaPost "scrap outline intersects itself".
- A line inside the passage is not a wall. In the streamway it's mostly
  the edge of a step down (a shelf, the stream in the low part): `line
  floor-step`, with the low side on the line's LEFT (Therion draws the
  ticks there). The low side is where the water is (flow arrows,
  pools), not necessarily where the survey line runs. One line per
  step, and steps don't run through the water. Otherwise `line border`
  (a ledge, the edge of another level).

## Symbols: general

- The default clipping normally gives the best result. Most symbols
  are clipped by the outer walls: use that for the best effect.
- `-clip off` only in exceptional circumstances.
- Labels and cross-sections must not overlap passages, including those
  of other surveys on the same sheet.

## Symbols: points

- Slope arrows (`point gradient`): inside the walls, not crossing steps
  or pitch edges, not in water.
- Water flow inside the walls.
- Climbs and pitches are labelled `C2`, `P5`: no units, placed outside
  the passage.
- Draught arrows (`point air-draught -orientation N`) go beside the
  passage, not across it, with a `point x y date -value YYYY.MM.DD`
  for when the draught was seen.

## Symbols: lines

- Rocks and boulders (`line rock-border`) are closed (`-close on`).
- They are drawn in file order and clip each other.
- Large boulders get `line rock-edge` lines inside them to look like 3D
  rocks.
- Boulders at the edge of a passage are best drawn going over the wall
  (the outline clips them).

## Symbols: areas

- Water: `line border -subtype invisible -id X -close on` and an `area
  water` naming X, with no other border.
- Water against an outer wall: draw its border outside the wall, so the
  wall is its edge.
- Areas can overlap to show a transition, or pebbles in water.
- Individually drawn rocks can be above or below the water; that needs
  careful ordering and use of clipping.

## Cross-sections

- A `line section` goes right across the passage.
- Its direction arrows don't overlap the passage they mark, and best not
  other passages either.
- `-direction both` by preference; arrows only at the start or end
  (`begin`, `end`) if that's the only option.
- Therion draws the arrows on the line's left, so draw it with the view
  direction (along the survey, from the station towards the next) on
  its left.
- A section drawing must not overlap a passage or another section,
  including those of other surveys on the same sheet and the displaced
  upper level of the Entrance Series.
- `python3 -m tools.sketch2therion sections` does all of this, and
  moves section labels off passages (see `tools/README.md`).

## Fill where nothing was drawn

Use the splay shots, not a guess: in elevation the steep splays give
the roof and floor at each station, in plan the splay ends give the
walls (`python3 -m tools.sketch2therion roofs`, see `tools/README.md`).

## Checking

Build with the `swildons*.thconfig` files (see `README.md`), then:

- `grep -E "^therion: error|invalid scrap outline" output/*.log`:
  there should be none.
- `grep "intersects itself" output/*.log | sort -u`: only scraps you
  didn't touch.
- Render and look. poppler (pdftoppm, Evince, Okular) can show white
  holes in Therion's smooth altitude shading that aren't in the PDF;
  check with another renderer (MuPDF) before chasing them.
- In PDFs, overlapping rocks fade rather than clip: a known bug, don't
  try to fix it.
