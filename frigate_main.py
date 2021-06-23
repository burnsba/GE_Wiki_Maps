from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import findBisector, drawSetBoundaries
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil
from lib.fov import drawFOV
from lib.misc import *

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# FRIGATE SPECIFIC

from level_specific.frigate.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.frigate import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, opaque_objects
from level_specific.frigate.group_names import *

def frig_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO):
    # ------ Hostage escape areas ------
    HOSTAGE_HEIGHT = 105    # measured, varies +-9 but mostly + so this is pretty fair
    ESCAPE_PAD_NUMS = [0x91, 0x93, 0xA9, 0x94, 0xA8, 0x8f]  # best to worst (when unloaded at least)
    HOSTAGE_IDS = [0x2c, 0x2d, 0x30, 0x31, 0x34, 0x35]

    spheres = []

    for padNum in ESCAPE_PAD_NUMS:
        padPos = list(pads[padNum]["position"])
        padPos[1] -= HOSTAGE_HEIGHT
        spheres.append((tuple(padPos), 500))

    colourSphereIntesectionWithTiles(spheres, tilePlanes, tiles, plt, axs)

    # -----------------------------------

    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    STD_SPEED = 5.4807696015788     # from my lua GuardData.get_speed, used to print lengths which are handy
    HOSTAGE_NAME = {
        0x2C : "Bridge",
        0x34 : "SA",
        0x31 : "Slowest",
        0x35 : "Engine room",
        0x30 : "Near Agent",
        0x2D : "Far Agent",
    }

    fastestEscapeTimes = []
    for g_id in HOSTAGE_IDS:
        hostage = guards[guardAddrWithId[g_id]]
        np = hostage["near_pad"]
        escapeTimes = []
        for tp in ESCAPE_PAD_NUMS:

            # Get the path from near pad to potential target
            path = getPathBetweenPads(np, tp, sets, pads)
            if tp == 0x91:  # Even unloaded we'll escape at 8b (between stairs)
                assert path[-2] == 0x8b
                path = path[:-1]
            if g_id == 0x2c and tp == 0x91:
                tweaked_path = path[:path.index(0x4E)+1]
            else:
                tweaked_path = path

            expectedEscapedTime = getPathTime(hostage, tweaked_path, pads, STD_SPEED) / 60  # nearly certainly a lower bound
            escapeTimes.append((expectedEscapedTime, tp))

            # `hostage` also has ["position"], ["tile"] so we can pass it as an extra first point
            drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, hostage)

        eet, eep = min(escapeTimes)
        assert eep == 0x91  # everyone's best pad

        fastestEscapeTimes.append((eet, g_id))

    fastestEscapeTimes.sort()
    for eet, g_id in fastestEscapeTimes:
        # We could draw these by the hostage or something..
        pass ##print(f"{eet:.2f} : {HOSTAGE_NAME[g_id]}")
    

    ON_TOP_FLOOR = guards[guardAddrWithId[0x30]]["tile"] in currentTiles

    if ON_TOP_FLOOR and False:
        # Hacky FOV doesn't work too well & it's not too interesting.
        drawFOV(pads[0x003E], [0x07, 0x08, 0x2C], tiles, guards, objects, opaque_objects, plt,
            ignoreTileAddrs = [], objTransforms = {})
        drawFOV(guards[guardAddrWithId[0x10]], [0x09, 0x08, 0x2C], tiles, guards, objects, opaque_objects, plt,
            ignoreTileAddrs = [], objTransforms = {})


    

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

    # Call frig specific code
    frig_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DECK_AND_UPSTAIRS, 'frigate/frigate_deck_and_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MIDSHIPS, 'frigate/frigate_midships')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_LOWER_DECK, 'frigate/frigate_lower_deck')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_ENGINE_ROOM, 'frigate/frigate_engine_room')