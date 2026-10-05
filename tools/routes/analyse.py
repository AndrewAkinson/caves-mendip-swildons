"""What a caver needs to know along a route: where the decisions are, which
way to go at each, how far, how deep, and what passages it goes through.

All of this is worked out from the survey graph. A route definition can
override or add to any instruction.
"""
import math

# Which way to go, by how far the passage turns (degrees, + is right)
TURNS = [(25, "carry straight on"), (60, "bear {side}"), (135, "turn {side}"), (181, "turn sharply back {side}")]


def trim_spurs(path, keep=()):
    """Remove out-and-back detours (A B A) that only happened because a
    waypoint was in a side passage, unless that side passage is the point."""
    keep = set(keep)
    changed = True
    while changed:
        changed = False
        for i in range(1, len(path) - 1):
            if path[i - 1] == path[i + 1] and path[i] not in keep:
                path = path[:i] + path[i + 2:]
                changed = True
                break
    return path


def bearing(a, b):
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def compass(deg):
    pts = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west']
    return pts[int(((deg % 360) + 22.5) // 45) % 8]


class Route:
    def __init__(self, survey, nodes):
        self.s = survey
        self.nodes = nodes
        self.chain = [0.0]          # distance along the route at each node
        for a, b in zip(nodes, nodes[1:]):
            self.chain.append(self.chain[-1] + survey.dist3(a, b))
        self.length = self.chain[-1]

    def xy(self, i):
        return self.s.pos[self.nodes[i]][:2]

    def z(self, i):
        return self.s.pos[self.nodes[i]][2]

    def point_at(self, d):
        """(x, y, z) at distance d along the route."""
        d = max(0.0, min(self.length, d))
        for i in range(len(self.nodes) - 1):
            if self.chain[i + 1] >= d:
                L = self.chain[i + 1] - self.chain[i] or 1
                t = (d - self.chain[i]) / L
                a, b = self.s.pos[self.nodes[i]], self.s.pos[self.nodes[i + 1]]
                return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
        return self.s.pos[self.nodes[-1]]

    def stats(self):
        zs = [self.z(i) for i in range(len(self.nodes))]
        down = sum(max(0, a - b) for a, b in zip(zs, zs[1:]))
        up = sum(max(0, b - a) for a, b in zip(zs, zs[1:]))
        return {'length': self.length, 'start_z': zs[0], 'low': min(zs), 'high': max(zs),
                'depth': zs[0] - min(zs), 'down': down, 'up': up,
                'loop': self.nodes[0] == self.nodes[-1]}

    def places(self, within=7.0):
        """Named places along the route, in order: [(distance, name)]."""
        out = []
        for i, n in enumerate(self.nodes):
            t = self.s.place_name(n, within)
            if t and t.startswith('('):
                continue
            if t and not (out and out[-1][1] == t):
                out.append((self.chain[i], t))
        # a name seen again within 25 m is the same place
        res = []
        for d, t in out:
            if not any(t == t2 and d - d2 < 25 for d2, t2 in res):
                res.append((d, t))
        return res

    # -- decisions -----------------------------------------------------------------
    def _branch(self, start, via, onroute, cap=30.0):
        """Explore a side passage from `start` through `via`, not crossing the route.
        Returns (passage length explored, nodes reached)."""
        seen = {start, via}
        total = self.s.adj[start][via]
        frontier = [via]
        reached = [via]
        while frontier and total < cap:
            u = frontier.pop()
            for v, c in self.s.adj[u].items():
                if v in seen or v in onroute:
                    continue
                seen.add(v)
                total += c
                frontier.append(v)
                reached.append(v)
        return total, reached

    def _lead_to(self, reached, start):
        """The nearest named place a side passage leads to."""
        best = None
        for n in reached:
            t = self.s.place_name(n, 6)
            if t and not t.startswith('('):
                d = self.s.dist3(start, n)
                if best is None or d < best[0]:
                    best = (d, t)
        return best[1] if best else None

    def _dir_at(self, i, sign, reach=4.0):
        """Plan bearing of the route leaving node i forwards (+1) or arriving (-1)."""
        d0 = self.chain[i]
        p = self.point_at(d0 + sign * reach)
        q = self.s.pos[self.nodes[i]]
        if math.dist(p[:2], q[:2]) < 0.3:
            return None
        return bearing(q, p) if sign > 0 else bearing(p, q)

    def decisions(self, min_branch=4.0, merge=5.0):
        """Junctions where the caver has to choose: [(index, [alternatives])],
        alternatives being (bearing, length, leads_to)."""
        onroute = set(self.nodes)
        raw = []
        for i, n in enumerate(self.nodes):
            if i == len(self.nodes) - 1:
                continue
            # at the start, every way but the one taken is a choice too
            prev, nxt = (self.nodes[i - 1] if i else None), self.nodes[i + 1]
            alts = []
            for v in self.s.adj[n]:
                if v in (prev, nxt):
                    continue
                if v in onroute:
                    # another part of the route: a shortcut or the loop closing
                    alts.append((bearing(self.s.pos[n], self.s.pos[v]), 99.0, None, v))
                    continue
                L, reached = self._branch(n, v, onroute)
                if L >= min_branch:
                    alts.append((bearing(self.s.pos[n], self.s.pos[v]), L, self._lead_to(reached, n), v))
            # a node met again: the second time, every other way out is a choice
            if alts:
                raw.append((i, alts))
        # merge decisions a few metres apart into one
        out = []
        for i, alts in raw:
            if out and self.chain[i] - self.chain[out[-1][0]] < merge:
                out[-1] = (out[-1][0], out[-1][1] + alts)
            else:
                out.append((i, alts))
        return out

    def instruction(self, i, alts):
        """Plain-words directions at decision i."""
        bin_ = self._dir_at(i, -1)
        bout = self._dir_at(i, +1)
        parts = []
        if bin_ is not None and bout is not None:
            a = (bout - bin_ + 180) % 360 - 180
            for lim, words in TURNS:
                if abs(a) < lim:
                    parts.append(words.format(side='right' if a > 0 else 'left'))
                    break
        else:
            parts.append("go " + compass(bout) if bout is not None else "carry on")
        # up or down in the next few metres
        dz = self.point_at(self.chain[i] + 6)[2] - self.z(i)
        if dz <= -1.5:
            parts.append(f"down about {abs(dz):.0f} m")
        elif dz >= 1.5:
            parts.append(f"up about {dz:.0f} m")
        nxt = next((t for d, t in self.places() if d > self.chain[i] + 3), None)
        if nxt:
            parts.append(f"towards {nxt}")
        text = ", ".join(parts)
        text = text[0].upper() + text[1:] + "."
        sides = {}
        for b, L, lead, v in alts:
            if L >= 99:
                continue
            if bin_ is None:
                where = f"the way {compass(b)}"
            else:
                r = (b - bin_ + 180) % 360 - 180
                go = ((bout - bin_ + 180) % 360 - 180) if bout is not None else 0
                where = ("behind you" if abs(r) > 150 else
                         f"on the {'right' if r > go else 'left'}")
            sides.setdefault(where, [])
            if lead and lead not in sides[where]:
                sides[where].append(lead)
        if sides:
            bits = []
            for where, leads in sides.items():
                to = f" (to {', '.join(leads)})" if leads else ""
                bits.append((where if where.startswith("the way") else "the way " + where) + to)
            text += " Not " + (", ".join(bits[:-1]) + " or " + bits[-1] if len(bits) > 1 else bits[0]) + "."
        return text

    def profile(self, step=1.0):
        """[(distance, altitude)] along the route."""
        n = max(2, int(self.length / step))
        return [(d, self.point_at(d)[2]) for d in (self.length * k / (n - 1) for k in range(n))]
