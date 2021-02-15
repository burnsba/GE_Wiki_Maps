# Field of view, showing the areas covered by the 0x3C command

# https://github.com/MrMinimal64/extremitypathfinder
# pip install extremitypathfinder
# the visibility in this should be sufficient since our LOS is a straight line, so a shortest path
from extremitypathfinder import PolygonEnvironment
from extremitypathfinder.helper_classes import Vertex
from extremitypathfinder.helper_fcts import find_visible
from math import atan2
import numpy as np
from itertools import repeat, count
from .path_finding import walkAcrossTiles, getLineSegmentIntersection, rotCWS, rotACWS



def walkClippingBoundary(addr, i, envTileAddrs, tiles, remExtEdges):
    """
    (addr -> tiles[addr]["links"][i]) must be crossing the boundary (out)
    Then we return the complete boundary and remove it from remExtEdges
    """
    boundary = []

    while True:
        # Move acws.
        i = (i + 1) % len(tiles[addr]["points"])
        l = tiles[addr]["links"][i-1]

        ##input(hex(tiles.get(l, {}).get("name", 0)))

        # If boundary, add it
        if l == 0 or l not in envTileAddrs:
            if len(boundary) > 0 and boundary[0] == (addr, i-1):
                break
            ##print("boundary", hex(tiles[addr]["name"]), "->", hex(tiles.get(l, {}).get("name", 0)))
            pr = (addr, i-1)
            assert pr in remExtEdges
            remExtEdges.remove(pr)
            boundary.append(pr)

        # Else, walk across it.
        else:
            i = tiles[l]["links"].index(addr) + 1
            addr = l
    
    # For each edge take 1 end, forms the whole polygon
    # .. but we need to remove duplicates (assumes len(set(-)) > 1)
    addr, j = boundary[-1]
    prev = tiles[addr]["points"][j]
    pnts = []
    origins = []
    for addr, j in boundary:
        curr = tiles[addr]["points"][j]
        if curr != prev:
            pnts.append(curr)
            origins.append((addr, j))
        prev = curr
    
    return pnts, origins

