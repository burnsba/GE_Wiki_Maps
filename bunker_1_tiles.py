# Modernised from 'spaces.py'
# Just shows in the interactive plot atm

from data.bunker_1 import tiles, pads, objects, guards
from lib.near_geoms import computeNearGeoms, drawNearGeoms
from lib.set_boundaries import drawNavGraph
import matplotlib.pyplot as plt

guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
boris = guards[guardAddrWithId[0x19]]

# Init global plot
fig, axs = plt.subplots()
axs.set_aspect('equal', 'datalim')

drawNavGraph(pads, plt, axs, edgeColour='w')

computeNearGeoms(pads, tiles)
drawNearGeoms(pads, axs)

# Special point for Boris
boris_x, boris_z = boris["position"]
axs.scatter([-boris_x], [boris_z])
axs.annotate("Boris", (-boris_x, boris_z))
axs.add_artist(plt.Circle((-boris_x, boris_z), 500, color='k', linewidth=1, fill=False))
axs.add_artist(plt.Circle((-boris_x, boris_z), 150, color='g', linewidth=1, fill=False))

# Objects
for addr, obj in objects.items():
    if "points" not in obj:
        continue
    xs, zs = zip(*obj["points"])
    xs = [-x for x in xs]
    xs += (xs[0],)
    zs += (zs[0],)
    plt.plot(xs, zs, linewidth=0.5, color='k')

plt.show()