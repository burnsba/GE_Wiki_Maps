from frigate_divisions import dividingTiles, startTileName
from data import tiles, objects, guards, pads, level_scale
from lib.seperate_groups import seperateGroups
from group_names import *
from math import sqrt, atan2, pi
import numpy as np
from functools import reduce

def sgn(x):
    if x == 0: return 0
    if x < 0: return -1
    return 1

def roundIfClose(r):
    n = round(r)
    if abs(n - r) < 0.00001:
        return n
    return r

groups = seperateGroups(tiles, startTileName, dividingTiles)

# ----------------------------------------------------------

# NOTES:
# 1) Unscale data? Looks like we have some rounding errors atm.
# 2) Recognise stairs (before we split things up) - colour
# 3) Automatic lines between the sections
# 4) Bring in all guards, with BA and such.
# 5) ! Swing direction, should be easy enough. Presumably the center is known

from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib import patches
from numpy.random import rand
from matplotlib.transforms import Bbox
from matplotlib import colors

# Create shapes only
for addr, td in tiles.items():

    xs, zs = zip(*td["points"])
    td["bounding_box"] = (min(xs), max(xs), min(zs), max(zs))

    if (
        (len(set(xs)) <= 1 or len(set(zs)) <= 1) or
        (len(set(td["points"])) < 3)
    ):
        td["shape"] = Polygon()
        continue

    td["shape"] = Polygon(td["points"])
    assert td["shape"].is_valid # crucial


groupBounds = []

for tileGrp in groups:
    bnds = [f(l) for f,l in zip([min, max, min, max], zip(*[ (tiles[tileAddr]["bounding_box"]) for tileAddr in tileGrp]))]
    groupBounds.append(bnds)







# Plotting

GROUP_NO = GRP_DECK_AND_UPSTAIRS 
currentTiles = set(groups[GROUP_NO])    # restrict to this group
# 1m GE world = 100 units = 1 cm (= 1/2.54 inches)
PAD_UNITS = 100
min_x, max_x, min_z, max_z = [(v+c) for v,c in zip(groupBounds[GROUP_NO], [-PAD_UNITS, PAD_UNITS, -PAD_UNITS, PAD_UNITS])]

# Init global plot
fig, axs = plt.subplots(figsize = ((max_x - min_x) / 254, (max_z - min_z) / 254))
plt.axis('off')
axs.set_aspect('equal')

# Finally we have defeated pyplot
axs.set_xlim(-max_x, -min_x)  # flipped remember
axs.set_ylim(min_z, max_z)

def draw(geom, colour):
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
        edge_colour = colors.colorConverter.to_rgba(colour, alpha=.5)
        axs.fill(xs, ys, alpha=1, ec=edge_colour, fc=edge_colour)




# Canvas..
for tileAddr in groups[GROUP_NO]:
    poly = tiles[tileAddr]["shape"]
    draw(poly, (0.75, 0.75, 0.75)) # light grey

for tileAddr in groups[GROUP_NO]:
    td = tiles[tileAddr]
    xs, zs = zip(*td["points"])
    xs += (xs[0],)
    zs += (zs[0],)
    xs = [-x for x in xs]
    for i,l in enumerate(td["links"]):
        if l != 0:
            continue

        axs.plot(xs[i:i+2], zs[i:i+2], color=(0.65, 0.65, 0.65), linewidth=1)



# Guards..
for addr, gd in guards.items():
    if gd["tile"] not in currentTiles:
        continue
    x,z = gd["position"]
    axs.add_artist(plt.Circle((-x, z), gd["radius"], color='g', linewidth=1, fill=False))



# Objects..

def euclidDist(t1, t2):
    return sqrt((t1[0] - t2[0])**2 + (t1[1] - t2[1])**2)

def unitVector(v, k=1):
    d = sqrt(v[0]**2 + v[1]**2)
    return (k * v[0] / d, k * v[1] / d)

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
    np = points[(p_i + 1) % len(points)]
    pp = points[p_i - 1]
    v = (np[0] - cp[0], np[1] - cp[1])
    w = (pp[0] - cp[0], pp[1] - cp[1])
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

