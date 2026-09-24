alua.state = alua.state or {}

local storage = core.get_mod_storage()
local CURRENT_SCHEMA = 1

function alua.state.get_schema_version()
    local raw = storage:get_string("meta:schema_version")
    if raw == "" then
        return 0
    end
    return tonumber(raw) or 0
end

function alua.state.set_schema_version(version)
    storage:set_string("meta:schema_version", tostring(version))
end

function alua.state.get_table(key, default)
    local raw = storage:get_string(key)
    if raw == "" then
        return default
    end

    local ok, value = pcall(core.deserialize, raw, true)
    if ok and type(value) == "table" then
        return value
    end

    core.log("warning", "[Alua] Could not deserialize state key: " .. key)
    return default
end

function alua.state.set_table(key, value)
    assert(type(value) == "table", "Alua persistent table value expected")
    storage:set_string(key, core.serialize(value))
end

function alua.state.initialize()
    local current = alua.state.get_schema_version()

    if current == 0 then
        alua.state.set_schema_version(CURRENT_SCHEMA)
        return
    end

    if current > CURRENT_SCHEMA then
        core.log("warning", "[Alua] Save schema is newer than this mod version: " .. current)
    end
end
