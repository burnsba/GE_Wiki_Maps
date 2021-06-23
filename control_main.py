from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil

# --------------------------------------------------------
# Control SPECIFIC

from level_specific.control.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.control import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects
from level_specific.control.group_names import *
import numpy as np
from lib.path_finding import rotACWS


def control_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    # Nothing so far    

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

    # Call specific code
    control_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))



main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_CONTROL_MAIN, "control/control_main")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, "control/protect_mid_floor")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, "control/protect_upper_floor")