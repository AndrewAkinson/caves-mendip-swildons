"""Build route cards: python3 -m tools.routes [route.toml ...]

Needs, in output/: Swildons.sql (from the main build, swildons.thconfig) and
routes-base.svg (from tools/routes/routes.thconfig). Writes
output/routes/<name>.html and, if Chromium is found, <name>.pdf, plus
output/routes/index.html.
"""
import argparse
import datetime
import glob
import math
import os
import re
import shutil
import subprocess
import sys
import tomllib

from . import render as R
from .analyse import Route, trim_spurs, compass
from .basemap import BaseMap
from .survey import Survey

OUT = 'output/routes'


def slug(path):
    return re.sub(r'\.toml$', '', os.path.basename(path))


def group_decisions(route, decs, near=6.0):
    """Decisions at the same place (a route passing a junction twice) become one
    numbered close-up with a line of directions per pass."""
    groups = []
    for i, alts in decs:
        p = route.xy(i)
        for g in groups:
            if math.dist(g['xy'], p) < near:
                last_i = g['passes'][-1][0]
                if route.chain[i] - route.chain[last_i] < 15:
                    # the same junction, spread over a few stations: one decision
                    g['passes'][-1] = (last_i, g['passes'][-1][1] + alts)
                else:
                    g['passes'].append((i, alts))
                break
        else:
            groups.append({'xy': p, 'passes': [(i, alts)]})
    for n, g in enumerate(groups, 1):
        g['num'] = n
    return groups


def svg_route(base, route):
    return R.chaikin([base.to_svg(route.xy(i)) for i in range(len(route.nodes))], 2)


