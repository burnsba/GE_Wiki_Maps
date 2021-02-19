import numpy as np
from math import sqrt
from matplotlib import patches
from math import atan2, pi

def euclidDistSq(v,w):
    diff = np.subtract(v,w)
    return np.dot(diff,diff)

def euclidDist(v,w):
    return sqrt(euclidDistSq(v,w))

def unitVector(v, k=1):
    d = np.linalg.norm(v)
    return tuple(np.multiply(v, k/d))

def getClearance(base_hr, target_hr):
    base_min, base_max = base_hr
    target_min, target_max = target_hr
    if target_min > base_max:   # target above base, return height
        return target_min - base_max
    if target_max < base_min:   # target below base, return negative number
        return target_max - base_min
    return 0    # overlapping

def getInsetPoint(p_i, points, distIn):
    # v, w the vectors to next and previous points
    # shape progresses CWS
    cp = points[p_i]
    nrp = points[(p_i + 1) % len(points)]
    pp = points[p_i - 1]
    v = np.subtract(nrp, cp)
    w = np.subtract(pp, cp)
    v_x, v_z = v
    w_x, w_z = w

    # Rotate unit vector of w cws, of v acws, and subtract.
    # So add and rotate cws
    uv_x, uv_z = unitVector(v, distIn)
    uw_x, uw_z = unitVector(w, distIn)
    c_x = (uv_z + uw_z)
    c_z = -(uv_x + uw_x)

    # Now a*v + b*w = (c_x, c_z)
    # | v_x  w_x |   | a |       | c_x |
    # | v_z  w_z | * | b |   =   | c_z |
    det = v_x * w_z - w_x * v_z
    a = (w_z * c_x - w_x * c_z) / det

    # Final result at -a*v + unit v rotate cws
    r_x = -a*v_x + uv_z
    r_z = -a*v_z - uv_x
    return (cp[0] + r_x, cp[1] + r_z)


def drawObjects(plt, axs, objects, tiles, currentTiles):
    """
    Export : draws all the objects.
    Will also add additional properties to the object dictionary as it processes them.
    """

    for addr, obj in objects.items():
        if obj["type"] == "lock":   # TODO locks
            continue

        if obj["tile"] not in currentTiles:
            continue

        if "health" in obj:
            obj["invincible"] = (obj["flags_1"] & 0x00020000) != 0 or (obj["health"] == 1.3635734469539e-36)  # 03e80000 as float, seems to be another invincible
            obj["explosive"] = not obj["invincible"] and obj["health"] < 250


        if obj["explosive"] and "points" not in obj:
            ##print("Boom @ " + hex(obj["preset"]))
            xs, zs = zip(*obj["preset_points"])
            xs += (xs[0],)
            zs += (zs[0],)
            plt.plot([-x for x in xs], zs, linewidth=0.5, color='r')

        if "points" in obj and len(obj["points"]) > 0:
            # Clean up points, removing duplicates
            pnts = obj["points"]
            pnts = obj["points"] = [p for p,q in zip(pnts, pnts[1:] + [pnts[0]]) if euclidDist(p,q) > 0.001]
            assert len(obj["points"]) != 0

            # Useful invention for inner lines. Shapes should be convex
            MAX_INSET = 10
            obj["center"] = tuple([sum(l) / len(l) for l in zip(*obj["points"])])
            cx,cz = obj["center"]
            dists = [euclidDist(obj["center"], p) for p in pnts]
            insetDist = min(min(dists) / 3, MAX_INSET)
        
            # Decide the number and colour of our outlines
            # Flipping x to get reality
            outlines = []
            outlines.append(([(-x, z) for x,z in obj["points"]], 'r' if obj["explosive"] else 'k'))
            if obj["invincible"] and obj["type"] != "door": # everyone knows doors are invincible
                # Making the inset points properly is a bit tricky
                insetPnts = [getInsetPoint(i, [(-x, z) for x,z in pnts], insetDist) for i in range(len(pnts))]
                outlines.append((insetPnts, outlines[0][1]))    # if invincible, add an inset outline the same colour

            # Determine if we are far below or above our clipping
            assert "tile" in obj and obj["tile"] in tiles
            td = tiles[obj["tile"]]
            tile_hr = (min(td["heights"]), max(td["heights"]))
            clearance = getClearance(tile_hr, obj["height_range"])
            obj["extreme_clearance"] = clearance < -10 or clearance > 300   # just a rough guess - frigate's spurious doors are at 404

            if not obj["extreme_clearance"]:
                for pntGroup,colour in outlines:
                    xs, zs = zip(*pntGroup)
                    xs += (xs[0],)
                    zs += (zs[0],)
                    plt.plot(xs, zs, linewidth=0.5, color=colour)

        if obj["type"] == "door":
            if obj["door_type"] not in [4,5,9]:
                print("Unsupported door type {}".format(obj["door_type"]))
            if obj.get("extreme_clearance"):
                pass #print("Door with extreme clearance ignored")
            if len(obj.get("hinges", [])) > 0 and not obj["extreme_clearance"]:
                assert len(obj["hinges"]) <= 2
                openBackward = ((obj["flags_1"] >> 29) & 0x1) == 1

                for hi, hingePos in enumerate(obj["hinges"]):
                    # We find the closest point to the hinge,
                    # then go one step clockwise / acws on the points
                    # And draw an arc through that point, in the correct direction

                    # Doors which only open backward are awkward..
                    if openBackward and len(obj["hinges"]) == 1:
                        hi = 1-hi

                    dists = [ euclidDist(hingePos, p) for p in obj["points"] ]
                    min_d = min(dists)
                    assert max(dists) > 5
                    pivotPointI = [i for i,d in enumerate(dists) if d == min_d][0]

                    # Walk around in the relevant direction, but keep going until we find a point atleast 5cm away
                    # (doors' points are weird, there are often more than 4)
                    stepDirc = [1,-1][hi]
                    nI = pivotPointI
                    while True:
                        nI = (nI + stepDirc) % len(obj["points"])
                        if dists[nI] > 5:
                            break

                    nx,nz = obj["points"][nI]
                    hx, hz = hingePos
                    shutAngle = atan2(nx-hx,nz-hz) * 180 / pi
                    shutAngle += 90 # GE-Pyplot 'North' disagreement

                    circ = 2*dists[nI]

                    t1, t2 = [
                        (shutAngle, shutAngle + 90),
                        (shutAngle - 90, shutAngle),
                    ][hi]
                    e = patches.Arc((-hx,hz), circ, circ, linewidth=0.5, angle=0.0, theta1=t1, theta2=t2)
                    axs.add_patch(e)



