"""Route cards: an A3 sheet per route, as HTML (printed to PDF by Chromium).

    +---------------------------------------------------------------+
    | 1  Title                                  [ length ][ depth ] |
    |    subtitle, description                  [ down/up ][ turns ]|
    +--------------------------------------+------------------------+
    |                                      |  1 [pull-out]  2 [...] |
    |   overview: the survey, the route    |  directions    ...     |
    |   with direction chevrons, numbered  |  3 [pull-out]  4 [...] |
    |   decision points, start and finish  |                        |
    +--------------------------------------+                        |
    |   profile: height along the route    |                        |
    +--------------------------------------+------------------------+
    | legend                                          credits, date |
    +---------------------------------------------------------------+

Every map panel is a window onto the same drawing, Therion's render of the
plan, embedded once per page and reused (<use>), with the route drawn on
top in the drawing's own coordinates.
"""
import datetime
import html
import math

ROUTE = '#e4572e'
ROUTE_DARK = '#9c2f12'
BADGE = '#1f3a5f'
GO = '#1d8a4e'
STOP = '#b3261e'
INK = '#1d2430'


def esc(t):
    return html.escape(str(t), quote=True)


def photo_uri(path):
    """A photo as a data: URI, so the card is one self-contained file (it works
    offline on a phone underground). Keep photos to a few hundred kB."""
    import base64
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or 'image/jpeg'
    data = open(path, 'rb').read()
    if len(data) > 1_500_000:
        print(f"  warning: {path} is {len(data) // 1000} kB; resize it to about 1600 px wide")
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def chaikin(pts, n=2):
    for _ in range(n):
        if len(pts) < 3:
            return pts
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]),
                  (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        q.append(pts[-1])
        pts = q
    return pts


def offset(pts, d):
    """Shift a polyline sideways by d (positive = right of travel, SVG's y-down
    frame), mitring the corners. Where it turns back on itself it goes round."""
    def unit_normal(a, b):
        L = math.dist(a, b)
        return (-(b[1] - a[1]) / L, (b[0] - a[0]) / L) if L > 1e-9 else None
    segs = [unit_normal(a, b) for a, b in zip(pts, pts[1:])]
    out = []
    for i, p in enumerate(pts):
        nin = next((segs[j] for j in range(i - 1, -1, -1) if segs[j]), None) if i > 0 else None
        nout = next((segs[j] for j in range(i, len(segs)) if segs[j]), None) if i < len(segs) else None
        if nin is None and nout is None:
            out.append(p)
            continue
        if nin is None or nout is None:
            n = nin or nout
            out.append((p[0] + n[0] * d, p[1] + n[1] * d))
            continue
        sx, sy = nin[0] + nout[0], nin[1] + nout[1]
        m = math.hypot(sx, sy)
        if m < 0.5:          # a U-turn: go round the outside
            out.append((p[0] + nin[0] * d, p[1] + nin[1] * d))
            tx, ty = nin[1], -nin[0]
            out.append((p[0] + tx * d, p[1] + ty * d))
            out.append((p[0] + nout[0] * d, p[1] + nout[1] * d))
            continue
        nx, ny = sx / m, sy / m
        cos = nx * nin[0] + ny * nin[1]
        L = min(d / max(cos, 0.4), 2.5 * d) if d >= 0 else max(d / max(cos, 0.4), 2.5 * d)
        out.append((p[0] + nx * L, p[1] + ny * L))
    return out


def path_d(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def along(pts, every, start=0.0):
    """Points and directions every `every` along a polyline: [(x, y, angle_deg)]."""
    out = []
    acc = 0.0
    nxt = start
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        while L > 0 and nxt <= acc + L:
            t = (nxt - acc) / L
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                        math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))))
            nxt += every
        acc += L
    return out


class View:
    """A window onto the base drawing: a survey-coordinate centre and width,
    fitted to a panel of w x h mm."""

    def __init__(self, base, centre, width_m, w_mm, h_mm):
        self.base = base
        self.w_mm, self.h_mm = w_mm, h_mm
        cx, cy = base.to_svg(centre)
        W = width_m * base.units_per_m
        H = W * h_mm / w_mm
        self.vb = (cx - W / 2, cy - H / 2, W, H)
        self.k = W / w_mm            # SVG units per mm on the page

    def mm(self, v):
        return v * self.k

    def svg(self, overlay, cls=''):
        x, y, W, H = self.vb
        return (f'<svg class="map {cls}" viewBox="{x:.1f} {y:.1f} {W:.1f} {H:.1f}" '
                f'width="{self.w_mm}mm" height="{self.h_mm}mm" preserveAspectRatio="xMidYMid slice">'
                f'<rect x="{x}" y="{y}" width="{W}" height="{H}" fill="#fbfaf7"/>'
                f'<use href="#basemap-root"/>{overlay}</svg>')


