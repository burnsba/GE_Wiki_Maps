require "Data\\GE\\PositionData"
require "Data\\GE\\GameData"
require "Data\\GE\\ObjectData"
require "Utilities\\GE\\ObjectDataReader"
require "Utilities\\GE\\GuardDataReader"
require "Data\\GE\\PresetData"
require "Data\\GE\\ScriptData"

-- ===========================================
local PRINT_TILES = true
local PRINT_OBJECTS = true
local PRINT_GUARDS = true
local PRINT_PADS = true
local PRINT_SETS = true
local PRINT_PRESETS = true

PRINT_OBJECTS = PRINT_OBJECTS and PRINT_TILES   -- objects needs tiles to get all rooms

local mission_name = GameData.get_mission_name(GameData.get_current_mission())
local filename = ("data\\" .. mission_name .. ".py"):lower()
console.log("Dumping to " .. filename)

-- ===========================================

file = io.open(filename, "w")

local scale = GameData.get_scale()
local all_tiles = TileData.getAllTiles()

file:write("level_scale = " .. scale .. "\n")

allRooms = {}   -- read from tiles to be safe because they aren't always contigious

if PRINT_TILES then
    file:write("tiles = {", "\n")
    isRoom = {}
    for i, tile in ipairs(all_tiles) do
        file:write(("0x%06X"):format(tile) .. " : {", "\n")
        file:write("  \"points\" : [")
        for _, pnt in ipairs(TileData.get_points(tile, scale)) do
            file:write(" (" .. pnt.x .. ", " .. pnt.z .. "),")
        end
        file:write("  ],", "\n")

        -- Seperate out the heights
        file:write("  \"heights\" : [")
        for _, pnt in ipairs(TileData.get_points(tile, scale)) do
            file:write(" " .. pnt.y .. ",")
        end
        file:write("  ],", "\n")

        local room = TileData:get_value(tile, "room")
        file:write("  \"room\" : " .. ("0x%04X"):format(room) .. ",", "\n")
        isRoom[room] = true
        
        file:write("  \"links\" : [")
        local links = TileData.get_links(tile)
        for _, lnk in ipairs(links) do
            file:write(("0x%06X, "):format(lnk))
        end
        file:write("],", "\n")
        file:write("  \"name\" : " .. ("0x%06X"):format(TileData:get_value(tile, "name")) .. ",", "\n")

        file:write("},", "\n")
    end
    file:write("}", "\n")

    for room, _ in pairs(isRoom) do
        table.insert(allRooms, room)
    end
end


local pdp, tile, room
local pdpLit = "position_data_pointer"

