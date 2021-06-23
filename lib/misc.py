from .circle_related import colourSphereIntesectionWithTiles

BOND_HEIGHT = 167.3     # measured in frigate, standing on a flat tile

def noiseAroundGuardHelper(guardData, noises, tilePlanes, tiles, plt, axs, base_colour, base_alpha=0.1, fill=True, inclTileTest=None):

    # Create the point using the guard's height and our height above the tiles
    gx, gz = guardData["position"]
    gh = guardData["height"]
    spherePos = (gx, gh - BOND_HEIGHT, gz)

    # Start with the loudest
    for noise in noises[::-1]:
        sphere = (spherePos, noise*100)
        colourSphereIntesectionWithTiles([sphere], tilePlanes, tiles, plt, axs, base_colour=base_colour, base_alpha=base_alpha, fill=fill, inclTileTest=inclTileTest)

    return spherePos


def drawGuards(guards, currentTiles, plt, axs):
    # Too simple for it's own module atm
    for addr, gd in guards.items():
        if gd["tile"] not in currentTiles:
            continue
        x,z = gd["position"]
        nadeOdds = gd["grenade_odds"]
        axs.add_artist(plt.Circle((-x, z), gd["radius"], color=('g' if nadeOdds == 0 else 'r'), linewidth=1, fill=False))

def drawCollectibles(objects, plt, axs, currentTiles):
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


def drawActivatables(plt, axs, activatable_objects, objects, currentTiles):
    for objAddr in activatable_objects:
        od = objects[objAddr]
        if od["tile"] not in currentTiles:
            continue
        
        radius = 200    ## & 22.5 degrees
        if od["type"] == "aircraft":
            radius = 400    ## & 120 degrees

        x,z = od["position"]
        axs.add_artist(plt.Circle((-x, z), radius, color='g', linewidth=1, fill=False))