def fit_view(base, pts_m, w_mm, h_mm, margin_m=10.0, min_width_m=30.0):
    xs = [p[0] for p in pts_m]
    ys = [p[1] for p in pts_m]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    W = max(max(xs) - min(xs) + 2 * margin_m, (max(ys) - min(ys) + 2 * margin_m) * w_mm / h_mm, min_width_m)
    return View(base, (cx, cy), W, w_mm, h_mm)


# -- overlay pieces --------------------------------------------------------------

def route_layer(view, pts_svg, width_mm=1.0, chevron_every=9.0, lane_mm=0.0):
    """The route: a slim, slightly see-through line with a faint white halo,
    so the drawing underneath stays readable, and chevrons for the way."""
    k = view.k
    p = offset(pts_svg, k * lane_mm) if lane_mm else pts_svg
    o = [f'<path d="{path_d(p)}" fill="none" stroke="#fff" stroke-opacity="0.6" stroke-width="{k * (width_mm + 0.6):.2f}" '
         f'stroke-linejoin="round" stroke-linecap="round"/>',
         f'<path d="{path_d(p)}" fill="none" stroke="{ROUTE}" stroke-opacity="0.85" stroke-width="{k * width_mm:.2f}" '
         f'stroke-linejoin="round" stroke-linecap="round"/>']
    s = k * width_mm * 0.36
    for x, y, a in along(p, k * chevron_every, k * chevron_every / 2):
        o.append(f'<path d="M{-s:.2f} {-s * 1.1:.2f} L{s * 0.6:.2f} 0 L{-s:.2f} {s * 1.1:.2f}" fill="none" stroke="#fff" '
                 f'stroke-width="{k * width_mm * 0.2:.2f}" stroke-linecap="round" stroke-linejoin="round" '
                 f'transform="translate({x:.2f} {y:.2f}) rotate({a:.1f})"/>')
    return "".join(o)


def badge(view, p, text, r_mm=2.4, fill=BADGE):
    k = view.k
    return (f'<g transform="translate({p[0]:.2f} {p[1]:.2f})"><circle r="{k * r_mm:.2f}" fill="{fill}" '
            f'stroke="#fff" stroke-width="{k * 0.45:.2f}"/><text text-anchor="middle" dy="0.36em" '
            f'font-size="{k * r_mm * 1.15:.2f}" fill="#fff" font-weight="700">{esc(text)}</text></g>')


def badge_k(k, p, text, r_mm=2.2, fill=BADGE):
    """A numbered badge, sized by map units per mm."""
    return (f'<g transform="translate({p[0]:.2f} {p[1]:.2f})"><circle r="{k * r_mm:.2f}" fill="{fill}" '
            f'stroke="#fff" stroke-width="{k * 0.45:.2f}"/><text text-anchor="middle" dy="0.36em" '
            f'font-size="{k * r_mm * 1.15:.2f}" fill="#fff" font-weight="700">{esc(text)}</text></g>')


def flag(view, p, kind):
    """Start (green) or finish (chequered) marker."""
    k = view.k
    if kind == 'start':
        return (f'<g transform="translate({p[0]:.2f} {p[1]:.2f})"><circle r="{k * 3:.2f}" fill="{GO}" stroke="#fff" '
                f'stroke-width="{k * 0.5:.2f}"/><path d="M{-k * 1.1:.2f} {-k * 1.6:.2f} L{k * 1.7:.2f} 0 '
                f'L{-k * 1.1:.2f} {k * 1.6:.2f}Z" fill="#fff"/></g>')
    s = k * 1.1
    sq = "".join(f'<rect x="{(i - 2) * s:.2f}" y="{(j - 2) * s:.2f}" width="{s:.2f}" height="{s:.2f}" '
                 f'fill="{INK if (i + j) % 2 else "#fff"}"/>' for i in range(4) for j in range(4))
    return (f'<g transform="translate({p[0]:.2f} {p[1]:.2f})"><circle r="{k * 3:.2f}" fill="#fff" stroke="{INK}" '
            f'stroke-width="{k * 0.5:.2f}"/><clipPath id="cf{abs(hash(p)) % 99999}"><circle r="{k * 2.3:.2f}"/></clipPath>'
            f'<g clip-path="url(#cf{abs(hash(p)) % 99999})">{sq}</g></g>')