local typeNames = {
    [0x01] = "door",
    [0x02] = "-", -- DoorScaleData,
    [0x03] = "generic",
    [0x04] = "key", 
    [0x05] = "alarm",
    [0x06] = "camera",
    [0x07] = "ammo",
    [0x08] = "weapon",
    [0x09] = "character",
    [0x0A] = "monitor",
    [0x0B] = "monitor", -- multi
    [0x0C] = "monitor", -- ceiling
    [0x0D] = "drone",
    [0x0E] = "-",
    [0x11] = "-",   -- hat
    [0x12] = "-",   -- grenade odds
    [0x13] = "-",
    [0x14] = "ammo",
    [0x15] = "body_armour",
    [0x16] = "-",
    [0x17] = "-",
    [0x23] = "-",
    [0x24] = "gas_container",
    [0x25] = "-", 
    [0x26] = "lock",
    [0x27] = "vehicle",
    [0x28] = "aircraft",
    [0x2A] = "glass",
    [0x2B] = "safe",
    [0x2C] = "safe_object",
    [0x2D] = "tank",
    [0x2E] = "",
    [0x2F] = "glass",
}
-- Special ones include grenade data (but we'll read this elsewhere), and lock data

if PRINT_OBJECTS then
    file:write("from math import nan\n")
    file:write("\n\nobjects = {", "\n")
    local isCollectible = ObjectData.getAllCollectables()

    ObjectDataReader.for_each(function(odr)

        local tile = 0
        local position = 0
        if odr:has_value(pdpLit) then
            local pdp = odr:get_value(pdpLit)
            if pdp ~= 0 then
                pdp = pdp - 0x80000000
                
                tile = PositionData:get_value(pdp, "tile_pointer")
                if tile ~= 0 then
                    tile = tile - 0x80000000
                end

                position = PositionData:get_value(pdp, "position")
            end
        end

        local type = typeNames[ObjectData.get_type(odr.current_address)]

        local B_1 = (tile ~= 0) -- and odr:is_collidable())
        local B_2 = (type == "lock")    -- not sure about this

        if (B_1 or B_2) then
            file:write(("0x%06X"):format(odr.current_address) .. " : {", "\n")

            if odr:has_value("preset") then -- has physical obj data
                file:write("  \"preset\" : " .. ("0x%04X"):format(odr:get_value("preset")) .. ",", "\n") -- handy for finding objects
                file:write("  \"flags_1\" : " .. ("0x%08X"):format(odr:get_value("flags_1")) .. ",", "\n")
                local presetPoints = getPresetPoints(odr.current_address)
                file:write("  \"preset_points\" : [")
                for i=1,4,1 do
                    file:write("(" .. presetPoints[i].x .. ", " .. presetPoints[i].z .. "), ")
                end
                file:write("],", "\n")
            end
            
            local collectible = isCollectible[odr.current_address]
            file:write("  \"collectible\" : " .. (collectible and "True" or "False") .. ",", "\n")

            if odr:is_collidable() then
                local points, min_y, max_y = odr:get_collision_data()
                file:write("  \"points\" : [")
                for _, pnt in ipairs(points) do
                    file:write("(" .. pnt.x .. ", " .. pnt.y .. "), ")
                end
                file:write("],", "\n")
                file:write("  \"height_range\" : (" .. min_y .. ", " .. max_y .. "),", "\n")
            end

            if tile ~= 0 then   
                file:write("  \"tile\" : " .. ("0x%06X"):format(tile) .. ",", "\n")
            end

            if position ~= 0 then
                file:write("  \"position\" : (" .. position.x .. ", " .. position.z .. "),", "\n")
            end

            if odr:has_value("health") then
                file:write("  \"health\" : " .. odr:get_value("health") .. ",", "\n")
            end
            
            if type == "door" then
                local doorType = DoorData:get_value(odr.current_address, "hinge_type")  -- 4 is roller door?
                local hingePositions = doorDataGetHinges(odr.current_address)
                file:write("  \"door_type\" : " .. doorType .. ",", "\n")
                file:write("  \"hinges\" : [")
                if table.getn(hingePositions) > 0 then
                    file:write("\n")
                end
                for _, hingePos in ipairs(hingePositions) do
                    file:write("    (" .. hingePos.x .. ", " .. hingePos.z .. "),", "\n")
                end
                file:write("  ],", "\n")

            end

            file:write("  \"type\" : \"" .. type .. "\",", "\n")
            file:write("},", "\n")
        end
    end)

    file:write("}", "\n")

    -- activatable objects
    file:write("activatable_objects = [", "\n")
    local actObjs = ScriptData.getActivatableObjects()
    for _, objAddr in ipairs(actObjs) do
        file:write(("  0x%06X"):format(objAddr) .. ",", "\n")
    end
    file:write("]", "\n")

    -- opaque objects in each room (block LOS)
    file:write("opaque_objects = {", "\n")
    for _, room in ipairs(allRooms) do
        file:write(("  0x%02X : ["):format(room))
        posDatasInRoom = PositionData.getCollidablesInRooms({room,})[room]
        for _, pd in ipairs(posDatasInRoom) do
            local odp = PositionData:get_value(pd, "object_data_pointer") - 0x80000000

            -- 0x11B in CMD 0x3C's data. Also ditch guards.
            if PositionData:get_value(pd, "object_type") ~= 3 and PositionData.checkFlags(pd, 0x11B) then  
                file:write(("0x%06X, "):format(odp))
            end
        end
        file:write("],", "\n")
    end
    file:write("}", "\n")
end

if PRINT_GUARDS then
    file:write("\nguards = {", "\n")
    GuardDataReader.for_each(function(gdr)
        local pdp = gdr:get_value("position_data_pointer") - 0x80000000
        local pos = PositionData:get_value(pdp, "position")
        local tile = PositionData:get_value(pdp, "tile_pointer") - 0x80000000
        local near_pad = PositionData.getNearPad(pdp)
        local cr = gdr:get_value("collision_radius")
        local id = gdr:get_value("id")
        local grenadeOdds = gdr:get_value("belligerency")
        file:write(("0x%06X"):format(gdr.current_address) .. " : {", "\n")
        file:write("  \"position\" : (" .. pos.x .. ", " .. pos.z .. "),", "\n") -- historically no y, so added seperately as height
        file:write("  \"height\" : " .. pos.y .. ",", "\n")
        file:write("  \"tile\" : " .. ("0x%06X"):format(tile) .. ",", "\n")
        file:write("  \"near_pad\" : " .. ("0x%04X"):format(near_pad) .. ",", "\n")
        file:write("  \"radius\" : " .. cr .. ",", "\n")
        file:write(("  \"id\" : 0x%04X,"):format(id), "\n")
        file:write("  \"grenade_odds\" : " .. grenadeOdds .. ",", "\n")
        file:write("},", "\n")
    end)

    file:write("}", "\n")
end

