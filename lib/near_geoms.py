from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import numpy as np

def splitIntoNearest(poly, nearPoint, farPoint):
    n_x, _, n_z = nearPoint["position"]
    f_x, _, f_z = farPoint["position"]

    k = 4

    # Dividing line
    mid = ((n_x + f_x) / 2, (n_z + f_z) / 2)
    v = ( (f_x - n_x)*k, (f_z - n_z)*k )
    rotL = (-v[1], v[0])
    linePts = [np.add(mid, rotL), np.subtract(mid, rotL)]


    farSide = [np.add(linePts[0], v), np.add(linePts[1], v)]
    farSide = Polygon(linePts + farSide[::-1])

    nearSide = [np.subtract(linePts[0], v), np.subtract(linePts[1], v)]
    nearSide = Polygon(linePts + nearSide[::-1])

    assert farSide.is_valid
    assert nearSide.is_valid

    return poly.intersection(nearSide), poly.intersection(farSide)

def computeNearGeoms(pads, tiles):
    for pad in pads:
        pads[pad]["assocTiles"] = []
        pads[pad]["nearGeom"] = []

    # Focus around pads, and create shapes
    for tile, td in tiles.items():
        pad = td["nearPad"]

        pads[pad]["assocTiles"].append(tile)

        xs, ys = zip(*td["points"])
        if (
            (len(set(xs)) <= 1 or len(set(ys)) <= 1) or
            (len(set(td["points"])) < 3)
        ):
            td["shape"] = Polygon()
            continue

        td["shape"] = Polygon(td["points"])
        if not td["shape"].is_valid:
            print(f"Warning: Invalid initial area of size {td['shape'].area} dropped")
            td["shape"] = Polygon()


    # For each pad, join all associated tiles together
    # Then we need to intersect with "half planes"

    for pad, pd in pads.items():
        pd["assocArea"] = [tiles[tile]["shape"] for tile in pd["assocTiles"]]
        pd["assocArea"] = unary_union(pd["assocArea"])

        remArea = pd["assocArea"]
        p_x, _, p_z = pd["position"]

        # Proceed through the neighbours in reverse order
        for neighbour in pd["neighbours"][::-1]:
            nd = pads[neighbour]
            n_x, _, n_z = nd["position"]
            if n_x == p_x and n_z == p_z:
                # Special case for where our points coincide (0x41, 0x62)
                nearGeom = Polygon()    # remArea preserved
            else:
                remArea, nearGeom = splitIntoNearest(remArea, pd, nd)
                pads[neighbour]["nearGeom"].append(nearGeom)

        # Whatever is left is ours
        pd["nearGeom"].append(remArea)

    # Join all together
    for pad, pd in pads.items():
        pd["nearGeom"] = unary_union(pd["nearGeom"])

def drawNearGeoms(pads, axs, colouring=None):
    for pad, pd in pads.items():
        colour = np.random.rand(3,) if colouring is None else colouring(pd)
        geom = pd["nearGeom"]

        if type(geom) == Polygon:
            plys = [geom]
        elif type(geom) == MultiPolygon:
            plys = list(geom.geoms)
        elif type(geom) == LineString:
            plys = []
        else:
            plys = list(geom.geoms)

        for ply in plys:
            if ply.is_empty:
                continue
            if type(ply) == LineString:
                continue
            xs, ys = ply.exterior.xy
            xs = [-x for x in xs]   # flip
            axs.fill(xs, ys, alpha=0.5, fc=colour, ec='none')
