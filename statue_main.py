from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.sphere_intersect_tiles import colourSphereIntesectionWithTiles
import matplotlib.pyplot as plt
import os


# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customise what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# STATUE SPECIFIC

dividingTiles = []
startTileName = 0x07FA00
from data.statue import tiles, guards, objects, pads, level_scale

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

def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path):
    # Global (above a specific group) preperations
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    assert len(tile_groups) == 1
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

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, 'statue_test')
