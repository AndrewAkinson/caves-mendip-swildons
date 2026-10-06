"""Readers for the files the 3D view is made from: Survex .3d (the
centreline), Therion .lox (the passage walls) and uncompressed GeoTIFF
(the LIDAR). Plain Python, no packages."""
import struct


def read_3d(path):
    """A Survex .3d file, version 8 (what Therion writes).

    Returns (legs, stations): legs as (from_xyz, to_xyz, flags) with
    flags 1 surface, 2 duplicate, 4 splay; stations as (name, xyz, flags)
    with flags 1 surface, 2 underground, 4 entrance, 8 exported, 16 fixed.
    Coordinates are metres in the file's own system (here OSGB:ST, the
    100 km square, as Swildons_Centreline.th sets).
    """
    d = open(path, 'rb').read()
    i = 0

    def line():
        nonlocal i
        j = d.index(b'\n', i)
        s, i = d[i:j], j + 1
        return s

    if line() != b'Survex 3D Image File':
        raise ValueError(f'{path} is not a Survex .3d file')
    ver = line()
    if ver != b'v8':
        raise ValueError(f'{path}: .3d {ver.decode()} not supported, only v8')
    line()          # title, then a NUL and the coordinate system
    line()          # timestamp
    i += 1          # file-wide flags
    label = b''

    def read_label():
        nonlocal i, label
        b = d[i]; i += 1
        if b:
            drop, add = b >> 4, b & 15
        else:
            drop = d[i]; i += 1
            if drop == 255:
                drop = struct.unpack_from('<I', d, i)[0]; i += 4
            add = d[i]; i += 1
            if add == 255:
                add = struct.unpack_from('<I', d, i)[0]; i += 4
        if drop:
            label = label[:-drop]
        label += d[i:i + add]
        i += add
        return label.decode('utf-8', 'replace')

    def xyz():
        nonlocal i
        x, y, z = struct.unpack_from('<3i', d, i)
        i += 12
        return (x / 100, y / 100, z / 100)

    legs, stations = [], []
    pos = None
    while i < len(d):
        c = d[i]; i += 1
        if c <= 0x04 or c == 0x10:      # leg style; no date
            continue
        if c == 0x0f:                   # move
            pos = xyz()
        elif 0x11 <= c <= 0x13:         # dates
            i += (2, 3, 4)[c - 0x11]
        elif c == 0x1f:                 # loop-closure error
            i += 20
        elif 0x30 <= c <= 0x33:         # passage cross-section (LRUD)
            read_label()
            i += 16 if c & 1 else 8
        elif 0x40 <= c <= 0x7f:         # leg
            if not c & 0x20:
                read_label()
            p = xyz()
            legs.append((pos, p, c & 0x1f))
            pos = p
        elif c >= 0x80:                 # station
            name = read_label()
            stations.append((name, xyz(), c & 0x7f))
        else:
            raise ValueError(f'{path}: unknown .3d item 0x{c:02x} at byte {i - 1}')
    return legs, stations


def read_lox_walls(path):
    """The passage-wall meshes from a Therion .lox file: one (points,
    triangles) per scrap, points as (x, y, z) in survey metres and
    triangles as index triples."""
    d = open(path, 'rb').read()
    i, walls = 0, []
    while i + 16 <= len(d):
        kind, rec_bytes, n, data_bytes = struct.unpack_from('<4I', d, i)
        recs, data = i + 16, i + 16 + rec_bytes
        if kind == 4 and n:             # scraps
            size = rec_bytes // n
            for r in range(n):
                (_, _, npts, ppos, _, ntri, tpos, _) = struct.unpack_from('<8I', d, recs + r * size)
                pts = struct.unpack_from(f'<{3 * npts}d', d, data + ppos)
                tri = struct.unpack_from(f'<{3 * ntri}I', d, data + tpos)
                walls.append(([pts[k:k + 3] for k in range(0, len(pts), 3)],
                              [tri[k:k + 3] for k in range(0, len(tri), 3)]))
        i = data + data_bytes
    return walls


def read_tiff(data):
    """A single-band, uncompressed, 32-bit float GeoTIFF (what the
    Environment Agency's WCS serves). Returns (width, height, values
    row by row from the top, (x0, y0) of the top-left corner, pixel size)."""
    end = '<' if data[:2] == b'II' else '>'
    if struct.unpack_from(end + 'H', data, 2)[0] != 42:
        raise ValueError('not a TIFF')
    off = struct.unpack_from(end + 'I', data, 4)[0]
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}
    fmts = {1: 'B', 2: 'c', 3: 'H', 4: 'I', 5: 'II', 11: 'f', 12: 'd', 16: 'Q'}
    tags = {}
    for k in range(struct.unpack_from(end + 'H', data, off)[0]):
        tag, typ, cnt, val = struct.unpack_from(end + 'HHI4s', data, off + 2 + 12 * k)
        nbytes = sizes.get(typ, 1) * cnt
        src = val if nbytes <= 4 else data[struct.unpack(end + 'I', val)[0]:][:nbytes]
        if typ in fmts and typ != 2:
            tags[tag] = struct.unpack_from(end + fmts[typ] * cnt, src)
    w, h = tags[256][0], tags[257][0]
    if tags.get(259, (1,))[0] != 1 or tags.get(258, (32,))[0] != 32 or tags.get(339, (3,))[0] != 3:
        raise ValueError('only uncompressed float32 TIFFs are supported')
    out = [0.0] * (w * h)
    if 322 in tags:                     # tiled
        tw, th = tags[322][0], tags[323][0]
        across = (w + tw - 1) // tw
        for t, o in enumerate(tags[324]):
            tx, ty = (t % across) * tw, (t // across) * th
            vals = struct.unpack_from(f'{end}{tw * th}f', data, o)
            for r in range(min(th, h - ty)):
                n = min(tw, w - tx)
                out[(ty + r) * w + tx:(ty + r) * w + tx + n] = vals[r * tw:r * tw + n]
    else:                               # strips
        rows = tags.get(278, (h,))[0]
        for s, o in enumerate(tags[273]):
            n = min(rows, h - s * rows) * w
            out[s * rows * w:s * rows * w + n] = struct.unpack_from(f'{end}{n}f', data, o)
    sx = tags[33550][0] if 33550 in tags else 1.0
    if 33922 in tags:                   # tie point
        x0, y0 = tags[33922][3], tags[33922][4]
    else:                               # transformation matrix
        x0, y0 = tags[34264][3], tags[34264][7]
        sx = tags[34264][0]
    return w, h, out, (x0, y0), sx
