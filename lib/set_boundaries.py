# Currently pretty simple, assuming that boundaries between sets only consist of individual links of 1 pad to 1 pad.
# But it's probably suited to most needs.

from lib.path_finding import walkAcrossTiles, rotACWS
import numpy as np

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
                    continue

                # Walk in each direction to discover the limits
                n = ray
                a = np.dot(n, midPoint)
                _, _, p = walkAcrossTiles(midTile, n, a, tiles, [0], tiles)
                a = -a
                n = np.multiply(n, -1)
                _, _, q = walkAcrossTiles(midTile, n, a, tiles, [0], tiles)

                xs, zs = zip(p,q)
                plt.plot([-x for x in xs], zs, linewidth=2, color='#a718d6')