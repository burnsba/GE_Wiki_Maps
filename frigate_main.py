from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# FRIGATE SPECIFIC

from level_specific.frigate.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.frigate import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects
from level_specific.frigate.group_names import *

def frig_specific(tilePlanes, currentTiles, plt, axs):
    # ------ Hostage escape areas ------
    HOSTAGE_HEIGHT = 105    # measured, varies +-9 but mostly + so this is pretty fair
    BOND_HEIGHT = 167.3     # measured, standing on a flat tile
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


    # Noise addition(s) with D5K
    maxNoise = 7
    noiseIncr = 1.2
    noises = [noiseIncr*i for i in range(1,ceil(maxNoise / noiseIncr))] + [maxNoise]
    # Override with slightly more sensible ones
    noises = [1.17, 2.27, 3.37, 4.43, 5.45, 6.38, 6.9125]
    noise4_25 = (3*noises[3] + noises[4]) / 4   # barely more than 4 reaches the height

    # Create the point using the guard's height and our height above the tiles
    nadeGuard2 = guards[guardAddrWithId[0x22]]
    gx, gz = nadeGuard2["position"]
    gh = nadeGuard2["height"]
    spherePos = (gx, gh - BOND_HEIGHT, gz)

    # Through away all tiles which aren't above the hostage
    higherTilePlanes = {}
    for plane, tileAddrs in tilePlanes.items():
        highTiles = [ta for ta in tileAddrs if max(tiles[ta]["heights"]) > gh]
        higherTilePlanes[plane] = highTiles


    # Start with the loudest
    for noise in noises[::-1]:
        sphere = (spherePos, noise*100)
        colourSphereIntesectionWithTiles([sphere], higherTilePlanes, tiles, plt, axs, base_colour='#d1512e')


# --------------------------------------------------------
# Generic stuff below 

def drawGuards(guards, currentTiles, axs):
    # Too simple for it's own module atm
    for addr, gd in guards.items():
        if gd["tile"] not in currentTiles:
            continue
        x,z = gd["position"]
        axs.add_artist(plt.Circle((-x, z), gd["radius"], color='g', linewidth=1, fill=False))

def drawCollectibles(objects, axs, currentTiles):
    # Also currently very simple, though we may add more detail to each type,
    # i.e. draw the ammo box / BA / a key shape.

    # ---- How we should be doing it ----
    # Is going to need to go in a lib though - we're drawing for all groups atm
    # So we need some bounds on Bond's height (crouching -> max)

    # Shift source down by Bond's minimum height, then be generous with max.
    # Cylinder not a sphere don't forget. Could be slightly tricky with sloping tiles.
    # Maybe first clip the tile between these heights. Won't be so hard since convex and flat.

    # For the extra check, get all current tiles within the specified radius which are reachable (not usable in the sphere code)

    # Can borrow the actual 'draw circle intersect tiles' from 
    # Just flatten the tiles.. after clipping using above code.

    # ---- How we're actually doing it.. just draw a circle :) ----

    colours = {
        "key" : (1,0.45,0),  # orange
        "body_armour" : (0,0.1,0.3), # blue
    }
    default_colour = (0,0,0)    # black : ammo_box, ammo, weapon

    for od in objects.values():
        if not od["collectible"]:
            continue
        if od["tile"] not in currentTiles:  # oversimplification - fixme eventually
            continue

        x,z = od["position"]
        colour = colours.get(od["type"], default_colour)
        # 1m radius hardcoded. Also needs to have LOS iirc.
        axs.add_artist(plt.Circle((-x, z), 100, color=colour, linewidth=1, fill=False))


def drawActivatables(axs, activatable_objects, objects, currentTiles):
    for objAddr in activatable_objects:
        od = objects[objAddr]
        if od["tile"] not in currentTiles:
            continue
        
        radius = 200    ## & 22.5 degrees
        if od["type"] == "aircraft":
            radius = 400    ## & 120 degrees

        x,z = od["position"]
        axs.add_artist(plt.Circle((-x, z), radius, color='g', linewidth=1, fill=False))



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

    drawGuards(guards, currentTiles, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, axs, currentTiles)

    drawActivatables(axs, activatable_objects, objects, currentTiles)

    # Call frig specific code
    frig_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DECK_AND_UPSTAIRS, 'frigate_deck_and_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MIDSHIPS, 'frigate_midships')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_LOWER_DECK, 'frigate_lower_deck')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_ENGINE_ROOM, 'frigate_engine_room')