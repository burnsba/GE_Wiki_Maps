
# Frigate divisions.
# Include them the first time we reach them, but not again

dividingTiles = [
    0x021F01, # left balcony
    0x021D01, # right balcony
    0x00142A, # garage door (not vertical)

    0x018119, # dividing first stairs
    0x06FF19,

    0x022721, # dividing pipe warp stairs
    0x056F21,

    0x020821, # dividing internal stairs
    0x059221,

    0x061831, # left engine room stairs
    0x060931, # right engine room stairs
]

startTileName = 0x004618

# Doors which we don't want reachability drawn for
excludeDoorReachPresets = [
    # Upper middle doors - irrel
    0x275F,
    0x2760,
    0x275E,
    0x275D,
    0x275C,
    0x275B,

    # Door to bug throw is needed for SA despite messyness

    0x2763, # other door to the helicopter, never used.
]