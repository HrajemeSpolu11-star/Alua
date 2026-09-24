alua.economy = alua.economy or {}

alua.register_module({
    id = "economy.core",
    requires = {"world.core", "population.core"},
    enabled = function()
        return alua.config.get_bool("economy")
    end,
    init = function()
        -- Zásoby, výroba, obchod a ceny budou samostatné ekonomické subsystémy.
    end,
})
