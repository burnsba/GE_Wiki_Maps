
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


def markStairs(tilePlanes, tiles, colour, plt):
    for (n,a), tileAddrs in tilePlanes.items():
        if n[1] != 0:
            continue
        
        # Plane is vertical, so it's just a series of line segments from above
        # Group into connected components then compare

        comps = connectedComponents(tileAddrs, tiles)

        # Search for the two most extreme points
        # This works because if x varies on the line, we are just comparing by x
        # Otherwise x is constant and we are just comparing by z
        # Either way we get the endpoints

        for comp in comps:
            min_p = max_p = tiles[comp[0]]["points"][0]
            for tileAddr in comp:
                td = tiles[tileAddr]
                for p in td["points"]:
                    min_p = min(min_p, p)
                    max_p = max(max_p, p)
            
            xs, zs = zip(min_p, max_p)
            plt.plot([-x for x in xs], zs, linewidth=0.5, color=colour)