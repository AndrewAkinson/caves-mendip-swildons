# Swildons Hole

[![Plan of Swildons Hole from the entrance to Sump 1](docs/swildons-plan.png)](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan.pdf)

The survey of **Swildons Hole**, Priddy, Mendip, Somerset. It combines
the resurvey led by Paul 'Footleg' Fretwell (2012–2019) with
W. I. Stanton's original survey of the 1950s and 60s, transcribed from
his logbooks. The resurvey was done with DistoX and PocketTopo; the
survey is drawn and built with [Therion](https://therion.speleo.sk/).

**[Open the survey](https://paperclipmonkey.github.io/caves-mendip-swildons/)**:
the latest sheets, rebuilt from this repository every time it changes.

| Sheet | |
|---|---|
| [Plan](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan.pdf) | Entrance to Sump 1, coloured by altitude, with cross-sections along the streamway. 1:500. |
| [Extended elevation](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-extended-elevation.pdf) | The whole drawn cave unrolled along its passages, entrance to Sump 1. 1:500. |
| [Streamway elevation](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-streamway-elevation.pdf) | Extended elevation from the Old 40 to Sump 1, with Barnes Loop above the streamway. 1:500. |
| [Entrance Series plan](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-entrance-plan.pdf) | The Entrance Series down to Rolling Thunder, with cross-sections. The entrances and Zig Zags, which lie on top of the passages below, are drawn 35 m to the east, joined to them by letters. 1:200. |
| [Entrance Series extended elevation](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-entrance-extended-elevation.pdf) | The Entrance Series unrolled along its passages. 1:200. |
| [Entrance Series east–west elevation](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-entrance-elevation.pdf) | Footleg's projected elevation, only partly drawn. 1:200. |
| [Plan, greyscale](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan-bw.pdf) | For a black-and-white printer. |
| [Plan with centreline](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan-centreline.pdf) | The plan with survey legs and station names, for resurveying. 1:500. |
| [Plan with Stanton's survey](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan-with-stanton.pdf) | The plan plus Stanton's survey beyond it as centreline, with station names, for planning where to resurvey next. 1:500. |

**Getting there**: for visitors new to the area, a map of where to park
and the walks to the entrance. See [tools/surface](tools/surface/README.md).

**Route cards** (draft): one sheet per route through the cave, with
the way to go at each junction, made automatically from the survey. See
[tools/routes](tools/routes/README.md); the routes are in `routes/`.

The survey site also has the 3D model (Survex `.3d` for Aven, Therion
`.lox` for Loch), Google Earth `.kml` files and the survey data as CSV
and SQL.

[![Extended elevation of the streamway from the Old 40 to Sump 1](docs/swildons-streamway-elevation.png)](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-streamway-elevation.pdf)

## What's surveyed

The centreline is about **4.2 km** of survey legs with **121 m** of
vertical range, fixed to the OS grid at the entrance by GPS.

- **The resurvey, about 1.8 km:** the Entrance Series, Rolling Thunder,
  and the streamway from the Old 40 down past the 20 ft Pot, Double
  Pots, Barnes Loop and Tratman's Temple to the free-dive bolt at
  Sump 1. All of it is drawn in plan and as an extended elevation
  (the streamway on its own sheet, the Entrance Series on another),
  with about 160 cross-sections: 39 along the streamway on the main
  plan, and the rest on the 1:200 Entrance Series plan. Footleg's
  projected east–west elevation of the Entrance Series is only partly
  drawn.
- **Stanton's survey, about 2.4 km:** everything beyond the resurvey,
  including St Paul's, Paradise Regained, the Maypole Series, Double
  Trouble and Swildons 2 (main streamway, Upper Mud Series, Black Hole
  Series, Vicarage Passage). It is centreline only, with no drawings.
  Where the resurvey has replaced one of his sections, his legs are kept
  to connect the rest of his survey but flagged `duplicate`, so they
  are not counted twice.

### Resurvey trips

| Date | Where | Team |
|---|---|---|
| 2012-09-09 | Zig Zags | Paul 'Footleg' Fretwell, Tony 'Badger' Radmall, Paul Wilman |
| 2013-02-23 | Long Dry Way (Pretty Way) | Footleg, Cave Ferret, Badger |
| 2013-02-24 | Short Dry Way, New Grottoes, Old Grotto to Water Chamber | Footleg, Paul Dold, Badger |
| 2013-06-29 | Water Rift to the Folded Strata corner; the Old 40 route | Badger, Paul Dold, Josh White; Ben Kent, Footleg |
| 2013-06-30 | Kenney's Dig to Showerbath; lower entrance area via Showerbath to Baptism | Badger, Paul Dold; Ben Kent, Footleg |
| 2016-01-16/17 | Wet Way oxbows; Butcombe oxbows | Footleg, Paul Dold, Ben Kent, Alistair Smith |
| 2016-07-09/10 | Water Chamber, Oxbow Junction, Wet Way keyhole, Lower Oxbow, inlet off Old Grotto | Footleg, Thomas Starnes, Paul Wilman |
| 2017-03-11 | Old 40 to the 20 ft Pot; Cistern Dig | Footleg, Josh White, Paul Wilman, Alistair Smith; Cave Ferret |
| 2017-03-25/26 | 20 ft Pot to Double Pots | Footleg, Michael Waterworth, Maxine Bateman, Duncan Simey, Paul Wilman, Paul Carruthers and Josh\* |
| 2017-07-08 | Double Pots through Barnes Loop | Footleg, Sarah Bischoff, Josh Benton |
| 2017-10-14 | Barnes Loop to Tratman's Temple | Footleg, Paul Taylor, Tim Kent |
| 2019-01-05 | Tratman's Temple to Sump 1; Rolling Thunder | Footleg, Tim Kent, Alistair Smith |

\* Josh's surname isn't recorded in the trip notes.

## How the drawings were made

Footleg drew the plan of the Entrance Series and the streamway down to
just below the 20 ft Pot himself, in xTherion. Everything else, the
plan from there to Sump 1 and all the extended elevations and
cross-sections, is converted from his PocketTopo sketches made
underground (the converter is in `tools/`):

- **Plan:** black lines are walls (brown for upper-level edges), smoothed,
  with retraced strokes dropped. Lines inside the passage become thin
  borders, as in his own drawings. Blue hatching becomes water, blue
  squiggles flow arrows, green marks flowstone, small loops boulders,
  and slope triangles gradient arrows. Passage names are placed from his
  station notes, and his handwritten notes become labels.
- **Floor detail:** floor steps, climbs (C1m to C2m) and gradients come
  from the floor line of his side-view sketches, checked against floor
  heights from the survey's downward splays. Floor sediment isn't
  recorded for this stretch, so none is drawn.
- **Elevation and cross-sections:** both come from the PocketTopo
  sketches, the elevations from the side views and the cross-sections
  from wherever Footleg drew them (the plan sketch on the 2013 trips,
  the side view later). Each leg's left/right direction from PocketTopo
  is copied into the survey files so Therion unrolls the cave the way
  he did. An unrolled elevation can't close a loop, so where Therion
  breaks one differently from a sketch the sketch is split, and
  passages can show a gap or an overlap there. Barnes Loop is drawn
  above the streamway as an oxbow. In the side views Footleg drew
  passages that overlap in other colours (the Wet Way in brown, the
  upper oxbows in grey), so those are walls too.
- **Which sketch:** the 2013 Entrance to Water Chamber side view comes
  from the original `.top` file, because the exported station list
  doesn't line up with its sketch. Wet Way Oxbows uses the January 2016
  sketch, which lines up better than the July 2016 one, except for the
  Wet Way Keyhole, which only the July sketch has. The 2017 Dry
  Way Stream sketch isn't used: its stations aren't in the Therion
  survey.

They are faithful to the sketches but not hand-finished. Each trip's
sketch is in `PocketTopo/` as an `.xvi` backdrop for anyone who wants
to refine the drawings in xTherion.

## Picking up the resurvey

The [plan with Stanton's survey](https://paperclipmonkey.github.io/caves-mendip-swildons/Swildons-plan-with-stanton.pdf)
shows where the resurvey stops and what Stanton surveyed beyond it,
with station names for both. The resurvey reaches:

- **Sump 1:** station 24.33, the bolt for the free-dive line. Beyond it
  only Stanton's Swildons 2 survey exists (`swildons2-a` to `-e.th`,
  starting from his station B1 at the entrance to the "P.G." passage,
  which is about 11 m from 24.28 on the current layout).
- **Tratman's Temple:** Stanton's St Paul's survey (`swildons1-f.th`)
  starts at his station AL, "below Trats Grotto", about 3 m from 24.2.
  Damascus, Paradise Regained, the Maypole Series and Double Trouble
  (`swildons1-g` and `-j` to `-o.th`) hang off it.

Stanton's survey is placed by his own measurements from the Forty, so
near the resurvey it is a few metres out. When a new trip reaches one of
his stations, equate it in `Swildons_Centreline.th` so the rest of his
survey hangs off the new data, and flag the legs it replaces
`duplicate`, as `swildons1-c/d/e.th` are. [tools/README.md](tools/README.md)
has the details, and the workflow for getting a SexyTopo trip and its
sketches into the survey.

## Working on the survey

**[`tools/README.md`](tools/README.md) explains how to add a new SexyTopo
trip, drawings included.** `ProjectWorkflow.txt` has the original
PocketTopo workflow.

| Path | What it is |
|---|---|
| `Swildons_*.th` | One file per survey trip: data, team, and the drawings it inputs. |
| `Swil1P_*.th2`, `Swil1E_*.th2` | Plan (`P`) and elevation (`E`) drawings. The `E` files also hold the cross-sections. |
| `Swildons_Centreline.th` | Joins every trip together; the GPS fix. |
| `Swildons_MAP*.th`, `swildonsmaster.th` | The maps: which drawings make up each sheet. |
| `swildons1-*.th`, `swildons2-*.th`, `Swildons_WIS*.th` | W. I. Stanton's survey. |
| `PocketTopo/` | The original PocketTopo files and their exports. |
| `tools/` | The sketch converter and helpers for adding new trips: see [tools/README.md](tools/README.md). |
| `routes/`, `tools/routes/` | Route card definitions, and the tool that makes them. |
| `WISLogbookTranscription/` | Scans and a transcription of Stanton's logbooks. |
| `SwildonsHole.svx` | The data in Survex format. |
| `thconfig`, `thconfig-entrance`, `thconfig-centreline`, `thconfig-stanton`, `gb_layout.thc` | Build configs and Footleg's British symbol set. |

### Building it yourself

With Docker, using the same pinned Therion image as the website:

```bash
mkdir -p proj output
curl -fL -o proj/uk_os_OSTN15_NTv2_OSGBtoETRS.tif \
  https://cdn.proj.org/uk_os_OSTN15_NTv2_OSGBtoETRS.tif   # OS grid shift, for the KML
therion() { docker run --rm -v "$PWD:/project" \
  -e PROJ_DATA=/project/proj:/usr/share/proj -e PROJ_NETWORK=OFF \
  ghcr.io/paperclipmonkey/therion:6.4.0 "$@"; }
therion thconfig
therion -l output/therion-entrance.log thconfig-entrance
therion -l output/therion-centreline.log thconfig-centreline
therion -l output/therion-stanton.log thconfig-stanton
```

Or with Therion installed:
`therion thconfig`, `therion thconfig-entrance`,
`therion thconfig-centreline` and `therion thconfig-stanton`. The sheets land in `output/`. The older
`swildons_*.thconfig` files from the SVN project still work and write
into the project root.

Every push to `main` rebuilds the survey and publishes it
(`.github/workflows/build.yml`). A pull request gets the built sheets
and survey statistics in a comment instead. Some things to know:

- Filenames are case-sensitive on the build machines, so an `input`
  must match the file's case exactly.
- `fix bottom` in `Swildons_Centreline.th` is a fake station that pins
  the bottom of the altitude colours. It is not a point in the cave.
- The Therion image is pinned to `6.4.0` so the survey renders the same
  until someone deliberately updates it.

## History

This repository was migrated from the `Swildons` folder of the
WookeyCatchment Subversion repository
(<https://www.cave-registry.org.uk/svn/WookeyCatchment/Swildons/>), with
its history from 2012 onwards. Each commit keeps its original author,
date and message, plus an `SVN-Revision:` line. Folders that are
access-restricted in SVN are not included.

## Licence

GPLv3. See `LICENSE`, which covers everything here unless a file or
folder says otherwise.
