"""Signed-distance modelling for organic parts (hands, cloth), meshed by surface nets.

Shapes are numpy functions of an (N, 3) point array returning signed distances in
metres (negative inside). They compose with smooth unions, so knuckles, finger webs
and cloth folds blend without the beads that overlapping ellipsoids leave. The
isosurface is extracted with naive surface nets: one vertex per surface cell at the
mean of its edge crossings and one quad per sign-changing grid edge. Pure numpy;
no dependency beyond the Blender module's own numpy.
"""
import numpy as np


# ------------------------------------------------------------------ primitives

def _v(p):
    return np.asarray(p, dtype=np.float64)


def frame(forward, up_hint):
    """Orthonormal rows (side, forward, up) with `forward` exact and `up` nearest `up_hint`."""
    f = _v(forward) / np.linalg.norm(forward)
    u = _v(up_hint) - f * np.dot(up_hint, f)
    u /= np.linalg.norm(u)
    s = np.cross(f, u)
    return np.stack((s, f, u))


def round_cone(P, a, b, r1, r2, up=(0, 0, 1), flat=1.0):
    """Tapered capsule from `a` (radius r1) to `b` (radius r2). `flat` < 1 squashes the
    section along `up` (a finger is thinner front to back than side to side)."""
    a, b = _v(a), _v(b)
    R = frame(b - a, up)
    q = (P - a) @ R.T
    q[:, 2] /= flat
    length = np.linalg.norm(b - a)
    # Inigo Quilez's exact rounded cone, in the frame where the axis is +Y.
    xz = np.hypot(q[:, 0], q[:, 2])
    y = q[:, 1]
    bb = (r1 - r2) / length
    aa = np.sqrt(max(1e-12, 1 - bb * bb))
    k = aa * y - bb * xz
    d = np.where(k < 0, np.hypot(xz, y) - r1,
                 np.where(k > aa * length, np.hypot(xz, y - length) - r2,
                          xz * aa + y * bb - r1))
    return d * flat


def capped_cone(P, a, b, r1, r2, up=(0, 0, 1), flat=1.0, rounding=0.0):
    """Flat-ended cone from `a` (radius r1) to `b` (radius r2), edges rounded by
    `rounding`, section squashed along `up` by `flat`. Quilez's exact capped cone."""
    a, b = _v(a), _v(b)
    R = frame(b - a, up)
    q = (P - a) @ R.T
    q[:, 2] /= flat
    h = np.linalg.norm(b - a) / 2
    ra, rb = r1 - rounding, r2 - rounding
    x = np.hypot(q[:, 0], q[:, 2])
    y = q[:, 1] - h
    k1 = np.array((rb, h))
    k2 = np.array((rb - ra, 2 * h))
    ca = np.stack((x - np.minimum(x, np.where(y < 0, ra, rb)), np.abs(y) - h), 1)
    qk = k1 - np.stack((x, y), 1)
    t = np.clip((qk @ k2) / (k2 @ k2), 0, 1)
    cb = np.stack((x, y), 1) - k1 + k2 * t[:, None]
    sign = np.where((cb[:, 0] < 0) & (ca[:, 1] < 0), -1.0, 1.0)
    d = sign * np.sqrt(np.minimum((ca * ca).sum(1), (cb * cb).sum(1))) - rounding
    return d * flat


def torus(P, c, axis, major, minor, up=(0, 0, 1), flat=1.0):
    """Ring of tube radius `minor` round `axis` at radius `major`, squashed like the cones."""
    R = frame(axis, up)
    q = (P - _v(c)) @ R.T
    q[:, 2] /= flat
    return (np.hypot(np.hypot(q[:, 0], q[:, 2]) - major, q[:, 1]) - minor) * flat


def ellipsoid(P, c, axes, radii):
    """Approximate ellipsoid distance (Quilez). `axes` rows are the local axes."""
    q = (P - _v(c)) @ np.asarray(axes, dtype=np.float64).T
    r = _v(radii)
    k0 = np.linalg.norm(q / r, axis=1)
    k1 = np.linalg.norm(q / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12)


def round_box(P, c, axes, half, radius):
    q = np.abs((P - _v(c)) @ np.asarray(axes, dtype=np.float64).T) - (_v(half) - radius)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - radius


