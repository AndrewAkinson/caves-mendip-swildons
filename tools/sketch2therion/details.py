"""Plan details that read as sketching: ledge lines and boulders.

- Lines inside the passage (the converter's borders, from brown and grey
  sketch strokes, or walls left inside the passage) are mostly the edge
  of a step down: a shelf, with the stream in the lowest part. Each open
  border over a metre long becomes a `line floor-step`, drawn so its
  ticks (which Therion puts on the line's left) are on the lower side,
  taken as the side the survey legs are on: the survey follows the
  stream.
- Boulders (`line rock-border -close on`) are straightened into clean
  polygons, and the bigger ones get facet edges from a ridge point to a
  few of their corners instead of one line straight across.

    python3 -m tools.sketch2therion details FILE.th2 [...]   (after a build)
"""
import math
import re

from shapely.geometry import LineString, Point, Polygon

from .roofs import Splays
from .sections import _survey_of
from .tidy import Obj, bezier_points, parse_scrap, scale_of

MIN_STEP = 1.0      # m: shorter interior lines stay borders


def _legs(objs, splays, survey):
    st = {}
    for o in objs:
        m = re.match(r'point (\S+) (\S+) station\b.*-name (\S+)', o.head) if o.kind == 'point' else None
        if m:
            n = m.group(3)
            st[n if '@' in n else f'{n}@{survey}'] = (float(m.group(1)), float(m.group(2)))
    return [LineString([st[a], st[b]]) for a in st for b in splays.legs.get(a, ()) if b in st and a < b]


def _side(pts, legs):
    """+1 if the legs are mostly on the line's left, -1 if on its right."""
    vote = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if d < 1e-9:
            continue
        m = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        near = min(legs, key=lambda l: l.distance(m))
        q = near.interpolate(near.project(m))
        cross = (b[0] - a[0]) * (q.y - a[1]) - (b[1] - a[1]) * (q.x - a[0])
        vote += d * (1 if cross > 0 else -1)
    return 1 if vote >= 0 else -1


def floor_steps(objs, K, legs):
    walls = [LineString(bezier_points(o.segments())) for o in objs
             if o.kind == 'line' and o.head.startswith('line wall') and '-subtype invisible' not in o.head
             and len(o.segments()) > 1]
    from shapely.ops import unary_union
    wall_all = unary_union(walls) if walls else None
    n = 0
    for o in objs:
        if o.kind == 'line' and o.head.split()[:2] == ['line', 'border'] and '-close on' not in o.head \
                and '-id' not in o.head and wall_all is not None:
            # a wall stroked twice: the second stroke runs alongside the wall
            pts = bezier_points(o.segments())
            if len(pts) > 1:
                line = LineString(pts)
                samples = [line.interpolate(i / 10, normalized=True) for i in range(11)]
                if sum(wall_all.distance(q) < 0.5 * K for q in samples) >= 8:
                    o.kind = 'drop'
                    continue
        if o.kind != 'line' or o.head.split()[:2] != ['line', 'border'] or '-close on' in o.head or '-id' in o.head:
            continue
        pts = bezier_points(o.segments())
        if len(pts) < 2 or LineString(pts).length < MIN_STEP * K:
            continue
        if legs and _side(pts, legs) < 0:
            from .tidy import reverse_segments
            o.set_segments(reverse_segments(o.segments()))
        o.head = 'line floor-step'
        n += 1
    return n


def boulders(objs, K):
    """Clean polygons with facet edges. Returns how many were redrawn."""
    out, n = [], 0
    for o in objs:
        if o.kind == 'drop':
            continue
        if o.kind == 'line' and o.head.startswith('line rock-edge'):
            continue                    # redrawn below
        out.append(o)
        if not (o.kind == 'line' and o.head.startswith('line rock-border')):
            continue
        pts = bezier_points(o.segments())
        if len(pts) < 4:
            continue
        g = Polygon(pts).buffer(0)
        if g.is_empty or g.geom_type != 'Polygon':
            continue
        size = math.sqrt(g.area) / K
        corners = list(g.exterior.simplify(max(0.06, 0.12 * size) * K).coords)[:-1]
        if len(corners) < 3:
            continue
        o.set_segments([[x, y] for x, y in corners + [corners[0]]])
        n += 1
        if g.area < (0.9 * K) ** 2:
            continue
        # a ridge point a little off the middle, joined to the corners
        # furthest round from each other
        c = g.centroid
        far = max(corners, key=lambda p: math.dist(p, (c.x, c.y)))
        rx = c.x + (far[0] - c.x) * 0.25
        ry = c.y + (far[1] - c.y) * 0.25
        by_angle = sorted(corners, key=lambda p: math.atan2(p[1] - ry, p[0] - rx))
        k = 3 if len(corners) >= 5 and size > 1.6 else 2
        step = len(by_angle) / k
        chosen = [by_angle[int(i * step)] for i in range(k)]
        for p in chosen:
            e = Obj('line', 'line rock-edge', [])
            # stop just short of the corner, as hand-drawn edges do
            e.set_segments([[rx, ry], [p[0] + (rx - p[0]) * 0.08, p[1] + (ry - p[1]) * 0.08]])
            out.append(e)
    objs[:] = out
    return n


def redo_file(path, splays=None, only=None):
    splays = splays or Splays()
    raw = open(path, 'rb').read()
    t = raw.decode('utf-8').replace('\r\n', '\n')
    survey = _survey_of(path)
    out, pos, report = [], 0, []
    for m in re.finditer(r'^(scrap (\S+)[^\n]*)\n(.*?)^endscrap', t, re.S | re.M):
        header, name, body = m.group(1), m.group(2), m.group(3)
        if '-projection plan' not in header or name.endswith('XS') or name.endswith('XSTop'):
            continue
        if only and name not in only:
            continue
        K = scale_of(header)
        objs = parse_scrap(body)
        legs = _legs(objs, splays, survey)
        steps = floor_steps(objs, K, legs)
        blocks = boulders(objs, K)
        out.append(t[pos:m.start(3)] + '\n'.join(o.text() for o in objs).rstrip('\n') + '\n')
        pos = m.end(3)
        report.append((name, steps, blocks))
    out.append(t[pos:])
    t = ''.join(out)
    if b'\r\n' in raw:
        t = t.replace('\n', '\r\n')
    open(path, 'wb').write(t.encode('utf-8'))
    return report
