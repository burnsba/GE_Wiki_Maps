from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries, drawSets
from lib.near_geoms import computeNearGeoms, drawNearGeoms
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos

# --------------------------------------------------------
# surface_1 SPECIFIC

from level_specific.surface_1.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.surface_1 import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
from level_specific.surface_1.group_names import *
import numpy as np


def surface_1_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    bg = guards[guardAddrWithId[0x13]]

    # For OOK-y thoughts, colour by set
    colourForSet = [np.random.rand(3,) for s in sets]   # sets are numbered 0,1,..
    def colourBySet(pd):
        return colourForSet[pd['set']]
        
    # Draw line through the points
    pntA = pads[0x00A3]["position"][::2]
    pntB = tiles[0x1B9EC4]["points"][1]
    xs, zs = map(list, zip(*[pntA, pntB]))
    v_x = (xs[1] - xs[0])*1.5
    v_z = (zs[1] - zs[0])*1.5
    xs[1] += v_x
    zs[1] += v_z
    xs = [-x for x in xs]
    plt.plot(xs, zs, linewidth=3, color='k')

    computeNearGeoms(pads, tiles)
    drawNearGeoms(pads, axs, colouring=colourBySet)

    # Something worth generalising perhaps
    # Draw the important border between rooms 5 and 7

    for ta, td in tiles.items():
        if td['room'] != 0x5:
            continue
        for i,na in enumerate(td["links"]):
            if na == 0:
                continue
            if tiles[na]['room'] != 0x7:
                continue
            p,q = (td['points'] + [td['points'][0]])[i:i+2]
            xs, zs = map(list, zip(*[p,q]))
            xs = [-x for x in xs]
            plt.plot(xs, zs, linewidth=5, color='k')

    # OOK calculation
    STD_SPEED = 5.4807696015788
    bgp = getPathBetweenPads(0x00A3, 0x0092, sets, pads)
    t = getPathTime(bg, bgp, pads, STD_SPEED) / 60

# --------------------------------------------------------
# Generic stuff below 


def saveFig(plt, fig, path, useWikiDpi):
    width, height = fig.get_size_inches()

    # 12.5MP max when rescaling on the wiki.
    wikiDPI = sqrt(12500000 / (width * height))
    stdDPI = 254 # 254 is 1 pixel per cm in GE world
    dpi = wikiDPI if useWikiDpi else stdDPI

    fig.tight_layout(pad=0)
    # (!) reduce the DPI if the map is too large
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)   
            


def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path, useWikiDpi=False):
    # Global (above a specific group) preperations
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)
    prepSets(sets, pads)

    # Group specific preperations
    currentTiles = set(tile_groups[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawSets(sets, pads, lone_pads, currentTiles, tiles, plt, axs, scale=5)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    surface_1_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path),useWikiDpi)

main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, "surface_1/surface_1_B")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, "surface_1/surface_1_C")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 3, "surface_1/surface_1_D")

print("Making massive main map..")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, "surface_1/surface_1_A", True)
print("Done")