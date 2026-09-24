alua.world_adapter = alua.world_adapter or {
    sensors = {},
    actions = {},
}

function alua.world_adapter.register_sensor(id, fn)
    assert(type(id) == "string" and id ~= "", "Sensor id is required")
    assert(type(fn) == "function", "Sensor callback must be a function")

    if alua.world_adapter.sensors[id] then
        error("Sensor already registered: " .. id)
    end

    alua.world_adapter.sensors[id] = fn
end

function alua.world_adapter.register_action(id, fn)
    assert(type(id) == "string" and id ~= "", "Action id is required")
    assert(type(fn) == "function", "Action callback must be a function")

    if alua.world_adapter.actions[id] then
        error("Action already registered: " .. id)
    end

    alua.world_adapter.actions[id] = fn
end

function alua.world_adapter.sense(id, agent_context, request)
    local sensor = alua.world_adapter.sensors[id]
    if not sensor then
        return nil, "unknown_sensor"
    end

    local ok, result = pcall(sensor, agent_context, request)
    if not ok then
        core.log("error", "[Alua] Sensor failed (" .. id .. "): " .. tostring(result))
        return nil, "sensor_failed"
    end

    return result
end

function alua.world_adapter.act(id, agent_context, request)
    local action = alua.world_adapter.actions[id]
    if not action then
        return false, "unknown_action"
    end

    local ok, result, detail = pcall(action, agent_context, request)
    if not ok then
        core.log("error", "[Alua] Action failed (" .. id .. "): " .. tostring(result))
        return false, "action_failed"
    end

    return result, detail
end

alua.register_module({
    id = "world.adapter",
    requires = {"world.core"},
    init = function()
        -- Záměrně zde nejsou žádné vševědoucí senzory.
        -- Konkrétní smysly budou přidávány jako explicitní, omezená rozhraní.
    end,
})
