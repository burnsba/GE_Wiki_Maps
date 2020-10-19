import numpy as np
from functools import reduce

def prepTiles(tiles):
    # Create shapes only
    # Shapely may be less relevant for us now?
    for _, td in tiles.items():
        xs, zs = zip(*td["points"])
        td["bounding_box"] = (min(xs), max(xs), min(zs), max(zs))

        degenerate = (
            (len(set(xs)) <= 1 or len(set(zs)) <= 1) or
            (len(set(td["points"])) < 3)
        )

        td["degenerate"] = degenerate   # area 0 essentially


def getGroupBounds(tiles, groups):
    groupBounds = []

    for tileGrp in groups:
        bnds = [f(l) for f,l in zip([min, max, min, max], zip(*[ (tiles[tileAddr]["bounding_box"]) for tileAddr in tileGrp]))]
        groupBounds.append(bnds)
    
    return groupBounds


def prepPlot(plt, currGroupBounds):
    # Fit all tiles and a 1 metre in-game border

    # 1m GE world = 100 units = 1 cm (= 1/2.54 inches)
    PAD_UNITS = 100
    min_x, max_x, min_z, max_z = [(v+c) for v,c in zip(currGroupBounds, [-PAD_UNITS, PAD_UNITS, -PAD_UNITS, PAD_UNITS])]

    # Init global plot
    fig, axs = plt.subplots(figsize = ((max_x - min_x) / 254, (max_z - min_z) / 254))
    plt.axis('off')
    axs.set_aspect('equal')

    # Finally we have defeated pyplot
    axs.set_xlim(-max_x, -min_x)  # flipped remember
    axs.set_ylim(min_z, max_z)

    return fig,axs

def drawTile(td, colour, axs, alpha):
    xs, zs = zip(*td["points"])
    xs += (xs[0],)
    zs += (zs[0],)
    xs = [-x for x in xs]   # flip
    axs.fill(xs, zs, alpha=alpha, ec=colour, fc=colour)


def drawTiles(currentTiles, tiles, colour, axs, alpha=1):
    for tileAddr in currentTiles:
        drawTile(tiles[tileAddr], colour, axs, alpha) # light grey


def drawTileHardEdges(currentTiles, tiles, colour, axs):
    for tileAddr in currentTiles:
        td = tiles[tileAddr]
        xs, zs = zip(*td["points"])
        xs += (xs[0],)
        zs += (zs[0],)
        xs = [-x for x in xs]
        for i,l in enumerate(td["links"]):
            if l != 0:
                continue

            axs.plot(xs[i:i+2], zs[i:i+2], color=colour, linewidth=1)


# -------------- Tile planes ---------------

def roundIfClose(r):
    n = round(r)
    if abs(r-n) < 0.0001:
        return n
    return r

def getUnscaledEnclosingPlane(td, level_scale):
    ps = [[roundIfClose(x * level_scale) for x in p] for p in td["points"]]
    hs = [roundIfClose(h * level_scale) for h in td["heights"]]
    ps = [[x,y,z] for y, (x,z) in zip(hs, ps)]
    assert len(ps) >= 3

    # Some straight lines are split in 2, so their cross product is 0
    # Walk around the tile to find one which isn't
    succ = False
    for i in range(len(ps)):
        v = np.subtract(ps[i-1], ps[i])
        w = np.subtract(ps[(i+1) % len(ps)], ps[i])
        n = tuple(np.cross(w,v))   # normal
        if n != (0,0,0):
            succ = True
            break

    assert succ

    p_as = [np.dot(n, p) for p in ps]
    assert len(set(p_as)) == 1, "tile is not flat"  # probably not rounding above if so
    a = p_as[0]

    # ! Need a standard form, remove gcd
    assert all(x == int(x) for x in n) and a == int(a)
    gcd = reduce(np.gcd, n + (a,))
    a //= gcd
    n = tuple(x // gcd for x in n)

    return n,a


# Scale the tile planes back into the level, and make the normals unit vectors
def rescalePlane(n, a, level_scale):
    # a = v.n for some v in the tile, so scale as we imagine scaling v
    a = a / level_scale
    # then n and a we need to scale down as we make n a unit vector
    n_mag = np.linalg.norm(n)
    assert n_mag >= 1    # not small
    a = a / n_mag
    n = tuple(x / n_mag for x in n)
    return (n,a)

def getTilePlanes(currentTiles, tiles, level_scale):
    # Get all planes, even those which are vertical
    tilePlanes = dict()
        
    for tileAddr in currentTiles:
        td = tiles[tileAddr]
        plane = getUnscaledEnclosingPlane(td, level_scale)
        n,a = plane

        assert n[1] >= 0     # no tiles should be pointing down, relied on elsewhere

        if plane in tilePlanes:
            tilePlanes[plane].append(tileAddr)
        else:
            tilePlanes[plane] = [tileAddr]

    # Rescale now that we've matched them
    tilePlanes = dict([(rescalePlane(n,a,level_scale), tileAddrs) for (n,a), tileAddrs in tilePlanes.items()])

    return tilePlanes