def smin(a, b, k):
    """Polynomial smooth union; `k` is the blend width in metres."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


class Shape:
    """A distance function with an axis-aligned bound outside which it is never
    evaluated (it is then assumed farther than any blend width)."""

    def __init__(self, fn, lo, hi, region=None):
        self.fn, self.lo, self.hi, self.region = fn, _v(lo), _v(hi), region

    def mask(self, P, pad):
        return np.all((P >= self.lo - pad) & (P <= self.hi + pad), axis=1)


def cone_shape(a, b, r1, r2, up=(0, 0, 1), flat=1.0, region=None):
    a, b = _v(a), _v(b)
    r = max(r1, r2)
    return Shape(lambda P: round_cone(P, a, b, r1, r2, up, flat), np.minimum(a, b) - r, np.maximum(a, b) + r, region)


def capped_shape(a, b, r1, r2, up=(0, 0, 1), flat=1.0, rounding=0.0, region=None):
    a, b = _v(a), _v(b)
    r = max(r1, r2)
    return Shape(lambda P: capped_cone(P, a, b, r1, r2, up, flat, rounding), np.minimum(a, b) - r, np.maximum(a, b) + r, region)


def torus_shape(c, axis, major, minor, up=(0, 0, 1), flat=1.0, region=None):
    c, r = _v(c), major + minor
    return Shape(lambda P: torus(P, c, axis, major, minor, up, flat), c - r, c + r, region)


def ellipsoid_shape(c, axes, radii, region=None):
    c, r = _v(c), max(radii)
    return Shape(lambda P: ellipsoid(P, c, axes, radii), c - r, c + r, region)


def box_shape(c, axes, half, radius, region=None):
    c, r = _v(c), np.linalg.norm(half)
    return Shape(lambda P: round_box(P, c, axes, half, radius), c - r, c + r, region)


def compose(P, adds, subs=(), k_add=0.0, k_sub=0.0, far=1.0):
    """Smooth union of `adds` (each (shape, k) or shape with k_add), then smooth
    subtraction of `subs`. Returns distances."""
    d = np.full(len(P), far)
    for item in adds:
        shape, k = item if isinstance(item, tuple) else (item, k_add)
        m = shape.mask(P, k + 0.002)
        if m.any():
            d[m] = smin(d[m], shape.fn(P[m]), k)
    for item in subs:
        shape, k = item if isinstance(item, tuple) else (item, k_sub)
        m = shape.mask(P, k + 0.002)
        if m.any():
            d[m] = smax(d[m], -shape.fn(P[m]), k)
    return d


def nearest_region(P, shapes, default):
    """Index of the region whose shape is nearest each point (for material zones)."""
    best = np.full(len(P), np.inf)
    out = np.full(len(P), default, dtype=object)
    for shape in shapes:
        if shape.region is None:
            continue
        m = shape.mask(P, 0.004)
        if not m.any():
            continue
        dist = np.abs(shape.fn(P[m]))
        idx = np.nonzero(m)[0]
        better = dist < best[idx]
        best[idx[better]] = dist[better]
        out[idx[better]] = shape.region
    return out


# ------------------------------------------------------------------ meshing

def sample(fn, lo, hi, h, slab=24):
    """Evaluate `fn` on a grid from `lo` to `hi` with spacing `h` (z slabs bound memory)."""
    lo, hi = _v(lo), _v(hi)
    n = np.ceil((hi - lo) / h).astype(int) + 1
    xs, ys, zs = (lo[i] + h * np.arange(n[i]) for i in range(3))
    field = np.empty(n, dtype=np.float32)
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    for k0 in range(0, n[2], slab):
        k1 = min(n[2], k0 + slab)
        pts = np.empty((n[0], n[1], k1 - k0, 3))
        pts[..., 0] = gx[..., None]
        pts[..., 1] = gy[..., None]
        pts[..., 2] = zs[None, None, k0:k1]
        field[:, :, k0:k1] = fn(pts.reshape(-1, 3)).reshape(n[0], n[1], k1 - k0)
    return field


CORNERS = np.array([(i, j, k) for k in (0, 1) for j in (0, 1) for i in (0, 1)])
EDGES = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.abs(CORNERS[a] - CORNERS[b]).sum() == 1]


def surface_nets(field, lo, h):
    """Quad mesh of the zero set of `field` (sampled from `lo` with spacing `h`)."""
    F = field
    nx, ny, nz = F.shape
    corners = [F[i:nx - 1 + i, j:ny - 1 + j, k:nz - 1 + k] for i, j, k in CORNERS]
    mn = np.minimum.reduce(corners)
    mx = np.maximum.reduce(corners)
    active = (mn < 0) & (mx >= 0)
    cells = np.argwhere(active)
    index = -np.ones(active.shape, dtype=np.int64)
    index[active] = np.arange(len(cells))
    vals = np.stack([c[active] for c in corners], 1).astype(np.float64)
    acc = np.zeros((len(cells), 3))
    cnt = np.zeros(len(cells))
    for a, b in EDGES:
        fa, fb = vals[:, a], vals[:, b]
        m = (fa < 0) != (fb < 0)
        t = fa[m] / (fa[m] - fb[m])
        acc[m] += CORNERS[a] + (CORNERS[b] - CORNERS[a]) * t[:, None]
        cnt[m] += 1
    verts = _v(lo) + (cells + acc / cnt[:, None]) * h
    inside = F < 0
    quads = []
    # Edge along x at (i, j, k): cells (i, j-1..j, k-1..k); normal +x when inside at i.
    s = inside[:-1, 1:-1, 1:-1] != inside[1:, 1:-1, 1:-1]
    i, j, k = np.nonzero(s)
    j, k = j + 1, k + 1
    q = np.stack((index[i, j - 1, k - 1], index[i, j, k - 1], index[i, j, k], index[i, j - 1, k]), 1)
    quads.append(np.where(inside[i, j, k][:, None], q, q[:, ::-1]))
    s = inside[1:-1, :-1, 1:-1] != inside[1:-1, 1:, 1:-1]
    i, j, k = np.nonzero(s)
    i, k = i + 1, k + 1
    q = np.stack((index[i - 1, j, k - 1], index[i - 1, j, k], index[i, j, k], index[i, j, k - 1]), 1)
    quads.append(np.where(inside[i, j, k][:, None], q, q[:, ::-1]))
    s = inside[1:-1, 1:-1, :-1] != inside[1:-1, 1:-1, 1:]
    i, j, k = np.nonzero(s)
    i, j = i + 1, j + 1
    q = np.stack((index[i - 1, j - 1, k], index[i, j - 1, k], index[i, j, k], index[i - 1, j, k]), 1)
    quads.append(np.where(inside[i, j, k][:, None], q, q[:, ::-1]))
    return verts, np.concatenate(quads)


def mesh(fn, lo, hi, h):
    return surface_nets(sample(fn, lo, hi, h), lo, h)