def card(route_def, s, base, path):
    nodes = trim_spurs(s.route(route_def['waypoints'], route_def.get('avoid', ())),
                       keep=[s.node(w) for w in route_def.get('visit', [])])
    route = Route(s, nodes)
    st = route.stats()
    places = route.places()
    decs = route.decisions(min_branch=route_def.get('min_branch', 4.0))
    groups = group_decisions(route, decs)
    # Your own settings for decisions: skip one, zoom its close-up, give it a
    # title, words or a photo, or add a point of interest where there's no
    # junction. [[note]] is the older name for the same thing.
    base_dir = route_def.get('_dir', 'routes')
    for d in route_def.get('decision', []) + route_def.get('note', []):
        k = s.node(d['at'])
        p = s.pos[k][:2]
        g = next((g for g in groups if any(route.nodes[i] == k for i, _ in g['passes'])), None)
        if g is None:
            near = min(groups, key=lambda g: math.dist(g['xy'], p), default=None)
            if near and math.dist(near['xy'], p) < 8:
                g = near
        if d.get('skip'):
            if g is None:
                print(f"  warning: no decision at {d['at']} to skip")
            else:
                groups.remove(g)
            continue
        if g is None:
            if not (d.get('text') or d.get('photo') or d.get('directions')):
                print(f"  warning: no decision at {d['at']}")
                continue
            i = route.nodes.index(k) if k in route.nodes else min(
                range(len(route.nodes)), key=lambda j: math.dist(route.xy(j), p))
            g = {'xy': p, 'passes': [(i, [])], 'info': True}
            groups.append(g)
        if d.get('text'):
            g.setdefault('notes', []).append(d['text'])
        for key in ('title', 'width', 'directions', 'caption'):
            if d.get(key):
                g[key] = d[key]
        if d.get('photo'):
            g['photo'] = R.photo_uri(os.path.join(base_dir, d['photo']))
    groups.sort(key=lambda g: min(route.chain[i] for i, _ in g['passes']))
    for n, g in enumerate(groups, 1):
        g['num'] = n

    pts = svg_route(base, route)
    xs = [route.xy(i)[0] for i in range(len(nodes))]
    ys = [route.xy(i)[1] for i in range(len(nodes))]
    aspect = (max(xs) - min(xs) + 24) / (max(ys) - min(ys) + 24)
    wide = aspect > 2.4
    # Two layouts. Tall: overview left, close-ups in a column on the right.
    # Wide (a long thin route, like the streamway): overview strip across the
    # sheet, close-ups in rows underneath.
    if wide:
        L = dict(ov=(400, 86), prof=(400, 32), cols=6, pw=64, area=86, maxn=12, chars=52)
    else:
        L = dict(ov=(252, 168), prof=(252, 44), cols=2, pw=68, area=194, maxn=12, chars=58)

    # ---- overview ---------------------------------------------------------------
    ov_w, ov_h = L['ov']
    view = R.fit_view(base, list(zip(xs, ys)), ov_w, ov_h, margin_m=12)
    lane = 0.45
    o = [R.route_layer(view, pts, 1.0 if not wide else 0.9, 10, lane)]
    for g in groups:
        o.append(f'<a href="#d{g["num"]}">' + R.badge(view, base.to_svg(g['xy']), g['num'], 2.4 if not wide else 2.1) + '</a>')
    start = base.to_svg(route.xy(0))
    end = base.to_svg(route.xy(len(nodes) - 1))
    o.append(R.flag(view, start, 'start'))
    if not st['loop']:
        o.append(R.flag(view, end, 'finish'))
    ov_svg = view.svg("".join(o)).replace(f'width="{ov_w}mm" height="{ov_h}mm"', 'width="100%" height="100%"')
    overview = f'<div class="overview" style="--ar:{ov_w}/{ov_h}">{ov_svg}{R.NORTH}{R.scalebar(view)}</div>'

    # ---- where in the cave: the whole drawn cave, the route and this map's frame ----
    drawn = [s.pos[k][:2] for k in s.pos if s.adj[k]]
    allx = sorted(p[0] for p in drawn)
    ally = sorted(p[1] for p in drawn)
    # the drawn plan runs from the entrance to Sump 1: use its stations' middle 98%
    lx0, lx1 = allx[int(len(allx) * 0.01)], allx[int(len(allx) * 0.99) - 1]
    ly0, ly1 = ally[int(len(ally) * 0.01)], ally[int(len(ally) * 0.99) - 1]
    loc_w, loc_h = 92, 30
    lv = R.fit_view(base, [(lx0, ly0), (lx1, ly1)], loc_w, loc_h, margin_m=8)
    x, y, W, H = view.vb
    loc = (lv.svg(f'<path d="{R.path_d(pts)}" fill="none" stroke="{R.ROUTE}" stroke-width="{lv.k * 1.1:.2f}" '
                  f'stroke-linejoin="round" stroke-linecap="round"/>'
                  f'<rect x="{x:.1f}" y="{y:.1f}" width="{W:.1f}" height="{H:.1f}" fill="none" stroke="{R.INK}" '
                  f'stroke-width="{lv.k * 0.35:.2f}" stroke-dasharray="{lv.k * 1.2:.2f} {lv.k * 0.8:.2f}"/>', 'locator'))
    locator = f'<div class="locator">{loc}<span>Where in the cave</span></div>'

    # ---- kit and tackle: from the route file, and the steep bits from the survey ----
    tackle = route_def.get('tackle', [])
    kit = route_def.get('kit', [])
    drops = route.drops()
    kit_html = ''
    if tackle or kit or drops:
        rows_ = []
        if tackle or drops:
            rows_.append('<div><b>Tackle</b> ' + (R.esc('; '.join(tackle)) if tackle else
                         '<span class="todo">not listed yet: ask someone who knows the route</span>') + '</div>')
        if kit:
            rows_.append('<div><b>Kit</b> ' + R.esc('; '.join(kit)) + '</div>')
        if drops:
            words = [f"{p[0].upper() + p[1:] if p else 'A pitch'}, about {abs(dz):.0f} m {'down' if dz < 0 else 'up'} "
                     f"({d:.0f} m along)" for d, dz, p in drops]
            rows_.append('<div><b>Steep on the survey</b> ' + R.esc('; '.join(words)) + '</div>')
        kit_html = '<div class="kit"><h2>Kit and tackle</h2>' + ''.join(rows_) + '</div>'
    kit_mm = 0 if not kit_html else 8 + 3.6 * sum(
        math.ceil(len(t) / (L['chars'] * (2.1 if not wide else 6.2))) for t in ['; '.join(tackle) or 'x' * 60, '; '.join(kit), ' ' * (len(drops) * 45)] if t)
    L['area'] -= kit_mm

    # ---- close-ups ----------------------------------------------------------------
    shown = groups[:L['maxn']]
    for g in shown:
        first = route.nodes[g['passes'][0][0]]
        g['survey_notes'] = [t for t in s.notes_near(first, 6)]
        g['text'] = ([g['directions']] if g.get('directions') else
                     [route.instruction(i, alts) for i, alts in g['passes'] if not g.get('info')]) \
            + g.get('notes', []) + g['survey_notes'] + ([g['caption']] if g.get('caption') else [])

    def text_mm(g):
        lines = sum(math.ceil((len(t) + 14) / L['chars']) for t in g["text"])
        return 7.5 + 3.5 * lines
    # as many close-ups as fit with maps at least 18 mm high; the rest go in a list
    while True:
        rows = [shown[k:k + L['cols']] for k in range(0, len(shown), L['cols'])]
        rest = groups[len(shown):]
        rest_mm = sum(3.5 * math.ceil((len(route.instruction(*g['passes'][0])) + 4) / (L['chars'] * 2.1)) for g in rest)
        avail = L['area'] - rest_mm - 2.6 * len(rows) - sum(max(text_mm(g) for g in r) for r in rows)
        ph = avail / max(1, sum(2 if any(g.get('photo') for g in r) else 1 for r in rows))
        if ph >= 18 or len(shown) <= 2:
            break
        shown = shown[:-1]
    pw = L['pw']
    ph = max(16, min(48, ph))
    L['maxn'] = len(shown)
    pulls = []
    for g in shown:
        cv = R.View(base, g['xy'], g.get('width', 24 * pw / 72), pw, round(ph))
        layer = [R.route_layer(cv, pts, 1.0, 7, lane)]
        crosses = []          # (position, label) already drawn in this close-up
        dirs = []             # (junction, bearing) of the ways already crossed
        lines = []
        for i, alts in g['passes']:
            node = route.nodes[i]
            for b, Lb, lead, v in alts:
                if Lb >= 99:
                    continue
                a = s.pos[node][:2]
                q = s.pos[v][:2]
                d = math.dist(a, q) or 1
                t = min(3.5, d) / d
                xp = base.to_svg((a[0] + (q[0] - a[0]) * t, a[1] + (q[1] - a[1]) * t))
                # one cross where two side passages start together, and each
                # place named once per close-up
                if any(math.dist(xp, c) < cv.k * 2.5 for c, _, _ in crosses) or \
                        any(n0 == node and abs((b - b0 + 180) % 360 - 180) < 35 for n0, b0 in dirs):
                    continue
                dirs.append((node, b))
                label, side = None, 'right'
                if lead and not any(l == lead for _, l, _ in crosses):
                    text = f"to {lead}"
                    w, h = cv.k * len(text) * 1.25, cv.k * 3.2      # label size, roughly
                    boxes = [b for _, _, b in crosses if b]
                    for sd in ('right', 'left'):
                        x0 = xp[0] + cv.k * 2 if sd == 'right' else xp[0] - cv.k * 2 - w
                        box = (x0, xp[1] - h / 2, x0 + w, xp[1] + h / 2)
                        if not any(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in boxes):
                            label, side = text, sd
                            break
                crosses.append((xp, lead, box if label else None))
                layer.append(R.cross(cv, xp, label, side))
            # the way to go: an arrowhead a few metres on
            ahead = [base.to_svg(route.point_at(route.chain[i] + d)[:2]) for d in (2.5, 4.0)]
            ahead = R.offset(ahead, cv.k * lane)
            layer.append(R.arrowhead(cv, ahead, 1.3))
            if not g.get('info') and not g.get('directions'):
                pass_label = ''
                if len(g['passes']) > 1:
                    pass_label = f'<span class="pass">{["1st", "2nd", "3rd", "4th"][min(3, g["passes"].index((i, alts)))]} time:</span> '
                lines.append(f'<div>{pass_label}{R.esc(route.instruction(i, alts))}</div>')
        layer.append(R.badge(cv, base.to_svg(g['xy']), g['num'], 2.6))
        first = route.nodes[g['passes'][0][0]]
        where = g.get('title') or s.place_name(first, 10)
        if not where:
            near = s.place_name(first, 40)
            where = f"Near {near}" if near else "Junction"
        dists = ", ".join(f"{route.chain[i]:.0f} m" for i, _ in g['passes'])
        stn = s.name(first).split('@')[0]
        if g.get('directions'):
            lines.append(f'<div>{R.esc(g["directions"])}</div>')
        notes_html = "".join(f'<div class="note">{R.esc(t)}</div>' for t in g.get('notes', []))
        notes_html += "".join(f'<div class="note">On the survey: “{R.esc(t)}”</div>' for t in g['survey_notes'])
        photo = ''
        if g.get('photo'):
            cap = f'<figcaption>{R.esc(g["caption"])}</figcaption>' if g.get('caption') else ''
            photo = f'<figure class="photo" style="--ph:{ph:.1f}mm"><img src="{g["photo"]}" alt="{R.esc(g.get("caption", where))}">{cap}</figure>'
        pulls.append(f'<div class="pull" id="d{g["num"]}" style="--ar:{pw}/{max(20, round(ph))}">{cv.svg("".join(layer))}{photo}<div class="txt"><div class="head">'
                     f'<span class="num">{g["num"]}</span><span class="where">{R.esc(where)}</span>'
                     f'<span class="dist">{dists} · stn {R.esc(stn)}</span></div>{"".join(lines)}{notes_html}</div></div>')
    more = ''
    if len(groups) > L['maxn']:
        more = '<div class="more">' + " ".join(
            f'<b>{g["num"]}</b> {R.esc(route.instruction(*g["passes"][0]))}' for g in groups[L['maxn']:]) + '</div>'

    # ---- profile, header, page --------------------------------------------------------
    prof = R.profile_svg(route, [(g['num'], route.chain[g['passes'][0][0]]) for g in groups], places, *L['prof'])
    via = [t for _, t in places]
    via = [t for k, t in enumerate(via) if t not in via[:k]]
    stats = [(f"{st['length']:.0f} m", "distance"),
             ((f"{st['depth']:.0f} m", "deepest, below the start") if st['depth'] >= st['high'] - st['start_z']
              else (f"{st['high'] - st['start_z']:.0f} m", "highest, above the start")),
             (f"{st['down']:.0f}↓ {st['up']:.0f}↑", "metres down / up"),
             (f"{len(groups)}", "decisions to make")]
    num = re.match(r'(\d+)', slug(path))
    date = datetime.date.today().isoformat()
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{R.esc(route_def["title"])} · Swildons Hole route card</title>
{R.FONTS}<style>{R.CSS}</style></head><body>
<svg class="basemap" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{base.inner.replace(' id="root"', ' id="basemap-root"', 1)}</svg>
<div class="sheet{' wide' if wide else ''}">
<header><div>
  <div class="kicker">Swildons Hole · route {num.group(1) if num else ''}{' · way out' if str(path).endswith('-out') else ''}</div>
  <h1>{R.esc(route_def["title"])}</h1>
  <div class="subtitle">{R.esc(route_def.get("subtitle", ""))}</div>
  <div class="desc">{R.esc(" ".join(route_def.get("description", "").split()))}</div>
  <div class="via">Via {R.esc(" → ".join(via))}{" and back" if st["loop"] else ""}</div>