def drawFOV(guardId, rooms, tiles, guards, objects, opaque_objects, plt, ignoreTileAddrs = None, objTransforms = None):
    """
    [!] The rooms you give must be simply linked i.e. project flat. i.e. only 1 floor
    Otherwise this will likely enter an infinite loop looking for the boundary
    Nothing is drawn inside the guard's current room
    NOTE: If a ray glances off an object and out of our room it will currently cause us big problems
    """
    if objTransforms is None:
        objTransforms = dict()
    
    # Get our 'guard'.
    ourGuard = [g for g in guards.values() if g["id"] == guardId][0]
    guardPos = ourGuard["position"] 
    guardRoom = tiles[ourGuard["tile"]]["room"]
    
    # 0. Ignore tiles used to ensure our boundary polygon doesn't overlap at all
    ignoreTileAddrs = set() if ignoreTileAddrs is None else set(ignoreTileAddrs)

    # 1. get tiles in our rooms (or use all tiles)
    envTileAddrs = set(
        tiles.keys() if rooms is None
        else [a for a,t in tiles.items() if t["room"] in rooms]
    )
    envTileAddrs.difference_update(ignoreTileAddrs)
    assert len(envTileAddrs) > 0

    externalEdges = set()

    # 2. Find the outside shape:
    # Get a point with max x (and z). Then from those tiles with this point,
    #   get one with a maximal 2nd point
    max_p = max(p for a in envTileAddrs for p in tiles[a]["points"])
    maxTiles = [a for a in envTileAddrs if max_p in tiles[a]["points"]]
    q, addr = max((p, a) for a in maxTiles for p in tiles[a]["points"] if p != max_p)
    pnts = tiles[addr]["points"]
    i = pnts.index(q)
    if pnts[i-1] != max_p:
        i = (i + 1) % len(pnts)
        assert pnts[i] == max_p


    # 3a/4a. Get all external edges.
    # Prepare to get clipping context, which will map to (loop, index)
    # Where loop == -1 means outerBoundary, otherwise holes[loop]
    remExtEdges = set([
        (addr, ((i+1) % len(tiles[addr]["links"])) - 1)
        for addr in envTileAddrs
        for i,l in enumerate(tiles[addr]["links"])
        if l == 0 or l not in envTileAddrs
    ])
    clippingContext = dict()
    objectContext = dict()

    # Now [i-1], [i] are these two points, and must be an external edge.
    # (note this is only external to the group we're looking at, but that's okay)
    # And this edge is ["links"][i-1]. And they go ACWS
    assert (addr, i-1) in remExtEdges
    
    outerBoundary, outerOrigins = walkClippingBoundary(addr, i-1, envTileAddrs, tiles, remExtEdges)
    clippingContext.update(dict(zip(outerBoundary, zip(repeat(-1), count(), outerOrigins))))

    # 3. Find all clipping holes. Untested.
    # Also we'll pick up any extra
    holes = []
    while len(remExtEdges) > 0:
        addr, i = next(iter(remExtEdges))
        hole, holeOrigins = walkClippingBoundary(addr, i, envTileAddrs, tiles, remExtEdges)
        holes.append(hole)    # CWS
        clippingContext.update(dict(zip(hole, zip(repeat(len(holes)-1), count(), holeOrigins))))

    # 4. Get objs
    cleanObjPnts = dict()
    for room in rooms:
        for objAddr in opaque_objects[room]:
            pnts = objects[objAddr]["points"]

            # Skip doors unless we're transforming them
            if objects[objAddr]["type"] == "door" and objAddr not in objTransforms:
                continue

            dists = [np.linalg.norm(np.subtract(p,q)) for p,q in zip(pnts, pnts[1:] + pnts[:1])]
            pnts = [p for p,d in zip(pnts, dists) if d > 0.05]
            if len(pnts) <= 2:  # glass
                continue

            if objAddr in objTransforms:
                pnts = [tuple(objTransforms[objAddr](p)) for p in pnts]

            cleanObjPnts[objAddr] = pnts
            objectContext.update(dict(zip(pnts, zip(repeat(objAddr), count()))))
            holes.append(pnts[::-1])

    # 5. Use library, digging a little into the internals to add the current path
    environment = PolygonEnvironment()
    environment.store(outerBoundary[::-1], holes, validate=True)  # probably don't validate O:) - objects may leak over
    environment.prepare()
    
    # Poking internals working okay..
    assert environment.within_map(guardPos)
    guardVertex = Vertex(guardPos)
    environment.translate(new_origin=guardVertex)
    candidates = set(filter(lambda n: n.get_angle_representation() is not None, environment.graph.get_all_nodes()))
    visibles = [
        tuple(pnt[0].coordinates)
        for pnt in find_visible(candidates, edges_to_check=set(environment.all_edges))
    ]


    # 6. Extend these points as far as possible.
    # Arrange visibles in a (A?)CWS order
    # Probably use more than just the coordinates - see if it's brushing the corner or going into it.
    # Lack of another point between them says they land on the same edge - save some processing
    # May even be able to infer if we're brushing past?
    # But ultimately we are doing Rare code - generalise that code which we walked down the frig stairs with,
    #   then test for intersection with each object.
    # May need to reach back to get the tiles from the points

    # Also for final drawing restrict it to the room which Nat aint in (pass as param, can generalise to tiles if needed later).

    visibles.sort(key = lambda v : atan2(*np.subtract(v, guardPos)))
    inside = True
    borderData = None
    currPoly = None
    far = False

    for p in visibles:

        # Get the next and previous points
        # Note that the orientations are opposite for the outerBoundary
        # .. though maybe not coz of the way we store them
        assert (p in clippingContext) ^ (p in objectContext)
        pnts = j = loopI = origins = None
        isClipping = p in clippingContext
        if isClipping:
            loopI, j, (tileAddr, tilePntI) = clippingContext[p]
            pnts = outerBoundary if loopI == -1 else holes[loopI]
        else:
            objAddr, j = objectContext[p]
            pnts = cleanObjPnts[objAddr]

        assert p == pnts[j]
        a = pnts[j-1]
        b = pnts[(j+1) % len(pnts)]

        # Determine if we glance or crash into this vertex
        # Get the 2 edges, both should be CWS around the shape, then turned in
        v = rotCWS(np.subtract(a,p))
        w = rotCWS(np.subtract(p,b))
        ray = np.subtract(p, guardPos)
        glances = not ((np.dot(v,ray) > 0) and (np.dot(w,ray) > 0))

        n = rotACWS(ray)
        n = np.multiply(n, 1 / np.linalg.norm(n))
        a = np.dot(n, guardPos)

        if not glances:
            q = p
            if isClipping:
                lastTile = tiles[tileAddr]
            else:
                _, lastTile, _ = walkAcrossTiles(ourGuard["tile"], n, a, envTileAddrs, [0], tiles, endPoint=p)
                if isinstance(lastTile, int):
                    lastTile = tiles[lastTile]
        else:
            # Awkward case of glancing clipping corner
            # If we started at the source, we touch the clipping so could wrongly stop
            # We still need to fetch all the tiles to this point.
            visitedTiles = []
            if isClipping:
                # Rotate around the corner until our ray leaves through an edge (rather than a corner)
                # We are pretty sure this just means rotating CWS,
                #   because this is against the direction we set up the clipping
                while True:
                    assert tiles[tileAddr]["points"][tilePntI] == p
                    q = tiles[tileAddr]["points"][tilePntI - 1]

                    l = tiles[tileAddr]["links"][tilePntI - 1]
                    v2 = rotCWS(np.subtract(q,p))   # p -> q, rotated
                    if np.dot(v2, ray) < 0:
                        break
                    
                    tilePntI = tiles[l]["links"].index(tileAddr)
                    tileAddr = l

                _ = walkAcrossTiles(ourGuard["tile"], n, a, envTileAddrs, [0], tiles, endPoint=p, visitedTiles=visitedTiles)
            else:
                # For an object, we can't easily establish a start tile,
                #   so we just start at the source
                tileAddr = ourGuard["tile"]
                

            # Get the far clipping collision, and complete the list of tiles
            # There may be a duplicate but this isn't an issue.
            _, lastTile, q = walkAcrossTiles(tileAddr, n, a, envTileAddrs, [0], tiles, visitedTiles=visitedTiles)
            p,q = map(tuple, (p,q))
            lastInGuardRoom = len(visitedTiles) - 1 - [tiles[a]["room"] for a in visitedTiles[::-1]].index(guardRoom)

            # Search for collisions with objects and clipping holes
            # This is proper line Segment intersection
            for pnts in holes:
                prevPnt = pnts[-1]
                for i,pnt in enumerate(pnts):
                    q = getLineSegmentIntersection(prevPnt, pnt, p, q, n, a, q)
                    prevPnt = pnt
                

        if lastTile["room"] != guardRoom:
            borderData = (visitedTiles[lastInGuardRoom:lastInGuardRoom+2], n, a, p, q)
            if inside:
                # Exiting
                currPoly = [borderData, []]
            inside = False

            if glances and far:
                currPoly[1].append(q)
            
            currPoly[1].append(p)
            
            if glances and not far:
                currPoly[1].append(q)
            
            if glances:
                far = not far

        else:
            if not inside:
                # Entering
                currPoly.append(borderData)
                
                # currPoly = (entryData, points, leaveData)
                # Find the points where we enter and leave
                borderPnts = []
                for (insideTile, outsideTile), n, a, p, q in currPoly[0:3:2]:
                    # Tiles may only share a point if we had to walk around, in which case the point is p
                    if outsideTile in tiles[insideTile]["links"]:
                        i = tiles[insideTile]["links"].index(outsideTile)
                        d = tiles[insideTile]["points"][i+1]
                        c = tiles[insideTile]["points"][i]
                        borderPnts.append( getLineSegmentIntersection(c,d,p,q,n,a,None,True) )
                    else:
                        borderPnts.append(p)

                # Drop first and last point in favour of these border points. Wrap.
                polyPnts = borderPnts[:1] + currPoly[1][1:-1] + borderPnts[1:] + borderPnts[:1]
                xs, zs = zip(*polyPnts)
                xs = [-x for x in xs]
                plt.fill(xs, zs, linewidth=1, fc='r', alpha=0.2)

            inside = True