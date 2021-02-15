import numpy as np

def rotCWS(v):
    x,z = v
    return (z,-x)

def rotACWS(v):
    x,z = v
    return (-z,x)

def prepSets(sets,pads):
    # Convert pad index lists to pad lists
    indexToPadNum = dict((pd["index"], pn) for pn,pd in pads.items())
    for i in range(len(sets)):
        sets[i]["pads"] = [indexToPadNum[j] for j in sets[i]["pad_indices"]]

def getPadsJoiningSets(s,t,sets,pads):
    for p in sets[s]["pads"]:
        for np in pads[p]["neighbours"]:
            if t == pads[np]["set"]:
                return p, np

def extendPathWithinSet(path, src_pad, dst_pad, s, sets, pads):
    # BFS between src_pad and dst_pad in the Exact same manner as for sets
    # Just ensure we remain within this set
    pad_tmp_dists = {}
    for p in sets[s]["pads"]:
        pad_tmp_dists[p] = -1

    pad_tmp_dists[src_pad] = 0

    iteration = 0
    while pad_tmp_dists[dst_pad] < 0:
        for p in sets[s]["pads"]:
            if pad_tmp_dists[p] != iteration:
                continue
            
            for np in pads[p]["neighbours"]:
                if pad_tmp_dists.get(np,0) < 0:     # ignore outside of set
                    pad_tmp_dists[np] = iteration + 1

        iteration += 1

    # Then we still search backward - the confusion is that it adds 10000 to them forwards
    # But you must go backwards because forwards isn't possible.
    revPath = []
    p = dst_pad
    while p != src_pad:
        revPath.append(p)
        for np in pads[p]["neighbours"]:
            if pad_tmp_dists.get(np, -2) == pad_tmp_dists[p] - 1:
                p = np
                break

    path.append(src_pad)
    path.extend(revPath[::-1])

def getPathBetweenPads(src_pad, dst_pad, sets, pads):
    srcSet = pads[src_pad]["set"]
    dstSet = pads[dst_pad]["set"]

    assert src_pad in sets[srcSet]["pads"]
    assert dst_pad in sets[dstSet]["pads"]

    # BFS on sets
    set_tmp_dists = [-1] * len(sets)
    set_tmp_dists[srcSet] = 0

    iteration = 0
    while set_tmp_dists[dstSet] < 0:
        for s in range(len(sets)):
            if set_tmp_dists[s] != iteration:
                continue

            for t in sets[s]["neighbours"]:
                if set_tmp_dists[t] < 0:
                    set_tmp_dists[t] = iteration + 1
                    
        iteration += 1


    # _then_mark_path
    # Path element [i] actually marked with tmp_dist = 10000 + i, we just collect them out
    revSetPath = []
    s = dstSet
    while set_tmp_dists[s] != 0:
        revSetPath.append(s)
        for t in sets[s]["neighbours"]:
            if set_tmp_dists[t] == set_tmp_dists[s] - 1:
                s = t
                break

    assert s == srcSet
    setPath = [srcSet] + revSetPath[::-1]
        

    # Extend the path in each set to join the next - choosing default links between pads.
    padPath = []
    currPad = src_pad
    for s,t in zip(setPath, setPath[1:]):
        pExit, pEnter = getPadsJoiningSets(s, t, sets, pads)

        extendPathWithinSet(padPath, currPad, pExit, s, sets, pads)

        # Move to the next set
        currPad = pEnter

    # Extend it within the final set to reach the target
    extendPathWithinSet(padPath, currPad, dst_pad, setPath[-1], sets, pads)

    ##print("pad path =", ", ".join(map(hex, padPath)))
    return padPath

def rotACWS(v):
    x,z = v
    return (-z,x)

def getLineSegmentIntersection(c,d,p,q,n=None,a=None,default=None,knownCollision=False):
    # STRICT
    # Used in trimming PQ, so if P=Q, return
    if p == q:
        return default

    # Get half plane for PQ if we don't already
    if n is None:
        n = rotACWS(np.subtract(q,p))
        n = np.multiply(n, 1 / np.linalg.norm(n))
    if a is None:
        a = np.dot(n,p)
    
    # Always get the half plane for AB
    n2 = rotACWS(np.subtract(d,c))
    n2 = np.multiply(n2, 1 / np.linalg.norm(n2))
    a2 = np.dot(c, n2)

    # If A,B same side of PQ, no collision
    if not knownCollision:
        dispA = np.dot(c, n) - a
        dispB = np.dot(d, n) - a
        if dispA * dispB >= 0:
            return default

    # Likewise if P,Q same side of AB
    dispA = np.dot(p, n2) - a2
    dispB = np.dot(q, n2) - a2
    if not knownCollision and dispA * dispB >= 0:
        return default
    
    # Compute intersection point
    dispAB = dispB - dispA
    alpha = (-dispA) / dispAB
    beta = (dispB) / dispAB
    intersectP = tuple(np.add(np.multiply(beta, p), np.multiply(alpha, q)))
    return intersectP

