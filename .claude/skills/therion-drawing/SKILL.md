---
name: therion-drawing
description: Conventions for drawing or editing Therion scraps (.th2) in this survey, and the checks to run afterwards. Use when converting sketches, editing walls, water, labels, cross-sections or other symbols, or reviewing a drawing.
---

# Drawing Therion scraps in this survey

These come from a Therion expert's review of the converted drawings.
`tools/sketch2therion` (convert, `tidy`, `roofs`, `details`, `sections`) follows
them; keep to them when editing by hand too.

## Walls and the outline

- Walls are the scrap's outline. Draw each `line wall` with the passage
  on its LEFT (Footleg's drawings do; `-reverse on` flips a line).
- Don't close the outline with invisible walls, and don't fill from a
  separate closed invisible line with the walls set `-outline none`
  (that hides walls drawn the wrong way, and the fill doesn't follow
  the walls). Therion closes the outline itself: it joins each outline
  line's end to the nearest free end of another with a straight line
  (`thscrap::get_outline`). So:
  - a gap where the wall runs along the passage but wasn't drawn is a
    `line wall -subtype presumed` (dashed);
  - a gap across the passage (an open end, a junction, where the
    drawing stops) is left open;
  - where walls meet, end one exactly where the next starts.
  Check that nearest-end joining gives one outline that doesn't cross
  itself (`therion_chain` in `tools/sketch2therion/tidy.py`).
- No wall may loop back on itself or the outline cross itself.
  Otherwise Therion warns "invalid scrap outline" (no 3D model for the
  scrap) or MetaPost "scrap outline intersects itself".
- A line inside the passage is not a wall. In the streamway it's mostly
  the edge of a step down (a shelf, the stream in the low part): `line
  floor-step`, with the lower side on the line's LEFT (Therion draws the
  ticks there). Otherwise `line border` (a ledge, the edge of another
  level).

## Symbols

- Never use `-clip off`. Boulders (`line rock-border -close on`) are
  clean polygons; large ones get a few `line rock-edge` facet lines from
  a ridge point towards their corners, not one line straight across.
- Water: one `line border -subtype invisible -id X -close on` and an
  `area water` naming X. Where the water lies against a wall the border
  runs a little way out under the wall, so the wall is the water's only
  edge (Therion clips areas to the outline). Never a second line just
  inside the wall.
- Fill, water, formations and slope arrows stay inside the walls.
- Slope arrows (`point gradient`) never cross a floor step or pitch.
- Climbs and pitches are labelled `C2`, `P5`: no units, placed
  outside the passage. Any label inside the passage breaks the walls
  under it.
- Draught arrows (`point air-draught -orientation N`) go beside the
  passage, not across it, with a `point x y date -value YYYY.MM.DD`
  for when the draught was seen.
- The sheets print the licence from `map-comment` in `gb_layout.thc`.

## Cross-sections

- Each `line section` has `-direction both`. Therion draws the arrows
  on the line's left, so draw it with the view direction (along the
  survey, from the station towards the next) on its left.
- A section drawing must not overlap a passage or another section,
  including those of other surveys on the same sheet and the displaced
  upper level of the Entrance Series.
  `python3 -m tools.sketch2therion sections` fixes both (see
  `tools/README.md`).

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
