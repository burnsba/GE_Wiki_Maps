
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