for addr, obj in objects.items():
    if obj["tile"] not in currentTiles:
        continue

    if "health" in obj:
        obj["invincible"] = (obj["flags_1"] & 0x00020000) != 0 or (obj["health"] == 1.3635734469539e-36)  # 03e80000 as float, seems to be another invincible
        obj["explosive"] = not obj["invincible"] and obj["health"] < 250


    if obj["explosive"] and "points" not in obj:
        print("Boom @ " + hex(obj["preset"]))
        xs, zs = zip(*obj["preset_points"])
        xs += (xs[0],)
        zs += (zs[0],)
        plt.plot([-x for x in xs], zs, linewidth=0.5, color='r')

    if "points" in obj:
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
        # Making the inset points properly is a bit tricky
        insetPnts = [getInsetPoint(i, [(-x, z) for x,z in pnts], insetDist) for i in range(len(pnts))]
    
        # Decide the number and colour of our outlines
        # Flipping x to get reality
        outlines = []
        outlines.append(([(-x, z) for x,z in obj["points"]], 'r' if obj["explosive"] else 'k'))
        if obj["invincible"] and obj["type"] != "door": # everyone knows doors are invincible
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
        if obj["extreme_clearance"]:
            pass #print("Door with extreme clearance ignored")
        if "hinge" in obj and not obj["extreme_clearance"]:
            dists = [ euclidDist(obj["hinge"], p) for p in obj["points"] ]

            # Angle will always be counter-clockwise (for these simple doors anyway)
            # So we'll go one step clockwise on the points
            min_d = min(dists)
            pivotPointI = [i for i,d in enumerate(dists) if d == min_d][0]
            nI = (pivotPointI+1) % len(obj["points"])
            nx,nz = obj["points"][nI]
            hx, hz = obj["hinge"]
            shutAngle = atan2(nx-hx,nz-hz) * 180 / pi

            circ = 2*dists[nI]

            e = patches.Arc((-hx,hz), circ, circ, linewidth=0.5, angle=0.0, theta1=shutAngle+90, theta2=shutAngle+180)
            axs.add_patch(e)







# Slightly more generic

def subVectors(v,w):
    return [x-y for x,y in zip(v,w)]

def getEnclosingPlane(td):
    ps = [[roundIfClose(x * level_scale) for x in p] for p in td["points"]]
    hs = [roundIfClose(h * level_scale) for h in td["heights"]]
    ps = [[x,y,z] for y, (x,z) in zip(hs, ps)]
    assert len(ps) >= 3

    # Some straight lines are split in 2, so their cross product is 0
    # Walk around the tile to find one which isn't
    succ = False
    for i in range(len(ps)):
        v = subVectors(ps[i-1], ps[i])
        w = subVectors(ps[(i+1) % len(ps)], ps[i])
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

# Get all planes which aren't vertical (those aren't visible from above)
tilePlanes = dict()
    
for tileAddr in groups[GROUP_NO]:
    td = tiles[tileAddr]
    plane = getEnclosingPlane(td)
    n,a = plane

    if n[1] == 0:
        continue
    assert n[1] > 0     # no tiles should be pointing down

    if plane in tilePlanes:
        tilePlanes[plane].append(tileAddr)
    else:
        tilePlanes[plane] = [tileAddr]


# Scale the tile planes back into the level, and make the normals unit vectors
def scalePlane(n, a):
    # a = v.n for some v in the tile, so scale as we imagine scaling v
    a = a / level_scale
    # then n and a we need to scale down as we make n a unit vector
    n_mag = np.linalg.norm(n)
    assert n_mag >= 1    # not small
    a = a / n_mag
    n = tuple(x / n_mag for x in n)
    return (n,a)


tilePlanes = dict([(scalePlane(*plane), tileAddrs) for plane, tileAddrs in tilePlanes.items()])

"""
# check
(n,a), tileAddrs = list(tilePlanes.items())[0]
for tileAddr in tileAddrs:
    td = tiles[tileAddr]
    for (x,z),y in zip(td["points"], td["heights"]):
        p = (x,y,z)
        print(np.dot(p,n) - a)
"""

