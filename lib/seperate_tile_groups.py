

def seperateGroups(tiles, startTileName, dividingTiles):
    dividingTiles = set(dividingTiles)

    groups = []
    stack = []
    currTile = dict((tile["name"], addr) for addr, tile in tiles.items())[startTileName]
    currGroup = []
    count = 0
    groupGood = False

    ##print("Initial tile at 0x{:x}".format(currTile))

    visited = set([0, currTile])  # Null tile not visitable

    while count < len(tiles):
        currGroup.append(currTile)
        count += 1

        assert currTile in tiles

        links = tiles.get(currTile, {}).get("links", [])
        for link in links:
            if link == 0:
                continue

            name = tiles[link]["name"]

            groupGood = groupGood or (name in dividingTiles)

            if link in visited:
                continue

            # If we first meet it, add it our group but not the stack
            if name in dividingTiles:
                currGroup.append(link)
            else:
                stack.append(link)

            # Regardless add the link
            visited.add(link)


        if len(stack) > 0:
            currTile = stack.pop()
        else:
            if groupGood:
                groups.append(currGroup)
            groupGood = False

            currGroup = []
            # Fetch a new tile
            for link in tiles:  # TODO make me more deterministic (across platforms)
                if link not in visited:
                    currTile = link
                    visited.add(currTile)
                    break


    assert len(currGroup) == 0
    return groups