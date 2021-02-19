
# Caverns divisions
# Include them the first time we reach them, but not again
dividingTiles = [
    0x0E2F02,   # Stairs down from A
    0x0E1602,   # Stairs up to A

    0x01F508,   # 3/4th around the spiral
    0x021208,   # 13/8th around maybe :)

    0x10A812,   # Stairs at SC
    0x10BC11,   # Stairs near radio room
    0x11C210,   # Into secret passway room - we don't want to divide the secret passway
]

startTileName = 0x003828

# Doors which we don't want reachability drawn for
excludeDoorReachPresets = [
]