def cross(view, p, label=None, side='right'):
    k = view.k
    s = k * 1.3
    o = (f'<g transform="translate({p[0]:.2f} {p[1]:.2f})">'
         f'<path d="M{-s} {-s} L{s} {s} M{-s} {s} L{s} {-s}" stroke="#fff" stroke-width="{k * 1.5:.2f}" stroke-linecap="round"/>'
         f'<path d="M{-s} {-s} L{s} {s} M{-s} {s} L{s} {-s}" stroke="{STOP}" stroke-width="{k * 0.7:.2f}" stroke-linecap="round"/>')
    if label:
        o += (f'<text x="{k * (2.2 if side == "right" else -2.2):.2f}" y="{k * 0.9:.2f}" font-size="{k * 2.3:.2f}" fill="{STOP}" '
              f'text-anchor="{"start" if side == "right" else "end"}" '
              f'stroke="#fbfaf7" stroke-width="{k * 0.6:.2f}" paint-order="stroke" font-weight="600">{esc(label)}</text>')
    return o + '</g>'


def arrowhead(view, pts, width_mm=1.6):
    """A bold arrowhead at the end of a polyline."""
    k = view.k
    a, b = pts[-2], pts[-1]
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    s = k * width_mm * 1.6
    return (f'<path d="M{-s:.2f} {-s:.2f} L{s * 0.9:.2f} 0 L{-s:.2f} {s:.2f} Z" fill="{ROUTE}" stroke="#fff" '
            f'stroke-width="{k * 0.5:.2f}" stroke-linejoin="round" transform="translate({b[0]:.2f} {b[1]:.2f}) rotate({ang:.1f})"/>')


def scalebar(view, x_mm=6, y_mm=None):
    """A scale bar in page mm, as an HTML-positioned SVG."""
    m_per_mm = view.k / view.base.units_per_m
    target = view.w_mm * 0.22 * m_per_mm
    nice = min((1, 2, 5, 10, 20, 25, 50, 100, 200), key=lambda v: abs(v - target))
    L = nice / m_per_mm
    seg = L / 2
    return (f'<svg class="scalebar" width="{L + 12:.1f}mm" height="9mm" viewBox="0 0 {L + 12:.1f} 9">'
            f'<rect x="1" y="4" width="{seg:.2f}" height="1.6" fill="{INK}"/>'
            f'<rect x="{1 + seg:.2f}" y="4" width="{seg:.2f}" height="1.6" fill="#fff" stroke="{INK}" stroke-width="0.3"/>'
            f'<text x="1" y="3" font-size="2.6" fill="{INK}">0</text>'
            f'<text x="{1 + L:.2f}" y="3" font-size="2.6" fill="{INK}" text-anchor="middle">{nice} m</text></svg>')


NORTH = ('<svg class="north" width="9mm" height="13mm" viewBox="0 0 9 13"><path d="M4.5 1 L8 11 L4.5 8.6 L1 11 Z" '
         f'fill="{INK}"/><path d="M4.5 1 L4.5 8.6 L1 11 Z" fill="#fff" stroke="{INK}" stroke-width="0.35"/>'
         f'<text x="4.5" y="13" font-size="3" text-anchor="middle" font-weight="700" fill="{INK}">N</text></svg>')


