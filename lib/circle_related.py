import numpy as np
from math import atan2, pi, sqrt
from matplotlib import patches
from bisect import bisect_left

def roundIfClose(r):
    n = round(r)
    if abs(r-n) < 0.0001:
        return n
    return r

def splitIntoPolygonAndArcs(points, center, radiusSq):
    """
    Breaks the circle down into arcs and the intersection with the given circle. 
    used below but also for door reachability.
    """
    assert len(points) > 1

    def inCircle(p):
        v = np.subtract(p,center)
        return np.dot(v,v) <= radiusSq

    # Init
    inside = inCircle(points[-1])
    polygon = [points[-1]] if inside else []
    arcLeaves = []
    arcEnters = []

    origIndexInInner = []

    for i,currPoint in enumerate(points):
        origIndexInInner.append(len(polygon) - 0.5)

        prevPoint = points[i-1]
        ##print("\nConsidering {} -> {}".format(i-1, i))

        # Find the closest point on (infinite) edge to the circle center
        edge = np.subtract(currPoint, prevPoint)
        ##print("Edge = {}".format(edge))
        w = np.subtract(center, prevPoint)
        edge_length = np.linalg.norm(edge)
        closest_a = np.dot(edge,w) / edge_length
        ##print("Closest a = {}, edge_length = {}".format(closest_a, edge_length))
        closestPoint = np.add(prevPoint, np.multiply(edge, closest_a / edge_length))

        # Find the range on the edge that is inside
        w = np.subtract(closestPoint, center)
        deltaSq = np.dot(w,w)
        if deltaSq < radiusSq:
            delta = sqrt(radiusSq - deltaSq)
            ##print("Infinite line in range, delta = {}".format(delta))
            entry = max(closest_a - delta, 0)
            leave = min(closest_a + delta, edge_length)

            if not inside:
                if leave > entry:
                    ##print("->")
                    # we were outside, we've entered back in
                    pntA = np.add(prevPoint, np.multiply(edge, entry / edge_length))
                    polygon.append(pntA)
                    arcLeaves.append(len(polygon) - 1) # we enter, arc leaves

                    pntB = np.add(prevPoint, np.multiply(edge, leave / edge_length))
                    polygon.append(pntB)    # may be next point, or actual leave
                    inside = (leave == edge_length)
                    if not inside:
                        ##print("<-")
                        arcEnters.append(len(polygon) - 1)
            else:
                if leave > 0:   # don't duplicate the point if we literally leave on it
                    pntB = np.add(prevPoint, np.multiply(edge, leave / edge_length))
                    polygon.append(pntB)

                if leave < edge_length:
                    # we were inside, now we've left
                    inside = False
                    ##print("<-")
                    arcEnters.append(len(polygon) - 1)  # we leave, so arc enters

        else:
            ##print("Infinite line out of range")
            if inside:
                # leave = 0 effectively, don't add previous point but add the arcEnters
                arcEnters.append(len(polygon) - 1)
                ##print("<-")

            inside = False  # infinite line is outside

    # Edge case for if we just enter immediately
    if len(arcLeaves) == len(arcEnters) - 1:
        arcLeaves.append(points[-1])
    assert len(arcLeaves) == len(arcEnters)

    if len(arcLeaves) > 0:
        arcLeaves = arcLeaves[1:] + [arcLeaves[0]]  # shuffle which we think is correct
    arcs = list(zip(arcEnters, arcLeaves))

    return polygon, arcs, origIndexInInner

def getSphereIntersection(plane, tileAddrs, sphere_center, sphere_radius, tiles):
    # Compute distance to the plane. If too far, no intersection
    n,a = plane
    disp = np.dot(n,sphere_center) - a
    if abs(disp) >= sphere_radius:
        return 0, None, None

    # Circle radius and center in the plane
    radiusSq = sphere_radius**2 - disp**2
    radius = sqrt(radiusSq)
    center = np.subtract(sphere_center, np.multiply(n, disp))

    assert radius > 0
    assert roundIfClose(np.dot(center,n) - a) == 0


    polyAndArcs = []

    for tileAddr in tileAddrs:            
        td = tiles[tileAddr]
        tile_points = [[x,y,z] for (x,z), y in zip(td["points"], td["heights"])]

        polygon, arcs, _ = splitIntoPolygonAndArcs(tile_points, center, radiusSq)

        polyAndArcs.append((polygon, arcs))

    # Return the radius and center (for arcs), and the list of polygon and arcs
    return radius, center, polyAndArcs

