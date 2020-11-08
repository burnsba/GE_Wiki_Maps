
# Facility divisions.
# Include them the first time we reach them, but not again

dividingTiles = [
    # Stairs have sides so are hard to break up
    0x019809,
    0x01C30A,   # side

    0x09740A,
    0x097C09,   # side

    # More normal stairs
    0x008C12,
    0x078E19,
    0x005012,

    # Upper exits, since these link upstairs and down
    # Should be claimed by the upstairs gang
    0x062A18,
    ##0x062918,
    0x062B18,
    ##0x062C18,
    ##0x062D18,
    0x062E18,
    """
    # Upstairs split
    0x015E19,
    0x017019,
    0x017919,
"""
]

startTileName = 0x009B1A   # so upstairs claims the jumps

excludeDoorReachPresets = [

]