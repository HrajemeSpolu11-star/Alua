alua.config = alua.config or {}

local defaults = {
    world = true,
    ai = true,
    population = true,
    economy = true,
    society = true,
    story = true,
    debug = true,
}

function alua.config.get_bool(key)
    local default = defaults[key]
    if default == nil then
        default = false
    end

    return core.settings:get_bool("alua_" .. key, default)
end

function alua.config.get_defaults()
    local copy = {}
    for key, value in pairs(defaults) do
        copy[key] = value
    end
    return copy
end