def profile_svg(route, decisions, places, w_mm, h_mm):
    prof = route.profile(max(0.5, route.length / 600))
    z0 = route.z(0)
    zs = [z - z0 for _, z in prof]
    lo, hi = min(zs), max(zs)
    pad = max(2.0, (hi - lo) * 0.12)
    lo -= pad
    hi += pad * 2.4
    L = route.length
    left, right, top, bottom = 14, 4, 8, 7
    W, H = w_mm - left - right, h_mm - top - bottom
    X = lambda d: left + W * d / L
    Y = lambda z: top + H * (hi - z) / (hi - lo)
    line = " L".join(f"{X(d):.2f} {Y(z - z0):.2f}" for d, z in prof)
    o = [f'<svg class="profile" width="{w_mm}mm" height="{h_mm}mm" viewBox="0 0 {w_mm} {h_mm}">',
         '<defs><linearGradient id="pf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e4572e" stop-opacity="0.28"/>'
         '<stop offset="1" stop-color="#e4572e" stop-opacity="0.03"/></linearGradient></defs>']
    # grid: height lines
    step = min((2, 5, 10, 20, 25, 50), key=lambda v: abs((hi - lo) / v - 4))
    z = math.ceil(lo / step) * step
    while z <= hi:
        o.append(f'<line x1="{left}" x2="{left + W}" y1="{Y(z):.2f}" y2="{Y(z):.2f}" stroke="#d9d6cf" stroke-width="0.2"/>'
                 f'<text x="{left - 1.2}" y="{Y(z) + 0.9:.2f}" font-size="2.4" text-anchor="end" fill="#6b7280">'
                 f'{"+" if z > 0 else ""}{z:g} m</text>')
        z += step
    dstep = min((10, 20, 25, 50, 100), key=lambda v: abs(L / v - 8))
    d = 0
    while d <= L:
        o.append(f'<text x="{X(d):.2f}" y="{top + H + 4.5:.2f}" font-size="2.4" text-anchor="middle" fill="#6b7280">{d:g} m</text>')
        d += dstep
    o.append(f'<path d="M{X(0):.2f} {top + H:.2f} L{line} L{X(L):.2f} {top + H:.2f} Z" fill="url(#pf)"/>')
    o.append(f'<path d="M{line}" fill="none" stroke="{ROUTE}" stroke-width="0.7" stroke-linejoin="round"/>')
    # places along the top
    last_end = -99
    shown = set()
    for dd, t in places:
        x = X(dd)
        half = len(t) * 0.62
        if x - half < last_end + 2 or (t in shown and x - last_end < 60):
            continue
        last_end = x + half
        shown.add(t)
        zz = route.point_at(dd)[2] - z0
        o.append(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{top - 1:.2f}" y2="{Y(zz) - 1.2:.2f}" stroke="#b9b4aa" stroke-width="0.2" stroke-dasharray="0.6 0.6"/>'
                 f'<text x="{x:.2f}" y="{top - 2:.2f}" font-size="2.5" text-anchor="middle" fill="{INK}">{esc(t)}</text>')
    for num, dd in decisions:
        zz = route.point_at(dd)[2] - z0
        o.append(f'<g transform="translate({X(dd):.2f} {Y(zz):.2f})"><circle r="2" fill="{BADGE}" stroke="#fff" stroke-width="0.35"/>'
                 f'<text text-anchor="middle" dy="0.36em" font-size="2.3" fill="#fff" font-weight="700">{esc(num)}</text></g>')
    o.append(f'<text x="{left}" y="{h_mm - 0.6:.2f}" font-size="2.3" fill="#6b7280">Height above or below the start, along the route</text>')
    o.append('</svg>')
    return "".join(o)


LEGEND = f'''
<div class="legend">
  <span><svg width="14mm" height="5mm" viewBox="0 0 14 5"><path d="M1 2.5 L13 2.5" stroke="#fff" stroke-opacity="0.6" stroke-width="1.6"/>
    <path d="M1 2.5 L13 2.5" stroke="{ROUTE}" stroke-opacity="0.85" stroke-width="1"/><path d="M6.3 2 L7 2.5 L6.3 3" fill="none" stroke="#fff" stroke-width="0.2"/></svg>
    The route: chevrons point the way; it keeps right where it passes twice</span>
  <span><svg width="6mm" height="6mm" viewBox="-3 -3 6 6"><circle r="2.4" fill="{BADGE}"/><text text-anchor="middle" dy="0.36em" font-size="2.7" fill="#fff" font-weight="700">3</text></svg>
    Decision, with a close-up</span>
  <span><svg width="6mm" height="6mm" viewBox="-3 -3 6 6"><path d="M-1.3 -1.3 L1.3 1.3 M-1.3 1.3 L1.3 -1.3" stroke="{STOP}" stroke-width="0.7"/></svg>
    Not this way</span>
  <span><svg width="7mm" height="7mm" viewBox="-3.5 -3.5 7 7"><circle r="3" fill="{GO}"/><path d="M-1.1 -1.6 L1.7 0 L-1.1 1.6Z" fill="#fff"/></svg> Start</span>
</div>'''


