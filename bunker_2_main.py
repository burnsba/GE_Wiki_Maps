from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# Bunker 2 SPECIFIC

from level_specific.bunker_2.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.bunker_2 import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects
from level_specific.bunker_2.group_names import *
import numpy as np
from lib.path_finding import rotACWS

STD_GUARD_SPEED = 5.4807696015788

def bunker_2_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    # Noise addition(s) with KF7
    maxNoise = 20
    noiseIncr = 2
    baseNoise = 2
    noises = [baseNoise + noiseIncr*i for i in range(1,ceil((maxNoise - baseNoise) / noiseIncr))] + [maxNoise]
    

    clipboardGuard = guards[guardAddrWithId[0x14]]
    cbGuardSpherePos = noiseAroundGuardHelper(clipboardGuard, [17.85, 19.85], tilePlanes, tiles, plt, axs, '#d1512e')

    keyGuard1 = guards[guardAddrWithId[0xB]]
    noiseAroundGuardHelper(keyGuard1, [3.966, 5.883, 7.809, 9.704, 11.528, 13.362], tilePlanes, tiles, plt, axs, '#bab21e')

    # Not so specific but we won't want to draw it on every map
    drawSetBoundaries(sets, pads, currentTiles, tiles, plt)

    # Creating the specific limit of the lure point
    tilesByName = dict((tile["name"], addr) for addr, tile in tiles.items())
    lureTiles = [tiles[tilesByName[n]] for n in [0x081F11, 0x080A11]]
    lureEdge = []
    for lt in lureTiles:
        i = lt["links"].index(0)
        i = (i+1) % len(lt["links"])
        lureEdge.append(lt["points"][i])
        lureEdge.append(lt["points"][i-1])

    p = lureEdge[0]
    maxDist, maxI = max((np.linalg.norm(np.subtract(p,q)),i) for i,q in enumerate(lureEdge[1:]))
    q = lureEdge[maxI]  # q extreme, p may not be
    v = np.subtract(p,q)
    v = np.multiply(v, 1 / np.linalg.norm(v))
    maxNorm, maxI = max((np.dot(v, np.subtract(r,q)), i) for i,r in enumerate(lureEdge))
    p = lureEdge[maxI]  # p now extreme

    # Get the halfplane (n,a)
    n = rotACWS(v)
    a = np.dot(n, q)

    # Get the displacement to the target
    t = cbGuardSpherePos[::2]
    b = np.dot(n, t)
    d = b - a

    # Orientate away from the target
    if d > 0:
        a = -a
        d = -d
        n = np.multiply(n, -1)
    
    # Shift away by Bond's radius, compute the 'remaining radius'
    br = 30
    d -= br
    sr = 19.85 * 100
    hd = cbGuardSpherePos[1] - lureTiles[0]["heights"][0]   # sphere pos subtracts bond height
    radius = sqrt(sr*sr - hd*hd - d*d)

    # Find the mid point on our line (q + b*v), then the new extremes
    b = np.dot(v, np.subtract(t,q))
    
    shift = np.multiply(br, n)
    p = np.add(np.add(q, np.multiply(b + radius, v)), shift)
    q = np.add(np.add(q, np.multiply(b - radius, v)), shift)
    
    # Draw
    lureEdge = (q,p)
    xs,zs = zip(*lureEdge)
    plt.plot([-x for x in xs], zs, linewidth=1, color='#1765e3')



    # ============

    # SA Henrik strat calculation
    nearPad = clipboardGuard["near_pad"]
    path = getPathBetweenPads(nearPad, 0x50, sets, pads)

    expectedTime = getPathTime(clipboardGuard, path, pads, STD_GUARD_SPEED) / 60 

    # `clipboardGuard` also has ["position"], ["tile"] so we can pass it as an extra first point
    drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, clipboardGuard)


# --------------------------------------------------------
# Generic stuff below 

def saveFig(plt, fig, path):
    width, height = fig.get_size_inches()

    # 12.5MP max when rescaling on the wiki.
    wikiDPI = sqrt(12500000 / (width * height))

    fig.tight_layout(pad=0)
    # (!) reduce the DPI if the map is too large
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=254)   # 254 is 1 pixel per cm in GE world
            


def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path):
    # Global (above a specific group) preperations
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)
    prepSets(sets, pads)

    # Group specific preperations
    currentTiles = set(tile_groups[GROUP_NO])
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call b2 specific code
    bunker_2_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_INSIDE, 'bunker_2/bunker_2_inside')