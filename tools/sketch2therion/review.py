"""Reviewing a drawing against the surveyor's sketch, with someone who
knows the cave.

    python3 -m tools.sketch2therion review build
        build the plan with station names (output/review-plan.pdf); copy it
        aside before editing to have a "before"
    python3 -m tools.sketch2therion review show OUT.png 23.10 23.11 ... [--title T]
        [--before OLD.pdf] [--ring 23.12 23.13]
        a split screen: the original sketch (PocketTopo or XVI, with its
        colours, legs and station names) beside the drawing at those
        stations; with --before, sketch | before | after
    python3 -m tools.sketch2therion review gaps FILE.th2 SCRAP [...]
        where Therion closes the outline with a straight line, and how much
        of each the sketch draws a wall along: walls lost in conversion
    python3 -m tools.sketch2therion review check FILE.th2 [SCRAP ...]
        the outlines as Therion joins them: valid (no 3D failure) and
        MetaPost's turning number (0 means "scrap outline intersects
        itself")

See the review section of .claude/skills/therion-drawing/SKILL.md.
"""
import glob
import io
import math
import os
import re
import subprocess
import sys

from shapely.geometry import LineString, Point

from . import pockettopo, register, xvi
from .tidy import bezier_points, parse_scrap, reverse_segments, therion_rings

K = 39.37
PLAN = 'output/review-plan.pdf'
LAYOUT = 'output/layout-plan.xvi'
COLOURS = {'BLACK': '#111111', 'GRAY': '#888888', 'BROWN': '#8b4513', 'BLUE': '#1f5fff',
           'RED': '#dd0000', 'GREEN': '#1a9a1a', 'ORANGE': '#ff9900'}


# -- sketches --------------------------------------------------------------------------

_SKETCHES = {}


def _sketch(path, view='plan'):
    if (path, view) not in _SKETCHES:
        if path.lower().endswith('.xvi'):
            _SKETCHES[(path, view)] = xvi.read(path)
        else:
            _SKETCHES[(path, view)] = pockettopo.sketch(path, view)
    return _SKETCHES[(path, view)]


def sketches_for(stations, view='plan'):
    """The sketch files that have these stations, most of them first."""
    files = glob.glob('PocketTopo/*.top') + glob.glob('drawings/**/*.xvi', recursive=True)
    hits = []
    for f in files:
        try:
            pos = _sketch(f, view).positions()
        except Exception:
            continue
        n = sum(s in pos for s in stations)
        if n:
            hits.append((n, f))
    return [f for n, f in sorted(hits, reverse=True)]


def _similarity(src, dst):
    import numpy as np
    A = np.array(src, float); B = np.array(dst, float)
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(a.T @ b); R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1; R = (U @ Vt).T
    s = S.sum() / (a ** 2).sum()
    return lambda p: tuple(s * R @ (np.array(p, float) - ma) + mb)


def scrap_objects(th2, scrap):
    t = open(th2, encoding='utf-8').read().replace('\r\n', '\n')
    m = re.search(r'^scrap %s\b[^\n]*\n(.*?)^endscrap' % re.escape(scrap), t, re.S | re.M)
    return parse_scrap(m.group(1))


def stations_of(objs):
    st = {}
    for o in objs:
        m = re.match(r'point (\S+) (\S+) station .*-name (\S+)', o.head) if o.kind == 'point' else None
        if m:
            st[m.group(3).split('@')[0]] = (float(m.group(1)), float(m.group(2)))
    return st


def sketch_to_th2(sketch, objs, view='plan'):
    """A transform from the sketch's metres to the scrap's th2 units, fitted
    on the stations they share."""
    pos = _sketch(sketch, view).positions(); st = stations_of(objs)
    common = [n for n in st if n in pos]
    return _similarity([pos[n] for n in common], [st[n] for n in common])


# -- pictures --------------------------------------------------------------------------

def sketch_panel(stations, view='plan', pad=4):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from PIL import Image
    files = sketches_for(stations, view)
    main, layers = None, []
    for f in files:
        sk = _sketch(f, view); pos = sk.positions(); off = (0.0, 0.0)
        if main is not None:
            common = [n for n in pos if n in main]
            if not common:
                continue
            off = (main[common[0]][0] - pos[common[0]][0], main[common[0]][1] - pos[common[0]][1])
        P = {n: (p[0] + off[0], p[1] + off[1]) for n, p in pos.items()}
        main = dict(P) if main is None else {**P, **main}
        layers.append((f, sk, P, off))
    xs = [main[s][0] for s in stations if s in main]; ys = [main[s][1] for s in stations if s in main]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    fig, ax = plt.subplots(figsize=(7, 7 * (y1 - y0) / max(x1 - x0, 1e-6)), dpi=110)
    for f, sk, P, off in layers:
        for col, pts in sk.lines:
            q = [(p[0] + off[0], p[1] + off[1]) for p in pts]
            if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in q):
                ax.plot([p[0] for p in q], [p[1] for p in q], color=COLOURS.get(col, 'm'), lw=1.4)
        for leg in sk.legs():
            a, b = leg[0], leg[1]
            if a in P and b in P:
                ax.plot([P[a][0], P[b][0]], [P[a][1], P[b][1]], color='#dd0000', lw=0.6, ls='--')
    for n, p in main.items():
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            ax.plot(*p, '+', color='#c00060', ms=7)
            ax.text(p[0] + 0.15, p[1] + 0.15, n, fontsize=8, color='#c00060')
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title('Original sketch (%s): %s' % (view, ', '.join(os.path.basename(f) for f, *_ in layers)), fontsize=8)
    ax.legend([Line2D([], [], color=COLOURS[c]) for c in ('BLACK', 'BROWN', 'GRAY', 'BLUE', 'GREEN', 'ORANGE')]
              + [Line2D([], [], color='#dd0000', ls='--')],
              ['black', 'brown', 'grey', 'blue', 'green', 'orange', 'survey leg'], fontsize=6, loc='lower right', ncol=4)
    buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
    return Image.open(buf).convert('RGB')