def getSphereIntersection(plane, tileAddrs, sphere_center, sphere_radius):
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

    def inCircle(p):
        v = np.subtract(p,center)
        return np.dot(v,v) <= radiusSq

    polyAndArcs = []

    for tileAddr in tileAddrs:            
        td = tiles[tileAddr]
        tile_points = [[x,y,z] for (x,z), y in zip(td["points"], td["heights"])]

        # Init
        inside = inCircle(tile_points[-1])
        polygon = [tile_points[-1]] if inside else []
        arcLeaves = []
        arcEnters = []

        for i,currPoint in enumerate(tile_points):
            prevPoint = tile_points[i-1]
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
            arcLeaves.append(tile_points[-1])
        assert len(arcLeaves) == len(arcEnters)

        if len(arcLeaves) > 0:
            arcLeaves = arcLeaves[1:] + [arcLeaves[0]]  # shuffle which we think is correct
        arcs = list(zip(arcEnters, arcLeaves))
        polyAndArcs.append((polygon, arcs))

    # Return the radius and center (for arcs), and the list of polygon and arcs
    return radius, center, polyAndArcs


# FRIGATE SPECIFIC - HOSTAGES
# Refactor into sphere intersection code - note that the ellipse code may be a bit off, particularly the angle.
# Find a slope to try it on
# Also have the hatch density as an optional parameter

ESCAPE_PAD_NAMES = "ABCDEF" # we're going to rename them in order
ESCAPE_PAD_NUMS = [0x91, 0x93, 0xA9, 0x94, 0xA8, 0x8f]  # best to worst when unloaded

HOSTAGE_HEIGHT = 105    # measured, varies +-9 but mostly + so this is pretty fair

for i, padNum in enumerate(ESCAPE_PAD_NUMS):
    # Get the pad position and bring it down to save bringing everything else up
    padPos = list(pads[padNum]["position"])
    padPos[1] -= HOSTAGE_HEIGHT
    padPos = tuple(padPos)

    for plane, tileAddrs in tilePlanes.items():
        # Call main func
        radius, center, polyAndArcs = getSphereIntersection(plane, tileAddrs, padPos, 500)

        if radius <= 0:
            continue

        cx, _, cz = center
        
        # Determine values needed for any arcs
        # First off, the angle of the ellipse, which we can get from the normal
        n, _ = plane
        nx, cosA, nz = n
        ellipse_angle = 180 * atan2(nx, nz) / pi   # 0,0 -> 0.

        # Then the extent of the squashing
        width = 2*radius
        height = width*cosA

        escape_alpha = 0.1
        escape_colour = 'g'

        for poly, arcs in polyAndArcs:
            # Note the poly may just be 2 points
            if len(poly) >= 3:
                xs = [-x for x,y,z in poly]
                zs = [z for x,y,z in poly]
                xs.append(xs[0])
                zs.append(zs[0])
                plt.fill(xs, zs, alpha=escape_alpha, fc=escape_colour)

            # arcs :) 
            for arc in arcs:
                pnts = [poly[i] for i in arc]
                vectors = [np.subtract(pnt, center) for pnt in pnts]
                headings = [((180 * atan2(x,z) / pi) + 360 + 90 - ellipse_angle) % 360 for x,y,z in vectors]

                e = patches.Arc((-cx,cz), width, height, alpha=escape_alpha, ec=escape_colour, linewidth=0.5, angle=ellipse_angle, theta1=headings[0], theta2=headings[1], hatch='-'*13)   # beautiful hack to fill
                
                
                axs.add_patch(e)


        # (1) group into planes - DONE
        # [ shift planes by hostage height ] - DONE (cunningly)
        # (2) get circle in each plane - DONE
        # (3) 'intersect' to give the circular boundary - DONE
        # (4) 'tilt' into ellipse arcs and lines to view from above, draw - DONE! - hatching hack works beautifully

        

# Save the fig
fig.tight_layout(pad=0)

print("Saving..")
plt.savefig('frigate_deck_and_upstairs', bbox_inches='tight', pad_inches=0, dpi=254)   # 254 is 1 pixel per cm in GE world