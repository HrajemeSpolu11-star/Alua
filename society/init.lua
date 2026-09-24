alua.society = alua.society or {}

alua.register_module({
    id = "society.core",
    requires = {"population.core"},
    enabled = function()
        return alua.config.get_bool("society")
    end,
    init = function()
        -- Vztahy, rodiny, reputace, frakce a osady budou rozdělené moduly.
    end,
})