_PDFMAP = {}


def pdf_rect(stations, pdf=PLAN, pad=15):
    """Where the stations are on a plan PDF, fitted on the drawing's labels."""
    import numpy as np
    import pymupdf
    if pdf not in _PDFMAP:
        lay = register.Layout(LAYOUT)
        def where(n):
            p = lay.find(n)
            return p[0] if p else None
        page = pymupdf.open(pdf)[0]; pairs = []
        for f in glob.glob('*.th2'):
            t = open(f, encoding='utf-8').read().replace('\r\n', '\n')
            for m in re.finditer(r'^scrap (\S+)[^\n]*\n(.*?)^endscrap', t, re.S | re.M):
                body = m.group(2)
                if '-projection plan' not in t[m.start():m.start(2)]:
                    continue
                st = [(n, p) for n, p in stations_of(parse_scrap(body)).items() if where(n) is not None]
                if len(st) < 2:
                    continue
                T = _similarity([p for n, p in st], [where(n) for n, p in st])
                for l in body.split('\n'):
                    mm = re.match(r'point (\S+) (\S+) label .*-text "([^"]+)"', l)
                    words = re.sub(r'<[^>]+>', ' ', mm.group(3)).split() if mm else []
                    hits = page.search_for(' '.join(words[:2])) if words else []
                    if len(hits) == 1:
                        r = hits[0]
                        pairs.append((T((float(mm.group(1)), float(mm.group(2)))), ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)))
        src = np.array([p for p, _ in pairs]); dst = np.array([q for _, q in pairs])
        A = np.zeros((2 * len(src), 3)); y = np.zeros(2 * len(src))
        A[0::2, 0] = 1; A[0::2, 2] = src[:, 0]; y[0::2] = dst[:, 0]
        A[1::2, 1] = 1; A[1::2, 2] = -src[:, 1]; y[1::2] = dst[:, 1]
        _PDFMAP[pdf] = (np.linalg.lstsq(A, y, rcond=None)[0], where)
    (a, b, s), where = _PDFMAP[pdf]
    ps = [where(n) for n in stations if where(n) is not None]
    xs = [a + s * p[0] for p in ps]; ys = [b - s * p[1] for p in ps]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def drawing_panel(pdf, clip, rings=(), dpi=220):
    import pymupdf
    from PIL import Image, ImageDraw
    page = pymupdf.open(pdf)[0]; c = pymupdf.Rect(*clip)
    pix = page.get_pixmap(dpi=dpi, clip=c)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    d = ImageDraw.Draw(im); k = dpi / 72
    for x0, y0, x1, y1 in rings:
        d.ellipse([(x0 - c.x0) * k, (y0 - c.y0) * k, (x1 - c.x0) * k, (y1 - c.y0) * k], outline=(220, 0, 0), width=5)
    return im


def show(out, stations, title='', before=None, after=PLAN, ring=(), pad=15, view='plan'):
    """sketch | drawing, or sketch | before | after, one PNG."""
    from PIL import Image, ImageDraw, ImageFont
    clip = pdf_rect(stations, after, pad)
    rings = [pdf_rect(ring, after, 6)] if ring else []
    panels = [(sketch_panel(stations, view), '')]
    if before:
        panels.append((drawing_panel(before, clip, rings), 'Before'))
    panels.append((drawing_panel(after, clip, rings), 'After' if before else 'Drawing (station names shown)'))
    h = 680
    panels = [(p.resize((int(p.width * h / p.height), h)), lab) for p, lab in panels]
    W = sum(p.width for p, _ in panels) + 30 * (len(panels) - 1)
    im = Image.new('RGB', (W, h + 50), 'white'); d = ImageDraw.Draw(im)
    try:
        big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
        bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except OSError:
        big = bold = None
    d.text((10, 10), title, fill=(0, 0, 0), font=big)
    x = 0
    for p, lab in panels:
        im.paste(p, (x, 50))
        if lab:
            d.text((x + 10, 52), lab, fill=(200, 0, 0), font=bold)
        x += p.width + 30
        if x < W:
            d.line([(x - 15, 50), (x - 15, h + 50)], fill=(150, 150, 150), width=2)
    im.save(out)
    return out


