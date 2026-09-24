alua.world = alua.world or {}

alua.register_module({
    id = "world.core",
    enabled = function()
        return alua.config.get_bool("world")
    end,
    init = function()
        alua.world.enabled = true
    end,
})
