---
name: therion-drawing
description: Conventions for drawing or editing Therion scraps (.th2) in this survey, and the checks to run afterwards. Use when converting sketches, editing walls, water, labels, cross-sections or other symbols, or reviewing a drawing.
---

# Drawing Therion scraps in this survey

These come from a Therion expert's review of the converted drawings.
`tools/sketch2therion` (convert, `tidy`, `sections`) already follows
them; keep to them when editing by hand too.

## Walls and the outline

- Walls are the scrap's outline. Draw each `line wall` with the passage
  on its LEFT (Footleg's drawings do; `-reverse on` flips a line).
- Close the gaps between walls with `line wall -subtype invisible`,
  starting and ending exactly on the wall ends, so the fill follows the
  walls. Don't fill from a separate closed invisible line with the
  walls set `-outline none`: that hides walls drawn the wrong way and
  the fill spills past the walls.
- The outline must not cross itself, and no wall may loop back on
  itself. Otherwise Therion warns "invalid scrap outline" (no 3D model
  for the scrap) or MetaPost "scrap outline intersects itself".
- A line inside the passage (a ledge, the edge of another level) is a
  `line border`, not a wall.

## Symbols

- Never use `-clip off`. Large boulders (`line rock-border -close on`)
  get a `line rock-edge` inside them.
- Water: `line border -subtype invisible -id X -close on` inside the
  walls, then `area water` naming X.
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

## Checking

Build with the `swildons*.thconfig` files (see `README.md`), then:

- `grep -E "^therion: error|invalid scrap outline" output/*.log`:
  there should be none.
- `grep "intersects itself" output/*.log | sort -u`: only scraps you
  didn't touch.
- Render and look. poppler (pdftoppm, Evince, Okular) can show white
  holes in Therion's smooth altitude shading that aren't in the PDF;
  check with another renderer (MuPDF) before chasing them.