# -- building --------------------------------------------------------------------------

def build(config='swildons.thconfig', out=PLAN, therion=('therion',)):
    """The plan with station names, from the sheet's own config."""
    s = open(config, encoding='utf-8').read()
    s = s[:s.index('\nexport ')] if '\nexport ' in s else s
    s = re.sub(r'^\s*symbol-hide point station.*$', '', s, flags=re.M)
    s = re.sub(r'^(layout plan-sheet\n)', r'\1  debug station-names\n', s, flags=re.M)
    s += f'\nexport map -projection plan -layout plan-sheet -o {out}\n'
    tmp = 'review-plan.thconfig'
    open(tmp, 'w', encoding='utf-8').write(s)
    try:
        subprocess.run(list(therion) + [tmp], check=True, stdout=subprocess.DEVNULL)
    finally:
        os.remove(tmp)
    _PDFMAP.pop(out, None)
    return out


# -- checks ----------------------------------------------------------------------------

def outline_lines(objs):
    return [o for o in objs if o.kind == 'line' and len(o.segments()) > 1 and '-close on' not in o.head
            and ('-outline out' in o.head or (o.head.startswith('line wall') and '-outline' not in o.head))]


def check(th2, scraps=None):
    """[(scrap, lines in the outline, valid, MetaPost turning number)]."""
    from .smooth import mp_turning, ring_ok
    t = open(th2, encoding='utf-8').read().replace('\r\n', '\n')
    res = []
    for m in re.finditer(r'^scrap (\S+)[^\n]*\n(.*?)^endscrap', t, re.S | re.M):
        if scraps and m.group(1) not in scraps:
            continue
        out = outline_lines(parse_scrap(m.group(2)))
        ol = [bezier_points(o.segments(), 20) for o in out]
        for ring in therion_rings(ol):
            pts = [p for i, r in ring for p in (ol[i][::-1] if r else ol[i])]
            segs = [reverse_segments(out[i].segments()) if r else out[i].segments() for i, r in ring]
            res.append((m.group(1), len(ring), ring_ok(pts)[0], mp_turning(segs)))
    return res


def gaps(th2, scrap, minlen=0.3, sketch=None):
    """[(metres, nearest station, a, b, share of the gap the sketch walls run along)]."""
    objs = scrap_objects(th2, scrap); st = stations_of(objs)
    out = outline_lines(objs)
    ol = [bezier_points(o.segments(), 8) for o in out]
    walls = []
    if sketch is None:
        found = sketches_for(list(st))
        sketch = found[0] if found else None
    if sketch:
        T = sketch_to_th2(sketch, objs)
        walls = [LineString([T(p) for p in pts]) for c, pts in _sketch(sketch).lines if c == 'BLACK' and len(pts) > 1]
    res = []
    for ring in therion_rings(ol):
        seq = [ol[i][::-1] if r else ol[i] for i, r in ring]
        for k in range(len(seq)):
            a, b = seq[k][-1], seq[(k + 1) % len(seq)][0]
            d = math.dist(a, b) / K
            if d <= minlen:
                continue
            ab = LineString([a, b])
            samples = [ab.interpolate(j / 10, normalized=True) for j in range(1, 10)]
            cov = sum(any(w.distance(q) < 0.3 * K for w in walls) for q in samples) / 9 if walls else 0
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            near = min(st, key=lambda n: math.dist(st[n], mid)) if st else ''
            res.append((round(d, 2), near, tuple(round(v) for v in a), tuple(round(v) for v in b), cov))
    return res


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog='review')
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build'); b.add_argument('--config', default='swildons.thconfig')
    b.add_argument('--therion', default='therion', help='the command that runs therion (e.g. a docker wrapper)')
    s = sub.add_parser('show'); s.add_argument('out'); s.add_argument('stations', nargs='+')
    s.add_argument('--title', default=''); s.add_argument('--before'); s.add_argument('--after', default=PLAN)
    s.add_argument('--ring', nargs='*', default=()); s.add_argument('--pad', type=float, default=15)
    g = sub.add_parser('gaps'); g.add_argument('th2'); g.add_argument('scraps', nargs='+')
    c = sub.add_parser('check'); c.add_argument('th2'); c.add_argument('scraps', nargs='*')
    a = ap.parse_args(argv)
    if a.cmd == 'build':
        print(build(a.config, therion=a.therion.split()))
    elif a.cmd == 'show':
        print(show(a.out, a.stations, a.title, a.before, a.after, a.ring, a.pad))
    elif a.cmd == 'gaps':
        for s_ in a.scraps:
            for d, near, p, q, cov in gaps(a.th2, s_):
                print(f'{s_}: {d:.2f} m near {near}: sketch wall along {cov:.0%}  {p} -> {q}')
    else:
        for s_, n, ok, tn in check(a.th2, a.scraps or None):
            flag = '' if ok and tn != 0 else '   <- ' + ('crosses itself' if not ok else 'MetaPost will warn')
            print(f'{s_}: {n} lines, valid {ok}, turning {tn}{flag}')
