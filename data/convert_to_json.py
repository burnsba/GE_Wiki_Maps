import os.path
import json

levels = ['archives', 'aztec', 'bunker_1', 'bunker_2', 'caverns', 'control', 'cradle', 'dam', 'depot', 'egyptian', 'facility', 'frigate', 'jungle', 'runway', 'silo', 'statue', 'streets', 'surface_1', 'surface_2', 'train']
for level in levels:

    versions = [level, level+"_pal"]
    for base_name in versions:
    
        if os.path.isfile(base_name+".py"):
        
            output_name = base_name+".json"
            
            stuff = __import__(base_name)

            level_scale = getattr(stuff, "level_scale")
            tiles = getattr(stuff, "tiles")
            sets = getattr(stuff, "sets")
            objects = getattr(stuff, "objects")
            activatable_objects = getattr(stuff, "activatable_objects")
            opaque_objects = getattr(stuff, "opaque_objects")
            guards = getattr(stuff, "guards")
            pads = getattr(stuff, "pads")
            lone_pads = getattr(stuff, "lone_pads")

            ge_setup = {
                "level_scale" : level_scale,
                "tiles" : tiles,
                "sets" : sets,
                "objects" : objects,
                "activatable_objects" : activatable_objects,
                "opaque_objects" : opaque_objects,
                "guards" : guards,
                "pads" : pads,
                "lone_pads" : lone_pads
            }
            
            with open(output_name,'w') as f:
                f.write(json.dumps(ge_setup, indent=4))