def walkAcrossTiles(currTile, n, a, universeTiles, endTiles, tiles, endPoint=None, visitedTiles=None):
    dispA = dispB = None
    index = None
    prevTile = None
    while currTile in universeTiles and currTile not in endTiles:
        if visitedTiles is not None:
            visitedTiles.append(currTile)

        currTileAddr = currTile
        currTile = tiles[currTile]
        dispA = np.dot(currTile["points"][-1], n)
        index = -1

        # Correct sign change in dot products indicates an edge we're leaving over.
        for i,pnt in enumerate(currTile["points"]):
            dispB = np.dot(pnt,n)
            if dispA > a and dispB <= a:
                index = i
                break
            dispA = dispB

        assert index != -1

        # If desired, test the edge we're crossing against the limit point to see if we should stop
        # Seems a weird way to do it looking back, hopefully it's reliable.
        
        if endPoint is not None:
            pntA = currTile["points"][index - 1]
            pntB = currTile["points"][index]
            n2 = rotACWS(np.subtract(pntB, pntA))
            a2 = np.dot(pntA, n2)
            if np.dot(endPoint,n2) < a2:
                # 2nd return will contain the endPoint
                return currTile["links"][index - 1], currTileAddr, None     # returning an address here vs dict below - hacky

        prevTile = currTile
        currTile = currTile["links"][index - 1]

    # Compute the intersection point using the weights
    dispAB = dispB - dispA
    alpha = (a-dispA) / dispAB
    beta = (dispB-a) / dispAB
    intersectP = np.add(np.multiply(beta, prevTile["points"][index-1]), np.multiply(alpha, prevTile["points"][index]))

    return currTile, prevTile, intersectP


def drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, guard=None, stdColour='b', padRadius=3):
    # If guard is not None, use their starting point. Should be data.
    # Should cope with paths entering and leaving the group many times, though it's untested

    if guard is not None:
        path = [None] + path
        assert None not in pads
        # Temporary change to pads
        pads[None] = {
            "tile" : guard["tile"],
            "position" : (guard["position"][0], None, guard["position"][1])
        }

    isInternal = [pads[p]["tile"] in currentTiles for p in path]
        
    isInternal.extend([True])  # [-1] and [len(isInternal)]

    exitingEdges = []
    fullEdges = []

    for i in range(len(path)):
        if not isInternal[i]:
            continue

        # Store all exiting edges as (inside_p, outside_p)
        if not isInternal[i-1]:
            exitingEdges.append((i, i-1))

        if isInternal[i+1]:
            fullEdges.append((i,i+1))
        else:
            exitingEdges.append((i, i+1))


    if len(fullEdges) > 0 and fullEdges[-1][1] == len(path):
        del fullEdges[-1]

    
    # Full edges : easy
    for edge in fullEdges:
        xs, ys, zs = zip(*[pads[path[x]]["position"] for x in edge])
        xs = [-x for x in xs]
        plt.plot(xs, zs, linewidth=0.5, color=stdColour)
        # Mark destinations - source will be the responsibility of
        # a partial edge, previous complete edge, or is the guard so is covered.
        axs.add_artist(plt.Circle((xs[1], zs[1]), padRadius, color=stdColour, linewidth=0.5, fill=True))

    # Walk along the partial edges across tiles, to contain them within the current group
    for p,q in exitingEdges:
        pd = pads[path[p]]
        qd = pads[path[q]]
        startPos = pd["position"][0:3:2]
        v = tuple(np.subtract(qd["position"][0:3:2],startPos))
        n = [-v[1], v[0]]   # acws
        n = np.multiply(n, 1 / np.linalg.norm(n))   # unit normal
        a = np.dot(n, startPos)

        if p > q:   # swish
            axs.add_artist(plt.Circle((-startPos[0], startPos[1]), padRadius, color=stdColour, linewidth=0.5, fill=True))

        currTile = pd["tile"]
        targetTile = qd["tile"]
        assert currTile != targetTile   # we're exiting the current tile group, so this is impossible


        currTile, prevTile, intersectP = walkAcrossTiles(currTile, n, a, currentTiles, [targetTile, 0], tiles)

        
        if currTile != 0:
            xs = [-pd["position"][0], -intersectP[0]]
            zs = [pd["position"][2], intersectP[1]]
            plt.plot(xs, zs, linewidth=0.5, color=stdColour)

        else:
            # Should be similar to the S1 secret entrance, where the edge goes to the tile above us,
            #   so you can't walk across tiles to it.
            # Draw the entire line in red to highlight this.
            xs, ys, zs = zip(*[pads[path[x]]["position"] for x in [p,q]])
            xs = [-x for x in xs]
            plt.plot(xs, zs, linewidth=0.5, color='r')
            axs.add_artist(plt.Circle((xs[1], zs[1]), padRadius, color='r', linewidth=0.5, fill=True))

    if guard is not None:
        del pads[None]