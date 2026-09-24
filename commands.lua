local function result(ok, message)
    return ok, "[Alua] " .. message
end

core.register_chatcommand("alua_test", {
    description = "Checks that Alua is loaded",
    func = function(name)
        return result(true, "Framework is running for player " .. name .. ".")
    end,
})

core.register_chatcommand("alua_spawn", {
    description = "Spawns your Alua autonomous companion",
    func = function(name)
        local object, message = alua.spawn(name)
        if not object then
            return result(false, message)
        end
        return result(true, "Companion spawned in follow mode.")
    end,
})

core.register_chatcommand("alua_follow", {
    description = "Sets your Alua companion to follow you",
    func = function(name)
        local ok, message = alua.set_mode(name, "follow")
        return result(ok, message)
    end,
})

core.register_chatcommand("alua_stay", {
    description = "Tells your Alua companion to stay",
    func = function(name)
        local ok, message = alua.set_mode(name, "stay")
        return result(ok, message)
    end,
})

core.register_chatcommand("alua_recall", {
    description = "Teleports your loaded Alua companion back to you",
    func = function(name)
        local ok, message = alua.recall(name)
        return result(ok, message)
    end,
})

core.register_chatcommand("alua_status", {
    description = "Shows the current state and simple memory of your Alua companion",
    func = function(name)
        local player = core.get_player_by_name(name)
        local object, entity = alua.find_owned(name)

        if not player or not object or not entity then
            return result(false, "No loaded Alua companion found.")
        end

        local pos = object:get_pos()
        local distance = pos and vector.distance(player:get_pos(), pos) or 0
        local memory = entity.memory or {}
        local last = memory.last_owner_pos
        local last_text = last and core.pos_to_string(last, 0) or "unknown"

        return result(true,
            "mode=" .. (entity.mode or "unknown")
            .. " | distance=" .. string.format("%.1f", distance)
            .. " | last owner position=" .. last_text)
    end,
})

core.register_chatcommand("alua_scan", {
    description = "Lets your Alua companion report simple local sensor data",
    func = function(name)
        local object = alua.find_owned(name)
        if not object then
            return result(false, "No loaded Alua companion found.")
        end

        local pos = object:get_pos()
        if not pos then
            return result(false, "Companion position is unavailable.")
        end

        local nearby_players = 0
        for _, candidate in ipairs(core.get_objects_inside_radius(pos, 12)) do
            if candidate:is_player() then
                nearby_players = nearby_players + 1
            end
        end

        local below = {
            x = math.floor(pos.x + 0.5),
            y = math.floor(pos.y - 1),
            z = math.floor(pos.z + 0.5),
        }
        local node = core.get_node_or_nil(below)
        local node_name = node and node.name or "unknown"

        return result(true,
            "sensor report: nearby players=" .. nearby_players
            .. " | node below=" .. node_name
            .. " | position=" .. core.pos_to_string(vector.round(pos), 0))
    end,
})

core.register_chatcommand("alua_remove", {
    description = "Removes your loaded Alua companion",
    func = function(name)
        local ok, message = alua.remove_owned(name)
        return result(ok, message)
    end,
})

core.register_chatcommand("alua_help", {
    description = "Lists Alua commands",
    func = function()
        return result(true,
            "/alua_spawn, /alua_follow, /alua_stay, /alua_recall, /alua_status, /alua_scan, /alua_remove")
    end,
})
