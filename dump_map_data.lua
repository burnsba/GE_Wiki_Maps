require "Data\\GE\\PositionData"
require "Data\\GE\\GameData"
require "Data\\GE\\ObjectData"
require "Utilities\\GE\\ObjectDataReader"
require "Utilities\\GE\\GuardDataReader"

-- ===========================================
local PRINT_TILES = true
local PRINT_OBJECTS = true
local PRINT_GUARDS = true
local PRINT_PADS = true

local filename = "frigate\\data.py"

-- ===========================================

file = io.open(filename, "w")

local scale = GameData.get_scale()
local all_tiles = TileData.getAllTiles()

file:write("level_scale = " .. scale .. "\n")

if PRINT_TILES then
    file:write("tiles = {", "\n")
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

        file:write("  \"room\" : " .. ("0x%04X"):format(TileData:get_value(tile, "room")) .. ",", "\n")
        
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
end

-- (PADs to be restored in places maybe later)


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
    ObjectDataReader.for_each(function(odr)

        local tile = 0
        local position = nil
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
                local hingePos = doorDataGetHinge(odr.current_address)  -- types 5 and 9 only atm
                file:write("  \"door_type\" : " .. doorType .. ",", "\n")
                if hingePos ~= nil then
                    file:write("  \"hinge\" : (" .. hingePos.x .. ", " .. hingePos.z .. "),", "\n")
                end
            end

            file:write("  \"type\" : \"" .. type .. "\",", "\n")
            file:write("},", "\n")
        end
    end)

    file:write("}", "\n")
end

if PRINT_GUARDS then
    file:write("\nguards = {", "\n")
    GuardDataReader.for_each(function(gdr)
        local pdp = gdr:get_value("position_data_pointer") - 0x80000000
        local pos = PositionData:get_value(pdp, "position")
        local tile = PositionData:get_value(pdp, "tile_pointer") - 0x80000000
        local cr = gdr:get_value("collision_radius")
        local id = gdr:get_value("id")
        file:write(("0x%06X"):format(gdr.current_address) .. " : {", "\n")
        file:write("  \"position\" : (" .. pos.x .. ", " .. pos.z .. "),", "\n") -- ignore y
        file:write("  \"tile\" : " .. ("0x%06X"):format(tile) .. ",", "\n")
        file:write("  \"radius\" : " .. cr .. ",", "\n")
        file:write(("  \"id\" : 0x%04X,"):format(id), "\n")
        file:write("},", "\n")
    end)

    file:write("}", "\n")
end

if PRINT_PADS then
    file:write("\npads = {", "\n")

    local padPtr = PadData.get_start_address()
	while true do
		local n = PadData:get_value(padPtr, "number")
        if n == -1 then
            break
        end
        local pos = PadData.padPosFromNum(n)

        file:write(("0x%04X : {\n"):format(n))
        file:write("  \"position\" : (" .. pos.x .. ", " .. pos.y .. ", " .. pos.z .. "),", "\n")
        file:write("  \"neighbours\" : [")
        for _, neighbour in ipairs(PadData.get_pad_neighbours(padPtr)) do
            file:write(("0x%04X, "):format(neighbour))
        end
        file:write("],", "\n")
        file:write("},", "\n")
    
		padPtr = padPtr + 0x10
    end
    
    file:write("}", "\n")
end

file:close()
console.log("Done.")