CSS = '''
@page { size: 420mm 297mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fbfaf7; }
body { width: 420mm; height: 297mm; font-family: "Source Sans 3", "Liberation Sans", Arial, sans-serif; color: #1d2430;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 420mm; height: 297mm; padding: 9mm 10mm 6mm; display: grid;
         grid-template-columns: 252mm 1fr; grid-template-rows: auto minmax(0, 1fr) 44mm auto; column-gap: 8mm; row-gap: 3.5mm; }
header { grid-column: 1 / 3; display: grid; grid-template-columns: 1fr auto; column-gap: 10mm; align-items: start;
         border-bottom: 0.5mm solid #1d2430; padding-bottom: 3.5mm; }
.kicker { font-size: 3.4mm; letter-spacing: 0.35mm; text-transform: uppercase; color: #9c2f12; font-weight: 700; }
h1 { font-family: "Fraunces", "DejaVu Serif", Georgia, serif; font-size: 11mm; line-height: 1.02; margin: 1mm 0 1.5mm; font-weight: 700; }
.subtitle { font-size: 4.6mm; color: #374151; margin-bottom: 2mm; }
.desc { font-size: 3.5mm; line-height: 1.38; max-width: 255mm; color: #1d2430; }
.via { font-size: 3.1mm; color: #5b6573; margin-top: 1.6mm; }
.side { display: flex; gap: 3mm; align-items: flex-start; }
.locator { display: flex; flex-direction: column; gap: 0.8mm; }
.locator .map { border: 0.3mm solid #e2ded5; border-radius: 2mm; background: #fff; }
.locator span { font-size: 2.4mm; color: #5b6573; text-transform: uppercase; letter-spacing: 0.2mm; }
.stats { display: grid; grid-template-columns: repeat(2, 36mm); gap: 2.4mm; }
.stat { background: #fff; border: 0.3mm solid #e2ded5; border-radius: 2mm; padding: 2mm 3mm; }
.stat b { display: block; font-size: 6.4mm; white-space: nowrap; line-height: 1; font-weight: 700; }
.stat span { font-size: 2.8mm; color: #5b6573; text-transform: uppercase; letter-spacing: 0.2mm; }
.overview .map { width: 100%; height: 100%; display: block; }
.overview { position: relative; min-height: 0; border: 0.3mm solid #cfcac0; border-radius: 2.5mm; overflow: hidden; background: #fbfaf7; }
.overview .north { position: absolute; top: 4mm; right: 4mm; }
.overview .scalebar { position: absolute; bottom: 3mm; left: 4mm; }
.profilebox { border: 0.3mm solid #e2ded5; border-radius: 2.5mm; background: #fff; overflow: hidden; }
aside { grid-row: 2 / 4; grid-column: 2; display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: max-content;
        gap: 2.6mm; align-content: start; min-height: 0; }
aside h2 { grid-column: 1 / 3; margin: 0; font-size: 3.6mm; letter-spacing: 0.3mm; text-transform: uppercase; color: #5b6573; }
.pull { background: #fff; border: 0.3mm solid #e2ded5; border-radius: 2.2mm; overflow: hidden; display: flex; flex-direction: column; }
.pull .map { display: block; border-bottom: 0.3mm solid #e2ded5; }
.pull .txt { padding: 1.4mm 2.2mm 1.8mm; font-size: 2.7mm; line-height: 1.28; }
.pull .head { display: flex; align-items: center; gap: 1.6mm; margin-bottom: 0.8mm; }
.num { display: inline-grid; place-items: center; width: 5mm; height: 5mm; border-radius: 50%; background: #1f3a5f; color: #fff;
       font-weight: 700; font-size: 2.9mm; flex: none; }
.pull .where { font-weight: 700; font-size: 3.1mm; }
.pull .dist { color: #6b7280; font-size: 2.5mm; margin-left: auto; white-space: nowrap; }
.pull .pass { color: #9c2f12; font-weight: 700; }
.pull .note { margin-top: 0.8mm; color: #374151; font-style: italic; }
.more { grid-column: 1 / 3; font-size: 2.8mm; line-height: 1.35; color: #374151; }
footer { grid-column: 1 / 3; display: grid; grid-template-columns: auto 1fr; align-items: center; gap: 8mm;
         font-size: 2.5mm; color: #5b6573; border-top: 0.3mm solid #d9d6cf; padding-top: 2mm; }
.legend { display: flex; gap: 5mm; align-items: center; white-space: nowrap; }
.credit { text-align: right; }
.legend span { display: inline-flex; align-items: center; gap: 1.5mm; }
.draft { color: #9c2f12; font-weight: 700; }
.sheet.wide { grid-template-columns: 1fr; grid-template-rows: auto 86mm 32mm minmax(0, 1fr) auto; }
.sheet.wide .overview { grid-row: 2; }
.sheet.wide .profilebox { grid-row: 3; }
.sheet.wide aside { grid-row: 4; grid-column: 1; grid-template-columns: repeat(6, 1fr); }
.sheet.wide aside h2 { grid-column: 1 / 7; }
.sheet.wide .more { grid-column: 1 / 7; }
.photo { margin: 0; position: relative; border-bottom: 0.3mm solid #e2ded5; }
.photo img { display: block; width: 100%; height: var(--ph, 40mm); object-fit: cover; }
.photo figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 0.8mm 2mm; font-size: 2.4mm;
                    color: #fff; background: linear-gradient(transparent, rgba(0,0,0,0.65)); }
.overview a, .pull a { cursor: pointer; }

/* On a phone (or any narrow screen): one column, maps full width, tap a number
   on the map to jump to its close-up. Printing keeps the A3 sheet. */
@media screen and (max-width: 1100px) {
  html, body { width: auto; height: auto; }
  body { font-size: 16px; }
  .sheet, .sheet.wide { display: block; width: auto; height: auto; padding: 14px; }
  header { display: block; padding-bottom: 12px; }
  h1 { font-size: 30px; }
  .kicker { font-size: 12px; } .subtitle { font-size: 17px; } .desc { font-size: 15px; } .via { font-size: 13px; }
  .sheet * { min-width: 0; max-width: 100%; }
  .side { display: block; margin-top: 12px; }
  .locator { display: block; } .locator .map { width: 100%; height: auto; aspect-ratio: 92 / 30; }
  .stats { grid-template-columns: repeat(2, 1fr); width: 100%; gap: 6px; margin-top: 8px; }
  .stat { padding: 6px 8px; } .stat b { font-size: 20px; } .stat span { font-size: 10px; }
  .overview { margin-top: 12px; aspect-ratio: var(--ar); height: auto; }
  .profilebox { margin-top: 10px; } .profilebox svg { width: 100%; height: auto; }
  aside, .sheet.wide aside { display: block; margin-top: 16px; }
  aside h2 { font-size: 13px; margin-bottom: 8px; }
  .pull { margin-bottom: 14px; scroll-margin-top: 10px; }
  .pull .map { width: 100%; height: auto; aspect-ratio: var(--ar, 16 / 10); }
  .photo img { height: auto; max-height: 70vh; }
  .photo figcaption { font-size: 13px; padding: 6px 10px; }
  .pull .txt { font-size: 15px; padding: 8px 10px 10px; }
  .num { width: 24px; height: 24px; font-size: 13px; } .pull .where { font-size: 16px; } .pull .dist { font-size: 11px; }
  .more { font-size: 14px; }
  footer { display: block; font-size: 12px; margin-top: 10px; } .legend { flex-wrap: wrap; white-space: normal; gap: 10px; }
  .legend span { white-space: normal; }
  .credit { text-align: left; margin-top: 8px; }
}
.kit { grid-column: 1 / -1; background: #fff; border: 0.3mm solid #e2ded5; border-left: 1.2mm solid #9c2f12;
       border-radius: 2mm; padding: 1.8mm 2.6mm 2mm; font-size: 2.75mm; line-height: 1.35; }
.kit h2 { margin: 0 0 0.8mm; }
.kit b { color: #1d2430; margin-right: 1mm; }
.kit .todo { color: #9c2f12; font-style: italic; }
@media screen and (max-width: 1100px) { .kit { font-size: 15px; padding: 10px 12px; margin-bottom: 14px; } }
.basemap { position: absolute; width: 0; height: 0; overflow: hidden; }
'''

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">')
