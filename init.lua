alua = rawget(_G, "alua") or {}
_G.alua = alua

alua.modname = core.get_current_modname()
alua.modpath = core.get_modpath(alua.modname)
alua.active = alua.active or {}

core.log("action", "[Alua] Loading modular autonomous companion framework")

dofile(alua.modpath .. "/core/module_registry.lua")
dofile(alua.modpath .. "/core/events.lua")
dofile(alua.modpath .. "/core/state.lua")

alua.state.initialize()

-- Existing gameplay is intentionally kept working while it is migrated
-- incrementally into the modular architecture.
dofile(alua.modpath .. "/npc.lua")
dofile(alua.modpath .. "/commands.lua")

alua.init_modules({
    modname = alua.modname,
    modpath = alua.modpath,
    events = alua.events,
    state = alua.state,
})

core.log("action", "[Alua] Loaded successfully")
