# Currently we have 2 similar functions:
#   - drawSets - shows all sets, with lines between sets highlighted using 
#   - drawNavGraph - shows all sets, labelling pads (including those that coincide) and sets

# Note that drawSets assumes that boundaries between sets only consist of individual links of 1 pad to 1 pad,
#   when there are actually at most 2 effectively (because of guard routing) and we should find these

# TODO improve

from lib.path_finding import walkAcrossTiles, rotACWS, drawPathWithinGroup
import numpy as np

def drawSets(sets, pads, lone_pads, currentTiles, tiles, plt, axs, scale=1):
    # Show all the sets and the connections of the 'navigation graph',
    #   with a different colour to show crossing between sets rather than internally
    # The stress is more on sets than the navigation graph, unlike the function below. 
    # We should combine it with the below sometime
    for p in pads:
        Pp = pads[p]
        if Pp["tile"] not in currentTiles:
            continue

        x,_,z = Pp["position"]
        axs.add_artist(plt.Circle((-x, z), 5, color='g', linewidth=1*scale, fill=True))

        for q in pads[p]["neighbours"]:
            Pq = pads[q]
            # Only draw the line once
            if q < p and Pq["tile"] in currentTiles:
                continue

            edgeColour = 'g' if Pq["set"] == Pp["set"] else 'k'
            drawPathWithinGroup(plt, axs, [p,q], pads, currentTiles, tiles,
                stdColour=edgeColour, secretColour=edgeColour,
                padRadius=0, linewidth=0.5*scale)


    padsByIndex = dict((p['index'], p) for p in pads.values())

    # Also draw the name for each set
    for sI, s in enumerate(sets):
        setPadPositions = [padsByIndex[i]["position"] for i in s["pad_indices"]]
        xs,ys,zs = zip(*setPadPositions)
        x = sum(xs) / len(xs) + 15
        z = sum(zs) / len(zs) + 5
        plt.text(-x, z, f"{sI:X}", fontsize=14*scale)

def drawNavGraph(pads, plt, axs, edgeColour='w'):
    # Named to distinguish it from drawSets, though there's some similarity
    #   -> join them at some point

    xs = []
    zs = []
    for pad, pd in pads.items():
        x,_,z = pd["position"]
        xs.append(-x)
        zs.append(z)

    axs.scatter(xs, zs)

    # Find coinciding pads
    posToPads = {}
    for pad, pd in pads.items():
        pos = pd["position"][::2]
        l = posToPads[pos] = posToPads.get(pos, [])
        l.append(pad)
    
    allCoincidingPads = set()
    coincidingPads = {}
    for pos, ps in posToPads.items():
        allCoincidingPads.update(ps[1:])
        if len(ps) > 1:
            coincidingPads[ps[0]] = ps[1:]

    # Label the pads, including duplicates
    for pad, pd in pads.items():
        x,_,z = pd["position"]
        lbl = "{:02x}".format(pad)
        if pad in allCoincidingPads:
            continue
        if pad in coincidingPads:
            lbl += "/" + "/".join(["{:02x}".format(q) for q in coincidingPads[pad]])
        axs.annotate(lbl, (-x, z))
        pd["num"] = pad

    for pad, pd in pads.items():
        p_x, _, p_z = pd["position"]
        for neighbour in pd["neighbours"][::-1]:
            nd = pads[neighbour]
            n_x, _, n_z = nd["position"]
            plt.plot([-p_x, -n_x], [p_z, n_z], color=edgeColour, linewidth=0.5)


def findBisector(startPad, endPad, currentTiles, tiles):
    startPos = startPad["position"][::2]
    endPos = endPad["position"][::2]

    midPoint = np.multiply(np.add(startPos, endPos), 0.5)

    # Define the halfplane which these points sit at the edge of
    ray = np.subtract(endPos, startPos)
    n = rotACWS(ray)
    a = np.dot(n, startPos)

    # Walk to the mid point
    _, midTile, rtnPoint = walkAcrossTiles(startPad["tile"], n, a, tiles, [0], tiles, endPoint=midPoint)
    assert rtnPoint is None, "line between pads goes OOB"

    if midTile not in currentTiles:
        return None, None

    # Walk in each direction to discover the limits
    n = ray
    a = np.dot(n, midPoint)
    _, _, p = walkAcrossTiles(midTile, n, a, tiles, [0], tiles)
    a = -a
    n = np.multiply(n, -1)
    _, _, q = walkAcrossTiles(midTile, n, a, tiles, [0], tiles)

    return p,q


def drawSetBoundaries(sets, pads, currentTiles, tiles, plt):
    for iA, setA in enumerate(sets):
        # Edges coming into A
        # Form these into a dictionary - note this will remove duplicates, but we're not prepared to deal with those
        inwardEdgesA = dict([(q,p) for p in setA["pads"] for q in pads[p]["neighbours"]])

        for iB in setA["neighbours"]:
            if iB < iA:
                continue
            assert iA != iB

            setB = sets[iB]
            for startPad in setB["pads"]:
                if startPad not in inwardEdgesA:
                    continue
                endPad = inwardEdgesA[startPad]

                startPad = pads[startPad]
                endPad = pads[endPad]

                if startPad["tile"] not in currentTiles and endPad["tile"] not in currentTiles:
                    continue

                
                p, q = findBisector(startPad, endPad, currentTiles, tiles)
                if p is None:
                    continue

                xs, zs = zip(p,q)
                plt.plot([-x for x in xs], zs, linewidth=2, color='#a718d6')