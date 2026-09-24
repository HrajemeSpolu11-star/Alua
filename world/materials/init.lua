alua.materials = alua.materials or {
    definitions = {},
}

function alua.materials.register(id, definition)
    assert(type(id) == "string" and id ~= "", "Material id is required")
    assert(type(definition) == "table", "Material definition must be a table")

    if alua.materials.definitions[id] then
        error("Material already registered: " .. id)
    end

    alua.materials.definitions[id] = definition
end

function alua.materials.get(id)
    return alua.materials.definitions[id]
end

alua.register_module({
    id = "world.materials",
    requires = {"world.core"},
    init = function()
        -- Registr je připravený, ale reálné materiálové hodnoty zatím nejsou zapnuté.
    end,
})
