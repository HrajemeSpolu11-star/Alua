alua.register_module({
    id = "debug.core",
    enabled = function()
        return alua.config.get_bool("debug")
    end,
    init = function()
        core.register_chatcommand("alua_modules", {
            description = "Vypíše stav modulární architektury Alua",
            func = function()
                local lines = {"[Alua] Moduly:"}
                for _, item in ipairs(alua.list_modules()) do
                    table.insert(lines, "- " .. item.id .. " = " .. item.status)
                end
                return true, table.concat(lines, "\n")
            end,
        })
    end,
})
