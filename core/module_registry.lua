alua.modules = alua.modules or {
    definitions = {},
    order = {},
    initialized = {},
}

function alua.register_module(def)
    assert(type(def) == "table", "Alua module definition must be a table")
    assert(type(def.id) == "string" and def.id ~= "", "Alua module requires a non-empty id")

    if alua.modules.definitions[def.id] then
        error("Alua module already registered: " .. def.id)
    end

    alua.modules.definitions[def.id] = def
    table.insert(alua.modules.order, def.id)
    return def
end

function alua.get_module(id)
    return alua.modules.definitions[id]
end

function alua.init_modules(ctx)
    for _, id in ipairs(alua.modules.order) do
        local def = alua.modules.definitions[id]

        if def.init and not alua.modules.initialized[id] then
            local ok, err = pcall(def.init, ctx)
            if ok then
                alua.modules.initialized[id] = true
                core.log("action", "[Alua] Initialized module: " .. id)
            else
                core.log("error", "[Alua] Module init failed (" .. id .. "): " .. tostring(err))
            end
        end
    end
end