if PRINT_PADS then
    file:write("\npads = {", "\n")

    local somePadInfo = memory.read_u32_be(0x075d18) - 0x80000000
    local padPtr = PadData.get_start_address()
    local index = 0
	while true do
		local n = PadData:get_value(padPtr, "number")
        if n == -1 then
            break
        end
        local pos = PadData.padPosFromNum(n)
        local set = PadData:get_value(padPtr, "setIndex")
        local assocTile = memory.read_u32_be(somePadInfo + (0x2c * n) + 0x28) - 0x80000000

        file:write(("0x%04X : {\n"):format(n))
        file:write("  \"index\" : " .. index .. ",", "\n")
        file:write("  \"position\" : (" .. pos.x .. ", " .. pos.y .. ", " .. pos.z .. "),", "\n")
        file:write("  \"neighbours\" : [")
        for _, neighbour in ipairs(PadData.get_pad_neighbours(padPtr)) do
            file:write(("0x%04X, "):format(neighbour))
        end
        file:write("],", "\n")
        file:write(("  \"set\" : 0x%02X,"):format(set), "\n")
        file:write(("  \"tile\" : 0x%06X,"):format(assocTile), "\n")
        file:write("},", "\n")
    
        padPtr = padPtr + 0x10
        index = index + 1
    end
    
    file:write("}", "\n")
end

if PRINT_SETS then
    -- We say that a set is it's index, unlike for pads where they have a seperate number
    file:write("\nsets = [", "\n")
    local setPtr = SetData.get_start_address()
    while true do
        local neighbours = SetData.get_set_neighbours(setPtr)
        if neighbours == nil then
            break
        end
        file:write("{", "\n")
        file:write("  \"neighbours\" : [")
        for _, nSet in ipairs(neighbours) do
            file:write(("0x%02X, "):format(nSet))
        end
        file:write("],", "\n")

        local pads = SetData.get_set_pads(setPtr)
        file:write("  \"pad_indices\" : [")
        for _, pad in ipairs(pads) do
            file:write(("0x%04X, "):format(pad))
        end
        file:write("],", "\n")
        file:write("},", "\n")

        -- update
        setPtr = setPtr + 0xc
    end
    file:write("]", "\n")
end

if PRINT_PRESETS then
    file:write("\npresets = {", "\n")
    local currPresetAddr = PresetData.get_start_address()
    local presetEnd = PresetData.get_end_address()
    assert((presetEnd - currPresetAddr) % 0x44 == 0)

    local count = 0
    while currPresetAddr < presetEnd do
        -- We output in 0x27XX (100YY) format, since that seems clearer.
        -- Many cases have their 10000 removed already, i.e. doors

        local pos = PresetData:get_value(currPresetAddr, "position")
        local norm_x = PresetData:get_value(currPresetAddr, "normal_x")
        local norm_y = PresetData:get_value(currPresetAddr, "normal_y")
        local low_x = PresetData:get_value(currPresetAddr, "low_x")
        local low_y = PresetData:get_value(currPresetAddr, "low_y")
        local low_z = PresetData:get_value(currPresetAddr, "low_z")
        local high_x = PresetData:get_value(currPresetAddr, "high_x")
        local high_y = PresetData:get_value(currPresetAddr, "high_y")
        local high_z = PresetData:get_value(currPresetAddr, "high_z")
        local tile = PresetData:get_value(currPresetAddr, "tile_pointer")
        if (tile > 0) then
            tile = tile - 0x80000000
        end

        -- Produce normal_z as cross product
        local norm_z = {
            ["z"] = (norm_x.x * norm_y.y - norm_y.x * norm_x.y),
            ["x"] = (norm_x.y * norm_y.z - norm_y.y * norm_x.z),
            ["y"] = (norm_x.z * norm_y.x - norm_y.z * norm_x.x),
        }
        
        file:write(("0x%04X : {\n"):format(10000 + count))
        file:write("  \"position\" : (" .. pos.x .. ", " .. pos.y .. ", " .. pos.z .. "),", "\n")
        file:write("  \"normal_x\" : (" .. norm_x.x .. ", " .. norm_x.y .. ", " .. norm_x.z .. "),", "\n")
        file:write("  \"normal_y\" : (" .. norm_y.x .. ", " .. norm_y.y .. ", " .. norm_y.z .. "),", "\n")
        file:write("  \"normal_z\" : (" .. norm_z.x .. ", " .. norm_z.y .. ", " .. norm_z.z .. "),", "\n")
        -- we'll produce normal_z in Python
        file:write(("  \"tile\" : 0x%06X,"):format(tile), "\n")
        file:write("  \"x_limits\" : (" .. low_x .. ", " .. high_x .. "),", "\n")
        file:write("  \"y_limits\" : (" .. low_y .. ", " .. high_y .. "),", "\n")
        file:write("  \"z_limits\" : (" .. low_z .. ", " .. high_z .. "),", "\n")
        file:write("},", "\n")

        currPresetAddr = currPresetAddr + 0x44
        count = count + 1
    end
    file:write("}", "\n")
end

file:close()
console.log("Done.")