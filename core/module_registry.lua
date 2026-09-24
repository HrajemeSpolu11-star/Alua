alua.modules = alua.modules or {
    definitions = {},
    order = {},
    initialized = {},
    failed = {},
}

function alua.register_module(def)
    assert(type(def) == "table", "Alua module definition must be a table")
    assert(type(def.id) == "string" and def.id ~= "", "Alua module requires a non-empty id")

    if alua.modules.definitions[def.id] then
        error("Alua module already registered: " .. def.id)
    end

    def.requires = def.requires or {}
    alua.modules.definitions[def.id] = def
    table.insert(alua.modules.order, def.id)
    return def
end

function alua.get_module(id)
    return alua.modules.definitions[id]
end

function alua.is_module_initialized(id)
    return alua.modules.initialized[id] == true
end

local function init_one(id, ctx, visiting)
    if alua.modules.initialized[id] then
        return true
    end

    if alua.modules.failed[id] then
        return false
    end

    local def = alua.modules.definitions[id]
    if not def then
        core.log("error", "[Alua] Missing required module: " .. tostring(id))
        alua.modules.failed[id] = "missing"
        return false
    end

    visiting = visiting or {}
    if visiting[id] then
        core.log("error", "[Alua] Circular module dependency detected at: " .. id)
        alua.modules.failed[id] = "dependency_cycle"
        return false
    end

    visiting[id] = true

    for _, dependency in ipairs(def.requires or {}) do
        if not init_one(dependency, ctx, visiting) then
            core.log("error", "[Alua] Module " .. id .. " cannot start because dependency failed: " .. dependency)
            alua.modules.failed[id] = "dependency_failed:" .. dependency
            visiting[id] = nil
            return false
        end
    end

    visiting[id] = nil

    if def.enabled and not def.enabled(ctx) then
        core.log("action", "[Alua] Module disabled by configuration: " .. id)
        alua.modules.initialized[id] = true
        return true
    end

    if def.init then
        local ok, err = pcall(def.init, ctx)
        if not ok then
            core.log("error", "[Alua] Module init failed (" .. id .. "): " .. tostring(err))
            alua.modules.failed[id] = tostring(err)
            return false
        end
    end

    alua.modules.initialized[id] = true
    core.log("action", "[Alua] Initialized module: " .. id)
    return true
end

function alua.init_modules(ctx)
    for _, id in ipairs(alua.modules.order) do
        init_one(id, ctx, {})
    end
end

function alua.list_modules()
    local result = {}

    for _, id in ipairs(alua.modules.order) do
        local status = "registered"
        if alua.modules.initialized[id] then
            status = "initialized"
        elseif alua.modules.failed[id] then
            status = "failed: " .. tostring(alua.modules.failed[id])
        end

        table.insert(result, {
            id = id,
            status = status,
            requires = alua.modules.definitions[id].requires or {},
        })
    end

    return result
end