</div><div class="side">{locator}<div class="stats">{"".join(f'<div class="stat"><b>{a}</b><span>{b}</span></div>' for a, b in stats)}</div></div></header>
{overview}
<aside>{kit_html}<h2>At each decision</h2>{"".join(pulls)}{more}</aside>
<div class="profilebox">{prof}</div>
<footer>{R.LEGEND}<div class="credit"><span class="draft">Draft:</span> directions are worked out automatically from the survey, not checked underground.
Survey: the Swildons resurvey (Paul 'Footleg' Fretwell and team, 2012–2019) and W. I. Stanton. Made {date}.</div></footer>
</div></body></html>'''
    return page, route, st


def chromium():
    for c in (os.environ.get('CHROMIUM'), shutil.which('chromium'), shutil.which('chromium-browser'),
              shutil.which('google-chrome'), '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'):
        if c and os.path.exists(c):
            return c
    for c in sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome')):
        return c
    return None


def to_pdf(html_path):
    exe = chromium()
    if not exe:
        print("  (no Chromium: HTML only)")
        return None
    pdf = html_path[:-5] + '.pdf'
    subprocess.run([exe, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    '--virtual-time-budget=15000', f'--print-to-pdf={os.path.abspath(pdf)}',
                    'file://' + os.path.abspath(html_path)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return pdf


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python3 -m tools.routes', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('routes', nargs='*', help='route definitions (default routes/*.toml)')
    ap.add_argument('--sql', default='output/Swildons.sql')
    ap.add_argument('--base', default='output/routes-base.svg')
    ap.add_argument('--no-pdf', action='store_true')
    a = ap.parse_args(argv)
    s = Survey(a.sql)
    s.load_labels()
    base = BaseMap(a.base, s)
    os.makedirs(OUT, exist_ok=True)
    index = []
    for path in a.routes or sorted(glob.glob('routes/*.toml')):
        rd = tomllib.load(open(path, 'rb'))
        rd['_dir'] = os.path.dirname(os.path.abspath(path))
        cards = [(slug(path), rd)]
        if rd.get('way_out'):
            # the same route backwards, with its own directions
            back = dict(rd, waypoints=rd['waypoints'][::-1], note=[], decision=rd.get('way_out_decision', []),
                        title=rd.get('way_out_title', 'The way out: ' + rd['title']),
                        subtitle=rd.get('way_out_subtitle', 'The same route in reverse, back to the start'),
                        description=rd.get('way_out_description', rd.get('description', '')))
            cards.append((slug(path) + '-out', back))
        for name, d in cards:
            page, route, st = card(d, s, base, name)
            out = os.path.join(OUT, name + '.html')
            open(out, 'w').write(page)
            pdf = None if a.no_pdf else to_pdf(out)
            print(f"{out}: {st['length']:.0f} m, {st['depth']:.0f} m deep" + (f", {pdf}" if pdf else ""))
            index.append((name, d, st, pdf))
    items = "".join(
        f'<li><a href="{n}.html"><b>{R.esc(rd["title"])}</b></a><br>'
        f'<span>{R.esc(rd.get("subtitle", ""))} · {st["length"]:.0f} m</span><br>'
        f'<a href="{n}.html">On screen or phone</a>' + (f' · <a href="{n}.pdf">PDF to print, A3</a>' if pdf else '') + '</li>'
        for n, rd, st, pdf in index)
    open(os.path.join(OUT, 'index.html'), 'w').write(
        f'<!doctype html><meta charset="utf-8"><title>Swildons Hole route cards</title>'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<style>body{{font-family:Arial,sans-serif;max-width:46em;margin:2em auto;padding:0 1em;line-height:1.45}}'
        f'li{{margin:.8em 0}}span{{color:#555}}</style><h1>Swildons Hole route cards</h1>'
        f'<p>Routes through the cave, with the way to go at each junction. Drafts: worked out from the survey, '
        f'not yet checked underground.</p><ol>{items}</ol>')


if __name__ == '__main__':
    main()
