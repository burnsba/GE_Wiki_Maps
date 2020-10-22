import numpy as np

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

def drawPathWithinGroup(plt, path, pads, currentTiles, guard=None):
    # If guard is not None, use their starting point. Should be data.
    # Should cope with paths entering and leaving the group multiple times, though it's untested

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
        plt.plot(xs, zs, linewidth=0.5, color='b')

    # TODO : walk along the partial edges across tiles.
    # We only need to know which edge we cross, so just dot product with the rotated vector (normal),
    # Different signs says they cross, in the correct order says we cross them leaving the tile.
    # So assuming the tiles are convex (reasonable) this method will work.
    for p,q in exitingEdges:
        pd = pads[path[p]]
        qd = pads[path[q]]
        v = tuple(np.subtract(qd["position"],pd["position"]))[0:3:2]
        n = [-v[1], v[0]]   # acws
        np.multiply(n, 1 / np.linalg.norm(n))   # unit normal
        a = np.dot(n, pd["position"][0:3:2])

        currTile = pd["tile"]
        targetTile = qd["tile"]
        assert currTile != targetTile   # we're exiting the current tile group, so this is impossible
        while currTile not in [targetTile, 0]:
            break

    # Termination will have to be arriving at the target tile OR a null tile.
    # If a null tile then we'll assume we're in a S1 secret entrance situation, and colour the edge red or something.

    # Then we do need to intersect with that final edge to determine how much of the line to draw.
    # We can use our 2 dot products from the previous round as weights on the 2 tile points.

    if guard is not None:
        del pads[None]