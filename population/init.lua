alua.population = alua.population or {
    simulation_levels = {
        ACTIVE = "active",
        NEAR = "near",
        BACKGROUND = "background",
        DORMANT = "dormant",
    },
}

alua.register_module({
    id = "population.core",
    requires = {"world.core"},
    enabled = function()
        return alua.config.get_bool("population")
    end,
    init = function()
        -- Populace je oddělená od AI: NPC může existovat i bez plné kognice.
    end,
})
