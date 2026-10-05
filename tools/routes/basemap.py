"""The drawn survey as the background of a route card.

Therion renders the plan to SVG (tools/routes/thconfig-routes). To draw a
route on top of it, the survey's coordinates have to be matched to the
SVG's. Therion morphs every drawing onto its stations, so the render
includes a tiny scrap, RouteReg (reg.th2), with three marks in an
unusual colour exactly at three stations far apart. Finding those marks
in the SVG gives the transform from survey metres to SVG units; the
marks are then removed.
"""
import itertools
import math
import re
import xml.etree.ElementTree as ET

REG_COLOUR = '#1f74c9'
REG_STATIONS = ['1.0@ZigZags', '24.33@TratmansToSump1', '25.12@RollingThunder']
SVG = '{http://www.w3.org/2000/svg}'


def _parse_transform(t):
    """3x2 affine (a, b, c, d, e, f) from an SVG transform attribute."""
    M = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.split(r'[\s,]+', args.strip()) if x]
        if name == 'matrix':
            N = tuple(v)
        elif name == 'translate':
            N = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            N = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        else:
            continue
        M = _mul(M, N)
    return M


def _mul(M, N):
    a, b, c, d, e, f = M
    A, B, C, D, E, F = N
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def _apply(M, p):
    a, b, c, d, e, f = M
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def _affine(src, dst):
    """Exact affine transform taking 3 source points to 3 destination points."""
    (x1, y1), (x2, y2), (x3, y3) = src
    det = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
    if abs(det) < 1e-9:
        return None
    out = []
    for k in range(2):
        u1, u2, u3 = (dst[0][k], dst[1][k], dst[2][k])
        a = (u1 * (y2 - y3) + u2 * (y3 - y1) + u3 * (y1 - y2)) / det
        b = (u1 * (x3 - x2) + u2 * (x1 - x3) + u3 * (x2 - x1)) / det
        c = (u1 * (x2 * y3 - x3 * y2) + u2 * (x3 * y1 - x1 * y3) + u3 * (x1 * y2 - x2 * y1)) / det
        out.append((a, b, c))
    return out


class BaseMap:
    def __init__(self, svg_path, survey):
        txt = open(svg_path, encoding='utf-8').read()
        self.viewbox = [float(v) for v in re.search(r'viewBox="([^"]+)"', txt).group(1).split()]
        marks = self._marks(txt)
        if len(marks) != 3:
            raise ValueError(f"expected 3 registration marks in {svg_path}, found {len(marks)}")
        src = [survey.pos[survey.node(n)][:2] for n in REG_STATIONS]
        best = None
        for perm in itertools.permutations(marks):
            A = _affine(src, list(perm))
            if A is None:
                continue
            (a, b, _), (c, d, _) = A
            s1, s2 = math.hypot(a, c), math.hypot(b, d)
            err = abs(s1 - s2) / max(s1, s2) + abs(a * b + c * d) / (s1 * s2)
            if best is None or err < best[0]:
                best = (err, A)
        if best[0] > 0.01:
            raise ValueError(f"registration marks don't fit the stations (error {best[0]:.3f})")
        self.A = best[1]
        self.units_per_m = math.hypot(self.A[0][0], self.A[1][0])
        # the drawing without the marks, ready to embed
        body = re.sub(r'<path fill="' + REG_COLOUR + r'"[^>]*/>\s*', '', txt)
        body = re.sub(r'<\?xml[^>]*>|<!DOCTYPE[^>]*>|<!--.*?-->', '', body, flags=re.S)
        inner = re.search(r'<svg[^>]*>(.*)</svg>', body, re.S).group(1)
        self.inner = inner

    def _marks(self, txt):
        root = ET.fromstring(re.sub(r'<!DOCTYPE[^>]*>', '', txt))
        found = []

        def walk(el, M):
            M = _mul(M, _parse_transform(el.get('transform')))
            if el.tag == SVG + 'path' and (el.get('fill') or '').lower() == REG_COLOUR:
                nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', el.get('d'))]
                pts = list(zip(nums[0::2], nums[1::2]))
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                found.append(_apply(M, ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)))
            for ch in el:
                walk(ch, M)
        walk(root, (1, 0, 0, 1, 0, 0))
        return found

    def to_svg(self, p):
        """Survey (x, y) metres -> SVG units."""
        (a, b, c), (d, e, f) = self.A
        return (a * p[0] + b * p[1] + c, d * p[0] + e * p[1] + f)
