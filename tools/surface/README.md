# The surface map

A page for visitors new to the area, such as a visiting club: where to
park and how to walk to the entrance. It works on a phone, and prints
on A4. It has:

- an OpenStreetMap background, which shows footpaths and field
  boundaries
- the places to park and the walks to the entrance, from
  `surface/surface.geojson`
- the entrance, with its grid reference, lat/long and a Google Maps link
- for each car park: the walk's length and time, a directions link and
  an "open in maps app" link
- on a phone, a **Show where I am** button that puts you on the map
  and says how far the entrance is. It works without signal, because
  the map is built into the page.
- an optional note on access arrangements (`surface/surface.toml`)

```bash
python3 -m tools.surface      # after the main build; writes output/surface/index.html and .pdf
```

## The GeoJSON

A FeatureCollection, for example drawn at <https://geojson.io>:

| Feature | Becomes |
|---|---|
| Point with `"type": "parking"` (or a name mentioning parking) | A car park marker, with directions links. |
| LineString with `"type": "route"` (or any LineString) | A walk to the entrance. Draw it from the parking towards the entrance: its arrows point the way it was drawn. |
| Any other Point | A labelled point on the way ("stile", "gate"). |

Each can have `name` (or `title`) and `description`. A walk is matched
to the car park within 120 m of either of its ends.

## Map tiles

They come from OpenStreetMap the first time and are kept in
`surface/tiles/`, so later builds don't fetch them again (OpenStreetMap
asks that tiles aren't downloaded repeatedly). Commit new tiles when the
map's area grows. The map credits OpenStreetMap, as its licence
requires.