def colourSphereIntesectionWithTiles(spheres, tilePlanes, tiles, plt, axs, HATCH_HACK_FACTOR=13, base_colour='g', base_alpha=0.1):
    # NOTE that the ellipse code may be a bit off, particularly the angle.
    # In frigate it's nearly all completely flat

    # (1) get circle in each plane
    # (2) 'intersect' to give the circular boundary
    # (3) 'tilt' into ellipse arcs and lines to view from above
    # (4) draw - hatching hack works beautifully

    for sphere_center,sphere_radius in spheres:

        for plane, tileAddrs in tilePlanes.items():
            n, _ = plane

            # Ignore any vertical planes
            if n[1] == 0:
                continue

            # Call main func
            radius, center, polyAndArcs = getSphereIntersection(plane, tileAddrs, sphere_center, sphere_radius, tiles)

            if radius <= 0:
                continue

            cx, _, cz = center
            
            # Determine values needed for any arcs
            # First off, the angle of the ellipse, which we can get from the normal
            nx, cosA, nz = n
            ellipse_angle = 180 * atan2(nx, nz) / pi   # 0,0 -> 0.
            cosA = abs(cosA)    # some tiles do point downward

            # Then the extent of the squashing
            width = 2*radius
            height = width*cosA

            for poly, arcs in polyAndArcs:
                # Note the poly may just be 2 points
                if len(poly) >= 3:
                    xs = [-x for x,y,z in poly]
                    zs = [z for x,y,z in poly]
                    xs.append(xs[0])
                    zs.append(zs[0])
                    plt.fill(xs, zs, alpha=base_alpha, fc=base_colour)

                # arcs :) 
                for arc in arcs:
                    pnts = [poly[i] for i in arc]
                    vectors = [np.subtract(pnt, center) for pnt in pnts]
                    headings = [((180 * atan2(x,z) / pi) + 360 + 90 - ellipse_angle) % 360 for x,y,z in vectors]

                    # Officially .Arc doesn't support filling but we can hack our way to the same result
                    #   with high enough density hatching. This should be only dependent on resolution,
                    #   so the fixed value 13 should always work but it can be tuned.
                    # This does create a bit more work but it saves a lot of painful code.
                    e = patches.Arc((-cx,cz), width, height, alpha=base_alpha, ec=base_colour, linewidth=0.5,
                        angle=ellipse_angle, theta1=headings[0], theta2=headings[1], hatch='-'*HATCH_HACK_FACTOR)
                    
                    
                    axs.add_patch(e)

def drawDoorReachability(plt, axs, objects, presets, currentTiles, excludePresets=None):
    for addr, obj in objects.items():
        if obj["type"] != "door":
            continue
        if obj["tile"] not in currentTiles:
            continue
        if obj["extreme_clearance"]:
            continue
        if excludePresets is not None:
            if obj["preset"] in excludePresets:
                continue
            if obj["preset"] + 10000 in excludePresets:
                continue

        preset = presets[10000 + obj["preset"]]
        assert preset["normal_y"][1] > 0.99     # we assume our doors are upright, simplier projection

        pos_x, _, pos_z = preset["position"]

        expansion = 150 # 1.5m expansion, hardcoded in the ASM

        js = [1,1,0,0]
        ks = [1,0,0,1]
        change = [-expansion, expansion]  
        xs = []
        zs = []
        pnts = []
        for j,k in zip(js, ks):
            doorX = (preset["x_limits"][j] + change[j])
            doorZ = (preset["z_limits"][k] + change[k])
            pnts.append((
                pos_x + preset["normal_x"][0]*doorX + preset["normal_z"][0]*doorZ, 
                pos_z + preset["normal_x"][2]*doorX + preset["normal_z"][2]*doorZ
            ))

        colour = (0,0,0,0.25)

        # Circle is centered on the object, not the preset (can differ slightly even when shut)
        # Radius is 2m
        cx, cz = obj["position"]
        RADIUS = 200
        innerPly, arcs, origIndexInInner = splitIntoPolygonAndArcs(pnts, obj["position"], RADIUS**2)

        assert len(arcs) > 0    # the corners of the square are 2.25m away, sides 1.5m so we will have arcs
        for leave, enter in arcs:
            origIndices = [i for i,newI in enumerate(origIndexInInner)
                if (leave < newI and newI < enter) or               # standard interval
                (enter < leave) and (newI > leave or newI < enter)  # if they wrap around, it's just got to be above the start or before the end
            ]
            # These indices need cycling to have the first 1st
            split = bisect_left([origIndexInInner[i] for i in origIndices], leave)
            origIndices = origIndices[split:] + origIndices[:split]

            segPnts = [innerPly[leave]] + [pnts[i-1] for i in origIndices] + [innerPly[enter]]  # -1 is a hack, may not be right generally..

            xs, zs = zip(*segPnts)
            xs = [-x for x in xs]
            plt.plot(xs, zs, linewidth=0.5, color=colour)

        leaves, enters = zip(*arcs)
        gaps = zip(enters, leaves[1:] + (leaves[0],))
        for gap in gaps:
            pnts = [innerPly[i] for i in gap]
            vectors = [np.subtract(pnt, obj["position"]) for pnt in pnts]
            headings = [((180 * atan2(x,z) / pi) + 360 + 90) % 360 for x,z in vectors]

            e = patches.Arc((-cx,cz), 2*RADIUS, 2*RADIUS, ec=colour, linewidth=0.5,
                angle=0, theta1=headings[0], theta2=headings[1])
            axs.add_patch(e)
