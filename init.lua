local MODNAME = core.get_current_modname()

core.log("action", "[" .. MODNAME .. "] Mod Alua byl uspesne nacten.")

core.register_chatcommand("alua_test", {
    description = "Overi, ze mod Alua bezi",
    func = function(name)
        return true, "Alua funguje. Hrac: " .. name
    end,
})
