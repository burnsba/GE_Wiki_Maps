from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
import matplotlib.pyplot as plt
import os


# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# FRIGATE SPECIFIC

from level_specific.frigate.divisions import dividingTiles, startTileName
from data.frigate import tiles, guards, objects, pads, level_scale, sets, presets
from level_specific.frigate.group_names import *

def frig_specific(tilePlanes, currentTiles, plt, axs):
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

    for g_id in HOSTAGE_IDS:
        hostage = guards[guardAddrWithId[g_id]]
        np = hostage["near_pad"]
        for tp in ESCAPE_PAD_NUMS:

            # Get the path from near pad to potential target
            path = getPathBetweenPads(np, tp, sets, pads)

            # `hostage` also has ["position"], ["tile"] so we can pass it as an extra first point
            drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, hostage)


# --------------------------------------------------------
# Generic stuff below 

def drawGuards(guards, currentTiles, axs):
    # Too simple for it's own module atm
    for addr, gd in guards.items():
        if gd["tile"] not in currentTiles:
            continue
        x,z = gd["position"]
        axs.add_artist(plt.Circle((-x, z), gd["radius"], color='g', linewidth=1, fill=False))

def drawCollectibles(objects, axs):
    # Also currently very simple, though we may add more detail to each type,
    # i.e. draw the ammo box / BA / a key shape, and use different colours

    # Is going to need to go in a lib though - we're drawing for all groups atm
    # So we need some bounds on Bond's height (crouching -> max)

    # Shift source down by Bond's minimum height, then be generous with max.
    # Cylinder not a sphere don't forget. Could be slightly tricky with sloping tiles.
    # Maybe first clip the tile between these heights. Won't be so hard since convex and flat.

    # For the extra check, get all current tiles within the specified radius which are reachable (not usable in the sphere code)
    # Probably just iterate through them all.
    # If there are any -> business :)
    # Going to need this for the key on S1!

    # Can borrow the actual 'draw circle intersect tiles' from 
    # Just flatten the tiles.. after clipping using above code.

    for od in objects.values():
        if od["collectible"]:
            x,z = od["position"]
            axs.add_artist(plt.Circle((-x, z), 100, color=(1,0.45,0), linewidth=1, fill=False))

def saveFig(plt, fig, path):
    fig.tight_layout(pad=0)
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

    drawGuards(guards, currentTiles, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles)
    drawCollectibles(objects, axs)

    # Call frig specific code
    frig_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DECK_AND_UPSTAIRS, 'frigate_deck_and_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MIDSHIPS, 'frigate_midships')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_LOWER_DECK, 'frigate_lower_deck')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_ENGINE_ROOM, 'frigate_engine_room')