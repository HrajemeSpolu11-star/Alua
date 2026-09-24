alua.story = alua.story or {
    events = {},
}

function alua.story.register_event_type(id, definition)
    assert(type(id) == "string" and id ~= "", "Story event id is required")
    assert(type(definition) == "table", "Story event definition must be a table")
    alua.story.events[id] = definition
end

alua.register_module({
    id = "story.core",
    requires = {"world.core"},
    enabled = function()
        return alua.config.get_bool("story")
    end,
    init = function()
        -- Kampaň má používat události a rozhraní, ne přepisovat interní stav AI.
    end,
})
