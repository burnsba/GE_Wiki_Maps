from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.sphere_intersect_tiles import colourSphereIntesectionWithTiles
import matplotlib.pyplot as plt
import os


# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# FRIGATE SPECIFIC

from level_specific.frigate.divisions import dividingTiles, startTileName
from data.frigate import tiles, guards, objects, pads, level_scale
from level_specific.frigate.group_names import *

def frig_specific(tilePlanes, tiles, plt, axs):
    HOSTAGE_HEIGHT = 105    # measured, varies +-9 but mostly + so this is pretty fair
    ESCAPE_PAD_NUMS = [0x91, 0x93, 0xA9, 0x94, 0xA8, 0x8f]  # best to worst (when unloaded at least)

    spheres = []

    for padNum in ESCAPE_PAD_NUMS:
        padPos = list(pads[padNum]["position"])
        padPos[1] -= HOSTAGE_HEIGHT
        spheres.append((tuple(padPos), 500))

    colourSphereIntesectionWithTiles(spheres, tilePlanes, tiles, plt, axs)

# --------------------------------------------------------

def drawGuards(guards, currentTiles, axs):
    # Too simple for it's own module atm
    for addr, gd in guards.items():
        if gd["tile"] not in currentTiles:
            continue
        x,z = gd["position"]
        axs.add_artist(plt.Circle((-x, z), gd["radius"], color='g', linewidth=1, fill=False))

def saveFig(plt, fig, path):
    fig.tight_layout(pad=0)
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=254)   # 254 is 1 pixel per cm in GE world

def connectedComponents(tileAddrs, tiles):
    stack = []
    comps = []
    seen = set([0]) # null tile
    universe = set(tileAddrs)

    i = 0

    while i < len(tileAddrs):
        tileAddr = tileAddrs[i]
        if tileAddr in seen:
            i += 1
        else:
            # New tileAddr
            stack = [tileAddr]
            seen.add(tileAddr)
            currComp = []

            while len(stack) > 0:
                tileAddr = stack.pop()
                currComp.append(tileAddr)

                for link in tiles[tileAddr]["links"]:
                    # Only ever add it to the link once
                    # Restrict to just the tiles we're interested in
                    if link not in seen and link in universe:
                        seen.add(link)
                        stack.append(link)
            
            comps.append(currComp)
    
    return comps


def markStairs(tilePlanes, tiles, plt):
    for (n,a), tileAddrs in tilePlanes.items():
        if n[1] != 0:
            continue
        
        comps = connectedComponents(tileAddrs, tiles)

        # Plane is vertical, so it's just a series of line segments from above
        # Group into connected components then compare

        # Search for the two most extreme points
        # This works because if x varies on the line, we are just comparing by x
        # Otherwise we are just comparing by z

        for comp in comps:
            min_p = max_p = tiles[comp[0]]["points"][0]
            for tileAddr in comp:
                td = tiles[tileAddr]
                for p in td["points"]:
                    min_p = min(min_p, p)
                    max_p = max(max_p, p)
            
            xs, zs = zip(min_p, max_p)
            plt.plot([-x for x in xs], zs, linewidth=0.5, color='b')
            

def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path):
    # Global (above a specific group) preperations
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)

    # Group specific preperations
    currentTiles = set(tile_groups[GROUP_NO])
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)

    # Draw stuff :) 
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)
    drawGuards(guards, currentTiles, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)

    # Testing
    markStairs(tilePlanes, tiles, plt)

    # Call frig specific code
    frig_specific(tilePlanes, tiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DECK_AND_UPSTAIRS, 'frigate_deck_and_upstairs')
