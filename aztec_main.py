from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, walkAcrossTiles
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos

# --------------------------------------------------------
# aztec SPECIFIC

from level_specific.aztec.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.aztec import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
from level_specific.aztec.group_names import *
import numpy as np

def aztec_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    mg = guards[guardAddrWithId[0x10]]

    # Draw a 'nose' to show which way he's facing
    heading = mg["facing_angle"]
    v = (sin(heading), cos(heading))
    q = np.add(mg["position"], np.multiply(v, 25))

    xs, zs = zip(mg["position"], q)
    plt.plot([-x for x in xs], zs, linewidth=0.5, color='k')

    blackRooms = [0x17, 0x16, 0x0E, 0x0D]
    def isTileInBlackRoom(ta, tiles):
        r = tiles[ta]["room"]
        return r in blackRooms

    # Noise for him too
    noiseAroundGuardHelper(mg, [19.85], tilePlanes, tiles, plt, axs, '#d1512e', base_alpha=1, fill=False,
        inclTileTest=isTileInBlackRoom)

    # And some line of sight-y tests
    # TODO move to a library

    currentBlackRoomTiles = [ta for ta in currentTiles if isTileInBlackRoom(ta, tiles)]

    for startTileAddr,startPoint,endData in [
        (0x1CC314, tiles[0x1CC314]["points"][0], [(0x1CC3B4, 0, []), (0x1CBC64, 0, [0x1CBC64])]),   # The two between pillars #0 and #1
        (mg["tile"], mg["position"], [(0x1CBBC4, 0, [0x1CBBC4])]),      # Mainframe guard to his side of #1
        (0x1CC404, tiles[0x1CC3B4]["points"][0], [(0x1CBC64, 0, [0x1CBC64])]),
    ]:
        for nextTileAddr,pi2,contAddrs in endData:
            q = tiles[nextTileAddr]["points"][pi2]
            v = np.subtract(q,startPoint)
            n = [-v[1], v[0]]
            n = np.multiply(n, 1 / np.linalg.norm(n)) 
            a = np.dot(n, startPoint)

            p = startPoint

            for ta in [startTileAddr] + contAddrs:
                _, _, r = walkAcrossTiles(ta, n, a, currentBlackRoomTiles, set([0]), tiles, endPoint=None, visitedTiles=None)

                xs, zs = zip(p,r)
                p = r
                plt.plot([-x for x in xs], zs, linewidth=0.5, color='k')

    
    

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
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    ##drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    aztec_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))




main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MAIN, "aztec/aztec_start")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_RATWAYS, "aztec/aztec_ratways")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_ENDING, "aztec/aztec_ending")