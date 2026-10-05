# Swildons Hole

Cave survey data for **Swildons Hole**, Priddy, Mendip, Somerset — the
resurvey project led by Paul 'Footleg' Fretwell, 2013–2019, plus
W. I. Stanton's original survey transcribed from his logbooks. Surveyed
with PocketTopo, drawn and rendered with
[Therion](https://therion.speleo.sk/).

**📄 [Latest drawn survey](https://paperclipmonkey.github.io/caves-mendip-swildons/)** —
rebuilt automatically from this repository on every push to `main`.

---

## Where this came from

This repository is a migration of the `Swildons` folder of the
WookeyCatchment Subversion repository,
<https://www.cave-registry.org.uk/svn/WookeyCatchment/Swildons/>,
with its full history (SVN r4–r230, 2012–2026).

- Every commit that changed something kept its author, date and
  message, with an `SVN-Revision:` trailer naming the original revision.
  Commits with no message in SVN say so.
- `footleg` is mapped to *Paul Fretwell (Footleg)*. SVN had no email
  addresses, so the commits keep git-svn's placeholder address.
- The SVN repository has access-restricted folders (the 2019 restructure
  moved some scrap drawings into one). Revisions that touched only those
  are not readable anonymously, came across empty, and were dropped (19
  of them). Nothing restricted is in here.
- `gb_layout.thc` lived one level up in SVN
  (`WookeyCatchment/gb_layout.thc`) and is copied in alongside the
  configs that use it.

## Status

The centreline is the whole cave as surveyed so far: about 4.2 km of
legs, 121 m of vertical range, fixed to the OS grid at the entrance by
GPS. About 1.8 km of that is the resurvey, from the entrance down the
streamway to Sump 1; the other 2.4 km is W. I. Stanton's survey of
everything beyond it (St Paul's, Paradise Regained, Swildons 2 and
more). Where the resurvey has replaced a Stanton section (the streamway
from the Forty to Sump 1, `swildons1-c/d/e.th`), his legs are flagged
`duplicate`: they still connect the rest of his survey but are not
counted in the length.

The **drawn plan** covers the whole resurvey: the Entrance Series,
Rolling Thunder, and the streamway from the Old 40 down past Barnes
Loop and Tratman's Temple to Sump 1. Below the 20 ft pot,
`StreamwaySP1` in `Swil1P_20toBarnesLoop.th2` is Footleg's drawing as
far as station 21.9. From there to Sump 1 (`StreamwaySP2`, and the
`Swil1P_DblPotsDownstream`, `Swil1P_BarnesLoopToTratmans` and
`Swil1P_TratmansToSump1` drawings) everything comes from his PocketTopo
sketches. In the plan sketches, black lines are walls (brown for
upper-level edges), smoothed, with retraced strokes dropped. Lines
along the passage edge are drawn as wall and lines inside it as thin
borders, as in his own drawings. Pools are the blue hatched areas,
flow arrows the blue squiggles, and flowstone (with the odd stalagmite
or stalactite) the green marks. The small notes are his handwritten
ones, and the passage names are placed from his station notes. Floor
steps, climbs (C1m, C1.5m, C2m) and gradient arrows come from the
floor line of his extended-elevation sketches, checked against the
floor heights from the downward splays. Floor sediment (pebbles, clay
and so on) isn't recorded anywhere for this stretch, so it isn't drawn.
Each trip's PocketTopo backdrop (`PocketTopo/*_th_p.xvi`) is there to
draw over. The **Entrance Series elevation** is only partly drawn.

## Building it yourself

The CI build is two config files, `thconfig` (the whole cave) and
`thconfig-entrance` (the Entrance Series plan at 1:200). Therion only
takes one selected map per projection per run, so the second plan
sheet needs its own file.

The survey is in OS grid coordinates, and the KML exports need
Ordnance Survey's OSTN15 grid-shift file to convert them. Fetch it once
into `proj/` (git-ignored):

```bash
mkdir -p proj output
curl -fL -o proj/uk_os_OSTN15_NTv2_OSGBtoETRS.tif \
  https://cdn.proj.org/uk_os_OSTN15_NTv2_OSGBtoETRS.tif
```

Then, with no local install, using the same container CI uses:

```bash
therion() { docker run --rm -v "$PWD:/project" \
  -e PROJ_DATA=/project/proj:/usr/share/proj -e PROJ_NETWORK=OFF \
  ghcr.io/paperclipmonkey/therion:6.4.0 "$@"; }
therion thconfig
therion -l output/therion-entrance.log thconfig-entrance
docker run --rm -v "$PWD:/project" --entrypoint python3 \
  ghcr.io/paperclipmonkey/therion:6.4.0 web/make_index.py
```

Or with Therion installed locally, `therion thconfig` and
`therion thconfig-entrance`. A local Therion with network access
downloads the grid file itself on first use.

Output lands in `output/` (git-ignored). Open `output/index.html`.

The SVN-era configs still work as they did and write into the project
root (also git-ignored):

| Config | What it builds |
|---|---|
| `swildons_all.thconfig` | Master plan, elevation, KML, SVG and models |
| `swildons_plan.thconfig` | Master plan only |
| `swildons_ent.thconfig` | Entrance Series plan and elevation |
| `swildons_elev.thconfig` | Entrance Series elevation centreline as an `.xvi` backdrop |
| `thconfig-swildons` | Centreline models only (`Swildons.th`, no drawings) |

## What is where

| Path | What it is |
|---|---|
| `thconfig`, `thconfig-entrance` | The CI build: every sheet and export, into `output/`. |
| `gb_layout.thc` | Footleg's British symbol set and colour layouts, used by every config. |
| `swildonsmaster.th` | Top of the project: centreline plus the plan and elevation maps. |
| `Swildons.th` | Centreline only, no drawings. |
| `Swildons_Centreline.th` | Pulls in every survey trip and equates them together; the GPS fix and `cs`. |
| `Swildons_*.th` | One file per survey trip: data, team, and the drawing it inputs. |
| `Swil1P_*.th2`, `Swil1E_*.th2` | Plan (`P`) and elevation (`E`) drawings. |
| `Swildons_MAP*.th` | Map definitions and the joins between scraps. |
| `swildons1-*.th`, `swildons2-*.th`, `Swildons_WIS*.th` | W. I. Stanton's original survey. |
| `PocketTopo/` | Raw PocketTopo `.top` files and their text, Therion and `.xvi` exports. |
| `WISLogbookTranscription/` | Scans and a transcription spreadsheet of Stanton's logbooks. |
| `drawings/` | Backdrops for drawing. |
| `*.svx` | Survex versions of the data. |
| `ProjectWorkflow.txt` | **How new survey trips are added.** Read this first. |
| `web/make_index.py` | Builds the GitHub Pages landing page from `output/`. |
| `.github/workflows/build.yml` | Build, publish, and PR previews. |

## How the automation works

`.github/workflows/build.yml` does the same build in all cases and then
branches on the event:

- **Push to `main`** → build → generate `index.html` → publish to GitHub
  Pages.
- **Pull request** → build → post (or update) a comment on the PR with
  the survey statistics and a link to the built sheets. Nothing is
  published until it merges.
- **Manual** → `workflow_dispatch`, same as a push.

Every run attaches `output/` to the run page as a downloadable artifact
for 14 days. The build fails if Therion logs an error; warnings are
collected into a collapsed group in the run log rather than failing the
build. Each run also writes a summary (station count, length, vertical
range, and the size of every artefact) to the Actions run page.

### First-time setup

GitHub Pages must be set to **Source: GitHub Actions** in
*Settings → Pages*. Until it is, the publish step fails, but the build
and its downloadable artifact still work.

## Notes for whoever edits this next

- **Filenames are case-sensitive on CI.** The runners are Linux, so an
  `input` whose case doesn't match the file builds on Windows or a Mac
  and fails here with *can't open file for input*. That has happened
  once already (`Swildons_20toBarnesLoop.th`).
- **The build is pinned to `ghcr.io/paperclipmonkey/therion:6.4.0`**, not
  `:latest`, so a survey rebuilt in a year renders identically. Bump it
  in `.github/workflows/build.yml` deliberately.
- **The OSTN15 grid is cached** in CI under a fixed key. If PROJ ever
  needs a different grid, add it to the fetch step and bump the `-v1`
  in the cache key.
- **`fix bottom` in `Swildons_Centreline.th` is a fake station** that
  pins the bottom of the colour-by-altitude scale. It is not a real
  point in the cave.
- The sheets give a handful of *scrap outline intersects itself*
  warnings from MetaPost. They are harmless, but each one is a scrap
  whose outline could be tidied.

## Licence

GPLv3 — see `LICENSE`, which applies to everything here unless a file
or folder says otherwise.

A sister project for C10 (`caves-wye-c10`) has the same build
structure.
